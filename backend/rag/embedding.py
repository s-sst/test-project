"""Embedding interfaces (implementation: Phase 2).

Provider-agnostic embedding contract. Concrete backends (Sentence
Transformers, nomic-embed-text via Ollama) are implemented in Phase 2 with
lazy imports so the base install stays light.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class Embedder(ABC):
    #: dimensionality of produced vectors (set by concrete backends)
    dimensions: int = 0

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover
        ...


def get_embedder(model_name: str | None = None) -> Embedder:
    """Factory for the configured embedding backend.

    TODO(phase-2): return a SentenceTransformers / nomic-embed-text backed
    embedder selected via settings/env.
    """
    raise NotImplementedError("TODO(phase-2): embedding backend factory.")
