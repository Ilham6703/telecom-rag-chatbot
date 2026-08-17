"""
DOCX Parser

Reads a 3GPP DOCX specification and converts it into a structured
document tree while preserving hierarchy and tables.

Responsibilities:
- Read DOCX
- Ignore TOC
- Ignore Editor Notes
- Preserve Heading hierarchy
- Preserve document order
- Extract tables
- Return structured sections

Does NOT:
- Chunk text
- Generate embeddings
- Store anything
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from docx import Document
from docx.document import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph


# ---------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------


@dataclass
class Section:

    number: str
    title: str
    level: int

    content: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    children: List["Section"] = field(default_factory=list)


# ---------------------------------------------------------------------
# DOCX Helpers
# ---------------------------------------------------------------------


def iter_block_items(document: DocxDocument):
    """
    Iterate through paragraphs and tables
    while preserving document order.
    """

    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl

    parent = document.element.body

    for child in parent.iterchildren():

        if isinstance(child, CT_P):
            yield Paragraph(child, document)

        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def table_to_markdown(table: Table) -> str:
    """
    Convert Word table into markdown.
    """

    rows = []

    for row in table.rows:
        rows.append(
            [cell.text.strip().replace("\n", " ") for cell in row.cells]
        )

    if not rows:
        return ""

    header = "| " + " | ".join(rows[0]) + " |"
    separator = "| " + " | ".join(["---"] * len(rows[0])) + " |"

    body = []

    for row in rows[1:]:
        body.append("| " + " | ".join(row) + " |")

    return "\n".join([header, separator] + body)


# ---------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------


class DocumentParser:

    TOC_STYLES = {
        "toc 1",
        "toc 2",
        "toc 3",
        "toc 4",
        "toc 5",
        "toc 6",
        "toc 7",
        "toc 8",
    }

    SKIP_STYLES = {
        "Editor's Note",
    }

    def parse(self, file_path: str | Path) -> List[Section]:

        document = Document(file_path)

        root_sections: List[Section] = []

        stack: List[Section] = []

        current_section = None

        for block in iter_block_items(document):

            # ------------------------------
            # Paragraph
            # ------------------------------

            if isinstance(block, Paragraph):

                text = block.text.strip()

                if not text:
                    continue

                style = block.style.name

                if style.lower() in self.TOC_STYLES:
                    continue

                if style in self.SKIP_STYLES:
                    continue

                if style.startswith("Heading"):

                    try:
                        level = int(style.split()[-1])
                    except ValueError:
                        level = 1

                    if "\t" in text:
                        number, title = text.split("\t", 1)
                    else:
                        number = ""
                        title = text

                    section = Section(
                        number=number.strip(),
                        title=title.strip(),
                        level=level,
                    )

                    while stack and stack[-1].level >= level:
                        stack.pop()

                    if stack:
                        stack[-1].children.append(section)
                    else:
                        root_sections.append(section)

                    stack.append(section)
                    current_section = section

                    continue

                if current_section:
                    current_section.content.append(text)

            # ------------------------------
            # Table
            # ------------------------------

            elif isinstance(block, Table):

                if current_section:
                    markdown = table_to_markdown(block)

                    if markdown:
                        current_section.tables.append(markdown)

        return root_sections