"""Vector index (Phase 3).

Abstracts similarity search behind a small interface with two backends:

* ``DjangoVectorIndex`` (default) — cosine search over embeddings persisted on
  ``DocumentChunk.embedding``. Durable, dependency-free, deterministic
  (ties broken by chunk id).
* ``ChromaVectorIndex`` (optional) — ChromaDB-backed, activated with
  ``VECTOR_INDEX=chroma``. Imported lazily so the base install stays light.

Multi-collection separation (governance vs. proposal documents) and
metadata-scoped filtering are expressed via the ``document_ids`` scope.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from django.conf import settings

from .embedding import cosine


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    page_number: int | None = None
    document_id: str | None = None
    metadata: dict = field(default_factory=dict)


class BaseVectorIndex(ABC):
    def add(self, chunks) -> None:  # noqa: D401 - default no-op for DB-backed index
        """Register chunks with the index. The DB-backed index stores vectors on
        the chunk rows at creation time, so this is a no-op there; external
        stores override it."""
        return None

    @abstractmethod
    def search(self, query_embedding: list[float], *, document_ids: list, top_k: int) -> list[RetrievedChunk]:
        ...


class DjangoVectorIndex(BaseVectorIndex):
    def search(self, query_embedding, *, document_ids, top_k=6) -> list[RetrievedChunk]:
        from documents.models import DocumentChunk

        qs = (
            DocumentChunk.objects.filter(document_id__in=document_ids)
            .exclude(embedding=None)
            .only("id", "text", "page_number", "document_id", "embedding", "metadata")
        )
        scored: list[tuple[float, object]] = []
        for chunk in qs.iterator():
            scored.append((cosine(query_embedding, chunk.embedding or []), chunk))
        # deterministic ordering: score desc, then chunk id for stable ties
        scored.sort(key=lambda pair: (-pair[0], str(pair[1].id)))
        return [
            RetrievedChunk(
                chunk_id=str(chunk.id),
                text=chunk.text,
                score=round(score, 6),
                page_number=chunk.page_number,
                document_id=str(chunk.document_id),
                metadata=chunk.metadata,
            )
            for score, chunk in scored[:top_k]
        ]


class ChromaVectorIndex(BaseVectorIndex):  # pragma: no cover - optional heavy dep
    """ChromaDB-backed index (opt-in). Requires ``pip install chromadb``."""

    def __init__(self, collection: str = "documents"):
        import chromadb

        self._client = chromadb.PersistentClient(path=settings.RAG["CHROMA_PERSIST_DIR"])
        self._collection = self._client.get_or_create_collection(collection)

    def add(self, chunks) -> None:
        self._collection.upsert(
            ids=[str(c.id) for c in chunks],
            embeddings=[c.embedding for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[
                {"document_id": str(c.document_id), "page_number": c.page_number or 0}
                for c in chunks
            ],
        )

    def search(self, query_embedding, *, document_ids, top_k=6) -> list[RetrievedChunk]:
        res = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"document_id": {"$in": [str(d) for d in document_ids]}},
        )
        out: list[RetrievedChunk] = []
        for cid, doc, dist, meta in zip(
            res["ids"][0], res["documents"][0], res["distances"][0], res["metadatas"][0]
        ):
            out.append(
                RetrievedChunk(
                    chunk_id=cid,
                    text=doc,
                    score=round(1.0 - dist, 6),
                    page_number=meta.get("page_number"),
                    document_id=meta.get("document_id"),
                    metadata=meta,
                )
            )
        return out


def get_vector_index() -> BaseVectorIndex:
    if settings.RAG["VECTOR_INDEX"] == "chroma":
        return ChromaVectorIndex()
    return DjangoVectorIndex()
