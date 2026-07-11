"""Wire the vault watcher + incremental re-ingest into the scheduler (vault-sync task).

The watcher (core) only signals; this scheduler-side module turns that signal into a durable
background `vault_sync` job and provides the handler that runs the idempotent re-ingest. So
all store mutation happens on the single supervisor writer (the queue's discipline), and the
core watcher stays free of any scheduler import (clean layering: scheduler depends on core,
never the reverse).

`vault_sync` is routed to the **pinned** tier (the router): it needs no chat model — it calls
the embedder directly — so making it "resident" is a no-op and the worker slot is never
evicted. It runs at **BACKGROUND** priority (yields to interactive/reactive work) but is NOT
in HEAVY_TIERS, so a note saved mid-session is re-ingested promptly rather than waiting for a
trough (the owner may want to query what they just wrote).
"""

from __future__ import annotations

from collections.abc import Callable

from config.loader import Config
from core.ingest.sync import VaultSync
from core.ingest.watch import VaultWatcher
from scheduler.queue import PRIORITY_BACKGROUND, Job, JobQueue
from scheduler.router import Router

VAULT_SYNC_KIND = "vault_sync"

Handler = Callable[[Job], "str | None"]


def vault_sync_handler(sync: VaultSync) -> Handler:
    def handle(_job: Job) -> str:
        report = sync.rescan()
        return f"vault sync: {report}"
    return handle


def enqueue_vault_sync(queue: JobQueue, router: Router) -> Job:
    """Enqueue one background re-ingest. Coalescing happens upstream (the watcher debounce);
    duplicate jobs are harmless because `rescan()` is idempotent."""
    plan = router.plan(VAULT_SYNC_KIND, priority=PRIORITY_BACKGROUND)
    return queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority)


def build_vault_watcher(
    queue: JobQueue, router: Router, config: Config | None = None
) -> VaultWatcher:
    """A watcher whose on_change enqueues a background vault_sync job. Call `.start()` to run.

    The supervisor must have the `vault_sync` handler registered (see `vault_sync_handler`) to
    actually process the enqueued jobs."""
    from config.loader import get_config

    cfg = config or get_config()

    def _on_change() -> None:
        enqueue_vault_sync(queue, router)

    return VaultWatcher(
        vault=cfg.vault.path,
        on_change=_on_change,
        debounce_s=cfg.vault.watch_debounce_s,
        poll_interval_s=cfg.vault.watch_poll_interval_s,
    )
