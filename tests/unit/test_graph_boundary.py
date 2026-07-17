"""The dn-core-graph-instruments boundary teeth (bp-065): P1 import purity + P3 one-Laplacian
equivalence.

(a) **P1 — the permanent tooth**: no file under `core/graph/` imports `eval`, ever. Scoped to
    the package's OWN files (a static AST scan), NOT the transitive closure — core substrate
    legitimately writes readings out through the tolerated sink (`core/temporal/spine.py:97`,
    P6), so a closure test would fail by design.
(b) **P3 — one Laplacian**: `core/graph`'s dense Laplacian adapter routes through
    `core/complex/laplacian.laplacian`; off-diagonals are EXACT vs the direct `D − W` and the
    degrees agree to ulps (summation reassociation), with R_eff values invariant at rtol 1e-10
    — the no-silent-metric-change clause (P4).

(The P5 re-export identity teeth were removed with the clean break, 2026-07-17: there are no
re-exports left — the σ*/conductance math lives in `core.graph` and every caller imports it
from there directly, so name identity is structural, nothing left to assert.)
"""

from __future__ import annotations

import ast
from pathlib import Path

_PKG = Path("core/graph")


def _package_files() -> list[Path]:
    files = sorted(_PKG.rglob("*.py"))
    assert files, "core/graph has no Python files — the package is missing"
    return files


# ── (a) P1: no eval import anywhere under core/graph ────────────────────────────────────────────


def test_core_graph_never_imports_eval() -> None:
    """The P1 invariant, statically: no `import eval` / `from eval...` in any core/graph file."""
    for path in _package_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                roots = [node.module.split(".")[0]] if node.module else []
            else:
                continue
            assert "eval" not in roots, (
                f"{path}: imports eval ({ast.dump(node)}) — P1 violated: core never imports "
                "eval for mathematics (dn-core-graph-instruments)"
            )


def test_core_graph_reads_no_clock() -> None:
    """Law C4 rides along at the package level: no `time`/`datetime` import under core/graph —
    the instruments are (σ, t, cut)-index-driven, never wall-time-driven."""
    for path in _package_files():
        tree = ast.parse(path.read_text())
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert "time" not in imported and "datetime" not in imported, f"{path} reads a clock"


# ── (b) P3: one Laplacian — the core/complex route equals the direct construction ───────────────


def test_dense_laplacian_equals_the_direct_construction() -> None:
    """P3/P4 equivalence tooth: `core.graph.conductance._dense_laplacian` (which routes through
    `core/complex/laplacian.laplacian`) equals the direct dense oracle `np.diag(W.sum(1)) − W` —
    bp-060's deleted `_laplacian`, inlined HERE as the reference.

    The measured relationship (bp-065 journal): **off-diagonals are EXACT** (both routes compute
    `0 − w[i,j]`); the **diagonal (degrees) may differ by ~1 ulp** — NumPy's unrolled
    multi-accumulator dense sum vs SciPy's sequential nonzero sum is float REASSOCIATION of the
    same values, not a metric change. The P4 STOP is metric-SCALE divergence (e.g. an L_sym
    substitution shows O(1) differences: degree-normalized entries); the tooth therefore pins
    off-diag exactness + ulp-tight degrees + VALUE-level R_eff invariance below."""
    import importlib

    import numpy as np

    gc = importlib.import_module("core.graph.conductance")

    rng_free_fixtures = [
        # two 3-cliques joined by one weak edge + an isolated node (degree-heterogeneous)
        np.array(
            [
                [0.0, 0.9, 0.8, 0.1, 0.0, 0.0, 0.0],
                [0.9, 0.0, 0.7, 0.0, 0.0, 0.0, 0.0],
                [0.8, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.1, 0.0, 0.0, 0.0, 0.6, 0.5, 0.0],
                [0.0, 0.0, 0.0, 0.6, 0.0, 0.4, 0.0],
                [0.0, 0.0, 0.0, 0.5, 0.4, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            ],
            dtype=np.float64,
        ),
        # a path graph with non-round weights (exercises float behaviour, not round numbers)
        np.diag([0.31, 0.57, 0.73], k=1) + np.diag([0.31, 0.57, 0.73], k=-1),
        # the empty graph (all-zero W: L must be exactly zero, not NaN)
        np.zeros((4, 4), dtype=np.float64),
    ]
    eps = np.finfo(np.float64).eps
    for w in rng_free_fixtures:
        oracle = np.diag(w.sum(axis=1)) - w                    # bp-060's _laplacian, verbatim
        routed = gc._dense_laplacian(w)
        assert routed.shape == oracle.shape
        # Off-diagonal: EXACT — both routes compute 0 − w[i,j] with no summation involved.
        off = ~np.eye(w.shape[0], dtype=bool)
        assert np.array_equal(routed[off], oracle[off]), (
            "off-diagonal Laplacian entries differ — this is NOT summation noise; "
            "P4 violated (a silent metric change); STOP per bp-065 §10"
        )
        # Diagonal: the same degree values summed in a different association order — within ulps.
        dmax = np.abs(np.diag(routed) - np.diag(oracle)).max()
        bound = 4.0 * eps * max(1.0, float(np.abs(np.diag(oracle)).max()))
        assert dmax <= bound, (
            f"degree divergence {dmax} exceeds the ulp bound {bound} — more than summation "
            "reassociation; P4 violated; STOP per bp-065 §10"
        )


def test_r_eff_values_invariant_under_the_laplacian_route() -> None:
    """The plan's item-2 VALUE-level invariance: R_eff computed through the core/complex-routed
    Laplacian equals the oracle-L computation to far tighter than any read precision (rtol 1e-10 —
    generous over ulp noise, catastrophically failed by any real metric change: an L_sym
    substitution differs at O(1))."""
    import importlib

    import numpy as np

    gc = importlib.import_module("core.graph.conductance")

    w = np.array(
        [
            [0.0, 0.9, 0.8, 0.1, 0.0, 0.0],
            [0.9, 0.0, 0.7, 0.0, 0.0, 0.0],
            [0.8, 0.7, 0.0, 0.0, 0.0, 0.0],
            [0.1, 0.0, 0.0, 0.0, 0.6, 0.5],
            [0.0, 0.0, 0.0, 0.6, 0.0, 0.4],
            [0.0, 0.0, 0.0, 0.5, 0.4, 0.0],
        ],
        dtype=np.float64,
    )
    labels = gc._components(w)
    routed_r = gc._r_eff_matrix(w, labels)                     # uses _dense_laplacian internally

    lp = np.linalg.pinv(np.diag(w.sum(axis=1)) - w)            # the oracle-L pipeline, inlined
    diag = np.diag(lp)
    oracle_r = diag[:, None] + diag[None, :] - 2.0 * lp
    same = labels[:, None] == labels[None, :]
    oracle_r = np.where(same, oracle_r, np.inf)
    np.fill_diagonal(oracle_r, 0.0)

    finite = np.isfinite(oracle_r)
    assert np.array_equal(np.isfinite(routed_r), finite)       # the same connectivity structure
    assert np.allclose(routed_r[finite], oracle_r[finite], rtol=1e-10, atol=1e-12), (
        "R_eff values drifted under the Laplacian route — P4 violated; STOP per bp-065 §10"
    )
