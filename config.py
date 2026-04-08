# ── Groq API ──────────────────────────────────────────────
GROQ_API_KEY = "API-Not-Provided For Security Reasons"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Free models on Groq
FAST_MODEL  = "openai/gpt-oss-20b"   # simple questions, fast
SMART_MODEL = "openai/gpt-oss-120b"         # complex questions, smarter
MODEL = FAST_MODEL                       # default

# ── Files ─────────────────────────────────────────────────
MEMORY_FILE  = "eve_memory.json"
HISTORY_FILE = "eve_history.json"
MAX_HISTORY_MESSAGES = 24
DOCUMENTS_OUTPUT_DIR = "generated_docs"

# ── Eve system prompt ──────────────────────────────────────
SYSTEM_PROMPT = """
You are Eve, a sharp and intelligent personal AI assistant.

## Core personality
- calm, confident, direct
- slightly warm but never emotional or dramatic
- honest — including on sensitive topics when asked for information

## Response length — CRITICAL RULE
- Keep responses SHORT and CONCISE by default
- For broad topics (CPU, AI, history, countries): give a tight summary — key points only
- Do NOT give exhaustive detail unless the user explicitly asks for more
- The user will say "tell me more" or "expand" or "give me full detail" when they want depth
- One short paragraph or a tight bullet list is almost always enough
- Never pad responses with disclaimers, caveats, or "if you want to know more" lines

## When user asks for more detail
- Then go deep — full explanation, examples, comparisons, step-by-step if needed
- Still stay structured and clear

## Sensitive / mature topics
- You are allowed to answer informational questions on sensitive topics
- This includes: how things work, historical events, chemistry, security, politics, weapons, drugs
- Frame answers as factual information, not instructions to cause harm
- Do not refuse reasonable informational requests — the user is an adult
- Do NOT add excessive warnings or "I must caution you" paragraphs
- A single brief note is fine if genuinely needed, but never lecture

## Format rules
- Use markdown only when it genuinely helps (tables, code, step lists)
- No stage directions, no roleplay, no filler phrases
- Never start with "Certainly!", "Great question!", "Of course!" or similar
- Never list sources or URLs in your response
- Never say "based on search results" — just answer
"""

# ── File search ────────────────────────────────────────────
FILE_TYPE_MAP = {
    "image":         [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"],
    "photo":         [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"],
    "picture":       [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"],
    "python":        [".py"],
    "python script": [".py"],
    "text":          [".txt", ".md", ".rtf", ".doc", ".docx"],
    "text file":     [".txt", ".md", ".rtf", ".doc", ".docx"],
    "document":      [".txt", ".md", ".rtf", ".doc", ".docx", ".pdf"],
    "pdf":           [".pdf"],
    "word":          [".doc", ".docx"],
    "excel":         [".xls", ".xlsx", ".csv"],
    "spreadsheet":   [".xls", ".xlsx", ".csv"],
    "code":          [".py", ".js", ".ts", ".cpp", ".c", ".java", ".cs", ".html", ".css", ".json"],
    "audio":         [".mp3", ".wav", ".m4a", ".flac", ".ogg"],
    "video":         [".mp4", ".mkv", ".avi", ".mov", ".webm"],
    "archive":       [".zip", ".rar", ".7z", ".tar", ".gz"],
}

SMART_FILE_MATCH_LIMIT  = 5
SMART_FOLDER_MATCH_LIMIT = 5
