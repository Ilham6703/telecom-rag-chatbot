"""
Hierarchical Chunker

Converts the parsed document tree into semantic chunks ready
for embedding and retrieval.

Design Principles
-----------------
1. Chunk only leaf sections.
2. Never cross section boundaries.
3. Preserve document hierarchy.
4. Preserve tables.
5. Split only oversized leaf sections.
6. Generate rich metadata.
7. Produce embedding-ready chunks.
"""

from __future__ import annotations

import re

from dataclasses import dataclass, field
from typing import List

import tiktoken

from app.config.settings import settings
from app.ingestion.parser import Section


# ============================================================
# Chunk Model
# ============================================================


@dataclass
class Chunk:
    """
    Final chunk produced by the ingestion pipeline.
    """

    text: str
    metadata: dict = field(default_factory=dict)


# ============================================================
# Token Counter
# ============================================================


class TokenCounter:
    """
    Wrapper around tiktoken.

    Using token counts instead of character counts keeps
    chunk sizes aligned with the embedding model.
    """

    def __init__(self):

        self.encoding = tiktoken.encoding_for_model(
            settings.OPENAI_EMBEDDING_MODEL
        )

    def count(self, text: str) -> int:

        return len(self.encoding.encode(text))


# ============================================================
# Chunker
# ============================================================


