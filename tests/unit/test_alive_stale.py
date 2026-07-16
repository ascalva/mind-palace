"""`alive_stale_energy` — the global alive/stale harmonic-velocity discriminator (bp-052 Item 2;
dn-velocity-instruments §2.2 (b)).

Proves the §2.2 falsifier clauses as tests (plan §8): a weight change lying ONLY along gradient
directions ⇒ harmonic-velocity energy ≈ 0 (the falsifier — harmonic energy from a gradient-only
change would be fabricated); β₁ = 0 on the common restriction ⇒ a void reading with the reason
recorded; the three Hodge components are mutually orthogonal within tolerance and the reported
energies equal an INDEPENDENT decomposition's norms; a version boundary inside the window ⇒ an empty
report (A7 — the exact apophenia leak the instrument refuses); the common restriction keeps only
edges present at BOTH anchors (X1 — birth/death a separate axis); deterministic run-to-run.
Backbones with KNOWN topology (4-cycle → β₁=1, triangle+hole → curl and harmonic live) — no store.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from core.complex.hodge import edge_index, hodge_decompose
from core.velocity_view import WeightedBackbone, alive_stale_energy


def _backbone(edge_weights: dict[tuple[str, str], float], *, anchor: str = "c1",
              version: str = "embed-v1", extra_nodes: tuple[str, ...] = ()) -> WeightedBackbone:
    """A weighted, symmetric, zero-diagonal `WeightedBackbone` from `{(u, v): weight}`, row-aligned
    to the sorted node ids. `extra_nodes` lets a snapshot carry an isolated node (a node-delta)."""
    names = sorted({n for e in edge_weights for n in e} | set(extra_nodes))
    nidx = {name: i for i, name in enumerate(names)}
    n = len(names)
    dense = np.zeros((n, n), dtype=np.float64)
    for (u, v), w in edge_weights.items():
        i, j = nidx[u], nidx[v]
        dense[i, j] = dense[j, i] = w
    return WeightedBackbone(anchor=anchor, interpreter_version=version,
                            nodes=tuple(names), A=sp.csr_matrix(dense))


# A chordless 4-cycle a-b-c-d-a → β₁ = 1, no triangles (curl space trivial).
_SQUARE_EDGES = [("a", "b"), ("b", "c"), ("c", "d"), ("a", "d")]
# A filled triangle a-b-c glued to a 4-cycle hole a-c-d-e-a → β₁ = 1 AND one triangle (curl live).
_TRI_PLUS_HOLE = [("a", "b"), ("a", "c"), ("b", "c"), ("c", "d"), ("d", "e"), ("a", "e")]


def test_gradient_only_change_has_zero_harmonic_energy():
    # THE falsifier: Δw lying purely along gradient directions (∂₁ᵀx, a node-potential difference)
    # must produce ≈ 0 harmonic velocity — a hole whose weights only shifted by a potential is NOT
    # being orbited. Base weight 5.0; potential x on the nodes; w_b(u,v) = 5 + (x[v] − x[u]).
    x = {"a": 1.0, "b": 3.0, "c": 2.0, "d": 5.0}
    w_a = {e: 5.0 for e in _SQUARE_EDGES}
    w_b = {(u, v): 5.0 + (x[v] - x[u]) for (u, v) in _SQUARE_EDGES}   # Δw = ∂₁ᵀx, a pure gradient
    report = alive_stale_energy(_backbone(w_a, anchor="c1"), _backbone(w_b, anchor="c2"))
    assert report.anchor_a == "c1" and report.anchor_b == "c2"
    assert report.empty_reason is None
    assert report.harmonic_energy < 1e-9          # no fabricated harmonic velocity
    assert report.curl_energy < 1e-12             # a 4-cycle has no triangles ⇒ curl ≡ 0
    assert report.gradient_energy > 1.0           # the change is real, just gradient-shaped


def test_beta1_zero_is_a_void_reading():
    # A path a-b-c (a tree) has β₁ = 0 — no hole to be alive or stale. Any Δw decomposes with a
    # structurally zero harmonic part; the report says so (honest seam), never a spurious claim.
    w_a = {("a", "b"): 2.0, ("b", "c"): 3.0}
    w_b = {("a", "b"): 9.0, ("b", "c"): 1.0}
    report = alive_stale_energy(_backbone(w_a), _backbone(w_b))
    assert report.harmonic_energy < 1e-9
    assert report.empty_reason is not None and "β₁=0" in report.empty_reason
    assert report.gradient_energy > 0.0           # the gradient reading is still real


def test_hodge_components_orthogonal_and_energies_match_independent_decomposition():
    # A structure with a live curl AND a live hole: every Hodge component is nonzero for a general
    # Δw. The three parts must be mutually orthogonal, and the report's energies must equal the
    # norms of an INDEPENDENT hodge_decompose on the same binary backbone + Δw.
    rng = np.random.default_rng(7)
    w_a = {e: float(rng.uniform(1.0, 2.0)) for e in _TRI_PLUS_HOLE}
    w_b = {e: float(rng.uniform(1.0, 2.0)) for e in _TRI_PLUS_HOLE}
    report = alive_stale_energy(_backbone(w_a), _backbone(w_b))
    assert report.empty_reason is None

    # independent path: binary structural backbone + Δw in edge_index order → hodge_decompose.
    names = sorted({n for e in _TRI_PLUS_HOLE for n in e})
    nidx = {name: i for i, name in enumerate(names)}
    ipairs = sorted((nidx[u], nidx[v]) if nidx[u] < nidx[v] else (nidx[v], nidx[u])
                    for u, v in _TRI_PLUS_HOLE)
    n = len(names)
    rows = np.array([u for u, _ in ipairs] + [v for _, v in ipairs], dtype=np.int64)
    cols = np.array([v for _, v in ipairs] + [u for u, _ in ipairs], dtype=np.int64)
    a_bin = sp.csr_matrix((np.ones(2 * len(ipairs)), (rows, cols)), shape=(n, n))
    idx = edge_index(a_bin)
    dw = np.zeros(len(idx), dtype=np.float64)
    for (u, v) in _TRI_PLUS_HOLE:
        key = (u, v) if u < v else (v, u)
        edge = (nidx[key[0]], nidx[key[1]])
        dw[idx[edge]] = w_b[(u, v)] - w_a[(u, v)]
    parts = hodge_decompose(dw, a_bin)

    assert abs(parts.gradient @ parts.curl) < 1e-8
    assert abs(parts.gradient @ parts.harmonic) < 1e-8
    assert abs(parts.curl @ parts.harmonic) < 1e-8
    assert np.isclose(report.harmonic_energy, np.linalg.norm(parts.harmonic), atol=1e-9)
    assert np.isclose(report.gradient_energy, np.linalg.norm(parts.gradient), atol=1e-9)
    assert np.isclose(report.curl_energy, np.linalg.norm(parts.curl), atol=1e-9)
    # the structure is chosen so both curl and harmonic are genuinely exercised (not trivially 0).
    assert report.harmonic_energy > 1e-6 and report.curl_energy > 1e-6


def test_version_boundary_voids_the_reading():
    # THE A7 falsifier: the two snapshots carry different interpreter versions ⇒ a re-embed
    # boundary sits inside the window ⇒ emit NOTHING (a reading across a re-embed = the leak).
    w_a = {e: 1.0 for e in _SQUARE_EDGES}
    w_b = {e: 4.0 for e in _SQUARE_EDGES}
    report = alive_stale_energy(
        _backbone(w_a, anchor="c1", version="embed-v1"),
        _backbone(w_b, anchor="c2", version="embed-v2"))
    assert report.empty_reason is not None and "A7" in report.empty_reason
    assert report.harmonic_energy == 0.0 and report.gradient_energy == 0.0
    assert report.curl_energy == 0.0
    assert report.interpreter_version == "embed-v1→embed-v2"    # the boundary is visible


def test_common_restriction_keeps_only_edges_present_at_both_anchors():
    # X1: Δw is defined only on edges present at BOTH anchors; a born/died edge is a separate axis.
    # snap_a carries a-b and b-c; snap_b carries b-c and c-d. The only common edge is b-c, so the
    # decomposition sees exactly Δw(b,c) = 10 − 4 = 6 on a one-edge (tree) complex ⇒ pure gradient.
    snap_a = _backbone({("a", "b"): 7.0, ("b", "c"): 4.0})
    snap_b = _backbone({("b", "c"): 10.0, ("c", "d"): 2.0})
    report = alive_stale_energy(snap_a, snap_b)
    assert report.empty_reason is not None and "β₁=0" in report.empty_reason  # one edge ⇒ β₁=0
    assert report.harmonic_energy < 1e-12
    assert np.isclose(report.gradient_energy, 6.0, atol=1e-9)   # only b-c carried, |10 − 4| = 6


def test_no_common_nodes_is_empty():
    report = alive_stale_energy(_backbone({("a", "b"): 1.0}), _backbone({("c", "d"): 1.0}))
    assert report.empty_reason is not None and "no common edges" in report.empty_reason
    assert report.harmonic_energy == 0.0


def test_energy_is_deterministic_run_to_run():
    w_a = {e: 1.0 for e in _TRI_PLUS_HOLE}
    w_b = {e: 2.5 for e in _TRI_PLUS_HOLE}
    r1 = alive_stale_energy(_backbone(w_a), _backbone(w_b))
    r2 = alive_stale_energy(_backbone(w_a), _backbone(w_b))
    assert (r1.harmonic_energy, r1.gradient_energy, r1.curl_energy) == \
           (r2.harmonic_energy, r2.gradient_energy, r2.curl_energy)
