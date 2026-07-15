---
type: design-note
id: dn-capability-scope
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only # nothing built; the five Views exist but carry no explicit scope type
created: 2026-07-15
updated: 2026-07-15
links:
  - docs/brainstorms/cq-scope-fable-pass.md # THE WARRANT — the 2026-07-15 fable pass (grades + derivations)
  - docs/design-notes/core-query-protocol.md # §2.1 the C2 seed this note completes; §2.2 the modes typed here
  - docs/brainstorms/temporal-clocks-and-strata.md # the owner-directed T-dimension warrant (read in full)
  - docs/design-notes/temporal-retrieval-algebra.md # §2.2 π_active/σ_*/σ^* — T's evaluation regimes
  - docs/brainstorms/edge-dynamics-lane-b-fable-pass.md # C2/C3 (the seed capsules)
  - docs/design-notes/supersession-lifecycle.md # §4A op-seq — the causal spine every clock coarsens
  - docs/design-notes/observed-data-and-the-assistant-tier.md # the mirror firewall, here an ideal
  - docs/design-notes/hands-and-the-effector-layer.md # the blast-radius chain W_world grades over
supersedes: null
superseded_by: null
warrant: docs/brainstorms/cq-scope-fable-pass.md
---

# The capability-scope algebra (`CQ-scope`) — the unified query language, formalized

> Composed at **fable** (`claude-fable-5`, 2026-07-15, on usage tokens — the owner's directed
> lead unit) directly from the same session's rigorous pass
> (`docs/brainstorms/cq-scope-fable-pass.md`); the brainstorm→design step's fable guard is
> satisfied *in-session*. This note states the decisions; derivations, grades, and rejected
> alternatives live in the pass. Ratification is a hand edit by the owner — no command performs
> it, `gate-guard` denies any agent attempt, and `/graduate` refuses this note until
> `status: ratified`.

## 1. Purpose and scope

`dn-core-query-protocol` §2.1 decided that every core-reader is a capability-scoped client of one
protocol and seeded the scope grammar (`s = (Σ, E, T, A)`, a bounded lattice — capsule C2). Its
§1.3 was explicit that the *formal type system* — what a scope **is**, how it composes, how it
enforces the boundary — remained fable-grade work. This note is that work. It decides:

1. **The four components, made well-posed (§2.1):** Σ as the stratum-refinement lattice (not a
   powerset); E unchanged; **T as a clock-plus-window** (the owner-directed sharpening from
   `temporal-clocks-and-strata.md`); A as a product of three chains (the "write" rung split).
2. **The composition laws (§2.2):** componentwise meet/join; T's meets partial-by-honesty; the
   SLICE rule for cross-stratum instants; firewalls as ideals; enforcement tier as an annotation.
3. **The result typing (§2.3):** `Inv` vs `Rate(κ)` — reparametrization-invariance as a
   compile-time distinction.
4. **The query language (§2.4):** mode as a corollary of scope; the five built Views as the
   inhabitation proof.

**Out of scope:** the retrieval *mathematics* (`dn-temporal-retrieval-algebra` is the math home);
the locally-clocked superconnection and velocity-conformal geometry (post-reset fable units —
nothing here forecloses them); any build (follows ratification → `/graduate`).

## 2. Principles / decision

### 2.1 The scope object

A scope is `s = (Σ, E, T, A)`:

- **Σ — stratum scope.** A downward-closed subset of the **refinement forest** R: base strata
  (mirror, curated, observed, ops, reference, interpreted, world) with refinement predicates
  below them — `reference_repo ⊂ reference` (the C1 predicate) and `mirror_authored ⊂ mirror`
  (the π_MR predicate) are *elements*, not annotations. Finite distributive lattice. The
  foundation denylist 𝔇 is an order-ideal subtracted from the top: **⊤_Σ = R ∖ 𝔇** — even the
  fullest grant structurally excludes `CONSTITUTION.md` / `eval/golden/**`.
