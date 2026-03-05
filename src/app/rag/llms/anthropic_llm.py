"""Anthropic Claude LLM wrapper."""

from __future__ import annotations

from anthropic import AsyncAnthropic

from src.app.rag.llms.base import BaseLLM


class AnthropicLLM(BaseLLM):
    """Async wrapper around Anthropic Messages API."""

    SUPPORTED_MODELS = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-sonnet-4-20250514",
    ]

    def __init__(self, model: str = "claude-3-5-sonnet-20241022", api_key: str | None = None):
        self._model = model
        self._client = AsyncAnthropic(api_key=api_key) if api_key else AsyncAnthropic()

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model

    async def agenerate(self, messages: list[dict]) -> str:
        # Separate system prompt from messages
        system_text = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text += msg["content"] + "\n"
            else:
                chat_messages.append(msg)

        # Ensure messages start with user role
        if not chat_messages or chat_messages[0]["role"] != "user":
            chat_messages.insert(0, {"role": "user", "content": "Hello."})

        kwargs = {
            "model": self._model,
            "max_tokens": 2048,
            "messages": chat_messages,
        }
        if system_text.strip():
            kwargs["system"] = system_text.strip()

        response = await self._client.messages.create(**kwargs)
        return response.content[0].text if response.content else ""
