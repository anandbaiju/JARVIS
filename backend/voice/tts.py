"""
Text-to-Speech using pyttsx3 (Windows SAPI5 voices).
Speaks JARVIS responses aloud in a non-blocking background thread.
"""

import re
import threading
from typing import Optional

try:
    import pyttsx3
    _TTS_AVAILABLE = True
except ImportError:
    pyttsx3 = None  # type: ignore[assignment]
    _TTS_AVAILABLE = False

# Module-level lock to prevent overlapping speech
_speak_lock = threading.Lock()


def _strip_markdown(text: str) -> str:
    """Remove common markdown formatting characters before speaking.

    Strips: **, *, #, `, > (blockquote markers)
    """
    cleaned = re.sub(r"[*#`]", "", text)
    # Remove blockquote markers at line starts
    cleaned = re.sub(r"^\s*>\s?", "", cleaned, flags=re.MULTILINE)
    # Collapse multiple whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _do_speak(text: str) -> None:
    """Internal blocking speak — runs inside a thread."""
    if not _TTS_AVAILABLE:
        return

    with _speak_lock:
        engine = pyttsx3.init()
        engine.setProperty("rate", 185)  # Slightly fast — sharp JARVIS feel

        # Optionally pick a male voice if available
        voices = engine.getProperty("voices")
        for voice in voices:
            if "male" in voice.name.lower() or "david" in voice.name.lower():
                engine.setProperty("voice", voice.id)
                break

        engine.say(text)
        engine.runAndWait()
        engine.stop()


def speak(text: str) -> None:
    """Speak the given text aloud in a background thread (non-blocking).

    Markdown formatting is stripped before passing to the TTS engine.

    Args:
        text: The text to speak aloud.
    """
    if not _TTS_AVAILABLE:
        return

    cleaned = _strip_markdown(text)
    if not cleaned:
        return

    thread = threading.Thread(target=_do_speak, args=(cleaned,), daemon=True)
    thread.start()
