"""Tests for all chunking strategies."""

from __future__ import annotations


from app.rag.chunking.adaptive import AdaptiveChunker
from app.rag.chunking.heading_aware import HeadingAwareChunker
from app.rag.chunking.recursive import RecursiveChunker
from app.rag.chunking.token import TokenChunker


class TestRecursiveChunker:
    def test_basic_chunking(self, sample_text):
        chunker = RecursiveChunker(chunk_size=200, chunk_overlap=50)
        chunks = chunker.chunk(sample_text, document_id="doc1")
        assert len(chunks) > 0
        assert all(c.document_id == "doc1" for c in chunks)
        assert chunks[0].chunk_index == 0

    def test_name(self):
        assert RecursiveChunker().name == "recursive"

    def test_empty_text(self):
        chunker = RecursiveChunker()
        chunks = chunker.chunk("", document_id="empty")
        # LangChain may return empty list or single chunk
        assert isinstance(chunks, list)

    def test_short_text(self):
        chunker = RecursiveChunker(chunk_size=1000)
        chunks = chunker.chunk("Short text.", document_id="short")
        assert len(chunks) == 1
        assert chunks[0].text == "Short text."


class TestTokenChunker:
    def test_basic_chunking(self, sample_text):
        chunker = TokenChunker(max_tokens=100, overlap_tokens=20)
        chunks = chunker.chunk(sample_text, document_id="doc2")
        assert len(chunks) > 1
        assert all(c.document_id == "doc2" for c in chunks)

    def test_name(self):
        assert TokenChunker().name == "token"

    def test_produces_multiple_chunks_for_long_text(self):
        text = "word " * 500
        chunker = TokenChunker(max_tokens=50, overlap_tokens=10)
        chunks = chunker.chunk(text)
        assert len(chunks) > 1
        # Each chunk should have a token_count set
        assert all(c.token_count > 0 for c in chunks)


class TestHeadingAwareChunker:
    def test_preserves_heading_path(self, sample_text):
        chunker = HeadingAwareChunker()
        chunks = chunker.chunk(sample_text, document_id="doc3")
        assert len(chunks) > 0

        # Should have chunks with heading paths
        chunks_with_headings = [c for c in chunks if c.heading_path]
        assert len(chunks_with_headings) > 0

    def test_name(self):
        assert HeadingAwareChunker().name == "heading_aware"

    def test_no_headings(self):
        text = "Just plain text without any headings at all."
        chunker = HeadingAwareChunker()
        chunks = chunker.chunk(text)
        assert len(chunks) == 1


class TestAdaptiveChunker:
    def test_uses_heading_for_markdown(self, sample_text):
        chunker = AdaptiveChunker()
        chunks = chunker.chunk(sample_text, document_id="doc4")
        assert len(chunks) > 0

    def test_name(self):
        assert AdaptiveChunker().name == "adaptive"

    def test_long_plain_text(self):
        # Long text with few paragraphs -> should use token chunker
        text = "A " * 3000
        chunker = AdaptiveChunker()
        chunks = chunker.chunk(text)
        assert len(chunks) > 1
