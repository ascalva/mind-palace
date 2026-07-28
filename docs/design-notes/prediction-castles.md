---
type: design-note
id: dn-prediction-castles
track: sync-diac-dreamers
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-28
updated: 2026-07-28
links:
  - docs/brainstorms/synchronic-diachronic-dreamer.md   # THE WARRANT — six owner seeds 2026-07-28 (02:54Z→05:49Z) + the 2026-07-21 forecaster capsule
  - docs/design-notes/synchronic-diachronic-dreamer.md  # RATIFIED — EXTENDED (§2.6/§2.7 gain the castle layer; §2.8 park honored; laziness gains its retention half)
  - docs/design-notes/capability-scope-algebra.md       # RATIFIED — the (Σ,E,T,A) lattice; T=(κ,W); W_world chain; every verdict here types against it
  - docs/design-notes/global-event-clock.md             # RATIFIED — the spine (Ev,≼), N_s, certified cuts (GC-3 BUILT, bp-055); the clock substrate §2.6 grounds on
  - docs/design-notes/temporal-retrieval-algebra.md     # RATIFIED — interval-window semantics; falsification dates and lease floors are T-windows, never wall dates
  - docs/design-notes/cross-strata-dreamer.md           # RATIFIED — the per-scope-grant regime; castle dispatches are grants under it
  - docs/design-notes/sigma-fibers-and-multiscale-dreaming.md  # RATIFIED — the axis table; castle tempo is result-side, never a scope coordinate
  - docs/design-notes/recursive-dreaming-bounded-by-grounding.md  # DRAFT — the four safety rules (+ the ratified fifth) the flinch must satisfy
  - docs/design-notes/dreamer-quality-suite-evaluation.md  # DRAFT — the harness the skill curve extends
supersedes: null
superseded_by: null
warrant: docs/brainstorms/synchronic-diachronic-dreamer.md
---

# Prediction castles — supersession forecasts, registration grading, the flinch, and the lease economy

> Filed by the chat agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it, and `gate-guard` denies any
> agent attempt (§10). `/graduate` refuses this note until `status: ratified`.
>
> Composed at **fable** (`claude-fable-5`, 2026-07-28) from the owner's six 2026-07-28 dreamer
> seeds (02:54Z–05:49Z) plus the 2026-07-21 falsifiable-forecaster capsule. **This note EXTENDS
> `dn-synchronic-diachronic-dreamer`** (the ratified dreamer note — agent-immutable; cited,
> never edited) in the family's EXTENDED pattern: its §2.6/§2.7 overlay machinery gains a layer
> above it, its §2.8 diachronic park is honored, and its laziness law gains its retention half.
> Chat-frame "decisions" in the warrant capsules are restated here as **proposals**; every
> ratification is the owner's alone. Sibling drafts in parallel PRs: **dn-scoped-context-queries**
> (PR #5 — the three-bound query compiler; its lattice rulings are ADOPTED here, not re-decided)
> and **dn-distributed-ecosystem** (forthcoming). Code claims were verified on disk this session
> (2026-07-28, worktree at `4c00ca5`).

## 1. Purpose and scope

### 1.1 What this note decides

The owner's seed, near-verbatim (2026-07-28T05:34Z, "last thought before sleep"): *"the
diachronic dreamer operates mostly with causal and supersession edges for its predictions, and
maybe in the interpretive realm it builds a castle, a 'palace', where based on temporal
observations it stacks causal edges that can include the synchronic's prediction nodes — weave a
prediction thread such that it predicts a supersession. … 'The current graph cut says something
is happening — how do I think this will evolve as I get more sensor data? Can I act retractively
to prepare me for potentially something?' A flinch."* Five more seeds the same night supplied the
grading rule (05:41Z), the geometry in four words (05:42Z), the lifecycle (05:46Z), and the clock
law (05:49Z); the 02:54Z reference-signal capsule supplies the §1 frame its own park promised.

This note decides:

1. **The prediction unit (§2.1):** the supersession event, graded against the corpus's own
   supersession ledgers; the dreamer's skill becomes a measured curve — study-not-product,
   applied to dreaming.
2. **The castle object (§2.2):** what a castle *is*, where it lives (the `interpreted@castle`
   refinement — the sibling note's lattice ruling, adopted), and how it relates to the ratified
   HYPOTHETICAL overlay machinery — **a new layer above it, not the same object refined**.
3. **Grading = registration (§2.3):** the scope-sweep rule (same query, semantic+temporal fixed,
   authority swept), misregistration as the error, the declared alignment tolerance — and the
   observation that grading is *synchronic*.
4. **The flinch (§2.4):** the dreamer's only motor form — internal, reversible, cost-asymmetric,
   bidirectional in time, strictly below every Track G effect tier; shown consistent with the
   recursive-dreaming safety rules; the flinch-watcher as a standing union-bound query.
5. **The lifecycle (§2.5):** retention asymmetry as law (evidence permanent, interpretation
   leased), the mechanical state machine, the lease floor, grades as permanent residue — and one
   deliberate refinement of the warrant's "touch" definition, with its tension named.
6. **The clocks (§2.6):** TTL derived, never configured — grounded honestly against what the
   ratified clock family actually built (certified cuts BUILT; no global-clock park exists to
   re-open); uniformity (κ is a parameter, not a fork); selection lives in the attention budget.
7. **The reconciliation (§2.7):** section-by-section EXTEND rulings against the ratified dreamer
   note, so nothing is absorbed silently.

### 1.2 Non-goals

Explicit, because wrong non-goals fail silently forever (finding-0150 — non-goals are
load-bearing; inferred clauses carry their marker for the ratification gate).

- **No build.** Design only; graduation follows ratification, and nothing here preempts the
  ratified dreamer note's own staging — in particular **SD-a** (its parked diachronic
  interval-window execution) stays parked exactly as written (§2.6, §2.7).
- **Not the query compiler.** The three-bound compilation, the authority axis's definition, and
  the union bound's legality conditions belong to `dn-scoped-context-queries` (PR #5, draft —
  "the corpus as its own onboarding organ"). This note *consumes* the epistemic duty and the
  union bound; it re-defines neither.
