"""
Streamlit Frontend

Simple UI for interacting with the Telecom RAG Chatbot.
"""

import uuid

import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000/chat"
STREAM_API_URL = "http://127.0.0.1:8000/chat/stream"


st.set_page_config(
    page_title="Telecom RAG Chatbot",
    page_icon="📡",
    layout="wide",
)


# -----------------------------------------------------
# Styling (visual only — no logic below this block changes)
# -----------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --bg-base: #0B1220;
        --bg-panel: #131B2E;
        --bg-panel-user: #16213A;
        --border: #1E293B;
        --signal: #2DD4BF;
        --signal-dim: rgba(45, 212, 191, 0.15);
        --amber: #F59E0B;
        --text-primary: #E2E8F0;
        --text-muted: #7C8AA5;
    }

    .stApp {
        background: radial-gradient(circle at 15% 0%, #0E1830 0%, var(--bg-base) 55%);
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }

    /* Hide default Streamlit chrome that clutters the demo */
    #MainMenu, footer, header {visibility: hidden;}

    /* ---------- Header ---------- */
    .telecom-header {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 4px 0 18px 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 22px;
    }
    .telecom-header .pulse {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--signal);
        box-shadow: 0 0 0 0 rgba(45, 212, 191, 0.7);
        animation: pulse 2s infinite;
        flex-shrink: 0;
    }
    @keyframes pulse {
        0%   { box-shadow: 0 0 0 0 rgba(45, 212, 191, 0.55); }
        70%  { box-shadow: 0 0 0 9px rgba(45, 212, 191, 0); }
        100% { box-shadow: 0 0 0 0 rgba(45, 212, 191, 0); }
    }
    .telecom-header h1 {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.55rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
        color: #F1F5F9;
    }
    .telecom-header .meta {
        margin-left: auto;
        text-align: right;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: var(--text-muted);
        line-height: 1.5;
    }
    .telecom-header .meta .status {
        color: var(--signal);
        font-weight: 500;
    }
    .telecom-caption {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: var(--text-muted);
        margin-top: -14px;
        margin-bottom: 20px;
        letter-spacing: 0.01em;
    }
    .telecom-caption .sep { color: var(--border); margin: 0 8px; }
    .telecom-caption .spec-tag {
        color: var(--signal);
        background: var(--signal-dim);
        padding: 1px 7px;
        border-radius: 3px;
        font-size: 0.72rem;
    }

    /* ---------- Chat bubbles ---------- */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        padding: 4px 0 !important;
    }
    [data-testid="stChatMessageContent"] {
        border-radius: 12px !important;
        border: 1px solid var(--border) !important;
        padding: 14px 18px !important;
    }
    /* Assistant bubble */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
        background: var(--bg-panel) !important;
        border-left: 2px solid var(--signal) !important;
    }
    /* User bubble */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
        background: var(--bg-panel-user) !important;
        border-left: 2px solid var(--amber) !important;
    }

    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] li {
        color: var(--text-primary) !important;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    [data-testid="stChatMessageContent"] strong { color: #F1F5F9; }
    [data-testid="stChatMessageContent"] code {
        background: var(--signal-dim) !important;
        color: var(--signal) !important;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85em;
    }

    /* ---------- Chat input ---------- */
    [data-testid="stChatInput"] {
        border: 1px solid var(--border) !important;
        background: var(--bg-panel) !important;
        border-radius: 10px !important;
    }
    [data-testid="stChatInput"] textarea {
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ---------- Spinner text ---------- */
    .stSpinner > div {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        color: var(--text-muted);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------
# Session State
# -----------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


# -----------------------------------------------------
# Header (visual replacement for st.title / st.caption)
# -----------------------------------------------------

st.markdown(
    f"""
    <div class="telecom-header">
        <div class="pulse"></div>
        <h1>Telecom Spec Assistant</h1>
        <div class="meta">
            <div class="status">● live</div>
            <div>session {st.session_state.session_id[:8]}</div>
        </div>
    </div>
    <div class="telecom-caption">
        GPT-4o <span class="sep">/</span> Hybrid Retrieval (BM25 + Qdrant) <span class="sep">/</span> Cohere Rerank
        <span class="sep">·</span> indexed <span class="spec-tag">TS 23.501</span> <span class="spec-tag">TS 23.502</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------
# Display Chat History
# -----------------------------------------------------

for message in st.session_state.messages:

    avatar = "📡" if message["role"] == "assistant" else "🧑"

    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


# -----------------------------------------------------
# User Input
# -----------------------------------------------------

user_input = st.chat_input(
    "Ask a question about the 3GPP Telecom Standards..."
)

if user_input:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="📡"):

        with st.spinner("Retrieving & grounding response..."):

            try:

                response = requests.post(
                    STREAM_API_URL,
                    json={
                        "message": user_input,
                        "session_id": st.session_state.session_id,
                    },
                    stream=True,
                    timeout=180,
                )

                response.raise_for_status()

                answer_parts = []
                placeholder = st.empty()

                for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                    if not chunk:
                        continue
                    answer_parts.append(chunk)
                    placeholder.markdown("".join(answer_parts))

                answer = "".join(answer_parts).strip()

            except Exception as e:

                answer = f"Error: {e}"
                st.markdown(answer)
            else:
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )