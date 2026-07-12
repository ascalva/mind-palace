---
type: design-note
id: dn-self-sensing
status: draft # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only # nothing built; the cost ledger (the first stream's source) exists in plan frontmatter, the projection does not
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/brainstorms/self-sensing.md # the consolidated, graduate-ready arc (warrant)
  - docs/brainstorms/cost-forecasting.md # origin thread; keeps the cost-ledger half + parked report generator
  - docs/design-notes/code-observation-projection.md # §2.2 interpreter contract; §2.4 seam; the sibling precedent
  - docs/design-notes/authorship-distance-axis.md # §3.7 interpreter formalism; the a-position cross-map question
  - docs/design-notes/observed-data-and-the-assistant-tier.md # the firewall, inherited verbatim
  - docs/findings/finding-0020.md # the honesty class: write-side substrate ≠ wired consumer
  - docs/findings/finding-0034.md # the CI cost-plane — a candidate later stream
supersedes: null
superseded_by: null
warrant: docs/brainstorms/self-sensing.md
---

# Self-sensing — the proprioceptive projection (φ_self into the observed stratum)

> Composed by the orchestrator (Fable/xhigh design session, 2026-07-12) from the
> graduate-ready brainstorm; filed as `draft`. Ratification is a hand edit by the owner —
> no command performs it, and `gate-guard` denies any agent attempt. `/graduate` refuses
> this note until `status: ratified`.

## 1. Purpose and scope

### 1.1 What this note decides

The agent's own operation is a **sensed stream** (owner arc, 2026-07-11): the
estimate-vs-actual cost ledger, and eventually other operational facts, are readings of
an instrument — and the instrument is one the system already senses. **φ_code and φ_self
read the same instrument (the repo) at different layers**: φ_code reads the code layer
(AST symbols per commit); φ_self reads the **workflow-artifact layer** — plan frontmatter
cost blocks, seal entries, findings, PROGRESS checkpoints. Commits are readings for both.
This note decides the stream's classification (a proprioceptive axis in the sensor
taxonomy), its interpreter contract, its schema and entry seam, its first stream (the
cost ledger), the worldview-supersession record that makes the stratum an
epistemology-over-time, and the safety line that keeps self-reference from regressing.

The one-sentence architecture: **φ_self is a second deterministic interpreter over the
repo — projecting committed workflow artifacts into an OBSERVED-only `agent_observations`
store through a sibling of the bp-012 seam — whose interpreter-versioned supersession
chain records not only what the agent did, but how the agent's way of seeing itself
changed over time.** This is the owner's distillation made structural: *"the projection
maps FROM agents interpreting results OVER TIME."*

### 1.2 Out of scope (explicit non-goals)

- **Any consumer.** The stratum is write-side. No recalibration loop, no scheduler input,
  no dreamer path. The first consumer (e.g. making the graduate skill's sizing heuristic
  empirical) requires its own design pass — this note builds the substrate only.
- **Auto-recalibration and model-mix optimization.** Choosing tiers from seal history
  stays a deliberate, workflow-layer act over committed artifacts (cost-forecasting.md's
  open questions) — never a live loop out of this store.
- **The cost-report generator** — workflow-side tooling; stays parked in
  `cost-forecasting.md` with its own re-entry (~2 weeks of seal data).
- **Transcript-derived streams.** φ_self reads committed artifacts only — never
  conversation transcripts (see §2.3; parked PD-b, owner-amendment re-entry).
- **No new provenance class.** Same ruling as the code stream: `OBSERVED` under the
  current enum; the axis note re-labels at its own gate (§5).
- **Shared calibration machinery with core.** Pattern, never code (§2.7).

## 2. Principles / decision

### 2.1 Stream classification — the proprioceptive axis

The sensor taxonomy gains an axis:

- **Exteroceptive** — biometric (the owner's body), code (φ_code): sensing the WORLD.
- **Proprioceptive** — φ_self: the agent sensing its OWN operation over time (cost,
  estimation error; later candidates: session shapes, tool-use, finding rates).

Classification of the rows: **`OBSERVED`**, by the code-stream note's §2.1 reasoning
inherited verbatim — never `AUTHORED_*` (agent output entering as authored would be
masquerade at origin), never `CURATED`, never `INTERPRETED` (these are measurements of
workflow facts, not inferences over the corpus). The subject being *the agent itself*
changes nothing about the class: what enters the corpus is exhaust about operation, and
it is mirror-opaque like every observation (§2.6).

The self-sensor is the **third stream through the sensing seam** (biometric, code, self)
— confirming the seam's core bet that it is sensor-agnostic. It arrives as a third
*instance*, not new infrastructure.

### 2.2 φ_self — the interpreter contract, instantiated

φ_self satisfies the axis note's §3.7 interpreter shape exactly as φ_code does
(code-observation-projection.md §2.2), and must keep doing so:

- **Deterministic.** Parses committed artifacts — YAML frontmatter, seal entries — plus
  git facts. No model in the loop; re-running φ_self over the same commit yields
  identical observations (content-addressable, testable). This is why the domain is
  committed-artifacts-only: determinism, privacy, and the regress line (§2.6) are all
  bought by the same restriction.
- **Sole path in.** Agent observations enter through φ_self and its sibling handoff only
  — never through vault sync, never through dialogue capture, never hand-inserted.
- **Transform-attributed.** Each batch attests `self_sensor / project_agent_observations`
  with the commit sha as input and the batch content hash as output, chained — the
  `CodeSensingHandoff.emit_batch` pattern verbatim.
- **Versioned re-interpretation.** A φ_self change is a re-projection: new rows
  superseding old at the same identity key, never in-place mutation. For this stream the
  clause is not bookkeeping — it is the point (§2.4).

**The artifact-first corollary.** If a fact about operation is worth observing, the
workflow must first make it a committed artifact — exactly the existing note-taking
obligation, now load-bearing for sensing. The ledger discipline (measured usage into
every seal) is retroactively revealed as sensor-calibration hygiene: it feeds S1.

### 2.3 The observation schema and the first stream

One observation = one fact about one workflow artifact, read at one commit:

```
AgentObservation:
  commit_sha   str    # time coordinate — the commit that landed the fact (git's content address)
  stream       str    # 'cost' first; each stream is a vocabulary entry, licensed additively
  subject_id   str    # the artifact the reading is about (e.g. 'bp-011')
  key          str    # the fact within the subject — stream-scoped vocabulary ('estimate' | 'actual')
  payload      JSON   # the fact, structured verbatim (e.g. {model, tokens, tool_calls, duration_min})
  interpreter  str    # φ_self version — the worldview coordinate (§2.4)
  provenance   OBSERVED (structural; no provenance parameter exists anywhere in the module's API)
```

Identity key: **(commit_sha, stream, subject_id, key)**; `interpreter` is the version
coordinate *outside* the identity key (§2.4). Idempotence: re-projection under the same
interpreter is a no-op (the `INSERT OR IGNORE` + attested-batch pattern the code store
proves).

**S1 — the cost stream (the only stream this note licenses).** Source: the `cost:` block
in build-plan frontmatter (`docs/templates/build-plan.md`; live since 2026-07-11).
Grain: one observation per cost fact — `estimate` lands at the graduation commit,
`actual` at the seal commit. The estimate-vs-actual pair is a **join, not a row**: the
two facts have different time coordinates because they came into being at different
moments, and the stratum records that honestly. First live pair: bp-011
(`estimate: {sonnet, 350k}` → `actual: {sonnet, 163k, 142 calls, 19 min}` — 0.47×).
Backfill over all sealed plans is cheap (the artifacts all exist in git) — PD-d records
the default.

Later candidate streams are **named but not licensed** — each re-enters per PD-a when
its facts are committed artifacts (or plain git facts), as its own small additive plan:
on the φ_self plane, session shapes, tool-use histograms, Stop-gate/finding rates, the
CI cost-plane (finding-0034); on the φ_code plane (owner direction, 2026-07-12 capsule),
**documentation-over-time** (the doc-coverage precursor already lives in the snapshot
ledger) and **scope-of-changes/churn per commit**. All streams share `commit_sha` as the
time coordinate — deliberately: that shared coordinate, plus the Lane-1 reference edges
and the supersession chains, is the join geometry a future cross-stream consumer would
weave threads through (§5).

### 2.4 The worldview record — supersession as epistemology-over-time

The interpreter IS the view. Per the ratified §2.2 contract, re-interpretation is
versioned supersession at the same identity key — so when the agent's way of reading its
own operation changes (new task-shape bins, a new normalization, a new notion of what
counts as "cost"), re-projecting the SAME artifacts under the NEW φ_self version
supersedes the old observations, and **the supersession chain is the fossil record of
the changing self-model.** The stratum then holds two orthogonal histories at once:

- across `commit_sha` at fixed `interpreter`: *what the agent's operation was, over time;*
- across `interpreter` at fixed identity key: *how the agent read that operation, over time.*

The second is the owner's epistemology-over-time, and it generalizes to every sensor:
each stream records readings AND the evolution of its interpretive view. The evolution
study gains this as an axis alongside economics (§5, owner call).

**The erasure test (owner question, 2026-07-12 capsule).** Would the system keep flowing
in the same direction if the edge *history* were reset but the current *snapshot* kept?
Today, behaviorally, yes — the stratum is passive, nothing that acts consults the record
— but the study would lose its baseline, and the study is the point. Once gated
consumers exist, no: recalibration and regime-shift detection are functionals of the
record, so the trajectory diverges at the first history-consuming act; and where edge
strengths update incrementally, the snapshot is itself compressed history — the
direction survives but attribution and shift-detection do not (dead reckoning: course
corrections came from the record, so the current course fossilizes). Erasure-invariance
is thus the operational form of the owner's smart-vs-wise distinction: a merely smart
system's trajectory is a function of its state; a wise one's is a functional of its
path. This system starts erasure-invariant and gains path-dependence only through
deliberate gates — one audited consumer at a time.

**The mechanism gap (verified in-session 2026-07-12).** The built code-observation store
implements only the degenerate case: `PRIMARY KEY (commit_sha, path, qualname)` +
`INSERT OR IGNORE`, plus a `projections` bookkeeping table that makes `sync()` skip
already-attested batches — same-interpreter idempotence, with no interpreter-version
column and no way to hold a superseding row. The §2.2 clause is ratified contract, not
yet built mechanics. **B-a builds it** — for the observation-store *family*, so φ_code
inherits the same upgrade: version column outside the identity key, latest-per-identity
as the default read, the chain queryable. This implements what §2.2 already states; no
supersession or amendment of the code-observation note is required.

### 2.5 The seam — a sibling, by recorded precedent

The brainstorm's first open question — own store vs a payload type on the existing seam —
is **already answered by bp-012's Q1 resolution**, recorded in `core/sensing.py`: the
handoff `collect()` is typed to its payload, so a second payload type cannot ride an
existing handoff without breaking its contract. The sibling pattern is the decided shape.
So, by direct analogy with `CodeSensingHandoff` / `CodeObservationStore`:

- **`AgentSensingHandoff`** (`core/sensing.py` sibling) — ops-side sensor
  (`ops/self_sensor.py`, the `ops/code_sensor.py` precedent: unsealed, restic-class)
  writes one batch per projected commit to `<handoff>/agent_observations/<sha>.json`;
  core collects. Atomic files, `from_dict` in, consume-and-heal rescan semantics.
- **No outbound half** — like the code stream, the instrument is local; nothing crosses
  toward a carrier, so there is no `Effect`/`EffectView` ceiling and no `[effectors]`
  gate to apply. The inbound guarantees are identical and total: the wire payload carries
  no provenance field, `to_row()` mints `observed` with no parameter, `ObservedView`
  admits the rows, `MirrorView` refuses them.
- **`AgentObservationStore`** (`core/stores/agent_observations.py`) — the
  `code_observations.py` mold: structural OBSERVED-only, identity-keyed idempotence,
  SQLite expected per that store's Q2 reasoning (an identity-keyed ledger, not the DuckDB
  telemetry lane — V4 confirms against CONVENTIONS). Reset semantics are **split by
  re-derivability** (owner ruling, 2026-07-12 capsule): current *readings* are
  corpus-class — wiped with the corpus and rebuilt by re-projection from git. The
  versioned *history* B-a creates — superseded worldview chains and, later,
  edge-strength series — is **ledger-class, reset-guarded**: it does not rebuild (the
  old interpreters no longer exist at HEAD), and the study of its change over time is
  the stratum's point. Mechanism (whole-store guard vs a readings/history split) is
  pinned at graduation with the rejected alternative recorded.

