"""Conversation summarizer for long contexts."""

from __future__ import annotations

SUMMARIZE_PROMPT = """Summarize the following conversation in 2-3 sentences,
preserving key facts, decisions, and context needed for future turns:

{conversation}

Summary:"""


async def summarize_history(
    messages: list[dict],
    llm,
) -> str:
    """Summarize conversation history to fit within context limits.

    Args:
        messages: Full conversation history
        llm: An LLM instance with agenerate()

    Returns:
        A concise summary string
    """
    conversation_text = "\n".join(
        f"{m['role'].title()}: {m['content']}" for m in messages
    )

    summary_messages = [
        {
            "role": "user",
            "content": SUMMARIZE_PROMPT.format(conversation=conversation_text),
        }
    ]

    return await llm.agenerate(summary_messages)
