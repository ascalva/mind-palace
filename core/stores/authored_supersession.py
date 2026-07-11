# ── Family 1 · provenance layer (authored-historical supersession, NOT the edge graph) ──
# OBJECT:    append-only OWNER-DECLARED authored-historical supersessions — a K₀↔K₀ supersession
#            across two DOCUMENTS (the-edge-model.md §4a; build plan Item 8 / 8f, PD11).
# INVARIANT: append-only; every write carries OWNER authority (a construction-guarded
#            `OwnerDeclaration`) or is REFUSED at this boundary (fail-closed, STRUCTURAL — not
#            "no machine path calls it"); the balance math has no handle here (never A_geom).
# ENFORCED:  structural — `record()` verifies the capability itself and raises
#            `MachineAuthorityRefused` otherwise, so a careless future caller (a shared helper,
#            a batch tool, a dreamer routed through the same function) is rejected here.
"""Owner-declared authored-historical supersession store (the-edge-model.md §4a; PD11).

A K₀↔K₀ supersession — "authored document B supersedes authored document A" — is a THIRD
dispositional edge type, distinct from note-version `supersedes` (versions of ONE `doc_id`,
`core/stores/versions.py`) and claim `supersede` (dialogue, `core/recursion_ops.py`).
It connects two documents, carries no warrant, mints no derived alternative; both endpoints
stay authored.

**Ungated only because it is owner-declared — enforced HERE, structurally.** The "no verdict gate"
property rests on it being the owner's hand. A supersession between two authored notes CAN
be machine-derived (Item 10's `s(C,D)` over authored `E_geom`; the curator finder), so
ungated-ness follows the AUTHORITY, not the edge type. This store admits ONLY an owner-declared
write: `record()` requires an `OwnerDeclaration` and verifies it at the boundary, so fail-closed
survives a careless future caller (capability-dissolution, `the-sacred-boundary.md` §3 — the
machine-write capability is removed, not guarded with a forgeable flag). A machine-inferred
authored↔authored supersession is a dreamer-proposed candidate for the blessing gate
(`supersession-lifecycle.md` §3), never a row here.

Append-only, keyed on the two authored digests; `superseded()` is the active-projection filter
(the superseded digest leaves the active view, as `ClaimOpStore.superseded` did — but the write is
owner-authorized). Ordering is the append `at` timestamp, never edge topology. Zone A, no network.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from config.loader import Config

# Private construction guard: only `owner_declaration()` holds it, so a valid `OwnerDeclaration`
# cannot be fabricated by a caller that merely imports this module (a model/scheduler/dreamer path).
_OWNER_TOKEN: Final = object()


class MachineAuthorityRefused(PermissionError):
    """A write to the authored-historical store carried no valid OWNER authority — refused at the
    store's own boundary (fail-closed, STRUCTURAL). This is the guarantee the owner-declared-only
    design exists for: a machine/model/scheduler/dreamer caller is rejected HERE, so the rule holds
    even if a future refactor routes a machine call through what used to be an owner-only path."""


@dataclass(frozen=True)
class OwnerDeclaration:
    """Capability proving a supersession is OWNER-ASSERTED (a founding manifest / an owner CLI), not
    machine-derived. Construction-guarded: a direct `OwnerDeclaration()` raises, because only
    `owner_declaration()` passes the module-private token. Holding a store reference is thus not
    enough to write it — a caller must present owner authority the store can verify."""

    _token: object = None

    def __post_init__(self) -> None:
        if self._token is not _OWNER_TOKEN:
            raise MachineAuthorityRefused(
                "OwnerDeclaration is construction-guarded — mint via owner_declaration() from an "
                "owner-operated entry point; a model/scheduler/dreamer path cannot fabricate one."
            )


def owner_declaration() -> OwnerDeclaration:
    """Mint an owner-authority token. Call ONLY from an owner-operated entry point (the founding
    ingest / an owner CLI). Importing this into a model / scheduler / dreamer path is a boundary
    violation an import-lint should catch (follow-up); the store's boundary check is the primary
    structural defense regardless."""
    return OwnerDeclaration(_OWNER_TOKEN)


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass(frozen=True)
class AuthoredSupersession:
    superseded: str        # the earlier authored (K₀) note's content digest — now historical
    superseding: str       # the later authored (K₀) note's content digest — now active
    at: str
    note: str = ""         # optional human description (e.g. "superseded in the founding sequence")


_DDL = """
CREATE TABLE IF NOT EXISTS authored_supersessions (
    superseded   TEXT NOT NULL,      -- earlier authored digest (K₀), goes historical
    superseding  TEXT NOT NULL,      -- later authored digest (K₀), goes active
    at           TEXT NOT NULL,      -- when the owner declared it (ordering; never edge topology)
    note         TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (superseded, superseding)
);
CREATE INDEX IF NOT EXISTS authored_supersessions_superseded ON authored_supersessions(superseded);
"""


@dataclass
class AuthoredSupersessionStore:
    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def record(self, superseded: str, superseding: str, *, declaration: OwnerDeclaration,
               note: str = "") -> AuthoredSupersession:
        """Append an OWNER-DECLARED authored-historical supersession (`superseding` replaces
        `superseded` in the active projection). Idempotent on the pair (INSERT OR REPLACE).

        Fail-closed, STRUCTURAL: `declaration` must be a valid `OwnerDeclaration` (owner authority),
        VERIFIED here at the store's own boundary — `None`, a forged object, or anything a machine
        caller could fabricate is REFUSED (`MachineAuthorityRefused`). The store checks; it does not
        rely on "no machine path calls it". A machine-inferred supersession belongs in the blessing
        gate as a dreamer-proposed candidate, never here."""
        # Verify authority at THIS boundary — not just the type (isinstance) but the guarded token
        # itself (getattr defends against a bypass-constructed `object.__new__(OwnerDeclaration)`),
        # so the store refuses machine authority regardless of how the value was produced.
        if not (isinstance(declaration, OwnerDeclaration)
                and getattr(declaration, "_token", None) is _OWNER_TOKEN):
            raise MachineAuthorityRefused(
                "supersession refused: no valid OwnerDeclaration. This store is "
                "owner-declared ONLY — a machine/scheduler/dreamer caller is rejected at "
                "this boundary. Route a machine candidate through the blessing gate as a "
                "dreamer-proposed candidate (supersession-lifecycle.md §3), not here."
            )
        rec = AuthoredSupersession(superseded=superseded, superseding=superseding,
                                   at=_utcnow(), note=note)
        self._conn.execute("INSERT OR REPLACE INTO authored_supersessions VALUES (?, ?, ?, ?)",
                           [rec.superseded, rec.superseding, rec.at, rec.note])
        self._conn.commit()
        return rec

    def superseded(self) -> set[str]:
        """Every superseded digest — the active-projection filter (a consumer excludes these
        from the active view; the superseded note lives on in history). Same role as
        `ClaimOpStore.superseded`, but every entry here is owner-authorized by construction."""
        return {r["superseded"] for r in self._conn.execute(
            "SELECT superseded FROM authored_supersessions")}

    def all(self) -> list[AuthoredSupersession]:
        return [AuthoredSupersession(superseded=r["superseded"], superseding=r["superseding"],
                                     at=r["at"], note=r["note"])
                for r in self._conn.execute(
                    "SELECT * FROM authored_supersessions ORDER BY at, superseded")]

    def count(self) -> int:
        row = self._conn.execute("SELECT count(*) FROM authored_supersessions").fetchone()
        return int(row[0]) if row else 0

    def close(self) -> None:
        self._conn.close()


def open_authored_supersession_store(config: Config | None = None) -> AuthoredSupersessionStore:
    from config.loader import get_config

    cfg = config or get_config()
    path = cfg.paths.derived_store.parent / "authored_supersessions.sqlite"
    return AuthoredSupersessionStore(path)
