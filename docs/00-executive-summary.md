# The 2026 draft, in one page

**League assumed:** 12-team, full PPR, 1QB / 2RB / 3WR / 1TE / 1FLEX / 1K / 1DST,
6 bench, 16 rounds, snake. Research current to 4 September 2026; the season opens
9 September. Other formats are covered in
[`05-format-adjustments.md`](05-format-adjustments.md).

## The three findings

**1. Wait on quarterback until round eight.** Replacement-level QB in a 1QB
league projects for 271 PPR points. That is the highest replacement level on the
board by a wide margin, which means the elite tier's advantage is both small and
expensive. Justin Herbert (ADP 92), Jaxson Dart (100), Joe Burrow (60) and Kyler
Murray (140) all rank 25 or more picks ahead of where they are drafted. Dart was
QB3 in fantasy points per dropback in 2025, behind only Josh Allen and Drake
Maye.

**2. Receivers are underpriced relative to running backs.** Among starters —
excluding kickers, defences and the late-round backs whose value is contingent on
an injury — fourteen of the sixteen largest gaps between ADP and model value in
the wrong direction are running backs. The backs going late in round one and through round two — Achane,
Barkley, Irving, Judkins — consistently score below their draft cost in
simulation. Meanwhile Nico Collins, George Pickens, Emeka Egbuka, Zay Flowers and
Ladd McConkey all sit 8–13 picks below their value.

**3. Rigid strategies lose to flexible ones.** This was the most useful thing the
simulator produced, and it is the opposite of how most draft guides are written.

## What the simulator actually found

Every strategy drafted against eleven ADP-driven opponents at **all twelve draft
slots**, then played out with injuries, byes and optimal weekly lineups.

| Strategy | Mean pts (Wk 1–14) | P10 | Playoff wks |
|---|---:|---:|---:|
| **Value over next available** | **1,817** | **1,632** | **411** |
| Elite TE | 1,802 | 1,621 | 408 |
| Hero RB | 1,799 | 1,608 | 407 |
| Best available (raw VOR) | 1,787 | 1,601 | 402 |
| Robust RB | 1,770 | 1,586 | 400 |
| Zero RB | 1,764 | 1,580 | 399 |

**Read this as an ordering, not a measurement.** The 15-point margin between the
top approach and Elite TE is inside the noise band at these sample sizes, so the
two are not meaningfully separated. Two things are meaningful:

- The value-driven approach was the best strategy at **10 of the 12 draft slots**.
  Elite TE won at picks 10 and 12, where the top tight ends fall furthest.
- It beat Robust RB and Zero RB — the two rigid scripts — at **all twelve slots
  without exception**, by about 50 points, or four points a week. That is roughly
  one won matchup a season.

The winning approach is not a positional plan at all. At every pick it asks:
*who gains me the most over the best player at his position I could still get at
my next turn?* That question is what pushes quarterback to round nine (because
the QB you can get eight rounds later is nearly as good) and receivers to the
front (because the receiver you pass on is not replaceable).

## The shape of the team to build

The model's highest-expectation rosters vary by slot, but they share a structure:

| Rounds | What to take |
|---|---|
| 1–2 | An anchor: an elite back at picks 1–2, otherwise the best receiver. Take **Bowers or McBride** in round 2 if you pick 5–11 — they reach you there. |
| 3–4 | Receivers. Nico Collins, Pickens, Egbuka, McMillan, Flowers, McConkey. |
| 5–8 | **The running back pocket.** D'Andre Swift (+23 VOR), Tony Pollard (+20), David Montgomery (+15) still clear replacement level at a fraction of a round-2 back's cost. This is where your RB2 and flex come from. |
| 8–9 | **One quarterback.** Herbert or Dart. Earlier only if an elite arm slides well past his ADP to a turn *and* the receiver tier has broken — the model's median QB round is 7+, but it does take that exception. |
| 10–12 | The tight end you skipped (Ferguson, Okonkwo), then handcuff your own backs. |
| 13–14 | Ceiling swings: Tre' Harris, Stribling, Michael Wilson, Worthy. |
| 15–16 | Kicker, then defence. Chargers DST streams Weeks 1–2 (ARI, then LV). |

Per-slot rosters and pick-by-pick plans are in
[`02-draft-plans-by-slot.md`](02-draft-plans-by-slot.md) and
[`output/sim_results.md`](../output/sim_results.md).

**A caveat on the "best roster" tables.** Those are the maximum of a noisy
estimate over 180 simulated drafts, so the point totals are optimistic by
construction — the winner's curse. Read them for **shape**, not for the number.
The strategy table above is the unbiased comparison.

## The five picks that matter most

1. **Jahmyr Gibbs at 1.01.** David Montgomery was traded to Houston. In the
   second half of 2025 Gibbs was already at 14.4 carries and 5.6 receptions per
   game on ~75% of snaps. He is a tier of one.
2. **Brock Bowers or Trey McBride in round 2**, if you pick 5–11. Roughly 250
   projected points against a tight-end replacement level near 119 — a bigger
   weekly edge than any back available at that pick.
3. **Do not take De'Von Achane at ADP 10.** Mike McDaniel is gone, Malik Willis
   is the quarterback, and the new coordinator is expected to run more. He is the
   loudest fade on the board and he will look like value.
4. **Justin Herbert or Jaxson Dart in round 8–9.** Herbert now has Mike McDaniel
   calling plays (confirmed: hired to replace Greg Roman) and Keenan Allen has
   left for Indianapolis.
5. **Handcuff your own backs in rounds 11–13.** Jordan James behind McCaffrey,
   Tank Bigsby behind Barkley (Bigsby was traded to Philadelphia), Blake Corum
   behind Kyren Williams. The static cheat sheet undervalues these badly, because
   a season-long point projection cannot express contingent value. The simulator,
   which models injuries, does not make that mistake.

## Two things to check before you draft

**Josh Jacobs is on the Commissioner Exempt List** and his first court date is in
November. Do not draft him in redraft. Green Bay traded for Kaleb Johnson from
Pittsburgh on 30 August specifically as insurance, which tells you what the team
expects.

**Week 11 has six teams on bye** — Falcons, Browns, Packers, Rams, Patriots,
Seahawks. If you finish with Nacua, London, Pitts, Kraft and Smith-Njigba, you
have built a bye-week disaster. Check it before your last picks.

## What this cannot do

Projections here are **reconstructed, not scraped** — direct page fetches were
blocked in the build environment, so the curves are anchored to published figures
and individual players inherit their positional rank from consensus. ADP is
estimated for most players; check your own platform, because ADP varies
enormously between Sleeper, ESPN and NFFC. And verify the injury board — Nabers,
Kittle, Kraft, Skattebo and the Atlanta quarterback job all move week to week.

Full accounting, including the four bugs whose corrections changed these
conclusions, is in [`01-methodology.md`](01-methodology.md).
