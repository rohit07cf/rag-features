"""Base LLM interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Minimal common interface for LLM providers."""

    @abstractmethod
    async def agenerate(self, messages: list[dict]) -> str:
        """Generate a completion from a list of messages.

        Args:
            messages: List of {"role": ..., "content": ...} dicts.

        Returns:
            The assistant's response text.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...
