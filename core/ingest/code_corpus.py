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

The three are joined by line-range coordinates carried ON the rows (the §2.4 L2a fiber — no edge
rows). `digest` = the git blob sha (git is already the content-addressed raw store for code), so
group-by-digest gives file = source object, chunks = members, UNCHANGED. Derivation is a PURE
function of (path, source): re-running yields bit-identical chunks (F-CI2 re-derivability). All
embedding is LOCAL (the core embedder) — zero network egress (non-negotiable #1).

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
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol

from core.kernel.ingest.chunk import chunk_text
from core.kernel.provenance import Provenance
from core.stores.vectorstore import (
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
    `(qualname, line_start, line_end)` are the §2.4 backpointers carried on the row.

    TWO renderings, deliberately different (D0): `text` is the EMBED rendering and KEEPS its
    coordinate header (retrieval context, R7); `canonical_body` is the IDENTITY input and is
    header-free. Every chunker passes the canonical body from the site that already holds it — it
    is NEVER re-derived by re-parsing `text`, so a body line that legitimately begins with `#` can
    never be mistaken for a coordinate header (a wrong strip is silent identity corruption)."""

    layer: str
    qualname: str
    line_start: int
    line_end: int
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
    coords: dict[str, tuple[str, int, int]] = {}   # qualname -> (header, line_start, line_end)
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
    """Best-effort (line_start, line_end, next_cursor) for an L0b window — located by matching the
    window's first/last non-blank line back into the source (windows overlap by design, so the
    cursor only hints, never hard-bounds). (0, 0) when unlocatable. L0b coords feed only the
    [INFERENCE]-graded M-C8 join, so best-effort is the right cost here."""
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

def code_rows(path: str, blob_sha: str, chunks: Sequence[CodeChunk],
              vectors: Sequence[list[float]], *, current: bool = True) -> list[dict[str, Any]]:
    """Assemble vector-store rows for one file version. Provenance is HARDCODED `CODE` — there is
    NO parameter, so a caller physically cannot launder code into an authored class (F-CI1). `id`
    is `(source_path, layer, chunk_hash)` — doc+layer-scoped and content-addressed, so an unchanged
    chunk keeps its point across versions and two layers with identical text stay distinct. `digest`
    is the git blob sha, so group-by-digest yields file = source object, its chunks = members.
    As of D0 the hash is CANONICAL-BODY-scoped (header-free), so a renamed file's chunks keep their
    point too — the id SHAPE still carries the path; the path-free `(layer, hash)` atom id is D1's
    change (bp-152), not this one.

    `current` (dn-temporal-code-corpus D2, bp-099) marks whether this version is the path's HEAD
    projection: the sync lands the new version `current=True` and flips the superseded one to False
    (keep-and-link — never a delete); a history backfill lands each version `current = (blob is
    HEAD's blob)`. `current` is a KEEP-AND-LINK flag, not a provenance parameter (F-CI1 intact)."""
    by_id: dict[str, dict[str, Any]] = {}
    for idx, (ch, vec) in enumerate(zip(chunks, vectors, strict=True)):
        rid = f"{path}:{ch.layer}:{ch.content_hash}"
        row: dict[str, Any] = {
            "id": rid,
            "digest": blob_sha,
            "title": path,
            "source_path": path,
            "chunk_index": idx,
            "provenance": Provenance.CODE.value,     # ← hardcoded; no parameter anywhere above
            "text": ch.text,
            "layer": ch.layer,
            "qualname": ch.qualname,
            "line_start": ch.line_start,
            "line_end": ch.line_end,
            "current": current,
            "vector": vec,
        }
        by_id.setdefault(rid, row)                   # one point per (path, layer, content)
    return list(by_id.values())


# ── incremental sync + the seed — blob-sha-keyed, unchanged file = zero embeds ───────────

@dataclass
class CodeSyncReport:
    embedded_rows: int = 0
    changed_files: int = 0
    unchanged_files: int = 0
    deleted_files: int = 0
    superseded_rows: int = 0        # rows flipped current=true→false, RETAINED (keep-and-link, D2)
    parse_failures: int = 0         # blobs that failed AST-parse → L0b-only, still embedded (D1)

    def __str__(self) -> str:
        return (f"embedded_rows={self.embedded_rows} changed={self.changed_files} "
                f"unchanged={self.unchanged_files} deleted={self.deleted_files} "
                f"superseded_rows={self.superseded_rows} parse_failures={self.parse_failures}")


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
    max_chars: int = _DEFAULT_MAX_CHARS
    overlap_chars: int = _DEFAULT_OVERLAP_CHARS

    def _embed_and_land(self, path: str, blob_sha: str, source: str, *,
                        current: bool = True) -> int:
        """Derive → embed → land one file version's rows. Keep-and-link (D2): it NEVER deletes the
        path's prior projection — the caller flips the superseded version to `current=false` first
        (`store.supersede_source`). `current` marks whether this version is HEAD's projection."""
        chunks = derive_code_chunks(path, source,
                                    max_chars=self.max_chars, overlap_chars=self.overlap_chars)
        if not chunks:
            return 0
        vectors = self.embedder.embed_documents([c.text for c in chunks])
        rows = code_rows(path, blob_sha, chunks, vectors, current=current)
        return self.store.add(rows)

    def sync(self) -> CodeSyncReport:
        report = CodeSyncReport()
        head = list_py_blobs(self.repo, "HEAD")       # [(path, blob_sha)]
        code_now = self.store.all_rows(provenances={Provenance.CODE})
        present_pd = {(str(r["source_path"]), str(r["digest"])) for r in code_now}
        present_paths = {str(r["source_path"]) for r in code_now}

        changed = [(p, b) for p, b in head if (p, b) not in present_pd]
        report.changed_files = len(changed)
        report.unchanged_files = len(head) - len(changed)

        deleted = present_paths - {p for p, _ in head}
        for p in deleted:                        # vanished file: keep rows, flip current=false (D2)
            report.superseded_rows += self.store.supersede_source(p)
        report.deleted_files = len(deleted)

        blobs = read_py_blobs(self.repo, sorted({b for _, b in changed}))
        for path, blob_sha in changed:
            report.superseded_rows += self.store.supersede_source(path)  # keep the old version (D2)
            report.embedded_rows += self._embed_and_land(path, blob_sha, blobs[blob_sha],
                                                         current=True)
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
        is counted. Store writes stay on the caller (the supervisor handler), single-writer kept."""
        report = CodeSyncReport()
        head = dict(list_py_blobs(self.repo, "HEAD"))          # path -> HEAD blob_sha
        code_now = self.store.all_rows(provenances={Provenance.CODE})
        present_pd = {(str(r["source_path"]), str(r["digest"])) for r in code_now}
        todo = [(p, b) for (p, b) in dict.fromkeys(versions) if (p, b) not in present_pd]
        if not todo:
            return report
        blobs = read_py_blobs(self.repo, sorted({b for _, b in todo}))
        for path, blob_sha in todo:
            source = blobs.get(blob_sha)
            if source is None:                                 # blob unreachable (shallow/pruned)
                continue
            if parse_source(path, blob_sha, source).parse_error:
                report.parse_failures += 1
            landed = self._embed_and_land(path, blob_sha, source,
                                          current=head.get(path) == blob_sha)
            if landed:
                report.embedded_rows += landed
                report.changed_files += 1
        return report


def build_code_corpus_sync(config: Any = None, *, repo: Path | None = None,
                           embedder: _Embedder | None = None) -> CodeCorpusSync:
    """Wire a CodeCorpusSync against the configured vector store + local embedder + repo root."""
    import subprocess

    from core.ingest.embed import build_embedder
    from core.kernel.config import get_config

    cfg = config or get_config()
    root = repo or Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                       check=True, capture_output=True, text=True).stdout.strip())
    return CodeCorpusSync(
        repo=root,
        store=VectorStore(cfg.paths.vector_store, dim=cfg.embedding.dim),
        embedder=embedder or build_embedder(cfg),
    )
