"""Tests for domain services (ChatService, IngestionService, AssistantsService)."""

from __future__ import annotations

import os
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.domain.models.errors import NotFoundError, ValidationError
from src.domain.services.chat_service import ChatService
from src.domain.services.ingestion_service import IngestionService
from src.domain.services.assistants_service import AssistantsService


# ── ChatService ──────────────────────────────────────────────────


class FakeMemory:
    """Minimal ConversationMemory for testing."""

    def __init__(self):
        self._store: dict[str, list[dict]] = {}

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        self._store.setdefault(conversation_id, []).append({"role": role, "content": content})

    def get_history(self, conversation_id: str, max_turns: int = 10) -> list[dict]:
        return self._store.get(conversation_id, [])

    def clear(self, conversation_id: str) -> None:
        self._store.pop(conversation_id, None)


class FakeLLM:
    """Minimal LLMClient for testing."""

    def __init__(self, answer: str = "test answer"):
        self._answer = answer

    async def agenerate(self, messages: list[dict]) -> str:
        return self._answer

    @property
    def provider_name(self) -> str:
        return "fake"

    @property
    def model_name(self) -> str:
        return "fake-model"


class TestChatServiceModelOnly:
    @pytest.mark.asyncio
    async def test_basic_response(self):
        memory = FakeMemory()
        service = ChatService(memory=memory)
        llm = FakeLLM(answer="Hello from LLM")

        response = await service.chat_model_only(
            llm=llm,
            message="Hi there",
            system_prompt="You are helpful.",
        )

        assert response.answer == "Hello from LLM"
        assert response.conversation_id  # Should be auto-generated
        assert response.model_used == "fake-model"
        assert response.provider == "fake"
        assert response.sources == []

    @pytest.mark.asyncio
    async def test_preserves_conversation_id(self):
        memory = FakeMemory()
        service = ChatService(memory=memory)
        llm = FakeLLM()

        response = await service.chat_model_only(
            llm=llm, message="Hi", conversation_id="conv123"
        )
        assert response.conversation_id == "conv123"

    @pytest.mark.asyncio
    async def test_stores_in_memory(self):
        memory = FakeMemory()
        service = ChatService(memory=memory)
        llm = FakeLLM(answer="bot reply")

        response = await service.chat_model_only(
            llm=llm, message="user msg", conversation_id="c1"
        )

        history = memory.get_history("c1")
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "user msg"}
        assert history[1] == {"role": "assistant", "content": "bot reply"}


class TestChatServiceRag:
    @pytest.mark.asyncio
    async def test_raises_without_pipeline(self):
        memory = FakeMemory()
        service = ChatService(memory=memory, retrieval_pipeline=None)
        llm = FakeLLM()

        with pytest.raises(RuntimeError, match="RetrievalPipeline not configured"):
            await service.chat_rag(
                llm=llm,
                message="What is X?",
                assistant_id="a1",
            )

    @pytest.mark.asyncio
    async def test_rag_with_mock_pipeline(self):
        memory = FakeMemory()
        pipeline = AsyncMock()
        pipeline.run.return_value = [
            {
                "document_id": "d1",
                "chunk_id": "c1",
                "text": "Relevant chunk text",
                "score": 0.95,
                "page_numbers": [1],
                "heading_path": ["Intro"],
            }
        ]

        service = ChatService(memory=memory, retrieval_pipeline=pipeline)
        llm = FakeLLM(answer="Based on the context...")

        response = await service.chat_rag(
            llm=llm,
            message="What is X?",
            assistant_id="a1",
            conversation_id="rag_conv",
        )

        assert response.answer == "Based on the context..."
        assert len(response.sources) == 1
        assert response.sources[0].document_id == "d1"
        assert response.sources[0].score == 0.95
        pipeline.run.assert_called_once()


# ── IngestionService ─────────────────────────────────────────────


