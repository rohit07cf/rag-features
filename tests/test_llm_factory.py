"""Tests for LLM factory and model routing."""

from __future__ import annotations

import pytest

from app.rag.llms.anthropic_llm import AnthropicLLM
from app.rag.llms.factory import PROVIDER_MODELS, create_llm, resolve_model
from app.rag.llms.openai_llm import OpenAILLM


class TestResolveModel:
    def test_resolve_openai_alias(self):
        assert resolve_model("openai", "gpt-4.1-mini") == "gpt-4.1-mini"
        assert resolve_model("openai", "gpt-4o") == "gpt-4o"

    def test_resolve_anthropic_alias(self):
        resolved = resolve_model("anthropic", "claude-3-5-sonnet")
        assert resolved == "claude-3-5-sonnet-latest"

    def test_resolve_anthropic_legacy_id(self):
        resolved = resolve_model("anthropic", "claude-3-5-sonnet-20241022")
        assert resolved == "claude-3-5-sonnet-latest"

    def test_resolve_unknown_passes_through(self):
        assert resolve_model("openai", "custom-model") == "custom-model"


class TestCreateLLM:
    def test_creates_openai(self):
        llm = create_llm("openai", "gpt-4.1-mini", api_key="sk-test")
        assert isinstance(llm, OpenAILLM)
        assert llm.provider_name == "openai"
        assert llm.model_name == "gpt-4.1-mini"

    def test_creates_anthropic(self):
        llm = create_llm("anthropic", "claude-3-5-sonnet", api_key="sk-ant-test")
        assert isinstance(llm, AnthropicLLM)
        assert llm.provider_name == "anthropic"
        assert llm.model_name == "claude-3-5-sonnet-latest"

    def test_invalid_provider_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            create_llm("gemini", "gemini-pro")


class TestProviderModels:
    def test_openai_models_listed(self):
        assert "gpt-4.1-mini" in PROVIDER_MODELS["openai"]
        assert "gpt-4o" in PROVIDER_MODELS["openai"]

    def test_anthropic_models_listed(self):
        assert "claude-3-5-sonnet" in PROVIDER_MODELS["anthropic"]
        assert "claude-3-5-haiku" in PROVIDER_MODELS["anthropic"]
