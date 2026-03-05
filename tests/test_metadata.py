"""Tests for chunk metadata and contextual chunking."""

from __future__ import annotations

import pytest

from src.app.rag.chunking.base import Chunk
from src.app.rag.chunking.contextual_docintel import ContextualDocIntelChunker


class TestChunkMetadata:
    def test_chunk_to_dict(self):
        chunk = Chunk(
            text="test content",
            chunk_index=0,
            document_id="doc1",
            page_numbers=[1, 2],
            heading_path=["Intro", "Background"],
            section_title="Background",
            token_count=5,
        )
        d = chunk.to_dict()
        assert d["text"] == "test content"
        assert d["page_numbers"] == [1, 2]
        assert d["heading_path"] == ["Intro", "Background"]
        assert d["section_title"] == "Background"

    def test_chunk_defaults(self):
        chunk = Chunk(text="hello")
        d = chunk.to_dict()
        assert d["page_numbers"] == []
        assert d["heading_path"] == []
        assert d["document_id"] == ""


class TestContextualDocIntelChunker:
    def test_name(self):
        chunker = ContextualDocIntelChunker()
        assert chunker.name == "contextual_docintel"

    def test_chunk_from_paragraphs(self):
        """Test chunking from pre-extracted paragraphs (mock Azure output)."""
        paragraphs = [
            {"content": "Introduction", "role": "title", "page_number": 1},
            {
                "content": "This is the first paragraph of the document. " * 5,
                "role": "body",
                "page_number": 1,
            },
            {"content": "Methods", "role": "sectionHeading", "page_number": 1},
            {
                "content": "We analyzed the data using statistical methods. " * 5,
                "role": "body",
                "page_number": 2,
            },
            {
                "content": "Additional validation was performed. " * 5,
                "role": "body",
                "page_number": 2,
            },
        ]

        chunker = ContextualDocIntelChunker(max_chunk_size=300, min_chunk_size=10)
        chunks = chunker.chunk("", document_id="doc1", paragraphs=paragraphs)

        assert len(chunks) > 0
        # Should have heading paths from the structure
        methods_chunks = [c for c in chunks if "Methods" in c.heading_path]
        assert len(methods_chunks) > 0
        # Page numbers should be preserved
        assert any(2 in c.page_numbers for c in chunks)

    def test_fails_without_azure_when_no_paragraphs(self):
        """Should raise when Azure credentials are missing and no paragraphs provided."""
        chunker = ContextualDocIntelChunker()
        with pytest.raises(Exception):
            chunker.chunk("/fake/path.pdf", document_id="doc1")

    def test_small_paragraphs_merged(self):
        """Small paragraphs should be merged into larger chunks."""
        paragraphs = [
            {"content": "Short para 1.", "role": "body", "page_number": 1},
            {"content": "Short para 2.", "role": "body", "page_number": 1},
            {"content": "Short para 3.", "role": "body", "page_number": 1},
        ]
        chunker = ContextualDocIntelChunker(max_chunk_size=500, min_chunk_size=10)
        chunks = chunker.chunk("", document_id="doc1", paragraphs=paragraphs)

        # All short paragraphs should merge into one chunk
        assert len(chunks) == 1
        assert "Short para 1." in chunks[0].text
        assert "Short para 3." in chunks[0].text
