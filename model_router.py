import json
import requests
from config import GROQ_API_KEY, GROQ_API_URL, FAST_MODEL, SMART_MODEL

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}

COMPLEXITY_PROMPT = """Classify the user's message as simple or complex.

Simple: greetings, basic facts, math, definitions, small talk, memory operations,
        open apps, check time, weather, calculator, short questions

Complex: multi-step reasoning, code generation, debugging, writing documents,
         deep explanations, research, analysis, comparisons

Reply ONLY with valid JSON:
{"complexity": "simple"} or {"complexity": "complex"}
"""


def pick_model(user_input: str) -> tuple[str, str]:
    payload = {
        "model": FAST_MODEL,
        "messages": [
            {"role": "system", "content": COMPLEXITY_PROMPT.strip()},
            {"role": "user", "content": user_input},
        ],
        "temperature": 0,
        "max_tokens": 16,
    }
    try:
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload, timeout=20)
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"].strip()

        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()

        parsed    = json.loads(raw)
        complexity = parsed.get("complexity", "simple").lower()

        if complexity not in ("simple", "complex"):
            complexity = "simple"

    except Exception:
        complexity = "simple"

    model = SMART_MODEL if complexity == "complex" else FAST_MODEL
    return model, complexity