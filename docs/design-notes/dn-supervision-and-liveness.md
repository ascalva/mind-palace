---
type: design-note
id: dn-supervision-and-liveness
track: ops
status: draft
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/brainstorms/supervision-and-liveness.md       # the commissioning capsule (session-47)
  - docs/brainstorms/design-pass-routing.md            # the routing map this note amends (see §1.1)
  - docs/brainstorms/local-model-runtime.md            # NEW NOTE 2 — shared boundary (§2.6)
  - docs/audits/ops-wave-2026-07-25.md                 # the audit that produced the warrants
  - docs/findings/finding-0171.md                      # unbounded drain (oq-0035's origin)
  - docs/findings/finding-0178.md                      # there is no job timeout
  - docs/findings/finding-0188.md                      # the wedge detector's ceiling
  - docs/findings/finding-0165.md                      # background starvation under a long job
  - docs/findings/finding-0174.md                      # the ceiling ignores the embedder
  - docs/findings/finding-0191.md                      # write_scope is not a partition (graduation input)
  - docs/build-plans/bp-105/journal.md                 # why nothing on the loop can emit during a wedge
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0188.md
---

# Supervision and liveness — the OS layer owns the thread

> Filed by the chat agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it, and `gate-guard` denies any
> agent attempt (§10). `/graduate` refuses this note until `status: ratified`.

**Owner's mandate (2026-07-25, verbatim):** *"the general liveness probe … is the OS side of the
system, it manages state, manages runs, manages memory, manages that the system runs as expected,
and the system's demands will only increase as we keep stacking features, density, runs, etc, so
we have to get this right"* — and the acceptance bar: *"we do not want something that is going to
allow us to shoot ourselves in the foot without realizing; the system's OS needs to maintain the
consistency and accuracy of the system with precision and appropriate guard rails."*

Read "without realizing" as the design test throughout: a bad state entered **silently** fails
this note even if the bad state is rare. Fail-closed beats fail-open; structurally-enforced beats
conventionally-observed; a loud wrong answer beats a quiet one.

## 1. Purpose and scope

This note decides the **execution model of the supervisor** — who owns the thread while a job
runs — and everything downstream of that one decision: how a running job is observed, bounded,
cancelled, and how its results are landed. It takes a position on **oq-0035** (§2.4) and carries
the evidence that position rests on (§2.3, the handler-shape survey).

### 1.1 Scoping decision — this note SPLITS OUT of NEW NOTE 1, deliberately

`design-pass-routing.md:57-64` scoped ONE ops note (NEW NOTE 1) with *liveness* as a Tier-2 macro
axis inside it. This note amends that assumption: **supervision/liveness is its own note, and
NEW NOTE 1 keeps the rest.** The routing map is not silently contradicted — this section is the
reconciliation it asked for. Three reasons:

