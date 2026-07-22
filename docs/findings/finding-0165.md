---
type: finding
id: finding-0165
status: open
created: 2026-07-22
updated: 2026-07-22
links:
  - scheduler/code_sync.py                             # the long-running BACKGROUND job class
  - core/ingest/watch.py                               # DirectoryWatcher poll-enqueue cadence
  - docs/build-plans/bp-099/plan.md                    # the backfill amplifies this (hours-long job)
  - scheduler/queue.py                                 # checkpoint support exists (job resumability)
ftype: discovery         # observed live during the first code seed
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Long-running BACKGROUND jobs starve the pinned-tier queue; poll-enqueues pile up behind them

## What (observed live, 2026-07-22, during the first code seed)

~35 minutes into the first `code_sync` seed (a single job that embeds all HEAD `.py` — ran ~75min
total), the queue held **368 chat_sync + 368 vault_sync** queued jobs, oldest 35m — one pair every
~5.7s, matching the watchers' `watch_poll_interval_s = 5.0` fallback cadence (+ overhead). The
single pinned-tier worker was occupied by `code_sync` the whole time, so every poll-enqueue
accumulated behind it. Both watchers appear to enqueue on effectively every poll tick while a
long job runs (this live session writes transcripts continuously; the equal counts suggest
enqueue-per-poll rather than change-detection gating — worth a look on its own).

Benign TODAY: jobs are idempotent no-ops when nothing changed, `0 failed` lifetime, and the queue
self-drains once the long job completes. Duplicate-enqueue-harmless is a recorded design stance.

## Why it matters

**bp-099's history backfill makes the long-job case the normal case:** ~1,542 versions ≈ 6× the
seed ≈ multiple HOURS holding the pinned-tier worker — accumulating thousands of queued no-ops,
delaying every other background lane (chat ingest freshness, vault reconcile) by the job's full
duration, and making `palace queue` unreadable. Also the §2.7-2 deploy-vs-ingest race widens: a
deploy's drain-wait now sits behind an hours-long in-flight job boundary.

## Candidate directions (for the fix session — not decided here)

1. **Chunked long jobs:** the queue already supports `checkpoint(job_id, token)` — the backfill
   (and seed) can process N versions per claim, checkpoint, and RE-ENQUEUE itself, yielding the
   worker between slices so other background lanes interleave. Cheapest structural fix; fits the
   existing queue contract.
2. **Enqueue dedup / coalescing:** skip enqueue when an identical (kind, state=queued) job already
   waits — collapses the 368s to 1. Small, surgical; keeps duplicate-harmless semantics as
   backstop rather than steady-state.
3. **Watcher gating audit:** confirm whether DirectoryWatcher's poll path enqueues on every tick
   regardless of change detection (the equal 368/368 counts hint yes) — if so that is its own
   small defect.

(1)+(2) compose; (1) is the one that matters for bp-099's backfill.

## Decision at the bp-099 merge (orchestrator, low-stakes, logged — 2026-07-22)

The one-time backfill ships **un-sliced** (accepted): it is a single historical catch-up, the
pileup is idempotent no-ops that self-drain, and slicing machinery was out of bp-099's scope. The
live observation strengthened the case for the structural fix, though — at seed-hour-one the pileup
had grown to **621+621**, and the un-deployed seed is exactly the job class at issue. The
STRUCTURAL fix stays owed: the composer is already born-sliced by design
(dn-integrator-densification D5, `compose_max_per_pass`), and directions (1)/(2)/(3) remain open
for `code_sync`/`code_backfill`/the watchers as their own small plan.

## Re-entry condition

Before or with the bp-099 seal/deploy: decide whether the backfill ships sliced (direction 1) or
the pileup is accepted for the one-time backfill run. Direction 2/3 can follow as a small plan.

## Routing

`discovery` → orchestrator. Overlaps bp-099's write_scope (scheduler/code_sync.py) — coordinate
with that build's merge; do not fork a parallel edit of the same surface while its builder runs.
