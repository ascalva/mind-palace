#!/usr/bin/env python
"""Mind-palace lifecycle — ONE command to run the whole system. From the repo root:

    ./.venv/bin/python scripts/palace.py start          # preflight → record run → supervise
    ./.venv/bin/python scripts/palace.py stop           # graceful drain of the live run
    ./.venv/bin/python scripts/palace.py status         # preflight + recent runs
    ./.venv/bin/python scripts/palace.py reset --confirm # fresh-start wipe of the corpus layer

`start` seals the core (Invariant 1 — loopback only), runs preflight (ensures our own
components, VERIFIES Vault/Ollama/podman, fail-closed), records the run pinned to the current
git commit, reconciles the corpus (rebuilds an empty cache), then supervises the queue + the
vault watcher until SIGTERM/SIGINT — at which point it drains the in-flight job at its boundary
and marks the run CLEAN (the graceful-shutdown / lifecycle hook). If the previous run didn't
exit cleanly it comes up in recovery mode; `start --force` resumes normally.

For an always-on daemon, install the launchd plist (ops/lifecycle/com.mind-palace.palace.plist)
— see docs/runbook.md → "One-command lifecycle". `--force` overrides a failed preflight or an
unclean prior shutdown.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal

USAGE = "usage: palace.py {start|stop|status|reset} [--force] [--confirm]"


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(USAGE)
        return 0
    seal()  # structural egress guard first (Invariant 1); the launcher works within it (loopback)
    from ops.lifecycle.launcher import build_launcher

    cmd, flags = argv[0], set(argv[1:])
    launcher = build_launcher()
    if cmd == "start":
        return launcher.start(force="--force" in flags)
    if cmd == "stop":
        return launcher.stop()
    if cmd == "status":
        return launcher.status()
    if cmd == "reset":
        return launcher.reset(confirm="--confirm" in flags)
    print(USAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
