---
type: build-plan
id: bp-112
track: ops
status: proposed
design_ref:
  - docs/design-notes/dn-supervision-and-liveness.md
contract: builder
write_scope:
  - scheduler/worker.py
  - scheduler/supervisor.py
  - ops/lifecycle/launcher.py
  - tests/unit/test_job_budgets.py
  - tests/integration/test_supervisor.py
  - tests/integration/test_lifecycle_control.py
  - tests/unit/test_lifecycle_honest_shutdown.py
  - tests/integration/test_status_report.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 280k
  actual: null
depends_on: [bp-111]
parallelizable_with: []
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0171.md
  - docs/findings/finding-0178.md
  - docs/findings/finding-0169.md
  - docs/inbox/owner-questions.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0171.md
---

# Build Plan — the teeth: budgets that are enforced, and a kill that is bounded and loud

## 0. Mode & provenance

Graduated from `dn-supervision-and-liveness` §2.5 (the three budgets), §2.10 and §4's wiring
paragraph. **This is oq-0035's option (a)** — the fail-safe behind (b), ruled together as **(c)
both** by the owner on 2026-07-25 (`941785d`), verbatim: *"I like (c), feels like the most robust
approach."* It closes **OPS-4**, the track's shutdown-contract DoD row.

⚑ **The escalation targets the WORKER, never the supervisor.** §2.4 is explicit: killing the
supervisor mid-landing is how you *create* the partial write the original crux worried about. That
is not a preference in this plan; it is the property that makes the whole design safe.

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.

## 1. Objective

A job that stops making progress is bounded by a deadline the supervisor owns, killed by the
kernel, and never killed silently.

### 1.2 Non-goals (explicit — see §9)

