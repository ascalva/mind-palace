"""Index ingest records into the vector store + provenance-aware semantic search
(BUILD-SPEC §8, §9).

Vectors are derived and regenerable: to re-index after a model/strategy change, rebuild
the vector store from the raw corpus (§8) rather than mutating in place.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.ingest.embed import Embedder
from core.ingest.pipeline import IngestRecord
from core.provenance import MIRROR_READABLE, Provenance
from core.stores.sourceset import SourceSet, group_sources
from core.stores.vectorstore import VectorStore


def index_records(records: Iterable[IngestRecord], embedder: Embedder, store: VectorStore) -> int:
    """Embed each record's chunks and add them to the vector store. Returns rows added.
    Identical-content notes (same digest) are embedded once."""
    rows = []
    seen_digests: set[str] = set()
    for r in records:
        if not r.chunks or r.digest in seen_digests:
            continue
        seen_digests.add(r.digest)
        vectors = embedder.embed_documents([c.text for c in r.chunks])
        for chunk, vector in zip(r.chunks, vectors, strict=True):
            rows.append({
                "id": f"{r.digest}:{chunk.index}",
                "digest": r.digest,
                "title": r.title,
                "source_path": r.source_path,
                "chunk_index": chunk.index,
                "provenance": r.provenance.value,
                "text": chunk.text,
                "vector": vector,
            })
    return store.add(rows)


def semantic_search(query: str, embedder: Embedder, store: VectorStore, *, k: int = 5,
                    provenances: Iterable[Provenance] | None = MIRROR_READABLE) -> list[dict]:
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
