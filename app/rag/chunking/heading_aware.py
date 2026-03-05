"""Heading-aware chunker that preserves document structure."""

from __future__ import annotations

import re

from app.rag.chunking.base import BaseChunker, Chunk


class HeadingAwareChunker(BaseChunker):
    """Split by markdown-style headings, preserving heading hierarchy."""

    def __init__(self, max_chunk_size: int = 1200):
        self.max_chunk_size = max_chunk_size

    @property
    def name(self) -> str:
        return "heading_aware"

    def chunk(self, text: str, document_id: str = "", **kwargs) -> list[Chunk]:
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        sections = self._split_by_headings(text, heading_pattern)

        chunks: list[Chunk] = []
        for idx, section in enumerate(sections):
            # If section is too long, split further
            if len(section["text"]) > self.max_chunk_size:
                sub_texts = self._split_long_section(section["text"])
                for sub_idx, sub_text in enumerate(sub_texts):
                    chunks.append(
                        Chunk(
                            text=sub_text,
                            chunk_index=len(chunks),
                            document_id=document_id,
                            heading_path=section["heading_path"],
                            section_title=section["title"],
                        )
                    )
            else:
                chunks.append(
                    Chunk(
                        text=section["text"],
                        chunk_index=len(chunks),
                        document_id=document_id,
                        heading_path=section["heading_path"],
                        section_title=section["title"],
                    )
                )
        return chunks

    def _split_by_headings(self, text: str, pattern) -> list[dict]:
        matches = list(pattern.finditer(text))
        if not matches:
            return [{"text": text.strip(), "heading_path": [], "title": ""}]

        sections = []
        heading_stack: list[tuple[int, str]] = []

        for i, match in enumerate(matches):
            level = len(match.group(1))
            title = match.group(2).strip()

            # Update heading stack
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))

            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()

            if section_text:
                sections.append(
                    {
                        "text": f"{title}\n\n{section_text}",
                        "heading_path": [h[1] for h in heading_stack],
                        "title": title,
                    }
                )

        # Text before first heading
        if matches and matches[0].start() > 0:
            preamble = text[: matches[0].start()].strip()
            if preamble:
                sections.insert(0, {"text": preamble, "heading_path": [], "title": ""})

        return sections or [{"text": text.strip(), "heading_path": [], "title": ""}]

    def _split_long_section(self, text: str) -> list[str]:
        paragraphs = text.split("\n\n")
        result: list[str] = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) > self.max_chunk_size and current:
                result.append(current.strip())
                current = para
            else:
                current = f"{current}\n\n{para}" if current else para
        if current.strip():
            result.append(current.strip())
        return result
