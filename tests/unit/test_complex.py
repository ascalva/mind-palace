"""Unit tests for the reasoning complex (H1–H3): build_complex, Laplacians, balance, clusterer.

Proves: the complex is built ONLY from a MirrorView (firewall structural); A is a symmetric,
zero-diagonal, non-negative similarity backbone; A_signed equals A until a contradiction edge is
overlaid; derivation hyperedges surface from the DerivedStore junction; the Laplacians have the
textbook spectra; the diffusion clusterer recovers planted structure.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
import scipy.sparse as sp

from core.complex.build import build_complex, cosine_adjacency
from core.complex.spectral import diffusion_cluster_notes, fiedler, louvain_labels
from core.kernel.clearance import Clearance
from core.kernel.complex.balance import frustration
from core.kernel.complex.laplacian import laplacian, laplacian_sym
from core.kernel.complex_types import EdgeSign
from core.kernel.mirror import MirrorView, NonMirrorRowError
from core.kernel.provenance import Provenance
from core.stores.derived import DREAM, DerivedStore
from core.stores.edges import CONTRADICTS, EdgeStore


class _Rows:
    """Minimal provenance-filtering row source (like the VectorStore) for MirrorView.project."""

    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def all_rows(self, *, clearance: Clearance[Provenance]) -> list[dict[str, Any]]:
        return [r for r in self._rows if clearance.admits(r.get("provenance"))]


def _row(digest: str, vec: list[float]) -> dict[str, Any]:
    return {"digest": digest, "title": digest, "vector": vec, "text": digest,
            "provenance": Provenance.AUTHORED_SOLO.value}


def _photo_synth_view() -> MirrorView:
    # two clean themes in an 8-dim token space
    photo = [1.0, 1, 1, 1, 0, 0, 0, 0]
    synth = [0.0, 0, 0, 0, 1, 1, 1, 1]
    rng = np.random.default_rng(0)
    rows = []
    for i in range(4):
        rows.append(_row(f"p{i}", list(np.array(photo) + rng.normal(0, 0.03, 8))))
    for i in range(4):
        rows.append(_row(f"s{i}", list(np.array(synth) + rng.normal(0, 0.03, 8))))
    return MirrorView.project(_Rows(rows))


# --- H1: build_complex ----------------------------------------------------------

def test_build_complex_is_mirrorview_only():
    # The firewall is the input type: a non-authored row can't even reach build_complex, because
    # MirrorView.project refuses to construct over it (Invariant 6, structural).
    with pytest.raises(NonMirrorRowError):
        MirrorView(_rows=({"digest": "x", "provenance": Provenance.OBSERVED.value, "vector": []},))


def test_build_complex_backbone_shape():
    kx = build_complex(_photo_synth_view())
    assert kx.n == 8
    A = kx.A.toarray()
    assert np.allclose(A, A.T)                        # symmetric
    assert np.allclose(np.diag(A), 0.0)               # zero diagonal (no self-loops)
    assert (A >= 0).all()                             # similarity backbone is non-negative
    # A_signed == A with no persisted edges (all-support ⇒ balanced)
    assert np.allclose(kx.A_signed.toarray(), A)
    lam, tris = frustration(kx.A_signed)
    assert lam <= 1e-6 and tris == []


def test_build_complex_overlays_contradiction_edges(tmp_path):
    view = _photo_synth_view()
    edges = EdgeStore(tmp_path / "edges.sqlite")
    edges.add("p0", "s0", sign=EdgeSign.CONTRADICT, rel_type=CONTRADICTS, w=1.0)
    kx = build_complex(view, edges=edges)
    i, j = kx.idx["p0"], kx.idx["s0"]
    assert kx.A_signed.toarray()[i, j] == pytest.approx(-1.0)   # polarity overlaid (−w)


def test_build_complex_surfaces_derivation_hyperedges(tmp_path):
    view = _photo_synth_view()
    derived = DerivedStore(tmp_path / "derived.sqlite")
    dream = derived.add(kind=DREAM, summary="t", subjects=["p0", "p1"], derived_from=["p0", "p1"])
    kx = build_complex(view, derived=derived)
    assert (frozenset({"p0", "p1"}), dream.id) in kx.hyper


# --- H2: Laplacians + clusterer -------------------------------------------------

def test_laplacian_spectra():
    A = cosine_adjacency(np.eye(3)[[0, 0, 1]])        # nodes 0,1 identical, 2 orthogonal
    L = laplacian(A).toarray()
    assert np.allclose(L.sum(axis=1), 0.0)            # row sums zero (D − A)
    ev = np.linalg.eigvalsh(laplacian_sym(A).toarray())
    assert ev.min() >= -1e-9 and ev.max() <= 2 + 1e-9  # L_sym spectrum ⊆ [0, 2]


def test_diffusion_clusterer_recovers_two_themes():
    from core.dreaming.cluster import note_centroids
    photo = [1.0, 1, 1, 1, 0, 0, 0, 0]
    synth = [0.0, 0, 0, 0, 1, 1, 1, 1]
    rows = [_row(f"p{i}", list(photo)) for i in range(4)] + \
           [_row(f"s{i}", list(synth)) for i in range(4)]
    clusters = diffusion_cluster_notes(note_centroids(rows), threshold=0.5, min_size=2)
    assert len(clusters) == 2
    parts = {frozenset(c.digests) for c in clusters}
    assert frozenset({"p0", "p1", "p2", "p3"}) in parts
    assert frozenset({"s0", "s1", "s2", "s3"}) in parts


def test_fiedler_detects_weak_cut():
    # two triangles joined by a single weak edge → small algebraic connectivity λ₂
    A = np.zeros((6, 6))
    for i, j in [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5)]:
        A[i, j] = A[j, i] = 1.0
    A[2, 3] = A[3, 2] = 0.05                            # the weak bridge
    lam2, _vec = fiedler(sp.csr_matrix(A))
    assert lam2 > 0.0                                   # connected
    assert lam2 < 0.2                                   # but only just — a weak cut


def test_louvain_cross_check_separates_two_triangles():
    # The scikit-network cross-check (a second, modularity-based method) recovers the two triangles.
    A = np.zeros((6, 6))
    for i, j in [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5)]:
        A[i, j] = A[j, i] = 1.0
    A[2, 3] = A[3, 2] = 0.05                             # weak bridge
    labels = louvain_labels(sp.csr_matrix(A))
    assert np.array_equal(labels, louvain_labels(sp.csr_matrix(A)))   # deterministic
    assert len(set(labels)) == 2                         # two communities, bridge not chained
    assert labels[0] == labels[1] == labels[2]           # triangle A together
    assert labels[3] == labels[4] == labels[5]           # triangle B together
    assert labels[0] != labels[3]                        # and the two are distinct
