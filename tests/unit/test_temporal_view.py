"""`TemporalView` — the commit-anchored β₁ read surface (bp-037 / CQ-wire, Item 2).

Proves the single-snapshot reads over in-memory fixtures with KNOWN topology (4-cycle → β₁=1, filled
triangle → β₁=0), that the anchor scopes to one commit (never the all-history union), that an empty
anchor is honest, and that no store/mutator surface is reachable through the frozen view (the scope
guard — mirrors `test_reference_view.py`). Deterministic; no model, no network.
"""

from __future__ import annotations

from pathlib import Path

from core.stores.reference_edges import ReferenceEdge, ReferenceEdgeStore
from core.stores.versions import VersionStore
from core.temporal.complex import build_citation_complex
from core.temporal_view import TemporalView, _restrict, supersession_wellfounded


def _cite_store(tmp_path: Path, edges: list[tuple[str, str, str]]) -> ReferenceEdgeStore:
    """A citation store of `(source, target, commit_sha)` doc→doc (`corpus_to_corpus`) edges."""
    store = ReferenceEdgeStore(tmp_path / "reference_edges.sqlite")
    store.add_batch([
        ReferenceEdge.mint(source_kind="corpus", source_ref=u, target_kind="corpus",
                           target_ref=v, ref_type="design-ref", commit_sha=c, source_line=i + 1)
        for i, (u, v, c) in enumerate(edges)
    ])
    return store


def test_citation_threads_counts_beta1_at_the_anchor(tmp_path):
    # A chordless 4-cycle a—b—c—d—a at c1 → β₁ = 1 (no triangle fills it).
    store = _cite_store(tmp_path, [
        ("a", "b", "c1"), ("b", "c", "c1"), ("c", "d", "c1"), ("d", "a", "c1"),
    ])
    view = TemporalView.over(store, commit="c1")
    assert view.commit == "c1"
    assert view.citation_threads() == 1
    assert view.boundary_composition_is_zero() is True
    assert view.n_nodes == 4
    assert view.n_edges == 4


def test_filled_triangle_has_no_thread(tmp_path):
    store = _cite_store(tmp_path, [("a", "b", "c1"), ("b", "c", "c1"), ("a", "c", "c1")])
    view = TemporalView.over(store, commit="c1")
    assert view.citation_threads() == 0        # the flag complex fills the triangle
    assert view.n_nodes == 3 and view.n_edges == 3


def test_anchor_scopes_to_one_commit(tmp_path):
    # The falsifier: an extra edge at c2 must not enter the c1 view (the all-history-union bug).
    store = _cite_store(tmp_path, [
        ("a", "b", "c1"), ("b", "c", "c1"), ("c", "d", "c1"), ("d", "a", "c1"),
        ("e", "f", "c2"),
    ])
    at_c1 = TemporalView.over(store, commit="c1")
    assert at_c1.n_nodes == 4 and at_c1.n_edges == 4    # no e/f leaked in
    assert at_c1.citation_threads() == 1
    at_c2 = TemporalView.over(store, commit="c2")
    assert at_c2.n_nodes == 2 and at_c2.n_edges == 1
    assert at_c2.citation_threads() == 0


def test_empty_anchor_is_honest(tmp_path):
    # A commit with no citation edges → the empty complex: β₁ = 0, ∂₁∂₂=0 trivially, not a crash.
    store = _cite_store(tmp_path, [("a", "b", "c1")])
    view = TemporalView.over(store, commit="nonesuch")
    assert view.n_nodes == 0 and view.n_edges == 0
    assert view.citation_threads() == 0
    assert view.boundary_composition_is_zero() is True


def test_no_store_or_mutator_reachable_through_the_view(tmp_path):
    # The scope guard (§2.1): the frozen view names reads only — no store handle, no mutator.
    store = _cite_store(tmp_path, [("a", "b", "c1")])
    view = TemporalView.over(store, commit="c1")
    for forbidden in ("add_batch", "_conn", "store", "_store", "all", "for_commit"):
        assert not hasattr(view, forbidden), f"scope leak: {forbidden} reachable via TemporalView"
    # The only fields are the frozen complex + the anchor commit — no live store reference retained.
    assert set(vars(view)) == {"_complex", "commit"}


# ── bp-038 Item 1: _restrict + coherence_to (two-snapshot ‖[d,τ]‖) ─────────────────────────────

def _coherence(store, commit_from, commit_to):
    return TemporalView.over(store, commit=commit_from).coherence_to(
        TemporalView.over(store, commit=commit_to))


