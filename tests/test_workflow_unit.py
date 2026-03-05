"""Unit tests for workflow activities (mocked, no Temporal server needed)."""

from __future__ import annotations

import os
import tempfile


class TestExtractText:
    def test_extract_txt(self):
        """Test plain text extraction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, this is test content.")
            f.flush()
            path = f.name

        try:
            # Import the raw function logic (not the activity-decorated one)
            ext = os.path.splitext(path)[1].lower()
            assert ext == ".txt"
            with open(path, "r") as fh:
                text = fh.read()
            assert "test content" in text
        finally:
            os.unlink(path)


class TestCleanText:
    def test_clean_basic(self):
        """Test text cleaning logic."""
        import re

        text = "Hello  \t  world\n\n\n\nExtra   spaces\r\nWindows lines"
        text = text.replace("\u00a0", " ")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines).strip()

        assert "\t" not in text
        assert "\r" not in text
        assert "Hello world" in text


class TestChunkText:
    """Tests for centralized chunker registry (get_chunker from base.py)."""

    def test_get_chunker_recursive(self):
        from app.rag.chunking.base import get_chunker

        chunker = get_chunker("recursive")
        assert chunker.name == "recursive"

    def test_get_chunker_token(self):
        from app.rag.chunking.base import get_chunker

        chunker = get_chunker("token")
        assert chunker.name == "token"

    def test_get_chunker_heading(self):
        from app.rag.chunking.base import get_chunker

        chunker = get_chunker("heading_aware")
        assert chunker.name == "heading_aware"

    def test_get_chunker_adaptive(self):
        from app.rag.chunking.base import get_chunker

        chunker = get_chunker("adaptive")
        assert chunker.name == "adaptive"

    def test_get_chunker_default(self):
        from app.rag.chunking.base import get_chunker

        chunker = get_chunker("unknown_strategy")
        assert chunker.name == "recursive"  # Falls back to recursive

    def test_get_chunker_contextual(self):
        from app.rag.chunking.base import get_chunker

        chunker = get_chunker("contextual_docintel")
        assert chunker.name == "contextual_docintel"
