import re
import time
import requests
from config import GROQ_API_KEY, GROQ_API_URL, MODEL, SYSTEM_PROMPT, FAST_MODEL
from memory_store import format_memory_block
from history_store import load_history, append_history

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
        "model":       model or MODEL,
        "messages":    messages,
        "temperature": 0.7,
        "max_tokens":  1024,
    }

    for attempt in range(retries):
        try:
            response = requests.post(
                GROQ_API_URL, headers=HEADERS, json=payload, timeout=60
            )

            if response.status_code == 429:
                if payload["model"] != FAST_MODEL:
                    print(f"\r[{payload['model']} rate limited — switching to fast model]", end="\r")
                    payload["model"] = FAST_MODEL
                    time.sleep(1)
                    continue

                wait = 2 ** attempt
                print(f"\r[Rate limited — waiting {wait}s]", end="\r")
                time.sleep(wait)
                continue

            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()

        except requests.exceptions.HTTPError:
            if attempt == retries - 1:
                return "Request failed after retries. Try again in a moment."
            time.sleep(2 ** attempt)

        except Exception as e:
            return f"Groq request failed: {e}"

    return "Request failed after retries. Try again in a moment."


def build_messages(user_input, system_prompt=None, extra_system_blocks=None, use_history=True):
    active_prompt = (system_prompt or SYSTEM_PROMPT).strip()

    messages = [
        {"role": "system", "content": active_prompt},
        {
            "role": "system",
            "content": "User's saved memory (use only when relevant):\n\n" + format_memory_block(),
        },
    ]

    if extra_system_blocks:
        for block in extra_system_blocks:
            messages.append({"role": "system", "content": block})

    if use_history:
        messages.extend(load_history())

    messages.append({"role": "user", "content": user_input})
    return messages


def parse_think_block(raw: str):
    match = re.search(r"<think>(.*?)</think>", raw, re.DOTALL | re.IGNORECASE)
    if not match:
        return "", raw.strip()
    thinking = match.group(1).strip()
    after    = raw[match.end():].strip()
    return thinking, after if after else raw.strip()


def chat(user_input, model=None, system_prompt=None, extra_system_blocks=None,
         use_history=True, record_history=True):

    messages = build_messages(
        user_input,
        system_prompt=system_prompt,
        extra_system_blocks=extra_system_blocks,
        use_history=use_history,
    )
    content = _call_groq(messages, model=model)

    if not content:
        content = "I could not generate a response."

    if record_history:
        append_history("user", user_input)
        append_history("assistant", content)

    return content


def think_then_chat(user_input, model=None, system_prompt=None,
                    extra_system_blocks=None, search_block=None,
                    expand_mode=False):

    think_blocks = [THINK_INJECTION.strip()]

    if expand_mode:
        think_blocks.append(
            "The user wants a FULL detailed explanation on the previous topic. "
            "Go deep — full breakdown, examples, sub-topics, comparisons. "
            "Do not hold back detail this time."
        )

    if search_block:
        think_blocks.append(
            "SEARCH RESULTS — extract the actual facts and answer directly.\n"
            "RULES:\n"
            "- Never say 'based on search results' or 'according to'\n"
            "- Never list URLs, source names, or links\n"
            "- Never add disclaimers or recommend visiting websites\n"
            "- Just answer like you already knew this\n"
            "- Give specific facts, names, numbers — not vague summaries\n\n"
            + search_block
        )

    if extra_system_blocks:
        think_blocks.extend(extra_system_blocks)

    messages = build_messages(
        user_input,
        system_prompt=system_prompt,
        extra_system_blocks=think_blocks,
        use_history=True,
    )

    raw = _call_groq(messages, model=model)

    if not raw:
        return "", "I could not generate a response."

    thinking, final_answer = parse_think_block(raw)

    append_history("user", user_input)
    append_history("assistant", final_answer or raw)

    return thinking, final_answer or raw