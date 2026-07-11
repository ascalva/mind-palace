#!/usr/bin/env python
"""Drive the code-sensor agent (ops/code_sensor.py). From the repo root:

    uv run scripts/snapshot_code.py    # sync: reconcile ledger vs branch history

Sync semantics subsume both the per-commit hook case (one missing commit) and backfill
(all missing commits) — idempotent, oldest first, a missed hook heals on the next run.
Model-less: the agent holds git-read, ledger-write, attest, and nothing else.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ops.code_sensor import build_code_sensor  # noqa: E402


def main() -> int:
    print(build_code_sensor().sync())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
