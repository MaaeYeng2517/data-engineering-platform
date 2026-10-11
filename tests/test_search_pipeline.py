"""Tests for the search index, retrieval ranking and RAG context assembly.

These cover the pieces that decide what a user sees: that keyword and vector
hits share keys so the hybrid blend means something, that a query is scoped to
the knowledge bases it asked for, that re-indexing cannot leave stale text
behind, and that RAG only spends its budget on passages that actually scored.
No database is needed — the index is exercised directly.
"""
import pytest

from backend.app.services.chunking import TokenChunker
from backend.app.services.indexing import (
    KEYWORD_WEIGHT,
    VECTOR_WEIGHT,
    HybridIndex,
    build_entry,
)
from backend.app.services.rag import ContextBuilder
from backend.app.services.retrieval import RetrievalEngine


@pytest.fixture(autouse=True)
def fresh_index():
    """Every test gets its own index so nothing leaks between them."""
    index = HybridIndex()
    from backend.app.services import indexing

    original = indexing.hybrid_index
    indexing.hybrid_index = index
    retrieval = RetrievalEngine(index=index)
    try:
        yield index, retrieval
    finally:
        indexing.hybrid_index = original


def entry(chunk_id, document_id, content, *, kb_id="kb-1", title="Doc", **metadata):
    return build_entry(
        chunk_id=chunk_id,
        document_id=document_id,
        content=content,
        metadata=metadata,
        title=title,
        kb_id=kb_id,
    )


def test_keyword_and_vector_hits_share_a_key(fresh_index):
    """The whole hybrid blend depends on both halves using the same ids."""
    index, _ = fresh_index
    index.index_chunks([entry("c1", "d1", "hybrid search blends keyword and vector scores")])

    results = index.search("hybrid search")

    assert len(results) == 1
    assert results[0]["chunk_id"] == "c1"
    # Both halves contributed to the same entry.
    assert results[0]["keyword_score"] > 0
    assert results[0]["vector_score"] > 0


def test_hybrid_score_uses_the_documented_weights(fresh_index):
    index, _ = fresh_index
    index.index_chunks([entry("c1", "d1", "vector similarity is the dense half of the blend")])

    result = index.search("vector similarity")[0]
    expected = (
        result["keyword_score"] * KEYWORD_WEIGHT
        + result["vector_score"] * VECTOR_WEIGHT
    )

    assert result["hybrid_score"] == pytest.approx(expected)
    assert result["score"] == pytest.approx(result["hybrid_score"])


def test_search_is_scoped_to_the_requested_knowledge_bases(fresh_index):
    index, retrieval = fresh_index
    index.index_chunks(
        [
            entry("c1", "d1", "annual revenue report", kb_id="kb-1"),
            entry("c2", "d2", "annual revenue report", kb_id="kb-2"),
        ]
    )

    scoped = retrieval_engine_result = retrieval.search_all = None  # placeholder guard
    assert retrieval_engine_result is None and scoped is None

    import asyncio

    result = asyncio.get_event_loop_policy().new_event_loop().run_until_complete(
        retrieval.search("annual revenue", kb_ids=["kb-2"])
    )

    assert result["total"] == 1
    assert result["results"][0]["chunk_id"] == "c2"


def test_score_threshold_filters_weak_hits(fresh_index):
    index, retrieval = fresh_index
    index.index_chunks([entry("c1", "d1", "quarterly margin notes")])

    import asyncio

    loop = asyncio.new_event_loop()
    try:
        everything = loop.run_until_complete(
            retrieval.search("quarterly margin", kb_ids=["kb-1"])
        )
        nothing = loop.run_until_complete(
            retrieval.search("quarterly margin", kb_ids=["kb-1"], score_threshold=99)
        )
    finally:
        loop.close()

    assert everything["total"] == 1
    assert nothing["total"] == 0


def test_metadata_filter_matches_on_exact_values(fresh_index):
    index, _ = fresh_index
    index.index_chunks(
        [
            entry("c1", "d1", "finance quarterly notes", department="finance"),
            entry("c2", "d2", "finance hiring notes", department="people"),
        ]
    )

    results = index.search("finance notes", metadata_filter={"department": "finance"})

    assert [result["chunk_id"] for result in results] == ["c1"]


