---
type: design-note
id: dn-agentic-loop
status: draft               # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: mostly-built  # the loop's valves exist at four different wiring states — §2.0 is the honest inventory
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/brainstorms/reference-integrator.md         # WARRANT — the reference sensor + active/passive sensing + the owner's hands reconciliation
  - docs/brainstorms/agent-causal-loop.md            # WARRANT — the causal loop, exhaust-as-sensor, the scope asymmetry (all capsules)
  - docs/design-notes/hands-and-the-effector-layer.md    # Track G — acting/sensing hands, the gate, blast radius (the external loop's machinery)
  - docs/design-notes/observed-data-and-the-assistant-tier.md  # the observed stratum + firewall ("senses what happened")
  - docs/design-notes/self-sensing.md                # RATIFIED — φ_self; the regress safety line §2.4 must honor
  - docs/design-notes/chat-sensor.md                 # RATIFIED — φ_chat; CS-2/CS-3/CS-5 bind the exhaust ruling
  - docs/design-notes/exhaust-lane.md                # RATIFIED — "exhaust never re-enters" (§2.2 there); honored verbatim in §2.4
  - docs/design-notes/agent-taxonomy.md              # RATIFIED — roles as scope signatures; the integrator's witness law; fiber C
  - docs/design-notes/capability-scope-algebra.md    # RATIFIED — the (Σ,E,T,A) lattice the §2.3 profiles are points of
  - docs/design-notes/synchronic-diachronic-dreamer.md  # RATIFIED — DreamCharter/force (bp-079), influence/conditioning (bp-082) = the internal probe
  - docs/design-notes/recursive-dreaming-bounded-by-grounding.md  # the grounding law the exhaust guardrail rides
  - docs/design-notes/authorship-distance-axis.md    # DRAFT — the α axis the self-authored class routes to
  - docs/design-notes/the-sacred-boundary.md         # the zone principle §2.3 derives from
  - docs/design-notes/the-edge-model.md              # edge assertion authority (E_disp/E_geom discipline)
  - docs/findings/finding-0011.md                    # max reachable effector tier = NONE — the external loop's dormancy, grounded on, never relitigated
  - docs/findings/finding-0141.md                    # filed by this pass — the internal probe loop is built-not-wired (posture accuracy)
supersedes: null
superseded_by: null
warrant: docs/brainstorms/agent-causal-loop.md
---

# The agentic loop — sense → act → confirm, reconciled with the built hands, sensors, and probes

> Composed at **fable** (`claude-fable-5`, 2026-07-21, session-39 dispatched design pass — the
> owner's "wrap it all up" synthesis over the sensing/acting brainstorm cluster). Filed as
> `draft`; ratification is an owner-only hand edit; `/graduate` refuses this note until
> `status: ratified`. **Design only; no build is authorized beyond §3's small licensed items.**
> This is a synthesis + reconciliation + gap-catch, not a green field: nearly all of the loop's
> machinery is already built, and the owner said so mid-brainstorm. The job here is to name the
> loop in the vocabulary the system already has (DRY at the design level), correct the two
> places the brainstorm's framing overstates, state the one genuinely new typed thing (the scope
> profiles, §2.3), and catch what is actually missing (§2.6). Every nontrivial claim is graded
> (`[ESTABLISHED]`/`[DERIVED]`/`[INFERENCE]`/`[ANALOGY]`); external-literature claims are
> `[FROM MEMORY]`. Code and store claims were verified on disk this session (2026-07-21,
> live data dir read-only; worktree tree at `f294c3e`). Ratified notes are cited, never edited
> (A8). The effector dormancy (finding-0011) is the ground this note stands on, not a question
> it reopens.

## 1. Purpose and scope

The 2026-07-21 brainstorm cluster (`reference-integrator.md`, `agent-causal-loop.md`) produced
five connected ideas: (1) sensors are **passive** (standing projections) or **active** (directed
instruments — the microscope); (2) sense → act → confirm is a **closed causal loop** the agent
inscribes into the corpus by acting; (3) the loop's application is **self**: Ouroboros senses its
own gaps and corrects itself; (4) the agent's **exhaust is itself a sensor** — its outputs
re-enter as sensed data; (5) internal and external acting carry **inverted scope profiles**.
The owner's own mid-thread correction stands as this note's charter: *"we already built the
framework a while ago"* — so the deliverable is a reconciliation map, not new machinery.

This note decides: the machinery inventory at honest wiring states (§2.0); the reconciliation
map — what is naming vs what is new (§2.1); the loop as a typed object, with two corrections to
the brainstorm's claims (§2.2); the internal/external scope asymmetry as two named profiles in
the ratified algebra, derived from the zone boundary (§2.3); the exhaust-as-sensor ruling,
measured first, with its guardrail bound (§2.4); the exhaust stratum + the provenance spine —
the owner's mid-pass refinement, ruled on both axes with trust propagation (§2.4b); the
self-sensing → gap → correct control law, split by gate tier (§2.5); the gap catalog, ranked
(§2.6); per-note reconciliation rulings (§2.7); and the measure-first battery with baselines
taken this session (§2.8).

