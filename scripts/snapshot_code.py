#!/usr/bin/env python
"""Snapshot the code's structure at a commit (ops/code_snapshot.py). From the repo root:

    ./.venv/bin/python scripts/snapshot_code.py              # snapshot HEAD
    ./.venv/bin/python scripts/snapshot_code.py <rev>        # snapshot a specific commit
    ./.venv/bin/python scripts/snapshot_code.py --backfill   # every commit on the branch

Stdlib only (git + ast + sqlite) — no models, no embeddings, no corpus writes. Installed as a
non-blocking post-commit hook via `git config core.hooksPath .githooks`. Idempotent by SHA.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from ops.code_snapshot import backfill, open_snapshot_db, snapshot_commit  # noqa: E402


def main(argv: list[str]) -> int:
    db = open_snapshot_db(REPO / "data" / "code_snapshots.sqlite")
    if "--backfill" in argv:
        print(f"code-snapshot: backfilled {backfill(db, REPO)} commit(s)")
        return 0
    rev = argv[0] if argv else "HEAD"
    sha = snapshot_commit(db, REPO, rev)
    print(f"code-snapshot: {'recorded ' + sha[:12] if sha else 'already recorded — no-op'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
