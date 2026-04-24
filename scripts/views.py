"""
Affiche des vues sur les données de course.

Usage:
    python scripts/views.py calendar              # prochaines courses
    python scripts/views.py recent [N]            # N dernières activités (défaut 10)
    python scripts/views.py stats [week|month|year|all]  # stats par période
    python scripts/views.py load [jours]          # graphique CTL/ATL/TSB (défaut 90)
    python scripts/views.py race "nom"            # chercher une course par nom
    python scripts/views.py prs                   # records personnels par distance
    python scripts/views.py filter [options]      # filtrage multi-critères

Options pour filter :
    --from  YYYY-MM-DD    date de début
    --to    YYYY-MM-DD    date de fin
    --min-dist KM         distance minimale en km
    --max-dist KM         distance maximale en km
    --type  Run|TrailRun|All   type d'activité (défaut: toutes les courses)
    --name  "texte"       filtre sur le nom (recherche partielle)
    --races-only          seulement les courses ciblées
    --has-feedback        seulement les activités avec un feedback
    --order date|dist|time|tss  tri (défaut: date)
    --limit N             nombre max de résultats (défaut: 50)
"""
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "running.db"
CALENDAR_PATH = ROOT / "data" / "calendar.md"


def fmt_time(seconds):
    if not seconds:
        return "-"
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}h{m:02d}m{s:02d}s"
    return f"{m}m{s:02d}s"


def fmt_pace(speed_ms, distance_m=None):
    """Convertit avg_speed (m/s) en allure min/km."""
    if not speed_ms or speed_ms == 0:
        return "-"
    pace_s = 1000 / speed_ms
    m, s = divmod(int(pace_s), 60)
    return f"{m}'{s:02d}\"/km"


def fmt_dist(meters):
    if not meters:
        return "-"
    return f"{meters / 1000:.2f} km"


def get_conn():
    if not DB_PATH.exists():
        print("Base de donnees introuvable. Lance d'abord strava_sync.py.")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------------------------
# Vue : Calendrier
# ---------------------------------------------------------------------------

