"""`core/temporal/` — the citation complex `X_cite` and its topological falsifier, living OUTSIDE
`core/complex/` so the isolation invariant (`core/complex/**` never imports `reference_edges`) is
never weakened (dn-temporal-retrieval-algebra §2.4 A4; bp-032). Read-only sensing: no store write
handle, no model, no network, and no path into the balance math (`build_complex`/`A_signed`).
"""

from __future__ import annotations

# The store-reading seams `supersession_poset` / `build_citation_complex` are NOT re-exported here:
# they relocated to `core/temporal/acquire.py` (bp-089, S1′ inner-ring promotion). Re-importing them
# here would pull the store types into this package `__init__`, making `core.temporal` OUTER again —
# the opposite of the promotion. Import them from `core.temporal.acquire` directly.
from core.kernel.temporal.boundary import (
    SupersessionCycleError,
    SupersessionPoset,
    coboundary_0,
    coboundary_1,
    delta_D_squared,
    delta_D_squared_is_zero,
    poset_from_chains,
    poset_from_pairs,
)
from core.kernel.temporal.complex import (
    CitationComplex,
    citation_distance_matrix,
    dim_ker_L1,
    flag_boundary_composition_is_zero,
)
from core.kernel.temporal.operators import (
    DiamondError,
    active_projection,
    is_chain_map,
    pullback_0,
    pushforward_0,
    pushforward_1,
    sigma_node_map,
    t_active,
)
from core.kernel.temporal.superconnection import (
    curvature,
    curvature_norm,
    is_flat,
    severed_citations,
)

__all__ = [
    "CitationComplex",
    "DiamondError",
    "SupersessionCycleError",
    "SupersessionPoset",
    "active_projection",
    "citation_distance_matrix",
    "coboundary_0",
    "coboundary_1",
    "curvature",
    "curvature_norm",
    "delta_D_squared",
    "delta_D_squared_is_zero",
    "dim_ker_L1",
    "flag_boundary_composition_is_zero",
    "is_chain_map",
    "is_flat",
    "poset_from_chains",
    "poset_from_pairs",
    "pullback_0",
    "pushforward_0",
    "pushforward_1",
    "severed_citations",
    "sigma_node_map",
    "t_active",
]
