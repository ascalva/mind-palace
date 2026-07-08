---
type: design-note
id: dn-capability-evaluation-harness
status: draft
implementation: not-built
created: 2026-07-08
updated: 2026-07-08
links:
  - docs/design-notes/supersession-recovery-evaluation.md # instance #1 of this family
  - docs/design-notes/dreamer-quality-suite-evaluation.md # F9 — the unit-scale sibling; shared philosophy
  - docs/design-notes/holistic-testing.md # process-correctness taxonomy this complements
  - docs/design-notes/test-organization.md # execution-profile homes
  - docs/design-notes/dream-phase-rnd-charter.md # the flag-gated lane all of this runs in
  - docs/design-notes/founding-corpus.md # ground-truth source for authored topology; control-corpus separation
  - docs/design-notes/live-adoption-and-longitudinal-harness.md # Track L; shared replay machinery
  - docs/NOTATION.md # family tags; family-5 honest-status banner (see verification item V1)
supersedes: null
superseded_by: null
warrant: null
---

# Design note — The capability evaluation harness: masked replay, a transformation algebra, and instrument attribution

*Family tag → family 5 (the reasoning complex), measured with family 4 (metric geometry); cross-cutting with the assurance hierarchy. See [`../NOTATION.md`](../NOTATION.md).*

**Status:** DRAFT — pending owner ratification. Design only; no build authorized by this
note. **Origin:** design dialogue, July 2026.
**Boundary:** none of this touches the live store. Every run is a scratch replay in the
`dream_rnd` flag-gated lane; outputs are proposals and score records, never promotions.

---

## 0. What this note is, and is not

The testing story already has three pillars, each answering a different question:

| Note | Question it answers |
|---|---|
| `holistic-testing.md` | *Was the output produced correctly?* (process, invariants, attestation-as-oracle) |
| `dreamer-quality-suite-evaluation.md` (F9) | *Is the output signal or well-attested noise?* (apophenia, calibration, at unit scale) |
| `supersession-recovery-evaluation.md` | *Can the Dreamer rediscover one known structure?* (one capability, one labeled set) |

This note generalizes the third into a **family**, and adds the machinery the family
needs: (a) a uniform **masked-replay** substrate so any eval is "filter the event
stream, rebuild a scratch complex, run, score against the mask"; (b) a small
**transformation algebra** so dataset variants are versioned, seeded code rather than
hand-built fixtures; (c) an **ablation ladder** so every score is attributed to the
instrument that earned it, generalizing F9's beats-the-dumb-baseline into a matrix; and
(d) a **capability-test catalog** (six batteries) covering structure recovery, edge
proposal, polarity/negation, prediction, reasoning traces, and metrology.

What it does **not** do: it does not replace or absorb the three notes above.
Process-correctness tests keep their homes (`test-organization.md` §1); F9 remains the
unit-scale quality suite and its `THRESH` tuning surface is untouched; the
supersession-recovery eval becomes **instance #1** of this family unchanged — its
fixture, answer key, leak-check, and two-condition protocol are the template several
sections below generalize from.

The question this family answers, distinct from the three above:

> **"Which capabilities does the system demonstrably have, at what scale, and which
> instrument is responsible for each?"**

---

## 1. The unit of evaluation: a scratch replay of a filtered event stream

Once the founding corpus lands as a **dated, supersession-linked sequence of events**
(`founding-corpus.md` §2.1) sharing the steady-state ingest path (§4/Q3 there), the
complex's topology is definitionally the replay of its edge- and chunk-assertion
events. An eval corpus is therefore never a hand-mutated copy of the store: it is a
**filtered, transformed replay** into a disposable scratch complex.

Consequences, each an invariant of the harness:

