# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    Lane-1 reference edges — deterministic doc↔code / doc↔doc cross-references,
#            the first fiber writer (code-observation-projection.md §2.5, B-c), generalized
#            to symmetric endpoints by bp-026 (finding-0059/0061/0062 — the doc→doc gap).
# INVARIANT: cross-stratum edges NEVER reach the balance math. `build_complex` holds
#            no handle to this store (no parameter exists), `core/complex/**` never
#            imports it, and nothing here feeds `A_signed`/`L`.
# ENFORCED:  structural — store separation (the `versions.py` pattern), grep-asserted
#            plus proven bit-identical by tests/integration/test_reference_edge_isolation.py
#            (the B-c falsifier, automated).
"""The Lane-1 reference-edge store — typed cross-references, balance-isolated (B-c).

One row = one deterministic reference observed at one commit: a code docstring citing a
design note (`code_to_corpus`), a design note naming a code path (`corpus_to_code`), or
(bp-026) a design note/finding/brainstorm citing another one (`corpus_to_corpus`) via
front-matter (`design_ref`/`links`/`depends_on`/`warrant`/`supersedes`/`superseded_by`),
inline note-citation, or `[[wikilink]]`. Extraction is φ_code (`ops/code_sensor.py`), the
sole interpreter, minting within `project_observations`.

**[banner: schema v2 — bp-026]** The v1 schema (code-observation-projection.md's original
shape, bp-013) had ASYMMETRIC endpoints: a code side `(commit_sha, code_path, qualname)`
fixed as the first slot and a corpus side `(corpus_ref, corpus_kind)` fixed as the second,
with `direction ∈ {code_to_corpus, corpus_to_code}` stored to say which was which. That
shape had no room for a `corpus_to_corpus` edge (findings 0059/0061/0062 — the reference
graph is doc→doc-blind, and the store's own field names encode the gap). v2 replaces the
fixed code/corpus slots with a SYMMETRIC `(source_kind, source_ref, source_detail) →
(target_kind, target_ref, target_detail)` pair, `kind ∈ KINDS = ("code", "corpus")` on
EITHER side, admitting `code_to_corpus | corpus_to_code | corpus_to_corpus` (and
`code_to_code`, reachable, not minted anywhere yet). `direction` is now DERIVED
(`f"{source_kind}_to_{target_kind}"`), never a stored column — it cannot drift from the
endpoints that define it. The migration is WIPE + RE-PROJECT (bp-026 §3 Q1/Q2: this store
is corpus-class, a deterministic projection of git history with near-zero reader blast
radius — no in-place row surgery, no attempt to preserve v1 `edge_id`s; every edge is
re-minted under the v2 identity formula from scratch. See `docs/build-plans/bp-026/plan.md`
§6(b) for the pinned interface and Q1/Q2/Q3 for the migration-safety argument.

**Why a dedicated store and not `EdgeStore` (v1 Q1, unchanged by v2 — the isolation
rationale).** These edges are geometry-class authority (observer-independent facts, the
edge model's §2 ownership rule) BUT their endpoints may be CROSS-STRATUM: an observed-stratum
code symbol on one side, an authored/curated corpus artifact on the other (or, since v2, both
sides authored/curated). The mirror's reasoning complex 𝔎|_MR is authored-only, and
`EdgeStore` feeds `A_signed` — so a cross-stratum edge landing there would smuggle
observed-stratum structure into the introspective balance math. The separation pattern is
`core/stores/versions.py`'s: a store `build_complex` has **no parameter for**.
`build_complex(view, *, edges=None, derived=None, sim_floor=...)` cannot receive this store;
`core/complex/**` never imports this module (grep-asserted in the isolation test). Separated
not because the edges carry intent (they don't — they are facts), but because their endpoints
may cross strata.

**The balance math holds no handle to this store.** The 2026-07-10 survey's standing fact
— nothing mints E_geom fibers; the balance math runs on recomputed cosine (plus `EdgeStore`
polarity overlays) — remains TRUE for E_geom/`A_signed` after this store exists: reference
edges live entirely outside the complex, and no instrument (balance, Laplacian, curvature,
clustering) can observe their presence or absence. Falsifier (B-c, verbatim): *"any
instrument result changes when reference edges are added or removed"* — automated forever
in `tests/integration/test_reference_edge_isolation.py`.

**Endpoints (v1 Q2, generalized).** `source_kind`/`target_kind` ∈ `KINDS`. For `kind="code"`:
`ref` = file path within the tree, `detail` = qualname (`''` = file/module grain) — the
observed reading's coordinates. For `kind="corpus"`: `ref` = repo-relative path
(design-note/findings/brainstorm target), `detail` = `''` (path-kind) or a digest (reserved
for vault-note targets when one becomes resolvable — none arise from bp-011's validated
patterns, so `detail=''` in every edge minted to date).

**Direction (v1 Q3, unchanged in spirit).** Stored AS EXTRACTED, but no longer as its own
column — it is DERIVED from `(source_kind, target_kind)`: `code_to_corpus`, `corpus_to_code`,
and (v2) `corpus_to_corpus` are different assertions by different authors; this store never
auto-symmetrizes. Consumers may symmetrize on read.

**Append-only.** Identity-keyed (source endpoint, target endpoint, ref_type, source_line)
via a content-derived edge_id; INSERT OR IGNORE — the first reading of an identity wins and
is never mutated (re-projection of the same commit is a no-op; a φ_code upgrade is a
versioned re-interpretation, §2.2, never an in-place overwrite).

**Reset semantics (v1 Q4, unchanged).** Corpus-layer, like `code_observations.sqlite`: wiped
with the corpus via `reset_targets()` (registration is the orchestrator's post-merge step,
oq-0013 concurrence), unlike the snapshot LEDGER (build history, reset-guarded).

Consumers: the detangling instruments, the parked s(C,D) external-corroboration feature
(finding-0021), and (bp-026's warrant) the dn-core-query-protocol algebra's `references_to`
query surface — this store is its prerequisite substrate, not yet its consumer.
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
# in ops/code_sensor.py — note-citation and path-mention only for code↔corpus; design-ref
# and note-citation for corpus↔corpus, bp-026 — wikilink is not even in this vocabulary and
# symbol-mention is below-bar/unvalidated for Lane 1).
REF_TYPES = ("note-citation", "path-mention", "symbol-mention", "design-ref")

# bp-026 v2: symmetric endpoint kinds. `code_to_code` is reachable (both endpoints kind
# "code") but nothing mints it — no call-graph reference need has arisen (plan §11 parked).
KINDS = ("code", "corpus")
DIRECTIONS = ("code_to_corpus", "corpus_to_code", "corpus_to_corpus", "code_to_code")

# v1 aliases, retained for the closed-vocabulary spirit (corpus_kind's old domain) — the
# v2 `*_detail` fields are free-form ('' | digest), no longer boundary-validated against a
# closed set (a code qualname is not closed either): kept here only as the historical
# marker of what CORPUS_KINDS meant, not as a validated field. finding-0063: the v1 READ
# surface (`.corpus_kind`) is still derived on ReferenceEdge for out-of-scope-file compat.
CORPUS_KINDS = ("path", "digest")

_DDL = """
CREATE TABLE IF NOT EXISTS reference_edges (
    edge_id       TEXT PRIMARY KEY,   -- content-id over (source endpoint, target endpoint,
                                       -- ref_type, source_line) — the v2 symmetric tuple
    commit_sha    TEXT NOT NULL,      -- time coordinate: the commit the reading landed at
    ref_type      TEXT NOT NULL,      -- REF_TYPES (unchanged vocabulary)
    source_kind   TEXT NOT NULL,      -- 'code' | 'corpus'
    source_ref    TEXT NOT NULL,      -- code: file path ; corpus: repo-relative doc path
    source_detail TEXT NOT NULL DEFAULT '',   -- code: qualname ('' = module grain) ;
                                               -- corpus: '' | digest
    target_kind   TEXT NOT NULL,      -- 'code' | 'corpus'
    target_ref    TEXT NOT NULL,      -- symmetric to source_ref
    target_detail TEXT NOT NULL DEFAULT '',   -- symmetric to source_detail
    source_line   INTEGER NOT NULL,   -- line in the SOURCE artifact where the ref appears
    created_at    TEXT NOT NULL       -- ISO ts (when the reading landed; not identity)
);
CREATE INDEX IF NOT EXISTS reference_edges_commit ON reference_edges(commit_sha);
CREATE INDEX IF NOT EXISTS reference_edges_source_ref ON reference_edges(source_ref);
CREATE INDEX IF NOT EXISTS reference_edges_target_ref ON reference_edges(target_ref);
"""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _edge_id(ref_type: str, commit_sha: str, source_kind: str, source_ref: str,
             source_detail: str, target_kind: str, target_ref: str, target_detail: str,
             source_line: int) -> str:
    """Content-derived id over the v2 symmetric tuple (source, target, ref_type,
    source_line) — the plan-pinned identity key (bp-026 §6(b)). Both endpoints
    participate in full, so re-asserting the same reading is idempotent. NOTE: this
    formula supersedes v1's — the migration is wipe+reproject (bp-026 §3), so no v1
    edge_id is ever compared against a v2 one."""
    payload = "\x00".join([ref_type, commit_sha, source_kind, source_ref, source_detail,
                           target_kind, target_ref, target_detail, str(source_line)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class ReferenceEdge:
    """One typed, directed reference — symmetric endpoints (bp-026 v2), no sign, no
    weight: this is a FACT record, not a balance input (no `EdgeSign` here on purpose —
    nothing about this row is assembled into any adjacency)."""

    edge_id: str
    ref_type: str                     # one of REF_TYPES
    commit_sha: str                   # the reading's time coordinate
    source_kind: str                  # 'code' | 'corpus'
    source_ref: str                   # code: file path ; corpus: repo-relative doc path
    source_detail: str                # code: qualname ('' = module grain) ; corpus: '' | digest
    target_kind: str                  # 'code' | 'corpus'
    target_ref: str                   # symmetric to source_ref
    target_detail: str                # symmetric to source_detail
    source_line: int
    created_at: str

    @property
    def direction(self) -> str:
        """DERIVED, never stored (bp-026 §6(b)) — cannot drift from the endpoints that
        define it: `f"{source_kind}_to_{target_kind}"`."""
        return f"{self.source_kind}_to_{self.target_kind}"

    # ── finding-0063: v1 read-compat properties ──────────────────────────────────────
    # tests/unit/test_reference_extraction.py (bp-013's fixed Item-7 test, outside
    # bp-026's write_scope) reads `.code_path`/`.qualname`/`.corpus_ref`/`.corpus_kind`
    # off returned edges. These are READ-ONLY DERIVED properties over the v2 symmetric
    # fields — no asymmetric residue is STORED (the Item 18 falsifier's letter: the DDL
    # and dataclass fields above are exactly the v2 tuple, nothing named code_path/
    # corpus_ref is a column). For the only directions v1 ever minted (code_to_corpus,
    # corpus_to_code) these recover the v1 read surface byte-for-byte. Accessing a
    # code-endpoint alias on a corpus_to_corpus edge (v2-only, unreachable by any v1
    # caller) raises — a misuse guard, not a silent wrong answer.
    @property
    def code_path(self) -> str:
        if self.source_kind == "code":
            return self.source_ref
        if self.target_kind == "code":
            return self.target_ref
        raise ValueError(f"edge {self.edge_id!r} has no code endpoint "
                         f"(direction={self.direction!r})")

    @property
    def qualname(self) -> str:
        if self.source_kind == "code":
            return self.source_detail
        if self.target_kind == "code":
            return self.target_detail
        raise ValueError(f"edge {self.edge_id!r} has no code endpoint "
                         f"(direction={self.direction!r})")

    @property
    def corpus_ref(self) -> str:
        if self.source_kind == "corpus" and self.target_kind != "corpus":
            return self.source_ref
        if self.target_kind == "corpus" and self.source_kind != "corpus":
            return self.target_ref
        raise ValueError(f"edge {self.edge_id!r} has no unambiguous corpus endpoint "
                         f"(direction={self.direction!r})")

    @property
    def corpus_kind(self) -> str:
        if self.source_kind == "corpus" and self.target_kind != "corpus":
            detail = self.source_detail
        elif self.target_kind == "corpus" and self.source_kind != "corpus":
            detail = self.target_detail
        else:
            raise ValueError(f"edge {self.edge_id!r} has no unambiguous corpus endpoint "
                             f"(direction={self.direction!r})")
        return "digest" if detail else "path"

    @classmethod
    def mint(cls, *, source_kind: str, source_ref: str, target_kind: str, target_ref: str,
             ref_type: str, commit_sha: str, source_detail: str = "", target_detail: str = "",
             source_line: int, created_at: str | None = None) -> ReferenceEdge:
        """Construct with the content-derived identity; validates the closed vocabularies
        at the boundary (a typo'd kind/ref_type is unrepresentable in the store)."""
        if source_kind not in KINDS:
            raise ValueError(f"source_kind must be one of {KINDS}, got {source_kind!r}")
        if target_kind not in KINDS:
            raise ValueError(f"target_kind must be one of {KINDS}, got {target_kind!r}")
        if ref_type not in REF_TYPES:
            raise ValueError(f"ref_type must be one of {REF_TYPES}, got {ref_type!r}")
        if source_line < 1:
            raise ValueError(f"source_line is 1-based, got {source_line}")
        return cls(
            edge_id=_edge_id(ref_type, commit_sha, source_kind, source_ref, source_detail,
                             target_kind, target_ref, target_detail, source_line),
            ref_type=ref_type, commit_sha=commit_sha,
            source_kind=source_kind, source_ref=source_ref, source_detail=source_detail,
            target_kind=target_kind, target_ref=target_ref, target_detail=target_detail,
            source_line=source_line, created_at=created_at or _utcnow(),
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
                    "INSERT OR IGNORE INTO reference_edges VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    [e.edge_id, e.commit_sha, e.ref_type, e.source_kind, e.source_ref,
                     e.source_detail, e.target_kind, e.target_ref, e.target_detail,
                     e.source_line, e.created_at],
                )
                added += cur.rowcount
        return added

    def all(self, *, direction: str | None = None, ref_type: str | None = None,
            source_ref: str | None = None, target_ref: str | None = None,
            ) -> list[ReferenceEdge]:
        """`direction` filters on the DERIVED value (source_kind_to_target_kind), computed
        server-side from the two kind columns — no stored direction column exists.
        `source_ref`/`target_ref` are bp-026's addition: the "references TO doc X" query
        (`all(target_ref=...)`) and its dual (`all(source_ref=...)`)."""
        sql = "SELECT * FROM reference_edges"
        params: list[str] = []
        clauses: list[str] = []
        if direction is not None:
            if direction not in DIRECTIONS:
                raise ValueError(f"direction must be one of {DIRECTIONS}, got {direction!r}")
            src_kind, _, tgt_kind = direction.partition("_to_")
            clauses.append("source_kind = ? AND target_kind = ?")
            params.extend([src_kind, tgt_kind])
        if ref_type is not None:
            clauses.append("ref_type = ?")
            params.append(ref_type)
        if source_ref is not None:
            clauses.append("source_ref = ?")
            params.append(source_ref)
        if target_ref is not None:
            clauses.append("target_ref = ?")
            params.append(target_ref)
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
            edge_id=r["edge_id"], commit_sha=r["commit_sha"], ref_type=r["ref_type"],
            source_kind=r["source_kind"], source_ref=r["source_ref"],
            source_detail=r["source_detail"], target_kind=r["target_kind"],
            target_ref=r["target_ref"], target_detail=r["target_detail"],
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