**Out of scope, explicitly:** relitigating the effector dormancy (finding-0011 — the external
loop's act valve stays at tier NONE until a deliberate, separate owner act); any change to
`MIRROR_READABLE`, the verdict taxonomy, or any ratified text; the Track-D correlator's own
charter (named as a gap, not designed here); the reference sensor's build (its parent brainstorm
owns its measure-first track — this note only places it on the map); wiring the DreamCharter
dispatch live (the R&D flag is the owner's lever); anything that preempts the sequenced queue
(the dreamer track just sealed bp-079–082; dn-fiber-geometry and dn-inner-outer-core await
owner ratification — nothing here blocks or is blocked by them).

## 2. Principles / decisions

### 2.0 The machinery inventory — five valves, four wiring states (verified)

The loop is not one mechanism; it is five valves at different states. Everything below was
verified on disk / in the live stores this session. `[ESTABLISHED]`

| valve | machinery | wiring state | evidence |
|---|---|---|---|
| **passive sensing** (standing φ) | φ_chat (`ops/chat_sensor.py`), φ_code (`ops/code_sensor.py`), φ_self (`ops/self_sensor.py`), vault ingest | **LIVE** in the daemon (`ops/lifecycle/launcher.py:246,316`) | chatlog 7,966 utterances (6,429 agent / 1,537 owner); chat_events 19,493; agent_observations 37; code stores populated |
| **integration** (witnessing the loop) | the chat↔code↔doc integrator (`core/integrator.py`), C-edges + witness bracket, C-coverage gauge | **LIVE** (`launcher.py:238,325`) | causal_edges 4,084 rows; `CausalEdgeStore`; `coverage()` built |
| **internal probe** (perturb the graph, read the diff) | DreamCharter + `force` (bp-079, `core/dreaming/charter.py`), HYPOTHETICAL/staging (bp-081), influence + conditioning law (bp-082) | **BUILT, flag-gated, not wired** — `[dream_rnd] enabled=false` (`config/defaults.toml:263-267`); no live entry point constructs a charter | finding-0141 (this pass) |
| **external act** (perturb the world) | Track G hands: `Effect`/gate/ledger/exec, `edge/effectors/` | **BUILT, DORMANT by design** — max reachable tier NONE | finding-0011; `[effectors] enabled=false` |
| **external sense-back** (sense what happened) | observed stratum + `ObservedView` (built); the Track-D **correlator** (designed only) | **PARTIAL** — the receiving type exists; the consumer that would close the return path does not | dn-observed-data / dn-cross-strata-dreamer; no correlator module exists |

The honest one-sentence status: **the internal record-keeping loop is live end-to-end; the
internal probe loop is built and parked behind the R&D flag; the external loop is dormant at
the act valve by design and unbuilt at the sense-back valve.** The brainstorm's "internal loop
closed and LIVE" conflated the first two rows — corrected here and in finding-0141; the
direction of the error is safe (dormant claimed live is the *unsafe* direction; here the live
half is the read-only half).

### 2.1 The reconciliation map — naming vs new

The deliverable the owner asked for first. Left column: the brainstorm vocabulary. Middle: the
built (or ratified-designed) thing it names. Right: the verdict.

| brainstorm word | built machinery | verdict |
|---|---|---|
| **passive sensor** | the sensor role (dn-agent-taxonomy §2.1/§2.4): a standing model-free φ-projection at declared rates — φ_chat, φ_code, φ_self; the proposed reference sensor is a fourth instance | **NAMING** — no new axis; "passive" = the sensor role, exactly |
| **active sensor** (the microscope) | *external target:* **sensing hands** (dn-hands §2 — "sensing hands are just new sensors", read-only, → observed tier). *Internal target:* the **DreamCharter instrument grant** + `force(grant, cut)` (bp-079) and the **influence probe** (bp-082, perturb-and-read) | **NAMING** — both instances pre-exist; the owner's distinction names the seam bp-079 built. The "one category or two?" residue is ruled in §2.3: one *form* (directed instrument use), two *capabilities* at opposite lattice corners — never one governance |
| **act** | **acting hands**: `Effect`, propose → approve → code-acts, blast-radius gate (Track G) — dormant | **NAMING** (dormant; finding-0011 grounds it) |
| **sense what happened** | the **observed stratum** + `ObservedView`; the Track-D correlator when built | **NAMING**, with the gap that the correlator is unbuilt (§2.6 G-B) |
| **the causal loop writes a C-fiber** | the **integrator** minting witnessed C-edges; the causal bracket `turn_i ≺ commit ≺ turn_{i+1}` (dn-agent-taxonomy §2.5); 4,084 edges live | **NAMING + one CORRECTION** (§2.2): closure lives in the *witness bracket*, not in graph cyclicity |
| **exhaust-as-sensor** | φ_chat already ingests agent utterances (80.7% of the chatlog is agent-authored); φ_self projects committed workflow artifacts; dream exhaust is provenance-tracked (`derived`/run ledger + the bp-082 conditioning law); actions are witnessed C-edges; the effect ledger will carry world-effects when hands wire | **MOSTLY NAMING** (§2.4 rules no new φ_exhaust); the genuine residues are the **self-authored provenance class** and the **exhaust stratum refinement + default-exclusion** (§2.4/§2.4b, gap G-C) |
| **exhaust → created-structure edges** (the provenance spine) | C-edges (exhaust→artifact, built); commit-keyed edge stores + witnesses/derives-tails make `origin(e)` a typed two-hop join | **NAMING + one derived VIEW** (§2.4b EX-2 — no new store; trust propagation composes four existing mechanisms) |
| **self-sensing → gap → correct** | gap instruments built: `long_lived_holes` (`core/complex/topology.py:104`, live as the dreamer's `hole` lens), doc_coverage (φ_code plane), drift axes (`eval/drift.py`, `eval/effector_drift.py`), C-coverage (`core/integrator.py:82`) | **NAMING** for the sensing; the *control law* (steering) is genuinely undesigned — ruled in §2.5 |
| **internal/external acting scopes** | expressible in the ratified (Σ,E,T,A) lattice but **not named there**; realized structurally by Track G's proposer/executor split and the DreamCharter grant | **NEW (naming layer)** — the one typed addition this note makes (§2.3), plus one missing enforcement test (G-D) |

**Summary verdict:** roughly seven-eighths naming, one-eighth new. The new eighth is: two named
scope profiles + one lattice-ideal test (§2.3), the exhaust coordinates — the self-authored
class and the `exhaust` refinement with default exclusion (§2.4/§2.4b EX-1), the `origin(e)`
provenance-spine view (§2.4b EX-2), and the steering-law gate split (§2.5). Everything else is
the built system, called by its right name — which is itself the value: the loop was grown
piecewise and never named as a loop.

### 2.2 The loop, typed — and two corrections

**The loop as the system actually holds it.** One pass of the agent's working loop, in the
types that exist:

```
orient   — read views / run instruments (granted reads; a charter's force, when wired)
act      — a dialogue action produces a commit / artifact write        (L1 action log, chat_events)
confirm  — the tool_result turn observes the outcome                   (the bracket's right endpoint)
witness  — the integrator mints C: (dialogue action) → (commit, path)  with witness
           (transcript_digest, turn_index, tool_record) and the causal bracket
           turn_i ≺ commit ≺ turn_{i+1}                                (dn-agent-taxonomy §2.5)
read-back— composed graph carries C as E_proven (core/graph/composed.py); C∘D answers
           "which conversation produced this version?"; C-coverage gauges the fabric
```

This is live today for the internal act-on-the-corpus loop `[ESTABLISHED — the five stores
above]`. Reasoning and acting share one representation — a typed causal path — exactly as the
fiber-chain grammar holds; the agent's autobiography and its reasoning are written in one
alphabet `[DERIVED — from dn-agent-taxonomy §2.5 + dn-fiber-geometry §2.0's alphabet]`. The
perception–action-cycle framing (act to test the model; the residual drives learning) is
`[FROM MEMORY — active inference / Friston free-energy; perception–action cycle; verify before
any book chapter cites it]` — used here as vocabulary only; no mechanism imports it.

**Correction 1 — closure is the witness bracket, not a graph cycle.** The brainstorm's payoff
claim ("a confirmed loop is a directed C-fiber cycle — precisely what the census reads back")
is wrong in its second half as stated. Every C-edge points dialogue-action → produced-artifact;
no C-edge points back. So **C is bipartite-directed and cycle-free by construction** — a census
cycle detector run over C would find nothing, structurally, forever. The confirmation is not
represented as a return edge; it is represented **inside** the edge, as the causal bracket
(the `tool_result` turn that observed the outcome is the bracket's right endpoint). The census's
directed cycle family (`core/graph/census.py`) reads X_cite (F-arcs), a different fiber.
`[ESTABLISHED — code read this session]` The corrected statement: *the agent's acting writes
witnessed C-edges whose brackets each contain one closed sense→act→confirm loop; the read-back
instruments are C-coverage, the composed E_proven layer, and the C∘D traversal — not cycle
detection.* The self-authored-causality payoff survives intact; only the instrument named for
reading it changes.

**Correction 2 — "closure is the ingest warrant" reduces to the witness law.** The brainstorm
proposed that a closed loop is self-justifying to record. As mechanism this is already the
system: the sensor tier records *unconditionally* (the lossless law — every turn, every commit),
and a C-edge exists *iff* its witness does (the witness law). There is no admission decision
left for "closure" to justify. Adopt the phrase as description, not as a new ingest rule
`[DERIVED]` — inventing an admission gate keyed on closure would be a parallel structure beside
the witness law (the DRY failure this pass exists to prevent).

**The two probe loops are one shape, two targets.** The internal probe (stage a HYPOTHETICAL
overlay, read the influence diff — bp-081/082) and the external probe (sensing hand → observed
return) are the same radar shape — emit a perturbation/query, measure the response
`[ANALOGY — radar/sonar; vocabulary only]`. They are *not* one capability: §2.3 shows they sit
at opposite corners of the scope lattice and are governed by different gates (budget/refusal vs
blast-radius/approval). Keep them as two named instances of one form; never unify their
governance.

### 2.3 The scope asymmetry — two named profiles, derived from the zone boundary

The owner's last thought, made a typed statement in the ratified algebra. Nothing here amends
`dn-capability-scope` (ratified, A8); this section is the profile layer *on top* — the same
relationship `core/agent_scope.py`'s role constructors already have to the lattice.

**Profile IA — the internal actor** (the dreamer/probe family; bp-079's grant is the built
instance):

- `Σ` — **broad by grant**: a downset up to `⊤_Σ = R ∖ 𝔇` (the foundation denylist is
  subtracted from every grant, structurally — `CONSTITUTION.md`/golden are unreachable at any
  breadth), optionally ∪ {HYPOTHETICAL}; the mirror ideal ι_MR applies unless the client class
  holds the cross-strata read exemption. Broad *read* never implies mirror *write*: the
  interpreted write path is structurally unforgeable (`DerivedStore` has no provenance
  parameter), so "internal acting" can touch the durable corpus only as marked interpretation.
- `E` — granted fibers as needed (it reasons over structure).
- `T` — cut-bound (SLICE fires on any multi-stratum point read; a counterfactual read must
  carry cut ∧ generation — bp-081 made this unconstructable otherwise).
- `A = (READ[+propose], W_Σ=1, W_world=NONE)` — interpreted-tier writes, **zero world reach**.
- Residence: core. Governance: the DreamCharter budget + estimate-then-force refusal gate.

**Profile EA — the external actor** — which Track G already *split in two*, and the split is
the design (dn-hands §5/§7):

- **EA-p, the proposer** (core-side tailoring): `Σ` = `mirror_authored` via `MirrorView` (or
  narrower), `A = (read+propose, 0, NONE)`. It composes a *proposal artifact*, never a sent one.
- **EA-x, the executor** (edge-side): `Σ = ⊥` over corpus strata — **it never reads the vault**
  (bright line 2); its only scope is the world coordinate, `A = (—, 0, W_world = ε)` with ε
  gated by the blast-radius-weighted approval and a per-action JIT scoped credential
  (bright line 3; sandbox per bright line 4).

**The derivation (the owner's asymmetry is the zone boundary, restated on the lattice).**
`[DERIVED]` Bright lines 1–2 say: the component with broad private-data access has no network;
the component that touches the world never reads the vault. On the lattice that is exactly the
inversion IA vs EA-x: **Σ-breadth and W_world are mutually exclusive above ⊥** —

> for any deployed grant s: `s.Σ ⊓ (private strata) ≠ ⊥  ⇒  s.A.W_world = NONE`.

Bright line 3 is the residual A-axis discipline on EA-x (propose→approve→code-acts = the gate
weight `w(β)`); the mirror firewall and least-privilege are the Σ-axis discipline. Two axes,
two disciplines, one lattice — the brainstorm capsule's phrasing, now typed. Today the
implication is *vacuously* true (`⊤_deployed.W_world = NONE`, finding-0011), and Track G's
structure realizes it by construction (`EffectView`'s Σ is `world` only). But per the
structural-enforcement rule, a property is only real when a test proves it: **the exclusion
above is not yet a firewall ideal / lattice-law test in `core/scope.py`** — it is held by the
shape of the code, not asserted by any ratchet. That is gap **G-D**, and §3 licenses the
one-test fix. *Falsifier (F-AL3): a constructable deployed grant with non-⊥ private Σ and
`W_world > NONE` — if the licensed test cannot be written to refuse it structurally, the
derivation above is decorative and this section must be reworked.*

**Reconciling IA's breadth with the DreamCharter grant (the capsule's open sub-question).**
"Broad Σ" stops exactly where bp-079 stops it: minus 𝔇 always (`⊤_Σ = R ∖ 𝔇`); minus the
mirror payload unless the class exemption is granted; HYPOTHETICAL only when named in the
grant; and *write*-side always confined to the interpreted tier. The DreamCharter is the IA
profile's constructor — no second construct is needed or proposed. `[ESTABLISHED — bp-079
sealed; core/dreaming/charter.py read this session]`

### 2.4 Exhaust-as-sensor — measured first, then ruled

**The measurement (taken this session, live stores, read-only).** The chat sensor already
ingests the agent's prose exhaust at scale: **6,429 of 7,966 chatlog utterances (80.7%) are
`speaker='agent'`**. The L1 action log holds 19,493 events; the integrator has witnessed 4,084
C-edges; φ_self holds 37 observations (cost stream only — young); dream exhaust sits in the run
ledger (210 runs) and `derived` (interpreted, provenance-marked). `[ESTABLISHED]`

**The ruling: NO new φ_exhaust.** The agent's exhaust is already sensed **piecewise, at its
sources**, and each piece lands in the right store under the right discipline:

| exhaust class | already sensed by | lands as |
|---|---|---|
| agent prose (reasoning, reports-in-chat) | φ_chat (CS-3 grain) | OBSERVED rows, speaker='agent' |
| agent actions (commits, writes) | L1 action log → integrator | chat_events + witnessed C-edges |
| agent workflow artifacts (plans, seals, findings) | φ_self over committed artifacts | OBSERVED `agent_observations` |
| dreams | run ledger + `DerivedStore` (+ bp-082 conditioning marks) | INTERPRETED, support-cited |
| world effects (when hands ever wire) | the effect ledger (G5) | attested effect records |

Three independent reasons a unified φ_exhaust is rejected, each sufficient:

1. **DRY / duplication-apophenia.** Every exhaust artifact already has a primal source in a
   store; re-projecting rendered outputs (e.g. the phone reports, which quote artifacts
   verbatim) would manufacture spurious conductance by duplication — CS-3's tool-strip
   reasoning, applied one level up. `[DERIVED]`
2. **The ratified exhaust-lane invariant.** `dn-exhaust-lane` §2.2 (ratified): *no ingest root
   inside `~/.mind-palace/exhaust/`, no core/ingest path reads it.* A φ_exhaust pointed at the
   report lane is structurally prohibited by ratified text. Exhaust-as-sensor must mean
   sensing at sources, or it means violating a ratified invariant. `[ESTABLISHED]`
3. **The self-sensing regress line.** `dn-self-sensing` §2.6 (ratified): a sensor's output is
   not in its input domain; streams observe each other's *instruments*, never each other's
   *output*. A φ_exhaust reading dream/report **stores** would be exactly the accumulator that
   ruling deleted. The piecewise coverage keeps every sensor's domain primal (transcripts,
   commits, artifacts). `[ESTABLISHED — ratified text]`

So "the exhaust of the agent is itself a sensor" is **true and already built** — it is the
composition φ_chat + L1 + integrator + φ_self + dream provenance, i.e. self-sensing generalized
to outputs happened piecewise over the last month. What the owner's framing *adds* is the name,
plus one genuine residue:

**The residue — the self-authored provenance discrimination (gap G-C).** Agent utterances land
`OBSERVED` — the same class whose docstring reads "third-party behavioral exhaust." The
distinction agent-authored vs instrument-sensed exists today only as row *metadata* (`speaker`),
never as a *class* — so no trust weighting, grounding grade, or renderer can discriminate them
without reaching into row internals. The twin question is already parked twice: owner-utterance
provenance (dn-agent-taxonomy §2.3, parked to a mirror-firewall pass) and the α-axis position
of proprioceptive rows (dn-self-sensing §5, deferred to the authorship-axis gate). The
authorship axis (draft) currently has **no aₓ position for agent-authored base rows** — its §1
treats system output as derived-footprint only, but 6,429 chat rows are *base* rows of agent
authorship. Ruling: route the class question to `dn-authorship-distance-axis`'s ratification
gate as a named amendment candidate (an a₂-adjacent position for self-authored, trust-weighted
below owner-authored and below instrument-observed, or a loss-model annotation on a₂ —
owner's call at that gate, not here). **Fail-safe note:** the current landing errs in the safe
direction — agent output is *over*-distrusted (treated as third-party exhaust), never
under-distrusted. The gap blocks refinement (graded trust), not safety. `[DERIVED]`

**The guardrail, bound (the non-negotiable the brainstorm named).** Exhaust sensing is
LOW-AUTHORITY — it records *"the agent produced X"*, never *"X is true"* — and this is already
structural, on four independent layers, each with an existing test surface:

1. **Mirror-opaque:** OBSERVED/INTERPRETED are unrepresentable in a `MirrorView`
   (`core/mirror.py` constructor proof; CS-2 falsifiers). The self-model can never read the
   agent's exhaust as ground.
2. **Surfacing-only:** chat-derived values never enter weights/confidences/promotions/baselines
   (CS-5, I1 — with named falsifiers in the ratified note).
3. **The grounding + conditioning laws:** dreams cannot cite dreams as evidence (rule 1);
   hypothesis-conditioned artifacts carry their marks and expire with their subspace (bp-082's
   conditioning law, built with taint tests). The dreams-cite-dreams laundering loop — the one
   way exhaust-as-sensor becomes a confirmation-bias amplifier — fails closed.
4. **Records-not-causes vocabulary:** the census/narration discipline (§2.9 of the dreamer
   note) binds any lens that ever narrates the agent's own loops.

A future self-authored class *refines* layer 1–2's granularity; it must never *replace* them.
*Falsifier (F-AL4): any exhaust-derived value found in a weight, confidence, promotion,
baseline, or mirror path — the existing CS-5/I1 falsifiers, restated as this note's tooth.*

### 2.4b The exhaust stratum and the provenance spine (owner refinement 2026-07-21, ruled)

Mid-pass the owner sharpened the exhaust question into two first-class design proposals:
(1) a dedicated **agent-specific exhaust stratum carrying low priority**; (2) **edges pointing
from exhaust to the structure it created** — the exhaust layer as the provenance spine of
agent-initiated change, with trust propagation ("provisional until corroborated"). Both are
ruled here, each against the stratum≠provenance distinction (dn-agent-taxonomy §2.3) and the
built machinery.

**EX-1 — the exhaust coordinates: BOTH axes, with the stratum side landed as a refinement,
not a new base.** The owner's "likely clean answer is both axes" is adopted `[DERIVED]`:

- **Provenance axis (the trust weight).** The self-authored class of §2.4/G-C — trust-weighted
  below owner-authored and below instrument-observed — routed to the authorship-axis gate
  (PD-1). This is the *"agent emitted X" is a fact; "X" is not thereby true* split the owner
  named: the **record** of emission is observed-side fact; the **content** is
  interpreted-grade until corroborated. One row, two readings, discriminated by class + the
  footprint rule — not by which store it sits in.
- **Stratum axis (structural isolation).** A refinement predicate, **`exhaust ⊂ dialogue`**
  (grant vocabulary), by the established named-extension pattern (`mirror_authored ⊂ mirror`;
  the `OBSERVED_DIALOGUE ⊂ observed` park in dn-chat-sensor §4) — NOT a new base stratum.
  Rejected alternative, recorded: a base `EXHAUST` stratum re-homing rows out of the three
  stores where exhaust already lands (chatlog/dialogue, agent_observations/observed,
  dreams/INTERPRETED) would be a parallel structure beside INTERPRETED — which *already is*
  the low-trust agent-output tier for dream content — and a disk migration in service of a
  grant-vocabulary need ("R is a forest of grant-vocabulary, not a partition of disk" —
  dn-agent-taxonomy §2.3, verbatim). The dream/report exhaust needs no new home at all; the
  refinement covers the one population whose stratum does not already say "agent output":
  the agent-side dialogue rows.
- **"Low priority," decomposed honestly — structure vs tuning.** The *safety* property is
  set-membership, three structural cuts: (i) mirror-opacity (existing, layer 1 above);
  (ii) **default-grant exclusion** — the bp-081 HYPOTHETICAL precedent applied to the
  refinement: a read that includes agent-exhaust rows is constructible only under a grant
  naming `exhaust` (Σ-visibility as the capability test); (iii) surfacing-only (CS-5,
  existing). The *ranking* property — exhaust weighs less in retrieval/reasoning — is the
  α-axis weight `w(a_self)` and the graded envelope: **tuning, never protection**
  (dn-authorship-distance-axis §3.4's rule, restated here precisely because "low priority"
  invites reading the weight as the guardrail; it is not — the set-membership cuts are).
- **Agent-specific, without lattice explosion.** Per-producing-agent attribution is
  row/witness-carried (the transform-attribution pattern: attested batches, interpreter
  identity; `session_id` in the C-witness) — NOT a stratum per agent (the lattice is a finite
  enum; producers are unbounded). Cross-agent laundering is blocked by attribution + class
  (a footprint never rises by changing hands — §3.3 of the axis note), not by enum growth.
  Re-entry: if a grant ever must include agent A's exhaust while excluding agent B's,
  producer-parameterized refinement predicates are expressible in the algebra then (PD-8).

*Falsifier (F-AL6): once the refinement lands, an agent-exhaust row reachable under a grant
that does not name it — the isolation is decorative and the stratum ruling must be re-tiered.*

**EX-2 — the provenance spine: the exhaust→created-structure relation EXISTS as a
composition; mint a view, never a second store.** `[DERIVED]` Audited against what is built:

- **exhaust → created *node/artifact*** is the C-edge, live (4,084 rows): dialogue action →
  (commit, file, doc), witness-carried. Nothing to build.
- **exhaust → created *edge*** — the owner's sharpest ask — is *derivable* today, because
  every durable edge already carries its origin coordinate: X_cite rows are **commit-keyed**;
  C-edges and derives-hyperedges carry witnesses/tails (bp-082's conditioning tails are this
  exact shape for dream exhaust). So `origin(e) := the C-edge whose witnessed commit minted e`
  is a typed two-hop join (C ∘ commit-keying), the same family as C∘D ("which conversation
  produced this version?", dn-agent-taxonomy §2.5). **Ruling: expose `origin` as a derived,
  regenerable traversal/view — do not mint edge-of-edges rows.** Two grounds: the
  fiber-vs-edge criterion warns that derivation tissue stored as graph edges duplicates what
  rows already carry and pollutes connectivity with derivation stars (dn-agent-taxonomy §2.4);
  and the edge-model's discipline classifies provenance-spine links as **dispositional**
  (E_disp — never assembled into `A_geom`/L), so materializing them buys no instrument any
  power the join lacks. Edge-as-endpoint mechanics, if a consumer ever needs row grain:
  created edges have stable ids (`CausalEdge.edge_id`; commit-keyed X_cite rows), so
  extending a target-kind vocabulary is expressible — parked with that consumer (PD-8).
- **Trust propagation ("provisional until corroborated") is a composition of four existing
  mechanisms — the trust ledger needs no new machinery:** (1) the **footprint meet** — a
  derived structure warranted only by exhaust carries exhaust-class footprint
  (α̂ = ⋀ support; §3.2 of the axis note); (2) **assertion authority** — it is
  `dreamer-proposed` until the verdict event certifies it (the-edge-model §3: proposed →
  verdict-certified IS the crossing gate the owner's "raises it" names); (3) the
  **corroboration lift** — agreement over *distinct* interpreters/sources raises c₀
  (`core/recursion.py`, competitive fusion — observed confirmation is exactly a distinct
  interpreter agreeing); (4) the **graded envelope** — c ≤ γ^d·g_w with w(a_self) low, so
  exhaust-only grounding yields nonzero-but-discounted confidence that *earns* its way up
  through corroboration, and only an owner verdict raises class or authority. What is missing
  from this stack is exactly one entry: **w(a_self) does not exist because the class does not
  exist** — the same PD-1 gate. The owner's trust ledger = these four, plus PD-1's entry.
- **Census/helix readability, kept honest (Correction 1 extended, not weakened).** With
  exhaust→created edges only, the origin graph is *acyclic by construction* (every arrow
  points from exhaust to what it made). Graph-grain loops would additionally need the
  **return class** — "informed-by" edges (existing structure → the later exhaust that read
  it). Deliberately NOT minted: reading is not influence, and an edge per context-read would
  manufacture dense derivation stars — the CS-3 anti-apophenia reasoning at edge grain. If
  loop-reading at graph grain is ever demonstrated necessary, the only admissible candidate
  is a *witnessed, deterministic* orientation record (the L1 action log's read events under
  the witness law), and it must clear that apophenia bar — parked (PD-7). Until then the
  loop's closure remains bracket-witnessed inside each C-edge, and the census reads the
  fabric through E_proven/C-coverage, not through cycles.

*Falsifier (F-AL7): an `origin(e)` result not re-derivable from witnesses + commit keys alone
(i.e. the view needs facts no row carries) — the composition claim fails and the spine needs a
store after all; re-open EX-2 by supersession, not silently.*

### 2.5 Self-sensing → gap → correct: the control law, split by gate tier

**The sensing half exists.** Gaps are already instrumented: `long_lived_holes` (persistent H₁ =
conceptual gaps — live as the dreamer's `hole` lens), doc_coverage (φ_code plane),
the drift gauge and axes (`eval/drift.py` A1; `eval/effector_drift.py` G7), C-coverage
(`core/integrator.py`), the parity ratchets. `[ESTABLISHED]`

**The correction half is the artifact chain, and must remain it.** The ruling, split cleanly by
what the "correction" touches:

- **Agent-autonomous (licensed in principle, interpreted tier, reversible):**
  (a) *surfacing* — gap readings become reports/findings (the existing norm; no new license
  needed); (b) *attention targeting* — when the owner wires charter dispatches, a dispatch's
  region/instrument choice MAY be informed by gap readings (point the next dream at the
  low-coverage, high-hole region). This is self-steering **curiosity as a dispatch-selection
  heuristic**: interpreted-only output, budget/refusal-gated, reversible by construction, and
  **logged for free** — the DreamCharter record + estimate/refusal events are the audit trail
  the brainstorm's "gated + logged?" question asks for. `[DERIVED — composition of built
  gates; no new mechanism]`
- **Owner-gated (bright line 5 / the fixed points):** any correction that changes durable
  priorities or state — plan status, design-note text, code, config, the loop's own gates, and
  a fortiori anything in 𝔇. These route through the artifact chain (finding → design → plan →
  blessing) exactly as today. **No gap signal ever auto-flips an artifact state** — high drift
  does not edit a plan; it files a finding. The self-correction loop inherits the
  self-modification gate; it does not route around it.

The asymmetry is the same §2.3 inversion one level up: reading its own gaps broadly is cheap
and safe (IA-shaped); acting on them durably is narrow and gated (EA-shaped). Park: the actual
curiosity heuristic (what function of hole/coverage/drift picks the next region) is **parked
until charters are owner-wired** (PD-3) — designing a steering policy for a probe loop the
owner has not turned on would be scheduling ahead of the R&D flag.

### 2.6 ⚑ The gap catalog — what is genuinely missing, ranked

Assessed, not assumed; each with severity and whether it blocks a loop. "Blocks" means the loop
cannot run/close; "refines" means the loop runs but coarsely.

| id | gap | state (verified) | severity | blocks? |
|---|---|---|---|---|
| **G-A** | **The internal probe loop is built-not-wired**, and the record said "live." `[dream_rnd] enabled=false`; no live entry constructs a DreamCharter; bp-079/082 sealed same-day as the claim | finding-0141 filed; posture accuracy, safe direction | medium (accuracy), low (risk) | blocks the *probe* loop until the owner wires the R&D flag + a dispatch entry point — a deliberate act, correctly owner-shaped |
| **G-B** | **The external sense-back has no consumer.** `ObservedView` exists; the Track-D correlator is design-only; sensing hands unwired (finding-0011). The external loop is open at BOTH act (by design) and sense-back (unbuilt) | no correlator module on disk | high *for the external loop's eventual closure*; nil today (nothing acts, so nothing returns) | blocks the external loop's confirm valve; the correlator is the right *next* Track-D build when the owner turns there — `ObservedView` is its seam (standing direction) |
| **G-C** | **The exhaust coordinates are unwired on both axes.** No self-authored provenance class (6,429 agent-authored base rows share OBSERVED with third-party exhaust; discrimination is metadata-only; the α axis has no position; `w(a_self)` therefore cannot exist) and no `exhaust` stratum refinement / default-grant exclusion (§2.4b EX-1) | §2.4/§2.4b | medium; fails safe (over-distrust) | refines (graded trust, renderer class-visibility, structural excludability); class → authorship-axis gate (PD-1), refinement → AL-3 |
| **G-D** | **The zone-boundary exclusion is not a lattice test.** `Σ(private) ≠ ⊥ ⇒ W_world = NONE` is held by Track G's shape, asserted by nothing | §2.3 | medium-low; one additive test | refines (turns a structural accident into a ratchet); licensed in §3 |
| **G-E** | **No lens narrates the agent's own action loops.** The autobiography is stored (4,084 witnessed C-edges) and composed-visible, but no consumer surfaces "this conversation produced this change" to the owner; the census's directed layer is F-only (and C-cycles are impossible — §2.2 correction) | code read | low-medium | refines; a small lens/vocabulary item riding the oq-0021 pattern (records-not-causes), after D-1 seals |
| **G-F** | **X_cite current-view staleness.** 893,991 accumulated rows vs ~hundreds of distinct current pairs; consumers re-derive the latest-commit view per read | store counted | low; owned by the reference-sensor track (parent brainstorm), measured real here | refines F-consumers (census, M2) |
| **G-G** | **φ_self is thin.** 37 rows, cost stream only; the exhaust table's "workflow artifacts" leg is licensed but young | store counted | low | refines; PD-a additive streams re-enter per the ratified note |

**Non-gaps caught (claims the brainstorm implied that need no work):** census-reads-C-cycles
(structurally impossible — corrected, §2.2); a closure-based ingest rule (reduces to the
witness law — §2.2); a φ_exhaust module (rejected three ways — §2.4); any active/passive
taxonomy axis (it decomposes — §2.1); any effector-tier change (out of scope, finding-0011).

### 2.7 Reconciliation rulings — every note touched, ruled

All EXTEND / cross-ref; no ratified text is edited (A8); no supersession anywhere.

| note | ruling | one-line warrant |
|---|---|---|
| `dn-hands-and-the-effector-layer` (draft) | **EXTEND** | Its sense/act split + gate + blast radius are the external loop's valves, named onto the map (§2.1); its §7 loop diagram is this note's external instance. Dormancy language defers to finding-0011's re-entry. |
| `dn-observed-data-and-the-assistant-tier` (draft) | **EXTEND** | The observed stratum is the sense-back valve; the firewall is guardrail layer 1. G-B names its correlator as the missing consumer — its own charter, not designed here. |
| `dn-self-sensing` (ratified) | **EXTEND** | Exhaust-as-sensor generalizes φ_self's subject from operation to outputs *piecewise at sources*, preserving §2.6's regress line verbatim (the no-φ_exhaust ruling is that line's application). |
| `dn-chat-sensor` (ratified) | **EXTEND** | CS-2/CS-3/CS-5 bind the exhaust ruling; the 80.7% measurement is its coverage read. No register change; the promotion seam stays untouched. |
| `dn-exhaust-lane` (ratified) | **HONORED** | Its §2.2 invariant is reason 2 of the φ_exhaust rejection; this note makes the lane's never-re-enters rule load-bearing for a second design. |
| `dn-agent-taxonomy` (ratified) | **EXTEND** | Roles unchanged; the witness law is the loop's spine; the §2.3 parked provenance row gains a sibling (agent-side) routed with G-C. Active/passive confirmed as not-an-axis. |
| `dn-capability-scope` (ratified) | **EXTEND** | The §2.3 profiles are named points/regions of its lattice, constructor-layer only (the `agent_scope` precedent); G-D's test asserts an ideal it already licenses in kind (firewalls-as-ideals). |
| `dn-synchronic-diachronic-dreamer` (ratified) | **EXTEND** | The DreamCharter is the IA constructor; influence/conditioning is the internal probe + guardrail layer 3. Wiring stays behind the R&D flag — nothing here accelerates it. |
| `dn-recursive-dreaming-bounded-by-grounding` (draft) | **EXTEND** | Rule 1 (+ the bp-082 fifth rule) is guardrail layer 3; the exhaust design adds no new crossing for it to police. |
| `dn-authorship-distance-axis` (draft) | **EXTEND (amendment candidate named)** | G-C/§2.4b route the self-authored class + `w(a_self)` to its ratification gate; until then OBSERVED stands (fail-safe). Its footprint meet + corroboration lift are two of EX-2's four trust-propagation mechanisms. |
| `dn-the-sacred-boundary` / `dn-the-edge-model` (drafts) | **EXTEND** | §2.3's derivation is the boundary principle restated on the lattice; edge assertion authority is EX-2's mechanism 2 (proposed → verdict-certified = "provisional until corroborated," reused not reinvented); E_disp discipline binds the origin view (spine links never enter `A_geom`). |
| brainstorms `reference-integrator` / `agent-causal-loop` | **ANSWERED** | Every open question dispositioned: placement (passive sensor, `ops/`), one-category-or-two (§2.2/§2.3), autobiography ingestion + provenance (§2.4/G-C), self-steering (§2.5), scope profiles (§2.3), census read-back (corrected, §2.2). |

### 2.8 The measure-first battery — baselines taken, and what to run before building

Readings taken this session (2026-07-21, live `data/`, read-only) — recorded so the next pass
measures *deltas*, not absolutes:

| # | measurement | baseline (2026-07-21) | instrument |
|---|---|---|---|
| M-1 | agent-exhaust chat coverage | 6,429 agent / 1,537 owner of 7,966 utterances (80.7%) | chatlog store |
| M-2 | witnessed action fabric | 4,084 C-edges; 19,493 L1 events | causal_edges, chat_events |
| M-3 | C-coverage (fraction of integrable D-events with a C-witness) | gauge built, **reading not yet taken** — run `core/integrator.py` coverage over the live stores | CCoverage view |
| M-4 | φ_self depth | 37 observations (cost stream) | agent_observations |
| M-5 | X_cite accumulation vs current view | 893,991 rows total; distinct-pair current view to be computed (reference-sensor track's own M) | reference_edges |
| M-6 | gap-instrument baselines: hole count/persistence, doc_coverage, drift profile vs anchor | **owed** — record once before any steering heuristic is even sketched (PD-3's precondition) | topology/hole lens, φ_code coverage, eval/drift A1 |
| M-7 | dream exhaust volume | 210 runs, 4 interpreted artifacts | run ledger, derived |

Rule: no plan graduated from this note may skip the M-row it depends on (the house
measure-first discipline; the reference-sensor precedent).

## 3. Consequences — what this licenses (small), what parks

**Licensed on ratification (session-sized, additive, nothing preempts the sequenced queue):**

- **AL-1 — the profile constructors + the zone ideal test.** Name `internal_actor` /
  `external_proposer` / `external_executor` profile constructors beside the existing role
  constructors (`core/agent_scope.py` precedent), and add the G-D lattice test: a grant with
  non-⊥ private Σ and `W_world > NONE` is unconstructable/refused, with the exclusion stated as
  a firewall ideal in `core/scope.py`'s existing ideal machinery. Zero behavior change;
  lattice-law tests extended. *Falsifier: F-AL3.* (~1 small session.)
- **AL-2 — the M-3/M-6 readings.** Run C-coverage and record the gap-instrument baselines into
  the journal/PROGRESS (read-only; can ride any session; arguably pre-ratification).
- **AL-3 — the exhaust refinement + the origin view (§2.4b).** (a) The `exhaust ⊂ dialogue`
  refinement predicate as an additive lattice extension (the bp-070 D1 pattern: enum element +
  refinement edge + lattice-law tests) with the default-grant exclusion test (F-AL6 as a
  test); (b) the `origin(e)` traversal as a derived, regenerable view over C-witnesses +
  commit keys (F-AL7 as a test) — no store, no minted rows, E_disp discipline asserted
  (origin links never enter `A_geom`). Independent of PD-1 (the class/weight stays
  owner-gated at the axis note). (~1 small session.)

**Parked (each with its re-entry):**

| id | decision | default | re-entry |
|---|---|---|---|
| PD-1 | self-authored provenance class (α-position or a₂ loss-model annotation) | stays OBSERVED + speaker metadata (fail-safe) | `dn-authorship-distance-axis` ratification gate; owner deliberation (MIRROR_READABLE-adjacent) |
| PD-2 | Track-D correlator build (the external sense-back consumer) | not designed here; `ObservedView` is its seam | the owner turns to Track D (standing direction in memory/PROGRESS); its own design pass |
| PD-3 | the curiosity/steering heuristic over gap instruments | none — surfacing only | owner wires the R&D flag + a charter entry point (G-A's re-entry) AND M-6 baselines recorded |
| PD-4 | the action-loop lens (C∘D narration, "records not causes") | autobiography stored, not narrated | D-1 (arrow-read) sealed + the oq-0021 vocabulary ruling lands; then a small rider, same discipline |
| PD-5 | the reference sensor (passive, F-freshness) | parent brainstorm's measure-first track | its staleness measurement (M-5's second half) sizes it |
| PD-6 | external loop activation of any kind | dormant, tier NONE | finding-0011's re-entry verbatim — a deliberate, gated, reversible owner act; never this note |
| PD-7 | "informed-by" return edges (structure → later exhaust that read it) | NOT minted — reading ≠ influence; the apophenia bar (§2.4b EX-2) | a consumer demonstrates graph-grain loop reading is necessary AND a witnessed, deterministic orientation record (L1 read events under the witness law) clears the apophenia bar — its own small design pass |
| PD-8 | edge-as-endpoint target-kind extension; producer-parameterized exhaust predicates | expressible, uninhabited | the first consumer needing row-grain origin materialization, or a grant that must split exhaust by producing agent |

**Explicitly NOT licensed:** any φ_exhaust module; any effector or R&D flag change; any
correlator build; any provenance enum change; any steering policy; any census change (the
C-cycle idea is corrected away, not deferred).

## Falsifiers (the load-bearing set)

- **F-AL1** (§2.1/§2.2) — a loop element is found that the map cannot place on built/ratified
  machinery without new mechanism ⇒ the "mostly naming" verdict is wrong; reopen as design.
- **F-AL2** (§2.2) — a C-edge is ever minted artifact→dialogue (a return edge) ⇒ the
  bipartite/no-cycle correction is wrong; the census question reopens.
- **F-AL3** (§2.3) — the zone-exclusion test cannot be made structural, or a deployed grant
  violating it is constructable ⇒ the derivation is decorative; rework §2.3.
- **F-AL4** (§2.4) — any exhaust-derived value in a weight/confidence/promotion/baseline/mirror
  path ⇒ the guardrail stack is breached; stop and treat as a firewall incident, not a bug.
- **F-AL5** (§2.5) — any gap signal auto-flipping an artifact state (plan status, note text,
  config) without the chain ⇒ the steering split failed; the autonomous tier narrows to
  surfacing-only until re-ruled.
- **F-AL6** (§2.4b) — post-AL-3, an agent-exhaust row reachable under a grant not naming the
  refinement ⇒ the isolation is decorative; re-tier the stratum ruling.
- **F-AL7** (§2.4b) — an `origin(e)` result underivable from witnesses + commit keys ⇒ the
  view-not-store composition claim fails; reopen EX-2 by supersession.

## Cross-references

**Warrant:** `docs/brainstorms/agent-causal-loop.md` (all three capsules) ·
`docs/brainstorms/reference-integrator.md` (both capsules + the owner's hands reconciliation).

**Code & stores (verified this session):** `ops/chat_sensor.py:64,124-137` (agent turns
ingested; born-scoped banner) · `ops/lifecycle/launcher.py:238,246,316,325` (sensor +
integrator live wiring) · `core/integrator.py:78-98` (C-coverage) ·
`core/stores/causal_edges.py` · `core/graph/census.py` (F-arcs only; cycle family) ·
`core/graph/composed.py` (E_proven attribution) · `core/dreaming/charter.py` (bp-079) ·
`core/dreaming/conditioning.py`, `core/graph/influence.py` (bp-082) · `core/dreaming/rnd.py:31`
+ `config/defaults.toml:263-267` (the R&D flag, off) · `core/complex/topology.py:104` +
`core/dreaming/interpreters.py:47,68` (the hole lens, live) · `eval/drift.py`,
`eval/effector_drift.py` · live stores: chatlog 7,966 / chat_events 19,493 / causal_edges
4,084 / agent_observations 37 / reference_edges 893,991 / dream_runs 210.

**Design:** the frontmatter links, each ruled in §2.7 · `docs/design-notes/fiber-geometry.md`
(draft, awaiting owner — the S/F/C/D alphabet §2.2 speaks; no dependency either way) ·
`docs/design-notes/inner-outer-core.md` (draft, awaiting owner — ring honesty; untouched) ·
finding-0011 (external dormancy — ground) · finding-0141 (internal probe posture — filed by
this pass).

**External claims flagged `[FROM MEMORY]`:** active inference / free-energy (Friston);
the perception–action cycle; radar/active-sensing terminology; Biba-style integrity reading
(via the authorship-axis note). All must pass the external-grounding gate before any book
chapter cites them.
