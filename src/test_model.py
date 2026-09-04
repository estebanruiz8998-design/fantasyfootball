"""
Sanity tests for the projection and draft model.

    python3 src/test_model.py

These are the checks that would have caught the three bugs described in
docs/01-methodology.md, so they exist mostly to stop those regressing.
"""

from __future__ import annotations

import random
import sys

from model import ANCHORS, DEFAULT_LEAGUE, build, _interp_log_rank
import draft_sim as ds

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}  {detail}")
        FAILURES.append(name)


def main() -> int:
    players, levels = build()
    print("Projection curves")
    for pos, anchors in ANCHORS.items():
        vals = [_interp_log_rank(anchors, r) for r in range(1, 60)]
        check(f"{pos} curve is monotonically decreasing",
              all(a >= b for a, b in zip(vals, vals[1:])))
        for rank, pts in anchors:
            got = _interp_log_rank(anchors, rank)
            check(f"{pos} curve hits its anchor at rank {rank:g}",
                  abs(got - pts) < 0.5, f"got {got:.1f}, expected {pts}")

    print("\nProjections and value")
    check("every player has a positive projection",
          all(p.proj > 0 for p in players))
    check("QB replacement is the highest of any position",
          levels["QB"] == max(levels.values()), f"{levels}")
    check("RB and WR replacement levels are within 25 points of each other",
          abs(levels["RB"] - levels["WR"]) < 25, f"{levels}")
    check("Gibbs is the top running back by projection",
          max((p for p in players if p.pos == "RB"), key=lambda p: p.proj).player
          == "Jahmyr Gibbs")
    check("an exempt-list player is projected far below his positional rank",
          next(p for p in players if p.player == "Josh Jacobs").proj < 130)

    print("\nTiers")
    for pos in ("RB", "WR", "TE", "QB"):
        lst = sorted((p for p in players if p.pos == pos), key=lambda p: -p.proj)
        check(f"{pos} tiers never decrease down the board",
              all(a.tier <= b.tier for a, b in zip(lst, lst[1:])))
        sizes: dict[int, int] = {}
        for p in lst:
            sizes[p.tier] = sizes.get(p.tier, 0) + 1
        check(f"{pos} has no tier larger than 15 players",
              max(sizes.values()) <= 15, f"sizes={sizes}")

    print("\nLineup value")
    rbs = sorted((p for p in players if p.pos == "RB"), key=lambda p: -p.proj)
    wrs = sorted((p for p in players if p.pos == "WR"), key=lambda p: -p.proj)
    three_wr = ds.lineup_value(wrs[:3])
    nine_wr = ds.lineup_value(wrs[:9])
    check("a 9-receiver roster is worth less than 3x a 3-receiver roster",
          nine_wr < 3 * three_wr, f"{nine_wr:.0f} vs {3*three_wr:.0f}")
    check("the 9th receiver adds less than the 3rd",
          (ds.lineup_value(wrs[:9]) - ds.lineup_value(wrs[:8]))
          < (ds.lineup_value(wrs[:3]) - ds.lineup_value(wrs[:2])))
    check("adding a player never lowers roster value",
          all(ds.lineup_value(rbs[:i + 1]) >= ds.lineup_value(rbs[:i]) for i in range(1, 8)))

    print("\nDrafts")
    rng = random.Random(4)
    for slot in (1, 6, 12):
        roster = ds.run_draft(players, slot, "MODEL", rng)
        check(f"slot {slot} draft fills all {ds.ROUNDS} rounds",
              len(roster) == ds.ROUNDS, f"got {len(roster)}")
        counts = {pos: sum(1 for p in roster if p.pos == pos)
                  for pos in ("QB", "RB", "WR", "TE", "K", "DST")}
        for pos, lo in ds.MIN_AT_POS.items():
            check(f"slot {slot} roster meets the {pos} minimum of {lo}",
                  counts[pos] >= lo, f"got {counts[pos]}")
        qb_round = next((i for i, p in enumerate(roster, 1) if p.pos == "QB"), 99)
        # Round 5 is legitimate when an elite quarterback falls to his ADP at a
        # turn; spending a top-four-round pick on one never is.
        check(f"slot {slot} does not spend a top-4 pick on a quarterback",
              qb_round >= 5, f"took one in round {qb_round}")
        check(f"slot {slot} does not roster three tight ends",
              counts["TE"] <= 2, f"got {counts['TE']}")

    print("\nSeason simulation")
    rng = random.Random(9)
    roster = ds.run_draft(players, 6, "MODEL", rng)
    regs = [ds.simulate_season(roster, rng)[0] for _ in range(60)]
    check("season scores are in a plausible range",
          1200 < sum(regs) / len(regs) < 2600, f"mean {sum(regs)/len(regs):.0f}")
    check("season scores vary between simulations", len(set(regs)) > 50)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed: {', '.join(FAILURES)}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
