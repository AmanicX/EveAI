import os
import json
import uuid

BASE_DIR = "data/chats"


def _ensure_base():
    os.makedirs(BASE_DIR, exist_ok=True)


def _chat_path(chat_id):
    return os.path.join(BASE_DIR, chat_id)


def _config_path(chat_id):
    return os.path.join(_chat_path(chat_id), "config.json")


def _history_path(chat_id):
    return os.path.join(_chat_path(chat_id), "history.json")


def create_chat(name="New Chat"):
    _ensure_base()

    chat_id = str(uuid.uuid4())[:8]
    path = _chat_path(chat_id)
    os.makedirs(path, exist_ok=True)

    config = {
        "name": name,
        "personality": "eve",   # 🔥 default personality
        "model": None           # None = auto (FAST/SMART)
    }

    with open(_config_path(chat_id), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    with open(_history_path(chat_id), "w", encoding="utf-8") as f:
        json.dump([], f)

    return chat_id


def list_chats():
    _ensure_base()
    chats = []

    for chat_id in os.listdir(BASE_DIR):
        config_file = _config_path(chat_id)
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            chats.append({
                "id": chat_id,
                "name": config.get("name", "Chat"),
                "personality": config.get("personality", "eve")
            })

    return chats


def load_config(chat_id):
    with open(_config_path(chat_id), "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(chat_id, config):
    with open(_config_path(chat_id), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


# 🔥 NEW: switch personality
def set_personality(chat_id, mode_name):
    config = load_config(chat_id)
    config["personality"] = mode_name.lower()
    save_config(chat_id, config)


# 🔥 NEW: set model manually
def set_model(chat_id, model_name):
    config = load_config(chat_id)
    config["model"] = model_name
    save_config(chat_id, config)


def load_history(chat_id):
    path = _history_path(chat_id)
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def append_history(chat_id, role, content):
    history = load_history(chat_id)
    history.append({"role": role, "content": content})

    with open(_history_path(chat_id), "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def clear_history(chat_id):
    with open(_history_path(chat_id), "w", encoding="utf-8") as f:
        json.dump([], f)