- **Reset is free and safe.** "Reset the system" = discard the scratch complex and
  replay. Nothing is ever deleted from the live store (it can't be — append-only). The
  existing `test_reset_from_raw_is_clean` expectation (`holistic-testing.md` §1d) is
  the primitive this leans on; **V2** below verifies the replay path supports
  event-level filtering, not only full re-ingest.
- **Eval isolation is a soundness invariant**, same rank as worktree isolation in the
  build system. Scratch complexes live outside the live store's paths; their outputs
  (proposals, dreams, scores) are **never ingest-eligible**.
- **Contamination channels are named and closed.** Two known ones:
  1. *Eval-dialogue leakage* — dialogues discussing eval results are themselves corpus,
     and once ingested they leak answer keys into every future masked replay of the
     same test. Mitigation: eval fixtures carry scrub-pattern files (the
     supersession-recovery §3 mechanism, generalized), and the pre-run **leak check is
     a test, not a hope** — a pattern hit fails the run before the Dreamer sees
     anything. Dialogues that name answer-key contents join the exclusion list the
     same way `docs/audits/**` and `docs/findings/**` already do for instance #1.
  2. *Eval-store leakage* — score records must never enter the complex (§6).
- **The control-corpus separation stands.** `founding-corpus.md` §2.3: the founding
  corpus cannot be Track L's control, and nothing here changes that. Eval fixtures are
  a third thing — disposable, per-test, frozen per-run — distinct from both the
  founding corpus and the frozen control. Three artifacts, three lifecycles; conflating
  any two confounds the measurements built on them.

---

## 2. The transformation algebra

A dataset variant is a **composable pipeline of typed transformations over the event
stream**, deterministic given a seed, versioned in the repo like any other artifact.
The initial operator set:

| Operator | Signature (informal) | Generalizes |
|---|---|---|
| `subset` | select events by stratum / time-window / id-set | fixture construction |
| `mask` | remove supersession edges, warrants, spans, or metadata fields | supersession-recovery §3 scrub, step 2 |
| `scrub` | remove prose patterns from chunk content (maintained pattern file) | supersession-recovery §3 scrub, step 2 |
| `inject` | insert synthetic documents/events of a declared class (§5.3) | new |
| `flip` | polarity-invert a chunk's claims, hold all else fixed | new |
| `permute` | reorder admissible event sequences | `test_order_independence` input side |
| `freeze` | pin the pipeline output with source ref + content hash | supersession-recovery §3, step 4 |

Rules:

- **Every pipeline ends in `freeze`.** A fixture is (pipeline spec, seed, source ref,
  output hash) — reproducible from the log, never casually edited. Golden-set
  *discipline* without living in `eval/golden/**`, which stays denylisted and owned by
  the drift suite (B and Θ are frozen anchors; this harness never writes near them).
- **Every `mask`/`scrub` ships its leak check.** The check greps the frozen fixture for
  the removed patterns and known answer strings; a hit fails the run. Inherited
  verbatim from instance #1 because a blind test with a leaky fixture returns
  confident, vacuous green.
- **`mask` declares its metadata policy.** The tiered-leakage lesson: masking
  supersession edges while leaving front-matter dates lets timestamp comparison recover
  direction — legitimate in deployment, near-vacuous as a reasoning test. Pipelines
  therefore run in declared tiers (e.g. `mask(edges)` vs `mask(edges+dates)`), and the
  **gap between tiers is itself a reported measurement**.
- A **test spec** is declarative: `(pipeline, seed, ladder rungs, scoring fn, baseline
  expectation, k)`. pytest parametrization over (spec × rung × seed) produces the
  results matrix; Hypothesis strategies generate `inject`/`flip` inputs where the class
  is generative. k-run reporting with per-case agreement (not single pass/fail) is
  inherited from instance #1 §5 — interpreter variance is real and reported, not hidden.

---

## 3. Ground-truth taxonomy

Every test in the catalog declares which of five ground-truth sources it scores
against. The source determines scale, trust, and failure semantics:

| Source | Examples | Scale | Trust & failure semantics |
|---|---|---|---|
| **Oracle** (mechanical) | front-matter `supersedes` blocks; codegraph edges (imports/calls/type refs, gated on P1); jj commit history — *oracle strength unverified, see V4* | large, grows for free | ground truth by construction; a miss is a real miss |
| **Owner-labeled** | findings 0010–0022; the instance-#1 answer key (2 positives / 7 negatives + rationale classes); rejected-alternatives records in parked decisions | small, highest value | certified by verdicts; append protocol per instance #1 §4 — each future certification grows the key |
| **Synthetic** | injection classes, polarity flips, distractors, shuffles | unlimited | validity bounded by generator quality; every generator needs its own honesty note (§8) |
| **Temporal** | freeze-at-t splits of the append-only log | grows with use | leakproof by construction (the log is the split) |
| **Self-consistency** | order invariance, seed stability | n/a | no external truth needed; failures are ingest/determinism bugs that **invalidate every replay-based result above them** — run first |

The oracle row has one prerequisite: a **codegraph extractor** emitting typed edges
from AST + jj into its own provenance stratum, deterministic, librarian-blind. Small,
separately planned build item (**P1**, §9); without it the only oracle is front-matter.

---

## 4. The ablation ladder: instrument attribution

F9's single most important test is beats-the-dumb-baseline (TF-IDF). This section
generalizes it: **every catalog test runs at multiple rungs, and each instrument is
credited only with its delta over the rung below.**

The ladder (rungs are cumulative):

```
r0  random / majority-class
r1  degree + recency heuristics
r2  lexical retrieval (TF-IDF — F9's existing baseline, unchanged)
r3  embedding retrieval (cosine over the fiber substrate)
r4  + typed edges (the authored/oracle topology)
r5  + signed Laplacian (frustration)
r6  + curvature (Ollivier/Forman — currently parked, Item 10)
r7  + persistent homology
r8  full Dreamer (panel + adjudicator)
```

Rules and consequences:

- **A capability claimed for the system is a claim about a rung delta.** "The Dreamer
  finds negations" means r5 (or r8) beats r3 on the polarity battery by a reported
  margin — not that r8's absolute score is high. Cosine at r3 is the floor every
  claim about reasoning must clear, because r3 passing alone means the layer under
  test is a thesaurus.
- **Re-entry conditions become named eval deltas.** Item 10's re-entry
  (Ollivier-Ricci) is currently prose; under the ladder it can be made concrete:
  *r6 − r5 > 0 with agreed margin on a named battery* (candidates: bridge detection
  against authored cross-domain fibers; injection-anomaly lift). Same template for
  any parked instrument. This note does **not** unpark Item 10 or set the margins —
  it provides the vocabulary for the unparking decision to be stated in.
- **Head-to-head slots.** Where two instruments claim the same capability, the ladder
  hosts the comparison on the same fixture: sheaf-cohomological residual vs signed
  Laplacian frustration on the contradiction battery is the first scheduled bout
  (a contradiction is a section that fails to glue; whether that formalism beats the
  cheaper signed graph is exactly a three-clause question with an executable answer).
- **Falsifier clause, per instrument** (field-guide discipline): each rung's entry in
  the results matrix carries (what it measures, validity assumptions, the observable
  that would show it is not earning its place). An instrument whose delta is
  indistinguishable from zero across the batteries at current scale gets the standard
  treatment: recorded as *no signal at this scale*, parked with a corpus-growth
  re-entry — not silently kept because the math is pretty.

---

## 5. The capability-test catalog

Six batteries. Each entry: ground-truth source · scale-now vs gated · headline score ·
falsifier. Tests already homed elsewhere are pointed at, not duplicated.

### 5.1 Structure recovery

- **Held-out supersession (design notes)** — *this is instance #1, unchanged.* Owner-labeled;
  runnable pre-Track-L; headline = hard-positive recovery + negative discrimination.
  Graded scoring (proximity noticed → supersession proposed → direction right → warrant
  matched) extends its per-case table without altering its protocol.
- **Held-out supersession (codegraph scale)** — mask VCS-derived supersession triples,
  score recovery per commit. Oracle-sourced; the only recovery test with error bars at
  current corpus size. Gated on P1 (extractor) only. Falsifier: recovery ≤ r1
  (recency heuristic) ⇒ the machinery adds nothing over "newer file wins."
- **Warrant reconstruction** — given (C, C′) with the warrant masked, produce one;
  grade topical vs semantic match against the authored warrant. Owner-labeled (the
  front-matter warrants written in the archive pass are the first key). Direction
  tests noticing; warrant tests *understanding why* — the actual reasoning claim.

### 5.2 Edge proposal

- **Distractor-resistant proposal** — for each authored edge, plant high-cosine
  wrong-semantics near-neighbors; test whether the typed proposal ranks the true
  target above the distractor. Synthetic; runnable at corpus scale post-founding.
  **Directly tests the architectural claim that embeddings are retrieval prior and
  typed edges are assertions**; falsifier: proposal ranking ≈ cosine ranking (r8 ≈ r3).
- **Temporal link prediction** — freeze at t, propose, score precision@k against
  edges actually authored after t. Temporal-sourced, leakproof, many values of t.
  Baseline to beat: r1.
- **Audit reconstruction (cross-stratum reconciliation)** — doc-asserted implementation
  claims minus codegraph-confirmed edges = overclaim candidates; score ranking against
  findings 0010–0022 (the-edge-model BUILT-&-WIRED downgrade is the canonical
  positive). Owner-labeled, n≈13, gated on P1. Payoff beyond the score: future corpus
  audits start from the reconciliation diff instead of a cold read.

### 5.3 Polarity and negation

Negation blindness is a named architectural threat; this battery is its measurement.

- **Injection classes**, ascending difficulty, each a typed `inject` generator:
  (i) *reintroduced stale content* — an already-superseded version fed back as new;
  ground truth free from front-matter; **run first: it is the realistic failure
  mode**, stale copies re-entering via ingest; (ii) *subtle negation* — `flip` with
  everything else held; (iii) *plausible fabrication*; (iv) *internally inconsistent
  documents*. **Governance clause:** the correct system response to a detected
  conflict is a typed tension flag in the adjudicator inbox — a Dreamer that mints a
  supersession edge autonomously has *failed the promotion gate*, whatever its
  reasoning score. Detection and governance are scored as two separate outcomes.
- **Rejected-alternatives typing** — the parked decisions' rejected-alternative
  records (e.g. the Rust/PyO3 rejections; TOTP-vs-Ed25519) are authored ground-truth
  *exclusion* relations. Cosine pulls rejected alternatives toward the chosen design
  (topically identical); test whether the system types them exclusionary rather than
  fiber. Owner-labeled negation on real data — sharper than any synthetic flip.
- **Polarity gradient** — documents disagreeing with a target by increasing degree;
  yields a detection-threshold curve, not a binary. "Catches contradiction, misses
  hedged disagreement" is a more useful result than pass/fail.
- **Paraphrase-invariance / flip-sensitivity pairs** — scored jointly: conclusions
  invariant under paraphrase, changed under flip. Invariance alone rewards ignoring
  the premise; sensitivity alone rewards surface-twitchiness. The invariance half
  already exists as F9's `paraphrase_invariance` — that implementation stays canonical
  there; this battery adds the flip half and the joint score. Falsifier:
  flip-sensitivity ≈ paraphrase-sensitivity ⇒ the reasoner reads geometry, not content.

### 5.4 Prediction

- **Co-change prediction** — given a code change, predict which design notes need
  updating; ground truth = docs subsequent commits actually touched. Temporal +
  oracle; runs at jj scale after P1. Operational payoff: the citation-drift detector
  run forward. (See **V1** for a live specimen.)
- **Supersession-risk ranking** — predict which notes are superseded next; baseline
  r1 (oldest-most-churned).
- **Verdict prediction** — before the owner rules on an inbox item, record a
  predicted verdict + confidence; score by Brier against the ruling. **Track L
  gated** — this is Track L instrumentation specified early, consistent with the
  verdict stream as experimental arbiter. **Governance clause: predictions are
  scored, never acted on.** A well-predicted verdict is still owner-promoted;
  anything else makes the prediction channel a soft bypass of the blessing gate.

### 5.5 Reasoning traces ("line of reason")

Dialogues and pipeline artifacts are authored reasoning traces — ground truth most
systems never have. All owner-labeled, anecdote-scale; nulls recorded as
no-signal-at-this-scale with corpus-growth re-entry.

- **Middle-masking** — mask a dialogue's intermediate turns; ask for the reasoning
  path over the complex connecting the endpoints; score concept overlap with the
  actual traversal.
- **Shuffle-recovery** — `permute` the steps of a typed pipeline artifact
  (brainstorm→design→build state machines give verified sequences for free); recover
  order; score by Kendall τ. The one trace test that scales now.
- **Derivation replay** — on real lineages (TOTP→Ed25519;
  secrets-management→vault-runtime-auth): mask the endpoint, ask for the next step.
  Highest value per case: each is a documented instance of the owner's actual
  reasoning style, which is what a mirror is supposed to reproduce.

### 5.6 Metrology (tests of the measuring apparatus)

Given that review fatigue is the named primary failure mode for Track L, this battery
may matter more than the object-level ones.

- **Calibration** — reliability diagram of proposal confidence vs adjudicated
  outcomes. F9's tercile calibration test is the unit-scale version and stays
  canonical there; this is its longitudinal extension over the eval store. An
  overconfident Dreamer floods the inbox and the stability filter cannot save it.
- **Stability** — same pass, different seeds/orderings; proposal-set overlap. Gives
  the stability filter an empirical operating point.
- **Abstention** — pose questions the fixture provably cannot answer; correct
  behavior is a dangling edge or explicit no-signal. The **hallucinated-edge rate**
  here is the single most safety-relevant number for a provenance-strict system.
- **Order invariance** — permuted admissible replays converge to identical topology.
  Already specified as metamorphic (`test_order_independence`); listed here because
  a failure invalidates every masked-replay result — it runs first, as gatekeeper
  for the whole family (§3, self-consistency row).

### 5.7 RAG substrate battery

Standard RAG evals (needle-in-haystack, retrieval P/R@k, multi-hop QA) test rungs
r2–r4 on **external corpora with zero authored topology** — the only way to isolate
discovery from replay of the owner's own labels. Two adaptations: grade the
**retrieved support subgraph and path**, not generated prose (no LLM-judge in the
loop); external corpora enter **scratch complexes only**, never near the live store.
Honest limit, recorded: these measure the substrate; passing them is necessary, not
sufficient — a system can ace multi-hop retrieval and fail warrant reconstruction.

---

## 6. The eval results store

Score records are themselves append-only: keyed by
`(spec hash, fixture hash, corpus-state ref, instrument-config hash, seed)`, written
to a dedicated store **outside the complex and non-promotable** — eval results must
not contaminate the corpus they measure (§1, channel 2). This keying is what makes
"many results → conclusions" possible: longitudinal comparison requires knowing
exactly what state each number was measured against.

**Assertions are regression-shaped, not threshold-shaped, initially.** At current
corpus scale nobody knows what good absolute numbers are; hard thresholds would
manufacture failures out of noise. Assert against the harness's own history
(no-worse-than, with agreed slack); graduate individual metrics to absolute
thresholds only when their distributions stabilize — the same lifecycle F9 already
prescribes for `THRESH` ("thresholds are tuning, not code"), applied family-wide.
The drift suite's frozen anchors (B, Θ) are explicitly **not** part of this store's
lifecycle and are never derived from it.

---

## 7. Candidate instruments this harness opens the door to

Each candidate enters through the ladder (a new rung or a head-to-head slot) and
carries its three clauses on arrival. Menu, not commitment — nothing here is
adopted by this note:

| Candidate | Battery it would serve | Measures | Key validity assumption | Not-earning-its-place observable |
|---|---|---|---|---|
| **Magnetic / directed Laplacian** | 5.1 direction recovery | direction structure via complex edge phases (supersession is directed; the ordinary Laplacian symmetrizes it away) | phase encoding of edge direction is faithful for sparse DAG-like relations | direction-recovery delta over r4 ≈ 0 |
| **Hodge decomposition** (same coboundary spine) | 5.5 traces; 5.3 inconsistency | gradient component = consistent global ordering (a potential function ≈ "line of reason"); curl/harmonic = local/global inconsistency | edge flows are meaningful on the typed graph | gradient-derived orderings no better than shuffle baseline at τ; harmonic residual flat under injection |
| **Zigzag persistence** | replay-state comparison (§1) | topological features stable across the growing/filtered replay sequence | replay states form a valid zigzag diagram | features indistinguishable from noise-model persistence |
| **Gromov-Wasserstein alignment** | cross-strata bridges (code↔prose, separate indices) | structural correspondence between per-stratum indices without a shared space | strata geometries are comparable up to isometry-ish distortion | alignment no better than lexical anchor matching |
| **Conformal prediction** | 5.6 calibration/abstention | distribution-free coverage on proposal confidence → principled inbox thresholds (review-fatigue control) | exchangeability across proposals (dubious under drift — say so) | empirical coverage misses nominal by more than slack |
| **Personalized PageRank / RWR** | new r-rung between r1 and r3 | cheap diffusion baseline | — (it *is* a baseline) | n/a — baselines earn their place by being beaten |

The philosophy stands: math as tool, discarded when it stops matching data, with the
eval matrix as the discard mechanism. Different instruments are *expected* to win
different batteries — the matrix is how "one is good at negations, another at lines
of reasoning, another at supersessions" becomes a recorded fact instead of a hunch.

---

## 8. Harness quality: testing the tests

- **Mutation testing of instruments.** Deliberately degrade an instrument (shuffle a
  Laplacian's signs, zero a curvature term, swap an interpreter for its r0 stub) and
  verify the suite's scores move. A battery that cannot detect a lobotomized
  instrument has no power over a subtly wrong one. Mutation score = fraction of
  planted degradations detected; this is the harness's own falsifier.
- **Coverage matrix.** Batteries × (stratum × edge-type × transformation). Empty
  cells are recorded as untested capability claims, not assumed green.
- **Discrimination analysis.** Over the accumulated eval store, per-test
  discrimination (does it separate ladder rungs at all?). Tests that never
  discriminate are dead weight and get cut — the three-clause test applied to the
  tests themselves.
- **Generator honesty notes.** Every synthetic generator (§5.3 classes, distractors)
  records what it cannot represent (e.g. `flip` cannot generate *hedged* disagreement
  — that is the polarity gradient's job) so a green synthetic battery is never read
  as covering its class exhaustively.
- **Power honesty.** Owner-labeled batteries report intervals, not points, at n≤13;
  the standing no-signal-at-this-scale rule applies to the assertions, not just the
  results.

---

## 9. Wiring, prerequisites, and sequencing

**Homes** (per `test-organization.md`): specs and pipelines in the harness's own
tree (proposal: `eval/capability/` — sibling of `eval/drift.py`, outside
`eval/golden/**`); fast oracle/self-consistency tests → CI tiers per the §2 profile
matrix; ladder sweeps → scheduled, alongside `longitudinal/`. All Dreamer-touching
runs in the `dream_rnd` lane.

**Prerequisites, explicit:**

- **P1 — codegraph extractor** (small build item, needs its own build plan): AST +
  jj → typed edges, own stratum, deterministic. Unlocks the entire oracle row.
- **P2 — provenance migration `--apply`** (existing blocker, unchanged): corpus-scale
  batteries over a mirror that currently reads empty measure nothing.
- **P3 — founding corpus ingest** (existing blocker, unchanged): authored-topology
  ground truth for 5.2/5.3/5.5 at corpus scale; instance #1's Q4 (musings in the
  blind corpus) resolves downstream of this, per its own parked-decisions table.
- **P4 — filtered replay** (verification, V2): confirm the event log supports
  selective replay, or scope the delta.

**Runnable before P2/P3** (i.e., now, modulo P1/P4): instance #1 as specified;
shuffle-recovery on pipeline artifacts; order-invariance and seed-stability;
codegraph held-out recovery, temporal link prediction, and co-change prediction once
P1 lands. Everything else queues behind the existing blockers — this note adds no
new path around them.

**Track L relationship:** the shadow runner and this harness want the same replay
machinery; build it once (P4 scopes whether that is already true). Verdict
prediction and longitudinal calibration are Track L's first passengers, not
independent workstreams.

**Verification items (accuracy discipline — do not assume).** These are
builder/orchestrator tasks, each a grep-and-cite deliverable with path:line
evidence, to be resolved before any build plan cites the corresponding section.
None are resolved by this note:

- **V1** — `docs/NOTATION.md` family-5 banner states `core/complex/` is *not built*
  (updated 2026-07-01); Track H completion with a large passing test count is
  understood to postdate that. Verify and reconcile the banner. If stale, it is (a) a
  finding-class doc-drift instance and (b) a ready-made positive example for the 5.4
  co-change battery — record it in the answer key either way.
- **V2** — confirm replay granularity (P4): does the current raw-store re-ingest
  path admit event-level filtering, or is `subset` a new capability? Cite the ingest
  code either way.
- **V3** — confirm `eval/golden/**` denylist boundaries so `eval/capability/` cannot
  collide (the bp-005 lesson: check the denylist *before* the build plan, not after
  the builder reverts). The denylist claim itself is sourced from
  `supersession-recovery-evaluation.md` §3, not read from config — verify at source.
- **V4** — the jj-history oracle claim (§3) is *aspirational until verified*:
  determine what supersession information is mechanically extractable from the
  existing history (diffs, change-ids, message text) versus what requires adopting a
  commit-trailer convention prospectively. If the existing history yields only
  heuristic triples, the codegraph recovery battery (§5.1) has error bars over a
  smaller-than-claimed oracle set, and the note's "large, grows for free" applies
  only going forward from convention adoption. Scope accordingly.
- **V5** — three §5 ground-truth references are carried from prior dialogue, not
  read this session: (a) the findings range 0010–0022 and per-finding shape assumed
  by the audit-reconstruction battery (§5.2 — instance #1 certifies only
  finding-0021 directly); (b) the repo locations and structure of the
  rejected-alternatives records cited in §5.3 (assumed to live in
  `docs/research/security-planes.md` and parked-decision tables — confirm they are
  extractable as typed exclusion pairs, or the battery needs a labeling pass first);
  (c) the claim that the archive-pass supersessions carry warrant blocks in
  front-matter suitable as the first warrant-reconstruction key (§5.1). Each is a
  grep-and-cite task for the builder before the corresponding battery is planned.

---

## 10. Non-goals

- Does not unpark Item 10 (Ollivier-Ricci) — it supplies the vocabulary (§4) in which
  that unparking decision can later be stated, with margins set at that time.
- Does not modify F9, its `THRESH` surface, instance #1's protocol, or the drift
  suite's frozen anchors.
- Does not authorize any build. P1 and the harness skeleton each need their own
  build plan through the standard pipeline.
- Does not validate the Dreamer generally — it is the frame in which specific
  capability claims become falsifiable, battery by battery, rung by rung.
- Does not ingest anything, anywhere, ever, from an eval run.

## 11. Open questions

- **Q1** — spec format: pytest-parametrized Python, or declarative YAML compiled to
  pytest? (Default leaning: Python specs, YAML only if a second consumer appears.)
- **Q2** — ladder rung granularity: are r5–r7 separate rungs or one
  "instrument-scored" rung with per-instrument ablation flags? (Cheaper matrix vs
  cleaner attribution.)
- **Q3** — k and agreement thresholds family-wide: inherit instance #1's Q3 answer,
  or per-battery?
- **Q4** — external RAG corpus selection for 5.7 (license, size, multi-hop structure)
  — and whether it enters the repo or is fetched per-run into scratch.
- **Q5** — eval store backend: same SQLite append-only pattern as the event log, or
  DuckDB (it is analytical by nature)?

## 12. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| Instrument candidates in §7 | menu only; none adopted | each enters via a ladder slot with three clauses + a named battery |
| Absolute thresholds in the eval store | regression-shaped assertions | per-metric distribution stability over the accumulated store |
| Musings in blind fixtures | inherit instance #1 parked row | founding corpus ingested with reconstructed dates (P3) |
| IRT-grade test-difficulty modeling | plain discrimination analysis (§8) | eval store large enough that difficulty modeling changes a decision |
| LLM-judged trace scoring (5.5) | concept-overlap / τ only | a case where mechanical scores demonstrably mis-rank against owner judgment |
