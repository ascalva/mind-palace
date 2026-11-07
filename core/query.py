"""The query engine's grants, scope table and β-curve — what the sentence algebra builds on
(dn-core-query-protocol §2.1–§2.5, dn-capability-scope §2.4, dn-temporal-retrieval-algebra
§2.1–§2.2).

Every verb has a REQUIRED scope `req(verb)` built from the four lattice coordinates of
`core.kernel.scope` — strata Σ, edge classes E ⊆ {F, D, C}, time T = (clock, window), authority
A = P × W_Σ × W_world — and a sentence is admissible iff `req ⊑ g` for some scope `g` the client was
granted. A client's grant is a SET of scopes, one per clock plane: `TimeScope.⊑` compares windows
only on one clock and a cross-clock join is a constructor error until the global clock N
materializes (CS-a), so "semantic, structural and temporal reads" cannot be one scope — they are
three, and a sentence fits under one of them.

**Mode is a corollary of scope, never a flag** (§2.4): C ∈ E → causal; D ∈ E or a non-point window →
temporal; E = {F} → structural; otherwise semantic.

What lives here now (2026-11-04, the owner's order retired the one-word executor):

* `Grant`, `AMBASSADOR` and the owner's `AMBASSADOR_OVERLAY` (`with_overlay`) — the grants in code.
* `Verb`, `required` and `mode_of` — the scope table of the eight one-word verbs, kept as the laws'
  anchor (SCO-8, QSA-8) and as `core/sentence/legacy.py`'s compatibility map; the sentence
  compiler (`core/sentence/types.py`) builds its clauses' scopes the same way and types them by
  the relation they walk (Rule NOUN), which the table did not.
* `free_energy_distances` — mode 1, the canonical randomized-shortest-path curve (TRA §2.1): costs
  c = −log w on the symmetrized similarity backbone, reference walk P = D⁻¹A, killed walk
  W_β = z·P∘w^β with z := γ (the recursion ceiling — "z's bound IS the γ-ceiling"), Z = (I − W_β)⁻¹,
  free energy φ_ij = −log(z_ij / z_jj)/β, symmetrized; with the graph's own degrees on a support
  (RSP-5). β→∞ is shortest path (1a); β→0 approaches resistance (1b).
* `QueryEngine` — the stores, opened lazily (`_get`), and the authored notes' similarity backbone
  (`note_graph`, `index_of`) that `link` resolves its endpoints through.
* `Hit` — one answer row, the sentence executor's too.

Sentences are compiled, executed and logged in `core/sentence/`; every result there is `Inv`
(it depends only on the event set read) or a `Hyp` under `assume`; no Rate is minted here.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any, Literal

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components

from core.kernel.clearance import MIRROR_READ
from core.kernel.config import Config, get_config
from core.kernel.recursion import DEFAULT_GAMMA
from core.kernel.scope import (
    ANCHOR,
    DENYLIST_IDEAL,
    Authority,
    Clock,
    EdgeScope,
    NoCommonClockError,
    Privilege,
    Scope,
    SliceError,
    Stratum,
    StratumScope,
    Tier,
    TimeScope,
    Window,
    WindowKind,
    WorldReach,
    admissible,
    req_admissible,
    zone_admissible,
)


class Verb(StrEnum):
    SEARCH = "search"
    REACH = "reach"
    DIFFUSE = "diffuse"
    HYBRID = "hybrid"
    HISTORY = "history"
    RELATED = "related"
    ORIGIN = "origin"
    CAPTURE = "capture"


class Mode(StrEnum):
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    TEMPORAL = "temporal"
    CAUSAL = "causal"


class InadmissibleGrant(PermissionError):
    """A grant that names a firewalled stratum or breaks the zone law (Σ-breadth ⊥ world reach)."""


CURATED_REF = "reference:"   # a curated paper's ref (scripts/curate_local.py), never a note path


# ── Scopes ──────────────────────────────────────────────────────────────────────────────────────


def scope(
    strata: Iterable[Stratum],
    fibers: Iterable[str],
    clock: Clock,
    window: Window,
    *,
    propose: bool = False,
    write: bool = False,
    cut: str | None = None,
) -> Scope:
    """A static+guard scope (this module checks it; nothing below it is structural)."""
    authority = Authority(
        Privilege.READ_PROPOSE if propose else Privilege.READ, int(write), WorldReach.NONE
    )
    return Scope(
        StratumScope.of(*strata),
        EdgeScope(frozenset(fibers)),
        TimeScope(clock, window),
        authority,
        tier=Tier.STATIC_GUARD,
        cut=cut,
    )


@dataclass(frozen=True)
class Grant:
    """A client's capability: one scope per clock plane. Admissibility is `req ⊑ g` for some g."""

    scopes: tuple[Scope, ...]

    def __post_init__(self) -> None:
        for s in self.scopes:
            if not admissible(s, [DENYLIST_IDEAL]):
                raise InadmissibleGrant(
                    f"grant names the foundation denylist: {sorted(s.sigma.strata)}"
                )
            if not zone_admissible(s):
                raise InadmissibleGrant("a grant that reads private strata may not reach the world")

    def admits(self, required: Scope) -> bool:
        return any(req_admissible(required, g) for g in self.scopes)

    def meet(self, other: Grant) -> Grant:
        """Safe delegation: the pairwise meets that exist. A cross-clock pair has no meet, and
        neither has a pair whose windows meet at a point across several strata with no shared
        cut (`[1,5] ⊓ [5,9] = pt(5)`): the SLICE rule refuses it (formal/Palace/Scope.lean)."""
        out: list[Scope] = []
        for a in self.scopes:
            for b in other.scopes:
                try:
                    out.append(a.meet(b))
                except (NoCommonClockError, SliceError):
                    continue
        return Grant(tuple(out))


