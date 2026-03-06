"""Activity: extract raw text from uploaded documents."""

from __future__ import annotations

import base64
import io
import os
import tempfile

from temporalio import activity


@activity.defn
async def extract_text(params: dict) -> str:
    """Extract text from PDF, DOCX, or TXT file content.

    Args:
        params: {"filename": str, "file_content_b64": str, "document_id": str}

    Returns:
        Raw extracted text
    """
    filename = params["filename"]
    file_content_b64 = params["file_content_b64"]
    ext = os.path.splitext(filename)[1].lower()

    content = base64.b64decode(file_content_b64)

    activity.logger.info("Extracting text from %s (type=%s, %d bytes)", filename, ext, len(content))

    if ext == ".txt":
        return content.decode("utf-8", errors="replace")

    elif ext == ".pdf":
        return _extract_pdf(content)

    elif ext == ".docx":
        return _extract_docx(content)

    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _extract_pdf(data: bytes) -> str:
    """Extract text from PDF bytes using PyPDF2."""
    from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append(f"[Page {i + 1}]\n{text}")
    return "\n\n".join(pages)


def _extract_docx(data: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    from docx import Document

    doc = Document(io.BytesIO(data))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)
