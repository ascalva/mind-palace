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
    uv run scripts/palace.py ingest-chat    # on-demand: ingest the local Claude Code transcripts
    uv run scripts/palace.py bless <id>     # owner-only: flip a build plan proposed -> ready (blessing gate)

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

import os
import re
import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))  # repo root on path

from core.sealing import seal

USAGE = ("usage: palace.py {start|stop|down|up|restart|status|reset|deploy|ingest-chat|bless} "
         "[--force] [--confirm] [--skip-tests] [<plan-id>]")


def bless(plan_id: str) -> int:
    """Owner-only blessing flip: a build plan's status ``proposed -> ready`` (§10, the
    readiness gate). This is decision-routing v1: a keystroke for the one gate the owner
    already performs by hand, with the SAME guarantees — never an agent, only ``proposed``,
    line-targeted so front-matter comments survive byte-identical. It mints NO new capability
    and does NOT loosen gate-guard / the Stop-gate audit (those remain the real guards; this
    is a convenience wrapper the owner drives). The guard order below is LAW.

    (1) refuse inside an agent session BEFORE any path resolution — even a probe with a fake
        id proves the guard fired, with zero flip risk. (2) resolve, missing -> exit 2.
    (3) status must be EXACTLY ``proposed`` (no force path exists). (4) rewrite ONLY the
        ``status:`` value and the ``updated:`` date, line-targeted — NEVER a YAML round-trip."""
    # (1) Agent-session refusal — precedes path resolution (belt-and-suspenders; the
    #     Stop-gate blessing audit is the structural guard, unchanged — Q5).
    if os.environ.get("CLAUDECODE"):
        print(
            "refusing: agent session detected (CLAUDECODE set) — the proposed->ready "
            "blessing is owner-only, by hand (§10). No plan was touched.",
            file=sys.stderr,
        )
        return 2
    # (2) Resolve.
    plan = _ROOT / "docs" / "build-plans" / plan_id / "plan.md"
    if not plan.exists():
        print(f"no such plan: {plan_id} ({plan.relative_to(_ROOT)} not found)", file=sys.stderr)
        return 2
    lines = plan.read_text(encoding="utf-8").splitlines(keepends=True)
    # Locate the front-matter block (first '---' ... next '---').
    bounds = [i for i, ln in enumerate(lines) if ln.strip() == "---"]
    if len(bounds) < 2:
        print(f"{plan_id}: no front-matter block found", file=sys.stderr)
        return 2
    fm_lo, fm_hi = bounds[0] + 1, bounds[1]
    status_i = updated_i = None
    for i in range(fm_lo, fm_hi):
        if re.match(r"^\s*status:\s*\S", lines[i]) and status_i is None:
            status_i = i
        elif re.match(r"^\s*updated:\s*\S", lines[i]) and updated_i is None:
            updated_i = i
    if status_i is None:
        print(f"{plan_id}: no status: line in front-matter", file=sys.stderr)
        return 2
    m = re.match(r"^(\s*status:\s*)(\S+)(.*)$", lines[status_i].rstrip("\n"))
    prefix, value, rest = m.group(1), m.group(2), m.group(3)
    # (3) EXACTLY proposed — no force, no override (the leading \S+ already excludes a
    #     trailing ' # comment', so the compare is on the bare value token).
    if value != "proposed":
        print(
            f"{plan_id}: status is '{value}', not 'proposed' — bless only flips "
            "proposed->ready (no force path exists).",
            file=sys.stderr,
        )
        return 2
    # (4) Line-targeted flip: status value proposed->ready, updated: -> today. `rest`
    #     (any trailing comment) is preserved verbatim; the rest of the file is untouched.
    nl = "\n" if lines[status_i].endswith("\n") else ""
    lines[status_i] = f"{prefix}ready{rest}{nl}"
    if updated_i is not None:
        um = re.match(r"^(\s*updated:\s*)(\S+)(.*)$", lines[updated_i].rstrip("\n"))
        if um:
            unl = "\n" if lines[updated_i].endswith("\n") else ""
            lines[updated_i] = f"{um.group(1)}{date.today().isoformat()}{um.group(3)}{unl}"
    plan.write_text("".join(lines), encoding="utf-8")
    # (5) Report.
    print(f"{plan_id}: proposed -> ready (blessed by hand). Now: uv run scripts/palace.py or /build.")
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(USAGE)
        return 0
    if argv[0] == "bless":  # owner-only gate; never touches the daemon -> dispatch BEFORE seal()/launcher
        if len(argv) != 2:
            print("usage: palace.py bless <plan-id>", file=sys.stderr)
            return 2
        return bless(argv[1])
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
    if cmd == "ingest-chat":
        return launcher.ingest_chat()
    print(USAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
