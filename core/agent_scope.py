# ── Family 1 boundary (capability algebra) · the agent layer · docs/NOTATION.md ──────────────────
# OBJECT:    the four role SIGNATURES (sensor / query / integrator / dreamer) as scope constructors
#            over the ratified (Σ,E,T,A) lattice (dn-agent-taxonomy §2.1), plus the conformance
#            check `assert_conforms` — a guard-tier assertion that an agent's ACTUAL store handles ⊑
#            its DECLARED scope. Roles are vocabulary, not gates: this adds NO new lattice machinery
#            (composition is the existing `Scope.meet`) and wires NO enforcement into any read path.
# INVARIANT: an agent is born inside its role's region — a sensor names ONE stratum and writes no
#            edges; an integrator spans ≥ 2 BASE strata and writes only fibers ⊆ {C, F}; a query
#            writes nothing (W_Σ=0). Delegation stays monotone: meet(parent, template) ⊑ parent
#            (non-negotiable #6, reused verbatim from `core.scope`). W_world = NONE for every role
#            (no effector reach in this taxonomy — dn-agent-taxonomy §2.1).
# ENFORCED:  static (this pure-core typing layer; mypy-checked) + guard
#            (tests/unit/test_agent_scope.py proves each constructor lands in its §2.1 region, that
#            an out-of-region request RAISES, and that `assert_conforms` rejects a smuggled handle).
"""The agent taxonomy as scope constructors (dn-agent-taxonomy §2.1, ratified 2026-07-18).

`dn-agent-taxonomy` settled a four-role ontology — **sensor**, **query agent**, **integrator**,
**dreamer** — and stated each as a *scope signature*: a reusable region of the `(Σ, E, T, A)`
lattice (`core.scope`) plus a model-class annotation. This module is that vocabulary: one
constructor per role returning the template `Scope` an agent of that role is born inside, and a
conformance helper that checks an agent's real store handles do not exceed what it declared.

It adds NO lattice machinery. Composition against a parent grant is the *existing* `Scope.meet`
(the ratified delegation law, `meet(parent, template) ⊑ parent`); admissibility is the existing
`req_admissible`/`admissible`. A role is a way of *building* a scope, never a new kind of scope.

PURE-CORE: imports only `core.scope`. It materializes no clock, reads no store, wires no read-path
gate (the enforcement stays where it lives — typed Views, structural store properties, the algebra's
admissibility; dn-capability-scope §2.2 / dn-agent-taxonomy §2.1). The tier is `STATIC_GUARD`
throughout (vocabulary + guard — dn-agent-taxonomy §2.1, plan §3 Q5).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.scope import (
    _REFINES,
    Authority,
    Clock,
    EdgeScope,
    Fiber,
    Privilege,
    Scope,
    Stratum,
    StratumScope,
    Tier,
    TimeScope,
    Window,
    WorldReach,
)

# The write fibers an integrator may hold: C (causal-witnessed production — its defining output) and
# F (pure citation resolution, as the proto-integrator `reference_edges` already writes). D
# (supersession) is the D-machinery's, never an integrator's (dn-agent-taxonomy §2.5).
_INTEGRATOR_WRITE_FIBERS: frozenset[str] = frozenset({"C", "F"})


def _base_of(s: Stratum) -> Stratum:
    """The base root of a stratum in R: a refinement maps up to its parent, a base maps to itself.
    Used only to count DISTINCT base strata for the integrator's ≥ 2 requirement — it is not a
    lattice operation (downward closure still goes the other way, `core.scope._downward_close`)."""
    return _REFINES.get(s, s)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# The role constructors (dn-agent-taxonomy §2.1)
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def sensor_scope(stratum: Stratum) -> Scope:
    """A **sensor agent** over one source/stratum (dn-agent-taxonomy §2.1/§2.4): reads and projects
    its OWN stratum, only. `Σ = {stratum}↓` (the downset — a base stratum pulls in its refinements),
    `E = ⊥` (sensors produce nodes, never edges), `T = (N_s, ∗)` (its stratum's event clock over the
    whole ledger window), `A = (READ, W_Σ=1, NONE)` — the "sensor dual" write bit is exactly this
    role's authority. Single-stratum, so the SLICE rule never fires."""
    return Scope(
        sigma=StratumScope.of(stratum),
        edges=EdgeScope.bottom(),
        time=TimeScope(Clock.N_S, Window.all()),
        authority=Authority(Privilege.READ, 1, WorldReach.NONE),
        tier=Tier.STATIC_GUARD,
    )


