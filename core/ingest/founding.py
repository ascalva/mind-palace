"""Founding-corpus ingest — authoring the initial condition (founding-corpus.md; build plan Item 3).

The founding corpus is NOT model training and NOT steady-state ingest (founding-corpus.md §1–§2): it
is a hand-selected batch of the owner's musings, authored across a long past, injected at once as
the graph's initial condition. It must be a **dated, supersession-linked sequence** (§2.1 —
reconstruct the partial order of thought, not a bag stamped "today"), and it MUST share the
steady-state ingest path or the provenance model fractures at the origin (§4 / Q3).

So this driver is a thin batch over the ONE pipeline — `ingest_note` (provenance AUTHORED_SOLO) →
`index_records` → `VaultCatalog.record`, exactly the `curated.py` shape, never a bespoke writer. Two
founding-specific disciplines it enforces:

  * **Dated, not a bag (§2.1).** Every item carries a reconstructed date, recorded as a `date::`
    property IN the note, so the raw content-addressed blob carries it (permanent provenance) and
    `parse_text` lifts it into `properties['date']`. An undated item is refused — the timestamp lie
    (collapsing years into simultaneous peers) is exactly what founding must avoid. (The temporal
    *layer* reading these dates is dormant today; the dates are recorded now regardless.)
  * **Supersession-linked (§2.1).** When a later musing revises an earlier one, it is recorded as an
    OWNER-DECLARED **authored-historical supersession** (`core/stores/authored_supersession.py`;
    8f / PD11) — a K₀↔K₀ RELATION between two authored documents, so the active projection shows the
    current musing and the earlier lives on in history. It is NOT a claim-`supersede` (no warrant,
    no derived alternative) and NOT a note-version `supersedes` (two documents, not one doc's
    versions). Founding is an owner entry point, so it mints an `OwnerDeclaration`; the store is
    owner-declared
    only and refuses any machine caller at its boundary (the-edge-model.md §4a).

Provenance is AUTHORED_SOLO — the owner's writing, the mirror's ground truth. The founding corpus
is deliberately biased-coherent, so it CANNOT be the Track-L control corpus (§2.3): the control
is a separate, non-curated CURATED-graph act. This driver writes only AUTHORED_SOLO and never the
control — the two acts stay mechanically distinct. Ingest, not fine-tuning; the weights never move.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.attestation import Attestor
from core.ingest.embed import Embedder
from core.ingest.index import index_records
from core.ingest.logseq import parse_text
from core.ingest.pipeline import ingest_note
from core.provenance import Provenance
from core.stores.authored_supersession import AuthoredSupersessionStore, owner_declaration
from core.stores.catalog import VaultCatalog
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore


class UndatedFoundingItem(ValueError):
    """A founding item with no reconstructed date — refused (§2.1: a dated sequence, not a bag
    stamped 'today'; the timestamp lie is exactly what founding must avoid)."""


class ForwardSupersession(ValueError):
    """A founding item supersedes one not yet ingested — refused: the sequence is ordered (a musing
    can only revise an EARLIER one), so a forward reference is a manifest error."""


@dataclass(frozen=True)
class FoundingItem:
    """One dated musing in the founding sequence. `body` is the text; `date` its reconstructed
    original date (a `date::` property in the note); `supersedes` the `source_path` of an
    EARLIER item this one revises, or None."""

    source_path: str
    title: str
    body: str
    date: str
    supersedes: str | None = None


@dataclass
class FoundingReport:
    ingested: int = 0
    chunks: int = 0
    superseded: int = 0

    def __str__(self) -> str:
        return (f"founding ingested={self.ingested} chunks={self.chunks} "
                f"superseded={self.superseded}")


def _note_text(item: FoundingItem) -> str:
    """The note as ingested: the reconstructed date as a `date::` property, then the musing — so the
    date lands in the raw content-addressed blob (permanent) and `parse_text` recovers it."""
    return f"date:: {item.date}\n\n{item.body}"


def ingest_founding(items: Iterable[FoundingItem], raw: RawStore, store: VectorStore,
                    embedder: Embedder, catalog: VaultCatalog, *,
                    supersession_store: AuthoredSupersessionStore | None = None,
                    attestor: Attestor | None = None) -> FoundingReport:
    """Ingest the founding sequence through the STEADY-STATE path (no bespoke writer): each item
    rides `ingest_note` (AUTHORED_SOLO) → `index_records` → `VaultCatalog.record`, exactly like
    curated/dialogue ingest. Dated (undated refused) and supersession-linked (recorded as an
    OWNER-DECLARED authored-historical supersession when a later musing revises an earlier — 8f).
    Ingest, not fine-tuning — weights never move (§1); AUTHORED_SOLO, never the control (§2.3)."""
    report = FoundingReport()
    digest_by_source: dict[str, str] = {}
    for item in items:
        if not item.date.strip():
            raise UndatedFoundingItem(f"founding item {item.source_path!r} has no date (§2.1)")
        text = _note_text(item)
        parsed = parse_text(text, source_path=item.source_path, title=item.title,
                            raw_bytes=text.encode("utf-8"))
        record = ingest_note(parsed, raw, provenance=Provenance.AUTHORED_SOLO)
        store.delete(digest=record.digest)                 # idempotent re-index (the curated idiom)
        report.chunks += index_records([record], embedder, store)
        catalog.record(record.source_path, record.digest, record.title,
                       provenance=Provenance.AUTHORED_SOLO)
        if attestor is not None:
            attestor.emit(agent_role="ambassador", action="ingest_founding",
                          input_hashes=[record.digest], output_hashes=[record.digest])
        digest_by_source[item.source_path] = record.digest
        report.ingested += 1

        if item.supersedes is not None:
            prior = digest_by_source.get(item.supersedes)
            if prior is None:
                raise ForwardSupersession(
                    f"founding item {item.source_path!r} supersedes {item.supersedes!r}, which is "
                    "not an earlier ingested item"
                )
            if supersession_store is not None:
                # Owner-declared: the founding manifest IS the owner's hand, so mint an
                # OwnerDeclaration. The store verifies it at its boundary (a machine caller is
                # refused there), keeping the authored-historical edge owner-only by construction.
                supersession_store.record(
                    prior, record.digest, declaration=owner_declaration(),
                    note=f"superseded in the founding sequence by {item.title!r}")
                report.superseded += 1
    return report


def build_and_ingest_founding(items: Iterable[FoundingItem],
                              config: object | None = None) -> FoundingReport:
    """Wire + run the founding ingest against the configured stores + embedder (owner-run; needs the
    live embedder — see scripts/ingest_founding.py)."""
    from config.loader import get_config
    from core.attestation import build_attestor
    from core.ingest.embed import build_embedder
    from core.stores.authored_supersession import open_authored_supersession_store

    cfg = config or get_config()
    return ingest_founding(
        items,
        raw=RawStore(cfg.paths.raw_store),
        store=VectorStore(cfg.paths.vector_store, dim=cfg.embedding.dim),
        embedder=build_embedder(cfg),
        catalog=VaultCatalog(cfg.paths.vault_catalog),
        supersession_store=open_authored_supersession_store(cfg),
        attestor=build_attestor(cfg),
    )
