"""The source-set: "a source object IS the set of its idea-vectors", as a type.

Deterministic — hand-built vectors and a fake embedder, no Ollama. Asserts the membership
round-trip, that grouped retrieval regroups the flat hits losslessly (flat stays the default
and unchanged), provenance/strata scoping, the provenance-parametric guarantee (a non-authored
stratum uses the SAME machinery), and the fail-closed mixed-provenance guard.
"""

import pytest

from core.ingest.index import grouped_semantic_search, semantic_search
from core.kernel.provenance import MIRROR_READABLE, Provenance
from core.kernel.stores.sourceset import (
    MixedProvenanceError,
    SourceId,
    group_sources,
    source_set,
    source_sets,
)
from core.stores.vectorstore import VectorStore, is_code_atom_row


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
    d0, d1 = grouped[0].best_distance(), grouped[1].best_distance()
    assert d0 is not None and d1 is not None  # both groups have members (asserted above)
    assert d0 <= d1


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


# ── the shed-atom guard (bp-152 Item 3, the note's §3 Q5 gap) ──

def _atom_row(rid, vec):
    """A shed CODE-ATOM row (dn-vector-membership-store D1): geometry with NO occupancy — no
    `source_path`, no `digest`, because those live in the membership relation now."""
    return {"id": rid, "digest": "", "title": "", "source_path": "", "chunk_index": 0,
            "provenance": Provenance.CODE.value, "text": rid, "layer": "code_ast",
            "qualname": "", "line_start": 0, "line_end": 0, "vector": vec}


def test_shed_code_atom_rows_never_collapse_into_a_bogus_source_set(tmp_path):
    """`source_sets(store)` defaults to ALL STRATA by design — "a structural grouping utility, not
    a mirror read" — and `group_sources` keys on `digest`. Shed atom rows all carry `digest=''`, so
    without a guard every code atom in the corpus collapses into ONE SourceSet keyed `''`.

    It fails SILENTLY: `MixedProvenanceError` needs a digest spanning several provenances and these
    rows are uniformly CODE, so a test that merely asserts "no exception" is itself vacuous and is
    deliberately not written. The guard lives on the SHED side (`VectorStore.all_rows`) because
    `sourceset` is a kernel module that may never learn about the outer-ring membership store (the
    C5/D3 ring pin)."""
    vs = VectorStore(tmp_path / "v.lance", dim=3)
    vs.add([
        _row("a", 0, [1.0, 0.0, 0.0], Provenance.AUTHORED_SOLO),
        _row("a", 1, [0.0, 1.0, 0.0], Provenance.AUTHORED_SOLO),
        _atom_row("code_ast:aaaa", [0.0, 0.0, 1.0]),
        _atom_row("code_ast:bbbb", [0.0, 0.0, 0.5]),
        _atom_row("code_text:cccc", [0.5, 0.0, 0.5]),
    ])
    # PRECONDITION: the store really holds ≥2 shed code atom rows. Without this the check below
    # passes on a store that simply had no code in it.
    shed = [r for r in vs.all_rows(provenances={Provenance.CODE}) if is_code_atom_row(r)]
    assert len(shed) >= 2

    # THE FALSIFIER, REPRODUCED: grouping the physical table DOES produce the bogus '' set — so
    # the guard below is load-bearing, not a claim about a bug that could not happen.
    bogus = {s.digest: s for s in group_sources(vs.all_rows(include_atom_rows=True))}
    assert "" in bogus and len(bogus[""]) == len(shed)

    # THE GUARD: the default (all-strata) read excludes them, so no such set is returned.
    sets = {s.digest: s for s in source_sets(vs)}
    assert "" not in sets
    assert set(sets) == {"a"} and len(sets["a"]) == 2
    # ...and the code lane still reads its own rows by asking for them by name (the sync path)
    assert len(vs.all_rows(provenances={Provenance.CODE})) == len(shed)


def test_the_guard_leaves_a_legacy_per_version_code_row_alone(tmp_path):
    """The guard keys on the SHED (`is_code_atom_row`), never on the provenance: a pre-D1 code row
    still carries its `(source_path, digest)` and is still a legitimate source object, so it keeps
    grouping. Without this, the guard would silently disappear the live store's existing code rows
    from every structural consumer before bp-153 has rebuilt anything."""
    vs = VectorStore(tmp_path / "v.lance", dim=3)
    legacy = {**_atom_row("m.py:code_ast:dddd", [1.0, 0.0, 0.0]),
              "digest": "blob1", "source_path": "m.py", "title": "m.py"}
    vs.add([legacy, _atom_row("code_ast:eeee", [0.0, 1.0, 0.0])])
    assert not is_code_atom_row(legacy)                      # PRECONDITION: it is NOT shed
    assert {s.digest for s in source_sets(vs)} == {"blob1"}
