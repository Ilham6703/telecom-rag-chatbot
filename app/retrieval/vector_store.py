"""
Qdrant Vector Store

Responsibilities
----------------
- Connect to Qdrant
- Create collection
- Upsert chunks
- Semantic search
- Delete collection

This module knows NOTHING about:
- OpenAI
- BM25
- GPT
- Chunking

Single Responsibility Principle.
"""
from __future__ import annotations

import time
import uuid
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from app.config.settings import settings
from app.ingestion.chunker import Chunk


class VectorStore:
    """
    Thin wrapper around Qdrant.
    """

    def __init__(self):

        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=60,
        )

        self.collection_name = settings.QDRANT_COLLECTION

    # --------------------------------------------------------

    def create_collection(
        self,
        vector_size: int,
    ) -> None:
        """
        Create collection if it doesn't exist.
        """

        collections = self.client.get_collections()

        existing = {
            c.name
            for c in collections.collections
        }

        if self.collection_name in existing:
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

    # --------------------------------------------------------

    def delete_collection(self) -> None:
        """
        Delete collection.
        Useful during development.
        """

        collections = self.client.get_collections()

        existing = {
            c.name
            for c in collections.collections
        }

        if self.collection_name in existing:

            self.client.delete_collection(
                self.collection_name
            )

    # --------------------------------------------------------

    def upsert(
        self,
        chunks: List[Chunk],
        embeddings: List[List[float]],
    ) -> None:
        """
        Store chunks + vectors.
        """

        if not embeddings:
            raise ValueError("Embeddings cannot be empty.")

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Chunks and embeddings must have the same length."
            )

        points = []

        for chunk, vector in zip(chunks, embeddings):

            payload = {
                "text": chunk.text,
                **chunk.metadata,
            }

            doc = payload.get("document", "")
            section = payload.get("section", "")
            chunk_index = payload.get("chunk_index", 0)
            chunk_id = f"{doc}:{section}:{chunk_index}"
            payload["chunk_id"] = chunk_id

            point_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    chunk_id,
                )
            )

            points.append(

                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )

            )

        batch_size = 50

        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            for attempt in range(3):
                try:
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=batch,
                    )
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    print(
                        f"Batch {i // batch_size + 1} failed (attempt {attempt + 1}), retrying: {e}"
                    )
                    time.sleep(2 ** attempt)

    # --------------------------------------------------------

    def search(
        self,
        embedding: List[float],
        top_k: int,
    ):
        """
        Semantic vector search.
        """

        return self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=top_k,
        ).points

    # --------------------------------------------------------

    def count(self) -> int:
        """
        Number of indexed vectors.
        """

        result = self.client.count(
            collection_name=self.collection_name
        )

        return result.count