- **Not the deployment/ecosystem architecture.** Panic-seals, envelope encryption, node
  federation belong to `dn-distributed-ecosystem` (sibling PR, forthcoming).
- [INFERENCE] **No new embedding grain beyond a parked derived thread grain.** The single-scale
  chunk-grain decision stands (`core/kernel/stores/sourceset.py` — a source object IS the set of
  its idea-vectors); trajectory/motif embedding is parked (PC-b), a *derived* grain if it ever
  enters, never a re-embedding.
- [INFERENCE] **No effector capability for dreams, ever.** The flinch is not a small effect; it
  is *zero* effect — `W_world = NONE`, below the SENSING floor of the effector chain (§2.4). No
  claim in this note licenses any dream-adjacent path into `ops/effect_*` machinery.
- [INFERENCE] **No promotion-path change.** The ratified §2.6-3 law stands verbatim: there is no
  promotion path from HYPOTHETICAL to anything, and castle content never crosses into the
  warranted chain. Grades cross (§2.5) — as new evidence *about the dreamer*, not as castle
  content.
- [INFERENCE] **No change to `MIRROR_READABLE`, the verdict taxonomy, the G0–G4 gate chain, or
  any ratified note.** All cited, none edited; castle dispatches are grants under the ratified
  per-scope regime (`dn-cross-strata-dreamer`, owner ruling 2026-07-16).

## 2. Principles / decision

### 2.0 The DRY audit — what exists, and the five genuinely new things

Per the §2-manifest discipline (owner rule: reuse before re-implement), the machinery this note
rides, verified on disk 2026-07-28:

| capability | existing home | status |
|---|---|---|
| the dispatch record (DreamCharter: scope grant, instrument grant ⊆ INSTRUMENT_MAX, budget, gauge) | `core/dreaming/charter.py` (bp-079, D-0) | built |
| the arrow-read census (cycles, diamonds, reach-backs — witnessed, gauge-immune) | `core/graph/census.py` (bp-080, D-1) | built |
| HYPOTHETICAL stratum + generation-clocked staging store (N_hyp; no promotion path, structural) | `core/kernel/scope.py:95`, `core/stores/staging.py` (bp-081, H-0/H-1) | built |
| overlay influence + the conditioning law (`infl_R(Δ) = R(G∪Δ) − R(G)`; with/without taint diff) | `core/graph/influence.py` (bp-082, H-2) | built |
| certified cuts (frontier + {COMMIT, TROUGH, HANDOFF} certificates; crossing-edge refusal) | `core/temporal/spine.py` (GC-3, bp-055) | built |
| per-stratum clocks as spine restrictions; the clock atlas T-meet seam | `core/kernel/scope.py:223-230` (`Clock.N_S`), `:376-384` (`ClockAtlas`) | built |
| the authored-supersession ledger (owner-declared K₀↔K₀; `MachineAuthorityRefused` structural) | `core/stores/authored_supersession.py:48,:136` | built |
| the derivation hypergraph ℋ (`derives` B-arcs, acyclic; interpreted-only provenance, structural) | `core/stores/derived.py:46,:62-76` | built |
| the effector blast-radius chain (SENSING-floored) + the NONE floor below it | `ops/effects.py:63`, `core/kernel/scope.py:467-472` | built |
| the three-bound query compiler; the authority bound as Σ-refinement; the union bound's legality | `dn-scoped-context-queries` (PR #5) | draft, adopted |
| interval-window semantics (σ_*/σ^* transports; windows on declared clocks) | `dn-temporal-retrieval-algebra` §2.2 | ratified |
| the dreamer-quality harness (per-grant A/B lanes) | `dn-dreamer-quality-suite-evaluation` | draft |

**Genuinely new in this note — five things**, each with its warrant: (N1) the **castle** — a
leased, addressable interpretive construction at `interpreted@castle`, carrying the typed
(prediction ⟶ target) relation (§2.2; warrant 05:34Z/05:42Z); (N2) the **prediction unit and its
grading target** — supersession events against the ledger, the skill curve as residue (§2.1;
warrant 05:34Z + 2026-07-21); (N3) the **registration grading rule** — scope-sweep composed with
the built influence diff (§2.3; warrant 05:41Z/05:42Z); (N4) the **flinch** class and the
flinch-watcher (§2.4; warrant 05:34Z); (N5) the **lease economy** — the derived-TTL law, the
touch definition, the mechanical state machine (§2.5–2.6; warrant 05:46Z/05:49Z). Everything
else is composition of the table above.

### 2.1 PC-1 — the prediction unit: supersession events, graded against the ledger

**The unit.** A diachronic prediction is a claim of the form *"artifact/belief/edge X will be
superseded, within window W on clock κ, by something of shape S"* — the owner's *"I saw this
pattern loosely occur so I think it will happen at this time like this."* The 2026-07-21 seed
made the dreamer a falsifiable forecaster; the 05:34Z seed names WHAT it forecasts. Supersession
is already a first-class typed event family in the corpus, so every prediction is gradeable
against a ledger the dreamer cannot touch:

- **The v1 grading target is the authored-supersession ledger**
  (`core/stores/authored_supersession.py` — owner-declared K₀↔K₀ document supersessions,
  append-only). Its write boundary is structural: `record()` requires a construction-guarded
  `OwnerDeclaration` and raises `MachineAuthorityRefused` otherwise (:48, :136). **The dreamer
  is structurally incapable of causing the events it predicts** — at the write boundary, the
  forecast target is machine-uninfluenceable, which is the cheap half of the self-fulfilling
  confound's mitigation. (The expensive half — the owner reads a dream and then supersedes; an
  exposure-witness / held-out shadow arm — stays with the 2026-07-21 capsule's open questions
  and the quality-suite's graduation, carried in §Open questions.)
