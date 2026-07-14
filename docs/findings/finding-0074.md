---
type: finding
id: finding-0074
status: resolved
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/build-plans/bp-029/plan.md
  - core/research/curate.py
  - docs/design-notes/external-grounding.md
ftype: spec-fidelity
origin_plan: bp-029
route: builder
resolution: >
  Resolved in-build by delivering the Item-30 mechanism (set_embedded / mark_manifest_embedded /
  ingestion_errors / schema_errors in core/research/curate.py, tested) and recording that real
  seed-card DISTILLED→EMBEDDED flips are a live/curation-time act, not an offline-build one.
---

# Item 30's real seed-card flips are a live/curation-time act — the offline build delivers the mechanism, not the flips

## What

bp-029 Item 30 reads "set `source_ingestion.state: embedded` … on its `manifest.md` — updating a
bp-027 card." Taken literally that flips real seed cards to EMBEDDED during this build. I did NOT,
for a hard invariant reason:

- Flipping a card to `embedded` requires a **real `store_ref` backed by real curated vectors** —
  otherwise it is the exact **dangling claim** the Item-30 falsifier forbids ("a manifest reads
  embedded with no corresponding curated-store vectors").
- Producing those vectors requires **fetching open-access full text**, which is a **Zone-C / edge
  or owner-curation-time** act — the sealed **core must never fetch (Inv 2)**, and this offline
  build has no live fetcher/airlock round-trip. So there are no genuine vectors for any real seed
  card to point at.

The honest deliverable is therefore the **mechanism**, fully built and tested: `set_embedded`
(surgical, comment-preserving block rewrite), `mark_manifest_embedded` (from a persist
`CuratedRecord`), `schema_errors` (v0 schema), and `ingestion_errors` (the dangling-claim guard
that refuses an `embedded` manifest without a store_ref backed by real vectors). The acceptance
test exercises the full 29→30 chain on TEMP manifests and validates every REAL seed manifest
against the v0 schema, confirming none were flipped.

## Why it matters

Not a blocker and not a defect in the code — it is the correct reading of the invariant boundary:
the DISTILLED→EMBEDDED transition is a runtime/curation event, gated on a real fetch, not a
build-time doc edit. Recording it so the plan's Item-30 acceptance is understood as met at the
**mechanism** level, and the real flips are one call away once a live run produces store_refs.

## Re-entry

A live research driver run (bp-028) with a deployed Zone-C fetcher — or an owner curation-time
full-text fetch — produces real curated vectors + a `store_ref` per keeper; `mark_manifest_embedded`
then flips that keeper's card, and `ingestion_errors(fm, curated_store=…)` gates the write so a
dangling claim can never land. (Also gated by the arXiv full-text deferral, finding-0073: the
current open-access tail is Europe PMC.)
