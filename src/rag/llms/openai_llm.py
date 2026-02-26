"""OpenAI LLM wrapper."""

from __future__ import annotations

from openai import AsyncOpenAI

from src.rag.llms.base import BaseLLM


class OpenAILLM(BaseLLM):
    """Async wrapper around OpenAI chat completions."""

    SUPPORTED_MODELS = [
        "gpt-4.1-mini",
        "gpt-4o-mini",
        "gpt-4.1",
        "gpt-4o",
        "gpt-3.5-turbo",
    ]

    def __init__(self, model: str = "gpt-4.1-mini", api_key: str | None = None):
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    async def agenerate(self, messages: list[dict]) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )
        return response.choices[0].message.content or ""
