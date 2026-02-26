"""Token budget management for context window packing."""

from __future__ import annotations


def _get_encoder():
    """Try to get tiktoken encoder, return None if unavailable."""
    try:
        import tiktoken
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None


def count_tokens(text: str) -> int:
    enc = _get_encoder()
    if enc:
        return len(enc.encode(text))
    # Fallback: rough estimate (~4 chars per token)
    return len(text) // 4


def fit_chunks_to_budget(
    chunks: list[dict],
    max_tokens: int = 3000,
) -> list[dict]:
    """Select chunks that fit within the token budget."""
    result: list[dict] = []
    total = 0
    for chunk in chunks:
        text = chunk.get("text", "")
        tokens = count_tokens(text)
        if total + tokens > max_tokens:
            break
        result.append(chunk)
        total += tokens
    return result
