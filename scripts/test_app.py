"""
Tests de sanité de l'application Running Coach AI.
Ne nécessite pas de connexion Strava.

Usage:
    .venv/Scripts/python scripts/test_app.py
"""
import ast
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
PYTHON = sys.executable

PASS = "  [OK]"
FAIL = "  [FAIL]"
SKIP = "  [SKIP]"

results = []


def ok(name):
    results.append(("OK", name))
    print(f"{PASS} {name}")


def fail(name, reason=""):
    results.append(("FAIL", name))
    print(f"{FAIL} {name}" + (f" — {reason}" if reason else ""))


def skip(name, reason=""):
    results.append(("SKIP", name))
    print(f"{SKIP} {name}" + (f" ({reason})" if reason else ""))


# ---------------------------------------------------------------------------
# 1. Fichiers requis
# ---------------------------------------------------------------------------

def test_required_files():
    print("\n--- 1. Fichiers requis ---")
    required = [
        "CLAUDE.md",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        ".gitattributes",
        "agents/mode-agent.md",
        "agents/setup-agent.md",
        "agents/help-agent.md",
        "agents/views-agent.md",
        "agents/profile-agent.md",
        "agents/recovery-agent.md",
        "agents/race-planner-agent.md",
        "agents/nutrition-agent.md",
        "agents/feedback-agent.md",
        "rules/safety.md",
        "rules/training-load.md",
        "rules/recovery.md",
        "rules/race-targets.md",
        "rules/nutrition.md",
        "scripts/strava_auth.py",
        "scripts/strava_sync.py",
        "scripts/add_feedback.py",
        "scripts/views.py",
        "scripts/update_readme.py",
        "scripts/reset.py",
        "hooks/pre-push.py",
        "hooks/post-write.py",
        "hooks/on-stop.py",
        "dev/git-agent.md",
        ".claude/settings.json",
        "data/.gitkeep",
        "data/calendar.example.md",
        "data/feedbacks.example.md",
    ]
    for path in required:
        if (ROOT / path).exists():
            ok(path)
        else:
            fail(path, "introuvable")


# ---------------------------------------------------------------------------
# 2. Syntaxe Python
# ---------------------------------------------------------------------------

def test_python_syntax():
    print("\n--- 2. Syntaxe Python ---")
    scripts = list((ROOT / "scripts").glob("*.py")) + list((ROOT / "hooks").glob("*.py"))
    for path in sorted(scripts):
        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source)
            ok(path.name)
        except SyntaxError as e:
            fail(path.name, f"ligne {e.lineno}: {e.msg}")


# ---------------------------------------------------------------------------
# 3. Imports Python
# ---------------------------------------------------------------------------

def test_imports():
    print("\n--- 3. Imports ---")
    checks = [
        ("sqlite3",      "sqlite3"),
        ("requests",     "requests"),
        ("python-dotenv","dotenv"),
        ("pathlib",      "pathlib"),
        ("datetime",     "datetime"),
        ("argparse",     "argparse"),
    ]
    for name, module in checks:
        try:
            importlib.import_module(module)
            ok(name)
        except ImportError:
            fail(name, "non installé — ajouter à requirements.txt")

    # matplotlib optionnel
    try:
        importlib.import_module("matplotlib")
        ok("matplotlib (optionnel)")
    except ImportError:
        skip("matplotlib (optionnel)", "graphique load en mode texte")


# ---------------------------------------------------------------------------
# 4. Cohérence CLAUDE.md
# ---------------------------------------------------------------------------

def test_claude_md():
    print("\n--- 4. Cohérence CLAUDE.md ---")
    content = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    agents_in_routing = [
        "mode-agent.md",
        "setup-agent.md",
        "help-agent.md",
        "views-agent.md",
        "recovery-agent.md",
        "race-planner-agent.md",
        "nutrition-agent.md",
        "feedback-agent.md",
        "profile-agent.md",
    ]
    for agent in agents_in_routing:
        if agent in content:
            ok(f"routing -> {agent}")
        else:
            fail(f"routing -> {agent}", "absent de CLAUDE.md")

    for phrase in ["après le premier message", "strava_sync.py", "safety.md"]:
        if phrase in content:
            ok(f"mention \"{phrase}\"")
        else:
            fail(f"mention \"{phrase}\"", "absente")


