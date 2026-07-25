---
type: finding
id: finding-0170
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - scheduler/queue.py                                 # enqueue() — the bare INSERT
  - scheduler/chat_sync.py                             # build_chat_watcher's unconditional on_change
  - docs/findings/finding-0165.md                      # background starvation — this is its amplifier
  - docs/findings/finding-0169.md                      # the quadratic job that exposed it
ftype: spec-defect
origin_plan: orchestrator
route: builder
resolution: null
---

# The job queue has no enqueue coalescing — idempotent syncs stack without bound

## What

`JobQueue.enqueue()` (`scheduler/queue.py:144`) is a bare `INSERT` with no dedup, no
"is one of this kind already queued?" check, and no coalescing:

```python
def enqueue(self, kind, tier, num_ctx, *, priority=..., payload=None):
    cur = self._conn.execute("INSERT INTO jobs (...) VALUES (...)")
```

The watchers call it unconditionally from `_on_change()` (`scheduler/chat_sync.py:70`), debounced
only by `chat.watch_debounce_s = 0.5`. So whenever the single-writer worker is occupied, identical
idempotent sync jobs accumulate with no upper bound.

Observed on run #35 while `code_backfill` held the worker (finding-0169):

| time | queue depth | `chat_sync` | `vault_sync` |
|---|---|---|---|
| 02:30 (backfill starts) | 13 | 4 | 3 |
| 23:44 EDT (~1 h in) | 1,714 | 855 | 855 |
| 00:07 EDT (daemon killed) | 1,766 | 883 | 883 |

Drain over the final 20 minutes: **3 done, 1 failed**, against 10 enqueued in 10 minutes. Net growth
with the worker pinned is ~1–2 jobs/min, indefinitely.

## Why it matters

Three consequences, in ascending order of seriousness:

1. **Waste.** ~1,760 redundant jobs, each of which will execute as a near-no-op re-sync. At the
   ~2 s each observed in the log, that is roughly an hour of pointless drain after any recovery.
2. **It masks real work.** Queue depth becomes uninformative — you cannot tell a backlog of *work*
   from a backlog of *duplicates*, so the one number an operator checks stops meaning anything.
3. **It is a feedback loop, and the agent is inside it.** The chat watcher watches Claude Code's
   transcript directory. Every tool call an agent makes writes to that directory, fires the watcher,
   and enqueues another `chat_sync`. During this incident, **investigating the queue was growing the
   queue.** Any long agent session with a busy worker inflates the backlog by construction.

Point 3 is the one worth carrying into design: the observer is part of the observed system, and the
sensing loop has positive feedback with no damping.

## The fix (builder-resolvable)

Coalesce at enqueue: for kinds declared idempotent-collapsible (`chat_sync`, `vault_sync`,
`code_sync`, `chat_events`), if a job of that kind is already `queued`, do not insert a second —
optionally bump its `created_at`/priority instead. A partial unique index on
`(kind, state) WHERE state = 'queued'` makes it structural rather than conventional, per the
standing rule that a property is only real when something enforces it.

Care needed for kinds that carry a distinguishing `payload` — collapse must key on
`(kind, payload)`, not `kind` alone, or a payload-bearing job could be silently dropped.

## Re-entry condition

Fold into the same restart as finding-0169 — both must land before `palace up`, since bringing the
daemon back up with the current enqueue path re-starts the accumulation. The existing ~1,766 queued
duplicates should be cleared as part of that restart (they are all idempotent re-syncs; dropping
them loses nothing).

## Routing

`codebase` → builder. Scoped to `scheduler/queue.py` plus the watcher call sites.
