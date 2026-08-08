# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    the membership relation M ⊆ V × O — which idea-atoms occupy which (path, blob_sha)
#            versions, at which slot and lines, and whether that occupancy is current
#            (dn-vector-membership-store D1/D2/D8, warrant finding-0168).
# INVARIANT: MULTISET, never a set — the key is the occupancy's coordinates
#            (path, blob_sha, layer, chunk_index), so two byte-identical windows in one blob are
#            TWO rows. No occupancy vanishes by key collision. `slot` is the qualname for L0a
#            only; L0b/L1 are membership-only and honestly chainless (R4).
# ENFORCED:  structural — this module lives in `core/stores/` (OUTER ring) and is NEVER imported
#            by `core/kernel/**`. Memberships reach the kernel as DATA, through the existing
#            `RowSource`-shaped protocol (`core/kernel/stores/sourceset.py`); a kernel import
#            would mechanically demote `sourceset` from the inner-ring fixed point
#            (`core/kernel/rings.py:36-41`, the C5/D3 pin). If the seam ever cannot stay
#            data-shaped, the design note is explicit: that is a finding, not an import.
"""The membership store — occupancy as a first-class relation (dn-vector-membership-store, bp-152).

A point is a point: geometry, assertion-free. **Meaning lives in membership** — who contains it —
and history in **lineage** — which occupancy chains pass through it. The vector plane
(`core/stores/vectorstore.py`) holds ONE row per distinct idea-atom `(layer, content_hash)`,
append-only; this store holds everything that used to be duplicated onto those rows once per
version:

  * **A version is a fiber.** `M(path, blob_sha)` — the complete projection of one file version.
    Landing a version writes its fiber; re-landing the same blob writes nothing new, because
    derivation is a pure function of `(path, source)` so the fiber is equal by construction.
  * **A re-land is idempotent BECAUSE reconciliation converges** — never because the call
    short-circuits. This is the C1 lesson the repo has already learned once
    (`core/stores/versions.py:22-27`: content-keyed identity cannot hold a revert). On A → B → A
    the fiber for blob A already EXISTS with `current=false`; a lander that returns early on
    "fiber exists" leaves **B** current, which is silent D3 corruption with nothing to see. So
    `reconcile_currency` runs on every land, including the ones that wrote no row.
  * **`current_any` is a cache, this store is the truth** (D8/R3). The lance `current` column is
    the cheap ANN prefilter; membership rows are what it caches, and `repair_current_any` rebuilds
    it from them. Write order is vector inserts FIRST (append-only, an unreferenced atom is
    harmless dormant geometry), fiber SECOND (one SQLite transaction), currency LAST — every step
    after the first is re-derivable, so a crash anywhere is repaired by the next land.
  * **Append-only, with ONE removal.** No API here deletes a vector except `purge_atom` (D5,
    finding-0164 — owner-gated, privacy outranks lineage), and a purge leaves a RECORDED HOLE: the
    row is gone and its memberships are tombstoned, never silently dropped.

Lineage is DERIVED here, never stored (PD-3): `slot_runs` / `slot_edges` collapse a path's
first-parent blob chain into runs of equal occupants per slot, so a revert reads as 3 runs and 2
edges rather than being flattened away. Chain members are a strict subset of the version set (D4/F3
— a side-branch fiber is a real member of M with no place on any chain), so the edge invariants are
quantified over the chain that is handed in, never over all fibers.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from core.kernel.config import Config
from core.stores.vectorstore import LAYER_CODE_AST, VectorStore, is_code_atom_row


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass(frozen=True)
class EmbedderIdentity:
    """The geometry an atom's stored vector came from — `EmbeddingConfig.model` + `dim`.

    Embed REUSE (D2 step 2, "insert only the atoms absent from the plane") is only valid within one
    embedder, and the owner pinned that explicitly (2026-08-01, issue #27 sub-confirmation 2): an
    atom already in the plane carries a vector from whichever embedder landed it, and serving it
    beside freshly-embedded atoms mixes two geometries in ONE ANN space — a corruption no
    downstream measurement can detect. So atom PRESENCE is keyed to `(layer, content_hash)` **and**
    this identity; a hit whose embedder differs from the live config is not a hit.

    `query_instruction` is deliberately excluded: it conditions *queries*, not stored document
    vectors, so two configs differing only there share a geometry."""

    model: str
    dim: int

    @classmethod
    def from_config(cls, config: Config) -> EmbedderIdentity:
        return cls(model=config.embedding.model, dim=config.embedding.dim)


@dataclass(frozen=True)
class Membership:
    """One occupancy: "atom `content_id` sits in version `(path, blob_sha)` at this slot".

    The key is `(path, blob_sha, layer, chunk_index)` — the occupancy's COORDINATES, not its
    content. That is the multiset pin (the note's F5): two byte-identical L0b windows in one blob
    differ only in `chunk_index`, and keying on content would silently merge them.

    ⚑ `slot_line_start` / `slot_line_end` are the **SLOT's declared extent** — where the symbol
    lives — and **never the atom's text coverage** (Amendment A2, issue #34). They coincide for
    leaf symbols. For a symbol with nested children the children's lines are carved OUT of the
    parent's chunk while the span still reports the parent's full `lineno..end_lineno`; for the
    module shell the span is the ENTIRE FILE by construction. The columns are named for what they
    measure precisely so the bad reading loses the vocabulary it was hiding in: a consumer that
    wants "where is this symbol" uses the span, and a consumer that wants the atom's content uses
    the stored `text`. Rendering the span and calling it the atom renders, for the shell, the whole
    file."""

    path: str
    blob_sha: str
    layer: str
    chunk_index: int
    content_id: str
    slot: str
    slot_line_start: int
    slot_line_end: int
    current: bool = False
    tombstoned: bool = False


@dataclass(frozen=True)
class CurrencyReport:
    """What D2 step 4 actually changed. Both counts are rows whose flag MOVED, so a converged
    re-land reports (0, 0) — the honest reading of "idempotent by convergence"."""

    made_current: int = 0
    superseded: int = 0


@dataclass(frozen=True)
class PurgeReport:
    """The recorded hole (D5). A purge that silently no-ops satisfies "never deletes" vacuously,
    so both halves are counted and a caller can assert the hole EXISTS."""

    vector_rows_deleted: int = 0
    memberships_tombstoned: int = 0


_DDL = """
CREATE TABLE IF NOT EXISTS memberships (
    path            TEXT NOT NULL,     -- the occupancy's file path (mutable: a rename is a NEW
                                       -- fiber over the SAME atoms, never a re-hash — D0)
    blob_sha        TEXT NOT NULL,     -- the git blob sha: the version's identity
    layer           TEXT NOT NULL,     -- code_ast (L0a) / code_text (L0b) / codedoc (L1)
    chunk_index     INTEGER NOT NULL,  -- position in the PURE derivation's chunk list, so two
                                       -- identical windows stay two rows (the F5 multiset pin)
    content_id      TEXT NOT NULL,     -- the atom: "{layer}:{content_hash}" (path-free, D1)
    slot            TEXT NOT NULL,     -- qualname for L0a ONLY; '' for L0b/L1 (R4, no re-slot)
    slot_line_start INTEGER NOT NULL,  -- the SLOT's declared extent, NOT the atom's coverage (A2)
    slot_line_end   INTEGER NOT NULL,
    current         INTEGER NOT NULL DEFAULT 0,   -- is this the path's HEAD projection? (D2 step 4)
    tombstoned      INTEGER NOT NULL DEFAULT 0,   -- a purged atom's recorded hole (D5)
    PRIMARY KEY (path, blob_sha, layer, chunk_index)
);
CREATE INDEX IF NOT EXISTS memberships_content ON memberships(content_id);
CREATE INDEX IF NOT EXISTS memberships_fiber   ON memberships(path, blob_sha);
CREATE INDEX IF NOT EXISTS memberships_path    ON memberships(path);

-- The atom ledger: which embedder geometry each landed atom's vector came from. NOT a second
-- truth about occupancy (PD-3's fence is about lineage edges, and this stores none) — it records
-- the one fact the vector table structurally CANNOT: its Arrow schema is shared with the prose
-- lane and has no embedder column, and a stored vector's `len()` gives back `dim` but never
-- `model`. Without it the embedder pin above is unenforceable, and a model change would silently
-- reuse the old geometry forever.
CREATE TABLE IF NOT EXISTS atoms (
    content_id     TEXT PRIMARY KEY,
    layer          TEXT NOT NULL,
    embedder_model TEXT NOT NULL,
    embedder_dim   INTEGER NOT NULL,
    landed_at      TEXT NOT NULL
);
"""


@dataclass
class MembershipStore:
    """The occupancy relation, in SQLite beside the vault catalog — outer ring, never imported by
    the kernel.

    Reads are cheap point/range queries over the two indexes; the whole surface is deliberately
    small, because everything history-shaped (runs, edges, forks, joins) is DERIVED from these rows
    rather than stored (PD-3: one source of truth for lineage)."""

    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    # ── the atom ledger: presence keyed to (layer, content_hash) AND the embedder ────────────

    def known_atoms(self, content_ids: Iterable[str], embedder: EmbedderIdentity) -> set[str]:
        """Which of `content_ids` are already in the plane UNDER THIS EMBEDDER (D2 step 2).

        The embedder half is the whole point: an atom landed by another model is present as a row
        but not usable as a reuse, because reusing it would put two geometries in one ANN space.
        A suite that only ever exercises one embedder cannot see the difference, which is why the
        pin carries its own test case."""
        wanted = list(dict.fromkeys(content_ids))
        if not wanted:
            return set()
        out: set[str] = set()
        for start in range(0, len(wanted), 400):
            batch = wanted[start:start + 400]
            marks = ", ".join("?" for _ in batch)
            rows = self._conn.execute(
                f"SELECT content_id FROM atoms WHERE content_id IN ({marks}) "
                "AND embedder_model = ? AND embedder_dim = ?",
                [*batch, embedder.model, embedder.dim]).fetchall()
            out.update(str(r["content_id"]) for r in rows)
        return out

    def record_atoms(self, atoms: Iterable[tuple[str, str]],
                     embedder: EmbedderIdentity) -> int:
        """Record `(content_id, layer)` pairs as landed under `embedder`. Returns rows written.

        A re-land under a CHANGED embedder overwrites the identity (the atom's vector really was
        re-embedded), so the ledger always describes the geometry currently in the plane."""
        rows = [(cid, layer, embedder.model, embedder.dim, _utcnow())
                for cid, layer in dict.fromkeys(atoms)]
        if not rows:
            return 0
        self._conn.executemany(
            "INSERT INTO atoms (content_id, layer, embedder_model, embedder_dim, landed_at) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT(content_id) DO UPDATE SET "
            "layer = excluded.layer, embedder_model = excluded.embedder_model, "
            "embedder_dim = excluded.embedder_dim, landed_at = excluded.landed_at", rows)
        self._conn.commit()
        return len(rows)

    def ledger_atom_ids(self) -> set[str]:
        return {str(r["content_id"])
                for r in self._conn.execute("SELECT content_id FROM atoms").fetchall()}

    def forget_atom(self, content_id: str) -> int:
        """Drop one atom from the ledger — the purge's other half (D5). Never called by anything
        else: nothing else removes geometry."""
        cur = self._conn.execute("DELETE FROM atoms WHERE content_id = ?", [content_id])
        self._conn.commit()
        return int(cur.rowcount)

    # ── fibers: a version's complete projection ─────────────────────────────────────────────

    def write_fiber(self, rows: Sequence[Membership]) -> int:
        """Write a version's fiber (D2 step 3). Returns rows actually inserted.

        `INSERT OR IGNORE`: an existing fiber's rows STAND, because derivation is pure so the
        re-derived fiber is equal by construction. Returning 0 is therefore the correct, expected
        answer on a re-land — and is precisely why it must NOT be read as "nothing to do": the
        caller still owes step 4. One transaction, so a crash leaves the fiber whole or absent,
        never half (D8: SQLite is the reference truth)."""
        if not rows:
            return 0
        before = self.count()
        self._conn.executemany(
            "INSERT OR IGNORE INTO memberships (path, blob_sha, layer, chunk_index, content_id, "
            "slot, slot_line_start, slot_line_end, current, tombstoned) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(m.path, m.blob_sha, m.layer, m.chunk_index, m.content_id, m.slot,
              m.slot_line_start, m.slot_line_end, int(m.current), int(m.tombstoned))
             for m in rows])
        self._conn.commit()
        return self.count() - before

    def fiber(self, path: str, blob_sha: str) -> list[Membership]:
        """One version's complete projection, in `chunk_index` order — i.e. in the order the pure
        derivation emitted the chunks, so a fiber read back IS the version's chunk list."""
        return [_row(r) for r in self._conn.execute(
            "SELECT * FROM memberships WHERE path = ? AND blob_sha = ? ORDER BY chunk_index",
            [path, blob_sha]).fetchall()]

    def blobs_of(self, path: str) -> list[str]:
        """Every blob this path has a fiber for, oldest-recorded first (by insertion rowid)."""
        return [str(r["blob_sha"]) for r in self._conn.execute(
            "SELECT blob_sha FROM memberships WHERE path = ? GROUP BY blob_sha ORDER BY MIN(rowid)",
            [path]).fetchall()]

    def fibers(self) -> list[tuple[str, str]]:
        return [(str(r["path"]), str(r["blob_sha"])) for r in self._conn.execute(
            "SELECT path, blob_sha FROM memberships GROUP BY path, blob_sha "
            "ORDER BY path, MIN(rowid)").fetchall()]

    def fiber_sizes(self) -> dict[tuple[str, str], int]:
        return {(str(r["path"]), str(r["blob_sha"])): int(r["n"]) for r in self._conn.execute(
            "SELECT path, blob_sha, count(*) AS n FROM memberships GROUP BY path, blob_sha"
        ).fetchall()}

    def count(self) -> int:
        """|M| — the total number of occupancies."""
        row = self._conn.execute("SELECT count(*) FROM memberships").fetchone()
        return int(row[0]) if row else 0

    # ── currency reconciliation: D2 step 4, the C1 case ─────────────────────────────────────

    def reconcile_currency(self, path: str, head_blob_sha: str) -> CurrencyReport:
        """Set `current=1` on exactly the fiber whose blob is the path's HEAD, and `current=0` on
        the path's every other fiber. **NEVER skipped, even when the fiber write was a no-op.**

        This is the whole reason a re-land is idempotent. The tempting shortcut — "the fiber
        already exists, so return" — is the C1 bug in its exact original form: land A, land B, land
        A again; A's fiber exists with `current=false`, the short-circuit skips this call, and the
        store is left claiming **B** is HEAD. Nothing raises, nothing logs, and every default
        (current-view) read is now wrong. Convergence, not short-circuiting.

        Idempotent by construction: the counts are of rows whose flag actually MOVED, so a second
        call reports (0, 0) and writes nothing."""
        cur = self._conn.execute(
            "SELECT count(*) FROM memberships WHERE path = ? AND blob_sha = ? AND current = 0",
            [path, head_blob_sha]).fetchone()
        stale = self._conn.execute(
            "SELECT count(*) FROM memberships WHERE path = ? AND blob_sha != ? AND current = 1",
            [path, head_blob_sha]).fetchone()
        made = int(cur[0]) if cur else 0
        dropped = int(stale[0]) if stale else 0
        if made:
            self._conn.execute(
                "UPDATE memberships SET current = 1 "
                "WHERE path = ? AND blob_sha = ? AND current = 0", [path, head_blob_sha])
        if dropped:
            self._conn.execute(
                "UPDATE memberships SET current = 0 WHERE path = ? AND blob_sha != ? "
                "AND current = 1", [path, head_blob_sha])
        if made or dropped:
            self._conn.commit()
        return CurrencyReport(made_current=made, superseded=dropped)

    # ── the frequency plane (D6): two counts, never conflated ────────────────────────────────

    def n_doc(self, content_id: str, *, current_only: bool = True) -> int:
        """Distinct PATHS holding this atom — the document-frequency reading, immune to
        within-file repetition. `current_any(v) ⇔ n_doc(v, t) > 0` is the carried invariant (R3)."""
        clause = "AND current = 1" if current_only else ""
        row = self._conn.execute(
            f"SELECT count(DISTINCT path) FROM memberships "
            f"WHERE content_id = ? AND tombstoned = 0 {clause}", [content_id]).fetchone()
        return int(row[0]) if row else 0

    def n_occ(self, content_id: str, *, current_only: bool = True) -> int:
        """Membership ROWS holding this atom — the multiset reading, where L0b's repeated windows
        count. Never conflated with `n_doc` (the F5 pin: they are different questions)."""
        clause = "AND current = 1" if current_only else ""
        row = self._conn.execute(
            f"SELECT count(*) FROM memberships "
            f"WHERE content_id = ? AND tombstoned = 0 {clause}", [content_id]).fetchone()
        return int(row[0]) if row else 0

    def atom_ids_of_path(self, path: str) -> set[str]:
        return {str(r["content_id"]) for r in self._conn.execute(
            "SELECT DISTINCT content_id FROM memberships WHERE path = ?", [path]).fetchall()}

    def currently_held(self, content_ids: Iterable[str]) -> set[str]:
        """Which of `content_ids` have at least one current, un-tombstoned occupancy — i.e. the
        set whose `current_any` should be true. One query, so D2 step 5's crossing arithmetic is
        cheap even when a path's history is long."""
        wanted = list(dict.fromkeys(content_ids))
        if not wanted:
            return set()
        out: set[str] = set()
        for start in range(0, len(wanted), 400):
            batch = wanted[start:start + 400]
            marks = ", ".join("?" for _ in batch)
            rows = self._conn.execute(
                f"SELECT DISTINCT content_id FROM memberships WHERE content_id IN ({marks}) "
                "AND current = 1 AND tombstoned = 0", batch).fetchall()
            out.update(str(r["content_id"]) for r in rows)
        return out

    # ── the read path (D3): one atom resolves to all its occupancies ─────────────────────────

    def occupancies(self, content_id: str, *,
                    include_superseded: bool = False) -> list[Membership]:
        """Where this atom lives. One atom may resolve to SEVERAL occupancies — that is the
        feature, not a defect: a hit natively answers "this idea lives in versions v3–v7 of X and
        also in Y". Default consumers see current occupancies only (D3)."""
        clause = "" if include_superseded else "AND current = 1"
        return [_row(r) for r in self._conn.execute(
            f"SELECT * FROM memberships WHERE content_id = ? {clause} "
            "ORDER BY path, blob_sha, layer, chunk_index", [content_id]).fetchall()]

    # ── derived lineage (PD-3: never a second stored truth) ─────────────────────────────────

    def slot_runs(self, path: str, chain: Sequence[str]) -> dict[str, list[str]]:
        """Per slotted `(path, slot)`, the occupancy chain collapsed into RUNS of equal occupants
        along `chain` (the path's FIRST-PARENT blob sequence, oldest first).

        **ADJACENT collapse, never distinct-collapse** — this is the C1 formulation and the whole
        reason §4 was re-keyed on runs: A → B → A gives runs `[A, B, A]`, three runs and two edges,
        so a revert stays visible. Collapsing distinct occupants would report one edge and quietly
        erase the revert, which is the same failure `core/stores/versions.py` documents at note
        grain. `ops/code_lineage.py:151-156` already collapses only adjacent repeats at file grain,
        so the two grains agree.

        `chain` is handed in rather than read from this store because chain MEMBERSHIP is not a
        membership fact: chains are first-parent while the ledger walks all commits, so a
        side-branch fiber is a real member of M that sits on NO chain (D4/F3). Quantifying over
        every fiber instead of over chain members is the error this signature makes hard.

        **Slotted means L0a — the LAYER, not a non-empty name** (D1/R4). L0b and L1 carry
        `qualname=''` as built and are membership-only, honestly chainless; the L0a MODULE SHELL
        also carries `''`, but that empty string is a real slot (the shell is a symbol-shaped
        region of the file) and it chains like any other. Reading slottedness off `slot != ''`
        would silently drop the shell's lineage — the one slot every file has."""
        runs: dict[str, list[str]] = {}
        for blob in chain:
            for m in self.fiber(path, blob):
                if m.layer != LAYER_CODE_AST:      # L0b/L1 are membership-only, chainless (R4)
                    continue
                seq = runs.setdefault(m.slot, [])
                if not seq or seq[-1] != m.content_id:
                    seq.append(m.content_id)
        return runs

    def slot_edges(self, path: str, chain: Sequence[str]) -> dict[str, list[tuple[str, str]]]:
        """The supersession edges: consecutive-run pairs per slot, so per slot
        `|edges| = |runs| - 1` by construction. Edge identity is
        `(path, slot, old_hash -> new_hash, at blob transition)`; the endpoints differ by
        construction because runs collapse equal adjacent occupants."""
        return {slot: list(zip(seq, seq[1:], strict=False))
                for slot, seq in self.slot_runs(path, chain).items()}

    # ── D5: purge — the ONE removal, and it leaves a recorded hole ───────────────────────────

    def tombstone_atom(self, content_id: str) -> int:
        """Mark every occupancy of a purged atom as a hole. Returns rows tombstoned."""
        cur = self._conn.execute(
            "UPDATE memberships SET tombstoned = 1, current = 0 "
            "WHERE content_id = ? AND tombstoned = 0", [content_id])
        self._conn.commit()
        return int(cur.rowcount)

    # ── D8: the repair pass — what makes a crash a non-event ────────────────────────────────

    def orphan_atom_ids(self) -> set[str]:
        """Atoms in the plane with NO occupancy at all — dormant geometry from a land that crashed
        between the vector insert and the fiber write (D8's named window).

        The state is deliberately OBSERVABLE rather than merely harmless: "nothing dangles by
        reference" is true of a store that never wrote anything, so a crash test that cannot see
        the orphan proves nothing about repair. Nothing here deletes them — the idempotent re-land
        adopts them at zero embed cost, which is exactly why the write order puts vectors first."""
        return {str(r["content_id"]) for r in self._conn.execute(
            "SELECT content_id FROM atoms WHERE content_id NOT IN "
            "(SELECT DISTINCT content_id FROM memberships)").fetchall()}

    def close(self) -> None:
        self._conn.close()


def _row(r: sqlite3.Row) -> Membership:
    return Membership(
        path=str(r["path"]), blob_sha=str(r["blob_sha"]), layer=str(r["layer"]),
        chunk_index=int(r["chunk_index"]), content_id=str(r["content_id"]), slot=str(r["slot"]),
        slot_line_start=int(r["slot_line_start"]), slot_line_end=int(r["slot_line_end"]),
        current=bool(r["current"]), tombstoned=bool(r["tombstoned"]),
    )


# ── cross-store operations: the read join, the repair pass, and the purge ────────────────────

@dataclass(frozen=True)
class ResolvedHit:
    """One ANN hit, resolved (D3). `row` is the atom — geometry, `text`, `_distance` if the hit came
    from a search — and `occupancies` are the places it lives.

    ⚑ `occupancies` carry the SLOT's extent, not the atom's text coverage (A2). A consumer
    rendering `slot_line_start..slot_line_end` as "this atom" is wrong, and maximally wrong for the
    module shell, whose extent is the whole file: the atom's content is `row["text"]`."""

    row: dict[str, object]
    occupancies: tuple[Membership, ...]


def resolve_occupancies(memberships: MembershipStore, hits: Sequence[dict[str, object]], *,
                        include_superseded: bool = False) -> list[ResolvedHit]:
    """The D3 read-path join: top-k atoms -> their occupancies `(path, blob, slot, lines, ...)`.

    Rows that are not shed atom rows (note rows, and any pre-D1 per-version code row) resolve to no
    occupancy and keep their own coordinates — this join adds a lane, it does not take one away."""
    out: list[ResolvedHit] = []
    for h in hits:
        cid = str(h.get("id", ""))
        occ = (tuple(memberships.occupancies(cid, include_superseded=include_superseded))
               if is_code_atom_row(dict(h)) else ())
        out.append(ResolvedHit(row=h, occupancies=occ))
    return out


def repair_current_any(vectors: VectorStore, memberships: MembershipStore) -> tuple[int, int]:
    """Rebuild the `current_any` cache from membership truth (D8/R3). Returns (raised, lowered).

    `current_any` is a cache with a rebuild path, and this is the rebuild path: the flag is
    recomputed as `n_doc(v, t) > 0` over every atom in the plane, and only the DRIFTED rows are
    written. Called after a crash, or on cadence as the R3 ratchet."""
    rows = vectors.atom_rows()
    ids = [str(r["id"]) for r in rows]
    held = memberships.currently_held(ids)
    to_true = [str(r["id"]) for r in rows if not bool(r.get("current")) and str(r["id"]) in held]
    to_false = [str(r["id"]) for r in rows if bool(r.get("current")) and str(r["id"]) not in held]
    return (vectors.set_current_any(to_true, True),
            vectors.set_current_any(to_false, False))


def current_any_drift(vectors: VectorStore, memberships: MembershipStore) -> list[str]:
    """Atom ids where the lance flag disagrees with membership truth — the R3 ratchet's reading,
    and the `current_any(v) ⇔ n_doc(v, t) > 0` invariant as a checkable list (empty ⇒ holds)."""
    rows = vectors.atom_rows()
    held = memberships.currently_held([str(r["id"]) for r in rows])
    return sorted(str(r["id"]) for r in rows
                  if bool(r.get("current")) != (str(r["id"]) in held))


def purge_atom(vectors: VectorStore, memberships: MembershipStore,
               content_id: str) -> PurgeReport:
    """The ONE removal (D5, finding-0164 — owner-gated; privacy outranks lineage).

    Delete the vector row, tombstone its memberships, forget its ledger entry: a RECORDED HOLE,
    never a silent one. Both counts are returned because "no code path deletes a vector" is
    satisfied vacuously by a purge that does nothing — the criterion is that the hole EXISTS."""
    deleted = vectors.delete_atom(content_id)
    tombstoned = memberships.tombstone_atom(content_id)
    memberships.forget_atom(content_id)
    return PurgeReport(vector_rows_deleted=deleted, memberships_tombstoned=tombstoned)


def open_membership_store(config: Config | None = None) -> MembershipStore:
    """The configured membership store — SQLite beside the vault catalog, exactly as
    `open_version_store` sites the version history."""
    from core.kernel.config import get_config

    cfg = config or get_config()
    return MembershipStore(cfg.paths.derived_store.parent / "memberships.sqlite")
