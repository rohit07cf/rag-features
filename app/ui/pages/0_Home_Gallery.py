"""Home Gallery — default landing page showing all assistants."""

from __future__ import annotations

import streamlit as st

from app.ui.components import badge_row, recruiter_demo_expander
from app.ui.ui_state import init_state

init_state()

st.markdown("# 🏠 Assistant Gallery")
st.markdown("*Your AI assistants at a glance*")
badge_row()
st.markdown("")
recruiter_demo_expander()
st.markdown("---")

# ── Create CTA ───────────────────────────────────────────────────
col_cta, col_refresh = st.columns([3, 1])
with col_cta:
    if st.button("➕ Create New Assistant", type="primary", use_container_width=True):
        st.switch_page("pages/1_Create_Assistant.py")
with col_refresh:
    refresh = st.button("🔄 Refresh", use_container_width=True)

# ── Load assistants ──────────────────────────────────────────────
user_id = st.session_state.get("user_id", "demo_user")

try:
    from app.ui.api_client import get_rag_status, list_assistants

    assistants = list_assistants(user_id)
except Exception as e:
    st.warning(f"Could not connect to API: {e}")
    assistants = []

if not assistants:
    st.markdown("---")
    st.markdown(
        """
### No assistants yet

Create your first assistant to get started. You can choose:
- **Model-only Chat** — Direct conversation with GPT or Claude
- **RAG Chat** — Upload documents, ingest with Temporal, and chat with citations
"""
    )
else:
    st.markdown(f"### {len(assistants)} Assistant{'s' if len(assistants) != 1 else ''}")

    # Grid layout (3 columns)
    cols = st.columns(3)
    for i, a in enumerate(assistants):
        with cols[i % 3]:
            a_type = a.get("type", "model_only")
            provider = a.get("provider", "openai")
            model = a.get("model", "")

            type_color = "#4F46E5" if a_type == "rag" else "#6B7280"
            type_label = "RAG" if a_type == "rag" else "Model-only"
            provider_color = "#10B981" if provider == "openai" else "#F59E0B"

            # Get RAG status
            status_html = ""
            is_ready = True
            if a_type == "rag":
                try:
                    rag_info = get_rag_status(a["id"])
                    if rag_info.get("has_documents"):
                        status_html = '<span style="color:#10B981;font-weight:600;">✅ Ready</span>'
                    else:
                        status_html = (
                            '<span style="color:#F59E0B;font-weight:600;">📄 Needs documents</span>'
                        )
                        is_ready = False
                except Exception:
                    status_html = '<span style="color:#6B7280;">Unknown</span>'

            st.markdown(
                f"""
<div style="border:1px solid #E5E7EB;border-radius:12px;padding:16px;margin-bottom:12px;background:white;min-height:180px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
        <strong style="font-size:1.05em;">{a.get("name", "Untitled")}</strong>
        <span style="background:{type_color};color:white;padding:2px 10px;border-radius:8px;font-size:0.72em;">{type_label}</span>
    </div>
    <div style="margin-bottom:8px;">
        <span style="background:{provider_color};color:white;padding:2px 8px;border-radius:6px;font-size:0.7em;">{provider.title()} · {model}</span>
    </div>
    <div style="color:#6B7280;font-size:0.78em;margin-bottom:8px;">Created: {a.get("created_at", "")[:16]}</div>
    <div>{status_html}</div>
</div>
""",
                unsafe_allow_html=True,
            )

            btn_cols = st.columns(2)
            with btn_cols[0]:
                if st.button("💬 Chat", key=f"chat_{a['id']}", use_container_width=True):
                    st.session_state["selected_assistant_id"] = a["id"]
                    st.session_state["selected_assistant"] = a
                    st.switch_page("pages/3_Chat_Assistant.py")
            with btn_cols[1]:
                if a_type == "rag" and not is_ready:
                    if st.button("📄 Upload", key=f"upload_{a['id']}", use_container_width=True):
                        st.session_state["selected_assistant_id"] = a["id"]
                        st.session_state["selected_assistant"] = a
                        st.switch_page("pages/2_Upload_Documents.py")

# ── What this demonstrates ───────────────────────────────────────
st.markdown("---")
st.markdown("""
### What This Demonstrates

- **Durable Ingestion Pipelines** — Temporal.io workflows survive failures and provide real-time progress tracking
- **Multi-Provider LLM Routing** — Seamlessly switch between OpenAI GPT and Anthropic Claude at the assistant level
- **Production RAG Architecture** — Vector search + cross-encoder reranking + contextual chunking + cited answers
""")