### 2.6 The safety line — why self-reference does not run away

Three cuts, from operational to structural:

1. **Passive stratum.** The store is write-side; the daemon does not consume observations
   (finding-0020 honesty — stated here, in the store docstring, and in this note's
   `implementation` field). Self-observations accumulate as history, not a feedback
   loop; any future recalibration is a deliberate, gated workflow-layer act over
   committed artifacts, not a consumer of this store.
2. **Domain excludes codomain.** φ_self reads committed workflow artifacts; it writes
   corpus-store rows. Its output is not in its input domain, so *φ_self observing its own
   observations is unrepresentable* — the regress has no fixed point to start from. Owner
   sharpening (2026-07-12 capsule): the sensor is **stateless** — it reads
   deterministically, projection-maps, and forgets; the store is durable retention of
   readings for future use, never working state a later run consumes. No accumulator
   exists for a loop to build on. (The
   streams do observe each other's **instruments** — φ_code will read
   `ops/self_sensor.py`'s docstrings as code — but never each other's **output**; an
   instrument being visible is not a loop.)
3. **The inherited firewall, verbatim.** OBSERVED provenance, mirror-opaque
   (`MIRROR_READABLE` untouched — the self-model never reads these rows), no promotion
   path (agent exhaust never becomes authored; the path does not exist, the
   code-stream's stronger-than-I1 stance inherited), sealed core touches no network
   (φ_self runs ops-side; core only collects). "The model advises; code acts": the
   sensor is code parsing artifacts — the model never introspects unboundedly into the
   corpus.

### 2.7 Calibration is a shared pattern, never shared machinery

The core's scheduler estimator (context/complexity pre-admission) and the workflow's cost
ledger are the same primitive — *predict → execute → measure → update the predictor* —
at two layers. What transfers is the **methodology**: bin predictions by task shape,
require a sample threshold before recalibrating, detect regime shifts, never retune off
one point (the bp-011 seal's explicit refusal to retune from a single 0.47× datum is the
standing precedent). What does not transfer is code: the units differ (LLM tokens vs
memory-GB/compute), and a shared calibration library would couple the workflow layer to
sealed core against non-negotiables #2/#3. Decision: **independent implementations,
common documented pattern.** (PD-c records the re-entry.)

### 2.8 Three-clause razor

1. **Measures:** the agent's own operation over time (the calibration axis) and the
   evolution of its way of reading that operation (the epistemology axis).
2. **Valid when:** extraction is deterministic over committed artifacts only; the
   identity-key/interpreter-version split holds; the §2.6 firewall holds structurally.
3. **Fails its keep if:** after ~a month of accumulation the cost stream is too sparse to
   bin by task shape, or a deliberate recalibration pass finds the projected history adds
   nothing over reading the seal files directly. Record as no-signal and stop projecting;
   the ledger discipline in the artifacts keeps its full value either way.

## 3. Consequences

### 3.1 What this note licenses

On ratification: a small build-plan family — the interpreter-version supersession
mechanics for the observation-store family (B-a), the `agent_observations` store +
sibling seam + φ_self cost-stream projection with backfill (B-b/B-c). It licenses **no**
consumer, no recalibration loop, no additional streams (each re-enters per PD-a), no
mirror change, no report generator (parked elsewhere).

### 3.2 Verification items (grounded pass before any build)

- **V1** — seam sibling at source: confirm `CodeSensingHandoff`/`CodeObservationStore`
  signatures still match what §2.5 assumes (verified 2026-07-12; a build re-verifies at
  its own HEAD).
- **V2** — the supersession gap: confirm the changed-interpreter re-projection is today a
  silent no-op (`projections` table skip); pin B-a's design — version column vs
  superseded_by chain, the latest-per-identity read, and **what identifies an interpreter
  version**. Recommended default: a declared semantic version PLUS a test asserting the
  sensor module's content hash matches the pinned hash for that version (the
  argless-mypy==69 ratchet pattern — an unbumped change is a red test, not a silent
  skip). Rejected: bare declared constant (a forgotten bump reproduces the exact silent
  no-op being fixed); pure content-hash (every refactor re-projects, filling the chain
  with non-worldview noise). The `projections` skip-table key gains the version too.
  **The escalation candidate is RESOLVED** (owner ruling, 2026-07-12 capsule in the
  warrant brainstorm): the epistemology record is **ledger-class, reset-guarded** —
  §2.5's split-by-re-derivability. V2's remaining duty is mechanical: confirm the
  guard's implementation fits the ruling, and check the interaction with the code
  store's plan-level Q4 (its corpus-side call predates chains — B-a revisits it for the
  history it creates, not for readings; the ratified note text pinned no reset
  semantics, so no amendment is triggered).
