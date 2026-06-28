"""CLI entrypoint for the scheduled backup — `ops/backup/backup.sh` drives it.

Builds the plan from config and runs restic via `ResticRunner`, which inherits `RESTIC_PASSWORD`
and `AWS_*` from the environment the wrapper populated from Keychain (so no secret is ever on the
command line). Subcommands: init | backup | forget | check | snapshots | restore <snap> <target>.
"""

from __future__ import annotations

import sys

from ops.backup.plan import ResticRunner, build_backup_plan

_USAGE = "usage: python -m ops.backup.run <init|backup|forget|check|snapshots|restore SNAP TARGET>"


def main(argv: list[str]) -> int:
    if not argv:
        print(_USAGE, file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]

    plan = build_backup_plan()
    if not plan.repository:
        print("no [backup] repository configured (set it in config/local.toml)", file=sys.stderr)
        return 1

    runner = ResticRunner()
    if not runner.available():
        print("restic not installed (brew install restic)", file=sys.stderr)
        return 1

    if cmd == "init":
        proc = runner.init(plan.repository)
    elif cmd == "backup":
        proc = runner.backup(plan)
    elif cmd == "forget":
        proc = runner.forget(plan)
    elif cmd == "check":
        proc = runner.check(plan.repository)
    elif cmd == "snapshots":
        proc = runner.snapshots(plan.repository)
    elif cmd == "restore":
        if len(rest) != 2:
            print("restore needs <snapshot> <target>", file=sys.stderr)
            return 2
        proc = runner.restore(plan.repository, rest[0], rest[1])
    else:
        print(f"unknown command {cmd!r}\n{_USAGE}", file=sys.stderr)
        return 2

    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
