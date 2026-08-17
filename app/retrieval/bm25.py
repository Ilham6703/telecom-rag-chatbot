"""
BM25 Retriever

Responsibilities
----------------
- Build BM25 index
- Save index
- Load index
- Keyword search

Does NOT:
- Generate embeddings
- Perform semantic search
- Call LLMs
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import List

from rank_bm25 import BM25Okapi

from app.config.settings import settings


class BM25Retriever:
    """
    Sparse keyword retriever using BM25.
    """

    def __init__(self):

        self.index_path = (
            settings.INDEX_DIR / "bm25.pkl"
        )

        self.documents_path = (
            settings.INDEX_DIR / "documents.pkl"
        )

        self.bm25 = None

        self.documents = []

        if (
            self.index_path.exists()
            and self.documents_path.exists()
        ):
            self.load()

    # ---------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """
        Simple tokenizer.

        Lowercase + whitespace split.

        Can be upgraded later if needed.
        """

        return text.lower().split()

    # ---------------------------------------------------------

    def build(
        self,
        chunks,
    ) -> None:
        """
        Build BM25 index.
        """

        self.documents = [
            {
                "text": chunk.text,
                **chunk.metadata,
            }
            for chunk in chunks
        ]

        corpus = [
            self._tokenize(doc["text"])
            for doc in self.documents
        ]

        self.bm25 = BM25Okapi(corpus)

    # ---------------------------------------------------------

    def save(self) -> None:
        """
        Save BM25 index.
        """

        self.index_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            self.index_path,
            "wb",
        ) as f:

            pickle.dump(
                self.bm25,
                f,
            )

        with open(
            self.documents_path,
            "wb",
        ) as f:

            pickle.dump(
                self.documents,
                f,
            )

    # ---------------------------------------------------------

    def load(self) -> None:
        """
        Load BM25 index.
        """

        with open(
            self.index_path,
            "rb",
        ) as f:

            self.bm25 = pickle.load(f)

        with open(
            self.documents_path,
            "rb",
        ) as f:

            self.documents = pickle.load(f)

    # ---------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int,
    ) -> List[dict]:
        """
        Sparse keyword search.
        """

        if self.bm25 is None:
            return []

        if not query or not query.strip():
            return []

        tokens = self._tokenize(query)

        scores = self.bm25.get_scores(tokens)

        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True,
        )

        results = []

        for index, score in ranked[:top_k]:

            document = dict(
                self.documents[index]
            )

            document["bm25_score"] = float(score)

            results.append(document)

        return results