"""Run a full ingest of the configured vault into the real stores (BUILD-SPEC §8, §9).

Rebuild semantics: the raw store is append-only and content-addressed (immutable, dedup);
the vector store is rebuilt from scratch each run, because vectors are a derived layer
regenerable from raw. This is the entry the scheduler (Phase 3) will drive as a job.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.ingest.embed import build_embedder
from core.ingest.index import index_records
from core.kernel.config import Config, get_config
from core.kernel.ingest.pipeline import ingest_vault
from core.kernel.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore


@dataclass(frozen=True)
class IngestSummary:
    notes: int
    new_raw: int          # notes whose content was new to the raw store (dedup signal)
    chunks_indexed: int
    vector_rows: int


def run_ingest(config: Config | None = None, *, rebuild: bool = True) -> IngestSummary:
    cfg = config or get_config()
    raw = RawStore(cfg.paths.raw_store)
    store = VectorStore(cfg.paths.vector_store, dim=cfg.embedding.dim)
    if rebuild:
        store.reset()
    embedder = build_embedder(cfg)
    records = ingest_vault(cfg.ingestion.vault.path, raw, pattern=cfg.ingestion.vault.pattern)
    added = index_records(records, embedder, store)
    return IngestSummary(
        notes=len(records),
        new_raw=sum(1 for r in records if r.is_new),
        chunks_indexed=added,
        vector_rows=store.count(),
    )
