---
type: build-plan
id: bp-039
alias: CQ-scope
status: in-progress
design_ref:
  - docs/design-notes/capability-scope-algebra.md
contract: builder
write_scope:
  - core/scope.py
  - tests/unit/test_scope.py
  - tests/unit/test_view_scopes.py
  - core/mirror.py
  - core/reference_view.py
  - core/temporal_view.py
  - core/ops_view.py
  - ops/effects.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 240k
    rationale: >-
      A NEW pure-typing module (`core/scope.py`) + a light additive retrofit (one class
      constant per View) + heavy property/law testing. Same deterministic, test-pinned,
      no-live-model character as bp-037 (180k est / 96k actual, self-driven) but with MORE
      distinct pieces: four component types (Σ refinement forest, E fibers, T clock+window
      with a PARTIAL meet, A product of three chains), lattice laws, firewall ideals, the
      clock poset, the enforcement-tier annotation, an optional Inv/Rate marker, and five
      View retrofits + declared-vs-actual guards. The math is banked theorem-grade in
      `dn-capability-scope` (fable, ratified) — NO fable, NO xhigh; deterministic algebra.
      Self-driven lands ~0.5–0.8× (week 92%, budget-tight); delegated ~1.6×.
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-15
updated: 2026-07-15
started: 2026-07-15
links:
  - docs/design-notes/capability-scope-algebra.md
  - docs/brainstorms/cq-scope-fable-pass.md
  - docs/build-plans/bp-037/plan.md
  - core/reference_view.py
  - ops/effects.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — `CQ-scope` (bp-039): the capability-scope typing layer — `Scope`, its lattice, and `req()` on the five Views

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan; **implementation proceeds item-by-item on owner
approval**. Authority-to-act (the owner's directed lead unit, ratifying `dn-capability-scope`) is
separate from the readiness blessing (owner-only `proposed → ready`, by hand) — no agent flips
readiness.

Graduated from ratified `dn-capability-scope` §3 Consequence 1 (named verbatim: *"One build plan:
the scope typing layer. `core/scope.py` … the frozen `Scope` dataclass, the lattice ops
(`meet`/`join`/`⊑`), the firewall ideals as data, the clock poset with the partial T-meet
(constructor error on no common clock), and `req()` declarations retrofitted onto the five View
constructors"*). The algebra is banked theorem-grade in the note (states the decisions) and its
warrant `cq-scope-fable-pass.md` (derivations, grades S1–S8). **This plan re-derives none of it —
it types what the note decided.** Model tier **opus**: deterministic algebra over a settled,
fully-specified surface; **no fable, no xhigh** (the design is banked, ratified).

**The whole plan is a PURE TYPING LAYER — zero behavior change to any View.** The five Views today
carry no explicit scope type (§3 Q2, confirmed); this plan gives them a *declared* `(Σ, E, T, A)`
scope and the algebra to compose scopes, but wires **no new enforcement into any read path or any
live caller**. The load-bearing falsifier for the whole plan: **every existing View test stays
green, unmodified — bit-identical reads.** If a read changes, the retrofit overreached.

## 1. Objective

Give the mind-palace a first-class `Scope` type — the `(Σ, E, T, A)` capability lattice with
`meet`/`join`/`⊑`, firewall ideals, the partial clock-`T` meet (a constructor error on no common
materialized clock), and the enforcement-tier annotation — in a new `core/scope.py`, and declare
each of the five built Views' scope (`req()`, from the note's §2.4 table) as a checkable constant,
with **zero change to any View's read behavior**.

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/capability-scope-algebra.md` — the ratified design. §2.1 (the four
   components, made well-posed), §2.2 (composition: meet/join, the PARTIAL T-meet, the SLICE rule,
   firewalls-as-ideals, tier-as-annotation), §2.3 (Inv vs Rate(κ), Rule CLOCK), §2.4 (the query
   language + the five-View inhabitation TABLE — the source of every `SCOPE` constant), Parked
   CS-a…CS-f.
2. `docs/brainstorms/cq-scope-fable-pass.md` — the warrant, for the *derivations* behind any choice
   the note states without proof (S1 Σ as refinement-forest downsets + denylist ideal; S2 the clock
   poset + partial-meet honesty; S3 the SLICE rule / vector clock; S5 the A = P × W_Σ × W_world
   split; S6 ideals + min-tier). Consult per-item, not cover-to-cover.
3. `ops/effects.py` — the effector blast-radius chain the scope's `W_world` grades over.
   `ReversibilityClass(IntEnum)` `SENSING=0 < REVERSIBLE=1 < IRREVERSIBLE=2` (`:47-56`);
   `ApprovalStrength` `NONE=0 < LIGHT < FULL_GATE` (`:59-65`) — **a DIFFERENT enum**; `blast_radius`
   (`:68-75`), `required_approval` (`:80-85`, `SENSING → NONE`); `EffectView` (`:170`) + its
   `ceiling: ReversibilityClass = SENSING` (`:183-184`) + factory `.admit(...)` (`:194-204`). This
   is the §4 reconciliation surface (the note's `NONE < SENSING` W_world floor is NOT this enum).
4. `core/reference_view.py` — the sibling View shape + the SLICE anchor. `ReferenceView` (`:47`),
   `.over(store, *, commit)` (`:60`), `_resolve_default_commit(cfg)` (`:111`, active-run
   `commit_sha` → git HEAD), `open_reference_view` (`:129`, anchor at `:138`). Its `SCOPE` = the
   table row `(reference_repo, {F}, (commit, pt), (read, 0, NONE), static+guard)`.
5. `core/temporal_view.py` — `TemporalView` (`:97`), `.over(store, *, commit)` (`:109`), the shared
   resolver import (`:176` `from core.reference_view import _resolve_default_commit`), `coherence_to`
   (`:138`), and **`CoherenceReport`** (`:56-70`) — the Inv audit target (count `coherence_norm` +
   two anchors `commit_from`/`commit_to`, no division).
6. `core/mirror.py` — `MirrorView` (`:54`), factory `.project(source)` (`:72`). Table row
   `(mirror_authored, —, (projection-event, pt), (read, 0, NONE), structural)`.
7. `core/ops_view.py` — `OpsView` (`:60`), factory `.over(attestations, ledger, *, drift=None)`
   (`:77`). Table row `(ops, —, (last-write, pt), (read, 0, NONE), static+guard)`.
8. `docs/build-plans/bp-037/plan.md` — the house style + the sibling precedent (an additive,
   behavior-preserving extension whose falsifier is "an existing call returns something different").

## 3. Investigation & grounding

- **Q1 — Do the five Views exist and carry no explicit scope type today? YES / confirmed.** No
  `class Scope`, no read-scope/grant type anywhere (`grep "class Scope"` → 0 hits; "write_scope"
  appears only in build-plan prose comments, e.g. `core/stores/reference_edges.py:181`). The note's
  claim holds. The five constructors: `MirrorView.project` (`core/mirror.py:72`), `ReferenceView.over`
  (`core/reference_view.py:60`), `TemporalView.over` (`core/temporal_view.py:109`), `OpsView.over`
  (`core/ops_view.py:77`), `EffectView.admit` (`ops/effects.py:194`). All are `@dataclass(frozen=True)`
  with a classmethod factory — the retrofit attaches a class-level `SCOPE` constant, touching neither
  the factory body nor any read.

- **Q2 — Existing "capability" machinery — collision risk?** There is unrelated capability code in
  `core/factory/` — `factory.grant(...)` (`core/factory/factory.py:63`), `roles.scope` = tool-ids a
  role may use (`core/factory/roles.py:11-33`), the object-capability tool handles
  (`core/factory/tools.py:64`). **This is agent-tool-handle capability, NOT a View read-scope.** The
  new `Scope` is a distinct concept; it must NOT be named to shadow or entangle with `factory.grant`.
  Wiring the delegation law `minted = meet(parent, template)` INTO `factory.grant` is behavior change
  and is **out of scope** (parked, §11) — this plan only makes the law *expressible and tested*.

- **Q3 — Where does `W_world`'s floor live? The note's `NONE < SENSING` is NOT `ReversibilityClass`.**
  `ReversibilityClass` (`ops/effects.py:47-56`) is `SENSING(0) < REVERSIBLE(1) < IRREVERSIBLE(2)` —
  **it has no `NONE`.** `NONE` is `ApprovalStrength.NONE` (`ops/effects.py:59-65`), a different enum.
  The note intends a `W_world` chain with a `NONE` floor *below* SENSING ("no world reach at all";
  Track G's standing fact `⊤_deployed.W_world = NONE`, finding-0011). **The code does not settle this
  — the plan settles it (§4, §6):** `core/scope.py` defines a NEW pure enum
  `WorldReach: NONE < SENSING < REVERSIBLE < IRREVERSIBLE`, and the `ReversibilityClass → WorldReach`
  bridge lives on the **ops side** (`ops/effects.py`, Item 3), preserving the ops→core dependency
  direction — `core/scope.py` imports nothing from `ops/`.

- **Q4 — The SLICE-rule anchor is real / shared? YES.** `_resolve_default_commit` is defined once
  (`core/reference_view.py:111`) and BOTH Views route through it — ReferenceView at `:138`,
  TemporalView via `from core.reference_view import _resolve_default_commit` (`:176`, used `:180`),
  whose docstring (`:172-174`) names it "the authoritative resolver … so this View and
  `ReferenceView` anchor identically." The commit SHA IS the consistent cut (§2.2 SLICE rule);
  the type will *state* this, and change nothing.

- **Q5 — Is `CoherenceReport` genuinely `Inv` (no division)? YES.** `core/temporal_view.py:56-70`:
  fields are `commit_from`/`commit_to` (two anchors) + `common_nodes`/`coherence_norm`/`nodes_added`/
  `nodes_dropped` (counts, `int`) + `severed` (tuple) + `is_flat` (bool). Construction (`:156-165`)
  computes only `len(...)`/`curvature_norm(...)` — **no `/` operator**. It audits as `Inv`; the Item-4
  audit test asserts this structurally.

- **Q6 — Dependency direction: may `core/scope.py` import from `ops/`?** Assumed NO — core is the
  inner layer (ops/edge depend on core, not the reverse; non-negotiable #1/#2 layering). The
  `WorldReach` enum is therefore pure-core, and the `ReversibilityClass`↔`WorldReach` bridge is
  authored ops-side. **If the builder finds core already imports ops, or that the bridge cannot be
  ops-side, STOP and file a `codebase` finding** (§10) — do not invert the layering to make the map
  convenient.

**Additional risks surfaced during reading:** (a) There are TWO more View-shaped types NOT in the
note's five — `core/sensing.py:190 ObservedView` and `core/dreams_view.py:44 DreamsView`. **The plan
scopes to the note's five ONLY**; ObservedView/DreamsView get scope declarations in a later unit when
their scope is designed (non-goal §9, park §11). (b) The **sensor** write-side dual `(read, 1, NONE)`
(§2.4) lives in `ops/self_sensor.py`/`ops/code_sensor.py` — retrofitting it widens blast radius into
the projection path; **parked (§11, CS-c re-entry)**, not built here.

## 4. Reconciliation

- **`ops/effects.py` — `W_world` is EXTENDED below `SENSING`, announced as an extension
  (cross-reference-on-extension), NOT a correction.** The note writes the effector chain
  `NONE < SENSING < …`; the code's `ReversibilityClass` starts at `SENSING`. Nothing in `effects.py`
  is *wrong* — the scope layer simply needs a floor the effector enum never had (a View may hold
  *no* world reach). Proposed: `core/scope.py` introduces `WorldReach(NONE<SENSING<REVERSIBLE<
  IRREVERSIBLE)`; `ops/effects.py` gains a small pure mapping `world_reach(rc: ReversibilityClass)
  -> WorldReach` (SENSING→SENSING, REVERSIBLE→REVERSIBLE, IRREVERSIBLE→IRREVERSIBLE) plus
  `EffectView.SCOPE`. `ReversibilityClass` itself is **unchanged** (no new member) — `NONE` is a
  scope-layer concept meaning "no `EffectView` granted," carried only in `WorldReach`. A one-line
  comment at the `ReversibilityClass` definition cross-references `core/scope.py:WorldReach` as the
  scope-side chain with the `NONE` floor.

- **`dn-capability-scope` frontmatter is `implementation: design-only` — becomes stale on build.**
  The ratified note is immutable (A8); this plan edits it nowhere. On completion the orchestrator
  batches the standing note-erratum ("`core/scope.py` now built") into `owner-questions.md` — the
  same pattern bp-035/037 used for `dn-core-query-protocol` (§10). No code is corrected/replaced;
  every change is additive.

- **No View read path is corrected.** Each View gains a `SCOPE` class constant and nothing else; the
  factory bodies and read methods are untouched (the bit-identical-reads falsifier). This is the
  whole reconciliation surface — there is no silent replacement anywhere.

## 5. Write scope

- `core/scope.py` — **NEW**: the `Scope` dataclass + the four component types (`StratumScope`,
  `EdgeScope`, `TimeScope`=(clock, window), `Authority`=P × W_Σ × `WorldReach`), the lattice ops
  (`meet`/`join`/`__le__`), the firewall ideals as data + admissibility, the clock poset + the
  partial T-meet, the `Tier` annotation with min-composition, and (Item 4) the `Inv`/`Rate(κ)` result
  markers + Rule CLOCK.
- `tests/unit/test_scope.py` — **NEW**: the lattice-law property tests, firewall-ideal admissibility,
  cross-clock-meet-raises, delegation-exceeding-parent-unrepresentable, SLICE-requires-cut, and the
  Inv/Rate audit.
- `tests/unit/test_view_scopes.py` — **NEW**: the declared-vs-actual guard, one per View (the `SCOPE`
  constant matches the note's §2.4 table AND the View's actual disposition), plus the bit-identical
  read spot-checks.
- `core/mirror.py`, `core/reference_view.py`, `core/temporal_view.py`, `core/ops_view.py`,
  `ops/effects.py` — Item 3 only: add ONE `SCOPE: Scope` class constant per View (and, in
  `effects.py`, the `world_reach` bridge). Additive; no factory/read change.

**Deliberately OUT of scope:** `core/factory/**` (the delegation law is expressible + tested but NOT
wired into `factory.grant` — behavior change, parked §11); `core/sensing.py` / `core/dreams_view.py`
(ObservedView/DreamsView — not the note's five); `ops/self_sensor.py` / `ops/code_sensor.py` (the
sensor write-dual — parked); `core/stores/**` (no store touched; clocks are *named*, not
materialized — N stays parked, CS-a); every design note (immutable, A8); the denylist
(`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`).

## 6. Interfaces pinned inline

```python
# core/scope.py — the NEW typing layer. Pure-core: imports NOTHING from ops/ or edge/ (§3 Q6).

from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import FrozenSet, Literal

# --- Σ: the stratum-refinement forest (§2.1). Base strata + refinement predicates as ELEMENTS. ---
# R = the finite forest; a StratumScope is a DOWNWARD-CLOSED subset of R (a downset).
# ⊤_Σ = R ∖ 𝔇 where 𝔇 (the foundation denylist) is an order-ideal subtracted from the top —
# even the fullest grant structurally excludes CONSTITUTION.md / eval/golden/**.
# Represent R's elements as a frozenset of tokens; refinement edges (reference_repo ⊂ reference,
# mirror_authored ⊂ mirror) are data, so downward-closure is checkable.

# --- E: edge-class fibers (§2.1). E ⊆ {F, D}; unchanged from the seed. ---

# --- T = (clock, window) (§2.1). Clocks are monotone coarsenings of the ledger causal order. ---
class Clock(IntEnum):          # the poset by materialization/fineness; N is PARKED (not materialized)
    # ...  N (finest, PARKED — CS-a) ⪰ N_s ⪰ …;  N ⪰ COMMIT ⪰ DISTINCT_SNAPSHOT;  WALL is exogenous
    ...
# common_refinement(a, b) -> Clock | None  — returns None when the only common refinement is the
# unmaterialized N ⇒ the T-meet raises a constructor error ("no common clock"). PARTIAL meet-semilattice.
# Window = pt(a) | [a, b] | ∗   (anchor first-class: now = (κ, pt(latest)); ledger = (N, ∗))

# --- A = P × W_Σ × W_world (§2.1). The "write" rung split into store-projection vs world-mutation. ---
class WorldReach(IntEnum):     # the NONE-floored chain the note's §2.1 W_world names (§3 Q3 / §4)
    NONE = 0                   # no world reach at all — the deployed ceiling (⊤_deployed.W_world = NONE)
    SENSING = 1
    REVERSIBLE = 2
    IRREVERSIBLE = 3
# P ∈ {READ < READ_PROPOSE} (non-negotiable #3); W_Σ ∈ {0 < 1} (projection-write; the sensor dual).

class Tier(IntEnum):           # enforcement STRENGTH — an annotation, never a lattice element (§2.2)
    CONVENTION = 0
    STATIC_GUARD = 1
    STRUCTURAL = 2             # composition takes the MIN tier along the construction chain

@dataclass(frozen=True)
class Scope:
    sigma: StratumScope        # a downset of R (∖ 𝔇 at the top)
    edges: FrozenSet[Literal["F", "D"]]
    time: TimeScope            # (clock, window)
    authority: Authority       # (P, W_Σ, WorldReach)
    tier: Tier                 # min-composed annotation

    def meet(self, other: "Scope") -> "Scope": ...   # componentwise; T-meet PARTIAL (raises on no common clock)
    def join(self, other: "Scope") -> "Scope": ...   # widening; grantable only by a holder of the join
    def __le__(self, other: "Scope") -> bool: ...     # ⊑ the partial order (delegation admissibility)

# Firewalls are ORDER-IDEALS (§2.2): a grant is admissible for client class c iff  s ⊓ ι = ⊥  for
# every ideal ι applicable to c (mirror payload for non-exempt clients; 𝔇 always). Ideals are DATA.
def admissible(s: Scope, ideals: "Iterable[Ideal]") -> bool: ...

# req(verb, s_granted): admissibility is  req(verb) ⊑ s_granted , checked at construction —
# ill-scoped sentences are UNREPRESENTABLE (the MirrorView move, made uniform). Each View exposes a
# SCOPE constant = req(read) from the §2.4 table.

# --- Item 4 (independently approvable): result typing Inv vs Rate(κ) (§2.3). ---
# Marker types; Rule CLOCK: a q: s -> Rate(κ) REQUIRES s.time.clock == κ. A Rate value carries its
# clock in its type, never a bare number. Every BUILT instrument audits Inv (CoherenceReport does).
```

```python
# The five View SCOPE constants (Item 3) — VERBATIM from dn-capability-scope §2.4, [VERIFIED] in S7.
# MirrorView   : Scope(mirror_authored, {},    (PROJECTION_EVENT, pt), (READ, 0, NONE), STRUCTURAL)
# ReferenceView: Scope(reference_repo,  {F},   (COMMIT, pt),          (READ, 0, NONE), STATIC_GUARD)
# TemporalView : Scope(reference_repo,  {F,D}, (COMMIT, pt);          (READ, 0, NONE), STATIC_GUARD)
#                 coherence read is the first INTERVAL window: (COMMIT, [n, n+1])
# OpsView      : Scope(ops,             {},    (LAST_WRITE, pt),      (READ, 0, NONE), STATIC_GUARD)
# EffectView   : Scope(world,           {},    (NOW, pt),             (READ, 0, ε),    STRUCTURAL)
#                 ε = world_reach(self.ceiling); deployed ceiling is NONE (⊤_deployed.W_world = NONE)
```

```python
# ops/effects.py — Item 3 additive bridge (ops → core; §3 Q6, §4). ReversibilityClass UNCHANGED.
from core.scope import WorldReach   # ops depends on core (never the reverse)
def world_reach(rc: "ReversibilityClass") -> WorldReach:
    """Lift the effector reversibility class into the scope-side W_world chain, whose NONE floor
    ('no world reach') has no ReversibilityClass member. SENSING→SENSING, REVERSIBLE→REVERSIBLE,
    IRREVERSIBLE→IRREVERSIBLE; NONE is reachable only by holding no EffectView. See core/scope.py."""
    ...
```

## 7. Items

### Item 1 — `core/scope.py`: the `Scope` type + the lattice (the pure algebra)
- **Objective:** the frozen `Scope` dataclass + its four component types (Σ downset, E fibers,
  T=(clock, window), A=P × W_Σ × `WorldReach`), the lattice ops `meet`/`join`/`__le__` (componentwise;
  A min-per-chain), the `WorldReach`/`Clock`/`Tier` enums, the firewall ideals as data + `admissible`,
  and the clock poset with the **partial** T-meet (constructor error on no common materialized clock).
- **Files:** `core/scope.py`.
- **Acceptance test:** the module imports; `Scope` is `frozen`; `meet`/`join`/`__le__` type-check
  under `mypy core` (0 errors); a smoke construction of `⊤_Σ = R ∖ 𝔇` excludes the denylist tokens;
  `Clock.common_refinement` returns `None` for a cross-clock pair whose only join is the unmaterialized
  `N`. (Laws proven in Item 2.)
- **Falsifier:** `core/scope.py` imports any symbol from `ops/`, `edge/`, or a store (layering
  inversion, §3 Q6); OR a cross-clock T-meet silently returns a scope instead of raising.
- **Invariant(s):** pure-core, no I/O, no store handle, no network; `Scope` is immutable (frozen);
  Sealed-core egress rule untouched (non-negotiable #1) — this file reads nothing external.
- **Touches stored data?** No (a type module; materializes no clock — N stays parked, CS-a).
  **Parallelizable?** No (Items 2–4 build on it).

### Item 2 — the lattice-law + firewall + delegation property tests
- **Objective:** prove the algebra: `meet`/`join` idempotent, commutative, associative, absorptive;
  `⊑` a partial order consistent with `meet` (`a ⊑ b ⟺ meet(a,b)==a`); firewall-ideal admissibility
  (`s ⊓ ι = ⊥`); the cross-clock T-meet **raises** "no common clock"; delegation-exceeding-parent is
  **unrepresentable** (`meet(parent, template) ⊑ parent` always; a template widening beyond parent
  cannot yield a child above parent); the SLICE rule (a `|Σ|>1` scope with a point window and no
  explicit consistent cut is rejected at construction).
- **Files:** `tests/unit/test_scope.py`.
- **Acceptance test:** all law tests pass under `pytest -q`; the cross-clock-meet test asserts the
  specific constructor error; the delegation test asserts `meet(parent, template) ⊑ parent` over a
  generated sample of scope pairs (property-style, fixed seed — no `Math.random`, enumerate a small
  lattice).
- **Falsifier:** any law fails on a concrete witness (e.g. `meet` non-associative on three real
  scopes) — a real algebra bug, recorded with the witness, NOT patched by weakening the law; OR the
  delegation test passes only because `meet` silently widens (masking a #6 violation).
- **Invariant(s):** non-negotiable #6 (monotone delegation) is the delegation test's subject; the
  tests introduce no store/network.
- **Touches stored data?** No.  **Depends on:** Item 1.

### Item 3 — `req()` retrofit: the five View `SCOPE` constants + the ops-side bridge
- **Objective:** add ONE `SCOPE: Scope` class constant to each of MirrorView, ReferenceView,
  TemporalView, OpsView, EffectView (verbatim from §2.4, pinned §6), and the `world_reach` bridge in
  `ops/effects.py`. **No factory body, read method, or return type changes.**
- **Files:** `core/mirror.py`, `core/reference_view.py`, `core/temporal_view.py`, `core/ops_view.py`,
  `ops/effects.py`, `tests/unit/test_view_scopes.py`.
- **Acceptance test:** `tests/unit/test_view_scopes.py` asserts, per View, that `SCOPE` equals the
  table row AND matches the View's actual disposition (MirrorView/EffectView `tier==STRUCTURAL`; the
  three others `STATIC_GUARD`; all five `W_Σ==0`, `P==READ`; MirrorView/Ref/Temporal/Ops
  `W_world==NONE`; EffectView `W_world==world_reach(ceiling)`; TemporalView carries `D` in E, the
  others do not). **Every pre-existing View test file passes UNMODIFIED** (the bit-identical-reads
  proof — run the full existing View suites and confirm green with no edits to them).
- **Falsifier:** any existing View test requires modification to stay green (a read path changed —
  the retrofit overreached); OR a declared `SCOPE` disagrees with the View's real disposition (e.g.
  EffectView's `SCOPE.tier` is not STRUCTURAL).
- **Invariant(s):** bit-identical reads (the whole-plan falsifier); ops→core dependency direction
  (§3 Q6); Views stay frozen, read-only, model-free.
- **Touches stored data?** No.  **Depends on:** Items 1, 2.

### Item 4 — (independently approvable) Inv vs Rate(κ) result markers + the CoherenceReport audit
- **Objective:** the `Inv` / `Rate(κ)` result-typing markers + **Rule CLOCK** (`q : s → Rate(κ)`
  requires `s.time.clock == κ`; a Rate carries its clock, never a bare number), and an audit test that
  `CoherenceReport` is `Inv` (holds a count + two anchors, performs no division). Lands the distinction
  *ahead of need* (§2.3) — no Rate instrument is built (R1 velocity is `dn-velocity-instruments`).
- **Files:** `core/scope.py` (the markers + Rule CLOCK), `tests/unit/test_scope.py` (Rule CLOCK test +
  the CoherenceReport-is-Inv audit).
- **Acceptance test:** Rule CLOCK rejects a `Rate(κ')` result requested under a scope whose
  `time.clock != κ'`; the audit imports `CoherenceReport` and asserts its fields are count/anchor/bool
  only (no ratio field) — structurally, so it stays true as the report evolves.
- **Falsifier:** a `Rate` value can be constructed without a clock in its type (the distinction is
  cosmetic, not enforced); OR the audit passes while `CoherenceReport` actually divides somewhere.
- **Invariant(s):** the A7 apophenia guard (a drift *rate* off an unacknowledged clock is caught one
  type earlier) — the reason this item earns its place; no behavior change to `CoherenceReport`.
- **Touches stored data?** No.  **Depends on:** Item 1. **The one deferrable item** — approvable/droppable
  independently at `proposed → ready` (park to the R1 velocity build if the owner prefers, §11 CS-f-adjacent).

## 8. Math carried explicitly

- **The scope lattice `(Σ, E, T, A)`** — *measures:* a capability as a point in a finite lattice, so
  "less authority than" is `⊑` and "safe composition of two grants" is `meet`. *valid when:* each
  component is itself a lattice (Σ a finite distributive lattice of forest downsets; E = 2^{F,D}; A a
  product of chains) and `meet`/`join` are componentwise — THEN the product is a lattice and the laws
  hold. *fails its keep if:* a law test (Item 2) exhibits a concrete non-idempotent/non-associative
  witness, or `⊑` disagrees with `meet` — the object is then not a lattice and the "safe composition"
  reading is unearned.
- **T as a PARTIAL meet-semilattice** — *measures:* whether two time-scopes have a well-defined
  common refinement (an honest "cut across two clocks"). *valid when:* the two share a materialized
  clock (same clock → intersect windows). *fails its keep if:* it ever returns a scope for a
  cross-clock pair whose only common refinement is the unmaterialized `N` — that would be a silent
  guess where the note demands a constructor error (the honesty the partiality exists to preserve).
- **Firewalls as order-ideals** — *measures:* admissibility as one algebraic test `s ⊓ ι = ⊥` instead
  of a per-query re-check; the grantable lattice is the ideal-quotient. *valid when:* each firewall is
  genuinely downward-closed (an ideal). *fails its keep if:* a grant that meets an applicable ideal
  non-trivially is still admitted (the ideal wasn't subtracted) — the firewall leaked.
- **The clock poset** — *measures:* monotone coarsenings of the ledger causal order (N ⪰ N_s;
  N ⪰ commit ⪰ distinct-snapshot; wall exogenous). *valid when:* the order is a genuine coarsening
  (finer clock refines coarser). *fails its keep if:* `common_refinement` returns a clock that is not
  ⪰-below both inputs — the poset edges are wrong.

## 9. Non-goals

- **No enforcement wiring into any live caller.** `req(verb) ⊑ s_granted` is *expressible and tested*;
  no read path, no `factory.grant`, no request handler gains a runtime scope check. This is the pure
  typing layer — the whole-plan falsifier is bit-identical reads.
- **No materialized global event clock `N`** (CS-a) — clocks are *named*; N stays parked, so
  cross-clock meets are honestly partial (constructor error). No store gains a column.
- **No scope declarations for ObservedView / DreamsView** — not the note's five; a later unit designs
  their scope (§11).
- **No sensor write-dual retrofit** (`(read, 1, NONE)`) — the sensors stay untouched; widening into
  the projection path is CS-c territory (§11).
- **No antichain / genuinely-partial causal machinery** (CS-b) — all strata factor through commit /
  per-doc chains; the consistent cut is the commit SHA (SLICE rule), specified but the general
  antichain type is uninhabited and not built.
- **No budget axis, no dependent `W_Σ` type, no diamond interval semantics, no Rate re-binning**
  (CS-c…CS-f, all parked in the note).

## 10. Stop-and-raise conditions

- `core/scope.py` cannot be authored without importing from `ops/`/`edge/`/a store → **STOP, file a
  `codebase` finding** (§3 Q6): the layering must not invert to make the `WorldReach` map convenient;
  the bridge belongs ops-side.
- Adding a `SCOPE` constant forces an edit to a View's read/factory body to stay green → **STOP, file
  a `codebase` finding**: the retrofit must be a pure additive annotation; if it can't be, the "pure
  typing layer" premise is wrong and needs re-graduation, not a workaround.
- A lattice law fails on a real witness (Item 2) → this is the test working: **record the witness,
  file a `math` finding**, do NOT weaken the law to green the test.
- The plan does not fit one session (the algebra + five retrofits + property tests overrun context) →
  **file a `spec-defect` finding and PARK** — the orchestrator re-graduates the split; a builder never
  re-splits mid-session.
- Any blessing flip (`proposed→ready`, `draft→ratified`) → **must not**; the builder has no blessing
  capability.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Materialized global event clock `N` (CS-a) | none — cross-clock meets are partial (constructor error) | eager N (rejected: no consumer; premature store change) | a consumer needs cross-stratum event-anchoring (φ_coh, event-anchored coherence) |
| Wire `minted = meet(parent, template)` into `factory.grant` | law expressible + tested only; `factory.grant` untouched | wire now (rejected: behavior change to the minting path — not a typing layer) | a second write-scoped client class is minted, OR the delegation law is promoted to a runtime gate |
| Antichain machinery for genuinely-partial causal order (CS-b) | specified, uninhabited (all strata factor through commit / per-doc chains) | build the antichain type now (rejected: no inhabitant) | a stratum ships whose store shares no coordinate with commit |
| ObservedView / DreamsView scope declarations | out of scope — the note's five only | declare all seven now (rejected: their scope isn't designed in `dn-capability-scope`) | the note (or a successor) designs ObservedView/DreamsView scope |
| Sensor write-dual `(read, 1, NONE)` retrofit (CS-c) | parked — sensors untouched | retrofit sensors now (rejected: widens blast radius into the projection path) | a second write-scoped client class is minted |
| Inv/Rate markers in THIS plan (Item 4) | included, but independently approvable | defer to the R1 velocity build (acceptable — the first Rate customer is `dn-velocity-instruments`) | owner drops Item 4 at `proposed→ready` ⇒ it rides the velocity plan instead |

## 12. Dependency & ordering summary

Blast-radius order: **Item 1** (new pure-core module — lowest radius, touches no existing code) →
**Item 2** (property tests over it) → **Item 3** (the five View retrofits + ops bridge — the ONLY
items touching existing code, highest radius) → **Item 4** (Inv/Rate markers — independently
approvable, the deferrable one). All within `core/scope.py` + two new test files + five one-line View
edits → **one session, not parallel.** `depends_on: []`. Model **opus** (deterministic algebra over a
ratified, fully-specified design — no fable, no xhigh).

**Cross-plan:** this plan is the typing substrate the note's §3 Consequences 2–4 consume — the
`delegate`-skill minting law becomes checkable (Consequence 2, but wiring parked here §11); future
instruments declare `Inv`/`Rate(κ)` at graduation (Consequence 3, the R1 velocity in
`dn-velocity-instruments` is the first `Rate` customer and MUST land clock-declared); the post-reset
fable geometry units consume T's clock machinery (Consequence 4). None of those is gated ON this plan
building — they consume its *vocabulary* at their own graduation. Recorded in `docs/PARKING-LOT.md`.
