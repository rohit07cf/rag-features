"""Activity: extract raw text from uploaded documents."""

from __future__ import annotations

import os

from temporalio import activity


@activity.defn
async def extract_text(params: dict) -> str:
    """Extract text from PDF, DOCX, or TXT file.

    Args:
        params: {"file_path": str, "document_id": str}

    Returns:
        Raw extracted text
    """
    file_path = params["file_path"]
    ext = os.path.splitext(file_path)[1].lower()

    activity.logger.info("Extracting text from %s (type=%s)", file_path, ext)

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    elif ext == ".pdf":
        return _extract_pdf(file_path)

    elif ext == ".docx":
        return _extract_docx(file_path)

    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _extract_pdf(path: str) -> str:
    """Extract text from PDF using PyPDF2."""
    from PyPDF2 import PdfReader

    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append(f"[Page {i + 1}]\n{text}")
    return "\n\n".join(pages)


def _extract_docx(path: str) -> str:
    """Extract text from DOCX using python-docx."""
    from docx import Document

    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)
