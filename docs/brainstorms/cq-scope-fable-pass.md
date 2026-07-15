# cq-scope-fable-pass — the capability-scope type system, formalized

> Fable rigorous pass (`claude-fable-5`, 2026-07-15, run on usage tokens — the owner's directed
> lead unit, roadmap #2). Input contract honored in full: `dn-core-query-protocol` §2.1 (the C2
> bounded-lattice seed), **`temporal-clocks-and-strata.md` read IN FULL** (owner-directed — it is
> load-bearing for the `T` dimension below), and the built View instances
> `core/reference_view.py` / `core/temporal_view.py` (+ `core/mirror.py`, `core/ops_view.py`,
> `ops/effects.py` as the remaining inhabitants). This pass **formalizes** the scope tuple
> `s = (Σ, E, T, A)` into a full type system — the unified query language. Results carry grades
> (`[ESTABLISHED]`/`[DERIVED]`/`[SKETCH]`/`[VERIFIED]`); the design note drafted from this pass
> (`dn-capability-scope`) states the decisions and cites here for the reasoning.

## 2026-07-15T18:03:40Z — the pass

### S1. The scope object is a product of four lattices — but two of the four needed repair

The C2 seed (`edge-dynamics-lane-b-fable-pass.md` §C2) gave `s = (Σ, E, T, A)` with componentwise
meet/join and called it a bounded lattice. That is correct **only after** `Σ` and `T` are given
real structure (the seed's `Σ ⊆ Strata` powerset and `T ∈ {now, [t₀,t₁], ledger}` tokens do not
support the claims already made of them — C1's `reference_repo ⊂ reference` is not an element of a
powerset of stratum *names*, and `now ∩ [t₀,t₁]` is undefined on opaque tokens). The repairs:

