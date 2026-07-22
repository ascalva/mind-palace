---
type: finding
id: finding-0154
status: open
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/findings/finding-0145.md                      # the reference-sensor sizing (this EXPANDS its scope)
  - docs/brainstorms/reference-integrator.md           # the reference-sensor track's home brainstorm
  - docs/design-notes/code-ingest-pipeline.md          # CI-3 (L2b) does EXTRACTION, not bookkeeping
  - core/librarian.py                                  # the async-agent analogy the owner drew
  - docs/findings/finding-0153.md                      # this track is a deskcheck-queue item (built vs done)
ftype: design
route: orchestrator
resolution: null
---

# The reference track is a BOOKKEEPER agent, not a current-view pass — async, librarian-like, owns F-edge consistency across all sources incl. external research

## Owner reframing (2026-07-21)

Q4 asked whether F-edges are maintained. The honest answer surfaced a bigger gap than
finding-0145 sized. The owner reframed the reference "sensor" as a **reference bookkeeper
agent** — async, "kind of like the librarian" — whose job is to keep **all** reference edges
consistent across the entire corpus, continuously, not just extract them once at ingestion.

## What is missing today (verified 2026-07-21)

1. **No deferred resolution.** `code_sensor` extracts references at a commit; a reference whose
   target does not resolve *then* is dropped, never retried when the target later appears. So
   the graph is only as consistent as each single-commit extraction.
2. **External references are unhandled entirely.** The extractors match in-tree targets only
   (`docs/…md`; CI-3 adds `dn-slug`/`finding-id`/`§`). When the **book** is ingested (curated
   prose) and cites a **research article** (arXiv/DOI/title), that citation becomes inert text —
   no edge, no resolution, no verification. Same for any code→research or doc→research citation.
   (This pairs with the book's "cite only VERIFIED research" rule — [[book-narrative-philosophy]]:
   the bookkeeper is where that verification/consistency would live.)
3. **No continuous reconciliation.** Minting fires per new commit; nothing maintains a
   consistent current view (finding-0145: 950k accumulated vs 2,199 current) or re-resolves the
   corpus as it evolves. There is **no agent that owns "the reference graph is consistent."**

## The vision — a reference bookkeeper (design content for the Fable pass)

An async agent (the sensor/librarian species — model-light or model-free where possible) that:
- **owns F-edge consistency** across code, docs, book, brainstorms, and external sources;
- **resolves deferred** — re-checks unresolved references as targets appear/change/are renamed;
- **handles external citations** — research articles/DOIs/arXiv as a distinct endpoint kind
  (resolve/verify against a bibliography or the external-grounding gate; recorded, not guessed);
- **maintains the current view** — the finding-0145 materialize/serve/prune half;
- stays within the reference store's balance-math isolation (edges never reach `A_signed`).

It is the librarian's sibling: where the Librarian (φ_text) owns embedding/retrieval quality,
the bookkeeper owns *reference* quality and consistency.

## Disposition

This **supersedes finding-0145's "small pass" sizing** — the reference track is a bookkeeper
agent, not a current-view projection. It joins the AFTER-builds Fable design queue (with the
integrator, finding-0151, and the deskcheck workflow, finding-0153). Recorded in the deskcheck
queue §A (reference sensor row, scope expanded) and §C (design pending).

## Routing

`design` → orchestrator. A Fable design pass (capture → note → ratify → graduate); the home
brainstorm is `reference-integrator.md`. External-reference handling likely wants its own
endpoint-kind design (the reference store's v2 symmetric schema can carry it — a new `KINDS`
member beyond `code`/`corpus`).