class TestIngestionServiceValidation:
    def test_validate_missing_assistant(self, db_session):
        service = IngestionService(db_session)
        with pytest.raises(NotFoundError, match="Assistant not found"):
            service.validate_upload("nonexistent_id", ["file.pdf"])

    def test_validate_non_rag_assistant(self, db_session):
        from src.app.storage import assistants_repo

        assistant = assistants_repo.create_assistant(
            db_session,
            user_id="user1",
            name="Model Bot",
            type="model_only",
            provider="openai",
            model="gpt-4.1-mini",
        )

        service = IngestionService(db_session)
        with pytest.raises(ValidationError, match="not a RAG assistant"):
            service.validate_upload(assistant.id, ["file.pdf"])

    def test_validate_unsupported_file_type(self, db_session):
        from src.app.storage import assistants_repo

        assistant = assistants_repo.create_assistant(
            db_session,
            user_id="user1",
            name="RAG Bot",
            type="rag",
            provider="openai",
            model="gpt-4.1-mini",
        )

        service = IngestionService(db_session)
        with pytest.raises(ValidationError, match="Unsupported file type"):
            service.validate_upload(assistant.id, ["data.csv"])

    def test_validate_success(self, db_session):
        from src.app.storage import assistants_repo

        assistant = assistants_repo.create_assistant(
            db_session,
            user_id="user1",
            name="RAG Bot",
            type="rag",
            provider="openai",
            model="gpt-4.1-mini",
        )

        service = IngestionService(db_session)
        # Should not raise
        service.validate_upload(assistant.id, ["doc.pdf", "notes.txt", "report.docx"])


class TestIngestionServiceStatus:
    def test_status_not_found(self, db_session):
        service = IngestionService(db_session)
        with pytest.raises(NotFoundError, match="Ingestion record not found"):
            service.get_ingestion_status("nonexistent")

    def test_status_returns_correct_data(self, db_session):
        from src.app.storage import assistants_repo

        assistant = assistants_repo.create_assistant(
            db_session,
            user_id="user1",
            name="RAG Bot",
            type="rag",
            provider="openai",
            model="gpt-4.1-mini",
        )

        record = assistants_repo.create_ingestion_record(
            db_session,
            assistant_id=assistant.id,
            user_id="user1",
            document_id="doc1",
            filename="test.pdf",
            state="running",
        )

        service = IngestionService(db_session)
        result = service.get_ingestion_status(record.id)

        assert result["ingestion_id"] == record.id
        assert result["state"] == "running"


# ── AssistantsService ────────────────────────────────────────────


class TestAssistantsService:
    def test_get_raises_not_found(self, db_session):
        service = AssistantsService(db_session)
        with pytest.raises(NotFoundError, match="Assistant not found"):
            service.get("fake_id")

    def test_create_and_get(self, db_session):
        service = AssistantsService(db_session)
        assistant = service.create(
            user_id="user1",
            name="Service Bot",
            type="rag",
            provider="anthropic",
            model="claude-3-5-sonnet",
        )
        assert assistant.name == "Service Bot"

        fetched = service.get(assistant.id)
        assert fetched.id == assistant.id

    def test_list_for_user(self, db_session):
        service = AssistantsService(db_session)
        service.create(
            user_id="svc_user",
            name="Bot A",
            type="model_only",
            provider="openai",
            model="gpt-4.1-mini",
        )
        service.create(
            user_id="svc_user",
            name="Bot B",
            type="rag",
            provider="openai",
            model="gpt-4o",
        )

        bots = service.list_for_user("svc_user")
        assert len(bots) == 2

    def test_get_rag_status(self, db_session):
        service = AssistantsService(db_session)
        assistant = service.create(
            user_id="rag_user",
            name="RAG Bot",
            type="rag",
            provider="openai",
            model="gpt-4.1-mini",
        )

        status = service.get_rag_status(assistant.id)
        assert status["has_documents"] is False
        assert status["num_docs"] == 0
