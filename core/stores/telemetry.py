"""DuckDB telemetry store (BUILD-SPEC §8).

Quantitative time-series — *system vitals only* at launch (the system is itself a
sensor source). Access is scoped in code (CONVENTIONS): a `TelemetryWriter` has no read
methods and a `TelemetryReader` has no write methods, so the wrong access is impossible,
not merely discouraged. The dormant `sensor_readings` table is the body/health adapter
target, built now so a wearable can later emit into the same store without rework
(§8, §20.6) — no adapter writes to it yet.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb

SCHEMA_VERSION = 2

_DDL = [
    """CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at TIMESTAMP NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS vitals (
        ts TIMESTAMP NOT NULL,
        metric VARCHAR NOT NULL,
        value DOUBLE NOT NULL,
        unit VARCHAR,
        source VARCHAR NOT NULL,
        labels VARCHAR              -- JSON object, or NULL
    );""",
    # Dormant: body/health sensor adapter target (§8, §20.6). Defined now; unused until
    # a wearable adapter is added. Kept structurally separate from system `vitals`.
    """CREATE TABLE IF NOT EXISTS sensor_readings (
        ts TIMESTAMP NOT NULL,
        sensor VARCHAR NOT NULL,
        metric VARCHAR NOT NULL,
        value DOUBLE NOT NULL,
        unit VARCHAR,
        meta VARCHAR
    );""",
    # v2: context-budget usage per agent/job (BUILD-SPEC §13) — budgets, drops, overflows
    # and escalations are visible so window right-sizing (§14 safe-lever) has data to learn from.
    """CREATE TABLE IF NOT EXISTS context_usage (
        ts TIMESTAMP NOT NULL,
        agent VARCHAR NOT NULL,
        job_id VARCHAR,
        tier VARCHAR,
        ctx_window INTEGER,         -- "window" is a DuckDB reserved word
        used_tokens INTEGER,
        retrieved_kept INTEGER,
        retrieved_dropped INTEGER,
        history_dropped INTEGER,
        tool_truncated INTEGER,
        escalated BOOLEAN
    );""",
]


def _utcnow() -> datetime:
    # Naive UTC: the TIMESTAMP columns are tz-naive, so we keep one consistent clock.
    return datetime.now(UTC).replace(tzinfo=None)


def _connect(path: Path) -> duckdb.DuckDBPyConnection:
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(path))
    for ddl in _DDL:
        conn.execute(ddl)
    row = conn.execute("SELECT max(version) FROM schema_migrations").fetchone()
    current = row[0] if row and row[0] is not None else 0
    if current < SCHEMA_VERSION:
        # All DDL above is idempotent (IF NOT EXISTS), so an older DB gains the new tables
        # on open; record the version bump.
        conn.execute("INSERT INTO schema_migrations VALUES (?, ?)", [SCHEMA_VERSION, _utcnow()])
    return conn


@dataclass
class TelemetryWriter:
    """Write-only handle. No read methods exist on this object BY DESIGN (scoped access)."""

    _conn: duckdb.DuckDBPyConnection

    def record_vital(self, metric: str, value: float, *, unit: str | None = None,
                     source: str = "core", labels: dict[str, Any] | None = None) -> None:
        self._conn.execute(
            "INSERT INTO vitals VALUES (?, ?, ?, ?, ?, ?)",
            [_utcnow(), metric, float(value), unit, source,
             json.dumps(labels) if labels else None],
        )

    def record_vitals(self, readings: Iterable[Any], *, source: str = "core") -> None:
        """Bulk-write objects exposing .metric/.value/.unit/.labels (e.g. vitals.Reading)."""
        for r in readings:
            self.record_vital(r.metric, r.value, unit=r.unit,
                              source=source, labels=getattr(r, "labels", None))

    def record_context_usage(self, agent: str, report: Any, *,
                             job_id: str | None = None, tier: str | None = None) -> None:
        """Record a context-budget outcome (BUILD-SPEC §13). `report` is duck-typed (a
        scheduler.budget.BudgetReport) so telemetry stays independent of the scheduler."""
        self._conn.execute(
            "INSERT INTO context_usage VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [_utcnow(), agent, job_id, tier, report.window, report.used_tokens,
             report.retrieved_kept, report.retrieved_dropped, report.history_dropped,
             report.tool_truncated, report.escalate],
        )


@dataclass
class TelemetryReader:
    """Read-only handle. No write methods exist on this object BY DESIGN (scoped access)."""

    _conn: duckdb.DuckDBPyConnection

    def latest(self, metric: str) -> float | None:
        row = self._conn.execute(
            "SELECT value FROM vitals WHERE metric = ? ORDER BY ts DESC LIMIT 1", [metric]
        ).fetchone()
        return row[0] if row else None

    def count(self, metric: str | None = None) -> int:
        if metric is None:
            row = self._conn.execute("SELECT count(*) FROM vitals").fetchone()
        else:
            row = self._conn.execute(
                "SELECT count(*) FROM vitals WHERE metric = ?", [metric]
            ).fetchone()
        return int(row[0]) if row else 0

    def window(self, metric: str, seconds: float) -> list[tuple[datetime, float]]:
        cutoff = _utcnow() - timedelta(seconds=seconds)
        return self._conn.execute(
            "SELECT ts, value FROM vitals WHERE metric = ? AND ts >= ? ORDER BY ts",
            [metric, cutoff],
        ).fetchall()

    def context_usage_count(self, agent: str | None = None) -> int:
        if agent is None:
            row = self._conn.execute("SELECT count(*) FROM context_usage").fetchone()
        else:
            row = self._conn.execute(
                "SELECT count(*) FROM context_usage WHERE agent = ?", [agent]
            ).fetchone()
        return int(row[0]) if row else 0


@dataclass
class TelemetryStore:
    path: Path
    _conn: duckdb.DuckDBPyConnection = field(init=False)

    def __post_init__(self) -> None:
        self._conn = _connect(self.path)

    def writer(self) -> TelemetryWriter:
        return TelemetryWriter(self._conn)

    def reader(self) -> TelemetryReader:
        return TelemetryReader(self._conn)

    def close(self) -> None:
        self._conn.close()


def open_store(config: Any = None) -> TelemetryStore:
    from config.loader import get_config

    config = config or get_config()
    return TelemetryStore(config.paths.telemetry_db)
