---
type: build-plan
id: bp-108
track: ops
status: proposed
design_ref:
  - docs/design-notes/dn-supervision-and-liveness.md
contract: builder
write_scope:
  - ops/lifecycle/lock.py
  - ops/lifecycle/launcher.py
  - scripts/watch.py
  - tests/unit/test_supervisor_lock.py
  - tests/unit/test_restart_trustworthy.py
  - tests/unit/test_lifecycle_honest_shutdown.py
  - tests/unit/test_children.py
  - tests/integration/test_lifecycle.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual: null
depends_on: []
parallelizable_with: [bp-115]
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0186.md
  - docs/findings/finding-0187.md
  - docs/build-plans/bp-105/journal.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0186.md
---

# Build Plan — the supervisor role becomes exclusive, and the loop keeps its duty cycle

## 0. Mode & provenance

Corrective + tier-upgrade, graduated from `dn-supervision-and-liveness` §2.6 (the supervisor lock)
and §2.5's interim paragraph (`run(max_ticks=K)`). Investigation and planning produced this;
implementation proceeds item-by-item on owner approval.

**Why these two live in one plan.** They are the first two of the note's three "small independent
pieces" (§3 Sequencing), and they are not independent *of each other* in the only way that matters
to a builder: both edit `ops/lifecycle/launcher.py`, so they can never run as parallel worktrees.
Two plans over one file buys nothing and costs a session. The third piece (leased RUNNING rows) is
a genuinely disjoint file and IS split out, as bp-109.

## 1. Objective

The serve loop's two structural guarantees — that it is the *only* claimant of the queue, and that
its supervisory ticks run at job boundaries — stop resting on convention.

### 1.2 Non-goals (explicit — see §9)

Not the worker subprocess, not the lease, not escalation, not queue schema. [INFERENCE] Also not a
fix for the watcher's enqueue-per-poll behaviour (`dn-supervision-and-liveness` §1.2 keeps that a
separate codebase item) — inferred from that non-goal, not owner-stated.

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/dn-supervision-and-liveness.md` §2.2, §2.6 (the lock bullet + the five-target
   table), §2.10 (`run(max_ticks=K)` falsifier), V7 and V8 — **the content spec**
2. `docs/findings/finding-0186.md` — the warrant; its **open half** is `scripts/watch.py`
3. `docs/findings/finding-0187.md` — why a tier-5 "remember to call it" guard is not a guard
4. `ops/lifecycle/launcher.py` — `start` `:595-660`, the gate `:606-611`, `_serve` `:662-695`
5. `scripts/watch.py` — whole file, 65 lines
6. `scheduler/supervisor.py:99-107` — `run()`; **it already takes `max_ticks`**
7. `docs/build-plans/bp-105/journal.md` — the identity gate this demotes, and its evidence

**Does core already have this?** No file lock exists anywhere in the repo. `core/sandbox/` owns
subprocess lifetime, not mutual exclusion. There is no second implementation to reuse and none to
duplicate — but see §3 Q5 on **not** adding a second liveness probe.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — is the interim fix actually one line?** **Yes, and smaller than the note implies.**
  `Supervisor.run` **already accepts `max_ticks`** (`scheduler/supervisor.py:99`); the defect is
  purely the call site, `ops/lifecycle/launcher.py:676`, which calls `c.supervisor.run()` bare.
  Nothing in `scheduler/` needs to change.
- **Q2 — is the note's `max_ticks` falsifier real, or hypothetical?** ⚑ **Real, and grounded.**
  `_serve`'s sleep is *unconditional per iteration*: `launcher.py:694-695` runs
  `if self.tick_seconds: time.sleep(self.tick_seconds)` at the bottom of every pass, regardless of
  whether `run()` dispatched anything. With `tick_seconds = 1.0` (`launcher.py`'s `Launcher`
  default) and `max_ticks=1`, draining 1,766 queued no-ops would take **≈29 minutes** instead of
  seconds. The fix is therefore two-part: bound the drain **and** make the sleep conditional on
  the drain having been idle. Item 4 carries both; either alone is a defect.
- **Q3 — where exactly must the lock be acquired?** Before `sweep_orphans`, which is
  `launcher.py:653`. The existing single-instance gate is earlier still (`:606-611`, ahead of
  preflight). Both may coexist — see Q4.
- **Q4 — does the lock make bp-105's gate redundant?** **No, and deleting it would lose
  information.** The note is explicit (§2.6): the lock is *held-or-not* and can only say "no"; the
  identity gate can say **why** (`run #N (pid P) is live`). They are guarantee and diagnostic. The
  gate also runs ahead of preflight so an unrunnable state does not first cost a 120 s Ollama
  probe (`launcher.py:603-605`, finding-0195). **Keep both; re-document the gate as a diagnostic.**