- **V3** — the source inventory (the feasibility probe; read-only, can run before
  ratification): parse every `docs/build-plans/*/plan.md` cost block; report how many
  complete estimate/actual pairs exist, their task-shape spread, and whether frontmatter
  form is stable enough for deterministic extraction (feeds the parked template
  tightening if not).
- **V4** — store engine: confirm SQLite vs DuckDB against CONVENTIONS §Data stores with
  citations (expected SQLite per the code store's Q2 precedent; record the rejected
  alternative).

### 3.3 Builder items (post-ratification, blast-radius ordered)

- **B-a** — interpreter-version supersession mechanics in the observation-store family
  (additive migration; φ_code inherits). _Falsifier: a re-projection under a bumped
  interpreter version either mutates rows in place or is silently ignored._
- **B-b** — `AgentSensingHandoff` + `AgentObservationStore` + φ_self over the cost
  stream; attested, idempotent per commit. _Falsifier: a second projection of the same
  commit changes row count; or any API surface accepts a provenance parameter._
- **B-c** — backfill over all sealed plans' graduation/seal commits. _Falsifier: a
  sealed plan with a complete cost block yields no estimate/actual join._

## 4. Parked decisions

| id   | decision                                   | default recorded                                                       | re-entry condition                                                                      |
| ---- | ------------------------------------------ | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| PD-a | additional streams (session shapes, tool-use, finding rates, CI plane) | not licensed; named only                    | per stream: its facts exist as committed artifacts + a small additive plan               |
| PD-b | transcript-derived streams                 | never (committed artifacts only)                                        | owner-ratified amendment with a concrete case that artifacts cannot carry                |
| PD-c | shared calibration machinery with core     | pattern only, independent implementations                               | a third estimator plane exists AND duplication causes a measured divergence in method    |
| PD-d | historical backfill vs forward-only        | backfill (artifacts all in git; projection cheap)                       | V3 measures the parse non-trivial or frontmatter too unstable to read deterministically  |
| PD-e | estimate-vs-actual as row vs join          | join (two facts, two time coordinates)                                  | a consumer design shows the join reconstruction is the dominant cost                     |
| PD-f | utility-graded edge durability             | binary — history is ledger-class, guarded (owner ruling 2026-07-12)     | a built consumer produces per-edge utility measurements worth weighting retention by     |