def query_scope(strata: Iterable[Stratum]) -> Scope:
    """A **query agent** (dn-agent-taxonomy §2.1): reads a grantable subset of the graph, answers,
    and writes NOTHING structural. `Σ =` the downset of `strata`, `E = ⊤` (it may read every edge
    class), `T = (N, ∗)` (the ledger — it reads the whole corpus), `A = (READ, W_Σ=0, NONE)`: the
    read-only, no-projection-write authority. Its own dialogue re-enters the corpus only through a
    sensor — a query agent never writes what it said."""
    return Scope(
        sigma=StratumScope.of(*strata),
        edges=EdgeScope.top(),
        time=TimeScope.ledger(),
        authority=Authority(Privilege.READ, 0, WorldReach.NONE),
        tier=Tier.STATIC_GUARD,
    )


def integrator_scope(
    read: Iterable[tuple[Stratum, str]], write_fibers: Iterable[Fiber]
) -> Scope:
    """An **integrator** (dn-agent-taxonomy §2.1/§2.5): resolves references across strata into
    proven edges. Inherently MULTI-strata — an edge's endpoints live in different strata by
    construction — so it requires `read` naming **≥ 2 distinct BASE strata** (owner's). `read` is a
    set of `(stratum, layer-label)` pairs; the layer labels document the layer-granular grant
    (`(dialogue_transcript, "L1-action-log") ⊔ (observed, "commit-ledger")`) but are NOT lattice
    elements in v1 — a layer-refinement lattice inside Σ is parked (plan §11). `Σ =` the downset of
    the named strata; `E =` the write fibers (⊆ {C, F} — C is its defining output, F for pure
    citation resolution); `T = (commit, ∗)` (the repo side of the pair-cut, a cut clock so the
    multi-stratum scope is well-typed); `A = (READ, W_Σ=1, NONE)` — model-free, edge-store writes.

    Raises `ValueError` for an out-of-region request: fewer than 2 base strata (that is a sensor,
    not an integrator) or a write fiber outside {C, F}.
    """
    pairs = list(read)
    strata = [s for s, _layer in pairs]
    bases = {_base_of(s) for s in strata}
    if len(bases) < 2:
        raise ValueError(
            f"integrator_scope: an integrator spans ≥ 2 base strata (an edge's endpoints live in "
            f"different strata) — got {len(bases)} base(s) {sorted(b.value for b in bases)} from "
            f"{[(s.value, layer) for s, layer in pairs]} (dn-agent-taxonomy §2.1)"
        )
    fibers = frozenset(write_fibers)
    if not fibers <= _INTEGRATOR_WRITE_FIBERS:
        raise ValueError(
            f"integrator_scope: write fibers must be ⊆ {{C, F}} (C = causal-witnessed, F = "
            f"citation; D is the D-machinery's, never an integrator's) — got {sorted(fibers)} "
            f"(dn-agent-taxonomy §2.5)"
        )
    return Scope(
        sigma=StratumScope.of(*strata),
        edges=EdgeScope(fibers),
        time=TimeScope(Clock.COMMIT, Window.all()),
        authority=Authority(Privilege.READ, 1, WorldReach.NONE),
        tier=Tier.STATIC_GUARD,
    )


