# ── Family: code rebuild — the one deliberate migration into the atom+membership model (bp-153) ──
# OBJECT:    the D7 rebuild — a read-only baseline that re-derives the dedup economics at the
#            CURRENT ledger cut, the step-0 `commit_diffs` capture, the carry-forward seed, and the
#            sliced/checkpointed/resumable walk that lands every ledger version as a fiber.
# INVARIANT: the OLD duplicated backfill is never run from here (52,755 vs 22,502 embeds is 2.34×
#            measured waste, D7). Every slice leaves DURABLE progress before it yields, so a run
#            killed mid-slice resumes without double-landing — and correctness does not depend on
#            the resume token at all: derivation is pure, so a re-landed fiber is equal by
#            construction (D2 step 3) and reconciliation converges (D2 step 4).
# ENFORCED:  structural — the rebuild NEVER stops the daemon and never writes from the CLI process:
#            it runs as a BACKGROUND queue job under the single writer (D7/S3), and the read-only
#            baseline holds no write handle to any store it measures.
"""The rebuild (dn-vector-membership-store D7/§3, bp-153; warrant finding-0168).

The membership store (bp-152) gave the corpus a lander; this module is the one deliberate migration
that fills it. Four movements, in strict blast-radius order — the order IS the design, because each
one is the precondition of the next:

  * **`measure_baseline` — read-only, and it writes nothing.** The economics that justified this
    rebuild were measured on the 2026-07-27 ledger cut; the corpus grows, so the constant is not
    portable and the RATIO is. This re-derives Σ per-version chunks (the duplicated model), the
    distinct atom count under D0, their ratio, the carry-forward seed, and whether that seed's
    embedder identity still matches the live config — at the cut the rebuild is actually about to
    run against. Nothing downstream may spend an embed before this has reported (§8 g).
  * **`capture_slice` — step 0, the first successful `commit_diffs` capture.** The machinery has
    shipped since bp-099 and has NEVER successfully run (the one attempt, job 300240, died in
    `TimeoutError` on 2026-07-25). Its resume token is not a token at all: `_commit_diffs_captured`
    is a durable per-commit marker, so the budget is enforced BETWEEN commits and every commit that
    completed stays completed. That is what makes a time-budgeted slice safe (§3 Q2).
  * **`seed_carry_forward` — the bulk embed-reuse, at zero embed cost.** The live store already
    holds L0a/L0b rows whose CANONICAL (header-free) body is exactly the atom D0 now identifies. The
    seed re-keys those rows to their atom id and COPIES the stored vector — no embedder call. It is
    governed by the embedder pin (bp-152 §6): a vector from another geometry is not a reuse, it is a
    silent corruption of the one ANN space, so the seed refuses unless the identity matches. L1 is
    deliberately excluded — its stored windows were cut over header-bearing prose and do not survive
    D0's windowing pin, so L1 re-embeds (D7).
  * **`rebuild_slice` — the walk.** Every ledger version becomes a fiber (D4/F3: a side-branch
    version sits on no chain but is still a member of M), landed through the D2 write path with its
    HEAD blob passed explicitly so currency reconciles correctly for a non-HEAD version.

**What the resume token is and is not.** The token records POSITION so a resumed run does not
re-derive work already done; it is not what makes the run safe. Landing version `v` twice is a
no-op by construction — the fiber is derived purely from `(path, source)` and `INSERT OR IGNORE`
leaves the existing rows standing — so a crash between the fiber write and the checkpoint costs one
re-derivation and changes nothing. R6's falsifier is therefore narrow and real: a slice that
exceeds its budget WITHOUT leaving durable progress. Every slice here leaves it before it yields.
"""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any

from core.ingest.code_corpus import CodeCorpusSync, atom_id, derive_code_chunks
from core.kernel.provenance import Provenance
from core.stores.memberships import EmbedderIdentity, MembershipStore
from core.stores.vectorstore import (
    ATOM_ROW_SHED,
    LAYER_CODE_AST,
    LAYER_CODE_TEXT,
    VectorStore,
)
from ops.code_lineage import capture_commit_diffs, ledger_commits, ledger_versions
from ops.code_snapshot import read_py_blobs

