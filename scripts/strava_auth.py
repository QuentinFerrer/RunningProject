"""
One-time OAuth setup for Strava API.
Run this script once to get your access and refresh tokens.

Usage:
    .venv/Scripts/python scripts/strava_auth.py
"""
import os
import sys
import webbrowser
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET or CLIENT_SECRET == "your_client_secret_here":
    print("ERREUR: Remplis STRAVA_CLIENT_ID et STRAVA_CLIENT_SECRET dans le fichier .env")
    sys.exit(1)

AUTH_URL = (
    f"https://www.strava.com/oauth/authorize"
    f"?client_id={CLIENT_ID}"
    f"&response_type=code"
    f"&redirect_uri=http://localhost/exchange_token"
    f"&approval_prompt=force"
    f"&scope=read,activity:read_all"
)

print("Ouverture de la page d'autorisation Strava dans le navigateur...")
print(f"\nURL: {AUTH_URL}\n")
webbrowser.open(AUTH_URL)

print("Après avoir autorisé l'application, tu seras redirigé vers une URL du type:")
print("  http://localhost/exchange_token?state=&code=XXXXXX&scope=...")
print("\nCopie la valeur du paramètre 'code' dans l'URL et colle-la ici:")
code = input("Code d'autorisation : ").strip()

if not code:
    print("Aucun code fourni. Abandon.")
    sys.exit(1)

print("\nÉchange du code contre les tokens...")
response = requests.post(
    "https://www.strava.com/oauth/token",
    data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    },
)

if response.status_code != 200:
    print(f"Erreur: {response.json()}")
    sys.exit(1)

data = response.json()
access_token = data["access_token"]
refresh_token = data["refresh_token"]
athlete = data.get("athlete", {})

print(f"\nSuccès ! Bienvenue {athlete.get('firstname', '')} {athlete.get('lastname', '')}")

# Update .env file
env_path = ROOT / ".env"
content = env_path.read_text(encoding="utf-8")

for key, value in [
    ("STRAVA_ACCESS_TOKEN", access_token),
    ("STRAVA_REFRESH_TOKEN", refresh_token),
]:
    lines = content.split("\n")
    updated = False
    new_lines = []
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
print(".env mis à jour avec les tokens.")
print("\nTu peux maintenant lancer la synchronisation :")
print("  .venv/Scripts/python scripts/strava_sync.py")