- **Q5 — what does `watch.py` actually do wrong?** `scripts/watch.py:39-46` constructs
  `JobQueue(...)` and a second `Supervisor` and never calls `sweep_orphans`, so `active_run_id`
  stays `None` (`scheduler/queue.py:211`) and every row it claims is stamped NULL
  (`queue.py:321`). A NULL stamp is *by definition* reclaimable (`queue.py:376`, and the docstring
  at `:366-368` says so), so the next real supervisor's sweep can requeue or FAIL live work that
  `watch.py` is mid-flight on. It also calls `supervisor.run()` bare (`watch.py:53`) — the same
  unbounded drain as Q1.
- **Q6 — V7: who uses `watch.py`?** **The code does not settle this.** Nothing in the repository
  imports or invokes it: it is a `__main__` script (`watch.py:63-64`) documented in its own
  docstring as `uv run scripts/watch.py`, and the daemon builds its own vault watcher instead
  (`launcher.py:495`, `build_vault_watcher`). Its function is fully subsumed by the daemon. What
  would settle it is an **owner statement** about whether it is still used by hand — §10 parks
  this rather than deleting a script on an inference. The safe action available without that
  answer is Item 5's: bring it under the lock, so it *cannot* be the second claimant regardless.
- **Q7 — V8: does `flock` behave as assumed here?** **Not settled by reading; Item 1 measures it.**
  Three specific unknowns, all local: (a) advisory `flock` semantics on APFS; (b) whether the lock
  is held by the **supervisor's** python process rather than a `uv run` wrapper that exits —
  `uv run` execs into python on this platform, but that must be *observed*, not assumed; (c)
  behaviour under launchd `KeepAlive` restart, where the successor may start before the
  predecessor's fd is reaped.

**Additional risks or questions surfaced during reading:**

- ⚑ **`start()` is called by four test files** (`tests/integration/test_lifecycle.py`,
  `tests/unit/{test_children,test_lifecycle_honest_shutdown,test_restart_trustworthy}.py`). An
  unconditional lock changes `start()`'s preconditions for **all** of them — a test that starts
  two launchers over one data dir, or reuses a dir across cases without releasing, will red. All
  four are pre-widened into `write_scope` (graduate skill's retrofit rule, findings
  0071/0072/0075/0084). Five further files construct a `Launcher` without calling `start()` and
  are deliberately **not** carried; if one turns out to call it transitively, that is a §10 raise.
- The lockfile path must sit beside the queue (`cfg.paths.data_dir`), not in the repo, or it will
  be scoped to a checkout instead of to an instance.

## 4. Reconciliation  <!-- Part B -->

- **`ops/lifecycle/launcher.py:596-605`** — the gate's comment block asserts it is the
  *"SINGLE-INSTANCE GATE — first, and NOT bypassable by --force"* → **banner: correction.** After
  this plan it is no longer the single-instance *guarantee*; the lock is. Amend the block to say
  the gate is the **diagnostic** layer (it explains *which* run is live) sitting ahead of the
  kernel-held lock, and cite `dn-supervision-and-liveness` §2.6. The behaviour is unchanged — only
  the claim about what enforces exclusivity.
- **`scripts/watch.py`'s module docstring** (`:1-13`) — describes itself as a standalone
  re-ingest loop with no mention that it builds a second supervisor over the shared queue →
  **banner: correction**, carried by Item 5. State the hazard and the lock that now bounds it.
- **`docs/findings/finding-0186.md`** — its open half → **cross-ref: extension.** The builder must
  **not** edit the finding (a builder may not edit an existing finding); record the closure
  evidence in the journal for the orchestrator to apply at seal.

## 5. Write scope

`ops/lifecycle/lock.py` is new and holds the lock primitive alone. `ops/lifecycle/launcher.py`
carries the acquisition site, the bounded drain, and the gate's re-documentation.
`scripts/watch.py` is carried because it is the finding's open half and Item 5 brings it under the
lock. `tests/unit/test_supervisor_lock.py` is new. The four remaining test files are **carried
because they pin the surface this plan moves** — they call `start()`, whose preconditions change.

