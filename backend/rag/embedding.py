"""Embedding backends (Phase 3).

Provider-agnostic embedding contract with two backends:

* ``HashingEmbedder`` (default) — a dependency-free, fully deterministic signed
  feature-hashing embedder. No PyTorch, no model download; identical text always
  yields an identical vector, keeping retrieval reproducible everywhere.
* ``SentenceTransformerEmbedder`` (optional) — real dense embeddings via
  sentence-transformers, activated with ``EMBEDDING_BACKEND=sentence_transformers``.

Both return L2-normalised vectors, so cosine similarity reduces to a dot product.
"""
from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

from django.conf import settings

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class Embedder(ABC):
    dimensions: int = 0

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover
        ...

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


class HashingEmbedder(Embedder):
    """Deterministic signed feature-hashing embedder (bag-of-words)."""

    def __init__(self, dimensions: int = 256):
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorise(t) for t in texts]

    def _vectorise(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        for token in _TOKEN_RE.findall(text.lower()):
            digest = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = digest % self.dimensions
            sign = 1.0 if (digest >> 8) & 1 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


class SentenceTransformerEmbedder(Embedder):  # pragma: no cover - optional heavy dep
    """Optional dense embedder backed by sentence-transformers."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self.dimensions = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        vecs = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, v)) for v in vecs]


def get_embedder() -> Embedder:
    """Return the configured embedder (default: deterministic hashing)."""
    cfg = settings.RAG
    backend = cfg["EMBEDDING_BACKEND"]
    if backend == "sentence_transformers":
        return SentenceTransformerEmbedder(cfg["EMBEDDING_MODEL"])
    return HashingEmbedder(dimensions=cfg["EMBEDDING_DIM"])


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity. Vectors from the embedders are pre-normalised, but we
    normalise defensively so mixed sources still compare correctly."""
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
