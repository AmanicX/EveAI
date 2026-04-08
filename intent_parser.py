import re


YES_WORDS = {
    "yes", "y", "confirm", "do it", "delete it", "go ahead", "proceed", "sure", "okay", "ok"
}

NO_WORDS = {
    "no", "n", "cancel", "stop", "don't", "do not", "never mind", "nevermind"
}

EXPAND_WORDS = {
    "more", "tell me more", "expand", "elaborate", "give me more",
    "go deeper", "full detail", "explain fully", "more detail",
    "more info", "more information", "give full", "give more detail",
    "continue", "keep going", "and?", "go on",
}


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def extract_after_prefix(raw: str, lower: str, prefixes):
    for prefix in prefixes:
        if lower.startswith(prefix):
            return raw[len(prefix):].strip(' "\'')
    return None


def extract_weather_location(text: str):
    raw = normalize_spaces(text)
    lower = raw.lower()

    patterns = [
        r"^what(?:'s| is) the weather in\s+(.+)$",
        r"^weather in\s+(.+)$",
        r"^tell me the weather in\s+(.+)$",
        r"^how is the weather in\s+(.+)$",
        r"^forecast for\s+(.+)$",
        r"^what(?:'s| is) the forecast for\s+(.+)$",
        r"^temperature in\s+(.+)$",
        r"^what(?:'s| is) the temperature in\s+(.+)$",
    ]

    for pattern in patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            return raw[m.start(1):m.end(1)].strip(" ?,.")
    return None


def looks_like_path(text: str) -> bool:
    text = text.strip()
    return (":\\" in text) or text.startswith("\\\\")


def is_math_expression(text: str) -> bool:
    return bool(re.fullmatch(r"[0-9\.\+\-\*\/%\(\)\s]+", text.strip()))