Not a retry/backoff/dead-letter policy (`dn-supervision-and-liveness` §1.2). Not the lease
(bp-111). Not any lane. [INFERENCE] Not a SLOW detector — §2.9 and Parked decisions leave mode 3
without a denominator, so a "too slow" judgement is out of scope; only *no progress within the
deadline* is actionable here.

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/dn-supervision-and-liveness.md` §2.4 (the ruling package), §2.5 (the three
   budgets: batch, job, drain), §2.10 (the escalation falsifier), §4 — the content spec
2. `docs/findings/finding-0171.md` — the warrant: `down` cannot bound an unbounded drain
3. `docs/findings/finding-0178.md` — there is no job timeout at all; the only real bound in the
   system is `[ollama] request_timeout_s = 120` on a single socket read
4. `docs/findings/finding-0169.md` — the pure-CPU wedge with **no terminating condition**
5. `scheduler/worker.py` — bp-110's protocol and child-process handle
6. `scheduler/supervisor.py` — `tick` `:63-97`; the clocks live here
7. `ops/lifecycle/launcher.py` — `_serve` `:662-695`, `_shutdown` `:704+`, `stop`/`down`
   `:820-853,939-983`, the status render `:1146-1169` (the line this replaces)
8. `ops/ledger.py` — the existing ops ledger; **read before Item 4** (§3 Q5)
9. `core/sandbox/runner.py:65-80` — the timeout+destroy precedent

**Does core already have this?** No timeout, deadline, alarm or watchdog exists at the job level —
that is finding-0178's whole content, so there is nothing to reuse and nothing to duplicate. What
**must** be reused: the ops ledger for the escalation record (do not create a second incident
store), and bp-110's worker handle for the kill (do not open a second process handle).

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — is there really no bound today?** **Confirmed.** `scheduler/supervisor.py:87` calls
  `handler(job)` with no timeout; the only timeouts in the system are socket-level
  (`config/defaults.toml:16-17`: `request_timeout_s = 120`, `generation_timeout_s = 600`) and they
  bound one HTTP read, not a job. `launcher.py:1158-1160` prints `(no enforced job budget)` — the
  code says so in its own output.
- **Q2 — why must the deadline be per-BATCH and not per-job-elapsed?** ⚑ **The note's named
  disqualifier** (§2.10): a per-job-elapsed deadline kills a healthy 14-hour backfill at hour N,
  on schedule, every time. The live `code_backfill` lane legitimately runs for hours (the last
  observed orphan ran 13 h 51 m). The batch deadline asks "did *this unit* finish", which is a
  progress question; job-elapsed asks "has it been long", which is not.
- **Q3 — what does a kill actually stop?** ⚑ **The burn stops, and this is now MEASURED, not
  assumed.** `dn-local-model-runtime` §2.1 A answers supervision's **V3** empirically: Ollama
  0.31.2 abandons generation when the HTTP client dies — in the palace's actual non-streaming mode
  (`core/models/ollama_client.py:116`), a client killed at t+7 s produced `srv stop: cancel task`
  at 429 of 8000 tokens, with a follow-up served in 0.457 s and no queueing. So SIGKILL of the
  worker does stop the model-side work. **Do not overstate it:** that is a property of software we
  do not control and it is re-answerable on every Ollama bump — which is why the escalation record
  (Item 4) must capture enough to notice if it ever stops being true.
- **Q4 — what about a pure-CPU wedge?** SIGKILL of the worker process ends it unconditionally —
  that is the kernel, not cooperation. This is the finding-0169 incident's terminating condition,
  which today does not exist at all.
- **Q5 — where does the escalation record go?** **The code does not settle this.** `ops/ledger.py`
  exists and is opened in the status path (`launcher.py:1119-1121`, `open_ledger(self.cfg)`), but
  whether it carries a record shape suitable for an escalation event is **not established by
  reading**. The builder must read `ops/ledger.py` before Item 4 and either reuse a shape or raise.
  **It must not be a `print`** — §2.10 requires the firing to mint a durable record, or the kill is
  the silent state change the mandate forbids.
- **Q6 — what happens to the killed job's row?** The queue's terminal states and `attempts`
  counter stay as they are (§1.2 of the note). A killed job is `fail`ed with an explicit cause, so
  it is **visible** rather than silently pending — the same discipline `sweep_orphans` already
  applies to stranded non-idempotent kinds (`scheduler/queue.py:391-393`).
- **Q7 — does `down` currently bound anything?** No. `_serve` loops until `self._stopping`
  (`launcher.py:675`), and `c.supervisor.run()` inside it drains the *entire* backlog before the
  flag is even re-read. So a SIGTERM during a 1,766-job drain waits for the whole backlog. That is
  finding-0171 in one sentence.

**Additional risks or questions surfaced during reading:**

- ⚑ **The escalation must never fire at the supervisor.** A builder generalizing "escalate on
  deadline" to the process it runs in would produce exactly the partial-write hazard §2.4 argues
  is dissolved. §10 makes this a STOP; §6 pins the target.
- The `llama-server` SIGTERM wedge measured in `dn-local-model-runtime` §2.1 G (mid-request
  SIGTERM did not exit in 30.9 s; SIGKILL required, while idle SIGTERM was 0.25 s) is evidence
  that **grace-then-SIGKILL is required, not belt-and-braces** — a graceful-only stop can hang.
  Same shape applies to a Python worker mid-embed.
- Four test files assert on shutdown/status surfaces and are carried.

## 4. Reconciliation  <!-- Part B -->

- **`ops/lifecycle/launcher.py:1158-1160`** — `(no enforced job budget)` → **banner: correction**,
  carried by Item 5. Replace it with the budget the system now has (elapsed vs deadline), and say
  in the commit that this closes finding-0178's observation. Removing the string without landing
  the budget would be the worse outcome: the honest admission is better than a silent absence.
- **`scheduler/supervisor.py:12-13`** — *"A reactive escalation is simply a high-priority job; it
  is dispatched at the next boundary, never as a mid-generation interrupt."* → **banner:
  correction.** After this plan, a *deadline* escalation **is** a mid-compute interrupt of the
  worker (never of the supervisor, and never of a landing). Distinguish reactive-scheduling from
  deadline-escalation explicitly, or a reader will conclude the queue gained preemption.
- **`docs/inbox/owner-questions.md`** oq-0035 → **cross-ref only**; the ruling is recorded and the
  builder must not edit it. Note in the journal that (a) landed and OPS-4 is discharged.
- **`docs/findings/finding-0171.md` / `finding-0178.md`** → **cross-ref: extension.** Closure
  evidence goes in the journal for the orchestrator at seal; a builder may not edit a finding.

## 5. Write scope

`scheduler/worker.py` gains the SIGTERM→grace→SIGKILL escalation of the child.
`scheduler/supervisor.py` owns the clocks and the deadline decision. `ops/lifecycle/launcher.py`
carries the bounded drain and the status render. `tests/unit/test_job_budgets.py` is new; the four
remaining test files are **carried because they pin the surface this plan moves** (shutdown
behaviour and the status render's job lines).

Deliberately OUT of scope: `scheduler/queue.py` (bp-109 — this plan *reads* the deadline column, it
does not add or change one), `ops/lifecycle/lease.py` (bp-111), every `core/ingest/` lane, and
every foundation-denylist file.

## 6. Interfaces pinned inline

**The escalation contract — target and ladder, both non-negotiable.**

```
TARGET:  the WORKER child process, and nothing else. Never the supervisor. Never a landing step.
LADDER:  missed batch deadline -> SIGTERM the worker -> wait `escalation_grace_s` -> SIGKILL
         -> waitpid (the kill is only complete when the child is REAPED)
