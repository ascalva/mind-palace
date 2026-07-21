"""The citation complex `X_cite` — assembly, boundary maps, and the topological falsifier
(bp-032 Items 5–7; dn-temporal-retrieval-algebra §3 Consequence 1).

The load-bearing check is `dim ker L₁ == ripser β₁` on fixtures with KNOWN cycle structure (tree →
β₁=0, 4-cycle → β₁=1): the incidence-algebra β₁ (reused from `core/complex/hodge`) must equal an
INDEPENDENT ripser H₁ count on `distance = 1 − w`. Plus `δ_D² = 0` on a multi-step supersession
chain (Result 1 H0) and the cycle stop-and-raise. Deterministic; no model, no network.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.complex.topology import persistence
from core.stores.reference_edges import ReferenceEdge, ReferenceEdgeStore
from core.temporal.acquire import build_citation_complex
from core.temporal.boundary import (
    SupersessionCycleError,
    delta_D_squared_is_zero,
    poset_from_chains,
    poset_from_pairs,
)
from core.temporal.complex import (
    citation_distance_matrix,
    dim_ker_L1,
    flag_boundary_composition_is_zero,
)


def _cite_store(tmp_path: Path, edges: list[tuple[str, str]]) -> ReferenceEdgeStore:
    """A citation store holding exactly the given doc→doc (`corpus_to_corpus`) edges."""
    store = ReferenceEdgeStore(tmp_path / "reference_edges.sqlite")
    store.add_batch([
        ReferenceEdge.mint(source_kind="corpus", source_ref=u, target_kind="corpus",
                           target_ref=v, ref_type="design-ref", commit_sha="c0", source_line=i + 1)
        for i, (u, v) in enumerate(edges)
    ])
    return store


def _ripser_b1(cx) -> int:
    """Independent β₁: ripser H₁ alive at the flag-complex scale `t = 0` (all citation edges are at
    distance 0; non-edges at 1). The Item-7 oracle, computed a different way than `dim ker L₁`."""
    D = citation_distance_matrix(cx)
    if D.shape[0] < 1:
        return 0
    dgm1 = persistence(D, maxdim=1)["dgms"][1]
    return sum(1 for b, d in dgm1 if b <= 1e-9 < d)


# ── Item 5: deterministic assembly ──────────────────────────────────────────────────────────

def test_assembly_is_deterministic(tmp_path):
    store = _cite_store(tmp_path, [("b", "a"), ("a", "c"), ("c", "b")])  # a triangle, mixed order
    cx1 = build_citation_complex(store)
    cx2 = build_citation_complex(store)
    assert cx1.nodes == cx2.nodes == ("a", "b", "c")          # sorted, order-independent
    assert cx1.edges == cx2.edges                             # undirected, sorted, deduped
    assert cx1.A_cite.toarray().tolist() == cx2.A_cite.toarray().tolist()  # identical backbone
    assert cx1.edges == ((0, 1), (0, 2), (1, 2))              # {a,b},{a,c},{b,c}


def test_self_citation_is_not_a_one_cell(tmp_path):
    store = _cite_store(tmp_path, [("a", "a"), ("a", "b")])
    cx = build_citation_complex(store)
    assert cx.edges == ((0, 1),)                              # the a→a self-loop dropped


def test_empty_store_is_the_empty_complex(tmp_path):
    cx = build_citation_complex(_cite_store(tmp_path, []))
    assert cx.n_nodes == 0 and cx.n_edges == 0
    assert dim_ker_L1(cx) == 0


# ── Item 7: dim ker L₁ == ripser β₁ on known fixtures ───────────────────────────────────────

def test_tree_has_no_threads(tmp_path):
    # A path a—b—c—d: a tree, β₁ = 0 (no cycle). Both oracles agree.
    store = _cite_store(tmp_path, [("a", "b"), ("b", "c"), ("c", "d")])
    cx = build_citation_complex(store)
    assert dim_ker_L1(cx) == 0
    assert dim_ker_L1(cx) == _ripser_b1(cx)


def test_four_cycle_has_one_thread(tmp_path):
    # A chordless 4-cycle a—b—c—d—a: β₁ = 1 (the fundamental empty hole). The flag complex has no
    # triangle to fill it; ripser agrees at t = 0.
    store = _cite_store(tmp_path, [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")])
    cx = build_citation_complex(store)
    assert dim_ker_L1(cx) == 1
    assert dim_ker_L1(cx) == _ripser_b1(cx)


def test_filled_triangle_has_no_thread(tmp_path):
    # A 3-clique a—b—c: the flag complex FILLS the triangle, β₁ = 0 (a bespoke 2-cell rule would
    # break this — the falsifier's whole point, §11).
    store = _cite_store(tmp_path, [("a", "b"), ("b", "c"), ("a", "c")])
    cx = build_citation_complex(store)
    assert dim_ker_L1(cx) == 0
    assert dim_ker_L1(cx) == _ripser_b1(cx)


def test_flag_boundary_composition_is_zero_on_a_cite(tmp_path):
    # ∂₁∂₂ = 0 on A_cite (Item 6 leg), reused from hodge — a citation-backbone incidence sign error
    # would break it.
    store = _cite_store(tmp_path, [("a", "b"), ("b", "c"), ("a", "c")])  # has a filled triangle
    assert flag_boundary_composition_is_zero(build_citation_complex(store))


# ── bp-037 Item 1: the OPTIONAL commit anchor (β₁ "as of" one commit, not the union) ─────────

def _multi_commit_store(tmp_path: Path,
                        edges: list[tuple[str, str, str]]) -> ReferenceEdgeStore:
    """A citation store holding `(source, target, commit_sha)` edges across multiple commits."""
    store = ReferenceEdgeStore(tmp_path / "reference_edges.sqlite")
    store.add_batch([
        ReferenceEdge.mint(source_kind="corpus", source_ref=u, target_kind="corpus",
                           target_ref=v, ref_type="design-ref", commit_sha=c, source_line=i + 1)
        for i, (u, v, c) in enumerate(edges)
    ])
    return store


def test_commit_anchor_filters_to_one_snapshot(tmp_path):
    # c1 is a chordless 4-cycle a—b—c—d—a (β₁=1 in isolation); c2 re-cites a→b (a duplicate that
    # dedups in the union) plus a lone e→f (new nodes, no cycle). The anchor sees only its slice.
    store = _multi_commit_store(tmp_path, [
        ("a", "b", "c1"), ("b", "c", "c1"), ("c", "d", "c1"), ("d", "a", "c1"),
        ("a", "b", "c2"), ("e", "f", "c2"),
    ])
    at_c1 = build_citation_complex(store, commit="c1")
    assert at_c1.nodes == ("a", "b", "c", "d")               # only the c1 endpoints
    assert at_c1.n_edges == 4
    assert dim_ker_L1(at_c1) == 1                            # the c1 4-cycle's one thread

    at_c2 = build_citation_complex(store, commit="c2")
    assert at_c2.nodes == ("a", "b", "e", "f")
    assert at_c2.n_edges == 2                                # {a,b} and {e,f}, no cycle
    assert dim_ker_L1(at_c2) == 0

    # The falsifier: a c2 edge never leaks into the c1 snapshot.
    assert "e" not in at_c1.node_index and "f" not in at_c1.node_index


def test_commit_none_is_the_all_history_union_unchanged(tmp_path):
    # The default (no kwarg) === commit=None === the union over BOTH commits — the pre-bp-037
    # behaviour, bit-for-bit. The a→b citation appears at both commits and collapses to one 1-cell.
    store = _multi_commit_store(tmp_path, [
        ("a", "b", "c1"), ("b", "c", "c1"), ("c", "d", "c1"), ("d", "a", "c1"),
        ("a", "b", "c2"), ("e", "f", "c2"),
    ])
    union = build_citation_complex(store)
    assert build_citation_complex(store, commit=None).edges == union.edges  # None ≡ default
    assert union.nodes == ("a", "b", "c", "d", "e", "f")   # all 6 nodes across history
    assert union.n_edges == 5                              # 4-cycle (4) + {e,f}; dup a→b deduped
    assert dim_ker_L1(union) == 1                            # still one thread (the c1 cycle)


# ── Item 6: δ_D² = 0 and the cycle stop-and-raise ───────────────────────────────────────────

def test_delta_D_squared_is_zero_on_a_multistep_chain():
    # A note revised v1 ▸ v2 ▸ v3 ▸ v4 (one doc): a total order ⇒ a valid poset ⇒ δ_D² = 0 (H0).
    poset = poset_from_chains({"doc-a": [1, 2, 3, 4], "doc-b": [1, 2]})
    assert delta_D_squared_is_zero(poset)
    # The order complex of the length-4 chain has the expected simplices.
    assert len(poset.pairs) == (6 + 1)                       # C(4,2)=6 within doc-a, 1 within doc-b
    assert ("doc-a", 1) in poset.elements


def test_supersession_cycle_is_a_stop_and_raise():
    # A cycle (a ▸ b ▸ a) is NOT a strict partial order — H0 violated. Assembly must raise, never
    # silently return a δ_D² ≠ 0 (§10 stop-and-raise).
    a, b = ("d", 1), ("d", 2)
    with pytest.raises(SupersessionCycleError):
        poset_from_pairs({a, b}, {(a, b), (b, a)})


def test_disjoint_docs_are_incomparable():
    # Versions of different docs never become comparable — no cross-doc D-arrow is invented.
    poset = poset_from_chains({"x": [1, 2], "y": [1, 2]})
    assert (("x", 2), ("y", 1)) not in poset.relation
    assert (("x", 1), ("x", 2)) in poset.relation
