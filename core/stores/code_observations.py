# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    the code-observation stratum — where φ_code's per-commit, symbol-grain
#            readings land (code-observation-projection.md §2.3–§2.4, B-b).
# INVARIANT: every row is ρ ≡ observed; a wrong-class row is UNREPRESENTABLE at this
#            boundary — no provenance parameter exists anywhere in this module's API.
# ENFORCED:  structural — `CodeObservation.to_row()` and `CodeObservationStore.add_batch()`
#            hardcode `Provenance.OBSERVED` (the DerivedStore/SensedObservation mint
#            discipline); identity key (commit_sha, path, qualname) + INSERT OR IGNORE
#            makes re-projection idempotent (the B-b falsifier, inverted).
"""OBSERVED-only store for code observations (ratified code-observation-projection.md B-b).

One row = one symbol-grain reading of one commit: the repo is an instrument, commits are
its readings, and the code sensor (`ops/code_sensor.py`) is the sole interpreter φ_code
(§2.2 — deterministic, transform-attributed, sole path in). Observations enter through the
`CodeSensingHandoff` seam (`core/sensing.py`, the sensing-seam sibling) and land here
wearing `observed` — there is deliberately NO provenance parameter on any API surface, so
a caller physically cannot launder a code reading into an authored (or any other) class:
the same structural move as `DerivedStore.add` and `SensedObservation.to_row`.

Mirror-opacity (§2.6): `observed` is not in `MIRROR_READABLE`, so a `MirrorView` refuses
these rows by construction and the self-model never reads them. The only typed container
is `ObservedView` (`all_rows` returns view-compatible dict rows).

HONESTY NOTE (finding-0020 class): the daemon (Ouroboros) does NOT consume these rows yet.
This store is write-side only — like the dispositional stores, the substrate lands before
its consumer (the Track-D correlator / detangling instruments read `ObservedView` when they
arrive). `references_out` is carried as a typed JSON column but is emitted EMPTY by B-b;
the deterministic reference extractor (Lane 1, V4-seeded patterns) is B-c / bp-013.

Engine: SQLite (plan Q2) — an identity-keyed append-style ledger, the runs/versions/
snapshots convention, not the DuckDB telemetry lane. Reset semantics (plan Q4): this store
is CORPUS-side (the observed stratum) and joins `reset_targets()` — wiped with the corpus,
unlike the snapshot LEDGER (build history, reset-guarded).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.loader import Config
from core.provenance import Provenance

# The observation grain's kind vocabulary (note §2.3): a module row (qualname '') carries
# the module docstring; the rest are the snapshot walk's def/class kinds.
KINDS = ("module", "class", "function", "async_function")

_DDL = """
CREATE TABLE IF NOT EXISTS code_observations (
    commit_sha     TEXT NOT NULL,                -- the reading's time coordinate (git's own
                                                 -- content address)
    path           TEXT NOT NULL,                -- file within the tree
    qualname       TEXT NOT NULL DEFAULT '',     -- symbol (module-level = '')
    kind           TEXT NOT NULL,                -- module | class | function | async_function
    signature      TEXT NOT NULL DEFAULT '',     -- unparsed arg list ('' for classes/modules)
    docstring      TEXT NOT NULL DEFAULT '',     -- the Rosetta payload — verbatim, '' if absent
    references_out TEXT NOT NULL DEFAULT '[]',   -- JSON: [{type, target, source_line}] (B-c fills)
    provenance     TEXT NOT NULL,                -- always 'observed' (nothing else is written)
    observed_at    TEXT NOT NULL,                -- when the projection landed the row
    PRIMARY KEY (commit_sha, path, qualname)
);
-- Projection bookkeeping (NOT part of the §2.3 schema): which commits φ_code has already
-- projected, and the attested batch content hash. Lets a zero-symbol commit be a recorded
-- no-op instead of re-projecting forever, and makes `sync()` re-runs skip attested batches.
CREATE TABLE IF NOT EXISTS projections (
    commit_sha   TEXT PRIMARY KEY,
    batch_hash   TEXT NOT NULL,                  -- sha256 of the canonical batch JSON
    projected_at TEXT NOT NULL
);
"""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass(frozen=True)
class CodeObservation:
    """One symbol-grain reading of one commit (note §2.3, verbatim columns).

    Deliberately has NO provenance field: like `SensedObservation`, the class label is
    minted at `to_row()` with no parameter — the wire payload (`to_dict`) carries nothing
    a caller could forge a class with."""

    commit_sha: str
    path: str
    qualname: str                                   # module-level = ""
    kind: str                                       # one of KINDS
    signature: str = ""                             # '' for classes/modules
    docstring: str = ""                             # verbatim, '' if absent
    # Typed: [{type: note-citation | path-mention | symbol-mention | design-ref,
    #          target: str, source_line: int}] — emitted () by B-b, filled by B-c (bp-013).
    references_out: tuple[dict[str, Any], ...] = ()

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CodeObservation:
        """Parse one handoff wire payload (the seam's inbound half, `SensedObservation` shape)."""
        return cls(
            commit_sha=str(d.get("commit_sha", "")),
            path=str(d.get("path", "")),
            qualname=str(d.get("qualname", "")),
            kind=str(d.get("kind", "")),
            signature=str(d.get("signature", "")),
            docstring=str(d.get("docstring", "")),
            references_out=tuple(dict(r) for r in d.get("references_out", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        """The handoff wire payload — schema fields only, NO provenance (nothing to forge)."""
        return {
            "commit_sha": self.commit_sha,
            "path": self.path,
            "qualname": self.qualname,
            "kind": self.kind,
            "signature": self.signature,
            "docstring": self.docstring,
            "references_out": [dict(r) for r in self.references_out],
        }

    def to_row(self) -> dict[str, Any]:
        """The observed-tier row. Provenance is HARDCODED — there is no parameter, so no
        caller can launder a code reading into another class (the `SensedObservation.to_row`
        move, verbatim). `ObservedView` admits these rows; `MirrorView` refuses them (§2.6)."""
        return {**self.to_dict(), "provenance": Provenance.OBSERVED.value}


def batch_content_hash(observations: Iterable[CodeObservation]) -> str:
    """Content hash of a projection batch — sha256 over the canonical (sorted-key, sorted-row)
    JSON of the wire payloads. Deterministic (§2.2): re-running φ_code over the same commit
    yields the same hash, so the `project_observations` attestation is content-addressed."""
    rows = sorted((o.to_dict() for o in observations),
                  key=lambda r: (r["commit_sha"], r["path"], r["qualname"]))
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class CodeObservationStore:
    """The observed stratum's code-observation table. Writes `observed` UNCONDITIONALLY —
    no method on this class accepts a provenance value (Item 3 falsifier, ruled out by
    construction and pinned by test)."""

    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def add_batch(self, observations: Iterable[CodeObservation]) -> int:
        """Land one projection batch. INSERT OR IGNORE on the identity key
        (commit_sha, path, qualname): a second projection of the same commit changes
        NOTHING (the B-b falsifier, inverted). Returns the number of NEW rows."""
        added = 0
        with self._conn:
            for o in observations:
                cur = self._conn.execute(
                    "INSERT OR IGNORE INTO code_observations VALUES (?,?,?,?,?,?,?,?,?)",
                    [o.commit_sha, o.path, o.qualname, o.kind, o.signature, o.docstring,
                     json.dumps([dict(r) for r in o.references_out]),
                     Provenance.OBSERVED.value, _utcnow()],
                )
                added += cur.rowcount
        return added

    # --- reads (view-compatible dict rows) ----------------------------------------------
    def all_rows(self, *,
                 provenances: Iterable[Provenance] | None = None) -> list[dict[str, Any]]:
        """Full scan, optionally restricted to provenance classes (the `RowSource` shape).
        Every stored row is `observed`, so a filter containing OBSERVED sees ALL rows and
        any filter excluding it sees NONE — there is no third case."""
        rows = [self._row(r) for r in self._conn.execute(
            "SELECT * FROM code_observations ORDER BY commit_sha, path, qualname"
        ).fetchall()]
        if provenances is None:
            return rows
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in rows if r["provenance"] in allowed]

    def rows_for(self, commit_sha: str) -> list[dict[str, Any]]:
        return [self._row(r) for r in self._conn.execute(
            "SELECT * FROM code_observations WHERE commit_sha = ? ORDER BY path, qualname",
            [commit_sha],
        ).fetchall()]

    def count(self) -> int:
        row = self._conn.execute("SELECT count(*) FROM code_observations").fetchone()
        return int(row[0]) if row else 0

    # --- projection bookkeeping (φ_code's idempotency ledger) ----------------------------
    def is_projected(self, commit_sha: str) -> bool:
        return self._conn.execute(
            "SELECT 1 FROM projections WHERE commit_sha = ?", [commit_sha]
        ).fetchone() is not None

    def mark_projected(self, commit_sha: str, content_hash: str) -> None:
        """Record that φ_code projected `commit_sha` (INSERT OR IGNORE: first mark wins —
        re-interpretation is a versioned supersession, §2.2, not an in-place overwrite)."""
        with self._conn:
            self._conn.execute("INSERT OR IGNORE INTO projections VALUES (?,?,?)",
                               [commit_sha, content_hash, _utcnow()])

    @staticmethod
    def _row(r: sqlite3.Row) -> dict[str, Any]:
        d = dict(r)
        d["references_out"] = json.loads(d["references_out"])
        return d

    def close(self) -> None:
        self._conn.close()


def open_code_observation_store(config: Config | None = None) -> CodeObservationStore:
    """The `open_*` helper: `data/code_observations.sqlite` (plan Q2 — the sibling-store
    convention beside `derived_store`, no dedicated cfg path; registered in
    `reset_targets()` as a corpus-side wipe target, plan Q4)."""
    from config.loader import get_config

    cfg = config or get_config()
    return CodeObservationStore(cfg.paths.data_dir / "code_observations.sqlite")
