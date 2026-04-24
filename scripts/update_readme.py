"""
Met à jour les sections dynamiques du README.md avant chaque push :
- Arborescence du projet (<!-- STRUCTURE_START/END -->)
- Table des agents      (<!-- AGENTS_TABLE_START/END -->)

Retourne exit code 1 si README a été modifié (le hook pre-push bloque alors
et demande de commiter la mise à jour).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Agents connus et leur déclencheur — dans l'ordre d'affichage
# ---------------------------------------------------------------------------

AGENTS = [
    ("mode-agent.md",        'Switch de mode ("mode dev", "mode utilisateur"...)'),
    ("setup-agent.md",       '"setup", "je suis nouveau", réinitialisation'),
    ("help-agent.md",        '"aide", "help", "que peux-tu faire"'),
    ("views-agent.md",       '"montre", "affiche", "stats", "graphique", "calendrier"'),
    ("recovery-agent.md",    "Surcharge, repos, récupération"),
    ("race-planner-agent.md","Objectifs, stratégie de course"),
    ("nutrition-agent.md",   "Nutrition le jour de course"),
    ("feedback-agent.md",    "Analyse d'un feedback post-course"),
    ("profile-agent.md",     "Mise à jour profil, sync Strava"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def list_dir(path, glob, indent="│   ", last_prefix="└── ", mid_prefix="├── "):
    files = sorted(Path(path).glob(glob))
    lines = []
    for i, f in enumerate(files):
        prefix = last_prefix if i == len(files) - 1 else mid_prefix
        lines.append(f"{indent}{prefix}{f.name}")
    return lines


def generate_structure():
    lines = ["```", "RunningProject/"]

    def section(label, path, glob, last=False):
        prefix = "└── " if last else "├── "
        indent = "    " if last else "│   "
        lines.append(f"{prefix}{label}/")
        files = sorted(Path(path).glob(glob))
        for i, f in enumerate(files):
            p = "└── " if i == len(files) - 1 else "├── "
            lines.append(f"{indent}{p}{f.name}")

    # Fixed top-level files
    for fname in [".env.example", ".gitignore / .gitattributes", "requirements.txt", "CLAUDE.md"]:
        lines.append(f"├── {fname}")

    section("agents", ROOT / "agents", "*.md")
    section("rules",  ROOT / "rules",  "*.md")
    section("scripts",ROOT / "scripts","*.py")
    section("hooks",  ROOT / "hooks",  "*.py")
    section("dev",    ROOT / "dev",    "*.md")

    # data/ (fixed)
    lines.append("└── data/")
    lines += [
        "    ├── .gitkeep",
        "    ├── calendar.example.md",
        "    └── feedbacks.example.md",
    ]
    lines.append("```")
    return "\n".join(lines)


def generate_agents_table():
    rows = ["| Agent | Déclenché par |", "|---|---|"]
    for filename, trigger in AGENTS:
        if (ROOT / "agents" / filename).exists():
            rows.append(f"| `agents/{filename}` | {trigger} |")
    return "\n".join(rows)


def replace_section(content, marker, new_body):
    start_tag = f"<!-- {marker}_START -->"
    end_tag   = f"<!-- {marker}_END -->"
    pattern   = re.compile(
        re.escape(start_tag) + r".*?" + re.escape(end_tag),
        re.DOTALL,
    )
    replacement = f"{start_tag}\n{new_body}\n{end_tag}"
    return pattern.sub(replacement, content)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    readme = ROOT / "README.md"
    if not readme.exists():
        print("README.md introuvable.")
        return 0

    original = readme.read_text(encoding="utf-8")
    updated  = original
    updated  = replace_section(updated, "STRUCTURE",     generate_structure())
    updated  = replace_section(updated, "AGENTS_TABLE",  generate_agents_table())

    if updated != original:
        readme.write_text(updated, encoding="utf-8")
        print("README.md mis a jour automatiquement.")
        print("Commitez README.md avant de pusher :")
        print("  git add README.md && git commit -m \"docs: mise a jour README\"")
        return 1

    print("README.md deja a jour.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
