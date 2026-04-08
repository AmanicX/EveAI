import os
from classifier import classify_request
from memory_store import add_memory_fact, forget_memory_fact, format_memory_block, set_memory_file
from history_store import clear_history, set_history_file, load_history
from tools import safe_calculate, open_website, get_local_time_text
from web_search import search_web, format_search_results, smart_search
from client import chat, think_then_chat
from app_launcher import launch_app
from intent_parser import extract_intent
from intent_router import ai_extract_intent
from weather_api import get_weather, format_weather_result
from auto_memory import auto_remember
from tts_engine import ReinaTTS
from personality_manager import get_eve_profile, load_personality
from doc_builder import (
    extract_relevant_history_block, generate_document_text,
    extract_title_from_output, remove_title_line,
)
from local_doc_writer import build_docx_file
from file_search import (
    index_path, get_index_summary, smart_find_files, smart_find_folders,
    smart_list_folder_contents, read_text_file, delete_path,
    path_exists, normalize_path,
)
from config import SMART_MODEL

ACTIVE_PROFILE = None
tts            = None
PENDING_ACTION = None

HELP_TEXT = """
Commands and natural language both work.

Examples:
  remember this: my pc has a gtx 1060
  what do you remember
  forget my name is X
  what time is it
  what is 25*17
  search best budget keyboard
  open youtube.com
  open steam / launch discord
  what's the weather in multan
  scan folder D:\\Projects
  find me the image sunset
  where is the folder Assets
  read notes.txt
  delete file D:\\old.txt
  make a document of the website list
  change mode to ava
  clear chat
  exit
"""

LAST_TOPIC = ""


def apply_profile(profile: dict):
    global ACTIVE_PROFILE, tts
    ACTIVE_PROFILE = profile
    set_memory_file(profile.get("memory_file", "eve_memory.json"))
    set_history_file(profile.get("history_file", "eve_history.json"))
    tts = ReinaTTS(voice=profile.get("voice", "en-IE-EmilyNeural"))


def say_and_print(text: str):
    name = ACTIVE_PROFILE.get("name", "Eve")
    print(f"\n{name}: {text}\n")
    try:
        tts.speak(text)
    except Exception:
        pass


def answer_with_tool_context(user_question: str, tool_text: str, instruction: str = "") -> str:
    extra = "Use the following result as your source of truth. Do not invent details.\n\n"
    if instruction:
        extra = instruction.strip() + "\n\n" + extra
    return chat(
        user_question,
        model=ACTIVE_PROFILE.get("model"),
        system_prompt=ACTIVE_PROFILE.get("system_prompt"),
        extra_system_blocks=[extra + tool_text],
    )


def looks_like_doc_request(text: str) -> bool:
    lower = text.lower().strip()
    return any(t in lower for t in [
        "make a document", "create a document", "save this as a document",
        "turn this into a document", "make a doc", "create a doc",
    ])


def resolve_intent(user_input: str):
    if looks_like_doc_request(user_input):
        return {"intent": "create_doc", "value": user_input}

    intent = extract_intent(user_input)

    if intent.get("intent") == "chat":
        ai_intent = ai_extract_intent(user_input)
        if ai_intent.get("intent") and ai_intent.get("intent") != "chat":
            return ai_intent

    return intent


def format_scored_path_list(matches):
    return "\n".join(
        f"{i}. {m['name']} -> {m['path']}"
        for i, m in enumerate(matches, 1)
    )


def format_folder_contents(folder_path, contents):
    folders = contents.get("folders", [])
    files   = contents.get("files",   [])
    lines   = [f"Inside {folder_path}:"]
    if folders:
        lines += ["", "Folders:"] + [f"- {os.path.basename(f)}" for f in folders]
    if files:
        lines += ["", "Files:"]   + [f"- {os.path.basename(f)}" for f in files]
    if not folders and not files:
        lines += ["", "That folder is empty."]
    return "\n".join(lines)


def handle_pending_confirmation(intent):
    global PENDING_ACTION
    if not PENDING_ACTION:
        return False, None

    kind = intent.get("intent")

    if kind == "confirm_no":
        PENDING_ACTION = None
        return True, "Okay, cancelled. Nothing was deleted."

    if kind == "confirm_yes":
        target = PENDING_ACTION["path"]
        ok, msg = delete_path(target)
        PENDING_ACTION = None
        return True, msg

    return False, None


