"""Chunking interfaces (implementation: Phase 2).

Supports recursive and page-based chunking with metadata, producing the
segments persisted as :class:`documents.models.DocumentChunk`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Chunk:
    text: str
    chunk_index: int
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    metadata: dict = field(default_factory=dict)


class Chunker(ABC):
    @abstractmethod
    def chunk(self, text: str, **kwargs) -> list[Chunk]:  # pragma: no cover
        ...


class RecursiveChunker(Chunker):
    """TODO(phase-2): recursive character/token splitting with overlap."""

    def __init__(self, chunk_size: int = 800, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, **kwargs) -> list[Chunk]:
        raise NotImplementedError("TODO(phase-2): recursive chunking.")


class PageChunker(Chunker):
    """TODO(phase-2): one chunk per page, preserving page citations."""

    def chunk(self, text: str, **kwargs) -> list[Chunk]:
        raise NotImplementedError("TODO(phase-2): page chunking.")
