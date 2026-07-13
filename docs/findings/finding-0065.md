---
type: finding
id: finding-0065
status: open
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/build-plans/bp-026/plan.md
  - ops/code_sensor.py
  - docs/findings/finding-0059.md
ftype: spec-defect
origin_plan: bp-026
route: orchestrator
resolution: null
---

# bp-026's corpus→corpus scan excludes build-plans (§6c said `docs/**`; implemented as `_CORPUS_DIRS`)

## What

bp-026 §6(c) pins the doc→doc extractor to scan "each `docs/**/*.md`". The landed
`_corpus_to_corpus_edges` (`ops/code_sensor.py:441`) instead scans
`_git(... "ls-tree" ... "--", *_CORPUS_DIRS)` where `_CORPUS_DIRS = ("docs/design-notes",
"docs/findings", "docs/brainstorms")` — bp-011's *authored-corpus* surface. And
`_RE_NOTE_CITATION` (used for both inline targets and the front-matter target filter) matches
only those three dirs. So **build-plans (`docs/build-plans/**`) are excluded as BOTH source
and target**: a plan's `design_ref: docs/design-notes/…` never mints an edge, and no edge
ever targets a build-plan.

Confirmed against the live migrated store: `references_to(docs/design-notes/self-sensing.md)`
returns citers from brainstorms/notes/findings but **none of bp-018/019/020** (which carry
`design_ref: self-sensing.md`); bp-026/plan.md — present at `e5b5d3c` with a `design_ref` to
`core-query-protocol.md` — has **0** outgoing edges. The builder's grep-oracle passed because
it only sampled notes/findings docs (`finding-0059`, `core-query-protocol.md`, `finding-0062`)
— it never tested a build-plan source, so the gap was invisible to the acceptance test.

## Why it matters

The plan-cites-note relationship is exactly finding-0059's motivating pain (a design note's
stale count cited by build **plans** bp-019/bp-020). With build-plans excluded, `references_to`
misses the single most operationally-relevant citing surface for that use case. The schema
migration and the extraction that DID land are correct; the scope is narrower than §6(c) pinned.

This is also **design-shaped**, not purely a bug: is the corpus→corpus citation graph over the
*authored corpus* (notes/findings/brainstorms — the "thoughts", the mirror's reasoning surface)
or over *all docs* (including the mechanical build-plan layer)? bp-011 deliberately scoped the
corpus→code surface to authored dirs; whether doc→doc should widen to build-plans is a genuine
ruling, not an obvious fix.

## Re-entry condition

The next /triage rules on the corpus scope. If we widen to build-plans (and other `docs/**`):
(a) extend `_corpus_to_corpus_edges`'s `ls-tree` scope + a build-plan-aware target regex;
(b) add a build-plan source to the grep-oracle acceptance (the gap this finding fills);
(c) a **re-migration** (another daemon-down wipe+reproject window — finding-0066) to backfill
the build-plan edges. If we keep the authored-only scope, amend bp-026 §6(c) to say
`_CORPUS_DIRS`, not `docs/**`, and note build-plans are deliberately out (record why).

## Routing

`spec-fidelity` with a design flavor → orchestrator (the corpus-scope ruling is not a builder
call). Non-blocking: the v2 store is live and correct for the authored-corpus citation graph;
the build-plan surface is the follow-up.
