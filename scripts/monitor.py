#!/usr/bin/env python
"""Run the edge monitor — the dashboard + chat surface (Zone B). From the repo root:

    ./.venv/bin/python scripts/monitor.py            # uses [monitor] from config

Palace spawns this as a SUPERVISED CHILD PROCESS when `[monitor] enabled = true`; you can also run
it by hand. It is network-facing (Zone B) and therefore deliberately NOT sealed — the sealing guard
protects the sealed core process, not this one. It reads only the core-emitted status snapshot and
relays chat over the interface handoff; it never imports core or reads a store (Invariant 2).

Bind `[monitor] host` to this machine's Tailscale IP to reach it from your phone — the tailnet is
the auth boundary (do NOT bind 0.0.0.0).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path


def main() -> int:
    from config.loader import get_config
    from edge.monitor import serve

    cfg = get_config()
    m = cfg.monitor
    serve(m.host, m.port, status_path=m.status_path, handoff=cfg.interface.handoff_dir,
          request_timeout_s=m.request_timeout_s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
