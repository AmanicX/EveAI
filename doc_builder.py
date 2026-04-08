import re
from typing import List, Dict, Tuple
from client import chat

DEFAULT_DOC_SYSTEM_PROMPT = """
You are a professional document writer.

Your job: take the conversation excerpt below and turn it into a clean, polished document.

Rules:
- Stay strictly within the content of the conversation — do not invent anything
- Output plain text only
- First line must be exactly: TITLE: <your document title>
- Then a blank line
- Use section headings as plain lines ending with a colon, like: Overview:
- Use numbered lists for options or steps
- Use "- " bullet points for supporting details
- Keep paragraphs short and professional
- No markdown, no bold, no headers with # symbols
"""


def tokenize(text: str):
    words = re.findall(r"[a-zA-Z0-9]+", (text or "").lower())
    stop  = {
        "the","a","an","and","or","to","of","for","is","are","in","on",
        "that","this","it","we","i","you","me","my","our","your","as",
        "from","with","make","document","doc","save","create","turn","into",
    }
    return [w for w in words if w not in stop]


def score_message(content: str, keywords: List[str]) -> int:
    text  = (content or "").lower()
    return sum(3 for kw in keywords if kw in text)


def history_to_blocks(history: List[Dict[str, str]]) -> List[str]:
    blocks = []
    for item in history:
        role    = item.get("role", "unknown").upper()
        content = item.get("content", "").strip()
        if content:
            blocks.append(f"{role}: {content}")
    return blocks


def extract_relevant_history_block(
    history: List[Dict[str, str]],
    user_request: str,
    window_size: int = 16,
) -> Tuple[str, List[Dict[str, str]]]:

    if not history:
        return "", []

    keywords   = tokenize(user_request)
    best_index = None
    best_score = -1

    for i, item in enumerate(history):
        score = score_message(item.get("content", ""), keywords)
        if score > best_score:
            best_score = score
            best_index = i

    if best_index is None or best_score <= 0:
        selected = history[-window_size:]
    else:
        start    = max(0, best_index - window_size // 2)
        end      = min(len(history), best_index + window_size // 2 + 1)
        selected = history[start:end]

    return "\n".join(history_to_blocks(selected)), selected


def extract_title_from_output(text: str) -> str:
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("TITLE:"):
            title = stripped[6:].strip()
            return title or "Eve Document"
    return "Eve Document"


def remove_title_line(text: str) -> str:
    lines   = (text or "").splitlines()
    cleaned = []
    removed = False
    for line in lines:
        if not removed and line.strip().upper().startswith("TITLE:"):
            removed = True
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def generate_document_text(
    raw_block:     str,
    title_hint:    str = "",
    model:         str = None,
    system_prompt: str = None,
) -> str:

    prompt = f"""Create a polished document from this conversation.

Title hint: {title_hint or "derive a good title from the content"}

Conversation:
{raw_block}
""".strip()

    return chat(
        prompt,
        model=model,
        system_prompt=system_prompt or DEFAULT_DOC_SYSTEM_PROMPT,
        use_history=False,
        record_history=False,
    )