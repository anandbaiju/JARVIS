"""
Task executor — parses natural language commands and routes to appropriate skills.
Detects intent from user messages and executes actions like opening apps,
browsing websites, searching, etc.
"""

import re
from typing import Optional, Tuple

from backend.skills.system_control import (
    open_app,
    open_url,
    open_website,
    search_google,
    search_youtube,
    get_system_info,
    set_volume,
)
from backend.skills.web_search import search as web_search
from backend.skills.reminders import add_reminder, get_upcoming


def detect_and_execute(message: str) -> Optional[str]:
    """Analyse a user message for actionable intent and execute if found.

    Returns the action result string if an action was taken, or None if
    the message is purely conversational (should go to the LLM only).

    Args:
        message: The raw user message text.

    Returns:
        Action result string, or None if no action was detected.
    """
    text = message.strip().lower()

    # ── Open website / URL ────────────────────────────────────────
    result = _try_open_website(text, message)
    if result:
        return result

    # ── Search commands ───────────────────────────────────────────
    result = _try_search(text, message)
    if result:
        return result

    # ── Open app ──────────────────────────────────────────────────
    result = _try_open_app(text, message)
    if result:
        return result

    # ── System info ───────────────────────────────────────────────
    if _matches_any(text, [
        "system info", "system status", "system stats",
        "cpu usage", "ram usage", "memory usage",
        "diagnostics", "how is my system", "how's my pc",
        "check my system", "system health",
    ]):
        return get_system_info()

    # ── Volume control ────────────────────────────────────────────
    result = _try_volume(text)
    if result:
        return result

    # ── Reminders ─────────────────────────────────────────────────
    if _matches_any(text, [
        "show reminders", "my reminders", "upcoming reminders",
        "list reminders", "what are my reminders",
    ]):
        return get_upcoming()

    # No actionable intent detected — let the LLM handle it
    return None


def _try_open_website(text: str, original: str) -> Optional[str]:
    """Detect and handle 'open <website>' commands."""

    # Patterns: "open youtube", "go to google", "launch github",
    #           "open youtube.com", "open https://example.com"
    patterns = [
        r"(?:open|go to|launch|visit|navigate to|browse|show me|take me to)\s+(.+?)(?:\s+(?:in|on|using)\s+(?:browser|chrome|edge|firefox))?$",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            target = match.group(1).strip()

            # Remove common filler words
            target = re.sub(r"^(the|a|my)\s+", "", target)
            target = target.strip(". ")

            # Skip if it's clearly an app command, not a website
            if target in ("settings", "task manager", "file explorer",
                          "explorer", "files", "cmd", "terminal",
                          "powershell", "notepad", "calculator", "calc",
                          "paint", "snipping tool", "camera"):
                return None

            # Check if it looks like a URL
            if "." in target or target.startswith("http"):
                return open_url(target)

            # Check if it's a known website
            from backend.skills.system_control import _SITE_MAP
            if target.lower() in _SITE_MAP:
                return open_website(target)

            # Check if it's a known app
            from backend.skills.system_control import _APP_MAP
            if target.lower() in _APP_MAP:
                return open_app(target)

            # Default: try as website
            return open_website(target)

    return None


def _try_search(text: str, original: str) -> Optional[str]:
    """Detect and handle search commands."""

    # YouTube search: "search youtube for cats", "youtube search cats",
    #                 "find on youtube funny videos"
    yt_patterns = [
        r"(?:search|find|look up|look for)\s+(?:on\s+)?youtube\s+(?:for\s+)?(.+)",
        r"youtube\s+search\s+(?:for\s+)?(.+)",
        r"(?:search|find)\s+(.+?)\s+on\s+youtube",
        r"play\s+(.+?)\s+on\s+youtube",
    ]
    for pattern in yt_patterns:
        match = re.search(pattern, text)
        if match:
            query = match.group(1).strip().strip(". ")
            return search_youtube(query)

    # Google search: "search google for AI news", "google search python tutorials"
    google_patterns = [
        r"(?:search|find|look up|look for)\s+(?:on\s+)?google\s+(?:for\s+)?(.+)",
        r"google\s+search\s+(?:for\s+)?(.+)",
        r"(?:search|find|look up)\s+(.+?)\s+on\s+google",
        r"google\s+(.+)",
    ]
    for pattern in google_patterns:
        match = re.search(pattern, text)
        if match:
            query = match.group(1).strip().strip(". ")
            return search_google(query)

    # Generic search: "search for AI news", "look up python tutorials"
    generic_patterns = [
        r"(?:search|search for|look up|look for|find|find me|browse for)\s+(.+)",
    ]
    for pattern in generic_patterns:
        match = re.search(pattern, text)
        if match:
            query = match.group(1).strip().strip(". ")
            # Don't match if this was already caught by open_website
            if not _matches_any(text, ["open", "go to", "launch", "visit"]):
                result = web_search(query)
                return result

    return None


def _try_open_app(text: str, original: str) -> Optional[str]:
    """Detect and handle 'open <app>' commands for desktop applications."""

    patterns = [
        r"(?:open|launch|start|run)\s+(.+?)(?:\s+app(?:lication)?)?$",
    ]

    from backend.skills.system_control import _APP_MAP

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            target = match.group(1).strip()
            target = re.sub(r"^(the|a|my)\s+", "", target)
            target = target.strip(". ")

            # Only match if it's a known app (not a website)
            if target.lower() in _APP_MAP:
                return open_app(target)

    return None


def _try_volume(text: str) -> Optional[str]:
    """Detect and handle volume commands."""

    # "set volume to 50", "volume 80", "turn volume to 30"
    match = re.search(r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)", text)
    if match:
        level = int(match.group(1))
        return set_volume(level)

    if "mute" in text and "volume" in text:
        return set_volume(0)

    if "max volume" in text or "full volume" in text:
        return set_volume(100)

    return None


def _matches_any(text: str, keywords: list[str]) -> bool:
    """Return True if text contains any of the given keywords/phrases."""
    return any(kw in text for kw in keywords)
