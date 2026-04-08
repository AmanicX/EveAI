import re
import time
import requests
import json
from personality_manager import load_personality, get_eve_profile
from config import GROQ_API_KEY, GROQ_API_URL, MODEL, SYSTEM_PROMPT, FAST_MODEL
from memory_store import format_memory_block
from chat_manager import load_history, append_history, load_config

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}

THINK_INJECTION = """
Reason through this before answering:
- What exactly is being asked?
- Is the user asking for a summary or full detail?
- If search results provided, extract the actual useful facts
- What is the most accurate concise answer?

Write reasoning in <think> tags, then give the final answer.

<think>
reasoning here
</think>

Final answer here.
"""


def _call_groq(messages: list, model: str = None, retries: int = 3) -> str:
    payload = {
        "model": model or MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    for attempt in range(retries):
        try:
            response = requests.post(
                GROQ_API_URL, headers=HEADERS, json=payload, timeout=60
            )

            if response.status_code == 429:
                if payload["model"] != FAST_MODEL:
                    payload["model"] = FAST_MODEL
                    time.sleep(1)
                    continue

                time.sleep(2 ** attempt)
                continue

            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()

        except Exception:
            time.sleep(2 ** attempt)

    return "Request failed after retries."


# 🔥 NEW
def get_personality_profile(chat_id):
    config = load_config(chat_id)
    mode = config.get("personality", "eve")

    success, error, profile = load_personality(mode)

    if not success:
        return get_eve_profile()

    return profile


# 🔥 NEW
def get_active_model(chat_id, fallback_model):
    config = load_config(chat_id)
    profile = get_personality_profile(chat_id)

    # Priority:
    # 1. Manual override (chat config)
    # 2. Personality model
    # 3. Classifier fallback
    return config.get("model") or profile.get("model") or fallback_model


def build_messages(chat_id, user_input, system_prompt=None, extra_system_blocks=None):
    profile = get_personality_profile(chat_id)
    active_prompt = system_prompt or profile["system_prompt"]

    messages = [
        {"role": "system", "content": active_prompt},
        {
            "role": "system",
            "content": "User's saved memory:\n\n" + format_memory_block(),
        },
    ]

    if extra_system_blocks:
        for block in extra_system_blocks:
            messages.append({"role": "system", "content": block})

    messages.extend(load_history(chat_id))

    messages.append({"role": "user", "content": user_input})
    return messages


def parse_think_block(raw: str):
    match = re.search(r"<think>(.*?)</think>", raw, re.DOTALL | re.IGNORECASE)
    if not match:
        return "", raw.strip()
    thinking = match.group(1).strip()
    after = raw[match.end():].strip()
    return thinking, after if after else raw.strip()


def chat(chat_id, user_input, model=None):
    model = get_active_model(chat_id, model)

    messages = build_messages(chat_id, user_input)
    content = _call_groq(messages, model=model)

    append_history(chat_id, "user", user_input)
    append_history(chat_id, "assistant", content)

    return content


def think_then_chat(chat_id, user_input, model=None, expand_mode=False):
    model = get_active_model(chat_id, model)

    think_blocks = [THINK_INJECTION.strip()]

    if expand_mode:
        think_blocks.append(
            "Give a full detailed explanation with examples and depth."
        )

    messages = build_messages(
        chat_id,
        user_input,
        extra_system_blocks=think_blocks,
    )

    raw = _call_groq(messages, model=model)

    thinking, final_answer = parse_think_block(raw)

    append_history(chat_id, "user", user_input)
    append_history(chat_id, "assistant", final_answer)

    return thinking, final_answer
