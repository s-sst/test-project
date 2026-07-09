"""Ingestion orchestration (implementation: Phase 2).

Coordinates extraction → metadata → (OCR fallback) → hand-off to the RAG
chunking/embedding stage, updating :class:`documents.models.UploadedDocument`
status as it goes.
"""
from __future__ import annotations

from common.exceptions import PipelineStageNotReady


def ingest_document(document) -> None:
    """Run the ingestion pipeline for a single ``UploadedDocument``.

    TODO(phase-2): extract text (+OCR fallback), detect tables/scanned pages,
    record page_count/metadata, then trigger RAG chunking + embedding.
    """
    raise PipelineStageNotReady(
        "TODO(phase-2): document ingestion pipeline is delivered in Phase 2."
    )
