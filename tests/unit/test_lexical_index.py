"""The lexical representation (core/ingest/lexical.py) and its store (core/stores/lexical.py):
tokens and BM25 weights with no model, landing idempotent by reconciliation, currency moving with
the version, scores read over current units of the cleared classes (dn-two-phase-ingestion D1,
D2)."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from core.ingest.lexical import (
    LexicalIndex,
    bm25,
    fuse,
    idf,
    rrf,
    term_counts,
    tf_weight,
    tokens,
)
from core.kernel.ingest.chunk import Chunk
from core.kernel.provenance import Provenance
from core.stores.lexical import LexicalStore

AUTHORED, OBSERVED = Provenance.AUTHORED_SOLO.value, Provenance.OBSERVED.value


def test_tokens_are_lower_cased_runs_of_letters_and_digits_in_any_script():
    assert tokens("Graph-theory's 4-colour THEOREM, 1976.") == [
        "graph", "theory", "s", "4", "colour", "theorem", "1976"]
    assert tokens("Café naïve_snake 東京") == ["café", "naïve", "snake", "東京"]
    assert term_counts("a b a") == {"a": 2, "b": 1}


def test_the_weights_are_robertson_and_zaragozas():
    assert idf(4, 2) == pytest.approx(math.log1p((4 - 2 + 0.5) / (2 + 0.5)))
    # a term at the mean length saturates toward k1 + 1 = 2.2 as its count grows
    assert tf_weight(1, 10, 10.0) == pytest.approx(2.2 / 2.2)
    assert tf_weight(100, 10, 10.0) == pytest.approx(100 * 2.2 / 101.2)
    # a longer unit is penalized, a shorter one favoured, by b
    assert tf_weight(1, 20, 10.0) < tf_weight(1, 10, 10.0) < tf_weight(1, 5, 10.0)


def test_the_in_memory_reference_ranks_by_shared_rare_terms():
    units = [term_counts(t) for t in ("spectral gap of a random graph", "random walks on graphs",
                                       "the gap between two numbers", "nothing relevant here")]
    scores = bm25("spectral gap", units)
    assert scores[0] > scores[2] > 0 and scores[1] == 0 and scores[3] == 0
    assert bm25("absent words", units) == [0.0] * 4
    assert bm25("spectral gap", []) == []


def _chunks(*texts: str) -> list[Chunk]:
    return [Chunk(i, t) for i, t in enumerate(texts)]


def test_the_store_scores_as_the_reference_does(tmp_path: Path):
    store = LexicalStore(tmp_path / "lex.sqlite")
    texts = {"a.md": "spectral gap of a random graph", "b.md": "random walks on graphs",
             "c.md": "the gap between two numbers", "d.md": "nothing relevant here"}
    for path, text in texts.items():
        store.land(source_path=path, digest=f"d-{path}", provenance=AUTHORED, title=path,
                   chunks=_chunks(text))
    reference = bm25("spectral gap", [term_counts(t) for t in texts.values()])
    scored = store.scores("spectral gap", classes=[Provenance.AUTHORED_SOLO])
    for (path, _), ref in zip(texts.items(), reference, strict=True):
        if ref > 0:
            assert scored[path] == pytest.approx(ref, rel=1e-9)
        else:
            assert path not in scored
    hits = store.search("spectral gap", k=2, classes=[Provenance.AUTHORED_SOLO])
    assert [h.source_path for h in hits] == ["a.md", "c.md"]
    assert store.search("absent words") == []
    # a path's score is the best of its units
    store.land(source_path="e.md", digest="d-e", provenance=AUTHORED, title="e",
               chunks=_chunks("random graph", "spectral gap spectral gap"))
    best = store.scores("spectral gap")["e.md"]
    assert best == pytest.approx(max(
        s for s in bm25("spectral gap", [term_counts(t) for t in
                                         [*texts.values(), "random graph",
                                          "spectral gap spectral gap"]])[4:]), rel=1e-9)


def test_landing_is_idempotent_and_currency_moves_with_the_version(tmp_path: Path):
    store = LexicalStore(tmp_path / "lex.sqlite")
    first = store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
                       chunks=_chunks("alpha beta", "gamma"))
    assert (first.units_written, first.made_current, first.superseded) == (2, True, 0)
    again = store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
                       chunks=_chunks("alpha beta", "gamma"))
    assert (again.units_written, again.made_current) == (0, False)      # nothing written twice
    assert store.holds_current("a.md", "v1") and store.units_of("a.md") == 2
    second = store.land(source_path="a.md", digest="v2", provenance=AUTHORED, title="A",
                        chunks=_chunks("alpha delta"))
    assert (second.units_written, second.made_current, second.superseded) == (1, True, 2)
    assert store.holds_current("a.md", "v2") and not store.holds_current("a.md", "v1")
    assert store.units_of("a.md", digest="v1", current=False) == 2   # history kept, not current
    assert "a.md" in store.scores("delta") and "a.md" not in store.scores("gamma")
    # a revert to the old bytes writes nothing and makes the old version current again
    back = store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
                      chunks=_chunks("alpha beta", "gamma"))
    assert (back.units_written, back.made_current, back.superseded) == (0, True, 1)
    assert store.retire("a.md") == 2 and store.units_of("a.md") == 0
    assert store.scores("gamma") == {} and store.count() == 0


def test_every_landed_version_is_recorded_with_its_units_even_with_none(tmp_path: Path):
    """The record that tells an item with no text (landed, complete) from one the index never
    saw (landed before the index was opened): the drain's pending set reads it."""
    store = LexicalStore(tmp_path / "lex.sqlite")
    out = store.land_many([("a.md", "v1", AUTHORED, "A", _chunks("alpha beta", "gamma")),
                           ("e.md", "ve", AUTHORED, "E", [])])
    assert [o.units_written for o in out] == [2, 0]
    assert store.landed_versions() == {("a.md", "v1"), ("e.md", "ve")}
    assert store.empty_versions() == {("e.md", "ve")}
    assert store.holds_current("a.md", "v1") and not store.holds_current("e.md", "ve")
    store.land(source_path="a.md", digest="v2", provenance=AUTHORED, title="A",
               chunks=_chunks("delta"))
    assert store.landed_versions() == {("a.md", "v1"), ("a.md", "v2"), ("e.md", "ve")}


