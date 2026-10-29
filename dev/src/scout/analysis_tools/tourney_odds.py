"""Tournament futures: Monte Carlo of a division's real double-elimination bracket → dated PDF board.

Bracket, dates, official corrections, and seeding rules come from the division's `postseason:`
block in the season YAML. Run from the repo root with the venv active:
    python -m scout.analysis_tools.tourney_odds --division Minors
"""

import argparse
import json
import math
from collections import defaultdict
from datetime import date, timedelta

import numpy as np

from scout.analysis_tools import games as td
from scout.analysis_tools.pitching_usage import pitcher_display
from scout.season_config import SEASON_DIR, SEASON_ID, load_season_yaml

N_SIMS = 20000
RUN_CAP = 5             # run rule for every inning except the last
MAX_INN_PER_GAME = 2
PITCH_CAP = 50
EMERGENCY = {"name": "Emergency arm", "D": 1.40, "ppi": 26.0}
D = date

# Populated from the season YAML by configure().
POST = {}
OFFICIAL_RECORDS = {}
BRACKET = {}
GAME_ORDER = []
IF_NECESSARY = None
WB_FINAL = FINAL = None


def configure(post):
    """Load bracket/seeding settings from a division's postseason config."""
    global POST, OFFICIAL_RECORDS, BRACKET, GAME_ORDER, IF_NECESSARY, WB_FINAL, FINAL
    POST = post
    OFFICIAL_RECORDS = {t: tuple(v) for t, v in (post.get("official_records") or {}).items()}
    BRACKET = {int(g): (v[0], v[1], v[2]) for g, v in post["bracket"].items()}
    GAME_ORDER = list(post["order"])
    nec = post.get("if_necessary")
    IF_NECESSARY = (nec["game"], nec["date"]) if nec else None
    WB_FINAL, FINAL = post["winners_final"], post["final"]


def rest_days(pitches):
    """Little League: 1–20 pitches = 0 days, 21–35 = 1, 36–50 = 2 (over 50 isn't allowed)."""
    return 0 if pitches <= 20 else 1 if pitches <= 35 else 2


def record_outing(avail, key, day, pitches):
    """Update a pitcher's availability after pitching on `day`.

    avail[key] = (first eligible date, last day pitched, consecutive days pitched, pitches that day).
    Rest days follow `rest_days`; pitching 2 days in a row also sits the 3rd day.
    """
    prev = avail.get(key)
    last, streak = (prev[1], prev[2]) if prev else (None, 0)
    if last == day:
        pitches += prev[3]
    else:
        streak = streak + 1 if last == day - timedelta(days=1) else 1
    back = day + timedelta(days=1 + rest_days(pitches))
    if streak >= 2:
        back = max(back, day + timedelta(days=2))
    avail[key] = (back, day, streak, pitches)


def eligible(avail, key, day):
    v = avail.get(key)
    return v is None or v[0] <= day


def quality_pitchers(R, team, n=3, min_ip=3):
    """A team's top `n` arms by opponent-adjusted rating (min `min_ip` innings)."""
    return [p for p in R["staffs"].get(team, []) if p["ip"] >= min_ip][:n]


# ── Ratings ────────────────────────────────────────────────────────────────

