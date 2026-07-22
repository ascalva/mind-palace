"""The code embed lane wired to RUN (bp-098) — the enable path CI-1..4 (bp-092..094) deferred.

CI-1..4 shipped the code embed lane but with an INERT flag (`[code_ingest].enabled` read by
nothing), no daemon enqueue of the `code_sync` KIND, and no CLI — flipping the flag did nothing
(finding-0159: the ON switch is part of finishing). These tests pin the three seams that make it
runnable through the proper discipline, all deterministic (no Ollama, no network; temp stores;
embedders build lazily so `build_components` runs fully offline):

  1. `CodeIngestConfig` — the loader now schemas `[code_ingest]`: ON by default (finding-0161/
     oq-0034 — the Ouroboros ingests its own code natively), and a local.toml override can opt out.
  2. `build_components` REGISTERS `code_sync` unconditionally (like vault_sync it eagerly opens the
     store) and `_housekeeping` enqueues the INCREMENTAL sync ONLY when `code_ingest.enabled` — the
     gate (note §2.7: a flag flip never fires the heavy seed).
  3. `Launcher.code_seed()` (the `palace code-seed` verb) inserts ONE deliberate `code_sync` job
     onto the shared supervisor queue — single-writer preserved (a job insert, never a store write
     from the CLI), independent of the incremental gate.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import io
import subprocess
from contextlib import redirect_stdout
from pathlib import Path

from core.kernel.config import REPO_ROOT, load_config
from ops.lifecycle.launcher import Launcher, build_components
from ops.lifecycle.runs import RunLedger
from scheduler.code_sync import CODE_BACKFILL_KIND, CODE_SYNC_KIND
from scheduler.queue import JobQueue

# --- Item 1: CodeIngestConfig loader schema -------------------------------------------------


def test_code_ingest_default_on() -> None:
    """The SHIPPED default (defaults.toml, read directly so this machine's local.toml can't mask it)
    now embeds code by default — finding-0161/oq-0034 (2026-07-22): the Ouroboros ingests its own
    code natively; gating-off was a not-yet, now flipped on. `max_chars`/`overlap_chars` mirror the
    note chunker (§2.2)."""
    ci = load_config(REPO_ROOT / "config" / "defaults.toml").code_ingest
    assert ci.enabled is True
    assert ci.max_chars == 1200
    assert ci.overlap_chars == 150


def test_code_ingest_local_override_can_opt_out(tmp_path, monkeypatch) -> None:
    """The default is now ON, so the meaningful override is opting OUT: a local.toml
    `[code_ingest] enabled=false` turns it off for one instance, honoring the overlay precedence
    (defaults ← levers ← local, loader.py) — the reverse of the old enable-flip."""
    local = tmp_path / "local.toml"
    local.write_text("[code_ingest]\nenabled = false\n", encoding="utf-8")
    monkeypatch.setattr("core.kernel.config.loader._LOCAL", local)
    assert load_config().code_ingest.enabled is False


# --- temp-config fixture (mirrors tests/integration/test_lifecycle.py::_cfg) -----------------


def _cfg(root: Path, *, enabled: bool):
    """A fully temp-pathed Config (every store under `root`) so build_components runs in isolation,
    with `code_ingest.enabled` set. Mirrors the test_lifecycle `_cfg` path set exactly."""
    root.mkdir(parents=True, exist_ok=True)
    base = load_config()
    paths = dataclasses.replace(
        base.paths, data_dir=root, raw_store=root / "raw", vector_store=root / "v.lance",
        vault_catalog=root / "cat.sqlite", derived_store=root / "d.sqlite",
        attestation_store=root / "att.sqlite", telemetry_db=root / "t.duckdb")
    vault = dataclasses.replace(base.vault, path=root / "vault")
    code_ingest = dataclasses.replace(base.code_ingest, enabled=enabled)
    return dataclasses.replace(base, paths=paths, vault=vault, code_ingest=code_ingest)


def _housekeeping_kinds(comps) -> list[str]:
    """Run one housekeeping pass and return the KINDs it enqueued onto the (fresh) queue."""
    comps.enqueue_housekeeping()
    return [j.kind for j in comps.queue.list()]


# --- Item 2: daemon registration + gated housekeeping enqueue --------------------------------


def test_code_sync_handler_registered_regardless(tmp_path) -> None:
    """The handler registers unconditionally (like vault_sync it eagerly opens the vector store) so
    the supervisor can drain a deliberate code_seed job even before the incremental gate is on."""
    comps = build_components(_cfg(tmp_path, enabled=False))
    try:
        # .handlers is on the concrete Supervisor; the narrow SupervisorLike Components contract
        # hides it, so the runtime attribute access is annotated for the type-checker.
        assert CODE_SYNC_KIND in comps.supervisor.handlers  # type: ignore[attr-defined]
    finally:
        comps.queue.close()


def test_housekeeping_enqueues_code_sync_only_when_enabled(tmp_path) -> None:
    """The GATE: enabled=True → housekeeping enqueues exactly one incremental code_sync; enabled=
    False → none (the seed stays deliberate, note §2.7 — a flag flip never fires the heavy op)."""
    off = build_components(_cfg(tmp_path / "off", enabled=False))
    try:
        assert _housekeeping_kinds(off).count(CODE_SYNC_KIND) == 0
    finally:
        off.queue.close()
    on = build_components(_cfg(tmp_path / "on", enabled=True))
    try:
        assert _housekeeping_kinds(on).count(CODE_SYNC_KIND) == 1
    finally:
        on.queue.close()


# --- Item 3: palace code-seed -> a queued code_sync job --------------------------------------


def test_code_seed_enqueues_one_code_sync(tmp_path) -> None:
    """`palace code-seed` inserts ONE code_sync job onto the shared supervisor queue (single-writer:
    a job insert, never a store write from the CLI) and returns 0. Works with enabled=False — the
    seed is the deliberate owner-visible path, independent of the incremental housekeeping gate."""
    cfg = _cfg(tmp_path, enabled=False)
    launcher = Launcher(cfg=cfg, runs=RunLedger(tmp_path / "runs.sqlite"),
                        repo_root=Path(".").resolve())
    assert launcher.code_seed() == 0
    q = JobQueue(cfg.paths.data_dir / "queue.sqlite")
    try:
        assert [j.kind for j in q.list()].count(CODE_SYNC_KIND) == 1
    finally:
        q.close()


# --- bp-099 Item 2: the history backfill KIND + catch-up probe + CLI -------------------------


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


def _seed_ledger(cfg) -> None:
    """Build a small φ_code snapshots ledger under the cfg's data_dir (where the catch-up probe
    reads it), so `ledger_versions` returns real versions while the vector store stays empty."""
    from ops.code_snapshot import backfill as ledger_backfill
    from ops.code_snapshot import open_snapshot_db
    repo = cfg.paths.data_dir / "src"
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / "m.py").write_text("def m():\n    return 1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "one")
    db = open_snapshot_db(cfg.paths.data_dir / "code_snapshots.sqlite")
    try:
        ledger_backfill(db, repo)
    finally:
        db.close()


def _catchup_kinds(comps) -> list[str]:
    comps.enqueue_catchup()
    return [j.kind for j in comps.queue.list()]


def test_code_backfill_handler_registered_regardless(tmp_path) -> None:
    """The backfill handler registers unconditionally (same species as code_sync) so the supervisor
    can drain a deliberate/catch-up code_backfill job."""
    comps = build_components(_cfg(tmp_path, enabled=False))
    try:
        assert CODE_BACKFILL_KIND in comps.supervisor.handlers  # type: ignore[attr-defined]
    finally:
        comps.queue.close()


def test_catchup_enqueues_backfill_only_when_incomplete(tmp_path) -> None:
    """The incompleteness probe (no loop — the falsifier): a ledger with versions + an empty store
    → exactly one code_backfill; a fresh instance (empty ledger == empty store) → none; enabled=
    False (even with a seeded ledger) → none."""
    # incomplete: ledger seeded, store empty → one backfill
    inc = _cfg(tmp_path / "inc", enabled=True)
    _seed_ledger(inc)
    comps = build_components(inc)
    try:
        assert _catchup_kinds(comps).count(CODE_BACKFILL_KIND) == 1
    finally:
        comps.queue.close()
    # complete/equal: no ledger, empty store → NONE (the probe must not loop)
    complete = build_components(_cfg(tmp_path / "eq", enabled=True))
    try:
        assert _catchup_kinds(complete).count(CODE_BACKFILL_KIND) == 0
    finally:
        complete.queue.close()
    # disabled → NONE even with a seeded ledger (the enabled-gate short-circuits the probe)
    off_cfg = _cfg(tmp_path / "off", enabled=False)
    _seed_ledger(off_cfg)
    off = build_components(off_cfg)
    try:
        assert _catchup_kinds(off).count(CODE_BACKFILL_KIND) == 0
    finally:
        off.queue.close()


def test_code_backfill_enqueues_one_job(tmp_path) -> None:
    """`palace code-backfill` inserts ONE code_backfill job onto the shared supervisor queue
    (single-writer: a job insert, never a store write from the CLI) and returns 0."""
    cfg = _cfg(tmp_path, enabled=False)
    launcher = Launcher(cfg=cfg, runs=RunLedger(tmp_path / "runs.sqlite"),
                        repo_root=Path(".").resolve())
    assert launcher.code_backfill() == 0
    q = JobQueue(cfg.paths.data_dir / "queue.sqlite")
    try:
        assert [j.kind for j in q.list()].count(CODE_BACKFILL_KIND) == 1
    finally:
        q.close()


def test_palace_usage_lists_code_backfill() -> None:
    """`palace.py --help` surfaces the new verb (the ON switch must be reachable — finding-0159)."""
    spec = importlib.util.spec_from_file_location(
        "palace_cli", REPO_ROOT / "scripts" / "palace.py")
    assert spec and spec.loader
    palace = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(palace)
    assert "code-backfill" in palace.USAGE
    buf = io.StringIO()
    with redirect_stdout(buf):
        assert palace.main(["--help"]) == 0
    assert "code-backfill" in buf.getvalue()
