"""The curated literature vector store (dn-external-grounding §2.2/§2.4).

A SECOND `VectorStore` instance, physically separate from the authored-mirror `vector_store`,
holding the embedded **open-access full text** of curated references (the EMBED tail, bp-029).
It reuses the proven LanceDB `VectorStore` unchanged — same schema, same embedder/dimension —
at a DISTINCT path (`cfg.paths.curated_store`, default `data/research_curated.lance`).

Two invariants are load-bearing and both hold STRUCTURALLY here, not by convention:

  * **Never pollute the mirror.** Curated rows carry `provenance="curated"` — a class that is
    deliberately excluded from `MIRROR_READABLE` (`core/provenance.py`), so a mirror/dreaming
    read (`provenances=MIRROR_READABLE`) cannot surface curated content. And the store is a
    *separate file* from the mirror, so objective-about-the-world text never lands in
    subjective-about-owner space even by accident.
  * **Inv 11 (the corpus never transits a third party; full text never enters git).** The path
    lives under `data/` (gitignored) with a `*.lance/` suffix (also gitignored) — the full
    source text is never committed and never egresses; the sealed core reasons over it offline.

This module is deliberately thin: it does NOT edit or subclass `VectorStore` (if the base store
needed a change, that is a `spec-defect` finding, not an edit here — bp-029 §5). It is only the
factory that aims the proven store at the curated path.
"""

from __future__ import annotations

from config.loader import Config
from core.stores.vectorstore import VectorStore


def open_curated_store(config: Config | None = None) -> VectorStore:
    """Open the curated-literature store at `cfg.paths.curated_store` (a separate LanceDB).

    Mirrors `open_vector_store` but for the curated path; the embedding dimension is shared
    (the same local embedder embeds both corpora — §8 derived layer)."""
    from config.loader import get_config

    cfg = config or get_config()
    return VectorStore(path=cfg.paths.curated_store, dim=cfg.embedding.dim)
