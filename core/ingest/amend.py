# ── Family 2 boundary (regenerable derivation) · the versioned-amendment mechanism ──
# OBJECT:    the chunk-level diff that makes an amendment a re-projection, not a destroy-replace
#            (ingest-identity-and-amendment.md §4; build plan Item 1c, PURE logic only).
# INVARIANT: chunk identity is (stable-doc-id, chunk-content-hash) — SCOPED to the document, so an
#            unchanged chunk of the SAME doc is retained across versions, while a verbatim chunk
#            shared by DISTINCT docs stays two points (corroboration, §7 — build plan R1).
# ENFORCED:  pure set arithmetic on content hashes; no store, no embed, no live-data touch here —
#            this is the mechanism the sync path will call once wired (gated: re-index + snapshot).
"""Versioned amendment as a chunk-level diff (ingest-identity-and-amendment.md §4).

Today an amendment is destroy-and-replace: a changed note gets a new whole-note digest, so EVERY
chunk re-embeds and the old rows are dropped (core/ingest/sync.py:88-101; proven by
tests/integration/test_index_keying.py). §4 wants the opposite — unchanged chunks keep their
points, only changed/new chunks embed, removed chunks are marked superseded — so the stable parts
of a frequently-edited note never churn and provenance is *enhanced*, not destroyed.

This module is the PURE core of that: given the old and new chunk sets of ONE document, compute
what to retain / embed / supersede, keyed by chunk-content-hash SCOPED to the document id. It does
not read or write any store and does not embed — those are the wiring (gated behind a re-index and
an owner-ratified §4 go, build plan PD5). Family 2: derived + regenerable, no network.

The scoping is load-bearing (build plan R1, resolving the §3-vs-§7 tension): identity is
(doc_id, chunk_hash), NOT a bare global chunk-hash. Two DISTINCT documents that happen to share a
verbatim paragraph keep BOTH points — independent provenance agreeing is corroboration (§7), never
coalesced. Only re-occurrences of a chunk WITHIN one document's version chain coalesce.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.ingest.chunk import Chunk


def chunk_point_id(doc_id: str, chunk: Chunk) -> str:
    """The document-scoped, content-addressed identity of a chunk point: (doc_id, chunk_hash).

    Stable across versions of the SAME document (an unchanged chunk keeps its id) and distinct
    across documents (shared verbatim text stays two points — §7). This REPLACES the current
    `f"{note_digest}:{chunk_index}"` key (core/ingest/index.py:33), whose note-digest prefix is
    exactly why an amendment re-keys every chunk. `doc_id` is a stable document identity (the
    catalog `source_path`, or a minted doc-id — never the whole-note content-hash, §4)."""
    return f"{doc_id}:{chunk.content_hash}"


@dataclass(frozen=True)
class AmendmentPlan:
    """The re-projection an amendment implies, as sets of chunk-content-hashes for ONE document.

    `retained` — in both versions (same hash): keep the existing point, do NOT re-embed.
    `added`    — new this version: embed a new point.
    `removed`  — gone this version: mark the point superseded (kept as provenance, never deleted).
    """

    retained: frozenset[str]
    added: frozenset[str]
    removed: frozenset[str]

    @property
    def is_noop(self) -> bool:
        """No content changed — nothing to embed or supersede (an idempotent re-ingest, e.g. a
        touch or a reorder-without-edit)."""
        return not self.added and not self.removed


def plan_amendment(old: tuple[Chunk, ...] | list[Chunk],
                   new: tuple[Chunk, ...] | list[Chunk]) -> AmendmentPlan:
    """Diff one document's old vs new chunk sets by content hash. Pure and order-insensitive:
    identity is the chunk's content, so a moved-but-unchanged chunk is `retained`, not churned —
    the property the current index-position key cannot provide."""
    old_h = {c.content_hash for c in old}
    new_h = {c.content_hash for c in new}
    return AmendmentPlan(
        retained=frozenset(old_h & new_h),
        added=frozenset(new_h - old_h),
        removed=frozenset(old_h - new_h),
    )
