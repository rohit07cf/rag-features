"""Retrieval pipeline — Template Method pattern.

RAG (Retrieval-Augmented Generation) is a technique that enhances LLM responses by:
1. Retrieving relevant information from a knowledge base before generating answers
2. Providing the LLM with factual context to reduce hallucinations
3. Enabling citations and source attribution

This pipeline implements the "Retrieve" part of RAG:
- Convert user query to vector embeddings
- Search for similar content in vector database
- Rerank results for better relevance
- Pack context within token limits

Staged pipeline: embed query → vector search → rerank → pack context.
Each stage is pluggable via protocol interfaces.
"""

from __future__ import annotations

from app.domain.protocols import Embedder, Reranker, VectorStore
from app.rag.utils.token_budget import fit_chunks_to_budget


class RetrievalPipeline:
    """Orchestrates the multi-stage retrieval process.

    RAG Flow in Real-Time:
    1. User asks: "What are the benefits of renewable energy?"
    2. Query gets converted to vector (numerical representation)
    3. Vector database finds similar stored document chunks
    4. Reranker improves ranking using cross-encoders
    5. Top chunks packed into LLM context window
    6. LLM generates answer using retrieved facts + citations

    Each component is injected, not hard-coded.
    """

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        reranker: Reranker,
    ):
        self._embedder = embedder
        self._vector_store = vector_store
        self._reranker = reranker

    async def run(
        self,
        query: str,
        assistant_id: str,
        top_k: int = 8,
        rerank_top_k: int = 4,
        max_context_tokens: int = 3000,
    ) -> list[dict]:
        """Execute the full retrieval pipeline.

        Args:
            query: User's question (e.g., "How does solar power work?")
            assistant_id: Which knowledge base to search
            top_k: How many candidates to retrieve initially (8-10 is typical)
            rerank_top_k: How many to keep after reranking (4-5 is optimal)
            max_context_tokens: LLM context limit (3000-4000 tokens)

        Returns:
            List of chunk dicts with text, metadata, and relevance scores.
            These chunks will be fed to the LLM as context.
        """
        # Stage 1: Convert natural language query to vector
        # Example: "What is machine learning?" → [0.1, -0.3, 0.8, ...] (1536 dimensions)
        # This allows mathematical similarity comparison
        query_vector = await self._embedder.embed_query(query)

        # Stage 2: Vector Search - Find similar content
        # Uses cosine similarity: higher score = more relevant
        # Filters by assistant_id to search only relevant documents
        candidates = self._vector_store.query(
            vector=query_vector,
            top_k=top_k,  # Get 8 candidates initially
            namespace=assistant_id,  # Isolate per assistant
            filter={"assistant_id": assistant_id},  # Additional filtering
        )
        if not candidates:
            return []  # No relevant documents found

        # Stage 3: Rerank for Precision
        # Bi-encoder retrieval is fast but less accurate
        # Cross-encoder reranking is slower but more precise
        # Reduces 8 candidates down to top 4 most relevant
        reranked = self._reranker.rerank(query, candidates, top_k=rerank_top_k)

        # Stage 4: Token Budget Management
        # LLMs have context limits (e.g., GPT-4: 8192 tokens)
        # Pack as much relevant info as possible without exceeding limit
        # Prioritizes highest-scoring chunks
        return fit_chunks_to_budget(reranked, max_tokens=max_context_tokens)