def build_ratings(games, apps):
    reg = [g for g in games if not g["playoff"]]
    reg_ids = {g["id"] for g in reg}
    # (game, inning, pitching team) -> {pitcher: BF}
    bf = defaultdict(dict)
    pitches = defaultdict(float)
    for (team, p, gid), a in apps.items():
        if gid not in reg_ids or p == "UNKNOWN":
            continue
        pitches[(team, p)] += a["pitches"]
        for inn, n in a["bf_by_inning"].items():
            bf[(gid, inn, team)][p] = n

    halves = []  # (batting team, pitching team, runs, {pitcher: share}, last_inning)
    for g in reg:
        last = max(h["inning"] for h in g["halves"])
        for h in g["halves"]:
            pt = next(t for t in g["teams"] if t != h["batting"])
            shares = bf.get((g["id"], h["inning"], pt), {})
            tot = sum(shares.values())
            halves.append((h["batting"], pt, h["runs"],
                           {p: n / tot for p, n in shares.items()} if tot else {}, h["inning"] == last))
    mu = sum(h[2] for h in halves) / len(halves)
    teams = sorted({h[0] for h in halves})
    O = {t: 1.0 for t in teams}
    Dp = defaultdict(lambda: 1.0)
    Dt = {t: 1.0 for t in teams}
    for _ in range(30):
        # Offense, adjusted for the pitchers faced.
        num, den = defaultdict(float), defaultdict(float)
        for bt, pt, r, sh, _l in halves:
            d_eff = sum(s * Dp[(pt, p)] for p, s in sh.items()) if sh else Dt[pt]
            num[bt] += r; den[bt] += mu * d_eff
        O = {t: (num[t] + 6 * mu) / (den[t] + 6 * mu) for t in teams}
        # Team defense, then pitchers shrunk toward their team.
        tn, tdn = defaultdict(float), defaultdict(float)
        pn, pdn = defaultdict(float), defaultdict(float)
        for bt, pt, r, sh, _l in halves:
            tn[pt] += r; tdn[pt] += mu * O[bt]
            for p, s in sh.items():
                pn[(pt, p)] += s * r; pdn[(pt, p)] += s * mu * O[bt]
        Dt = {t: (tn[t] + 15 * mu) / (tdn[t] + 15 * mu) for t in teams}
        Dp = defaultdict(lambda: 1.0, {k: (pn[k] + 4 * mu * Dt[k[0]]) / (pdn[k] + 4 * mu) for k in pn})
        # Offense and defense trade off scale; pin both league means to 1.0.
        o_mean = sum(O.values()) / len(O)
        d_mean = sum(Dt.values()) / len(Dt)
        O = {t: v / o_mean for t, v in O.items()}
        Dt = {t: v / d_mean for t, v in Dt.items()}
        Dp = defaultdict(lambda: 1.0, {k: v / d_mean for k, v in Dp.items()})

    inn_share = defaultdict(float)
    for _bt, pt, _r, sh, _l in halves:
        for p, s in sh.items():
            inn_share[(pt, p)] += s
    staffs = {t: [] for t in teams}
    team_ppi = {}
    for t in teams:
        tp = sum(pitches[k] for k in pitches if k[0] == t)
        ti = sum(inn_share[k] for k in inn_share if k[0] == t)
        team_ppi[t] = tp / ti if ti else 25.0
    for (t, p), ip in inn_share.items():
        ppi = (pitches[(t, p)] + 3 * team_ppi[t]) / (ip + 3)
        staffs[t].append({"name": p, "D": Dp[(t, p)], "ppi": ppi, "ip": ip})
    for t in staffs:
        staffs[t].sort(key=lambda x: x["D"])
    return {"mu": mu, "O": O, "Dt": Dt, "staffs": staffs, "halves": halves, "team_ppi": team_ppi}


def fit_run_distribution(halves):
    """Fit a negative-binomial half-inning run model to non-final innings (capped at RUN_CAP)."""
    obs = np.zeros(RUN_CAP + 1)
    for _bt, _pt, r, _s, last in halves:
        if not last:
            obs[min(r, RUN_CAP)] += 1
    obs /= obs.sum()
    best = None
    for r in np.arange(0.3, 4.01, 0.05):
        for m in np.arange(1.0, 6.01, 0.05):
            p = r / (r + m)
            pmf = [math.exp(math.lgamma(k + r) - math.lgamma(r) - math.lgamma(k + 1)
                            + r * math.log(p) + k * math.log(1 - p)) for k in range(RUN_CAP)]
            probs = np.array(pmf + [1 - sum(pmf)])
            err = float(((probs - obs) ** 2).sum())
            if best is None or err < best[0]:
                best = (err, r, m)
    return best[1], best[2], obs


# ── Simulation ─────────────────────────────────────────────────────────────

