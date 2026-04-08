import re
from memory_store import load_memory, save_memory

MAX_FACT_LENGTH = 120


def normalize_fact(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" .,!?:;")
    return text


def looks_temporary(text: str) -> bool:
    lower = text.lower().strip()

    bad_starts = (
        "open ",
        "search ",
        "run ",
        "launch ",
        "start ",
        "what is ",
        "what's ",
        "tell me ",
        "can you ",
        "could you ",
        "please ",
        "weather ",
        "time ",
        "calc ",
        "calculate ",
        "help ",
        "who is ",
        "latest ",
        "news ",
        "clear ",
        "forget ",
        "remember ",
        "look up ",
        "find ",
        "show ",
        "list ",
        "open website ",
        "open site ",
        "open url ",
        "open link ",
    )

    if lower.startswith(bad_starts):
        return True

    if "?" in text:
        return True

    return False


def is_useful_fact(text: str) -> bool:
    lower = text.lower().strip()

    too_vague = {
        "i gave you an upgrade",
        "i upgraded you",
        "i changed you",
        "i fixed you",
        "i updated you",
        "i made you better",
        "i improved you",
        "i did an upgrade",
    }

    if lower in too_vague:
        return False

    useless_fragments = (
        "today",
        "right now",
        "just now",
        "maybe",
        "probably",
        "something",
        "anything",
    )

    if any(fragment == lower for fragment in useless_fragments):
        return False

    if len(text.strip()) < 4:
        return False

    return True


def extract_candidate_facts(user_input: str):
    raw = user_input.strip()
    lower = raw.lower()

    if not raw or looks_temporary(raw):
        return []

    facts = []

    patterns = [
        (
            r"\bmy name is ([a-zA-Z][a-zA-Z\s\-']{0,40})",
            lambda m: f"My name is {m.group(1).strip()}",
        ),
        (
            r"\bi am ([^.!?\n]{1,60})",
            lambda m: f"I am {m.group(1).strip()}",
        ),
        (
            r"\bi'm ([^.!?\n]{1,60})",
            lambda m: f"I'm {m.group(1).strip()}",
        ),
        (
            r"\bi am working on ([^.!?\n]{1,80})",
            lambda m: f"I am working on {m.group(1).strip()}",
        ),
        (
            r"\bi work on ([^.!?\n]{1,80})",
            lambda m: f"I work on {m.group(1).strip()}",
        ),
        (
            r"\bi use ([^.!?\n]{1,80})",
            lambda m: f"I use {m.group(1).strip()}",
        ),
        (
            r"\bi like ([^.!?\n]{1,80})",
            lambda m: f"I like {m.group(1).strip()}",
        ),
        (
            r"\bi love ([^.!?\n]{1,80})",
            lambda m: f"I love {m.group(1).strip()}",
        ),
        (
            r"\bi prefer ([^.!?\n]{1,80})",
            lambda m: f"I prefer {m.group(1).strip()}",
        ),
        (
            r"\bi live in ([^.!?\n]{1,80})",
            lambda m: f"I live in {m.group(1).strip()}",
        ),
        (
            r"\bi live at ([^.!?\n]{1,80})",
            lambda m: f"I live at {m.group(1).strip()}",
        ),
        (
            r"\bmy favorite ([^.!?\n]{1,40}) is ([^.!?\n]{1,60})",
            lambda m: f"My favorite {m.group(1).strip()} is {m.group(2).strip()}",
        ),
        (
            r"\bmy favourite ([^.!?\n]{1,40}) is ([^.!?\n]{1,60})",
            lambda m: f"My favourite {m.group(1).strip()} is {m.group(2).strip()}",
        ),
        (
            r"\bmy pc has ([^.!?\n]{1,80})",
            lambda m: f"My PC has {m.group(1).strip()}",
        ),
        (
            r"\bmy phone is ([^.!?\n]{1,80})",
            lambda m: f"My phone is {m.group(1).strip()}",
        ),
    ]

    for pattern, formatter in patterns:
        m = re.search(pattern, raw, re.IGNORECASE)
        if m:
            fact = normalize_fact(formatter(m))
            if 0 < len(fact) <= MAX_FACT_LENGTH and is_useful_fact(fact):
                facts.append(fact)

    if "always use multan" in lower or "default weather location is multan" in lower:
        facts.append("Default weather location is Multan, Pakistan")

    if "youtube_api.py was removed" in lower or "i removed youtube_api.py" in lower:
        facts.append("youtube_api.py was removed from the project")

    seen = set()
    final = []

    for fact in facts:
        key = fact.lower()
        if key not in seen:
            seen.add(key)
            final.append(fact)

    return final


def auto_remember(user_input: str):
    facts = extract_candidate_facts(user_input)
    if not facts:
        return []

    memory = load_memory()
    existing = {f.lower() for f in memory.get("facts", [])}
    added = []

    for fact in facts:
        if fact.lower() not in existing:
            memory["facts"].append(fact)
            existing.add(fact.lower())
            added.append(fact)

    if added:
        save_memory(memory)

    return added