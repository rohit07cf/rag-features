"""Page 3: Chat with an assistant."""

from __future__ import annotations

import streamlit as st

from src.app.ui.components import recruiter_demo_expander, step_indicator
from src.app.ui.ui_state import init_state

init_state()

st.markdown("# 💬 Chat")
step_indicator(current=2)
st.markdown("---")
recruiter_demo_expander()

# ── Guard ────────────────────────────────────────────────────────
assistant = st.session_state.get("selected_assistant")
if not assistant:
    st.warning("No assistant selected. Please create or select one from the Gallery.")
    if st.button("🏠 Go to Gallery"):
        st.switch_page("src/ui/pages/0_Home_Gallery.py")
    st.stop()

# Check if RAG assistant needs documents
if assistant.get("type") == "rag":
    try:
        from src.app.ui.api_client import get_rag_status

        rag_info = get_rag_status(assistant["id"])
        if not rag_info.get("has_documents"):
            st.warning(
                "This RAG assistant has no documents yet. Upload documents first for best results."
            )
            if st.button("📄 Upload Documents"):
                st.switch_page("src/ui/pages/2_Upload_Documents.py")
    except Exception:
        pass

# ── Header ───────────────────────────────────────────────────────
a_type = "RAG" if assistant["type"] == "rag" else "Model-only"
st.markdown(
    f"**{assistant['name']}** · {a_type} · {assistant['provider'].title()} · `{assistant['model']}`"
)
st.markdown("---")

# ── Suggested prompts ────────────────────────────────────────────
if assistant["type"] == "rag":
    suggestions = [
        "Give me a 5-bullet summary with citations and page numbers",
        "Extract all action items from this document",
        "Explain the key findings with source references",
    ]
else:
    suggestions = [
        "Rewrite this text to be more professional",
        "Brainstorm 10 creative ideas for...",
        "Create a structured plan for...",
    ]

st.markdown("**Try these:**")
suggestion_cols = st.columns(len(suggestions))
for col, suggestion in zip(suggestion_cols, suggestions):
    if col.button(
        suggestion[:40] + "..." if len(suggestion) > 40 else suggestion,
        key=f"sug_{suggestion[:20]}",
        use_container_width=True,
    ):
        st.session_state["pending_message"] = suggestion

# ── Chat history ─────────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

for msg in st.session_state["chat_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Show sources for assistant RAG messages
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander(f"📚 Sources ({len(msg['sources'])} references)"):
                for i, src in enumerate(msg["sources"], 1):
                    pages = src.get("page_numbers", [])
                    pages_str = ", ".join(str(p) for p in pages) if pages else "N/A"
                    heading = " > ".join(src.get("heading_path", [])) or "N/A"

                    st.markdown(
                        f"""**[Source {i}]** Score: {src.get("score", 0):.3f}
- Document: `{src.get("document_id", "")}`
- Pages: {pages_str}
- Heading: {heading}
- Preview: _{src.get("text_snippet", "")[:150]}..._
"""
                    )

# ── Chat input ───────────────────────────────────────────────────
# Check for pending message from suggestion buttons
pending = st.session_state.pop("pending_message", None)
user_input = st.chat_input("Type your message...")

message = pending or user_input

if message:
    # Show user message
    st.session_state["chat_messages"].append({"role": "user", "content": message})
    with st.chat_message("user"):
        st.markdown(message)

    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                from src.app.ui.api_client import chat

                response = chat(
                    assistant_id=assistant["id"],
                    user_id=st.session_state["user_id"],
                    message=message,
                    conversation_id=st.session_state.get("conversation_id"),
                )

                st.session_state["conversation_id"] = response.get("conversation_id")
                answer = response.get("answer", "")
                sources = response.get("sources", [])

                st.markdown(answer)

                # Show sources
                if sources:
                    with st.expander(f"📚 Sources ({len(sources)} references)"):
                        for i, src in enumerate(sources, 1):
                            pages = src.get("page_numbers", [])
                            pages_str = ", ".join(str(p) for p in pages) if pages else "N/A"
                            heading = " > ".join(src.get("heading_path", [])) or "N/A"

                            st.markdown(
                                f"""**[Source {i}]** Score: {src.get("score", 0):.3f}
- Document: `{src.get("document_id", "")}`
- Pages: {pages_str}
- Heading: {heading}
- Preview: _{src.get("text_snippet", "")[:150]}..._
"""
                            )

                st.session_state["chat_messages"].append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    }
                )

            except Exception as e:
                error_msg = f"Error: {e}"
                st.error(error_msg)
                st.session_state["chat_messages"].append(
                    {
                        "role": "assistant",
                        "content": error_msg,
                    }
                )

# ── Clear chat button ────────────────────────────────────────────
if st.session_state["chat_messages"]:
    if st.button("🗑️ Clear conversation"):
        st.session_state["chat_messages"] = []
        st.session_state["conversation_id"] = None
        st.rerun()