class Sim:
    def __init__(self, R, nb_r, nb_m, inning_dist, rng, alpha=1.0, scale=1.0):
        self.R, self.nb_r, self.nb_m, self.rng = R, nb_r, nb_m * scale, rng
        self.alpha = alpha
        self.inn_vals, self.inn_p = zip(*sorted(inning_dist.items()))
        self.emergency_uses = 0
        self.emergency_by_team = defaultdict(int)

    def runs(self, off, d, last):
        mean = self.nb_m * (off * d) ** self.alpha
        r = self.rng.negative_binomial(self.nb_r, self.nb_r / (self.nb_r + mean))
        return r if last else min(r, RUN_CAP)

    def pick(self, team, day, avail, used, today):
        for p in self.R["staffs"][team]:
            key = (team, p["name"])
            if key not in used and eligible(avail, key, day) and today.get(key, 0) == 0:
                return p
        self.emergency_uses += 1
        self.emergency_by_team[team] += 1
        return EMERGENCY

    def half(self, bat, pitch_team, st, last, day, avail):
        cur = st["cur"]
        if (cur is None or st["inn"][cur["name"]] >= MAX_INN_PER_GAME
                or st["pc"][cur["name"]] >= PITCH_CAP - 5):
            cur = self.pick(pitch_team, day, avail, st["used"], st["pc"])
            st["cur"] = cur
            st["used"].add((pitch_team, cur["name"]))
        st["inn"][cur["name"]] += 1
        r = self.runs(self.R["O"][bat], cur["D"], last)
        n = max(6.0, self.rng.normal(cur["ppi"], 0.25 * cur["ppi"])) + 2 * max(0, r - 2)
        room = PITCH_CAP - st["pc"][cur["name"]]
        if n > room:
            st["pc"][cur["name"]] += room
            relief = self.pick(pitch_team, day, avail, st["used"], st["pc"])
            st["used"].add((pitch_team, relief["name"]))
            st["inn"][relief["name"]] += 1
            st["pc"][relief["name"]] += n - room
            st["cur"] = relief
        else:
            st["pc"][cur["name"]] += n
        return r

    def game(self, a, b, day, avail):
        sts = {t: {"cur": None, "inn": defaultdict(int), "pc": defaultdict(float), "used": set()}
               for t in (a, b)}
        n_inn = self.rng.choice(self.inn_vals, p=self.inn_p)
        score = {a: 0, b: 0}
        inning = 0
        while True:
            inning += 1
            last = inning >= n_inn
            score[a] += self.half(a, b, sts[b], last, day, avail)
            score[b] += self.half(b, a, sts[a], last, day, avail)
            if inning >= n_inn and score[a] != score[b]:
                break
            if inning >= n_inn + 3:
                score[a if self.rng.random() < 0.5 else b] += 1
                break
        for t in (a, b):
            for name, pc in sts[t]["pc"].items():
                if name != EMERGENCY["name"]:
                    record_outing(avail, (t, name), day, pc)
        return (a, b) if score[a] > score[b] else (b, a)


def run_tournament(sim, fixed, avail0):
    res, avail = {}, dict(avail0)
    losses = defaultdict(int)

    def team(slot):
        return slot if not slot[:1] in "WL" or not slot[1:].isdigit() else res[int(slot[1:])][0 if slot[0] == "W" else 1]

    for gnum in GAME_ORDER:
        day, sa, sb = BRACKET[gnum]
        a, b = team(sa), team(sb)
        res[gnum] = fixed[gnum] if gnum in fixed else sim.game(a, b, day, avail)
        losses[res[gnum][1]] += 1
    w, l = res[FINAL]
    nec = IF_NECESSARY[0] if IF_NECESSARY else None
    if nec and losses[w] == 1:  # losers-bracket team won the final → if-necessary game
        res[nec] = sim.game(w, l, IF_NECESSARY[1], avail)
    champ = res[nec][0] if nec in res else res[FINAL][0]
    return champ, res


def simulate(R, nb, inning_dist, fixed, avail0, alpha, scale, n=N_SIMS, seed=7):
    sim = Sim(R, nb[0], nb[1], inning_dist, np.random.default_rng(seed), alpha, scale)
    champ, final, wb = defaultdict(int), defaultdict(int), defaultdict(int)
    for _ in range(n):
        c, res = run_tournament(sim, fixed, avail0)
        champ[c] += 1
        for t in res[FINAL]:
            final[t] += 1
        wb[res[WB_FINAL][0]] += 1
    return ({t: v / n for t, v in champ.items()}, {t: v / n for t, v in final.items()},
            {t: v / n for t, v in wb.items()}, {t: v / n for t, v in sim.emergency_by_team.items()})


