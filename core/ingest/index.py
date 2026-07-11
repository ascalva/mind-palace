"""Index ingest records into the vector store + provenance-aware semantic search
(BUILD-SPEC §8, §9).

Vectors are derived and regenerable: to re-index after a model/strategy change, rebuild
the vector store from the raw corpus (§8) rather than mutating in place.

Chunk points are keyed by a DOC-SCOPED content address `(source_path, chunk_hash)` (§3/§4,
build plan R1): stable across versions of a note (an unchanged chunk keeps its point) and
distinct across documents (two notes sharing a verbatim chunk keep both points — corroboration,
§7). `index_amendment` uses that to re-embed only the chunks that actually changed.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from core.ingest.amend import chunk_point_id, text_hash
from core.ingest.chunk import Chunk
from core.ingest.embed import Embedder
from core.ingest.pipeline import IngestRecord
from core.provenance import MIRROR_READABLE, Provenance
from core.stores.sourceset import SourceSet, group_sources
from core.stores.vectorstore import VectorStore


def _chunk_row(record: IngestRecord, chunk: Chunk, vector: list[float]) -> dict[str, Any]:
    """Build one vector-store row for a chunk — the SINGLE place the row schema is assembled, so
    `index_records` and `index_amendment` never drift. `id` is the doc-scoped content address
    `(source_path, chunk_hash)`; `digest` stamps the note's CURRENT version."""
    return {
        "id": chunk_point_id(record.source_path, chunk),
        "digest": record.digest,
        "title": record.title,
        "source_path": record.source_path,
        "chunk_index": chunk.index,
        "provenance": record.provenance.value,
        "text": chunk.text,
        "vector": vector,
    }


def index_records(records: Iterable[IngestRecord], embedder: Embedder, store: VectorStore) -> int:
    """Embed each record's chunks and add them to the vector store. Returns rows added.
    Identical-content notes (same digest) are embedded once; within a note, chunks are
    deduplicated by content hash — one point per canonical chunk (§3)."""
    rows: list[dict[str, Any]] = []
    seen_digests: set[str] = set()
    for r in records:
        if not r.chunks or r.digest in seen_digests:
            continue
        seen_digests.add(r.digest)
        vectors = embedder.embed_documents([c.text for c in r.chunks])
        by_hash: dict[str, dict[str, Any]] = {}
        for chunk, vector in zip(r.chunks, vectors, strict=True):
            by_hash.setdefault(chunk.content_hash, _chunk_row(r, chunk, vector))
        rows.extend(by_hash.values())
    return store.add(rows)


def index_amendment(record: IngestRecord, existing_rows: list[dict[str, Any]], embedder: Embedder,
                    store: VectorStore) -> tuple[int, int]:
    """Re-index one note as a chunk-level amendment (ingest-identity-and-amendment.md §4).

    Reuse the vector of any chunk whose content is unchanged from the note's current projection
    (`existing_rows`) — NO re-embed — embed only genuinely new chunks, dedup this version's chunks
    by content, and replace the note's projection under its stable `source_path`. Returns
    `(embedded, reused)`. The stable parts of a frequently-edited note therefore never re-embed and
    keep a stable point id; only changed/new chunks cost an embedding call."""
    vec_by_hash = {text_hash(r["text"]): r["vector"] for r in existing_rows}
    canonical: dict[str, Chunk] = {}
    for c in record.chunks:
        canonical.setdefault(c.content_hash, c)          # one point per canonical chunk (§3)
    to_embed = [c for h, c in canonical.items() if h not in vec_by_hash]
    fresh = dict(zip((c.content_hash for c in to_embed),
                     embedder.embed_documents([c.text for c in to_embed]), strict=True)) \
        if to_embed else {}
    rows = [_chunk_row(record, c, vec_by_hash[h] if h in vec_by_hash else fresh[h])
            for h, c in canonical.items()]
    store.delete_source(record.source_path)              # replace the projection atomically-ish
    store.add(rows)
    return len(to_embed), len(canonical) - len(to_embed)


def _row_new_id(row: dict[str, Any]) -> str:
    """The doc-scoped content id a stored row SHOULD have — `(source_path, chunk_hash)`, computed
    from the row's own `source_path` + `text`. The one place the migration and the dry-run agree."""
    return chunk_point_id(row["source_path"], Chunk(int(row.get("chunk_index", 0)), row["text"]))


def rekey_preview(store: VectorStore) -> tuple[int, int]:
    """(total rows, count whose id would change) under the doc-scoped re-key — a read that mutates
    nothing. The dry-run half of the Item-1c migration."""
    rows = store.all_rows()
    return len(rows), sum(1 for r in rows if r["id"] != _row_new_id(r))


def rekey_store(store: VectorStore) -> tuple[int, int]:
    """Re-key every stored row to its doc-scoped content id `(source_path, chunk_hash)` IN PLACE,
    preserving vectors (NO re-embed) — the migration off the old `{digest}:{chunk_index}` scheme
    (build plan Item 1c). Identical chunks within a source coalesce to one point (§3). Idempotent:
    a row already under the new key re-keys to itself, so re-running is a no-op. Returns
    (rows_read, points_written); the raw store and catalog are untouched (this is a derived-layer
    re-key, not a re-ingest — so it needs no embedder and cannot be defeated by catalog change-
    detection the way a reset + `rescan()` would be). Regenerable from raw regardless (§8)."""
    rows = store.all_rows()
    by_new_id: dict[str, dict[str, Any]] = {}
    for r in rows:
        r["id"] = _row_new_id(r)
        by_new_id[r["id"]] = r                 # last wins — coalesce identical chunks (§3)
    store.reset()
    return len(rows), store.add(list(by_new_id.values()))


def semantic_search(query: str, embedder: Embedder, store: VectorStore, *, k: int = 5,
                    provenances: Iterable[Provenance] | None = MIRROR_READABLE,
                    ) -> list[dict[str, Any]]:
    """Search the thought-graph. Defaults to MIRROR_READABLE (AUTHORED only) — the
    introspective default that keeps observed exhaust out of the mirror. Pass
    provenances=None for the assistant tier to search across all classes."""
    return store.search(embedder.embed_query(query), k=k, provenances=provenances)


def grouped_semantic_search(query: str, embedder: Embedder, store: VectorStore, *, k: int = 5,
                            provenances: Iterable[Provenance] | None = MIRROR_READABLE
                            ) -> list[SourceSet]:
    """Semantic search returning results grouped by SOURCE OBJECT instead of flat chunks.

    The explicit opt-in to source-grained retrieval: flat `semantic_search` stays the default
    and is untouched (byte-identical), and this is a separate entry point rather than a flag on
    it — the recursive-strata I3 floor-zero posture (the grouped mode adds nothing to the flat
    path). `k` is the flat *chunk* budget; the returned sources are those chunks grouped by
    digest, so a query hitting two chunks of one note yields one source with two members. Source
    order follows search rank (each source at its best hit; see `group_sources`). Defaults to
    MIRROR_READABLE like `semantic_search`. To expand a hit to its full membership rather than
    only the matched chunks, call `source_set(store, hit.digest)`."""
    hits = semantic_search(query, embedder, store, k=k, provenances=provenances)
    return group_sources(hits)
