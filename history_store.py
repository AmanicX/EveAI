import json
import os
from config import HISTORY_FILE, MAX_HISTORY_MESSAGES

CURRENT_HISTORY_FILE = HISTORY_FILE


def set_history_file(path):
    global CURRENT_HISTORY_FILE
    CURRENT_HISTORY_FILE = path


def get_history_file():
    return CURRENT_HISTORY_FILE


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_history():
    return _load_json(CURRENT_HISTORY_FILE, [])


def save_history(history):
    _save_json(CURRENT_HISTORY_FILE, history)


def append_history(role, content):
    history = load_history()
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY_MESSAGES:
        history = history[-MAX_HISTORY_MESSAGES:]
    save_history(history)


def clear_history():
    save_history([])