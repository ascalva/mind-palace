"""Persist ranked open-access keepers into the curated store (bp-029 Item 29, §2.4/§2.6).

The flip the whole arc turns on: `rank_literature` produced a reading list that was **ranked and
DISCARDED** (transient — there was no curated home). This module gives the keepers a home: for a
keeper whose **open-access full text** clears the licence gate, `chunk_text → embed_documents →
curated_store.add(...)` with `provenance="curated"`. The result is the pattern-finding substrate
the design note calls EMBEDDED (§2.2).

Three invariants are load-bearing and all hold STRUCTURALLY here:

  * **Inv 2 / core never fetches.** This step reads the full text ALREADY on the `Paper` (fetched
    by the Zone-C fetcher, carried back through the airlock `results/`); it imports no network and
    performs no fetch. The full text is an input, never something core reaches for.
  * **Never-pollute-the-mirror.** Rows are written with `provenance="curated"` — a class excluded
    from `MIRROR_READABLE` — into the SEPARATE curated store the caller passes
    (`open_curated_store`), never the mirror. `source_path` is a `reference:` marker, never a note.
  * **The licence gate (default-DENY, §11).** A keeper is embedded ONLY if `open_access` is set AND
    it carries non-empty `full_text`. Belt-and-suspenders: the explicit OA flag (set at the fetch
    boundary, Item 27), not mere text-presence, is what admits a paper. Everything else is SKIPPED
    and stays DISTILLED-only — the plan's Item-29 falsifier.

`store_ref` is the content-address of the full text (sha256), the manifest's join to `data/`
(Item 30). The step returns data (curated records), takes no action — Inv 4.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from core.ingest.chunk import chunk_text
from core.ingest.embed import Embedder
from core.provenance import Provenance
from core.research.criteria import Paper
from core.research.rank import RankedPaper
from core.stores.vectorstore import VectorStore


@dataclass(frozen=True)
class CuratedRecord:
    """One persisted keeper — the handle Item 30 writes into its `reference_material/` manifest."""

    paper_source: str        # "europepmc" | "arxiv" — the manifest `venue`
    paper_id: str            # the source's canonical id
    title: str
    store_ref: str           # sha256 of the full text; the manifest join to the curated store
    source_path: str         # the curated marker the chunks are stored under
    n_chunks: int


def _passes_licence_gate(paper: Paper) -> bool:
    """Default-DENY: embed ONLY clearly open-access full text (§11). The explicit `open_access`
    flag AND non-empty `full_text` are BOTH required — presence of text alone is not a licence."""
    return bool(paper.open_access and paper.full_text and paper.full_text.strip())


def persist_keepers(
    ranked: list[RankedPaper],
    embedder: Embedder,
    curated_store: VectorStore,
    *,
    retrieved: str | None = None,
) -> list[CuratedRecord]:
    """Embed every open-access keeper's full text into the curated store; skip the rest.

    Pure over its inputs + the passed store: reads `RankedPaper`s (full text already fetched),
    never touches the network. Keepers without open-access full text are left DISTILLED-only.
    `retrieved` is accepted for symmetry with the manifest write (Item 30) and is not used here."""
    records: list[CuratedRecord] = []
    for r in ranked:
        paper = r.paper
        if not _passes_licence_gate(paper):
            continue  # DISTILLED-only — never embed on an unclear licence basis
        full_text = paper.full_text
        assert full_text is not None  # narrowed by the gate; for the type checker
        chunks = chunk_text(full_text)
        if not chunks:
            continue
        store_ref = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
        source_path = f"reference:{paper.source}:{paper.id}"  # curated marker, never a mirror path
        vectors = embedder.embed_documents([c.text for c in chunks])
        rows = [
            {
                "id": f"{source_path}:{c.content_hash}",
                "digest": store_ref,               # the curated analog of a source's raw identity
                "title": paper.title,
                "source_path": source_path,
                "chunk_index": c.index,
                "provenance": Provenance.CURATED.value,
                "text": c.text,
                "vector": vec,
            }
            for c, vec in zip(chunks, vectors, strict=True)
        ]
        curated_store.add(rows)
        records.append(CuratedRecord(
            paper_source=paper.source, paper_id=paper.id, title=paper.title,
            store_ref=store_ref, source_path=source_path, n_chunks=len(chunks),
        ))
    return records
