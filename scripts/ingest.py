"""
Knowledge Base Ingestion Script

Builds the searchable knowledge base from the
3GPP DOCX documents.
"""

from pathlib import Path

from app.config.settings import settings
from app.ingestion.indexer import KnowledgeIndexer


def main() -> None:
    """
    Run the ingestion pipeline.
    """

    raw_directory = settings.RAW_DATA_DIR

    if not raw_directory.exists():
        raise FileNotFoundError(
            f"Raw data directory not found: {raw_directory}"
        )

    print("=" * 60)
    print("Starting Knowledge Base Ingestion")
    print("=" * 60)

    indexer = KnowledgeIndexer()

    indexer.index_directory(raw_directory)

    print("\n" + "=" * 60)
    print("Knowledge Base built successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()