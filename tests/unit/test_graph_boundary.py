"""The dn-core-graph-instruments boundary teeth (bp-065): P1 import purity + P5 re-export
identity + P3 one-Laplacian equivalence.

(a) **P1 — the permanent tooth**: no file under `core/graph/` imports `eval`, ever. Scoped to
    the package's OWN files (a static AST scan), NOT the transitive closure — core substrate
    legitimately writes readings out through the tolerated sink (`core/temporal/spine.py:97`,
    P6), so a closure test would fail by design.
(b) **P5 — the compatibility contract**: every name the eval harness re-exports IS the core
    object (`is`-identity) — a drifted copy would silently fork the math.
(c) **P3 — one Laplacian** (added with item 2): `core/graph`'s dense Laplacian adapter routes
    through `core/complex/laplacian.laplacian` and equals the direct dense construction
    `D − W` EXACTLY on fixture-scale graphs (n < 128: NumPy's pairwise summation reduces to
    sequential there, and interleaved zeros perturb nothing, so float64 equality is exact —
    the no-silent-metric-change clause).
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


# ── (b) P5: the eval harness re-exports ARE the core objects ────────────────────────────────────


def test_connectivity_reexports_are_the_core_objects() -> None:
    """`eval.harness.connectivity`'s relocated names are `is`-identical to `core.graph.sigma_star`'s
    — the re-export surface every downstream pin (bp-061/062) and the bp-059 suites resolve
    through. A drifted copy would silently fork the math. (importlib: the package re-exports the
    *function* `sigma_star`, which shadows the same-named submodule as a package attribute — the
    modules must be addressed via sys.modules, not attribute access.)"""
    import importlib

    gs = importlib.import_module("core.graph.sigma_star")
    conn = importlib.import_module("eval.harness.connectivity")

    for name in (
        "ConnIndex",
        "CrossingEdgeError",
        "MaxSpanningForest",
        "SigmaStar",
        "acquire_mirror_cut",
        "build_max_spanning_tree",
        "cut_fingerprint",
        "pairwise_sigma_star",
        "sigma_star",
    ):
        assert getattr(conn, name) is getattr(gs, name), f"{name} drifted from core.graph"


def test_conductance_reexports_are_the_core_objects() -> None:
    """Same P5 contract for the conductance wrapper: the relocated names ARE the core objects."""
    import importlib

    gc = importlib.import_module("core.graph.conductance")
    cond = importlib.import_module("eval.harness.conductance")

    for name in (
        "CONDUCTANCE_THRESH",
        "ConductanceProfile",
        "ReconnectionEvent",
        "chi_s",
        "chi_s_all",
        "churn_weight",
        "effective_conductance",
        "reconnection_scan",
        "sigma_t_profile",
    ):
        assert getattr(cond, name) is getattr(gc, name), f"{name} drifted from core.graph"


# ── (c) P3: one Laplacian — the core/complex route equals the direct construction EXACTLY ───────


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
