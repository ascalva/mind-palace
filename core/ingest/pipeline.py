"""Ingest pipeline: vault -> raw store (dedup) -> chunks (BUILD-SPEC §8, §9).

The deterministic write path. Embedding + LanceDB indexing consume `IngestRecord`.

`ingest_note` is provenance-PARAMETRIC (default `AUTHORED_SOLO`, the mirror's ground truth):
vault notes are solo-authored, but the same chunk/embed path is reused — never a bespoke
writer — for the Ambassador's `AUTHORED_DIALOGUE` capture and the `CURATED` self-knowledge
ingest, which pass their own provenance through this one pipeline (the §1 spectrum split).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.ingest.chunk import Chunk, chunk_text
from core.ingest.logseq import ParsedNote, iter_vault, parse_note
from core.provenance import Provenance
from core.stores.rawstore import RawStore


@dataclass(frozen=True)
class IngestRecord:
    digest: str               # content hash of the raw note (identity in the raw store)
    source_path: str
    title: str
    provenance: Provenance
    tags: frozenset[str]
    links: frozenset[str]
    chunks: tuple[Chunk, ...]
    is_new: bool              # False => raw content already present (deduped)


def ingest_note(note: ParsedNote, raw: RawStore, *,
                provenance: Provenance = Provenance.AUTHORED_SOLO,
                max_chars: int = 1200, overlap_chars: int = 150) -> IngestRecord:
    # Store the verbatim ORIGINAL bytes (raw is sacred, §8); chunk the decoded text view.
    # `provenance` defaults to AUTHORED_SOLO (vault notes); dialogue capture / curated ingest
    # pass AUTHORED_DIALOGUE / CURATED through this same path.
    digest, is_new = raw.add(note.raw_bytes)
    chunks = tuple(chunk_text(note.text, max_chars=max_chars, overlap_chars=overlap_chars))
    return IngestRecord(
        digest=digest,
        source_path=note.source_path,
        title=note.title,
        provenance=provenance,
        tags=note.tags,
        links=note.links,
        chunks=chunks,
        is_new=is_new,
    )


def ingest_vault(vault: Path, raw: RawStore, *, pattern: str = "**/*.md",
                 max_chars: int = 1200, overlap_chars: int = 150) -> list[IngestRecord]:
    return [
        ingest_note(parse_note(path, vault), raw, max_chars=max_chars, overlap_chars=overlap_chars)
        for path in iter_vault(vault, pattern=pattern)
    ]
