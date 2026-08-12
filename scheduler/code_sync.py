"""Wire the code embed lane into the scheduler as a background `code_sync` job (bp-092/CI-1).

The lane itself (`core/ingest/code_corpus.py`) is a pure ingest entry point; this scheduler-side
module turns "sync the code corpus" into a durable background job, so all store mutation stays on
the single supervisor writer (the queue's discipline), exactly like `vault_sync`/`chat_sync`.

Same SPECIES as vault_sync: `code_sync` needs no CHAT model — it calls the embedder directly — so
it routes to the always-warm PINNED tier (`router._PINNED_KINDS`), making `ensure_tier` a no-op so
no worker slot is evicted, and runs at **BACKGROUND** priority (yields to interactive/reactive
work). The memory ceiling (non-negotiable #8) is enforced by the loader on each embed call, and
BACKGROUND priority keeps the seed from running beside a slot-2 heavyweight — the deploy-vs-ingest
race is the recorded warning (note §2.7-2). No daemon restart: the lane is not a resident.

Deliberately NOT auto-wired into `build_components` housekeeping — the lane is OFF by default
(`[code_ingest].enabled`, note §2.7); wiring the enqueue into the daemon is a later, owner-visible
step. The seed run is `sync()` on an empty store (every HEAD blob embedded, once).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from scheduler.queue import PRIORITY_BACKGROUND, Job, JobQueue
from scheduler.router import Router

if TYPE_CHECKING:  # the sync driver is INJECTED into the handler — no runtime core import here
    from core.ingest.code_corpus import CodeCorpusSync

CODE_SYNC_KIND = "code_sync"
CODE_BACKFILL_KIND = "code_backfill"     # the history backfill (bp-099) — sibling of code_sync
CODE_REBUILD_KIND = "code_rebuild"       # the D7 atom+membership rebuild (bp-153) — checkpointed

Handler = Callable[[Job], "str | None"]


def code_sync_handler(sync: CodeCorpusSync) -> Handler:
    def handle(_job: Job) -> str:
        report = sync.sync()
        return f"code sync: {report}"
    return handle


def enqueue_code_sync(queue: JobQueue, router: Router) -> Job:
    """Enqueue one background code re-sync (or the seed). `sync()` is idempotent + blob-sha keyed
    (an unchanged file re-embeds nothing), so duplicate jobs are harmless. `code_sync` is in
    `router._PINNED_KINDS`, so it plans onto the always-warm tier; enqueued at BACKGROUND so a
    model-less-tier ingest yields to interactive work."""
    plan = router.plan(CODE_SYNC_KIND, priority=PRIORITY_BACKGROUND)
    return queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority)


def code_backfill_handler(sync: CodeCorpusSync, db_path: Path, repo: Path) -> Handler:
    """The history-backfill job (dn-temporal-code-corpus D1/D4, bp-099): embed every ledger version
    (idempotent — already-embedded digests are skipped) AND capture the first-parent commit diffs
    that thread the supersession chains (D5). Both ride ONE job so the substrate lands together; the
    store write stays on the supervisor (single-writer). Same species as `code_sync` (model-less,
    pinned tier, BACKGROUND) — it opens the snapshots ledger itself, mirroring how `code_sync`'s
    injected `CodeCorpusSync` eagerly opens the vector store."""
    def handle(_job: Job) -> str:
        from ops.code_lineage import capture_commit_diffs, ledger_commits, ledger_versions
        from ops.code_snapshot import open_snapshot_db
        db = open_snapshot_db(db_path)
        try:
            report = sync.backfill(ledger_versions(db))
            n_commits = capture_commit_diffs(db, repo, ledger_commits(db))
        finally:
            db.close()
        return f"code backfill: {report}; commit_diffs+={n_commits} commits"
    return handle


def code_rebuild_handler(sync: CodeCorpusSync, db_path: Path, queue: JobQueue, *,
                         capture_budget_s: float = 60.0,
                         rebuild_budget_s: float = 120.0) -> Handler:
    """The D7 rebuild (dn-vector-membership-store, bp-153) as a CHECKPOINTED background job.

    This is the first handler in the system to use the queue's `checkpoint`/resume protocol, and it
    is the one the protocol was built for: the same lane wedged on 2026-07-25 because the whole
    history rode one unbounded job (`code_sync` 300246, with 1,766 jobs queued behind it), and D7's
    answer is slices with resume tokens and a per-slice time budget — never a monolith, and never a
    daemon stop.

    One dispatch runs ONE slice. If work remains, the handler persists its resume token and
    re-queues itself through `queue.checkpoint`, which also CLEARS the lease — so a yielded row
    reads as waiting rather than as an orphan, and the next `claim` stamps a fresh per-batch
    deadline (the shape §2.10 requires: "a healthy 14-hour backfill" must not die at hour N on a
    per-job deadline). The supervisor completes the job only when it is still RUNNING after the
    handler returns, so returning after a checkpoint yields rather than finishes.

    ⚑ It NEVER calls `CodeCorpusSync.backfill` — the old duplicated backfill is 52,755 embeds
    against 22,502 atoms, 2.34× measured waste (D7), and this whole plan exists to not pay it."""
    def handle(job: Job) -> str | None:
        from ops.code_rebuild import rebuild_step
        from ops.code_snapshot import open_snapshot_db
        db = open_snapshot_db(db_path)
        try:
            step = rebuild_step(sync, db, token=job.checkpoint,
                                capture_budget_s=capture_budget_s,
                                rebuild_budget_s=rebuild_budget_s)
        finally:
            db.close()
        if not step.done:
            queue.checkpoint(job.id, step.token or "")
        return f"code rebuild [{step.phase}]: {step.message}"
    return handle


def enqueue_code_rebuild(queue: JobQueue, router: Router) -> Job:
    """Enqueue the D7 rebuild. Same pinned-tier, BACKGROUND species as its two siblings (it is a
    model-less embed lane), and idempotent in the strong sense: every phase converges, so a
    duplicate job re-derives at worst and re-lands nothing."""
    plan = router.plan(CODE_SYNC_KIND, priority=PRIORITY_BACKGROUND)
    return queue.enqueue(CODE_REBUILD_KIND, plan.tier, plan.num_ctx, priority=plan.priority)


def enqueue_code_backfill(queue: JobQueue, router: Router) -> Job:
    """Enqueue the history backfill. It reuses `code_sync`'s pinned-tier routing (the backfill is
    the same model-less species; `router._PINNED_KINDS` is out of this plan's write_scope, so we
    borrow the sibling's plan rather than register a second pinned kind) but enqueues under
    `CODE_BACKFILL_KIND` so the supervisor dispatches it to the backfill handler. BACKGROUND — it
    yields to interactive work; idempotent, so a duplicate job re-embeds nothing."""
    plan = router.plan(CODE_SYNC_KIND, priority=PRIORITY_BACKGROUND)
    return queue.enqueue(CODE_BACKFILL_KIND, plan.tier, plan.num_ctx, priority=plan.priority)
