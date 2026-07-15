---
type: finding
id: finding-0065
status: routed
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

## Ruling (2026-07-13, fable pass `claude-fable-5`, tier-verified; orchestrator-captured)

**Option 2-narrow: add a distinct `workflow` node kind** (do NOT widen `corpus`). Grounded:

- **"Corpus" = the authored-thought layer**, by the store's own contract (`reference_edges.py`
  corpus-kind = design-note/findings/brainstorm target) AND an existing owner ruling ("code,
  comments, and documentation are **not** authored-dialogue corpus", code-observation-projection
  §, 2026-07-11). Build-plans/journals/PROGRESS are the artifact-chain's *work-motion* layer —
  process, not thought. Folding them into `corpus` (option 1) makes the kind-name lie and
  erodes the §2.4 sacred-boundary claim ("corpus-structural, not observed exhaust").
- **§6(c)'s "`docs/**`" was a scope typo, not a decision** — `docs/**` includes
  `docs/templates/build-plan.md` (placeholder `<docs/design-notes/....md>` → a garbage edge to
  a nonexistent target), plus archive/book/research. The builder's `_CORPUS_DIRS` reuse was the
  *safer* wrong answer. The deliberated surface is **corpus + workflow**, not `docs/**`.
- **Option 3 (authored-only) rejected** — defeats the graph's motivating purpose (plans are the
  most operationally-relevant citing surface for THIS finding + 0059).
- **The v2 schema was built for this** — a kind is a boundary-validated TEXT column; adding
  `workflow` needs no DDL/identity-formula change. The math consumers WANT the split (the §2.5
  citation complex is built over `corpus↔corpus` only).

**Scope, phased:** `docs/build-plans/**/plan.md` NOW (source + target); journals behind a
bp-011-style precision measurement (they narrate paths, not always cite); PROGRESS/inbox
deferred (mutable queue state, re-entry: a consumer wants queue provenance); templates/book/
archive explicitly out; `research/` a plausible future *corpus* (not workflow) addition.
**Directions to mint** (all have live instances): `workflow_to_corpus` (the warranted one),
`corpus_to_workflow`, `workflow_to_workflow`, `code_to_workflow`; `workflow_to_code`
precision-gate first (a plan's `write_scope` is a capability grant, NOT a citation).

**Cost (lighter than §"Re-entry" feared):** likely an **additive backfill, not wipe+reproject**
— edge_id formula unchanged, widened extractor is a strict superset → replay re-mints existing
edges as INSERT-OR-IGNORE no-ops + adds only new kind-tagged edges; rollback = `DELETE WHERE
'workflow' IN (source_kind, target_kind)`. `[INFERENCE — make it an acceptance check.]` Still an
owner-coordinated finding-0066 window (deploy + replay).

## Resolution path (two follow-ups; neither blocks — the v2 store is live + correct for what it scans)

1. **Design-note shaping (the already-owed fable-vet of `dn-core-query-protocol`, pre-ratification):**
   name the reference stratum's kind vocabulary `{code, corpus, workflow}` in §2.1 (with the
   orchestrator's "build-plane artifacts" scope row = the `workflow` kind); restate the §2.4
   boundary claim per-kind; fix §3.1's "`docs/**`" wording; scope the §2.5 citation complex to
   `corpus↔corpus`. NB: `workflow` is a node kind + scope atom, NOT a γ^d-damped recursive
   stratum — say so, so nobody wires it into edge budgets.
2. **A small follow-up plan (warrant = this finding; does NOT need the note ratified — it
   completes bp-026 §6c's pinned-but-unmet scope):** `KINDS`/`DIRECTIONS` + path→kind classifier
   in `reference_edges.py`; scan + target-regex widening in `ops/code_sensor.py`; **a build-plan
   source in the grep-oracle acceptance** (the exact gap this finding names); the superset-property
   acceptance check; the additive backfill in an owner-coordinated finding-0066 window.

## Routing

`spec-fidelity` with a design flavor → orchestrator. Ruling made (option 2-narrow); flips
`open → promoted` when the owner concurs and the follow-up plan is minted. Non-blocking: the v2
store is live and correct for the authored-corpus citation graph; workflow edges are the follow-up.
