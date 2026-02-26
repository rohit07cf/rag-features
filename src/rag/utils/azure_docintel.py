"""Azure Document Intelligence client wrapper.

Provides structural document analysis (headings, paragraphs, pages)
for contextual chunking.
"""

from __future__ import annotations

import os


class AzureDocIntelError(Exception):
    """Raised when Azure Doc Intel is unavailable or fails."""


class AzureDocIntelClient:
    """Wrapper around Azure AI Document Intelligence (Form Recognizer)."""

    def __init__(
        self,
        endpoint: str | None = None,
        key: str | None = None,
        model: str | None = None,
    ):
        self.endpoint = endpoint or os.getenv("AZURE_DOCINTEL_ENDPOINT", "")
        self.key = key or os.getenv("AZURE_DOCINTEL_KEY", "")
        self.model = model or os.getenv("AZURE_DOCINTEL_MODEL", "prebuilt-layout")

        if not self.endpoint or not self.key:
            raise AzureDocIntelError(
                "Azure Document Intelligence credentials not configured. "
                "Set AZURE_DOCINTEL_ENDPOINT and AZURE_DOCINTEL_KEY environment variables."
            )

    def _get_client(self):
        """Lazy-init the Azure SDK client."""
        from azure.ai.formrecognizer import DocumentAnalysisClient
        from azure.core.credentials import AzureKeyCredential

        return DocumentAnalysisClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key),
        )

    def analyze_document(self, file_path: str) -> list[dict]:
        """Analyze a document file and return structured paragraphs.

        Returns:
            List of dicts with keys: content, role, page_number, bounding_regions
        """
        client = self._get_client()

        with open(file_path, "rb") as f:
            poller = client.begin_analyze_document(self.model, f)
            result = poller.result()

        paragraphs: list[dict] = []
        for para in result.paragraphs or []:
            page_num = 0
            if para.bounding_regions:
                page_num = para.bounding_regions[0].page_number

            paragraphs.append({
                "content": para.content,
                "role": para.role or "body",
                "page_number": page_num,
            })

        return paragraphs

    def analyze_document_bytes(self, data: bytes) -> list[dict]:
        """Analyze document from bytes."""
        import io

        client = self._get_client()
        poller = client.begin_analyze_document(self.model, io.BytesIO(data))
        result = poller.result()

        paragraphs: list[dict] = []
        for para in result.paragraphs or []:
            page_num = 0
            if para.bounding_regions:
                page_num = para.bounding_regions[0].page_number
            paragraphs.append({
                "content": para.content,
                "role": para.role or "body",
                "page_number": page_num,
            })
        return paragraphs
