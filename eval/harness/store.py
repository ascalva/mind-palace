"""The eval-results store — the harness keystone (dn-evaluation-harness §2.2, E1/bp-042).

An append-only, analytical DuckDB table. Every reading is addressed by the unified key
`(spec_hash, corpus_ref, config_fingerprint, seed)` (§2.1) plus its `metric_name`; a row is
`(key, metric_name, value, type_tag, interval_lo/hi?, evidence_ref)`. Two properties fall out of
append-only KEYING, not from any bolted-on feature:

* **resumability** — a keyed cell already present is *skipped* on re-`put` (`put` returns False),
  so an interrupted overnight sweep resumes for free by replaying;
* **honest longitudinal comparison** — every number knows exactly what state it measured, because
  the three confounds (corpus growth, config change, pipeline change) each have their own key
  component and never collapse.

The store is its OWN Σ: non-promotable, outside the complex, ∉ `MIRROR_READABLE` (§2.10). It imports
no `core/` read path and holds no model (the eval-isolation integrity tooth proves both). DuckDB is
the engine (A-4: the access pattern is analytical group-by); *append-only* is a discipline this code
enforces (DuckDB will happily insert a duplicate — `put` refuses one).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

# One keyed table. The PRIMARY KEY is the unified key (§2.1) + metric_name — the append-only
# discipline's structural backstop; `put` also checks membership first so it can *report* a skip.
_DDL = """
CREATE TABLE IF NOT EXISTS eval_results (
    spec_hash          VARCHAR NOT NULL,   -- instrument id+version ‖ pipeline ‖ battery params
    corpus_ref         VARCHAR NOT NULL,   -- "fixture:<hash>" | "<merkle-digest>"
    config_fingerprint VARCHAR NOT NULL,   -- sha256 of the resolved tuning manifest
    seed               BIGINT  NOT NULL,
    metric_name        VARCHAR NOT NULL,   -- MUST be a registered registry key (registry.py)
    value              DOUBLE  NOT NULL,
    type_tag           VARCHAR NOT NULL,   -- "Inv" | "Rate(<clock>)" (Rule CLOCK)
    interval_lo        DOUBLE,             -- EH-f: intervals at n<=13 owner scale; else point value
    interval_hi        DOUBLE,
    evidence_ref       VARCHAR,            -- opaque pointer (attestation id / report path)
    PRIMARY KEY (spec_hash, corpus_ref, config_fingerprint, seed, metric_name)
);
"""


@dataclass(frozen=True)
class EvalKey:
    """The unified key (§2.1). Every reading is addressed by exactly this tuple."""

    spec_hash: str
    corpus_ref: str
    config_fingerprint: str
    seed: int


@dataclass(frozen=True)
class Reading:
    """One reading = one row (§2.2). `type_tag` carries the Inv/Rate(κ) discipline (§2.3)."""

    key: EvalKey
    metric_name: str
    value: float
    type_tag: str
    interval_lo: float | None = None
    interval_hi: float | None = None
    evidence_ref: str | None = None


def _connect(path: Path | str) -> duckdb.DuckDBPyConnection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(path))
    conn.execute(_DDL)
    return conn


@dataclass
class EvalResultsStore:
    """Append-only BY KEY. `put` is idempotent-by-key: a present `(key, metric_name)` cell is
    SKIPPED (resumability), never overwritten (the append-only falsifier). `query` is the group-by
    substrate curves are built over. `path` accepts `":memory:"` (an ephemeral in-process DB, for
    tests) as well as a real on-disk `Path`."""

    path: Path | str
    _conn: duckdb.DuckDBPyConnection = None  # type: ignore[assignment]  # set in __post_init__

    def __post_init__(self) -> None:
        self._conn = _connect(self.path)

    def has(self, key: EvalKey, metric_name: str) -> bool:
        """The resume check: is this keyed cell already present?"""
        row = self._conn.execute(
            "SELECT 1 FROM eval_results WHERE spec_hash = ? AND corpus_ref = ? "
            "AND config_fingerprint = ? AND seed = ? AND metric_name = ? LIMIT 1",
            [key.spec_hash, key.corpus_ref, key.config_fingerprint, key.seed, metric_name],
        ).fetchone()
        return row is not None

    def put(self, r: Reading) -> bool:
        """Insert the reading unless its `(key, metric_name)` cell is already present. Returns True
        if inserted, False if skipped (already present) — NEVER overwrites, NEVER duplicates."""
        if self.has(r.key, r.metric_name):
            return False
        self._conn.execute(
            "INSERT INTO eval_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [r.key.spec_hash, r.key.corpus_ref, r.key.config_fingerprint, r.key.seed,
             r.metric_name, float(r.value), r.type_tag, r.interval_lo, r.interval_hi,
             r.evidence_ref],
        )
        return True

    def get(self, key: EvalKey, metric_name: str) -> Reading | None:
        row = self._conn.execute(
            "SELECT value, type_tag, interval_lo, interval_hi, evidence_ref FROM eval_results "
            "WHERE spec_hash = ? AND corpus_ref = ? AND config_fingerprint = ? AND seed = ? "
            "AND metric_name = ?",
            [key.spec_hash, key.corpus_ref, key.config_fingerprint, key.seed, metric_name],
        ).fetchone()
        if row is None:
            return None
        return Reading(key=key, metric_name=metric_name, value=row[0], type_tag=row[1],
                       interval_lo=row[2], interval_hi=row[3], evidence_ref=row[4])

    def query(self, *, metric_name: str | None = None,
              corpus_ref: str | None = None) -> list[Reading]:
        """The group-by substrate for curves. Filters compose (AND); no filter → all rows."""
        clauses: list[str] = []
        params: list[Any] = []
        if metric_name is not None:
            clauses.append("metric_name = ?")
            params.append(metric_name)
        if corpus_ref is not None:
            clauses.append("corpus_ref = ?")
            params.append(corpus_ref)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self._conn.execute(
            "SELECT spec_hash, corpus_ref, config_fingerprint, seed, metric_name, value, "
            "type_tag, interval_lo, interval_hi, evidence_ref FROM eval_results" + where
            + " ORDER BY spec_hash, corpus_ref, config_fingerprint, seed, metric_name",
            params,
        ).fetchall()
        return [
            Reading(
                key=EvalKey(spec_hash=row[0], corpus_ref=row[1], config_fingerprint=row[2],
                            seed=int(row[3])),
                metric_name=row[4], value=row[5], type_tag=row[6],
                interval_lo=row[7], interval_hi=row[8], evidence_ref=row[9],
            )
            for row in rows
        ]

    def close(self) -> None:
        self._conn.close()


def open_eval_store(config: Any = None) -> EvalResultsStore:
    """Open the configured eval-results store (its DuckDB file lives beside the derived store —
    the telemetry precedent). Import of `config.loader` is lazy so the module stays dependency-light
    and the isolation tooth sees no ingest coupling."""
    from config.loader import get_config

    config = config or get_config()
    return EvalResultsStore(config.paths.derived_store.parent / "eval_results.duckdb")
