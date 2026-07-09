"""RAG indexing orchestration (Phase 3).

Chunks a document's extracted text, embeds each chunk, and persists
``DocumentChunk`` rows (with vectors) that the retriever searches. Idempotent:
re-indexing replaces the document's chunks.
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.db import transaction

from audit_logs.services import record_action
from common.enums import AuditAction, ChunkType
from documents.models import DocumentChunk

from .chunker import RecursiveChunker
from .embedding import get_embedder
from .vector_store import get_vector_index

logger = logging.getLogger(__name__)


@transaction.atomic
def index_document(document, *, chunker=None, embedder=None) -> int:
    """Chunk + embed + persist a processed document. Returns the chunk count."""
    cfg = settings.RAG
    chunker = chunker or RecursiveChunker(cfg["CHUNK_SIZE"], cfg["CHUNK_OVERLAP"])
    embedder = embedder or get_embedder()

    text = document.extracted_text or ""
    chunks = chunker.chunk(text, page_map=document.page_map or [])

    # Idempotency: clear any previous index for this document.
    document.chunks.all().delete()

    if not chunks:
        return 0

    embeddings = embedder.embed([c.text for c in chunks])
    rows = [
        DocumentChunk(
            document=document,
            chunk_index=c.chunk_index,
            page_number=c.page_number,
            chunk_type=ChunkType.RECURSIVE,
            text=c.text,
            char_start=c.char_start,
            char_end=c.char_end,
            token_count=len(c.text.split()),
            embedding=emb,
            embedding_id=f"{document.id}:{c.chunk_index}",
        )
        for c, emb in zip(chunks, embeddings)
    ]
    DocumentChunk.objects.bulk_create(rows)

    # Populate an external vector store if configured (no-op for the DB index).
    persisted = list(document.chunks.all())
    get_vector_index().add(persisted)

    record_action(
        AuditAction.PROCESS,
        entity=document,
        summary=f"Indexed '{document.original_filename}' into {len(rows)} chunk(s)",
        metadata={"chunk_count": len(rows), "embedding_backend": cfg["EMBEDDING_BACKEND"]},
    )
    logger.info("Indexed document %s into %d chunks", document.id, len(rows))
    return len(rows)
