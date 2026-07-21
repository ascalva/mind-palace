---
type: finding
id: finding-0145
status: open
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/brainstorms/reference-integrator.md    # the reference sensor's warrant (PD-5)
  - docs/design-notes/agentic-loop.md            # PD-5; G-F (X_cite staleness); §2.8 M-5 (deferred second half)
  - docs/findings/finding-0143.md                # AL-2 recorded 893,991 total, deferred the distinct-pair current view
  - core/stores/reference_edges.py               # the store measured
  - docs/PARKING-LOT.md                           # the `ref-sensor` row (measure-first-then-small-pass)
ftype: discovery
origin_plan: null                                # a standalone measure-first reading (owner-requested)
route: orchestrator                              # direction — sizes PD-5 / the reference-sensor track
resolution: null
---

# The X_cite staleness gap, measured — sizing the reference sensor (PD-5 / G-F)

## What — the reading (live `data/reference_edges.sqlite`, read-only, 2026-07-21)

| metric | value |
|---|---|
| total rows (accumulated) | **943,374** |
| distinct `commit_sha` (readings over time) | **899** |
| distinct `(source_ref, target_ref)` pairs, all-time | 1,719 |
| latest commit (by `created_at`) | `20253d5` (current HEAD — sensor is live) |
| **edges at the latest commit (the CURRENT view)** | **2,199** |
| distinct pairs at latest | 1,681 |
| **corpus→corpus (doc→doc, the F-fiber) at latest** | **624** (634 all-time) |
| rows per commit-snapshot (top-5, uniform) | ~2,190–2,199 |

**Staleness ratio ≈ 429×** (943,374 accumulated ÷ 2,199 current). `[GROUNDED]` — direct sqlite
counts against the live store.

## Why it matters — what the measure DECIDES

- **The gap is pure history accumulation, not extraction debt.** Each commit re-snapshots the FULL
  edge set (~2,199 rows), keyed by `commit_sha`; 899 commits × ~2,199 ≈ 943k. The extractor already
  works and is complete (the current view is real and fresh at HEAD). `[DERIVED]`
- **The current view is small and stable** — 2,199 edges / 1,681 pairs / **624 doc→doc**. This
  confirms G-F's "893,991 rows vs ~hundreds current" (the "hundreds" = the 624 doc→doc F-fiber).
- **So the reference sensor's job is scoped: materialize + serve the latest-commit view (a
  `WHERE commit_sha = HEAD`-shaped current-view projection / index), and optionally prune or
  compact the 899-deep history** — NOT a re-extraction and NOT a new extractor. Exactly the
  parking-lot ruling: *"the extractor EXISTS (code_sensor + note-ingest) — schedule + reconcile,
  don't reinvent."* `[DERIVED]`
- **Consumer cost today:** census / M2 / the `origin(e)` view (bp-088) all filter to the current
  commit per read over a 943k-row table. A materialized current-view (2.2k rows) is ~429× smaller —
  a cheap index/view win. `[INFERENCE]`

## Closes / advances

- **Closes M-5's deferred second half** (`dn-agentic-loop` §2.8 — AL-2/finding-0143 recorded the
  893,991 total but deferred the distinct-pair current view; now computed: 2,199 current / 624 doc→doc).
- **Sizes PD-5** (the reference sensor): a small pass = a current-view projection + a history-prune
  policy. No design-note change (A8); a `/capture` → `/graduate` when the owner prioritizes it.

## Re-entry / next step

The reference-sensor build (PD-5): a small plan for (a) a latest-commit current-view projection on
`reference_edges` (materialized table or view + index), consumed by census / M2 / `origin`; (b) an
optional history-compaction policy (keep last-N commit snapshots, or a tombstone-on-supersede). Its
own `/capture` → `/graduate`; the parent brainstorm (`reference-integrator.md`) owns the design.

## Routing

`direction` → orchestrator. No owner decision required to record; feeds `/triage` and the
reference-sensor track's sizing. Parking-lot `ref-sensor` row can move from "measure the staleness
gap first" to "measured — small pass sized (current-view projection + prune)".
