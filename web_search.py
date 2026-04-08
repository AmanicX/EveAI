import requests
from ddgs import DDGS

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def search_web(query, max_results=5):
    results = []
    try:
        with DDGS() as ddgs:
            for item in list(ddgs.text(query))[:max_results]:
                results.append({
                    "title":   item.get("title",  "").strip(),
                    "url":     item.get("href",   "").strip(),
                    "snippet": item.get("body",   "").strip(),
                })
    except Exception as e:
        return False, f"Search failed: {e}", []

    if not results:
        return False, "No results found.", []

    return True, "Search complete.", results


def fetch_page_text(url: str, max_chars: int = 3000) -> str:
    """Fetch and extract plain text from a URL."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        raw = response.text

        # Strip HTML tags simply
        import re
        text = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.DOTALL)
        text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&[a-z]+;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text[:max_chars]
    except Exception:
        return ""


def smart_search(query: str, max_results: int = 5, fetch_top: int = 2) -> dict:
    """
    Full search pipeline:
    - Gets results from DuckDuckGo
    - Fetches actual page content from top N results
    - Returns everything as one block for Eve to use
    """
    ok, msg, results = search_web(query, max_results=max_results)

    if not ok or not results:
        return {"ok": False, "block": msg}

    enriched = []
    for i, r in enumerate(results):
        entry = {
            "title":   r["title"],
            "url":     r["url"],
            "snippet": r["snippet"],
            "content": "",
        }
        # Fetch full content for top results
        if i < fetch_top and r["url"]:
            content = fetch_page_text(r["url"])
            if content:
                entry["content"] = content
        enriched.append(entry)

    block = format_smart_results(query, enriched)
    return {"ok": True, "block": block, "results": enriched}


def format_smart_results(query: str, results: list) -> str:
    lines = [f"Search query: {query}", ""]

    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']}")
        lines.append(f"URL: {r['url']}")

        # Prefer full content over snippet if available
        body = r.get("content") or r.get("snippet") or ""
        if body:
            lines.append(f"Content: {body[:1000]}")
        lines.append("")

    return "\n".join(lines)


def format_search_results(results: list) -> str:
    """Legacy format — kept for compatibility."""
    lines = ["Web search results:"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   URL: {r['url']}")
        lines.append(f"   Snippet: {r['snippet']}")
    return "\n".join(lines)