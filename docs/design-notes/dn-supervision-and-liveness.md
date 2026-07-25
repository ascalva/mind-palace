---
type: design-note
id: dn-supervision-and-liveness
track: ops
status: ratified
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/brainstorms/supervision-and-liveness.md       # the commissioning capsule (session-47)
  - docs/brainstorms/design-pass-routing.md            # the routing map this note amends (see §1.1)
  - docs/brainstorms/local-model-runtime.md            # NEW NOTE 2 — shared boundary (§2.7)
  - docs/audits/ops-wave-2026-07-25.md                 # the audit that produced the warrants
  - docs/findings/finding-0171.md                      # unbounded drain (oq-0035's origin)
  - docs/findings/finding-0178.md                      # there is no job timeout
  - docs/findings/finding-0188.md                      # the wedge detector's ceiling
  - docs/findings/finding-0165.md                      # background starvation under a long job
  - docs/findings/finding-0174.md                      # the ceiling ignores the embedder
  - docs/findings/finding-0191.md                      # write_scope is not a partition
  - docs/build-plans/bp-105/journal.md                 # why the loop cannot emit mid-wedge
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
we have to get this right"* — the acceptance bar: *"we do not want something that is going to
allow us to shoot ourselves in the foot without realizing; the system's OS needs to maintain the
consistency and accuracy of the system with precision and appropriate guard rails"* — and the
escalation (same day): *"the ultimate goal for the system OS/scheduler is to make this class of
error impossible, unrepresentable if possible."*

Read the escalation as the design test throughout: **detection is the fallback, not the goal.**
For each failure mode the first question is whether the bad state can be denied a representation
at all; a detector is what remains when it cannot. This is non-negotiable #1's discipline applied
one layer down — "enforce structurally, not by convention" — and the OS layer should be designed
the way the sealed core was.

### The enforcement ladder (every mechanism in this note is ranked on it, explicitly)

| tier | name | meaning |
|---|---|---|
| 1 | unrepresentable | no value inhabits the bad state |
| 2 | capability | the component is never given the means |
| 3 | protocol | an external authority enforces it — held-or-not |
| 4 | ratchet | a test/scan proves the property in CI |
| 5 | runtime check | the bad state is constructible; a check looks for it |

Tier 3's authority is the kernel, the clock or the filesystem — the point is that it is
*held-or-not*, never check-then-act. Tier 5 is the **weakest** and the standing proof is
finding-0187: deleting bp-105's sweep call left 85/85 green.

