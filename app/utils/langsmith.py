"""LangSmith tracing initialization for observability only.

This module does not modify application logic or call the LLM.
It only enables/disables LangSmith tracing based on environment variables.
"""

from __future__ import annotations

import os

_LANGSMITH_INITIALIZED = False


def initialize_langsmith() -> None:
    """Initialize LangSmith tracing if configuration is present.

    The chatbot behavior is unchanged if tracing is disabled or not configured.
    """

    global _LANGSMITH_INITIALIZED

    if _LANGSMITH_INITIALIZED:
        return

    tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2")
    api_key = os.getenv("LANGCHAIN_API_KEY")
    project = os.getenv("LANGCHAIN_PROJECT")
    endpoint = os.getenv("LANGCHAIN_ENDPOINT")

    if not tracing_v2 or tracing_v2.lower() not in {"true", "1", "yes", "on"}:
        return

    if not api_key:
        return

    try:
        from langsmith import Client
    except Exception:
        return

    if project:
        os.environ["LANGCHAIN_PROJECT"] = project
    if endpoint:
        os.environ["LANGCHAIN_ENDPOINT"] = endpoint

    _ = Client()
    _LANGSMITH_INITIALIZED = True


__all__ = ["initialize_langsmith"]
