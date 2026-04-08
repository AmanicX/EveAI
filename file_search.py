import json
import os
from datetime import datetime

from config import SMART_FILE_MATCH_LIMIT, SMART_FOLDER_MATCH_LIMIT
from file_query_parser import parse_file_query
from file_matcher import find_best_file_matches, find_best_folder_matches

FILE_INDEX_PATH = "file_paths_memory.json"


def _default_index():
    return {
        "roots": [],
        "last_indexed": None,
        "files_by_name": {},
        "folders_by_name": {},
    }


def load_file_index():
    if not os.path.exists(FILE_INDEX_PATH):
        return _default_index()

    try:
        with open(FILE_INDEX_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return _default_index()

        default = _default_index()
        for key, value in default.items():
            data.setdefault(key, value)

        if not isinstance(data.get("files_by_name"), dict):
            data["files_by_name"] = {}

        if not isinstance(data.get("folders_by_name"), dict):
            data["folders_by_name"] = {}

        if not isinstance(data.get("roots"), list):
            data["roots"] = []

        return data
    except Exception:
        return _default_index()


def save_file_index(data):
    with open(FILE_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _add_unique_record(bucket, key, record):
    bucket.setdefault(key, [])
    existing_paths = {item["path"].lower() for item in bucket[key]}
    if record["path"].lower() not in existing_paths:
        bucket[key].append(record)


def index_path(root_path):
    root_path = os.path.abspath(os.path.normpath(root_path))

    if not os.path.exists(root_path):
        return False, f"That path does not exist: {root_path}", None

    if not os.path.isdir(root_path):
        return False, f"That path is not a folder: {root_path}", None

    data = load_file_index()

    files_by_name = data["files_by_name"]
    folders_by_name = data["folders_by_name"]

    total_files = 0
    total_folders = 0

    for current_root, dirs, files in os.walk(root_path):
        for folder_name in dirs:
            folder_path = os.path.join(current_root, folder_name)
            record = {
                "name": folder_name,
                "path": os.path.abspath(folder_path),
            }
            _add_unique_record(folders_by_name, folder_name.lower(), record)
            total_folders += 1

        for file_name in files:
            file_path = os.path.join(current_root, file_name)
            record = {
                "name": file_name,
                "path": os.path.abspath(file_path),
            }
            _add_unique_record(files_by_name, file_name.lower(), record)
            total_files += 1

    data["roots"] = sorted(list({*data.get("roots", []), root_path}))
    data["last_indexed"] = datetime.now().isoformat(timespec="seconds")

    save_file_index(data)

    stats = {
        "root": root_path,
        "files": total_files,
        "folders": total_folders,
    }
    return True, f"Indexed {root_path}", stats


def get_index_summary():
    data = load_file_index()
    file_count = sum(len(v) for v in data.get("files_by_name", {}).values())
    folder_count = sum(len(v) for v in data.get("folders_by_name", {}).values())

    return {
        "roots": data.get("roots", []),
        "last_indexed": data.get("last_indexed"),
        "file_count": file_count,
        "folder_count": folder_count,
    }


def find_files_by_name(name):
    data = load_file_index()
    key = name.strip().lower()
    if not key:
        return []
    return data.get("files_by_name", {}).get(key, [])


def find_folders_by_name(name):
    data = load_file_index()
    key = name.strip().lower()
    if not key:
        return []
    return data.get("folders_by_name", {}).get(key, [])


def smart_find_files(user_query):
    data = load_file_index()
    parsed = parse_file_query(user_query)

    return find_best_file_matches(
        data,
        name_query=parsed.get("name_query", ""),
        extensions=parsed.get("extensions"),
        drive=parsed.get("drive"),
        parent_hint=parsed.get("parent_folder_hint"),
        limit=SMART_FILE_MATCH_LIMIT,
    )


def smart_find_folders(user_query):
    data = load_file_index()
    parsed = parse_file_query(user_query)

    return find_best_folder_matches(
        data,
        folder_query=parsed.get("folder_query", ""),
        drive=parsed.get("drive"),
        parent_hint=parsed.get("parent_folder_hint"),
        limit=SMART_FOLDER_MATCH_LIMIT,
    )


def smart_list_folder_contents(user_query):
    data = load_file_index()
    parsed = parse_file_query(user_query)

    folder_matches = find_best_folder_matches(
        data,
        folder_query=parsed.get("folder_query", ""),
        drive=parsed.get("drive"),
        parent_hint=parsed.get("parent_folder_hint"),
        limit=1,
    )

    if not folder_matches:
        return False, "I couldn't find a matching folder.", None

    target_path = folder_matches[0]["path"]
    contents, err = get_folder_contents(target_path)
    if err:
        return False, err, None

    return True, target_path, contents


def get_folder_contents(path):
    path = os.path.abspath(os.path.normpath(path))

    if not os.path.exists(path):
        return None, f"Path does not exist: {path}"

    folder_results = []
    file_results = []

    if os.path.isdir(path):
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                folder_results.append(full_path)
            elif os.path.isfile(full_path):
                file_results.append(full_path)

    folder_results.sort()
    file_results.sort()

    return {
        "folders": folder_results,
        "files": file_results,
    }, None


def path_exists(path):
    return os.path.exists(os.path.abspath(os.path.normpath(path)))


def normalize_path(path):
    return os.path.abspath(os.path.normpath(path))


def read_text_file(file_path, max_chars=12000):
    file_path = normalize_path(file_path)

    if not os.path.exists(file_path):
        return False, f"That file does not exist: {file_path}"

    if not os.path.isfile(file_path):
        return False, f"That path is not a file: {file_path}"

    ext = os.path.splitext(file_path)[1].lower()
    blocked_exts = {
        ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp",
        ".mp3", ".wav", ".ogg", ".flac", ".mp4", ".mkv", ".avi",
        ".exe", ".dll", ".bin", ".zip", ".rar", ".7z", ".pdf",
        ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"
    }

    if ext in blocked_exts:
        return False, f"I can’t safely read that file as plain text: {file_path}"

    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding, errors="replace") as f:
                content = f.read(max_chars + 1)

            if len(content) > max_chars:
                content = content[:max_chars] + "\n\n[truncated]"
            return True, content
        except Exception:
            continue

    return False, f"I couldn’t read that file: {file_path}"


def delete_path(target_path):
    target_path = normalize_path(target_path)

    if not os.path.exists(target_path):
        return False, f"That path does not exist: {target_path}"

    try:
        if os.path.isfile(target_path):
            os.remove(target_path)
            removed_type = "file"
        elif os.path.isdir(target_path):
            os.rmdir(target_path)
            removed_type = "folder"
        else:
            return False, f"I can’t delete that path type: {target_path}"

        _remove_deleted_path_from_index(target_path)
        return True, f"Deleted {removed_type}: {target_path}"
    except OSError as e:
        return False, (
            f"I couldn’t delete that path. If it is a folder, it may not be empty. Error: {e}"
        )
    except Exception as e:
        return False, f"Delete failed: {e}"


def _remove_deleted_path_from_index(target_path):
    data = load_file_index()
    target_lower = target_path.lower()

    for bucket_name in ("files_by_name", "folders_by_name"):
        bucket = data.get(bucket_name, {})
        for key in list(bucket.keys()):
            filtered = [item for item in bucket[key] if item["path"].lower() != target_lower]
            if filtered:
                bucket[key] = filtered
            else:
                del bucket[key]

    save_file_index(data)