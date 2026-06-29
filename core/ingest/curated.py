"""Ingest the system's own white papers + design notes as a `curated` self-knowledge graph
(Track B / B4; nervous-system-and-ambassador.md §4).

The Ambassador can explain its own architecture by reading this graph — "fittingly, the white
papers + design notes ARE the corpus" for self-narration. It is `CURATED`, not authored: it is
the system's design prose, kept in its OWN graph and **never merged into the authored mirror**
(curated ∉ MIRROR_READABLE — the same firewall as book dreaming). The Ambassador reaches it
only via a deliberate, non-default `provenances={CURATED}` query.

Reuses the parametrized ingest pipeline (provenance=CURATED) into the existing multi-provenance
VectorStore — no new store. Only PROSE docs are ingested (Constitution, Conventions, the docs/
tree). Config and anything that could hold a secret are never sourced here (there are none in
the .md tree; the note's own caveat: explain the design, never expose live keys).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.attestation import Attestor
from core.ingest.embed import Embedder
from core.ingest.index import index_records
from core.ingest.logseq import parse_note
from core.ingest.pipeline import ingest_note
from core.provenance import Provenance
from core.stores.catalog import VaultCatalog
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore


def curated_sources(repo_root: Path) -> list[Path]:
    """The self-knowledge corpus: the Constitution, the Conventions, and the whole docs/ tree
    (white papers + design notes). Prose only — never config or secrets."""
    sources = [repo_root / "CONSTITUTION.md", repo_root / "CONVENTIONS.md"]
    docs = repo_root / "docs"
    if docs.is_dir():
        sources += sorted(docs.rglob("*.md"))
    return [p for p in sources if p.is_file()]


@dataclass
class CuratedReport:
    ingested: int = 0
    chunks: int = 0

    def __str__(self) -> str:
        return f"curated ingested={self.ingested} chunks={self.chunks}"


def ingest_curated(paths: list[Path], raw: RawStore, store: VectorStore, embedder: Embedder,
                   catalog: VaultCatalog, *, repo_root: Path,
                   attestor: Attestor | None = None) -> CuratedReport:
    """Ingest each doc as CURATED. Titles are repo-relative (e.g. `docs/design-notes/...`).
    Idempotent: delete-then-index per digest, so re-running after a doc edit re-embeds cleanly."""
    report = CuratedReport()
    for p in paths:
        parsed = parse_note(p, repo_root)
        record = ingest_note(parsed, raw, provenance=Provenance.CURATED)
        store.delete(digest=record.digest)
        added = index_records([record], embedder, store)
        catalog.record(record.source_path, record.digest, record.title,
                       provenance=Provenance.CURATED)
        if attestor is not None:
            attestor.emit(agent_role="ambassador", action="ingest_curated",
                          input_hashes=[record.digest], output_hashes=[record.digest])
        report.ingested += 1
        report.chunks += added
    return report


def build_and_ingest_curated(config: object | None = None) -> CuratedReport:
    """Wire + run the curated ingest against the configured stores + embedder (needs the live
    embedder — owner-run, see scripts/ingest_self_knowledge.py)."""
    from config.loader import REPO_ROOT, get_config
    from core.attestation import build_attestor
    from core.ingest.embed import build_embedder

    cfg = config or get_config()
    return ingest_curated(
        curated_sources(REPO_ROOT),
        raw=RawStore(cfg.paths.raw_store),
        store=VectorStore(cfg.paths.vector_store, dim=cfg.embedding.dim),
        embedder=build_embedder(cfg),
        catalog=VaultCatalog(cfg.paths.vault_catalog),
        repo_root=REPO_ROOT,
        attestor=build_attestor(cfg),
    )
