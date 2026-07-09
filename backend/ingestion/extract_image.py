"""Image / OCR extraction interfaces (implementation: Phase 2).

Handles scanned pages and embedded images: OCR fallback via pytesseract, image
extraction from PDFs, and scanned-page detection. Concrete code + heavy imports
(Pillow, pytesseract, fitz) arrive in Phase 2.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OcrResult:
    page_number: int
    text: str
    confidence: float | None = None


class ImageExtractor(ABC):
    @abstractmethod
    def ocr_page(self, image_bytes: bytes, page_number: int) -> OcrResult:  # pragma: no cover
        ...


def ocr_document(file_path: str) -> list[OcrResult]:
    """OCR every scanned page of a document.

    TODO(phase-2): implement pytesseract-based OCR with scanned-page detection
    and per-page confidence, used as a fallback when native text extraction
    yields little/no text.
    """
    raise NotImplementedError(
        "TODO(phase-2): OCR is implemented in the ingestion phase."
    )
