"""Derived-artifact store for the INTERPRETED layer (BUILD-SPEC §8).

The interpreted layer is what the *system* inferred — dreams (thematic synthesis) and
curator findings (near-duplicate / prune / contradiction candidates). Per §8 it is kept
SEPARATE and PROVENANCE-MARKED from the owner's authored ground truth: this store holds
`INTERPRETED` only and exposes NO way to write any other provenance — so the derived layer
can never masquerade as authored ground truth. That is the structural form of "explicit vs
interpreted — separate, provenance-marked layers"; it is not an honor-system check.

Everything here is regenerable: `reset()` drops it and a fresh dreaming/curation run
rebuilds it from the (immutable) corpus. Artifact ids are content-derived, so re-running a
cron pass is idempotent (INSERT OR REPLACE) rather than accumulating duplicates.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from core.provenance import Provenance

# Artifact kinds (the discriminator). Dreams are thematic synthesis; findings are the
# curator's flagged candidates (subkind carries the finding type); dream_log entries are the
# confidence-ranked output of the R&D adjudicator (flag-OFF track, R1).
DREAM = "dream"
FINDING = "finding"
DREAM_LOG = "dream_log"

_DDL = """
CREATE TABLE IF NOT EXISTS interpreted_artifacts (
    id           TEXT PRIMARY KEY,
    kind         TEXT NOT NULL,        -- 'dream' | 'finding'
    subkind      TEXT,                 -- finding type: near_duplicate | prune | contradiction
    provenance   TEXT NOT NULL,        -- always 'interpreted' (this store writes nothing else)
    summary      TEXT NOT NULL,
    subjects     TEXT NOT NULL,        -- JSON array of note titles the artifact concerns
    data         TEXT NOT NULL,        -- JSON payload, kind-specific
    derived_from TEXT NOT NULL DEFAULT '[]',  -- JSON array of refs this was derived FROM (G2)
    created_at   TEXT NOT NULL,
    attestation_id TEXT                       -- the attestation that produced this record (or NULL)
);
"""


class DerivationCycleError(ValueError):
    """Inserting an artifact would create a cycle in the derivation DAG (Invariant 10).

    Confidence decay `c ≤ γ^d·g` is only well-defined on an ACYCLIC graph with authored
    leaves — a chain that closes on itself has unbounded (or undefined) depth, the formal
    shape of the rumination loop the recursion bound exists to tame. So a cycle is refused at
    insert time, structurally, rather than detected later."""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _artifact_id(kind: str, subkind: str | None, subjects: tuple[str, ...]) -> str:
    """Content-derived id so re-running a pass over the same notes is idempotent."""
    key = "|".join([kind, subkind or "", *sorted(subjects)])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def artifact_id(kind: str, subkind: str | None, subjects: tuple[str, ...] | list[str]) -> str:
    """Public, stable artifact id for a (kind, subkind, subjects) triple — same value `add()`
    will assign. An emitter precomputes it so an attestation can record this record as its
    output BEFORE the record is written, then `add(..., attestation_id=...)` links back."""
    return _artifact_id(kind, subkind, tuple(subjects))


@dataclass(frozen=True)
class Artifact:
    id: str
    kind: str
    subkind: str | None
    provenance: Provenance       # always INTERPRETED
    summary: str
    subjects: tuple[str, ...]
    data: dict
    created_at: str
    # Refs this artifact was derived FROM (gap G2): authored note digests (the LEAVES,
    # depth 0) and/or other artifact ids (interpreted parents). The support closure must be
    # acyclic and bottom out in authored leaves, so derivation depth d(κ) is computable and
    # the recursion bound c ≤ γ^d·g holds. Empty = scaffolding not recorded (treated depth 1).
    derived_from: tuple[str, ...] = ()
    # The attestation that produced this record (runtime proof layer). None when the artifact
    # predates the attestation layer or was written without an attestor (attestation-layer.md §5).
    attestation_id: str | None = None


@dataclass
class DerivedStore:
    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._migrate()
        self._conn.commit()

    def _migrate(self) -> None:
        """Additive migrations for an existing store. `derived_from` (G2) was added after the
        first Phase-7 schema; backfill the column on older DBs. The derived layer is
        regenerable, so this is a convenience — `reset()` + a fresh run would also suffice."""
        cols = {r["name"] for r in self._conn.execute("PRAGMA table_info(interpreted_artifacts)")}
        if "derived_from" not in cols:
            self._conn.execute(
                "ALTER TABLE interpreted_artifacts ADD COLUMN derived_from TEXT NOT NULL "
                "DEFAULT '[]'"
            )
        if "attestation_id" not in cols:
            # Added with the attestation layer (Step 2). Nullable: old rows have no attestation.
            self._conn.execute(
                "ALTER TABLE interpreted_artifacts ADD COLUMN attestation_id TEXT"
            )

    def add(self, *, kind: str, summary: str, subjects: tuple[str, ...] | list[str],
            data: dict | None = None, subkind: str | None = None,
            derived_from: tuple[str, ...] | list[str] | None = None,
            attestation_id: str | None = None) -> Artifact:
        """Store one INTERPRETED artifact. There is deliberately NO `provenance` parameter:
        the derived store writes `INTERPRETED` and nothing else (§8 firewall, structural).

        `derived_from` records the refs this artifact was built from (gap G2): authored note
        digests (leaves) and/or other artifact ids. The edge set is checked for acyclicity
        BEFORE insert — a cycle is refused (`DerivationCycleError`), so the derivation DAG is
        always acyclic and depth d(κ) is computable (Invariant 10).

        `attestation_id` links this record to the signed attestation that produced it (the
        runtime proof layer, attestation-layer.md §5); None when written without an attestor."""
        subjects = tuple(subjects)
        edges = tuple(derived_from or ())
        new_id = _artifact_id(kind, subkind, subjects)
        self._guard_acyclic(new_id, edges)
        rec = Artifact(
            id=new_id,
            kind=kind,
            subkind=subkind,
            provenance=Provenance.INTERPRETED,
            summary=summary,
            subjects=subjects,
            data=data or {},
            created_at=_utcnow(),
            derived_from=edges,
            attestation_id=attestation_id,
        )
        self._conn.execute(
            "INSERT OR REPLACE INTO interpreted_artifacts "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [rec.id, rec.kind, rec.subkind, rec.provenance.value, rec.summary,
             json.dumps(list(rec.subjects)), json.dumps(rec.data),
             json.dumps(list(rec.derived_from)), rec.created_at, rec.attestation_id],
        )
        self._conn.commit()
        return rec

    # --- derivation graph (gap G2 / Invariant 10) --------------------------------
    def _is_artifact(self, ref: str) -> bool:
        """True if `ref` is an interpreted artifact id (an internal node); otherwise it is an
        authored leaf digest (external, depth 0)."""
        return self._conn.execute(
            "SELECT 1 FROM interpreted_artifacts WHERE id = ?", [ref]
        ).fetchone() is not None

    def _edges_of(self, artifact_id: str) -> list[str]:
        row = self._conn.execute(
            "SELECT derived_from FROM interpreted_artifacts WHERE id = ?", [artifact_id]
        ).fetchone()
        return json.loads(row["derived_from"]) if row else []

    def _guard_acyclic(self, new_id: str, edges: tuple[str, ...]) -> None:
        """Refuse an insert that would close a cycle: `new_id` must not already be reachable
        from any of its parents by following derived_from among existing artifacts. (A direct
        self-reference is the start-of-traversal case and is caught too.)"""
        stack = [e for e in edges if self._is_artifact(e) or e == new_id]
        seen: set[str] = set()
        while stack:
            node = stack.pop()
            if node == new_id:
                raise DerivationCycleError(
                    f"artifact {new_id!r} is reachable from its own derived_from "
                    f"{list(edges)!r} — a derivation cycle (Invariant 10)"
                )
            if node in seen:
                continue
            seen.add(node)
            stack.extend(p for p in self._edges_of(node) if self._is_artifact(p))

    def depth(self, artifact_id: str) -> int:
        """Derivation depth d(κ): 0 for an authored leaf; for an interpreted artifact,
        1 + the max depth of its interpreted parents (authored-leaf parents count 0). An
        artifact with no recorded scaffolding is depth 1 (interpreted, minimally one step from
        ground). Well-defined because the graph is acyclic by construction."""
        return self._depth(artifact_id, set())

    def _depth(self, ref: str, on_path: set[str]) -> int:
        if not self._is_artifact(ref):
            return 0                      # authored leaf
        if ref in on_path:                # defensive; inserts prevent cycles
            return 0
        edges = self._edges_of(ref)
        if not edges:
            return 1
        return 1 + max(self._depth(p, on_path | {ref}) for p in edges)

    def leaf_refs(self, artifact_id: str) -> set[str]:
        """The support closure's LEAVES — every ref reachable from `artifact_id` that is not
        itself an artifact (i.e. authored note digests). A caller checks these are authored
        (Invariant 10: 'every leaf of the support-closure is authored')."""
        leaves: set[str] = set()
        stack, seen = [artifact_id], set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            for p in self._edges_of(node):
                if self._is_artifact(p):
                    stack.append(p)
                else:
                    leaves.add(p)
        return leaves

    def all(self, *, kind: str | None = None, subkind: str | None = None) -> list[Artifact]:
        sql = "SELECT * FROM interpreted_artifacts"
        clauses, params = [], []
        if kind is not None:
            clauses.append("kind = ?")
            params.append(kind)
        if subkind is not None:
            clauses.append("subkind = ?")
            params.append(subkind)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at, id"
        return [self._row(r) for r in self._conn.execute(sql, params).fetchall()]

    def count(self, *, kind: str | None = None) -> int:
        if kind is None:
            return self._conn.execute("SELECT count(*) FROM interpreted_artifacts").fetchone()[0]
        return self._conn.execute(
            "SELECT count(*) FROM interpreted_artifacts WHERE kind = ?", [kind]
        ).fetchone()[0]

    def reset(self) -> None:
        """Drop all derived artifacts. Interpreted data is regenerable (§8): a fresh
        dreaming/curation run rebuilds it from the immutable corpus."""
        self._conn.execute("DELETE FROM interpreted_artifacts")
        self._conn.commit()

    @staticmethod
    def _row(r: sqlite3.Row) -> Artifact:
        keys = r.keys()
        derived_from = tuple(json.loads(r["derived_from"])) if "derived_from" in keys else ()
        attestation_id = r["attestation_id"] if "attestation_id" in keys else None
        return Artifact(
            id=r["id"], kind=r["kind"], subkind=r["subkind"],
            provenance=Provenance(r["provenance"]),
            summary=r["summary"], subjects=tuple(json.loads(r["subjects"])),
            data=json.loads(r["data"]), created_at=r["created_at"],
            derived_from=derived_from,
            attestation_id=attestation_id,
        )

    def close(self) -> None:
        self._conn.close()


def open_derived_store(config: object | None = None) -> DerivedStore:
    from config.loader import get_config

    cfg = config or get_config()
    return DerivedStore(cfg.paths.derived_store)
