"""Streamlit session state helpers."""

from __future__ import annotations

import streamlit as st


def init_state():
    """Initialize session state defaults."""
    defaults = {
        "user_id": "demo_user",
        "selected_assistant_id": None,
        "selected_assistant": None,
        "assistants_cache": [],
        "conversation_id": None,
        "chat_messages": [],
        "ingestion_ids": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_user_id() -> str:
    return st.session_state.get("user_id", "demo_user")


def set_assistant(assistant: dict):
    st.session_state["selected_assistant_id"] = assistant.get("id")
    st.session_state["selected_assistant"] = assistant


def get_assistant() -> dict | None:
    return st.session_state.get("selected_assistant")


def get_assistant_id() -> str | None:
    return st.session_state.get("selected_assistant_id")
