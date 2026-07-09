"""Retriever interface (implementation: Phase 2).

Combines an :class:`~rag.embedding.Embedder` and a
:class:`~rag.vector_store.VectorStore` into per-requirement retrieval with
framework-scoped filtering, providing the grounded context handed to the LLM.
"""
from __future__ import annotations

from dataclasses import dataclass

from .vector_store import RetrievedChunk


@dataclass
class RetrievalQuery:
    text: str
    top_k: int = 8
    where: dict | None = None


class Retriever:
    """TODO(phase-2): embed the query, search the vector store, return the
    top-k grounded chunks used as evidence context for a requirement."""

    def retrieve(self, query: RetrievalQuery) -> list[RetrievedChunk]:
        raise NotImplementedError("TODO(phase-2): retrieval.")