## 5. Open questions

- **The axis cross-map**: the code stream recorded a₂ (author-sensed) for its rows. Are
  proprioceptive rows also a₂, or does the agent-sensing-itself warrant a distinct
  position? Defer to the authorship-distance-axis gate; recorded here so re-labeling
  needs no redesign — the OBSERVED landing is unaffected either way.
- **The evolution study**: does it formally adopt the epistemology axis (§2.4) alongside
  economics? Owner call at ratification; costs nothing now.
- **Rule of three**: with a third sibling through the seam, does a generic
  `ObservationStream` abstraction pay for itself, or do three explicit siblings stay
  clearer? Default: siblings stay explicit; a refactor decision for a future plan, not
  this note.
- **The weaving consumer** (owner direction, 2026-07-12 capsule in the warrant
  brainstorm): the more related planes accumulate — cost, documentation,
  scope-of-changes, over time — the higher the chance a thread weaves through them via
  fibers and supersession edges; "see what the dreamer can reason about that." Per the
  standing firewall this lands as a Track-D / correlator-class reader over
  `ObservedView` emitting INTERPRETED proposals (dreamer-proposed authority) — the
  mirror-side dream path stays opaque to observations. That consumer's charter belongs
  to Track D's design pass; this note only guarantees the substrate it would read
  (shared time coordinates, versioned chains) exists and is safe to accumulate. The
  charter's mathematical vocabulary — phase space, Hodge threads, persistence, the
  continuum-approximates-the-discrete inversion — is consolidated in
  `docs/brainstorms/edge-dynamics-and-continuum.md` (2026-07-12).

## Cross-references

Verified in-session 2026-07-12: `core/sensing.py` (`SensingHandoff`; `CodeSensingHandoff`
+ the Q1 sibling-precedent comment; `ObservedView` constructor-enforced observed-only);
`core/stores/code_observations.py` (structural OBSERVED mint; `PRIMARY KEY (commit_sha,
path, qualname)` + `INSERT OR IGNORE`; `projections` bookkeeping; SQLite Q2 note;
finding-0020 honesty note); `docs/templates/build-plan.md` (the `cost:` estimate/actual
block); `docs/build-plans/bp-011/plan.md` (the first live pair, 0.47×). Asserted from the
design record: code-observation-projection §2.1/§2.2/§2.4/§2.6 (ratified);
authorship-distance-axis §3.7; observed-data-and-the-assistant-tier (firewall);
findings 0020/0034; the owner capsules of 2026-07-11 in `cost-forecasting.md`.
