---
type: finding
id: finding-0186
status: routed
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/audits/ops-wave-2026-07-25.md
  - scheduler/queue.py
  - ops/lifecycle/launcher.py
ftype: blocker
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# `start --force` sweeps a still-live run's in-flight jobs: double execution and false failures

## What
`sweep_orphans` reclaims every RUNNING row whose `claimed_by_run != active_run_id`.
Its safety argument (`scheduler/queue.py:360-362`) establishes only that a run will not
eat its OWN rows; it silently equates "stamped by a different run" with "stamped by a
DEAD run". Nothing enforces the missing premise: `Launcher.start()` reads
`last_was_clean()` (a ledger predicate) and never probes `_pid_alive(prev.pid)`, while
`reset()` performs exactly that probe at `launcher.py:1128`.

Reproduced independently by TWO auditors (bp-101 and SEAMS) from disjoint diffs with
journals withheld:

```
run A (id 10, LIVE) claimed: [(1,vault_sync,running,10), (2,research,running,10)]
run B sweeps with id 11 -> OrphanSweep(requeued=(1,), failed=(2,))
  job 1: state=queued, claimed_by_run=None   <- run A still executing it
  job 2: state=failed, error='orphaned by unclean exit of run #10'
```

Two reachable routes: `scripts/watch.py:39-47` builds a second `Supervisor` on the
shared queue with `active_run_id=None` (so every row it claims is NULL-stamped, and the
sweep's own safety argument is false for it); and `palace start --force`, which has no
single-instance guard — and which `launcher.py:528-529` PRINTS as the recovery remedy.

## Why it matters
This is bp-101's own §10 STOP condition — "a reclaim that races a live worker is worse
than the orphan it fixes" — and it shipped un-stopped, because the test asserts a
weaker proposition than the falsifier states. For non-idempotent kinds the live job is
written FAILED with a fabricated cause under the running worker, then flipped DONE: a
lying ledger. Before `be225fd` a second instance was a contention bug; after it, a
second instance actively rewrites the first one's rows.

The one-line fix (refuse, or skip the sweep, when `prev.active and _pid_alive(prev.pid)`,
reusing `reset()`'s check) is clear, but the DESIGN question is the owner's: should
`start` refuse outright, or sweep-but-not-start? Hence orchestrator routing.

## Re-entry condition
Blocks nothing on a single-supervisor start. Until ruled on: do NOT `start --force`
over a live supervisor, and do NOT run `scripts/watch.py` against the shared queue
concurrently. Re-entry: owner rules on refuse-vs-skip, then a plan owns the guard.

## Owner ruling — 2026-07-25

**`start` refuses outright.** Verbatim: *"the start should refuse outright if there is
any potential for an issue to occur, it is the system deeming an unrunable state, which
helps us not shoot ourselves in the foot."*

Fail-closed. `--force` must NOT bypass the guard — it overrides *preflight*, not
*safety*. The recovery message at `launcher.py:528-529`, which currently prints
`start --force` as the remedy, must instead direct the operator to `palace stop`.

### The trap the ruling must survive (surfaced at ruling time, not discovered later)

`_pid_alive` is pure pid-EXISTENCE (`os.kill(pid, 0)`) and deliberately reports a
foreign owner as ALIVE — an explicit passing test,
`test_pid_alive_treats_a_foreign_owner_as_ALIVE`. After an unclean exit the OS may
recycle the dead supervisor's pid to an unrelated process. A fail-closed `start` keyed on
existence alone would then refuse **forever**, and under launchd `KeepAlive` that is a
self-inflicted brick — the system correctly deeming itself unrunnable, for a false reason,
with `--force` (the very flag being closed) as the only escape.

Resolution: liveness must be **identity-checked**. A process created BEFORE its own run
row cannot be that run's supervisor. `psutil>=5.9` is already a dependency
(`pyproject.toml:11`) with a §2.5 typedshim, so `Process(pid).create_time()` compared
against `run.started_at` needs no new dependency and no subprocess.

**On ambiguity, refuse** — that is the ruling applied. The recycled-pid carve-out fires
only when identity is *positively disproven*.

Implementation: **bp-105 Item 2** (`docs/build-plans/bp-105/plan.md`), with the
recycled-pid case as a required named falsifier, not an afterthought.
