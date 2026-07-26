#!/usr/bin/env python
"""Run the local vault watcher + incremental re-ingest loop (vault-sync task). From repo root:

    uv run scripts/watch.py

Seals the core first (Invariant 1), then watches the configured vault. On change → a
background `vault_sync` job is enqueued and the supervisor re-ingests through the Phase-1
pipeline (idempotent via content-addressing). Real-time via `watchdog` if installed, else
polling. Ctrl-C to stop.

The watcher is core-side and reaches NO network — only the local filesystem and local stores.
The sync transport (Syncthing/Tailscale) is a SEPARATE process; see docs/runbook.md.

⚑ **THIS SCRIPT IS A SUPERVISOR, and that used to be a hazard.** It does not merely watch: it
builds its own `Supervisor` over the SHARED job queue and claims work from it. Run beside the
palace daemon, that made two claimants on one queue — and worse than contention, because it
never adopted a run id. Every row it claimed was stamped `claimed_by_run = NULL`, and a NULL
stamp is *by definition* reclaimable, so the daemon's next orphan sweep could re-queue or write
FAILED the very jobs this process was mid-flight on: double execution, or a fabricated failure
under a running worker. That is finding-0186's open half.

Two things close it here, and they are different closures for different failure modes:

* **The supervisor lock** (`dn-supervision-and-liveness` §2.6) is acquired before anything else
  is built. If the daemon is up, this script exits non-zero having claimed nothing — the
  exclusion is a kernel fact, not a convention, so it holds however this script is invoked.
* **A real run row.** The lock stops a *second* claimant; it does nothing about the NULL stamp
  when this script is the *only* one. So when it does run, it opens a row in the run ledger and
  sweeps orphans with that id, exactly as `palace start` does. A lock-holding NULL-stamping
  claimant would be the same lying ledger, one step later.

Consequence worth knowing: because it now keeps a run row, `palace status` will show this
process as the live run while it is up, and killing it uncleanly leaves an unclean row, so the
next `palace start` comes up in recovery mode. That is the honest reading of what this script
is — a supervisor — rather than a quiet exception to the accounting.

**Its function is fully subsumed by the daemon**, which builds its own vault watcher
(`build_vault_watcher`, `ops/lifecycle/launcher.py`). Nothing in the repository imports or
invokes this script; whether any human still runs it by hand is unresolved (V7 /
`docs/build-plans/bp-108/plan.md` §3 Q6), which is why it is bounded here rather than deleted.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))  # repo root on path

# noqa: E402 — ruff exempts a bare `sys.path` bootstrap before imports, but not the named
# REPO_ROOT above it, and the name is wanted twice (the bootstrap, and `git_state` in main()).
from core.sealing import seal  # noqa: E402


def main() -> int:
    seal()  # structural egress guard first (Invariant 1)

    from config.loader import get_config
    from core.ingest.sync import build_vault_sync
    from core.models import Registry, TwoSlotLoader
    from core.models.ollama_client import OllamaClient
    from ops.lifecycle.launcher import DEFAULT_DRAIN_MAX_TICKS
    from ops.lifecycle.lock import SupervisorLock, SupervisorLockHeld
    from ops.lifecycle.runs import RunLedger, git_state
    from scheduler.queue import JobQueue
    from scheduler.router import Router
    from scheduler.supervisor import Supervisor
    from scheduler.vault_sync import VAULT_SYNC_KIND, build_vault_watcher, vault_sync_handler

    cfg = get_config()

    # FIRST — before the queue, the loader, or the watcher exist. Nothing may be claimed, swept
    # or even opened until this process is established as the sole supervisor.
    lock = SupervisorLock(cfg.paths.data_dir / "supervisor.lock")
    try:
        lock.acquire()
    except SupervisorLockHeld:
        print(f"refusing to start — another process holds the supervisor lock ({lock.path}).\n"
              "The palace daemon supervises this queue and runs this watcher itself, so there is "
              "nothing for this script to do while it is up. Check with `palace status`; stop it "
              "with `palace stop` if you really want to run the watcher standalone.")
        return 1

    runs = RunLedger(cfg.paths.data_dir / "runs.sqlite")
    commit, dirty = git_state(REPO_ROOT)
    run = runs.open_run(commit_sha=commit, dirty=dirty, pid=os.getpid())
    clean = False
    try:
        queue = JobQueue(cfg.paths.data_dir / "queue.sqlite")
        router = Router(cfg)
        loader = TwoSlotLoader(config=cfg, client=OllamaClient(cfg.ollama), registry=Registry(cfg))
        supervisor = Supervisor(
            queue=queue,
            loader=loader,
            handlers={VAULT_SYNC_KIND: vault_sync_handler(build_vault_sync(cfg))},
        )
        # Adopt the run id BEFORE the first claim — this is what stops every row this process
        # takes from being stamped NULL, and it reclaims anything a previous unclean exit left
        # stranded RUNNING (bp-101, findings 0173/0177).
        print(queue.sweep_orphans(run.id).render())

        watcher = build_vault_watcher(queue, router, cfg)
        backend = watcher.start()
        print(f"run #{run.id}: watching {cfg.vault.path} (backend={backend}); Ctrl-C to stop")
        try:
            while True:
                # The same bounded drain + conditional sleep as the daemon's serve loop (bp-108
                # Item 4). Bounding without the condition would make a backlog of N trivial jobs
                # cost ceil(N/K) sleeps of pure waiting.
                if supervisor.run(max_ticks=DEFAULT_DRAIN_MAX_TICKS) == 0:
                    time.sleep(1.0)
        except KeyboardInterrupt:
            print("\nstopping…")
        finally:
            watcher.stop()
            queue.close()
        clean = True
    finally:
        # Ledger first, then the role — a successor that acquired the lock while this row was
        # still active would sweep it as an orphan.
        runs.mark_stopped(run.id, clean=clean)
        lock.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
