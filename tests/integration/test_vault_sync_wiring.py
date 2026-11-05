"""Vault sync wired into the scheduler as a background task (vault-sync task).

Pins the scheduler integration: the kind routes to the always-pinned tier (no chat-model
swap), enqueues at BACKGROUND priority, the handler runs the library script `sync_vault` through
the door's writer (dn-door-language §E7), and the watcher's on_change enqueues a job (the trigger
path) — all without core importing scheduler.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

from config.loader import get_config
from scheduler.door import library_handler
from scheduler.queue import PRIORITY_BACKGROUND, Job, JobQueue
from scheduler.router import Router
from scheduler.vault_sync import VAULT_SYNC_KIND, build_vault_watcher, enqueue_vault_sync
from tests.fixtures.door import palace_at, write_file


def test_routes_to_pinned_tier_no_worker_swap():
    cfg = get_config()
    plan = Router(cfg).plan(VAULT_SYNC_KIND)
    assert plan.tier == cfg.pinned_model.tier        # always resident → ensure_tier is a no-op


def test_enqueue_is_background_priority():
    cfg = get_config()
    queue = JobQueue(Path(":memory:"))
    job = enqueue_vault_sync(queue, Router(cfg))
    assert job.kind == VAULT_SYNC_KIND
    assert job.tier == cfg.pinned_model.tier
    assert job.priority == PRIORITY_BACKGROUND       # yields to interactive/reactive work


def test_the_handler_runs_the_sync_vault_script(tmp_path):
    p = palace_at(tmp_path)
    write_file(p.vault, "pages/a.md", "# A\n\nalpha\n")
    handler = library_handler(p.cfg, "sync_vault", [{}], stores=lambda: p.stores)
    # The handler ignores its Job argument entirely -- a bare placeholder is the right test
    # double; the cast says "this never matters here."
    msg = handler(cast(Job, object()))
    assert msg is not None and "'landed': 1" in msg
    (entry,) = p.stores.catalog.active_entries()
    assert entry.source_path == str(p.vault / "pages" / "a.md")
    assert "'unchanged': 1" in str(handler(cast(Job, object())))      # idempotent


def test_watcher_on_change_enqueues_a_job():
    cfg = get_config()
    queue = JobQueue(Path(":memory:"))
    watcher = build_vault_watcher(queue, Router(cfg), cfg)
    assert queue.depth() == 0
    watcher.on_change()                              # the trigger the FS event would cause
    assert queue.depth() == 1
    assert queue.list()[0].kind == VAULT_SYNC_KIND