# ── Odds formatting ────────────────────────────────────────────────────────

def american(p):
    if p <= 0:
        return "OFF"
    if p >= 0.5:
        v = -100 * p / (1 - p)
        return f"{int(round(v / 5) * 5)}"
    v = 100 * (1 - p) / p
    step = 5 if v < 300 else 25 if v < 1000 else 50 if v < 2500 else 100 if v < 5000 else 500
    return f"+{int(round(v / step) * step)}"


def book(probs, overround=1.25):
    tot = sum(probs.values())
    return {t: min(0.95, p / tot * overround) for t, p in probs.items()}


def win_prob(sim, a, b, n):
    """P(a beats b) on a fresh-arms day."""
    wins = 0
    for _ in range(n):
        wins += sim.game(a, b, D(2030, 1, 1), {})[0] == a
    return wins / n


def tune(R, nb, inning_dist, games, apps):
    """Pick scoring scale to match runs/game, then alpha (rating dampening) by log-loss."""
    reg = [g for g in games if not g["playoff"]]
    po = [g for g in games if g["playoff"]]
    actual = sum(sum(g["runs"].values()) for g in reg) / len(reg)
    scale = 1.0
    for _ in range(4):
        sim = Sim(R, nb[0], nb[1], inning_dist, np.random.default_rng(1), 1.0, scale)
        tot = 0
        for i in range(3000):
            g = reg[i % len(reg)]
            a, b = g["teams"]
            sts = {t: {"cur": None, "inn": defaultdict(int), "pc": defaultdict(float), "used": set()} for t in (a, b)}
            n_inn = sim.rng.choice(sim.inn_vals, p=sim.inn_p)
            for inn in range(1, n_inn + 1):
                last = inn == n_inn
                tot += sim.half(a, b, sts[b], last, g["date"], {}) + sim.half(b, a, sts[a], last, g["date"], {})
        scale *= actual / (tot / 3000)

    def logloss_with(Rx, alpha, gs, n=400):
        sim = Sim(Rx, nb[0], nb[1], inning_dist, np.random.default_rng(2), alpha, scale)
        cache, ll, m = {}, 0.0, 0
        for g in gs:
            a, b = g["teams"]
            if g["runs"][a] == g["runs"][b]:
                continue
            if (a, b) not in cache:
                cache[(a, b)] = min(0.97, max(0.03, win_prob(sim, a, b, n)))
            p = cache[(a, b)] if g["runs"][a] > g["runs"][b] else 1 - cache[(a, b)]
            ll -= math.log(p)
            m += 1
        return ll / m

    def logloss(alpha, gs):
        return logloss_with(R, alpha, gs)

    grid = [0.3, 0.5, 0.7, 0.85, 1.0]
    folds = [reg[i::5] for i in range(5)]
    cv = defaultdict(float)
    for k, fold in enumerate(folds):
        held = {g["id"] for g in fold}
        Rk = build_ratings([g for g in games if g["id"] not in held], apps)
        for a in grid:
            cv[a] += logloss_with(Rk, a, fold) / len(folds)
    scores = {a: (cv[a], logloss(a, po)) for a in grid}
    alpha = min(grid, key=lambda a: scores[a][0])
    return scale, alpha, scores, actual


def actual_results(games, through):
    """Fixed bracket results for games played on or before `through`, plus who played in each."""
    fixed = {}

    def team(slot):
        if slot[:1] in "WL" and slot[1:].isdigit():
            g = int(slot[1:])
            return fixed[g][0 if slot[0] == "W" else 1] if g in fixed else None
        return slot

    for gnum in GAME_ORDER:
        day, sa, sb = BRACKET[gnum]
        a, b = team(sa), team(sb)
        if day > through or a is None or b is None:
            continue
        g = next((g for g in games if g["date"] == day and set(g["teams"]) == {a, b}), None)
        if g:
            fixed[gnum] = (a, b) if g["runs"][a] > g["runs"][b] else (b, a)
    return fixed