def test_land_many_commits_every_version_or_none(tmp_path: Path):
    store = LexicalStore(tmp_path / "lex.sqlite")
    store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
               chunks=_chunks("alpha"))
    broken: Any = [object()]                       # not a chunk: the landing raises midway
    with pytest.raises(AttributeError):
        store.land_many([("b.md", "v1", AUTHORED, "B", _chunks("beta")),
                         ("c.md", "v1", AUTHORED, "C", broken)])
    assert store.landed_versions() == {("a.md", "v1")}
    assert store.units_of("b.md", current=False) == 0 and store.scores("beta") == {}
    assert store.holds_current("a.md", "v1")                  # what was there is untouched


def test_scores_read_only_the_cleared_classes(tmp_path: Path):
    store = LexicalStore(tmp_path / "lex.sqlite")
    store.land(source_path="n.md", digest="dn", provenance=AUTHORED, title="n",
               chunks=_chunks("sleep debt and recovery"))
    store.land(source_path="dialogue/t/1", digest="dt", provenance=OBSERVED, title="t",
               chunks=_chunks("sleep debt, the model said"))
    assert set(store.scores("sleep debt")) == {"n.md", "dialogue/t/1"}
    assert set(store.scores("sleep debt", classes=[Provenance.AUTHORED_SOLO])) == {"n.md"}
    assert store.scores("sleep debt", classes=[]) == {}
    assert set(store.scores("sleep debt", paths=["dialogue/t/1"])) == {"dialogue/t/1"}
    # the document frequencies are the cleared classes' own: with one class cleared, "sleep" is
    # in one unit of one, and its weight is the single-unit idf
    one = store.scores("sleep", classes=[Provenance.AUTHORED_SOLO])["n.md"]
    assert one == pytest.approx(idf(1, 1) * tf_weight(1, 4, 4.0))


def test_reciprocal_rank_fusion_favours_agreement():
    fused = fuse([["a", "b", "c"], ["c", "a", "d"]], k=4)
    assert fused[:2] == ["a", "c"] and set(fused) == {"a", "b", "c", "d"}
    assert fuse([[], []], k=3) == []


# ── the in-memory index of a fixed set of units (the corpus battery's) ──────────────────────────

def test_the_in_memory_index_holds_the_reference_weights():
    texts = ["spectral gap of a random graph", "random walks on graphs",
             "the gap between two numbers", "nothing relevant here"]
    index = LexicalIndex.build(texts)
    assert index.units == 4
    n, df = 4, 2                                         # "gap" is in two of four units
    dl, avgdl = 6, (6 + 4 + 5 + 3) / 4
    w = idf(n, df) * tf_weight(1, dl, avgdl)
    assert index.weights[0, index.vocab["gap"]] == pytest.approx(w, rel=1e-6)
    assert index.scores("spectral gap").tolist() == pytest.approx(
        bm25("spectral gap", [term_counts(x) for x in texts]), rel=1e-5)
    top = index.search("spectral gap", k=2)
    assert top.tolist()[0] == 0 and set(top.tolist()) == {0, 2}
    assert index.search("absent words").tolist() == []
    assert index.search("random", among=np.asarray([1, 2, 3], dtype=np.int64)).tolist() == [1]


def test_the_in_memory_index_survives_a_round_trip(tmp_path: Path):
    index = LexicalIndex.build(["alpha beta", "beta gamma", "gamma delta"])
    assert index.save(tmp_path / "lex") > 0
    back = LexicalIndex.load(tmp_path / "lex")
    assert back.vocab == index.vocab
    assert np.allclose(back.scores("beta gamma"), index.scores("beta gamma"))


def test_rrf_is_fuse_over_unit_numbers_with_ties_by_unit():
    a = np.asarray([1, 2, 3], dtype=np.int64)
    b = np.asarray([3, 1, 4], dtype=np.int64)
    fused = rrf([a, b], k=4).tolist()
    assert fused[:2] == [1, 3]                            # both rank them high
    assert set(fused) == {1, 2, 3, 4}
    assert fused[:2] == fuse([a.tolist(), b.tolist()], k=2)
    assert rrf([np.asarray([7], np.int64), np.asarray([5], np.int64)], k=2).tolist() == [5, 7]
