import json
import os

CURRENT_MEMORY_FILE = "eve_memory.json"


def set_memory_file(path):
    global CURRENT_MEMORY_FILE
    CURRENT_MEMORY_FILE = path


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


def load_memory():
    return _load_json(CURRENT_MEMORY_FILE, {"facts": []})


def save_memory(memory):
    _save_json(CURRENT_MEMORY_FILE, memory)


def add_memory_fact(text):
    memory = load_memory()
    fact = text.strip()
    if not fact:
        return False, "Nothing to remember."
    if fact not in memory["facts"]:
        memory["facts"].append(fact)
        save_memory(memory)
        return True, f"Remembered: {fact}"
    return True, f"I already remembered that: {fact}"


def forget_memory_fact(text):
    memory = load_memory()
    fact = text.strip()
    if fact in memory["facts"]:
        memory["facts"].remove(fact)
        save_memory(memory)
        return True, f"Forgot: {fact}"
    return False, f"I couldn't find that memory: {fact}"


def format_memory_block():
    memory = load_memory()
    facts = memory.get("facts", [])
    if not facts:
        return "No saved long-term memory."
    lines = [f"{i+1}. {fact}" for i, fact in enumerate(facts)]
    return "Saved long-term memory:\n" + "\n".join(lines)