"""Base memory interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseMemory(ABC):
    @abstractmethod
    def add_message(self, conversation_id: str, role: str, content: str) -> None: ...

    @abstractmethod
    def get_history(self, conversation_id: str, max_turns: int = 10) -> list[dict]: ...

    @abstractmethod
    def clear(self, conversation_id: str) -> None: ...
