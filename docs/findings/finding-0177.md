---
type: finding
id: finding-0177
status: resolved
created: 2026-07-25
updated: 2026-07-26
links:
  - scheduler/queue.py                                 # JobQueue.sweep_orphans — built, public, UNCALLED
  - ops/lifecycle/launcher.py                          # the call site owed (bp-102 owns this file)
  - docs/build-plans/bp-101/plan.md                    # §3 Q6 + §7 Item 2 hand-off
  - docs/findings/finding-0173.md                      # the orphan defect this closes
  - docs/findings/finding-0172.md                      # status trusts the orphan
ftype: spec-defect
origin_plan: bp-101
route: builder
resolution: resolved — `be225fd` wired it: `QueueLike` declares `sweep_orphans` (`launcher.py:83-89`) and it is called at `:721`, before catchup and signal handlers
---

# The orphan sweep is built but not wired — `sweep_orphans` has no caller (hand-off to bp-102)

> **Triage 2026-07-26 (session-52) — CLOSED on evidence.** This finding was routed to `builder` and the fix landed, but nobody flipped it, so it has been inflating the open backlog. Closed here as bookkeeping, not as an orchestrator resolution of builder work — the citation in `resolution:` is the code or commit that contradicts the finding as filed. It was one of **10 stale-open** builder findings found this sweep (against **13 orphaned** ones that stay open); the lane's missing mechanism is **finding-0209**.
>
> **Residual, recorded not lost:** ⚑ That call site is itself finding-0197 (unguarded, pre-signal-handler) — still OPEN and orphaned; see finding-0209.

## What

bp-101 Item 2 shipped `JobQueue.sweep_orphans(active_run_id) -> OrphanSweep`
(`scheduler/queue.py`), tested against the live orphan's fixture (job 300246) and against the
double-execution falsifier. **Nothing calls it.** The call site is in `ops/lifecycle/launcher.py`,
which bp-101's write_scope deliberately excludes (bp-102 owns that file), so the switch is handed
over here rather than skipped — wiring-is-part-of-finishing.

The mechanical result today: `palace up` still comes up with job 300246 stuck in `running`, and a
future `kill -9` still strands its row. The queue can now heal itself; the supervisor has not been
told to ask it to.

## The wiring owed — two lines, both in `ops/lifecycle/launcher.py`

1. **Widen the `QueueLike` Protocol** (`launcher.py:56-60`), which today declares only `close()`:

   ```python
   class QueueLike(Protocol):
       def close(self) -> None: ...
       def sweep_orphans(self, active_run_id: int) -> object: ...   # bp-101 / finding-0173
   ```

2. **Call it at supervisor start, BEFORE the first `claim()`** — in `Launcher.start()`, in the
   non-recovery branch, immediately after `self._components = self.components_factory(self.cfg)`
   and before `self._components.enqueue_catchup()` (`launcher.py:501-502`):

   ```python
   print(self._components.queue.sweep_orphans(run.id).render())
   ```

   `run` is already in scope (`launcher.py:485`) and `run.id` is exactly the `runs.id` the column
   references. `OrphanSweep.render()` returns `"orphan sweep: nothing stranded"` on the normal
   path, so the start banner stays quiet when nothing was stranded.

### Why that position, precisely

`sweep_orphans` is safe **because** it runs before the run's first claim, and for two independent
reasons documented on the method:

* run ids are `INTEGER PRIMARY KEY AUTOINCREMENT` (`ops/lifecycle/runs.py:28`), so a freshly-opened
  run's id cannot already appear on any row;
* the guard is positive — a row is reclaimed only when `claimed_by_run != active_run_id`, so work
  this run actually claimed (stamped by `claim()`) is never taken back.

The call also **adopts** the run id into the queue handle, which is what makes every subsequent
`claim()` stamp `claimed_by_run`. Without the call, the stamp stays NULL and `running` means only
what it meant before this plan — so the wiring is not cosmetic: it is what turns the column on.

Whether the **recovery** branch (`launcher.py:495-499`) should also sweep is a judgement for
bp-102/the owner. The conservative reading is **no**: recovery mode deliberately does not claim
work, and leaving the stranded rows visible is the point of the mode. Recorded, not decided here.

## Why it matters

- Job 300246 stays `running` forever until someone sweeps or a `palace reset` wipes the queue — a
  corpus-scoped operation wildly out of proportion (finding-0173).
- finding-0172's self-report defect persists: `status` will keep saying a worker is busy when
  nothing is running.
- A capability that exists but is never invoked is the exact failure mode the
  wiring-is-part-of-finishing rule was written for. It is recorded as owed, with the diff spelled
  out, so the merge cannot lose it.

## Re-entry condition

Apply the two lines as part of bp-102 (or at the bp-101/bp-102 merge) — **before `palace up`**, so
the recovered daemon does not start with a phantom running job. Verification after wiring: start
the daemon and confirm the banner prints `orphan sweep: requeued 1 [300246]` on the first start and
`orphan sweep: nothing stranded` on the second.

## Routing

`codebase` → builder (bp-102). No design question; the interface is settled and tested, only the
call site is out of bp-101's write_scope.