# How many ledger versions one slice derives before the clock is consulted. Small enough that a
# budget is honored promptly, large enough that the per-slice git batch read stays worthwhile.
VERSION_SLICE = 64

# How many distinct blobs one `git cat-file --batch` reads. Bounds peak memory on the read, never
# the semantics — a slice's versions are the unit of progress, not the blob batch.
BLOB_BATCH = 256

# The layers whose STORED embed text still recovers its canonical body (D7's carry-forward seed).
# L1 is absent deliberately, and that absence is the measured half of D0: its windows were cut over
# header-bearing prose, so a stored L1 window is not a window the current chunker would ever emit.
CARRY_FORWARD_LAYERS = (LAYER_CODE_AST, LAYER_CODE_TEXT)


# ── recovering an atom's identity from a row the OLD model wrote ─────────────────────────────


def canonical_body_of_stored(layer: str, text: str, source_path: str) -> str | None:
    """The CANONICAL (header-free) body behind a pre-D1 stored embed rendering, or None if this row
    cannot carry forward.

    ⚑ A wrong strip is silent identity corruption — it mints an atom nobody can ever hit again — so
    the header is not guessed from the shape of the line. L0a's stored text is
    `# {source_path}:{qualname}{signature}\\n{body}`, and the row still carries `source_path`, so
    the first line is verified to be THAT path's header before anything is removed. A body line that
    legitimately begins with `#` cannot pass that check.

    * **L0a** (`code_ast`) — strip the verified header line; the remainder is the identity input.
    * **L0b** (`code_text`) — raw-source windows are headerless by construction, so the stored text
      IS its own canonical body.
    * **L1** (`codedoc`) — None, always. Under D0 the windows are cut over canonical prose while
      these were cut over header-bearing prose, so the stored window is not a chunk the current
      derivation emits; carrying it forward would land geometry for an atom that does not exist
      (D7: L1 recuts and re-embeds).
    """
    if layer == LAYER_CODE_TEXT:
        return text
    if layer != LAYER_CODE_AST:
        return None
    head, sep, body = text.partition("\n")
    if not sep or not head.startswith(f"# {source_path}"):
        return None
    return body


def atom_id_of(layer: str, canonical_body: str) -> str:
    """`"{layer}:{content_hash}"` from a canonical body — the same identity `atom_id` mints from a
    live `CodeChunk`, spelled once here so a carried-forward row and a freshly derived chunk can
    never disagree about what an atom is (D1)."""
    return f"{layer}:{sha256(canonical_body.encode('utf-8')).hexdigest()}"


# ── Item 1: the read-only baseline ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class LayerBaseline:
    """One lane's half of the measurement. `ratio` is the lane's dedup factor at this cut."""

    chunks: int = 0
    atoms: int = 0
    seed: int = 0

    @property
    def ratio(self) -> float:
        return (self.chunks / self.atoms) if self.atoms else 0.0


@dataclass(frozen=True)
class EmbedderCheck:
    """Whether the carry-forward seed's geometry is the one the live config would produce.

    The check is deliberately split into what the store CAN answer and what it structurally cannot.
    `dim` is recoverable from any stored vector's length. **`model` is not recorded on a pre-D1
    row** — the vector table's Arrow schema is shared with the prose lane and has no embedder
    column, which is precisely the gap bp-152's `atoms` ledger exists to close. So for rows the
    membership ledger already knows, the model is checked against the recorded identity; for the
    legacy rows the honest answer is "unrecorded", and `unrecorded_rows` says how many carry that
    status rather than letting a silent assumption ride into a 13k-atom bulk reuse."""

    live: EmbedderIdentity
    stored_dim: int | None = None
    ledger_atoms: int = 0
    ledger_mismatched: int = 0
    unrecorded_rows: int = 0

    @property
    def dim_match(self) -> bool:
        return self.stored_dim is None or self.stored_dim == self.live.dim

    @property
    def matches(self) -> bool:
        """True when nothing CHECKABLE contradicts reuse. An unrecorded model is not a match claim
        — `unrecorded_rows` carries that, and the caller decides whether the evidence outside the
        store (the config's own history) closes it."""
        return self.dim_match and self.ledger_mismatched == 0


