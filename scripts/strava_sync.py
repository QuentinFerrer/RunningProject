"""
Synchronise les activités Strava vers SQLite et génère data/profile.md.

Usage:
    .venv/Scripts/python scripts/strava_sync.py
"""
import os
import sys
import math
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

DB_PATH = ROOT / "data" / "running.db"
PROFILE_PATH = ROOT / "data" / "profile.md"

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def refresh_access_token():
    resp = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
        },
    )
    resp.raise_for_status()
    data = resp.json()

    env_path = ROOT / ".env"
    content = env_path.read_text(encoding="utf-8")
    for key, value in [
        ("STRAVA_ACCESS_TOKEN", data["access_token"]),
        ("STRAVA_REFRESH_TOKEN", data["refresh_token"]),
    ]:
        lines = content.split("\n")
        new_lines = []
        updated = False
        for line in lines:
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={value}")
                updated = True
            else:
                new_lines.append(line)
        if not updated:
            new_lines.append(f"{key}={value}")
        content = "\n".join(new_lines)
    env_path.write_text(content, encoding="utf-8")

    return data["access_token"]


def get_valid_token():
    token = ACCESS_TOKEN
    if not token:
        print("ERREUR: Lance d'abord strava_auth.py pour obtenir les tokens.")
        sys.exit(1)
    resp = requests.get(
        "https://www.strava.com/api/v3/athlete",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code == 401:
        print("Token expiré, rafraîchissement...")
        token = refresh_access_token()
    return token


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def init_db():
    (ROOT / "data").mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS activities (
            id            INTEGER PRIMARY KEY,
            name          TEXT,
            sport_type    TEXT,
            start_date    TEXT,
            distance      REAL,
            moving_time   INTEGER,
            elapsed_time  INTEGER,
            elevation_gain REAL,
            avg_heartrate REAL,
            max_heartrate REAL,
            avg_speed     REAL,
            suffer_score  INTEGER,
            workout_type  INTEGER,
            tss           REAL,
            synced_at     TEXT
        );

        CREATE TABLE IF NOT EXISTS races (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            date        TEXT NOT NULL,
            distance_km REAL,
            target_time TEXT,
            target_pace TEXT,
            race_type   TEXT,
            notes       TEXT,
            status      TEXT DEFAULT 'upcoming',
            created_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS feedbacks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            race_name       TEXT NOT NULL,
            date            TEXT NOT NULL,
            distance_km     REAL,
            finish_time     TEXT,
            avg_heartrate   REAL,
            nutrition_notes TEXT,
            feeling_score   INTEGER,
            positive_points TEXT,
            negative_points TEXT,
            notes           TEXT,
            activity_id     INTEGER REFERENCES activities(id),
            created_at      TEXT
        );

        CREATE TABLE IF NOT EXISTS athlete (
            id         INTEGER PRIMARY KEY,
            firstname  TEXT,
            lastname   TEXT,
            city       TEXT,
            country    TEXT,
            sex        TEXT,
            weight     REAL,
            updated_at TEXT
        );
    """)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# DB migration (ajout de colonnes sur DB existante)
# ---------------------------------------------------------------------------

def migrate_db(conn):
    new_activity_cols = [
        ("is_targeted_race",   "INTEGER DEFAULT 0"),
        ("race_target_time",   "TEXT"),
        ("race_calendar_type", "TEXT"),
        ("race_calendar_notes","TEXT"),
        ("has_feedback",       "INTEGER DEFAULT 0"),
    ]
    new_feedback_cols = [
        ("activity_id", "INTEGER"),
    ]
    for col, col_type in new_activity_cols:
        try:
            conn.execute(f"ALTER TABLE activities ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass
    for col, col_type in new_feedback_cols:
        try:
            conn.execute(f"ALTER TABLE feedbacks ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass
    conn.commit()


# ---------------------------------------------------------------------------
# Calendar matching
# ---------------------------------------------------------------------------

CALENDAR_PATH = ROOT / "data" / "calendar.md"


def parse_calendar():
    """Retourne la liste des courses du calendar.md."""
    if not CALENDAR_PATH.exists():
        return []
    races = []
    for line in CALENDAR_PATH.read_text(encoding="utf-8").split("\n"):
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        # Ignore header and separator rows
        if not parts or parts[0].startswith("Nom") or parts[0].startswith("---") or parts[0].startswith("-"):
            continue
        if len(parts) < 3:
            continue
        name, date_str, dist_str = parts[0], parts[1], parts[2]
        race_type = parts[3] if len(parts) > 3 else ""
        target    = parts[4] if len(parts) > 4 else ""
        notes     = parts[5] if len(parts) > 5 else ""
        try:
            date = datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError:
            continue
        try:
            distance_km = float(dist_str.replace("km", "").replace(",", ".").strip())
        except ValueError:
            continue
        races.append({
            "name": name, "date": date, "date_str": date_str,
            "distance_km": distance_km, "race_type": race_type,
            "target": target, "notes": notes, "original_line": line,
        })
    return races


def match_calendar_races(conn):
    """
    Pour chaque course passée dans calendar.md, cherche l'activité Strava
    correspondante et la tague 'course ciblée'. Retire la ligne du calendar.
    """
    today = datetime.utcnow().date()
    races = parse_calendar()
    matched = []

    for race in races:
        if race["date"] > today:
            continue  # Course future, on garde dans le calendar

        dist_m   = race["distance_km"] * 1000
        date_from = (race["date"] - timedelta(days=2)).isoformat()
        date_to   = (race["date"] + timedelta(days=2)).isoformat()

        c = conn.cursor()
        c.execute("""
            SELECT id, name, start_date, distance FROM activities
            WHERE DATE(start_date) BETWEEN ? AND ?
              AND distance BETWEEN ? AND ?
            ORDER BY ABS(distance - ?) ASC LIMIT 1
        """, (date_from, date_to, dist_m * 0.85, dist_m * 1.15, dist_m))

        row = c.fetchone()
        if row:
            activity_id = row[0]
            conn.execute("""
                UPDATE activities
                SET is_targeted_race    = 1,
                    race_target_time    = ?,
                    race_calendar_type  = ?,
                    race_calendar_notes = ?
                WHERE id = ?
            """, (race["target"], race["race_type"], race["notes"], activity_id))
            matched.append(race)
            print(f"  [calendar] '{race['name']}' liee a '{row[1]}' ({row[2][:10]}, {row[3]/1000:.1f}km)")

    conn.commit()

    if matched:
        content = CALENDAR_PATH.read_text(encoding="utf-8")
        for race in matched:
            content = content.replace(race["original_line"] + "\n", "")
            content = content.replace(race["original_line"], "")
        CALENDAR_PATH.write_text(content.strip() + "\n", encoding="utf-8")
        print(f"  -> {len(matched)} course(s) transferee(s) du calendar vers la DB")

    return len(matched)


# ---------------------------------------------------------------------------
# Strava API
# ---------------------------------------------------------------------------

def fetch_activities(token, after_ts=None):
    activities = []
    page = 1
    while True:
        params = {"per_page": 200, "page": page}
        if after_ts:
            params["after"] = int(after_ts)
        resp = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        activities.extend(batch)
        if len(batch) < 200:
            break
        page += 1
    return activities


def fetch_athlete(token):
    resp = requests.get(
        "https://www.strava.com/api/v3/athlete",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# TSS estimation
# ---------------------------------------------------------------------------

def estimate_tss(act):
    """Estimate Training Stress Score. Uses suffer_score if available."""
    duration_h = (act.get("moving_time") or 0) / 3600
    suffer = act.get("suffer_score")
    avg_hr = act.get("average_heartrate")

    if suffer and suffer > 0:
        return float(suffer)
    if avg_hr:
        # Rough IF from HR assuming max ~185 bpm
        intensity = avg_hr / 185
        return round(duration_h * intensity * intensity * 100, 1)
    return round(duration_h * 50, 1)


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

def sync_athlete(conn, token):
    data = fetch_athlete(token)
    conn.execute(
        """INSERT OR REPLACE INTO athlete
           (id, firstname, lastname, city, country, sex, weight, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data.get("id"),
            data.get("firstname", ""),
            data.get("lastname", ""),
            data.get("city", ""),
            data.get("country", ""),
            data.get("sex", ""),
            data.get("weight"),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    return data


def sync_activities(conn, token):
    c = conn.cursor()
    c.execute("SELECT MAX(start_date) FROM activities")
    last_date = c.fetchone()[0]

    after_ts = None
    if last_date:
        after_ts = datetime.strptime(last_date, "%Y-%m-%dT%H:%M:%SZ").timestamp()
        print(f"Récupération des activités depuis {last_date[:10]}...")
    else:
        print("Première sync — récupération de tout l'historique (peut prendre du temps)...")

    activities = fetch_activities(token, after_ts)
    print(f"{len(activities)} nouvelle(s) activité(s) trouvée(s)")

    inserted = 0
    for act in activities:
        try:
            conn.execute(
                """INSERT OR REPLACE INTO activities
                   (id, name, sport_type, start_date, distance, moving_time,
                    elapsed_time, elevation_gain, avg_heartrate, max_heartrate,
                    avg_speed, suffer_score, workout_type, tss, synced_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    act["id"],
                    act.get("name", ""),
                    act.get("sport_type", act.get("type", "")),
                    act.get("start_date", ""),
                    act.get("distance", 0),
                    act.get("moving_time", 0),
                    act.get("elapsed_time", 0),
                    act.get("total_elevation_gain", 0),
                    act.get("average_heartrate"),
                    act.get("max_heartrate"),
                    act.get("average_speed"),
                    act.get("suffer_score"),
                    act.get("workout_type"),
                    estimate_tss(act),
                    datetime.utcnow().isoformat(),
                ),
            )
            inserted += 1
        except sqlite3.Error as e:
            print(f"  Erreur activité {act.get('id')}: {e}")

    conn.commit()
    return inserted


# ---------------------------------------------------------------------------
# Training load (CTL / ATL / TSB)
# ---------------------------------------------------------------------------

def calculate_training_load(conn):
    c = conn.cursor()
    c.execute(
        """SELECT DATE(start_date) as day, SUM(tss) as daily_tss
           FROM activities
           WHERE sport_type IN ('Run', 'TrailRun', 'VirtualRun')
           GROUP BY day ORDER BY day"""
    )
    rows = c.fetchall()
    if not rows:
        return 0.0, 0.0, 0.0

    tss_by_day = {r[0]: r[1] for r in rows}
    first_day = datetime.strptime(rows[0][0], "%Y-%m-%d").date()
    today = datetime.utcnow().date()

    ctl_decay = math.exp(-1 / 42)
    atl_decay = math.exp(-1 / 7)
    ctl = atl = 0.0

    current = first_day
    while current <= today:
        tss = tss_by_day.get(current.strftime("%Y-%m-%d"), 0)
        ctl = ctl * ctl_decay + tss * (1 - ctl_decay)
        atl = atl * atl_decay + tss * (1 - atl_decay)
        current += timedelta(days=1)

    return round(ctl, 1), round(atl, 1), round(ctl - atl, 1)


# ---------------------------------------------------------------------------
# Profile.md generation
# ---------------------------------------------------------------------------

def fmt_duration(seconds):
    seconds = int(seconds or 0)
    h, m = divmod(seconds, 3600)
    m //= 60
    return f"{h}h{m:02d}" if h else f"{m}min"


def fmt_pace(avg_speed_ms):
    if not avg_speed_ms or avg_speed_ms <= 0:
        return "—"
    spm = 1000 / avg_speed_ms
    return f"{int(spm // 60)}:{int(spm % 60):02d}/km"


def ctl_label(ctl):
    if ctl < 30:
        return "Base faible / récupération"
    if ctl < 50:
        return "Base aérobie modérée"
    if ctl < 70:
        return "Bonne forme compétitive"
    if ctl < 90:
        return "Haute performance"
    return "Élite / très haute charge"


def tsb_label(tsb):
    if tsb > 15:
        return "Très frais — risque de sous-charge"
    if tsb > 5:
        return "Frais — idéal pour une compétition"
    if tsb > -10:
        return "Zone optimale d'entraînement"
    if tsb > -20:
        return "Fatigue modérée — surveiller la récupération"
    return "Surcharge — repos obligatoire"


def generate_profile(conn, athlete):
    c = conn.cursor()
    today = datetime.utcnow().date()
    run_types = "('Run', 'TrailRun', 'VirtualRun')"

    def query_period(days):
        since = (today - timedelta(days=days)).isoformat()
        c.execute(
            f"""SELECT COUNT(*), SUM(distance), SUM(moving_time), SUM(elevation_gain), AVG(avg_speed)
                FROM activities
                WHERE sport_type IN {run_types} AND DATE(start_date) >= ?""",
            (since,),
        )
        row = c.fetchone()
        return {
            "runs": row[0] or 0,
            "dist_km": (row[1] or 0) / 1000,
            "time_s": row[2] or 0,
            "elev_m": row[3] or 0,
            "speed": row[4],
        }

    # Global stats (running only)
    c.execute(
        f"SELECT COUNT(*), SUM(distance)/1000, SUM(moving_time), SUM(elevation_gain) FROM activities WHERE sport_type IN {run_types}"
    )
    tot = c.fetchone()

    p30 = query_period(30)
    p7 = query_period(7)
    ctl, atl, tsb = calculate_training_load(conn)

    # Last 10 runs
    c.execute(
        f"""SELECT name, sport_type, start_date, distance, moving_time, avg_speed, elevation_gain
            FROM activities WHERE sport_type IN {run_types}
            ORDER BY start_date DESC LIMIT 10"""
    )
    recent = c.fetchall()

    # Sport type breakdown last 12 months
    since_year = (today - timedelta(days=365)).isoformat()
    c.execute(
        "SELECT sport_type, COUNT(*) FROM activities WHERE DATE(start_date) >= ? GROUP BY sport_type ORDER BY 2 DESC",
        (since_year,),
    )
    breakdown = c.fetchall()
    total_year = sum(r[1] for r in breakdown)

    firstname = (athlete or {}).get("firstname", "Athlète")
    city = (athlete or {}).get("city", "")

    lines = [
        f"# Profil Athlète — {firstname}",
        f"",
        f"**Mise à jour :** {today.strftime('%d/%m/%Y')}  " + (f"**Ville :** {city}" if city else ""),
        f"",
        f"---",
        f"",
        f"## Charge d'entraînement",
        f"",
        f"| Indicateur | Valeur | Interprétation |",
        f"|------------|-------:|----------------|",
        f"| **CTL** – Forme / Fitness | **{ctl}** | {ctl_label(ctl)} |",
        f"| **ATL** – Fatigue aiguë | **{atl}** | — |",
        f"| **TSB** – Fraîcheur | **{tsb:+.1f}** | {tsb_label(tsb)} |",
        f"",
        f"---",
        f"",
        f"## Statistiques globales (course à pied)",
        f"",
        f"- Sorties totales : **{tot[0]}**",
        f"- Distance totale : **{tot[1]:,.0f} km**",
        f"- Temps total : **{fmt_duration(tot[2])}**",
        f"- Dénivelé total : **{(tot[3] or 0):,.0f} m**",
        f"",
        f"---",
        f"",
        f"## 30 derniers jours",
        f"",
        f"| Sorties | Distance | Temps | Dénivelé | Allure moy. |",
        f"|--------:|---------:|------:|---------:|-------------|",
        f"| {p30['runs']} | {p30['dist_km']:.1f} km | {fmt_duration(p30['time_s'])} | {p30['elev_m']:.0f} m | {fmt_pace(p30['speed'])} |",
        f"",
        f"## 7 derniers jours",
        f"",
        f"| Sorties | Distance | Temps | Dénivelé |",
        f"|--------:|---------:|------:|---------:|",
        f"| {p7['runs']} | {p7['dist_km']:.1f} km | {fmt_duration(p7['time_s'])} | {p7['elev_m']:.0f} m |",
        f"",
        f"---",
        f"",
        f"## 10 dernières sorties",
        f"",
        f"| Date | Activité | Type | Distance | Durée | Allure | D+ |",
        f"|------|----------|------|----------:|------:|-------:|---:|",
    ]

    for row in recent:
        name_a, sport, date_s, dist, dur, speed, elev = row
        try:
            d = datetime.strptime(date_s, "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y")
        except Exception:
            d = (date_s or "")[:10]
        lines.append(
            f"| {d} | {name_a or '—'} | {sport or '—'} | {(dist or 0)/1000:.1f} km"
            f" | {fmt_duration(dur)} | {fmt_pace(speed)} | {int(elev or 0)} m |"
        )

    if breakdown and total_year:
        lines += [
            f"",
            f"---",
            f"",
            f"## Types d'activités (12 derniers mois)",
            f"",
        ]
        for sport_type, cnt in breakdown:
            pct = cnt / total_year * 100
            lines.append(f"- **{sport_type}** : {cnt} sorties ({pct:.0f}%)")

    lines.append("")
    PROFILE_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"profile.md généré : {PROFILE_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Strava Sync ===\n")
    conn = init_db()
    migrate_db(conn)
    token = get_valid_token()

    print("Sync profil athlete...")
    athlete = sync_athlete(conn, token)
    print(f"  -> {athlete.get('firstname')} {athlete.get('lastname')}")

    new_count = sync_activities(conn, token)
    print(f"  -> {new_count} activite(s) inseree(s)")

    print("Matching calendar -> DB...")
    match_calendar_races(conn)

    print("Generation de profile.md...")
    generate_profile(conn, athlete)

    conn.close()
    print("\nSync terminee !")


if __name__ == "__main__":
    main()
