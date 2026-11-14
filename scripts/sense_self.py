#!/usr/bin/env python
"""Drive the self sensor (ops/self_sensor.py). From the repo root:

    uv run scripts/sense_self.py    # sync: reconcile the observed stratum vs branch history

Sync semantics subsume both the per-commit hook case (one missing commit) and full-history
backfill — idempotent, oldest first, a missed hook heals on the next run. Stateless: reads
git subprocess output + config paths only (§2.6); no model, no transcript access. Refused while a
reset of the instance is pending (`data/reset.pending`), since the agent observations are a store
the reset rebuilds: the post-commit hook reports a failed sync, and a sync after the reset heals.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ops.self_sensor import build_self_sensor  # noqa: E402


def main() -> int:
    from config.loader import get_config
    from ops.lifecycle.inventory import refusal

    pending = refusal(get_config(), "the self sensor's sync")   # a pending reset refuses writers
    if pending is not None:
        print(pending)
        return 1
    print(build_self_sensor().sync())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
