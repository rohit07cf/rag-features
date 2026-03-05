"""Prompt templates for RAG conversations with citations."""

from __future__ import annotations

RAG_SYSTEM_TEMPLATE = """You are a knowledgeable assistant that answers questions based on the provided context documents.

INSTRUCTIONS:
1. Answer ONLY based on the provided context. If the context doesn't contain enough information, say so clearly.
2. Include citations in your answer using [Source N] format where N corresponds to the source number.
3. When referencing specific information, include the page number if available: [Source N, p.X].
4. Be concise and well-structured. Use bullet points for lists.
5. If multiple sources support a point, cite all relevant ones.

{custom_system_prompt}"""

CONTEXT_TEMPLATE = """
--- CONTEXT SOURCES ---
{context_block}
--- END CONTEXT ---
"""

SOURCE_TEMPLATE = """[Source {index}] (Document: {document_id}, Pages: {pages})
Heading: {heading}
{text}
"""


def build_rag_prompt(
    query: str,
    chunks: list[dict],
    system_prompt: str = "",
    history: list[dict] | None = None,
) -> list[dict]:
    """Build the full message list for a RAG completion.

    Returns:
        List of message dicts ready for the LLM.
    """
    # Build context block from chunks
    source_blocks = []
    for i, chunk in enumerate(chunks, 1):
        pages = chunk.get("page_numbers", [])
        pages_str = ", ".join(str(p) for p in pages) if pages else "N/A"
        heading = " > ".join(chunk.get("heading_path", [])) or "N/A"

        source_blocks.append(
            SOURCE_TEMPLATE.format(
                index=i,
                document_id=chunk.get("document_id", "unknown"),
                pages=pages_str,
                heading=heading,
                text=chunk.get("text", ""),
            )
        )

    context_block = "\n".join(source_blocks)

    # Build system message
    system_text = RAG_SYSTEM_TEMPLATE.format(
        custom_system_prompt=system_prompt,
    )

    messages = [{"role": "system", "content": system_text}]

    # Add conversation history
    if history:
        messages.extend(history)

    # Add user message with context
    user_content = CONTEXT_TEMPLATE.format(context_block=context_block) + f"\nQuestion: {query}"
    messages.append({"role": "user", "content": user_content})

    return messages
