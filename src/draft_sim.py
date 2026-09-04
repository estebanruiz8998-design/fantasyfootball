"""
Monte Carlo snake-draft simulator for the 2026 season.

Why this exists: a cheat sheet tells you who is underpriced, but it cannot tell
you whether a strategy actually survives contact with eleven other drafters.
This simulates the whole thing — opponent behaviour, injuries, byes, and weekly
lineup decisions — so strategies are judged on points that actually reach a
starting lineup rather than on raw roster talent.

Model
-----
* Opponents draft from ADP with Gumbel noise plus soft positional needs, which
  reproduces real-draft behaviour: runs at a position, occasional reaches, and
  kickers/defenses going late.
* Each simulated season draws a per-player scoring level and a contiguous block
  of missed games, so depth and handcuffs earn their value honestly.
* Lineups are set optimally each week from whoever is available, including byes.
* Scoring is split into the fantasy regular season (Weeks 1-14) and the fantasy
  playoffs (Weeks 15-17), because those are different questions.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field

from model import DEFAULT_LEAGUE, Player, build

ROSTER_SLOTS = ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "FLEX", "K", "DST"]
FLEX_OK = {"RB", "WR", "TE"}
ROUNDS = 16
REG_WEEKS = list(range(1, 15))
PLAYOFF_WEEKS = [15, 16, 17]

# Positional caps stop the opponent model and the strategies from doing absurd
# things like rostering six quarterbacks.
MAX_AT_POS = {"QB": 2, "RB": 7, "WR": 8, "TE": 2, "K": 1, "DST": 1}
MIN_AT_POS = {"QB": 1, "RB": 4, "WR": 5, "TE": 1, "K": 1, "DST": 1}


@dataclass
class Team:
    name: str
    players: list[Player] = field(default_factory=list)

    def count(self, pos: str) -> int:
        return sum(1 for p in self.players if p.pos == pos)

    def needs(self) -> dict[str, int]:
        return {pos: max(0, MIN_AT_POS[pos] - self.count(pos)) for pos in MIN_AT_POS}


# --------------------------------------------------------------------------
# Opponent model
# --------------------------------------------------------------------------

def opponent_pick(team: Team, available: list[Player], pick_no: int, rng: random.Random) -> Player:
    """
    Choose by noisy ADP. Noise grows later in the draft, mirroring how consensus
    tightens at the top and dissolves by round 10.
    """
    rounds_left = ROUNDS - len(team.players)
    best, best_score = None, float("inf")
    for p in available:
        if team.count(p.pos) >= MAX_AT_POS[p.pos]:
            continue
        # Kickers and defenses are almost never taken before the last three rounds.
        if p.pos in ("K", "DST") and rounds_left > 3:
            continue
        # Must leave room to fill mandatory slots.
        unmet = sum(v for k, v in team.needs().items() if k != p.pos)
        if unmet >= rounds_left:
            if team.needs().get(p.pos, 0) == 0:
                continue
        noise = rng.gauss(0, 6 + 0.35 * pick_no)
        score = p.adp + noise
        # Mild need bonus so rosters stay coherent.
        if team.needs().get(p.pos, 0) > 0:
            score -= 12
        if score < best_score:
            best, best_score = p, score
    if best is None:
        best = min(available, key=lambda p: p.adp)
    return best


# --------------------------------------------------------------------------
# Strategies
# --------------------------------------------------------------------------
# A strategy is a list of allowed position sets by round. None means "anything".

STRATEGIES: dict[str, list[set[str] | None]] = {
    # Three of the first four picks on running backs.
    "ROBUST_RB": [{"RB"}, {"RB"}, {"WR"}, {"RB"}, {"WR"}, {"WR", "TE"}, None, None,
                  None, None, None, None, None, None, {"K"}, {"DST"}],
    # One anchor back, then receivers.
    "HERO_RB": [{"RB"}, {"WR"}, {"WR"}, {"WR", "TE"}, {"RB"}, {"RB"}, None, None,
                None, None, None, None, None, None, {"K"}, {"DST"}],
    # No running back until round five.
    "ZERO_RB": [{"WR"}, {"WR"}, {"WR", "TE"}, {"WR", "TE"}, {"RB"}, {"RB"}, {"RB"}, None,
                None, None, None, None, None, None, {"K"}, {"DST"}],
    # Elite tight end early, then best value.
    "ELITE_TE": [{"RB", "WR"}, {"TE"}, {"WR"}, {"RB"}, {"WR"}, {"RB"}, None, None,
                 None, None, None, None, None, None, {"K"}, {"DST"}],
    # Pure value: always take the highest VOR that fits, no positional dogma.
    "BEST_VALUE": [None] * 14 + [{"K"}, {"DST"}],
}

# --------------------------------------------------------------------------
# The recommended strategy is not a fixed positional script. Scripts lose to
# flexible value-taking because they force picks the board is not offering.
# Instead it takes the best value available under soft guardrails.
# --------------------------------------------------------------------------

# Weight applied to bench players by depth order. A first bench piece has real
# expected value through byes and injuries; a seventh has very little.
BENCH_WEIGHTS = [0.34, 0.24, 0.17, 0.12, 0.08, 0.05, 0.03, 0.02]


def lineup_value(roster: list[Player]) -> float:
    """
    Expected value of a roster measured the way scoring actually works: only
    starters count in full, and bench players count for the fraction of the
    season they are realistically needed.

    This is the correction to naive VOR. A sixth receiver has a large VOR and
    almost no marginal value, because he cannot get into the lineup.
    """
    by_pos: dict[str, list[float]] = {}
    for p in roster:
        by_pos.setdefault(p.pos, []).append(p.proj)
    for v in by_pos.values():
        v.sort(reverse=True)

    used: dict[str, int] = {}
    total = 0.0
    for slot in ROSTER_SLOTS:
        if slot == "FLEX":
            continue
        i = used.get(slot, 0)
        pool = by_pos.get(slot, [])
        if i < len(pool):
            total += pool[i]
            used[slot] = i + 1

    # Flex goes to the best remaining RB/WR/TE.
    flex_pos, flex_val = None, 0.0
    for pos in FLEX_OK:
        i = used.get(pos, 0)
        pool = by_pos.get(pos, [])
        if i < len(pool) and pool[i] > flex_val:
            flex_pos, flex_val = pos, pool[i]
    if flex_pos:
        total += flex_val
        used[flex_pos] = used.get(flex_pos, 0) + 1

    # Everything left over is bench, valued at a decaying weight.
    bench: list[float] = []
    for pos, pool in by_pos.items():
        bench.extend(pool[used.get(pos, 0):])
    bench.sort(reverse=True)
    for i, val in enumerate(bench):
        w = BENCH_WEIGHTS[i] if i < len(BENCH_WEIGHTS) else 0.01
        total += w * val
    return total


def _survivors(available: list[Player], next_pick: int) -> dict[str, Player | None]:
    """Best player at each position likely to still be on the board next turn."""
    out: dict[str, Player | None] = {}
    for p in available:
        # ADP is a mean, so require a small buffer before treating a player as
        # someone we can confidently wait on.
        if p.adp < next_pick + 2:
            continue
        cur = out.get(p.pos)
        if cur is None or p.proj > cur.proj:
            out[p.pos] = p
    return out


def model_score(p: Player, team: Team, rnd: int, base: float,
                alt_gains: dict[str, float]) -> float:
    """
    Value Over Next Available (VONA).

    The question at every pick is not "who is best?" but "who gains me the most
    over the player I could still get at this position next time round?" That
    single change is what stops the model taking an elite quarterback in round
    one: the quarterback you can get eight rounds later is nearly as good, while
    the receiver you pass on is not replaceable at all.
    """
    own_gain = lineup_value(team.players + [p]) - base

    # Opportunity cost: what this same roster slot would gain from the best
    # player at this position still likely to be there at our next turn. If the
    # player himself is likely to survive, taking him now buys nothing.
    gain = own_gain - alt_gains.get(p.pos, 0.0)

    # Handcuff premium: a backup behind a back you already own inherits a full
    # workload, so he is worth more to you than to anyone else at the table.
    if p.pos == "RB" and rnd >= 7:
        if any(o.pos == "RB" and o.team == p.team for o in team.players):
            gain += 14

    # Late picks should buy ceiling, not floor — a bench player only helps if he
    # turns into a starter.
    if rnd >= 9:
        gain += 2.5 * (p.ceiling - 3)
        gain -= 1.5 * (p.risk - 3)

    # Bye-week collision among likely starters at the same position.
    same_bye = sum(1 for o in team.players if o.bye == p.bye and o.pos == p.pos)
    if same_bye >= 2:
        gain -= 6 * same_bye

    # Discount players unlikely to be available at the start of the season.
    if p.games < 12:
        gain -= 12
    return gain


def model_pick(team: Team, available: list[Player], rnd: int, next_pick: int,
               rng: random.Random) -> Player:
    rounds_left = ROUNDS - len(team.players)
    base = lineup_value(team.players)
    # Opportunity cost depends only on position, so compute it once per position
    # rather than once per candidate.
    survivors = _survivors(available, next_pick)
    alt_gains = {
        pos: (lineup_value(team.players + [alt]) - base)
        for pos, alt in survivors.items() if alt is not None
    }

    pool: list[Player] = []
    for p in available:
        if team.count(p.pos) >= MAX_AT_POS[p.pos]:
            continue
        if p.pos in ("K", "DST") and rounds_left > 2:
            continue
        unmet = sum(v for k, v in team.needs().items() if k != p.pos)
        if unmet >= rounds_left and team.needs().get(p.pos, 0) == 0:
            continue
        pool.append(p)
    if not pool:
        pool = list(available)
    return max(pool, key=lambda p: model_score(p, team, rnd, base, alt_gains))


def strategy_pick(team: Team, available: list[Player], rnd: int, plan: list, rng: random.Random) -> Player:
    rounds_left = ROUNDS - len(team.players)
    allowed = plan[rnd] if rnd < len(plan) else None

    def eligible(pos_filter: set[str] | None) -> list[Player]:
        out = []
        for p in available:
            if team.count(p.pos) >= MAX_AT_POS[p.pos]:
                continue
            if pos_filter is not None and p.pos not in pos_filter:
                continue
            if p.pos in ("K", "DST") and rounds_left > 2:
                continue
            unmet = sum(v for k, v in team.needs().items() if k != p.pos)
            if unmet >= rounds_left and team.needs().get(p.pos, 0) == 0:
                continue
            out.append(p)
        return out

    pool = eligible(allowed)
    if not pool:
        pool = eligible(None)
    if not pool:
        return available[0]

    # Take the best value available, with a small nudge toward upside late.
    def key(p: Player) -> float:
        bonus = 0.0
        if rnd >= 8:
            bonus = 3.0 * (p.ceiling - 3)
        return -(p.vor + bonus)

    return min(pool, key=key)


# --------------------------------------------------------------------------
# Season simulation
# --------------------------------------------------------------------------

def simulate_season(roster: list[Player], rng: random.Random) -> tuple[float, float]:
    """Return (regular-season starter points, playoff-week starter points)."""
    weekly: dict[int, list[tuple[float, str]]] = {w: [] for w in range(1, 18)}

    for p in roster:
        # Scoring level for the season. Higher risk and higher ceiling both widen
        # the distribution; ceiling skews it right.
        sigma = 0.13 + 0.045 * p.risk
        skew = 1.0 + 0.020 * (p.ceiling - 3)
        level = p.ppg * rng.lognormvariate(-0.5 * sigma**2, sigma) * skew

        # Missed games as one contiguous block, which is how injuries actually land.
        expected_missed = max(0.0, 17.0 - p.games)
        missed = max(0, int(round(rng.gauss(expected_missed, 1.0 + expected_missed * 0.5))))
        missed = min(missed, 17)
        out_weeks: set[int] = set()
        if missed:
            start = rng.randint(1, max(1, 18 - missed))
            out_weeks = set(range(start, start + missed))

        for w in range(1, 18):
            if w == p.bye or w in out_weeks:
                continue
            weekly[w].append((level * rng.lognormvariate(0, 0.28), p.pos))

    def best_lineup(entries: list[tuple[float, str]]) -> float:
        by_pos: dict[str, list[float]] = {}
        for score, pos in entries:
            by_pos.setdefault(pos, []).append(score)
        for v in by_pos.values():
            v.sort(reverse=True)
        used: dict[str, int] = {}
        total = 0.0
        for slot in ROSTER_SLOTS:
            if slot == "FLEX":
                continue
            i = used.get(slot, 0)
            pool = by_pos.get(slot, [])
            if i < len(pool):
                total += pool[i]
                used[slot] = i + 1
        # Flex takes the best remaining RB/WR/TE.
        best_flex = 0.0
        for pos in FLEX_OK:
            i = used.get(pos, 0)
            pool = by_pos.get(pos, [])
            if i < len(pool):
                best_flex = max(best_flex, pool[i])
        total += best_flex
        return total

    reg = sum(best_lineup(weekly[w]) for w in REG_WEEKS)
    post = sum(best_lineup(weekly[w]) for w in PLAYOFF_WEEKS)
    return reg, post


def filler_pool(players: list[Player]) -> list[Player]:
    """
    A 12-team, 16-round draft consumes 192 picks; the curated board holds fewer
    than that. Without this, drafts silently truncate and every roster ends up
    short — which is exactly the bug that made an all-receiver roster look
    survivable. These are generic replacement-level bodies representing the
    waiver tier, priced to go at the very end of drafts.
    """
    import copy

    fillers: list[Player] = []
    spec = [("RB", 14, 70.0), ("WR", 16, 72.0), ("TE", 6, 62.0), ("QB", 6, 190.0),
            ("K", 6, 112.0), ("DST", 6, 86.0)]
    adp = 210.0
    for pos, n, top in spec:
        for i in range(n):
            f = copy.copy(players[0])
            f.player = f"FA {pos}{i+1}"
            f.pos = pos
            f.team = "FA"
            f.bye = 5 + (i % 10)
            f.pos_rank = 90 + i
            f.adp = adp
            f.games = 15.0
            f.adj = 1.0
            f.risk = 3
            f.ceiling = 2
            f.note = "replacement-level filler"
            f.proj = round(top * (0.97**i), 1)
            f.vor = 0.0
            f.tier = 9
            f.auction = 1.0
            fillers.append(f)
            adp += 1.0
    return fillers


def run_draft(players: list[Player], my_slot: int, strategy: str, rng: random.Random,
              teams: int = 12) -> list[Player]:
    available = sorted(players + filler_pool(players), key=lambda p: p.adp)
    board = [Team(f"T{i+1}") for i in range(teams)]
    me = my_slot - 1
    plan = STRATEGIES.get(strategy)

    pick_no = 0
    for rnd in range(ROUNDS):
        order = range(teams) if rnd % 2 == 0 else reversed(range(teams))
        for t in order:
            pick_no += 1
            if not available:
                break
            if t == me:
                if strategy == "MODEL":
                    # Where our next turn lands in the snake, used for VONA.
                    slot = my_slot
                    if rnd % 2 == 0:
                        gap = 2 * (teams - slot) + 1
                    else:
                        gap = 2 * slot - 1
                    choice = model_pick(board[t], available, rnd, pick_no + gap, rng)
                else:
                    choice = strategy_pick(board[t], available, rnd, plan, rng)
            else:
                choice = opponent_pick(board[t], available, pick_no, rng)
            board[t].players.append(choice)
            available.remove(choice)
    return board[me].players


def evaluate(strategy: str, slot: int, players: list[Player], n_drafts: int = 120,
             seasons_per_draft: int = 12, seed: int = 0) -> dict:
    rng = random.Random(seed)
    regs, posts, rosters = [], [], []
    for _ in range(n_drafts):
        roster = run_draft(players, slot, strategy, rng)
        rosters.append(roster)
        for _ in range(seasons_per_draft):
            r, p = simulate_season(roster, rng)
            regs.append(r)
            posts.append(p)
    regs.sort()
    return {
        "strategy": strategy,
        "slot": slot,
        "mean_reg": statistics.mean(regs),
        "median_reg": statistics.median(regs),
        "p10": regs[int(0.10 * len(regs))],
        "p90": regs[int(0.90 * len(regs))],
        "mean_playoff": statistics.mean(posts),
        "rosters": rosters,
    }


if __name__ == "__main__":
    players, _ = build()
    print(f"{'STRATEGY':<12}{'SLOT':>5}{'MEAN':>9}{'P10':>9}{'P90':>9}{'PLAYOFF':>9}")
    for strat in list(STRATEGIES) + ["MODEL"]:
        for slot in (1, 6, 12):
            r = evaluate(strat, slot, players, n_drafts=40, seasons_per_draft=8, seed=7)
            print(f"{strat:<12}{slot:>5}{r['mean_reg']:>9.0f}{r['p10']:>9.0f}"
                  f"{r['p90']:>9.0f}{r['mean_playoff']:>9.0f}")
