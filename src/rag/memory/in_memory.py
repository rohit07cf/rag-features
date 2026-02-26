"""Simple in-memory conversation store."""

from __future__ import annotations

from collections import defaultdict

from src.rag.memory.base import BaseMemory


class InMemoryStore(BaseMemory):
    """Thread-safe in-memory conversation history.

    Note: In production, replace with Redis or DB-backed store.
    """

    _store: dict[str, list[dict]] = defaultdict(list)

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        self._store[conversation_id].append({"role": role, "content": content})

    def get_history(self, conversation_id: str, max_turns: int = 10) -> list[dict]:
        history = self._store.get(conversation_id, [])
        # Return last N turns (each turn = user + assistant = 2 messages)
        return history[-(max_turns * 2) :]

    def clear(self, conversation_id: str) -> None:
        self._store.pop(conversation_id, None)