Deliberately OUT of scope: `scheduler/supervisor.py` (Q1 — `max_ticks` already exists; touching it
is a sign the fix is being done in the wrong place), `scheduler/queue.py` (bp-109 owns it, and the
lock guards the supervisor **role**, not queue writes — CLI enqueues stay lock-free under WAL),
every design note, and every foundation-denylist file.

## 6. Interfaces pinned inline

**The primitive — acquire-or-fail, never acquire-or-wait.** A supervisor that blocks waiting for
the lock is a second supervisor that starts the moment the first dies, which is the failure the
lock exists to deny.

```python
# ops/lifecycle/lock.py
class SupervisorLockHeld(RuntimeError):
    """Another process holds the supervisor role."""

@dataclass
class SupervisorLock:
    path: Path                       # cfg.paths.data_dir / "supervisor.lock" — beside the queue

    def acquire(self) -> None:
        """flock(LOCK_EX | LOCK_NB) held for the process lifetime. Raises SupervisorLockHeld if
        another process holds it. The fd is kept on the instance and never closed except by
        release() or process death — the kernel drops it either way, so NO stale-lock state
        exists and there is nothing to clean up after a crash."""

    def release(self) -> None: ...
    def __enter__(self) -> SupervisorLock: ...
    def __exit__(self, *exc: object) -> None: ...
```

**The call site's exact current form** (`ops/lifecycle/launcher.py:649-656`, the region Item 3
wraps):

```python
                self._components = self.components_factory(self.cfg)
                print(self._components.queue.sweep_orphans(run.id).render())
                self._components.enqueue_catchup()
                self._install_signal_handlers()
                self._serve(max_ticks)
```

**The drain's exact current form** (`ops/lifecycle/launcher.py:675-695`, the region Item 4 edits):

```python
        while not self._stopping and (max_ticks is None or ticks < max_ticks):
            c.supervisor.run()                            # drain runnable jobs at boundaries
            ...
            ticks += 1
            if self.tick_seconds:
                time.sleep(self.tick_seconds)
```

**`Supervisor.run`'s signature — unchanged, already sufficient** (`scheduler/supervisor.py:99`):

```python
    def run(self, *, max_ticks: int | None = None) -> int:
        """Drain the queue cooperatively. Returns the number of jobs dispatched. Stops when
        nothing is runnable (e.g. only heavy jobs remain while the owner is present)."""
```

⚑ **`run()` returns the dispatch count.** That return value is what makes the sleep conditional
(Item 4): sleep only when it returned 0.

## 7. Items

Blast radius: read-only measurement → new isolated module → wiring → the contended script.

### Item 1 — V8: measure `flock` where it will actually run

- **Objective:** the lock's tier-3 claim rests on observation, not on POSIX documentation.
- **Files:** none (a scratchpad script; findings recorded in `journal.md`)
- **Acceptance test:** three observations recorded in the journal with their commands: (a) two
  processes on **APFS under `data/`** — the second's `LOCK_EX|LOCK_NB` fails while the first
  holds; (b) `uv run python -c '<hold the lock>'` — the holder pid **is** the python process, not
  a wrapper (`lsof <lockfile>`); (c) the lock is released on `SIGKILL` of the holder with no
  residue, and a successor acquires immediately.
- **Falsifier:** ⚑ *`uv run` holds the lock from a wrapper process that outlives or precedes
  python.* Then the lock guards the wrong lifetime and the whole mechanism is mis-tiered — §10
  STOP, do not build on it.
- **Invariant(s) it must not violate:** measurement only; nothing is written under `data/` except
  a throwaway lockfile the item deletes.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** none.

### Item 2 — `ops/lifecycle/lock.py`

- **Objective:** an acquire-or-fail file lock exists, tested in isolation.
- **Files:** `ops/lifecycle/lock.py`, `tests/unit/test_supervisor_lock.py`
- **Acceptance test:** in-process, a second `SupervisorLock` on the same path from a **forked
  subprocess** raises `SupervisorLockHeld`; the same object re-acquiring is an explicit error, not
  a silent success; `release()` then re-acquire succeeds; a killed holder frees it.
