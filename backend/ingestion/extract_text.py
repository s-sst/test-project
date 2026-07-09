"""Text extraction interfaces (implementation: Phase 2).

Defines the stable contract the rest of the pipeline depends on. Concrete
extractors (PyMuPDF for born-digital PDFs, pdfplumber for tables/layout,
python-docx for DOCX) are implemented in Phase 2. Heavy libraries are imported
lazily *inside* the concrete implementations so importing this module — and
booting Django — never requires the optional ingestion dependencies.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ExtractedTable:
    page_number: int
    rows: list[list[str]] = field(default_factory=list)


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    is_scanned: bool = False
    tables: list[ExtractedTable] = field(default_factory=list)


@dataclass
class ExtractedDocument:
    """Normalised output of any text extractor — the pipeline's ingestion
    contract. Page-level structure is preserved so evidence can cite pages
    (Rule 2: every quote requires a page citation)."""

    pages: list[ExtractedPage]
    metadata: dict = field(default_factory=dict)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)


class TextExtractor(ABC):
    """Strategy interface for format-specific extraction."""

    #: file extensions this extractor handles, e.g. {"pdf"}
    supported_extensions: set[str] = set()

    @abstractmethod
    def extract(self, file_path: str) -> ExtractedDocument:  # pragma: no cover
        ...


def extract_text(file_path: str, *, extension: str | None = None) -> ExtractedDocument:
    """Facade: dispatch to the right extractor for ``file_path``.

    TODO(phase-2): implement PyMuPDF/pdfplumber/python-docx extractors with
    page extraction, table detection, layout preservation and XREF tracking,
    then dispatch here by extension.
    """
    raise NotImplementedError(
        "TODO(phase-2): document text extraction is implemented in the ingestion phase."
    )