- **Σ — the stratum-refinement lattice, not a powerset.** `[DERIVED]` Let the *refinement forest*
  R be the poset of stratum predicates: base strata (mirror, curated, observed, ops, reference,
  interpreted, world) as roots, refinements below them (`reference_repo ⊂ reference` = both
  endpoints repo-derivable, never vault-backed — the C1 predicate; `mirror_authored ⊂ mirror` =
  provenance ∈ MIRROR_READABLE — the π_MR predicate). **Σ ranges over downward-closed subsets of
  R** (finite, so this is a finite distributive lattice; meet = ∩, join = ∪). C1 and the mirror
  firewall stop being prose annotations and become *elements*. The foundation denylist 𝔇
  (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`) is an **order-ideal subtracted from the
  top**: the grantable top is ⊤_Σ = R ∖ 𝔇 — "even ⊤ honors the denylist" is now a lattice fact,
  not a footnote.
- **E — unchanged.** `2^{F,D}`, the four-element Boolean lattice. Correct as seeded.
- **T — repaired in S2–S3** (the owner-directed sharpening; the bulk of this pass).
- **A — repaired in S5** (the seed's 3-chain conflates two incomparable write capabilities).

**Theorem S1 (well-posedness).** `[DERIVED — standard order theory]` With Σ a finite distributive
lattice, E Boolean, T a (partial) meet-semilattice per S2, and A a product of chains per S5, the
product `Scope = Σ × E × T × A` under componentwise order is a bounded lattice wherever T's meets
are defined; ⊥ = (∅, ∅, ⊥_T, ⊥_A), ⊤ = (R∖𝔇, {F,D}, (N,∗), ⊤_A). Meet = safe composition (a
delegated agent receives `meet(parent, template)` — monotone delegation, non-negotiable #6, per
C2, unchanged); join = widening, grantable only by a holder of the join (unchanged).

### S2. T is a clock plus a window — clocks are monotone coarsenings of the ledger order

`[DERIVED; the temporal-clocks thread made formal]` The brainstorm's four decisions land as:

- **A clock** is a pair `κ = (I_κ, p_κ)`: an index set `I_κ` and a **monotone surjection**
  `p_κ : Ev → I_κ` from the event trajectory (the append-only ledger's causal order — the op-seq
  spine, `supersession-lifecycle` §4A; the Sz.-Nagy dilation space, TRA §2.3 R5). Clocks are
  ordered by **refinement**: κ₁ ⪰ κ₂ iff p_κ₂ factors through p_κ₁ by a monotone map. The known
  clocks form a genuine hierarchy under this order, all coarsenings of the (not-yet-materialized)
  global event clock **N** = id:
  - **N** (ledger position) ⪰ **N_s** (per-stratum count: `p(e) = |{e′ ≤ e : e′ touches s}|` —
    total, monotone, ticks only on s-events) ⪰ nothing finer per-stratum;
  - **N** ⪰ **commit** (`p(e)` = last commit at-or-before e; a commit is a **range** of N, not a
    tick — the grain caveat) ⪰ **distinct-snapshot** (dedup byte-identical citation states —
    bp-038's live-probe clock: 6 commits, 1 snapshot);
  - **wall-time** is an *exogenous labeling*, not an event clock — admissible as a coordinate,
    load-bearing only for physical rates (S4).
- **A time-scope** is `T = (κ, W)` with `W ∈ {pt(a)} ∪ {[a,b]} ∪ {∗}` a window on I_κ. Semantics:
  the event set `p_κ⁻¹(W)`, **plus the evaluation regime** — a point window evaluates in the
  active view at that point (`π_active(a)` ambient iff `D ∉ E` — the A2/C3 ruling, now indexed by
  the anchor); an interval window evaluates transports (`σ_*`/`σ^*`) between its endpoint slices;
  `(N, ∗)` is the dilation space, no compression. The seed's tokens are recovered as
  `now = (κ, pt(latest))`, `window = (κ, [a,b])`, `ledger = (N, ∗)` — **the anchor is first-class**
  (temporal-clocks decision 3): two scopes at different anchors are different scopes.
- **T-meet.** Same clock: intersect windows. **Different clocks: pull back to a common
  refinement** — `T₁ ⊓ T₂ = (κ*, p₁⁻¹(W₁) ∩ p₂⁻¹(W₂))` computed in any materialized κ* refining
  both (canonically N). **Theorem S2.** `[DERIVED]` T is a meet-semilattice **iff** the clock
  poset has materialized common refinements for the clocks in use. Today N is *parked* (no
  unified index exists — version_seq is per-doc, RunLedger per-run, op-seq supersession-only), so
  T is a **partial** meet-semilattice: cross-clock meets are defined exactly when both scopes
  share a clock or one clock factors through the other. **Typing consequence: a cross-clock meet
  with no materialized common refinement is a CONSTRUCTOR ERROR ("no common clock"), never a
  silent guess.** The type system is honest about what the store layer can actually anchor.

### S3. Relativity of simultaneity — the slice rule, and why commit-anchoring was already right

`[DERIVED; ESTABLISHED frames flagged for verification per external-grounding]`

- **No canonical cross-stratum "now."** Per-stratum clocks tick at different rates
  (`dN_s/dN < 1`, stratum-specific), so the family of per-stratum latest positions is not, in
  general, certified consistent by anything — reading two stores "now" is two non-atomic reads.
  This is the classical **distributed-snapshot problem**: absent a materialized total order, a
  cross-stratum instant must be a **consistent cut** (a global state no in-flight causality
  straddles), i.e. the causal-set **maximal antichain** of the temporal-clocks thread. The
  per-stratum family `{N_s}` is literally a **vector clock**, and a consistent cut is a vector
  timestamp. `[ESTABLISHED — from memory, VERIFY: Lamport 1978; Chandy–Lamport 1985 (distributed
  snapshots); Mattern 1989 / Fidge 1988 (vector clocks); Bombelli–Lee–Meyer–Sorkin 1987 (causal
  sets).]`
- **Typing rule (SLICE).** A scope with `|Σ| > 1` and a point window **must carry the cut
  explicitly**: `T = (κ_shared, pt(cut))` where κ_shared is a clock every stratum in Σ factors
  through, or a materialized antichain id. Bare "now" is well-typed only for single-stratum
  scopes. `[DERIVED]`
- **The commit SHA is a consistent cut for repo-backed strata.** A commit snapshots the whole
  repo atomically, so anchoring every View of a multi-stratum read at ONE commit yields a
  consistent slice — and two Views resolving "now" independently may straddle a cut. **This is
  exactly why bp-035/037 made `_resolve_default_commit` the single shared resolver** ("so the two
  Views agree on what 'now' means" — `temporal_view.py:26`): the slice rule was discovered
  empirically before it was typed. The type system now *explains* the built discipline instead of
  merely permitting it. `[VERIFIED against core/reference_view.py:111–126,
  core/temporal_view.py:168–182]`
- **Remark (the reader/writer duality).** Readers *consume* T; write-scoped clients *generate*
  it — a sensor's projections ARE the ticks of the clocks its stratum carries (its `commit_sha`
  stamps mint the index ReferenceView anchors on). The clock structure is not imposed on the
  system; it is generated by its write-scoped agents. `[DERIVED — a remark, but it is why T and A
  are not independent axes at ⊤: holding write on Σ means minting T on Σ.]`

### S4. Reparametrization-invariant vs rate-dependent is a RESULT typing, not a scope field

`[DERIVED — new; temporal-clocks decision 4 made formal]` The typing distinction the brainstorm
asked the algebra to carry lands on the **query result type**, not on the scope tuple:

- `Inv` — reparametrization-invariant: the value depends only on the event set `p_κ⁻¹(W)`, not on
  the clock through which it was named (counts, sets, booleans: β₁, ‖[d,τ]‖ as a count, the
  severed set, connected_set, well-foundedness). An Inv query is well-typed under any clock whose
  window pulls back to the same events.
- `Rate(κ)` — clock-indexed: a difference quotient against I_κ (severings *per commit*, events
  *per wall-second* — the J(x) field; velocity `ẇ`). **Typing rule (CLOCK): `q : s → Rate(κ)`
  requires `s.T.clock = κ`** (or an explicitly declared re-binning to another clock); a Rate
  value carries its clock in its type and is never a bare number. "Velocity is dW/d(which
  clock?)" is now a compile-time obligation.
- **Audit of the built surface:** every shipped instrument is Inv — `CoherenceReport` returns the
  count + both anchors and deliberately *never* a rate (bp-038's §3 Q4 "node-delta is a separate
  axis" is, in this light, the refusal to divide by an undeclared clock). The first Rate customer
  is the R-ladder velocity (R1, parked on sample depth). The type system lands **ahead of its
  first Rate inhabitant, by design** — the failure mode it forecloses (a drift *rate* read off an
  unacknowledged clock) is the apophenia engine A7 guards against, one type earlier.
  `[VERIFIED — grep of core/temporal_view.py, core/reference_view.py return types]`

### S5. A is not a chain — "write" conflates two incomparable capabilities

`[DERIVED]` The seed's `A ∈ {read < read+propose < write}` puts the sensor's store-projection and
the effector's world-mutation on one rung. The built system already refutes the conflation
structurally: a sensor holds no world reach (core has zero egress, non-negotiable #1); the
effector executor holds no store reach (`edge/` never reads the vault, #2; Track G's executor is
JIT-credentialed at the world boundary only). Neither ≤ the other. The repair:

- `A = P × W_Σ × W_world` — a **product of three chains**: `P ∈ {read < read+propose}` (the
  advisory ladder — "the model advises," #3); `W_Σ ∈ {0 < 1}` (projection-write into the scoped
  strata — the sensor dual; meaningful only relative to Σ, see the parked dependent-type note);
  `W_world` = the **blast-radius chain** of the effector gate (`NONE < SENSING < …` — EffectView's
  ceiling ε, `Effects_{β≤ε}` as a type). Product of chains ⇒ distributive lattice; min/max
  componentwise. `[DERIVED]`
- The seed's rungs embed: `read = (read, 0, NONE)`, `read+propose = (propose, 0, NONE)`, the old
  "write" splits into `(·, 1, NONE)` (sensor) vs `(·, 0, ε)` (effector). **Track G's standing
  fact — max reachable effector tier is NONE (finding-0011) — is the single lattice statement
  `⊤_deployed.W_world = NONE`.** `[VERIFIED against MEMORY/Track G; ops/effects.py:29,52]`
- Instances: sensor `(read, 1, NONE)`; orchestrator `(read+propose, 1_scoped, NONE)`; Ambassador
  `(read+propose, 0, NONE)`; effector executor `(read, 0, ε-gated)`.

### S6. Firewalls are ideals; enforcement tier is an annotation, never a lattice element

- **Ideals (completes C2).** `[DERIVED]` Each firewall is an order-ideal ι in Scope (mirror
  payload for non-introspective-exempt clients; 𝔇 always). Admissibility of granted scope s for
  client class c: `s ⊓ ι = ⊥` for every ι applicable to c. The grantable lattice is the
  ideal-quotient — firewalls are *subtracted from the space of scopes*, not checked per query.
- **Enforcement tier.** `[DERIVED — design ruling]` Each scope *instance* carries an assurance
  annotation from the ladder `structural ≻ static+guard ≻ convention` (MirrorView/EffectView are
  structural — the wrong state is unrepresentable; OpsView/ReferenceView/TemporalView are
  static+guard — typed read closures + a no-mutator integrity test, honestly labelled weaker,
  `ops_view.py:9–14`). The tier is **not** a lattice component: meets don't strengthen assurance,
  so composition law = **min tier along the construction chain**. Keeping it an annotation stops
  the type system from laundering a convention-tier grant through a structural-tier wrapper.

### S7. The unified query language, assembled

`[DERIVED — the synthesis]` A **query** is a sentence `(verb, s)` with a required scope
`req(verb)`; admissibility is `req(verb) ⊑ s_granted`, checked at construction (ill-scoped
sentences unrepresentable — the MirrorView move, now uniform). **Mode is a corollary of scope,
never a flag:** `E = {F}`, point window → mode 1 (1a/1b by β); kernel-carrying Σ → mode 2;
`D ∈ E` or interval window → mode 3 with direction ∈ {σ_*, σ^*}; point window ∧ D∉E ⇒ π_active(a)
ambient; `(N, ∗)` ⇒ dilation space. The five Views are the inhabitation proof:

| View | Σ | E | T | A | tier |
|---|---|---|---|---|---|
| MirrorView | mirror_authored | — | (projection-event, pt) | (read,0,NONE) | structural |
| ReferenceView | reference_repo | {F} | (commit, pt(anchor)) | (read,0,NONE) | static+guard |
| TemporalView | reference_repo | {F}; +D in wellfounded | (commit, pt) · coherence_to: (commit, [n,n+1]) | (read,0,NONE) | static+guard |
| OpsView | ops | — | (last-write, pt) | (read,0,NONE) | static+guard |
| EffectView | world | — | (now, pt) | (read,0,ε) | structural |

`coherence_to` is the system's first genuinely interval-window sentence — its restrict-to-common
is exactly the σ-totalization the interval semantics requires, computed before the type existed.
`[VERIFIED against core/temporal_view.py:138–165]`

### S8. What the pass does NOT settle (honest edges)

- **The materialized global N** stays parked (temporal-clocks capsule 1) — the type admits it;
  no consumer yet forces the store write. Cross-clock meets stay partial until then.
- **Genuinely-partial causal order** (independent stores with no shared coordinate): the
  antichain machinery is specified but has no inhabitant — every current stratum factors through
  commit or a per-doc chain. Parked with N.
- **`W_Σ`'s Σ-dependence** is a dependent type (write-authority *on which strata* fuses A with
  Σ). v1 keeps A independent and lets construction enforce the pairing, as today. Parked with a
  named re-entry: a second write-scoped client class.
- **Diamond/merge windows** (an interval crossing a supersession merge) inherit TA-c's sketch
  status — interval semantics is proven on linear chains only.
- The **locally-clocked superconnection** and **velocity-conformal geometry** threads are
  enriching context, deliberately NOT folded in — they are the post-reset fable units
  (PARKING-LOT), and nothing here forecloses them: a per-region clock field is a *family* of
  T-scopes, which S2's partial-meet honesty already accommodates.

```capsule
topic: cq-scope-fable-pass
date: 2026-07-15

decisions:
  - Scope = Σ × E × T × A as a bounded lattice made WELL-POSED: Σ = downward-closed sets of the
    stratum-refinement forest (C1/π_MR as elements; denylist as an ideal subtracted from ⊤);
    E = 2^{F,D} unchanged; T repaired (clock+window); A repaired (product of three chains).
  - T = (clock, window): a clock is a monotone coarsening of the ledger's causal order (N ⪰ N_s,
    N ⪰ commit ⪰ distinct-snapshot; wall-time exogenous); windows pt/[a,b]/∗; anchor first-class;
    point-window ⇒ π_active(anchor) ambient iff D∉E; (N,∗) = dilation space. Cross-clock meets
    pull back to a materialized common refinement or are a CONSTRUCTOR ERROR — T is honestly a
    partial meet-semilattice until the global N materializes (parked).
  - SLICE rule: multi-stratum point scopes must carry an explicit consistent cut (vector-clock /
    antichain form); bare "now" is single-stratum only. Commit SHA = the consistent cut for
    repo-backed strata — retro-explains the shared _resolve_default_commit discipline (bp-035/037).
  - Inv vs Rate(κ) is a RESULT-type grading with rule CLOCK (a Rate is well-typed only under its
    declared clock); every built instrument audits as Inv; first Rate customer = R1 velocity.
  - A = {read<propose} × {store-write} × {world-write blast-radius}: the old "write" rung
    conflated sensor projection and effector mutation, which the architecture already separates;
    Track G's max-tier-NONE is the lattice fact ⊤_deployed.W_world = NONE.
  - Firewalls = ideals (grantable lattice = ideal-quotient); enforcement tier = an annotation
    with min-tier composition, never a lattice element.
  - Query language: sentence (verb, s), admissible iff req(verb) ⊑ granted; mode is a corollary
    of (E, T), never a flag; the five Views are the inhabitation proof (table in S7).