def view_calendar():
    if not CALENDAR_PATH.exists():
        print("Aucun calendrier (data/calendar.md n'existe pas).")
        return
    print(CALENDAR_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Vue : Activités récentes
# ---------------------------------------------------------------------------

def view_recent(n=10):
    conn = get_conn()
    rows = conn.execute("""
        SELECT name, sport_type, start_date, distance, moving_time,
               elevation_gain, avg_speed, avg_heartrate, tss, is_targeted_race
        FROM activities
        ORDER BY start_date DESC
        LIMIT ?
    """, (n,)).fetchall()
    conn.close()

    if not rows:
        print("Aucune activite trouvee.")
        return

    print(f"\n{'#':<3} {'Nom':<30} {'Type':<12} {'Date':<12} {'Dist':>8} {'Temps':>9} {'Allure':>9} {'D+':<6} {'FC':>5} {'TSS':>5}")
    print("-" * 110)
    for i, r in enumerate(rows, 1):
        name, stype, date, dist, mvtime, elev, speed, hr, tss, is_race = r
        date_fmt = date[:10] if date else "-"
        flag = " *" if is_race else ""
        print(
            f"{i:<3} {(str(name)[:28] + flag):<30} {str(stype or '')[:12]:<12} {date_fmt:<12} "
            f"{fmt_dist(dist):>8} {fmt_time(mvtime):>9} {fmt_pace(speed):>9} "
            f"{int(elev or 0):<6} {int(hr or 0):>5} {int(tss or 0):>5}"
        )
    print("\n* = course ciblée au calendrier")


# ---------------------------------------------------------------------------
# Vue : Stats par période
# ---------------------------------------------------------------------------

def view_stats(period="month"):
    periods = {
        "week":  (datetime.now() - timedelta(days=7)).isoformat(),
        "month": (datetime.now() - timedelta(days=30)).isoformat(),
        "year":  (datetime.now() - timedelta(days=365)).isoformat(),
        "all":   "1970-01-01",
    }
    since = periods.get(period, periods["month"])
    label = {"week": "7 derniers jours", "month": "30 derniers jours",
             "year": "12 derniers mois", "all": "Tout temps"}.get(period, period)

    conn = get_conn()
    row = conn.execute("""
        SELECT COUNT(*), SUM(distance), SUM(moving_time), SUM(elevation_gain),
               AVG(avg_heartrate), SUM(tss)
        FROM activities
        WHERE start_date >= ? AND sport_type IN ('Run','TrailRun','VirtualRun')
    """, (since,)).fetchone()

    monthly = conn.execute("""
        SELECT strftime('%Y-%m', start_date) as month,
               COUNT(*) as nb,
               ROUND(SUM(distance)/1000, 1) as km,
               SUM(moving_time) as time_s
        FROM activities
        WHERE start_date >= ? AND sport_type IN ('Run','TrailRun','VirtualRun')
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """, (since,)).fetchall()
    conn.close()

    nb, dist, mvtime, elev, hr, tss = row
    print(f"\n=== Stats — {label} ===\n")
    print(f"  Sorties       : {nb or 0}")
    print(f"  Distance      : {(dist or 0)/1000:.1f} km")
    print(f"  Temps total   : {fmt_time(mvtime or 0)}")
    print(f"  Dénivelé +    : {int(elev or 0)} m")
    print(f"  FC moy        : {int(hr or 0)} bpm")
    print(f"  TSS total     : {int(tss or 0)}")

    if monthly and period in ("year", "all"):
        print(f"\n{'Mois':<10} {'Sorties':>8} {'Km':>8} {'Temps':>10}")
        print("-" * 40)
        for m, nb_m, km_m, t_m in monthly:
            print(f"{m:<10} {nb_m:>8} {km_m:>8.1f} {fmt_time(t_m):>10}")


# ---------------------------------------------------------------------------
# Vue : Charge d'entraînement (CTL/ATL/TSB)
# ---------------------------------------------------------------------------

def _compute_load(days=90):
    conn = get_conn()
    rows = conn.execute("""
        SELECT DATE(start_date), SUM(tss)
        FROM activities
        WHERE start_date >= ?
        GROUP BY DATE(start_date)
        ORDER BY DATE(start_date)
    """, ((datetime.now() - timedelta(days=days + 60)).isoformat(),)).fetchall()
    conn.close()

    daily = {r[0]: r[1] for r in rows if r[1]}
    start = datetime.now() - timedelta(days=days + 60)
    end   = datetime.now()

    ctl = atl = 0.0
    series = []
    d = start
    while d <= end:
        key = d.strftime("%Y-%m-%d")
        tss = daily.get(key, 0)
        ctl = ctl + (tss - ctl) / 42
        atl = atl + (tss - atl) / 7
        tsb = ctl - atl
        if d >= datetime.now() - timedelta(days=days):
            series.append((key, round(ctl, 1), round(atl, 1), round(tsb, 1), tss))
        d += timedelta(days=1)
    return series


def view_load(days=90):
    series = _compute_load(days)
    if not series:
        print("Pas assez de données pour calculer la charge.")
        return

    # Try matplotlib
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        dates = [datetime.strptime(r[0], "%Y-%m-%d") for r in series]
        ctls  = [r[1] for r in series]
        atls  = [r[2] for r in series]
        tsbs  = [r[3] for r in series]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
        fig.suptitle(f"Charge d'entraînement — {days} derniers jours", fontsize=13)

        ax1.plot(dates, ctls, label="CTL (forme)", color="#2196F3", linewidth=2)
        ax1.plot(dates, atls, label="ATL (fatigue)", color="#F44336", linewidth=2)
        ax1.fill_between(dates, ctls, atls, alpha=0.1, color="gray")
        ax1.set_ylabel("Charge (TSS)")
        ax1.legend(loc="upper left")
        ax1.grid(True, alpha=0.3)

        colors = ["#4CAF50" if t >= 0 else "#F44336" for t in tsbs]
        ax2.bar(dates, tsbs, color=colors, width=0.8, label="TSB (fraîcheur)")
        ax2.axhline(0, color="black", linewidth=0.8)
        ax2.axhline(-30, color="#FF9800", linewidth=0.8, linestyle="--", label="Zone fatigue")
        ax2.set_ylabel("TSB")
        ax2.legend(loc="upper left")
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        fig.autofmt_xdate()

        out = ROOT / "data" / "load_chart.png"
        plt.tight_layout()
        plt.savefig(out, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"Graphique sauvegarde : {out}")

    except ImportError:
        # Fallback texte
        print(f"\n=== Charge d'entraînement — {days} derniers jours ===\n")
        print(f"{'Date':<12} {'CTL':>6} {'ATL':>6} {'TSB':>6}")
        print("-" * 35)
        step = max(1, len(series) // 30)
        for row in series[::step]:
            date, ctl, atl, tsb = row[0], row[1], row[2], row[3]
            bar = "#" * int(ctl / 3) if ctl > 0 else ""
            print(f"{date:<12} {ctl:>6.1f} {atl:>6.1f} {tsb:>6.1f}  {bar}")

        last = series[-1]
        print(f"\n--- Aujourd'hui ---")
        print(f"  CTL  : {last[1]:.1f}  (forme de base)")
        print(f"  ATL  : {last[2]:.1f}  (fatigue récente)")
        print(f"  TSB  : {last[3]:.1f}  {'-> repose-toi' if last[3] < -20 else '-> bonne forme' if last[3] >= 0 else '-> entraine-toi'}")


# ---------------------------------------------------------------------------
# Vue : Recherche d'une course
# ---------------------------------------------------------------------------

def view_race(query):
    conn = get_conn()
    rows = conn.execute("""
        SELECT name, sport_type, start_date, distance, moving_time,
               elevation_gain, avg_speed, avg_heartrate, tss,
               is_targeted_race, has_feedback
        FROM activities
        WHERE LOWER(name) LIKE LOWER(?)
        ORDER BY start_date DESC
        LIMIT 10
    """, (f"%{query}%",)).fetchall()

    feedbacks = {}
    for r in rows:
        name, _, date = r[0], r[1], r[2]
        if r[10]:  # has_feedback
            fb = conn.execute("""
                SELECT feeling_score, finish_time, positive_points, negative_points
                FROM feedbacks
                WHERE DATE(date) = DATE(?)
                ORDER BY created_at DESC LIMIT 1
            """, (date,)).fetchone()
            if fb:
                feedbacks[r[2]] = fb
    conn.close()

    if not rows:
        print(f"Aucune activite trouvee pour « {query} ».")
        return

    for r in rows:
        name, stype, date, dist, mvtime, elev, speed, hr, tss, is_race, has_fb = r
        print(f"\n{'='*50}")
        print(f"  {name}")
        print(f"  {date[:10]} | {stype}")
        print(f"  Distance   : {fmt_dist(dist)}")
        print(f"  Temps      : {fmt_time(mvtime)}")
        print(f"  Allure     : {fmt_pace(speed)}")
        print(f"  Dénivelé + : {int(elev or 0)} m")
        print(f"  FC moy     : {int(hr or 0)} bpm")
        print(f"  TSS        : {int(tss or 0)}")
        if is_race:
            print(f"  [Course ciblée]")
        if date in feedbacks:
            fb = feedbacks[date]
            print(f"\n  Feedback:")
            print(f"    Ressenti  : {fb[0]}/10")
            print(f"    Temps off.: {fb[1]}")
            print(f"    Positif   : {fb[2]}")
            print(f"    A améliorer: {fb[3]}")


# ---------------------------------------------------------------------------
# Vue : Records personnels
# ---------------------------------------------------------------------------

DISTANCE_BUCKETS = [
    ("5 km",       4500,    5500),
    ("10 km",      9000,   11000),
    ("Semi",      19000,   22000),
    ("Marathon",  40000,   44000),
    ("50 km",     47000,   53000),
    ("100 km",    95000,  105000),
]


def view_prs():
    conn = get_conn()
    print("\n=== Records personnels ===\n")
    found_any = False
    for label, dmin, dmax in DISTANCE_BUCKETS:
        rows = conn.execute("""
            SELECT name, start_date, distance, moving_time, avg_speed
            FROM activities
            WHERE distance BETWEEN ? AND ?
              AND sport_type IN ('Run','TrailRun','VirtualRun')
            ORDER BY moving_time ASC
            LIMIT 3
        """, (dmin, dmax)).fetchall()
        if rows:
            found_any = True
            print(f"  {label}")
            for i, r in enumerate(rows, 1):
                medal = ["", "Or", "Argent", "Bronze"][i]
                name, date, dist, mvtime, speed = r
                print(f"    {medal:<8} {fmt_time(mvtime):>9}  ({fmt_pace(speed)})  {date[:10]}  {name[:30]}")
            print()
    conn.close()
    if not found_any:
        print("Aucun record trouvé — lance d'abord strava_sync.py.")


# ---------------------------------------------------------------------------
# Vue : Filtre multi-critères
# ---------------------------------------------------------------------------

def view_filter(args_list):
    import argparse
    parser = argparse.ArgumentParser(prog="views.py filter", add_help=True)
    parser.add_argument("--from",       dest="date_from",   metavar="YYYY-MM-DD")
    parser.add_argument("--to",         dest="date_to",     metavar="YYYY-MM-DD")
    parser.add_argument("--min-dist",   dest="min_dist",    type=float, metavar="KM")
    parser.add_argument("--max-dist",   dest="max_dist",    type=float, metavar="KM")
    parser.add_argument("--type",       dest="sport_type",  metavar="Run|TrailRun|All")
    parser.add_argument("--name",       dest="name",        metavar="TEXTE")
    parser.add_argument("--races-only", dest="races_only",  action="store_true")
    parser.add_argument("--has-feedback",dest="has_feedback",action="store_true")
    parser.add_argument("--order",      dest="order",       choices=["date","dist","time","tss"], default="date")
    parser.add_argument("--limit",      dest="limit",       type=int, default=50)

    try:
        opts = parser.parse_args(args_list)
    except SystemExit:
        return

    conditions = []
    params     = []

    if opts.date_from:
        conditions.append("start_date >= ?")
        params.append(opts.date_from)
    if opts.date_to:
        conditions.append("start_date <= ?")
        params.append(opts.date_to + " 23:59:59")
    if opts.min_dist is not None:
        conditions.append("distance >= ?")
        params.append(opts.min_dist * 1000)
    if opts.max_dist is not None:
        conditions.append("distance <= ?")
        params.append(opts.max_dist * 1000)
    if opts.sport_type and opts.sport_type.lower() != "all":
        conditions.append("sport_type LIKE ?")
        params.append(f"%{opts.sport_type}%")
    else:
        # Par défaut : seulement les activités de course
        conditions.append("sport_type IN ('Run','TrailRun','VirtualRun')")
    if opts.name:
        conditions.append("LOWER(name) LIKE LOWER(?)")
        params.append(f"%{opts.name}%")
    if opts.races_only:
        conditions.append("is_targeted_race = 1")
    if opts.has_feedback:
        conditions.append("has_feedback = 1")

    where = " AND ".join(conditions) if conditions else "1=1"
    order_map = {"date": "start_date DESC", "dist": "distance DESC",
                 "time": "moving_time ASC",  "tss":  "tss DESC"}
    order_sql = order_map[opts.order]

    sql = f"""
        SELECT name, sport_type, start_date, distance, moving_time,
               elevation_gain, avg_speed, avg_heartrate, tss,
               is_targeted_race, has_feedback
        FROM activities
        WHERE {where}
        ORDER BY {order_sql}
        LIMIT ?
    """
    params.append(opts.limit)

    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    # Résumé des filtres appliqués
    desc = []
    if opts.date_from or opts.date_to:
        desc.append(f"du {opts.date_from or '?'} au {opts.date_to or 'aujourd\\'hui'}")
    if opts.min_dist is not None or opts.max_dist is not None:
        desc.append(f"distance {opts.min_dist or 0}–{opts.max_dist or '+inf'} km")
    if opts.sport_type and opts.sport_type.lower() != "all":
        desc.append(f"type : {opts.sport_type}")
    if opts.name:
        desc.append(f"nom contient \"{opts.name}\"")
    if opts.races_only:
        desc.append("courses ciblées")
    if opts.has_feedback:
        desc.append("avec feedback")

    title = " | ".join(desc) if desc else "Toutes les activités"
    print(f"\n=== {title} — {len(rows)} résultat(s) ===\n")

    if not rows:
        print("Aucune activite trouvee pour ces criteres.")
        return

    print(f"{'#':<3} {'Nom':<30} {'Type':<12} {'Date':<12} {'Dist':>8} "
          f"{'Temps':>9} {'Allure':>9} {'D+':>5} {'FC':>5} {'TSS':>5} {'':>2}")
    print("-" * 115)
    for i, r in enumerate(rows, 1):
        name, stype, date, dist, mvtime, elev, speed, hr, tss, is_race, has_fb = r
        flags = ("*" if is_race else "") + ("F" if has_fb else "")
        print(
            f"{i:<3} {(str(name)[:28] + flags):<30} {str(stype or '')[:12]:<12} "
            f"{(date or '')[:10]:<12} {fmt_dist(dist):>8} {fmt_time(mvtime):>9} "
            f"{fmt_pace(speed):>9} {int(elev or 0):>5} {int(hr or 0):>5} {int(tss or 0):>5}"
        )
    print("\n* = course ciblée   F = feedback disponible")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0].lower()

    if cmd == "calendar":
        view_calendar()
    elif cmd == "recent":
        n = int(args[1]) if len(args) > 1 else 10
        view_recent(n)
    elif cmd == "stats":
        period = args[1] if len(args) > 1 else "month"
        view_stats(period)
    elif cmd == "load":
        days = int(args[1]) if len(args) > 1 else 90
        view_load(days)
    elif cmd == "race":
        if len(args) < 2:
            print("Usage: views.py race \"nom de la course\"")
            return
        view_race(" ".join(args[1:]))
    elif cmd == "prs":
        view_prs()
    elif cmd == "filter":
        view_filter(args[1:])
    else:
        print(f"Commande inconnue : {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
