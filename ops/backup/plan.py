"""restic command construction for the scheduled backup (BUILD-SPEC §16b, Phase 9).

The argv builders are pure and deterministic (unit-tested the same way `core/sandbox/policy.py`'s
argv is) — the *what to back up* and the restic flags are code-reviewed, not buried in a shell
script. Secrets are NEVER on the command line: the restic repo password and the AWS key are passed
to `ResticRunner` via the environment (`RESTIC_PASSWORD`, `AWS_*`), so they never appear in argv,
`ps`, or a log. `ResticRunner` is the thin subprocess wrapper both the scheduled runner and the
round-trip test drive.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from config.loader import Config

DEFAULT_TAG = "mind-palace"


@dataclass(frozen=True)
class BackupPlan:
    """Everything needed to drive one backup of this host. `paths` are the roots restic walks;
    `excludes` are restic exclude patterns (basename globs, or absolute paths for a specific
    subtree — e.g. the live Vault raft dir, which is captured via a consistent snapshot instead).
    Retention drives `forget --prune`."""

    repository: str
    paths: tuple[str, ...]
    excludes: tuple[str, ...] = ()
    tags: tuple[str, ...] = (DEFAULT_TAG,)
    keep_daily: int = 7
    keep_weekly: int = 4
    keep_monthly: int = 6


def init_argv(repository: str) -> list[str]:
    """`restic init` — one-time repo creation (idempotent-safe: errors if already initialized)."""
    return ["restic", "-r", repository, "init"]


def backup_argv(plan: BackupPlan) -> list[str]:
    """`restic backup` of the plan's paths, tagged + excluded. Flags precede the paths."""
    argv = ["restic", "-r", plan.repository, "backup"]
    for tag in plan.tags:
        argv += ["--tag", tag]
    for pattern in plan.excludes:
        argv += ["--exclude", pattern]
    argv += list(plan.paths)
    return argv


def forget_argv(plan: BackupPlan) -> list[str]:
    """`restic forget --prune` scoped to this host's tag, applying the retention policy."""
    argv = ["restic", "-r", plan.repository, "forget", "--prune"]
    for tag in plan.tags:
        argv += ["--tag", tag]
    argv += [
        "--keep-daily", str(plan.keep_daily),
        "--keep-weekly", str(plan.keep_weekly),
        "--keep-monthly", str(plan.keep_monthly),
    ]
    return argv


def restore_argv(repository: str, snapshot: str, target: str) -> list[str]:
    """`restic restore <snapshot> --target <dir>` — `snapshot` may be an id or `latest`."""
    return ["restic", "-r", repository, "restore", snapshot, "--target", target]


def check_argv(repository: str) -> list[str]:
    """`restic check` — verify repository integrity."""
    return ["restic", "-r", repository, "check"]


def snapshots_argv(repository: str) -> list[str]:
    """`restic snapshots --json` — list snapshots (machine-readable)."""
    return ["restic", "-r", repository, "snapshots", "--json"]


@dataclass
class ResticRunner:
    """Thin subprocess wrapper. `env` carries the secrets restic reads from the environment
    (`RESTIC_PASSWORD`, and for an S3 repo `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`) — merged
    over the process environment per call so they never touch argv. Methods return the
    `CompletedProcess`; callers inspect `.returncode` (kept un-raising so the runner can log and the
    test can assert)."""

    env: dict[str, str] = field(default_factory=dict)

    def available(self) -> bool:
        return shutil.which("restic") is not None

    def _run(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            argv,
            env={**os.environ, **self.env},
            capture_output=True,
            text=True,
            check=False,
        )

    def init(self, repository: str) -> subprocess.CompletedProcess[str]:
        return self._run(init_argv(repository))

    def backup(self, plan: BackupPlan) -> subprocess.CompletedProcess[str]:
        return self._run(backup_argv(plan))

    def forget(self, plan: BackupPlan) -> subprocess.CompletedProcess[str]:
        return self._run(forget_argv(plan))

    def restore(
        self, repository: str, snapshot: str, target: str
    ) -> subprocess.CompletedProcess[str]:
        return self._run(restore_argv(repository, snapshot, target))

    def check(self, repository: str) -> subprocess.CompletedProcess[str]:
        return self._run(check_argv(repository))

    def snapshots(self, repository: str) -> subprocess.CompletedProcess[str]:
        return self._run(snapshots_argv(repository))


def build_backup_plan(config: Config | None = None) -> BackupPlan:
    """Assemble the host's BackupPlan from `[backup]` + the data/vault paths. Backs up the note
    vault + the data dir; EXCLUDES the live Vault raft store (`<data>/vault`) because it is captured
    separately as a consistent `vault operator raft snapshot` (the runner stages that snapshot
    inside the data dir, so it rides along in this same backup)."""
    from config.loader import get_config

    cfg = config or get_config()
    bak = cfg.backup
    data_dir = Path(cfg.paths.data_dir)
    return BackupPlan(
        repository=bak.repository,
        paths=(str(cfg.vault.path), str(data_dir)),
        # config excludes (transient/regenerable basenames) + the live raft dir (snapshotted apart).
        excludes=(*bak.exclude, str(data_dir / "vault")),
        tags=(DEFAULT_TAG,),
        keep_daily=bak.keep_daily,
        keep_weekly=bak.keep_weekly,
        keep_monthly=bak.keep_monthly,
    )
