"""Token-based chunker using tiktoken."""

from __future__ import annotations

from src.app.rag.chunking.base import BaseChunker, Chunk


class TokenChunker(BaseChunker):
    """Split text into chunks of N tokens with overlap.

    Falls back to character-based splitting if tiktoken
    encoding data is unavailable.
    """

    def __init__(
        self,
        max_tokens: int = 512,
        overlap_tokens: int = 64,
        encoding_name: str = "cl100k_base",
    ):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self._encoding_name = encoding_name
        self._enc = None
        self._use_fallback = False

    def _get_encoder(self):
        if self._enc is None and not self._use_fallback:
            try:
                import tiktoken

                self._enc = tiktoken.get_encoding(self._encoding_name)
            except Exception:
                self._use_fallback = True
        return self._enc

    @property
    def name(self) -> str:
        return "token"

    def chunk(self, text: str, document_id: str = "", **kwargs) -> list[Chunk]:
        enc = self._get_encoder()

        if enc is not None:
            return self._chunk_with_tiktoken(text, document_id, enc)
        else:
            return self._chunk_by_words(text, document_id)

    def _chunk_with_tiktoken(self, text: str, document_id: str, enc) -> list[Chunk]:
        tokens = enc.encode(text)
        chunks: list[Chunk] = []
        start = 0
        idx = 0

        while start < len(tokens):
            end = min(start + self.max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = enc.decode(chunk_tokens)
            chunks.append(
                Chunk(
                    text=chunk_text,
                    chunk_index=idx,
                    document_id=document_id,
                    token_count=len(chunk_tokens),
                )
            )
            start = end - self.overlap_tokens if end < len(tokens) else end
            idx += 1

        return chunks

    def _chunk_by_words(self, text: str, document_id: str) -> list[Chunk]:
        """Fallback: approximate token count using words (~0.75 tokens/word)."""
        words = text.split()
        # Approximate: 1 word ≈ 1.3 tokens, so max_tokens words ≈ max_tokens tokens
        words_per_chunk = max(1, int(self.max_tokens * 0.75))
        overlap_words = max(0, int(self.overlap_tokens * 0.75))

        chunks: list[Chunk] = []
        start = 0
        idx = 0

        while start < len(words):
            end = min(start + words_per_chunk, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            chunks.append(
                Chunk(
                    text=chunk_text,
                    chunk_index=idx,
                    document_id=document_id,
                    token_count=len(chunk_words),
                )
            )
            start = end - overlap_words if end < len(words) else end
            idx += 1

        return chunks
