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
    # Property checks over many drafts per slot. A single draft is one draw from
    # a stochastic process, so asserting against one is a flaky test, not a check.
    N = 25
    for slot in (1, 6, 12):
        rosters = [ds.run_draft(players, slot, "MODEL", random.Random(1000 * slot + i))
                   for i in range(N)]
        check(f"slot {slot}: every draft fills all {ds.ROUNDS} rounds",
              all(len(r) == ds.ROUNDS for r in rosters),
              f"lengths {sorted({len(r) for r in rosters})}")

        for pos, lo in ds.MIN_AT_POS.items():
            worst = min(sum(1 for p in r if p.pos == pos) for r in rosters)
            check(f"slot {slot}: every roster meets the {pos} minimum of {lo}",
                  worst >= lo, f"worst was {worst}")

        qb_rounds = [next((i for i, p in enumerate(r, 1) if p.pos == "QB"), 99)
                     for r in rosters]
        early = sum(1 for q in qb_rounds if q < 5)
        # An early quarterback is defensible in the tail: when the board in front
        # of you is receiver-depleted and an elite arm has fallen well past his
        # ADP to a turn, the model takes him. What must not happen is that being
        # the normal behaviour, so this bounds the rate rather than forbidding it.
        check(f"slot {slot}: early quarterback is a tail case, not the plan",
              early <= 0.2 * N, f"{early}/{N} drafts, rounds {sorted(set(qb_rounds))}")
        median_qb = sorted(qb_rounds)[N // 2]
        check(f"slot {slot}: typical quarterback round is 7 or later",
              median_qb >= 7, f"median round {median_qb}")

        most_te = max(sum(1 for p in r if p.pos == "TE") for r in rosters)
        check(f"slot {slot}: never rosters three tight ends",
              most_te <= 2, f"max was {most_te}")

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
