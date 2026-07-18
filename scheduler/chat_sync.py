"""Wire the chat sensor into the scheduler as a background `chat_sync` job (dn-chat-sensor CS-1/3).

The sensor itself lives in `ops/chat_sensor.py` (bp-063 — the model-free φ_chat pipeline over the
local Claude Code transcripts) and its builder `build_chat_sensor(cfg)` is there too; this
scheduler-side module only turns "run the sensor" into a durable background job. So all store
mutation happens on the single supervisor writer (the queue's discipline), exactly like vault_sync.
This mirrors `scheduler/vault_sync.py`, with ONE deliberate difference: the driver-builder is NOT
re-declared here — the launcher builds it from where it lives (`chat_sync_handler(build_chat_sensor
(cfg))`), the same way it builds vault_sync's driver from `core.ingest.sync.build_vault_sync`
(launcher.py:208), never from the scheduler module. (Re-declaring `build_chat_sensor` here would
duplicate the working bp-063 one — see finding-0108.)

`chat_sync` is model-less (the sensor calls no chat model — it reads local files), so it runs on the
always-warm PINNED tier: `ensure_tier` is then a no-op and no worker slot is evicted to run a file
scan. vault_sync gets that tier via `router._PINNED_KINDS`; chat_sync is not registered there (that
file is out of this plan's scope, finding-0108), so `enqueue_chat_sync` pins the job DIRECTLY — the
supervisor dispatches on the job's stored `job.tier` (supervisor.py:71), never re-planning by kind,
so a directly-pinned enqueue is sufficient. It runs at **BACKGROUND** priority (yields to
interactive/reactive work), matching vault_sync and bp-064's `observed → {TROUGH}` lane.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from scheduler.queue import PRIORITY_BACKGROUND, Job, JobQueue
from scheduler.router import Router

if TYPE_CHECKING:  # the sensor is INJECTED into the handler — no runtime ops import needed here
    from ops.chat_sensor import ChatSensor

CHAT_SYNC_KIND = "chat_sync"

Handler = Callable[[Job], "str | None"]


def chat_sync_handler(sensor: ChatSensor) -> Handler:
    def handle(_job: Job) -> str:
        report = sensor.sync()
        return f"chat sync: {report}"
    return handle


def enqueue_chat_sync(queue: JobQueue, router: Router) -> Job:
    """Enqueue one background chat re-ingest. `sync()` is idempotent (a session already in the
    store is frozen/skipped), so duplicate jobs are harmless. Pins the job to the always-warm tier
    directly (chat_sync isn't in `router._PINNED_KINDS`, finding-0108) — a model-less file scan
    must not force a worker load; the supervisor honours the stored `job.tier`."""
    pinned = router.config.pinned_model
    return queue.enqueue(CHAT_SYNC_KIND, pinned.tier, pinned.num_ctx,
                         priority=PRIORITY_BACKGROUND)