@dataclass(frozen=True)
class Baseline:
    """The rebuild's economics, re-derived at the CURRENT cut (§3 Q6/Q7, §8 g).

    `ratio` is the portable claim; the absolute counts are not, because the corpus grows between
    the measurement and the run. The design's falsifier compares THIS ratio to 2.34× like-for-like,
    and a deviation beyond ~10% is a finding rather than a shrug."""

    versions: int = 0
    unreadable: int = 0
    chunks: int = 0
    atoms: int = 0
    seed: int = 0
    per_layer: dict[str, LayerBaseline] = field(default_factory=dict)
    embedder: EmbedderCheck | None = None

    @property
    def ratio(self) -> float:
        """Σ per-version chunks ÷ distinct atoms — the dedup factor the rebuild is buying."""
        return (self.chunks / self.atoms) if self.atoms else 0.0

    @property
    def embeds_avoided(self) -> int:
        """Embeds the membership model does not pay that the duplicated model would have."""
        return self.chunks - self.atoms

    def __str__(self) -> str:
        lanes = " · ".join(f"{k} {v.ratio:.2f}×" for k, v in sorted(self.per_layer.items()))
        return (f"versions={self.versions} chunks={self.chunks} atoms={self.atoms} "
                f"ratio={self.ratio:.2f}× ({lanes}) seed={self.seed} "
                f"embeds_avoided={self.embeds_avoided}")


def _slice_sources(repo: Path, versions: Sequence[tuple[str, str]]) -> dict[str, str]:
    """blob_sha -> source for one slice, in ONE batched git read (φ_code's own reader, never a
    second one). A blob git cannot produce (shallow clone, pruned object) is simply absent."""
    return read_py_blobs(repo, sorted({b for _, b in versions}))


def measure_baseline(sync: CodeCorpusSync, db: sqlite3.Connection, *,
                     progress: Callable[[int, int], None] | None = None) -> Baseline:
    """Re-derive the rebuild's target and cost at the current ledger cut. **Writes nothing.**

    The two counts are the whole point and they are computed over the SAME version set, in one
    walk, so they cannot drift apart:

      * Σ per-version chunks — what the duplicated model would embed, one row per chunk per version;
      * |distinct atoms| — what the membership model embeds, one row per `(layer, content_hash)`
        under D0's header-free identity, corpus-wide.

    The version set is `ledger_versions` — every distinct `(path, blob_sha)` the ledger recorded,
    not only chain members: a side-branch version lands a fiber though it sits on no chain (D4/F3),
    so quantifying over chains here would under-count the rebuild's work.

    No figure this function reports is a constant. That is not tidiness: the same defect class
    (issue #28) has docstrings in this repo claiming an edge count 8.4× off the live store, and a
    baseline that inherited July's 22,502 would authorize spending against a number nobody
    re-checked."""
    versions = ledger_versions(db)
    chunks = 0
    atoms: set[str] = set()
    per_layer_chunks: dict[str, int] = {}
    per_layer_atoms: dict[str, set[str]] = {}
    unreadable = 0

    for start in range(0, len(versions), BLOB_BATCH):
        window = versions[start:start + BLOB_BATCH]
        sources = _slice_sources(sync.repo, window)
        for path, blob_sha in window:
            source = sources.get(blob_sha)
            if source is None:
                unreadable += 1
                continue
            for ch in derive_code_chunks(path, source, max_chars=sync.max_chars,
                                         overlap_chars=sync.overlap_chars):
                chunks += 1
                cid = atom_id(ch)
                atoms.add(cid)
                per_layer_chunks[ch.layer] = per_layer_chunks.get(ch.layer, 0) + 1
                per_layer_atoms.setdefault(ch.layer, set()).add(cid)
        if progress is not None:
            progress(min(start + BLOB_BATCH, len(versions)), len(versions))

    seed_ids = carry_forward_candidates(sync.store, targets=atoms)
    embedder = _check_embedder(sync.store, sync.memberships, sync.embedder_identity, seed_ids)
    per_layer = {
        layer: LayerBaseline(
            chunks=per_layer_chunks.get(layer, 0),
            atoms=len(per_layer_atoms.get(layer, ())),
            seed=sum(1 for cid in seed_ids if cid.startswith(f"{layer}:")),
        )
        for layer in sorted(set(per_layer_chunks) | set(per_layer_atoms))
    }
    return Baseline(versions=len(versions), unreadable=unreadable, chunks=chunks,
                    atoms=len(atoms), seed=len(seed_ids), per_layer=per_layer,
                    embedder=embedder)


