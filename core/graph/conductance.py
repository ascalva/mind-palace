# ── Family: σ-connectivity instruments (graph measurement at a certified cut) · docs/NOTATION.md ──
# OBJECT:    the (σ,t) conductance-profile family over the CN-4 churn-weighted Laplacian —
#            pairwise R_eff (L⁺ two-point resistance), finite-t heat-kernel distances, the
#            von-Luxburg degeneracy self-diagnostic, χ_s/depth-budget, and leave-one-out
#            reconnection attribution over the weight-increased edge set (finding-0099).
# INVARIANT: never one scalar — always the (σ,t) profile with the diagnostic PRESENT; the churn
#            signs are LAW (series impedes −s_seq, parallel conducts +s_lat; only magnitudes tune,
#            shipped 0 — no ops/levers entry); ONE Laplacian — core/complex's (P3) — and no silent
#            metric change (P4: the combinatorial heat kernel is NOT the L_sym `diffusion_map`
#            sibling; Φ(S) in `core/complex/cut` is NOT pairwise R_eff); a bridging edge is named
#            only leave-one-out-CONFIRMED; imports core substrate only — NEVER eval (P1).
# ENFORCED:  the sign-law + THRESH-dict + no-ops/no-clock AST falsifiers scan THIS file
#            (`tests/unit/test_conductance.py`); the L-equivalence and P1 no-eval teeth live in
#            `tests/unit/test_graph_boundary.py`; `_dense_laplacian` routes through
#            `core.complex.laplacian` and nothing else.
r"""CN-3 + CN-4 mathematics: the (σ,t) conductance profile, the churn measure, reconnection.

The σ-connectivity family's conductance math, harvested from bp-060's build and re-homed by
bp-065 under `dn-core-graph-instruments` (P1/P2: graph mathematics is CORE vocabulary; the
eval harness keeps the *instrument* — readings, evidence — and imports this). Deterministic,
model-free NumPy/SciPy linear algebra; no model import, no LLM call, no clock (Law C4); this
module imports core substrate ONLY — never `eval` (the P1 boundary tooth). Design:
`docs/design-notes/connectivity-instruments.md` CN-3 §2.3 + CN-4 §2.4 (RATIFIED — math held
verbatim, never re-derived here).

**One Laplacian (P3).** The combinatorial Laplacian comes from `core/complex/laplacian.py`
(`laplacian`, L = D − A) — THE core primitive; the dense CN-4 weights wrap to csr at the
`_dense_laplacian` boundary and L densifies for `eigh`/`pinv` (corpus scale is small —
finding-0096). bp-060's dense re-derivation is deleted; the boundary test pins exact equality.
**No silent metric change (P4):** `core/complex/spectral.diffusion_map` is the L_sym
(normalized) geometry — a SIBLING metric, not this one. The finite-t distances here are the
heat kernel `exp(−tL)` of the COMBINATORIAL L (the von-Luxburg diagnostic is calibrated
against R_eff over the SAME L); substituting one for the other would change every profile
value. Likewise `core/complex/cut.conductance(A, S)` is set (Cheeger) conductance Φ(S);
`R_eff(a,b)` here is the two-point resistance (commute time = vol·R_eff) — related through the
same electrical network, not the same function.

**Conductance is reported ONLY as the (σ,t) profile (CN-3).** Raw effective resistance R_eff
provably degenerates to `1/d_A + 1/d_B` in dense regimes (the von Luxburg result), so a single
dense-graph resistance is never "the conductance". Every emitted `ConductanceProfile` carries
the **degeneracy self-diagnostic** `corr(R_eff, 1/d_A + 1/d_B)` at the loosest σ — the math
reports its own domain of validity; when the diagnostic is high, the finite-t diffusion
distances are the authoritative reading. Rayleigh monotonicity binds: as σ loosens (edges are
added) effective conductance is non-decreasing; removals never raise conductance.

**The churn change-of-measure — signs are LAW, not knobs (CN-4 §2.4; D1 RETIRED 2026-07-17).**
The edge weight is `w(u,v) = cos(u,v)^α · exp(s_lat·a_lat − s_seq·a_seq)`. The two churn signs
are derived by **circuit law**, not chosen: sequential churn (supersession depth) acts in
**series** ⇒ impedes (the `−s_seq·a_seq` term); lateral churn (new cross-links) acts in
**parallel** ⇒ conducts (the `+s_lat·a_lat` term) — Rayleigh monotonicity. The code NEVER
pairs lateral churn with a minus or sequential churn with a plus. Only the *magnitudes*
`(s_seq, s_lat)` are sweepable, and they ship at **0** in `CONDUCTANCE_THRESH` (α default 1).
No entry lives in `ops/levers.py`: promoting the magnitudes to registered levers is a separate
owner-visible act, never done here.

**The depth budget + χ_s (CN-4).** Events partition by stratum, so the global budget is
additive `N(W) = Σ_s N_s(W)`; any ≼-chain confined to a stratum within a window has ≤ `N_s(W)`
events — proper time is the sequential-depth budget. Sequentiality `χ_s(W) = longest-chain /
N_s(W) ∈ (0,1]`, = 1 iff the window-events are totally ordered. finding-0090 (proper-time-
exactness erratum, OPEN) does NOT gate this: CN-4 consumes N_s event *counts* (built objects),
not the proper-time metric's exactness (note §Cross-references) — a documented non-dependency.

**The reconnection rider (CN-3 + finding-0099).** A reconnection event is a Δ-conductance
spike between two cuts across a large proper-time gap, **verified** by leave-one-out
re-computation naming the bridging edge(s). Under the CN-4 *weighted* measure the exact
Rayleigh law is monotonicity in each edge WEIGHT: a rise requires ≥1 edge-weight increase, of
which a new edge is the 0→w special case. So the attribution set is the **weight-increased
edges** (added OR edited — an edit that raises `cos` qualifies), not new-edges-only
(finding-0099, numerically checked). A named bridging edge is reported only when leave-one-out
confirms it — never a guess.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp

from core.complex.laplacian import laplacian as _combinatorial_laplacian
from core.dreaming.graph import MirrorGraph
from core.temporal.spine import Spine

_MIRROR_STRATUM = "mirror"              # the σ-graph is cut over the mirror stratum

# α default 1; the churn magnitudes ship at 0. The SIGNS are LAW (series impedes → −s_seq; parallel
# conducts → +s_lat) and live in the code, never in this dict — the dict holds MAGNITUDES only. No
# `ops/levers.py` entry: promoting these to registered levers is a separate owner-visible act.
CONDUCTANCE_THRESH: dict[str, float] = {
    "alpha": 1.0,     # cos(u,v)^α edge exponent
    "s_seq": 0.0,     # sequential-churn magnitude (series, impedes — the MINUS sign is structural)
    "s_lat": 0.0,     # lateral-churn magnitude (parallel, conducts — the PLUS sign is structural)
}

# Tolerances — kept OUT of CONDUCTANCE_THRESH so the pinned dict stays exactly the three CN-4 keys
# (the `NOISE_SETTLED_MAX` contrast in `gate.py`). `_DEGENERACY_HIGH`: above this correlation the
# R_eff reading is degenerate ⇒ the finite-t diffusion distance is authoritative. `_RISE_EPS`: a
# Δ-conductance below this is float noise, not a reconnection.
_DEGENERACY_HIGH: float = 0.9
_RISE_EPS: float = 1e-9
_ZERO_EPS: float = 1e-12


# ── the CN-4 change-of-measure weight (signs are LAW) ────────────────────────────────────────────


def churn_weight(
    sim_uv: float, a_lat: float, a_seq: float, thresh: Mapping[str, float]
) -> float:
    r"""The CN-4 edge weight `w = cos^α · exp(s_lat·a_lat − s_seq·a_seq)` (note §2.4).

    The signs are **structural circuit law, not tuning** (D1 retired): lateral churn `a_lat` acts in
    parallel and CONDUCTS, so it enters with a **plus** (`+s_lat·a_lat`); sequential churn `a_seq`
    acts in series and IMPEDES, so it enters with a **minus** (`−s_seq·a_seq`). This pairing is
    fixed here and never inverted in the module (the sign-law AST falsifier scans for a violation).
    Only the magnitudes `(s_seq, s_lat)` and the exponent α are read from `thresh` — all shipped so
    that at the default magnitudes (0) the exp term is 1 and the weight reduces to `cos^α` (α=1 ⇒
    the raw cosine): zero-magnitude ships inert."""
    alpha = thresh["alpha"]
    s_lat = thresh["s_lat"]
    s_seq = thresh["s_seq"]
    base = sim_uv**alpha
    # +s_lat·a_lat: lateral churn conducts (parallel).  −s_seq·a_seq: sequential churn impedes
    # (series).  The signs are law; do not invert either term.
    return float(base * math.exp(s_lat * a_lat - s_seq * a_seq))


# ── the (σ,t) profile + the von-Luxburg degeneracy self-diagnostic (CN-3) ────────────────────────


@dataclass(frozen=True)
class ConductanceProfile:
    """One pair's conductance reading — the (σ,t) profile, NEVER one scalar (CN-3). `commute` is the
    (σ × t) grid of finite-t diffusion distances; `r_eff_loosest` the effective resistance at the
    loosest σ (∞ ⇒ "not connected within grid"); `degeneracy_diag` the von-Luxburg self-diagnostic
    `corr(R_eff, 1/d_A + 1/d_B)` at the loosest σ, **always present** (absent ⇒ malformed); `chi_s`
    the per-stratum sequentiality χ_s(W) (attached by the harness entry point; `{}` from the
    graph-only `sigma_t_profile`, which has no spine)."""

    a: str
    b: str
    sigma_grid: tuple[float, ...]
    t_grid: tuple[float, ...]
    commute: tuple[tuple[float, ...], ...]   # (σ × t) finite-t diffusion distances
    r_eff_loosest: float                     # R_eff at the loosest σ (∞ ⇒ not connected in grid)
    degeneracy_diag: float                   # corr(R_eff, 1/d_A+1/d_B) at loosest σ (always)
    chi_s: dict[str, float] = field(default_factory=dict)

    @property
    def connected_at_loosest(self) -> bool:
        """Whether the pair shares a component at the loosest σ (finite R_eff)."""
        return math.isfinite(self.r_eff_loosest)

    def finite_t_authoritative(self) -> bool:
        """CN-3's domain-of-validity flag: when the degeneracy diagnostic is high, R_eff has
        collapsed to local degrees (von Luxburg) and the **finite-t diffusion distance** is the
        authoritative reading, not R_eff. The threshold is a tolerance (module constant), not a
        tunable magnitude — it stays OUT of `CONDUCTANCE_THRESH`."""
        return self.degeneracy_diag >= _DEGENERACY_HIGH


@dataclass(frozen=True)
class ReconnectionEvent:
    """A verified Δ-conductance spike between two cuts (CN-3). `bridging_edges` are named ONLY when
    leave-one-out re-computation confirms them (reverting the edge's weight increase erases the
    rise) — never a guess. Over the CN-4 weighted measure the attribution set is the
    weight-INCREASED edges (finding-0099): a new edge is the 0→w special case, an edit that raises
    `cos` also qualifies."""

    a: str
    b: str
    delta_conductance: float
    proper_time_gap: int
    bridging_edges: tuple[tuple[str, str], ...]   # leave-one-out VERIFIED, never guessed


def _weighted_matrix(graph: MirrorGraph, sigma: float, thresh: Mapping[str, float]) -> np.ndarray:
    """The CN-4 weighted adjacency `W` at threshold σ: `W[i,j] = churn_weight(cos(i,j), …)` for
    pairs the graph admits at σ (`cos ≥ σ`), 0 otherwise; symmetric, zero diagonal. v1 passes the
    churn statistics as 0 (the ship-inert default; a future act wires the per-edge `a_•` from the
    spine — bp-060 §11 parked convention), so at shipped magnitudes `W = cos^α`."""
    n = graph.n
    w = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            c = float(graph.sim[i, j])
            if c >= sigma:
                weight = churn_weight(c, 0.0, 0.0, thresh)
                w[i, j] = w[j, i] = weight
    return w


def _dense_laplacian(w: np.ndarray) -> np.ndarray:
    """`L = D − W` via THE core primitive (`core/complex/laplacian.laplacian` — P3, one Laplacian):
    the dense CN-4 weights wrap to csr at this boundary and L densifies for `eigh`/`pinv` (corpus
    scale is small — finding-0096). Numerically identical to the direct dense construction — the
    boundary test (`tests/unit/test_graph_boundary.py`) pins exact equality on fixtures (P4:
    no silent metric change)."""
    return np.asarray(_combinatorial_laplacian(sp.csr_matrix(w)).toarray(), dtype=np.float64)


def _components(w: np.ndarray) -> np.ndarray:
    """Connected-component labels over the edges present in `W` (union-find). R_eff is ∞ across
    components (a disconnected pair is "not connected within grid", never a huge finite number from
    the pseudo-inverse)."""
    n = w.shape[0]
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if w[i, j] > _ZERO_EPS:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[max(ri, rj)] = min(ri, rj)
    return np.array([find(i) for i in range(n)], dtype=np.int64)


def _r_eff_matrix(w: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """The pairwise effective-resistance matrix via the Laplacian pseudo-inverse `L⁺`:
    `R(i,j) = L⁺[i,i] + L⁺[j,j] − 2·L⁺[i,j]` within a component, `∞` across components (von Luxburg
    / commute-time identity, valid PER connected component; bp-060 §3 risk-a)."""
    lp = np.linalg.pinv(_dense_laplacian(w))
    diag = np.diag(lp)
    r = diag[:, None] + diag[None, :] - 2.0 * lp
    same = labels[:, None] == labels[None, :]
    out = np.where(same, r, np.inf)
    np.fill_diagonal(out, 0.0)
    return np.asarray(out, dtype=np.float64)


def _diffusion_distances(w: np.ndarray, t_grid: Sequence[float]) -> dict[float, np.ndarray]:
    """Finite-t diffusion-distance matrices over the heat kernel `exp(−tL)` (CN-3 authoritative
    reading in the degenerate regime; L COMBINATORIAL — P4, never the L_sym sibling). Via the
    eigendecomposition `L = Σ λ_k φ_k φ_kᵀ`:
    `d_t(i,j)² = Σ_k e^{−2 t λ_k} (φ_k[i] − φ_k[j])²` — always finite, declared over the pinned
    t-grid."""
    vals, vecs = np.linalg.eigh(_dense_laplacian(w))
    out: dict[float, np.ndarray] = {}
    for t in t_grid:
        weights = np.exp(-2.0 * float(t) * vals)              # per-eigenvalue heat weight
        scaled = vecs * np.sqrt(np.maximum(weights, 0.0))[None, :]
        gram = scaled @ scaled.T                              # Σ_k e^{−2tλ}φ_k[i]φ_k[j]
        d2 = np.diag(gram)[:, None] + np.diag(gram)[None, :] - 2.0 * gram
        out[float(t)] = np.sqrt(np.maximum(d2, 0.0))
    return out


def _degeneracy_diag(w_loosest: np.ndarray, r_loosest: np.ndarray, labels: np.ndarray) -> float:
    """The von-Luxburg self-diagnostic `corr(R_eff(A,B), 1/d_A + 1/d_B)` over all CONNECTED pairs at
    the loosest σ (the densest graph). High ⇒ R_eff has collapsed to local degrees ⇒ the finite-t
    diffusion distance is authoritative. `0.0` when it cannot be estimated (< 2 connected pairs, or
    either series has zero variance — an honest "undiagnosable", never a fabricated correlation)."""
    degree = w_loosest.sum(axis=1)
    n = w_loosest.shape[0]
    xs: list[float] = []
    ys: list[float] = []
    for i in range(n):
        for j in range(i + 1, n):
            if labels[i] != labels[j]:
                continue
            di, dj = float(degree[i]), float(degree[j])
            if di <= _ZERO_EPS or dj <= _ZERO_EPS:
                continue
            xs.append(float(r_loosest[i, j]))
            ys.append(1.0 / di + 1.0 / dj)
    if len(xs) < 2:
        return 0.0
    xa, ya = np.array(xs), np.array(ys)
    if xa.std() <= _ZERO_EPS or ya.std() <= _ZERO_EPS:
        return 0.0
    return float(np.corrcoef(xa, ya)[0, 1])


def effective_conductance(
    graph: MirrorGraph, a: str, b: str, *, sigma: float, thresh: Mapping[str, float]
) -> float:
    """Effective conductance `1/R_eff` between two notes at threshold σ (0 across disconnected
    components). The Rayleigh-monotone quantity: as σ loosens (edges are added) this is
    non-decreasing (the falsifier is a rise as σ *tightens*)."""
    digests = [graph.digest(i) for i in range(graph.n)]
    ia, ib = digests.index(a), digests.index(b)
    w = _weighted_matrix(graph, sigma, thresh)
    labels = _components(w)
    if labels[ia] != labels[ib]:
        return 0.0
    r = _r_eff_matrix(w, labels)[ia, ib]
    return 1.0 / r if r > _ZERO_EPS else 0.0


def sigma_t_profile(
    graph: MirrorGraph,
    *,
    sigma_grid: Sequence[float],
    t_grid: Sequence[float],
    thresh: Mapping[str, float] = CONDUCTANCE_THRESH,
) -> list[ConductanceProfile]:
    """Every pair's (σ,t) conductance profile over the CN-4 weighted Laplacian. For each σ (loosest
    first) the weighted adjacency, its components, the R_eff matrix, and the finite-t
    diffusion distances are built ONCE; each pair's profile then reads them off. `degeneracy_diag`
    (the von-Luxburg self-diagnostic at the loosest σ) is computed once and stamped on EVERY profile
    (absent ⇒ malformed). `chi_s` is `{}` here — this function has no spine; the harness entry
    point attaches it. Never one scalar: always the full (σ,t) profile."""
    sigma_grid = tuple(sorted(float(s) for s in sigma_grid))
    t_grid = tuple(float(t) for t in t_grid)
    if not sigma_grid:
        raise ValueError("sigma_t_profile: empty σ-grid — an instrument must declare its grid")
    if not t_grid:
        raise ValueError("sigma_t_profile: empty t-grid — (σ,t)-indexed, both grids pinned")

    n = graph.n
    r_by_sigma: list[np.ndarray] = []
    dist_by_sigma: list[dict[float, np.ndarray]] = []
    loosest_w: np.ndarray | None = None
    loosest_labels: np.ndarray | None = None
    for k, sigma in enumerate(sigma_grid):
        w = _weighted_matrix(graph, sigma, thresh)
        labels = _components(w)
        r_by_sigma.append(_r_eff_matrix(w, labels))
        dist_by_sigma.append(_diffusion_distances(w, t_grid))
        if k == 0:
            loosest_w, loosest_labels = w, labels
    assert loosest_w is not None and loosest_labels is not None    # sigma_grid is non-empty
    degeneracy = _degeneracy_diag(loosest_w, r_by_sigma[0], loosest_labels)

    digests = [graph.digest(i) for i in range(n)]
    profiles: list[ConductanceProfile] = []
    for i in range(n):
        for j in range(i + 1, n):
            commute = tuple(
                tuple(float(dist_by_sigma[k][t][i, j]) for t in t_grid)
                for k in range(len(sigma_grid))
            )
            profiles.append(
                ConductanceProfile(
                    a=digests[i], b=digests[j],
                    sigma_grid=sigma_grid, t_grid=t_grid,
                    commute=commute,
                    r_eff_loosest=float(r_by_sigma[0][i, j]),
                    degeneracy_diag=degeneracy,
                    chi_s={},
                )
            )
    return profiles


# ── CN-4: the depth budget + the χ_s sequentiality statistic (grounded in the spine) ─────────────


def _longest_chain(stratum_spine: Spine, event_ids: Sequence[str]) -> int:
    """The longest ≼-chain (in EVENT count) among `event_ids` within a stratum-restricted spine.
    `proper_time(a,b)` returns the max-chain length of the causal interval `[a,b]`; the maximum over
    all comparable pairs is the global longest chain (its endpoints are the chain's bottom/top). A
    single event is a 1-chain. finding-0090 note: we use the CHAIN length here as the numerator; the
    budget itself (below) uses N_s COUNTS, sidestepping the proper-time-exactness erratum."""
    if not event_ids:
        return 0
    longest = 1
    for a in event_ids:
        for b in event_ids:
            if a == b:
                continue
            length, _complete = stratum_spine.proper_time(a, b)
            longest = max(longest, length)
    return longest


def chi_s(spine: Spine, stratum: str, *, window: Sequence[str] | None = None) -> float | None:
    r"""The CN-4 sequentiality statistic `χ_s(W) = longest-chain / N_s(W) ∈ (0,1]` for a stratum
    over a window W (v1: the whole stratum unless `window` restricts the event ids). `N_s(W)` = the
    per-stratum event COUNT (finding-0090: a count, not the proper-time metric — the erratum does
    not gate this). `χ_s = 1` iff the window-events are totally ordered; the depth budget
    `longest-chain ≤ N_s(W)` is exactly `χ_s ≤ 1`. Returns `None` when `N_s(W) = 0` (χ_s undefined
    with no events)."""
    stratum_spine = spine.n_s(stratum)
    ids = [e.event_id for e in stratum_spine.events()]
    if window is not None:
        keep = set(window)
        ids = [i for i in ids if i in keep]
    n_s = len(ids)
    if n_s == 0:
        return None
    return _longest_chain(stratum_spine, ids) / n_s


def chi_s_all(spine: Spine, *, strata: Sequence[str] = (_MIRROR_STRATUM,)) -> dict[str, float]:
    """Per-stratum χ_s over the given strata (v1: the mirror stratum), omitting empty strata
    (χ_s undefined at `N_s = 0`). The `dict[str, float]` attached to every emitted profile."""
    out: dict[str, float] = {}
    for s in strata:
        value = chi_s(spine, s)
        if value is not None:
            out[s] = value
    return out


# ── CN-3: the reconnection rider (leave-one-out verified over weight-increased edges) ────────────


def _common_index(before: MirrorGraph, after: MirrorGraph) -> tuple[dict[str, int], list[str]]:
    """A shared digest→index map over the union of both graphs' nodes (a graph may add nodes between
    cuts). Sorted for determinism."""
    digests = sorted(
        {before.digest(i) for i in range(before.n)} | {after.digest(i) for i in range(after.n)}
    )
    return {d: i for i, d in enumerate(digests)}, digests


def _graph_weights(
    graph: MirrorGraph, index_of: Mapping[str, int], size: int, thresh: Mapping[str, float]
) -> np.ndarray:
    """The graph's CN-4 weighted adjacency lifted into a shared `size × size` index space (edges the
    graph admits at its own built σ, weighted by `churn_weight`)."""
    w = np.zeros((size, size), dtype=np.float64)
    for i in range(graph.n):
        gi = index_of[graph.digest(i)]
        for j in graph.neighbors(i):
            if j > i:
                gj = index_of[graph.digest(j)]
                weight = churn_weight(float(graph.sim[i, j]), 0.0, 0.0, thresh)
                w[gi, gj] = w[gj, gi] = weight
    return w


def _pair_conductance(w: np.ndarray, ia: int, ib: int) -> float:
    """`1/R_eff` between two indices over weighted adjacency `W` (0 across components)."""
    labels = _components(w)
    if labels[ia] != labels[ib]:
        return 0.0
    r = _r_eff_matrix(w, labels)[ia, ib]
    return 1.0 / r if r > _ZERO_EPS else 0.0


def reconnection_scan(
    before: MirrorGraph,
    after: MirrorGraph,
    *,
    proper_time_gap: int,
    thresh: Mapping[str, float] = CONDUCTANCE_THRESH,
) -> list[ReconnectionEvent]:
    """Δ-conductance spikes from `before`→`after`, each **verified** by leave-one-out attribution
    over the WEIGHT-INCREASED edges (finding-0099 — added OR edited; a new edge is the 0→w case, an
    edit that raises `cos` also qualifies). For every pair whose conductance rose, each
    weight-increased edge is reverted to its before-weight in isolation; an edge whose reversion
    ERASES the rise is a confirmed bridging edge. Reports only leave-one-out-confirmed edges, never
    a guess. A decay-only interval (no weight increased) yields no rise and no event (the null)."""
    index_of, digests = _common_index(before, after)
    size = len(digests)
    w_before = _graph_weights(before, index_of, size, thresh)
    w_after = _graph_weights(after, index_of, size, thresh)

    # The weight-INCREASED edge set (added OR edited): the exact CN-4 attribution domain.
    increased: list[tuple[int, int]] = [
        (i, j)
        for i in range(size)
        for j in range(i + 1, size)
        if w_after[i, j] > w_before[i, j] + _RISE_EPS
    ]

    events: list[ReconnectionEvent] = []
    for p in range(size):
        for q in range(p + 1, size):
            c_before = _pair_conductance(w_before, p, q)
            c_after = _pair_conductance(w_after, p, q)
            delta = c_after - c_before
            if delta <= _RISE_EPS:
                continue                                      # no rise (decay/flat) — no reconnect
            bridging: list[tuple[str, str]] = []
            for i, j in increased:
                w_loo = w_after.copy()
                w_loo[i, j] = w_loo[j, i] = w_before[i, j]    # revert this edge's increase only
                if _pair_conductance(w_loo, p, q) <= c_before + _RISE_EPS:
                    bridging.append((digests[i], digests[j]))  # leave-one-out CONFIRMED
            events.append(
                ReconnectionEvent(
                    a=digests[p], b=digests[q],
                    delta_conductance=float(delta),
                    proper_time_gap=int(proper_time_gap),
                    bridging_edges=tuple(sorted(bridging)),
                )
            )
    events.sort(key=lambda e: (-e.delta_conductance, e.a, e.b))
    return events
