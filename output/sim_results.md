# Draft simulation results

League: 12-team, full PPR, 1QB/2RB/3WR/1TE/1FLEX/1K/1DST, 6 bench, 16 rounds.

Each cell is 25 simulated drafts x 6 simulated seasons. Scores are starting-lineup points, Weeks 1-14. `p10` is the tenth-percentile outcome, which is the number that decides whether a season is salvageable.

## Strategy comparison

| Strategy | Slot | Mean | P10 | P90 | Playoff wks |
|---|---:|---:|---:|---:|---:|
| HERO_RB | 1 | 1858 | 1670 | 2088 | 420 |
| MODEL | 1 | 1854 | 1691 | 2022 | 417 |
| BEST_VALUE | 1 | 1847 | 1648 | 2066 | 419 |
| ELITE_TE | 1 | 1833 | 1655 | 2018 | 418 |
| ROBUST_RB | 1 | 1807 | 1616 | 2026 | 412 |
| ZERO_RB | 1 | 1777 | 1570 | 2021 | 402 |
| HERO_RB | 6 | 1819 | 1629 | 2024 | 411 |
| MODEL | 6 | 1802 | 1593 | 2027 | 410 |
| ELITE_TE | 6 | 1796 | 1625 | 1979 | 405 |
| BEST_VALUE | 6 | 1796 | 1594 | 1994 | 404 |
| ZERO_RB | 6 | 1775 | 1609 | 1954 | 403 |
| ROBUST_RB | 6 | 1770 | 1587 | 1965 | 402 |
| MODEL | 12 | 1770 | 1607 | 1937 | 398 |
| ELITE_TE | 12 | 1769 | 1578 | 1968 | 402 |
| HERO_RB | 12 | 1765 | 1574 | 1962 | 403 |
| ZERO_RB | 12 | 1746 | 1538 | 1932 | 391 |
| ROBUST_RB | 12 | 1731 | 1559 | 1925 | 392 |
| BEST_VALUE | 12 | 1728 | 1571 | 1885 | 395 |

## Mean by strategy across all simulated slots

| Strategy | Mean | P10 | Playoff wks |
|---|---:|---:|---:|
| HERO_RB | 1814 | 1624 | 411 |
| MODEL | 1809 | 1630 | 408 |
| ELITE_TE | 1799 | 1619 | 408 |
| BEST_VALUE | 1791 | 1604 | 406 |
| ROBUST_RB | 1769 | 1587 | 402 |
| ZERO_RB | 1766 | 1572 | 398 |

## Highest-expectation roster found at each draft slot

### Pick 1

Expected starting-lineup points, Weeks 1-14: **1989** (playoff weeks 447)

| Rd | Player | Pos | Team | Bye | Proj |
|---:|---|---|---|---:|---:|
| 1 | Jahmyr Gibbs | RB | DET | 6 | 330 |
| 2 | Kenneth Walker III | RB | KC | 5 | 206 |
| 3 | Nico Collins | WR | HOU | 8 | 252 |
| 4 | Colston Loveland | TE | CHI | 10 | 213 |
| 5 | Tyler Warren | TE | IND | 13 | 186 |
| 6 | D'Andre Swift | RB | CHI | 10 | 155 |
| 7 | DK Metcalf | WR | PIT | 9 | 168 |
| 8 | Stefon Diggs | WR | WAS | 7 | 165 |
| 9 | Jaxson Dart | QB | NYG | 8 | 299 |
| 10 | Jordan James | RB | SF | 8 | 102 |
| 11 | Patrick Mahomes II | QB | KC | 5 | 271 |
| 12 | Isiah Pacheco | RB | DET | 6 | 69 |
| 13 | Zachariah Branch | WR | ATL | 11 | 117 |
| 14 | _(waiver tier)_ | WR | FA | 5 | 72 |
| 15 | Texans | DST | HOU | 8 | 140 |
| 16 | _(waiver tier)_ | K | FA | 5 | 112 |

### Pick 6

Expected starting-lineup points, Weeks 1-14: **1967** (playoff weeks 437)

| Rd | Player | Pos | Team | Bye | Proj |
|---:|---|---|---|---:|---:|
| 1 | Bijan Robinson | RB | ATL | 11 | 296 |
| 2 | CeeDee Lamb | WR | DAL | 14 | 247 |
| 3 | George Pickens | WR | DAL | 14 | 232 |
| 4 | Tetairoa McMillan | WR | CAR | 5 | 218 |
| 5 | Tyler Warren | TE | IND | 13 | 186 |
| 6 | Quinshon Judkins | RB | CLE | 11 | 146 |
| 7 | Dallas Goedert | TE | PHI | 10 | 145 |
| 8 | Jaxson Dart | QB | NYG | 8 | 299 |
| 9 | Jordan Addison | WR | MIN | 6 | 155 |
| 10 | Bo Nix | QB | DEN | 10 | 282 |
| 11 | De'Zhaun Stribling | WR | SF | 8 | 128 |
| 12 | Mike Washington Jr. | RB | LV | 13 | 90 |
| 13 | _(waiver tier)_ | RB | FA | 5 | 70 |
| 14 | _(waiver tier)_ | RB | FA | 7 | 66 |
| 15 | Texans | DST | HOU | 8 | 140 |
| 16 | Tyler Bass | K | BUF | 7 | 123 |

### Pick 12

Expected starting-lineup points, Weeks 1-14: **1902** (playoff weeks 435)

| Rd | Player | Pos | Team | Bye | Proj |
|---:|---|---|---|---:|---:|
| 1 | Jaxon Smith-Njigba | WR | SEA | 11 | 276 |
| 2 | Amon-Ra St. Brown | WR | DET | 6 | 270 |
| 3 | Kenneth Walker III | RB | KC | 5 | 206 |
| 4 | Colston Loveland | TE | CHI | 10 | 213 |
| 5 | Jaylen Waddle | WR | DEN | 10 | 207 |
| 6 | David Montgomery | RB | HOU | 8 | 147 |
| 7 | Joe Burrow | QB | CIN | 6 | 310 |
| 8 | Bhayshul Tuten | RB | JAX | 7 | 133 |
| 9 | Woody Marks | RB | HOU | 8 | 105 |
| 10 | Tre' Harris | WR | LAC | 7 | 147 |
| 11 | Brock Purdy | QB | SF | 8 | 262 |
| 12 | Michael Wilson | WR | ARI | 14 | 131 |
| 13 | Terrance Ferguson | TE | LAR | 11 | 106 |
| 14 | _(waiver tier)_ | RB | FA | 7 | 66 |
| 15 | Rams | DST | LAR | 11 | 129 |
| 16 | Harrison Butker | K | KC | 5 | 126 |

## Most frequent model pick by round

| Rd | Most common | 2nd | 3rd |
|---:|---|---|---|
| 1 | Jahmyr Gibbs (RB, DET) 70x | Brock Bowers (TE, LV) 24x | Jonathan Taylor (RB, IND) 18x |
| 2 | Brock Bowers (TE, LV) 24x | Chase Brown (RB, CIN) 22x | Nico Collins (WR, HOU) 18x |
| 3 | Rashee Rice (WR, KC) 30x | George Pickens (WR, DAL) 24x | Nico Collins (WR, HOU) 23x |
| 4 | Colston Loveland (TE, CHI) 95x | Tyler Warren (TE, IND) 17x | Tetairoa McMillan (WR, CAR) 15x |
| 5 | Kyle Pitts Sr. (TE, ATL) 43x | Tyler Warren (TE, IND) 25x | Zay Flowers (WR, BAL) 19x |
| 6 | D'Andre Swift (RB, CHI) 25x | RJ Harvey (RB, DEN) 21x | Rome Odunze (WR, CHI) 18x |
| 7 | Stefon Diggs (WR, WAS) 38x | Luther Burden III (WR, CHI) 25x | Bhayshul Tuten (RB, JAX) 23x |
| 8 | Justin Herbert (QB, LAC) 55x | Jaxson Dart (QB, NYG) 22x | Stefon Diggs (WR, WAS) 12x |
| 9 | Jaxson Dart (QB, NYG) 23x | Blake Corum (RB, LAR) 15x | Kyle Monangai (RB, CHI) 14x |
| 10 | Bo Nix (QB, DEN) 24x | Tank Bigsby (RB, PHI) 17x | Jaxson Dart (QB, NYG) 16x |
| 11 | Kyler Murray (QB, MIN) 34x | Bo Nix (QB, DEN) 20x | De'Zhaun Stribling (WR, SF) 15x |
| 12 | Zachariah Branch (WR, ATL) 28x | Makai Lemon (WR, PHI) 27x | Michael Wilson (WR, ARI) 14x |
| 13 | Keaton Mitchell (RB, LAC) 17x | Chris Brooks (RB, GB) 17x | Charlie Kolar (TE, BAL) 10x |
| 14 | Chris Brooks (RB, GB) 2x | Sean Tucker (RB, TB) 2x | Keaton Mitchell (RB, LAC) 1x |
| 15 | Broncos (DST, DEN) 31x | Texans (DST, HOU) 30x | Rams (DST, LAR) 28x |
| 16 | Chris Boswell (K, PIT) 14x | Harrison Butker (K, KC) 14x | Jake Bates (K, DET) 12x |