def _check_embedder(vectors: VectorStore, memberships: MembershipStore,
                    live: EmbedderIdentity, seed_ids: set[str]) -> EmbedderCheck:
    """Is the seed's stored geometry the live one? Read-only, and honest about what it cannot see.

    Reuse across a model change puts two geometries in ONE ANN space, and no downstream measurement
    can detect it — which is why the owner pinned reuse to the embedder identity and why this runs
    BEFORE Item 3 spends anything."""
    sample = vectors.project(["vector"], where=f"provenance = '{Provenance.CODE.value}'", limit=1)
    stored_dim = len(list(sample[0]["vector"])) if sample and sample[0].get("vector") else None
    known = memberships.known_atoms(seed_ids, live) if seed_ids else set()
    ledger_all = memberships.ledger_atom_ids() & seed_ids if seed_ids else set()
    return EmbedderCheck(live=live, stored_dim=stored_dim, ledger_atoms=len(ledger_all),
                         ledger_mismatched=len(ledger_all - known),
                         unrecorded_rows=len(seed_ids - ledger_all))


# ── the carry-forward seed: bulk embed-reuse by canonical re-hash ────────────────────────────


def carry_forward_candidates(vectors: VectorStore, *,
                             targets: set[str] | None = None) -> set[str]:
    """Atom ids recoverable from rows the OLD model already embedded — the D7 seed, as a set.

    Read-only and vector-free: only `id`, `layer`, `text` and `source_path` are projected, so
    measuring the seed never pays for 2560 floats per row. `targets` restricts the answer to atoms
    the CURRENT derivation actually emits, which is what makes the count meaningful — a stored row
    cut under a superseded rule (bp-151's A1.2 threshold change, say) re-hashes to an atom no
    version would ever reference, and counting it would inflate the seed with dead geometry."""
    seed: set[str] = set()
    for row in vectors.project(["id", "layer", "text", "source_path"],
                               where=f"provenance = '{Provenance.CODE.value}'"):
        layer = str(row.get("layer") or "")
        if layer not in CARRY_FORWARD_LAYERS:
            continue
        source_path = str(row.get("source_path") or "")
        if not source_path:                      # already a shed atom row (D1) — not a candidate
            continue
        body = canonical_body_of_stored(layer, str(row.get("text") or ""), source_path)
        if body is None:
            continue
        cid = atom_id_of(layer, body)
        if targets is None or cid in targets:
            seed.add(cid)
    return seed


@dataclass(frozen=True)
class SeedReport:
    """What the carry-forward actually moved. `embeds` is asserted zero by the acceptance test —
    the seed's entire claim is that ~59% of the atom set enters the plane without an embedder
    call."""

    rows_written: int = 0
    atoms_recorded: int = 0
    embeds: int = 0
    refused_embedder_mismatch: bool = False


