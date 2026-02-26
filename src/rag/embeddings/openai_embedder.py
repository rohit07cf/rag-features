"""OpenAI embeddings wrapper."""

from __future__ import annotations

from openai import AsyncOpenAI

from src.rag.embeddings.base import BaseEmbedder


class OpenAIEmbedder(BaseEmbedder):
    """text-embedding-3-small via OpenAI API."""

    def __init__(self, model: str = "text-embedding-3-small", api_key: str | None = None):
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()
        self._dim = 1536

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    async def embed_query(self, text: str) -> list[float]:
        results = await self.embed_texts([text])
        return results[0]
