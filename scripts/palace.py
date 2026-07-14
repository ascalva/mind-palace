#!/usr/bin/env python
"""Mind-palace lifecycle — ONE command to run the whole system. From the repo root:

    uv run scripts/palace.py start          # preflight → record run → supervise
    uv run scripts/palace.py stop           # graceful drain of the live run
    uv run scripts/palace.py down           # maintenance-down (bootout — outlasts KeepAlive)
    uv run scripts/palace.py up             # bring the agent back (bootstrap)
    uv run scripts/palace.py restart        # plain down→up cycle (NOT deploy)
    uv run scripts/palace.py status         # preflight + recent runs + system snapshot
    uv run scripts/palace.py reset --confirm # fresh-start wipe of the corpus layer
    uv run scripts/palace.py deploy         # promotion gate: cycle the live run onto HEAD

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

USAGE = ("usage: palace.py {start|stop|down|up|restart|status|reset|deploy} "
         "[--force] [--confirm] [--skip-tests]")


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
    if cmd == "down":
        return launcher.down()
    if cmd == "up":
        return launcher.up()
    if cmd == "restart":
        return launcher.restart()
    if cmd == "status":
        return launcher.status()
    if cmd == "reset":
        return launcher.reset(confirm="--confirm" in flags)
    if cmd == "deploy":
        return launcher.deploy(skip_tests="--skip-tests" in flags)
    print(USAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
