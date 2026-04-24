"""
Supprime toutes les données personnelles pour repartir à zéro.
À utiliser lors d'un changement d'utilisateur ou d'une réinitialisation complète.

Usage:
    .venv/Scripts/python scripts/reset.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

PERSONAL_FILES = [
    ROOT / "data" / "running.db",
    ROOT / "data" / "profile.md",
    ROOT / "data" / "calendar.md",
    ROOT / "data" / "feedbacks.md",
]

ENV_FILE = ROOT / ".env"


def reset():
    print("=" * 50)
    print("  REINITIALISATION DU PROJET")
    print("=" * 50)
    print()

    existing = [f for f in PERSONAL_FILES if f.exists()]
    env_has_tokens = False

    if ENV_FILE.exists():
        content = ENV_FILE.read_text(encoding="utf-8")
        env_has_tokens = "STRAVA_ACCESS_TOKEN=" in content and len(
            [l for l in content.splitlines() if l.startswith("STRAVA_ACCESS_TOKEN=") and l.split("=", 1)[1].strip()]
        ) > 0

    if not existing and not env_has_tokens:
        print("Le projet est deja vierge. Rien a supprimer.")
        return

    print("Les elements suivants vont etre supprimes :\n")
    for f in existing:
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name}  ({size_kb:.0f} Ko)")
    if env_has_tokens:
        print("  - Tokens Strava dans .env (CLIENT_ID et CLIENT_SECRET conserves)")
    print()

    confirm = input("Confirmer la suppression ? (oui / non) : ").strip().lower()
    if confirm not in ("oui", "o", "yes", "y"):
        print("\nAnnule. Aucune donnee supprimee.")
        sys.exit(0)

    print()
    for f in existing:
        f.unlink()
        print(f"  Supprime : {f.name}")

    # Effacer uniquement les tokens Strava, pas les credentials
    if env_has_tokens and ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        new_lines = []
        for line in lines:
            if line.startswith("STRAVA_ACCESS_TOKEN=") or line.startswith("STRAVA_REFRESH_TOKEN="):
                key = line.split("=")[0]
                new_lines.append(f"{key}=")
            else:
                new_lines.append(line)
        ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print("  Tokens Strava effaces dans .env")

    print()
    print("Reinitialisation terminee.")
    print("Prochaine etape : lancer strava_auth.py pour reconnecter Strava.")


if __name__ == "__main__":
    reset()
