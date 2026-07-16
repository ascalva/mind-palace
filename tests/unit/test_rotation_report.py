"""`RotationReport` — the harmonic-subspace rotation between two commit-anchored citation snapshots
(bp-052 Item 1; dn-velocity-instruments §2.2 (a)).

Proves the §2.2 falsifier clauses as tests (plan §8): identical snapshots ⇒ all principal angles 0
(no fabricated rotation); β₁ = 0 at either anchor ⇒ an empty report with a recorded reason and
`principal_angles == ()` (the honest seam, no fabricated geometry); the reported angles agree with
an INDEPENDENT SVD-based computation on the same harmonic bases (`scipy.linalg.subspace_angles`);
and the result is deterministic run-to-run. Built over in-memory `CitationComplex` fixtures with
KNOWN topology (4-cycle → β₁=1, path → β₁=0) — no store, no model, no network; `Inv` (no clock).
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from scipy.linalg import subspace_angles

from core.complex.hodge import edge_index, harmonic_basis
from core.temporal.complex import CitationComplex
from core.temporal_view import TemporalView


def _cx(edges: list[tuple[str, str]]) -> CitationComplex:
    """A `CitationComplex` over the note ids appearing in `edges` (undirected, binary `A_cite`) —
    mirrors `build_citation_complex`'s deterministic assembly without a store."""
    node_set: set[str] = {n for e in edges for n in e}
    nodes = tuple(sorted(node_set))
    node_index = {name: i for i, name in enumerate(nodes)}
    edge_set: set[tuple[int, int]] = set()
    for u, v in edges:
        a, b = node_index[u], node_index[v]
        if a == b:
            continue
        edge_set.add((a, b) if a < b else (b, a))
    es = tuple(sorted(edge_set))
    n = len(nodes)
    if es:
        rows = np.array([u for u, _ in es] + [v for _, v in es], dtype=np.int64)
        cols = np.array([v for _, v in es] + [u for u, _ in es], dtype=np.int64)
        data = np.ones(2 * len(es), dtype=np.float64)
        a_cite: sp.csr_matrix = sp.csr_matrix((data, (rows, cols)), shape=(n, n))
    else:
        a_cite = sp.csr_matrix((n, n))
    return CitationComplex(nodes=nodes, node_index=node_index, edges=es, A_cite=a_cite)


def _view(edges: list[tuple[str, str]], commit: str) -> TemporalView:
    return TemporalView(_complex=_cx(edges), commit=commit)


# A chordless 4-cycle a-b-c-d-a → β₁ = 1 (one thread, no triangle fills it).
_SQUARE = [("a", "b"), ("b", "c"), ("c", "d"), ("a", "d")]
# A "twisted" 4-cycle on the same nodes a-b-d-c-a → β₁ = 1, a DIFFERENT edge set (rotated thread).
_TWISTED = [("a", "b"), ("b", "d"), ("c", "d"), ("a", "c")]
# A path a-b-c-d (a tree) → β₁ = 0 (no thread).
_PATH = [("a", "b"), ("b", "c"), ("c", "d")]


def test_identical_snapshots_have_zero_rotation():
    # THE falsifier: identical snapshots ⇒ every principal angle 0 (no fabricated rotation).
    report = _view(_SQUARE, "c1").rotation_to(_view(_SQUARE, "c2"))
    assert report.anchor_a == "c1" and report.anchor_b == "c2"
    assert report.n_common == 4
    assert report.beta1_a == 1 and report.beta1_b == 1
    assert report.empty_reason is None
    assert len(report.principal_angles) == 1              # min(β₁ₐ, β₁_b)
    assert max(report.principal_angles) < 1e-6            # all angles ≈ 0


def test_beta1_zero_at_one_anchor_is_an_empty_report():
    # β₁ = 0 at the later anchor (the thread was filled/severed to a tree) ⇒ empty report, no
    # fabricated geometry (angles ()), the reason recorded.
    report = _view(_SQUARE, "c1").rotation_to(_view(_PATH, "c2"))
    assert report.beta1_a == 1 and report.beta1_b == 0
    assert report.principal_angles == ()
    assert report.empty_reason is not None
    assert "β₁=0" in report.empty_reason and "anchor_b" in report.empty_reason


def test_beta1_zero_at_both_anchors_is_empty():
    report = _view(_PATH, "c1").rotation_to(_view(_PATH, "c2"))
    assert report.beta1_a == 0 and report.beta1_b == 0
    assert report.principal_angles == ()
    assert report.empty_reason is not None
    assert "anchor_a" in report.empty_reason and "anchor_b" in report.empty_reason


def test_angles_agree_with_independent_svd_on_the_same_bases():
    # The note's falsifier: the reported principal angles must agree with an INDEPENDENT SVD-based
    # computation on the same harmonic bases. Here the two snapshots share all four nodes but carry
    # DIFFERENT threads (square vs twisted-square) ⇒ a genuine nonzero rotation in the union edge
    # space. The oracle embeds the same bases and calls `scipy.linalg.subspace_angles` (QR + SVD),
    # a code path independent of `rotation_to`'s `Qaᵀ Qb` SVD.
    cx_a, cx_b = _cx(_SQUARE), _cx(_TWISTED)
    report = TemporalView(_complex=cx_a, commit="c1").rotation_to(
        TemporalView(_complex=cx_b, commit="c2"))
    assert report.empty_reason is None and report.beta1_a == 1 and report.beta1_b == 1

    q_a, q_b = harmonic_basis(cx_a.A_cite), harmonic_basis(cx_b.A_cite)
    idx_a, idx_b = edge_index(cx_a.A_cite), edge_index(cx_b.A_cite)
    union = sorted(set(idx_a) | set(idx_b))
    uix = {e: k for k, e in enumerate(union)}
    emb_a = np.zeros((len(union), q_a.shape[1]))
    emb_b = np.zeros((len(union), q_b.shape[1]))
    for e, r in idx_a.items():
        emb_a[uix[e]] = q_a[r]
    for e, r in idx_b.items():
        emb_b[uix[e]] = q_b[r]
    oracle = sorted(float(x) for x in subspace_angles(emb_a, emb_b))

    assert np.allclose(report.principal_angles, oracle, atol=1e-9)
    # a genuine rotation: the twisted thread is not the same subspace (angle strictly positive).
    assert report.principal_angles[0] > 1e-3


def test_rotation_is_deterministic_run_to_run():
    a, b = _view(_SQUARE, "c1"), _view(_TWISTED, "c2")
    first = a.rotation_to(b).principal_angles
    second = a.rotation_to(b).principal_angles
    assert first == second                                 # byte-identical, no seed


def test_partial_node_overlap_restricts_to_common():
    # X_n carries a square on {a,b,c,d}; X_{n+1} adds node e via a d-e-a ear (a filled triangle
    # a-d-e). The common restriction to {a,b,c,d} is still the 4-cycle → n_common = 4, both β₁ = 1.
    later = _SQUARE + [("d", "e"), ("a", "e")]             # e is X_{n+1}-only; triangle a-d-e fills
    report = _view(_SQUARE, "c1").rotation_to(_view(later, "c2"))
    assert report.n_common == 4                            # e is X_{n+1}-only, dropped from common
    assert report.beta1_a == 1 and report.beta1_b == 1     # both restrict to the a-b-c-d-a square
    assert report.empty_reason is None
    assert max(report.principal_angles) < 1e-6             # same thread survives on common nodes