RECORD:  every firing mints a durable structured record. A kill with no record is the silent
         state-change the mandate forbids (note §2.10).
```

**The three budgets, verbatim from `dn-supervision-and-liveness` §2.5:**

```
1. Batch budget  — a batch that exceeds its deadline => escalation (a). The batch is also the
                   fairness unit: between batches the supervisor may claim other-lane work.
2. Job budget    — per-kind wall-clock ceiling enforced by the supervisor.
3. Drain bound   — SIGTERM to the daemon => finish landing the current batch, persist the
                   worker's checkpoint, escalate the worker if it ignores its own SIGTERM for
                   N seconds, exit. `down` becomes verifiably boundable.
```

**The config keys already exist** — bp-110 landed the whole `[scheduler]` section so it could
never be half-defined. This plan **consumes** them and adds none:

```python
    batch_deadline_s: float = 0.0      # 0 = no deadline (today's behaviour)
    job_budget_s: float = 0.0          # 0 = no budget (finding-0178's status quo)
    escalation_grace_s: float = 30.0   # SIGTERM -> N -> SIGKILL
```

⚑ **Zero means "no budget", and zero is the default.** Landing this plan must not change the
behaviour of any deployment that has not opted in. A non-zero default would kill jobs on upgrade.

**The line being replaced** (`ops/lifecycle/launcher.py:1158-1160`):

```python
                # No budget fraction: no job-level timeout exists (bp-102 Q4 / finding-0174).
                print(f"  running: #{j.id} {j.kind} — elapsed "
                      f"{humanize_seconds(j.elapsed_s)} (no enforced job budget){flag}")
