"""RAG orchestration (implementation: Phase 2)."""
from __future__ import annotations

from common.exceptions import PipelineStageNotReady


def index_document(document) -> None:
    """Chunk + embed + store a processed document.

    TODO(phase-2): recursive/page chunking → embeddings → vector store upsert,
    persisting :class:`documents.models.DocumentChunk` rows with embedding ids.
    """
    raise PipelineStageNotReady("TODO(phase-2): RAG indexing.")