_ALL = Window.all()
_NOW = Window.point(ANCHOR)

# The Ambassador (the local model's entry point): read + propose over the mirror, curated,
# interpreted, dialogue (incl. its own observed replies) and the reference stratum; projection-write
# into the dialogue stratum only; never any world reach. Three planes, one per clock.
AMBASSADOR = Grant(
    (
        scope(
            {
                Stratum.MIRROR,
                Stratum.CURATED,
                Stratum.INTERPRETED,
                Stratum.DIALOGUE,
                Stratum.OBSERVED,
                Stratum.REFERENCE,
            },
            {"F", "D"},
            Clock.PROJECTION_EVENT,
            _ALL,
            propose=True,
            write=True,
        ),
        scope({Stratum.REFERENCE, Stratum.DIALOGUE}, {"F", "C"}, Clock.COMMIT, _ALL, propose=True),
        scope({Stratum.MIRROR}, {"D"}, Clock.N_S, _ALL),
    )
)

# The grant the owner's own surfaces hold at the door (dn-ingest-door D3, §8): the terminal, the
# heartbeat and the watchers, which speak for the owner, not for an agent. The Ambassador's three
# planes with the write bit at both clocks, so `do sync code`, `do observe code` and `do sync chat`
# are admissible to the owner's surfaces and refused to the Ambassador (DOR-1, Door.lean). No world
# reach, as every grant in code.
OPERATOR = Grant(
    (
        scope(
            {
                Stratum.MIRROR,
                Stratum.CURATED,
                Stratum.INTERPRETED,
                Stratum.DIALOGUE,
                Stratum.OBSERVED,
                Stratum.REFERENCE,
            },
            {"F", "D"},
            Clock.PROJECTION_EVENT,
            _ALL,
            propose=True,
            write=True,
        ),
        scope({Stratum.REFERENCE, Stratum.DIALOGUE}, {"F", "C"}, Clock.COMMIT, _ALL, propose=True,
              write=True),
        scope({Stratum.MIRROR}, {"D"}, Clock.N_S, _ALL),
    )
)


def with_overlay(g: Grant) -> Grant:
    """`g` with the hypothetical overlay named on every plane — what the owner grants a client to
    evaluate `assume` sentences (dn-query-sentence-algebra §4 d; granted 2026-11-04). Σ is a
    downset and the overlay has nothing below it, so naming it adds the one stratum and nothing
    else widens: no world reach, the same clocks, windows and edge fibers (formal: `overlayGrant`,
    `Sentence.lean`). A result under `assume` is a `Hyp` regardless (`not_isInv_assume`)."""
    return Grant(tuple(
        replace(s, sigma=StratumScope.of(*s.sigma.strata, Stratum.HYPOTHETICAL)) for s in g.scopes
    ))


