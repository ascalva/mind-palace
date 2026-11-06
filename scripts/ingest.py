#!/usr/bin/env python
"""(Re)build the knowledge base from the configured vault. Run from the repo root:

    uv run scripts/ingest.py

Seals the core (Invariant 1) before doing any work, then ingests the configured Logseq/
markdown vault into the raw store + LanceDB vectors. Vectors rebuild from raw each run.

Refuses while a daemon run is live, through the launcher's `_refuse_if_live`, as the on-demand
verbs do: a rebuild starts with `VectorStore.reset()`, which drops the table and every relation the
daemon writes, a write that commutes with none of the daemon's (dn-ingress §9; ING-12's one
writer). Stop the daemon first. The check reads the run ledger and then acts, so the rebuild also
holds the supervisor lock for its whole duration (acquire-or-fail, `ops/lifecycle/lock.py`): a
daemon that starts after the check finds the lock taken and refuses to start, and one that holds
it already refuses the rebuild.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal


def main() -> int:
    seal()  # structural egress guard first (Invariant 1)
    from ops.lifecycle import launcher
    from ops.lifecycle.lock import SupervisorLock, SupervisorLockHeld

    lnch = launcher.build_launcher()
    if lnch._refuse_if_live("ingest"):                           # the daemon is the one writer
        return 1
    from core.ingest import run

    try:
        with SupervisorLock(lnch.cfg.paths.data_dir / "supervisor.lock"):
            summary = run.run_ingest()
    except SupervisorLockHeld:
        print("refusing ingest: another process holds the supervisor lock; stop the daemon "
              "first.")
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
