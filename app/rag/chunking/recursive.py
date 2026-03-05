"""Recursive character text splitter (LangChain-backed)."""

from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.chunking.base import BaseChunker, Chunk


class RecursiveChunker(BaseChunker):
    """Split text recursively by separators with overlap."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 200):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    @property
    def name(self) -> str:
        return "recursive"

    def chunk(self, text: str, document_id: str = "", **kwargs) -> list[Chunk]:
        splits = self._splitter.split_text(text)
        return [
            Chunk(
                text=s,
                chunk_index=i,
                document_id=document_id,
            )
            for i, s in enumerate(splits)
        ]
