#!/usr/bin/env python
"""Owner-run body-only re-embed + dream regeneration experiment (bp-036; finding-0077). Daemon DOWN:

    uv run scripts/reembed_bodyonly.py --dry-run   # report what would happen; mutates nothing
    uv run scripts/reembed_bodyonly.py --confirm    # snapshot → re-embed → wipe dreams → re-dream

The bp-036 strip removes `key::` properties from the embedded text, so the mirror graph reverts from
the id::-polluted 9 edges to ~4 content-only edges (measured). Dreams built on the polluted graph
were CLUSTERED by that artifact, so they are wiped and regenerated on the clean graph. Framed as an
experiment: the pre-wipe dreams are SNAPSHOT to JSON first, so old vs new can be judged (better? new
discovery? regression?). Mirrors `scripts/mint_ids.py`: seal, daemon-down gate, `confirm`-gated,
reversible (vectors regenerate from raw §8; the snapshot + a derived-store backup restore the
"before"). Requires bp-036 DEPLOYED (the running pipeline must strip). Build-don't-run: the OWNER
runs it once, offline.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal


class ReembedRefusedError(RuntimeError):
    """The re-embed was refused by a safety gate — no `confirm`, or a live daemon (offline-only)."""


class _DerivedLike(Protocol):
    def all(self) -> list[Any]: ...
    def reset(self) -> None: ...


class _DreamerLike(Protocol):
    def dream(self) -> list[Any]: ...


@dataclass(frozen=True)
class ReembedReport:
    snapshot_path: str = ""          # where the pre-wipe dreams were saved (the "before")
    dreams_snapshotted: int = 0
    vector_rows: int = 0             # after the body-only rebuild
    new_dreams: int = 0             # generated on the clean graph (the "after")
    backup_dir: str = ""

    def __str__(self) -> str:
        return (f"snapshotted={self.dreams_snapshotted} → {self.snapshot_path} | "
                f"body-only vector_rows={self.vector_rows} | new_dreams={self.new_dreams} | "
                f"backup={self.backup_dir}")


def _artifact_to_dict(a: Any) -> dict[str, Any]:
    """Serialize a DerivedStore Artifact for the JSON snapshot (the human-readable 'before')."""
    return {
        "id": a.id, "kind": a.kind, "subkind": a.subkind,
        "summary": a.summary, "subjects": list(a.subjects),
        "created_at": a.created_at, "derived_from": list(a.derived_from),
    }


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _daemon_is_up(run_ledger: Any) -> bool:
    last = getattr(run_ledger, "last", lambda: None)()
    if last is None:
        return False
    return bool(getattr(last, "active", False)) and _pid_alive(int(getattr(last, "pid", -1)))


def run(*, derived: _DerivedLike, dreamer: _DreamerLike, reindex: Callable[[], Any],
        snapshot_path: Path, backup_dir: Path, derived_db: Path | None,
        confirm: bool = False, run_ledger: Any | None = None) -> ReembedReport:
    """The experiment, offline + reversible: gate → SNAPSHOT dreams → backup → re-embed body-only →
    WIPE dreams → re-dream on the clean graph → report. `reindex` is the vector rebuild
    (`run_ingest(rebuild=True)`); `dreamer.dream()` regenerates. All injectable so the build tests
    the orchestration with fakes (no model/store) — the owner runs it with the real ones."""
    if run_ledger is not None and _daemon_is_up(run_ledger):
        raise ReembedRefusedError(
            "re-embed refused: a live daemon is running — this is OFFLINE (finding-0066). Bring it "
            "down first (launchctl bootout under KeepAlive)."
        )
    if not confirm:
        raise ReembedRefusedError(
            "reembed_bodyonly is owner-gated — pass confirm=True (dry-run first)."
        )

    # 1. SNAPSHOT the pre-wipe dreams (the experiment's "before") + back up the derived store so the
    #    exact state is restorable (the vector store regenerates from raw §8, needing no backup).
    dreams = list(derived.all())
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps([_artifact_to_dict(a) for a in dreams], indent=2),
                             encoding="utf-8")
    backup_dir.mkdir(parents=True, exist_ok=True)
    if derived_db is not None and derived_db.exists():
        shutil.copy2(derived_db, backup_dir / derived_db.name)

    # 2. re-embed body-only (reset the vector store + rebuild from raw through the strip pipeline).
    summary = reindex()
    vector_rows = int(getattr(summary, "vector_rows", 0))

    # 3. WIPE all dreams (clustered on the polluted graph) and regenerate on the clean graph.
    derived.reset()
    themes = dreamer.dream()

    return ReembedReport(
        snapshot_path=str(snapshot_path), dreams_snapshotted=len(dreams),
        vector_rows=vector_rows, new_dreams=len(themes), backup_dir=str(backup_dir),
    )


def main(argv: list[str]) -> int:
    seal()  # structural egress guard first (Invariant 1)
    from config.loader import get_config
    from core.dreaming import build_dreamer
    from core.ingest.run import run_ingest
    from core.stores.derived import open_derived_store
    from ops.lifecycle.runs import open_run_ledger

    cfg = get_config()
    derived = open_derived_store(cfg)

    if "--confirm" not in argv:                          # dry-run is the default (fail-safe)
        n = len(derived.all())
        print(f"dry-run: would SNAPSHOT {n} dream(s), re-embed the vault BODY-ONLY (properties "
              f"stripped), WIPE all dreams, and regenerate. Re-run with --confirm.")
        return 0

    backup_dir = cfg.paths.data_dir / "reembed_bodyonly_backup"
    snapshot_path = backup_dir / "dreams_pre_bodyonly.json"
    try:
        report = run(
            derived=derived,
            dreamer=build_dreamer(cfg),
            reindex=lambda: run_ingest(cfg, rebuild=True),
            snapshot_path=snapshot_path,
            backup_dir=backup_dir,
            derived_db=cfg.paths.derived_store,
            confirm=True,
            run_ledger=open_run_ledger(cfg),
        )
    except ReembedRefusedError as e:
        print(f"REFUSED: {e}")
        return 1
    print(f"re-embedded + re-dreamed: {report}")
    print(f"the 'before' dreams are at {report.snapshot_path} — compare against the new ones.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
