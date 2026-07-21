"""The mode-3 temporal operators — π_active, σ_*/σ^*, ‖[d,τ]‖, T_active (bp-033 Items 9–12;
dn-temporal-retrieval-algebra §2.2–§2.3).

Each operator law from the note is a runnable check: π_active is an idempotent contraction that is
NOT a chain map; σ_* is a chain map iff F1 (a severed citation visibly breaks the law); ‖[d,τ]‖
EQUALS the discrete severed-citation count (Result 2, "not a proxy"); T_active is a contraction; a
diamond stop-and-raises. Deterministic; a fake fixture store, no model, no network.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from core.complex.hodge import boundary_1
from core.stores.reference_edges import ReferenceEdge, ReferenceEdgeStore
from core.temporal.acquire import build_citation_complex
from core.temporal.complex import CitationComplex
from core.temporal.operators import (
    DiamondError,
    active_projection,
    is_chain_map,
    pullback_0,
    pushforward_0,
    pushforward_1,
    sigma_node_map,
    t_active,
)
from core.temporal.superconnection import curvature, curvature_norm, is_flat, severed_citations


def _complex(tmp_path: Path, name: str, edges: list[tuple[str, str]]) -> CitationComplex:
    store = ReferenceEdgeStore(tmp_path / f"{name}.sqlite")
    store.add_batch([
        ReferenceEdge.mint(source_kind="corpus", source_ref=u, target_kind="corpus",
                           target_ref=v, ref_type="design-ref", commit_sha=name, source_line=i + 1)
        for i, (u, v) in enumerate(edges)
    ])
    return build_citation_complex(store)


_CYCLE = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")]     # 4-cycle, all 4 nodes present
_PATH = [("a", "b"), ("b", "c"), ("c", "d")]        # drop d—a → the {d,a} citation is severed
_IDENTITY = {"a": "a", "b": "b", "c": "c", "d": "d"}          # rename-stable ids carry the node id


def _spectral_norm(M: np.ndarray) -> float:
    return float(np.linalg.norm(M, 2)) if M.size else 0.0


# ── Item 9: π_active ────────────────────────────────────────────────────────────────────────

def test_pi_active_is_an_idempotent_contraction(tmp_path):
    cx = _complex(tmp_path, "n", _CYCLE)
    pi = active_projection(cx, superseded={"c"})
    assert np.allclose(pi @ pi, pi)                          # idempotent Π² = Π
    assert _spectral_norm(pi) <= 1.0 + 1e-9                  # contraction ‖Π‖ ≤ 1
    assert pi[cx.node_index["c"], cx.node_index["c"]] == 0.0  # annihilates the superseded node
    assert pi[cx.node_index["a"], cx.node_index["a"]] == 1.0  # keeps the active node


def test_pi_active_is_not_a_chain_map(tmp_path):
    # π_active must NOT intertwine with the coboundary δ⁰ (node→edge): unlike σ_*, it destroys
    # structure. Π_edge δ⁰ ≠ δ⁰ Π_node whenever an edge joins an active and a superseded node.
    cx = _complex(tmp_path, "n", _CYCLE)
    superseded = {"c"}
    pi_node = active_projection(cx, superseded)
    delta0 = boundary_1(cx.A_cite).toarray().T              # C⁰ → C¹, (δ⁰f)(u,v) = f(v) − f(u)
    edge_active = np.diag([0.0 if (cx.nodes[u] in superseded or cx.nodes[v] in superseded)
                           else 1.0 for u, v in cx.edges])
    assert not np.allclose(edge_active @ delta0, delta0 @ pi_node)   # NOT a chain map


# ── Item 10: σ_* / σ^* ──────────────────────────────────────────────────────────────────────

def test_sigma_star_is_a_chain_map_and_degree_zero_under_F1(tmp_path):
    cx_n = _complex(tmp_path, "n", _CYCLE)
    cx_np1 = _complex(tmp_path, "np1", _CYCLE)               # every citation carries forward (F1)
    imap = sigma_node_map(cx_n, cx_np1, _IDENTITY)
    assert is_chain_map(cx_n, cx_np1, imap)                  # σ_* ∂ = ∂ σ_*
    # degree 0: nodes → nodes, edges → edges (shapes preserve the grading).
    assert pushforward_0(cx_n, cx_np1, imap).shape == (cx_np1.n_nodes, cx_n.n_nodes)
    assert pushforward_1(cx_n, cx_np1, imap).shape == (cx_np1.n_edges, cx_n.n_edges)


def test_severed_citation_breaks_the_chain_map_law(tmp_path):
    cx_n = _complex(tmp_path, "n", _CYCLE)
    cx_np1 = _complex(tmp_path, "np1", _PATH)               # {d,a} severed — F1 fails
    imap = sigma_node_map(cx_n, cx_np1, _IDENTITY)
    assert not is_chain_map(cx_n, cx_np1, imap)             # the honest negative


def test_pullback_is_a_contraction(tmp_path):
    cx_n = _complex(tmp_path, "n", _CYCLE)
    cx_np1 = _complex(tmp_path, "np1", _CYCLE)
    imap = sigma_node_map(cx_n, cx_np1, _IDENTITY)
    s0 = pullback_0(cx_n, cx_np1, imap).toarray()
    assert _spectral_norm(s0) <= 1.0 + 1e-9                 # σ^* always a contraction


# ── Item 11: ‖[d,τ]‖ = the discrete severed-citation count ──────────────────────────────────

def test_curvature_norm_equals_the_discrete_severed_count(tmp_path):
    cx_n = _complex(tmp_path, "n", _CYCLE)
    cx_np1 = _complex(tmp_path, "np1", _PATH)              # exactly one severed citation: {d,a}
    imap = sigma_node_map(cx_n, cx_np1, _IDENTITY)
    severed = severed_citations(cx_n, cx_np1, imap)
    da = (cx_n.node_index["a"], cx_n.node_index["d"])
    assert severed == [(min(da), max(da))]                 # the {d,a} edge, exactly
    # Result 2, "not a proxy": the operator norm IS the discrete count.
    assert curvature_norm(cx_n, cx_np1, imap) == len(severed) == 1
    # and the [d,τ] matrix is supported on exactly that edge's row.
    C = curvature(cx_n, cx_np1, imap).toarray()
    nonzero_rows = {int(r) for r in np.nonzero(C.any(axis=1))[0]}
    assert nonzero_rows == {cx_n.edges.index((min(da), max(da)))}


def test_flat_when_every_citation_carries_forward(tmp_path):
    cx_n = _complex(tmp_path, "n", _CYCLE)
    cx_np1 = _complex(tmp_path, "np1", _CYCLE)             # F1 fully holds
    imap = sigma_node_map(cx_n, cx_np1, _IDENTITY)
    assert is_flat(cx_n, cx_np1, imap)                     # [d,τ] = 0 — the bicomplex case
    assert curvature_norm(cx_n, cx_np1, imap) == 0


# ── Item 12: T_active composite + contraction; the diamond stop-and-raise ───────────────────

def test_t_active_is_a_contraction(tmp_path):
    cx_n = _complex(tmp_path, "n", _CYCLE)
    cx_np1 = _complex(tmp_path, "np1", _CYCLE)
    imap = sigma_node_map(cx_n, cx_np1, _IDENTITY)
    T = t_active(cx_n, cx_np1, imap, superseded_np1={"c"})
    assert _spectral_norm(T) <= 1.0 + 1e-9                 # ‖T_active‖ ≤ 1 (Result 5)


def test_diamond_is_a_stop_and_raise(tmp_path):
    # A merge (two X_n notes onto one successor) is not single-valued σ — the linear-chain
    # operators do not apply (§10 / TA-c).
    cx_n = _complex(tmp_path, "n", [("a", "b")])
    cx_np1 = _complex(tmp_path, "np1", [("x", "y")])
    with pytest.raises(DiamondError):
        sigma_node_map(cx_n, cx_np1, {"a": "x", "b": "x"})
