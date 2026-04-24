"""
Hook PostToolUse (Write) — appelé après chaque écriture de fichier par Claude.
Affiche une confirmation horodatée si le fichier écrit est dans data/.
"""
import os
from datetime import datetime

tool_input = os.environ.get("CLAUDE_TOOL_INPUT", "")

if "data/" in tool_input or "data\\" in tool_input:
    ts = datetime.now().strftime("%H:%M:%S")
    # Extraire le nom du fichier depuis l'input JSON
    import json
    try:
        data = json.loads(tool_input)
        path = data.get("file_path", "")
        filename = path.split("/")[-1].split("\\")[-1]
        print(f"[RunningCoach] {ts} — {filename} sauvegarde.")
    except Exception:
        print(f"[RunningCoach] {ts} — Donnee sauvegardee.")
