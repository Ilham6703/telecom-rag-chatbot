"""
Application configuration.

This module is the single source of truth for all configurable values.
Never hardcode API keys, model names, file paths, or retrieval settings
outside this file.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project Root
ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Application Settings
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------

    OPENAI_API_KEY: str
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # ------------------------------------------------------------------
    # Cohere
    # ------------------------------------------------------------------

    COHERE_API_KEY: str
    COHERE_RERANK_MODEL: str = "rerank-v3.5"

    # ------------------------------------------------------------------
    # Qdrant
    # ------------------------------------------------------------------

    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION: str = "telecom_knowledge_base"

    # ------------------------------------------------------------------
    # Data Paths
    # ------------------------------------------------------------------

    RAW_DATA_DIR: Path = ROOT_DIR / "data" / "raw"
    PROCESSED_DATA_DIR: Path = ROOT_DIR / "data" / "processed"
    INDEX_DIR: Path = ROOT_DIR / "data" / "indexes"

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    MAX_CHUNK_TOKENS: int = 800
    CHUNK_OVERLAP_TOKENS: int = 100

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    VECTOR_TOP_K: int = 10
    BM25_TOP_K: int = 10
    RERANK_TOP_K: int = 5

    MIN_RETRIEVAL_SCORE: float = 0.35

    # ------------------------------------------------------------------
    # Conversation
    # ------------------------------------------------------------------

    MAX_HISTORY_MESSAGES: int = 15

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached settings object.

    This ensures environment variables are loaded only once.
    """
    return Settings()


settings = get_settings()