# The sentence surfaces' grant while `[query] hypotheticals` is on (the owner's grant of
# 2026-11-04): the Ambassador's planes, each naming the overlay. The base `AMBASSADOR` stays what
# the legacy table and `link` admit against; the Lean keeps both (`ambassador_no_assume`,
# `ambassadorOverlay_admits_assume_iff`).
AMBASSADOR_OVERLAY = with_overlay(AMBASSADOR)


# Which provenance classes a stratum's rows carry lives in the kernel
# (`core.kernel.clearance.STRATUM_CLASSES`), so the query engine and every other mint read one
# table. A sentence reads by the same table after admission: its universe holds only the strata
# its admitted clauses name, and each clause is evaluated on its own
# (`core.sentence.execute.membership`, `core.sentence.universe.admitted_strata`).


def required(
    verb: Verb,
    *,
    strata: Iterable[Stratum] = (Stratum.MIRROR_AUTHORED,),
    history: bool = False,
    authored: bool = True,
) -> Scope:
    """`req(verb)` — the least scope a sentence of this verb needs."""
    if verb is Verb.SEARCH:
        sigma = tuple(strata)
        # The SLICE rule counts strata after downward closure, and `reference` closes to two
        # (`reference_repo` below it), so the single-read cut follows the closed set, not the
        # names: counting names made a search over `reference` alone raise SliceError.
        return scope(
            sigma,
            {"D"} if history else set(),
            Clock.PROJECTION_EVENT,
            _ALL if history else _NOW,
            cut="single-read" if len(StratumScope.of(*sigma).strata) > 1 else None,
        )
    if verb in (Verb.DIFFUSE, Verb.HYBRID, Verb.RELATED):
        return scope({Stratum.MIRROR_AUTHORED}, {"F"}, Clock.PROJECTION_EVENT, _NOW)
    if verb is Verb.REACH:
        return scope({Stratum.REFERENCE}, {"F"}, Clock.COMMIT, _NOW)
    if verb is Verb.HISTORY:
        return scope({Stratum.MIRROR_AUTHORED}, {"D"}, Clock.N_S, _ALL)
    if verb is Verb.ORIGIN:
        return scope({Stratum.REFERENCE, Stratum.DIALOGUE_TRANSCRIPT}, {"C"}, Clock.COMMIT, _NOW)
    if verb is Verb.CAPTURE:
        target = Stratum.DIALOGUE_TRANSCRIPT if authored else Stratum.OBSERVED
        return scope({target}, set(), Clock.PROJECTION_EVENT, _NOW, write=True)
    raise ValueError(f"unknown verb {verb!r}")


def mode_of(s: Scope) -> Mode:
    """§2.4: the mode follows from the scope."""
    if "C" in s.edges.fibers:
        return Mode.CAUSAL
    if "D" in s.edges.fibers or s.time.window.kind is not WindowKind.POINT:
        return Mode.TEMPORAL
    if s.edges.fibers == frozenset({"F"}):
        return Mode.STRUCTURAL
    return Mode.SEMANTIC


# ── Results ─────────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Hit:
    ref: str
    title: str = ""
    score: float | None = None
    stratum: str = ""
    provenance: str = ""
    text: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


# ── The β-curve (mode 1, TRA §2.1) ──────────────────────────────────────────────────────────────


