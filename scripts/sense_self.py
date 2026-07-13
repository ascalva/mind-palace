#!/usr/bin/env python
"""Drive the self sensor (ops/self_sensor.py). From the repo root:

    uv run scripts/sense_self.py    # sync: reconcile the observed stratum vs branch history

Sync semantics subsume both the per-commit hook case (one missing commit) and full-history
backfill — idempotent, oldest first, a missed hook heals on the next run. Stateless: reads
git subprocess output + config paths only (§2.6); no model, no transcript access.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ops.self_sensor import build_self_sensor  # noqa: E402


def main() -> int:
    print(build_self_sensor().sync())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
