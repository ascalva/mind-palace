---
type: design-note
id: dn-synchronic-diachronic-dreamer
status: ratified            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-20
updated: 2026-07-20
links:
  - docs/brainstorms/synchronic-diachronic-dreamer.md   # THE WARRANT — the owner's four ingredients + the laziness addendum (a requirement, not an optimization)
  - docs/brainstorms/hypothetical-subspace.md           # the counterfactual seed — FOLDED IN here (§2.6/§2.7); its capsule's open questions answered
  - docs/brainstorms/graph-at-a-past-cut.md             # the temporal-read substrate (D1–D9) — honored, consumed, NOT absorbed (its memory-curve family keeps its own graduation)
  - docs/brainstorms/cross-strata-and-multiscale-dreamers.md
  - docs/brainstorms/dreamer-and-graph-direction.md     # the seed question §2.8 answers (mode vs distinct interpreter: neither — a grant value)
  - docs/brainstorms/temporal-clocks-and-strata.md      # dreaming-is-necessary (two prime movers); the clock frame
  - docs/design-notes/inner-outer-core.md               # DRAFT (v2 + S1) — the ring vocabulary; instrument purity is PER-INSTRUMENT (§2.3 here)
  - docs/design-notes/agent-taxonomy.md                 # RATIFIED — role = scope signature; this note is its worked example at full depth
  - docs/design-notes/capability-scope-algebra.md       # RATIFIED — the (Σ,E,T,A) lattice every dispatch here is a point of
  - docs/design-notes/cross-strata-dreamer.md           # RATIFIED — the per-scope-grant regime + G0–G4; EXTENDED (§2.10)
  - docs/design-notes/sigma-fibers-and-multiscale-dreaming.md  # RATIFIED — the axis table this completes; EXTENDED (§2.10)
  - docs/design-notes/connectivity-instruments.md       # RATIFIED — the senses (CN-1..7); the attribution law §2.7 generalizes
  - docs/design-notes/global-event-clock.md             # RATIFIED — certified cuts (GC-3, BUILT bp-055) — the anchor substrate
  - docs/design-notes/magnetic-laplacian.md             # RATIFIED — ML-a deferral honored; owner decision 2 (oq-0021) grounded in §2.9
  - docs/design-notes/temporal-retrieval-algebra.md     # RATIFIED — π_active/σ_*/σ^* — the interval-window evaluation semantics
  - docs/design-notes/recursive-dreaming-bounded-by-grounding.md  # EXTENDED — the four safety rules gain a fifth (§2.7 conditioning law)
  - docs/design-notes/dreaming-on-curated-graphs.md     # EXTENDED — R5 re-read as a scope grant (§2.10)
  - docs/design-notes/dream-phase-rnd-charter.md        # EXTENDED — the R&D flag boundary binds every dispatch here (§2.10)
  - docs/findings/finding-0126.md                       # filed by this pass — the diachronic park's stated blocker (certified cuts) is built
supersedes: null
superseded_by: null
warrant: docs/brainstorms/synchronic-diachronic-dreamer.md
---

# The synchronic/diachronic dreamer — scoped dreaming, the algebra as tools, laziness as law

