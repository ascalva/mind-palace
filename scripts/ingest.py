#!/usr/bin/env python
"""(Re)build the knowledge base from the configured vault. Run from the repo root:

    uv run scripts/ingest.py

Seals the core (Invariant 1) before doing any work, then ingests the configured Logseq/
markdown vault into the raw store + LanceDB vectors. Vectors rebuild from raw each run.

Refuses while a daemon run is live, through the launcher's `_refuse_if_live`, as the on-demand
verbs do: a rebuild starts with `VectorStore.reset()`, which drops the table and every relation the
daemon writes, a write that commutes with none of the daemon's (dn-ingest-door §9; DOR-12's one
writer). Stop the daemon first.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal


def main() -> int:
    seal()  # structural egress guard first (Invariant 1)
    from ops.lifecycle import launcher

    if launcher.build_launcher()._refuse_if_live("ingest"):     # the daemon is the one writer
        return 1
    from core.ingest import run

    summary = run.run_ingest()
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
