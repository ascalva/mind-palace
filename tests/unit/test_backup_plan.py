"""restic argv builders are deterministic and secret-free (BUILD-SPEC §16b, Phase 9).

The *what to back up* and the restic flags are reviewed here, not buried in a shell script; and no
password or AWS key can leak into argv — restic reads those from the environment (the runner sets
them), and `BackupPlan` has no field that could carry one.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from config.loader import get_config
from ops.backup.plan import (
    BackupPlan,
    backup_argv,
    build_backup_plan,
    check_argv,
    forget_argv,
    init_argv,
    restore_argv,
    snapshots_argv,
)

_BASE_PLAN = BackupPlan(
    repository="s3:s3.us-east-1.amazonaws.com/b", paths=("/v", "/d"),
    excludes=("logs", "*-shm"), tags=("mind-palace",),
    keep_daily=7, keep_weekly=4, keep_monthly=6,
)


def _plan(**kw) -> BackupPlan:
    return replace(_BASE_PLAN, **kw)


def test_init_argv():
    assert init_argv("repo") == ["restic", "-r", "repo", "init"]


def test_backup_argv_flags_then_paths():
    argv = backup_argv(_plan())
    assert argv[:4] == ["restic", "-r", "s3:s3.us-east-1.amazonaws.com/b", "backup"]
    assert ["--tag", "mind-palace"] == argv[4:6]
    assert argv.count("--exclude") == 2
    assert "logs" in argv and "*-shm" in argv
    assert argv[-2:] == ["/v", "/d"]                    # paths are positional, last


def test_forget_argv_retention_and_prune():
    argv = forget_argv(_plan(keep_daily=10))
    assert "--prune" in argv and "--tag" in argv
    assert argv[argv.index("--keep-daily") + 1] == "10"
    assert argv[argv.index("--keep-weekly") + 1] == "4"
    assert argv[argv.index("--keep-monthly") + 1] == "6"


def test_restore_check_snapshots_argv():
    assert restore_argv("repo", "latest", "/tgt") == [
        "restic", "-r", "repo", "restore", "latest", "--target", "/tgt",
    ]
    assert check_argv("repo") == ["restic", "-r", "repo", "check"]
    assert snapshots_argv("repo") == ["restic", "-r", "repo", "snapshots", "--json"]


def test_no_secret_can_appear_in_argv():
    # restic reads RESTIC_PASSWORD + AWS_* from the ENV, never argv. There is no password field on
    # BackupPlan, so a secret cannot ride along by construction.
    assert not hasattr(BackupPlan("r", ()), "password")
    for argv in (init_argv("r"), backup_argv(_plan()), forget_argv(_plan()), check_argv("r")):
        assert not any("password" in a.lower() or a.startswith("AKIA") for a in argv)


def test_build_backup_plan_backs_up_vault_and_data_excluding_live_raft():
    cfg = get_config()
    plan = build_backup_plan(cfg)
    assert plan.paths == (str(cfg.vault.path), str(cfg.paths.data_dir))
    # The live Vault raft store is excluded — it's captured via a consistent snapshot instead.
    assert str(Path(cfg.paths.data_dir) / "vault") in plan.excludes
    assert plan.keep_daily == cfg.backup.keep_daily
    # The configured transient/regenerable excludes are carried through.
    assert "logs" in plan.excludes
