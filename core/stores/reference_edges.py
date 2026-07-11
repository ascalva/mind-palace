# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    Lane-1 reference edges — deterministic doc↔code cross-references, the
#            first fiber writer (code-observation-projection.md §2.5, B-c).
# INVARIANT: cross-stratum edges NEVER reach the balance math. `build_complex` holds
#            no handle to this store (no parameter exists), `core/complex/**` never
#            imports it, and nothing here feeds `A_signed`/`L`.
# ENFORCED:  structural — store separation (the `versions.py` pattern), grep-asserted
#            plus proven bit-identical by tests/integration/test_reference_edge_isolation.py
#            (the B-c falsifier, automated).
"""The Lane-1 reference-edge store — typed doc↔code cross-references, balance-isolated (B-c).

One row = one deterministic cross-reference observed at one commit: a code docstring citing
a design note (`code_to_corpus`), or a design note naming a code path (`corpus_to_code`).
Extraction is Lane 1 of the ratified code-observation-projection.md §2.5 — mechanical,
model-free, precision-gated by bp-011's V4 inventory; the extractor is φ_code
(`ops/code_sensor.py`), the sole interpreter, minting within `project_observations`.

**Why a dedicated store and not `EdgeStore` (plan Q1 — the isolation rationale).** These
edges are geometry-class authority (observer-independent facts, the edge model's §2
ownership rule) BUT their endpoints are CROSS-STRATUM: an observed-stratum code symbol on
one side, an authored/curated corpus artifact on the other. The mirror's reasoning complex
𝔎|_MR is authored-only, and `EdgeStore` feeds `A_signed` — so a cross-stratum edge landing
there would smuggle observed-stratum structure into the introspective balance math. The
separation pattern is `core/stores/versions.py`'s: a store `build_complex` has **no
parameter for**. `build_complex(view, *, edges=None, derived=None, sim_floor=...)` cannot
receive this store; `core/complex/**` never imports this module (grep-asserted in the
isolation test). Separated not because the edges carry intent (they don't — they are
facts), but because their endpoints cross strata.

**The balance math holds no handle to this store.** The 2026-07-10 survey's standing fact
— nothing mints E_geom fibers; the balance math runs on recomputed cosine (plus `EdgeStore`
polarity overlays) — remains TRUE for E_geom/`A_signed` after this store exists: reference
edges live entirely outside the complex, and no instrument (balance, Laplacian, curvature,
clustering) can observe their presence or absence. Falsifier (B-c, verbatim): *"any
instrument result changes when reference edges are added or removed"* — automated forever
in `tests/integration/test_reference_edge_isolation.py`.

**Endpoints (plan Q2).** Code side = (commit_sha, path, qualname) — the observed reading's
coordinates (qualname '' for file/module grain). Corpus side = repo-relative path
(`corpus_kind='path'`) for design-note/findings/brainstorm targets; `corpus_kind='digest'`
is reserved for vault-note targets when one becomes resolvable (none arise from bp-011's
validated patterns — design notes are not vault catalog content, so no digest exists today).

**Direction (plan Q3).** Stored AS EXTRACTED — doc→code and code→doc are different
assertions by different authors; this store never auto-symmetrizes. Consumers may
symmetrize on read.

**Append-only.** Identity-keyed (source endpoint, target endpoint, ref_type, source_line)
via a content-derived edge_id; INSERT OR IGNORE — the first reading of an identity wins and
is never mutated (re-projection of the same commit is a no-op; a φ_code upgrade is a
versioned re-interpretation, §2.2, never an in-place overwrite).

**Reset semantics (plan Q4).** Corpus-layer, like `code_observations.sqlite`: wiped with
the corpus via `reset_targets()` (registration is the orchestrator's post-merge step,
oq-0013 concurrence), unlike the snapshot LEDGER (build history, reset-guarded).

Consumers: the detangling instruments and (when it unparks) Item 10's s(C,D)
external-corroboration feature — finding-0021's manual arbitration, made structural.
Zone A, no network, no model anywhere in the path.
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from config.loader import Config

# The §2.3 references_out type vocabulary — the note's pinned shape. NOTE: this is the
# schema DOMAIN, not a precision verdict; which types the extractor actually mints is
# gated per (pattern, direction) by bp-011's measured precision bar (see VALIDATED_PATTERNS
# in ops/code_sensor.py — note-citation and path-mention only; wikilink is not even in
# this vocabulary and symbol-mention/design-ref are below-bar or unvalidated for Lane 1).
REF_TYPES = ("note-citation", "path-mention", "symbol-mention", "design-ref")

DIRECTIONS = ("code_to_corpus", "corpus_to_code")
CORPUS_KINDS = ("path", "digest")

_DDL = """
CREATE TABLE IF NOT EXISTS reference_edges (
    edge_id     TEXT PRIMARY KEY,     -- content-id(direction, ref_type, endpoints, line)
    direction   TEXT NOT NULL,        -- code_to_corpus | corpus_to_code (Q3: as extracted)
    ref_type    TEXT NOT NULL,        -- note-citation | path-mention | symbol-mention | design-ref
    commit_sha  TEXT NOT NULL,        -- code endpoint: the reading's time coordinate
    code_path   TEXT NOT NULL,        -- code endpoint: file within the tree
    qualname    TEXT NOT NULL DEFAULT '',   -- code endpoint: symbol ('' = file/module grain)
    corpus_ref  TEXT NOT NULL,        -- corpus endpoint: repo-relative path (or digest)
    corpus_kind TEXT NOT NULL DEFAULT 'path',   -- path | digest (Q2)
    source_line INTEGER NOT NULL,     -- line in the SOURCE artifact where the ref appears
    created_at  TEXT NOT NULL         -- ISO ts (when the reading landed; not identity)
);
CREATE INDEX IF NOT EXISTS reference_edges_commit ON reference_edges(commit_sha);
CREATE INDEX IF NOT EXISTS reference_edges_corpus ON reference_edges(corpus_ref);
CREATE INDEX IF NOT EXISTS reference_edges_code ON reference_edges(code_path);
"""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _edge_id(direction: str, ref_type: str, commit_sha: str, code_path: str,
             qualname: str, corpus_kind: str, corpus_ref: str, source_line: int) -> str:
    """Content-derived id over (source, target, ref_type, source_line) — the plan-pinned
    identity key. `direction` orients which typed endpoint is the source; both endpoints
    participate in full, so re-asserting the same reading is idempotent."""
    payload = "\x00".join([direction, ref_type, commit_sha, code_path, qualname,
                           corpus_kind, corpus_ref, str(source_line)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class ReferenceEdge:
    """One typed, directed doc↔code reference — cross-stratum endpoints, no sign, no
    weight: this is a FACT record, not a balance input (no `EdgeSign` here on purpose —
    nothing about this row is assembled into any adjacency)."""

    edge_id: str
    direction: str                    # code_to_corpus | corpus_to_code
    ref_type: str                     # one of REF_TYPES
    commit_sha: str                   # code endpoint (Q2)
    code_path: str                    # code endpoint
    qualname: str                     # code endpoint ('' = file/module grain)
    corpus_ref: str                   # corpus endpoint (repo-relative path or digest)
    corpus_kind: str                  # path | digest
    source_line: int
    created_at: str

    @classmethod
    def mint(cls, *, direction: str, ref_type: str, commit_sha: str, code_path: str,
             qualname: str = "", corpus_ref: str, corpus_kind: str = "path",
             source_line: int, created_at: str | None = None) -> ReferenceEdge:
        """Construct with the content-derived identity; validates the closed vocabularies
        at the boundary (a typo'd type/direction/kind is unrepresentable in the store)."""
        if direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {DIRECTIONS}, got {direction!r}")
        if ref_type not in REF_TYPES:
            raise ValueError(f"ref_type must be one of {REF_TYPES}, got {ref_type!r}")
        if corpus_kind not in CORPUS_KINDS:
            raise ValueError(f"corpus_kind must be one of {CORPUS_KINDS}, got {corpus_kind!r}")
        if source_line < 1:
            raise ValueError(f"source_line is 1-based, got {source_line}")
        return cls(
            edge_id=_edge_id(direction, ref_type, commit_sha, code_path, qualname,
                             corpus_kind, corpus_ref, source_line),
            direction=direction, ref_type=ref_type, commit_sha=commit_sha,
            code_path=code_path, qualname=qualname, corpus_ref=corpus_ref,
            corpus_kind=corpus_kind, source_line=source_line,
            created_at=created_at or _utcnow(),
        )


@dataclass
class ReferenceEdgeStore:
    """The Lane-1 reference-edge table. Append-only: INSERT OR IGNORE on the content
    identity — a re-extracted reference never mutates the first reading. Deliberately
    unreachable from `core/complex/**` (see module docstring; isolation test-pinned)."""

    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def add_batch(self, edges: Iterable[ReferenceEdge]) -> int:
        """Land extracted edges. Idempotent on identity (INSERT OR IGNORE, append-only) —
        a second extraction of the same commit changes NOTHING. Returns NEW rows."""
        added = 0
        with self._conn:
            for e in edges:
                cur = self._conn.execute(
                    "INSERT OR IGNORE INTO reference_edges VALUES (?,?,?,?,?,?,?,?,?,?)",
                    [e.edge_id, e.direction, e.ref_type, e.commit_sha, e.code_path,
                     e.qualname, e.corpus_ref, e.corpus_kind, e.source_line, e.created_at],
                )
                added += cur.rowcount
        return added

    def all(self, *, direction: str | None = None,
            ref_type: str | None = None) -> list[ReferenceEdge]:
        sql = "SELECT * FROM reference_edges"
        params: list[str] = []
        clauses: list[str] = []
        if direction is not None:
            clauses.append("direction = ?")
            params.append(direction)
        if ref_type is not None:
            clauses.append("ref_type = ?")
            params.append(ref_type)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY edge_id"
        return [self._row(r) for r in self._conn.execute(sql, params).fetchall()]

    def for_commit(self, commit_sha: str) -> list[ReferenceEdge]:
        return [self._row(r) for r in self._conn.execute(
            "SELECT * FROM reference_edges WHERE commit_sha = ? ORDER BY edge_id",
            [commit_sha],
        ).fetchall()]

    def count(self) -> int:
        row = self._conn.execute("SELECT count(*) FROM reference_edges").fetchone()
        return int(row[0]) if row else 0

    @staticmethod
    def _row(r: sqlite3.Row) -> ReferenceEdge:
        return ReferenceEdge(
            edge_id=r["edge_id"], direction=r["direction"], ref_type=r["ref_type"],
            commit_sha=r["commit_sha"], code_path=r["code_path"], qualname=r["qualname"],
            corpus_ref=r["corpus_ref"], corpus_kind=r["corpus_kind"],
            source_line=int(r["source_line"]), created_at=r["created_at"],
        )

    def close(self) -> None:
        self._conn.close()


def open_reference_edge_store(config: Config | None = None) -> ReferenceEdgeStore:
    """The `open_*` helper: `data/reference_edges.sqlite` — the sibling-store convention
    beside `code_observations.sqlite`. Corpus-layer (Q4): a `reset_targets()` wipe target
    (registered by the orchestrator post-merge, oq-0013 concurrence)."""
    from config.loader import get_config

    cfg = config or get_config()
    return ReferenceEdgeStore(cfg.paths.data_dir / "reference_edges.sqlite")
