"""OpenAI embeddings wrapper.

Embeddings are the "magic" that makes RAG possible. They convert human language
into numerical vectors that computers can understand and compare.

How Embeddings Work:
1. Text input: "The cat sat on the mat"
2. Neural network processes the text
3. Output: [0.123, -0.456, 0.789, ...] (1536 numbers for text-embedding-3-small)
4. Similar meanings = similar vectors (cosine similarity)

Real-Time Example:
- "I love cats" → [0.1, 0.2, 0.3, ...]
- "I adore felines" → [0.09, 0.21, 0.31, ...] (very similar vectors)
- "I hate quantum physics" → [-0.8, 0.1, -0.5, ...] (very different vector)

This allows finding relevant documents even when exact keywords don't match!
"""

from __future__ import annotations

from openai import AsyncOpenAI

from app.rag.embeddings.base import BaseEmbedder


class OpenAIEmbedder(BaseEmbedder):
    """text-embedding-3-small via OpenAI API.

    Why text-embedding-3-small?
    - 1536 dimensions: Good balance of accuracy vs speed
    - Trained on diverse internet text
    - Captures semantic meaning, not just keywords
    - Fast and cost-effective for production RAG

    Real-time usage:
    - Document ingestion: Convert chunks to vectors for storage
    - Query time: Convert user question to vector for search
    - Similarity: Compare question vector to document vectors
    """

    def __init__(self, model: str = "text-embedding-3-small", api_key: str | None = None, dimensions: int = 1024):
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()
        self._dim = dimensions

    @property
    def dimension(self) -> int:
        """Vector dimensionality - all embeddings from this model have this size."""
        return self._dim

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Convert multiple text chunks to vectors.

        Batch processing is more efficient than individual calls.
        OpenAI API accepts up to 2048 texts per request.

        Example:
        Input: ["What is AI?", "Machine learning explained"]
        Output: [[0.1, 0.2, ...], [0.3, 0.4, ...]]
        """
        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
            dimensions=self._dim,
        )
        # Extract vectors from API response
        return [item.embedding for item in response.data]

    async def embed_query(self, text: str) -> list[float]:
        """Convert a single query to vector.

        Used for searching - converts user question to same vector space
        as stored document chunks for similarity comparison.

        Example: "How do neural networks work?" → [0.1, -0.3, 0.8, ...]
        """
        results = await self.embed_texts([text])
        return results[0]  # Return single vector (not list of lists)