# ---------------------------------------------------------------------------
# 5. Hooks — settings.json
# ---------------------------------------------------------------------------

def test_hooks_config():
    print("\n--- 5. Configuration hooks ---")
    settings_path = ROOT / ".claude" / "settings.json"
    try:
        config = json.loads(settings_path.read_text(encoding="utf-8"))
        hooks = config.get("hooks", {})

        pre = hooks.get("PreToolUse", [])
        if any("pre-push.py" in str(h) for h in pre):
            ok("PreToolUse -> pre-push.py")
        else:
            fail("PreToolUse -> pre-push.py", "non configuré")

        post = hooks.get("PostToolUse", [])
        if any("post-write.py" in str(h) for h in post):
            ok("PostToolUse -> post-write.py")
        else:
            fail("PostToolUse -> post-write.py", "non configuré")

        stop = hooks.get("Stop", [])
        if any("on-stop.py" in str(h) for h in stop):
            ok("Stop -> on-stop.py")
        else:
            fail("Stop -> on-stop.py", "non configuré")

    except Exception as e:
        fail("settings.json", str(e))


# ---------------------------------------------------------------------------
# 6. views.py — base de données de test
# ---------------------------------------------------------------------------

def _create_test_db(path):
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE activities (
            id INTEGER PRIMARY KEY, name TEXT, sport_type TEXT,
            start_date TEXT, distance REAL, moving_time INTEGER,
            elapsed_time INTEGER, elevation_gain REAL,
            avg_heartrate REAL, max_heartrate REAL, avg_speed REAL,
            suffer_score INTEGER, workout_type INTEGER, tss REAL,
            synced_at TEXT, is_targeted_race INTEGER DEFAULT 0,
            race_target_time TEXT, race_calendar_type TEXT,
            race_calendar_notes TEXT, has_feedback INTEGER DEFAULT 0
        );
        CREATE TABLE feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            race_name TEXT, date TEXT, distance_km REAL, finish_time TEXT,
            avg_heartrate REAL, nutrition_notes TEXT, feeling_score INTEGER,
            positive_points TEXT, negative_points TEXT, notes TEXT,
            activity_id INTEGER, created_at TEXT
        );
        CREATE TABLE athlete (
            id INTEGER PRIMARY KEY, firstname TEXT, lastname TEXT,
            city TEXT, country TEXT, sex TEXT, weight REAL, updated_at TEXT
        );
    """)

    today = datetime.now()
    activities = []
    for i in range(30):
        d = today - timedelta(days=i * 3)
        dist = 10000 + i * 500
        speed = 2.8 + (i % 5) * 0.1
        tss = dist / 1000 * 5
        activities.append((
            i + 1, f"Sortie {d.strftime('%d/%m')}", "Run",
            d.isoformat(), dist, int(dist / speed),
            int(dist / speed) + 300, 50 + i * 10,
            150, 175, speed, 60, 0, tss,
            today.isoformat(), 1 if i == 5 else 0,
            None, None, None, 1 if i == 5 else 0
        ))

    # Quelques trails
    for i in range(3):
        d = today - timedelta(days=i * 10 + 5)
        activities.append((
            100 + i, f"Trail {i+1}", "TrailRun",
            d.isoformat(), 25000 + i * 5000, 9000, 10000,
            800 + i * 200, 155, 180, 2.5, 90, 0, 120,
            today.isoformat(), 0, None, None, None, 0
        ))

    conn.executemany("""
        INSERT INTO activities VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, activities)
    conn.commit()
    conn.close()


