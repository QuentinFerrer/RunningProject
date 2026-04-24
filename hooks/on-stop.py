"""
Hook Stop — appelé à la fin de chaque session Claude.
Vérifie si une sync Strava est recommandée selon l'âge de profile.md.
"""
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).parent.parent
profile = ROOT / "data" / "profile.md"

if not profile.exists():
    print("[RunningCoach] Session terminee. Lance le setup pour initialiser le projet.")
else:
    age = datetime.now() - datetime.fromtimestamp(profile.stat().st_mtime)
    hours = int(age.total_seconds() / 3600)
    if age > timedelta(hours=12):
        print(f"[RunningCoach] Session terminee. Derniere sync il y a {hours}h — pense a sync Strava au prochain demarrage.")
    else:
        print("[RunningCoach] Session terminee. A bientot !")
