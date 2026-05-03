"""
Short-term conversation memory — in-memory rolling buffer.
Keeps the last N messages for context injection into the LLM prompt.
"""

from typing import List, Dict


class ConversationBuffer:
    """Rolling conversation buffer that retains the most recent messages."""

    MAX_MESSAGES: int = 20

    def __init__(self) -> None:
        self._messages: List[Dict[str, str]] = []

    def add(self, role: str, content: str) -> None:
        """Append a message to the buffer.

        Args:
            role: Either ``"user"`` or ``"assistant"``.
            content: The message text.
        """
        self._messages.append({"role": role, "content": content})
        # Trim to keep only the most recent messages
        if len(self._messages) > self.MAX_MESSAGES:
            self._messages = self._messages[-self.MAX_MESSAGES:]

    def get_messages(self) -> List[Dict[str, str]]:
        """Return the current conversation history as a list of dicts."""
        return list(self._messages)

    def clear(self) -> None:
        """Reset the conversation buffer."""
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)

    def __repr__(self) -> str:
        return f"ConversationBuffer(messages={len(self._messages)})"
