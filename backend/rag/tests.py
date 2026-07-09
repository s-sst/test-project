"""Tests for Phase 3 RAG (embedder, chunker, indexing, retrieval)."""
from __future__ import annotations

import pytest

from rag.chunker import PageChunker, RecursiveChunker, page_for_offset
from rag.embedding import HashingEmbedder, cosine


# --- Embedder --------------------------------------------------------------
def test_hashing_embedder_deterministic_and_normalised():
    emb = HashingEmbedder(dimensions=128)
    v1 = emb.embed_one("data governance and provenance")
    v2 = emb.embed_one("data governance and provenance")
    assert v1 == v2
    assert len(v1) == 128
    assert cosine(v1, v2) == pytest.approx(1.0)


def test_cosine_similar_text_scores_higher():
    emb = HashingEmbedder()
    q = emb.embed_one("human oversight reviewer monitors the ai system")
    related = emb.embed_one("human oversight procedures assign reviewers to the system")
    unrelated = emb.embed_one("financial quarterly revenue projections spreadsheet")
    assert cosine(q, related) > cosine(q, unrelated)


# --- Chunker ---------------------------------------------------------------
def test_recursive_chunker_splits_with_overlap():
    text = " ".join(f"sentence{i}." for i in range(200))
    chunks = RecursiveChunker(chunk_size=120, overlap=20).chunk(text, page_map=[])
    assert len(chunks) > 1
    assert all(len(c.text) <= 200 for c in chunks)
    assert chunks[0].chunk_index == 0


def test_page_for_offset():
    page_map = [
        {"page": 1, "char_start": 0, "char_end": 10},
        {"page": 2, "char_start": 12, "char_end": 30},
    ]
    assert page_for_offset(page_map, 5) == 1
    assert page_for_offset(page_map, 20) == 2


# --- Indexing + retrieval --------------------------------------------------
@pytest.fixture
def indexed_document(db):
    from documents.models import UploadedDocument
    from rag.services import index_document

    p1 = "Data governance and provenance are documented with dataset lineage records."
    p2 = "Human oversight procedures assign named reviewers to monitor the AI system."
    full = p1 + "\n\n" + p2
    doc = UploadedDocument.objects.create(
        original_filename="policy.pdf",
        extension="pdf",
        mime_type="application/pdf",
        size_bytes=len(full),
        sha256="0" * 64,
        extracted_text=full,
        page_map=[
            {"page": 1, "char_start": 0, "char_end": len(p1)},
            {"page": 2, "char_start": len(p1) + 2, "char_end": len(full)},
        ],
    )
    count = index_document(doc, chunker=PageChunker())
    assert count == 2
    return doc


@pytest.mark.django_db
def test_index_document_persists_chunks_with_embeddings(indexed_document):
    chunks = list(indexed_document.chunks.all())
    assert len(chunks) == 2
    assert all(c.embedding and len(c.embedding) > 0 for c in chunks)
    assert all(c.page_number in (1, 2) for c in chunks)


@pytest.mark.django_db
def test_retriever_returns_relevant_page(indexed_document):
    from rag.retriever import Retriever

    results = Retriever().retrieve(
        "who provides human oversight of the system?",
        document_ids=[indexed_document.id],
        top_k=2,
    )
    assert results
    # the page-2 chunk (human oversight) should rank first
    assert results[0].page_number == 2
    assert "oversight" in results[0].text.lower()


@pytest.mark.django_db
def test_index_document_is_idempotent(indexed_document):
    from rag.services import index_document

    index_document(indexed_document, chunker=PageChunker())
    assert indexed_document.chunks.count() == 2  # replaced, not duplicated
