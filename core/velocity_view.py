# ── Family: velocity instruments (diachronic measurement) · OUTSIDE core/complex/ (isolation) ──
# OBJECT:    the global alive/stale hole discriminator (dn-velocity-instruments §2.2 (b)) — the
#            harmonic-velocity energy ‖P_harm(Δw)‖ (+ the gradient/curl split) of the weight change
#            Δw over the mirror-side weighted backbone's common restriction. A hole whose carrying
#            cycle shows sustained harmonic velocity is being actively orbited (alive); one with
#            P_harm(Δw) ≈ 0 is abandoned structure (stale).
# INVARIANT: read-only, deterministic, model-free, erasure-invariant. A pure function of two given
#            `WeightedBackbone` snapshots — NO store handle, NO model, NO spine (plan §9); the
#            production consumer (DD-1) assembles the backbones from build.py's cosine_adjacency and
#            passes them as data. Reuses core/complex/hodge (the safe import direction — this module
#            never reaches into core/complex internals, and core/complex never imports back).
# ENFORCED:  static (frozen dataclasses expose values only) + the A7 guard below (a version boundary
#            inside the window voids the reading) + guard (test_alive_stale.py falsifier clauses).
"""`velocity_view` — the global alive/stale harmonic-velocity energy (bp-052 Item 2).

The measurement-class instrument (b) of dn-velocity-instruments §2.2, thin and `core/complex`-using:
between two anchors, on the **mirror-side weighted backbone** restricted to the edges present at
BOTH (the X1 common restriction — edge birth/death are a separate axis, never folded into `Δw`),
split the weight-velocity 1-cochain `Δw = w_{n+1} − w_n` into its Hodge parts with the projectors:

    Δw = P_grad Δw  +  P_curl Δw  +  P_harm Δw          (mutually orthogonal, v1 combinatorial)

and report the three energies. `‖P_harm(Δw)‖ > 0` sustained = a hole being actively orbited (alive);
`≈ 0` = abandoned structure (stale). **Type `Inv`** per window pair (an energy on the common
restriction; no clock division — the `Rate(κ)` version is VI-a, parked).

**A7 — the apophenia guard (dn-temporal-retrieval-algebra §2.5).** Holes live on the interpreted,
versioned similarity backbone, so genuine evolution = Δ(record) at a **fixed** interpreter version;
a re-embed is a supersession event in the interpreter-version chain, not evolution. If the two
snapshots carry different interpreter versions, a version boundary sits inside the window and it is
**void — emit nothing** (an empty report with the reason recorded). This is the exact apophenia leak
the instrument exists to refuse: never a harmonic-velocity reading across a re-embed.

**Substrate is given, not fetched (plan §9 non-goals).** `WeightedBackbone` is passed in as data —
this module holds no store handle, runs no model, and has no spine dependency; it is a
deterministic, read-only pure function. The Hodge projectors key on the backbone's STRUCTURE (which
edges/triangles exist), not the weights (v1 inner product is combinatorial), so `Δw` decomposes over
the common
restriction's flag complex. Determinism + the dense-path size guard are inherited from `hodge.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

from core.complex.hodge import edge_index, harmonic_basis, hodge_decompose


@dataclass(frozen=True)
class WeightedBackbone:
    """A mirror-side weighted similarity backbone at one anchor, plus its interpreter version.

    `A` is the weighted, symmetric, zero-diagonal adjacency (`w ≥ 0`) — `build.py`'s
    `cosine_adjacency` output; row `i` corresponds to `nodes[i]` (the ordering is row-aligned to
    `A`). Assembled by the caller (DD-1) and passed as data; `velocity_view` retains no store
    handle. `interpreter_version` is the embedder-version coordinate the A7 guard reads (§2.4)."""

    anchor: str                            # commit SHA (recorded — Inv carries its anchors)
    interpreter_version: str               # embedder version; FIXED across the window or void (A7)
    nodes: tuple[str, ...]                 # row-aligned to A: A row i ↔ nodes[i]
    A: sp.csr_matrix                       # weighted, symmetric, zero-diagonal, w ≥ 0


@dataclass(frozen=True)
class AliveStaleReport:
    """The global alive/stale harmonic-velocity energy over the common restriction (dn-velocity-
    instruments §2.2 (b)). `harmonic_energy = ‖P_harm(Δw)‖`; `gradient_energy`/`curl_energy` are the
    complementary Hodge parts (`Δw = P_grad Δw + P_curl Δw + P_harm Δw`, mutually orthogonal).

    The honest seam: `empty_reason` is set (and nothing is claimed) when the reading is void — an
    interpreter-version boundary inside the window (A7), no common edges, or β₁ = 0 on the common
    restriction (no hole to be alive or stale)."""

    anchor_a: str                          # earlier commit SHA
    anchor_b: str                          # later commit SHA
    interpreter_version: str               # the FIXED window version, or "va→vb" at a void boundary
    harmonic_energy: float                 # ‖P_harm(Δw)‖ — sustained > 0 ⇒ alive
    gradient_energy: float                 # ‖P_grad(Δw)‖
    curl_energy: float                     # ‖P_curl(Δw)‖
    empty_reason: str | None               # the honest seam — void reading, no claim


def _weighted_edges(bb: WeightedBackbone, common: set[str]) -> dict[tuple[str, str], float]:
    """The nonzero upper-triangle edges of `bb.A` with BOTH endpoints in `common`, keyed by the
    lexicographically ordered note-id pair. Positional read: `bb.A` row `i` ↔ `bb.nodes[i]`."""
    coo = sp.triu(bb.A, k=1).tocoo()
    out: dict[tuple[str, str], float] = {}
    for i, j, w in zip(coo.row, coo.col, coo.data, strict=True):
        if w == 0.0:
            continue
        ni, nj = bb.nodes[int(i)], bb.nodes[int(j)]
        if ni in common and nj in common:
            out[(ni, nj) if ni < nj else (nj, ni)] = float(w)
    return out


def _common_restriction(
    a: WeightedBackbone, b: WeightedBackbone,
) -> tuple[sp.csr_matrix, np.ndarray]:
    """The structural (binary) backbone over the common nodes' common edges — the pairs present and
    nonzero at BOTH anchors (X1: `Δw` is defined only on common edges; birth/death are a separate
    axis) — and `Δw = w_b − w_a` on those edges, keyed by `edge_index(A_common)`. Deterministic."""
    common = set(a.nodes) & set(b.nodes)
    ea, eb = _weighted_edges(a, common), _weighted_edges(b, common)
    common_keys = sorted(ea.keys() & eb.keys())

    common_nodes = sorted(common)
    nidx = {name: i for i, name in enumerate(common_nodes)}
    n = len(common_nodes)
    int_edges = [(nidx[u], nidx[v]) for u, v in common_keys]   # u < v by name ⇒ by index

    if int_edges:
        rows = np.array([u for u, _ in int_edges] + [v for _, v in int_edges], dtype=np.int64)
        cols = np.array([v for _, v in int_edges] + [u for u, _ in int_edges], dtype=np.int64)
        data = np.ones(2 * len(int_edges), dtype=np.float64)
        a_common: sp.csr_matrix = sp.csr_matrix((data, (rows, cols)), shape=(n, n))
    else:
        a_common = sp.csr_matrix((n, n))

    idx = edge_index(a_common)
    dw = np.zeros(len(idx), dtype=np.float64)
    for key, edge in zip(common_keys, int_edges, strict=True):
        dw[idx[edge]] = eb[key] - ea[key]
    return a_common, dw


def alive_stale_energy(a: WeightedBackbone, b: WeightedBackbone) -> AliveStaleReport:
    """The global alive/stale harmonic-velocity energy between snapshot `a` (earlier) and `b`
    (later) — `‖P_harm(Δw)‖` and its gradient/curl complement over the common restriction
    (dn-velocity-instruments §2.2 (b)). Read-only, deterministic, model-free, `Inv` (no clock).

    A7 guard first: a mismatched interpreter version means a re-embed boundary sits inside the
    window, so `Δw` mixes content-change with embedder-artifact — the reading is void (an empty
    report, reason recorded). Then the Hodge split of `Δw` over the common backbone; the honest
    seam also fires when there are no common edges, or β₁ = 0 (no hole to be alive/stale)."""
    if a.interpreter_version != b.interpreter_version:
        return AliveStaleReport(
            anchor_a=a.anchor, anchor_b=b.anchor,
            interpreter_version=f"{a.interpreter_version}→{b.interpreter_version}",
            harmonic_energy=0.0, gradient_energy=0.0, curl_energy=0.0,
            empty_reason=("interpreter-version boundary inside the window "
                          f"({a.interpreter_version}→{b.interpreter_version}): A7 voids Δw across "
                          "a re-embed (genuine evolution is Δ(record) at a fixed embedder) — "
                          "emitting nothing, never a reading across a re-embed"),
        )

    a_common, dw = _common_restriction(a, b)
    if dw.shape[0] == 0:
        return AliveStaleReport(
            anchor_a=a.anchor, anchor_b=b.anchor, interpreter_version=a.interpreter_version,
            harmonic_energy=0.0, gradient_energy=0.0, curl_energy=0.0,
            empty_reason="no common edges: Δw is empty — nothing to decompose (honest seam)",
        )

    beta1 = int(harmonic_basis(a_common).shape[1])
    parts = hodge_decompose(dw, a_common)
    empty_reason = None if beta1 > 0 else (
        "β₁=0 on the common restriction: no harmonic subspace — no hole to be alive or stale "
        "(honest seam; harmonic_energy is structurally 0)")
    return AliveStaleReport(
        anchor_a=a.anchor, anchor_b=b.anchor, interpreter_version=a.interpreter_version,
        harmonic_energy=float(np.linalg.norm(parts.harmonic)),
        gradient_energy=float(np.linalg.norm(parts.gradient)),
        curl_energy=float(np.linalg.norm(parts.curl)),
        empty_reason=empty_reason,
    )