def extract_intent(text: str):
    raw = normalize_spaces(text)
    lower = raw.lower()

    if lower in EXPAND_WORDS or any(lower.startswith(p) for p in [
        "tell me more", "give me more", "more about", "expand on",
        "more detail", "more info", "go deeper", "explain fully",
    ]):
        return {"intent": "expand", "value": ""}

    if not lower:
        return {"intent": "none", "value": ""}

    if lower in YES_WORDS:
        return {"intent": "confirm_yes", "value": ""}

    if lower in NO_WORDS:
        return {"intent": "confirm_no", "value": ""}

    doc_patterns = [
        r"^make a document(?: of| from)?\s+(.+)$",
        r"^create a document(?: of| from)?\s+(.+)$",
        r"^make a google doc(?: of| from)?\s+(.+)$",
        r"^create a google doc(?: of| from)?\s+(.+)$",
        r"^save this as a google doc$",
        r"^turn this into a document$",
        r"^turn this into a google doc$",
        r"^save this as a document$",
        r"^export this to google docs$",
    ]
    for pattern in doc_patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            if m.groups():
                value = raw[m.start(1):m.end(1)].strip(" ?,.")
            else:
                value = ""
            return {"intent": "create_doc", "value": value}

    mode_patterns = [
        r"^change mode to\s+(.+)$",
        r"^switch mode to\s+(.+)$",
        r"^switch to\s+(.+)$",
        r"^use\s+(.+?)\s+mode$",
        r"^go back to\s+(.+)$",
        r"^change to\s+(.+)$",
    ]
    for pattern in mode_patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            value = raw[m.start(1):m.end(1)].strip(" ?,.")
            return {"intent": "change_mode", "value": value}

    index_prefixes = [
        "scan folder ",
        "scan path ",
        "index folder ",
        "index path ",
        "search my computer in ",
        "search my files in ",
        "scan my files in ",
        "remember files in ",
    ]
    indexed_path = extract_after_prefix(raw, lower, index_prefixes)
    if indexed_path:
        return {"intent": "index_path", "value": indexed_path}

    read_prefixes = [
        "read file ",
        "read this file ",
        "open file ",
        "show file ",
    ]
    read_target = extract_after_prefix(raw, lower, read_prefixes)
    if read_target and looks_like_path(read_target):
        return {"intent": "read_file", "value": read_target}

    delete_prefixes = [
        "delete path ",
        "delete file ",
        "delete folder ",
        "remove path ",
        "remove file ",
        "remove folder ",
    ]
    delete_target = extract_after_prefix(raw, lower, delete_prefixes)
    if delete_target and looks_like_path(delete_target):
        return {"intent": "delete_path", "value": delete_target}

    folder_contents_patterns = [
        r"^what is inside the folder\s+(.+)$",
        r"^what is inside folder\s+(.+)$",
        r"^show me what is inside the folder\s+(.+)$",
        r"^show me what is inside folder\s+(.+)$",
        r"^show contents of the folder\s+(.+)$",
        r"^show contents of folder\s+(.+)$",
        r"^list contents of the folder\s+(.+)$",
        r"^list contents of folder\s+(.+)$",
    ]
    for pattern in folder_contents_patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            value = raw[m.start(1):m.end(1)].strip(" ?,.")
            return {"intent": "list_folder_contents", "value": value}

    if lower in {
        "what's the weather",
        "what is the weather",
        "weather",
        "tell me the weather",
        "forecast",
        "what's the forecast",
        "what is the forecast",
        "temperature",
    }:
        return {"intent": "weather", "value": ""}

    weather_location = extract_weather_location(raw)
    if weather_location is not None:
        return {"intent": "weather", "value": weather_location}

    if lower in {"what do you remember", "show memories", "show memory", "list memories", "memories"}:
        return {"intent": "memories", "value": ""}

    if lower in {"clear chat", "clear history", "reset chat", "wipe chat"}:
        return {"intent": "clear", "value": ""}

    if lower in {"what time is it", "time", "tell me the time", "current time"}:
        return {"intent": "time", "value": ""}

    remember_patterns = [
        r"^remember this[:\s]+(.+)$",
        r"^remember that[:\s]+(.+)$",
        r"^remember[:\s]+(.+)$",
        r"^hey remember this[:\s]+(.+)$",
        r"^please remember[:\s]+(.+)$",
    ]
    for pattern in remember_patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            return {"intent": "remember", "value": raw[m.start(1):m.end(1)].strip()}

    forget_patterns = [
        r"^forget this[:\s]+(.+)$",
        r"^forget that[:\s]+(.+)$",
        r"^forget[:\s]+(.+)$",
        r"^remove memory[:\s]+(.+)$",
    ]
    for pattern in forget_patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            return {"intent": "forget", "value": raw[m.start(1):m.end(1)].strip()}

    explicit_file_patterns = [
        r"^where is the file\s+(.+)$",
        r"^where is file\s+(.+)$",
        r"^where can i find the file\s+(.+)$",
        r"^where can i find file\s+(.+)$",
        r"^find the file\s+(.+)$",
        r"^find file\s+(.+)$",
    ]
    for pattern in explicit_file_patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            value = raw[m.start(1):m.end(1)].strip(" ?,.")
            return {"intent": "find_file", "value": value}

    explicit_folder_patterns = [
        r"^where is the folder\s+(.+)$",
        r"^where is folder\s+(.+)$",
        r"^where can i find the folder\s+(.+)$",
        r"^where can i find folder\s+(.+)$",
        r"^find the folder\s+(.+)$",
        r"^find folder\s+(.+)$",
    ]
    for pattern in explicit_folder_patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            value = raw[m.start(1):m.end(1)].strip(" ?,.")
            return {"intent": "find_folder", "value": value}

    read_file_patterns = [
        r"^read\s+(.+)$",
        r"^open\s+(.+\.txt|.+\.py|.+\.md|.+\.json|.+\.csv)$",
        r"^show me\s+(.+\.txt|.+\.py|.+\.md|.+\.json|.+\.csv)$",
    ]
    for pattern in read_file_patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            value = raw[m.start(1):m.end(1)].strip(" ?,.")
            return {"intent": "read_file", "value": value}

    open_site_patterns = [
        r"^open website[:\s]+(.+)$",
        r"^open site[:\s]+(.+)$",
        r"^open url[:\s]+(.+)$",
        r"^open link[:\s]+(.+)$",
        r"^open[:\s]+(https?://.+)$",
        r"^open[:\s]+([a-zA-Z0-9\-]+\.[a-zA-Z]{2,}.*)$",
    ]
    for pattern in open_site_patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            value = raw[m.start(1):m.end(1)].strip()
            return {"intent": "open_site", "value": value}

    run_patterns = [
        r"^run[:\s]+(.+)$",
        r"^launch[:\s]+(.+)$",
        r"^open app[:\s]+(.+)$",
        r"^start[:\s]+(.+)$",
        r"^open program[:\s]+(.+)$",
    ]
    for pattern in run_patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            value = raw[m.start(1):m.end(1)].strip()
            return {"intent": "run_app", "value": value}

    m = re.match(r"^open[:\s]+(.+)$", lower, re.IGNORECASE)
    if m:
        value = raw[m.start(1):m.end(1)].strip()
        if "." in value or value.startswith("http://") or value.startswith("https://"):
            return {"intent": "open_site", "value": value}
        return {"intent": "run_app", "value": value}

    calc_patterns = [
        r"^calc[:\s]+(.+)$",
        r"^calculate[:\s]+(.+)$",
        r"^what is[:\s]+([0-9\.\+\-\*\/%\(\)\s]+)$",
        r"^what'?s[:\s]+([0-9\.\+\-\*\/%\(\)\s]+)$",
        r"^solve[:\s]+([0-9\.\+\-\*\/%\(\)\s]+)$",
        r"^what is the answer to[:\s]+([0-9\.\+\-\*\/%\(\)\s]+)$",
    ]
    for pattern in calc_patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            return {"intent": "calc", "value": m.group(1).strip()}

    if is_math_expression(raw):
        return {"intent": "calc", "value": raw.strip()}

    smart_find_patterns = [
        r"^where is\s+(.+)$",
        r"^find me\s+(.+)$",
        r"^find\s+(.+)$",
    ]
    for pattern in smart_find_patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            candidate = raw[m.start(1):m.end(1)].strip(" ?,.")
            candidate_lower = candidate.lower()

            if "folder" in candidate_lower:
                return {"intent": "find_folder", "value": candidate}

            file_words = [
                "image", "photo", "picture", "python", "python file", "python script",
                "text", "text file", "document", "pdf", "word", "excel",
                "spreadsheet", "code", "code file", "audio", "video", "archive",
                "file", ".py", ".txt", ".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"
            ]
            if any(word in candidate_lower for word in file_words):
                return {"intent": "find_file", "value": candidate}

    search_patterns = [
        r"^search[:\s]+(.+)$",
        r"^search for[:\s]+(.+)$",
        r"^look up[:\s]+(.+)$",
        r"^can you search[:\s]+(.+)$",
        r"^search this[:\s]+(.+)$",
        r"^google[:\s]+(.+)$",
    ]
    for pattern in search_patterns:
        m = re.match(pattern, lower, re.IGNORECASE)
        if m:
            value = raw[m.start(1):m.end(1)].strip()
            return {"intent": "search", "value": value}

    return {"intent": "chat", "value": ""}