"""
Hook PreToolUse (Bash) — intercepte les commandes git push.

Vérifie deux choses :
1. Aucune donnée personnelle dans les fichiers committés
2. La branche n'a pas divergé de origin/main (risque de conflit)

Exit code 0 → push autorisé
Exit code 2 → push bloqué
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

if "git push" not in tool_input:
    sys.exit(0)

errors = []

# --- Vérification 1 : données personnelles ---
try:
    committed = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        capture_output=True, text=True
    ).stdout.strip().split("\n")

    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True
    ).stdout.strip().split("\n")

    for f in committed + staged:
        for pattern in BLOCKED_PATTERNS:
            if pattern in f:
                errors.append(f"  Donnee personnelle detectee : {f}")
                break
except Exception:
    pass

# --- Vérification 2 : divergence avec origin/main ---
try:
    subprocess.run(["git", "fetch", "origin", "main", "--quiet"],
                   capture_output=True)

    current_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True
    ).stdout.strip()

    behind = subprocess.run(
        ["git", "log", "--oneline", "HEAD..origin/main"],
        capture_output=True, text=True
    ).stdout.strip()

    if behind:
        count = len([l for l in behind.split("\n") if l])
        errors.append(
            f"  Branche '{current_branch}' en retard de {count} commit(s) sur origin/main.\n"
            f"  Rebase avant de pusher :\n"
            f"    git rebase origin/main\n"
            f"  Puis :\n"
            f"    git push --force-with-lease origin {current_branch}"
        )
except Exception:
    pass

# --- Résultat ---
if errors:
    print("\n[SECURITE] Push bloque :\n")
    for e in errors:
        print(e)
    print()
    sys.exit(2)

print("[OK] Verification pre-push reussie.")
sys.exit(0)
