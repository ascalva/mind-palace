#!/usr/bin/env python
"""Run the local vault watcher + incremental re-ingest loop (vault-sync task). From repo root:

    uv run scripts/watch.py

Seals the core first (Invariant 1), then watches the configured vault. On change → a
background `vault_sync` job is enqueued and the supervisor re-ingests through the Phase-1
pipeline (idempotent via content-addressing). Real-time via `watchdog` if installed, else
polling. Ctrl-C to stop.

The watcher is core-side and reaches NO network — only the local filesystem and local stores.
The sync transport (Syncthing/Tailscale) is a SEPARATE process; see docs/runbook.md.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal


def main() -> int:
    seal()  # structural egress guard first (Invariant 1)

    from config.loader import get_config
    from core.ingest.sync import build_vault_sync
    from core.models import Registry, TwoSlotLoader
    from core.models.ollama_client import OllamaClient
    from scheduler.queue import JobQueue
    from scheduler.router import Router
    from scheduler.supervisor import Supervisor
    from scheduler.vault_sync import VAULT_SYNC_KIND, build_vault_watcher, vault_sync_handler

    cfg = get_config()
    queue = JobQueue(cfg.paths.data_dir / "queue.sqlite")
    router = Router(cfg)
    loader = TwoSlotLoader(config=cfg, client=OllamaClient(cfg.ollama), registry=Registry(cfg))
    supervisor = Supervisor(
        queue=queue,
        loader=loader,
        handlers={VAULT_SYNC_KIND: vault_sync_handler(build_vault_sync(cfg))},
    )

    watcher = build_vault_watcher(queue, router, cfg)
    backend = watcher.start()
    print(f"watching {cfg.vault.path} (backend={backend}); Ctrl-C to stop")
    try:
        while True:
            supervisor.run()          # drain any enqueued vault_sync jobs
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nstopping…")
    finally:
        watcher.stop()
        queue.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
