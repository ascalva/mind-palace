"""Live gate (BUILD-SPEC §16b, Phase 9): an encrypted backup + restore round-trips, and the repo
holds NO plaintext.

Proven against a LOCAL restic repository — restic's encryption is identical whether the backend is
a local dir or S3, so this verifies the "AWS sees no plaintext" gate with no AWS/network. The S3
backend adds only credentials + transport; the encryption boundary (what matters) is exercised
here. Auto-skips without restic. Run: pytest -m needs_restic.
"""

from __future__ import annotations

import pytest

from ops.backup.plan import BackupPlan, ResticRunner

pytestmark = pytest.mark.needs_restic

_HAS_RESTIC = ResticRunner().available()
_skip = pytest.mark.skipif(not _HAS_RESTIC, reason="restic not installed (brew install restic)")


@_skip
def test_backup_restore_roundtrips_and_repo_has_no_plaintext(tmp_path):
    secret = "MIND-PALACE-SECRET-NOTE-42 anxiety and sleep insomnia"
    src = tmp_path / "src"
    src.mkdir()
    (src / "note.md").write_text(secret + "\n")
    repo = tmp_path / "repo"
    target = tmp_path / "restored"

    runner = ResticRunner(env={"RESTIC_PASSWORD": "round-trip-test-pw"})
    assert runner.init(str(repo)).returncode == 0
    plan = BackupPlan(repository=str(repo), paths=(str(src),))
    assert runner.backup(plan).returncode == 0

    # Restore the latest snapshot and confirm the bytes survive the round-trip.
    assert runner.restore(str(repo), "latest", str(target)).returncode == 0
    restored = next(target.rglob("note.md"))
    assert restored.read_text() == secret + "\n"

    # The gate: the plaintext appears NOWHERE in the repository's bytes — restic encrypted
    # everything before it would ever reach a backend (local here, S3 in production).
    repo_bytes = b"".join(p.read_bytes() for p in repo.rglob("*") if p.is_file())
    assert secret.encode() not in repo_bytes

    # And the repository passes its own integrity check.
    assert runner.check(str(repo)).returncode == 0
