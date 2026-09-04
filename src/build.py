"""
Runs the whole analysis and writes everything under output/.

  python3 src/build.py            # full run (several minutes)
  python3 src/build.py --quick    # fast pass for iteration
"""

from __future__ import annotations

import csv
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

from model import DEFAULT_LEAGUE, build
from draft_sim import STRATEGIES, ROUNDS, evaluate, run_draft, simulate_season

OUT = Path(__file__).resolve().parent.parent / "output"
OUT.mkdir(exist_ok=True)

QUICK = "--quick" in sys.argv
N_DRAFTS = 25 if QUICK else 60
N_SEASONS = 6 if QUICK else 10
ROSTER_SEARCH = 60 if QUICK else 250
ROSTER_EVAL = 12 if QUICK else 40
SLOTS = [1, 6, 12] if QUICK else list(range(1, 13))
ALL_STRATS = list(STRATEGIES) + ["MODEL"]


def write_cheatsheet(players):
    path = OUT / "cheatsheet.csv"
    rows = sorted(players, key=lambda p: -p.vor)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["value_rank", "player", "pos", "pos_rank", "tier", "team", "bye",
                    "proj_ppr", "ppg", "vor", "auction", "adp", "adp_edge", "risk",
                    "ceiling", "note"])
        for p in rows:
            w.writerow([p.value_rank, p.player, p.pos, p.pos_rank, p.tier, p.team, p.bye,
                        p.proj, round(p.ppg, 1), p.vor, p.auction, p.adp, p.edge,
                        p.risk, p.ceiling, p.note])
    return path