- **Falsifier:** *a second acquirer in the SAME process succeeds.* `flock` is per-open-file-
  description, so a naïve implementation that re-opens can self-grant — the test must fork, and a
  same-process test alone would pass while the guarantee is absent.
- **Invariant(s) it must not violate:** no busy-wait, no timeout, no retry loop; acquisition is
  non-blocking and terminal.
- **Touches stored data?** No — the lockfile is derived state, not corpus. **Parallelizable?** No.
  **Depends on:** Item 1.

### Item 3 — `start()` acquires the lock, and the gate is re-documented as a diagnostic

- **Objective:** the supervisor role is kernel-held, and the old gate stops claiming to be the
  guarantee.
- **Files:** `ops/lifecycle/launcher.py`, plus the four carried test files as needed
- **Acceptance test:** the lock is acquired **before** `sweep_orphans` (`:653`) and released in
  `_shutdown`; a second `start()` over a live one exits non-zero with a message naming the lock;
  `start --force` **does not** bypass it. The four carried test files pass.
- **Falsifier:** ⚑ *deleting the `acquire()` call leaves the suite green.* This is finding-0187's
  exact failure mode reproduced in a new mechanism — the same standing proof the note cites (§ the
  ladder, tier 5). Plant that mutation and record that it reddens.
- **Invariant(s) it must not violate:** the lock ships **unconditional, never behind a flag** (§4
  of the note: "a mutual-exclusion guarantee behind a flag is a contradiction"); the bp-105
  identity gate is **kept**, not deleted; `recovery` mode still holds the lock (it is a live
  supervisor — `launcher.py:634-646`).
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 2.

### Item 4 — the drain is bounded, and the sleep stops being unconditional

- **Objective:** health, snapshot and housekeeping ticks run at job boundaries again, without
  turning a no-op backlog into a 29-minute crawl.
- **Files:** `ops/lifecycle/launcher.py`
- **Acceptance test:** `_serve` calls `c.supervisor.run(max_ticks=K)`; **and** the `tick_seconds`
  sleep executes only when that call returned 0. A test with N ≫ K queued no-op jobs asserts the
  health tick fires **during** the drain, and that wall-clock is not ≈ N × `tick_seconds`.
- **Falsifier:** ⚑ *no-op drain throughput collapses* — the note's own §2.10 falsifier, grounded
  at `launcher.py:694-695` (Q2). If 1,766 trivial jobs take tens of minutes, this item has traded
  one availability defect for another and must be reverted.
- **Invariant(s) it must not violate:** `scheduler/supervisor.py` is unmodified; a job that
  checkpoint-yields is still dispatched at a boundary, not starved by the bound; `max_ticks` as
  passed to `start()` (the test seam, `:595`) keeps its existing meaning — do not conflate the
  outer loop's bound with the inner drain's.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** none (independent of
  Items 1–3; ordered after them only by blast radius).

### Item 5 — `watch.py` cannot be the second claimant

- **Objective:** finding-0186's open half closes structurally, whatever `watch.py`'s future.
- **Files:** `scripts/watch.py`
- **Acceptance test:** `watch.py` acquires the same `SupervisorLock` before constructing its
  `Supervisor` and exits with a clear message if the daemon holds it; its `supervisor.run()` call
  (`:53`) gains the same bound as Item 4. Running it while the daemon is up exits non-zero
  **without claiming a single row**.
- **Falsifier:** *it acquires the lock but still runs with `active_run_id = None`.* The lock stops
  concurrency; it does not stop a NULL stamp. If `watch.py` is ever the sole supervisor it must
  either call `sweep_orphans` or refuse — a lock-holding NULL-stamping claimant is the same lying
  ledger one step later.
- **Invariant(s) it must not violate:** the script is **not deleted** — V7 is unanswered (Q6) and
  retiring a possibly-used tool on an inference is a §10 raise, not a builder's call.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 2.

## 8. Math carried explicitly

N/A — no mathematical object. `flock` is a kernel primitive; the drain bound is a loop counter.

## 9. Non-goals

- **No worker subprocess, no lease, no escalation, no drain report.** bp-110, bp-111, bp-112.
- **No queue schema change.** bp-109 owns `scheduler/queue.py`.
- **No deletion of `scripts/watch.py`** — V7 unanswered (§3 Q6).
- **No deletion of the bp-105 identity gate** — it is demoted in documentation, kept in code.
- **No lock over queue *writes*.** §2.6 is explicit: CLI enqueues (`palace code-seed`,
  `launcher.py:882-907`) legitimately insert concurrently and stay lock-free under WAL. A lock
  that covers enqueues would break them.
