"""
Enregistre un feedback de course dans la DB et dans feedbacks.md,
en le liant automatiquement à l'activité Strava correspondante.

Usage (appelé par l'agent) :
    .venv/Scripts/python scripts/add_feedback.py \
        --race "Nom de la course" \
        --date "07/04/2026" \
        --distance 42.2 \
        --time "03:45:22" \
        --feeling 7 \
        --hr 158 \
        --nutrition "2 gels à 20 et 35km" \
        --positive "Bonne première moitié" \
        --negative "Mur à 35km" \
        --notes "Météo fraîche"
"""
import argparse
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

DB_PATH        = ROOT / "data" / "running.db"
FEEDBACKS_PATH = ROOT / "data" / "feedbacks.md"


def find_matching_activity(conn, date_str, distance_km):
    """
    Cherche l'activité Strava la plus proche par date (± 2 jours)
    et distance (± 15%). Retourne (id, name, start_date, distance) ou None.
    """
    try:
        race_date = datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        race_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    dist_m    = distance_km * 1000
    date_from = (race_date - timedelta(days=2)).isoformat()
    date_to   = (race_date + timedelta(days=2)).isoformat()

    c = conn.cursor()
    c.execute("""
        SELECT id, name, start_date, distance, moving_time
        FROM activities
        WHERE DATE(start_date) BETWEEN ? AND ?
          AND distance BETWEEN ? AND ?
        ORDER BY ABS(distance - ?) ASC
        LIMIT 1
    """, (date_from, date_to, dist_m * 0.85, dist_m * 1.15, dist_m))
    return c.fetchone()


def add_feedback(args):
    conn = sqlite3.connect(DB_PATH)

    # Lier au feedback à l'activité Strava
    activity = find_matching_activity(conn, args.date, args.distance)
    activity_id = None

    if activity:
        activity_id = activity[0]
        print(f"Activite Strava trouvee : '{activity[1]}' ({activity[2][:10]}, {activity[3]/1000:.1f}km)")
        conn.execute(
            "UPDATE activities SET has_feedback = 1 WHERE id = ?",
            (activity_id,),
        )
    else:
        print(f"Aucune activite Strava correspondante pour '{args.race}' ({args.date}, {args.distance}km)")
        print("Feedback enregistre sans lien Strava.")

    # Insérer dans la table feedbacks
    conn.execute("""
        INSERT INTO feedbacks
            (race_name, date, distance_km, finish_time, avg_heartrate,
             nutrition_notes, feeling_score, positive_points,
             negative_points, notes, activity_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        args.race,
        args.date,
        args.distance,
        args.time,
        args.hr,
        args.nutrition,
        args.feeling,
        args.positive,
        args.negative,
        args.notes,
        activity_id,
        datetime.utcnow().isoformat(),
    ))
    conn.commit()

    # Écrire dans feedbacks.md (lecture humaine)
    strava_link = f"Strava #{activity_id}" if activity_id else "Non liée"
    entry = f"""
---

## {args.race} — {args.date}

- **Distance :** {args.distance} km
- **Temps réalisé :** {args.time or '—'}
- **Ressenti global :** {args.feeling}/10
- **FC moyenne :** {args.hr or '—'} bpm
- **Nutrition :** {args.nutrition or '—'}
- **Points positifs :** {args.positive or '—'}
- **Points à améliorer :** {args.negative or '—'}
- **Notes :** {args.notes or '—'}
- **Activité Strava :** {strava_link}

"""
    existing = FEEDBACKS_PATH.read_text(encoding="utf-8") if FEEDBACKS_PATH.exists() else ""
    FEEDBACKS_PATH.write_text(existing + entry, encoding="utf-8")

    conn.close()
    print(f"Feedback '{args.race}' enregistré.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enregistrer un feedback de course")
    parser.add_argument("--race",     required=True,       help="Nom de la course")
    parser.add_argument("--date",     required=True,       help="Date JJ/MM/AAAA")
    parser.add_argument("--distance", required=True, type=float, help="Distance en km")
    parser.add_argument("--time",                          help="Temps réalisé HH:MM:SS")
    parser.add_argument("--feeling",  type=int,            help="Ressenti 1-10")
    parser.add_argument("--hr",       type=float,          help="FC moyenne (bpm)")
    parser.add_argument("--nutrition",                     help="Notes nutrition")
    parser.add_argument("--positive",                      help="Points positifs")
    parser.add_argument("--negative",                      help="Points à améliorer")
    parser.add_argument("--notes",                         help="Notes libres")
    args = parser.parse_args()
    add_feedback(args)
