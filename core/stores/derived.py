# ── Family 2 boundary (regenerable derivation) · symbols in docs/NOTATION.md ──
# OBJECT:    the INTERPRETED layer of the derivation DAG; its `derived_from` edges seed
#            the hypergraph ℋ (family 5).
# INVARIANT: every artifact here is ρ ≡ interpreted (I5); the graph is acyclic, so depth
#            d(κ) and the decay c ≤ γ^d·g are well-defined (I10).
# ENFORCED:  structural — no `provenance` parameter exists (I5); a cycle is refused at insert
#            (_guard_acyclic → DerivationCycleError, I10). Residual G9: authored-leaf-only
#            is by-convention, not checked against the raw store.
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
from typing import Any

from config.loader import Config
from core.complex_types import HyperedgeRole
from core.provenance import Provenance

# Artifact kinds (the discriminator). Dreams are thematic synthesis; findings are the
# curator's flagged candidates (subkind carries the finding type); dream_log entries are the
# confidence-ranked output of the R&D adjudicator (flag-OFF track, R1).
DREAM = "dream"
FINDING = "finding"
DREAM_LOG = "dream_log"

# The only hyperedge relation today: a `derives` B-arc (tail set → single head κ), acyclic. Other
# rel_types (supports/contradicts/similar) belong to the signed `edges` table (Prompt H1), not here.
DERIVES = "derives"

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