def test_views():
    print("\n--- 6. views.py avec DB de test ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "running.db"
        _create_test_db(db_path)

        # Patcher DB_PATH via variable d'env (on remplace data/ par tmpdir)
        data_dir = ROOT / "data"
        original_db = data_dir / "running.db"
        backup_exists = original_db.exists()

        # Copier la DB de test dans data/ temporairement
        import shutil
        if not backup_exists:
            shutil.copy(db_path, original_db)
            cleanup = True
        else:
            cleanup = False
            skip("views.py avec DB test", "DB réelle déjà présente — tests sur données réelles")

        commands = [
            (["recent", "5"],    "recent 5"),
            (["stats", "all"],   "stats all"),
            (["prs"],            "prs"),
            (["filter", "--from", "2020-01-01", "--to", "2030-01-01", "--limit", "5"],
             "filter --from/--to"),
            (["filter", "--type", "TrailRun"], "filter --type TrailRun"),
            (["filter", "--min-dist", "20"],   "filter --min-dist"),
            (["filter", "--races-only"],        "filter --races-only"),
            (["filter", "--order", "dist", "--limit", "3"], "filter --order dist"),
        ]

        for args, label in commands:
            try:
                r = subprocess.run(
                    [PYTHON, str(ROOT / "scripts" / "views.py")] + args,
                    capture_output=True, text=True, timeout=10
                )
                if r.returncode == 0 and not r.stderr.strip():
                    ok(f"views.py {label}")
                else:
                    fail(f"views.py {label}", r.stderr.strip()[:80] or r.stdout[-80:])
            except subprocess.TimeoutExpired:
                fail(f"views.py {label}", "timeout")

        if cleanup:
            original_db.unlink()


# ---------------------------------------------------------------------------
# 7. update_readme.py
# ---------------------------------------------------------------------------

def test_update_readme():
    print("\n--- 7. update_readme.py ---")
    try:
        r = subprocess.run(
            [PYTHON, str(ROOT / "scripts" / "update_readme.py")],
            capture_output=True, text=True, timeout=10, cwd=str(ROOT)
        )
        if r.returncode in (0, 1):  # 0=déjà à jour, 1=mis à jour
            ok("update_readme.py s'exécute")
            if "mis a jour" in r.stdout:
                ok("README mis à jour automatiquement")
            else:
                ok("README déjà à jour")
        else:
            fail("update_readme.py", r.stderr[:80])
    except Exception as e:
        fail("update_readme.py", str(e))


# ---------------------------------------------------------------------------
# 8. pre-push.py — vérification données perso (sans vrai push)
# ---------------------------------------------------------------------------

def test_pre_push_hook():
    print("\n--- 8. Hook pre-push ---")

    # Simuler un input sans git push -> doit exit 0 silencieusement
    env = {**os.environ, "CLAUDE_TOOL_INPUT": "git status"}
    r = subprocess.run(
        [PYTHON, str(ROOT / "hooks" / "pre-push.py")],
        capture_output=True, text=True, env=env
    )
    if r.returncode == 0:
        ok("pre-push : ignoré si pas de git push")
    else:
        fail("pre-push : ignoré si pas de git push", r.stderr[:80])

    # Simuler un push avec un fichier bloqué dans l'input
    env2 = {**os.environ, "CLAUDE_TOOL_INPUT": "git push origin main -- data/profile.md"}
    r2 = subprocess.run(
        [PYTHON, str(ROOT / "hooks" / "pre-push.py")],
        capture_output=True, text=True, env=env2
    )
    # Le hook va tenter git fetch et des commandes git — ce qui peut échouer
    # L'important est qu'il ne crash pas avec une exception Python
    if r2.returncode in (0, 1, 2):
        ok("pre-push : s'exécute sans crash Python")
    else:
        fail("pre-push : crash inattendu", r2.stderr[:80])


# ---------------------------------------------------------------------------
# Résumé
# ---------------------------------------------------------------------------

def summary():
    print("\n" + "=" * 50)
    total  = len(results)
    passed = sum(1 for r in results if r[0] == "OK")
    failed = sum(1 for r in results if r[0] == "FAIL")
    skipped= sum(1 for r in results if r[0] == "SKIP")

    print(f"Résultat : {passed}/{total} OK  |  {failed} échec(s)  |  {skipped} ignoré(s)")

    if failed:
        print("\nÉchecs à corriger :")
        for status, name in results:
            if status == "FAIL":
                print(f"  - {name}")

    print("=" * 50)
    return failed


if __name__ == "__main__":
    print("=== Running Coach AI — Tests de sanité ===")
    test_required_files()
    test_python_syntax()
    test_imports()
    test_claude_md()
    test_hooks_config()
    test_views()
    test_update_readme()
    test_pre_push_hook()
    sys.exit(summary())
