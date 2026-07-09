"""Retriever (Phase 3).

Combines the configured embedder + vector index into per-query retrieval scoped
to a set of documents, returning the top-k grounded chunks used as evidence
context for a requirement.
"""
from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from .embedding import Embedder, get_embedder
from .vector_store import BaseVectorIndex, RetrievedChunk, get_vector_index


@dataclass
class RetrievalQuery:
    text: str
    document_ids: list
    top_k: int | None = None


class Retriever:
    def __init__(self, embedder: Embedder | None = None, index: BaseVectorIndex | None = None):
        self.embedder = embedder or get_embedder()
        self.index = index or get_vector_index()

    def retrieve(self, text: str, *, document_ids: list, top_k: int | None = None) -> list[RetrievedChunk]:
        if not document_ids:
            return []
        top_k = top_k or settings.RAG["RETRIEVAL_TOP_K"]
        query_vec = self.embedder.embed_one(text)
        return self.index.search(query_vec, document_ids=document_ids, top_k=top_k)
