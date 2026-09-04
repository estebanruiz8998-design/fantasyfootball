"""
Builds the published draft-board page from the model outputs.

Reads output/cheatsheet.csv and output/sim_results.md, computes the per-slot
round plans from the model itself, and writes artifact/draft-board.html.

    python3 src/make_artifact.py
"""

from __future__ import annotations

import csv
import json
import random
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from model import build
from draft_sim import run_draft

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
ART = ROOT / "artifact"
ART.mkdir(exist_ok=True)

PLAN_DRAFTS = 120
STRAT_LABEL = {
    "MODEL": "Value over next available",
    "ELITE_TE": "Elite TE",
    "HERO_RB": "Hero RB",
    "BEST_VALUE": "Best available",
    "ROBUST_RB": "Robust RB",
    "ZERO_RB": "Zero RB",
}


def load_cheatsheet() -> list[dict]:
    rows = []
    with open(OUT / "cheatsheet.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append(dict(
                player=r["player"], pos=r["pos"], team=r["team"],
                bye=int(r["bye"]), tier=int(r["tier"]),
                proj=float(r["proj_ppr"]), vor=float(r["vor"]),
                adp=float(r["adp"]), edge=float(r["adp_edge"]),
                vrank=int(r["value_rank"]), ppg=float(r["ppg"]),
                risk=int(r["risk"]), ceiling=int(r["ceiling"]), note=r["note"],
            ))
    return rows