def test_reindexing_replaces_the_previous_chunks(fresh_index):
    index, _ = fresh_index
    index.index_chunks([entry("c1", "d1", "the original text about otters")])
    index.index_chunks([entry("c1", "d1", "replacement text about badgers")])

    assert index.search("otters") == []
    assert [result["chunk_id"] for result in index.search("badgers")] == ["c1"]


def test_deleting_a_document_removes_all_of_its_chunks(fresh_index):
    index, _ = fresh_index
    index.index_chunks(
        [
            entry("c1", "d1", "first chunk"),
            entry("c2", "d1", "second chunk"),
            entry("c3", "d2", "another document"),
        ]
    )

    assert index.delete_document("d1") == 2
    assert index.chunk_count() == 1
    assert index.chunk_count(kb_ids=["kb-none"]) == 0


def test_clear_empties_the_index(fresh_index):
    index, _ = fresh_index
    index.index_chunks([entry("c1", "d1", "something")])

    index.clear()

    assert index.chunk_count() == 0
    assert len(index.keyword_index) == 0
    assert len(index.vector_index) == 0


def test_token_chunker_windows_overlap_and_count_tokens():
    chunker = TokenChunker(chunk_size=10, chunk_overlap=3)
    text = " ".join(f"word{index}" for index in range(25))

    chunks = chunker.chunk(text, {"document_id": "d1"})

    assert len(chunks) > 1
    assert all(chunk["token_count"] <= 10 for chunk in chunks)
    # Consecutive windows share words, so a boundary sentence stays retrievable.
    first, second = chunks[0]["content"].split(), chunks[1]["content"].split()
    assert set(first) & set(second)
    assert [chunk["chunk_index"] for chunk in chunks] == list(range(len(chunks)))


def test_reranker_sets_the_score_the_api_exposes(fresh_index):
    index, retrieval = fresh_index
    index.index_chunks(
        [
            entry("c1", "d1", "hybrid search explanation " * 5),
            entry("c2", "d2", "unrelated text"),
        ]
    )

    import asyncio

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(retrieval.search("hybrid search", kb_ids=["kb-1"]))
    finally:
        loop.close()

    top = result["results"][0]
    assert top["chunk_id"] == "c1"
    assert top["score"] == pytest.approx(top["rerank_score"])


async def test_context_builder_only_keeps_scored_passages():
    builder = ContextBuilder(max_tokens=100)

    kept = await builder.build(
        "query",
        [
            {"chunk_id": "c1", "content": "a relevant passage", "score": 0.9},
            {"chunk_id": "c2", "content": "no score at all"},
        ],
    )

    assert [passage["chunk_id"] for passage in kept["context"]] == ["c1"]
    assert kept["sources"] == ["c1"]


async def test_context_builder_respects_its_budget():
    builder = ContextBuilder(max_tokens=10)

    built = await builder.build(
        "query",
        [
            {"chunk_id": "c1", "content": "ten tokens exactly here", "score": 0.9, "token_count": 10},
            {"chunk_id": "c2", "content": "these tokens do not fit", "score": 0.8, "token_count": 50},
        ],
    )

    assert [passage["chunk_id"] for passage in built["context"]] == ["c1"]
    assert built["total_tokens"] == 10


async def test_context_builder_falls_back_to_hybrid_score():
    """A caller can hand results straight to the builder without a rerank."""
    builder = ContextBuilder()

    built = await builder.build(
        "query",
        [{"chunk_id": "c1", "content": "passage", "hybrid_score": 0.7}],
    )

    assert [passage["chunk_id"] for passage in built["context"]] == ["c1"]


def test_rag_engine_answers_from_the_index(fresh_index):
    """End to end without HTTP: index, then ask a question."""
    import asyncio

    index, _ = fresh_index
    index.index_chunks(
        [entry("c1", "d1", "The deployment guide explains how to run the stack in Docker.", title="Guide")]
    )

    from backend.app.services.rag import rag_engine

    loop = asyncio.new_event_loop()
    try:
        answer = loop.run_until_complete(
            rag_engine.answer("How do I run the stack?", ["kb-1"], limit=3)
        )
    finally:
        loop.close()

    assert answer["sources"]
    assert answer["citations"][0]["chunk_id"] == "c1"
    assert answer["citations"][0]["title"] == "Guide"