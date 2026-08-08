# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    the code embed lane — the repo's source, docstrings, and comments as a first-class
#            semantic source (dn-code-ingest-pipeline, warrant finding-0146). Three co-registered
#            projections of one file: L0a (structural), L0b (textual), L1 (prose).
# INVARIANT: every code chunk row is ρ ≡ CODE — a wrong-class row is UNREPRESENTABLE here: NO
#            provenance parameter exists anywhere on this module's API (F-CI1). CODE ∉
#            MIRROR_READABLE, so a MirrorView / the default semantic_search never surface it.
# ENFORCED:  structural — `code_rows()` hardcodes `Provenance.CODE` (the `CodeObservation.to_row`
#            move); it does NOT call the provenance-parametric `ingest_note` (a laundering surface),
#            it reuses chunk_text / Embedder.embed_documents / VectorStore.add BELOW the parameter.
"""The code embed lane (dn-code-ingest-pipeline §2.1/§2.1b/§2.2/§2.3/§2.7; bp-092/CI-1).

Ouroboros's largest artifact — its own code, carrying the math and the §-warrants — was the one
region outside the semantic self-map (finding-0146). This lane pulls it in under the SAME vector
store, embedder, and group-by-digest machinery the notes use, discriminated by a `layer` coordinate:

  * **L0a — the structural (AST) reading** (`layer=code_ast`): one chunk per symbol, sliced at AST
    boundaries, header-prefixed `# {path}:{qualname}{signature}`. Nested defs own their lines, so a
    parent embeds as its SHELL (own lines minus descendants) and the module shell covers preamble +
    inter-symbol + trailing — **every source line in exactly one L0a chunk** (F-CI2 byte-cover).
  * **L0b — the windowed textual reading** (`layer=code_text`): the note chunker's sliding
    char-window (`chunk_text`, the ONE window machinery — NOT `derive_chunks`, whose Logseq
    property-strip must not run on code) over the RAW source; bodies and `#` comments flow together.
  * **L1 — the prose reading** (`layer=codedoc`): module + symbol docstrings + inline comments in
    source order, windowed as CANONICAL (header-free) prose and prefixed for retrieval by a single
    `# {path}` line — it lives in the note neighbourhood.

Derivation is a PURE function of (path, source): re-running yields bit-identical chunks (F-CI2
re-derivability). All embedding is LOCAL (the core embedder) — zero network egress
(non-negotiable #1).

[banner: correction] The three projections WERE joined by line-range coordinates carried ON the
vector rows, and `digest` (the git blob sha) made group-by-digest yield "file = source object,
chunks = members". **Neither is true of a code row any more** (dn-vector-membership-store D1,
bp-152). The vector plane holds ONE row per distinct idea-atom `(layer, content_hash)`,
corpus-wide and append-only; ALL occupancy — which `(path, blob_sha)` version holds which atom, at
which slot and lines, and whether that occupancy is current — moved into the membership relation
(`core/stores/memberships.py`). A version is a FIBER `M(path, blob_sha)`, the source object is
that fiber, and a code consumer resolves a hit through the membership join (D3), never through
group-by-digest. The measured payoff is the reason: 52,755 duplicated embeds over the full ledger
history become 22,502 atoms (2.34×, D7), and a revert or a `git mv` costs zero geometry.

[banner: correction] A chunk's IDENTITY (`content_hash`) hashed its full embed text — coordinate
header included — so a `git mv` re-hashed every chunk of the file and every `(path, slot)` lineage
chain through it severed, on an operation this repo performs constantly (dn-vector-membership-store
§0.1 F1/F2). CORRECTED per D0 (owner-ruled 2026-07-27, `strip-headers-from-the-atom-hash`):
**identity is the header-free CANONICAL body; the embed text still carries its header** (retrieval
context is untouched, R7). L1 additionally cuts its windows over the canonical prose — stripping at
hash time alone leaves window boundaries computed over header-bearing text, so a path-length change
still recuts them. Measured over all 580 tracked `.py` files at 45c4a15, renaming every one of them:
**11,096** atoms minted under the old identity → **2,373** under strip-at-hash-only → **3** under
this pin (those 3 are the parked oversize-threshold residue, issue #31); a one-line top-of-file
insert in every file: 2,114 → 2,114 → **0**. Consequence, named: identity now differs from embed
text, so a shared atom's stored text/vector is its FIRST-LANDED rendering and display coordinates
resolve from memberships, never from the stored text.

[banner: supersession] The incremental sync's delete+replace contract (old §2.7) is REVERSED to
keep-and-link per `dn-temporal-code-corpus` D2 (warrant finding-0163, bp-099): a superseded code
version is RETAINED with `current=false`, never deleted, and `backfill()` embeds the full ledger
history (D1) — so every code version is a semantic node and the causal graph's supersession edge
`blob(v)→blob(v+1)` has both endpoints resolvable. Default retrieval stays current-view (D3).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol

from core.kernel.ingest.chunk import chunk_text
from core.kernel.provenance import Provenance
from core.stores.memberships import (
    CurrencyReport,
    EmbedderIdentity,
    Membership,
    MembershipStore,
)
from core.stores.vectorstore import (
    ATOM_ROW_SHED,
    LAYER_CODE_AST,
    LAYER_CODE_TEXT,
    LAYER_CODEDOC,
    VectorStore,
)
from ops.code_snapshot import FileShape, Symbol, list_py_blobs, parse_source, read_py_blobs

_DEFAULT_MAX_CHARS = 1200
_DEFAULT_OVERLAP_CHARS = 150


class _Embedder(Protocol):
    """The one method the lane calls — embedding runs LOCALLY in core (no network, #1)."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class CodeChunk:
    """One embeddable code chunk with its fiber coordinates. `layer` discriminates the projection;
    `(qualname, slot_line_start, slot_line_end)` are the §2.4 backpointers, and they travel to the
    MEMBERSHIP row now (bp-152 D1), not to the vector row.

    TWO renderings, deliberately different (D0): `text` is the EMBED rendering and KEEPS its
    coordinate header (retrieval context, R7); `canonical_body` is the IDENTITY input and is
    header-free. Every chunker passes the canonical body from the site that already holds it — it
    is NEVER re-derived by re-parsing `text`, so a body line that legitimately begins with `#` can
    never be mistaken for a coordinate header (a wrong strip is silent identity corruption).

    [banner: correction] `line_start` / `line_end` are RENAMED to `slot_line_start` /
    `slot_line_end` (dn-vector-membership-store Amendment A2, owner-ruled 2026-08-06 on issue #34).
    The stored values do not change; the name does, because the old name licensed a wrong reading.
    **They are the SLOT's declared extent — where the symbol lives — never the atom's text
    coverage.** L0a partitions by INNERMOST OWNER, so a class's chunk holds the class statement,
    its docstring and its attributes but NOT its methods (which became their own chunks) — while
    the emitted coordinates are `owner.lineno, owner.end_lineno`, the owner's full declared span.
    They coincide exactly for leaf symbols, which is why every leaf-symbol fixture is blind to the
    divergence; the module shell is the maximal case, carrying `1..n` (the ENTIRE file) for a few
    lines of preamble. The values are also non-contiguous in general: a symbol with nested children
    owns lines scattered across its span. A consumer that wants "where is this symbol" reads the
    span; a consumer that wants the atom's content reads `text`. This is the intended behavior, not
    a defect to fix — the fix was to stop letting the field name hide the difference."""

    layer: str
    qualname: str
    slot_line_start: int
    slot_line_end: int
    text: str                # the embed rendering: header + body (headerless for L0b)
    canonical_body: str      # the identity input: header-free (== text for L0b)

    @property
    def content_hash(self) -> str:
        """[banner: correction] Identity = the CANONICAL (header-free) body, never the embed text
        (D0, owner-ruled 2026-07-27; this hashed `self.text` before). A filename is mutable: with
        the coordinate header inside the hash, a rename re-hashes every chunk and every
        (path, slot) occupancy chain through the file severs — on an operation this repo performs
        constantly. Embed text may keep headers; identity may not."""
        return sha256(self.canonical_body.encode("utf-8")).hexdigest()


# ── L0a: the structural (AST) reading — per-symbol slices + module shell (byte-cover) ────

def _innermost_owner(symbols: Sequence[Symbol], line: int) -> Symbol | None:
    """The innermost symbol whose lineno..end_lineno span contains `line` (smallest span wins), or
    None for a module-shell line. This ownership IS the L0a partition: every line has exactly one
    owner (a symbol or the shell), so the slices byte-cover the file (F-CI2)."""
    containing = [s for s in symbols if s.lineno <= line <= s.end_lineno]
    if not containing:
        return None
    return min(containing, key=lambda s: s.end_lineno - s.lineno)


def _l0a_chunks(path: str, lines: list[str], shape: FileShape, *,
                max_chars: int, overlap_chars: int) -> list[CodeChunk]:
    n = len(lines)
    # group source-line numbers by innermost owner (qualname, or '' for the module shell)
    owned: dict[str, list[int]] = {}
    coords: dict[str, tuple[str, int, int]] = {}   # qualname -> (header, slot extent start/end)
    for i in range(1, n + 1):
        owner = _innermost_owner(shape.symbols, i)
        if owner is None:
            key = ""
            coords.setdefault(key, (f"# {path}", 1, n))
        else:
            key = owner.qualname
            coords.setdefault(key, (f"# {path}:{owner.qualname}{owner.signature}",
                                    owner.lineno, owner.end_lineno))
        owned.setdefault(key, []).append(i)

    out: list[CodeChunk] = []
    # emit in source order (by first owned line) so the layer is deterministic
    for key in sorted(owned, key=lambda k: owned[k][0]):
        header, ls, le = coords[key]
        body = "\n".join(lines[i - 1] for i in owned[key])
        full = f"{header}\n{body}"
        # identity = the header-free body (D0); the header rides only on the embed text.
        # The whole↔windowed cut is decided over the CANONICAL body (Amendment A1.2,
        # dn-vector-membership-store): len(body), not len(full). This closes issue #31 — a
        # rename that crossed the budget used to flip a slice whole↔windowed on path length
        # alone, minting a spurious atom. The decision is now path-independent; the embed text
        # emitted below is unchanged (`text=full`) so L0a text still keeps its header (D0/R7).
        if len(body) <= max_chars:
            out.append(CodeChunk(LAYER_CODE_AST, key, ls, le, text=full, canonical_body=body))
        else:  # oversized slice: hard-split the body via the ONE window machinery, re-headered
            for piece in chunk_text(body, max_chars=max_chars, overlap_chars=overlap_chars):
                out.append(CodeChunk(LAYER_CODE_AST, key, ls, le,
                                     text=f"{header}\n{piece.text}", canonical_body=piece.text))
    return out


# ── L0b: the windowed textual reading — chunk_text over raw source ───────────────────────

def _locate_span(chunk_body: str, lines: list[str], cursor: int) -> tuple[int, int, int]:
    """Best-effort (slot_line_start, slot_line_end, next_cursor) for an L0b window — located by
    matching the window's first/last non-blank line back into the source (windows overlap by
    design, so the cursor only hints, never hard-bounds). (0, 0) when unlocatable. L0b coords feed
    only the [INFERENCE]-graded M-C8 join, so best-effort is the right cost here."""
    body = [ln.strip() for ln in chunk_body.split("\n") if ln.strip()]
    if not body:
        return (0, 0, cursor)
    first, last = body[0], body[-1]
    start = next((i for i in range(cursor, len(lines)) if lines[i].strip() == first), None)
    if start is None:
        start = next((i for i in range(len(lines)) if lines[i].strip() == first), None)
    if start is None:
        return (0, 0, cursor)
    end = start
    for j in range(start, len(lines)):
        if lines[j].strip() == last:
            end = j
    return (start + 1, end + 1, start)


def _l0b_chunks(source: str, lines: list[str], *,
                max_chars: int, overlap_chars: int) -> list[CodeChunk]:
    out: list[CodeChunk] = []
    cursor = 0
    for c in chunk_text(source, max_chars=max_chars, overlap_chars=overlap_chars):
        ls, le, cursor = _locate_span(c.text, lines, cursor)
        # headerless by construction, so the window IS its own canonical body (D0)
        out.append(CodeChunk(LAYER_CODE_TEXT, "", ls, le, text=c.text, canonical_body=c.text))
    return out


# ── L1: the prose reading — docstrings + comments, note-path chunked ─────────────────────

def _l1_chunks(path: str, n_lines: int, shape: FileShape, *,
               max_chars: int, overlap_chars: int) -> list[CodeChunk]:
    """[banner: correction] Per-item coordinate headers (`# {path}`, `# {path}:{qualname}`,
    `# {path}:{lineno}`) were INTERLEAVED into the prose BEFORE windowing, so window boundaries were
    computed over header-bearing text: a rename that changed the path's length, or a line shift that
    moved a comment's lineno, RECUT every window downstream and re-minted its atoms — stripping at
    hash time alone could not fix that (measured at 45c4a15: renaming every tracked `.py` file still
    minted 2,373 atoms under strip-at-hash-only, essentially ALL of them L1 recuts, vs 3 under this
    pin; a one-line top-of-file insert, 2,114 vs 0). CORRECTED per D0: windows are cut over the
    CANONICAL (header-free) prose, and that window is both the identity input and the embed body,
    prefixed for retrieval by a single `# {path}` line — exactly the L0a shape, one strippable line.
    Per-item linenos are deliberately NOT re-introduced: occupancy coordinates live in memberships
    (bp-152), not in the text. L1 stays slotless (`qualname=''`, R4) — no quiet re-slot (PD-5)."""
    items: list[tuple[int, str]] = []   # (source line, canonical body) in source order — NO header
    if shape.docstring:
        items.append((1, shape.docstring))
    for s in shape.symbols:
        if s.docstring:
            items.append((s.lineno, s.docstring))
    for c in shape.comments:
        body = c.text.lstrip("#").strip() or c.text
        items.append((c.lineno, body))
    if not items:
        return []
    items.sort(key=lambda t: t[0])
    prose = "\n\n".join(block for _, block in items)
    return [CodeChunk(LAYER_CODEDOC, "", 1, n_lines,
                      text=f"# {path}\n{c.text}", canonical_body=c.text)
            for c in chunk_text(prose, max_chars=max_chars, overlap_chars=overlap_chars)]


def derive_code_chunks(path: str, source: str, *,
                       max_chars: int = _DEFAULT_MAX_CHARS,
                       overlap_chars: int = _DEFAULT_OVERLAP_CHARS) -> list[CodeChunk]:
    """The PURE derivation: (path, source) -> the file's L0a + L0b + L1 chunks. Deterministic and
    bit-identically re-derivable from the blob (F-CI2) — parses ONCE with φ_code's `parse_source`
    (the same interpreter, not a second parser). A parse-error file still yields L0b windows and a
    module-shell L0a chunk (it embeds as text even when unparseable)."""
    shape = parse_source(path, "", source)
    lines = source.splitlines()
    return [
        *_l0a_chunks(path, lines, shape, max_chars=max_chars, overlap_chars=overlap_chars),
        *_l0b_chunks(source, lines, max_chars=max_chars, overlap_chars=overlap_chars),
        *_l1_chunks(path, len(lines), shape, max_chars=max_chars, overlap_chars=overlap_chars),
    ]


# ── the structural CODE mint — row assembly with NO provenance parameter (F-CI1) ─────────

def atom_id(chunk: CodeChunk) -> str:
    """The atom's identity (D1): `"{layer}:{content_hash}"` — PATH-FREE and corpus-wide.

    The one place the id shape is spelled, so the vector row and the membership row can never
    disagree about what an atom is. Dropping the path from the id is the whole atom model in one
    character-level change: it promotes `code_rows`' old per-path dedup to corpus-wide dedup, so
    the same body in two files is ONE point with two memberships (PD-1, owner-ruled in). The layer
    stays inside identity because two layers with identical text are different readings, not the
    same idea (the D1 stratum fence, carried as a test invariant)."""
    return f"{chunk.layer}:{chunk.content_hash}"


def code_rows(chunks: Sequence[CodeChunk], vectors: Sequence[list[float]], *,
              current: bool = False) -> list[dict[str, Any]]:
    """Assemble ATOM rows — one per distinct `(layer, content_hash)` (D1). Provenance is HARDCODED
    `CODE`: there is NO parameter, so a caller physically cannot launder code into an authored class
    (F-CI1).

    [banner: correction] The old docstring said `id` is `(source_path, layer, chunk_hash)` —
    "doc+layer-scoped" — and that `digest` is the git blob sha "so group-by-digest yields file =
    source object, its chunks = members". **Both clauses stop being true here.** Under D1 the id is
    `(layer, content_hash)`, corpus-wide; the source object is now the MEMBERSHIP FIBER
    `M(path, blob_sha)` (`code_memberships`, below), and group-by-digest is not the code lane's
    path at all — `VectorStore.all_rows` structurally keeps shed atom rows out of it, because a
    grouping keyed on a column these rows do not have produces one bogus set rather than an error
    (bp-152 Item 3; the note's §3 Q5).

    **The shed, stated exactly.** The occupancy columns — `source_path`, `digest`, `title`,
    `chunk_index`, `qualname`, `line_*` — leave the ROW, not the schema: note rows still carry
    them and no prose-lane consumer changes. (`title` is shed with them because on a code row it
    WAS the path under another name; leaving it would stamp each shared atom with its first-landed
    path — a coordinate that lies for every other occupancy, which is exactly what D0's consequence
    note forbids relying on. Occupancy resolves from memberships, never from the row.)
    **`provenance` STAYS**, and that is load-bearing rather than incidental: the mirror firewall is
    a row PREFILTER — `provenance IN (...)` with `prefilter=True` in `VectorStore.search` — so
    shedding the column would not weaken the firewall, it would REMOVE it, silently and with no
    failing call anywhere.

    **The dedup here is the atom side and ONLY the atom side.** `by_id.setdefault` collapses
    duplicates, which is correct for geometry — two identical bodies are one idea — and WRONG for
    occupancy: two byte-identical L0b windows in one blob are TWO memberships with distinct
    `chunk_index` (the F5 multiset pin). `code_memberships` therefore builds its own list and never
    reuses this dict.

    `current` is the `current_any` reading now (D1): does ANY current membership contain this atom?
    A freshly landed atom defaults to **False** — it has no occupancy yet at insert time, since D8
    puts the vector insert BEFORE the fiber write — and the lander raises it in step 5 for exactly
    the atoms whose current-membership count crossed 0→1."""
    by_id: dict[str, dict[str, Any]] = {}
    for ch, vec in zip(chunks, vectors, strict=True):
        rid = atom_id(ch)
        row: dict[str, Any] = {
            **ATOM_ROW_SHED,                         # occupancy lives in memberships now (D1)
            "id": rid,
            "title": "",
            "provenance": Provenance.CODE.value,     # ← hardcoded; no parameter anywhere above
            "text": ch.text,
            "layer": ch.layer,
            "current": current,
            "vector": vec,
        }
        by_id.setdefault(rid, row)                   # one point per (layer, content) — corpus-wide
    return list(by_id.values())


def code_memberships(path: str, blob_sha: str,
                     chunks: Sequence[CodeChunk]) -> list[Membership]:
    """The version's FIBER: one membership row per chunk, in derivation order (D1/D2 step 3).

    This is the A2 translation point — `CodeChunk.slot_line_*` becomes `Membership.slot_line_*`
    with the name intact, so the "declared extent, not text coverage" reading survives the trip to
    storage instead of being re-lost at the boundary.

    **One row per CHUNK, never per distinct atom.** `chunk_index` is the position in
    `derive_code_chunks`' output, which is a pure deterministic function of `(path, source)`
    (F-CI2), so the key `(path, blob_sha, layer, chunk_index)` is stable and re-derivable — and two
    identical windows in one blob keep both occupancies instead of colliding. Rows land
    `current=False`; currency is not a property of the fiber's construction but of reconciliation
    against the path's HEAD (D2 step 4), which is the only place that decides it."""
    return [
        Membership(
            path=path, blob_sha=blob_sha, layer=ch.layer, chunk_index=idx,
            content_id=atom_id(ch),
            slot=ch.qualname,                       # L0a's symbol; '' for L0b/L1 (R4, no re-slot)
            slot_line_start=ch.slot_line_start, slot_line_end=ch.slot_line_end,
            current=False, tombstoned=False,
        )
        for idx, ch in enumerate(chunks)
    ]


# ── land(): the D2 write path — five steps, and step 4 is the one that must never be skipped ──

@dataclass(frozen=True)
class LandReport:
    """What one `land()` actually did. `atoms_embedded == 0` on a re-land is the reuse claim; the
    CURRENCY numbers are what prove idempotence, because a do-nothing lander also embeds zero."""

    atoms_embedded: int = 0
    atoms_reused: int = 0
    membership_rows: int = 0        # NEW occupancy rows; 0 on a re-land — the fiber already stands
    currency: CurrencyReport = field(default_factory=CurrencyReport)
    current_any_raised: int = 0
    current_any_lowered: int = 0


@dataclass
class CodeLander:
    """`land(path, blob_sha, chunks)` — the D2 write path, in the D8 order.

    Vector inserts FIRST (append-only; an unreferenced atom is dormant geometry, harmless), the
    membership fiber SECOND (one SQLite transaction — the reference truth), currency reconciliation
    and `current_any` maintenance LAST (both re-derivable, so a crash anywhere is repaired by the
    next land or by `repair_current_any`).

    ⚑ **Re-landing is idempotent BECAUSE reconciliation converges, not because the call
    short-circuits.** Step 4 runs even when step 3 wrote nothing. The tempting "the fiber already
    exists, so return" is the C1 bug in its exact original form: on A → B → A the fiber for blob A
    already exists carrying `current=false`, so a short-circuit leaves **B** marked HEAD — silent
    corruption of every default (current-view) read, with nothing raised and nothing logged. The
    repo already learned this once at note grain (`core/stores/versions.py:22-27`)."""

    vectors: VectorStore
    memberships: MembershipStore
    embedder: _Embedder
    embedder_identity: EmbedderIdentity

    def land(self, path: str, blob_sha: str, chunks: Sequence[CodeChunk], *,
             head_blob_sha: str | None = None) -> LandReport:
        """Land one file version. `head_blob_sha` names the path's CURRENT HEAD blob — it defaults
        to the version being landed (the incremental case) and is passed explicitly by a history
        backfill, where the version being landed is usually NOT head."""
        head = blob_sha if head_blob_sha is None else head_blob_sha

        # (1) canonical identity per chunk — D0/bp-151: the hash is over the header-free body, so a
        #     rename mints nothing and the atom survives `git mv`.
        ids = [atom_id(ch) for ch in chunks]

        # (2) insert only the atoms absent from the plane — the embed step; everything else is
        #     reuse by construction. Presence is keyed to (layer, content_hash) AND the embedder
        #     identity: a model change must invalidate every reuse, or two geometries share one ANN
        #     space and no downstream measurement can tell.
        known = self.memberships.known_atoms(ids, self.embedder_identity)
        fresh: dict[str, CodeChunk] = {}
        for ch, cid in zip(chunks, ids, strict=True):
            if cid not in known:
                fresh.setdefault(cid, ch)            # atoms dedup here; memberships never do
        reused = len(set(ids)) - len(fresh)
        if fresh:
            vecs = self.embedder.embed_documents([c.text for c in fresh.values()])
            # current=False: at insert time the atom has no occupancy yet (D8 puts vectors first),
            # so `current_any` is false until step 5 sees it cross 0→1.
            self.vectors.add(code_rows(list(fresh.values()), vecs, current=False))
            self.memberships.record_atoms(
                [(cid, ch.layer) for cid, ch in fresh.items()], self.embedder_identity)

        # The step-5 "before" reading, taken BEFORE the fiber write. The candidate set is the
        # atoms this land could possibly move: the version's own atoms plus everything already
        # occupying this path (reconciliation is path-scoped, so nothing else can cross).
        candidates = set(ids) | self.memberships.atom_ids_of_path(path)
        before = self.memberships.currently_held(candidates)

        # (3) write the fiber; an existing fiber's rows STAND (pure derivation ⇒ fiber equality)
        written = self.memberships.write_fiber(code_memberships(path, blob_sha, chunks))

        # (4) currency reconciliation — NEVER skipped, even when (3) was a no-op (the C1 case)
        currency = self.memberships.reconcile_currency(path, head)

        # (5) maintain `current_any` on exactly the atoms whose current-membership count crossed
        #     0↔1 — `current` is a lance column, so an unconditional flip would rewrite fragments
        #     for every atom of every landing (the §3 physical-maintenance pin).
        after = self.memberships.currently_held(candidates)
        raised = self.vectors.set_current_any(after - before, True)
        lowered = self.vectors.set_current_any(before - after, False)

        return LandReport(atoms_embedded=len(fresh), atoms_reused=reused,
                          membership_rows=written, currency=currency,
                          current_any_raised=raised, current_any_lowered=lowered)

    def reconcile(self, path: str, head_blob_sha: str) -> LandReport:
        """Steps 4–5 alone, for a path whose HEAD fiber already stands.

        This exists so the incremental sync can honor the C1 rule without re-deriving chunks for
        every unchanged file on every pass. "Unchanged blob ⇒ skip the path entirely" is the same
        short-circuit at one level up: after A → B → A the HEAD fiber exists, the file looks
        unchanged, and B is left current forever. Reconciliation is two counting queries per path,
        so convergence costs nothing worth trading for that."""
        candidates = self.memberships.atom_ids_of_path(path)
        before = self.memberships.currently_held(candidates)
        currency = self.memberships.reconcile_currency(path, head_blob_sha)
        after = self.memberships.currently_held(candidates)
        return LandReport(currency=currency,
                          current_any_raised=self.vectors.set_current_any(after - before, True),
                          current_any_lowered=self.vectors.set_current_any(before - after, False))

    def supersede_path(self, path: str) -> LandReport:
        """A vanished file: every fiber of `path` goes `current=false`, nothing is deleted
        (keep-and-link, D2). Expressed as reconciliation against a blob no fiber has, so there is
        ONE currency mechanism rather than a second, subtly different one."""
        return self.reconcile(path, "")


# ── incremental sync + the seed — blob-sha-keyed, unchanged file = zero embeds ───────────

@dataclass
class CodeSyncReport:
    embedded_rows: int = 0          # ATOM rows inserted (D1) — an unchanged/duplicate atom is 0
    changed_files: int = 0
    unchanged_files: int = 0
    deleted_files: int = 0
    superseded_rows: int = 0        # MEMBERSHIP rows flipped current=true→false, RETAINED (D2)
    parse_failures: int = 0         # blobs that failed AST-parse → L0b-only, still embedded (D1)
    membership_rows: int = 0        # new occupancies recorded this pass

    def __str__(self) -> str:
        return (f"embedded_rows={self.embedded_rows} changed={self.changed_files} "
                f"unchanged={self.unchanged_files} deleted={self.deleted_files} "
                f"superseded_rows={self.superseded_rows} parse_failures={self.parse_failures} "
                f"membership_rows={self.membership_rows}")


@dataclass
class CodeCorpusSync:
    """Blob-sha-keyed sync of the tracked `.py` corpus into the vector store. The store's own set of
    CODE `(source_path, digest)` pairs IS the D-fiber state: a file whose blob is already embedded
    costs ZERO embeds. On a changed blob the incremental `sync()` is now **keep-and-link**
    (dn-temporal-code-corpus D2, bp-099 — reverses the §2.7 delete contract): the superseded version
    is RETAINED with `current=false` (never deleted) and the new version lands `current=true`; a
    vanished file's rows likewise flip `current=false` rather than being removed. `backfill()`
    embeds every HISTORICAL ledger version (D1) so the whole code history is a set of nodes. The
    one-time SEED is `sync()` against an empty store. The embedder runs locally (no network, #1)."""

    repo: Path
    store: VectorStore
    embedder: _Embedder
    memberships: MembershipStore
    embedder_identity: EmbedderIdentity
    max_chars: int = _DEFAULT_MAX_CHARS
    overlap_chars: int = _DEFAULT_OVERLAP_CHARS

    @property
    def lander(self) -> CodeLander:
        return CodeLander(vectors=self.store, memberships=self.memberships,
                          embedder=self.embedder, embedder_identity=self.embedder_identity)

    def _land(self, path: str, blob_sha: str, source: str, *,
              head_blob_sha: str | None = None) -> LandReport:
        """Derive → land one file version through the D2 write path."""
        chunks = derive_code_chunks(path, source,
                                    max_chars=self.max_chars, overlap_chars=self.overlap_chars)
        if not chunks:
            return LandReport()
        return self.lander.land(path, blob_sha, chunks, head_blob_sha=head_blob_sha)

    def sync(self) -> CodeSyncReport:
        """[banner: correction] The D-fiber state WAS the store's own set of CODE
        `(source_path, digest)` pairs. Atom rows carry neither column (D1), so the state re-homes
        to the membership store's `(path, blob_sha)` fibers — the same number, a sturdier home
        (the note's §6 re-home (1), applied here; the daemon's incompleteness probe is bp-153's).

        A path whose HEAD fiber already stands is UNCHANGED and re-derives nothing — but it is
        still reconciled. Skipping it outright is the C1 short-circuit one level up: after
        A → B → A the HEAD fiber exists, the file reads as unchanged, and B stays current."""
        report = CodeSyncReport()
        head = list_py_blobs(self.repo, "HEAD")       # [(path, blob_sha)]
        present_fibers = set(self.memberships.fibers())
        present_paths = {p for p, _ in present_fibers}
        lander = self.lander

        changed = [(p, b) for p, b in head if (p, b) not in present_fibers]
        report.changed_files = len(changed)
        report.unchanged_files = len(head) - len(changed)

        deleted = present_paths - {p for p, _ in head}
        for p in sorted(deleted):                # vanished file: keep rows, flip current=false (D2)
            report.superseded_rows += lander.supersede_path(p).currency.superseded
        report.deleted_files = len(deleted)

        for path, blob_sha in head:              # converge EVERY head version (the C1 rule)
            if (path, blob_sha) in present_fibers:
                report.superseded_rows += lander.reconcile(path, blob_sha).currency.superseded

        blobs = read_py_blobs(self.repo, sorted({b for _, b in changed}))
        for path, blob_sha in changed:
            landed = self._land(path, blob_sha, blobs[blob_sha])
            report.embedded_rows += landed.atoms_embedded
            report.membership_rows += landed.membership_rows
            report.superseded_rows += landed.currency.superseded
        return report

    def seed(self) -> CodeSyncReport:
        """The one-time seed run — `sync()` on a store with no code rows embeds every HEAD blob
        (§2.7-2). Scheduler-gated at the call site (BACKGROUND, pinned tier); the memory ceiling
        (#8) is enforced by the loader on each embed call, exactly as for vault_sync."""
        return self.sync()

    def backfill(self, versions: Sequence[tuple[str, str]]) -> CodeSyncReport:
        """Embed the full code HISTORY (dn-temporal-code-corpus D1, bp-099): every distinct ledger
        `(path, blob_sha)` version in `versions` (from `ops.code_lineage.ledger_versions`) becomes a
        semantic node. Idempotent by construction — a `(path, digest)` already in the store is
        skipped at zero embeds (`digest` = blob sha, content-addressed) — so a re-run embeds nothing
        and re-running after the seed only adds the *non-HEAD* versions. Each landed version is
        `current = (blob is that path's HEAD blob)`, so backfilling into an un-seeded store also
        marks HEAD correctly and every superseded version `current=false`. A parse-fail blob still
        embeds (L0b windows + module shell, `derive_code_chunks` degrades — never a hard stop) and
        is counted. Store writes stay on the caller (the supervisor handler), single-writer kept.

        [banner: correction] "Already in the store" is now "already has a FIBER" (D1 — the atom row
        carries no `(source_path, digest)` to test). Idempotence is unchanged in kind and stronger
        in fact: a re-run derives nothing for a version whose fiber stands, and a version whose
        atoms are all already in the plane costs zero embeds even the FIRST time it is landed —
        which is the whole point of the split (D7's 52,755 → 22,502 measured)."""
        report = CodeSyncReport()
        head = dict(list_py_blobs(self.repo, "HEAD"))          # path -> HEAD blob_sha
        present_fibers = set(self.memberships.fibers())
        todo = [(p, b) for (p, b) in dict.fromkeys(versions) if (p, b) not in present_fibers]
        if not todo:
            return report
        blobs = read_py_blobs(self.repo, sorted({b for _, b in todo}))
        for path, blob_sha in todo:
            source = blobs.get(blob_sha)
            if source is None:                                 # blob unreachable (shallow/pruned)
                continue
            if parse_source(path, blob_sha, source).parse_error:
                report.parse_failures += 1
            landed = self._land(path, blob_sha, source,
                                head_blob_sha=head.get(path, blob_sha))
            if landed.membership_rows:
                report.embedded_rows += landed.atoms_embedded
                report.membership_rows += landed.membership_rows
                report.superseded_rows += landed.currency.superseded
                report.changed_files += 1
        return report


def build_code_corpus_sync(config: Any = None, *, repo: Path | None = None,
                           embedder: _Embedder | None = None) -> CodeCorpusSync:
    """Wire a CodeCorpusSync against the configured vector store, membership store, local embedder
    and repo root. The membership store and the embedder identity are REQUIRED fields rather than
    optional ones: a lander without an occupancy record is not a lander, and a reuse decision
    without an embedder identity is the geometry-mixing bug (D2 step 2's pin) waiting to happen."""
    import subprocess

    from core.ingest.embed import build_embedder
    from core.kernel.config import get_config
    from core.stores.memberships import open_membership_store

    cfg = config or get_config()
    root = repo or Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                       check=True, capture_output=True, text=True).stdout.strip())
    return CodeCorpusSync(
        repo=root,
        store=VectorStore(cfg.paths.vector_store, dim=cfg.embedding.dim),
        embedder=embedder or build_embedder(cfg),
        memberships=open_membership_store(cfg),
        embedder_identity=EmbedderIdentity.from_config(cfg),
    )
