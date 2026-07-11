"""R0 — the interpreter panel (design-notes/dreaming-v2-interpreter-panel.md; §6/§8; BUILD §3.2).

Generalizes the Phase-7 single clusterer into a REGISTRY of deterministic interpreters — the
"workers", specialists by METHOD (not source). Each is a different lens on the *same* authored
mirror graph and emits candidate pattern-claims plus the authored graph evidence that supports
them:

    φ_i : G_MR → 2^K,   κ = (statement, support ⊆ authored notes)

All are model-free — the §9 deterministic floor; the model is earned only for narration/judging,
which R0 does NOT do. No adjudication here (that is R1): R0 just produces the raw claims. Inputs
are a `MirrorView`, so every claim's support is authored (Invariant 6, structural) — observed
exhaust can never seed a claim.

Two generations of lens share the panel (BUILD §3.2 — "each interpreter is a thin adapter over a
`core/complex/` function"):

  * the original NumPy lenses over the σ-graph: community (connected components), centrality
    (degree hubs), density (cores + explicit noise);
  * the STRUCTURAL lenses over the reasoning complex (H4–H7): `bridge` (Forman–Ricci curvature —
    upgraded from the local-clustering proxy to the real instrument, companion III §3.2), `hole`
    (persistent H₁ — conceptual gaps, NEVER contradictions, §4.2), `theme` (DC-SBM posterior with
    a model-selected count + a spectral cross-check, §6.2).

Change-point is a registered but DEFERRED seam — it needs a per-note temporal axis the MirrorView
does not yet carry, so it returns nothing rather than fake a trend (the honest-seam pattern).
Contradiction (`tension`) stays routed through the signed Laplacian (`core/complex/balance.py`) +
typed `contradicts` edges; it joins the panel when a contradiction detector exists to assert them.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from config.loader import Config, DreamRnDConfig
from core.complex.blocks import sbm
from core.complex.build import ReasoningComplex, build_complex
from core.complex.curvature import most_negative_edges
from core.complex.spectral import spectral_labels
from core.complex.topology import cosine_distance_matrix, long_lived_holes
from core.dreaming.cluster import cluster_notes, note_centroids
from core.dreaming.graph import MirrorGraph
from core.dreaming.rnd import require_rnd_enabled
from core.mirror import MirrorView
from core.stores.edges import EdgeStore

# Method names (the discriminator carried on every claim).
COMMUNITY = "community"
CENTRALITY = "centrality"
BRIDGE = "bridge"
DENSITY = "density"
THEME = "theme"                 # H7: SBM blocks with posterior + model-selected count
HOLE = "hole"                   # H5: long-lived H₁ — a conceptual gap, never a contradiction
TENSION = "tension"             # H3/H8: frustrated triangles — commitments that can't co-hold
CHANGE_POINT = "change_point"   # deferred seam


@dataclass(frozen=True)
class Claim:
    """A candidate pattern-claim from one interpreter. `support` is the set of authored note
    digests the claim rests on — content-addressed evidence (G1), and the LEAVES that ground it
    (G2). `data` is method-specific. No confidence here; ranking is the adjudicator's job (R1)."""

    method: str
    statement: str
    support: tuple[str, ...]
    data: dict[str, Any] = field(default_factory=dict[str, Any])


# An interpreter is a deterministic map from the mirror graph (+ tunables) to claims.
Interpreter = Callable[[MirrorGraph, DreamRnDConfig], "list[Claim]"]


def community_interpreter(graph: MirrorGraph, cfg: DreamRnDConfig) -> list[Claim]:
    """Connected components over the σ-graph — thematic groups (the Phase-7 lens, as one of
    many). Each component of >=2 notes is a theme; support = the component's notes."""
    clusters = cluster_notes(list(graph.notes), threshold=cfg.sigma, min_size=2)
    return [
        Claim(method=COMMUNITY,
              statement=f"{c.size} notes group into a theme",
              support=c.digests,
              data={"size": c.size})
        for c in clusters
    ]


def centrality_interpreter(graph: MirrorGraph, cfg: DreamRnDConfig) -> list[Claim]:
    """Degree centrality — which notes are load-bearing hubs. The top-k highest-degree notes
    (degree >= min_degree); support = the hub plus the notes it links."""
    ranked = sorted(range(graph.n), key=lambda i: (-graph.degree(i), graph.title(i)))
    claims: list[Claim] = []
    for i in ranked[: cfg.centrality_top_k]:
        deg = graph.degree(i)
        if deg < cfg.min_degree:
            break                      # ranked desc — once below the floor, all the rest are too
        support = graph.digests_for([i, *graph.neighbors(i)])
        claims.append(Claim(
            method=CENTRALITY,
            statement=f"'{graph.title(i)}' is a hub linking {deg} related notes",
            support=support,
            data={"degree": deg, "focus": graph.digest(i)},
        ))
    return claims