```

**What must keep working, untouched** (`launcher.py:1161-1169`) — bp-105's store-clock line, the
one channel that distinguishes a healthy backfill from a wedged one. The note keeps bp-105's
diagnostics in place throughout; a builder tidying the render must not absorb it.

## 7. Items

Blast radius: read-only deadline arithmetic → the kill → the record → the drain → the render.

### Item 1 — the deadline is computed and reported, but fires nothing

- **Objective:** the supervisor knows a batch or job is over budget, and says so, without acting.
- **Files:** `scheduler/supervisor.py`, `tests/unit/test_job_budgets.py`
- **Acceptance test:** with `batch_deadline_s`/`job_budget_s` set, an over-budget unit is
  identified with its elapsed and its deadline; with both at 0 nothing is ever over budget.
- **Falsifier:** *a healthy long batch is reported over budget.* Run the real `code_backfill`
  shape against the proposed defaults before Item 2 gives this any teeth — an over-eager deadline
  discovered *after* the kill lands is a killed backfill, not a bug report.
- **Invariant(s) it must not violate:** deadlines are per-batch, not per-job-elapsed (§3 Q2); 0
  means no budget.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** none.

### Item 2 — bounded escalation of the worker

- **Objective:** an over-deadline worker is stopped by the kernel, within a bounded time.
- **Files:** `scheduler/worker.py`, `scheduler/supervisor.py`, `tests/unit/test_job_budgets.py`
- **Acceptance test:** a worker that ignores SIGTERM is SIGKILLed after `escalation_grace_s` and
  **reaped** (`waitpid` returns); total time from deadline to reaped is bounded by
  `grace + ε`; the supervisor survives and continues its loop; the job's row is `fail`ed with an
  explicit cause.
- **Falsifier:** ⚑ *the escalation is reachable with the supervisor's own pid as its target.*
  Assert this structurally — the kill path must take a worker handle, never a pid parameter a
  caller could supply. ⚑ Also: *grace-then-SIGKILL still leaves a process.* An unkillable child
  means the ladder has no teeth and the fail-safe is decorative.
- **Invariant(s) it must not violate:** the supervisor is never a target; a landing step is never
  interrupted; a killed job loses only computation, never a landed row (bp-110's split is what
  makes this true — if it is not true, that is a bp-110 defect and a §10 raise).
- **Touches stored data?** No (the worker holds no writer). **Parallelizable?** No.
  **Depends on:** Item 1.

### Item 3 — no kill is silent

- **Objective:** every firing leaves a durable, structured, greppable record.
- **Files:** `scheduler/supervisor.py`, `tests/unit/test_job_budgets.py`
- **Acceptance test:** a fired escalation writes a record carrying job id, kind, elapsed, deadline,
  which signal ended it, and the reap latency. It survives process exit and is readable afterwards.
- **Falsifier:** ⚑ *the record is a `print`.* Stdout is not durable and the daemon runs under
  launchd; a kill visible only in a log the operator was not tailing is the silent state change
  §2.10 forbids.
- **Invariant(s) it must not violate:** **no second incident store** — reuse `ops/ledger.py` or
  raise (§3 Q5, §10); the record must not contain secrets or vault content.
- **Touches stored data?** Yes (ledger append). **Parallelizable?** No. **Depends on:** Item 2.

### Item 4 — `down` becomes verifiably boundable

- **Objective:** finding-0171 closes: SIGTERM to the daemon leads to exit within a stated bound.
- **Files:** `ops/lifecycle/launcher.py`, `tests/integration/test_lifecycle_control.py`,
  `tests/unit/test_lifecycle_honest_shutdown.py`
- **Acceptance test:** with a long job in flight, SIGTERM to the daemon: the current batch's
  landing completes, the worker's checkpoint persists, the worker is escalated if it ignores its
  own SIGTERM, and the process exits within the stated bound. `down`/`stop` print **what was
  signalled, what was verified, and within what bound** (§4 of the note).
- **Falsifier:** ⚑ *`down` waits for the whole backlog.* That is finding-0171 unchanged (§3 Q7).
  Test it with a deep queue, not a single job — a one-job test passes today.
- **Invariant(s) it must not violate:** the *landing* is allowed to finish (interrupting it is how
  a partial write is created); `_shutdown`'s idempotence (`launcher.py:704-707`) holds; the run row
  still closes clean, so the successor does not come up in recovery mode.
- **Touches stored data?** Yes (a landing completes; a checkpoint persists). **Parallelizable?**
  No. **Depends on:** Item 2.

### Item 5 — the status line stops admitting there is no budget

- **Objective:** `status` shows elapsed against the budget that now exists.
- **Files:** `ops/lifecycle/launcher.py`, `tests/integration/test_status_report.py`
- **Acceptance test:** a running job renders elapsed **and** its deadline/fraction; with budgets at
  0 the line keeps its current honest wording. `status` stays cheap — bounded aggregates only,
  asserted by the existing `tests/unit/test_status_cost_bound.py`.
- **Falsifier:** ⚑ *`status` gets more expensive.* bp-102's Item 2 falsifier: a status command that
  repeats finding-0169 one level up has failed even if every number is right.
- **Invariant(s) it must not violate:** bp-105's `embedding: YES / ⚠ WEDGED` line
  (`launcher.py:1161-1169`) and the ORPHANED render are **kept** — they are the diagnostic layer
  the note preserves throughout.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 1.

## 8. Math carried explicitly

N/A — no mathematical object. Elapsed-vs-deadline is a subtraction. The *choice* of budget values
is deliberately parked (§11): a declared budget without history is a magic number, which the note's
own rot argument forbids, and §2.9's SLOW denominator does not exist yet.

## 9. Non-goals

- ⚑ **No escalation of the supervisor, ever** (§2.4).
- **No SLOW detector.** Mode 3 needs a denominator that does not exist (§2.9, Parked decisions).
- **No retry / backoff / dead-letter redesign** (§1.2 of the note).
- **No per-kind budget values shipped non-zero.** Defaults stay 0 = no budget (§6).
- **No new config keys** — bp-110 landed the section.
- **No second incident store** — reuse `ops/ledger.py` or raise.
- **No lane changes, no lease changes.**

## 10. Stop-and-raise conditions

- ⚑ **The escalation path can be aimed at the supervisor** ⇒ **STOP.** This is the one design
  property whose violation recreates the partial-write hazard the whole oq-0035 ruling dissolves.
- ⚑ **`ops/ledger.py` has no suitable record shape** (§3 Q5) ⇒ **STOP and file.** Do not invent a
  second incident store (DRY), and do not downgrade to a `print` (§2.10). Park the criterion and
  continue with the other items.
- **Item 1's falsifier fires** — a healthy `code_backfill` batch reads over budget under the
  proposed defaults ⇒ **STOP before Item 2.** Giving teeth to a mis-calibrated deadline kills a
  14-hour backfill on schedule (bp-102 §10's disqualifier).
- **A killed job turns out to lose a landed row** ⇒ STOP and file a `spec-defect` against bp-110.
  The claim that interrupting the worker interrupts only computation is the design's foundation;
  if it is false, this plan must not ship.
- **A carried test cannot be made green without weakening an assertion** ⇒ STOP and file.
- Any blessing transition — never.

## 11. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| per-kind budget values | 0 (no budget) | a week of batch timings exists |
| `escalation_grace_s` | 30 s | an owner call at ratification; then observation |
| killed job's disposition | FAILED with explicit cause | a retry policy is designed |
| drain bound value | grace + one landing | Item 4's measurement |

**Rejected alternatives, per row:**

- **Budget values.** Rejected: *a per-kind number now* — the note's Parked decisions (Q3, the SLOW
  denominator) say a declared budget without history is a magic number, and no batch telemetry
  exists yet to derive a p50 from. Rejected: *one global budget* — the lanes differ by four orders
  of magnitude in honest runtime. Re-entry is explicitly *"after the first split lane has
  accumulated a week of batch timings."*
- **Grace.** The note records 30 s as its default proposal and marks the value an **owner call at
  ratification**; the note is ratified, so 30 s stands unless the owner says otherwise. Rejected:
  *0 (SIGKILL immediately)* — loses the worker's chance to persist a checkpoint. Rejected: *a long
  grace* — `dn-local-model-runtime` §2.1 G measured a mid-request SIGTERM not exiting in 30.9 s, so
  a long grace just delays the inevitable SIGKILL while the drain bound slips.
- **Killed job disposition.** Rejected: *auto-requeue* — that is retry policy, an explicit non-goal,
  and for a non-idempotent kind it is double execution.
- **Drain bound.** Rejected: *a fixed wall-clock* — it would have to exceed the longest honest
  landing, which is V1's number, so it is derived, not chosen.

## 12. Dependency & ordering summary

Items: **1 → 2 → {3, 4}**, with **5** depending only on Item 1. Ordered by blast radius so a
builder that stops early has stopped before anything can kill anything.

**`depends_on: [bp-111]`** for two reasons: `ops/lifecycle/launcher.py` contention (bp-108 →
bp-111 → bp-112 → bp-116, strictly sequenced), and because the drain report and status render
both read the liveness surface bp-111 establishes. Transitively this sits after bp-108, bp-109 and
bp-110 — it is the last plan of the supervision wave's *seam* half, and the two lane plans
(bp-113, bp-114) follow it.

**Not parallelizable with anything.**

⚑ **This plan closes OPS-4.** At its seal the orchestrator should check the DoD row in
`docs/tracks/ops.md:13` — *"the shutdown contract closed — oq-0035 ruled and built (finding-0171);
`down` must be able to stop a wedged daemon"* — and the completion-claims-honesty rule applies:
the *design* half was discharged by the ratified note, the *build* half by this plan, and the lane
migrations (bp-113/bp-114) are still owed before the wave is complete.