def availability(apps, games, through):
    """Real availability per (team, pitcher) from pitch counts in games on or before `through`."""
    gdate = {g["id"]: g["date"] for g in games}
    daily = defaultdict(float)
    for (team, p, gid), a in apps.items():
        d = gdate.get(gid)
        if d and d <= through and p != "UNKNOWN":
            daily[(team, p, d)] += a["pitches"]
    avail = {}
    for (team, p, d), pc in sorted(daily.items(), key=lambda kv: kv[0][2]):
        record_outing(avail, (team, p), d, pc)
    return avail


def qp_status(R, avail, team, day, name_of):
    """(available count, total, notes on each unavailable quality pitcher) for `team` on `day`."""
    qps = quality_pitchers(R, team)
    notes = []
    for p in qps:
        key = (team, p["name"])
        if eligible(avail, key, day):
            continue
        back, last, streak, pc = avail[key]
        if streak >= 2 and rest_days(pc) == 0:
            why = f"pitched {last - timedelta(days=1):%-m/%-d} & {last:%-m/%-d}"
        else:
            why = f"{pc:.0f} pitches {last:%-m/%-d}"
        notes.append(f"{name_of(team, p['name'])}: {why} → back {back:%-m/%-d}")
    return len(qps) - len(notes), len(qps), notes


def records(games):
    rec, cnt = defaultdict(lambda: [0, 0, 0, 0, 0]), defaultdict(int)
    limit = POST.get("seeding_games") or 10 ** 6
    per_team = POST.get("seeding_games_by_team") or {}
    for g in games:
        if g["playoff"]:
            continue
        a, b = g["teams"]
        for t, o in ((a, b), (b, a)):
            if cnt[t] >= per_team.get(t, limit):
                continue
            cnt[t] += 1
            rs, ra = g["runs"][t], g["runs"][o]
            r = rec[t]
            r[0] += rs > ra; r[1] += rs < ra; r[2] += rs == ra; r[3] += rs; r[4] += ra
    for t, (w, l, ti) in OFFICIAL_RECORDS.items():
        rec[t][:3] = [w, l, ti]
    return rec


def game_line(R, nb, inning_dist, alpha, scale, a, b, day, avail, n=20000):
    sim = Sim(R, nb[0], nb[1], inning_dist, np.random.default_rng(11), alpha, scale)
    wins = sum(sim.game(a, b, day, dict(avail))[0] == a for _ in range(n))
    return wins / n


def moneyline(p, vig=1.045):
    return american(min(0.97, p * vig)), american(min(0.97, (1 - p) * vig))


def team_notes(R):
    teams = list(R["O"])
    o_rank = {t: i + 1 for i, t in enumerate(sorted(teams, key=lambda t: -R["O"][t]))}
    d_rank = {t: i + 1 for i, t in enumerate(sorted(teams, key=lambda t: R["Dt"][t]))}
    quality = {t: sum(1 for p in R["staffs"][t] if p["D"] <= 1.0 and p["ip"] >= 3) for t in teams}
    return o_rank, d_rank, quality


def seed_order(recs, games):
    """Win % (ties = half), then head-to-head, then run differential."""
    def pct(t):
        w, l, ti, *_ = recs[t]
        return (w + ti / 2) / (w + l + ti)

    def h2h(a, b):
        net = 0
        for g in games:
            if not g["playoff"] and set(g["teams"]) == {a, b}:
                net += (g["runs"][a] > g["runs"][b]) - (g["runs"][a] < g["runs"][b])
        return net

    from functools import cmp_to_key

    def cmp(a, b):
        if pct(a) != pct(b):
            return -1 if pct(a) > pct(b) else 1
        if h2h(a, b):
            return -1 if h2h(a, b) > 0 else 1
        da, db = recs[a][3] - recs[a][4], recs[b][3] - recs[b][4]
        return -1 if da > db else 1 if da < db else 0

    return sorted(recs, key=cmp_to_key(cmp))


