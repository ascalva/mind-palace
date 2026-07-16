"""The run ledger — the harness's append-only record of dream runs + claims (E2, bp-043).

Carried from Track L L1 (the protocol annex of record in the superseded
`live-adoption-and-longitudinal-harness.md` §2 — its `dream_runs` / `dream_claims` column lists are
honored VERBATIM here). Two append-only tables:

* **`dream_runs`** — one row per (pipeline, snapshot) execution (phase7 | dream_v2), carrying the
  run's `config_fingerprint` + `corpus_digest` (so two pipelines over "one snapshot" are provably
  comparable — dn-evaluation-harness §2.2) and cheap descriptive stats.
* **`dream_claims`** — one row per claim, addressed by a **content-addressed `claim_id`**
  `= sha256(kind ‖ canonical(support) ‖ polarity)` — EXCLUDING surface wording + confidence (§2.2):
  "the same tension, found twice" is one id, however it was worded. `novel` is computed ON INSERT
  against ALL prior runs (an INDEX on `claim_id` backs the check), so re-emitted claims are marked
  `novel=False` and inherit prior verdicts (E6's job).

SQLite/WAL, **scheduler single-writer** (`scheduler/__init__.py` — one supervisor owns the queue;
the run ledger follows the same discipline, written only by the trough handler in production; unit
tests write a tmp/`:memory:` ledger directly). Append-only: no update, no delete. This store holds
no model and no network — it is a passive record. The distinct SQLite engine (not E1's DuckDB
eval-results table) is the A-4 routing pin: the access pattern here is point lookups + inserts, not
analytical group-by.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# --- content-addressed claim identity (dn-evaluation-harness §2.2) -----------------------------


def claim_id(kind: str, support: tuple[str, ...], polarity: str) -> str:
    """Content-address a claim EXCLUDING its surface wording + confidence (§2.2). The canonical
    support set is `sorted(set(...))` so identity is order-insensitive and duplicate-insensitive
    — "the same pattern, found twice" hashes to one id."""
    canon = json.dumps(sorted(set(support)), separators=(",", ":"))
    return hashlib.sha256(f"{kind}‖{canon}‖{polarity}".encode()).hexdigest()


# The method -> polarity map (§3 Q3). The keys are the interpreter `method` names
# (`core/dreaming/interpreters.py:56-64`), kept as string literals so this low-level store does not
# import the dreaming layer. TENSION is the only "-" (a frustrated commitment); the gap/theme/hub
# family is "+". A method with no explicit mapping defaults "+" and is FLAGGED (a sensible default
# exists, so this is not a §10 stop — the flag lets a caller log the gap).
_POLARITY: dict[str, str] = {
    "tension": "-",
    "community": "+",
    "theme": "+",
    "hole": "+",
    "thread": "+",
}
DEFAULT_POLARITY = "+"


def polarity_for(kind: str) -> str:
    """The polarity of a claim `kind` for `claim_id` (§3 Q3). Unmapped kinds default `+`."""
    return _POLARITY.get(kind, DEFAULT_POLARITY)


def polarity_and_flag(kind: str) -> tuple[str, bool]:
    """`(polarity, defaulted)` — `defaulted=True` when `kind` has no explicit polarity mapping and
    fell back to `+` (§3 Q3's "unknown -> + flagged"). Lets a caller log the under-specified kind
    once per run rather than silently."""
    if kind in _POLARITY:
        return _POLARITY[kind], False
    return DEFAULT_POLARITY, True


# --- the store ---------------------------------------------------------------------------------

_DDL = [
    # dream_runs — columns VERBATIM from the L1 annex (§2 / plan §6).
    """CREATE TABLE IF NOT EXISTS dream_runs (
        run_id             TEXT PRIMARY KEY,
        started_at         TEXT NOT NULL,          -- ISO-8601 UTC timestamp
        pipeline           TEXT NOT NULL,          -- "phase7" | "dream_v2"
        config_fingerprint TEXT NOT NULL,
        corpus_digest      TEXT NOT NULL,
        node_count         INTEGER NOT NULL,
        edge_count         INTEGER NOT NULL,
        duration_s         REAL NOT NULL,
        spectral_stats_json TEXT NOT NULL
    );""",
    # dream_claims — claim_id content-addressed (§2.2); novel computed on insert.
    """CREATE TABLE IF NOT EXISTS dream_claims (
        claim_id     TEXT NOT NULL,
        run_id       TEXT NOT NULL,                -- FK -> dream_runs.run_id
        kind         TEXT NOT NULL,
        confidence   REAL NOT NULL,
        support_json TEXT NOT NULL,
        surface_text TEXT NOT NULL,
        novel        INTEGER NOT NULL              -- BOOLEAN 0/1
    );""",
    # The novel check queries by claim_id across ALL prior runs — index it (§3 risk b).
    "CREATE INDEX IF NOT EXISTS idx_dream_claims_claim_id ON dream_claims(claim_id);",
]


def _connect(path: Path | str) -> sqlite3.Connection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    # WAL: concurrent readers alongside the single writer (:memory: reports "memory" — harmless).
    conn.execute("PRAGMA journal_mode=WAL")
    for ddl in _DDL:
        conn.execute(ddl)
    conn.commit()
    return conn


@dataclass
class RunLedger:
    """Append-only SQLite/WAL ledger. Writes (`start_run`, `add_claim`) and reads (`runs`,
    `claims`) are distinct method groups over one single-writer handle (SQLite single-writer
    discipline, §3 Q5). `path` accepts `":memory:"` for tests as well as a real on-disk `Path`."""

    path: Path | str
    _conn: sqlite3.Connection = None  # type: ignore[assignment]  # set in __post_init__

    def __post_init__(self) -> None:
        self._conn = _connect(self.path)

    # -- writes -------------------------------------------------------------------------------
    def start_run(self, *, pipeline: str, config_fingerprint: str, corpus_digest: str,
                  node_count: int, edge_count: int, duration_s: float,
                  spectral_stats: dict[str, Any]) -> str:
        """Open a run (one (pipeline, snapshot) execution) and return its fresh `run_id`. A run is
        an EVENT — a new id every invocation even for the same snapshot (claims carry the identity,
        runs carry the occurrence)."""
        run_id = uuid.uuid4().hex
        from datetime import UTC, datetime
        started_at = datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")
        self._conn.execute(
            "INSERT INTO dream_runs (run_id, started_at, pipeline, config_fingerprint, "
            "corpus_digest, node_count, edge_count, duration_s, spectral_stats_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [run_id, started_at, pipeline, config_fingerprint, corpus_digest,
             int(node_count), int(edge_count), float(duration_s),
             json.dumps(spectral_stats, sort_keys=True, separators=(",", ":"))],
        )
        self._conn.commit()
        return run_id

    def add_claim(self, run_id: str, *, kind: str, confidence: float,
                  support: tuple[str, ...], surface_text: str, polarity: str) -> bool:
        """Append one claim; compute its `claim_id` + `novel` (unseen `claim_id` across ALL prior
        runs, this row included on re-emit within the same run). Returns `novel`. Append-only:
        a re-emitted claim is a NEW row marked `novel=False`, never an update of the first."""
        cid = claim_id(kind, support, polarity)
        seen = self._conn.execute(
            "SELECT 1 FROM dream_claims WHERE claim_id = ? LIMIT 1", [cid]
        ).fetchone()
        novel = seen is None
        self._conn.execute(
            "INSERT INTO dream_claims (claim_id, run_id, kind, confidence, support_json, "
            "surface_text, novel) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [cid, run_id, kind, float(confidence),
             json.dumps(sorted(set(support)), separators=(",", ":")),
             surface_text, 1 if novel else 0],
        )
        self._conn.commit()
        return novel

    # -- reads --------------------------------------------------------------------------------
    def runs(self, *, pipeline: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM dream_runs"
        params: list[Any] = []
        if pipeline is not None:
            sql += " WHERE pipeline = ?"
            params.append(pipeline)
        sql += " ORDER BY started_at, run_id"
        return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def claims(self, *, run_id: str | None = None,
               novel_only: bool = False) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if run_id is not None:
            clauses.append("run_id = ?")
            params.append(run_id)
        if novel_only:
            clauses.append("novel = 1")
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self._conn.execute(
            "SELECT * FROM dream_claims" + where + " ORDER BY rowid", params
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self._conn.close()


def open_run_ledger(config: Any = None) -> RunLedger:
    """Open the configured run ledger — its SQLite file lives beside the derived store (the
    telemetry precedent). Import of `config.loader` is lazy so the module stays dependency-light."""
    from config.loader import get_config

    config = config or get_config()
    return RunLedger(config.paths.derived_store.parent / "run_ledger.sqlite")