def free_energy_distances(
    weights: np.ndarray, *, beta: float, z: float = DEFAULT_GAMMA,
    degrees: np.ndarray | None = None,
) -> np.ndarray:
    """Symmetrized RSP free-energy distance on a weighted graph with weights in (0, 1].

    `weights` is symmetric with a zero diagonal; 0 = no edge. Requires β > 0 and 0 < z < 1, which
    with w ≤ 1 bounds ρ(z·P∘w^β) ≤ z < 1 — the walk sum converges (Theorem A1's condition, carried
    by the γ-ceiling). Unreachable pairs are +inf.

    `degrees`, when given, are the FULL graph's degrees of these nodes — the walk on a support
    whose complement absorbs (RSP-5, dn-query-sentence-algebra §2.9): a transition to a node
    outside the support becomes a killing, so the support's nearness never exceeds the graph's.
    They must be at least the support's own degrees; smaller ones would make the walk invent
    weight, and are refused."""
    if beta <= 0 or not 0 < z < 1:
        raise ValueError("need beta > 0 and 0 < z < 1")
    n = weights.shape[0]
    own = weights.sum(axis=1)
    if degrees is None:
        deg = own
    else:
        deg = np.asarray(degrees, dtype=np.float64)
        if deg.shape != (n,):
            raise ValueError(f"degrees must be one per node: {deg.shape} for {n} nodes")
        if np.any(deg < own - 1e-9):
            raise ValueError("degrees must be at least the support's own: a smaller degree would "
                             "make the walk invent weight (RSP-5)")
    p_ref = np.divide(weights, deg[:, None], out=np.zeros_like(weights), where=deg[:, None] > 0)
    w_beta = z * p_ref * np.power(weights, beta, where=weights > 0, out=np.zeros_like(weights))
    zmat = np.linalg.inv(np.eye(n) - w_beta)
    diag = np.diag(zmat)
    with np.errstate(divide="ignore", invalid="ignore"):
        phi = -np.log(zmat / diag[None, :]) / beta
    phi = np.where(np.isfinite(phi) & (zmat > 0), phi, np.inf)
    sym = (phi + phi.T) / 2
    np.fill_diagonal(sym, 0.0)
    return sym


# Above this many nodes, `free_energy_distances_from` solves the walk on the source's connected
# component alone. Measured (docs/experiments/profile-2026-11-06.md, one session): a sparse direct
# solve of the whole resolvent was tried first and lost, 28x slower than the dense inverse on a
# connected support of 5,000 nodes (34 s against 1.2 s), because the distance needs the diagonal of
# the inverse, one solve a node, and LU fill makes each solve dear. The win is the decomposition:
# the walk matrix is block diagonal over components, so the dense inverse of the source's block is
# the source's row of the whole one.
COMPONENT_SOLVE_ABOVE = 300


def free_energy_distances_from(
    weights: np.ndarray, source: int, *, beta: float, z: float = DEFAULT_GAMMA,
    degrees: np.ndarray | None = None, method: Literal["auto", "full", "component"] = "auto",
) -> np.ndarray:
    """Row `source` of `free_energy_distances(weights, …)`: the distance from one node to every
    node, which is all `diffuse` reads.

    The walk matrix W_β is block diagonal over the connected components of the graph, so its
    resolvent is too: nodes in other components are unreachable (+inf, as in the full matrix) and
    the source's row depends on its own component alone. With `method="component"`, or "auto"
    above `COMPONENT_SOLVE_ABOVE` nodes, the dense inverse is taken of that block only: cubic in
    the component's size, and memory its square, not the support's. With `method="full"`, or
    "auto" at or below the threshold, it is that function's row, computed exactly as before.

    The solver is not part of what `diffuse` means: RSP-1 to RSP-5 are statements about the exact
    solution Z, and both routes compute it, to rounding (they agree to 1e-10 on random supports;
    the test pins it). They differ in time and memory, never in the walk."""
    n = weights.shape[0]
    if method == "full" or (method == "auto" and n <= COMPONENT_SOLVE_ABOVE):
        return np.asarray(free_energy_distances(weights, beta=beta, z=z, degrees=degrees)[source])
    if beta <= 0 or not 0 < z < 1:
        raise ValueError("need beta > 0 and 0 < z < 1")
    deg = None
    if degrees is not None:
        deg = np.asarray(degrees, dtype=np.float64)
        if deg.shape != (n,):
            raise ValueError(f"degrees must be one per node: {deg.shape} for {n} nodes")
        if np.any(deg < weights.sum(axis=1) - 1e-9):
            raise ValueError("degrees must be at least the support's own: a smaller degree would "
                             "make the walk invent weight (RSP-5)")
    _, label = connected_components(sp.csr_matrix(weights), directed=False)
    comp = np.flatnonzero(label == label[source])
    out = np.full(n, np.inf)
    out[comp] = free_energy_distances(
        weights[np.ix_(comp, comp)], beta=beta, z=z,
        degrees=None if deg is None else deg[comp])[int(np.searchsorted(comp, source))]
    return out


