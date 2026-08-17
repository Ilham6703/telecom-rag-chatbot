"""
Knowledge Base Indexer

Pipeline

DOCX
   ↓
Parser
   ↓
Chunker
   ↓
Embeddings
   ↓
Qdrant

Builds the complete vector index.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from app.config.settings import settings
from app.ingestion.chunker import Chunker, Chunk
from app.ingestion.embeddings import EmbeddingGenerator
from app.ingestion.parser import DocumentParser
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector_store import VectorStore


class KnowledgeIndexer:
    """
    Builds the complete knowledge base.
    """

    def __init__(self):

        self.parser = DocumentParser()

        self.chunker = Chunker()

        self.embedding_generator = EmbeddingGenerator()

        self.vector_store = VectorStore()
        self.all_chunks: List[Chunk] = []

    # -------------------------------------------------------------

    def index_document(
        self,
        document_path: str | Path,
        spec: str,
        version: str,
        release: str,
    ) -> int:
        """
        Index a single DOCX document.

        Returns
        -------
        Number of chunks indexed.
        """

        document_path = Path(document_path)

        print(f"\nIndexing {document_path.name}")

        # ---------------------------------------------------------
        # Parse
        # ---------------------------------------------------------

        sections = self.parser.parse(document_path)

        # ---------------------------------------------------------
        # Chunk
        # ---------------------------------------------------------

        chunks: List[Chunk] = self.chunker.chunk_document(
            sections=sections,
            spec=spec,
            version=version,
            release=release,
            document_name=document_path.name,
        )

        self.all_chunks.extend(chunks)

        if not chunks:
            print(
                f"Warning: skipping {document_path.name} because no chunks were produced."
            )
            return 0

        print(f"Generated {len(chunks)} chunks")

        # ---------------------------------------------------------
        # Embeddings
        # ---------------------------------------------------------

        texts = [chunk.text for chunk in chunks]

        embeddings = self.embedding_generator.embed_batch(texts)

        print("Embeddings generated")

        # ---------------------------------------------------------
        # Create collection
        # ---------------------------------------------------------

        vector_size = len(embeddings[0])

        self.vector_store.create_collection(
            vector_size=vector_size
        )

        # ---------------------------------------------------------
        # Upload
        # ---------------------------------------------------------

        self.vector_store.upsert(
            chunks=chunks,
            embeddings=embeddings,
        )

        print("Stored in Qdrant")

        return len(chunks)

    # -------------------------------------------------------------

    def index_directory(
        self,
        directory: str | Path,
    ):
        """
        Index every DOCX inside a directory.
        """

        self.all_chunks = []
        self.vector_store.delete_collection()

        directory = Path(directory)

        files = sorted(
            directory.glob("*.docx")
        )

        if not files:
            raise FileNotFoundError(
                f"No DOCX files found in {directory}"
            )

        total_chunks = 0

        for file in files:

            # ---------------------------------------------
            # Extract metadata from filename
            #
            # Example:
            # 23501-ic0.docx
            # ---------------------------------------------

            stem = file.stem

            parts = stem.split("-")

            spec = parts[0]

            version = parts[1] if len(parts) > 1 else ""

            release = parts[1][0].upper() if len(parts) > 1 else ""

            total_chunks += self.index_document(
                document_path=file,
                spec=spec,
                version=version,
                release=release,
            )

        print("\n--------------------------------")

        print(f"Indexed {len(files)} documents")

        print(f"Total chunks : {total_chunks}")

        print("--------------------------------")