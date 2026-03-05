"""Streamlit app entry point — Assistant Studio."""

from __future__ import annotations

import streamlit as st

from src.app.ui.components import badge_row, recruiter_demo_expander
from src.app.ui.ui_state import init_state

st.set_page_config(
    layout="wide",
    page_title="Assistant Studio",
    page_icon="🧠",
    initial_sidebar_state="expanded",
)

init_state()

# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧠 Assistant Studio")
    st.text_input(
        "User ID",
        value=st.session_state["user_id"],
        key="user_id_input",
        on_change=lambda: st.session_state.update({"user_id": st.session_state["user_id_input"]}),
    )
    st.session_state["user_id"] = st.session_state.get("user_id_input", st.session_state["user_id"])

    # Load assistants for sidebar
    try:
        from src.app.ui.api_client import list_assistants

        assistants = list_assistants(st.session_state["user_id"])
        st.session_state["assistants_cache"] = assistants
    except Exception:
        assistants = st.session_state.get("assistants_cache", [])

    if assistants:
        names = [a["name"] for a in assistants]
        selected_idx = 0

        # Try to preserve selection
        current_id = st.session_state.get("selected_assistant_id")
        if current_id:
            for i, a in enumerate(assistants):
                if a["id"] == current_id:
                    selected_idx = i
                    break

        choice = st.selectbox("Select Assistant", names, index=selected_idx)
        selected = next((a for a in assistants if a["name"] == choice), None)
        if selected:
            st.session_state["selected_assistant_id"] = selected["id"]
            st.session_state["selected_assistant"] = selected

            # Mini card
            a_type = "RAG" if selected["type"] == "rag" else "Model-only"
            st.markdown(f"""
**{selected["name"]}**
- Type: `{a_type}`
- Provider: `{selected["provider"].title()}`
- Model: `{selected["model"]}`
            """)

    st.divider()
    st.page_link("src/ui/pages/0_Home_Gallery.py", label="🏠 Gallery", icon="🏠")
    st.page_link("src/ui/pages/1_Create_Assistant.py", label="➕ Create", icon="➕")

    a = st.session_state.get("selected_assistant")
    if a and a.get("type") == "rag":
        st.page_link("src/ui/pages/2_Upload_Documents.py", label="📄 Upload", icon="📄")
    if a:
        st.page_link("src/ui/pages/3_Chat_Assistant.py", label="💬 Chat", icon="💬")

# ── Main area (redirect to Gallery) ─────────────────────────────
st.markdown("# 🧠 Assistant Studio")
st.markdown("*Temporal-powered RAG ingestion + citations + reranking*")
st.markdown("---")

badge_row()
st.markdown("")
recruiter_demo_expander()

st.markdown("---")
st.info("👈 Use the sidebar to navigate, or go to the **Gallery** page to get started.")
st.page_link("src/ui/pages/0_Home_Gallery.py", label="Open Gallery →", icon="🏠")
