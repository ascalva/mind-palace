"""The unified query language — one sentence type over the core (dn-core-query-protocol §2.1–§2.5,
dn-capability-scope §2.4, dn-temporal-retrieval-algebra §2.1–§2.2).

A query is a sentence `(verb, s)`. Every verb has a REQUIRED scope `req(verb)` built from the four
lattice coordinates of `core.kernel.scope` — strata Σ, edge classes E ⊆ {F, D, C}, time T = (clock,
window), authority A = P × W_Σ × W_world — and a sentence is admissible iff `req(verb) ⊑ g` for some
scope `g` the client was granted. The check runs when the `Query` is constructed, so an ill-scoped
sentence never exists (the MirrorView move, made uniform). A client's grant is a SET of scopes, one
per clock plane: `TimeScope.⊑` compares windows only on one clock and a cross-clock join is a
constructor error until the global clock N materializes (CS-a), so "semantic, structural and
temporal reads" cannot be one scope — they are three, and a sentence fits under one of them.

**Mode is a corollary of scope, never a flag** (§2.4): C ∈ E → causal; D ∈ E or a non-point window →
temporal; E = {F} → structural; otherwise semantic. The operators:

* SEARCH — mode 2, the embedding Gram kernel, over the provenance classes Σ names. The mirror is
  read through `MIRROR_READABLE` only; superseded rows surface only when D ∈ E.
* REACH — mode 1a, hard reachability over citation fibers (`ReferenceView.connected_set`).
* DIFFUSE — mode 1 on the canonical randomized-shortest-path curve (TRA §2.1): costs c = −log w on
  the symmetrized similarity backbone, reference walk P = D⁻¹A, killed walk W_β = z·P∘w^β with
  z := γ (the recursion ceiling — "z's bound IS the γ-ceiling"), Z = (I − W_β)⁻¹, free energy
  φ_ij = −log(z_ij / z_jj)/β, symmetrized. β→∞ is shortest path (1a); β→0 approaches resistance
  (1b). One dial, β, as the note pins for v1.
* HYBRID — K_sem ⊙ K_struct (Schur product in the PSD cone): "near the query AND near the anchor".
* HISTORY — mode 3, σ_* (forward) / σ^* (back) along a note's version chain; the ledger window.
* RELATED — the signed relation edges (supports / contradicts / contextualizes) touching an atom.
* ORIGIN — the C-fiber: which witnessed commit minted a durable reference edge.
* CAPTURE — the one write verb: a projection-write (W_Σ = 1) into the dialogue stratum. Its
  provenance is fixed by the caller's role, never by the text (no laundering into an authored
  class).

Every result is `Inv` (it depends only on the event set read); no Rate is minted here.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

import numpy as np

from core.kernel.config import Config, get_config
from core.kernel.provenance import MIRROR_READABLE, Provenance
from core.kernel.recursion import DEFAULT_GAMMA
from core.kernel.scope import (
    ANCHOR,
    DENYLIST_IDEAL,
    Authority,
    Clock,
    EdgeScope,
    Inv,
    NoCommonClockError,
    Privilege,
    Scope,
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


class IllScopedQuery(PermissionError):
    """`req(verb) ⋢ grant` — the sentence is not constructible for this client."""


class InadmissibleGrant(PermissionError):
    """A grant that names a firewalled stratum or breaks the zone law (Σ-breadth ⊥ world reach)."""


class OutOfScopeTarget(LookupError):
    """The sentence's target lives in a stratum its verb does not walk (outside req(verb)'s Σ): a
    curated paper handed to a verb over the owner's notes. Refused with where to go instead,
    never answered with an empty result that reads like "nothing there"."""


CURATED_REF = "reference:"   # a curated paper's ref (scripts/curate_local.py), never a note path
_NOTE_GRAPH_VERBS = frozenset({"diffuse", "hybrid", "related", "history"})


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
        """Safe delegation: the pairwise meets that exist (a cross-clock pair has no meet)."""
        out: list[Scope] = []
        for a in self.scopes:
            for b in other.scopes:
                try:
                    out.append(a.meet(b))
                except NoCommonClockError:
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

# Which provenance classes a stratum's kernel rows carry (mode 2 reads rows by provenance).
_PROVENANCES: dict[Stratum, frozenset[Provenance]] = {
    Stratum.MIRROR: MIRROR_READABLE,
    Stratum.MIRROR_AUTHORED: MIRROR_READABLE,
    Stratum.CURATED: frozenset({Provenance.CURATED}),
    Stratum.INTERPRETED: frozenset({Provenance.INTERPRETED}),
    Stratum.OBSERVED: frozenset({Provenance.OBSERVED}),
    Stratum.DIALOGUE: frozenset({Provenance.OBSERVED, Provenance.AUTHORED_DIALOGUE}),
    Stratum.DIALOGUE_TRANSCRIPT: frozenset({Provenance.OBSERVED, Provenance.AUTHORED_DIALOGUE}),
    Stratum.REFERENCE: frozenset({Provenance.CODE}),
    Stratum.REFERENCE_REPO: frozenset({Provenance.CODE}),
}
_STRATUM_OF: dict[str, str] = {
    Provenance.AUTHORED_SOLO: "mirror",
    Provenance.AUTHORED_DIALOGUE: "dialogue",
    Provenance.CURATED: "curated",
    Provenance.INTERPRETED: "interpreted",
    Provenance.OBSERVED: "observed",
    Provenance.CODE: "reference",
}


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
        return scope(
            sigma,
            {"D"} if history else set(),
            Clock.PROJECTION_EVENT,
            _ALL if history else _NOW,
            cut="single-read" if len(sigma) > 1 else None,
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


@dataclass(frozen=True)
class Query:
    """A sentence `(verb, s)`; constructing one IS the admissibility check."""

    verb: Verb
    grant: Grant
    text: str | None = None
    target: str | None = None
    strata: tuple[Stratum, ...] = (Stratum.MIRROR_AUTHORED,)
    history: bool = False
    k: int = 5
    depth: int = 1
    beta: float = 1.0
    direction: Literal["forward", "back"] = "forward"
    req: Scope = field(init=False)

    def __post_init__(self) -> None:
        req = required(self.verb, strata=self.strata, history=self.history)
        if not self.grant.admits(req):
            raise IllScopedQuery(
                f"{self.verb.value}: required scope Σ={sorted(req.sigma.strata)} "
                f"E={sorted(req.edges.fibers)} "
                f"T=({req.time.clock.value}, {req.time.window.kind.value}) "
                f"is not under any granted scope"
            )
        object.__setattr__(self, "req", req)

    @property
    def mode(self) -> Mode:
        return mode_of(self.req)


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


@dataclass(frozen=True)
class Answer:
    verb: Verb
    mode: Mode
    operator: str
    result: Inv[tuple[Hit, ...]]
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "verb": self.verb.value,
            "mode": self.mode.value,
            "operator": self.operator,
            "notes": list(self.notes),
            "hits": [
                {k: v for k, v in h.__dict__.items() if v not in (None, "", {})}
                for h in self.result.value
            ],
        }


# ── The β-curve (mode 1, TRA §2.1) ──────────────────────────────────────────────────────────────


def free_energy_distances(
    weights: np.ndarray, *, beta: float, z: float = DEFAULT_GAMMA
) -> np.ndarray:
    """Symmetrized RSP free-energy distance on a weighted graph with weights in (0, 1].

    `weights` is symmetric with a zero diagonal; 0 = no edge. Requires β > 0 and 0 < z < 1, which
    with w ≤ 1 bounds ρ(z·P∘w^β) ≤ z < 1 — the walk sum converges (Theorem A1's condition, carried
    by the γ-ceiling). Unreachable pairs are +inf."""
    if beta <= 0 or not 0 < z < 1:
        raise ValueError("need beta > 0 and 0 < z < 1")
    n = weights.shape[0]
    deg = weights.sum(axis=1)
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


# ── The engine ──────────────────────────────────────────────────────────────────────────────────


@dataclass
class QueryEngine:
    """Executes admissible sentences against the instance's stores. Stores open lazily."""

    config: Config = field(default_factory=get_config)
    _cache: dict[str, Any] = field(default_factory=dict)

    # stores ----------------------------------------------------------------------------------
    def _get(self, name: str) -> Any:
        if name not in self._cache:
            cfg = self.config
            if name == "vectors":
                from core.stores.vectorstore import VectorStore

                self._cache[name] = VectorStore(cfg.paths.vector_store, dim=cfg.embedding.dim)
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
            else:
                raise KeyError(name)
        return self._cache[name]

    def ask(self, q: Query) -> Answer:
        if q.verb.value in _NOTE_GRAPH_VERBS and (q.target or "").startswith(CURATED_REF):
            raise OutOfScopeTarget(
                f"{q.target!r} is a curated paper; {q.verb.value} walks the owner's notes only. "
                'For papers: search with strata ["curated"], or read the ref.')
        return {
            Verb.SEARCH: self._search,
            Verb.REACH: self._reach,
            Verb.DIFFUSE: self._diffuse,
            Verb.HYBRID: self._hybrid,
            Verb.HISTORY: self._history,
            Verb.RELATED: self._related,
            Verb.ORIGIN: self._origin,
        }[q.verb](q)

    # mode 2 ----------------------------------------------------------------------------------
    def _search(self, q: Query) -> Answer:
        if not q.text:
            raise ValueError("search needs text")
        provs: set[Provenance] = set()
        for s in q.strata:
            provs |= _PROVENANCES.get(s, frozenset())
        vec = self._get("embedder").embed_query(q.text)
        rows = self._get("vectors").search(
            vec, k=q.k, provenances=provs, include_superseded="D" in q.req.edges.fibers
        )
        if Provenance.CURATED in provs:
            # Literature lives in its OWN store (dn-external-grounding §2.2), physically apart from
            # the mirror; a sentence whose Σ admits CURATED reads it too, merged by distance.
            lit = self._get("curated").search(vec, k=q.k, provenances={Provenance.CURATED})
            rows = sorted([*rows, *lit], key=lambda r: float(r.get("_distance", 0.0)))[: q.k]
        hits = tuple(_hit_from_row(r, score=1.0 - float(r.get("_distance", 0.0))) for r in rows)
        return Answer(
            q.verb,
            q.mode,
            "cosine over the embedding Gram kernel K_sem",
            Inv(hits),
            (f"provenances={sorted(p.value for p in provs)}",),
        )

    # mode 1 ----------------------------------------------------------------------------------
    def _note_graph(self) -> tuple[list[dict[str, Any]], np.ndarray, np.ndarray]:
        """Authored notes (chunks averaged per source), their unit vectors, and the σ-backbone."""
        rows = self._get("vectors").all_rows(provenances=MIRROR_READABLE)
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

    def _index(self, notes: list[dict[str, Any]], target: str | None) -> int:
        for i, n in enumerate(notes):
            if target in (n["source_path"], n["digest"], n["title"]):
                return i
        raise LookupError(f"no authored note matches {target!r}")

    def _diffuse(self, q: Query) -> Answer:
        notes, _, weights = self._note_graph()
        i = self._index(notes, q.target)
        dist = free_energy_distances(weights, beta=q.beta)[i]
        order = [j for j in np.argsort(dist) if j != i and np.isfinite(dist[j])][: q.k]
        hits = tuple(
            Hit(
                ref=notes[j]["source_path"],
                title=notes[j]["title"],
                score=float(dist[j]),
                stratum="mirror",
                provenance=notes[j]["provenance"],
                detail={"free_energy_distance": round(float(dist[j]), 4)},
            )
            for j in order
        )
        return Answer(
            q.verb,
            q.mode,
            f"RSP free-energy distance, β={q.beta}, z=γ={DEFAULT_GAMMA}, "
            f"σ={self.config.dreaming.similarity_threshold}",
            Inv(hits),
            ("smaller is closer; unreachable notes are omitted",),
        )

    def _hybrid(self, q: Query) -> Answer:
        if not q.text:
            raise ValueError("hybrid needs text and a target anchor")
        notes, mat, weights = self._note_graph()
        i = self._index(notes, q.target)
        k_struct = np.exp(-free_energy_distances(weights, beta=q.beta)[i])
        qv = np.asarray(self._get("embedder").embed_query(q.text), dtype=np.float64)
        k_sem = np.clip(mat @ (qv / (np.linalg.norm(qv) or 1.0)), 0.0, None)
        score = k_sem * k_struct
        order = [j for j in np.argsort(-score) if j != i and score[j] > 0][: q.k]
        hits = tuple(
            Hit(
                ref=notes[j]["source_path"],
                title=notes[j]["title"],
                score=float(score[j]),
                stratum="mirror",
                provenance=notes[j]["provenance"],
                detail={
                    "k_sem": round(float(k_sem[j]), 4),
                    "k_struct": round(float(k_struct[j]), 4),
                },
            )
            for j in order
        )
        return Answer(q.verb, q.mode, f"K_sem ⊙ K_struct (Schur), β={q.beta}", Inv(hits))

    def _reach(self, q: Query) -> Answer:
        from core.reference_view import open_reference_view

        if not q.target:
            raise ValueError("reach needs a target")
        view = open_reference_view(self.config)
        refs = sorted(view.connected_set(q.target, depth=q.depth))
        hits = tuple(Hit(ref=r, stratum="reference") for r in refs)
        return Answer(q.verb, q.mode, f"reachability over F, depth ≤ {q.depth}", Inv(hits))

    # mode 3 ----------------------------------------------------------------------------------
    def _history(self, q: Query) -> Answer:
        if not q.target:
            raise ValueError("history needs a target note")
        # Versions are keyed by the note's stable doc_id (its `id::`, else its path — bp-031), so a
        # rename never forks the chain; resolve a path to it through the catalog.
        catalog = self._get("catalog")
        doc_id = catalog.doc_id_for(q.target) if catalog.get(q.target) is not None else q.target
        versions = self._get("versions").history(doc_id)
        if q.direction == "back":
            versions = list(reversed(versions))
        hits = tuple(
            Hit(
                ref=f"{v.doc_id}@{v.version_seq}",
                score=float(v.version_seq),
                stratum="mirror",
                detail={"digest": v.digest, "at": v.at},
            )
            for v in versions
        )
        op = "σ_* (forward transport)" if q.direction == "forward" else "σ^* (pullback)"
        return Answer(q.verb, q.mode, f"{op} along the version chain, ledger window", Inv(hits))

    def _related(self, q: Query) -> Answer:
        if not q.target:
            raise ValueError("related needs a target")
        notes, _, _ = self._note_graph()
        i = self._index(notes, q.target)
        digest = notes[i]["digest"]
        by_digest = {n["digest"]: n for n in notes}
        hits = []
        for e in self._get("edges").all():
            if digest not in (e.u, e.v):
                continue
            other = e.v if e.u == digest else e.u
            n = by_digest.get(other, {})
            hits.append(
                Hit(
                    ref=n.get("source_path", other),
                    title=n.get("title", ""),
                    score=e.w,
                    stratum="mirror",
                    provenance=e.provenance,
                    detail={
                        "relation": e.rel_type,
                        "sign": int(e.sign),
                        "direction": "out" if e.u == digest else "in",
                    },
                )
            )
        return Answer(
            q.verb,
            q.mode,
            "signed relation edges (supports/contradicts/contextualizes)",
            Inv(tuple(hits)),
        )

    def _origin(self, q: Query) -> Answer:
        from core.origin_view import origin

        if not q.target:
            raise ValueError("origin needs a reference-edge id")
        edge = origin(
            q.target, causal_edges=self._get("causal"), reference_edges=self._get("references")
        )
        hits = (
            ()
            if edge is None
            else (
                Hit(
                    ref=q.target,
                    stratum="dialogue",
                    detail={k: str(v) for k, v in edge.__dict__.items()},
                ),
            )
        )
        return Answer(q.verb, q.mode, "C ∘ commit-keying (two-hop join)", Inv(hits))


def _hit_from_row(r: dict[str, Any], *, score: float) -> Hit:
    prov = str(r.get("provenance", ""))
    return Hit(
        ref=str(r.get("source_path", r.get("id", ""))),
        title=str(r.get("title", "")),
        score=round(score, 4),
        stratum=_STRATUM_OF.get(prov, ""),
        provenance=prov,
        text=str(r.get("text", ""))[:300],
        detail={"chunk": int(r.get("chunk_index", 0) or 0)},
    )
