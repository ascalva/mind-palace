"""Status snapshot — the core→edge monitoring handoff (Invariant 2).

The launcher writes a small JSON snapshot of operational METADATA to a file each health tick; the
edge monitor process READS only that file to render its dashboard. Same asymmetry as the airlock:
the core emits, the networked side never reads a store. The snapshot carries only what the OpsView
already narrates — action counts, health, the *shape* of recent activity, queue depth, memory
headroom — plus dream/finding counts. NO note text, NO authored-note titles, NO secrets/tokens.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def build_status(*, ops_view, dreams_view, queue_depth: int, run=None,
                 mem_available_gb: float | None = None, flags=()) -> dict[str, Any]:
    """Assemble the snapshot dict from the read-only views. Pure — no I/O — so it is unit-testable
    against in-memory stores. `run` is the active RunRecord (commit-pinned); `flags` are the OS
    watchdog's crossed-threshold flags."""
    snap = ops_view.snapshot()
    return {
        "generated_at": _utcnow(),
        "run": None if run is None else {
            "id": run.id,
            "commit": run.commit_sha[:12],
            "dirty": run.dirty,
            "started_at": run.started_at,
        },
        "activity": {
            "actions_logged": snap.attestation_count,
            # (role, action, timestamp) — operational shape, never corpus content.
            "recent": [{"role": r, "action": a, "at": ts} for r, a, ts in snap.recent_actions],
            "pending_approvals": snap.pending_proposals,
        },
        "health": {
            "drift_within_tolerance": snap.drift_within_tolerance,
            "constitution_intact": snap.constitution_intact,
            "memory_available_gb": mem_available_gb,
            "flags": [{"metric": f.metric, "value": f.value, "threshold": f.threshold,
                       "note": f.note} for f in flags],
        },
        "patterns": {
            "dreams": dreams_view.dream_count(),
            "tidy_suggestions": dreams_view.finding_count(),
        },
        "queue_depth": queue_depth,
    }


def write_status(path: Path, data: dict[str, Any]) -> None:
    """Write the snapshot atomically — the edge reader never sees a partial file (rename swap)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)
