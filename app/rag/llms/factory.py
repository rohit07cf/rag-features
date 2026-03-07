"""LLM factory — creates the right provider based on config."""

from __future__ import annotations

from app.rag.llms.anthropic_llm import AnthropicLLM
from app.rag.llms.base import BaseLLM
from app.rag.llms.openai_llm import OpenAILLM

# Friendly model name -> actual model ID mapping
MODEL_ALIASES: dict[str, dict[str, str]] = {
    "openai": {
        "gpt-4.1-mini": "gpt-4.1-mini",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-4.1": "gpt-4.1",
        "gpt-4o": "gpt-4o",
    },
    "anthropic": {
        # Friendly UI aliases
        "claude-3-5-sonnet": "claude-3-5-sonnet-latest",
        "claude-3-5-haiku": "claude-3-5-haiku-latest",
        "claude-sonnet-4": "claude-sonnet-4-latest",
        # Backward-compatibility for previously persisted dated IDs
        "claude-3-5-sonnet-20241022": "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-20241022": "claude-3-5-haiku-latest",
        "claude-sonnet-4-20250514": "claude-sonnet-4-latest",
    },
}

PROVIDER_MODELS: dict[str, list[str]] = {
    "openai": list(MODEL_ALIASES["openai"].keys()),
    "anthropic": list(MODEL_ALIASES["anthropic"].keys()),
}


def resolve_model(provider: str, model: str) -> str:
    """Resolve friendly model name to full model ID."""
    aliases = MODEL_ALIASES.get(provider, {})
    return aliases.get(model, model)


def create_llm(provider: str, model: str, api_key: str | None = None) -> BaseLLM:
    """Instantiate the right LLM wrapper.

    Args:
        provider: "openai" or "anthropic"
        model: Model name (friendly alias or full ID)
        api_key: Optional explicit API key

    Returns:
        An LLM instance implementing BaseLLM
    """
    resolved = resolve_model(provider, model)

    if provider == "openai":
        return OpenAILLM(model=resolved, api_key=api_key)
    elif provider == "anthropic":
        return AnthropicLLM(model=resolved, api_key=api_key)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