def create_doc_from_history(user_input: str, title_hint: str = ""):
    history = load_history()
    if not history:
        return False, "No chat history yet to turn into a document."

    raw_block, _ = extract_relevant_history_block(history, user_input)
    if not raw_block.strip():
        return False, "I couldn't find a useful conversation block."

    structured_text = generate_document_text(
        raw_block=raw_block,
        title_hint=title_hint,
        model=ACTIVE_PROFILE.get("model"),
        system_prompt=ACTIVE_PROFILE.get("system_prompt"),
    )

    doc_title = extract_title_from_output(structured_text)
    doc_body  = remove_title_line(structured_text)
    ok, msg, info = build_docx_file(title=doc_title, body_text=doc_body)

    if not ok:
        return False, msg
    return True, f"Document created.\nTitle: {info['title']}\nSaved at: {info['path']}"


def handle_structured_intent(user_input: str):
    global PENDING_ACTION

    intent = resolve_intent(user_input)
    handled, result = handle_pending_confirmation(intent)
    if handled:
        return True, result

    kind  = intent.get("intent")
    value = intent.get("value", "")

    if kind == "none":
        return True, "Say something first."

    if kind == "change_mode":
        mode = value.lower().strip()
        if not mode:
            return True, "Tell me which mode you want."
        if mode == "eve":
            apply_profile(get_eve_profile())
            return True, "Switched back to Eve."
        ok, msg, profile = load_personality(mode)
        if not ok:
            return True, msg
        apply_profile(profile)
        return True, f"Switched to {profile.get('name', mode.title())}."
    
    if kind == "expand":
        if not LAST_TOPIC:
            return True, "I'm not sure what to expand on. Ask me something first."
        # Re-ask the last topic with expand mode
        thinking, reply = think_then_chat(
            f"Give me a full detailed explanation of: {LAST_TOPIC}",
            model=ACTIVE_PROFILE.get("model") or SMART_MODEL,
            system_prompt=ACTIVE_PROFILE.get("system_prompt"),
            expand_mode=True,
        )
        if thinking:
            print(f"\033[2m[Reasoning: {thinking[:180]}{'...' if len(thinking) > 180 else ''}]\033[0m")
        return True, reply

    if kind == "create_doc":
        ok, msg = create_doc_from_history(user_input, title_hint=value)
        return True, msg

    if kind == "remember":
        ok, msg = add_memory_fact(value)
        if ok:
            reply = answer_with_tool_context(user_input, f"Memory result: {msg}",
                instruction="Briefly acknowledge you saved the memory. Keep it short.")
            return True, reply
        return True, msg

    if kind == "forget":
        ok, msg = forget_memory_fact(value)
        if ok:
            reply = answer_with_tool_context(user_input, f"Memory result: {msg}",
                instruction="Briefly acknowledge you removed the memory. Keep it short.")
            return True, reply
        return True, msg

    if kind == "memories":
        memory_block = format_memory_block()
        reply = answer_with_tool_context(user_input, memory_block,
            instruction="Show the saved memories in a helpful way. Do not invent extras.")
        return True, reply

    if kind == "clear":
        clear_history()
        return True, "Chat history cleared."

    if kind == "time":
        time_text = get_local_time_text()
        reply = answer_with_tool_context(user_input, time_text,
            instruction="Tell the user the current time clearly.")
        return True, reply

    if kind == "calc":
        result, err = safe_calculate(value)
        if err:
            return True, f"Calculation failed: {err}"
        reply = answer_with_tool_context(user_input, f"Result: {result}",
            instruction="Give the answer clearly and naturally.")
        return True, reply

    if kind == "open_site":
        ok, msg = open_website(value)
        return True, f"Opened {value}." if ok else msg

    if kind == "run_app":
        ok, msg = launch_app(value)
        return True, f"Launched {value}." if ok else msg

    if kind == "search":
        query = value.strip()
        if not query:
            return True, "Give me something to search for."
        ok, msg, results = search_web(query, max_results=5)
        if not ok:
            return True, msg
        search_block = format_search_results(results)
        reply = answer_with_tool_context(user_input, search_block,
            instruction="Make clear these are search results, then answer using only them.")
        return True, reply

    if kind == "weather":
        ok, msg, result = get_weather(value.strip())
        if not ok:
            return True, msg
        return True, format_weather_result(result)

    if kind == "index_path":
        ok, msg, stats = index_path(value)
        if not ok:
            return True, msg
        return True, (f"Indexed {stats['root']}. "
                      f"Found {stats['files']} files and {stats['folders']} folders.")

    if kind == "find_file":
        matches = smart_find_files(value)
        if not matches:
            summary = get_index_summary()
            if not summary["roots"]:
                return True, "Scan a folder first: scan folder D:\\Projects"
            return True, f"No close match found for: {value}"
        if len(matches) == 1 or matches[0].get("score", 0) >= 90:
            item = matches[0]
            return True, f"Found: {item['name']} at {item['path']}"
        return True, f"Close matches for '{value}':\n{format_scored_path_list(matches)}"

    if kind == "find_folder":
        matches = smart_find_folders(value)
        if not matches:
            return True, f"No close folder match for: {value}"
        if len(matches) == 1 or matches[0].get("score", 0) >= 90:
            item = matches[0]
            return True, f"Found: {item['name']} at {item['path']}"
        return True, f"Close matches:\n{format_scored_path_list(matches)}"

    if kind == "list_folder_contents":
        ok, folder_path, contents = smart_list_folder_contents(value)
        if not ok:
            return True, folder_path
        return True, format_folder_contents(folder_path, contents)

    if kind == "read_file":
        target = value.strip()
        if not target:
            return True, "Tell me which file to read."
        if (":\\" in target or target.startswith("\\\\")) and path_exists(target):
            ok, content = read_text_file(target)
            if not ok:
                return True, content
            return True, f"Content of {normalize_path(target)}:\n\n{content}"
        matches = smart_find_files(target)
        if not matches:
            return True, f"No indexed file matching: {target}"
        if len(matches) > 1 and matches[0].get("score", 0) < 90:
            return True, f"Multiple matches:\n{format_scored_path_list(matches)}\nGive me the full path."
        ok, content = read_text_file(matches[0]["path"])
        if not ok:
            return True, content
        return True, f"Content of {matches[0]['path']}:\n\n{content}"

    if kind == "delete_path":
        target = value.strip()
        if not target:
            return True, "Give me the exact path to delete."
        normalized = normalize_path(target)
        if not path_exists(normalized):
            return True, f"Path does not exist: {normalized}"
        PENDING_ACTION = {"action": "delete", "path": normalized}
        return True, f"Found: {normalized}\n\nDelete it? Say yes to confirm or no to cancel."

    if kind == "chat":
        return False, None

    return False, None


