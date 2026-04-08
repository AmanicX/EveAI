import json
import requests
from config import GROQ_API_KEY, GROQ_API_URL, FAST_MODEL

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}

ROUTER_PROMPT = """
Classify the user's message into exactly one intent. Be precise.

Valid intents and when to use them:
- remember      → user wants to save a fact ("remember that...", "remember this:")
- forget        → user wants to remove a memory
- memories      → user wants to see saved memories
- clear         → user wants to clear chat history
- time          → user asks for the current time
- calc          → user wants math calculated
- open_site     → user wants to open a website or URL
- run_app       → user wants to open an application on their PC
- search        → user explicitly asks to search something
- weather       → user asks about weather
- index_path    → user wants to scan/index a folder
- find_file     → user wants to find a file on their PC
- find_folder   → user wants to find a folder on their PC
- list_folder_contents → user wants to see what is inside a folder
- read_file     → user wants to read the content of a file
- delete_path   → user wants to delete a file or folder
- change_mode   → user wants to switch AI personality
- create_doc    → user wants to create a document from the conversation
- expand        → user wants more detail on the previous topic ("tell me more", "go deeper", "expand")
- confirm_yes   → user is confirming something (yes, sure, do it)
- confirm_no    → user is cancelling something (no, cancel, never mind)
- chat          → anything else — general conversation or questions

Return ONLY valid JSON:
{"intent": "...", "value": "..."}

Value rules:
- empty string for: clear, time, chat, confirm_yes, confirm_no, memories, expand
- math expression for: calc
- city/country or empty for: weather
- URL or domain for: open_site
- app name for: run_app
- search query for: search
- the fact text for: remember, forget
- folder path for: index_path
- file name or description for: find_file, read_file, delete_path
- folder name or description for: find_folder, list_folder_contents
- mode name for: change_mode
- topic or empty for: create_doc

Examples:
{"intent":"run_app","value":"steam"}
{"intent":"calc","value":"25*17"}
{"intent":"weather","value":"Multan"}
{"intent":"expand","value":""}
{"intent":"change_mode","value":"ava"}
{"intent":"chat","value":""}
"""


def ai_extract_intent(user_input: str):
    payload = {
        "model": FAST_MODEL,
        "messages": [
            {"role": "system", "content": ROUTER_PROMPT.strip()},
            {"role": "user", "content": user_input},
        ],
        "temperature": 0,
        "max_tokens": 64,
    }

    try:
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"].strip()

        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()

        parsed = json.loads(raw)
        intent = parsed.get("intent", "chat")
        value  = parsed.get("value", "")

        valid_intents = {
            "remember", "forget", "memories", "clear", "time", "calc",
            "open_site", "run_app", "search", "weather",
            "index_path", "find_file", "find_folder", "list_folder_contents",
            "read_file", "delete_path", "change_mode", "create_doc",
            "confirm_yes", "confirm_no", "chat",
        }

        if intent not in valid_intents:
            return {"intent": "chat", "value": ""}

        return {"intent": intent, "value": str(value)}

    except Exception:
        return {"intent": "chat", "value": ""}