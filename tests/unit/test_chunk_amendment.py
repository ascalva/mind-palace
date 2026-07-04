"""Chunk content-hash + versioned-amendment diff — build plan Items 1b/1c (pure mechanism).

Proves the mechanism that closes the Q1 §4 gap without touching any store: a chunk's identity is
its content (so an unchanged chunk is recognizable across versions), and identity is SCOPED to the
document (so two distinct notes sharing a verbatim chunk keep both points — §7 corroboration,
build plan R1). Pure: no store, no embed, no network.
"""

from __future__ import annotations

from core.ingest.amend import AmendmentPlan, chunk_point_id, plan_amendment
from core.ingest.chunk import Chunk, chunk_text


def test_content_hash_is_deterministic_and_content_sensitive():
    a, b = Chunk(0, "the same text"), Chunk(7, "the same text")   # index differs, text identical
    assert a.content_hash == b.content_hash                        # identity is content, not index
    assert Chunk(0, "different").content_hash != a.content_hash


def test_point_id_is_document_scoped_not_global():
    # The R1 resolution as a live assertion: a verbatim chunk shared by two DISTINCT documents
    # gets DIFFERENT point ids, so corroboration (§7) is preserved — never coalesced by content.
    shared = Chunk(0, "a paragraph both notes happen to contain")
    assert chunk_point_id("notes/a.md", shared) != chunk_point_id("notes/b.md", shared)
    # ... while the SAME chunk in the SAME document is one stable id across versions.
    same_doc_later_version = chunk_point_id("notes/a.md", Chunk(9, shared.text))
    assert chunk_point_id("notes/a.md", shared) == same_doc_later_version


def test_amending_one_chunk_retains_the_rest():
    old = [Chunk(0, "intro stays"), Chunk(1, "body v1")]
    new = [Chunk(0, "intro stays"), Chunk(1, "body v2")]
    plan = plan_amendment(old, new)
    assert plan.retained == frozenset({Chunk(0, "intro stays").content_hash})
    assert plan.added == frozenset({Chunk(1, "body v2").content_hash})
    assert plan.removed == frozenset({Chunk(1, "body v1").content_hash})
    assert not plan.is_noop


def test_identical_reingest_is_a_noop():
    chunks = chunk_text("alpha\n\nbeta\n\ngamma")
    plan = plan_amendment(chunks, list(chunks))
    assert plan.is_noop and not plan.added and not plan.removed
    assert plan.retained == {c.content_hash for c in chunks}


def test_diff_is_order_insensitive():
    # Reordering chunks without editing their text changes nothing — identity is content, not order.
    a, b, c = Chunk(0, "one"), Chunk(1, "two"), Chunk(2, "three")
    assert plan_amendment([a, b, c], [c, a, b]).is_noop


def test_removing_a_chunk_marks_it_removed_only():
    old = [Chunk(0, "keep"), Chunk(1, "drop me")]
    new = [Chunk(0, "keep")]
    plan = plan_amendment(old, new)
    assert plan.removed == frozenset({Chunk(1, "drop me").content_hash})
    assert plan.added == frozenset()
    assert isinstance(plan, AmendmentPlan)
