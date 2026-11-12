"""Append-only store for attestation records + chain assembly (attestation-layer.md §4–5).

APPEND-ONLY IS STRUCTURAL: this class exposes `append` and reads, and deliberately NO `delete`
or `update`. There is no API to mutate or remove a record — the gate's purge-raw action appends
a *deletion attestation* rather than erasing history (attestation-layer.md §4). That makes the
audit trail tamper-evident-by-construction even before signatures land (Step 3).

Thread-safety mirrors the JobQueue fix (PROGRESS 2026-06-27): the vault watcher emits ingest
attestations from a spawned thread, so the connection is opened `check_same_thread=False` and
every method is guarded by a reentrant lock.

The producer lookups (which attestations name a hash among their outputs) read a side table of
the ledger, one row for each element of each record's `output_hashes` with the record's id and
action, keyed by the hash: a lookup is an index seek, where it was a decode of every record. The
table is written by a trigger on the ledger, so every append writes its rows in its own statement
and transaction, whatever process appends, and a rolled-back append leaves none. A ledger written
before the table existed gets it on its first open, filled from the records in one transaction.
That migration does not wait for the file's write lock: a process that opens the ledger while
another holds the lock, or one that cannot write the file, opens at once and answers the lookups
by one pass over the records, as the ledger answered them before the table, until the table
exists. The table is derived from the records and changes no record: the ledger stays
append-only.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from core.attestation.record import Attestation
from core.kernel.config import Config

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

# The output-hash side table: created, filled from the records and given its trigger in one
# transaction (`AttestationStore._migrate`), so its presence means it is complete. `pos` is the
# element's place in the record's `output_hashes`, so a record that names a hash twice has two
# rows, as the records do.
_OUTPUTS = (
    "CREATE TABLE output_hashes (hash TEXT NOT NULL, att_id TEXT NOT NULL, action TEXT NOT NULL, "
    "pos INTEGER NOT NULL, PRIMARY KEY (hash, att_id, pos)) WITHOUT ROWID",
    "INSERT INTO output_hashes (hash, att_id, action, pos) "
    "SELECT j.value, a.id, a.action, j.key FROM attestations a, "
    "json_each(a.payload_json, '$.output_hashes') j",
    "CREATE TRIGGER attestation_outputs AFTER INSERT ON attestations BEGIN "
    "INSERT INTO output_hashes (hash, att_id, action, pos) "
    "SELECT j.value, NEW.id, NEW.action, j.key FROM json_each(NEW.payload_json, "
    "'$.output_hashes') j; END",
)
_BATCH = 400
_TIMEOUT_S = 5.0          # how long a statement waits for another connection's lock
# a lock another connection holds, or a file this process cannot write
_UNWRITABLE = (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED, sqlite3.SQLITE_READONLY)


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
        self._defer = False
        self._conn = sqlite3.connect(str(self.path), timeout=_TIMEOUT_S,
                                     check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_DDL)
            self._conn.commit()
            self._indexed = self._migrate()

    def _has_outputs(self) -> bool:
        return self._conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' "
                                  "AND name = 'output_hashes'").fetchone() is not None

    def _migrate(self) -> bool:
        """Give a ledger written before the output-hash side table its table, its rows and its
        trigger, in one transaction (another process may have done it first: checked again
        inside); True once the table exists. The migration does not wait for the write lock:
        while another connection holds it, or when this process cannot write the file, nothing is
        written and the answer is False, and the lookups pass over the records until a later
        open or lookup finds the table or makes it. A crash midway leaves the ledger as it was,
        to be migrated at the next open."""
        if self._has_outputs():
            return True
        conn = self._conn
        if conn.in_transaction:         # inside a deferred block: its appends are not ours to end
            return False
        try:
            conn.execute("PRAGMA busy_timeout = 0")
            try:
                conn.execute("BEGIN IMMEDIATE")
            finally:
                conn.execute(f"PRAGMA busy_timeout = {int(_TIMEOUT_S * 1000)}")
            if not self._has_outputs():
                for statement in _OUTPUTS:
                    conn.execute(statement)
            conn.commit()
        except sqlite3.OperationalError as exc:
            conn.rollback()
            if (getattr(exc, "sqlite_errorcode", 0) & 0xFF) in _UNWRITABLE:
                return False
            raise
        except BaseException:
            conn.rollback()
            raise
        return True

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
            if not self._defer:
                self._conn.commit()
        return att

    @contextmanager
    def deferred(self) -> Iterator[None]:
        """The attestations appended inside commit once, at the end (a batch's, before its keys);
        an exception inside rolls them back."""
        with self._lock:
            self._defer = True
            try:
                yield
                self._conn.commit()
            except BaseException:
                self._conn.rollback()
                raise
            finally:
                self._defer = False

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

    def producers_by_output(self, hashes: set[str]) -> dict[str, list[tuple[str, str]]]:
        """Each hash's producers, (action, id), sorted, an attestation once for each time its
        outputs name the hash: what a batch of landings asks once instead of `producers_of` per
        landing, a seek of the output-hash table a hash."""
        out: dict[str, list[tuple[str, str]]] = {h: [] for h in hashes}
        for h, action, att_id in self._outputs(hashes, "hash, action, att_id"):
            out[str(h)].append((str(action), str(att_id)))
        return {h: sorted(ps) for h, ps in out.items()}

    def _outputs(self, hashes: set[str], columns: str) -> list[sqlite3.Row]:
        """The output-hash table's rows for the hashes (`columns` of `hash`, `att_id`, `action`),
        by seeks of its key, a statement a few hundred hashes; while the ledger has no table yet
        (`_migrate`), the same rows from one pass over the records. Reads alone: no transaction is
        opened, so no lock outlives the call."""
        wanted = list(hashes)
        rows: list[sqlite3.Row] = []
        with self._lock:
            if not self._indexed:
                self._indexed = self._migrate()
            if not self._indexed:
                return self._scanned(wanted, columns) if wanted else []
            for i in range(0, len(wanted), _BATCH):
                batch = wanted[i:i + _BATCH]
                rows += self._conn.execute(
                    f"SELECT {columns} FROM output_hashes WHERE hash IN "
                    f"({', '.join('?' for _ in batch)})", batch).fetchall()
        return rows

    def _scanned(self, wanted: list[str], columns: str) -> list[sqlite3.Row]:
        """`_outputs`'s rows from the records themselves, for a ledger without the table: one
        pass of SQLite's JSON functions over every record, the hashes asked for given as one JSON
        array (no temporary table, so no transaction)."""
        names = {"hash": "j.value", "att_id": "a.id", "action": "a.action"}
        select = ", ".join(f"{names[c.strip()]} AS {c.strip()}" for c in columns.split(","))
        return self._conn.execute(
            f"SELECT {select} FROM attestations a, json_each(a.payload_json, '$.output_hashes') j "
            "WHERE j.value IN (SELECT value FROM json_each(?))", [json.dumps(wanted)]).fetchall()

    def producers_of(self, hashes: set[str]) -> set[str]:
        """Ids of attestations whose `output_hashes` intersect `hashes` — the attestations that
        PRODUCED any of those outputs. This is the chain-linking lookup: an action consuming
        hash h derives from whatever attested producing h (attestation-layer.md §2)."""
        return {str(r[0]) for r in self._outputs(hashes, "att_id")}

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
    from core.kernel.config import get_config

    cfg = config or get_config()
    return AttestationStore(cfg.paths.attestation_store)
