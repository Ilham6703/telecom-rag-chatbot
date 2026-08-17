"""
Hybrid Retriever

Responsibilities
----------------
- Dense retrieval (Qdrant)
- Sparse retrieval (BM25)
- Merge candidates
- Rerank with Cohere
- Return best chunks

Does NOT:
- Generate embeddings
- Talk to GPT
- Build prompts
"""

from __future__ import annotations

from typing import List

import cohere
from langsmith import traceable

from app.config.settings import settings
from app.ingestion.embeddings import EmbeddingGenerator
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector_store import VectorStore


class HybridRetriever:

    def __init__(self):

        self.embedding_generator = EmbeddingGenerator()

        self.vector_store = VectorStore()

        self.bm25 = BM25Retriever()

        self.cohere = cohere.ClientV2(
            api_key=settings.COHERE_API_KEY
        )

    # ---------------------------------------------------------

    @traceable(name="HybridRetriever.retrieve")
    def retrieve(
        self,
        query: str,
    ) -> List[dict]:
        """
        Hybrid Retrieval

        1. Dense Search
        2. Sparse Search
        3. Merge
        4. Rerank
        """

        if not query or not query.strip():
            return []

        query_embedding = self.embedding_generator.embed_text(
            query
        )

        dense_results = self.vector_store.search(
            embedding=query_embedding,
            top_k=settings.VECTOR_TOP_K,
        )

        sparse_results = self.bm25.search(
            query=query,
            top_k=settings.BM25_TOP_K,
        )

        merged = self._merge_results(
            dense_results,
            sparse_results,
        )

        reranked = self._rerank(
            query=query,
            documents=merged,
        )

        return reranked

    # ---------------------------------------------------------

    def _merge_results(
        self,
        dense_results,
        sparse_results,
    ):
        """
        Merge results removing duplicates.
        """

        merged = {}

        for result in dense_results:

            key = (
                result.payload.get("document", ""),
                result.payload.get("section", ""),
                result.payload.get("chunk_index", 0),
            )

            merged[key] = result.payload

        for result in sparse_results:

            key = (
                result.get("document", ""),
                result.get("section", ""),
                result.get("chunk_index", 0),
            )

            if key not in merged:
                merged[key] = result

        return list(merged.values())

    # ---------------------------------------------------------

    def _rerank(
        self,
        query: str,
        documents: List[dict],
    ):
        """
        Cohere Rerank
        """

        if not documents:
            return []

        response = self.cohere.rerank(
            model=settings.COHERE_RERANK_MODEL,
            query=query,
            documents=[
                d["text"]
                for d in documents
            ],
            top_n=settings.RERANK_TOP_K,
        )

        results = []

        for item in response.results:

            if item.index >= len(documents):
                continue

            doc = documents[item.index]

            doc["rerank_score"] = item.relevance_score

            if (
                item.relevance_score
                >= settings.MIN_RETRIEVAL_SCORE
            ):
                results.append(doc)

        return results