def dreamer_scope(strata: Iterable[Stratum]) -> Scope:
    """A **dreamer** (dn-agent-taxonomy §2.1) — the apex/general class: core-resident, up to `⊤_Σ`
    per OWNER grant, produces interpreted nodes and all edge types. `Σ =` the downset of the granted
    `strata` (the caller passes what the owner declared — this constructor never widens on its own),
    `E = ⊤` (all fiber types), `T = (N, ∗)` (the ledger), `A = (READ, W_Σ=1, NONE)` — writes are
    `interpreted`-provenance only (structurally unforgeable — the `DerivedStore` has no provenance
    parameter). Constructor only: each dreamer is an owner-declared, harness-evaluable scope grant
    (dn-cross-strata-dreamer); the T-subtype split (synchronic point-cut vs diachronic interval) is
    the dreamer program's, bound per grant."""
    return Scope(
        sigma=StratumScope.of(*strata),
        edges=EdgeScope.top(),
        time=TimeScope.ledger(),
        authority=Authority(Privilege.READ, 1, WorldReach.NONE),
        tier=Tier.STATIC_GUARD,
    )


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# The three actor PROFILES (dn-agentic-loop §2.3) — the internal/external scope asymmetry, typed
# ═══════════════════════════════════════════════════════════════════════════════════════════════
#
# Where the four ROLE constructors above are the taxonomy's read/witness signatures, these three are
# the ACTOR profiles the agentic loop names: IA (internal actor — the dreamer/probe family), and the
# external actor split into EA-p (proposer, core-side) + EA-x (executor, edge-side). They are the
# same KIND of thing — template scopes, composed against a parent by the existing `Scope.meet`,
# pure-core (imports only `core.scope`) — layered on the ratified lattice, exactly as the roles are.
#
# Their point is the zone-boundary inversion (§2.3, gap G-D — `core.scope.zone_admissible`):
# broad PRIVATE read ⊥ world reach. All three are zone-admissible BY CONSTRUCTION — IA/EA-p carry
# `W_world = NONE` (private, no world reach); EA-x carries `Σ = ⊥` (world reach, reads no vault —
# bright line 2). The test surface (tests/unit/test_agent_scope.py) proves each lands in its §2.3
# region AND passes `zone_admissible`.


def internal_actor(
    strata: Iterable[Stratum] | None = None, *, hypothetical: bool = False
) -> Scope:
    """**Profile IA — the internal actor** (dn-agentic-loop §2.3; the DreamCharter is its built
    constructor, bp-079). Broad private read, no world reach. `Σ =` the granted downset, default
    to `⊤_Σ` (`R ∖ 𝔇` — broad by grant; the caller passes what the owner declared, this never widens
    past top), optionally ∪ {HYPOTHETICAL} when staging counterfactuals (`hypothetical=True`
    — named explicitly, per the overlay's Σ-visibility rule). `E = ⊤` (it reasons over all edge
    classes); `T = (commit, ∗)` — a CUT clock, so the multi-stratum scope is well-typed and any
    point read carries the pair-cut (§2.3: "SLICE fires on any multi-stratum point read"); `A =
    (READ_PROPOSE, W_Σ=1, W_world=NONE)` — interpreted-tier projection-writes (structurally
    unforgeable: `DerivedStore` has no provenance parameter), zero world reach. Residence: core.

    Zone-admissible by construction: `W_world = NONE`, so the §2.3 antecedent's consequent holds
    however broad Σ is."""
    base = StratumScope.top() if strata is None else StratumScope.of(*strata)
    sigma = (
        StratumScope(base.strata | frozenset({Stratum.HYPOTHETICAL})) if hypothetical else base
    )
    return Scope(
        sigma=sigma,
        edges=EdgeScope.top(),
        time=TimeScope(Clock.COMMIT, Window.all()),
        authority=Authority(Privilege.READ_PROPOSE, 1, WorldReach.NONE),
        tier=Tier.STATIC_GUARD,
    )


def external_proposer(strata: Iterable[Stratum] = (Stratum.MIRROR_AUTHORED,)) -> Scope:
    """**Profile EA-p — the external proposer** (dn-agentic-loop §2.3; core-side tailoring half of
    Track G's proposer/executor split, dn-hands §5/§7). Composes a PROPOSAL artifact, never a sent
    one. `Σ =` `mirror_authored` (via `MirrorView`) or narrower — the owner-authored corpus the
    outbound tailoring reads; `E = ⊤` (it reads every edge class to compose); `T = (N, ∗)` (single
    stratum — SLICE never fires); `A = (READ_PROPOSE, W_Σ=0, W_world=NONE)` — propose-only, writes
    NOTHING structural, zero world reach. Residence: core.

    Zone-admissible: it reads private strata (`mirror_authored ∈ PRIVATE_STRATA`) but
    `W_world = NONE`, so the law holds."""
    return Scope(
        sigma=StratumScope.of(*strata),
        edges=EdgeScope.top(),
        time=TimeScope.ledger(),
        authority=Authority(Privilege.READ_PROPOSE, 0, WorldReach.NONE),
        tier=Tier.STATIC_GUARD,
    )