def seed_carry_forward(vectors: VectorStore, memberships: MembershipStore,
                       embedder: EmbedderIdentity, *, targets: set[str],
                       stored_dim: int | None = None) -> SeedReport:
    """Land the seed atoms by COPYING stored vectors onto atom-keyed rows (D7). Zero embeds.

    Each pre-D1 row whose canonical body hashes to a wanted atom becomes a new shed atom row
    (`ATOM_ROW_SHED`) carrying the SAME vector, and is recorded in the membership ledger under
    `embedder` so `land()` sees it as present and never re-embeds it. The old row is neither
    deleted nor modified — append-only holds, and retiring the duplicated model is a separate,
    explicitly reported step (`retire_legacy_rows`).

    **The pin is a refusal, not a warning.** If the stored dimension contradicts the live config
    the seed does nothing at all and says so: a partial seed under a changed embedder would put two
    geometries in one ANN space, which is the one failure this whole path exists to prevent.

    `current=False` on every seeded row is correct rather than conservative: at seed time the atom
    has no occupancy — the fibers land afterwards — and `land()` raises `current_any` in step 5 for
    exactly the atoms whose current-membership count crosses 0→1 (D8's write order)."""
    if stored_dim is not None and stored_dim != embedder.dim:
        return SeedReport(refused_embedder_mismatch=True)
    already = memberships.known_atoms(targets, embedder)
    wanted = targets - already
    rows: dict[str, dict[str, Any]] = {}
    for row in vectors.project(["id", "layer", "text", "source_path", "vector"],
                               where=f"provenance = '{Provenance.CODE.value}'"):
        layer = str(row.get("layer") or "")
        source_path = str(row.get("source_path") or "")
        if layer not in CARRY_FORWARD_LAYERS or not source_path:
            continue
        text = str(row.get("text") or "")
        body = canonical_body_of_stored(layer, text, source_path)
        if body is None:
            continue
        cid = atom_id_of(layer, body)
        if cid not in wanted or cid in rows:
            continue
        rows[cid] = {
            **ATOM_ROW_SHED,
            "id": cid, "title": "", "provenance": Provenance.CODE.value,
            "text": text, "layer": layer, "current": False,
            "vector": [float(v) for v in list(row["vector"])],   # copied, never re-embedded
        }
    if not rows:
        return SeedReport()
    written = vectors.add(list(rows.values()))
    recorded = memberships.record_atoms(
        [(cid, str(r["layer"])) for cid, r in rows.items()], embedder)
    return SeedReport(rows_written=written, atoms_recorded=recorded, embeds=0)


# ── Item 2: step 0 — the sliced `commit_diffs` capture ───────────────────────────────────────


@dataclass(frozen=True)
class CaptureProgress:
    """One capture slice's outcome. `remaining > 0` with `budget_spent` true is the NORMAL yield —
    the slice ran out of clock and stopped at a commit boundary, having left every commit it
    finished durably marked."""

    captured: int = 0
    remaining: int = 0
    budget_spent: bool = False

    @property
    def done(self) -> bool:
        return self.remaining == 0


def pending_commits(db: sqlite3.Connection) -> list[str]:
    """Ledger commits whose diffs are not yet captured, in capture order. Empty ⇒ step 0 is done.

    Reading the marker table IS reading the resume position, which is why this lane needs no
    separate token: progress lives where the work landed.

    ⚑ **This is a READ, so it does not create the schema it reads.** The obvious spelling calls
    `_ensure_schema` first (the tables may not exist — on the live ledger they never have), and
    that is a write: a CREATE TABLE on a connection the caller opened `mode=ro` raises, and on a
    read-write connection it silently mutates the file a dry-run promised not to touch. The
    read-only baseline behind `palace code-rebuild --dry-run` calls this against the LIVE ledger,
    so the absent-table case is answered instead of created: no marker table means nothing has
    been captured, which is the true answer and the one step 0 exists to act on."""
    marked: set[str] = set()
    exists = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = '_commit_diffs_captured'"
    ).fetchone()
    if exists:
        marked = {str(s) for (s,) in db.execute("SELECT commit_sha FROM _commit_diffs_captured")}
    return [c for c in ledger_commits(db) if c not in marked]


def capture_slice(db: sqlite3.Connection, repo: Path, *, budget_s: float = 60.0,
                  batch: int = 25) -> CaptureProgress:
    """Capture `commit_diffs` for as many ledger commits as `budget_s` allows, then yield (D7/R6).

    The shipped `capture_commit_diffs` has never successfully run against real data — the one
    attempt died in `TimeoutError` (job 300240, 2026-07-25) because the whole history rode one
    unbounded job. This wraps it in a clock without changing what it does: commits are handed over
    in small batches and the budget is checked BETWEEN batches, never inside one.

    **Why that is safe, and why it satisfies R6.** Each commit is captured under its own `with db:`
    transaction and marked in `_commit_diffs_captured` (`ops/code_lineage.py:119-129`). So the
    durable progress is the marker table itself: a slice that stops after batch *k* has committed
    batches 1..*k*, and the next slice re-computes `pending_commits` and continues. There is no
    window in which work is done but unrecorded, which is exactly the state R6's falsifier names —
    "a slice exceeding its budget WITHOUT leaving a checkpoint". A budget overrun here leaves one.

    The first batch always runs, whatever the budget: a slice that yields having done nothing would
    turn a tight budget into a livelock rather than slow progress."""
    pending = pending_commits(db)
    if not pending:
        return CaptureProgress()
    deadline = time.monotonic() + budget_s
    captured = 0
    index = 0
    while index < len(pending):
        window = pending[index:index + batch]
        captured += capture_commit_diffs(db, repo, window)
        index += len(window)
        if time.monotonic() >= deadline and index < len(pending):
            return CaptureProgress(captured=captured, remaining=len(pending) - index,
                                   budget_spent=True)
    return CaptureProgress(captured=captured, remaining=0)