- **The adjacent event families** — per-doc version-chain supersessions
  (`core/stores/versions.py`) and dialogue claim-supersede ops — are spine chains too (GC g1)
  and are lawful grading targets; whether v1 grades only the ledger or the union is a
  graduation-time call (parked PC-d). The design is target-family-generic; the ledger is the
  exemplar because every event on it is owner-authored ground truth.

**The skill curve is measured residue — study-not-product, applied to dreaming.** Every graded
forecast leaves a grade (§2.5: grades outlive castles); the curve *predicted-vs-actual over
time, keyed by horizon and target stratum* is computed over exactly that residue. It extends
`dn-dreamer-quality-suite-evaluation` (draft — the harness) with a retrodictive-skill axis, as
that capsule already parked. Dreams earn trust by measured forecast skill, not eloquence.

**Forecast issuance is synchronic — the staging honesty.** A forecast is issued *at a certified
cut*: the dispatch reads the present graph (arrows included — the built census is exactly
"direction is time's residue," ratified §2.8's clock-free v1) plus the supersession ledgers as
present state, and writes an interpreted artifact. No interval-window transport is needed to
*issue* or to *grade* (§2.3). What DOES need interval windows is **motif mining** — *"I saw this
pattern loosely occur"* as retrieval over past trajectory — and that is diachronic execution,
which stays behind the ratified SD-a park (§2.6, §2.7). v1 castles are built from synchronic
reads; the pattern library deepens when SD-a unparks, without changing any surface here.

### 2.2 PC-2 — the castle: a new layer above the overlay, in the same coordinate system

**The reconciliation this section owes (the ratified §2.6/§2.7 question): the castle is NOT the
hypothetical subspace refined further — it is a distinct object one layer above it, which USES
the overlay machinery as its workbench.** The two objects answer different questions:

- The ratified HYPOTHETICAL overlay (SD-6, built bp-081) answers *"where may counterfactual rows
  exist so instruments can read `graph ∪ Δ`?"* — a per-dispatch, generation-addressed
  **read-composition** mechanism. Its rows are scratch: never corpus, no promotion path,
  tombstoned on expiry, invisible to every grant that does not name HYPOTHETICAL.
- The castle answers *"where does a persistent, addressable, graded interpretive construction
  live?"* — an **artifact** question. A castle takes *"many dreams to build"* (owner, 05:46Z),
  survives across dispatches, carries a lifecycle state that queries can filter on, and is
  graded over weeks. None of that is staging-store semantics.

**Ruling (proposed): the castle realm is the refinement `interpreted@castle ⊂ interpreted` — the
sibling note's lattice decision, adopted verbatim** (`dn-scoped-context-queries` §2.2.2: statuses
and realms are refinement *elements* of the ratified refinement forest R, below existing base
strata; jurisdiction is an annotation on the compiled plan; no new lattice component). Castle
rows are system-inferred interpretation, which is exactly what the interpreted stratum holds:
they write through the `DerivedStore` (provenance structurally `interpreted` — no parameter
exists to write anything else), and prediction threads are `derives`-style hyperedges in the
derivation hypergraph ℋ (`core/stores/derived.py:62-76`), stacked causal edges with tails in
authored evidence and declared prediction nodes. The refinement element means the authority
bound reaches castles *by name*: default grants exclude the realm; `q(…, castle)` includes it —
warrant discipline survives dreaming because the query that retrieves a prediction says which
realm it came from.

**The overlay is the castle's workbench.** When a castle's predicted geometry must be read
*beside* the real graph — registration (§2.3), influence, the flinch-watcher's union view — its
predicted nodes/edges are staged as a HYPOTHETICAL overlay in exactly the ratified SD-6/SD-7
sense, and the built with/without machinery (`core/graph/influence.py`) does the comparison. The
conditioning law binds unchanged: any artifact derived while looking through the staged geometry
records `(subspace_id, generation, staged digests)` and inherits the overlay's TTL. Division of
labor, stated once: **the castle persists and is graded; the overlay is transiently staged per
read and never persists anything.**

**Same coordinate system — the union bound's condition (iii), adopted as an architectural
requirement.** The castle is built with the corpus's own coordinates: the same embedding space
(chunk grain; the parked thread grain would be derived *from* it, PC-b), the same clocks (spine
events, N_s restrictions), the same certified cuts — a different refinement stratum being the
ONLY offset. *Same base space, different fiber: comparison is projection, never translation*
(sibling §2.4.3). If the interpretive realm ever needed its own representation, no single query
could span prediction and evidence, and grading would need a translator — that is this section's
falsifier (F-PC2).

**The pairing is typed.** Owner, verbatim, the four-word compression (05:42Z): *"prediction
strata overlayed against target strata."* Each castle names its **target stratum** — the fiber
it forecasts — and (prediction ⟶ target) is itself a typed relation in the strata graph,
alongside the refinement relations already built. Per-stratum dreaming, per-stratum grading:
"predicting castles over the code stratum" is a WHERE clause (authority tier + castle state as
queryable fields), not a bespoke index.

### 2.3 PC-3 — grading is registration; error is misregistration; the sweep is the instrument

Owner, near-verbatim (05:41Z): *"you can compare a prediction [to] reality by changing the scope
of the same query… Under what bound are both predictions and evidence returned by the same
query?"*

