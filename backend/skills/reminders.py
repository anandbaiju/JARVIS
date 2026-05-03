"""
Reminders skill — SQLite-backed scheduler with background checker.
Due reminders are spoken aloud via TTS.
"""

import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
_DB_PATH: Path = _PROJECT_ROOT / "data" / "reminders.db"

# Module-level lock for thread-safe DB access
_db_lock = threading.Lock()
_checker_running = False


def _get_connection() -> sqlite3.Connection:
    """Open (and initialise if needed) the reminders database."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            remind_at TEXT NOT NULL,
            notified INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def add_reminder(text: str, remind_at_str: str) -> str:
    """Create a new reminder.

    Args:
        text: What to remind about.
        remind_at_str: When to remind, as an ISO-format datetime string
                       (e.g. ``"2026-05-04T09:00:00"``).

    Returns:
        Confirmation message with the scheduled time.
    """
    try:
        remind_at = datetime.fromisoformat(remind_at_str)
    except ValueError:
        return (
            f"Invalid datetime format: '{remind_at_str}'. "
            f"Use ISO format, e.g. 2026-05-04T09:00:00"
        )

    with _db_lock:
        conn = _get_connection()
        conn.execute(
            "INSERT INTO reminders (text, remind_at, created_at) VALUES (?, ?, ?)",
            (text, remind_at.isoformat(), datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

    return f"Reminder set: \"{text}\" at {remind_at.strftime('%Y-%m-%d %H:%M')}"


def get_upcoming(limit: int = 5) -> str:
    """Return the next N upcoming (un-notified) reminders.

    Args:
        limit: Maximum number of reminders to return.

    Returns:
        Formatted string of upcoming reminders.
    """
    with _db_lock:
        conn = _get_connection()
        cursor = conn.execute(
            """
            SELECT id, text, remind_at FROM reminders
            WHERE notified = 0
            ORDER BY remind_at ASC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()

    if not rows:
        return "No upcoming reminders."

    lines: list[str] = ["Upcoming Reminders:"]
    for row_id, text, remind_at in rows:
        lines.append(f"  #{row_id} — {text} (at {remind_at})")

    return "\n".join(lines)


def _check_due_reminders() -> None:
    """Background loop: check for due reminders every 60 seconds and speak them."""
    # Import TTS lazily to avoid circular imports
    from backend.voice.tts import speak

    while _checker_running:
        now = datetime.now().isoformat()

        with _db_lock:
            conn = _get_connection()
            cursor = conn.execute(
                """
                SELECT id, text FROM reminders
                WHERE notified = 0 AND remind_at <= ?
                """,
                (now,),
            )
            due = cursor.fetchall()

            for row_id, text in due:
                conn.execute(
                    "UPDATE reminders SET notified = 1 WHERE id = ?",
                    (row_id,),
                )
                speak(f"Reminder: {text}")

            conn.commit()
            conn.close()

        time.sleep(60)


def start_reminder_checker() -> None:
    """Start the background reminder checker thread (idempotent)."""
    global _checker_running
    if _checker_running:
        return

    _checker_running = True
    thread = threading.Thread(target=_check_due_reminders, daemon=True)
    thread.start()


def stop_reminder_checker() -> None:
    """Signal the background checker to stop."""
    global _checker_running
    _checker_running = False
