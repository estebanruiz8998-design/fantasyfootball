# 2026 Fantasy Football — Draft Model

A projection, valuation and draft-simulation pipeline for the 2026 NFL season,
built to answer one question: **what is the best team you can actually draft,
from your pick, in your league?**

Research current to **4 September 2026**. The season opens 9 September.

---

## Start here

| If you want | Read |
|---|---|
| The recommended team and the short version | [`docs/00-executive-summary.md`](docs/00-executive-summary.md) |
| Your round-by-round plan from your pick | [`docs/02-draft-plans-by-slot.md`](docs/02-draft-plans-by-slot.md) |
| Who to target, who to fade, and why | [`docs/03-player-notes.md`](docs/03-player-notes.md) |
| How the numbers were produced | [`docs/01-methodology.md`](docs/01-methodology.md) |
| What to do after the draft | [`docs/04-in-season-management.md`](docs/04-in-season-management.md) |
| Half PPR, superflex, TE premium, best ball, auction | [`docs/05-format-adjustments.md`](docs/05-format-adjustments.md) |
| A sortable board to draft from | [`output/cheatsheet.csv`](output/cheatsheet.csv) |
| Tier breaks by position | [`output/tiers.md`](output/tiers.md) |
| Full simulation results | [`output/sim_results.md`](output/sim_results.md) |

## Running it

```bash
pip install numpy pandas          # only needed for ad-hoc analysis
python3 src/model.py              # projections, VOR, tiers, auction values
python3 src/draft_sim.py          # strategy comparison at three draft slots
python3 src/build.py --quick      # full pipeline, fast pass (~4 min)
python3 src/build.py              # full pipeline, all 12 slots (~40 min)
```

Everything regenerates from `data/players_2026.csv`. Disagree with a projection?
Change one number and re-run — the recommendations move with it.

## What is in the box

```
data/
  players_2026.csv      177 players: consensus rank, ADP, expected games,
                        per-game adjustment, risk, ceiling, and a note each
  sources.md            every source used, linked
src/
  model.py              scoring curves -> projections -> VOR -> tiers -> auction $
  draft_sim.py          opponent model, season simulation, strategy definitions
  build.py              orchestrates everything, writes output/
docs/                   the written analysis
output/                 generated: cheat sheet, tiers, simulation results
```

## The model in one paragraph

Positional scoring curves are anchored to published 2026 projections and
interpolated in log-rank space, then scaled by expected games played and a
research-driven per-game adjustment. Value over replacement uses actual starter
demand with flex slots allocated to whichever position wins them. Tiers are cut
at statistically real gaps rather than fixed sizes. Then the whole draft is
simulated — eleven ADP-driven opponents, injuries as contiguous blocks of missed
games, byes, and optimal weekly lineups — so strategies are judged on points that
reach a starting lineup, not on roster talent.

## Three findings

**Wait on quarterback.** Replacement-level QB in a 1QB league projects around
271 points, so the elite tier's edge is small and expensive. Justin Herbert,
Jaxson Dart, Joe Burrow and Kyler Murray all rank 25 or more picks better than
their ADP.

**Receivers are underpriced relative to running backs.** Among starters, 14 of
the 16 largest gaps between ADP and model value in the wrong direction are
running backs — Judkins, Irving, Etienne and Rhamondre Stevenson among them. The market is
still paying 2019 prices for the position.

**Rigid strategies lose to flexible ones.** Scripted plans underperform because
they force picks the board is not offering. Taking the best value over *next
available* at every pick beat Zero RB and Robust RB at all twelve draft slots
without exception, and beat every approach on average — though its 15-point
margin over an Elite TE script is inside the noise band.

## Honest limitations

- Projections are **reconstructed, not scraped** — direct page fetches were
  blocked in this environment, so figures come from search-result summaries.
  Curve shapes are anchored to published numbers; individual players inherit
  their positional rank from consensus.
- **ADP is estimated for most players.** Check your own platform before drafting;
  ADP varies enormously between Sleeper, ESPN and NFFC.
- **News moves faster than this repository.** Verify Nabers, Kittle, Kraft,
  Skattebo and the Atlanta quarterback job before you draft.
- Simulation differences under about 25 points are noise at these sample sizes.
