"""Vault sync wired into the scheduler as a background task (vault-sync task).

Pins the scheduler integration: the kind routes to the always-pinned tier (no chat-model
swap), enqueues at BACKGROUND priority, the handler runs the idempotent rescan, and the
watcher's on_change enqueues a job (the trigger path) — all without core importing scheduler.
"""

from __future__ import annotations

from config.loader import get_config
from scheduler.queue import PRIORITY_BACKGROUND, JobQueue
from scheduler.router import Router
from scheduler.vault_sync import (
    VAULT_SYNC_KIND,
    build_vault_watcher,
    enqueue_vault_sync,
    vault_sync_handler,
)


class _FakeReport:
    def __str__(self) -> str:
        return "indexed=1 unchanged=0 tombstoned=0"


class _FakeSync:
    def __init__(self) -> None:
        self.calls = 0

    def rescan(self) -> _FakeReport:
        self.calls += 1
        return _FakeReport()


def test_routes_to_pinned_tier_no_worker_swap():
    cfg = get_config()
    plan = Router(cfg).plan(VAULT_SYNC_KIND)
    assert plan.tier == cfg.pinned_model.tier        # always resident → ensure_tier is a no-op


def test_enqueue_is_background_priority():
    cfg = get_config()
    queue = JobQueue(":memory:")
    job = enqueue_vault_sync(queue, Router(cfg))
    assert job.kind == VAULT_SYNC_KIND
    assert job.tier == cfg.pinned_model.tier
    assert job.priority == PRIORITY_BACKGROUND       # yields to interactive/reactive work


def test_handler_runs_rescan():
    sync = _FakeSync()
    handler = vault_sync_handler(sync)
    msg = handler(object())
    assert sync.calls == 1
    assert "indexed=1" in msg


def test_watcher_on_change_enqueues_a_job():
    cfg = get_config()
    queue = JobQueue(":memory:")
    watcher = build_vault_watcher(queue, Router(cfg), cfg)
    assert queue.depth() == 0
    watcher.on_change()                              # the trigger the FS event would cause
    assert queue.depth() == 1
    assert queue.list()[0].kind == VAULT_SYNC_KIND