- **E — edge-class scope.** `E ⊆ {F, D}` (fibers; dispositional). Unchanged from the seed.
- **T — time scope = (clock κ, window W).** A **clock** is a monotone coarsening
  `p_κ : Ev → I_κ` of the append-only ledger's causal order (the op-seq spine). The clock
  hierarchy: global event clock **N** (finest; **not yet materialized — parked**) ⪰ per-stratum
  **N_s** ⪰ nothing finer; N ⪰ **commit** (a commit is a *range* of N, not a tick) ⪰
  **distinct-snapshot**; wall-time is an exogenous labeling, not an event clock. A **window** is
  `pt(a)`, `[a,b]`, or `∗`. **The anchor is first-class**: `now = (κ, pt(latest))`,
  `ledger = (N, ∗)`. Evaluation regimes are part of T's semantics: a point window applies
  `π_active(anchor)` iff `D ∉ E` (the TRA §2.2 ambient-default ruling, now anchor-indexed); an
  interval window evaluates `σ_*`/`σ^*` transports between endpoint slices; `(N, ∗)` is the
  dilation space, uncompressed.
- **A — authority.** `A = P × W_Σ × W_world`, a product of three chains:
  `P ∈ {read < read+propose}` (the advisory ladder — non-negotiable #3);
  `W_Σ ∈ {0 < 1}` (projection-write into the scoped strata — the sensor dual);
  `W_world` = the effector blast-radius chain (`NONE < SENSING < …`), EffectView's ceiling ε.
  **The seed's single "write" rung conflated sensor projection and effector mutation** — two
  capabilities the architecture already separates structurally (#1/#2: a sensor has no world
  reach, the executor no store reach); the product repairs the conflation. Track G's standing
  fact — max reachable effector tier is NONE — is the lattice statement
  `⊤_deployed.W_world = NONE`.

### 2.2 Composition

- **Meet** (componentwise; Σ∩, E∩, T per below, A min per chain) is **safe composition**: a
  delegated agent receives `meet(parent, template)`. Monotone delegation — you cannot delegate
  more than you hold — **is** non-negotiable #6, one statement (unchanged from C2).
- **Join** is a widening, grantable only by an authority already holding the join (unchanged).
- **T-meet:** same clock → intersect windows. Different clocks → pull both windows back to a
  **materialized** common refinement (canonically N). Until N exists, T is honestly a **partial
  meet-semilattice**: a cross-clock meet with no shared materialized clock is a **constructor
  error** ("no common clock"), never a silent guess.
- **The SLICE rule.** A scope with `|Σ| > 1` and a point window must carry an explicit
  **consistent cut** (vector-clock timestamp / causal-set antichain); bare "now" is well-typed
  only single-stratum. **The commit SHA is the consistent cut for repo-backed strata** — this
  retro-explains why bp-035/037 route both Views through one `_resolve_default_commit`: the
  slice discipline was discovered empirically; the type now enforces it.
- **Firewalls are ideals.** Each firewall (mirror payload for non-exempt clients; 𝔇 always) is
  an order-ideal ι; a grant is admissible for client class c iff `s ⊓ ι = ⊥` for every ι
  applicable to c. The grantable lattice is the ideal-quotient — firewalls are subtracted from
  the space of scopes, not re-checked per query.
- **Enforcement tier is an annotation, never a lattice element.** Ladder:
  `structural ≻ static+guard ≻ convention`; composition takes the **min tier along the
  construction chain**. This stops a convention-tier grant laundering through a structural
  wrapper. (MirrorView/EffectView are structural; OpsView/ReferenceView/TemporalView are
  static+guard, honestly labelled.)

### 2.3 Result typing — `Inv` vs `Rate(κ)`

Query results are graded by clock-dependence: **`Inv`** (depends only on the window's event set —
counts, sets, booleans: β₁, ‖[d,τ]‖-as-count, connected sets, well-foundedness) vs **`Rate(κ)`**
(a difference quotient against a clock's index — severings per commit, events per wall-second,
velocity `ẇ`). **Rule CLOCK: `q : s → Rate(κ)` requires `s.T.clock = κ`**; a Rate value carries
its clock in its type and is never a bare number. Every built instrument audits as `Inv`
(`CoherenceReport` returns the count plus both anchors and deliberately never divides); the first
`Rate` inhabitant will be the R-ladder velocity (R1). The distinction lands ahead of need — the
failure it forecloses (a drift *rate* read off an unacknowledged clock) is the A7 apophenia
class, caught one type earlier.

### 2.4 The unified query language

A query is a sentence `(verb, s)`; admissibility is `req(verb) ⊑ s_granted`, checked at
construction — ill-scoped sentences are **unrepresentable** (the MirrorView move, made uniform).
**Mode is a corollary of scope, never a flag:** `E={F}` + point window → structural (1a/1b by β);
kernel-carrying Σ → semantic; `D ∈ E` or interval window → temporal with declared direction
(`σ_*`/`σ^*`); point ∧ D∉E ⇒ `π_active(anchor)` ambient; `(N,∗)` ⇒ dilation. The Views inhabit
the type as follows (`[VERIFIED]` in the pass, S7):

| View | Σ | E | T | A | tier |
|---|---|---|---|---|---|
| MirrorView | mirror_authored | — | (projection-event, pt) | (read, 0, NONE) | structural |
| ReferenceView | reference_repo | {F} | (commit, pt) | (read, 0, NONE) | static+guard |
| TemporalView | reference_repo | {F}; +D wellfounded | (commit, pt) · coherence: (commit, [n,n+1]) | (read, 0, NONE) | static+guard |
| OpsView | ops | — | (last-write, pt) | (read, 0, NONE) | static+guard |
| EffectView | world | — | (now, pt) | (read, 0, ε) | structural |

`coherence_to` is the first interval-window sentence (its restrict-to-common IS the interval
semantics' σ-totalization); the sensor is the write-side dual `(read, 1, NONE)` whose projections
*generate* the clocks readers consume.

## 3. Consequences — what this note licenses (on ratification)

1. **One build plan: the scope typing layer.** `core/scope.py` (or `core/query/scope.py` —
   graduating plan pins it): the frozen `Scope` dataclass, the lattice ops (`meet`/`join`/`⊑`),
   the firewall ideals as data, the clock poset with the partial T-meet (constructor error on no
   common clock), and `req()` declarations retrofitted onto the five View constructors. **A pure
   typing layer: zero behavior change to any View — bit-identical reads is the falsifier**,
   alongside lattice property tests (idempotent/commutative/associative/absorption), a
   declared-vs-actual scope guard test per View, cross-clock-meet-raises, and
   delegation-exceeding-parent unrepresentable.
2. **The delegation surface** (`delegate` skill, minted builders) gains a checkable law:
   `minted = meet(parent, template)` — the runtime form of non-negotiable #6.
3. **Future instruments** declare `Inv`/`Rate(κ)` at graduation; the R1 velocity is the first
   `Rate` customer and MUST land clock-declared.
4. **The post-reset fable units** (locally-clocked superconnection; velocity-conformal geometry)
   consume T's clock machinery as their typing substrate; a per-region clock field is a family
   of T-scopes, already expressible.

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| CS-a | materialized global event clock N | none — cross-clock meets partial (constructor error) | a consumer needs cross-stratum event-anchoring (φ_coh, event-anchored coherence) |
| CS-b | antichain machinery for genuinely-partial causal order | specified, uninhabited (all strata factor through commit / per-doc chains) | a stratum ships whose store shares no coordinate with commit |
| CS-c | `W_Σ` as a dependent type (write-authority fused to Σ) | A independent; pairing enforced by construction as today | a second write-scoped client class is minted |
| CS-d | interval semantics across supersession diamonds | linear chains only (inherits TA-c) | measured diamond frequency (TA-c's gate) |
| CS-e | a budget axis (γ^d edge_budget) as a fifth scope component | verb-side, not scope-side | a cross-stratum grounding walk is typed |
| CS-f | Rate re-binning between comparable clocks | always a new measurement (conservative) | a Rate consumer needs cross-clock comparison |

## Cross-references

- `docs/brainstorms/cq-scope-fable-pass.md` — **the warrant**: derivations, grades (S1–S8),
  rejected alternatives, and the external citations flagged `[FROM MEMORY — verify]` (Lamport;
  Chandy–Lamport; Mattern/Fidge; Bombelli–Lee–Meyer–Sorkin) which MUST be verified before a book
  chapter cites this note (external-grounding discipline).
- `docs/design-notes/core-query-protocol.md` §2.1/§2.2 — the seed and the modes; this note is
  its promised type-system completion (§1.3 item 2).
- `docs/brainstorms/temporal-clocks-and-strata.md` — the owner-directed T warrant (clocks,
  per-stratum rates, relativity-of-simultaneity, anchor-as-first-class, Inv/Rate).
- `docs/design-notes/temporal-retrieval-algebra.md` §2.2 — `π_active`/`σ_*`/`σ^*`, T's
  evaluation regimes; §2.3 R5 — the ledger/dilation space `(N,∗)` names.
- code: `core/reference_view.py`, `core/temporal_view.py`, `core/mirror.py`, `core/ops_view.py`,
  `ops/effects.py` (the inhabitants); `core/stores/reference_edges.py` (the commit coordinate);
  `ops/effect_gate.py` (the blast-radius chain).
