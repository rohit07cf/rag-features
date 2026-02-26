"""Reusable Streamlit UI components."""

from __future__ import annotations

import streamlit as st


def badge_row():
    """Render the technology badge row."""
    badges = [
        ("Temporal Workflows", "#4F46E5"),
        ("Azure Doc Intelligence", "#0078D4"),
        ("Pinecone", "#00B4AB"),
        ("Reranking", "#E11D48"),
        ("Memory", "#7C3AED"),
        ("LangChain", "#2DD4BF"),
    ]
    cols = st.columns(len(badges))
    for col, (label, color) in zip(cols, badges):
        col.markdown(
            f'<span style="background-color:{color};color:white;padding:4px 12px;'
            f'border-radius:12px;font-size:0.8em;font-weight:600;">{label}</span>',
            unsafe_allow_html=True,
        )


def recruiter_demo_expander():
    """Show the recruiter quick demo script."""
    with st.expander("🎯 Recruiter Quick Demo", expanded=False):
        st.markdown("""
**Try this 60-second demo:**

1. **Gallery** → Click **"Create New Assistant"**
2. Choose **RAG** type, pick **OpenAI GPT-4.1-mini**
3. Upload any PDF document
4. Watch the **real-time ingestion progress bar** (Temporal workflow!)
5. Once done, ask: *"Give me 5 bullet summary with citations and page numbers"*

**What you're seeing:**
- **Temporal.io** orchestrating a durable 5-step ingestion pipeline
- **Azure Document Intelligence** extracting document structure
- **Pinecone** storing vector embeddings
- **Cross-encoder reranking** for precision retrieval
- **Cited answers** with page numbers and heading paths
        """)


def assistant_card(assistant: dict, rag_status: dict | None = None, show_actions: bool = True):
    """Render an assistant card."""
    a_type = assistant.get("type", "model_only")
    provider = assistant.get("provider", "openai")
    model = assistant.get("model", "")

    type_color = "#4F46E5" if a_type == "rag" else "#6B7280"
    type_label = "RAG" if a_type == "rag" else "Model-only"

    provider_color = "#10B981" if provider == "openai" else "#F59E0B"
    provider_label = f"{provider.title()} · {model}"

    with st.container():
        st.markdown(
            f"""
<div style="border:1px solid #E5E7EB;border-radius:12px;padding:16px;margin-bottom:8px;background:white;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <h4 style="margin:0;">{assistant.get('name', 'Untitled')}</h4>
        <span style="background-color:{type_color};color:white;padding:2px 10px;border-radius:8px;font-size:0.75em;">{type_label}</span>
    </div>
    <div style="margin-bottom:8px;">
        <span style="background-color:{provider_color};color:white;padding:2px 8px;border-radius:6px;font-size:0.7em;">{provider_label}</span>
    </div>
    <div style="color:#6B7280;font-size:0.8em;">Created: {assistant.get('created_at', '')[:16]}</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if a_type == "rag" and rag_status:
            if rag_status.get("has_documents"):
                st.success("Ready", icon="✅")
            else:
                st.warning("Needs documents", icon="📄")


def step_indicator(current: int, total: int = 3):
    """Show step progress indicator."""
    steps = ["Create", "Upload", "Chat"]
    cols = st.columns(total)
    for i, (col, label) in enumerate(zip(cols, steps)):
        if i < current:
            col.markdown(f"✅ **{label}**")
        elif i == current:
            col.markdown(f"🔵 **{label}**")
        else:
            col.markdown(f"⚪ {label}")
