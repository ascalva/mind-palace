"""Index ingest records into the vector store + provenance-aware semantic search
(BUILD-SPEC §8, §9).

Vectors are derived and regenerable: to re-index after a model/strategy change, rebuild
the vector store from the raw corpus (§8) rather than mutating in place.

Chunk points are keyed by a DOC-SCOPED content address `(source_path, chunk_hash)` (§3/§4,
build plan R1): stable across versions of a note (an unchanged chunk keeps its point) and
distinct across documents (two notes sharing a verbatim chunk keep both points — corroboration,
§7). `index_amendment` uses that to re-embed only the chunks that actually changed.

[banner: extension] dn-vector-membership-store A3 (2026-10-29): the row a reader sees keeps that
doc-scoped id, while the store keeps ONE atom per distinct chunk text for every prose stratum, so a
chunk two documents share is embedded and stored once and corroboration becomes a count of its
holders. `embed_new` is where the saving happens: only texts the store does not hold are embedded.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from core.ingest.embed import Embedder
from core.kernel.clearance import MAINTENANCE_READ, MIRROR_READ, Clearance, Row
from core.kernel.ingest.amend import chunk_point_id, text_hash
from core.kernel.ingest.chunk import Chunk
from core.kernel.ingest.pipeline import IngestRecord
from core.kernel.provenance import Provenance
from core.kernel.stores.sourceset import SourceSet, group_sources
from core.stores.plane import atom_id as plane_atom_id
from core.stores.plane import row_key as plane_row_key
from core.stores.vectorstore import VectorStore


def _chunk_row(record: IngestRecord, chunk: Chunk, vector: list[float] | None) -> dict[str, Any]:
    """Build one vector-store row for a chunk — the SINGLE place the row schema is assembled, so
    `index_records` and `index_amendment` never drift. `id` is the doc-scoped content address
    `(source_path, chunk_hash)`; `digest` stamps the note's CURRENT version. `vector` is None when
    the plane already holds the chunk's atom (A3): the landing reuses it, nothing is embedded."""
    return {
        "id": chunk_point_id(record.source_path, chunk),
        "digest": record.digest,
        "title": record.title,
        "source_path": record.source_path,
        "chunk_index": chunk.index,
        "provenance": record.provenance.value,
        "text": chunk.text,
        # The layer coordinate (dn-code-ingest-pipeline §2.2): a note is 'prose' with empty code
        # fiber coordinates. The code lane assembles its own rows (hardcoded CODE + real coords) —
        # this keeps the ONE shared schema uniform so a note re-ingest lands the new columns.
        "layer": "prose",
        "qualname": "",
        "line_start": 0,
        "line_end": 0,
        "vector": vector,
    }


def embed_new(store: VectorStore, embedder: Embedder,
              texts: Iterable[str]) -> dict[str, list[float]]:
    """Embed each distinct text whose atom the store does not already hold — and only those (A3:
    the embeds the shared plane saves). Returns `{atom id: vector}`; a text whose atom is known
    lands with no vector at all."""
    wanted = {plane_atom_id(t): t for t in texts}
    known = store.known_atoms(list(wanted))
    todo = [(a, t) for a, t in wanted.items() if a not in known]
    if not todo:
        return {}
    vectors = embedder.embed_documents([t for _, t in todo])
    return {a: v for (a, _), v in zip(todo, vectors, strict=True)}


def index_records(records: Iterable[IngestRecord], embedder: Embedder, store: VectorStore) -> int:
    """Embed what the store does not already hold and land every record. Returns rows landed.

    Within a note, chunks dedupe by content (one point per canonical chunk, §3). Across notes and
    strata, an identical chunk is one shared atom (A3): embedded once, landed once per document.

    [banner: correction] Was: "Identical-content notes (same digest) are embedded once" — by
    skipping the second record ENTIRELY, so a second note with the same bytes at another path got
    no rows and could never be found. Embedding is still paid once; every document now lands."""
    staged: list[tuple[IngestRecord, list[Chunk]]] = []
    for r in records:
        if not r.chunks:
            continue
        canonical: dict[str, Chunk] = {}
        for c in r.chunks:
            canonical.setdefault(c.content_hash, c)          # one point per canonical chunk (§3)
        staged.append((r, list(canonical.values())))
    fresh = embed_new(store, embedder, (c.text for _, cs in staged for c in cs))
    return store.add([_chunk_row(r, c, fresh.get(plane_atom_id(c.text)))
                      for r, cs in staged for c in cs])