# ── Item 3: the sliced, checkpointed, resumable rebuild ──────────────────────────────────────


@dataclass(frozen=True)
class RebuildProgress:
    """One rebuild slice's outcome, and the resume token that positions the next one.

    `token` is JSON so the queue's `checkpoint` column carries it unchanged; `None` means the walk
    finished. `atoms_embedded` is the number that must stay near zero for the carry-forward lanes —
    it is the acceptance's arithmetic, not a log line."""

    versions_landed: int = 0
    atoms_embedded: int = 0
    atoms_reused: int = 0
    membership_rows: int = 0
    remaining: int = 0
    token: str | None = None

    @property
    def done(self) -> bool:
        return self.token is None


def _resume_index(token: str | None, versions: Sequence[tuple[str, str]]) -> int:
    """Where a resumed run picks up. A token naming a version resumes AT it (never after), so a
    version whose fiber write and whose checkpoint straddled a crash is simply re-landed — which is
    a no-op, because derivation is pure and `write_fiber` leaves an existing fiber standing."""
    if not token:
        return 0
    try:
        mark = json.loads(token)
        path, blob = str(mark["path"]), str(mark["blob_sha"])
    except (ValueError, KeyError, TypeError):
        return 0                                   # an unreadable token costs a re-walk, never a
    for i, (p, b) in enumerate(versions):          # wrong landing — the walk is idempotent
        if (p, b) == (path, blob):
            return i
    return 0


def rebuild_slice(sync: CodeCorpusSync, db: sqlite3.Connection, *, token: str | None = None,
                  budget_s: float = 120.0, slice_size: int = VERSION_SLICE) -> RebuildProgress:
    """Land one time-budgeted slice of the ledger's versions, then yield with a resume token.

    Every distinct `(path, blob_sha)` the ledger recorded becomes a fiber — not only the chain
    members, because a side-branch version lands a fiber while sitting on no chain (D4/F3). Each
    version is landed through the D2 write path with its path's HEAD blob passed explicitly, so a
    historical (non-HEAD) version reconciles to `current=false` and the HEAD one to `current=true`
    rather than the last-landed version winning.

    **Resumability is a property of the walk, not of the token.** Landing a version twice writes no
    row (`INSERT OR IGNORE` over a purely derived fiber) and embeds nothing (the atoms are already
    in the plane), and reconciliation converges on every call — so the token only saves
    re-derivation time. The acceptance test kills a run mid-slice and resumes precisely to
    demonstrate that the invariant does not depend on the token surviving.

    **The old duplicated backfill is never called from here.** `CodeCorpusSync.backfill` would walk
    the same versions, but this walk exists to be SLICED and budgeted; the invariant that matters is
    the one D7 states as measured waste, and it is honored by landing atoms, not by which function
    is called."""
    versions = ledger_versions(db)
    start = _resume_index(token, versions)
    head = dict(_head_blobs(sync))
    lander = sync.lander
    deadline = time.monotonic() + budget_s
    landed = embedded = reused = rows = 0
    index = start

    while index < len(versions):
        window = versions[index:index + slice_size]
        sources = _slice_sources(sync.repo, window)
        for path, blob_sha in window:
            source = sources.get(blob_sha)
            index += 1
            if source is None:                     # blob unreachable (shallow/pruned) — skip, said
                continue
            chunks = derive_code_chunks(path, source, max_chars=sync.max_chars,
                                        overlap_chars=sync.overlap_chars)
            if not chunks:
                continue
            report = lander.land(path, blob_sha, chunks,
                                 head_blob_sha=head.get(path, blob_sha))
            landed += 1
            embedded += report.atoms_embedded
            reused += report.atoms_reused
            rows += report.membership_rows
        if time.monotonic() >= deadline and index < len(versions):
            nxt = versions[index]
            return RebuildProgress(
                versions_landed=landed, atoms_embedded=embedded, atoms_reused=reused,
                membership_rows=rows, remaining=len(versions) - index,
                token=json.dumps({"path": nxt[0], "blob_sha": nxt[1]}))
    return RebuildProgress(versions_landed=landed, atoms_embedded=embedded, atoms_reused=reused,
                           membership_rows=rows, remaining=0, token=None)