1. **This material is a prerequisite, not a sibling.** Three of NEW NOTE 1's scoped items —
   the liveness macro axis, detection lag as a tracked metric, and "anomaly as a computable
   predicate" — need a continuous probe, and a continuous probe needs a home that is not the
   blocked serve loop (`ops/lifecycle/launcher.py:676` + `scheduler/supervisor.py:99-107`; the
   capsule's Q5). That home is exactly what this note decides. Writing the instrument doctrine
   before the execution model would park NEW NOTE 1's load-bearing sections on this one anyway.
2. **The gate-count arithmetic does not get worse.** The routing map's real constraint is the
   panel/ratification queue, and it already says oq-0035 must be ruled *"without it the ops note
   carries a parked decision in a load-bearing section"* (`design-pass-routing.md:140`). This
   note IS the evidence package for that ruling: ratifying it and ruling oq-0035 are one owner
   sitting, not two. NEW NOTE 1 then arrives at the panel without a parked decision inside it.
3. **A single mega-note fails the ratification bar.** The owner reads non-goals and falsifiers
   explicitly at ratification (finding-0150 discipline). One note carrying an execution-model
   change AND the command-center doctrine AND the ratchet doctrine is too large to ratify in one
   honest read — the M2/K1 lesson (finding-0148).

**What NEW NOTE 1 retains** (unchanged from the routing map): the command center TIER 2 (macro
axes: corpus completeness · history realized · causal density · drift · headroom · liveness *as a
rendered axis*); the level-vs-derivative layout rule; cost as a checkable property / the
perf-ratchet suite generalized (OPS-6); structured residuals as an instrument requirement;
detection lag as a *tracked metric* (its four-mode refinement is defined here, §2.8, and handed
to NEW NOTE 1 to render). **What moves here:** the four-mode taxonomy, the one-seam finding, the
compute/land split, the oq-0035 ruling package, the shutdown escalation contract (OPS-4's design
half), and — answering the routing map's open Q2 — **finding-0165 (background starvation)**,
because fairness between lanes is a property of the execution model (the batch unit, §2.5), not
of the instrument layer.

### 1.2 Non-goals (load-bearing — read at ratification)

- **NOT a per-lane mtime probe for each store.** The capsule's explicit anti-goal, kept: bp-105's
  store-clock (`ops/lifecycle/snapshot.py:381-412`) is right for the embedding lane and does not
  deserve to be a pattern. N ad-hoc detectors, each with its own falsifier and its own rot, is the
  failure mode this note exists to avoid. (Owner-stated via the capsule.)
- **NOT the command-center Tier 2 / macro-axis rendering.** Retained by NEW NOTE 1 (§1.1).
- **NOT the local model runtime.** llama.cpp-direct migration, embedder residency re-grounding,
  and `resident_gb` semantics are NEW NOTE 2's (finding-0174 folds there). This note only flags
  the shared boundary (§2.6) and constrains its own design to not foreclose it.
- **NOT a retry / dead-letter / backoff policy redesign.** `[INFERENCE]` The queue's existing
  terminal states and `attempts` counter stay as they are; a killed job's disposition is decided
  here (§2.4) but a general retry policy is not designed. Inferred out-of-scope: no artifact
  scopes it here, and it is separable.
- **NOT the queue schema beyond additive columns.** `[INFERENCE]` `data/queue.sqlite` carries
  300k+ lifetime rows and is never recreated (`scheduler/queue.py:117-120`); this note licenses
  only additive-only migrations in the established `_MIGRATIONS` pattern.
- **NOT the watcher enqueue-per-poll defect.** finding-0165's *observation* half (watchers appear
  to enqueue every poll tick) stays its own codebase item; this note fixes the starvation it
  amplifies, not the enqueue behavior.
- **NOT agent/model-tier behavior.** Nothing here touches what any model does. This is pure
  "code acts" layer (Constitution §II.2); the model side is unchanged.

## 2. Principles / decision

### 2.1 The failure taxonomy (carried from the capsule, verified against code)

Four modes, four different mechanisms — the taxonomy survives verification and is kept:

