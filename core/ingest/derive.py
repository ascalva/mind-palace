"""The derived field: an item's vector plane rows, derived from the raw store after the item has
landed (dn-two-phase-ingestion D1, D3; ING-19 to ING-21).

The embedder produces one relation of the store, semantic similarity. Every other relation and
the lexical index are functions of the bytes and the graph alone, so an item is complete without
its vector: under `[embedding] lazy = true` the writer lands the raw object, the lexical units, the
version, the attestation and, last, the key (ING-7), and writes no plane row. The vector is a
derived field of the item's bytes and the embedder's identity, and this module is the drain that
writes it. `pending` lists the active catalog entries whose current version the plane does not
hold; `drain` reads each one's bytes back by digest, chunks them as the landing chunked them,
embeds the atoms the plane lacks in batches of the configured size, and lands the rows through the
plane, whose current occupancy of `(path, digest)` is the drain's own idempotence key, written in
the plane's transaction after the atoms (`SharedPlane.land`, PLN-4). Run again, the drain finds
nothing pending and embeds nothing; interrupted anywhere, the next run lands what the interrupted
one would have, since an atom inserted before the interruption is found held and not embedded
again (ING-5) and an occupancy not yet written leaves the item pending (ING-20). A reader that
needs a vector the drain has not written finds the item pending and says so (ING-21).

Re-embedding after a model change is the same drain over a reset plane: the plane records the
embedder's identity, model, document template and dimension (`core/stores/plane.py::Fingerprint`),
refuses another, and `reset` forgets it, after which every active item is pending and the drain
derives it under the new identity. The catalog, the raw store, the versions, the edges and the
lexical index are untouched by both.

The batch policy follows the measurement of docs/experiments/corpus-measurements-2026-11-07.md:
one stream of 64 chunks a request saturates the embedder at 26 chunks a second, and each further
stream buys at most 15% while every other caller's latency grows to the length of the queue in
front of it; so `streams` is 1 unless the instance's configuration raises it.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from typing import Any

from core.ingest.embed import embed_fitting
from core.ingest.index import _chunk_row
from core.kernel.clearance import CURATED_READ, MIRROR_READ, OBSERVED_READ, Clearance
from core.kernel.ingest.chunk import Chunk
from core.kernel.ingest.logseq import _decode, parse_text
from core.kernel.ingest.pipeline import IngestRecord, ingest_note
from core.kernel.provenance import Provenance
from core.stores.catalog import CatalogEntry
from core.stores.plane import atom_id as plane_atom_id

# The chunker's budget for prose, the writer's own defaults (`Writer.max_chars`).
CHUNK_MAX_CHARS = 1200
CHUNK_OVERLAP_CHARS = 150
EMBED_JOB = "embed"      # the queue kind, and the job a script starts (`run "embed"`)

# The clearance under which the plane is asked whether it holds a label's rows: the writer's
# UNCHANGED check and the drain's pending check ask the same question.
HOLDS: dict[str, Clearance[Provenance]] = {
    Provenance.AUTHORED_SOLO.value: MIRROR_READ,
    Provenance.AUTHORED_DIALOGUE.value: MIRROR_READ,
    Provenance.OBSERVED.value: OBSERVED_READ,
    Provenance.CURATED.value: CURATED_READ,
}


@dataclass(frozen=True)
class DrainReport:
    """What one drain did: the items whose rows it landed and their chunks, the atoms it embedded
    and the ones the plane held already, the items with no chunk (complete, nothing to derive),
    the items it left pending under a limit, and its wall time."""

    items: int = 0
    chunks: int = 0
    embedded: int = 0
    reused: int = 0
    empty: int = 0
    left: int = 0
    seconds: float = 0.0
    cut: int = 0             # texts the embedder took only a prefix of (`embed_fitting`)

    def __str__(self) -> str:
        return (f"{self.items} item(s), {self.chunks} chunk(s), {self.embedded} embedded, "
                f"{self.reused} reused, {self.empty} empty, {self.left} left pending, "
                f"{self.cut} cut, {self.seconds:.1f}s")


def pending(catalog: Any, plane: Any, *, lexical: Any | None = None,
            classes: Iterable[Provenance] | None = None) -> list[CatalogEntry]:
    """The active catalog entries whose current version the plane does not hold current, of
    `classes` (every plane class when None), in the catalog's order. With the lexical index given,
    an entry it records as landed with no unit (an item with no text) is complete with nothing to
    derive and is not pending; an entry it has no record of (landed before the index was opened)
    stays pending, and the drain finds out by chunking it. The vector's absence is read from the
    plane itself, never from a flag: a drain that died before its plane transaction leaves the
    item pending, and one that died after it does not (ING-20). The plane is read once a clearance
    (`current_versions`) where it can be, so the set is one pass over the catalog however large
    the corpus."""
    wanted = {p.value for p in classes} if classes is not None else set(HOLDS)
    empty = lexical.empty_versions() if lexical is not None else set()
    bulk = getattr(plane, "current_versions", None)
    held: dict[int, set[tuple[str, str]]] = {}
    out = []
    for e in catalog.active_entries():
        label = str(e.provenance)
        clearance = HOLDS.get(label)
        if clearance is None or label not in wanted:
            continue
        key = (e.source_path, e.digest)
        if key in empty:
            continue
        if callable(bulk):
            have = held.get(id(clearance))
            if have is None:
                have = held[id(clearance)] = bulk(clearance=clearance)
            if key in have:
                continue
        elif plane.holds_current(e.source_path, e.digest, clearance=clearance):
            continue
        out.append(e)
    return out


def record_of(raw: Any, entry: CatalogEntry, *, max_chars: int = CHUNK_MAX_CHARS,
              overlap_chars: int = CHUNK_OVERLAP_CHARS) -> IngestRecord:
    """An entry's chunks, derived from its bytes exactly as the landing derived them
    (`Writer.store`): the same parse, the same chunker, so the drain's rows are the rows a
    synchronous landing would have written."""
    data = raw.get(entry.digest)
    parsed = parse_text(_decode(data), source_path=entry.source_path, title=entry.title,
                        raw_bytes=data)
    return ingest_note(parsed, raw, provenance=Provenance(str(entry.provenance)),
                       max_chars=max_chars, overlap_chars=overlap_chars)


def canonical_chunks(record: IngestRecord) -> list[Chunk]:
    """One chunk per distinct text within a record (`index_amendment`'s canonical form)."""
    seen: dict[str, Chunk] = {}
    for c in record.chunks:
        seen.setdefault(c.content_hash, c)
    return list(seen.values())


def embed_missing(plane: Any, embedder: Any, texts: Sequence[str], *, batch: int = 64,
                  streams: int = 1) -> tuple[dict[str, list[float]], int, int]:
    """Embed the distinct texts whose atoms the plane does not hold, `batch` a request and
    `streams` requests in flight at once, a text the server refuses for its length cut to fit
    (`embed_fitting`, which the embedder applies to every request; it is applied again here for an
    embedder object that does not). Returns `{atom id: vector}`, how many atoms the plane held
    already, and how many texts were cut, by either."""
    wanted = {plane_atom_id(t): t for t in dict.fromkeys(texts)}
    known = set(plane.known_atoms(list(wanted)))
    todo = [(a, t) for a, t in wanted.items() if a not in known]
    if not todo:
        return {}, len(known), 0
    groups = [todo[i:i + batch] for i in range(0, len(todo), batch)]

    before = getattr(embedder, "cut", None)

    def one(group: list[tuple[str, str]]) -> tuple[list[tuple[str, list[float]]], int]:
        vectors, cuts = embed_fitting(embedder.embed_documents, [t for _, t in group])
        return [(a, v) for (a, _), v in zip(group, vectors, strict=True)], len(cuts)

    out: dict[str, list[float]] = {}
    cut = 0
    if streams > 1 and len(groups) > 1:
        with ThreadPoolExecutor(max_workers=streams) as pool:
            for result, n in pool.map(one, groups):
                out.update(result)
                cut += n
    else:
        for group in groups:
            result, n = one(group)
            out.update(result)
            cut += n
    if isinstance(before, int):
        cut += int(getattr(embedder, "cut", before)) - before      # the embedder's own cuts
    return out, len(known), cut


def drain(stores: Any, *, batch: int = 64, streams: int = 1, max_items: int | None = None,
          max_chars: int = CHUNK_MAX_CHARS, overlap_chars: int = CHUNK_OVERLAP_CHARS,
          landed: Callable[[Sequence[str]], None] | None = None,
          clock: Callable[[], float] = time.monotonic) -> DrainReport:
    """Derive the plane rows of every pending item (at most `max_items`), in groups of about
    `batch × streams` chunks: each group's atoms the plane lacks are embedded, then the group's
    rows land in one plane transaction, so a long drain commits as it goes and a reader sees each
    group's items leave the pending set together. `landed` is told each group's paths once their
    rows are current, for a caller that measures the lag between landing and vector. Idempotent:
    a second drain finds nothing pending and embeds nothing (ING-20)."""
    start = clock()
    entries = pending(stores.catalog, stores.plane, lexical=stores.lexical)
    left = max(0, len(entries) - max_items) if max_items is not None else 0
    if max_items is not None:
        entries = entries[:max_items]
    report = derive_entries(stores, entries, batch=batch, streams=streams, max_chars=max_chars,
                            overlap_chars=overlap_chars, landed=landed, clock=clock)
    return replace(report, left=left, seconds=clock() - start)


def derive_entries(stores: Any, entries: Iterable[CatalogEntry], *, batch: int = 64,
                   streams: int = 1, max_chars: int = CHUNK_MAX_CHARS,
                   overlap_chars: int = CHUNK_OVERLAP_CHARS,
                   landed: Callable[[Sequence[str]], None] | None = None,
                   clock: Callable[[], float] = time.monotonic) -> DrainReport:
    """Derive the plane rows of the given entries, as `drain` derives the pending ones: in groups
    of about `batch × streams` chunks, each group's missing atoms embedded and its rows landed in
    one plane transaction. The caller picks the entries (the corpus runner's backfill takes them
    round robin over its sources); an entry whose rows are current already lands its occupancy
    again, which the plane's landing reconciles to nothing, and one with no chunk is counted
    empty."""
    start = clock()
    items = chunks = embedded = reused = empty = cut = 0
    group: list[tuple[IngestRecord, list[Chunk]]] = []
    size = 0
    target = max(1, batch * max(1, streams))

    def flush() -> None:
        nonlocal items, chunks, embedded, reused, cut, group, size
        if not group:
            return
        texts = [c.text for _, cs in group for c in cs]
        fresh, held, n_cut = embed_missing(stores.plane, stores.embedder, texts, batch=batch,
                                           streams=streams)
        rows = [_chunk_row(r, c, fresh.get(plane_atom_id(c.text))) for r, cs in group for c in cs]
        stores.plane.add(rows)                                    # the key: the occupancy, last
        items += len(group)
        chunks += len(rows)
        embedded += len(fresh)
        reused += held
        cut += n_cut
        if landed is not None:
            landed([r.source_path for r, _ in group])
        group, size = [], 0

    for e in entries:
        record = record_of(stores.raw, e, max_chars=max_chars, overlap_chars=overlap_chars)
        cs = canonical_chunks(record)
        if not cs:
            empty += 1
            continue
        group.append((record, cs))
        size += len(cs)
        if size >= target:
            flush()
    flush()
    return DrainReport(items=items, chunks=chunks, embedded=embedded, reused=reused, empty=empty,
                       seconds=clock() - start, cut=cut)


# ── the lexical index's own backfill ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LexicalReport:
    """What one lexical backfill did: the items whose units it landed, the units, the items with
    no unit (recorded, complete), the items it left under a limit, and its wall time."""

    items: int = 0
    units: int = 0
    empty: int = 0
    left: int = 0
    seconds: float = 0.0

    def __str__(self) -> str:
        return (f"{self.items} item(s), {self.units} unit(s), {self.empty} empty, "
                f"{self.left} left, {self.seconds:.1f}s")


def lexical_missing(catalog: Any, lexical: Any, *,
                    classes: Iterable[Provenance] | None = None) -> list[CatalogEntry]:
    """The active entries of the plane's classes (of `classes` when given) whose current version
    the lexical index has no record of: items landed before the index was opened, by an earlier
    writer or while the instance embedded synchronously."""
    wanted = {p.value for p in classes} if classes is not None else set(HOLDS)
    have = lexical.landed_versions()
    return [e for e in catalog.active_entries()
            if str(e.provenance) in wanted and (e.source_path, e.digest) not in have]


def derive_lexical(stores: Any, *, max_items: int | None = None, group: int = 500,
                   max_chars: int = CHUNK_MAX_CHARS, overlap_chars: int = CHUNK_OVERLAP_CHARS,
                   clock: Callable[[], float] = time.monotonic) -> LexicalReport:
    """Land the lexical units of every active item the index has no record of (at most
    `max_items`), read back from the raw store and chunked as the landing chunked them, `group`
    items a transaction. The index is derived and regenerable, as the vectors are, and this is its
    drain: run again, it finds nothing missing and writes nothing. It writes no key, no label and
    no plane row."""
    start = clock()
    lexical = stores.lexical
    if lexical is None:
        return LexicalReport()
    entries = lexical_missing(stores.catalog, lexical)
    left = max(0, len(entries) - max_items) if max_items is not None else 0
    if max_items is not None:
        entries = entries[:max_items]
    items = units = empty = 0
    todo: list[tuple[str, str, str, str, Sequence[Chunk]]] = []
    for e in entries:
        record = record_of(stores.raw, e, max_chars=max_chars, overlap_chars=overlap_chars)
        todo.append((e.source_path, e.digest, str(e.provenance), e.title, record.chunks))
        items += 1
        units += len({c.index for c in record.chunks})
        empty += not record.chunks
        if len(todo) >= group:
            lexical.land_many(todo)
            todo = []
    if todo:
        lexical.land_many(todo)
    return LexicalReport(items=items, units=units, empty=empty, left=left,
                         seconds=clock() - start)
