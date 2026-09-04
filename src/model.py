"""
2026 fantasy football projection + valuation model.

Pipeline
--------
1. Positional scoring curves are anchored to published 2026 projection points
   (see ANCHORS below) and interpolated in log-rank space. This reproduces the
   shape of a real projection set without inventing precision we do not have.
2. Each player's raw projection = curve(pos, consensus_pos_rank), then scaled by
   expected games played and a research-driven per-game multiplier (`adj`).
3. Value Over Replacement (VOR) is computed against a starter-demand baseline
   derived from league settings, not against an arbitrary "RB24" cutoff.
4. Tiers are cut where the drop between consecutive players at a position
   exceeds a within-position dispersion threshold.
5. Auction values distribute the league budget across positive-VOR players.

All inputs live in data/players_2026.csv so the assumptions stay auditable.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "players_2026.csv"

# Anchor points: (positional rank, projected full-season PPR points).
# Sourced/calibrated from published 2026 projections — Josh Allen ~361, Gibbs
# ~331, Lamar ~326, George Pickens ~252 at WR12-ish consensus rank — then filled
# out with historically typical positional decay shapes.
ANCHORS: dict[str, list[tuple[float, float]]] = {
    # QB12 ~ 4,200 yds / 28 pass TD / 300 rush yds ~ 290 PPR, so the elite-QB
    # edge is much smaller than it looks in raw points.
    "QB": [(1, 361.0), (3, 336.0), (6, 316.0), (12, 288.0), (18, 260.0), (24, 236.0), (30, 214.0)],
    "RB": [(1, 331.0), (3, 281.0), (6, 249.0), (12, 206.0), (18, 176.0), (24, 155.0), (36, 116.0), (55, 78.0)],
    # Anchored on the published George Pickens projection: 82.6/1201/8.4 = 252 PPR.
    "WR": [(1, 308.0), (4, 276.0), (10, 252.0), (20, 205.0), (30, 178.0), (40, 152.0), (53, 122.0)],
    # McBride went 126/1239/11 = 316 PPR in 2025; that was a peak outcome, so the
    # TE1 line regresses to roughly 95/1100/8.
    "TE": [(1, 255.0), (2, 247.0), (5, 176.0), (10, 142.0), (15, 116.0), (18, 101.0)],
    "K": [(1, 152.0), (5, 133.0), (10, 118.0)],
    "DST": [(1, 140.0), (6, 112.0), (12, 92.0)],
}

# Standard 12-team league: 1QB / 2RB / 3WR / 1TE / 1FLEX / 1K / 1DST, 6 bench.
DEFAULT_LEAGUE = dict(teams=12, qb=1, rb=2, wr=3, te=1, flex=1, k=1, dst=1, bench=6, budget=200)


def _interp_log_rank(anchors: list[tuple[float, float]], rank: float) -> float:
    """Piecewise-linear interpolation in log(rank) space, flat-extrapolated with decay."""
    xs = [math.log(a[0]) for a in anchors]
    ys = [a[1] for a in anchors]
    x = math.log(max(rank, 1.0))
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        # Continue the final slope, but never below a small floor.
        slope = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
        return max(ys[-1] + slope * (x - xs[-1]), 8.0)
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + t * (ys[i + 1] - ys[i])
    return ys[-1]


@dataclass
class Player:
    player: str
    pos: str
    team: str
    bye: int
    pos_rank: int
    adp: float
    games: float
    adj: float
    risk: int
    ceiling: int
    note: str
    proj: float = 0.0
    vor: float = 0.0
    tier: int = 0
    auction: float = 0.0
    value_rank: int = 0
    edge: float = 0.0  # ADP minus value rank; positive means the market is late on him

    @property
    def ppg(self) -> float:
        return self.proj / self.games if self.games else 0.0


def load_players(path: Path = DATA) -> list[Player]:
    out: list[Player] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out.append(
                Player(
                    player=row["player"],
                    pos=row["pos"],
                    team=row["team"],
                    bye=int(row["bye"]),
                    pos_rank=int(row["pos_rank"]),
                    adp=float(row["adp"]),
                    games=float(row["games"]),
                    adj=float(row["adj"]),
                    risk=int(row["risk"]),
                    ceiling=int(row["ceiling"]),
                    note=row["note"],
                )
            )
    return out


def project(players: list[Player]) -> None:
    """Full-season projection = curve(pos_rank) * (games/17) * per-game adjustment."""
    for p in players:
        base = _interp_log_rank(ANCHORS[p.pos], p.pos_rank)
        p.proj = round(base * (p.games / 17.0) * p.adj, 1)


def replacement_levels(players: list[Player], league: dict) -> dict[str, float]:
    """
    Replacement level = the projection of the last player at each position who
    would realistically be started, accounting for FLEX demand.

    FLEX slots are allocated to whichever of RB/WR/TE actually wins them, which
    is what makes the RB/WR baselines move relative to each other year to year.
    """
    teams = league["teams"]
    by_pos: dict[str, list[Player]] = {}
    for p in players:
        by_pos.setdefault(p.pos, []).append(p)
    for lst in by_pos.values():
        lst.sort(key=lambda x: -x.proj)

    # Base starter demand before flex.
    demand = {
        "QB": teams * league["qb"],
        "RB": teams * league["rb"],
        "WR": teams * league["wr"],
        "TE": teams * league["te"],
        "K": teams * league["k"],
        "DST": teams * league["dst"],
    }

    # Award flex slots one at a time to the best remaining RB/WR/TE.
    flex_slots = teams * league["flex"]
    for _ in range(flex_slots):
        best_pos, best_val = None, -1.0
        for pos in ("RB", "WR", "TE"):
            idx = demand[pos]
            pool = by_pos.get(pos, [])
            if idx < len(pool) and pool[idx].proj > best_val:
                best_pos, best_val = pos, pool[idx].proj
        if best_pos is None:
            break
        demand[best_pos] += 1

    levels: dict[str, float] = {}
    for pos, n in demand.items():
        pool = by_pos.get(pos, [])
        if not pool:
            levels[pos] = 0.0
            continue
        idx = min(n, len(pool)) - 1
        levels[pos] = pool[idx].proj
    return levels


def compute_vor(players: list[Player], league: dict = DEFAULT_LEAGUE) -> dict[str, float]:
    levels = replacement_levels(players, league)
    for p in players:
        p.vor = round(p.proj - levels[p.pos], 1)
    ranked = sorted(players, key=lambda x: -x.vor)
    for i, p in enumerate(ranked, 1):
        p.value_rank = i
        p.edge = round(p.adp - i, 1)
    return levels


def assign_tiers(players: list[Player]) -> None:
    """
    Cut a new tier whenever the gap to the next player at that position exceeds
    0.75 standard deviations of the gap distribution for that position. This
    finds the real cliffs rather than imposing fixed tier sizes.
    """
    by_pos: dict[str, list[Player]] = {}
    for p in players:
        by_pos.setdefault(p.pos, []).append(p)
    for pos, lst in by_pos.items():
        lst.sort(key=lambda x: -x.proj)
        gaps = [lst[i].proj - lst[i + 1].proj for i in range(len(lst) - 1)]
        if not gaps:
            for p in lst:
                p.tier = 1
            continue
        mean = sum(gaps) / len(gaps)
        var = sum((g - mean) ** 2 for g in gaps) / len(gaps)
        sd = math.sqrt(var)
        threshold = mean + 0.75 * sd
        tier = 1
        lst[0].tier = 1
        for i in range(1, len(lst)):
            if lst[i - 1].proj - lst[i].proj > threshold:
                tier += 1
            lst[i].tier = tier


def auction_values(players: list[Player], league: dict = DEFAULT_LEAGUE) -> None:
    """
    Distribute the league's discretionary budget over positive-VOR players.
    Every roster spot costs at least $1, so only the surplus is allocated by VOR.
    """
    teams = league["teams"]
    roster_size = (
        league["qb"] + league["rb"] + league["wr"] + league["te"]
        + league["flex"] + league["k"] + league["dst"] + league["bench"]
    )
    total_budget = teams * league["budget"]
    total_slots = teams * roster_size
    discretionary = total_budget - total_slots  # $1 minimum per slot

    pos_vor = [p for p in players if p.vor > 0]
    vor_sum = sum(p.vor for p in pos_vor) or 1.0
    dollars_per_vor = discretionary / vor_sum
    for p in players:
        p.auction = round(1 + max(p.vor, 0.0) * dollars_per_vor, 1) if p.vor > 0 else 1.0


def build(league: dict = DEFAULT_LEAGUE) -> tuple[list[Player], dict[str, float]]:
    players = load_players()
    project(players)
    levels = compute_vor(players, league)
    assign_tiers(players)
    auction_values(players, league)
    return players, levels


if __name__ == "__main__":
    players, levels = build()
    print("Replacement levels (PPR points):")
    for pos, v in sorted(levels.items()):
        print(f"  {pos:>3}: {v:6.1f}")
    print("\nTop 40 by value over replacement:")
    print(f"{'#':>3} {'PLAYER':<24}{'POS':<5}{'TM':<5}{'PROJ':>7}{'VOR':>7}{'ADP':>7}{'EDGE':>7}{'$':>6}")
    for p in sorted(players, key=lambda x: -x.vor)[:40]:
        print(
            f"{p.value_rank:>3} {p.player:<24}{p.pos + str(p.pos_rank):<5}{p.team:<5}"
            f"{p.proj:>7.1f}{p.vor:>7.1f}{p.adp:>7.1f}{p.edge:>+7.1f}{p.auction:>6.0f}"
        )
