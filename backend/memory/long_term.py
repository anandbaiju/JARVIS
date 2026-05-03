"""
Long-term vector memory powered by ChromaDB.
Stores and retrieves facts, preferences, and episodic memories.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import chromadb


# Resolve project root relative to this file's location
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
_CHROMA_PATH: Path = _PROJECT_ROOT / "data" / "chroma_db"
_PROFILE_PATH: Path = _PROJECT_ROOT / "data" / "user_profile.json"


class LongTermMemory:
    """Persistent vector memory using ChromaDB for semantic recall."""

    def __init__(self, persist_dir: Optional[str] = None) -> None:
        path = persist_dir or str(_CHROMA_PATH)
        # Ensure directory exists
        Path(path).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=path)
        self._collection = self._client.get_or_create_collection(
            name="jarvis_memory",
            metadata={"hnsw:space": "cosine"},
        )

    def save(self, text: str) -> None:
        """Embed and store a memory with a UTC timestamp.

        Args:
            text: The memory content to persist.
        """
        now = datetime.now(timezone.utc).isoformat()
        doc_id = f"mem_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        self._collection.add(
            documents=[text],
            ids=[doc_id],
            metadatas=[{"timestamp": now, "source": "conversation"}],
        )

    def recall(self, query: str, top_k: int = 3) -> str:
        """Return the top-k most relevant memories as a formatted string.

        Args:
            query: The search query to match against stored memories.
            top_k: Maximum number of results to return.

        Returns:
            A formatted string of matching memories, or a note if none found.
        """
        results = self._collection.query(query_texts=[query], n_results=top_k)

        if not results["documents"] or not results["documents"][0]:
            return "No relevant memories found."

        lines: list[str] = []
        for i, (doc, meta) in enumerate(
            zip(results["documents"][0], results["metadatas"][0]), start=1
        ):
            ts = meta.get("timestamp", "unknown")
            lines.append(f"{i}. [{ts}] {doc}")

        return "\n".join(lines)

    @staticmethod
    def load_user_profile() -> str:
        """Read ``data/user_profile.json`` and return a human-readable summary.

        Returns:
            Formatted string of user profile data, or an error note.
        """
        if not _PROFILE_PATH.exists():
            return "User profile not found."

        try:
            data = json.loads(_PROFILE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return "User profile could not be read."

        parts: list[str] = [
            f"Name: {data.get('name', 'Unknown')}",
            f"Location: {data.get('location', 'Unknown')}",
            f"Occupation: {data.get('occupation', 'Unknown')}",
            f"Interests: {', '.join(data.get('interests', []))}",
            f"Personality notes: {data.get('personality_notes', '')}",
        ]
        return "\n".join(parts)