def index_amendment(record: IngestRecord, existing_rows: Sequence[Mapping[str, Any]],
                    embedder: Embedder, store: VectorStore) -> tuple[int, int]:
    """Re-index one note as a chunk-level amendment (ingest-identity-and-amendment.md §4). Returns
    `(embedded, reused)`: the stable parts of a frequently-edited note never re-embed.

    [banner: extension] A3: on the shared plane, embed only the chunks the plane does not hold and
    land the new version — the old one is SUPERSEDED with an edge and its occupancies kept (the
    owner's "supersession edge … with the new vector reference set"), never deleted; an emptied
    note retires its path. `existing_rows` is not read there. A table not yet migrated keeps the
    pre-A3 replace, reusing `existing_rows`' vectors."""
    canonical: dict[str, Chunk] = {}
    for c in record.chunks:
        canonical.setdefault(c.content_hash, c)          # one point per canonical chunk (§3)
    if store.plane_enabled():
        if not canonical:
            store.delete_source(record.source_path)
            return 0, 0
        fresh = embed_new(store, embedder, (c.text for c in canonical.values()))
        store.add([_chunk_row(record, c, fresh.get(plane_atom_id(c.text)))
                   for c in canonical.values()])
        return len(fresh), len(canonical) - len(fresh)
    vec_by_hash = {text_hash(str(r["text"])): list(r["vector"]) for r in existing_rows}
    to_embed = [c for h, c in canonical.items() if h not in vec_by_hash]
    embedded = dict(zip((c.content_hash for c in to_embed),
                        embedder.embed_documents([c.text for c in to_embed]), strict=True)) \
        if to_embed else {}
    rows = [_chunk_row(record, c, vec_by_hash[h] if h in vec_by_hash else embedded[h])
            for h, c in canonical.items()]
    store.delete_source(record.source_path)              # replace the projection atomically-ish
    store.add(rows)
    return len(to_embed), len(canonical) - len(to_embed)


def _row_new_id(row: Mapping[str, Any]) -> str:
    """The doc-scoped content id a stored row SHOULD have — `(source_path, chunk_hash)`, computed
    from the row's own `source_path` + `text`. The one place the migration and the dry-run agree."""
    return chunk_point_id(str(row["source_path"]),
                          Chunk(int(row.get("chunk_index", 0) or 0), str(row["text"])))


def _note_record_ids(store: VectorStore) -> list[tuple[str, str]]:
    """(id, key) of every note row the migration re-keys: the physical note records of a table
    that predates the plane, and every plane occupancy, superseded ones included."""
    out = [(str(r["id"]), _row_new_id(r))
           for r in store.note_records(["id", "source_path", "chunk_index", "text"])]
    out.extend((o.row_id, plane_row_key(o.source_path, o.atom_id)) for o in
               store.reader(MAINTENANCE_READ).occupancies(include_superseded=True))
    return out


def rekey_preview(store: VectorStore) -> tuple[int, int]:
    """(note rows, how many ids would change) under the doc-scoped re-key: a read that mutates
    nothing, over exactly the rows `rekey_store` writes."""
    ids = _note_record_ids(store)
    return len(ids), sum(1 for i, k in ids if i != k)


def rekey_store(store: VectorStore) -> tuple[int, int]:
    """Re-key every note row to its doc-scoped content id `(source_path, chunk_hash)` IN PLACE: the
    migration off the old `{digest}:{chunk_index}` scheme (build plan Item 1c). Returns (note rows,
    ids changed); a second run changes none.

    [banner: correction] Was: read `all_rows()`, `reset()` the store and add the rows back. That
    read returns neither the shed CODE atoms (D1, bp-152's guard) nor the plane's superseded
    occupancies, and `reset()` drops the table and every relation, so a run deleted every code
    atom, every superseded version and every supersession edge, and gave code records the note
    lane's key, merging two layers' rows of one text (issue #37; `formal/Palace/Plane.lean`'s
    witnesses `rekeyReset_drops_history`, `rekeyReset_merges`). The re-key is SCOPED now (PLN-6,
    `rekey_keeps`): the plane's occupancies take their key in place (`SharedPlane.rekey_rows`,
    one column of one transaction), a table that predates the plane re-keys its note records in
    place (`VectorStore.rekey_records`), and no other row, atom, edge or cache entry is read or
    written. No vector moves, so there is nothing to re-embed; the raw store and the catalog are
    untouched."""
    read, changed = store.rekey_records(_row_new_id)
    plane_rows, plane_changed = store.plane.rekey_rows()
    return read + plane_rows, changed + plane_changed


def semantic_search(query: str, embedder: Embedder, store: VectorStore, *, k: int = 5,
                    clearance: Clearance[Provenance] = MIRROR_READ) -> list[Row[Provenance]]:
    """Search the thought-graph. Defaults to the mirror — the introspective default that keeps
    observed exhaust out of it. A wider read passes a wider clearance, which only an authority can
    mint (A3.4); a free provenance set is no longer a way in."""
    return store.search(embedder.embed_query(query), k=k, clearance=clearance)


def grouped_semantic_search(query: str, embedder: Embedder, store: VectorStore, *, k: int = 5,
                            clearance: Clearance[Provenance] = MIRROR_READ) -> list[SourceSet]:
    """Semantic search returning results grouped by SOURCE OBJECT instead of flat chunks.

    The explicit opt-in to source-grained retrieval: flat `semantic_search` stays the default
    and is untouched (byte-identical), and this is a separate entry point rather than a flag on
    it — the recursive-strata I3 floor-zero posture (the grouped mode adds nothing to the flat
    path). `k` is the flat *chunk* budget; the returned sources are those chunks grouped by
    `SourceId`, so a query hitting two chunks of one note yields one source with two members.
    Source order follows search rank (each source at its best hit; see `group_sources`). Defaults
    to the mirror like `semantic_search`. To expand a hit to its full membership rather than only
    the matched chunks, call `source_set(store, hit.digest, clearance=…)`."""
    hits = semantic_search(query, embedder, store, k=k, clearance=clearance)
    return group_sources(hits)