def _head_blobs(sync: CodeCorpusSync) -> list[tuple[str, str]]:
    """`(path, blob_sha)` at HEAD — reused from φ_code's blob walk, never a second git shell."""
    from ops.code_snapshot import list_py_blobs

    return list_py_blobs(sync.repo, "HEAD")


# ── the phase machine: what one queue slice of the rebuild does ──────────────────────────────

PHASE_CAPTURE = "capture"      # step 0 — `commit_diffs` (§3)
PHASE_SEED = "seed"            # the carry-forward bulk reuse (D7)
PHASE_LAND = "land"            # the sliced walk over every ledger version
PHASE_COMPACT = "compact"      # physical maintenance + retiring the duplicated rows (§3)


@dataclass(frozen=True)
class StepResult:
    """One queue slice's outcome. `token is None` means the whole rebuild is complete — which is
    what the handler reads to decide between completing the job and checkpointing it."""

    phase: str
    message: str
    token: str | None = None

    @property
    def done(self) -> bool:
        return self.token is None


def rebuild_step(sync: CodeCorpusSync, db: sqlite3.Connection, *, token: str | None = None,
                 capture_budget_s: float = 60.0, rebuild_budget_s: float = 120.0,
                 capture_batch: int = 25, slice_size: int = VERSION_SLICE) -> StepResult:
    """Run ONE time-budgeted slice of the rebuild and return the token that positions the next.

    The phases are the D7/§3 ordering, and they are ordered because each is the other's
    precondition: `capture` (step 0 — the chains' substrate, never successfully run before this
    plan) → `seed` (bulk embed-reuse, so the walk pays for ~a third of the atoms rather than all of
    them) → `land` (every ledger version becomes a fiber) → `compact` (the physical maintenance §3
    makes part of the store's semantics, plus retiring the duplicated rows the rebuild replaced).

    **No phase depends on the token for correctness.** `capture` resumes from its own marker table;
    `seed` is keyed on atoms already present, so re-running it seeds nothing; `land` re-lands
    idempotently; `compact` is physical. The token buys time, and only time — which is why killing
    a run mid-slice and resuming is a test that passes rather than a risk that is managed.

    **The daemon is never stopped.** This is a queue citizen: it runs inside one job's dispatch,
    yields at a slice boundary, and re-queues itself (D7/S3). The job class it enlarges is exactly
    the one that wedged, which is why the budget is enforced and why every yield leaves durable
    progress.

    `capture_batch` / `slice_size` are the units the budget is checked BETWEEN, exposed rather than
    fixed because they set the granularity of yielding: a budget cannot interrupt a batch, so the
    smallest slice that can be observed to yield is one batch. They are what the acceptance test
    turns down to 1 to force mid-phase yields on a small fixture."""
    mark = _read_token(token)
    phase = str(mark.get("phase") or PHASE_CAPTURE)

    if phase == PHASE_CAPTURE:
        prog = capture_slice(db, sync.repo, budget_s=capture_budget_s, batch=capture_batch)
        if not prog.done:
            return StepResult(PHASE_CAPTURE,
                              f"capture: +{prog.captured} commits, {prog.remaining} to go",
                              json.dumps({"phase": PHASE_CAPTURE}))
        return StepResult(PHASE_CAPTURE, f"capture: +{prog.captured} commits, COMPLETE",
                          json.dumps({"phase": PHASE_SEED}))

    if phase == PHASE_SEED:
        # ONE derivation pass feeds all three: the target set, the seed's filter, and the pin's
        # check. Deriving twice here would double the phase's cost for no new information.
        seed_ids = carry_forward_candidates(sync.store, targets=_target_atoms(sync, db))
        check = _check_embedder(sync.store, sync.memberships, sync.embedder_identity, seed_ids)
        report = seed_carry_forward(sync.store, sync.memberships, sync.embedder_identity,
                                    targets=seed_ids, stored_dim=check.stored_dim)
        if report.refused_embedder_mismatch:
            # Not a silent downgrade: the seed is the geometry-mixing hazard the pin exists for, so
            # a mismatch stops the phase rather than proceeding to re-embed 15k atoms unannounced.
            return StepResult(PHASE_SEED,
                              "seed REFUSED: stored vector dim does not match the live embedder — "
                              "the carry-forward is not free and the rebuild's economics changed",
                              None)
        return StepResult(PHASE_SEED,
                          f"seed: {report.rows_written} atoms carried forward at "
                          f"{report.embeds} embeds (of {len(seed_ids)} recoverable)",
                          json.dumps({"phase": PHASE_LAND}))

    if phase == PHASE_LAND:
        walk = rebuild_slice(sync, db, token=token, budget_s=rebuild_budget_s,
                             slice_size=slice_size)
        msg = (f"land: {walk.versions_landed} versions, +{walk.atoms_embedded} embeds, "
               f"{walk.atoms_reused} reused, +{walk.membership_rows} occupancies")
        if walk.token is not None:
            nxt = dict(json.loads(walk.token))
            nxt["phase"] = PHASE_LAND
            return StepResult(PHASE_LAND, f"{msg}, {walk.remaining} versions to go",
                              json.dumps(nxt))
        return StepResult(PHASE_LAND, f"{msg}, COMPLETE",
                          json.dumps({"phase": PHASE_COMPACT}))

    retired = retire_legacy_rows(sync.store)
    compaction = sync.store.compact(older_than=timedelta(0))
    return StepResult(PHASE_COMPACT,
                      f"compact: {compaction}; {retired} legacy rows superseded (retained)", None)