-- The derivation hypergraph ℋ as a JUNCTION (companion III §1.2–§1.3 schema): each `derives`
-- B-arc is one hyperedge with a single head κ and its tail set supp(κ). This NORMALIZES the
-- `derived_from` column above (kept as the denormalized projection for the Artifact API and O(1)
-- traversal); `add` writes both together and they never drift. role ∈ {tail, head} (HyperedgeRole);
-- today every head-set has size 1. The acyclicity guard still runs on `derived_from` at insert.
CREATE TABLE IF NOT EXISTS hyperedges (
    edge_id     TEXT PRIMARY KEY,
    rel_type    TEXT NOT NULL,        -- 'derives' (acyclic); other rel_types are Prompt H1
    provenance  TEXT NOT NULL,        -- always 'interpreted' (no other value is ever written)
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS hyperedge_nodes (
    edge_id     TEXT NOT NULL,
    node_id     TEXT NOT NULL,
    role        TEXT NOT NULL,        -- 'tail' | 'head'  (HyperedgeRole)
    PRIMARY KEY (edge_id, node_id, role)
);
CREATE INDEX IF NOT EXISTS hyperedge_nodes_edge ON hyperedge_nodes(edge_id);
CREATE INDEX IF NOT EXISTS hyperedge_nodes_node ON hyperedge_nodes(node_id, role);
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


def _hyperedge_id(head: str, tails: tuple[str, ...], rel_type: str = DERIVES) -> str:
    """Content-derived id for a `derives` B-arc, so re-writing the same (head, tails) is
    idempotent (INSERT OR REPLACE). Independent of tail order."""
    key = "\x00".join([rel_type, head, *sorted(tails)])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Artifact:
    id: str
    kind: str
    subkind: str | None
    provenance: Provenance       # always INTERPRETED
    summary: str
    subjects: tuple[str, ...]
    data: dict[str, Any]
    created_at: str
    # Refs this artifact was derived FROM (gap G2): authored note digests (the LEAVES,
    # depth 0) and/or other artifact ids (interpreted parents). The support closure must be
    # acyclic and bottom out in authored leaves, so derivation depth d(κ) is computable and
    # the recursion bound c ≤ γ^d·g holds. Empty = scaffolding not recorded (treated depth 1).
    derived_from: tuple[str, ...] = ()
    # The attestation that produced this record (runtime proof layer). None when the artifact
    # predates the attestation layer or was written without an attestor (attestation-layer.md §5).
    attestation_id: str | None = None


@dataclass(frozen=True)
class Hyperedge:
    """One `derives` B-arc of the derivation hypergraph ℋ (companion III §1.3): the tail set
    supp(κ) jointly entails the single head κ. The typed, normalized form of an artifact's
    `derived_from` — named for what it is. Today every head-set has size 1."""

    edge_id: str
    head: str
    tails: frozenset[str]
    rel_type: str = DERIVES


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
        self._backfill_hyperedges()
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
            data: dict[str, Any] | None = None, subkind: str | None = None,
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
        self._write_hyperedge(rec.id, edges)   # normalized ℋ, kept in sync with derived_from
        self._conn.commit()
        return rec

    # --- derivation graph (gap G2 / Invariant 10) --------------------------------
    def is_artifact(self, ref: str) -> bool:
        """True if `ref` is an interpreted (DERIVED) artifact id; False if it is an authored leaf
        digest (external, depth 0). The public authored-vs-derived predicate for a grounding
        decision — e.g. a `supersede` may ground a revision on an authored `C` (bedrock, g=1) but
        never on a derived `C` (which decays / is superseded without a verdict); see
        `core.recursion_ops.apply_operations`."""
        return self._is_artifact(ref)

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

    # --- derivation hypergraph ℋ as a junction (companion III §1.3; the type move) --------
    def _write_hyperedge(self, head: str, tails: tuple[str, ...]) -> None:
        """Sync the junction (ℋ) for artifact `head` to its current tail set, so the normalized
        hyperedge form never drifts from the denormalized `derived_from`. Idempotent: any prior
        `derives` hyperedge for this head is cleared first (an INSERT-OR-REPLACE'd artifact leaves
        no stale tails); no tails ⇒ no hyperedge (matching an empty derived_from)."""
        stale = self._conn.execute(
            "SELECT edge_id FROM hyperedge_nodes WHERE node_id = ? AND role = ?",
            [head, HyperedgeRole.HEAD.value],
        ).fetchall()
        for r in stale:
            self._conn.execute("DELETE FROM hyperedge_nodes WHERE edge_id = ?", [r["edge_id"]])
            self._conn.execute("DELETE FROM hyperedges WHERE edge_id = ?", [r["edge_id"]])
        if not tails:
            return
        edge_id = _hyperedge_id(head, tails)
        self._conn.execute(
            "INSERT OR REPLACE INTO hyperedges VALUES (?, ?, ?, ?)",
            [edge_id, DERIVES, Provenance.INTERPRETED.value, _utcnow()],
        )
        self._conn.execute(
            "INSERT OR REPLACE INTO hyperedge_nodes VALUES (?, ?, ?)",
            [edge_id, head, HyperedgeRole.HEAD.value],
        )
        for t in tails:
            self._conn.execute(
                "INSERT OR REPLACE INTO hyperedge_nodes VALUES (?, ?, ?)",
                [edge_id, t, HyperedgeRole.TAIL.value],
            )

    def _backfill_hyperedges(self) -> None:
        """One-time backfill of ℋ from the denormalized `derived_from` column for a store created
        before the junction existed (additive migration). Idempotent: only artifacts with edges but
        no head row in the junction are written, so re-opening a migrated store is a no-op."""
        have_head = {
            r["node_id"] for r in self._conn.execute(
                "SELECT DISTINCT node_id FROM hyperedge_nodes WHERE role = ?",
                [HyperedgeRole.HEAD.value],
            )
        }
        rows = self._conn.execute(
            "SELECT id, derived_from FROM interpreted_artifacts"
        ).fetchall()   # materialize before writing (don't interleave writes with a live cursor)
        for r in rows:
            edges = tuple(json.loads(r["derived_from"] or "[]"))
            if edges and r["id"] not in have_head:
                self._write_hyperedge(r["id"], edges)

    def hyperedges(self) -> list[Hyperedge]:
        """The derivation hypergraph ℋ as typed B-arcs (the normalized form of every artifact's
        `derived_from`). What the reasoning complex (family 5, `core/complex/`) consumes."""
        out: list[Hyperedge] = []
        for he in self._conn.execute(
            "SELECT edge_id, rel_type FROM hyperedges ORDER BY edge_id"
        ).fetchall():
            nodes = self._conn.execute(
                "SELECT node_id, role FROM hyperedge_nodes WHERE edge_id = ?", [he["edge_id"]]
            ).fetchall()
            head = next(n["node_id"] for n in nodes if n["role"] == HyperedgeRole.HEAD.value)
            tails = frozenset(n["node_id"] for n in nodes if n["role"] == HyperedgeRole.TAIL.value)
            out.append(Hyperedge(edge_id=he["edge_id"], head=head, tails=tails,
                                 rel_type=he["rel_type"]))
        return out

    def tails_of(self, head: str) -> frozenset[str]:
        """The tail set supp(κ) of artifact `head` read from the junction — equals, as a set, its
        `derived_from` (the invariant `_write_hyperedge` maintains)."""
        rows = self._conn.execute(
            "SELECT n_tail.node_id FROM hyperedge_nodes n_head "
            "JOIN hyperedge_nodes n_tail ON n_head.edge_id = n_tail.edge_id "
            "WHERE n_head.node_id = ? AND n_head.role = ? AND n_tail.role = ?",
            [head, HyperedgeRole.HEAD.value, HyperedgeRole.TAIL.value],
        ).fetchall()
        return frozenset(r["node_id"] for r in rows)

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
            row = self._conn.execute("SELECT count(*) FROM interpreted_artifacts").fetchone()
        else:
            row = self._conn.execute(
                "SELECT count(*) FROM interpreted_artifacts WHERE kind = ?", [kind]
            ).fetchone()
        return int(row[0]) if row else 0

    def reset(self) -> None:
        """Drop all derived artifacts and their hyperedges. Interpreted data is regenerable (§8):
        a fresh dreaming/curation run rebuilds it from the immutable corpus."""
        self._conn.execute("DELETE FROM interpreted_artifacts")
        self._conn.execute("DELETE FROM hyperedge_nodes")
        self._conn.execute("DELETE FROM hyperedges")
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


def open_derived_store(config: Config | None = None) -> DerivedStore:
    from config.loader import get_config

    cfg = config or get_config()
    return DerivedStore(cfg.paths.derived_store)
