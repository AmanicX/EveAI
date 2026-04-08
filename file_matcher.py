import os
import re
from pathlib import Path
from rapidfuzz import fuzz


def normalize_name(name: str) -> str:
    name = Path(name).stem.lower()
    name = name.replace("_", " ").replace("-", " ")
    name = re.sub(r"\s+", " ", name).strip()
    return name


def normalize_text(text: str) -> str:
    text = text.lower().replace("_", " ").replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extension_matches(path: str, allowed_extensions):
    if not allowed_extensions:
        return True
    ext = os.path.splitext(path)[1].lower()
    return ext in {e.lower() for e in allowed_extensions}


def drive_matches(path: str, drive: str):
    if not drive:
        return True
    norm = os.path.abspath(path)
    return norm.lower().startswith(f"{drive.lower()}:\\") or norm.lower().startswith(f"{drive.lower()}:/")


def parent_hint_matches(path: str, parent_hint: str):
    if not parent_hint:
        return True
    return parent_hint.lower() in path.lower()


def compute_match_score(query: str, candidate_name: str, path: str, drive=None, parent_hint=None):
    q = normalize_text(query)
    n = normalize_name(candidate_name)

    base_score = max(
        fuzz.ratio(q, n),
        fuzz.partial_ratio(q, n),
        fuzz.token_sort_ratio(q, n),
        fuzz.token_set_ratio(q, n),
    )

    score = float(base_score)

    if q == n:
        score += 20

    if drive and drive_matches(path, drive):
        score += 10

    if parent_hint and parent_hint_matches(path, parent_hint):
        score += 12

    return score


def find_best_file_matches(index_data, name_query, extensions=None, drive=None, parent_hint=None, limit=5):
    if not name_query:
        return []

    results = []

    for items in index_data.get("files_by_name", {}).values():
        for item in items:
            path = item["path"]
            name = item["name"]

            if not extension_matches(path, extensions):
                continue

            if not drive_matches(path, drive):
                continue

            score = compute_match_score(name_query, name, path, drive=drive, parent_hint=parent_hint)

            if parent_hint and parent_hint.lower() in path.lower():
                score += 8

            results.append({
                "name": name,
                "path": path,
                "score": round(score, 2),
            })

    results.sort(key=lambda x: (-x["score"], x["name"].lower()))
    return results[:limit]


def find_best_folder_matches(index_data, folder_query, drive=None, parent_hint=None, limit=5):
    if not folder_query:
        return []

    results = []

    for items in index_data.get("folders_by_name", {}).values():
        for item in items:
            path = item["path"]
            name = item["name"]

            if not drive_matches(path, drive):
                continue

            score = compute_match_score(folder_query, name, path, drive=drive, parent_hint=parent_hint)

            if parent_hint and parent_hint.lower() in path.lower():
                score += 8

            results.append({
                "name": name,
                "path": path,
                "score": round(score, 2),
            })

    results.sort(key=lambda x: (-x["score"], x["name"].lower()))
    return results[:limit]