| mode | definition | mechanism today | status |
|---|---|---|---|
| 1 GONE | process dead, ledger says RUNNING | pid liveness + identity (`_supervisor_alive`, launcher.py:166-212; `run_state`, snapshot.py:91) | ✅ have |
| 2 STUCK-IN-LANE | job alive, landing nothing in its lane | store-clock side channel (snapshot.py:199-223) | ⚠️ embedding lane only (bp-105's stated ceiling) |
| 3 SLOW | progressing, too slowly to matter | a rate AND an expectation | ❌ none (no denominator exists — §2.8, Q3) |
| 4 HUNG | thread wedged, stopped cooperating | external observation + the power to act | ❌ none, and impossible without §2.2 |

The trap stands verified: a cooperative heartbeat detects (3) and not (4), because a wedge IS a
handler that stopped cooperating. bp-105's own build record proves the stronger form: **nothing
on the supervisor's thread can emit while the wedge is happening** — the health tick, snapshot
tick and housekeeping tick all live on the loop the handler blocks
(`launcher.py:675-695`), and even `Supervisor._record` runs only *after* `handler(job)` returns
(`supervisor.py:96, 109-115`). The one channel that worked (the store's filesystem mtime) worked
precisely because it is written from *inside* the blocked call (bp-105 journal, Checkpoint 3).

### 2.2 The structural finding, confirmed: one seam, and it is worse than one job

`Supervisor.tick` calls `handler(job)` synchronously and unbounded (`scheduler/supervisor.py:87`).
Cancellation and observation are therefore the same missing seam: you cannot budget a synchronous
in-process call from outside it, and you cannot observe from a loop it blocks.

Verified and **sharpened**: the blocked span is not one job but the whole drain. `_serve` calls
`c.supervisor.run()` with no `max_ticks` (`launcher.py:676`; `supervisor.py:99-107` loops until
nothing is runnable), so with a 1,766-job backlog the health/snapshot/housekeeping ticks do not
run even *between* jobs. The documented contract ("record vitals … and repeat", supervisor.py:10)
holds inside `run()`, but the launcher's supervisory functions stall for the full backlog. As
lanes multiply, P(something is running) → 1 and the supervisor's supervisory duty-cycle → 0. That
is an availability property degrading with density — the owner's exact argument.

### 2.3 I1 — the handler-shape survey (the load-bearing evidence)

Every registered kind in the daemon's handler map (`ops/lifecycle/launcher.py:458-489`), surveyed
for whether it computes-then-writes or irreducibly interleaves. "Land" = short store write(s)
terminal to one item; "compute" = the long span (model call / embed / parse / scan).

| kind | route | per-item shape | split verdict |
|---|---|---|---|
| `vault_sync` | vault_sync.py:31 → core/ingest/sync.py:83,146 | raw.add → parse+embed → 5-store landing (see below) | splittable; landing = 5 ordered short writes |
| `chat_sync` | chat_sync.py:40 → ops/chat_sensor.py:289-341 | parse (model-free) → add_text + add_batch (:310,:329) | splittable, trivially (compute is cheap) |
| `code_sync` | code_sync.py:37 → code_corpus.py:280-301 | derive+embed (:272-277) → supersede+add (:298-300) | **splittable — already separate statements** |
| `code_backfill` | code_sync.py:53 → code_corpus.py:309-338 | parse+embed → store.add (:333); then diff capture | splittable; the hours-long lane that matters most |
| `chat_events` | cron.py:106 → core/chat_events.py:199-215 | pure `extract_events` → `replace_session` (:215) | splittable, trivially; capped 50/pass |
| `integrate` | cron.py:126 → core/integrator.py:97-116 | pure resolution (:118-146) → `replace_session` (:113) | splittable, trivially; capped 50/pass |
| `dream` | cron.py:50 → core/dreaming/dreamer.py:126-165 | model calls (long) → attest + derived.add (:143-162) | splittable per theme; writes terminal per iteration |
| `curate` | cron.py:58 → core/curator/curator.py:156-179 | all findings computed (:159), then a write-only loop | **already compute-then-write** |
| `ambassador` | interface.py:45 → core/interface.py:57-77 | model call → atomic response-file write + unlink | near-target; writes ARE the handoff, id-idempotent |
| `ambassador_task` | scheduler/interface.py:53-59 | pure compute; returns text, SUPERVISOR lands it (supervisor.py:94-95) | **already exactly the target shape** |
| `research` | cron.py:147 → scheduler/research.py:76-93 | airlock.emit (the diode) → collect → rank (pure) → returns text | near-pure; nothing lost on interruption |

`vault_sync`'s per-note landing, in order: raw.add (`sync.py:92`, idempotent archive, pre-compute)
· delete+add (`index.py:87-88`) · catalog.record (`sync.py:119`) · attestor.emit (`:122`) ·
version_store.record (`:135`). All short; the compute is the embed at `index.py:82-84`.

(`shadow` exists in `scheduler/cron.py:82` but is not registered in `build_components` — it is
not a daemon kind today.)

**Survey result: NO registered handler is irreducibly write-interleaved.** Every span longer than
a second is a model call, an embed call, or a pure scan; every store write is a short step
terminal to one item (note / file version / session / cluster / message). Two handlers are
*already* in the target shape, and one of them (`ambassador_task`) already uses the exact
mechanism this note proposes — the handler returns data and the supervisor lands it. The
compute/land split is not an invention; it is the system's own existing pattern, generalized.
(Fifth arrival of "returns data, never actions" — after non-negotiables #3/#4, the airlock, and
the append-only-substrate principle.)

Honest qualifications, so the survey cannot be quoted stronger than it is:

- `vault_sync`'s landing is a five-store ordered sequence per note, including an internal
  delete→add window (`core/ingest/index.py:87-88`, "atomically-ish"). The split does not make
  that window atomic — it moves it into a supervisor-owned landing step that is never
  interrupted at SIGTERM (signals act at landing boundaries). Recoverable today (re-derivable
  from raw), structural after the split.
- `code_sync` has the same shape one store down: supersede (flip `current=false`) then add
  (`code_corpus.py:298-300`); a kill between them leaves a path with no `current=true` version
  until the next idempotent pass. Same remedy, same structural closure.
- `code_sync`, `code_backfill` and `vault_sync` have **no iteration cap** (unlike
  chat_events/integrate/dream), which is why they are the hours-long lanes.

### 2.4 The position on oq-0035: **(c) both** — and the stated crux is an artifact

oq-0035's crux as written: *"whether an interrupted store write is acceptable to guarantee
availability. That trades data integrity against a shutdown guarantee."*

**Verified: for every registered handler, that trade does not exist at the span where
interruption matters.** The survey (§2.3) shows the hours-long spans are compute; the writes are
short and item-terminal. Interrupting between items interrupts a *computation* and loses nothing
but the in-flight item's re-derivable work. The only genuine partial-write windows (vault's
delete→add, code's supersede→add) are seconds wide, already self-healing under idempotent re-run,
and close structurally once landing is supervisor-owned. So the ruling the owner was asked for —
"is data loss acceptable?" — was conditioned on an architecture, not on physics. Change the
architecture and the question dissolves for the registered kinds.

The recommendation, in dependency order:

- **(b) is the real fix, and it is the compute/land split.** The handler computes one bounded
  batch and returns it; the supervisor lands it. Budgets become *enforceable* (the supervisor
  owns a clock between batches and around the whole job) rather than merely configured — which is
  what finding-0178 established is currently missing entirely: no deadline, no alarm, no
  watchdog; the only real bound in the system is `[ollama] request_timeout_s = 120`
  (`config/defaults.toml:16`) on a single socket read, and a pure-CPU wedge (the actual
  finding-0169 incident) has **no terminating condition at all**.
- **(a) is the fail-safe behind it, not the fix.** Bounded escalation — SIGTERM → wait N →
  SIGKILL — targeted **only at the worker** (§2.5), never at the supervisor (killing the
  supervisor mid-landing is how you *create* the partial-write the crux worried about). (a)
  alone is close to the status quo plus a timer: it bounds the damage of a wedge without ever
  making the system able to *see* one — modes (3) and (4) stay undetected forever, which fails
  "without realizing" by construction.

What each half would NOT catch (the falsifier duty, per mechanism, in §2.9): the split does not
detect a wedge, it makes one killable and observable; the escalation does not explain a wedge, it
bounds it. Both, together, or the mandate is not met.

### 2.5 The execution model: worker subprocess computes; supervisor lands

The capsule's Q1 (thread vs subprocess vs cooperative batch), decided with evidence:

- **Cooperative batching alone is insufficient.** It fixes SLOW/starvation (finding-0165's
  chunked-long-jobs direction) but a wedge *within* a batch still owns the thread — mode 4
  survives. It also collides with coalescing today: `queue.checkpoint()` re-queues the row
  (`scheduler/queue.py:396-403`), and a QUEUED row of an `_IDEMPOTENT_KINDS` member is a
  collapse target (`queue.py:260-271`) whose resumed pass is *not* the full re-derivation
  membership assumes — bp-105 Checkpoint 1 disqualified this channel on exactly that ground.
- **A thread is insufficient.** It restores loop liveness for IO-bound spans, but Python threads
  cannot be cancelled, and a pure-CPU wedge — precisely the finding-0169 incident, 96% CPU —
  holds the GIL and starves the supervisor loop anyway (V5 verifies the degree). The mode-4
  power-to-act never arrives.
- **A worker subprocess gives both halves of the seam.** The supervisor stays live (observation),
  can SIGTERM→SIGKILL the worker without dying itself (cancellation, crash isolation), and the
  landing step stays in the single-writer supervisor — **strengthened**, because the worker holds
  no store handles at all: it returns rows, never actions. The pattern already exists in-repo:
  `core/sandbox/runner.py:65-75` runs a subprocess under a wall-clock timeout and destroys it on
  expiry, and `[sandbox] max_concurrency = 1` shows the ceiling-respecting concurrency discipline
  (`config/defaults.toml:315-330`). That machinery is for *untrusted* code; the worker here is
  trusted core code — the isolation is borrowed for liveness, not for privilege reduction.

**Decision:** one worker subprocess per dispatched job; the handler's compute half runs there and
returns bounded batches (IPC); the supervisor lands each batch and owns all clocks:

1. **Batch budget** — a batch that exceeds its deadline ⇒ escalation (a). The batch is also the
   fairness unit: between batches the supervisor may claim other-lane work (closes
   finding-0165's starvation *and* bp-105's "no channel can emit" — the landing itself is now
   the progress signal, in-band, lane-agnostic: mode 2 detection generalizes past the embedding
   lane with zero per-lane probes, honoring the §1.2 anti-goal).
2. **Job budget** — per-kind wall-clock ceiling enforced by the supervisor (finding-0178's
   missing mechanism, now buildable because the seam exists).
3. **Drain bound** — SIGTERM to the daemon ⇒ finish landing the current batch, persist the
   worker's checkpoint, escalate the worker if it ignores its own SIGTERM for N seconds, exit.
   `down` becomes verifiably boundable (finding-0171 closes).

Interim step, independently valuable and cheap: `_serve` should call `run(max_ticks=K)` (or a
time-boxed drain) so the health/snapshot/housekeeping ticks run at job boundaries again even
before any handler is split (§2.2's sharpening; falsifier in §2.9).

### 2.6 The memory ceiling (non-negotiable #8) under the worker model

What actually changes and what does not, against `core/models/loader.py`:

- **Model weights do not move.** They live in the Ollama server process today and still would;
  the worker calls the same localhost API. The ceiling gate (`loader.py:57-69`) runs in the
  supervisor at dispatch (`supervisor.py:71`) *before* the worker spawns — the refusal point
  survives unchanged.
- **The books stay in-supervisor, and their blind spot stays.** `_resident` is an in-process
  belief (`loader.py:33`) that nothing reconciles against Ollama's actual residency
  (`OllamaClient.ps()` exists and is read only for the status embedder line,
  `launcher.py:1080-1098`). finding-0174's embedder is one unaccounted consumer; the general
  defect is that *no* reconciliation of belief-vs-`ps()` exists anywhere (§2.7). NEW NOTE 2 owns
  the accounting redesign; this note's obligation is only to not widen the gap.
- **What the split adds: two new consumers and one new hazard.** The worker's own Python RSS
  (+ the serialized batch in flight) is a new unaccounted term — small, but it must be *declared*
  in whatever accounting NEW NOTE 2 lands, not discovered later (the finding-0174 species).
  The hazard is concurrency: today "≤ 2 resident models" is enforced *implicitly* by
  one-job-at-a-time serialization. A supervisor that stays live while a worker computes could
  claim a second model-using job, and `ensure_tier` for job B would evict the model job A is
  mid-generation on. **Rule: at most one in-flight model-using job; while one is out, the
  supervisor may dispatch only jobs sharing its `load_key` or doing landing/housekeeping.**
  That keeps ceiling semantics identical with zero new accounting.
- **The shared boundary with NEW NOTE 2, flagged not resolved:** "is the embedder a third
  process or an unaccounted ghost" is the same question from two directions. If NEW NOTE 2 makes
  the embedder a palace-owned process, the worker's embed calls route there and the worker gets
  *thinner*; nothing in this note's design forecloses that, and neither note should resolve the
  embedder's residency without the other.

### 2.7 I5 — "consistency and accuracy", mechanically

The owner named consistency as the OS's job. The concrete pairs this layer owns, and whether
anything detects divergence today:

| consistency pair | detector today | gap |
|---|---|---|
| run ledger vs process reality | `run_state` + `_supervisor_alive` (pull, at `status`/`start`) | continuous detection has no home — the blocked loop (§2.2); closes with §2.5 |
| queue RUNNING rows vs a live claimant | `sweep_orphans` at start (queue.py:350-394); ORPHANED render (launcher.py:1146-1157) | nothing while live: a wedged-but-alive job is visible only via the embedding store-clock |
| queue QUEUED uniqueness vs coalescing | conventional (enqueue-time); the partial UNIQUE index is parked until the restart clears 1,766 dups (queue.py:121-126) | the consistency claim exists; its structural enforcement is a queued hand-off |
| store vs code ledger (versions embedded) | `_code_backfill_incomplete` at start only (launcher.py:343-362) | not in `status` (no cheap reader — the 3.5 s scan, snapshot.py:355-376; finding-0178 hand-off) |
| vector store vs vault catalog | `rescan` re-derives and repairs silently every pass | self-healing but not *reporting* — divergence is fixed without ever being said [INFERENCE: acceptable, because raw is the substrate and the repair is the contract] |
| loader `_resident` books vs Ollama actual | **none** | belief-only accounting; `ps()` is never reconciled against the books — the finding-0174 class, generalized (input to NEW NOTE 2) |
| second-supervisor exclusion | `start` gate (launcher.py:606-611) | `scripts/watch.py:39-47` still builds a second Supervisor on the shared queue — the un-lifted half of finding-0186 |

The class, named: **every ops ledger is written by the actor whose failure it must record.**
Reconciliation exists at boundaries (start, pull-time status) and nowhere continuously — and the
reason it is not continuous is the same one seam (§2.2). The bp-105 orphan was one instance;
this table is the class. The worker model gives continuous reconciliation a home; NEW NOTE 1's
instruments then have something to render.

### 2.8 Detection lag gets four numbers, not one (handed to NEW NOTE 1)

Per the capsule's Q4, the taxonomy prices lag per mode: GONE = time-to-next-pull (unbounded
today; becomes one tick under §2.5); STUCK = one landing-batch interval (in-band, lane-agnostic);
SLOW = the expectation window (needs Q3's denominator — parked, see Parked decisions); HUNG = the
batch budget + escalation deadline (bounded for the first time). NEW NOTE 1 tracks these as four
metrics; this note defines them.

### 2.9 Falsifiers (the owner ratifies falsifiers, not proofs)

Per mechanism: the observable that would show it WRONG, and what it would NOT catch.

- **Compute/land split** — *wrong if:* the landing step is not short — if p95 landing time per
  batch approaches the tick budget, the supervisor is blocked again in its own landing loop and
  the seam has just moved (V1 measures); or if serializing a batch across the process boundary
  costs a nontrivial fraction of computing it (V2). *Does not catch:* a wedged **landing** (a
  hung store write in the supervisor itself) — that residual is exactly why (a) alone must never
  target the supervisor, and why the store-clock stays as corroboration.
- **Worker subprocess** — *wrong if:* supervisor+worker RSS breaches headroom under the watchdog
  (`scheduler/router.py:92-104` flags it — for once the instrument exists first); or if killing
  the worker does not actually stop the work (V3: does Ollama abort a generation when the client
  socket dies? If not, SIGKILL of the worker leaves the GPU/CPU burn running — the incident's 96%
  CPU, orphaned one level down). *Does not catch:* a supervisor-process wedge; GONE-mode of the
  supervisor itself remains launchd's + `status`'s job.
- **Bounded escalation (a)** — *wrong if:* the deadline fires on healthy long batches (the
  cry-wolf disqualifier, bp-102 §10 — deadlines must be per-batch, not per-job-elapsed, or a
  healthy 14-hour backfill dies at hour N on schedule); *does not catch:* anything — it detects
  nothing, explains nothing; it only bounds. An escalation that fires must always mint a finding,
  or the kill is the silent state-change the mandate forbids.
- **Single-model-in-flight rule (§2.6)** — *wrong if:* it serializes the system back to
  one-job-at-a-time in practice because every lane is model-using (then the fairness win of the
  batch unit is theatre for model lanes; measure the interleave actually achieved).
- **`run(max_ticks=K)` interim** — *wrong if:* no-op drain throughput collapses (1,766 queued
  no-ops must not take 30 minutes because each tick eats a `tick_seconds` sleep; the sleep must
  apply only when nothing was runnable).

### V-series (not settled by reading; each blocks the item that cites it)

- **V1** — measure the landing cost: `store.add` rows/sec for a representative batch (100–500
  chunks with 2560-dim vectors) on the real store. Settles "landing is short".
- **V2** — measure IPC serialization of one batch (≈10 KB/vector float32; ~1–5 MB/batch
  expected) worker→supervisor. Settles the split's overhead claim.
- **V3** — does the Ollama server abort embed/generation when the requesting client dies?
  Kill a client mid-call and watch server CPU. Decides whether worker-SIGKILL actually stops
  the burn or must be paired with an Ollama-side cancel/unload.
- **V4** — `core/sealing.py`'s seal is a per-process monkeypatch; verify the worker re-applies
  it at spawn (spawn, not fork, on macOS — nothing inherits). The sealed-core invariant (#1)
  must be *asserted* in the worker, not assumed from the parent.
- **V5** — quantify GIL starvation: run a finding-0169-shaped pure-CPU scan on a thread and
  measure the supervisor loop's achieved tick rate. Grounds the thread-model rejection with a
  number (currently reasoned, not measured).
- **V6** — the checkpoint/coalescing collision: confirm a checkpointed `_IDEMPOTENT_KINDS` row
  can swallow a follow-up request (bp-105 CP1's reading), and pin the fix (exclude rows with a
  non-NULL `checkpoint` from the coalesce key) before any batch-yield lands.
- **V7** — enumerate `scripts/watch.py`'s users; either wire it through the single-instance gate
  or retire it (the open half of finding-0186).

## 3. Consequences

**Plans this licenses (after ratification, via `/graduate`):** the decomposition must respect
that this change spans `scheduler/` (supervisor + queue additive columns), `core/ingest/` and
`core/` handler modules (the compute/land refactor per lane), and `ops/lifecycle/` (escalation,
drain bound, probe rendering). **That is finding-0191 territory: the write_scope partition is a
graduation-time decision, not a build-time one.** The audit's own remedy applies — per-lane
builder plans with disjoint scopes, plus one **integrator plan** whose write_scope is exactly the
seam files (the supervisor dispatch path + the worker protocol), carrying a named falsifier per
hand-off. The last commit before the wave's seal must never be the first commit of a behaviour.

**Sequencing:** the interim `run(max_ticks=K)` fix and the escalation fail-safe (a) are small and
independent; the split (b) proceeds lane-by-lane, longest-lane first (`code_backfill`,
`code_sync`, `vault_sync` — the uncapped three, §2.3), with `ambassador_task` as the existing
in-repo reference shape. bp-105's store-clock stays in place throughout as the independent
corroboration channel (it needs no cooperation from any of this to keep working).

**Findings this bears on:** closes the design half of finding-0171/0178 (via the oq-0035 ruling);
gives finding-0165 its structural home (the batch unit); generalizes finding-0188's mode-2
detection past the embedding lane; adds the loader-reconciliation gap (§2.7) as an input NEW
NOTE 2 must account for.

## 4. Wiring & enablement

**How it wires:** a `[scheduler]` config section (schema'd in the config loader — unknown
sections are dropped silently, bp-102/finding-0174's lesson, so the schema change is part of the
deliverable, not a follow-up): `worker_mode = "inproc" | "subprocess"` (default `inproc` at
first landing), `batch_deadline_s`, `job_budget_s` per-kind overrides, `escalation_grace_s`.
`palace status` renders the worker pid, current batch age vs deadline, and last landing time —
replacing the "(no enforced job budget)" line (`launcher.py:1158-1160`) with the budget it now
has. `down`/`stop` gain the bounded-drain report (what was signalled, what was verified, within
what bound). The interim `run(max_ticks=K)` ships wired, not flagged.

**What it takes to flip it on:** (a) a build lands the worker protocol + one lane
(`code_backfill`) split, behind `worker_mode = "subprocess"`; (b) the owner flips
`worker_mode` in `config/local.toml` after a parallel-run deskcheck (same backfill, both modes,
diffed reports); (c) remaining lanes migrate lane-by-lane, each with its own deskcheck
demonstrable. The flip is owner-visible and reversible per lane — no lane is force-migrated.

## Parked decisions

- **Q3 — the SLOW denominator** (what expectation makes mode 3 computable): per-kind historical
  p50 from the queue's own history vs declared per handler. Default: no SLOW detector until the
  batch telemetry exists to derive p50 from (a declared budget without history is a magic number
  — the rot §1.2 forbids). Re-entry: after the first split lane has accumulated a week of batch
  timings.
- **Worker pooling / reuse** (one process per job vs a warm worker): default one-per-job
  (simplest kill semantics, the sandbox's "overran ⇒ discarded, never reused" discipline,
  `core/sandbox/pool.py:5`). Re-entry: if V2/spawn cost is measurable against short jobs.
- **Escalation deadline values** (N seconds SIGTERM→SIGKILL): owner call at ratification;
  default proposal 30 s grace after a missed batch deadline, logged + finding-minted on every
  firing. Re-entry: the oq-0035 ruling itself.
- **Whether `ambassador`'s reactive path also moves out-of-process**: default NO — it is the
  conversational front door, latency-sensitive, holds no store handles, and its writes are the
  handoff files themselves. Re-entry: only if a wedged Ambassador model call is ever observed
  blocking the loop past its budget.

## Cross-references

Code (all at `f4a51fd`): `scheduler/supervisor.py:63-107` (tick/run, the seam) ·
`scheduler/queue.py:71-72,232-279,292-324,350-394,396-403` (idempotent kinds, coalescing, claim,
sweep, checkpoint) · `ops/lifecycle/launcher.py:343-362,458-520,595-660,662-695,820-853,939-983,
1100-1205` (catch-up probe, handler map, start gate, serve loop, stop/down, status render) ·
`ops/lifecycle/snapshot.py:91-117,157-265,381-412` (run_state, QueueStats + predicates,
store-clock) · `ops/lifecycle/runs.py:100-144` (run ledger) · `core/ingest/sync.py:83-180` ·
`core/ingest/index.py:68-89` · `core/ingest/code_corpus.py:267-338` · `ops/chat_sensor.py:289-353`
· `core/chat_events.py:193-215` · `core/integrator.py:97-146` · `core/dreaming/dreamer.py:126-165`
· `core/curator/curator.py:156-179` · `scheduler/interface.py:45-59` · `core/interface.py:57-77` ·
`scheduler/research.py:76-93` · `core/models/loader.py:28-101` · `scheduler/router.py:92-104` ·
`core/sandbox/runner.py:65-86` · `config/defaults.toml:10-16,93-94,274,315-330` ·
`scripts/watch.py:30-50`.

Artifacts: the commissioning capsule (`docs/brainstorms/supervision-and-liveness.md`) ·
`docs/brainstorms/design-pass-routing.md:30-160` (amended by §1.1, not edited) · oq-0035
(`docs/inbox/owner-questions.md:1013-1043`) · findings 0165, 0169, 0171, 0172, 0173, 0174, 0178,
0186, 0187, 0188, 0191, 0198 · `docs/build-plans/bp-105/journal.md` (Checkpoints 1 and 3 carry
the channel eliminations this note builds on) · `docs/audits/ops-wave-2026-07-25.md` ·
`docs/tracks/ops.md` (OPS-4 is this note's DoD row).
