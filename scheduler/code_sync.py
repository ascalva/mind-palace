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


def enqueue_code_backfill(queue: JobQueue, router: Router) -> Job:
    """Enqueue the history backfill. It reuses `code_sync`'s pinned-tier routing (the backfill is
    the same model-less species; `router._PINNED_KINDS` is out of this plan's write_scope, so we
    borrow the sibling's plan rather than register a second pinned kind) but enqueues under
    `CODE_BACKFILL_KIND` so the supervisor dispatches it to the backfill handler. BACKGROUND — it
    yields to interactive work; idempotent, so a duplicate job re-embeds nothing."""
    plan = router.plan(CODE_SYNC_KIND, priority=PRIORITY_BACKGROUND)
    return queue.enqueue(CODE_BACKFILL_KIND, plan.tier, plan.num_ctx, priority=plan.priority)
