# Methodology

## What this is

A projection, valuation and draft-simulation pipeline for the 2026 NFL season,
built on research gathered on 4 September 2026 — five days before the Seahawks
host the Patriots to open the season on 9 September.

Everything here is reproducible from two files: `data/players_2026.csv` (the
inputs) and `src/` (the model). If you disagree with a projection, change one
number in the CSV and re-run; the recommendations move with it.

## The four steps

### 1. Projections

Public projection tables were not machine-readable from this environment, so
projections are reconstructed rather than scraped, in three parts:

**Positional scoring curves.** Each position gets a curve anchored to published
2026 projection points and interpolated in log-rank space:

| Position | Anchors used |
|---|---|
| QB | QB1 361 (Josh Allen), QB12 288 |
| RB | RB1 331 (Jahmyr Gibbs), RB12 206, RB24 155 |
| WR | WR10 252 (George Pickens: 82.6 / 1,201 / 8.4), WR1 308 |
| TE | TE1 255, TE10 142 |

The Pickens line is the most useful anchor in the set because it was published
as an explicit stat line, so it can be verified: 82.6 receptions + 120.1 points
of yardage + 50.4 points of touchdowns = 253 PPR, which matches the quoted 252.
The TE1 anchor deliberately regresses Trey McBride's 2025 season (126 / 1,239 /
11 = 316 PPR) because that year was driven by a run of team injuries that is not
a reasonable baseline.

**Availability.** Every player carries an expected games-played figure. This is
where the injury research lands: George Kittle at 13.0 games coming off a
January Achilles, Malik Nabers at 14.5 off a torn ACL, Josh Jacobs at 6.0
because of the Commissioner Exempt List.

**A per-game adjustment.** A multiplier, typically 0.88–1.10, encoding
research-driven disagreement with consensus. De'Von Achane sits at 0.90 (Mike
McDaniel gone, Malik Willis at quarterback, a coordinator expected to run more);
Ladd McConkey sits at 1.06 (McDaniel now calls his plays, Keenan Allen left for
Indianapolis).

Full-season projection = `curve(positional rank) × (games / 17) × adjustment`.

### 2. Value over replacement

Raw points do not tell you what to draft, because a 288-point quarterback is
worth less than a 206-point running back when every other team also has a
288-point quarterback.

Replacement level is computed from actual starter demand, with flex slots
awarded one at a time to whichever of RB/WR/TE wins them. For a 12-team league
with 1QB/2RB/3WR/1TE/1FLEX, that produces:

| Position | Replacement level (PPR) |
|---|---|
| QB | ~257 |
| RB | ~132 |
| WR | ~131 |
| TE | ~109 |
| K | ~118 |
| DST | ~92 |

The quarterback replacement level being so high is the entire argument for
waiting on the position.

### 3. Tiers

A new tier is cut whenever the projection gap between consecutive players at a
position exceeds 0.75 standard deviations of that position's gap distribution.
This finds the genuine cliffs instead of imposing fixed-size buckets, which is
what makes tiers useful on the clock: you take the last player in a tier, not
the first player in the next one.

### 4. Draft simulation

A cheat sheet cannot tell you whether a plan survives eleven other drafters, so
the whole draft is simulated:

- **Opponents** draft from ADP with Gumbel noise that grows as the draft goes
  on, plus soft positional needs. This reproduces position runs, occasional
  reaches, and kickers going last.
- **Seasons** draw a per-player scoring level (variance scaled by the risk and
  ceiling fields) and a *contiguous* block of missed games, because that is how
  injuries actually land. Lineups are then set optimally each week from whoever
  is available, byes included.
- **Scoring** is split into the fantasy regular season (Weeks 1–14) and the
  fantasy playoffs (Weeks 15–17).

## Four bugs worth reporting

The first version of this model produced results I did not believe, and chasing
them down changed the conclusions. Recording them because the corrections are
the actual analytical content:

**The board ran out.** A 12-team, 16-round draft consumes 192 picks; the curated
player pool held 173. Drafts silently truncated at 14 rounds, so every roster
was short two players and thin rosters looked survivable. Fixed by adding an
explicit replacement-level filler pool representing the waiver tier.

**Value over replacement stacked eight receivers.** VOR is a standalone measure:
a sixth receiver has a large VOR and almost no marginal value, because he cannot
get into the lineup. Fixed by scoring candidates on *marginal lineup value* —
what they add to an optimally-set starting lineup, with bench players weighted
by how often they are realistically needed.

**Marginal value drafted Josh Allen first overall.** With an empty roster every
slot is empty, so absolute points dominate and the highest-scoring player in
football wins. The fix is opportunity cost: score each player against the best
player at his own position likely to survive to your *next* pick. If he will
still be there, taking him now buys nothing. This is what pushes quarterback to
round 9 and receivers to the front, and it is the single change that moved the
recommended strategy from worst to best.

**Opportunity cost went degenerate at snake turns.** A test asserting the model
never spends premium capital on a quarterback caught this one. At a turn your two
picks are adjacent — 48 then 49 — so the best player at *every* position still
available "at your next pick" is the same player you would take anyway. Every
VONA collapsed toward zero, and the choice fell to whichever position happened to
have a non-zero gap. At pick 48 that was quarterback, on an 18-point edge that
means nothing. The horizon is now the next pick at least six selections away, so
at a turn the model asks what survives to the pick *after* the pair — which is
the question that actually matters there. Worth roughly 30–45 points a season.

The checks in `src/test_model.py` exist to stop all four regressing. The most
useful one asserts that lineup value has diminishing returns — that the ninth
receiver adds less than the third — which is exactly the property the
receiver-stacking bug violated.

## Honest limitations

- **Projections are reconstructed, not scraped.** The curve shapes are anchored
  to published figures, but individual players inherit their positional rank
  from consensus. A player I have mis-ranked will be mis-projected.
- **ADP is estimated for most players.** Directly sourced values (Saquon Barkley
  13, Kenneth Walker 22.3, Omarion Hampton 25.3, Garrett Wilson 38, Jeremiyah
  Love 21–25) are used where known; the rest are interpolated from consensus
  positional rank. Check your own platform's ADP before drafting, because ADP
  varies enormously between Sleeper, ESPN and NFFC.
- **News moves faster than this file.** Everything is current to 4 September.
  Verify injury statuses before you draft, particularly Nabers, Kittle, Kraft,
  Skattebo and the Falcons quarterback job.
- **Simulation differences of under about 25 points are noise** at these sample
  sizes. Treat the strategy table as ordinal, not precise.