def next_games(fixed):
    """Unplayed bracket games on the next game date whose two teams are already known."""
    def team(slot):
        if slot[:1] in "WL" and slot[1:].isdigit():
            g = int(slot[1:])
            return fixed[g][0 if slot[0] == "W" else 1] if g in fixed else None
        return slot

    ready = [(g, team(BRACKET[g][1]), team(BRACKET[g][2]), BRACKET[g][0])
             for g in GAME_ORDER if g not in fixed]
    ready = [r for r in ready if r[1] and r[2]]
    if not ready:
        return []
    day = min(r[3] for r in ready)
    return [r for r in ready if r[3] == day]


def build_pdf(path, R, recs, opening, updated, fixed, lines, alpha, scale, nb, games, as_of, division):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                    TableStyle)

    navy, amber = colors.HexColor("#1a2b4a"), colors.HexColor("#f5a623")
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], textColor=navy, fontSize=22)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=navy)
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9, leading=12)
    small = ParagraphStyle("s", parent=body, fontSize=8, leading=10, textColor=colors.grey)
    o_rank, d_rank, quality = team_notes(R)
    seeds = seed_order(recs, games)
    seed_of = {t: i + 1 for i, t in enumerate(seeds)}

    def style(tbl, n_rows):
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), navy), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef1f6")]),
            ("FONTNAME", (3, 1), (3, n_rows), "Helvetica-Bold"),
            ("TEXTCOLOR", (3, 1), (3, n_rows), colors.HexColor("#0a7a32")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c8ced8")),
        ]))
        return tbl

    def board(res, status=None):
        champ, final, wb, emerg = res
        bk = book(champ)
        hdr = ["#", "Team", "Rec (RS-RA)", "Odds", "Title %", "Final %", "Win WB %",
               "Off rk", "Pitch rk", "Quality arms", "Out-of-arms*"]
        if status:
            hdr.insert(2, "Status")
        rows = [hdr]
        for t in sorted(seeds, key=lambda t: -champ.get(t, 0)):
            w, l, ti, rs, ra = recs[t]
            row = [str(seed_of[t]), t, f"{w}-{l}-{ti} ({rs}-{ra})", american(bk.get(t, 0)),
                   f"{champ.get(t, 0):.1%}", f"{final.get(t, 0):.1%}", f"{wb.get(t, 0):.1%}",
                   f"{o_rank[t]}", f"{d_rank[t]}", f"{quality[t]} / {len(R['staffs'][t])}",
                   f"{emerg.get(t, 0):.2f}"]
            if status:
                row.insert(2, status[t])
                if status[t] == "Eliminated":
                    row[4] = "OFF"
            rows.append(row)
        widths = [0.3, 1.6, 1.4, 0.75, 0.65, 0.65, 0.75, 0.55, 0.6, 0.85, 0.85]
        if status:
            widths.insert(2, 1.0)
        return style(Table(rows, colWidths=[w * 72 for w in widths], repeatRows=1), len(rows) - 1)

    losses = defaultdict(int)
    for w, l in fixed.values():
        losses[l] += 1
    status = {t: "Eliminated" if losses[t] >= 2 else "Losers bracket" if losses[t] == 1 else "Winners bracket"
              for t in seeds}

    reg = [g for g in games if not g["playoff"]]
    start = POST["start"]
    end = IF_NECESSARY[1] if IF_NECESSARY else BRACKET[FINAL][0]
    title = f"WCWAA {SEASON_ID.replace('-', ' ').title()} {division} — Tournament Futures"
    n_roll = len(POST.get("rollbacks") or {})
    n_rec = len(OFFICIAL_RECORDS)
    corrections = (f" Official corrections from the season config: {n_roll} weather rollback(s), "
                   f"{n_rec} record override(s)." if n_roll or n_rec else "")
    seeding = (f" Seeds = record over each team's first {POST['seeding_games']} games"
               if POST.get("seeding_games") else " Seeds = regular-season record")
    story = [Paragraph(title, h1),
             Paragraph(f"Double elimination · {len(recs)} teams · {start:%-m/%-d} – {end:%-m/%-d} · "
                       f"{N_SIMS:,} simulated tournaments per board", body),
             Paragraph("<br/>".join(["To rerun after the latest games, open Terminal and run:"]
                                    + [f"<font face='Courier'>{c}</font>" for c in td.rerun_commands(division)]),
                       small),
             Spacer(1, 8),
             Paragraph(f"Opening Line — as of {start:%-m/%-d} (regular season only)", h2), board(opening), Spacer(1, 6),
             Paragraph("Odds include a 25% sportsbook hold (the implied %s add up to ~125%). Title % is the "
                       "model's fair probability. *Out-of-arms = average times per simulated tournament the team "
                       "had no rested, eligible pitcher left and had to use an emergency arm.", small),
             PageBreak(),
             Paragraph(f"Updated Line — as of {as_of:%a %-m/%-d} "
                       f"(after games {', '.join(str(g) for g in sorted(fixed))})", h2),
             board(updated, status), Spacer(1, 10)]
    if lines:
        story.append(Paragraph(f"Next Games — {lines[0][4]:%a %-m/%-d} (moneyline, standard -110-style hold)", h2))
    gl = [["Game", "Matchup", "Moneyline", "Win %", "Win % if fully rested", "Quality arms available"]]
    outs = []
    for gnum, a, b, p, _day, p_full, qa, qb in lines:
        ma, mb = moneyline(p)
        gl.append([f"G{gnum}", f"{a}  vs  {b}", f"{ma}  /  {mb}", f"{p:.0%} / {1 - p:.0%}",
                   f"{p_full:.0%} / {1 - p_full:.0%}", f"{qa[0]} of {qa[1]}  /  {qb[0]} of {qb[1]}"])
        outs += [f"G{gnum} {t}: {n}" for t, q in ((a, qa), (b, qb)) for n in q[2]]
    story += [style(Table(gl, colWidths=[w * 72 for w in (0.5, 3.3, 1.4, 1.0, 1.5, 1.6)]), 0), Spacer(1, 6)]
    if lines:
        story.append(Paragraph("<b>Unavailable quality arms:</b> " + ("; ".join(outs) if outs else "none — every "
                               "team has its top 3 rested."), body))
    story += [Spacer(1, 4),
              Paragraph(f"Game lines use each staff's real rest status from pitch counts through "
                        f"{as_of:%-m/%-d}. Quality arms = each team's top 3 pitchers by rating (3+ innings). "
                        "'If fully rested' = the same game with every pitcher available, so the gap shows what "
                        "fatigue is costing.", small),
              PageBreak(),
              Paragraph("How the Book Was Made", h2)]
    method = [
        f"<b>Data.</b> {len(reg)} regular-season games (through {start - timedelta(days=1):%-m/%-d}) of "
        "GameChanger play-by-play. Runs per half-inning come from GC's running score and match every final score."
        + corrections + seeding + "; ties broken by head-to-head, then run differential.",
        "<b>Team ratings.</b> Each team gets an offense rating and every pitcher a runs-allowed rating, solved together "
        "so a lineup isn't penalized for facing aces and a pitcher isn't flattered by weak lineups. Small samples are "
        "pulled toward the team (pitchers) or league (teams) average.",
        "<b>Game engine.</b> Each half-inning draws runs from a distribution fitted to this division's real innings "
        f"(scaled by offense × pitcher, scoring scale {scale:.2f}). Every inning but the last is capped at "
        f"{RUN_CAP} runs. Game length follows the real mix of innings played; ties go to extra innings.",
        "<b>Pitching rules.</b> Each coach starts their best <i>rested</i> arm. A pitcher may pitch at most "
        f"{MAX_INN_PER_GAME} innings and {PITCH_CAP} pitches in a game; pitches per inning come from his real average "
        "(+2 per run allowed beyond 2). Rest follows Little League rules on calendar days: 1–20 pitches = no rest, "
        "21–35 = 1 day, 36–50 = 2 days, and no one pitches more than 2 days in a row. If no one is eligible, the "
        "team uses an emergency arm rated well below "
        "average — that's where depth pays off on back-to-back game days.",
        f"<b>Bracket.</b> The real {max(BRACKET)}-game bracket and calendar from the season config"
        + (f", including the if-necessary G{IF_NECESSARY[0]} on {IF_NECESSARY[1]:%-m/%-d}." if IF_NECESSARY else "."),
        f"<b>Calibration.</b> How much to trust ratings vs. luck was chosen by 5-fold cross-validation (dampening "
        f"{alpha:.2f}; 1.00 = full trust): ratings were rebuilt on 80% of games and scored on the other 20%.",
        "<b>Off rk / Pitch rk</b> = 1 is best. <b>Quality arms</b> = pitchers at or better than league-average with "
        "3+ innings, out of all arms used.",
    ]
    story += [Paragraph(m, body) for m in method]
    story += [Spacer(1, 8), Paragraph("For entertainment only. No wagering. Please don't show the kids. 🙂", small)]
    SimpleDocTemplate(str(path), pagesize=landscape(letter), leftMargin=30, rightMargin=30,
                      topMargin=28, bottomMargin=28, title=title).build(story)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--division", default="Minors")
    run(ap.parse_args().division)


