"""The source-set: "a source object IS the set of its idea-vectors", as a type.

Deterministic — hand-built vectors and a fake embedder, no Ollama. Asserts the membership
round-trip, that grouped retrieval regroups the flat hits losslessly (flat stays the default
and unchanged), provenance/strata scoping, the provenance-parametric guarantee (a non-authored
stratum uses the SAME machinery), and the fail-closed mixed-provenance guard.
"""

import pytest

from core.ingest.index import grouped_semantic_search, semantic_search
from core.provenance import MIRROR_READABLE, Provenance
from core.stores.sourceset import (
    MixedProvenanceError,
    SourceId,
    group_sources,
    source_set,
    source_sets,
)
from core.stores.vectorstore import VectorStore


def _row(digest, idx, vec, prov, title="t"):
    return {
        "id": f"{digest}:{idx}", "digest": digest, "title": title, "source_path": "p",
        "chunk_index": idx, "provenance": prov.value, "text": f"{digest}-{idx}", "vector": vec,
    }


class FakeEmbedder:
    """`semantic_search` only calls `embed_query`; a fixed query vector keeps ranking exact."""

    def __init__(self, qvec):
        self._q = qvec

    def embed_query(self, text):
        return self._q


# ── membership round-trip: group-by-digest == the full chunk set for a source ──

def test_membership_round_trip(tmp_path):
    vs = VectorStore(tmp_path / "v.lance", dim=3)
    vs.add([
        _row("a", 0, [1.0, 0.0, 0.0], Provenance.AUTHORED_SOLO),
        _row("a", 1, [0.0, 1.0, 0.0], Provenance.AUTHORED_SOLO),
        _row("a", 2, [0.0, 0.0, 1.0], Provenance.AUTHORED_SOLO),
        _row("b", 0, [1.0, 1.0, 0.0], Provenance.AUTHORED_SOLO),
    ])
    sets = {s.digest: s for s in source_sets(vs)}
    assert set(sets) == {"a", "b"}
    assert len(sets["a"]) == 3 and len(sets["b"]) == 1

    # the source's member set equals every stored row for that digest (round-trip)
    a_rows = [r for r in vs.all_rows() if r["digest"] == "a"]
    assert {m["id"] for m in sets["a"].members} == {r["id"] for r in a_rows}
    # members reconstruct the note in reading order
    assert [m["chunk_index"] for m in sets["a"].members] == [0, 1, 2]
    # every stored row is accounted for exactly once across the sources
    assert sum(len(s) for s in sets.values()) == vs.count()

    # single-source constructor agrees with the full-scan grouping
    assert source_set(vs, "a") == sets["a"]
    assert source_set(vs, "missing") is None


def test_vectors_are_raw_members_never_aggregated(tmp_path):
    # The "no coarse/note-level vector" guard at the type level: a 3-chunk source exposes THREE
    # idea-vectors, not one mean. A stored coarse vector would be a separate DERIVED cache.
    vs = VectorStore(tmp_path / "v.lance", dim=3)
    vs.add([
        _row("a", 0, [1.0, 0.0, 0.0], Provenance.AUTHORED_SOLO),
        _row("a", 1, [0.0, 1.0, 0.0], Provenance.AUTHORED_SOLO),
    ])
    (s,) = source_sets(vs)
    assert s.vectors() == [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]


# ── grouped retrieval regroups the flat hits; flat stays the default and unchanged ──

def test_grouped_retrieval_regroups_flat_hits_losslessly(tmp_path):
    vs = VectorStore(tmp_path / "v.lance", dim=3)
    # note "a" has two chunks near the query; note "b" one chunk further away.
    vs.add([
        _row("a", 0, [1.0, 0.0, 0.0], Provenance.AUTHORED_SOLO),
        _row("a", 1, [0.95, 0.05, 0.0], Provenance.AUTHORED_SOLO),
        _row("b", 0, [0.0, 1.0, 0.0], Provenance.AUTHORED_SOLO),
    ])
    emb = FakeEmbedder([1.0, 0.0, 0.0])

    flat = semantic_search("q", emb, vs, k=3)
    grouped = grouped_semantic_search("q", emb, vs, k=3)

    # flat retrieval is byte-identical to the underlying store search — the default is untouched
    assert flat == vs.search(emb.embed_query("q"), k=3, provenances=MIRROR_READABLE)
    assert [r["id"] for r in flat] == ["a:0", "a:1", "b:0"]

    # grouped collapses the two "a" chunks into one source object, "a" ranked first (best hit)
    assert [s.digest for s in grouped] == ["a", "b"]
    assert len(grouped[0]) == 2 and len(grouped[1]) == 1
    # lossless: the grouped members are exactly the flat hits, regrouped
    assert {m["id"] for s in grouped for m in s.members} == {r["id"] for r in flat}
    # best_distance orders sources the way the search ranked them
    assert grouped[0].best_distance() <= grouped[1].best_distance()


# ── provenance / strata scoping ──

def test_provenance_scoping_filters(tmp_path):
    vs = VectorStore(tmp_path / "v.lance", dim=3)
    vs.add([
        _row("a", 0, [1.0, 0.0, 0.0], Provenance.AUTHORED_SOLO),
        _row("o", 0, [0.0, 1.0, 0.0], Provenance.OBSERVED),
    ])
    assert {s.digest for s in source_sets(vs)} == {"a", "o"}
    mirror = source_sets(vs, provenances={Provenance.AUTHORED_SOLO})
    assert {s.digest for s in mirror} == {"a"}
    assert mirror[0].provenance is Provenance.AUTHORED_SOLO


def test_non_authored_stratum_uses_the_same_machinery(tmp_path):
    # provenance-parametric: a curated-external item at another stratum groups with no bespoke
    # path — the SourceId simply carries a different label.
    vs = VectorStore(tmp_path / "v.lance", dim=3)
    vs.add([
        _row("c", 0, [1.0, 0.0, 0.0], Provenance.CURATED),
        _row("c", 1, [0.0, 1.0, 0.0], Provenance.CURATED),
    ])
    (s,) = source_sets(vs, provenances={Provenance.CURATED})
    assert s.id == SourceId(digest="c", provenance=Provenance.CURATED)
    assert s.provenance is Provenance.CURATED and len(s) == 2


def test_mixed_provenance_digest_raises():
    # A single digest spanning strata is a data-integrity error, not a mergeable state.
    with pytest.raises(MixedProvenanceError):
        group_sources([
            _row("x", 0, [1.0], Provenance.AUTHORED_SOLO),
            _row("x", 1, [1.0], Provenance.OBSERVED),
        ])
