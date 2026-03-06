"""Tests for provider/model validation, sequential flow helpers, and retrieval pipeline namespace."""

from __future__ import annotations

import pytest
from pydantic import ValidationError


class TestProviderModelValidation:
    """Backend validation: provider/model combos must be valid."""

    def test_openai_with_valid_model(self):
        from app.api.schemas import AssistantCreate

        ac = AssistantCreate(
            user_id="u1",
            name="Bot",
            type="rag",
            provider="openai",
            model="gpt-4.1-mini",
        )
        assert ac.model == "gpt-4.1-mini"
        assert ac.provider.value == "openai"

    def test_anthropic_with_valid_model(self):
        from app.api.schemas import AssistantCreate

        ac = AssistantCreate(
            user_id="u1",
            name="Bot",
            type="model_only",
            provider="anthropic",
            model="claude-3-5-sonnet",
        )
        assert ac.model == "claude-3-5-sonnet"

    def test_openai_with_claude_model_rejected(self):
        from app.api.schemas import AssistantCreate

        with pytest.raises(ValidationError, match="not valid for provider"):
            AssistantCreate(
                user_id="u1",
                name="Bot",
                type="rag",
                provider="openai",
                model="claude-3-5-sonnet",
            )

    def test_anthropic_with_gpt_model_rejected(self):
        from app.api.schemas import AssistantCreate

        with pytest.raises(ValidationError, match="not valid for provider"):
            AssistantCreate(
                user_id="u1",
                name="Bot",
                type="rag",
                provider="anthropic",
                model="gpt-4o",
            )

    def test_unknown_model_rejected(self):
        from app.api.schemas import AssistantCreate

        with pytest.raises(ValidationError, match="not valid for provider"):
            AssistantCreate(
                user_id="u1",
                name="Bot",
                type="rag",
                provider="openai",
                model="made-up-model",
            )

    def test_invalid_provider_rejected(self):
        from app.api.schemas import AssistantCreate

        with pytest.raises(ValidationError):
            AssistantCreate(
                user_id="u1",
                name="Bot",
                type="rag",
                provider="google",
                model="gemini-pro",
            )


class TestProviderModelMapping:
    """The factory provider/model mapping is consistent and complete."""

    def test_openai_models_are_all_openai(self):
        from app.rag.llms.factory import PROVIDER_MODELS

        for model in PROVIDER_MODELS["openai"]:
            assert "claude" not in model.lower()

    def test_anthropic_models_are_all_claude(self):
        from app.rag.llms.factory import PROVIDER_MODELS

        for model in PROVIDER_MODELS["anthropic"]:
            assert "claude" in model.lower()

    def test_provider_models_matches_aliases(self):
        from app.rag.llms.factory import MODEL_ALIASES, PROVIDER_MODELS

        for provider in ("openai", "anthropic"):
            assert set(PROVIDER_MODELS[provider]) == set(MODEL_ALIASES[provider].keys())


class TestEmbedBatchesNamespace:
    """Verify embed_batches passes namespace=assistant_id to upsert."""

    def test_upsert_receives_namespace(self):
        """Read the embed_batches source to verify namespace is passed."""
        with open("app/workflows/activities/embed_batches.py") as f:
            source = f.read()
        assert "namespace=assistant_id" in source, (
            "embed_batches must pass namespace=assistant_id to store.upsert_vectors()"
        )


class TestRetrievalPipelineNamespace:
    """Verify retrieval pipeline queries with namespace=assistant_id."""

    def test_retrieval_queries_by_namespace(self):
        """Read the retrieval pipeline source to verify namespace usage."""
        import inspect
        from app.domain.pipelines.retrieval_pipeline import RetrievalPipeline

        source = inspect.getsource(RetrievalPipeline.run)
        assert "namespace=assistant_id" in source, (
            "RetrievalPipeline.run must query with namespace=assistant_id"
        )


class TestSequentialFlow:
    """Verify UI pages enforce sequential gating."""

    def test_chat_page_gates_rag_without_documents(self):
        """Chat page source should call st.stop() for RAG assistants without docs."""
        import inspect
        import app.ui.pages  # noqa: F401
        import importlib

        # Read the chat page source directly
        with open("app/ui/pages/3_Chat_Assistant.py") as f:
            source = f.read()

        # Should block RAG assistants without documents
        assert "st.stop()" in source
        assert "Upload" in source

    def test_create_page_auto_navigates(self):
        """Create page should auto-navigate after creation."""
        with open("app/ui/pages/1_Create_Assistant.py") as f:
            source = f.read()

        # Should auto-navigate to Upload for RAG or Chat for model-only
        assert 'st.switch_page("pages/2_Upload_Documents.py")' in source
        assert 'st.switch_page("pages/3_Chat_Assistant.py")' in source

    def test_gallery_disables_chat_for_unready_rag(self):
        """Gallery should disable Chat button for RAG assistants without documents."""
        with open("app/ui/pages/0_Home_Gallery.py") as f:
            source = f.read()

        assert "disabled=chat_disabled" in source
        assert "Upload documents first" in source
