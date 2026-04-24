"""
Hook PreToolUse (Bash) — intercepte les commandes git push.
Scanne les fichiers committés et bloque si des données personnelles sont détectées.

Exit code 0 → push autorisé
Exit code 2 → push bloqué (Claude ne peut pas exécuter la commande)
"""
import os
import sys
import subprocess

BLOCKED_PATTERNS = [
    ".env",
    "data/running.db",
    "data/profile.md",
    "data/calendar.md",
    "data/feedbacks.md",
    "personal/",
]

tool_input = os.environ.get("CLAUDE_TOOL_INPUT", "")

# Ne s'active que si la commande contient "git push"
if "git push" not in tool_input:
    sys.exit(0)

# Récupère les fichiers du dernier commit + staged
try:
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        capture_output=True, text=True
    )
    committed_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

    staged_result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True
    )
    staged_files = staged_result.stdout.strip().split("\n") if staged_result.stdout.strip() else []

    all_files = committed_files + staged_files
except Exception:
    sys.exit(0)

violations = []
for f in all_files:
    for pattern in BLOCKED_PATTERNS:
        if pattern in f:
            violations.append(f)
            break

if violations:
    print("\n[SECURITE] Push bloque — donnees personnelles detectees :\n")
    for v in violations:
        print(f"  ❌  {v}")
    print("\nRetire ces fichiers avant de pusher.")
    print("Verifie ton .gitignore et utilise : git rm --cached <fichier>\n")
    sys.exit(2)

print("[SECURITE] Verification OK — aucune donnee personnelle detectee.")
sys.exit(0)
