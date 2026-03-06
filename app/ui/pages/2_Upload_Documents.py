"""Page 2: Upload documents for RAG ingestion."""

from __future__ import annotations

import time

import streamlit as st

from app.ui.components import recruiter_demo_expander, step_indicator
from app.ui.ui_state import init_state

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
        st.switch_page("app/ui/pages/1_Create_Assistant.py")
    st.stop()

if assistant.get("type") != "rag":
    st.info(f"**{assistant['name']}** is a model-only assistant (no documents needed).")
    if st.button("💬 Go to Chat"):
        st.switch_page("app/ui/pages/3_Chat_Assistant.py")
    st.stop()

st.markdown(
    f"**Assistant:** {assistant['name']}  |  **Provider:** {assistant['provider'].title()} · {assistant['model']}"
)
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
    "Upload documents (PDF, DOCX, TXT)",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
    help="Select one or more files. Maximum 50MB per file. Supported: PDF, Word (.docx), Text (.txt)",
)

if uploaded_files:
    # Show file details
    st.markdown("### 📁 Selected Files")
    total_size = 0
    for i, file in enumerate(uploaded_files, 1):
        size_mb = len(file.read()) / (1024 * 1024)
        total_size += size_mb
        file.seek(0)  # Reset file pointer

        # Determine mime type
        if file.name.lower().endswith(".pdf"):
            mime_type = "application/pdf"
            icon = "📄"
        elif file.name.lower().endswith(".docx"):
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            icon = "📝"
        elif file.name.lower().endswith(".txt"):
            mime_type = "text/plain"
            icon = "📃"
        else:
            mime_type = "application/octet-stream"
            icon = "❓"

        st.write(f"{icon} **{file.name}** - {size_mb:.1f} MB ({mime_type})")

    st.markdown(f"**Total: {len(uploaded_files)} files, {total_size:.1f} MB**")

    # Size validation
    max_size_mb = 50
    oversized_files = [
        f.name for f in uploaded_files if len(f.read()) / (1024 * 1024) > max_size_mb
    ]
    for f in uploaded_files:
        f.seek(0)  # Reset all file pointers

    if oversized_files:
        st.error(f"❌ Files exceed {max_size_mb}MB limit: {', '.join(oversized_files)}")
        st.button("🚀 Start Ingestion", disabled=True)
    else:
        if st.button("🚀 Start Ingestion", type="primary", use_container_width=True):
            from app.ui.api_client import get_ingestion_status, upload_documents

            # Prepare files with proper mime types
            files_data = []
            for f in uploaded_files:
                content = f.read()

                # Determine correct mime type based on extension
                if f.name.lower().endswith(".pdf"):
                    mime = "application/pdf"
                elif f.name.lower().endswith(".docx"):
                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif f.name.lower().endswith(".txt"):
                    mime = "text/plain"
                else:
                    mime = "application/octet-stream"

                files_data.append((f.name, content, mime))

            # Upload with progress
            with st.spinner(f"Uploading {len(files_data)} file(s)... This may take a moment."):
                try:
                    results = upload_documents(
                        assistant_id=assistant["id"],
                        user_id=st.session_state["user_id"],
                        chunk_strategy=chunk_strategy,
                        files=files_data,
                    )
                except Exception as e:
                    st.error(f"❌ Upload failed: {e}")
                    st.stop()

            st.success(
                f"✅ Successfully uploaded {len(results)} file(s)! Ingestion workflows started."
            )

            # ── Progress tracking ────────────────────────────────────────
            st.markdown("### 📊 Ingestion Progress")

            ingestion_ids = [r["ingestion_id"] for r in results]
            filenames = {r["ingestion_id"]: r["filename"] for r in results}

            # Create progress containers
            progress_containers = {}
            for ing_id in ingestion_ids:
                fname = filenames.get(ing_id, "file")
                with st.container():
                    st.markdown(f"**{fname}**")
                    progress_containers[ing_id] = {
                        "bar": st.progress(0),
                        "status": st.empty(),
                    }

            # Poll for progress
            import time

            completed = set()

            while len(completed) < len(ingestion_ids):
                for ing_id in ingestion_ids:
                    if ing_id in completed:
                        continue

                    try:
                        status = get_ingestion_status(ing_id)
                        progress_pct = status.get("progress_pct", 0)
                        current_step = status.get("current_step", "unknown")

                        # Update progress
                        progress_containers[ing_id]["bar"].progress(min(progress_pct, 100))
                        progress_containers[ing_id]["status"].text(
                            f"{current_step} ({progress_pct}%)"
                        )

                        if current_step == "succeeded":
                            progress_containers[ing_id]["status"].text("✅ Complete")
                            completed.add(ing_id)
                        elif current_step == "failed":
                            progress_containers[ing_id]["status"].text("❌ Failed")
                            completed.add(ing_id)

                    except Exception as e:
                        progress_containers[ing_id]["status"].text(f"⚠️ Error: {e}")

                if len(completed) < len(ingestion_ids):
                    time.sleep(2)  # Poll every 2 seconds

            st.success("🎉 All files processed! You can now chat with your documents.")
else:
    st.info("💡 Select files to upload and configure your ingestion settings above.")
