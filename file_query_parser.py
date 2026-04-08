import re
from config import FILE_TYPE_MAP


def normalize_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def detect_drive(text: str):
    patterns = [
        r"\b([a-z]) drive\b",
        r"\bdrive ([a-z])\b",
        r"\bin ([a-z]) drive\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).upper()
    return None


def detect_parent_folder_hint(text: str):
    patterns = [
        r"\binside the ([a-zA-Z0-9_\-\s]+) folder\b",
        r"\bin the ([a-zA-Z0-9_\-\s]+) folder\b",
        r"\bunder the ([a-zA-Z0-9_\-\s]+) folder\b",
    ]
    for pattern in patterns:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if matches:
            last = matches[-1].group(1).strip()
            return normalize_text(last)
    return None


def infer_extensions(text: str):
    lower = text.lower()

    matched_exts = set()

    for key, exts in FILE_TYPE_MAP.items():
        if key in lower:
            matched_exts.update(exts)

    if matched_exts:
        return sorted(matched_exts)

    return None


def remove_known_phrases(text: str) -> str:
    lower = text.lower()
    cleaned = text

    phrases = [
        "where is the file",
        "where is file",
        "where can i find the file",
        "where can i find file",
        "find the file",
        "find file",
        "find me the file",
        "find me file",
        "find me this file",
        "find this file",
        "where is the folder",
        "where is folder",
        "find the folder",
        "find folder",
        "find me the folder",
        "find me folder",
        "what is inside the folder",
        "what is inside folder",
        "show me what is inside the folder",
        "show me what is inside folder",
        "show contents of folder",
        "show contents of the folder",
        "list contents of folder",
        "list contents of the folder",
        "image",
        "photo",
        "picture",
        "python file",
        "python script",
        "text file",
        "document",
        "pdf",
        "word file",
        "excel file",
        "spreadsheet",
        "code file",
        "located in the",
        "located in",
        "inside the",
        "inside",
        "under the",
        "under",
        "folder",
        "file",
    ]

    for phrase in sorted(phrases, key=len, reverse=True):
        cleaned = re.sub(rf"\b{re.escape(phrase)}\b", " ", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\b[a-zA-Z]\s+drive\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bdrive\s+[a-zA-Z]\b", " ", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"[?.,]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def extract_folder_name(text: str):
    patterns = [
        r"\bfolder\s+([a-zA-Z0-9_\-\. ]+?)(?:\s+located|\s+inside|\s+under|$)",
        r"\bdirectory\s+([a-zA-Z0-9_\-\. ]+?)(?:\s+located|\s+inside|\s+under|$)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return normalize_text(m.group(1))
    return None


def parse_file_query(user_input: str):
    raw = normalize_text(user_input)
    lower = raw.lower()

    drive = detect_drive(raw)
    parent_hint = detect_parent_folder_hint(raw)
    extensions = infer_extensions(raw)

    if any(phrase in lower for phrase in [
        "what is inside the folder",
        "what is inside folder",
        "show contents of folder",
        "show contents of the folder",
        "list contents of folder",
        "list contents of the folder",
    ]):
        folder_query = extract_folder_name(raw) or remove_known_phrases(raw)
        return {
            "action": "list_folder_contents",
            "folder_query": folder_query.strip(),
            "drive": drive,
            "parent_folder_hint": parent_hint,
            "extensions": None,
        }

    if "folder" in lower and any(x in lower for x in ["where is", "find"]):
        folder_query = extract_folder_name(raw) or remove_known_phrases(raw)
        return {
            "action": "find_folder",
            "folder_query": folder_query.strip(),
            "drive": drive,
            "parent_folder_hint": parent_hint,
            "extensions": None,
        }

    return {
        "action": "find_file",
        "name_query": remove_known_phrases(raw).strip(),
        "drive": drive,
        "parent_folder_hint": parent_hint,
        "extensions": extensions,
    }