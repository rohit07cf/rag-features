"""Page 2: Upload documents for RAG ingestion."""

from __future__ import annotations

import time

import streamlit as st

from src.ui.components import recruiter_demo_expander, step_indicator
from src.ui.ui_state import init_state

init_state()

st.markdown("# 📄 Upload Documents")
step_indicator(current=1)
st.markdown("---")
recruiter_demo_expander()

# ── Guard: need a RAG assistant ──────────────────────────────────
assistant = st.session_state.get("selected_assistant")
if not assistant:
    st.warning("No assistant selected. Please create or select one first.")
    if st.button("➕ Create Assistant"):
        st.switch_page("src/ui/pages/1_Create_Assistant.py")
    st.stop()

if assistant.get("type") != "rag":
    st.info(f"**{assistant['name']}** is a model-only assistant (no documents needed).")
    if st.button("💬 Go to Chat"):
        st.switch_page("src/ui/pages/3_Chat_Assistant.py")
    st.stop()

st.markdown(f"**Assistant:** {assistant['name']}  |  **Provider:** {assistant['provider'].title()} · {assistant['model']}")
st.markdown("---")

# ── Chunk strategy ───────────────────────────────────────────────
STRATEGIES = {
    "recursive": "Recursive — general purpose default",
    "token": "Token-based — precise token control",
    "heading_aware": "Heading-Aware — preserves structure",
    "adaptive": "Adaptive — auto-selects per document",
    "contextual_docintel": "Azure Doc Intelligence — contextual (requires Azure keys)",
}

chunk_strategy = st.selectbox(
    "Chunking Strategy",
    list(STRATEGIES.keys()),
    index=list(STRATEGIES.keys()).index(assistant.get("default_chunk_strategy", "recursive")),
    format_func=lambda k: STRATEGIES[k],
)

# ── File uploader ────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "Upload PDF or DOCX files",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
)

if uploaded_files and st.button("🚀 Start Ingestion", type="primary", use_container_width=True):
    from src.ui.api_client import get_ingestion_status, upload_documents

    # Prepare files
    files_data = []
    for f in uploaded_files:
        content = f.read()
        mime = "application/pdf" if f.name.endswith(".pdf") else "application/octet-stream"
        files_data.append((f.name, content, mime))

    # Upload
    with st.spinner("Uploading files..."):
        try:
            results = upload_documents(
                assistant_id=assistant["id"],
                user_id=st.session_state["user_id"],
                chunk_strategy=chunk_strategy,
                files=files_data,
            )
        except Exception as e:
            st.error(f"Upload failed: {e}")
            st.stop()

    st.success(f"Uploaded {len(results)} file(s). Ingestion started!")

    # ── Progress tracking ────────────────────────────────────────
    st.markdown("### Ingestion Progress")

    ingestion_ids = [r["ingestion_id"] for r in results]
    filenames = {r["ingestion_id"]: r["filename"] for r in results}

    # Create progress containers
    progress_containers = {}
    for ing_id in ingestion_ids:
        fname = filenames.get(ing_id, "file")
        progress_containers[ing_id] = {
            "label": st.empty(),
            "bar": st.progress(0),
            "status": st.empty(),
        }
        progress_containers[ing_id]["label"].markdown(f"**{fname}**")

    overall_bar = st.progress(0)
    status_text = st.empty()

    # Poll loop
    all_done = False
    max_polls = 300  # 5 minutes max

    for poll in range(max_polls):
        done_count = 0
        total_pct = 0

        for ing_id in ingestion_ids:
            try:
                status = get_ingestion_status(ing_id)
            except Exception:
                status = {"state": "unknown", "progress_pct": 0, "current_step": "unknown", "error_message": ""}

            pct = status.get("progress_pct", 0)
            step = status.get("current_step", "")
            state = status.get("state", "")
            total_pct += pct

            pc = progress_containers[ing_id]
            pc["bar"].progress(min(pct, 100))

            if state == "succeeded":
                pc["status"].success(f"✅ Complete")
                done_count += 1
            elif state == "failed":
                pc["status"].error(f"❌ Failed: {status.get('error_message', '')}")
                done_count += 1
            else:
                pc["status"].info(f"⏳ {step} ({pct}%)")

        avg_pct = total_pct // len(ingestion_ids) if ingestion_ids else 0
        overall_bar.progress(min(avg_pct, 100))
        status_text.markdown(f"**Overall:** {done_count}/{len(ingestion_ids)} complete ({avg_pct}%)")

        if done_count >= len(ingestion_ids):
            all_done = True
            break

        time.sleep(1)

    if all_done:
        st.balloons()
        st.success("🎉 All documents ingested! Your assistant is ready for chat.")
        if st.button("💬 Start Chatting →", type="primary", use_container_width=True):
            st.switch_page("src/ui/pages/3_Chat_Assistant.py")
    else:
        st.warning("Ingestion is still running. You can check back later or start chatting.")
