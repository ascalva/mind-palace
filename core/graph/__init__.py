# ── Family: σ-connectivity instruments (graph measurement at a certified cut) · docs/NOTATION.md ──
# OBJECT:    the package — σ*/MST (`sigma_star`), the (σ,t) conductance family (`conductance`);
#            bridges + helix land here on their re-mints (dn-core-graph-instruments P2).
# INVARIANT: graph mathematics is CORE vocabulary (P1): this package imports core substrate +
#            stdlib/NumPy/SciPy ONLY — never eval; the eval harness imports US and keeps the
#            instrument layer (readings, evidence, gates). ONE Laplacian: core/complex's (P3).
# ENFORCED:  the P1 no-eval + Law-C4 no-clock AST teeth over every package file, and the P5
#            re-export `is`-identity pins — `tests/unit/test_graph_boundary.py`, permanent.
"""core/graph — the σ-connectivity instruments (dn-core-graph-instruments P2).

The σ/temporal connectivity mathematics over `MirrorGraph` + `Spine`: σ*/MST (`sigma_star`),
the (σ,t) conductance-profile family (`conductance` — lands with bp-065 item 2; bridges and
helix follow on their re-mints). Distinct from `core/complex/` (the ReasoningComplex math) but
built on its primitives — ONE Laplacian (P3). This package imports core substrate and stdlib/
NumPy/SciPy ONLY — never `eval` (the P1 boundary tooth, `tests/unit/test_graph_boundary.py`);
the eval harness imports *us* and keeps the instrument layer (readings, evidence, gates).
"""

from core.graph.conductance import (
    CONDUCTANCE_THRESH,
    ConductanceProfile,
    ReconnectionEvent,
    chi_s,
    chi_s_all,
    churn_weight,
    effective_conductance,
    reconnection_scan,
    sigma_t_profile,
)
from core.graph.sigma_star import (
    ConnIndex,
    CrossingEdgeError,
    MaxSpanningForest,
    SigmaStar,
    acquire_mirror_cut,
    build_max_spanning_tree,
    cut_fingerprint,
    pairwise_sigma_star,
    sigma_star,
)

__all__ = [
    "CONDUCTANCE_THRESH",
    "ConductanceProfile",
    "ConnIndex",
    "CrossingEdgeError",
    "MaxSpanningForest",
    "ReconnectionEvent",
    "SigmaStar",
    "acquire_mirror_cut",
    "build_max_spanning_tree",
    "chi_s",
    "chi_s_all",
    "churn_weight",
    "cut_fingerprint",
    "effective_conductance",
    "pairwise_sigma_star",
    "reconnection_scan",
    "sigma_star",
    "sigma_t_profile",
]
