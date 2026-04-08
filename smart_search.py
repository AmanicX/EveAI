import json
import requests
from config import GROQ_API_KEY, GROQ_API_URL, FAST_MODEL
from web_search import search_web, format_search_results

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}

SEARCH_DECISION_PROMPT = """You are a search decision engine.

Decide if the user's message needs a live internet search.

Search IS needed for:
- Current news, recent events, latest updates
- Real-time prices, scores, releases
- Specific people, companies, recent news
- Anything with: latest, current, right now, today, who won, is X still

Search is NOT needed for:
- Concepts, explanations, definitions
- Math, coding, creative writing
- Personal conversation, opinions
- Historical facts
- Weather, time, calculator (Eve has dedicated tools)

Reply ONLY with valid JSON, no markdown:
{"should_search": true, "query": "short optimized search query"}
or
{"should_search": false, "query": ""}
"""


def decide_search(user_input: str) -> dict:
    payload = {
        "model": FAST_MODEL,
        "messages": [
            {"role": "system", "content": SEARCH_DECISION_PROMPT.strip()},
            {"role": "user", "content": user_input},
        ],
        "temperature": 0,
        "max_tokens": 64,
    }
    try:
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload, timeout=20)
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"].strip()

        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()

        parsed = json.loads(raw)
        return {
            "should_search": bool(parsed.get("should_search", False)),
            "query": str(parsed.get("query", "")).strip(),
        }
    except Exception:
        return {"should_search": False, "query": ""}


def auto_search_if_needed(user_input: str):
    decision = decide_search(user_input)

    if not decision["should_search"]:
        return None, ""

    query = decision["query"] or user_input
    ok, msg, results = search_web(query, max_results=5)

    if not ok or not results:
        return None, query

    return format_search_results(results), query