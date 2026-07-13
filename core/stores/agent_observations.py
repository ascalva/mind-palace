# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    the agent-observation stratum — where φ_self's per-commit, cost-stream
#            readings land (dn-self-sensing.md §2.3, B-b).
# INVARIANT: every row is ρ ≡ observed; a wrong-class row is UNREPRESENTABLE at this
#            boundary — no provenance parameter exists anywhere in this module's API.
# ENFORCED:  structural — `AgentObservation.to_row()` and `AgentObservationStore.add_batch()`
#            hardcode `Provenance.OBSERVED` (the CodeObservation/SensedObservation mint
#            discipline, verbatim); identity key (commit_sha, stream, subject_id, key):
#            same-interpreter re-projection is idempotent (the B-b falsifier, inverted);
#            a DIFFERENT interpreter archives-then-replaces (§2.2 versioned supersession
#            — the main table holds exactly latest-per-identity by construction).
"""OBSERVED-only store for agent (self-sensing) observations (ratified self-sensing.md B-b).

One row = one fact reading of one commit: the agent's own operation is the THIRD stream
through the sensing seam (after the biometric stream and the code stream, bp-012), and the
self sensor (`ops/self_sensor.py`) is the sole interpreter φ_self (§2.2 — deterministic,
transform-attributed, sole path in, stateless). Observations enter through the
`AgentSensingHandoff` seam (`core/sensing.py`, the sensing-seam's third sibling) and land
here wearing `observed` — there is deliberately NO provenance parameter on any API surface,
so a caller physically cannot launder an agent reading into an authored (or any other)
class: the same structural move as `DerivedStore.add`, `SensedObservation.to_row`, and
`CodeObservation.to_row`.

This plan (B-b) licenses exactly ONE stream: `stream == 'cost'` (build-plan `cost:`
frontmatter blocks — estimate at the plan's landing commit, actual at its seal commit).
Additional streams re-enter per-stream with their own small plans (note PD-a) — this store's
schema is stream-generic (the `stream` column), but nothing in THIS plan projects anything
else.

Mirror-opacity (§2.6): `observed` is not in `MIRROR_READABLE`, so a `MirrorView` refuses
these rows by construction and the self-model never reads them. The only typed container
is `ObservedView` (`all_rows` returns view-compatible dict rows).

HONESTY NOTE (finding-0020 class, code-store precedent): no consumer reads these rows yet
(bp-019 non-goal §9 — "any consumer (nothing reads ObservedView here)"). This store is
write-side only; the live first projection over history is bp-020's, deliberately deferred.

Engine: SQLite (plan Q6) — an identity-keyed append-style ledger, the runs/versions/
snapshots convention, not the DuckDB telemetry lane. Reset semantics (plan §6(h)): this
store is CORPUS-side (the observed stratum) and joins `reset_targets()` — wiped with the
corpus, unlike the snapshot LEDGER pattern. That corpus-side call covers current READINGS
only, which rebuild by re-projection from git; the worldview HISTORY — generations
superseded when a bumped interpreter re-projects — lives in the ledger-class, reset-guarded
sidecar (`core/stores/observation_history.py`, discriminator `store='agent'`;
dn-self-sensing §2.5 ruling).
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
from core.stores.observation_history import ObservationHistoryStore

_DDL = """
CREATE TABLE IF NOT EXISTS agent_observations (
    commit_sha   TEXT NOT NULL,   -- time coordinate — the commit that landed the fact
    stream       TEXT NOT NULL,   -- 'cost' ONLY in this plan (S1; other streams unlicensed)
    subject_id   TEXT NOT NULL,   -- the artifact the reading is about, e.g. 'bp-011'
    key          TEXT NOT NULL,   -- stream-scoped fact name: 'estimate' | 'actual'
    payload      TEXT NOT NULL,   -- JSON
    interpreter  TEXT NOT NULL,   -- phi_self version (outside the identity key)
    provenance   TEXT NOT NULL,   -- always 'observed' (nothing else is written)
    observed_at  TEXT NOT NULL,
    PRIMARY KEY (commit_sha, stream, subject_id, key)
);
-- Projection bookkeeping (NOT part of the §2.3 schema): which commits phi_self has already
-- projected UNDER WHICH interpreter version, and the attested batch content hash. Lets a
-- zero-fact commit be a recorded no-op instead of re-projecting forever, and — version-keyed
-- from birth (§6(a) shape, the bp-018 pattern) — makes every commit eligible again after an
-- interpreter bump.
CREATE TABLE IF NOT EXISTS projections (
    commit_sha   TEXT NOT NULL,
    interpreter  TEXT NOT NULL,
    batch_hash   TEXT NOT NULL,
    projected_at TEXT NOT NULL,
    PRIMARY KEY (commit_sha, interpreter)
);
"""


class MissingHistoryError(RuntimeError):
    """A superseding write arrived with `history=None` — refusing to silently drop a
    worldview generation (the bp-018 §6(c) archive-then-replace discipline, verbatim)."""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass(frozen=True)
class AgentObservation:
    """One fact reading of one commit (note §2.3, verbatim columns).

    Deliberately has NO provenance field: like `CodeObservation`/`SensedObservation`, the
    class label is minted at `to_row()` with no parameter — the wire payload (`to_dict`)
    carries nothing a caller could forge a class with."""

    commit_sha: str
    stream: str
    subject_id: str
    key: str
    payload: dict[str, Any]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AgentObservation:
        """Parse one handoff wire payload (the seam's inbound half, the sibling shape)."""
        return cls(
            commit_sha=str(d.get("commit_sha", "")),
            stream=str(d.get("stream", "")),
            subject_id=str(d.get("subject_id", "")),
            key=str(d.get("key", "")),
            payload=dict(d.get("payload", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """The handoff wire payload — schema fields only, NO provenance (nothing to forge)."""
        return {
            "commit_sha": self.commit_sha,
            "stream": self.stream,
            "subject_id": self.subject_id,
            "key": self.key,
            "payload": dict(self.payload),
        }

    def to_row(self) -> dict[str, Any]:
        """The observed-tier row. Provenance is HARDCODED — there is no parameter, so no
        caller can launder an agent reading into another class (the `CodeObservation.to_row`
        move, verbatim). `ObservedView` admits these rows; `MirrorView` refuses them (§2.6)."""
        return {**self.to_dict(), "provenance": Provenance.OBSERVED.value}


def batch_content_hash(observations: Iterable[AgentObservation]) -> str:
    """Content hash of a projection batch — sha256 over the canonical (sorted-key, sorted-row)
    JSON of the wire payloads. Deterministic (§2.2): re-running φ_self over the same commit
    yields the same hash, so the `project_agent_observations` attestation is content-addressed.
    Sort key: (commit_sha, stream, subject_id, key) — the identity key, module-local (this
    store's own copy; §11 parked decision — a fourth stream re-decides the shared-helper
    question)."""
    rows = sorted((o.to_dict() for o in observations),
                  key=lambda r: (r["commit_sha"], r["stream"], r["subject_id"], r["key"]))
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class AgentObservationStore:
    """The observed stratum's agent-observation table. Writes `observed` UNCONDITIONALLY —
    no method on this class accepts a provenance value (Item 5 falsifier, ruled out by
    construction and pinned by test)."""

    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def add_batch(self, observations: Iterable[AgentObservation], *,
                  interpreter: str,
                  history: ObservationHistoryStore | None = None) -> tuple[int, int]:
        """Land one projection batch under a declared interpreter version. Returns
        (new rows, superseded rows). Three cases per identity key (§6(b)):

        - no existing row → INSERT (a new reading);
        - existing row, SAME interpreter → no-op (idempotence — the B-b falsifier, inverted);
        - existing row, DIFFERENT interpreter → archive the existing generation to
          `history` (store='agent'), then replace: versioned supersession (§2.2), and
          the main table stays exactly latest-per-identity by construction. A
          superseding write with `history=None` raises `MissingHistoryError` — a
          generation is never silently dropped."""
        added = superseded = 0
        with self._conn:
            for o in observations:
                existing = self._conn.execute(
                    "SELECT * FROM agent_observations "
                    "WHERE commit_sha = ? AND stream = ? AND subject_id = ? AND key = ?",
                    [o.commit_sha, o.stream, o.subject_id, o.key]).fetchone()
                if existing is not None and existing["interpreter"] == interpreter:
                    continue
                if existing is not None:
                    if history is None:
                        raise MissingHistoryError(
                            f"superseding ({o.commit_sha}, {o.stream}, {o.subject_id}, "
                            f"{o.key}) [{existing['interpreter']} → {interpreter}] with no "
                            f"history store — a worldview generation would be silently dropped")
                    history.archive("agent", [(self._row(existing),
                                               str(existing["interpreter"]), interpreter)])
                    superseded += 1
                else:
                    added += 1
                self._conn.execute(
                    "INSERT OR REPLACE INTO agent_observations "
                    "(commit_sha, stream, subject_id, key, payload, interpreter, "
                    " provenance, observed_at) VALUES (?,?,?,?,?,?,?,?)",
                    [o.commit_sha, o.stream, o.subject_id, o.key,
                     json.dumps(o.payload, sort_keys=True), interpreter,
                     Provenance.OBSERVED.value, _utcnow()],
                )
        return added, superseded

    # --- reads (view-compatible dict rows) ----------------------------------------------
    def all_rows(self, *,
                 provenances: Iterable[Provenance] | None = None) -> list[dict[str, Any]]:
        """Full scan, optionally restricted to provenance classes (the `RowSource` shape).
        Every stored row is `observed`, so a filter containing OBSERVED sees ALL rows and
        any filter excluding it sees NONE — there is no third case."""
        rows = [self._row(r) for r in self._conn.execute(
            "SELECT * FROM agent_observations ORDER BY commit_sha, stream, subject_id, key"
        ).fetchall()]
        if provenances is None:
            return rows
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in rows if r["provenance"] in allowed]

    def rows_for(self, commit_sha: str) -> list[dict[str, Any]]:
        return [self._row(r) for r in self._conn.execute(
            "SELECT * FROM agent_observations WHERE commit_sha = ? "
            "ORDER BY stream, subject_id, key",
            [commit_sha],
        ).fetchall()]

    def count(self) -> int:
        row = self._conn.execute("SELECT count(*) FROM agent_observations").fetchone()
        return int(row[0]) if row else 0

    # --- projection bookkeeping (φ_self's idempotency ledger, version-keyed from birth) ----
    def is_projected(self, commit_sha: str, interpreter: str | None = None) -> bool:
        """Was `commit_sha` projected under `interpreter`? With `interpreter=None`: under
        ANY interpreter (the any-generation read, kept for parity with the code store's
        finding-0047 shape). The sensor always passes its version."""
        if interpreter is None:
            return self._conn.execute(
                "SELECT 1 FROM projections WHERE commit_sha = ?", [commit_sha]
            ).fetchone() is not None
        return self._conn.execute(
            "SELECT 1 FROM projections WHERE commit_sha = ? AND interpreter = ?",
            [commit_sha, interpreter],
        ).fetchone() is not None

    def mark_projected(self, commit_sha: str, content_hash: str, interpreter: str) -> None:
        """Record that φ_self-at-`interpreter` projected `commit_sha`. INSERT OR IGNORE
        on (commit_sha, interpreter): first mark per worldview wins, and a NEW interpreter's
        mark is a NEW row — the versioned supersession §2.2 promises."""
        with self._conn:
            self._conn.execute("INSERT OR IGNORE INTO projections VALUES (?,?,?,?)",
                               [commit_sha, interpreter, content_hash, _utcnow()])

    def chain_for(self, commit_sha: str, stream: str, subject_id: str, key: str,
                  history: ObservationHistoryStore) -> list[dict[str, Any]]:
        """The queryable worldview chain at one identity key (§2.4): archived
        generations + the current row, oldest → current. Each element carries its own
        `interpreter` — the second orthogonal history (across interpreter at fixed
        identity), readable without touching default reads."""
        identity = {"commit_sha": commit_sha, "stream": stream,
                    "subject_id": subject_id, "key": key}
        chain = history.chain("agent", identity)
        current = self._conn.execute(
            "SELECT * FROM agent_observations "
            "WHERE commit_sha = ? AND stream = ? AND subject_id = ? AND key = ?",
            [commit_sha, stream, subject_id, key]).fetchone()
        if current is not None:
            chain.append(self._row(current))
        return chain

    @staticmethod
    def _row(r: sqlite3.Row) -> dict[str, Any]:
        d = dict(r)
        d["payload"] = json.loads(d["payload"])
        return d

    def close(self) -> None:
        self._conn.close()


def open_agent_observation_store(config: Config | None = None) -> AgentObservationStore:
    """The `open_*` helper: `data/agent_observations.sqlite` (plan §6(b) — the sibling-store
    convention beside `code_observations`, no dedicated cfg path; registered in
    `reset_targets()` as a corpus-side wipe target, plan §6(h))."""
    from config.loader import get_config

    cfg = config or get_config()
    return AgentObservationStore(cfg.paths.data_dir / "agent_observations.sqlite")
