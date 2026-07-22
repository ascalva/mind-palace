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
from typing import TYPE_CHECKING

from scheduler.queue import PRIORITY_BACKGROUND, Job, JobQueue
from scheduler.router import Router

if TYPE_CHECKING:  # the sync driver is INJECTED into the handler — no runtime core import here
    from core.ingest.code_corpus import CodeCorpusSync

CODE_SYNC_KIND = "code_sync"

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