def external_executor(reach: WorldReach = WorldReach.SENSING) -> Scope:
    """**Profile EA-x — the external executor** (dn-agentic-loop §2.3; edge-side half of Track G's
    split). It NEVER reads the vault (bright line 2): `Σ = ⊥` over corpus strata — its only scope is
    the world coordinate. `E = ⊥`; `T = (now, ∗)` (the live present — EffectView's clock); `A =
    (READ, W_Σ=0, W_world=reach)`, `reach` the blast-radius-gated effector ceiling ε (default the
    minimal nonzero `SENSING`; ops-side gates the actual grant per bright line 3, and finding-0011
    keeps the DEPLOYED ceiling NONE — this template is vocabulary, wires nothing). Residence: edge.

    Zone-admissible by construction NOT via `W_world` (it HOLDS world reach) but via `Σ = ⊥`: the
    law's antecedent `Σ ⊓ PRIVATE_STRATA ≠ ⊥` is FALSE, so any reach is admissible. This is the
    inversion's other corner — the whole point of the executor reading no vault."""
    return Scope(
        sigma=StratumScope.bottom(),
        edges=EdgeScope.bottom(),
        time=TimeScope(Clock.NOW, Window.all()),
        authority=Authority(Privilege.READ, 0, reach),
        tier=Tier.STATIC_GUARD,
    )


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Conformance — an agent's actual handles ⊑ its declared scope (guard tier)
# ═══════════════════════════════════════════════════════════════════════════════════════════════


class ConformanceError(ValueError):
    """An agent's actual store handles exceed its declared scope — a handle reaches a stratum
    outside the declared Σ, projection-writes beyond the declared W_Σ, or writes an edge fiber
    outside the declared E. The guard-tier analog of the Views' declared-vs-actual `SCOPE` check
    (tests/unit/test_view_scopes.py): honestly labeled, a runtime assertion, not a structural
    impossibility."""


@dataclass(frozen=True)
class Handle:
    """One store/graph handle an agent actually holds, described by the scope coordinates it
    exercises: the `stratum` it reaches, whether it projection-writes there (`writes_stratum` ⇒
    exercises W_Σ=1), and any edge fiber it writes (`writes_fiber` ∈ {C, F, D} or None for a
    read-only handle). The inventory a real agent presents at construction; `assert_conforms` checks
    it against the declared scope."""

    name: str
    stratum: Stratum
    writes_stratum: bool = False
    writes_fiber: str | None = None


HandleInventory = tuple[Handle, ...]


def assert_conforms(declared: Scope, handles: HandleInventory) -> None:
    """Assert every handle in `handles` is within `declared` — the conformance pattern
    (dn-agent-taxonomy §2.1; precedent `test_view_scopes.py`). Each handle must:
      * reach a stratum **in** `declared.sigma` (the declared Σ is already downward-closed, so a
        handle on a refinement of a granted base stratum passes);
      * projection-write only if `declared.authority.store_write ≥ 1`;
      * write an edge fiber only if that fiber is **in** `declared.edges`.
    Raises `ConformanceError` on the first violation (a smuggled extra handle). Guard tier: this is
    a check a construction site runs, not a structural guarantee — honest labeling (plan §3 Q3)."""
    for h in handles:
        if h.stratum not in declared.sigma.strata:
            raise ConformanceError(
                f"handle {h.name!r} reaches stratum {h.stratum.value!r}, outside the declared Σ "
                f"{sorted(s.value for s in declared.sigma.strata)}"
            )
        if h.writes_stratum and declared.authority.store_write < 1:
            raise ConformanceError(
                f"handle {h.name!r} projection-writes stratum {h.stratum.value!r}, but declared "
                f"authority is read-only (W_Σ=0)"
            )
        if h.writes_fiber is not None and h.writes_fiber not in declared.edges.fibers:
            raise ConformanceError(
                f"handle {h.name!r} writes edge fiber {h.writes_fiber!r}, outside the declared "
                f"E {sorted(declared.edges.fibers)}"
            )
