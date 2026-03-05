"""Activity: save chunks to temporary file to avoid large Temporal payloads."""

from __future__ import annotations

import json
import os
import tempfile

from temporalio import activity


@activity.defn
async def save_chunks_to_file(params: dict) -> str:
    """Save chunks list to temporary JSON file.

    This avoids passing large chunk lists through Temporal payloads,
    which have a 4MB hard limit.

    Args:
        params: {"chunks": list[dict], "document_id": str}

    Returns:
        str — path to the temporary JSON file
    """
    chunks = params["chunks"]
    document_id = params["document_id"]

    chunks_file = os.path.join(tempfile.gettempdir(), f"chunks_{document_id}.json")

    activity.logger.info(
        "Saving %d chunks to %s for document %s",
        len(chunks),
        chunks_file,
        document_id,
    )

    with open(chunks_file, "w") as f:
        json.dump(chunks, f)

    activity.logger.info("Chunks saved successfully")
    return chunks_file