def test_restrict_keeps_only_the_common_subgraph(tmp_path):
    # A 4-cycle a-b-c-d-a restricted to {a,b,c}: the two edges touching d are dropped.
    cx = build_citation_complex(_cite_store(tmp_path, [
        ("a", "b", "c1"), ("b", "c", "c1"), ("c", "d", "c1"), ("d", "a", "c1")]), commit="c1")
    r = _restrict(cx, {"a", "b", "c"})
    assert r.nodes == ("a", "b", "c")
    assert r.n_edges == 2                        # {a,b},{b,c}; {c,d},{d,a} dropped (d out)
    assert set(r.edges) == {(0, 1), (1, 2)}                  # a-b, b-c in the re-indexed complex


def test_coherence_counts_a_severed_citation(tmp_path):
    # X_n = 4-cycle a-b-c-d-a at c1; X_{n+1} = a-b-c-d (the d→a citation SEVERED) at c2, all nodes
    # still present → ‖[d,τ]‖ = 1, severed = {a,d}, not flat, no node departure.
    store = _cite_store(tmp_path, [
        ("a", "b", "c1"), ("b", "c", "c1"), ("c", "d", "c1"), ("d", "a", "c1"),
        ("a", "b", "c2"), ("b", "c", "c2"), ("c", "d", "c2")])
    report = _coherence(store, "c1", "c2")
    assert report.commit_from == "c1" and report.commit_to == "c2"
    assert report.common_nodes == 4
    assert report.coherence_norm == 1
    assert report.severed == (("a", "d"),)                  # the severed citation, lex-sorted
    assert report.is_flat is False
    assert report.nodes_added == 0 and report.nodes_dropped == 0


def test_coherence_is_flat_when_every_citation_carries_forward(tmp_path):
    # Only an ADDITION (c→d at c2), nothing severed → ‖[d,τ]‖ = 0, flat, one node added.
    store = _cite_store(tmp_path, [
        ("a", "b", "c1"), ("b", "c", "c1"),
        ("a", "b", "c2"), ("b", "c", "c2"), ("c", "d", "c2")])
    report = _coherence(store, "c1", "c2")
    assert report.coherence_norm == 0
    assert report.severed == ()
    assert report.is_flat is True
    assert report.nodes_added == 1                           # d
    assert report.nodes_dropped == 0
    assert report.common_nodes == 3                          # a,b,c


def test_coherence_a_dropped_node_is_not_a_severed_citation(tmp_path):
    # THE restrict-to-common falsifier (§3 Q1): e→a exists at c1, e is GONE at c2. The e→a citation
    # must NOT count as severed — it's a node departure (nodes_dropped), not a coherence loss
    # (if it counted as coherence_norm == 1, the rejected augment-semantics would have leaked in).
    store = _cite_store(tmp_path, [
        ("e", "a", "c1"), ("a", "b", "c1"), ("b", "c", "c1"),
        ("a", "b", "c2"), ("b", "c", "c2")])                 # e (and e→a) gone at c2
    report = _coherence(store, "c1", "c2")
    assert report.nodes_dropped == 1                         # e departed
    assert report.coherence_norm == 0                        # e→a NOT counted as severed
    assert report.severed == ()
    assert report.is_flat is True
    assert report.common_nodes == 3                          # a,b,c


# ── bp-038 Item 2: supersession_wellfounded (poset δ_D²=0) ─────────────────────────────────────

def test_supersession_wellfounded_on_a_clean_chain(tmp_path):
    # A total order v1 ▸ v2 ▸ v3 (one doc) + a two-version doc → a valid poset ⇒ δ_D² = 0.
    # (A cycle can't be built through VersionStore's append-only API — that stop-and-raise is proven
    # at the boundary layer, test_temporal_complex.py::test_supersession_cycle_is_a_stop_and_raise;
    # supersession_wellfounded does not catch it, so it propagates.)
    vs = VersionStore(tmp_path / "versions.sqlite")
    for _ in range(3):
        vs.record("docs/a.md", "digest-a")                  # v1 ▸ v2 ▸ v3
    vs.record("docs/b.md", "digest-b")
    try:
        assert supersession_wellfounded(doc_ids=["docs/a.md", "docs/b.md"], version_store=vs)
        assert supersession_wellfounded(doc_ids=["docs/never-recorded.md"], version_store=vs)
    finally:
        vs.close()
