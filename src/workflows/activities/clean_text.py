"""Activity: clean and normalize extracted text."""

from __future__ import annotations

import re

from temporalio import activity


@activity.defn
async def clean_text(params: dict) -> str:
    """Clean extracted text: normalize whitespace, remove artifacts.

    Args:
        params: {"text": str, "document_id": str}

    Returns:
        Cleaned text
    """
    text = params["text"]

    activity.logger.info("Cleaning text for document %s (%d chars)", params["document_id"], len(text))

    # Normalize Unicode
    text = text.replace("\u00a0", " ")  # non-breaking space
    text = text.replace("\u200b", "")   # zero-width space
    text = text.replace("\ufeff", "")   # BOM

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse excessive whitespace within lines
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse excessive blank lines (3+ -> 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove common PDF artifacts
    text = re.sub(r"Page \d+ of \d+", "", text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()