# ---------------------------------------------------------------------------------
# Structural lenses (H4–H7): thin Claim-emitters over core/complex/ (BUILD §3.2).
# Each consumes the SAME complex, built once per pass from the MirrorView (so a non-authored
# claim is unrepresentable — the firewall is the constructor's input type).
# ---------------------------------------------------------------------------------

@dataclass(frozen=True)
class StructuralContext:
    """One pass's shared structural state: the reasoning complex 𝔎|_MR at the working σ, plus
    the full cosine-distance matrix (the persistence filtration sweeps thresholds, so it must
    not be pre-thresholded). Built by `run_panel`; consumed by the structural interpreters."""

    complex: ReasoningComplex
    distances: np.ndarray          # cosine distance over note centroids (n×n)


StructuralInterpreter = Callable[[StructuralContext, DreamRnDConfig], "list[Claim]"]


def bridge_interpreter(ctx: StructuralContext, cfg: DreamRnDConfig) -> list[Claim]:
    """H4 — the curvature bridge lens: Forman–Ricci over the σ-backbone, most negative first
    (companion III §3.2 — the principled replacement for the local-clustering proxy). A very
    negative edge is a surprising cross-domain link: exactly what a synthesis pass should look
    at first. Support = the two linked notes."""
    kx = ctx.complex
    claims: list[Claim] = []
    for i, j, curv in most_negative_edges(kx.A, top_k=cfg.bridge_top_k):
        u, v = kx.nodes[i], kx.nodes[j]
        claims.append(Claim(
            method=BRIDGE,
            statement=(f"'{kx.titles.get(u, u)}' and '{kx.titles.get(v, v)}' form a "
                       f"cross-domain link (curvature {curv:.1f})"),
            support=(u, v),
            data={"curvature": curv, "edge": [u, v]},
        ))
    return claims


def hole_interpreter(ctx: StructuralContext, cfg: DreamRnDConfig) -> list[Claim]:
    """H5 — the persistence lens: long-lived H₁ features of the flag complex are conceptual
    holes — notes pairwise related in a ring with no center. A hole is a GAP to surface (a
    utility-axis prompt), never a contradiction (§4.2: dissonance is balance.py's job)."""
    kx = ctx.complex
    claims: list[Claim] = []
    for hole in long_lived_holes(ctx.distances, min_persistence=cfg.hole_min_persistence):
        digests = tuple(kx.nodes[v] for v in hole.vertices)
        claims.append(Claim(
            method=HOLE,
            statement=(f"{len(digests)} notes circle a theme without stating its center — a "
                       f"conceptual hole (open from similarity "
                       f"{1 - hole.birth:.2f} down to {1 - hole.death:.2f})"),
            support=digests,
            data={"birth": round(hole.birth, 4), "death": round(hole.death, 4),
                  "lifetime": round(hole.lifetime, 4)},
        ))
    return claims


def theme_interpreter(ctx: StructuralContext, cfg: DreamRnDConfig) -> list[Claim]:
    """H7 — the SBM lens: degree-corrected blocks give theme membership WITH a posterior and a
    model-selected theme count (§6.2 — "how many concerns, how sure"), cross-checked against the
    spectral partition (agreement = robust, disagreement = fragile — a signal in itself). The
    posterior organizes the graph; it never certifies a thought (§6.3)."""
    kx = ctx.complex
    if kx.n == 0:
        return []
    result = sbm(kx.A, k_max=cfg.sbm_k_max)
    k_spectral = len(np.unique(spectral_labels(kx.A)))
    claims: list[Claim] = []
    for block in range(result.k):
        members = np.where(result.labels == block)[0]
        if len(members) < 2:
            continue                       # a singleton is not a theme
        mean_post = float(result.posterior[members, block].mean())
        claims.append(Claim(
            method=THEME,
            statement=(f"{len(members)} notes form one of {result.k} distinct concerns "
                       f"(membership confidence {mean_post:.2f})"),
            support=tuple(kx.nodes[i] for i in members),
            data={"k_sbm": result.k, "k_spectral": k_spectral,
                  "counts_agree": result.k == k_spectral,
                  "mean_posterior": round(mean_post, 4)},
        ))
    return claims


