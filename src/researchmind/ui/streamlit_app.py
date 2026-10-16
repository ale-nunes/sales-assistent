"""Minimal Phase 2 Streamlit dashboard."""

import streamlit as st

from researchmind.config import get_settings

st.set_page_config(
    page_title="ResearchMind",
    page_icon="🔎",
    layout="wide",
)

settings = get_settings()

st.title("ResearchMind")
st.caption("Multi-agent research assistant · Phase 2")

st.info(
    "The current milestone validates configuration and project setup. "
    "RAG, Gemini calls, Telegram workflows, and Gmail integration "
    "arrive in later phases."
)

left, right = st.columns(2)

with left:
    st.subheader("Configuration")
    st.write(f"Environment: `{settings.app_env}`")
    st.write(f"Generation model: `{settings.gemini_model}`")
    st.write(f"Embedding model: `{settings.gemini_embedding_model}`")
    st.write(f"Critic iteration limit: `{settings.max_critic_iterations}`")

with right:
    st.subheader("Credential status")
    st.write(
        "Gemini API key:",
        "configured" if settings.gemini_api_key else "not configured",
    )
    st.write(
        "Telegram bot token:",
        "configured" if settings.telegram_bot_token else "not configured",
    )
    st.write(
        "Gmail read-only mode:",
        "enabled" if settings.gmail_read_only else "disabled",
    )
    st.write(
        "Gmail draft creation:",
        "enabled" if settings.gmail_allow_draft_creation else "disabled",
    )

st.warning(
    "Never share screenshots containing credentials. "
    "This page intentionally does not show secret values."
)