def parse_sim_results() -> tuple[list[dict], dict[int, dict]]:
    """Pull the strategy table and the best roster per slot out of sim_results.md."""
    text = (OUT / "sim_results.md").read_text(encoding="utf-8")

    # Aggregate the per-slot strategy rows into one row per strategy.
    agg: dict[str, list[tuple[float, float, float, float]]] = defaultdict(list)
    for m in re.finditer(
        r"^\|\s*([A-Z_]+)\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|$",
        text, re.M,
    ):
        strat = m.group(1)
        agg[strat].append((float(m.group(3)), float(m.group(4)),
                           float(m.group(5)), float(m.group(6))))
    strategies = []
    for strat, rows in agg.items():
        n = len(rows)
        strategies.append(dict(
            strategy=strat,
            label=STRAT_LABEL.get(strat, strat.replace("_", " ").title()),
            mean=round(sum(r[0] for r in rows) / n, 1),
            p10=round(sum(r[1] for r in rows) / n, 1),
            p90=round(sum(r[2] for r in rows) / n, 1),
            playoff=round(sum(r[3] for r in rows) / n, 1),
        ))
    strategies.sort(key=lambda d: -d["mean"])

    # Best roster per slot.
    rosters: dict[int, dict] = {}
    for block in re.split(r"^### Pick ", text, flags=re.M)[1:]:
        # The final block runs to end of file, so cut it at the next H2.
        block = re.split(r"^## ", block, flags=re.M)[0]
        slot = int(block.split("\n", 1)[0].strip())
        tot = re.search(r"Weeks 1-14: \*\*([\d.]+)\*\*", block)
        players = []
        for m in re.finditer(
            r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*([A-Z]+)\s*\|\s*([A-Z]+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|$",
            block, re.M,
        ):
            name = m.group(2)
            if name.startswith("_") or "waiver" in name.lower():
                name = "Waiver tier"
            players.append(dict(rd=int(m.group(1)), player=name, pos=m.group(3),
                                team=m.group(4), bye=int(m.group(5)), proj=int(m.group(6))))
        if players:
            rosters[slot] = dict(total=int(float(tot.group(1))) if tot else 0,
                                 players=players)
    return strategies, rosters


def split_lineup(players: list[dict]) -> tuple[list[dict], list[dict]]:
    """Assign the optimal starting lineup; everything else is bench."""
    pools = defaultdict(list)
    for p in players:
        pools[p["pos"]].append(p)
    for v in pools.values():
        v.sort(key=lambda p: -p["proj"])

    starters, used = [], defaultdict(int)
    for pos, n in (("QB", 1), ("RB", 2), ("WR", 3), ("TE", 1)):
        for i in range(n):
            if i < len(pools[pos]):
                p = dict(pools[pos][i])
                p["slot"] = pos if n == 1 else f"{pos}{i+1}"
                starters.append(p)
                used[pos] += 1
    # Flex
    best, bestpos = None, None
    for pos in ("RB", "WR", "TE"):
        i = used[pos]
        if i < len(pools[pos]) and (best is None or pools[pos][i]["proj"] > best["proj"]):
            best, bestpos = pools[pos][i], pos
    if best:
        p = dict(best); p["slot"] = "FLEX"
        starters.append(p); used[bestpos] += 1
    for pos in ("K", "DST"):
        if pools[pos]:
            p = dict(pools[pos][0]); p["slot"] = pos
            starters.append(p); used[pos] += 1

    bench = []
    for pos, lst in pools.items():
        for p in lst[used[pos]:]:
            q = dict(p); q["slot"] = ""
            bench.append(q)
    bench.sort(key=lambda p: -p["proj"])
    return starters, bench


def rationale(players: list[dict], slot: int) -> list[dict]:
    """Explain the roster's shape from the roster itself, not from a template."""
    by_rd = {p["rd"]: p for p in players}
    out = []

    anchor = by_rd.get(1)
    if anchor:
        out.append(dict(
            h=f"Round 1 &mdash; {anchor['player']}",
            p=f"The anchor. At pick {slot} the model takes the "
              f"{'scarce back' if anchor['pos'] == 'RB' else 'best receiver'} rather than reaching "
              f"past a tier break." if anchor["pos"] in ("RB", "WR") else
              f"An unusual round-one shape driven by what the board offered at pick {slot}.",
        ))

    te = next((p for p in players if p["pos"] == "TE"), None)
    if te:
        rd = te["rd"]
        if rd <= 3:
            msg = (f"Paid up in round {rd}. Against a tight-end replacement level near 119 points, "
                   f"this is the single biggest weekly positional edge on the board.")
        elif rd >= 9:
            msg = (f"Waited until round {rd}. The capital saved went into receivers in the middle "
                   f"rounds, which is the other coherent tight-end plan.")
        else:
            msg = f"Taken in round {rd}, in the value tier below the top two."
        out.append(dict(h=f"Tight end &mdash; {te['player']}", p=msg))

    qb = next((p for p in players if p["pos"] == "QB"), None)
    if qb:
        out.append(dict(
            h=f"Quarterback &mdash; round {qb['rd']}",
            p=f"{qb['player']} projects close to the elite tier at a fraction of the cost. "
              f"Replacement-level QB is 271 points, so every pick spent here before round eight "
              f"buys the smallest edge on the board.",
        ))

    rbs = [p for p in players if p["pos"] == "RB"]
    pocket = [p for p in rbs if 4 <= p["rd"] <= 8]
    if pocket:
        out.append(dict(
            h="The running back pocket",
            p="Rounds five to eight: " + ", ".join(p["player"] for p in pocket[:3]) +
              ". These backs sit at or below replacement cost while the ones drafted in rounds two "
              "to four sit well above it.",
        ))

    byes = Counter(p["bye"] for p in players)
    worst, n = byes.most_common(1)[0]
    if n >= 4:
        out.append(dict(
            h=f"Watch week {worst}",
            p=f"{n} players on this roster share the week {worst} bye. Plan the replacement two weeks "
              f"early, before everyone else is bidding on the same names.",
        ))
    return out


def build_plans(players_model, slots) -> dict[int, list[list[str]]]:
    """Most frequent model picks per round, per slot — the plan is what it actually does."""
    plans: dict[int, list[list[str]]] = {}
    for slot in slots:
        rng = random.Random(31337 + slot)
        freq: dict[int, Counter] = defaultdict(Counter)
        for _ in range(PLAN_DRAFTS):
            roster = run_draft(players_model, slot, "MODEL", rng)
            for rnd, p in enumerate(roster, 1):
                if not p.player.startswith("FA "):
                    freq[rnd][(p.player, p.pos)] += 1
        rounds = []
        for rnd in range(1, 17):
            top = freq[rnd].most_common(3)
            if not top:
                rounds.append(["<i>best available</i>"])
                continue
            total = sum(freq[rnd].values()) or 1
            rounds.append([
                f"<b>{nm}</b> <span class='mono' style='font-size:11px;color:var(--ink-3)'>"
                f"{pos} · {round(100 * c / total)}%</span>"
                for (nm, pos), c in top
            ])
        plans[slot] = rounds
        print(f"  plan for slot {slot} done", flush=True)
    return plans


RISK_NOTES = [
    ("George Kittle", "TE", 13.0, "Aggressive return from a January Achilles tear; activated off PUP on 23 August. Elite ceiling, real availability risk."),
    ("Malik Nabers", "WR", 14.5, "Ramping up from a torn ACL. Reported as a reasonable bet for Week 1, but he was non-committal himself."),
    ("Tucker Kraft", "TE", 14.0, "Off PUP in late July after a torn ACL. Likely opens the season on managed snaps."),
    ("Cam Skattebo", "RB", 14.5, "Back from a serious leg and ankle injury; still sharing the top of the depth chart with Tyrone Tracy."),
    ("Josh Jacobs", "RB", 6.0, "On the Commissioner Exempt List. First court date is in November — Week 11. Green Bay traded for Kaleb Johnson as insurance. Do not draft him in redraft."),
    ("Jeremiyah Love", "RB", 15.0, "High-ankle sprain in August. The No. 3 overall pick may be slowed through September, with Conner and Allgeier splitting work."),
    ("Chuba Hubbard", "RB", 14.0, "Week-to-week hamstring, and losing his grip on the job to Jonathon Brooks."),
    ("Michael Penix Jr.", "QB", 11.0, "Knee injury in camp and Atlanta has not named a Week 1 starter. Drake London's value moves with this."),
    ("Jordyn Tyson", "WR", 9.0, "First-round rookie ruled out roughly two months with a hamstring. Stash only, and only in deep leagues."),
    ("Sam LaPorta", "TE", 15.0, "Hip injury clouding Week 1 on top of a target share that never came back."),
    ("Puka Nacua", "WR", 15.5, "Back at practice after groin and psoas problems cost him camp reps. Expected to be ready."),
    ("Isiah Pacheco", "RB", 14.5, "Sprained MCL. His role is to spell Gibbs, not to inherit Montgomery's touches."),
]


def main():
    players_model, _ = build()
    rows = load_cheatsheet()
    strategies, rosters_raw = parse_sim_results()
    slots = sorted(rosters_raw) or [6]
    print(f"Parsed {len(strategies)} strategies, {len(rosters_raw)} slot rosters.")

    print("Building round plans...", flush=True)
    plans = build_plans(players_model, slots)

    rosters = {}
    for slot, r in rosters_raw.items():
        starters, bench = split_lineup(r["players"])
        rosters[slot] = dict(total=r["total"], starters=starters, bench=bench,
                             why=rationale(r["players"], slot))

    skill = {"K", "DST"}
    startery = [r for r in rows if r["pos"] not in skill and r["adp"] < 145
                and not (r["pos"] == "RB" and r["adp"] > 95)]
    buys = sorted(startery, key=lambda r: -r["edge"])[:14]
    fades = sorted(startery, key=lambda r: r["edge"])[:14]

    def slim(lst):
        return [dict(player=r["player"], pos=r["pos"], adp=f"{r['adp']:g}",
                     vrank=r["vrank"], edge=int(r["edge"])) for r in lst]

    board = [dict(player=r["player"], pos=r["pos"], team=r["team"], tier=r["tier"],
                  proj=r["proj"], adp=f"{r['adp']:g}", edge=r["edge"]) for r in rows]

    risk = [dict(player=p, pos=q, games=f"{g:g}", note=n) for p, q, g, n in RISK_NOTES]

    tpl = (Path(__file__).resolve().parent / "artifact_template.html").read_text(encoding="utf-8")
    n_slots = max(len(slots), 1)
    html = (tpl
            .replace("__PLAYERS_JSON__", json.dumps(board))
            .replace("__STRATEGY_JSON__", json.dumps(strategies))
            .replace("__ROSTERS_JSON__", json.dumps(rosters))
            .replace("__PLANS_JSON__", json.dumps(plans))
            .replace("__RISK_JSON__", json.dumps(risk))
            .replace("__BUYS_JSON__", json.dumps(slim(buys)))
            .replace("__FADES_JSON__", json.dumps(slim(fades)))
            .replace("__NPLAYERS__", str(len(rows)))
            # strategy study + roster search + round frequency + these round plans
            .replace("__NDRAFTS__", f"{len(strategies) * n_slots * 60 + n_slots * (180 + 180 + PLAN_DRAFTS):,}")
            .replace("__NSEASONS__", f"{len(strategies) * n_slots * 600 + n_slots * 180 * 30:,}")
            .replace("__ROSTERSEARCH__", "180")
            .replace("__GENERATED__", date.today().strftime("%-d %B %Y")))

    dest = ART / "draft-board.html"
    dest.write_text(html, encoding="utf-8")
    print("Wrote", dest, f"({len(html):,} bytes)")


if __name__ == "__main__":
    main()