def density_interpreter(graph: MirrorGraph, cfg: DreamRnDConfig) -> list[Claim]:
    """Density split (the HDBSCAN-style contribution): notes with >= min_degree neighbours are
    'core'; notes with no σ-neighbour are explicit NOISE/outliers. Emits a core-region claim
    and, distinctively, an outliers claim — the signal the connected-components lens hides."""
    cores = [i for i in range(graph.n) if graph.degree(i) >= cfg.min_degree]
    noise = [i for i in range(graph.n) if graph.degree(i) == 0]
    claims: list[Claim] = []
    if len(cores) >= 2:
        claims.append(Claim(
            method=DENSITY,
            statement=f"a dense region of {len(cores)} closely-related notes",
            support=graph.digests_for(cores),
            data={"core_count": len(cores)},
        ))
    if noise:
        claims.append(Claim(
            method=DENSITY,
            statement=f"{len(noise)} note(s) stand apart from any theme (outliers)",
            support=graph.digests_for(noise),
            data={"outlier_count": len(noise)},
        ))
    return claims


def change_point_interpreter(graph: MirrorGraph, cfg: DreamRnDConfig) -> list[Claim]:
    """DEFERRED seam: temporal change-point detection needs a per-note timestamp, which the
    MirrorView does not yet carry. Returns nothing rather than fabricate a trend — the same
    honest-seam discipline as the §4 judge and the contradiction detector. Wire it when an
    authored temporal axis lands on the mirror rows."""
    return []


# The registries — the panel. Order is the run order; the adjudicator re-ranks by confidence.
# σ-graph lenses (the original NumPy floor):
INTERPRETERS: dict[str, Interpreter] = {
    COMMUNITY: community_interpreter,
    CENTRALITY: centrality_interpreter,
    DENSITY: density_interpreter,
    CHANGE_POINT: change_point_interpreter,
}
# Structural lenses over core/complex/ (H4–H7):
STRUCTURAL_INTERPRETERS: dict[str, StructuralInterpreter] = {
    BRIDGE: bridge_interpreter,
    HOLE: hole_interpreter,
    THEME: theme_interpreter,
}


def build_structural_context(view: MirrorView, cfg: DreamRnDConfig, *,
                             edges: EdgeStore | None = None) -> StructuralContext:
    """One pass's shared structural state: the σ-backbone complex (optionally with persisted
    typed/signed edges overlaid — the tension lens's input) + the unthresholded distance matrix
    (the persistence filtration). Authored-only by the constructor's input type."""
    notes = note_centroids(view.rows())
    return StructuralContext(
        complex=build_complex(view, edges=edges, sim_floor=cfg.sigma),
        distances=cosine_distance_matrix(
            np.asarray([n.vector for n in notes], dtype=np.float64)),
    )


def tension_claims(kx: ReasoningComplex) -> list[Claim]:
    """The tension lens (§2.3): every frustrated triangle — an odd number of − edges — is three
    commitments that cannot all co-hold ("you keep circling this"). Consumes the signed adjacency
    (contradiction = a persisted `contradicts` edge overlaid by `build_complex`); with no asserted
    contradictions the graph is all-support and this honestly emits nothing. Dissonance lives
    HERE, never in H₁ (§4.2)."""
    from core.complex.balance import frustrated_triangles
    claims: list[Claim] = []
    for i, j, k in frustrated_triangles(kx.A_signed):
        digests = (kx.nodes[i], kx.nodes[j], kx.nodes[k])
        titles = [kx.titles.get(d, d) for d in digests]
        claims.append(Claim(
            method=TENSION,
            statement=(f"'{titles[0]}', '{titles[1]}' and '{titles[2]}' are in tension — "
                       f"they cannot all hold together (a frustrated triangle)"),
            support=digests,
            data={"triangle": list(digests)},
        ))
    return claims


def collect_claims(graph: MirrorGraph, ctx: StructuralContext,
                   cfg: DreamRnDConfig) -> list[Claim]:
    """Run both registries (σ-graph lenses + structural lenses) plus the tension lens over
    already-built state. The un-gated core of `run_panel`, shared with the loop-v2 dream pass
    (which builds its own context so it can overlay persisted edges)."""
    claims: list[Claim] = []
    for interpret in INTERPRETERS.values():
        claims.extend(interpret(graph, cfg))
    for interpret_structural in STRUCTURAL_INTERPRETERS.values():
        claims.extend(interpret_structural(ctx, cfg))
    claims.extend(tension_claims(ctx.complex))
    return claims


def run_panel(view: MirrorView, *, config: Config | None = None) -> list[Claim]:
    """Run every registered interpreter (σ-graph lenses + structural lenses over one shared
    reasoning complex) and return all candidate claims (R0 — no adjudication). Refuses unless
    the R&D flag is on (hard boundary)."""
    cfg = require_rnd_enabled(config)
    graph = MirrorGraph.build(view, sigma=cfg.sigma)
    ctx = build_structural_context(view, cfg)
    return collect_claims(graph, ctx, cfg)
