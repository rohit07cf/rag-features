"""Contextual chunker powered by Azure Document Intelligence.

Extracts structural metadata (headings, sections, page numbers) from the
document layout analysis and produces semantically rich chunks.
"""

from __future__ import annotations

from src.app.rag.chunking.base import BaseChunker, Chunk
from src.app.rag.utils.azure_docintel import AzureDocIntelClient


class ContextualDocIntelChunker(BaseChunker):
    """Chunk using Azure Document Intelligence layout analysis.

    Each chunk includes:
    - heading_path: hierarchy of headings leading to the chunk
    - section_title: immediate section heading
    - page_numbers: pages the chunk spans
    """

    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        client: AzureDocIntelClient | None = None,
    ):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self._client = client

    @property
    def name(self) -> str:
        return "contextual_docintel"

    def _get_client(self) -> AzureDocIntelClient:
        if self._client is None:
            self._client = AzureDocIntelClient()
        return self._client

    def chunk(self, text: str, document_id: str = "", **kwargs) -> list[Chunk]:
        """Chunk from pre-extracted paragraphs or fall back to text.

        If `paragraphs` kwarg is provided (from Azure Doc Intel extraction),
        use those directly. Otherwise, analyze text as a file path.
        """
        paragraphs = kwargs.get("paragraphs")

        if paragraphs is None:
            # text is a file path — run Azure analysis
            file_path = kwargs.get("file_path", text)
            client = self._get_client()
            paragraphs = client.analyze_document(file_path)

        return self._build_chunks(paragraphs, document_id)

    def _build_chunks(self, paragraphs: list[dict], document_id: str) -> list[Chunk]:
        """Merge paragraphs into appropriately sized chunks."""
        chunks: list[Chunk] = []
        current_text = ""
        current_pages: set[int] = set()
        current_heading_path: list[str] = []
        current_section: str = ""
        heading_stack: list[str] = []

        for para in paragraphs:
            role = para.get("role", "")
            content = para.get("content", "").strip()
            page = para.get("page_number", 0)

            if not content:
                continue

            # Track heading hierarchy
            if role.startswith("sectionHeading") or role == "title":
                heading_stack.append(content)
                current_section = content
                continue

            # Would adding this paragraph exceed max size?
            combined = f"{current_text}\n\n{content}" if current_text else content
            if len(combined) > self.max_chunk_size and current_text:
                chunks.append(
                    Chunk(
                        text=current_text.strip(),
                        chunk_index=len(chunks),
                        document_id=document_id,
                        page_numbers=sorted(current_pages),
                        heading_path=list(current_heading_path),
                        section_title=current_section,
                    )
                )
                current_text = content
                current_pages = {page} if page else set()
                current_heading_path = list(heading_stack)
            else:
                current_text = combined
                if page:
                    current_pages.add(page)
                current_heading_path = list(heading_stack)

        # Flush remaining
        if current_text.strip() and len(current_text.strip()) >= self.min_chunk_size:
            chunks.append(
                Chunk(
                    text=current_text.strip(),
                    chunk_index=len(chunks),
                    document_id=document_id,
                    page_numbers=sorted(current_pages),
                    heading_path=list(current_heading_path),
                    section_title=current_section,
                )
            )

        return chunks