> Composed at **fable** (`claude-fable-5`, 2026-07-20, session-39 dispatched design pass — the
> owner's "likely the last fable pass of the arc"). Filed as `draft`; ratification is an
> owner-only hand edit; `/graduate` refuses this note until `status: ratified`. **Design only; no
> build is authorized by this note.** This is a convergence pass, not a green field: it types the
> dreamer program in machinery that is ratified and largely built, rules explicitly on each of the
> five prior dreamer notes (§2.10), folds the hypothetical-subspace seed in (§2.6–2.7), and
> grounds the open oq-0021 narration decision for the owner to rule at ratification (§2.9).
> Code claims were verified on disk this session (2026-07-20, main tree); ring-membership claims
> cite `dn-inner-outer-core`'s computation at `97c245c`/`658e090` and are honest about its
> draft status.

## 1. Purpose and scope

The owner named four ingredients and one law for the next dreamer track: (1) the **synchronic vs
diachronic** axis — dreaming over the graph at a cut vs over its history; (2) **dreamer scopes** —
dispatch parameterized by the capability-scope algebra (strata, fibers, time/world, instrument
grants); (3) **the algebra as the dreamer's tools** — the dreamer is a *client* of the algebra,
never the algebra; (4) **connectivity instruments as its senses**; and (law) **laziness is a
requirement, not an optimization** — the graph grows in size and time, so evaluation strategy is
first-class design.

This note decides: the dispatch decomposition and the world-parameter verdict (§2.1); the
dispatch record and its enforcement seams (§2.2); the senses, with per-instrument ring honesty
(§2.3); the laziness laws and the lazy-view/capability verdict (§2.4); the store-layout honesty
check for cuts-as-pointers (§2.5); the hypothetical subspace, folded in — where it lives, its TTL
clock, admission/expiry, isolation (§2.6); influence as the perturbation term, and the
conditioning law that stops hypothesis laundering through dream exhaust (§2.7); the diachronic
axis in full with execution parked and a clock-free v1 licensed for design (§2.8); the oq-0021
recommendation (§2.9); and the extend/supersede ruling for each of the five existing dreamer
notes (§2.10).

**Out of scope:** any build (follows ratification → `/graduate`, and nothing here preempts the
already-sequenced lead work — bp-069/070/071 and the inner-outer-core M0/S1 plans); the magnetic
**operator** (ML-a's deferral is ratified and not relitigated — §2.3/§2.9); the memory-curve /
retro-gauge instrument family (`graph-at-a-past-cut` keeps its own graduation; this note consumes
its cut machinery and pins the seam, §2.5); the σ-sweep RUN (oq-0024 — operational, not design;
its readings calibrate §2.8's honest seams but gate nothing here); any change to
`MIRROR_READABLE`, the verdict taxonomy, or any ratified note (all cited, none edited).

## 2. Principles / decision

### 2.0 The DRY audit — what exists, and the four genuinely new things

Per the §2-manifest discipline (owner rule: reuse before re-implement), the machinery this note
rides, verified in code:

| capability | existing home | status |
|---|---|---|
| the scope lattice (Σ, E, T, A), meets/joins/⊑, SLICE, ideals, `Inv`/`Rate(κ)`/`Res(π)` | `core/scope.py` | built |
| the four role constructors + `assert_conforms` (handles ⊑ declared scope) | `core/agent_scope.py` | built |
| the tool-handle ceiling pattern (`scope ∩ MAX` at mint, structural refuse) | `core/factory/roles.py:24-40` | built |
| the View firewall pattern (structural authored-only; `RowSource` seam) | `core/mirror.py:54-101` | built |
| composed assembly — union enters at assembly, math fed unchanged | `core/graph/composed.py` (D3) | built |
| certified cuts — frontier + composed certificates {COMMIT, TROUGH, HANDOFF}, refusal | `core/temporal/spine.py:159-274` (GC-3/bp-055) | built |
| σ*/MST + conductance math | `core/graph/{sigma_star,conductance}.py` (bp-065 home) | built |
| bridge/arc search, helix detector | CN-5/CN-6/CN-7 | ratified design; their own tranche gates (helix uuid-gated) |
| the arrow-aware combinatorial census | Thread-C sweep (TRA §3 item 2 + ML §3 item 2) | licensed, no new license needed |
| σ-persistence (`Res(σ)`), strength-gated surfacing | dn-sigma-fibers FB-1..3 | ratified |
| per-grant harness A/B (per-scope = per-σ machinery) | dn-cross-strata-dreamer owner ruling | ratified |
| digest-keyed derived caching (group-by-digest) | `core/stores/sourceset.py` | built |
| interval-window evaluation semantics (π_active point; σ_*/σ^* endpoint transports) | dn-capability-scope §2.1 / TRA §2.2 | ratified |

**Genuinely new in this note — exactly four things**, each with its warrant: (N1) the
**dispatch record** binding a scope grant to an instrument grant and a budget (§2.2); (N2) the
**materialization boundary** — one evaluator seam where admissibility, cost-refusal, and caching
coincide (§2.4); (N3) the **HYPOTHETICAL stratum** + staging store + TTL semantics (§2.6); (N4)
the **influence/conditioning law** — the perturbation term as both the influence metric and the
taint detector (§2.7). Everything else is composition of the table above.

### 2.1 SD-1 — the world-parameter verdict: one dreamer, no new axis (adopt-refined)

**The candidate unification tested:** are present-read / past-cut read / counterfactual read /
across-cuts four values of ONE "world-parameter" scope axis?

**Verdict: the unification is real, but it is not a new axis — it is a decomposition over the
coordinates the ratified algebra already has.** Introducing a fifth "world" coordinate would
duplicate what `(Σ, T)` already expresses — a DRY violation at the algebra level, the same error
`dn-sigma-fibers` §2.6 caught for σ ("a fifth scope coordinate would be a fictional capability").
The four modes factor exactly:

| mode | Σ (strata) | T-anchor (which cut) | T-window | already typed by |
|---|---|---|---|---|
| present read (synchronic) | granted strata | latest certified cut | `pt(c_now)` | dn-agent-taxonomy §2.1 ("point window at a consistent cut") |
| past-cut read | granted strata | an earlier certified cut | `pt(c)` | GC-3 cuts; `Window.point` is anchor-agnostic (`core/scope.py:248-250`) |
| counterfactual read | granted strata **∪ {HYPOTHETICAL}** (§2.6) | a certified cut ∧ a subspace generation | `pt(c) ∧ gen g` | Σ-side: the overlay changes *what may be seen* — the GC §2.6 capability-visibility test |
| across-cuts (diachronic) | granted strata | — | `[c₁, c₂]` | interval-window semantics (σ_*/σ^* endpoint transports, TRA §2.2; cut-pair windows, GC §2.9-4) |

The decisive instrument is the clock/resolution line already drawn once in
`dn-global-event-clock` §2.6: *does the parameter change what the client may see?* The cut anchor
and the window change **which events** a grant denotes → T-side, scope. The overlay changes
**which rows exist to be seen** → Σ-side, scope. The **gauge** of a past read (ANCHORED /
RETRO / ARCHIVAL, `graph-at-a-past-cut` D4) changes only the derived construction over identical
grants → result-side, a declared descriptor in every reading's evidence (π-kin), never a scope
coordinate.

**Consequently: the modes need no structurally different dreamers.** There is one dreamer role
(`dreamer_scope`, `core/agent_scope.py:143-158`), and synchronic/diachronic/past/counterfactual
are values of its grant. This is the answer to the `dreamer-and-graph-direction` seed question
("second dreamer mode, or a distinct diachronic interpreter?"): **neither — a grant value.** The
dispatch machinery, the harness evaluation (per-grant A/B), the interpreted-only output law, and
the promotion gate are identical across all four; only the grant and the legality obligations it
triggers differ. Note the algebra's teeth fire *for free* in the right places: a multi-stratum
point read demands its cut (SLICE, `core/scope.py:527-536`); a composed counterfactual read is
multi-stratum by construction and therefore **cannot be dispatched cut-less**; a cross-clock T
composes only through the built atlas (`core/scope.py:378-398`).

*Falsifier (F-SD1):* a mode is found that cannot be expressed as a `(Σ, E, T, A)` grant plus an
instrument grant — e.g. the counterfactual read turns out to need write authority into a durable
stratum, or the diachronic read needs a temporal object that is not a window over a registered
clock. Then the decomposition is wrong, the fifth-axis question re-opens, and this section is
amended by supersession, not silently.

### 2.2 SD-2 — the dispatch record: a DreamCharter is (scope grant, instrument grant, budget, gauge)

A dream dispatch is a typed record — the worked example of dn-agent-taxonomy's "role = scope
signature," at full depth:

1. **The scope grant** — `meet(owner_grant, dreamer_scope(strata))`: the owner declares strata
   (the per-scope-grant regime, dn-cross-strata-dreamer owner ruling 2026-07-16 — each grant
   owner-declared, harness-evaluable); the role constructor supplies the region; the meet is the
   ratified delegation law (`core/scope.py:538-549`, non-negotiable #6). T is bound per dispatch:
   `pt(cut)` (synchronic) or `[c₁, c₂]` (diachronic, parked §2.8). Output authority is the role's
   `(READ, W_Σ=1, NONE)` — interpreted-only writes, structurally unforgeable (the `DerivedStore`
   has no provenance parameter), zero world reach.
2. **The instrument grant** — the dreamer's *senses* are named tool handles over evaluators
   (σ*/MST, conductance profile, census, persistence, …), granted as a set `⊆ INSTRUMENT_MAX`,
   resolved at mint — **the factory's existing ceiling pattern reused verbatim**
   (`core/factory/roles.py:24-40`: capability = `scope ∩ MAX`, refuse at construction, a skill
   never widens). Instruments are NOT a scope coordinate (they are result-side machinery over
   already-granted reads — the §2.1 visibility test again); they are a capability over *code*,
   and the factory already owns that shape. No new lattice.
3. **The budget** — the §2.4 cost-model parameters (node/edge ceilings, eigensolve dimension cap,
   walk budget) the refusal gate reads.
4. **The gauge declaration** — ANCHORED by default; RETRO/ARCHIVAL only when the dispatch's
   question needs then-geometry (both parked with `graph-at-a-past-cut`'s own graduation). Every
   reading pins its gauge fingerprint beside its `(σ, t, cut)` tuple (CN-1's evidence discipline
   extended — already anticipated by `graph-at-a-past-cut` D4).

**Enforcement (structural-enforcement rule — each property names its test):** the dispatch's
handle inventory is checked by the existing `assert_conforms` (`core/agent_scope.py:191-215`) —
declared-vs-actual, guard tier, honestly labelled; the instrument set is refused at construction
if it exceeds `INSTRUMENT_MAX` (structural, the `RoleTemplate.__post_init__` shape); admissibility
of the grant is the existing `admissible`/`req_admissible` (`core/scope.py:603-624`) under the
ideals applicable to the client class (𝔇 always; ι_MR unless the class holds the
cross-strata-dreamer read exemption). New tests licensed at D-0 (§3): a dispatch constructed with
a store handle not derivable from its evaluator is a `ConformanceError`; an instrument handle
outside the grant is unconstructable.

### 2.3 SD-3 — the algebra as tools; the senses, with per-instrument ring honesty

The dreamer is an **outer-core agent, a client of the inner algebra** — dn-inner-outer-core §2.8,
where the computation *agrees*: the dreamer, librarian, curator all compute outer; the vocabulary
they are written in (`scope`, `agent_scope`, `mirror`) computes inner. The dreamer never holds the
algebra's internals; it holds grants and forces evaluators.

**Instrument purity is PER-INSTRUMENT** (binding constraint from the v2 ruling — do not write
"the instruments are inner"):

| sense | module | ring status (computed, dn-inner-outer-core A.1/A.3) |
|---|---|---|
| σ*/MST, conductance, composed assembly | `core/graph/` | outer today (packaging via `graph/__init__` + spine closure); the math's route in is the K3 split, named-not-licensed there |
| the arrow-aware census (cycles, diamonds, retro-citations) | spine-side + `reference_edges` | outer **permanently by design** (spine is acquisition machinery, sqlite-coupled) |
| temporal math ([d,τ], boundary, operators) | `core/temporal/` | enters the ring when **S1 lands** (licensed, owner-ruled 22:55Z) — not before |
| spectral family | `core/complex/spectral.py` (sknetwork) | outer under v2; parked **P8** — a dependency decision out of this note's scope |
| σ-persistence | eval-side consumer (FB-1) | harness machinery, not core at all |
| MirrorGraph / cluster | `core/dreaming/` | lax-inner, strict-outer (packaging debt A.2) |

The ring is a *meaning* boundary, not the egress boundary (§2.5 there) — no capability claim in
this note depends on ring membership; the table exists so no downstream plan asserts purity the
computation refutes.

**The directional sense is the combinatorial census, and only the census.** The ML-a operator
deferral is ratified and honored: the dreamer's arrow-awareness rides the already-licensed
Thread-C sweep (directed influence cycles on `X_cite`; unbalanced diamonds / revision-effort
asymmetry; retro-citations) — exact, deterministic, gauge-immune, honest-seam (emits nothing when
empty). **This design's verdict on sufficiency: the census suffices for everything §2.8's v1
narrates; no ML-a gate-(ii) census-insufficiency argument is made here.** If a future dispatch
demonstrably needs graded/soft direction (ranking by "how directed" rather than enumerating exact
cycles), that demonstration is the gate-(ii) argument and goes to the owner as such — the
operator is never designed in by a dreamer plan. Caution carried forward verbatim: the diamond
conjecture is REFUTED (ML §2.3 — no abelian/spectral object closes TA-c); spectral
direction-reading has proven limits, and eigenvector phases are gauge-dependent (ML-b) — a
narration layer that spoke "flux language" would manufacture apophenia from a gauge choice.

### 2.4 SD-4 — laziness as law: the materialization boundary

The owner's addendum, adopted as five laws. The honest baseline first: **the symbolic half
already exists** — a `Scope` is a pure description (`core/scope.py` is "vocabulary, not a gate";
meets/joins compose at O(expression) with zero store reads), and the eager half is real —
`MirrorView.project` pulls rows at construction (`core/mirror.py:96-101`) and
`MirrorGraph.build` computes the full cosine matrix eagerly (`core/dreaming/graph.py:33-40`).
At today's corpus scale eager is correct; the laws below govern the dispatch layer so that
growth in size AND time never forces a redesign.

- **L1 — composition is symbolic; cost is O(expression).** A dispatch composes scope expressions
  (meet/restrict/anchor-shift) and instrument plans without touching a store. *Test:* a counting
  `RowSource` fake proves composing k expressions performs zero reads.
- **L2 — one materialization boundary.** `force : (grant, cut[, generation]) → readings` is the
  single seam where rows become real. The evaluator applies the admissibility check at the same
  call — which is the point of the unification verdict below. *Test:* the dispatch's handle
  inventory contains exactly the evaluator (conformance); a red-team test constructing a dreamer
  with a direct store handle expects `ConformanceError`.
- **L3 — estimate-then-force (the refusal gate, rule-#8 kin).** Every force is preceded by a
  cost estimate computed from the *unevaluated* expression (store stats: chain counts, node
  counts, grid sizes, eigensolve dims — metadata reads only). The estimate is pure data computed
  core-side; the **refusal is enforced by the dispatch machinery/scheduler, outer-side** — the
  same split as everything else (core computes, machinery refuses; the memory-ceiling scheduler
  refusal extended to views). A refused dispatch reports "refused at estimate: <budget>, <est>"
  — quantified, the CN-7 refusal posture. *Test:* an over-budget estimate refuses with zero row
  reads (counting fake); *falsifier F-SD4a:* any ceiling breach reached through a forced view
  without a prior estimate event.
- **L4 — no transitive-closure materialization.** Composed relations (C∘D traversals, reachability,
  fiber chains) stay unevaluated; only demanded restrictions evaluate, as budget-bounded searches
  with principled refusal (CN-7 is the built shape). The σ*/MST keystone is the *exemplar*, not
  the exception: one O(E log V) spanning tree is a compact certificate from which any pair's σ*
  derives on demand — all-pairs answers without an all-pairs table. *Test:* no instrument surface
  exposes an all-pairs closure constructor; path queries below budget refuse rather than
  partially materialize (CN-7's falsifier, inherited).
- **L5 — incrementality per instrument family** (the capsule's open question, answered):

  | family | incremental move | recompute trigger |
  |---|---|---|
  | σ*/MST | edge insertion via the cycle property, O(V)/edge `[FROM MEMORY — verify; standard]`; pure addition only ever raises σ* (D5-ii growth monotonicity) | edits/tombstones (weight decreases) — recompute or attribute via CN-3 |
  | conductance / heat-kernel | first-order eigen-perturbation for small ΔL (§2.7); Weyl bounds bracket validity `[FROM MEMORY — verify]` | ‖ΔL‖ comparable to spectral gaps; degeneracy near-crossings |
  | census (integer invariants) | delta-local combinatorics (affected SCCs, new diamonds) | never perturbative — integers do not perturb; recompute is exact and cheap |
  | persistence | append new cells; `pers` is monotone-refinable on a densified grid (FB §2.3) | grid/range change (a new ruler = a new π, never comparable) |
  | derived caches | digest-keyed memoization — the sourceset group-by-digest precedent; a (digest, gauge-fingerprint) re-embed is content-addressed and cacheable forever | never invalidated (content-addressed); only superseded |

**The lazy-view = capability unification — verdict: ADOPTED, under one named condition, at an
honest tier.** The claim (materialization boundary = authorization boundary; a scoped dreamer
holding a lazy view structurally cannot read outside its scope) is the `MirrorView` pattern
generalized — project-and-validate in one act. But laziness alone enforces nothing: if any code
path in the dispatch can reach a store directly, the lazy view is a performance construct wearing
a capability's clothes. The unification holds **iff the evaluator is the dispatch's only
store-touching capability** (the closed-evaluator condition) — then authorization and
materialization are literally the same call, and the L3 estimate rides the same seam, so the
three gates (admissibility, budget, cache) are one boundary, not three. Enforcement tier, honest:
**guard** (conformance inventory + counting-fake tests), like the non-structural Views — the
structural version (the evaluator as the only constructor of store handles in the dispatched
process) is a v2, and if the isolation argument ever needs "provably effect-free," that is
dn-inner-outer-core's P1/v3 re-entry, named there. *Falsifier (F-SD4b):* a dispatch obtains a row
with no corresponding force event — the unification is theater; separate the mechanisms and say
so.

### 2.5 SD-5 — cuts as pointers: the store-layout honesty check (compatible; no migration)

The capsule asked whether "cuts as pointers into an append-only structure" fits the current
layout or demands a migration. Evaluated store-by-store, the verdict is **compatible today, no
migration** — with one seam and one park named honestly:

- **The event/history layer is already the persistent structure.** Versions are append-only
  per-doc chains, byte-preserved across the owner-gated rekey; the rawstore is content-addressed
  and immutable; a `CertifiedCut` is a frontier *vector of chain positions* plus certificates
  (`core/temporal/spine.py:218-229`) — cuts ARE pointers, built (bp-055), with refusal-not-
  fabrication semantics for missing certificates. Nothing to migrate; structure-sharing across
  cut views is free because nothing is copied.
- **The vector/graph layer is current-only BY DESIGN, and the gauge split keeps that honest**
  (`graph-at-a-past-cut` D2/D4): the ANCHORED gauge (today's vectors, membership-at-c) is
  pointer-cheap — membership derives from version chains alone, no historical content; the RETRO
  gauge (content-at-c re-embedded) is *regeneration-priced*, not pointer-priced — O(changed docs)
  compute through the rawstore, and its products are digest-keyed cacheable forever (L5). The
  design therefore never pretends a past σ-graph is a pointer-follow; it prices the two gauges
  differently and defaults to ANCHORED.
- **The one genuinely new mechanism** remains `graph-at-a-past-cut` O1 (frontier-at-a-past-commit:
  versions rows record no commit). Default adopted here for planning purposes: the **digest-join**
  derivation (git tree at SHA → content digest → chain position) — exact for git-tracked sources,
  zero writes; the additive ingest-ledger commit column stays that note's own call at its
  graduation. This note only *consumes* the seam (the `RowSource` Protocol,
  `core/mirror.py:54-60` — a `HistoricalRowSource` passes the Invariant-6 check unchanged,
  finding-0100).
- **Parked (SD-c): a delta-log / persistent-adjacency structure for the σ-graph.** The eager
  cosine matrix is O(n²) and recomputed per projection; a persistent incremental structure is the
  known upgrade. NOT adopted now — the scaling note's own discipline binds (measure growth
  first); re-entry: a measured cut-sweep or projection cost crosses a stated budget on the grown
  corpus. Laziness is why this park is safe: the L2 boundary localizes the change to the
  evaluator's internals — no dispatch, grant, or instrument surface changes when the
  representation does. *That containment is the falsifiable content of the laziness design
  (F-SD5): if a representation swap behind `force` requires touching any dispatch or instrument
  surface, L2 failed.*

### 2.6 SD-6 — the hypothetical subspace, folded in: the counterfactual value of the dispatch

**Ruling: the subspace FOLDS IN — it is the counterfactual value of §2.1's decomposition, not its
own note.** Its capsule's parked default ("its own design pass after inner-outer-core") is
superseded by this section with the owner's own suspicion as warrant ("one last fable pass");
each of its four open questions is answered here. Its *build* remains its own plan family (§3).

1. **Where it lives: a new base stratum, `HYPOTHETICAL` — an overlay, not a refinement.** One
   additive `Stratum` enum element (the DIALOGUE precedent, bp-070 D1: enum + laws tests, no
   store schema change elsewhere). Staged items carry their *would-be* stratum/provenance as row
   data (stratum ≠ provenance — dn-agent-taxonomy §2.3's own distinction), so one lattice element
   serves overlays beside any stratum. Flat and grouped retrieval **never** see it: default
   grants exclude it (Σ-visibility is the capability test — a read including staged rows is only
   constructible under a grant naming HYPOTHETICAL). The composed counterfactual read
   `{…, HYPOTHETICAL}` is multi-stratum by construction, so **SLICE fires automatically**: it
   must carry the durable side's certified cut *and* the subspace generation — a counterfactual
   read is well-typed only as "the graph at cut c ∪ the subspace at generation g."
2. **The TTL clock: the staging store's own event clock, never wall.** Admission and expiry are
   staging-store append events on its own chain (g1) — a per-stratum clock `N_hyp` whose ticks
   are generations. Wall-denominated TTLs ("expire in 3 days") are owner convenience: they
   resolve to generations at sweep time through the interval-valued, ambiguity-widening resolver
   posture (`graph-at-a-past-cut` D8); wall never orders anything (Law C4). Every reading pins
   its generation, so a dream report stays reproducible *as a record* after expiry.
3. **Admission and expiry.** Expiry: a housekeeping sweep (outer machinery, trough-tier) advances
   the generation and removes expired items from every readable view; default disposition is
   **tombstone** (append-only discipline, cheap at this scale), with the honest note that TTL'd
   staging is the one store class where hard delete is *admissible by design* (the data was never
   corpus) — parked SD-d, a plan-level call. Admission: **there is no promotion path from
   HYPOTHETICAL to anything.** A hypothesis the owner comes to believe enters the corpus the way
   everything enters — the owner authors it, or its real source is ingested through the normal
   pipeline. No new crossing; the laundering-proof answer, identical in shape to
   dn-cross-strata-dreamer §2.1 (ratification/authoring is the only crossing).
4. **Isolation, structural.** Staged rows live only in the staging store; the durable stores
   cannot hold them — the vectorstore/derived writers have no hypothetical class to write, and a
   `MirrorView` rejects any non-MIRROR_READABLE row at construction (`core/mirror.py:86-94`), so
   "staged data in the mirror" is unrepresentable, not forbidden. The composed read happens at
   **assembly** — the `core/graph/composed.py` seam exactly (an explicit node set × edge union
   presented through the `MirrorGraph` surface, math fed unchanged); a staged overlay is a second
   edge/node class at assembly, not a store merge. And the dispatch is **not the mirror's
   reflective dreamer**: a grant whose Σ includes HYPOTHETICAL beside mirror strata is an
   interpreted-tier dispatch under the cross-strata regime (per-grant, owner-declared, the ι_MR
   exemption per client class, G-gates binding) — I6 verbatim. *Tests:* durable stores scan to
   zero staged rows after any dispatch; `MirrorView` + staged row raises; the composed assembly
   without the HYPOTHETICAL grant is unconstructable (`req_admissible` fails).

### 2.7 SD-7 — influence is the perturbation term; the conditioning law

**Influence, operationally:** the differential of instrument readings along the overlay
direction. For a staged perturbation Δ (added nodes/edges with their weights), define per
instrument reading R:

    infl_R(Δ) = R(G ∪ Δ) − R(G),

computed two ways by family, which must agree where both apply:

- **Smooth family (Rayleigh/spectral objects — conductance, heat-kernel quantities):** the
  first-order term IS the definition — for a simple eigenpair (λ, x),
  `infl_λ(Δ) ≈ x*ΔL x` (the Rayleigh-quotient directional derivative
  `[FROM MEMORY — verify; standard first-order eigenvalue perturbation]`) — both the efficient
  estimator and the mathematically honest formulation (the laziness addendum's sharp case,
  adopted). The exact recompute-diff is its finite-difference check; *falsifier (F-SD7a):* the
  perturbation estimate and the exact diff disagree beyond the stated second-order bound on a
  synthetic instance ⇒ the estimator is invalid at that Δ and the reading must say "recomputed,
  not perturbative."
- **Integer family (the census; σ* component structure):** integers do not perturb —
  influence is the exact recompute-diff over the composed assembly, delta-local where the
  combinatorics allow (new SCCs through staged arcs; diamonds minted by staged supersessions).
- **One-sided laws for free (the honesty anchor):** a *pure-addition* overlay can only raise
  conductance and σ* (weighted Rayleigh + growth monotonicity, `graph-at-a-past-cut` D5) — so
  additive influence is signed non-negative *structurally*, and any negative reading is an
  implementation bug, not a finding. Overlays that stage *edits or removals* ("what if this note
  were gone") are a **v2** with the opposite one-sided law, parked (SD-e) — different math,
  different tests, never conflated with v1 addition.
- **Attribution is CN-3's law, generalized verbatim:** the Δ-elements are exactly the staged
  items; every influence claim names the staged element(s) it verified leave-one-out. No new
  machinery — the reconnection report pointed at a hypothesis instead of a spike.

**The conditioning law (the anti-laundering invariant — the load-bearing new law of this note).**
A dream over graph ∪ subspace is a *hypothesis-conditioned* artifact, and the taint is
structural, not editorial:

1. **Provenance carries the condition.** A conditioned artifact records
   `(subspace_id, generation, staged-item digests)` in its data, and its `derives` hyperedge
   tails include the staged items' content addresses — the grounding chain *visibly* bottoms out
   partly outside the corpus.
2. **TTL inheritance.** When the subspace expires, its conditioned artifacts leave the surfacing
   set with it (retained as records, never surfaced as live dreams). A hypothesis cannot outlive
   its own expiry through the dreamer's exhaust.
3. **Taint attribution IS the influence computation** (the unification that makes this cheap):
   a per-claim leave-the-subspace-out recomputation splits claims into *corpus-grounded* (the
   claim holds bit-identically without the overlay — it may shed the condition mark) and
   *conditioned* (nonzero delta — it keeps it). One computation does double duty: influence
   detection and taint attribution are the same with/without diff.
4. **The grounding rules extend, not break.** `recursive-dreaming-bounded-by-grounding`'s rule 1
   becomes: grounding terminates in authored evidence **or declared hypothesis, marked as such —
   never in prior interpretation.** The recursion bound is untouched (dreams still cannot cite
   dreams as evidence); the citation classes split (durable vs staged) and the split is visible
   in every report.

*Falsifiers (F-SD7b):* a claim marked corpus-grounded whose report changes when the subspace is
removed (taint test, per-claim, mechanical); a conditioned artifact surfacing after its
generation expired (sweep test); a `derives` edge over a composed read whose tails omit staged
digests (lineage audit).

### 2.8 SD-8 — the diachronic axis: designed in full, execution parked; the clock-free v1

**The axis, fully designed.** A diachronic dispatch is the interval-window value of the grant:
`T = (κ, [c₁, c₂])` over certified cuts, evaluated per the ratified semantics — endpoint slices
with σ_*/σ^* transports between them, per-stratum between frontiers for cross-strata windows
(GC §2.9-4); readings are `Inv` counts or clock-declared `Rate(κ)` (Rule CLOCK — a drift rate
off an unacknowledged clock is unconstructable, `core/scope.py:666-675`); window purity binds
(no interpreter-version event inside the window, the A7 discriminator as a spine predicate,
GC §2.9-2). What it narrates when built: where the graph is *moving* — threads consolidating vs
dissolving, drift direction, the memory-curve jump points — over the instrument family
`graph-at-a-past-cut` pre-registered (its own graduation, consumed here, not absorbed).

**Execution stays PARKED, and the park is honored with its re-entry restated honestly
(finding-0126).** The standing park (dn-agent-taxonomy: "diachronic dreamer — blocked on
certified cuts (G3)") names a blocker that is now **built** — GC-3 shipped (bp-055;
`core/temporal/spine.py:159-274`, composed certificates, crossing-edge refusal). The park does
not thereby dissolve: what actually remains is (i) the interval-window instrument family (the
memory curve et al. — designed in the brainstorm, not yet graduated or built), (ii) the
harness's per-grant lane for interval dispatches, and (iii) the owner's sequencing. **Re-entry
(replaces "G3 materializes"):** the owner unparks after the `graph-at-a-past-cut` family
graduates AND the synchronic dispatcher (D-1, §3) is sealed — at which point diachronic
execution is a grant value away, not a program away.

**The clock-free v1 — licensed for design here: the ARROW-READ dispatch.** Direction is time's
residue in the synchronic graph: a directed edge (supersession, citation, derivation) is a frozen
record of a temporal event, so a *synchronic* dispatch (point window, one certified cut — full
legality, no cross-cut transport) whose instrument grant includes the census reads temporal
structure without touching the parked execution: influence loops ("these notes cite in a closed
directed cycle"), revision-effort asymmetry ("this branch took three revisions where its sibling
took one"), reach-backs ("this note re-cites something younger than its own first authorship —
a revision-mediated backflow"). Every claim cites its witness (edge set, commit SHAs) — census
invariants come witnessed by construction. Honest seams: the census emits nothing when empty
(likely on today's corpus — the σ-sweep run, oq-0024, and the Thread-C sweep will say); no rates
without a declared clock; no spectral/flux vocabulary (§2.3 caution). This v1 is what makes
oq-0021 decidable now (§2.9) — the "lens plan" whose absence parked it has arrived.

### 2.9 SD-9 — oq-0021 grounded: the narration recommendation (owner rules at ratification)

**The question (dn-magnetic-laplacian owner decision 2, parked as oq-0021):** does the
arrow-aware census claim family enter the dreamer's narration, and with what language?

**Recommendation (for the owner to rule — a taste call prepared, not a fait accompli): ADMIT,
as equal-citizen structural-panel claims, in arrow-literal, witness-citing language.**
Specifically: (a) census claims join the structural panel beside `bridge`/`hole`/`theme` with
adjudication unchanged (the PD-f equal-citizen precedent); (b) the vocabulary narrates **records,
not causes** — "A cites B cites C cites A, a closed influence loop" (fact, witnessed), never
"B shaped your thinking on A" (inference the census cannot support); direction is presented as
time's residue ("this loop closed through revisions you made in March"), the honest conceptual
frame §2.8 licensed; (c) gauge-immune quantities only — combinatorial invariants are immune by
construction (ML §2.7b); no spectral phrasing exists to leak; (d) the honest seam surfaces as
silence, never as filler ("no directed structure found" is not a dream).

**Rejected alternative, recorded:** keep the census out of narration entirely (census as
telemetry only). Rejected because the census is precisely the mirror-safe, embedder-independent,
exactly-witnessed claim class — the *strongest*-grounded family the dreamer could narrate;
excluding it while narrating cosine communities would invert the grounding hierarchy.

**Falsifier for the recommendation (F-SD9):** on F9-style fixtures — planted directed cycles /
diamonds / retro-citations vs an arrowless control — the narration surfaces each planted structure
with its correct witness AND emits zero census claims on the control. A census claim without a
verifiable witness, or any census narration phrased as influence-causation, fails review and the
vocabulary is re-ruled. If ratification rejects admission, the default stands (census computes
via Thread-C, narrates nothing) at zero cost — the D-1 plan simply drops its narration item.

### 2.10 SD-10 — reconciliation: the five dreamer notes, ruled one by one

No silent absorption; each ruling carries its warrant.

| note | ruling | warrant |
|---|---|---|
| `dn-cross-strata-dreamer` (ratified) | **EXTEND** | Its per-scope-grant regime is this note's chassis; the owner ruling ("dreamers scoped to different strata and combinations, per-grant, harness-evaluated") is exactly what §2.1–2.2 instantiate. Nothing relaxes: G0–G4 bind every non-mirror grant; interpreted-only output and owner-ratification-only crossing bind every dispatch; HYPOTHETICAL joins the *grantable* coordinates with its own conditioning law on top. Ratified text untouched (A8). |
| `dn-sigma-fibers` (ratified) | **EXTEND** | Its §2.8 axis table (temporal→T; scale→Res(π); strata→Σ) is the seed §2.1 completes with the anchor and overlay coordinates; its §2.6 ruling (resolution is result-side) is reused as the decisive test. Its instruments are senses in §2.2's grant; FB-1..4 and all parks unchanged. |
| `dn-recursive-dreaming-bounded-by-grounding` (draft) | **EXTEND** | The four safety rules bind every dispatch here unchanged and gain a fifth sibling: the §2.7 conditioning law. Rule 1 is *sharpened, not weakened*: grounding terminates in authored evidence or declared hypothesis (marked, TTL-inherited) — never in prior interpretation. Its build-order rule (recursion last, gauge first) stands. |
| `dn-dreaming-on-curated-graphs` (draft, R5) | **EXTEND** | R5 re-reads as one grant: Σ = {curated}, point window, panel + resonance instruments — the per-scope regime with zero bespoke machinery. Its firewall content (curated ∉ MIRROR_READABLE; own graph; resonance interpreted-only, never merged) is untouched and is an instance of the general laws. When R5 builds, it is minted AS a dispatch record (§2.2), not a bespoke engine — that is the one forward-binding change. |
| `dn-dream-phase-rnd-charter` (draft) | **EXTEND** | The R&D governance stands whole: the two-axes-of-worker distinction, the safety spine, consensus-vs-adjudication, and the hard flag boundary (`core/dreaming/rnd.py:31-40` — every new dispatch mode lands behind `require_rnd_enabled` until the owner wires it). Its R0–R5 ladder re-reads as grant shapes under §2.1; the charter remains the R&D home; this note is the typed dispatch its items are instances of. |

Verdict on supersession: **none.** The two ratified notes are extended within their own
anticipations; the three drafts remain accurate governance whose content this note types rather
than replaces. The one superseded *default* is in a brainstorm, not a note: the
hypothetical-subspace capsule's "graduates as its own design note" park resolves as §2.6's
fold-in (recorded there as this note's warrant chain).

### 2.11 Constraints honored

| constraint | binding form here |
|---|---|
| Mirror firewall (I6) | the mirror's reflective dreamer stays authored-only; composed/counterfactual dispatches are interpreted-tier per-grant clients (ι_MR exemption per class, G-gates); staged rows unrepresentable in `MirrorView` (§2.6) |
| The model advises; code acts | dispatch, evaluator, estimate, sweep are code; the model appears only at narration over scrubbed, granted reads; refusal is machinery-side (§2.4 L3) |
| Memory ceiling (#8) | the refusal gate is the ceiling *extended to views*; census/σ*/conductance are model-free; narration is one earned model call under existing tiering |
| Sacred fixed points | 𝔇 subtracted from every grant (`⊤_Σ = R ∖ 𝔇`); the frozen corpus is a flat region of the spine; no lever names golden |
| Append-only discipline | staging is append-only with generations; expiry defaults to tombstone (SD-d); durable stores never hold staged rows |
| No wall ordering (Law C4) | TTLs resolve wall→generation at sweep via interval-valued resolution; every reading indexed by (σ, t, cut, generation, gauge) |
| Two prime movers (dreaming is necessary) | the dreamer remains the continuous drive into the interpreted layer; nothing here touches the promotion gate that couples it to the owner |

## 3. Consequences — the plan decomposition (on ratification; session-sized; preempts nothing)

Sequencing constraint honored: everything below queues **behind** the already-sequenced lead work
(bp-069/070/071; inner-outer-core M0 then S1) and behind the G-gates where they apply.
`/graduate` decides final splits; each item names its acceptance and falsifier surface.

- **D-0 — the dispatch record + the materialization boundary** (the typing/evaluator layer):
  the DreamCharter type over the existing constructors (`dreamer_scope` + the factory ceiling
  pattern for `INSTRUMENT_MAX`), the `force`/estimate seam with counting-fake tests, conformance
  wiring, refusal gate reading budget from the charter. Pure additive; no store schema; no
  behavior change to any existing dreamer path. Acceptance: §2.2 tests + §2.4 L1–L3 tests green;
  falsifiers F-SD4a/F-SD4b as tests.
- **D-1 — the ARROW-READ synchronic dispatch (the clock-free v1)**: census readings (consumed
  from the already-licensed Thread-C sweep — no new census license) surfaced through the
  structural panel behind the R&D flag; narration vocabulary per the §2.9 ruling **as the owner
  rules it at ratification** (if rejected: computation lands, narration item drops). Acceptance:
  F-SD9 fixture battery; honest-seam (empty census ⇒ zero claims); A7 (no undeclared rates).
- **H-0 — the HYPOTHETICAL stratum** (a small rider, bp-070-D1-shaped): the enum element +
  lattice-law tests + ideal/admissibility coverage. Additive only.
- **H-1 — the staging store + overlay assembly + TTL sweep**: append-only staging with
  generations; the composed-assembly overlay (reusing `core/graph/composed.py`'s surface);
  the trough-tier expiry sweep with wall→generation resolution. Acceptance: §2.6 isolation
  tests (durable-store zero-scan; MirrorView rejection; cut-less composed read unconstructable).
- **H-2 — influence v1 + the conditioning law**: Δσ*/ΔC/Δcensus over the overlay with CN-3
  attribution; the perturbation estimator with its finite-difference check; per-claim
  taint attribution; TTL-inheritance surfacing test. Acceptance: F-SD7a/F-SD7b as tests; the
  one-sided addition laws asserted structurally. Gated on H-0/H-1 and on the cross-strata
  G-gates for any grant touching non-mirror strata.
- **Owner-operational, not a plan:** run the σ-sweep (oq-0024) and the Thread-C census sweep
  before or alongside D-1 — their readings turn §2.8's "likely empty at this scale" from a guess
  into a measurement.
- **Explicitly NOT licensed:** diachronic execution (§2.8 park; re-entry stated there and in
  finding-0126); the past-cut dispatch build (waits on `graph-at-a-past-cut`'s own graduation —
  this note only pinned its typing, §2.1, and its seam, §2.5); the magnetic operator (ML-a);
  edit/removal overlays (SD-e); any spectral influence upgrade (P8-coupled, SD-f).

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| SD-a | diachronic EXECUTION (interval-window dispatches) | parked — §2.8; the axis is fully designed, the substrate (GC-3) is built | owner unparks after the `graph-at-a-past-cut` family graduates AND D-1 is sealed (finding-0126 restates the stale "G3 materializes" re-entry) |
| SD-b | past-cut dispatch build (ANCHORED first; RETRO/ARCHIVAL behind it) | typed here (§2.1), seam pinned (§2.5); build waits | `graph-at-a-past-cut` graduates its instrument note; the HistoricalRowSource adapter plan (finding-0100 shape) is minted there |
| SD-c | persistent/incremental σ-graph representation (delta-log adjacency) | eager `sim` matrix behind the L2 boundary | a measured projection/cut-sweep cost crosses a stated budget on the grown corpus (the scaling note's measure-first rule) |
| SD-d | expired staging rows: tombstone vs hard delete | tombstone (append-only discipline; cheap) | staging growth is measured material; hard delete is admissible by design for this one store class — plan-level call with the owner |
| SD-e | edit/removal overlays ("what if this were gone") | addition-only v1; the opposite one-sided law noted | a real counterfactual question needs removal; its own small design pass (different math, different falsifiers) |
| SD-f | spectral influence (eigenvector localization over the overlay) | combinatorial + Rayleigh v1 only | P8 resolves (sknetwork dependency decision) AND F-SD7a shows the perturbation family needs the finer instrument |
| SD-g | structural (v3) closed-evaluator enforcement | guard-tier conformance (§2.4, honest label) | F-SD4b fires, or the isolation argument needs "provably effect-free" (dn-inner-outer-core P1's named candidate — decide there) |
| SD-h | per-dispatch σ/resolution defaults | inherit the sweep-selected σ + `Res(π)` discipline unchanged | FB-3's gate validates tiers; tier-differentiated dispatches revisit under SF-c |

## Falsifiers (the load-bearing set, collected)

- **F-SD1** (§2.1) — a mode inexpressible as a grant + instrument set ⇒ the no-new-axis verdict
  is wrong; reopen the fifth-axis question by supersession.
- **F-SD4a** (§2.4) — a ceiling breach through a forced view with no prior estimate event ⇒ the
  refusal gate is decorative.
- **F-SD4b** (§2.4) — a row obtained with no force event ⇒ lazy-view=capability is theater;
  separate the mechanisms and relabel the tier.
- **F-SD5** (§2.5) — a representation swap behind `force` that touches any dispatch/instrument
  surface ⇒ the materialization boundary leaked.
- **F-SD7a** (§2.7) — perturbation estimate vs exact diff beyond the stated second-order bound ⇒
  the estimator is invalid at that Δ; readings must declare recompute.
- **F-SD7b** (§2.7) — a "corpus-grounded" claim that changes without the overlay; a conditioned
  artifact surfacing past expiry; a derives edge omitting staged digests ⇒ the conditioning law
  is broken (this is the anti-laundering tooth; it fails closed).
- **F-SD9** (§2.9) — a census narration without a verifiable witness, phrased as causation, or
  emitted on an arrowless control ⇒ the vocabulary ruling is re-opened.

## Cross-references

**Warrant:** `docs/brainstorms/synchronic-diachronic-dreamer.md` (the four ingredients; the
laziness addendum; every capsule open question answered above) ·
`docs/brainstorms/hypothetical-subspace.md` (folded in — §2.6/§2.7) ·
`docs/brainstorms/graph-at-a-past-cut.md` D1–D9 (honored; consumed §2.1/§2.5; its instrument
family keeps its own graduation) · `docs/brainstorms/dreamer-and-graph-direction.md` (answered
§2.1/§2.8) · `docs/brainstorms/temporal-clocks-and-strata.md` (the two-prime-movers frame;
clock laws) · `docs/brainstorms/cross-strata-and-multiscale-dreamers.md` (the family's founding
capsules).

**Code (verified on disk 2026-07-20):** `core/scope.py` (:55-74 Stratum; :248-250 point windows;
:378-398 atlas meet; :497-536 SLICE; :538-549 meet; :603-624 admissibility/req; :666-675 Rule
CLOCK) · `core/agent_scope.py` (:143-158 `dreamer_scope`; :191-215 `assert_conforms`) ·
`core/factory/roles.py` (:24-40 the ceiling pattern §2.2 reuses) · `core/mirror.py` (:54-60
RowSource — the §2.5 seam; :86-101 structural rejection + project) · `core/dreaming/graph.py`
(:33-40 the eager build §2.4 baselines) · `core/dreaming/rnd.py` (:31-40 the flag boundary) ·
`core/graph/composed.py` (the assembly seam §2.6 reuses) · `core/temporal/spine.py` (:159-187
certificates; :218-229 CertifiedCut; :253-274 stratum→certificate composition — GC-3, built) ·
`core/stores/sourceset.py` (digest-keyed identity — the §2.4 L5 cache precedent).

**Design:** dn-inner-outer-core §2.2/§2.6b/§2.8, P1/P8 (ring honesty §2.3; draft — cited as
such) · dn-agent-taxonomy §2.1/§2.3/§2.5 + its parked diachronic row (restated by
finding-0126) · dn-capability-scope §2.1–2.4, CS-c · dn-global-event-clock §2.4/§2.6/§2.9 ·
dn-connectivity-instruments CN-1..CN-7 (the senses; the attribution law) · dn-magnetic-laplacian
§2.3/§2.7/ML-a..d + owner decision 2 (→ §2.9; oq-0021) · dn-temporal-retrieval-algebra §2.2
(interval semantics), §2.5 (as corrected by the two-prime-movers capsule) · dn-sigma-fibers
§2.3/§2.6/§2.8 · dn-cross-strata-dreamer §2.1–2.4/XS-a..d · dn-edge-dynamics §2.5 (the
inversion; fits are interpretations) + §5 (the vocabulary question §2.9 extends) ·
dn-evaluation-harness (the per-grant A/B lane) · finding-0100 (RowSource retro seam) ·
finding-0126 (this pass — the diachronic park's re-entry restated) · oq-0021 (grounded §2.9) ·
oq-0024 (the owed run; operational).

**External claims flagged:** first-order eigenvalue perturbation / Rayleigh-quotient derivative;
Weyl eigenvalue bounds; incremental-MST cycle property — all `[FROM MEMORY — verify]` before any
book chapter cites them (external-grounding discipline).