Overclaiming a tier is itself the foot-gun — "unrepresentable" delivered as a tier-5 check is
"shoot ourselves in the foot without realizing," one level up. Python bounds what tier 1 can
mean here (mypy is static and two-tier; SQLite cannot retrofit CHECK constraints), so most of
this note lands honestly at tiers 2–3 — each claim below says which, and what would falsify it.

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
detection lag as a *tracked metric* (its four-mode refinement is defined here, §2.9, and handed
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
  the shared boundary (§2.7) and constrains its own design to not foreclose it.
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
| 1 GONE | process dead, ledger says RUNNING | pid liveness + identity | ✅ tier 5, pull-only |
| 2 STUCK-IN-LANE | alive, landing nothing in lane | store-clock channel | ⚠️ tier 5, one lane |
| 3 SLOW | progressing, too slowly to matter | a rate AND an expectation | ❌ none |
| 4 HUNG | thread wedged, stopped cooperating | outside view + power to act | ❌ none, needs §2.2 |

Citations and qualifications, by mode. **1** — `_supervisor_alive` (`launcher.py:166-212`) and
`run_state` (`snapshot.py:91`). **2** — the store-clock (`snapshot.py:199-223`); the "one lane"
caveat is bp-105's own stated ceiling, embedding only. **3** — nothing exists because no
denominator does (§2.9, Q3). **4** — impossible while the handler owns the loop (§2.2).

The trap stands verified: a cooperative heartbeat detects (3) and not (4), because a wedge IS a
handler that stopped cooperating. bp-105's own build record proves the stronger form: **nothing
on the supervisor's thread can emit while the wedge is happening** — the health tick, snapshot
tick and housekeeping tick all live on the loop the handler blocks
(`launcher.py:675-695`), and even `Supervisor._record` runs only *after* `handler(job)` returns
(`supervisor.py:96, 109-115`). The one channel that worked (the store's filesystem mtime) worked
precisely because it is written from *inside* the blocked call (bp-105 journal, Checkpoint 3).

Under the escalated mandate the taxonomy is re-read with the unrepresentability question FIRST,
detector second. The answers this note reaches: mode 1's bad state (dead-but-reported-RUNNING)
loses its representation under the dead-man inversion (§2.6 — liveness stops being a stored bit
anyone can fail to update); mode 2's detector generalizes into an in-band signal (the landing
cadence, §2.5) whose *absence* is the alarm — no per-lane probe exists to rot; mode 4 splits in
two: a hung **worker** becomes kernel-boundable (§2.5) and a hung **supervisor** becomes loud by
lease decay (§2.6); mode 3 (SLOW) is the one mode that irreducibly needs a detector plus an
expectation, and it stays parked until a denominator exists (Parked decisions).

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

| kind | per-item shape | split verdict |
|---|---|---|
| `vault_sync` | raw.add → parse+embed → 5-store landing | splittable; landing = 5 short writes |
| `chat_sync` | parse (model-free) → add_text + add_batch | splittable, trivially |
| `code_sync` | derive+embed → supersede+add | **already separate statements** |
| `code_backfill` | parse+embed → store.add; then diff capture | splittable; the lane that matters |
| `chat_events` | pure extract → `replace_session` | splittable; capped 50/pass |
| `integrate` | pure resolution → `replace_session` | splittable; capped 50/pass |
| `dream` | model calls (long) → attest + derived.add | splittable per theme |
| `curate` | all findings computed, then a write loop | **already compute-then-write** |
| `ambassador` | model call → atomic file write + unlink | near-target; writes ARE the handoff |
| `ambassador_task` | pure compute; returns text | **already exactly the target shape** |
| `research` | emit → collect → rank (pure); returns text | near-pure; nothing lost on interrupt |

Routes, in the same order: `vault_sync.py:31` → `core/ingest/sync.py:83,146` · `chat_sync.py:40` →
`ops/chat_sensor.py:289-341` (writes at `:310,:329`) · `code_sync.py:37` →
`code_corpus.py:280-301` (embed `:272-277`, land `:298-300`) · `code_sync.py:53` →
`code_corpus.py:309-338` (land `:333`) · `cron.py:106` → `core/chat_events.py:199-215` (`:215`) ·
`cron.py:126` → `core/integrator.py:97-116` (resolve `:118-146`, land `:113`) · `cron.py:50` →
`core/dreaming/dreamer.py:126-165` (land `:143-162`) · `cron.py:58` →
`core/curator/curator.py:156-179` (compute `:159`) · `interface.py:45` →
`core/interface.py:57-77` · `scheduler/interface.py:53-59` — **and here the supervisor already
lands the result, `supervisor.py:94-95`** · `cron.py:147` → `scheduler/research.py:76-93`.

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

**And the survey licenses the stronger reading (reframing A, verified): the split is a
CAPABILITY restriction, not a discipline.** Because no handler irreducibly *needs* a store
writer, the compute half can be constructed without one — the worker is handed sources, blobs,
and an embedder client, never a `VectorStore`/`VaultCatalog`/ledger handle. "Handler interleaves
writes" then stops being a rule handlers follow and becomes a thing the compute side *cannot
express* — **tier 2**, and honestly not tier 1: the stores are files on a shared disk, and a
worker that independently called `open_vector_store` could still write. Two backings close that:
a tier-4 ratchet (the worker entrypoint's import graph contains no store-opening constructor —
the `check_imports.py` species, applied to a new boundary) now, and tier 3 under the
dn-plane-principals split (the worker principal simply lacks filesystem write permission to
`data/`) later. The in-process interim, before any worker exists, is tier 5 and must be reported
as such.

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

### 2.4 The position on oq-0035: **(c) both** — and the stated crux dissolves under the split

oq-0035's crux as written: *"whether an interrupted store write is acceptable to guarantee
availability. That trades data integrity against a shutdown guarantee."*

**Verified — and under reframing A the crux is not mitigated but NONEXISTENT for the registered
kinds.** The survey (§2.3) shows the hours-long spans are compute; the writes are short and
item-terminal. With the compute side constructed store-less (tier 2), the interruptible region
contains no writes *by construction*: interrupting the worker interrupts a computation that holds
nothing to corrupt. "Is an interrupted store write acceptable?" stops being a trade to rule on
because the actor being interrupted cannot write. The only genuine partial-write windows (vault's
delete→add, code's supersede→add) are seconds wide, already self-healing under idempotent re-run,
and move into the supervisor's landing step — where the interrupting party is no longer this
design's escalation (which targets only the worker) but a power loss or an operator `kill -9` of
the supervisor itself, the same residual every store write in the system already carries. So the
ruling the owner was asked for — "is data loss acceptable?" — was conditioned on an architecture,
not on physics. Change the architecture and the question dissolves for the registered kinds.

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

What each half would NOT catch (the falsifier duty, per mechanism, in §2.10): the split does not
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
returns bounded batches (IPC); the supervisor lands each batch and owns all clocks. Tier
accounting for this mechanism, stated plainly: the *no-writes-in-the-worker* property is tier 2
(capability, §2.3) with a tier-4 import-ratchet backing; the *cancellability* property is tier 3
— the process boundary makes "stop" a kernel operation (SIGKILL is enforced by the OS, an
authority outside the wedge), where an in-process cancel flag would be tier-5 cooperation with
the very code that stopped cooperating. The escalation policy itself (when to fire) is runtime
logic and cannot be higher than tier 5 — what the ladder buys is that when it fires, it *works*:

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
before any handler is split (§2.2's sharpening; falsifier in §2.10). Tier 5, reported as such.

### 2.6 The dead-man inversion (reframing B, verified with one correction) and the five targets

Today the system **asserts** health: `stopped_at IS NULL` means running (`runs.py:72-74`),
`state = 'running'` means working (`queue.py:47`), and every incident in this track's history is
a stored assertion outliving the actor that made it. Reframing B inverts the polarity: nothing
asserts health; health **decays** unless renewed, and every reader treats staleness as DOWN by
default. Then "a blocked supervisor still reporting healthy" loses its representation — there is
no "I am healthy" bit left to lie with. Verified as the right move, with the caveat named
honestly: **the inversion does not escape the seam (§2.2).** A lease renewer must live off the
blocked path, which only the worker split provides — so B *depends on* §2.5; it does not replace
it. What B changes is what the seam buys: not "the supervisor can now observe" but "the
supervisor's own absence becomes meaningful." A wedged landing step, the split's one residual
blocking hazard, now reads DOWN/AILING instead of silent-green — the loud wrong answer the
mandate prefers.

Three concrete mechanisms, then the five targets ranked:

- **The supervisor lock (two-supervisors, upgraded tier 5 → tier 3).** An OS-exclusive `flock`
  on a lockfile beside the queue, acquired before `sweep_orphans` and held for the supervisor's
  lifetime. Held-or-not is a kernel fact: it dies with the process (no stale-lock state exists),
  and acquisition is atomic (no check-then-act race — bp-105's gate at `launcher.py:606-611`
  probes then proceeds, a TOCTOU the lock does not have). It guards the **supervisor role**
  (sweep + claim), NOT queue writes — CLI enqueues (`palace code-seed`, launcher.py:882-907)
  legitimately insert concurrently and stay lock-free under WAL. This also closes the
  `scripts/watch.py:39-47` second-supervisor route structurally (the open half of
  finding-0186): a second claimant fails to acquire, whatever entrypoint built it. bp-105's
  identity gate stays as the *diagnostic* layer (it can say WHY, the lock can only say no).
- **The supervisor lease (health polarity).** The serve loop renews a small lease (a row in
  `runs.sqlite` or the lockfile's mtime) every tick; `status`, `start`, and any future
  continuous probe compute liveness as `lease_age < ttl`. Renewal has exactly one site — the
  loop body, never a handler, never the landing step's interior — so the signal means "the
  supervisory loop cycled recently" and nothing weaker. Tier 3 (the clock and filesystem are
  the authority; no reader trusts a stored bit). Single-host, so clock skew reduces to
  wall-vs-monotonic care, not distributed-systems lease semantics.
- **Leased RUNNING rows (jobs).** `claim()` — already the queue's only RUNNING-constructor
  (`queue.py:292-324`) — stamps a deadline on every row it takes; readers treat an
  expired-deadline row as orphaned *by definition*, whatever its `state` byte says. The orphan
  sweep stops being a call someone must remember to make (finding-0187's exact failure: deleting
  the call left 85/85 green) and becomes a derived view plus a lazy reap. SQLite cannot make an
  undeadlined RUNNING row uninhabitable (no retrofitted CHECK, additive-only migration), so this
  is tier 2 (single constructor) + tier 4 (a ratchet asserting no RUNNING row lacks a deadline),
  NOT tier 1 — claimed as such.

**The five unrepresentability targets, ranked** (tier reached · cost · what shows it wrong):

| target | tier | cost |
|---|---|---|
| RUNNING job, no deadline | 2 + 4 | additive column; reader change |
| handler writes the store | 2 + 4 (3 under principals) | the §2.5 split |
| active run row, process gone | 3 for reporting | one renewal site + readers |
| two supervisors, one queue | 3 (kernel flock), was 5 | lockfile + acquire-or-exit |
| stopped supervising, reads healthy | 3 | needs §2.5 (renewer off loop) |

**The tier, justified, and the falsifier that would show each wrong** — the owner ratifies
falsifiers, so this half is prose, not a cell:

- **RUNNING job, no deadline** — tier 2 because `claim()` becomes the sole constructor of a RUNNING
  row, plus tier 4 (a ratchet asserting none lacks a deadline). SQLite bars tier 1: no retrofitted
  CHECK on an additive-only migration. *Wrong if:* a RUNNING row is minted outside `claim()`, or a
  reader still trusts `state` alone.
- **handler writes the store** — tier 2 by capability (the worker is handed no store), tier 4 by an
  import ratchet; tier 3 if separate principals land. *Wrong if:* the worker imports a store
  constructor, or landing p95 approaches the tick budget.
- **active run row, process gone** — tier 3: liveness is never stored, it decays. *Wrong if:* a
  second renewal site appears, or a reader keys on `stopped_at IS NULL` alone.
- **two supervisors, one queue** — tier 3 via kernel `flock`; bp-105's gate drops to tier 5
  diagnostic. *Wrong if:* a claimant sits outside the lock (`watch.py` — V7), or flock's semantics
  fail verification (V8).
- **stopped supervising, reads healthy** — tier 3: health is computed from lease age, never
  asserted. *Wrong if:* renewal happens from inside compute/landing, or the ttl cries wolf
  (bp-102 §10's disqualifier).

The honest summary the ladder forces: **nothing here reaches tier 1.** Python and SQLite bound
the reachable tiers at 2–3 for every target; what changes is that today's tier-5 checks (probe
the pid, remember to sweep, trust the row) become kernel facts, decaying signals, and absent
capabilities. bp-105's runtime checks are kept, demoted to diagnostics — the layer that explains,
not the layer that guarantees.

### 2.7 The memory ceiling (non-negotiable #8) under the worker model

What actually changes and what does not, against `core/models/loader.py`:

- **Model weights do not move.** They live in the Ollama server process today and still would;
  the worker calls the same localhost API. The ceiling gate (`loader.py:57-69`) runs in the
  supervisor at dispatch (`supervisor.py:71`) *before* the worker spawns — the refusal point
  survives unchanged.
- **The books stay in-supervisor, and their blind spot stays.** `_resident` is an in-process
  belief (`loader.py:33`) that nothing reconciles against Ollama's actual residency
  (`OllamaClient.ps()` exists and is read only for the status embedder line,
  `launcher.py:1080-1098`). finding-0174's embedder is one unaccounted consumer; the general
  defect is that *no* reconciliation of belief-vs-`ps()` exists anywhere (§2.8). NEW NOTE 2 owns
  the accounting redesign; this note's obligation is only to not widen the gap.
- **What the split adds: two new consumers and one new hazard.** The worker's own Python RSS
  (+ the serialized batch in flight) is a new unaccounted term — small, but it must be *declared*
  in whatever accounting NEW NOTE 2 lands, not discovered later (the finding-0174 species).
  The hazard is concurrency: today "≤ 2 resident models" is enforced *implicitly* by
  one-job-at-a-time serialization. A supervisor that stays live while a worker computes could
  claim a second model-using job, and `ensure_tier` for job B would evict the model job A is
  mid-generation on. **Rule: at most one in-flight model-using job; while one is out, the
  supervisor may dispatch only jobs sharing its `load_key` or doing landing/housekeeping.**
  That keeps ceiling semantics identical with zero new accounting. Tier accounting: a dispatch
  guard at the one claim site — tier 5 with a tier-4 test, stated as such; the ceiling *refusal*
  itself stays where it is (`_check_ceiling` raising before any load, tier 5 today, unchanged
  by this note — its upgrade belongs to NEW NOTE 2's accounting redesign).
- **The shared boundary with NEW NOTE 2, flagged not resolved:** "is the embedder a third
  process or an unaccounted ghost" is the same question from two directions. If NEW NOTE 2 makes
  the embedder a palace-owned process, the worker's embed calls route there and the worker gets
  *thinner*; nothing in this note's design forecloses that, and neither note should resolve the
  embedder's residency without the other.

### 2.8 I5 — "consistency and accuracy", mechanically

The owner named consistency as the OS's job. The concrete pairs this layer owns, and whether
anything detects divergence today:

| consistency pair | detector today | gap |
|---|---|---|
| run ledger vs process reality | `run_state`, `_supervisor_alive` | pull-only; no continuous home |
| queue RUNNING vs a live claimant | `sweep_orphans` at start | nothing while live |
| queue QUEUED vs coalescing | conventional, enqueue-time | structural version parked |
| store vs code ledger (versions) | start-time probe only | absent from `status` |
| vector store vs vault catalog | `rescan` repairs each pass | self-healing, never reports |
| loader `_resident` vs Ollama | **none** | belief-only accounting |
| second-supervisor exclusion | `start` gate | a second claimant route remains |

Per row: **run ledger** — pull-only at `status`/`start`; continuous detection has no home while the
loop is blocked (§2.2), and closes with §2.5. **queue RUNNING** — `queue.py:350-394` plus the
ORPHANED render; a wedged-but-alive job surfaces only via the store-clock. **QUEUED uniqueness** —
the partial UNIQUE index is parked at `queue.py:121-126`; the claim exists, the enforcement is a
queued hand-off. **store vs code ledger** — `_code_backfill_incomplete` (`launcher.py:343-362`)
runs at start only; no cheap reader exists (the 3.5 s scan, finding-0178). **vector store vs
catalog** — [INFERENCE: acceptable; raw is the substrate and repair is the contract]. **loader
`_resident`** — `ps()` is never reconciled; finding-0174 generalized, and now **finding-0199**,
which traces a ceiling breach on the crash-restart path. Input to NEW NOTE 2.
**second-supervisor** — the gate is `launcher.py:606-611`, but `scripts/watch.py:39-47` still
builds a second `Supervisor`: finding-0186's un-lifted half.

The class, named: **every ops ledger is written by the actor whose failure it must record.**
Reconciliation exists at boundaries (start, pull-time status) and nowhere continuously — and the
reason it is not continuous is the same one seam (§2.2). The bp-105 orphan was one instance;
this table is the class. The escalated mandate's answer to the class is §2.6: stop storing the
assertions (liveness becomes lease-derived; RUNNING becomes deadline-bounded by its only
constructor) so most of the table's left column stops being *checkable state* and becomes
*derived fact*. What remains genuinely stored-and-reconciled — the loader books vs `ps()`, the
store-vs-ledger coverage — gets its continuous home from the worker model, and NEW NOTE 1's
instruments then have something to render.

### 2.9 Detection lag gets four numbers, not one (handed to NEW NOTE 1)

Per the capsule's Q4, the taxonomy prices lag per mode: GONE = the lease ttl under §2.6 (today:
time-to-next-pull, unbounded); STUCK = one landing-batch interval (in-band, lane-agnostic);
SLOW = the expectation window (needs Q3's denominator — parked, see Parked decisions); HUNG = the
batch budget + escalation deadline (bounded for the first time). NEW NOTE 1 tracks these as four
metrics; this note defines them.

### 2.10 Falsifiers (the owner ratifies falsifiers, not proofs)

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
- **Single-model-in-flight rule (§2.7)** — *wrong if:* it serializes the system back to
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
- **V7** — enumerate `scripts/watch.py`'s users; either bring it under the supervisor lock or
  retire it (the open half of finding-0186 — under §2.6 the lock, not the gate, is the closure).
- **V8** — verify `flock` semantics where they will actually run: APFS, under launchd, across
  `uv run` process trees (the lock must be held by the supervisor python process, not a wrapper
  that exits). Advisory locking is only as good as every claimant acquiring it — V7 enumerates
  the claimants; V8 proves the kernel behavior.
- **V9** — measure lease-renewal cost and pick the clock (file mtime vs a `runs.sqlite` row;
  wall vs monotonic). Settles the ttl floor: the ttl must comfortably exceed the loop's worst
  honest tick (including a p99 landing step, V1) or the dead-man cries wolf — the §2.6 falsifier.

## 3. Consequences

**Plans this licenses (after ratification, via `/graduate`):** the decomposition must respect
that this change spans `scheduler/` (supervisor + queue additive columns), `core/ingest/` and
`core/` handler modules (the compute/land refactor per lane), and `ops/lifecycle/` (escalation,
drain bound, probe rendering). **That is finding-0191 territory: the write_scope partition is a
graduation-time decision, not a build-time one.** The audit's own remedy applies — per-lane
builder plans with disjoint scopes, plus one **integrator plan** whose write_scope is exactly the
seam files (the supervisor dispatch path + the worker protocol), carrying a named falsifier per
hand-off. The last commit before the wave's seal must never be the first commit of a behaviour.

**Sequencing:** three small independent pieces first — the supervisor lock (tier 3, upgrades the
bp-105 gate), the interim `run(max_ticks=K)` fix, and leased RUNNING rows (additive column +
derived readers) — none waits on the worker protocol. Then the split (b) lane-by-lane,
longest-lane first (`code_backfill`, `code_sync`, `vault_sync` — the uncapped three, §2.3), with
`ambassador_task` as the existing in-repo reference shape; the supervisor lease and escalation
fail-safe (a) land with the first split lane (the lease's renewer needs the unblocked loop,
§2.6). bp-105's store-clock and identity gate stay in place throughout as the diagnostic layer
(they need no cooperation from any of this to keep working).

**Findings this bears on:** closes the design half of finding-0171/0178 (via the oq-0035 ruling);
gives finding-0165 its structural home (the batch unit); generalizes finding-0188's mode-2
detection past the embedding lane; adds the loader-reconciliation gap (§2.8) as an input NEW
NOTE 2 must account for.

## 4. Wiring & enablement

**How it wires:** a `[scheduler]` config section (schema'd in the config loader — unknown
sections are dropped silently, bp-102/finding-0174's lesson, so the schema change is part of the
deliverable, not a follow-up): `worker_mode = "inproc" | "subprocess"` (default `inproc` at
first landing), `batch_deadline_s`, `job_budget_s` per-kind overrides, `escalation_grace_s`,
`lease_ttl_s`. The supervisor lock (§2.6) ships **unconditional, not flagged** — a mutual-
exclusion guarantee behind a flag is a contradiction; it wires into `start` before
`sweep_orphans` and into whatever `scripts/watch.py` becomes (V7). The lease renewal wires into
the serve loop's tick; `status` computes liveness from lease age (falling back to the bp-105
identity probe when no lease exists yet — old ledgers must not read as DOWN forever) and renders
the worker pid, current batch age vs deadline, and last landing time — replacing the "(no
enforced job budget)" line (`launcher.py:1158-1160`) with the budget it now has. `down`/`stop`
gain the bounded-drain report (what was signalled, what was verified, within what bound). The
interim `run(max_ticks=K)` ships wired, not flagged.

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
- **Lease ttl** (`lease_ttl_s`): blocked on V9's measured tick ceiling; default proposal
  3× the worst honest tick. Too tight is the cry-wolf falsifier (§2.6); too loose re-widens
  GONE-mode detection lag toward today's pull-only bound. Re-entry: V9.
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
