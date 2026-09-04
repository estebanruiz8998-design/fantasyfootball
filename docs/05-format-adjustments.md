# Format adjustments

Everything else in this repository assumes the most common setup: **12 teams,
full PPR, 1QB / 2RB / 3WR / 1TE / 1FLEX / 1K / 1DST, 6 bench, snake draft.**

If your league differs, re-run the model with the settings changed rather than
adjusting by feel:

```python
from model import build
league = dict(teams=10, qb=1, rb=2, wr=3, te=1, flex=2, k=1, dst=1, bench=6, budget=200)
players, levels = build(league)
```

Replacement levels move, and the whole board moves with them.

## Half PPR

Receptions are worth half as much, so the pass-catching backs and high-volume
slot receivers lose the most.

- **Down:** Wan'Dale Robinson, Josh Downs, De'Von Achane, RJ Harvey, Amon-Ra
  St. Brown (relatively — he is still elite).
- **Up:** Derrick Henry, Mike Evans, Jameson Williams, DK Metcalf — the
  touchdown- and yardage-dependent profiles.
- The elite tight end edge shrinks slightly, but Bowers and McBride still clear
  the field.

## Standard (no PPR)

Amplify every half-PPR adjustment. Derrick Henry moves up several spots; Wan'Dale
Robinson becomes nearly undraftable. Running backs regain some of the early-round
priority the model strips from them in PPR.

## Superflex / 2QB

**This changes everything.** A second quarterback slot roughly doubles quarterback
demand, so replacement level collapses and quarterback VOR explodes.

- Josh Allen, Lamar Jackson, Drake Maye and Jayden Daniels become genuine
  first-round picks.
- Take **two quarterbacks in the first four rounds.** Not one.
- The late-QB values the model loves in 1QB — Herbert, Dart, Burrow, Murray,
  Shough — move up two to four rounds and are still good picks, just not steals.
- **Fernando Mendoza** (No. 1 overall pick, Kubiak offense) is a real superflex
  asset rather than a dynasty-only name.
- Run the model with `qb=2` to see it properly.

## TE premium (1.5 points per tight-end reception)

Brock Bowers and Trey McBride move into the first round outright, and the gap to
TE3 widens rather than narrows. Colston Loveland and Tyler Warren become
second-round picks. The "wait on tight end" plan stops working — in TE premium,
the position is where the scarcity actually is.

## Best ball

No waivers and no lineup decisions, so the whole calculus changes:

- **Ceiling beats floor.** The `ceiling` column in the data file matters more
  than `risk`. Draft Brian Thomas Jr., Luther Burden, De'Zhaun Stribling,
  Zachariah Branch and Tank Dell aggressively.
- **Injury-discounted players are worth more**, not less, because you are never
  forced to start them. Jordyn Tyson and George Kittle are better best-ball
  picks than redraft picks.
- **Handcuffs are worth much less** — you cannot react to news, so contingency
  is only valuable if it materialises.
- Draft more quarterbacks and tight ends than you would in redraft; spike weeks
  are collected automatically.

## Auction

The `auction` column in `output/cheatsheet.csv` gives values for a $200,
12-team budget, allocating the surplus above a $1-per-slot floor by VOR.

Two things to keep in mind:

1. **Nominate your fade list early.** Put De'Von Achane, Saquon Barkley and
   Bucky Irving up in the first ten nominations while everyone still has money
   and will overpay.
2. **The model's values are systematically low on late-round running backs** for
   the contingent-value reason in the player notes. Add a few dollars for
   handcuffs behind backs you already own.

## League size

- **10-team:** replacement level rises at every position, so elite players matter
  less and the waiver wire is genuinely useful. Fade the injury risks — you can
  replace them.
- **14-team:** the opposite. Replacement level collapses, depth becomes scarce,
  and handcuffs and high-floor starters gain a lot. Take your tight end earlier
  than the model says, because TE12 in a 14-team league is genuinely unstartable.