def handle_slash_commands(text: str):
    lower = text.lower().strip()

    if lower in {"/help", "help"}:
        return True, HELP_TEXT
    if lower in {"/memories"}:
        return True, format_memory_block()
    if lower in {"/clear"}:
        clear_history()
        return True, "History cleared."
    if lower in {"/time"}:
        return True, get_local_time_text()
    if lower in {"/exit", "exit", "quit"}:
        return True, "__EXIT__"
    if lower.startswith("/remember "):
        _, msg = add_memory_fact(text[10:].strip())
        return True, msg
    if lower.startswith("/forget "):
        _, msg = forget_memory_fact(text[8:].strip())
        return True, msg
    if lower.startswith("/calc "):
        result, err = safe_calculate(text[6:].strip())
        return True, f"Result: {result}" if not err else f"Error: {err}"
    if lower.startswith("/search "):
        query = text[8:].strip()
        ok, msg, results = search_web(query, max_results=5)
        if not ok:
            return True, msg
        reply = answer_with_tool_context(query, format_search_results(results),
            instruction="Make clear these are search results.")
        return True, reply
    if lower.startswith("/doc "):
        topic = text[5:].strip()
        ok, msg = create_doc_from_history(topic, title_hint=topic)
        return True, msg

    return False, None


def main():
    apply_profile(get_eve_profile())

    print("Eve booted — powered by Groq.")
    print("PC control, memory, search, weather all active.")
    print("Type help for examples.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            say_and_print("Goodbye.")
            break

        if not user_input:
            continue

        handled, result = handle_slash_commands(user_input)
        if handled:
            if result == "__EXIT__":
                say_and_print("Goodbye.")
                break
            say_and_print(result)
            continue

        try:
            handled, result = handle_structured_intent(user_input)
            if handled:
                say_and_print(result)
                continue

            # Smart pipeline — model routing + optional search + thinking
            routing = classify_request(user_input)
            model   = routing["model"]
            label   = routing["label"]

            search_block = None
            search_query = routing.get("query", "")

            if routing["should_search"] and search_query:
                print(f"Eve: [searching: {search_query}]", end="\r")
                result = smart_search(search_query, max_results=5, fetch_top=2)
                if result["ok"]:
                    search_block = result["block"]

            print(f"Eve: [{routing['complexity']} → {label}]", end="\r")

            thinking, reply = think_then_chat(
                user_input,
                model=model,
                system_prompt=ACTIVE_PROFILE.get("system_prompt"),
                search_block=search_block,
            )

            # track last topic for expand
            global LAST_TOPIC
            LAST_TOPIC = user_input

            if thinking:
                print(f"\033[2m[Reasoning: {thinking[:180]}{'...' if len(thinking) > 180 else ''}]\033[0m")

            added = auto_remember(user_input)
            if added:
                reply += f"\n\n[Saved to memory: {', '.join(added)}]"

            say_and_print(reply)

        except Exception as e:
            say_and_print(f"Something broke: {e}")


if __name__ == "__main__":
    main()