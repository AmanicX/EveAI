import json
import requests
from config import GROQ_API_KEY, GROQ_API_URL, FAST_MODEL, SMART_MODEL

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}

CLASSIFIER_PROMPT = """You are a request classifier for a personal AI assistant.

Decide THREE things about the user's message:

1. complexity — "simple" or "complex"
   simple: greetings, math, small talk, time, weather, memory, open apps, short factual questions
   complex: coding, deep explanations, writing, research, multi-step reasoning, current events analysis

2. should_search — true or false
   true: anything needing live data — news, prices, scores, trends, "right now", "today", "latest", current events
   false: general knowledge, math, coding, personal chat, weather (has own tool), time, historical facts

3. query — if should_search is true, write a sharp targeted search query
   - Always add specific context: dates, platforms, locations
   - "what is trending" → "trending topics internet today April 2026 Twitter Reddit"
   - "usa iran situation" → "USA Iran conflict latest news April 2026"
   - "bitcoin price" → "bitcoin price today April 2026"
   - "latest pakistan news" → "Pakistan news today April 2026"
   - Never write vague queries like "trending topics" alone

Reply ONLY with valid JSON, no markdown:
{"complexity": "simple", "should_search": false, "query": ""}
"""


def classify_request(user_input: str) -> dict:
    defaults = {
        "complexity":    "simple",
        "should_search": False,
        "query":         "",
        "model":         FAST_MODEL,
        "label":         FAST_MODEL,
    }

    payload = {
        "model": FAST_MODEL,
        "messages": [
            {"role": "system", "content": CLASSIFIER_PROMPT.strip()},
            {"role": "user",   "content": user_input},
        ],
        "temperature": 0,
        "max_tokens":  64,
    }

    try:
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload, timeout=20)
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"].strip()

        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()

        parsed        = json.loads(raw)
        complexity    = parsed.get("complexity", "simple").lower()
        should_search = bool(parsed.get("should_search", False))
        query         = str(parsed.get("query", "")).strip()

        if complexity not in ("simple", "complex"):
            complexity = "simple"

        model = SMART_MODEL if complexity == "complex" else FAST_MODEL

        return {
            "complexity":    complexity,
            "should_search": should_search,
            "query":         query,
            "model":         model,
            "label":         model,
        }

    except Exception:
        return defaults