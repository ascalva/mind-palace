"""Unit tests for the Lane-1 reference-edge store (bp-013 Item 6, B-c).

Typed directed endpoints, content-derived identity, append-only idempotency, closed
vocabularies at the boundary — plus the Item 6 falsifier, grep-asserted: NO import path
from `core/complex/**` to this store may exist (the balance math holds no handle; the
bit-identical instruments proof lives in tests/integration/test_reference_edge_isolation.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.stores.reference_edges import (
    CORPUS_KINDS,
    DIRECTIONS,
    REF_TYPES,
    ReferenceEdge,
    ReferenceEdgeStore,
)

REPO = Path(__file__).resolve().parents[2]


def _edge(**over: object) -> ReferenceEdge:
    kw: dict = dict(direction="code_to_corpus", ref_type="note-citation",
                    commit_sha="c1", code_path="core/recursion.py", qualname="",
                    corpus_ref="docs/design-notes/recursive-strata.md",
                    corpus_kind="path", source_line=1)
    kw.update(over)
    return ReferenceEdge.mint(**kw)


# --- typed endpoints ------------------------------------------------------------------------
def test_endpoints_are_typed_and_round_trip(tmp_path):
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    e = _edge(qualname="Thing.method", source_line=42)
    assert store.add_batch([e]) == 1
    (got,) = store.all()
    # code side = (commit_sha, path, qualname); corpus side = repo-relative path (Q2).
    assert (got.commit_sha, got.code_path, got.qualname) == ("c1", "core/recursion.py",
                                                             "Thing.method")
    assert (got.corpus_ref, got.corpus_kind) == ("docs/design-notes/recursive-strata.md",
                                                 "path")
    assert got.source_line == 42 and got.ref_type == "note-citation"
    assert got == e                                       # full round trip, identity included


def test_direction_is_stored_as_extracted_never_symmetrized(tmp_path):
    # Q3: doc→code and code→doc are different assertions; adding one never creates the other.
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([_edge(direction="corpus_to_code", ref_type="path-mention",
                           corpus_ref="docs/design-notes/the-edge-model.md",
                           source_line=7)])
    assert [e.direction for e in store.all()] == ["corpus_to_code"]
    assert store.all(direction="code_to_corpus") == []
    assert len(store.all(direction="corpus_to_code")) == 1


# --- identity + append-only idempotency -----------------------------------------------------
def test_re_adding_the_same_identity_is_a_no_op(tmp_path):
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    assert store.add_batch([_edge()]) == 1
    assert store.add_batch([_edge()]) == 0                # idempotent re-extraction
    assert store.count() == 1


def test_append_only_first_reading_wins(tmp_path):
    # Same identity, different created_at: the stored row is never mutated (INSERT OR IGNORE).
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([_edge(created_at="2026-07-11T00:00:00")])
    store.add_batch([_edge(created_at="2026-07-12T09:00:00")])
    (got,) = store.all()
    assert got.created_at == "2026-07-11T00:00:00"


def test_identity_key_spans_source_target_ref_type_and_line(tmp_path):
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    variants = [
        _edge(),
        _edge(source_line=2),                             # different line → different edge
        _edge(ref_type="path-mention"),                   # different type → different edge
        _edge(qualname="f"),                              # different code endpoint
        _edge(corpus_ref="docs/findings/finding-0021.md"),  # different corpus endpoint
        _edge(commit_sha="c2"),                           # different reading coordinate
    ]
    assert len({e.edge_id for e in variants}) == len(variants)
    assert store.add_batch(variants) == len(variants)


# --- closed vocabularies at the boundary ----------------------------------------------------
def test_vocabularies_are_closed_at_mint():
    with pytest.raises(ValueError):
        _edge(direction="sideways")
    with pytest.raises(ValueError):
        _edge(ref_type="wikilink")        # not in the §2.3 shape — unrepresentable (0% in V4)
    with pytest.raises(ValueError):
        _edge(corpus_kind="url")
    with pytest.raises(ValueError):
        _edge(source_line=0)
    assert set(DIRECTIONS) == {"code_to_corpus", "corpus_to_code"}
    assert set(CORPUS_KINDS) == {"path", "digest"}
    assert set(REF_TYPES) == {"note-citation", "path-mention", "symbol-mention", "design-ref"}


# --- reads ----------------------------------------------------------------------------------
def test_for_commit_and_ref_type_filters(tmp_path):
    store = ReferenceEdgeStore(tmp_path / "refs.sqlite")
    store.add_batch([_edge(), _edge(commit_sha="c2"),
                     _edge(ref_type="path-mention", corpus_ref="config/levers.toml")])
    assert len(store.for_commit("c1")) == 2
    assert len(store.for_commit("c2")) == 1
    assert [e.ref_type for e in store.all(ref_type="path-mention")] == ["path-mention"]


def test_open_helper_places_the_store_beside_its_siblings(tmp_path):
    from types import SimpleNamespace

    from core.stores.reference_edges import open_reference_edge_store
    cfg = SimpleNamespace(paths=SimpleNamespace(data_dir=tmp_path))
    store = open_reference_edge_store(cfg)  # type: ignore[arg-type]
    assert store.path == tmp_path / "reference_edges.sqlite"
    store.close()


# --- the Item 6 falsifier, grep-asserted ----------------------------------------------------
def test_no_import_path_from_core_complex_to_this_store():
    """Any import of `reference_edges` from `core/complex/**` breaks the plan's premise:
    the balance math must hold NO handle to the Lane-1 store (plan §6; note §2.5)."""
    complex_dir = REPO / "core" / "complex"
    offenders = [p.name for p in sorted(complex_dir.rglob("*.py"))
                 if "reference_edges" in p.read_text(encoding="utf-8")]
    assert offenders == [], f"core/complex/** must not reference the Lane-1 store: {offenders}"
