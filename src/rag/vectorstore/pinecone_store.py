"""Pinecone vector store integration."""

from __future__ import annotations

import os
from typing import Optional

from src.rag.logging_helper import get_logger

logger = get_logger(__name__)


class PineconeStore:
    """Thin wrapper around Pinecone for upsert + query."""

    def __init__(
        self,
        api_key: str | None = None,
        index_name: str | None = None,
        host: str | None = None,
    ):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY", "")
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME", "rag-assistant")
        self.host = host or os.getenv("PINECONE_HOST", "")
        self._index = None

    def _get_index(self):
        if self._index is None:
            from pinecone import Pinecone

            pc = Pinecone(api_key=self.api_key)
            if self.host:
                self._index = pc.Index(host=self.host)
            else:
                self._index = pc.Index(self.index_name)
        return self._index

    def upsert_vectors(
        self,
        ids: list[str],
        vectors: list[list[float]],
        metadatas: list[dict],
        namespace: str = "",
        batch_size: int = 100,
    ) -> int:
        """Upsert vectors with metadata to Pinecone."""
        index = self._get_index()
        total = 0

        for i in range(0, len(ids), batch_size):
            batch = [
                {
                    "id": ids[j],
                    "values": vectors[j],
                    "metadata": metadatas[j],
                }
                for j in range(i, min(i + batch_size, len(ids)))
            ]
            index.upsert(vectors=batch, namespace=namespace)
            total += len(batch)

        logger.info("Upserted %d vectors to namespace=%s", total, namespace)
        return total

    def query(
        self,
        vector: list[float],
        top_k: int = 10,
        namespace: str = "",
        filter: Optional[dict] = None,
        include_metadata: bool = True,
    ) -> list[dict]:
        """Query Pinecone and return matches with metadata."""
        index = self._get_index()
        kwargs = {
            "vector": vector,
            "top_k": top_k,
            "namespace": namespace,
            "include_metadata": include_metadata,
        }
        if filter:
            kwargs["filter"] = filter

        response = index.query(**kwargs)
        results = []
        for match in response.get("matches", []):
            meta = match.get("metadata", {})
            results.append({
                "chunk_id": match["id"],
                "score": match["score"],
                "text": meta.get("text", ""),
                "document_id": meta.get("document_id", ""),
                "page_numbers": meta.get("page_numbers", []),
                "heading_path": meta.get("heading_path", []),
                "section_title": meta.get("section_title", ""),
            })
        return results

    def delete_by_filter(self, filter: dict, namespace: str = "") -> None:
        """Delete vectors matching a metadata filter."""
        index = self._get_index()
        index.delete(filter=filter, namespace=namespace)
