---
type: finding
id: finding-0173
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - scheduler/queue.py                                 # no reclaim/lease on RUNNING rows
  - docs/findings/finding-0171.md                      # the kill that orphaned the row
  - docs/findings/finding-0172.md                      # status trusts the orphan
ftype: spec-defect
origin_plan: orchestrator
route: builder
resolution: null
---

# A killed worker orphans its `running` job row — no lease, no reclaim, no requeue

## What

When the daemon dies without closing a job — SIGKILL, crash, power loss — the job's row stays
`state = 'running'` forever. There is no lease, no heartbeat, no startup reclaim pass, and no
requeue. Grepping `scheduler/queue.py` and `ops/lifecycle/launcher.py` for `reclaim|requeue|stale`
returns one unrelated hit (a `reset` docstring).

Observed after the 2026-07-25 `kill -9` of run #35:

```
running rows: [{'id': 300246, 'kind': 'code_sync', 'started_at': '2026-07-25T03:45:07'}]
```

Nothing alive is running job 300246. It will remain `running` until a `palace reset` wipes the
stale queue — a heavy, corpus-scoped operation wildly out of proportion to the problem.

## Why it matters

- **The work is silently dropped.** A job interrupted mid-flight is neither completed nor retried.
  Here it is benign (`code_sync` is idempotent and the catch-up probe re-derives the same work),
  but the queue offers no guarantee of that in general — a payload-bearing job would simply vanish.
- **It corrupts the queue's own accounting.** `1 running` is reported to `status` and to any future
  operator as though a worker were busy. Combined with finding-0172's missing liveness check, the
  system will describe itself as actively working when nothing is running at all.
- **It compounds the recovery story.** Recovery mode exists as the fail-safe for an unclean exit
  (cleared by `start --force`), but it acts at the *run* level. The *job* level has no equivalent,
  so a clean-looking recovered run can still carry orphaned rows from the run that died.

## The fix (builder-resolvable)

On supervisor start, before claiming any work: sweep rows in `running` whose owning run is no longer
active and either requeue them (idempotent kinds) or mark them `failed` with an explicit
`error = 'orphaned by unclean exit of run #N'` (payload-bearing kinds). Prefer an explicit
`claimed_by_run` column over inference so the sweep is exact rather than heuristic.

A lease/heartbeat column would be stronger still — it makes orphan detection work for a hung worker
that has not exited, not just a dead one — and it pairs naturally with finding-0171's job-budget
enforcement. Consider designing them together.

## Re-entry condition

Fold into the finding-0169/0170 restart: the sweep must exist (or job 300246 must be cleared by
hand) **before** `palace up`, so the recovered daemon does not start with a phantom running job.

## Routing

`codebase` → builder. Scoped to `scheduler/queue.py` and the supervisor's startup path.
