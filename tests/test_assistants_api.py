"""Tests for assistant CRUD and RAG status logic."""

from __future__ import annotations


from app.storage.assistants_repo import (
    create_assistant,
    create_ingestion_record,
    get_assistant,
    get_rag_status,
    list_assistants,
    update_ingestion_state,
)


class TestAssistantsCRUD:
    def test_create_and_retrieve(self, db_session):
        assistant = create_assistant(
            db_session,
            user_id="user1",
            name="My Bot",
            type="rag",
            provider="openai",
            model="gpt-4.1-mini",
        )
        assert assistant.id
        assert assistant.name == "My Bot"

        fetched = get_assistant(db_session, assistant.id)
        assert fetched is not None
        assert fetched.provider == "openai"

    def test_list_by_user(self, db_session):
        for i in range(3):
            create_assistant(
                db_session,
                user_id="user2",
                name=f"Bot {i}",
                type="model_only",
                provider="anthropic",
                model="claude-3-5-haiku",
            )
        # Different user
        create_assistant(
            db_session,
            user_id="other_user",
            name="Other Bot",
            type="rag",
            provider="openai",
            model="gpt-4o",
        )

        user2_bots = list_assistants(db_session, "user2")
        assert len(user2_bots) == 3

        other_bots = list_assistants(db_session, "other_user")
        assert len(other_bots) == 1

    def test_get_nonexistent_returns_none(self, db_session):
        assert get_assistant(db_session, "fake_id") is None


class TestRagStatus:
    def test_no_ingestions(self, db_session):
        assistant = create_assistant(
            db_session,
            user_id="user_rag",
            name="RAG Bot",
            type="rag",
            provider="openai",
            model="gpt-4.1-mini",
        )
        status = get_rag_status(db_session, assistant.id)
        assert status["has_documents"] is False
        assert status["num_docs"] == 0
        assert status["last_ingestion_state"] is None

    def test_with_succeeded_ingestion(self, db_session):
        assistant = create_assistant(
            db_session,
            user_id="user_rag2",
            name="RAG Bot 2",
            type="rag",
            provider="openai",
            model="gpt-4.1-mini",
        )

        _record = create_ingestion_record(
            db_session,
            assistant_id=assistant.id,
            user_id="user_rag2",
            document_id="doc1",
            filename="test.pdf",
            state="succeeded",
        )

        status = get_rag_status(db_session, assistant.id)
        assert status["has_documents"] is True
        assert status["num_docs"] == 1
        assert status["last_ingestion_state"] == "succeeded"

    def test_with_failed_ingestion(self, db_session):
        assistant = create_assistant(
            db_session,
            user_id="user_rag3",
            name="RAG Bot 3",
            type="rag",
            provider="anthropic",
            model="claude-3-5-sonnet",
        )

        create_ingestion_record(
            db_session,
            assistant_id=assistant.id,
            user_id="user_rag3",
            document_id="doc_fail",
            filename="bad.pdf",
            state="failed",
        )

        status = get_rag_status(db_session, assistant.id)
        assert status["has_documents"] is False  # Failed doesn't count
        assert status["total_ingestions"] == 1

    def test_update_ingestion_state(self, db_session):
        assistant = create_assistant(
            db_session,
            user_id="user_update",
            name="Updatable Bot",
            type="rag",
            provider="openai",
            model="gpt-4o-mini",
        )

        record = create_ingestion_record(
            db_session,
            assistant_id=assistant.id,
            user_id="user_update",
            document_id="doc_update",
            filename="test.pdf",
            state="pending",
        )

        updated = update_ingestion_state(
            db_session,
            record.id,
            state="running",
            current_step="extracting",
            progress_pct=20,
        )

        assert updated.state == "running"
        assert updated.current_step == "extracting"
        assert updated.progress_pct == 20
        assert updated.updated_at is not None
