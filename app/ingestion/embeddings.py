"""
OpenAI Embedding Generator

Responsibilities
----------------
- Generate embeddings
- Batch requests
- Handle retries
- Return vectors

Does NOT:
- Store vectors
- Chunk documents
- Search vectors
"""

from __future__ import annotations

import time
from typing import List

from openai import OpenAI

from app.config.settings import settings


class EmbeddingGenerator:
    """
    Generates embeddings using OpenAI.
    """

    def __init__(self):

        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY
        )

        self.model = settings.OPENAI_EMBEDDING_MODEL

    # --------------------------------------------------------

    def embed_text(
        self,
        text: str,
    ) -> List[float]:
        """
        Generate embedding for a single text.
        """

        response = self.client.embeddings.create(
            model=self.model,
            input=text,
        )

        return response.data[0].embedding

    # --------------------------------------------------------

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100,
    ) -> List[List[float]]:
        """
        Generate embeddings in batches.

        More efficient than one request per chunk.
        """

        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):

            batch = texts[i:i + batch_size]

            success = False

            attempts = 0

            while not success:

                try:

                    response = self.client.embeddings.create(
                        model=self.model,
                        input=batch,
                    )

                    all_embeddings.extend(
                        [
                            item.embedding
                            for item in response.data
                        ]
                    )

                    success = True

                except Exception:

                    attempts += 1

                    if attempts >= 3:
                        raise

                    time.sleep(2)

        return all_embeddings