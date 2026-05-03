"""
Web search skill using DuckDuckGo (no API key required).
"""

from typing import Optional


def search(query: str, max_results: int = 3) -> str:
    """Search the web via DuckDuckGo and return formatted results.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.

    Returns:
        Formatted string of search results, or an error message.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return "[Web search unavailable — duckduckgo-search is not installed]"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"No results found for: {query}"

        lines: list[str] = ["Search Results:"]
        for i, r in enumerate(results, start=1):
            title = r.get("title", "No title")
            body = r.get("body", r.get("snippet", "No snippet"))
            href = r.get("href", "")
            lines.append(f"{i}. [{title}] — {body}")
            if href:
                lines.append(f"   Link: {href}")

        return "\n".join(lines)

    except Exception as exc:
        return f"Search failed: {exc}"
