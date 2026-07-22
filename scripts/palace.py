#!/usr/bin/env python
"""Mind-palace lifecycle — ONE command to run the whole system. From the repo root:

    uv run scripts/palace.py start          # preflight → record run → supervise
    uv run scripts/palace.py stop           # graceful drain of the live run
    uv run scripts/palace.py down           # maintenance-down (bootout — outlasts KeepAlive)
    uv run scripts/palace.py up             # bring the agent back (bootstrap)
    uv run scripts/palace.py restart        # plain down→up cycle (NOT deploy)
    uv run scripts/palace.py status         # preflight + recent runs + system snapshot
    uv run scripts/palace.py queue          # read-only: waiting jobs, grouped by kind
    uv run scripts/palace.py reset --confirm # fresh-start wipe of the corpus layer
    uv run scripts/palace.py deploy         # promotion gate: cycle the live run onto HEAD
    uv run scripts/palace.py ingest-chat    # on-demand: ingest the local Claude Code transcripts
    uv run scripts/palace.py code-seed      # on-demand: seed the code embed lane (HEAD .py blobs)
    uv run scripts/palace.py code-backfill  # on-demand: embed the full code history (bp-099)
    uv run scripts/palace.py bless <id>     # owner-only: flip a plan proposed -> ready (gate)

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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal

_ROOT = Path(__file__).resolve().parent.parent  # repo root, for the bless path resolution

USAGE = ("usage: palace.py "
         "{start|stop|down|up|restart|status|queue|reset|deploy|ingest-chat|code-seed|"
         "code-backfill|bless} "
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
    if m is None:  # unreachable: status_i was found by the same-shape finder regex (defensive)
        print(f"{plan_id}: malformed status: line", file=sys.stderr)
        return 2
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
    print(f"{plan_id}: proposed -> ready (blessed by hand). Next: /build {plan_id}.")
    return 0


def _fmt_age(seconds: float) -> str:
    """Compact human age for the oldest-waiting column: 41s / 6m / 2h / 3d."""
    s = int(max(0, seconds))
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        return f"{s // 3600}h"
    return f"{s // 86400}d"


def queue_overview() -> int:
    """Read-only overview of the daemon's job queue — how many jobs of each KIND are waiting,
    so the bare depth number becomes legible (what is the daemon actually behind on?).

    Opens the queue SQLite **read-only** (``mode=ro``): a view must never take a write lock on
    the live single-writer daemon's db, so this deliberately issues raw aggregate reads rather
    than constructing a ``JobQueue`` (whose ``__post_init__`` runs DDL + flips WAL — a write).
    It reuses the queue's own state/priority vocabulary so the labels never drift from source."""
    import sqlite3
    from datetime import UTC, datetime

    from core.kernel.config.loader import get_config
    from scheduler.queue import (
        DEFERRED,
        DONE,
        FAILED,
        PRIORITY_BACKGROUND,
        PRIORITY_DEFAULT,
        PRIORITY_INTERACTIVE,
        PRIORITY_REACTIVE,
        QUEUED,
        RUNNING,
    )

    db = get_config().paths.data_dir / "queue.sqlite"
    if not db.exists():
        print(f"no queue yet ({db} not found) — the daemon has not run.")
        return 0

    prio_name = {
        PRIORITY_REACTIVE: "reactive",
        PRIORITY_INTERACTIVE: "interactive",
        PRIORITY_DEFAULT: "default",
        PRIORITY_BACKGROUND: "background",
    }
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        state_rows = conn.execute("SELECT state, count(*) FROM jobs GROUP BY state").fetchall()
        by_state = {r[0]: r[1] for r in state_rows}
        # Active (non-terminal) jobs, grouped by kind so "how many of each kind" reads off directly;
        # tier + priority + oldest give the number meaning (what tier is backed up, and how stale).
        rows = conn.execute(
            "SELECT kind, state, tier, priority, count(*) AS n, min(created_at) AS oldest "
            "FROM jobs WHERE state IN (?, ?, ?) "
            "GROUP BY kind, state, tier, priority ORDER BY n DESC, kind",
            [QUEUED, RUNNING, DEFERRED],
        ).fetchall()
    finally:
        conn.close()

    active = sum(r["n"] for r in rows)
    print(f"\nmind-palace queue — {db}\n")
    print(
        f"  {active} active   "
        f"({by_state.get(QUEUED, 0)} queued · {by_state.get(RUNNING, 0)} running · "
        f"{by_state.get(DEFERRED, 0)} deferred)\n"
    )
    if not rows:
        print("  nothing waiting — the queue is drained.\n")
    else:
        now = datetime.now(UTC).replace(tzinfo=None)  # match _utcnow(): naive UTC, seconds
        print(f"  {'kind':<16}{'state':<9}{'tier':<11}{'priority':<13}{'n':>4}   oldest")
        print(f"  {'-' * 15:<16}{'-' * 8:<9}{'-' * 10:<11}{'-' * 12:<13}{'-' * 4:>4}   {'-' * 6}")
        for r in rows:
            age = _fmt_age((now - datetime.fromisoformat(r["oldest"])).total_seconds())
            pn = prio_name.get(r["priority"], str(r["priority"]))
            print(f"  {r['kind']:<16}{r['state']:<9}{r['tier']:<11}{pn:<13}{r['n']:>4}   {age}")
    print(f"\n  lifetime: {by_state.get(DONE, 0):,} done, {by_state.get(FAILED, 0):,} failed\n")
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(USAGE)
        return 0
    if argv[0] == "queue":  # read-only view; never touches the daemon -> before seal()/launcher
        return queue_overview()
    if argv[0] == "bless":  # owner-only gate; never touches the daemon -> before seal()/launcher
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
    if cmd == "code-seed":
        return launcher.code_seed()
    if cmd == "code-backfill":
        return launcher.code_backfill()
    print(USAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