# ── The engine ──────────────────────────────────────────────────────────────────────────────────


@dataclass
class QueryEngine:
    """The instance's stores, opened lazily, and the authored notes' backbone. The sentence
    executor (`core/sentence/execute.py`) reads the stores through `_get`."""

    config: Config = field(default_factory=get_config)
    _cache: dict[str, Any] = field(default_factory=dict)

    # stores ----------------------------------------------------------------------------------
    def _get(self, name: str) -> Any:
        if name not in self._cache:
            cfg = self.config
            if name == "vectors":
                from core.stores.vectorstore import open_vector_store

                self._cache[name] = open_vector_store(cfg)
            elif name == "curated":
                from core.stores.curated_store import open_curated_store

                self._cache[name] = open_curated_store(cfg)
            elif name == "embedder":
                from core.ingest.embed import build_embedder

                self._cache[name] = build_embedder(cfg)
            elif name == "edges":
                from core.stores.edges import open_edge_store

                self._cache[name] = open_edge_store(cfg)
            elif name == "versions":
                from core.stores.versions import open_version_store

                self._cache[name] = open_version_store(cfg)
            elif name == "catalog":
                from core.stores.catalog import VaultCatalog

                self._cache[name] = VaultCatalog(cfg.paths.vault_catalog)
            elif name == "references":
                from core.stores.reference_edges import open_reference_edge_store

                self._cache[name] = open_reference_edge_store(cfg)
            elif name == "causal":
                from core.stores.causal_edges import open_causal_edge_store

                self._cache[name] = open_causal_edge_store(cfg)
            elif name == "chatlog":
                from core.stores.chatlog import open_chatlog_store

                self._cache[name] = open_chatlog_store(cfg)
            elif name == "attestations":
                from core.attestation.store import open_attestation_store

                self._cache[name] = open_attestation_store(cfg)
            elif name == "memberships":
                from core.stores.memberships import open_membership_store

                self._cache[name] = open_membership_store(cfg)
            else:
                raise KeyError(name)
        return self._cache[name]

    # the authored notes' backbone ------------------------------------------------------------
    def note_graph(self) -> tuple[list[dict[str, Any]], np.ndarray, np.ndarray]:
        """Authored notes (chunks averaged per source), their unit vectors, and the σ-backbone —
        what `link` resolves its endpoints through."""
        rows = self._get("vectors").all_rows(clearance=MIRROR_READ)
        by_src: dict[str, list[dict[str, Any]]] = {}
        for r in rows:
            by_src.setdefault(str(r["source_path"]), []).append(r)
        notes, vecs = [], []
        for src, rs in sorted(by_src.items()):
            v = np.mean([np.asarray(r["vector"], dtype=np.float64) for r in rs], axis=0)
            notes.append(
                {
                    "source_path": src,
                    "title": rs[0].get("title", ""),
                    "digest": rs[0].get("digest", ""),
                    "provenance": rs[0].get("provenance", ""),
                }
            )
            vecs.append(v / (np.linalg.norm(v) or 1.0))
        mat = np.asarray(vecs) if vecs else np.zeros((0, self.config.embedding.dim))
        sims = mat @ mat.T if len(vecs) else np.zeros((0, 0))
        sigma = self.config.dreaming.similarity_threshold
        weights = np.where(sims >= sigma, np.clip(sims, 0.0, 1.0), 0.0)
        np.fill_diagonal(weights, 0.0)
        return notes, mat, weights

    def index_of(self, notes: list[dict[str, Any]], target: str | None) -> int:
        """The note a path, digest or title names, in `note_graph`'s order."""
        for i, n in enumerate(notes):
            if target in (n["source_path"], n["digest"], n["title"]):
                return i
        raise LookupError(f"no authored note matches {target!r}")
