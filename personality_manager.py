import json
import os
from config import SYSTEM_PROMPT, MODEL, MEMORY_FILE, HISTORY_FILE

PERSONALITIES_DIR = "personalities"


def get_eve_profile():
    return {
        "name": "Eve",
        "mode_id": "eve",
        "model": MODEL,
        "voice": "en-IE-EmilyNeural",
        "memory_file": MEMORY_FILE,
        "history_file": HISTORY_FILE,
        "system_prompt": SYSTEM_PROMPT,
    }


def load_personality(mode_name):
    path = os.path.join(PERSONALITIES_DIR, f"{mode_name}.json")

    if not os.path.exists(path):
        return False, f"I couldn't find a personality called {mode_name}.", None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        base = get_eve_profile()
        profile = {
            "name": data.get("name", mode_name.title()),
            "mode_id": data.get("mode_id", mode_name.lower()),
            "model": data.get("model", base["model"]),
            "voice": data.get("voice", base["voice"]),
            "memory_file": data.get("memory_file", f"{mode_name.lower()}_memory.json"),
            "history_file": data.get("history_file", f"{mode_name.lower()}_history.json"),
            "system_prompt": data.get("system_prompt", base["system_prompt"]),
        }

        return True, "", profile
    except Exception as e:
        return False, f"Failed to load personality: {e}", None