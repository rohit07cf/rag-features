"""Page 1: Create a new assistant."""

from __future__ import annotations

import streamlit as st

from app.ui.components import recruiter_demo_expander, step_indicator
from app.ui.ui_state import init_state

init_state()

st.markdown("# ➕ Create Assistant")
step_indicator(current=0)
st.markdown("---")
recruiter_demo_expander()

# ── Provider / Model mappings ────────────────────────────────────
MODELS = {
    "openai": ["gpt-4.1-mini", "gpt-4o-mini", "gpt-4.1", "gpt-4o"],
    "anthropic": ["claude-3-5-sonnet", "claude-3-5-haiku", "claude-sonnet-4"],
}

CHUNK_STRATEGIES = {
    "recursive": "Recursive Character Splitting — general purpose, good default",
    "token": "Token-based — precise token count control",
    "heading_aware": "Heading-Aware — preserves document structure",
    "adaptive": "Adaptive — auto-selects best strategy per document",
    "contextual_docintel": "Azure Doc Intelligence — structural + contextual (requires Azure keys)",
}

# ── Form ─────────────────────────────────────────────────────────
with st.form("create_assistant_form"):
    st.markdown("### Assistant Configuration")

    name = st.text_input("Assistant Name", placeholder="e.g., Quarterly Report Analyst")

    col1, col2 = st.columns(2)
    with col1:
        a_type = st.selectbox(
            "Type",
            ["rag", "model_only"],
            format_func=lambda x: "RAG Chat" if x == "rag" else "Model-only Chat",
        )
    with col2:
        provider = st.selectbox(
            "LLM Provider",
            ["openai", "anthropic"],
            format_func=lambda x: "OpenAI GPT" if x == "openai" else "Anthropic Claude",
        )

    model = st.selectbox("Model", MODELS[provider])

    chunk_strategy = "recursive"
    if a_type == "rag":
        chunk_strategy = st.selectbox(
            "Default Chunk Strategy",
            list(CHUNK_STRATEGIES.keys()),
            format_func=lambda k: (
                f"{k} — {CHUNK_STRATEGIES[k].split('—')[1].strip()}"
                if "—" in CHUNK_STRATEGIES[k]
                else k
            ),
        )

    with st.expander("Advanced: System Prompt"):
        system_prompt = st.text_area(
            "Custom system prompt (optional)",
            placeholder="You are a helpful assistant that...",
            height=100,
        )

    submitted = st.form_submit_button("Create Assistant", type="primary", use_container_width=True)

if submitted:
    if not name.strip():
        st.error("Please enter an assistant name.")
    else:
        try:
            from app.ui.api_client import create_assistant

            result = create_assistant(
                {
                    "user_id": st.session_state["user_id"],
                    "name": name.strip(),
                    "type": a_type,
                    "provider": provider,
                    "model": model,
                    "system_prompt": system_prompt or "",
                    "default_chunk_strategy": chunk_strategy,
                }
            )

            st.session_state["selected_assistant_id"] = result["id"]
            st.session_state["selected_assistant"] = result
            st.toast(f"✅ Assistant '{name}' created!", icon="🎉")

            st.success(f"Assistant **{name}** created successfully!")

            if a_type == "rag":
                st.markdown("**Next step:** Upload documents to enable RAG.")
                if st.button("📄 Upload Documents →", type="primary"):
                    st.switch_page("pages/2_Upload_Documents.py")
            else:
                st.markdown("**Your assistant is ready!** Start chatting now.")
                if st.button("💬 Start Chatting →", type="primary"):
                    st.switch_page("pages/3_Chat_Assistant.py")

        except Exception as e:
            st.error(f"Failed to create assistant: {e}")
