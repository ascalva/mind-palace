---
type: finding
id: finding-0036
status: resolved
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/build-plans/bp-013/plan.md
  - docs/design-notes/code-observation-projection.md
  - docs/build-plans/bp-011/inventory.json
ftype: question
origin_plan: bp-013
route: builder
resolution: >
  Resolved in-session (spec-fidelity class): Item 7 mints BOTH directions within the
  same attested projection pass. Annotated in the bp-013 journal; the orchestrator can
  reverse by deleting CodeSensor._corpus_reference_edges + its call (one seam).
---

# bp-013 Item 7 under-specifies whether corpus→code edges are minted at projection time

## What

Plan §7 Item 7's objective reads "the sensor's projection pass populates
`references_out` ... and mints the corresponding edges." `references_out` is a field on
`CodeObservation` (code-side rows), so a literal reading mints only the code→corpus
direction. But bp-011's validated-pattern list — which the same sentence pins as the
extraction set — includes `corpus_to_code/path-mention` at rank 2: 100% measured
precision and the highest-volume pattern (211 of 364 raw edges). No other item in the
plan extracts it, and the ratified note §2.5 names "a design note naming
`core/recursion.py`" as a canonical Lane-1 fact.

## Why it matters

A literal reading silently drops ~58% of the validated edge inventory — including the
direction finding-0021's corroboration arbitration actually used — while the plan's §1
objective ("deterministic cross-references (validated patterns from bp-011's V4
inventory) are extracted at projection time") and §3 Q2 (which types BOTH endpoints,
direction-agnostic) read as both-directions.

## Resolution taken (builder, spec-fidelity)

Implemented both directions inside the same `project_observations`-attested pass
(`ops/code_sensor.py`): code→corpus from each observation's `references_out`;
corpus→code by scanning the commit's OWN tree state (`git show sha:path`, deterministic
per §2.2) over the bp-011 corpus surfaces (`docs/design-notes|findings|brainstorms`)
with the probe's `path-mention` regex verbatim. No new attestation kind; below-bar
patterns (wikilink, symbol-mention) mint nothing (test-pinned). The Q2 endpoint typing
covers both directions unchanged.

## Re-entry condition

None needed (not parked). If the orchestrator prefers the literal single-direction
reading at diff scrutiny, the corpus→code half is one method + one call to delete;
the store schema is direction-typed either way.
