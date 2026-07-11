"""Append-only store for attestation records + chain assembly (attestation-layer.md §4–5).

APPEND-ONLY IS STRUCTURAL: this class exposes `append` and reads, and deliberately NO `delete`
or `update`. There is no API to mutate or remove a record — the gate's purge-raw action appends
a *deletion attestation* rather than erasing history (attestation-layer.md §4). That makes the
audit trail tamper-evident-by-construction even before signatures land (Step 3).

Thread-safety mirrors the JobQueue fix (PROGRESS 2026-06-27): the vault watcher emits ingest
attestations from a spawned thread, so the connection is opened `check_same_thread=False` and
every method is guarded by a reentrant lock.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from config.loader import Config
from core.attestation.record import Attestation

_DDL = """
CREATE TABLE IF NOT EXISTS attestations (
    id           TEXT PRIMARY KEY,
    timestamp    TEXT NOT NULL,
    agent_role   TEXT NOT NULL,
    action       TEXT NOT NULL,
    payload_json TEXT NOT NULL,          -- the full Attestation record as JSON
    signature    TEXT NOT NULL,          -- '' until Step 3
    signer       TEXT NOT NULL           -- '' until Step 3
);
CREATE INDEX IF NOT EXISTS att_role_ts ON attestations(agent_role, timestamp);
"""


@dataclass(frozen=True)
class AttestationChain:
    """The transitive closure of an attestation and the prior attestations it derived from."""

    root_id: str
    attestations: tuple[Attestation, ...]
    complete: bool   # every derived_from_id in the closure resolved to a stored attestation

    def is_complete(self) -> bool:
        """No broken links AND the root itself was found."""
        return self.complete and bool(self.attestations)

    def leaves(self) -> tuple[Attestation, ...]:
        """Attestations with no parents — the bottom of the chain (e.g. ingest attestations,
        whose inputs are authored content digests)."""
        return tuple(a for a in self.attestations if not a.derived_from_ids)

    def leaf_input_hashes(self) -> set[str]:
        hashes: set[str] = set()
        for a in self.leaves():
            hashes.update(a.input_hashes)
        return hashes

    def roles(self) -> set[str]:
        return {a.agent_role for a in self.attestations}

    def constitution_fingerprints(self) -> set[str]:
        return {a.constitution_fingerprint for a in self.attestations}

    def verify_signatures(self, verify: Callable[[Attestation], bool]) -> bool:
        """Step-3 hook: True iff `verify(att)` holds for every link. The caller supplies the
        verifier appropriate to the phase (unsigned records have no signature to check)."""
        return all(verify(a) for a in self.attestations)


@dataclass
class AttestationStore:
    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_DDL)
            self._conn.commit()

    def append(self, att: Attestation) -> Attestation:
        """Insert one attestation. Append-only: an id already present is left untouched
        (INSERT OR IGNORE), never overwritten. Ids are content-addressed, so a collision is a
        re-emission of the identical record — a no-op, not a conflict."""
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO attestations VALUES (?, ?, ?, ?, ?, ?, ?)",
                [att.id, att.timestamp, att.agent_role, att.action,
                 json.dumps(att.to_dict(), separators=(",", ":")),
                 att.signature, att.signer],
            )
            self._conn.commit()
        return att

    def get(self, att_id: str) -> Attestation | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT payload_json FROM attestations WHERE id = ?", [att_id]
            ).fetchone()
        return Attestation.from_dict(json.loads(row["payload_json"])) if row else None

    def all(self) -> list[Attestation]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT payload_json FROM attestations ORDER BY timestamp, id"
            ).fetchall()
        return [Attestation.from_dict(json.loads(r["payload_json"])) for r in rows]

    def by_role(self, role: str) -> list[Attestation]:
        return [a for a in self.all() if a.agent_role == role]

    def producers_of(self, hashes: set[str]) -> set[str]:
        """Ids of attestations whose `output_hashes` intersect `hashes` — the attestations that
        PRODUCED any of those outputs. This is the chain-linking lookup: an action consuming
        hash h derives from whatever attested producing h (attestation-layer.md §2)."""
        if not hashes:
            return set()
        return {a.id for a in self.all() if hashes & set(a.output_hashes)}

    def chain_for(self, att_id: str) -> AttestationChain:
        """Assemble the transitive closure following `derived_from_ids`. `complete` is False if
        any referenced parent (or the root) is absent — a broken link."""
        seen: dict[str, Attestation] = {}
        complete = True
        stack = [att_id]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            att = self.get(cur)
            if att is None:
                complete = False
                continue
            seen[cur] = att
            stack.extend(att.derived_from_ids)
        return AttestationChain(root_id=att_id, attestations=tuple(seen.values()),
                                complete=complete)

    def count(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT count(*) FROM attestations").fetchone()
        return int(row[0]) if row else 0

    def close(self) -> None:
        with self._lock:
            self._conn.close()


def open_attestation_store(config: Config | None = None) -> AttestationStore:
    from config.loader import get_config

    cfg = config or get_config()
    return AttestationStore(cfg.paths.attestation_store)