parked:
  - decision: materialized global event index N (unchanged from temporal-clocks)
    default: none; cross-clock meets partial (constructor error absent a shared clock)
    re_entry: a consumer needs cross-stratum event-anchoring (event-anchored coherence, φ_coh)
  - decision: antichain machinery for genuinely-partial causal order
    default: specified, uninhabited (all strata factor through commit or per-doc chains)
    re_entry: a stratum ships whose store shares no coordinate with commit
  - decision: W_Σ as a dependent type (write-authority fused with Σ)
    default: A independent of Σ; the pairing enforced by construction as today
    re_entry: a second write-scoped client class is minted
  - decision: interval semantics across supersession diamonds
    default: linear chains only (inherits TA-c)
    re_entry: measured diamond frequency (TA-c's gate)

open_questions:
  - Should the scope carry a BUDGET axis (the γ^d edge_budget as a fifth component), or is budget
    a property of the verb? (v1: verb-side; revisit when a cross-stratum grounding walk is typed.)
  - Is the enforcement-tier min-law too pessimistic for structural-wrapping-structural chains?
  - Does Rate(κ) need a declared re-binning functor between comparable clocks, or is re-binning
    always a new measurement? (v1: new measurement — conservative.)

next_steps:
  - dn-capability-scope drafted THIS session from this pass (status draft, owner ratifies).
  - After ratification, /graduate: one plan — core/scope.py (the Scope type, lattice ops, ideals
    as data, req() on View constructors) + property tests; a pure typing layer, zero behavior
    change to any View (bit-identical reads is the falsifier).
  - VERIFY the flagged external citations (Lamport; Chandy–Lamport; Mattern/Fidge; BLMS) against
    primary sources before the note is cited by a book chapter (external-grounding discipline).

references:
  - docs/design-notes/core-query-protocol.md  # §2.1 the C2 seed this completes
  - docs/brainstorms/edge-dynamics-lane-b-fable-pass.md  # C2/C3 (the seed capsules)
  - docs/brainstorms/temporal-clocks-and-strata.md  # the owner-directed T-dimension warrant
  - docs/design-notes/temporal-retrieval-algebra.md  # §2.2 π_active/σ_* (T's evaluation regimes)
  - core/reference_view.py · core/temporal_view.py · core/mirror.py · core/ops_view.py ·
    ops/effects.py  # the inhabitants
  - docs/design-notes/supersession-lifecycle.md  # §4A op-seq (the causal spine T coarsens)
  - external [FROM MEMORY — verify]: Lamport 1978; Chandy–Lamport 1985; Mattern 1989 / Fidge
    1988; Bombelli–Lee–Meyer–Sorkin 1987.
```