class Chunker:

    def __init__(self):

        self.token_counter = TokenCounter()

        self.max_tokens = settings.MAX_CHUNK_TOKENS

        self.overlap = settings.CHUNK_OVERLAP_TOKENS

    # --------------------------------------------------------

    def chunk_document(
        self,
        sections: List[Section],
        spec: str,
        version: str,
        release: str,
        document_name: str,
    ) -> List[Chunk]:
        """
        Convert the parsed document tree into chunks.
        """

        chunks: List[Chunk] = []
        chunk_counter = {"value": 0}

        self._walk_tree(
            sections=sections,
            parent_titles=[],
            parent_numbers=[],
            spec=spec,
            version=version,
            release=release,
            document_name=document_name,
            chunks=chunks,
            chunk_counter=chunk_counter,
        )

        return chunks

    # --------------------------------------------------------

    def _walk_tree(
        self,
        sections: List[Section],
        parent_titles: List[str],
        parent_numbers: List[str],
        spec: str,
        version: str,
        release: str,
        document_name: str,
        chunks: List[Chunk],
        chunk_counter: dict,
    ):
        """
        Recursively traverse the document tree.

        Internal nodes recurse.

        Leaf nodes become chunks.
        """

        for section in sections:

            current_titles = parent_titles + [section.title]

            current_numbers = parent_numbers + [section.number]

            if section.children:

                self._walk_tree(
                    sections=section.children,
                    parent_titles=current_titles,
                    parent_numbers=current_numbers,
                    spec=spec,
                    version=version,
                    release=release,
                    document_name=document_name,
                    chunks=chunks,
                    chunk_counter=chunk_counter,
                )

            else:

                self._process_leaf(
                    section=section,
                    parent_titles=current_titles,
                    parent_numbers=current_numbers,
                    spec=spec,
                    version=version,
                    release=release,
                    document_name=document_name,
                    chunks=chunks,
                    chunk_counter=chunk_counter,
                )
        # --------------------------------------------------------

    def _process_leaf(
        self,
        section: Section,
        parent_titles: List[str],
        parent_numbers: List[str],
        spec: str,
        version: str,
        release: str,
        document_name: str,
        chunks: List[Chunk],
        chunk_counter: dict,
    ):
        """
        Convert one leaf section into one or more semantic chunks.
        """

        # ----------------------------------------------------
        # Build contextual heading
        # ----------------------------------------------------

        hierarchy = "\n".join(parent_titles)

        heading = f"{section.number} {section.title}".strip()

        body: List[str] = [
            f"Specification: {spec}",
            f"Release: {release}",
            "",
            hierarchy,
            "",
            heading,
            "",
        ]

        # ----------------------------------------------------
        # Add paragraph content
        # ----------------------------------------------------

        body.extend(section.content)

        # ----------------------------------------------------
        # Add tables
        # ----------------------------------------------------

        if section.tables:

            body.append("")

            body.extend(section.tables)

        full_text = "\n".join(body).strip()

        token_count = self.token_counter.count(full_text)

        # ----------------------------------------------------
        # Small enough
        # ----------------------------------------------------

        if token_count <= self.max_tokens:

            chunk_counter["value"] += 1

            chunks.append(

                self._create_chunk(

                    text=full_text,

                    chunk_index=chunk_counter["value"],

                    total_chunks=1,

                    spec=spec,

                    version=version,

                    release=release,

                    document_name=document_name,

                    section=section,

                    parent_titles=parent_titles,

                    parent_numbers=parent_numbers,

                )

            )

            return

        # ----------------------------------------------------
        # Large section
        # ----------------------------------------------------

        split_chunks = self._split_large_section(

            heading="\n".join(
                [
                    f"Specification: {spec}",
                    f"Release: {release}",
                    "",
                    hierarchy,
                    "",
                    heading,
                ]
            ),

            paragraphs=section.content,

            tables=section.tables,

        )

        total = len(split_chunks)

        for chunk_text in split_chunks:

            chunk_counter["value"] += 1

            chunks.append(

                self._create_chunk(

                    text=chunk_text,

                    chunk_index=chunk_counter["value"],

                    total_chunks=total,

                    spec=spec,

                    version=version,

                    release=release,

                    document_name=document_name,

                    section=section,

                    parent_titles=parent_titles,

                    parent_numbers=parent_numbers,

                )

            )

        # --------------------------------------------------------

    def _split_large_section(
        self,
        heading: str,
        paragraphs: List[str],
        tables: List[str],
    ) -> List[str]:
        """
        Split an oversized leaf section while preserving
        semantic boundaries.

        Priority:
        1. Paragraph
        2. Sentence
        3. Token window (last resort)
        """

        blocks = list(paragraphs)

        if tables:
            blocks.extend(tables)

        chunks: List[str] = []

        current_chunk = [heading, ""]
        current_tokens = self.token_counter.count("\n".join(current_chunk))

        for block in blocks:

            block_tokens = self.token_counter.count(block)

            # ------------------------------------------------
            # Block fits
            # ------------------------------------------------

            if current_tokens + block_tokens <= self.max_tokens:

                current_chunk.append(block)
                current_tokens += block_tokens
                continue

            # ------------------------------------------------
            # Save current chunk
            # ------------------------------------------------

            if len(current_chunk) > 2:

                chunks.append("\n".join(current_chunk).strip())

            # ------------------------------------------------
            # Huge paragraph
            # ------------------------------------------------

            if block_tokens > self.max_tokens:

                sentences = re.split(r'(?<=[.!?])\s+', block)

                current_chunk = [heading, ""]
                current_tokens = self.token_counter.count(
                    "\n".join(current_chunk)
                )

                for sentence in sentences:

                    sentence_tokens = self.token_counter.count(sentence)

                    if current_tokens + sentence_tokens <= self.max_tokens:

                        current_chunk.append(sentence)
                        current_tokens += sentence_tokens

                    else:

                        if len(current_chunk) > 2:

                            chunks.append(
                                "\n".join(current_chunk).strip()
                            )

                        # ------------------------------------
                        # Extremely large sentence
                        # ------------------------------------

                        if sentence_tokens > self.max_tokens:

                            encoded = self.token_counter.encoding.encode(
                                sentence
                            )

                            start = 0

                            while start < len(encoded):

                                end = min(
                                    start + self.max_tokens,
                                    len(encoded),
                                )

                                piece = self.token_counter.encoding.decode(
                                    encoded[start:end]
                                )

                                chunks.append(
                                    "\n".join(
                                        [heading, "", piece]
                                    ).strip()
                                )

                                if end == len(encoded):
                                    break

                                start = max(
                                    end - self.overlap,
                                    start + 1,
                                )

                            current_chunk = [heading, ""]
                            current_tokens = self.token_counter.count(
                                "\n".join(current_chunk)
                            )

                        else:

                            current_chunk = [
                                heading,
                                "",
                                sentence,
                            ]

                            current_tokens = self.token_counter.count(
                                "\n".join(current_chunk)
                            )

            else:

                current_chunk = [
                    heading,
                    "",
                    block,
                ]

                current_tokens = self.token_counter.count(
                    "\n".join(current_chunk)
                )

        if len(current_chunk) > 2:

            chunks.append(
                "\n".join(current_chunk).strip()
            )

        return chunks

    # --------------------------------------------------------

    def _create_chunk(
        self,
        text: str,
        chunk_index: int,
        total_chunks: int,
        spec: str,
        version: str,
        release: str,
        document_name: str,
        section: Section,
        parent_titles: List[str],
        parent_numbers: List[str],
    ) -> Chunk:
        """
        Create the final embedding-ready chunk.
        """

        metadata = {

            "spec": spec,

            "version": version,

            "release": release,

            "document": document_name,

            "section": section.number,

            "title": section.title,

            "parent_sections": parent_numbers,

            "section_path": " > ".join(parent_titles),

            "chunk_index": chunk_index,

            "total_chunks": total_chunks,

            "contains_table": bool(section.tables),

        }

        return Chunk(
            text=text,
            metadata=metadata,
        )