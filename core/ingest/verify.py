# ── Family 2 boundary (regenerable derivation) · symbols in docs/NOTATION.md ──
# OBJECT:    a retrieved chunk row verified against its content-addressed source H(raw) ∈ Σ —
#            "derived is regenerable from raw" (§8) turned from promise into a checkable predicate.
# INVARIANT: a row is trusted iff its `text` is one of the chunks re-derived from the raw blob it
#            claims (by `digest`); anything else is not fed to a model (fail-closed).
# ENFORCED:  deterministic re-derivation (derive_chunks) == the ingest derivation, so a legitimate
#            row always verifies and only tampered/unreproducible text is dropped (no false drop).
"""Retrieval-time content integrity (BUILD-SPEC §8, closes prompt-integrity audit G9.5).

The raw store is the immutable, content-addressed source of truth (`H(raw) = digest`); the vector
store's chunk rows are a *derived*, mutable layer. Retrieval reads the chunk `text` field at face
value, so a mutated LanceDB row would reach the prompt while the read attestation logged the clean
digest — a false-fidelity record, and an injection vector once lower-trust provenances become
retrievable. This verifies each retrieved row against its raw source before it can be cited: the
`text` must be one of the chunks re-derived from the raw blob it claims. The check is exact — the
same `raw bytes → _decode → chunk_text` derivation the ingest pipeline used (`derive_chunks`), so a
legitimate row always passes and only text that does not reproduce from the sacred layer is dropped.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from core.ingest.pipeline import derive_chunks
from core.stores.rawstore import RawStore


@dataclass(frozen=True)
class IntegrityDrop:
    """A row that could not be verified against the raw store and was withheld from the prompt."""

    digest: str
    chunk_index: int
    reason: str        # "raw-missing" | "text-not-in-raw"


def verify_rows_against_raw(
    rows: Iterable[dict[str, Any]], raw: RawStore, *,
    max_chars: int = 1200, overlap_chars: int = 150,
) -> tuple[list[dict[str, Any]], list[IntegrityDrop]]:
    """Split `rows` into (verified, dropped).

    A row is verified iff its `text` is one of the chunks re-derived from the raw blob identified by
    its `digest` — the exact ingest derivation (`derive_chunks`). The raw blob is fetched and
    re-chunked once per digest (a query hitting several chunks of one note pays one raw read).
    A missing raw blob ("raw-missing") or a `text` that does not reproduce ("text-not-in-raw") is
    dropped fail-closed — unverified content never reaches a model. Verified rows keep input order
    (so a distance-ranked result stays ranked); `dropped` carries each withheld row's reason.
    """
    ordered = list(rows)
    # Re-derive the legitimate chunk set once per source (by content-address). None = raw absent.
    expected: dict[str, set[str] | None] = {}
    for digest in {r.get("digest", "") for r in ordered}:
        try:
            blob = raw.get(digest)
        except OSError:  # FileNotFoundError and friends — the sacred source is gone
            expected[digest] = None
            continue
        expected[digest] = {
            c.text for c in derive_chunks(blob, max_chars=max_chars, overlap_chars=overlap_chars)
        }

    verified: list[dict[str, Any]] = []
    dropped: list[IntegrityDrop] = []
    for r in ordered:
        digest = r.get("digest", "")
        legit = expected.get(digest)
        if legit is None:
            dropped.append(IntegrityDrop(digest, int(r.get("chunk_index", -1)), "raw-missing"))
        elif r.get("text", "") in legit:
            verified.append(r)
        else:
            dropped.append(IntegrityDrop(digest, int(r.get("chunk_index", -1)), "text-not-in-raw"))
    return verified, dropped
