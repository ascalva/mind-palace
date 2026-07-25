---
type: journal
plan: bp-105
started: 2026-07-25
updated: 2026-07-25
---

# Journal — bp-105 (the restart is trustworthy)

Session-47. Contract: `builder`. Ordering per §12: **Item 2 → Item 3 → Item 1**.

---

## Checkpoint 1 — §2 manifest read; Item 2's identity rule GROUNDED, and the plan's stated rule is INVERTED

### What the manifest actually says (two line refs in the plan are stale)

- `ops/lifecycle/snapshot.py:574,585` → the file is **431 lines**. `stalled` is at
  `snapshot.py:191`, `wedged` at `snapshot.py:202`. Same predicates, different lines;
  finding-0188 carries the same stale refs. Not a defect, just re-anchor when reading.
- Everything else in §2 checked out: `launcher.py:505-545` (`start`, sweep call at `:538`),
  `launcher.py:115-122` (`_pid_alive`, pure `os.kill(pid,0)`), `launcher.py:1124-1128`
  (`reset()`'s guard — the pattern to copy), `runs.py` (`pid` `:64`, `started_at` `:65`),
  `scheduler/code_sync.py:53` (`code_backfill_handler`, one synchronous `sync.backfill(...)`).

### ⚑ THE FINDING: the pinned identity rule is backwards and would have built a no-op guard

The plan §6 docstring and finding-0186 both state:

> *"A process created BEFORE its own run row cannot be that run's supervisor."*

**This is inverted.** `start()` does `run = self.runs.open_run(..., pid=os.getpid(), ...)` —
the supervisor process necessarily **exists before** it writes its own row. Measured:

```
create_time epoch: 1784999058.294983  -> 2026-07-25T17:04:18.294
started_at (as runs.py writes it):       2026-07-25T17:04:18      # timespec="seconds"
=> a genuine supervisor ALWAYS predates its own run row
```

Implementing the rule as written makes `_supervisor_alive` return **False for every genuine
live supervisor** — the guard never fires, Item 2's entire purpose defeated, falsifier A
unreachable. Filed as **finding-0198** (spec-fidelity; builder-resolved per CLAUDE.md routing).

The plan's *governing* sentence is right and is what I built to: **"the recycled-pid carve-out
fires only when identity is _positively disproven_."**

### The rule actually implemented — two one-sided DISPROOFS, refuse otherwise

`_supervisor_alive(run)` = `_pid_alive(run.pid)` AND not positively disproven, where
disproof is either:

- **D1 — the process postdates the row.** `create_time > started_at + 5 s` ⇒ it cannot have
  written a row that already existed. Airtight. The 5 s absorbs `started_at`'s whole-second
  truncation (measured above: a genuine supervisor can read up to ~1 s *after* its own row)
  plus clock jitter; a real recycle needs the pid counter to wrap (~99k spawns) and so is
  never within seconds.
- **D2 — the process is not a Python interpreter.** The supervisor is always one: the plist
  runs `uv run scripts/palace.py start` and `os.getpid()` is evaluated inside python
  (`ops/lifecycle/com.mind-palace.palace.plist:26-33`). `psutil.Process(pid).name()` is
  readable **without privilege even for root-owned foreign processes** on macOS (measured:
  `pid 1 name -> 'launchd'`, `exe -> '/sbin/launchd'`, while `cmdline()` raises AccessDenied)
  — so this disproof is available exactly where it is needed.

Anything else — `AccessDenied`, `NoSuchProcess`, an unparseable `started_at`, a python
process created before the row — **refuses**. That is the owner ruling applied.

**Why D2 is load-bearing and not decoration.** D1 alone cannot clear a stale row whose pid was
recycled to a *long-lived* process (the pid counter wrapped onto `launchd`/`systemd`): such a
process predates the row, so D1 is silent and the system bricks — the exact self-inflicted
brick the ruling's trap section warns about. It is also the shape the existing suite already
encodes: `tests/integration/test_lifecycle.py:239,250` open run rows with **`pid=1`**, and
`_pid_alive(1)` is True. A window-based rule (`create_time` within N seconds *before* the row)
was considered and **rejected**: it needs a magic bound on how long `start` takes to reach
`open_run` (preflight alone can burn 120 s on the Ollama probe, finding-0195), and on a
freshly-booted `ubuntu-latest` CI runner pid 1's create_time falls *inside* any such bound —
those two tests would go red in CI on machine uptime. D2 is uptime-independent and is a
statement about identity rather than about timing.

### Rejected: the psutil typedshim (out of write_scope)

`core/typedshims/psutil.py` is the single site that touches raw `psutil`
(`core/vitals.py` and `launcher.py:291,1003` both go through it) and is where
`process_create_time`/`process_name` belong. It is **not in bp-105's `write_scope`**, so per
CLAUDE.md ("narrow the scope or file a finding — never route around") the probe lives in
`ops/lifecycle/launcher.py` behind one narrow helper, warranted inline, and the hand-off is
recorded in **finding-0198**. Not shelling out to `ps` (§2 forbids it, correctly).

### §3 grounding item 1 — `checkpoint()` DISQUALIFIED, confirmed against the code

`scheduler/queue.py:396-403` sets `state = QUEUED`. `code_backfill` **is** in
`_IDEMPOTENT_KINDS`, and `enqueue` (`:260-271`) returns the waiting QUEUED row instead of
inserting. So a job heartbeating via `checkpoint()` becomes a collapse target mid-flight and a
follow-up pass is silently swallowed — which is precisely the falsifier `enqueue`'s own
docstring says the QUEUED-only rule exists to prevent (`:242-245`). Confirmed DISQUALIFIED.
Item 1's channel choice + the other rejected alternatives land in the next checkpoint.

### State

- Plan flipped `ready → in-progress`; `.claude/state/active-plan` points at bp-105.
- Nothing written to code yet. **Next: implement Item 2** in `ops/lifecycle/launcher.py`.

---

## Checkpoint 2 — Items 2 and 3 BUILT and MUTATION-VERIFIED (9 mutations, 9 caught)

### What landed

`ops/lifecycle/launcher.py`:

- `_CLOCK_SLACK_S = 5.0`, `_process_identity(pid)` (the quarantined raw-`psutil` probe returning
  `(create_time, name)`, never raising), and `_supervisor_alive(run, *, pid_alive, identity)` —
  both probes injected, the same discipline `snapshot.run_state` applies to `pid_alive`.
- The **single-instance gate** at the top of `start()`, *ahead of preflight* (an unrunnable state
  should not first cost the operator preflight's uncosted 120 s Ollama probe, finding-0195), and
  **not** gated on `force`.
- The recovery banner now prescribes `palace stop`, not `start --force` — with the gate in place
  the old remedy is a wall, since the recovery run is itself a live supervisor. A graceful stop
  closes the row CLEAN, so the successor comes up normally with no flag at all.

`tests/unit/test_restart_trustworthy.py` (new): 17 tests, all green.

### Mutation verification — every falsifier bites

| # | mutation | verdict | test that caught it |
|---|---|---|---|
| M1 | `sweep_orphans` call DELETED | ✓ caught | `..._against_a_real_queue` (+2) |
| M2 | sweep called with the WRONG run id | ✓ caught | `..._against_a_real_queue` (+1) |
| M3 | sweep MOVED after `_serve()` | ✓ caught | `..._against_a_real_queue` (+1) |
| M4 | the gate removed entirely | ✓ caught | `..._refuses_over_a_live_supervisor` (+1) |
| M5 | D1 removed (a postdating pid bricks start) | ✓ caught | `..._recycled_pid_does_not_brick_start` |
| M6 | D2 removed (a pid recycled onto `launchd` bricks) | ✓ caught | `..._long_lived_system_process...` |
| M7 | clock slack → 0 | ✓ caught | 4 tests, incl. both gate tests |
| M8 | `--force` bypasses the gate | ✓ caught | `test_force_does_not_bypass...` |
| M9 | identity dropped → bare `_pid_alive` | ✓ caught | both recycle tests |

M1–M3 are finding-0187's exact falsifier — *"deleting the call leaves the suite green (85/85)"*.
It no longer does.

**M7 is the sharpest result and worth recording.** With slack at 0, the *real-probe* test
`test_this_very_process_reads_as_a_live_supervisor` FAILS — a genuine live supervisor, measured
on this host, reads as postdating its own run row. That is the whole-second truncation of
`started_at` (`runs.py:106`), and without the slack the gate would have silently stopped
protecting anything while every other test stayed green.

**M6, cross-checked outside my own test file.** Removing D2 turns
`tests/integration/test_lifecycle.py` red — `test_unclean_prior_run_enters_recovery` and
`test_force_resumes_normally_after_unclean` both open run rows with **`pid=1`**, which is alive.
So the pre-existing suite independently demanded the not-a-python-process disproof; without it
the recovery path is unreachable. Confirms D2 is load-bearing, not decoration, and confirms the
one-sided rule the plan pinned would have bricked the system's own recovery mode.

Adjacent suites green with no edits needed: `test_lifecycle.py` + `test_lifecycle_liveness.py`
+ `test_lifecycle_honest_shutdown.py` + `test_status_incident_oracle.py` = **53 passed**.

### Item 3's seam question — resolved, no STOP needed

§10 said to stop and raise if `Components` could not take a real `JobQueue`. It can: `Components`
is structurally typed and `JobQueue` satisfies the two methods the launcher calls
(`sweep_orphans`, `close`). The reason it had never been done is the one finding-0187 names —
all three test constructions passed `_FakeQueue`, so nobody tried. `_RecordingQueue` **subclasses**
the real `JobQueue` to record sweep-vs-claim ORDER; the rows are seeded through the real schema
and read back over a fresh read-only connection, because `_shutdown` closes the handle it was
given (`launcher.py:610-614`).

### State

- **Item 2 ✅ · Item 3 ✅.** finding-0198 filed (spec-fidelity, builder-resolved).
- **Next: Item 1** — §3 channel grounding, then the two-state discriminating render.

---

## Checkpoint 3 — §3 channel CHOSEN and grounded; Item 1 BUILT; 8 more mutations, 8 caught

### ⚑ The grounding that eliminated every channel the plan listed

**All three of §3's candidates share one fatal assumption: that something can EMIT while the wedge
is happening. Nothing can.** `Supervisor.tick` calls `handler(job)` synchronously with no timeout
(`scheduler/supervisor.py:87`), so `Launcher._serve`'s loop is **blocked for the entire duration of
the very job being diagnosed**. Its health tick, its snapshot tick and its housekeeping tick all
stop. This is the fact that disqualifies the plan's own recommendation:

- **(a) a supervisor-written periodic sample** — *recommended by §3, and it cannot work.* The
  writer is the blocked loop. Worse, a naive baseline is a **false-green generator**:
  `Supervisor.run()` has no `max_ticks` in `_serve`, so it drains the whole 1,766-job backlog
  without ever returning; rows landed by earlier jobs would read as the wedged job's progress.
- **(b) an additive `jobs` column** — requires `scheduler/queue.py`, **not in write_scope** (and
  §3 itself flags its check+ALTER as not race-safe). Out on capability grounds.
- **(c) the existing vitals surface** — found and read: `Supervisor._record` writes
  `record_vital("queue.depth", …)` at `supervisor.py:109-114`, i.e. **only after `handler(job)`
  returns**. It is another job-BOUNDARY signal and is blind to an intra-job wedge for exactly the
  same reason `done_in_window` is. This answers §3's grounding item 2: the mechanism the SEAMS
  auditor referenced exists, and it is the wrong channel.
- **`checkpoint()`** — DISQUALIFIED in Checkpoint 1.

### The channel actually built: the store's own filesystem clock

The embed happens *inside* the blocked call, and it writes to disk. **The filesystem is the one
channel the wedge cannot mute**, and it needs no cooperation from core, the scheduler or the
supervisor. `store_idle_seconds(vector_store)` → seconds since anything was last written under
`data/vectors.lance`.

The predicate is **threshold-free**, which is what makes it trustworthy — the job's own elapsed is
the denominator:

> **Was the vector store written after the running job started?**
> Yes ⇒ that job has landed rows ⇒ working. If the last write PREDATES the job's own start ⇒ it has
> landed nothing since it began ⇒ wedged.

Same "positive disproof" shape as Item 2, and no tuned window to rot.

**Measured, not assumed** (cost is a correctness property here — finding-0169):

| probe | result |
|---|---|
| dirs-only walk of the real 22,621-row store | **8 stats, 0.80 ms** |
| full-tree walk (897 files) | 3.90 ms — **identical answer** |
| does a landed row advance the mtime? | **yes**, verified with a real `VectorStore.add` |
| does `open_vector_store` / `count()` advance it? | **no** — `status` is not self-blinding |

O(directories), independent of row count — the same bound `read_queue_stats` carries, so bp-102's
Item-2 cost falsifier still holds.

`scheduler/code_sync.py` is in `write_scope` for "progress emission if the chosen channel needs
it". **It does not — left untouched, deliberately.** No handler change, no core change.

### What landed

- `snapshot.py`: `store_idle_seconds()`; `QueueStats.store_idle_s`; the new tri-state
  `embedding` + `progressing` properties; `stalled`/`wedged` suppressed while progressing;
  `store_idle_s` + `anomalies.embedding` in the JSON payload.
- `launcher.py`: the probe feeds `read_queue_stats`, and the `embedding:` line renders it.
- `test_restart_trustworthy.py`: 7 Item-1 tests. `test_status_incident_oracle.py`: the two tests
  finding-0188 named are annotated honestly (below).

### The falsifier, discharged — the two renders side by side

Identical queue, identical live daemon, differing in one physical fact:

```
HEALTHY
  queue depth: 40   (in 1.0/min · out 0.0/min · net +1.0/min over 20 min)
  throughput: 0 done, 0 failed in the last 20 min
  running: #1 code_backfill — elapsed 1h15m00s (no enforced job budget)
  embedding: YES — rows last landed 12s ago, inside the running job's 1h15m00s. …
                                                          ← not one ⚠ in the block

WEDGED
  queue depth: 40   (… net +1.0/min over 20 min)  ⚠ ZERO DRAIN (0 completed)
  throughput: 0 done, 0 failed in the last 20 min  ⚠ nothing completed
  running: #1 code_backfill — elapsed 1h15m00s …  ⚠ running while NOTHING completed this window
  embedding: NO — the vector store has not been written in 1h30m00s, which PREDATES
             the running job. It has landed nothing since it started.  ⚠ WEDGED
```

### Mutation verification — Item 1

| # | mutation | verdict |
|---|---|---|
| N1 | `stalled` fires unconditionally | ✓ caught (2 tests) |
| N2 | `wedged` fires unconditionally | ✓ caught (2 tests) |
| N3 | suppression reverted to bp-102 behaviour | ✓ caught (2 tests) |
| N4 | `embedding` always True (blanket false-green) | ✓ caught (3 tests) |
| N5 | `embedding` compares to `max` elapsed, not `min` | ✓ caught (3 tests) |
| N6 | the idle probe always returns `None` | ✓ caught (4 tests) |
| N7 | the mtime walk skips subdirectories | **✗ SURVIVED → now caught** |
| N8 | an absent store fabricates `0.0` instead of `None` | ✓ caught (2 tests) |

N1–N3 are §7's second falsifier discharged: *"prove the guard bites by mutating each predicate to
fire unconditionally."* Against bp-102's fixture that mutation passed all 9 tests; against the
non-trivial fixture (`depth > 0` **with** a running job) it fails.

**⚑ N7 is the one worth carrying forward — I reproduced the audit's own defect class in my own
test.** Stubbing the subdirectory walk out of `store_idle_seconds` left all 22 tests green, because
every fixture aged the tree *uniformly* and the root then carried the answer. **The real store does
not look like that**: measured on `data/vectors.lance`, the root's mtime was 14.9 h old while
`chunks.lance/{_versions,_transactions,data}` were 13.7 h — a lance write adds entries to the
nested dirs and never touches the root. A root-only probe would report a store written minutes ago
as idle for hours, i.e. call a *healthy* backfill WEDGED. The fixture, not the code, was blind.
Closed by `test_a_write_into_a_nested_fragment_directory_counts_as_a_write`, which builds the real
layout (stale root, fresh fragment dir). **Mutation testing found this; no amount of reading would
have.**

### The two bp-102 tests finding-0188 named — annotated, not quietly deleted

- `test_a_healthy_system_raises_no_flags` → renamed `test_an_idle_drained_queue_raises_no_flags`
  and scoped honestly to the IDLE case, with a pointer to the non-trivial guard. Kept rather than
  removed: an idle drained queue must read clean too.
- `test_a_running_row_under_a_LIVE_daemon_is_not_called_orphaned` — finding-0188's charge that it
  "encodes the false alarm as EXPECTED" is now answered in place: its fixture has **no vector
  store**, so the render says `embedding: unknown` and the flags fall back to bp-102's behaviour.
  That is the honest answer when nothing can be measured, and the test now asserts the `unknown`
  line so the distinction is explicit rather than accidental.

### Gate status

`ruff` ✅ · import-firewall ✅ · `mypy core agents eval ops scheduler scripts` **0 errors** ✅ ·
`mypy` full **exactly 69** (the pinned tests baseline) ✅ · `ops.type_gate` ✅.
Reaching 69 needed real fixes, not suppressions: `_Run` became a genuine `RunRecord` (a structural
fake would have forced `_supervisor_alive` to widen to `Any`), and every `runs.last()` is
None-checked.

Targeted suites: 75 passed (`test_restart_trustworthy` + `test_status_incident_oracle` +
`test_status_cost_bound` + `test_lifecycle` + `test_lifecycle_liveness`). Full green-gate suite
before Item 1: **2036 passed, 8 skipped**. Full re-run pending.

### State

- **Item 1 ✅ · Item 2 ✅ · Item 3 ✅.** All three warrants discharged. 17 mutations, 17 caught.
- **Next:** full-suite confirmation, then commit. Nothing is parked; no owner decision is owed.

---

## Checkpoint 4 — verified against the REAL incident state, not a fixture

`uv run scripts/palace.py status` on the live data dir, daemon down (read-only; nothing mutated):

```
running: #300246 code_sync — elapsed 13h51m17s   ⚠ ORPHANED — no live daemon owns this row
embedding: NO — the vector store has not been written in 13h53m21s, which PREDATES
           the running job. It has landed nothing since it started.  ⚠ WEDGED
```

**The two figures are ~2 minutes apart, and in the right order.** The store's last write predates
job 300246's start, so the orphan embedded exactly nothing in its ~14 hours — the instrument
reaches the correct verdict on the actual incident, independently of any fixture. It also
corroborates the audit's account from a completely different measurement: 300246 started at
03:45:07 and never did any work. (Also visible: `1766` queued, `22,621` vector rows, `300242 done`
— every figure matches the resume brief.)

This is the deskcheck demonstrable for the Ops row: *the instrument discriminates, shown on the
incident it was built for.*

### Two cleanups on review (not test-driven — read-driven)

1. The render recomputed `embedding`'s denominator inline with a truthiness filter
   (`if j.elapsed_s`), which drops a legitimate `0.0` and can raise `ValueError` on an empty
   sequence. It was safe only via a non-obvious invariant. Replaced with
   `QueueStats.youngest_running_elapsed_s`, so the render prints the number the predicate actually
   decided on. DRY, and the fragility is gone.
2. `embedding` was initially placed under `anomalies` in the JSON payload, which is semantically
   backwards — `embedding: true` is the evidence that SUPPRESSES two anomalies. Moved to a sibling
   `progress` block with `store_idle_s`.

### Gate — final

| gate | result |
|---|---|
| `ruff check .` | ✅ all checks passed |
| `scripts/check_imports.py` (Invariant 2) | ✅ OK |
| `mypy core agents eval ops scheduler scripts` | ✅ **0 errors** (Tier-2 floor) |
| `mypy` (full, tests baseline) | ✅ **exactly 69** |
| `ops.type_gate` | ✅ membership + bare-ignore scans OK |
| every suite touching the changed surfaces (20 files) | ✅ **189 passed** |
| full green-gate suite | ✅ **2043 passed, 8 skipped, 21 deselected** (12m19s) |

Suite arithmetic checks out: 2036 before Item 1 (itself already including Items 2–3's 17 tests),
+7 for Item 1's new tests, = 2043. One test was renamed, not added.

### ⚑ Hand-off to the orchestrator — findings I cannot close myself

The builder contract's writable surfaces are `write_scope` + this journal + **new** files in
`docs/findings/`. Editing an existing finding is out of scope, so these need `/triage`:

- **finding-0186** — DISCHARGED by Item 2. The guard is built, `--force` cannot bypass it, and the
  recycled-pid trap is closed. ⚑ **The `⛔` constraint in the session-46 brief can be lifted:
  `palace start` can no longer be run over a live supervisor.** (`scripts/watch.py` building a
  second `Supervisor` on the shared queue is a SEPARATE route and is **still open** — this plan
  did not touch it. Do not lift that half.)
- **finding-0187** — DISCHARGED by Item 3. Deleting the sweep call now fails the suite.
- **finding-0188** — DISCHARGED by Item 1.
- **finding-0198** — filed here, builder-resolved, with one OPEN hand-off: move
  `_process_identity`'s raw-`psutil` touch into `core/typedshims/psutil.py`. Mechanical, one plan,
  no behaviour change.

### What the restart brief should now say

Both qualifications on the session-46 restart checklist are lifted:

- **Step 3** was qualified on finding-0187 (untested sweep wiring) + finding-0186 (live-run
  hazard). Both are closed. The sweep is covered against a real `JobQueue`, and single-supervisor
  start is now enforced rather than merely advised.
- **Step 5** was qualified on finding-0188 (*"the instrument is blind — expect the cry-wolf
  output"*). It no longer is. **The re-enqueued backfill will read `embedding: YES` and raise no
  flag while it is healthy**, and `⚠ WEDGED` if it genuinely stops embedding. The rate IS
  observable in the discriminating sense, which is what the Ops track's DoD asked for.

`palace up` remains **owner-gated, never autonomous**.
