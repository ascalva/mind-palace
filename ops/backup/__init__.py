"""Encrypted backups — restic → S3 (BUILD-SPEC §16b, Phase 9).

Operational, NOT part of the sealed core. The scheduled OS-level job (launchd) reads data dirs and
writes restic ciphertext to S3; the sealed core never runs backups. restic encrypts + deduplicates
client-side, so the only bytes that cross the network are ciphertext — AWS never sees plaintext
private data (the §16b backup boundary, analogous to the airlock's de-identification boundary).
"""

from ops.backup.plan import (
    BackupPlan,
    ResticRunner,
    backup_argv,
    build_backup_plan,
    check_argv,
    forget_argv,
    init_argv,
    restore_argv,
    snapshots_argv,
)

__all__ = [
    "BackupPlan",
    "ResticRunner",
    "backup_argv",
    "build_backup_plan",
    "check_argv",
    "forget_argv",
    "init_argv",
    "restore_argv",
    "snapshots_argv",
]