def run(division):
    """Build the futures PDF for `division`; returns its path."""
    post = td.postseason(division)
    if not post.get("bracket"):
        raise SystemExit(f"No postseason bracket configured for {division} in config/{SEASON_ID}.yaml")
    configure(post)
    sb, _post, games, (apps, *_) = td.division_data(division)
    R = build_ratings(games, apps)
    nb = fit_run_distribution(R["halves"])
    reg = [g for g in games if not g["playoff"]]
    inn_counts = defaultdict(int)
    for g in reg:
        inn_counts[max(h["inning"] for h in g["halves"])] += 1
    inning_dist = {k: v / len(reg) for k, v in inn_counts.items()}
    scale, alpha, scores, act_rpg = tune(R, nb, inning_dist, games, apps)
    print(f"scale={scale:.3f} alpha={alpha}  actual {act_rpg:.1f} runs/game  log-loss (5-fold CV, playoffs): "
          + ", ".join(f"{a}: {s[0]:.3f}/{s[1]:.3f}" for a, s in scores.items()))

    open_day = post["start"] - timedelta(days=1)
    as_of = max(g["date"] for g in games)  # last game in the data, not the run date
    upd_day = as_of
    opening = simulate(R, nb, inning_dist, {}, availability(apps, reg, open_day), alpha, scale)
    fixed = actual_results(games, upd_day)
    updated = simulate(R, nb, inning_dist, fixed, availability(apps, games, upd_day), alpha, scale)
    for name, (champ, final, wb, emerg) in (("OPENING", opening), ("UPDATED", updated)):
        print(name, f"emergency arms/tournament {sum(emerg.values()):.2f}")
        for t, p in sorted(champ.items(), key=lambda kv: -kv[1]):
            print(f"  {t:20s} {p:6.1%}  final {final.get(t, 0):6.1%}  WB {wb.get(t, 0):6.1%}  {american(book(champ)[t])}")

    avail_now = availability(apps, games, upd_day)
    lines = []
    rosters = json.loads((SEASON_DIR / load_season_yaml()[1]["divisions"][division]["roster_json"])
                         .read_text(encoding="utf-8"))
    name_of = lambda team, init: pitcher_display(rosters, team, init)  # noqa: E731
    for gnum, a, b, day in next_games(fixed):
        p = game_line(R, nb, inning_dist, alpha, scale, a, b, day, avail_now)
        p_full = game_line(R, nb, inning_dist, alpha, scale, a, b, day, {})
        qa, qb = (qp_status(R, avail_now, t, day, name_of) for t in (a, b))
        lines.append((gnum, a, b, p, day, p_full, qa, qb))
        print(f"G{gnum} {day} {a} vs {b}: {p:.1%}  {moneyline(p)}  (full rest {p_full:.1%})  "
              f"QPs {qa[0]}/{qa[1]} vs {qb[0]}/{qb[1]}")
        for note in qa[2] + qb[2]:
            print(f"    out: {note}")

    out = (sb.parent / f"{SEASON_ID}_{division}_Tournament_Futures_asof_{as_of:%Y-%m-%d}.pdf")
    build_pdf(out, R, records(games), opening, updated, fixed, lines, alpha, scale, nb, games, as_of, division)
    for i, t in enumerate(seed_order(records(games), games), 1):
        w, l, ti, rs, ra = records(games)[t]
        print(f"  #{i:<2} {t:20s} {w}-{l}-{ti}  {rs}-{ra}")
    print(f"PDF → {out}")
    return out


if __name__ == "__main__":
    main()
