"""Anthropic Claude LLM wrapper."""

from __future__ import annotations

import logging

from anthropic import AsyncAnthropic, NotFoundError

from app.rag.llms.base import BaseLLM


class AnthropicLLM(BaseLLM):
    """Async wrapper around Anthropic Messages API."""

    logger = logging.getLogger(__name__)

    SUPPORTED_MODELS = [
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
        "claude-sonnet-4-latest",
    ]

    def __init__(self, model: str = "claude-3-5-sonnet-latest", api_key: str | None = None):
        self._model = model
        self._client = AsyncAnthropic(api_key=api_key) if api_key else AsyncAnthropic()

    def _candidate_models(self) -> list[str]:
        """Return candidate models to try if the selected model is unavailable.

        Anthropic model availability can vary by account/region and can change
        over time. We keep a pragmatic fallback chain to avoid hard failures.
        """
        fallbacks: dict[str, list[str]] = {
            "claude-3-5-sonnet-latest": [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-sonnet-20240620",
                "claude-3-7-sonnet-latest",
                "claude-sonnet-4-latest",
            ],
            "claude-3-5-haiku-latest": [
                "claude-3-5-haiku-20241022",
                "claude-3-5-haiku-20240307",
                "claude-3-haiku-20240307",
                "claude-sonnet-4-latest",
            ],
            "claude-sonnet-4-latest": [
                "claude-sonnet-4-20250514",
                "claude-3-7-sonnet-latest",
                "claude-3-5-sonnet-latest",
            ],
        }

        candidates = [self._model, *fallbacks.get(self._model, []), *self.SUPPORTED_MODELS]
        # De-duplicate while preserving order
        deduped: list[str] = []
        for model in candidates:
            if model not in deduped:
                deduped.append(model)
        return deduped

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

        base_kwargs = {
            "max_tokens": 2048,
            "messages": chat_messages,
        }
        if system_text.strip():
            base_kwargs["system"] = system_text.strip()

        last_not_found: NotFoundError | None = None
        for candidate_model in self._candidate_models():
            try:
                response = await self._client.messages.create(
                    model=candidate_model,
                    **base_kwargs,
                )
                # Keep model_name accurate in API responses after a fallback.
                self._model = candidate_model
                return response.content[0].text if response.content else ""
            except NotFoundError as exc:
                last_not_found = exc
                self.logger.warning("Anthropic model unavailable: %s", candidate_model)
                continue

        if last_not_found is not None:
            raise last_not_found
        raise RuntimeError("Anthropic generation failed without a recoverable error")