- **No flag.** §4 of the note forbids one here.

## 10. Stop-and-raise conditions

- ⚑ **Item 1's falsifier fires** (the lock is held by a `uv run` wrapper, or APFS advisory locking
  does not hold) ⇒ **STOP.** The mechanism is mis-tiered and the note's §2.6 claim needs revisiting
  by the owner, not a workaround by a builder.
- **The lock would refuse a legitimate start** — e.g. launchd `KeepAlive` restarts faster than the
  predecessor's fd is reaped ⇒ **STOP.** That converts an exclusivity guarantee into a restart
  outage, the same shape as bp-107's brick risk.
- **V7 needs answering to proceed** (a `watch.py` user is discovered, or Item 5 cannot be done
  without retiring it) ⇒ park the criterion with a re-entry condition, file the question, and
  continue with the rest. Never block on the owner.
- **A carried test cannot be made green without weakening an assertion** ⇒ STOP and file. In
  particular `tests/unit/test_restart_trustworthy.py` is bp-105's 24-test evidence base; a
  weakened assertion there is invisible and permanent.
- Any blessing transition — never.

## 11. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| lockfile location | `data_dir / "supervisor.lock"` | an instance runs two data dirs |
| `max_ticks` value K | 64 | Item 4's throughput measurement |
| `watch.py`'s fate | keep, under the lock | V7 — an owner statement on use |
| lease home | not decided here | bp-111 (V9 picks the clock) |

**Rejected alternatives, per row:**

- **Lockfile location.** Rejected: *repo root* — scopes exclusion to a checkout, so two worktrees
  over one `data/` would both start. Rejected: `/tmp` — cleared by the OS, and not co-located with
  the resource it guards.
- **K.** Rejected: *K = 1* — maximal responsiveness, but Q2's arithmetic makes a no-op backlog
  crawl. Rejected: *time-boxed drain* (`run` until T elapsed) — the note offers it as an
  alternative and it is strictly better on paper, but `run()` has no time bound today and adding
  one edits `scheduler/supervisor.py`, which §5 puts out of scope. Re-entry: if a single job
  routinely exceeds the tick budget, the count bound stops helping and the time box is the fix.
- **`watch.py`.** Rejected: *delete it now* — nothing proves it is unused (Q6) and deleting a
  documented operator tool on an inference is out of a builder's authority. Rejected: *leave it
  alone* — it is the finding's open half and the note names it as the route the lock closes.
- **Lease home.** Deliberately not decided here: §2.6 offers "a row in `runs.sqlite` **or** the
  lockfile's mtime", and V9 measures before choosing. Recording the lockfile as a *candidate* is
  why bp-111 depends on this plan.

## 12. Dependency & ordering summary

Items: **1 → 2 → {3, 5}**, with **4 independent** of all of them (it touches only `_serve`'s loop
body). Ordered 1–5 by blast radius, so a builder that stops early has stopped at a safe point.

Against other plans: **no `depends_on`.** Parallelizable with **bp-115** only (disjoint:
`core/models/` + `core/ingest/embed.py`).

⚑ **NOT parallelizable with bp-109**, despite the two plans having disjoint *production* surfaces
(`ops/lifecycle/` here, `scheduler/queue.py` there). Both carry
`tests/unit/test_restart_trustworthy.py` and `tests/integration/test_lifecycle.py`: this plan
because `start()`'s preconditions change, bp-109 because sweep results and row shape change. Two
concurrent worktrees over those files is the finding-0191 shape in miniature, so bp-109 is
sequenced after this plan. **Write_scope is not a partition of the diff** — the test files are the
part a naïve read of the production surfaces misses.

⚑ **`ops/lifecycle/launcher.py` is one of the wave's two contended files** — bp-108, bp-111,
bp-112 and bp-116 all edit it. (The other is `core/kernel/config/loader.py`: bp-110 and bp-115.)
They are strictly sequenced and must **never** be run as concurrent worktrees. That is the
finding-0191 discipline applied at graduation: the contention is named here rather than
discovered at merge.

bp-110 depends on this plan, for two reasons worth stating: the launcher contention above, and
that the worker split's value depends on a loop that is no longer hostage to the backlog (Item 4).