def _read_token(token: str | None) -> dict[str, object]:
    """A token is advisory, so an unreadable one restarts the walk rather than failing the job —
    every phase is idempotent, so the cost of a bad token is time, never a wrong landing."""
    if not token:
        return {}
    try:
        mark = json.loads(token)
    except ValueError:
        return {}
    return dict(mark) if isinstance(mark, dict) else {}


def _target_atoms(sync: CodeCorpusSync, db: sqlite3.Connection) -> set[str]:
    """Every atom the CURRENT derivation emits over the whole ledger — the seed's filter, so a row
    cut under a superseded rule never carries geometry forward for an atom no version references."""
    targets: set[str] = set()
    versions = ledger_versions(db)
    for start in range(0, len(versions), BLOB_BATCH):
        window = versions[start:start + BLOB_BATCH]
        sources = _slice_sources(sync.repo, window)
        for path, blob_sha in window:
            source = sources.get(blob_sha)
            if source is None:
                continue
            for ch in derive_code_chunks(path, source, max_chars=sync.max_chars,
                                         overlap_chars=sync.overlap_chars):
                targets.add(atom_id(ch))
    return targets


def retire_legacy_rows(vectors: VectorStore) -> int:
    """Flip every pre-D1 duplicated CODE row to `current=false`, RETAINING it. Returns rows flipped.

    [cross-ref: extension] The plan does not enumerate this step and it is reported separately for
    exactly that reason. The rebuild lands the atom plane beside the duplicated rows it replaces,
    and both would answer the default current-view search — the old model's per-version rows are
    what D1 supersedes, so leaving them current means the rebuild bought its dedup and then served
    the duplication anyway.

    It is a SUPERSESSION, not a removal, and that is the whole reason it is expressible here: this
    is keep-and-link (D2) applied to the rows the row model retired — nothing is deleted, `|V|`
    does not decrease, and D5's "purge is the ONE removal" is untouched. A reviewer who disagrees
    reverses it with one `update`, and the rows are all still there to reverse it with."""
    return vectors.supersede_legacy_code_rows()
