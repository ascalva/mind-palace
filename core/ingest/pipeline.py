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
from core.ingest.logseq import ParsedNote, _decode, iter_vault, parse_note, strip_properties
from core.provenance import Provenance
from core.stores.rawstore import RawStore


def derive_chunks(raw_bytes: bytes, *, max_chars: int = 1200,
                  overlap_chars: int = 150) -> tuple[Chunk, ...]:
    """The chunks a raw blob yields — the ONE authoritative raw→chunks derivation, deterministic
    and reproducible from the immutable raw store alone: decode (the tolerant text view, §8),
    strip Logseq `key::` page-property lines (metadata, NOT prose — bp-036/finding-0077: an `id::`
    uuid and the shared `"id:: "` prefix moved the σ-graph off note CONTENT), then chunk the body.
    `ingest_note` performs exactly this (it chunks `strip_properties(note.text)`, `note.text` being
    `_decode(note.raw_bytes)`), so the retrieval-integrity check (`core.ingest.verify`) re-derives
    the SAME body chunks and a re-embedded row still matches ("derived is regenerable from raw" made
    checkable), and the strip stays consistent across ingest and verify via this one derivation. The
    raw bytes + digest keep the properties; only the derived text drops them."""
    return tuple(chunk_text(strip_properties(_decode(raw_bytes)),
                            max_chars=max_chars, overlap_chars=overlap_chars))


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
    # Store the verbatim ORIGINAL bytes (raw is sacred, §8); chunk the property-stripped body — the
    # same derivation `derive_chunks` uses, so ingest + verify never disagree (bp-036).
    # `provenance` defaults to AUTHORED_SOLO (vault notes); dialogue capture / curated ingest
    # pass AUTHORED_DIALOGUE / CURATED through this same path.
    digest, is_new = raw.add(note.raw_bytes)
    chunks = tuple(chunk_text(strip_properties(note.text),
                              max_chars=max_chars, overlap_chars=overlap_chars))
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