**The scope-sweep rule (proposed as the family's grading law).** Hold the semantic and temporal
bounds fixed; sweep the authority bound: `q(s, t, castle)` returns the predicted thread,
`q(s, t, evidence)` returns what happened, and **the prediction error IS the difference of the
two projections**. No bespoke comparison machinery — the three-bound compiler
(`dn-scoped-context-queries`, PR #5) is already the grading instrument; the authority axis is
the epistemic axis you differentiate along (its §2.4 duty 3, whose definition that note owns and
this note consumes).

**The union bound is legal under exactly the sibling's three conditions** (adopted, not
re-decided): (i) explicitly requested; (ii) every atom carries its realm tag — never-bare-text
is what makes the union non-contaminating; (iii) shared coordinate system (§2.2). A union read
that includes castle rows is castle-conditioned exhaust and carries the §2.2 conditioning marks.

**Grading is registration — the imaging vocabulary, adopted with its warrant.** Two strata over
the same base coordinates, one epistemic offset apart: grading aligns the prediction overlay
against the target stratum, and the error is **misregistration**. Mechanically, the comparison
reuses the built influence family: stage the predicted thread as an overlay at the grading cut
and read the with/without differential per instrument — where the prediction materialized, the
overlay's edges coincide with real edges (zero differential on the integer family); where it
misregistered, the differential names exactly the staged elements that failed, leave-one-out
(CN-3 attribution, already generalized by the ratified SD-7). The **alignment tolerance** — how
much structural deviation still counts — must be DECLARED in the forecast (§2.5's triple), else
the forecast can be gamed vague-then-graded-loose. Whether the tolerance metric is
graph-structural, embedding-geometric, or both with declared weights is carried as an open
question (owner rules at graduation).

**Grading is synchronic — no diachronic dispatch required.** Both projections are read at ONE
certified cut (the grading cut): the castle rows exist *now* as records; the evidence exists
*now* as corpus. The forecast's content refers to the future, but reading and comparing are
present reads with authority swept. This is why the grading machinery deploys without touching
the SD-a park (§2.7) — the only interval-window consumer in this design is motif mining (§2.1).

### 2.4 PC-4 — the flinch: the dreamer's only motor form

Owner (05:34Z): *"Can I act retractively to prepare me for potentially something? A flinch."*

**Definition (proposed).** A flinch is the dreamer's ONLY motor form: an **internal, reversible,
cost-asymmetric** posture change triggered by a prediction — never an action. Bidirectional in
time: **forward** (pre-position: prefetch/warm context along the predicted thread, raise the
castle's registration-watch priority *within the attention budget*, pre-draft an owner-question
as interpreted material — filed only through normal channels), and **backward** (the owner's
"retractively", read as retro-: retrodiction — re-read history under the new thread,
re-annotating past observations the hypothesis now explains, as interpreted-tier annotations).
Cheap flinches justify false positives exactly the way biology justifies them — the cost
asymmetry is the design, so flinch frequency is a tunable expenditure, not an error rate.

**Strictly below every Track G effect tier — by type, not by discipline.** The effector chain is
SENSING-floored (`ops/effects.py:63` — `ReversibilityClass`, an IntEnum with no member below
SENSING); the capability lattice adds the `NONE` floor beneath it (`core/kernel/scope.py:467-472`
— `WorldReach.NONE`, "no world reach at all", held by every read-only View; and finding-0011's
standing fact: the deployed ceiling is `⊤_deployed.W_world = NONE`, no EffectView wired at any
tier). **A flinch lives at `W_world = NONE`**: it never constructs an `Effect`, never enters the
effect catalog/gate/ledger, and a dreamer grant's authority is the role's `(READ, W_Σ=1, NONE)`
— interpreted-only writes, zero world reach, unchanged from the ratified §2.2. "The model
advises; code acts" (non-negotiable #3) is untouched: the dreamer's strongest output is a
prepared stance and a graded forecast, never an effect.

**Consistency with the recursive-dreaming safety rules** (`dn-recursive-dreaming-bounded-by-
grounding`, draft — four rules; plus the fifth the ratified §2.7 added), shown rule by rule:

| rule | how the flinch/castle satisfies it |
|---|---|
| 1 — grounding ends in authored evidence (or marked hypothesis) | threads bottom out in authored anchors + marked prediction nodes; retrodiction cites authored history only |
| 2 — confidence decays with depth, never compounds | prediction nodes carry generation/depth; deeper castles are visibly less confident; lease renewal is NOT confidence (§2.5) |
| 3 — confidence and utility are separate axes | the attention budget (touch/extend) and the registration grade (alignment) are separate fields, never collapsed |
| 4 — the authored floor stays the fixed point | castle content never becomes ground truth (§1.2); grades cross as evidence about the DREAMER, not its claims |
| 5 — the conditioning law (ratified §2.7) | castle-conditioned exhaust carries `(castle, generation, staged digests)` and TTL-inherits; lapsed lease ⇒ it leaves surfacing |

Two of those rows compress load-bearing detail, restated in prose: rule 2's sharp edge is that
**touches keep a castle alive but never raise its standing** — renewal and confidence are
different currencies; and rule 3's is that selection spends attention while grading spends
nothing, so a well-attended castle can still grade badly (and must).

**The flinch-watcher.** The trigger is a **standing union-bound query** — the interleaved view of
predicted thread and arriving evidence, watched for **registration drift**: *"look through both
layers and flinch when they stop lining up"* (owner's stub, 05:42Z, restated). Its cadence
inherits the castle's clock (§2.6 — you do not poll a year-scale castle every minute). The
watcher READS; a triggered flinch is the internal posture change above; nothing in the loop has
world reach. Flinches leave typed traces (a flinch is an append — spine-visible), so the cost
asymmetry is itself measurable: flinches-per-landed-prediction is a harness metric, carried from
the capsule's open question into the quality suite's lane.

### 2.5 PC-5 — the lifecycle: evidence permanent, interpretation leased

**The retention asymmetry, proposed as law** (owner, 05:46Z: *"prediction space has TTL unless
touched; a castle can take many dreams to build"*): **the warranted corpus is keep-and-link
forever; the castle realm expires by default and lives only while touched.** An interpretation
nothing returns to has no living warrant to exist. This is also the noise-floor control for
union-bound queries (dead layers evaporate, so registration is computed against living
conjecture only) and the resource-ceiling philosophy applied to imagination — a lease, not a
landfill. **And it is the ratified laziness law's retention half, named as such:** the ratified
§2.4 made *evaluation* demand-driven (a requirement, not an optimization, because the graph
grows in size and time); tonight extends the same law to *retention* — do not retain
interpretation no evaluation demands. One law, two tenses: compute on demand; persist on
citation.

**The state machine — the artifact-chain discipline reaching into dream-space:**

    under-construction ──(triple complete)──▶ predicting ──(date reached | registration converged)──▶ graded
           │                                      │
           └────────── lease expiry ──▶ abandoned ◀┘

`abandoned` is reachable from the first two states only, by lease expiry; `graded` is terminal.

- **Promotion to `predicting` is MECHANICAL, never blessed.** A castle is `predicting` the
  moment its thread carries the complete **self-grading triple** — (target stratum,
  falsification date, alignment tolerance) — everything needed to grade it travels with it.
  Falsifiability is the promotion criterion; **there is no blessing gate in dream-space.** The
  two owner-only blessing gates guard the warranted chain (design notes and plan splits); dreams
  promote themselves by becoming gradeable, and the fresh distinction is load-bearing: blessing
  guards what may be *believed*; the triple only decides what may be *scored*. State is a
  queryable field (§2.2).
- **The falsification date is a T-object, never a wall date.** It is a declared window bound on
  the target stratum's clock (`T = (κ_target, W)` — the ratified temporal-retrieval semantics),
  or a certified-cut predicate; wall-denominated owner phrasing resolves at sweep time through
  the interval-valued, ambiguity-widening resolver posture the staging store already uses
  (Law C4: wall never orders).
- **The lease floor:** a `predicting` castle's lease window must contain its own falsification
  date — *a prediction must survive long enough to be wrong.* Under-construction castles ride a
  sliding touch-window; predicting castles hold a term lease.
- **Grades outlive castles.** When a castle is graded, the castle may evaporate but its GRADE
  crosses into the permanent realm — the outcome is evidence *of the dreamer's skill*, and
  evidence is forever. Dreams are mortal; the track record is immortal; §2.1's skill curve is
  computed over exactly this residue. Abandonment needs no tombstones-as-corpses: a
  started-vs-finished aggregate (the dreamer's focus ratio) is a telemetry row.

**"Touched" — the warrant's definition, refined, with the tension named.** The 05:46Z capsule
proposed touch = any citation event, *including a union-bound query hit*. Adopted with one
refinement, forced by the flinch-watcher itself: **a touch is a WRITE-side citation event** — a
dream extending the castle, a flinch citing it, a registration update against it — each an
append whose row references the castle (a spine-visible reads-from edge). **Bare read hits do
not renew.** The tension that forces this: the flinch-watcher is a *standing* union query over
every predicting castle; if its hits renewed leases, everything under watch would be immortal
and the watcher would defeat the mortality law it exists to observe. Reads mint no events
(GC Law C3); renewals must be events; so renewals are appends. A castle survives by earning NEW
citations, not by being looked at. This is a refinement of the chat-side scrutiny, not of the
owner's seed ("TTL unless touched" — the seed does not define touch); the owner rules the final
definition at ratification (falsifier F-PC6 covers the failure both ways).

**The flinch-runaway loop, closed.** A flinch may queue a dream; the dream renews a castle's
lease; but leases + the dream budget bound the loop — a castle that only ever gets
flinch-touched without advancing toward its triple spends lease renewals without earning
promotion, and the focus-ratio telemetry makes that visible.

### 2.6 PC-6 — the clocks: TTL derived, never configured; and the honest clock grounding

**The derivation rule** (owner, 05:49Z: *"timescales are just another clock for diachronic
dreamers… TTL is a dynamic value based on the timescale(s) of the derived castle"*): no single
TTL constant exists. Each castle derives its lease tempo from its own characteristic timescale —
**the target stratum's clock composed with the declared horizon of its threads**: construction
window and renewal size scale with it; a reflex gets a reflex's scaffolding window, a cathedral
a cathedral's. Castles span clocks (short-horizon prediction nodes stacking into a long-horizon
thread): each layer carries its own sub-lease, and **the castle's outer lease derives from the
slowest load-bearing layer**. The lease floor (§2.5) was already timescale-proportional by
accident — the falsification date scales with horizon; this makes the construction window
proportional on purpose.

**The honest grounding — what the clock substrate actually is (checked against reality
2026-07-28, which outranks tonight's chat framing).** Two of tonight's threads framed
"per-strata clocks instead of a global clock" as a pending reframe against an old park
(`dn-agent-taxonomy`'s diachronic row, "blocked on certified cuts (G3)"). The reality:

- `dn-global-event-clock` is **RATIFIED**, and its N is *already* per-store-total /
  globally-partial — a derived, read-side causal spine over per-store append chains, with a
  write-side global sequencer **rejected structurally** (its GC-a park, "recorded so it is never
  re-litigated casually"). Per-stratum clocks N_s are its restrictions, materialized
  (`Clock.N_S`, `core/kernel/scope.py:230`); cross-clock meets compose through the built atlas.
- **GC-3 certified cuts are BUILT** (bp-055; `core/temporal/spine.py` — frontier + {COMMIT,
  TROUGH, HANDOFF} certificates, crossing-edge refusal). The old "blocked on certified cuts"
  park text is stale, and the ratified dreamer note already restated it honestly
  (finding-0126): what actually remains behind **SD-a** is the interval-window instrument
  family (`graph-at-a-past-cut`'s own graduation), the harness's interval lane, and the owner's
  sequencing — with D-1 sealed (bp-080), *half* of SD-a's stated re-entry is now met, and the
  other half (the past-cut family's graduation) is not. **The park stands; this note does not
  touch it** — nothing here needs it (§2.1, §2.3).

So there is no global master clock to depose and no clock park to re-open: *"timescales are just
another clock"* lands as **the ratified κ parameter of `T = (κ, W)`** — exactly the coordinate
the algebra already carries. What tonight genuinely adds is the *derivation rule* above, plus
one honest residue, parked (PC-c): the **characteristic-timescale estimator** — how many N_s
ticks constitute a stratum's "tempo" (tick-density measurement; the clock-curvature thread's
kin) — is neither designed nor built; until it exists, the derivation composes the declared
horizon with the target clock's ticks directly.

**Castle tempo is result-side, never a scope coordinate.** The ratified capability-visibility
test (`dn-global-event-clock` §2.6: does the parameter change what the client may see?) rules
it: a castle's tempo changes no denoted events — it parameterizes lease bookkeeping and watch
cadence over unchanged grants. So no new `Clock` member, no fifth axis; tempo is a derived
reading (`Res`/`Rate`-typed at graduation), the same verdict σ received in `dn-sigma-fibers`
§2.6.

**Uniformity — one dreamer at every horizon.** The 5-minute prediction and the year prediction
are the same dreamer role, the same castle type, the same grading geometry — **κ is a
parameter of the grant, not a fork.** This is the ratified §2.1 verdict ("one dreamer, no new
axis; synchronic/diachronic/past/counterfactual are values of the grant") extended one
coordinate: horizon joins them as a T-window value. No separate short-term predictor exists;
falsifier F-PC7 kills this section if the horizons ever demand structurally different machinery.

**Selection lives in the attention budget, not wall-time.** The clock only sets the UNITS of
survival; the touch budget does the selecting. A year-scale castle is not granted a free year —
it is granted year-scale renewal *windows*, renewals cost touches, and touches are budgeted
dream-attention flowing toward earned standing. Strong ideas evolve because dreams keep choosing
them; TTL translates that choice into survival at the right tempo. Scarcity is attention; the
clock is its unit conversion. (What "earned standing" is pre-grade, mechanically, is carried as
an open question — the owner picks the falsifiable subset at graduation.) Registration cadence
and flinch tempo inherit the castle's clock (§2.4).

### 2.7 PC-7 — reconciliation with the ratified dreamer note, section by section

No silent absorption; each ruling carries its locus. The ratified note is agent-immutable (A8);
every row below is EXTEND-from-outside, the family's pattern.

| ratified locus | ruling | how |
|---|---|---|
| §2.1 (one dreamer, no new axis) | **EXTEND** | horizon is a T-window value of the same grant; the castle realm is a Σ-refinement (sibling) — dispatches stay `(Σ,E,T,A)` points |
| §2.2 (DreamCharter) | **EXTEND** | castle/grading/flinch dispatches are DreamCharters: grant names `interpreted@castle` (± HYPOTHETICAL); instruments incl. census/influence |
| §2.6 (HYPOTHETICAL fold-in) | **EXTEND** | the castle is a NEW LAYER ABOVE the overlay (§2.2 here): overlay = per-read workbench; no staging semantics change; no promotion path |
| §2.7 (influence + conditioning) | **EXTEND** | the with/without diff is the misregistration instrument (§2.3); the conditioning law binds castle exhaust verbatim |
| §2.8 (diachronic axis; SD-a) | **EXTEND, park honored** | issuance and grading are synchronic (§2.1/§2.3); motif mining is the one interval consumer and waits on SD-a (§2.6) |
| §2.4 (laziness laws L1–L5) | **EXTEND** | the lease economy is laziness's retention half (§2.5): compute on demand, persist on citation; L2 localizes castle-store internals |
| §3 (plan decomposition) | **honored** | D-0/D-1/H-0/H-1/H-2 sealed (bp-079..082; bp-055); §3 here queues as a NEW wave behind ratification |

Constraints honored, the binding table: mirror firewall — castle rows are interpreted-tier,
`∉ MIRROR_READABLE`, unreachable by the mirror's reflective dreamer (I6 verbatim); model
advises/code acts — grading, sweeps, leases, watchers are code, the model appears only at
narration over granted reads; memory ceiling — census/influence/registration are model-free
arithmetic; sacred fixed points — 𝔇 subtracted from every grant, no lever names golden;
append-only — castles append, expiry tombstones, grades append; wall never orders — Law C4
via the staging resolver posture (§2.5).

## 3. Consequences — what this note licenses (on ratification; `/graduate` decides splits)

Sequenced BEHIND ratification and behind anything the owner has queued; nothing here preempts
SD-a or the past-cut family's graduation. Sketch of session-sized plans:

- **P-0 — the castle object + lifecycle**: the `interpreted@castle` refinement element (additive
  lattice extension, the bp-081 enum-precedent shape), the castle artifact class over the
  DerivedStore with the (prediction ⟶ target) relation and state field, the lease bookkeeping +
  trough-tier expiry sweep (the staging sweep's sibling), the mechanical-promotion check
  (triple-complete ⇒ `predicting`). Acceptance: state-machine property tests; lease-floor test
  (a predicting castle cannot expire pre-falsification-date); F-PC5/F-PC6 as tests.
- **P-1 — forecast issuance + registration grading**: the forecast artifact carrying the
  self-grading triple; the scope-sweep grading read (consumes the sibling's compiler when built,
  or its View-level equivalent meanwhile); misregistration via the influence diff; the grade
  residue appended permanently; the skill-curve lane in the quality suite. Acceptance: a planted
  ledger event grades a matching forecast within tolerance and fails a mismatched one; grades
  survive castle expiry (F-PC6); determinism at a pinned cut.
- **P-2 — the flinch + flinch-watcher**: the typed flinch trace, the standing union-bound watch
  at castle-clock cadence, drift-triggered posture changes, the flinches-per-landed-prediction
  metric. Acceptance: F-PC4 as tests (no Effect construction reachable; every flinch reversible
  and internal); watcher reads renew nothing.
- **Explicitly NOT licensed:** diachronic motif mining (SD-a; its re-entry is restated in §2.6);
  the thread/motif derived grain (PC-b); the characteristic-timescale estimator (PC-c); any
  effector path for dreams (never); any promotion path from castle content (never).

## 4. Wiring & enablement

**How it wires:** every dispatch mode this note licenses lands behind the R&D flag boundary
exactly as the ratified note's D/H waves did — `require_rnd_enabled`
(`core/dreaming/rnd.py:31`) fronts every new entry point until the owner wires it on. The
graduating plans must build, in write_scope: (a) a **castle config block** (e.g.
`[dreamer.castles] enabled=false`, lease constant k, budget shares) in the config schema;
(b) the **trough-tier lease sweep** registered beside the existing staging sweep (daemon
housekeeping, no new process); (c) the **registration-watch scheduling** at castle-clock
cadence inside the existing dream/attention budget; (d) a **read surface for the skill curve
and focus ratio** (a quality-suite lane plus a `palace`-side read, shape decided at
graduation). Gated off is fine; absent is not (wiring-is-part-of-finishing, owner 2026-07-22).

**What it takes to flip it on:** (a) the P-0..P-2 builds land flag-off with the config block
present; (b) the owner sets `[dreamer.castles] enabled=true` and runs the owner-visible seed:
one castle built over a chosen target stratum, its triple declared, one flinch-watcher cycle
observed, and — after its falsification window — the first grade landing in the permanent
residue. Deskcheck before the track is called done.

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| PC-a | diachronic motif mining (interval-window trajectory retrieval) | not designed; v1 castles build from synchronic reads (§2.1) | SD-a unparks (owner-sequenced; §2.6) |
| PC-b | thread/motif embedding as a derived grain | none built; hyperedge ℋ is the candidate substrate; chunk grain stays the only grain | graduation + retrieval needs geometry ℋ lacks |
| PC-c | characteristic-timescale estimator (tempo measurement) | not designed; TTL composes declared horizon with target-clock ticks | a castle plan needs tempo this cannot express |
| PC-d | grading-target extent (ledger only, or wider) | ledger-primary (owner-authored ground truth); target-family-generic design | P-1 pins the v1 target set |
| PC-e | castle store home: DerivedStore vs a dedicated leased store | DerivedStore (reuse-first; regenerable suits leases) | P-0 graduation; awkward lease bookkeeping re-opens it |

## Falsifiers (the load-bearing set)

- **F-PC1** (§2.2) — the castle lifecycle turns out to need staging-store rows that persist
  beyond generation semantics, or any promotion path out of HYPOTHETICAL ⇒ the two-layer
  reconciliation is wrong; re-decide the layering by supersession, never by quiet drift.
- **F-PC2** (§2.2/§2.3) — grading prediction against evidence needs a representation translator
  (separate embedding space or clocks) ⇒ the shared-coordinate condition failed (inherits the
  sibling's union-bound falsifier); the castle realm's construction is re-opened.
- **F-PC3** (§2.1) — a graded forecast whose score requires model judgment about whether the
  ledger event "counts" (not computable from the triple + the ledger row) ⇒ the unit is not the
  falsifiable one claimed; the triple is incomplete and must be re-specified.
- **F-PC4** (§2.4) — any flinch that constructs an `Effect`, enters the effect gate/ledger, or
  holds `W_world > NONE`; or a flinch residue that cannot be reversed or that outlives its
  castle's conditioning marks ⇒ the motor-form claim is broken; the flinch class is frozen until
  re-ruled.
- **F-PC5** (§2.5) — a castle reaching `predicting` without its complete triple, or any
  dream-space state flip that waits on a blessing ⇒ the mechanical-promotion law failed (in
  either direction).
- **F-PC6** (§2.5) — a `predicting` castle expiring before its falsification date; a grade lost
  when its castle evaporates; an untouched castle surviving indefinitely; or the standing
  watcher's reads renewing leases (the immortality bug) ⇒ the lease economy is broken.
- **F-PC7** (§2.6) — a horizon that demands structurally different dreamer machinery (a separate
  short-term predictor), or a TTL that must be hand-set per castle to behave ⇒ the uniformity /
  derived-TTL claims fail; the clock parameterization is re-opened.
- **F-PC8** (§2.1) — grades accumulating without a computable skill curve keyed by horizon and
  target stratum ⇒ the measured-residue claim is decorative; study-not-product failed here.

## Open questions

Carried from the warrant capsules (owner rules at ratification/graduation):

1. **The alignment metric:** graph-structural (motif/edit distance), embedding-geometric (thread
   distance in the shared space), or both with declared weights? (05:41Z capsule.)
2. **Earned standing pre-grade, mechanically:** registration trend of sub-predictions, Σ of
   foundations (the warrant sense — a belief's support set), touch diversity? Pick the
   falsifiable subset at graduation. (05:49Z capsule.)
3. **Rival castles over one target stratum:** ensemble (co-existence is signal) or conflict the
   dreamer must resolve before promotion? (05:46Z capsule.)
4. **The TTL constant k** (`TTL = k × timescale`): does it live in the levers overlay
   (`dn-evaluation-harness`'s self-mod knob discipline), making the dreamer's patience itself
   tunable-and-audited? (05:49Z capsule.)
5. **The exposure confound:** the held-out shadow arm (forecasts never surfaced, scored beside
   surfaced ones) and exposure witnessing — carried from the 2026-07-21 capsule into the
   quality-suite's graduation.

Added by this note (beyond the capsules):

6. **The touch ruling (§2.5):** does the owner adopt write-side-citation-only touches, or should
   *some* read class renew (e.g. owner-initiated reads only — reads the attention budget did not
   schedule)? The watcher-immortality bug constrains but does not fully determine the answer.
7. **The grade's type and home:** is a registration grade `Inv` or `Res(π)`-typed (it carries an
   alignment tolerance — a ruler), and which permanent store holds the residue (eval-results
   lane vs telemetry vs a grade ledger)? Graduation pins it; the type question is decidable now.
8. **Retrodiction's surface:** backward flinches re-annotate history as interpreted material —
   do these annotations enter the same castle (one lease) or a sibling retrodiction layer with
   its own lease, so a dead forecast's useful re-reading of history can outlive it?

## Cross-references

- `docs/brainstorms/synchronic-diachronic-dreamer.md` — **the warrant**: 2026-07-28T02:54Z (the
  reference-signal frame; the brief retired), 05:34Z (supersession + the flinch), 05:41Z
  (scope-sweep grading; the union-bound question), 05:42Z (the four-word geometry), 05:46Z (the
  lifecycle), 05:49Z (timescale-derived TTL); plus 2026-07-21T02:20Z (the falsifiable
  forecaster; the exposure confound).
- `docs/design-notes/synchronic-diachronic-dreamer.md` (`dn-synchronic-diachronic-dreamer`,
  RATIFIED) — **EXTENDED**, per §2.7's table; its SD-6/SD-7/SD-8 and laziness laws are this
  note's chassis.
- `docs/design-notes/scoped-context-queries.md` (`dn-scoped-context-queries`, PR #5, draft) —
  the three-bound compiler; the authority bound as Σ-refinement; `interpreted@castle` as a
  refinement element; the union bound's three legality conditions (its §2.2.2/§2.4 — adopted
  here, not re-decided).
- **dn-distributed-ecosystem** (sibling PR, forthcoming) — jurisdiction duty; per-node clock
  framing (its capsules share tonight's warrant night).
- `docs/design-notes/global-event-clock.md` (`dn-global-event-clock`, RATIFIED) — the spine
  (Ev,≼); N_s; certified cuts (GC-3 BUILT, bp-055); Law C3/C4; the capability-visibility test
  §2.6 here applies to castle tempo.
- `docs/design-notes/temporal-retrieval-algebra.md` (`dn-temporal-retrieval-algebra`, RATIFIED)
  — window semantics for falsification dates and lease floors.
- `docs/design-notes/capability-scope-algebra.md` (`dn-capability-scope`, RATIFIED) — the
  (Σ,E,T,A) lattice; refinements as elements; `W_world`; `⊤_deployed.W_world = NONE`.
- `docs/design-notes/cross-strata-dreamer.md` (`dn-cross-strata-dreamer`, RATIFIED) — the
  per-scope-grant regime castle dispatches run under; G0–G4 unchanged.
- `docs/design-notes/sigma-fibers-and-multiscale-dreaming.md` (`dn-sigma-fibers`, RATIFIED) —
  the axis table; the result-side-not-scope verdict §2.6 here reuses.
- `docs/design-notes/recursive-dreaming-bounded-by-grounding.md`
  (`dn-recursive-dreaming-bounded-by-grounding`, draft) — the four safety rules the flinch
  satisfies (§2.4's table); the ratified fifth (conditioning) binds via SD-7.
- `docs/design-notes/dreamer-quality-suite-evaluation.md`
  (`dn-dreamer-quality-suite-evaluation`, draft) — the harness the skill curve and
  flinch-economy metrics extend.
- `docs/design-notes/hands-and-the-effector-layer.md` + `docs/findings/finding-0011.md` — the
  blast-radius ladder the flinch sits below; the deployed `W_world = NONE` ceiling.
- `docs/findings/finding-0126.md` — the SD-a park's re-entry, restated (consumed §2.6);
  `docs/findings/finding-0150.md` — non-goals are load-bearing (§1.2 discipline).
- **Code (verified on disk 2026-07-28, worktree at `4c00ca5`):**
  `core/stores/authored_supersession.py` (:48 `MachineAuthorityRefused`; :136 `record()`
  owner-declaration-guarded — the grading target the dreamer cannot write) ·
  `core/stores/derived.py` (:46 `DERIVES`; :62-76 the hypergraph ℋ junction; interpreted-only,
  structural) · `core/stores/staging.py` (generations N_hyp; `read_at(g)`; tombstone; no
  promotion path — the overlay workbench) · `core/graph/influence.py` (`infl_R`; the
  with/without diff §2.3 reuses) · `core/graph/census.py` (the arrow-read senses) ·
  `core/dreaming/charter.py` (the DreamCharter §2.7 extends) · `core/dreaming/rnd.py` (:31
  `require_rnd_enabled` — the §4 flag boundary) · `core/temporal/spine.py` (:175 certificates;
  :218 `CertifiedCut`; :620 `Spine`) · `core/kernel/scope.py` (:95 `Stratum.HYPOTHETICAL`;
  :223-230 `Clock` incl. `N_S`; :376-384 `ClockAtlas`; :467-472 `WorldReach` NONE floor) ·
  `core/kernel/stores/sourceset.py` (the single-scale chunk grain PC-b would derive from) ·
  `core/stores/versions.py` (per-doc supersession chains, PC-d).
- **Build plans (all `complete`; the ratified note's §3 executed):** bp-079 (D-0 DreamCharter) ·
  bp-080 (D-1 arrow-read) · bp-081 (H-0/H-1 HYPOTHETICAL + staging) · bp-082 (H-2 influence +
  conditioning) · bp-055 (GC-3 certified cuts).
