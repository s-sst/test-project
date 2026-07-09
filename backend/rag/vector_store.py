"""Vector store interfaces (implementation: Phase 2).

Abstracts the vector database so ChromaDB can be swapped for another backend
without touching callers. Supports multiple collections (governance documents
vs. proposal documents) and framework-scoped metadata filtering.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    metadata: dict


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, collection: str, ids: list[str], embeddings: list[list[float]],
               documents: list[str], metadatas: list[dict]) -> None:  # pragma: no cover
        ...

    @abstractmethod
    def query(self, collection: str, embedding: list[float], *, top_k: int = 8,
              where: dict | None = None) -> list[RetrievedChunk]:  # pragma: no cover
        ...


class ChromaVectorStore(VectorStore):
    """TODO(phase-2): ChromaDB-backed implementation (lazy ``import chromadb``)."""

    def upsert(self, *args, **kwargs) -> None:
        raise NotImplementedError("TODO(phase-2): ChromaDB upsert.")

    def query(self, *args, **kwargs):
        raise NotImplementedError("TODO(phase-2): ChromaDB query.")
