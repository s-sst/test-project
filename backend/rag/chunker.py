"""Chunking (Phase 3).

Splits extracted document text into retrievable segments. ``RecursiveChunker``
uses a hierarchy of separators (paragraph → line → sentence → word) to keep
chunks semantically coherent, with a configurable size and overlap. Each chunk
is mapped back to its source page via the document ``page_map`` so retrieved
evidence always carries a page citation (Rule 2).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

_SEPARATORS = ["\n\n", "\n", ". ", " "]


@dataclass
class Chunk:
    text: str
    chunk_index: int
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    metadata: dict = field(default_factory=dict)


def page_for_offset(page_map: list[dict], offset: int) -> int | None:
    """Resolve a global char offset to a page number using the page map."""
    for entry in page_map:
        if entry["char_start"] <= offset < entry["char_end"]:
            return entry["page"]
    return page_map[-1]["page"] if page_map else None


class Chunker(ABC):
    @abstractmethod
    def chunk(self, text: str, *, page_map: list[dict] | None = None) -> list[Chunk]:  # pragma: no cover
        ...


class RecursiveChunker(Chunker):
    def __init__(self, chunk_size: int = 900, overlap: int = 150):
        self.chunk_size = max(1, chunk_size)
        self.overlap = max(0, min(overlap, self.chunk_size - 1))

    def _split_points(self, text: str) -> list[str]:
        """Greedy window split honouring separators near the window edge."""
        pieces: list[str] = []
        start = 0
        n = len(text)
        while start < n:
            end = min(start + self.chunk_size, n)
            if end < n:
                # try to break on the latest separator within the window
                window = text[start:end]
                cut = -1
                for sep in _SEPARATORS:
                    idx = window.rfind(sep)
                    if idx > self.chunk_size // 2:
                        cut = idx + len(sep)
                        break
                if cut != -1:
                    end = start + cut
            pieces.append(text[start:end])
            if end >= n:
                break
            start = max(end - self.overlap, start + 1)
        return pieces

    def chunk(self, text: str, *, page_map: list[dict] | None = None) -> list[Chunk]:
        page_map = page_map or []
        chunks: list[Chunk] = []
        cursor = 0
        idx = 0
        for piece in self._split_points(text):
            stripped = piece.strip()
            char_start = text.find(piece, cursor)
            if char_start == -1:
                char_start = cursor
            char_end = char_start + len(piece)
            cursor = char_end - self.overlap
            if not stripped:
                continue
            chunks.append(
                Chunk(
                    text=stripped,
                    chunk_index=idx,
                    page_number=page_for_offset(page_map, char_start),
                    char_start=char_start,
                    char_end=char_end,
                )
            )
            idx += 1
        return chunks


class PageChunker(Chunker):
    """One chunk per page — preserves page citations exactly."""

    def chunk(self, text: str, *, page_map: list[dict] | None = None) -> list[Chunk]:
        page_map = page_map or []
        chunks: list[Chunk] = []
        for i, entry in enumerate(page_map):
            segment = text[entry["char_start"]:entry["char_end"]].strip()
            if segment:
                chunks.append(
                    Chunk(
                        text=segment,
                        chunk_index=i,
                        page_number=entry["page"],
                        char_start=entry["char_start"],
                        char_end=entry["char_end"],
                    )
                )
        return chunks