def write_tiers(players):
    path = OUT / "tiers.md"
    by_pos = defaultdict(list)
    for p in players:
        by_pos[p.pos].append(p)
    lines = ["# 2026 positional tiers", "",
             "Tiers are cut where the projection gap to the next player exceeds "
             "0.75 standard deviations of that position's gap distribution — the "
             "real cliffs, not fixed-size buckets.", ""]
    for pos in ("RB", "WR", "TE", "QB", "DST", "K"):
        lines.append(f"## {pos}")
        lines.append("")
        cur = None
        for p in sorted(by_pos[pos], key=lambda x: -x.proj):
            if p.tier != cur:
                cur = p.tier
                lines.append(f"**Tier {cur}**")
                lines.append("")
            lines.append(f"- {p.player} ({p.team}, bye {p.bye}) — "
                         f"{p.proj:.0f} proj, VOR {p.vor:+.0f}, ADP {p.adp:g}, ${p.auction:.0f}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def strategy_study(players):
    results = []
    for strat in ALL_STRATS:
        for slot in SLOTS:
            r = evaluate(strat, slot, players, n_drafts=N_DRAFTS,
                         seasons_per_draft=N_SEASONS, seed=1234 + slot)
            r.pop("rosters", None)
            results.append(r)
            print(f"  {strat:<12} slot {slot:>2}  mean={r['mean_reg']:7.0f} "
                  f"p10={r['p10']:7.0f} playoff={r['mean_playoff']:6.0f}", flush=True)
    return results


def best_rosters(players):
    """Search for the highest-expectation MODEL roster at each draft slot."""
    out = {}
    for slot in SLOTS:
        rng = random.Random(9000 + slot)
        scored = []
        for _ in range(ROSTER_SEARCH):
            roster = run_draft(players, slot, "MODEL", rng)
            regs, posts = [], []
            for _ in range(ROSTER_EVAL):
                r, p = simulate_season(roster, rng)
                regs.append(r)
                posts.append(p)
            scored.append((statistics.mean(regs), statistics.mean(posts), roster))
        scored.sort(key=lambda x: -x[0])
        out[slot] = scored[0]
        print(f"  slot {slot:>2} best roster mean={scored[0][0]:.0f}", flush=True)
    return out


def round_frequency(players):
    """Which players the model actually takes, by round and slot."""
    freq: dict[int, Counter] = defaultdict(Counter)
    rng = random.Random(4242)
    for slot in SLOTS:
        for _ in range(ROSTER_SEARCH):
            roster = run_draft(players, slot, "MODEL", rng)
            for rnd, p in enumerate(roster, 1):
                if not p.player.startswith("FA "):
                    freq[rnd][f"{p.player}|{p.pos}|{p.team}"] += 1
    return freq


def write_sim_results(results, rosters, freq):
    path = OUT / "sim_results.md"
    L = ["# Draft simulation results", "",
         f"League: {DEFAULT_LEAGUE['teams']}-team, full PPR, "
         "1QB/2RB/3WR/1TE/1FLEX/1K/1DST, 6 bench, 16 rounds.", "",
         f"Each cell is {N_DRAFTS} simulated drafts x {N_SEASONS} simulated seasons. "
         "Scores are starting-lineup points, Weeks 1-14. `p10` is the tenth-percentile "
         "outcome, which is the number that decides whether a season is salvageable.", "",
         "## Strategy comparison", "",
         "| Strategy | Slot | Mean | P10 | P90 | Playoff wks |",
         "|---|---:|---:|---:|---:|---:|"]
    for r in sorted(results, key=lambda x: (x["slot"], -x["mean_reg"])):
        L.append(f"| {r['strategy']} | {r['slot']} | {r['mean_reg']:.0f} | "
                 f"{r['p10']:.0f} | {r['p90']:.0f} | {r['mean_playoff']:.0f} |")

    L += ["", "## Mean by strategy across all simulated slots", "",
          "| Strategy | Mean | P10 | Playoff wks |", "|---|---:|---:|---:|"]
    agg = defaultdict(list)
    for r in results:
        agg[r["strategy"]].append(r)
    for strat, rs in sorted(agg.items(), key=lambda kv: -statistics.mean(x["mean_reg"] for x in kv[1])):
        L.append(f"| {strat} | {statistics.mean(x['mean_reg'] for x in rs):.0f} | "
                 f"{statistics.mean(x['p10'] for x in rs):.0f} | "
                 f"{statistics.mean(x['mean_playoff'] for x in rs):.0f} |")

    L += ["", "## Highest-expectation roster found at each draft slot", ""]
    for slot, (mean_reg, mean_post, roster) in sorted(rosters.items()):
        L += [f"### Pick {slot}", "",
              f"Expected starting-lineup points, Weeks 1-14: **{mean_reg:.0f}** "
              f"(playoff weeks {mean_post:.0f})", "",
              "| Rd | Player | Pos | Team | Bye | Proj |", "|---:|---|---|---|---:|---:|"]
        for i, p in enumerate(roster, 1):
            name = p.player if not p.player.startswith("FA ") else "_(waiver tier)_"
            L.append(f"| {i} | {name} | {p.pos} | {p.team} | {p.bye} | {p.proj:.0f} |")
        L.append("")

    L += ["## Most frequent model pick by round", "",
          "| Rd | Most common | 2nd | 3rd |", "|---:|---|---|---|"]
    for rnd in sorted(freq):
        top = freq[rnd].most_common(3)
        cells = []
        for key, n in top:
            nm, pos, tm = key.split("|")
            cells.append(f"{nm} ({pos}, {tm}) {n}x")
        while len(cells) < 3:
            cells.append("—")
        L.append(f"| {rnd} | {cells[0]} | {cells[1]} | {cells[2]} |")

    path.write_text("\n".join(L), encoding="utf-8")
    return path


def main():
    players, levels = build()
    print("Replacement levels:", {k: round(v, 1) for k, v in sorted(levels.items())})
    print("\nWriting cheat sheet and tiers...", flush=True)
    print(" ", write_cheatsheet(players))
    print(" ", write_tiers(players))

    print("\nStrategy study...", flush=True)
    results = strategy_study(players)

    print("\nRoster search...", flush=True)
    rosters = best_rosters(players)

    print("\nRound frequency...", flush=True)
    freq = round_frequency(players)

    print("\n ", write_sim_results(results, rosters, freq))
    print("\nDone.")


if __name__ == "__main__":
    main()
