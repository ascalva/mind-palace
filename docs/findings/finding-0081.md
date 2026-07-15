---
type: finding
id: finding-0081
status: open
created: 2026-07-15
updated: 2026-07-15
links:
  - docs/design-notes/core-query-protocol.md
  - docs/build-plans/bp-035/plan.md
  - ops/code_sensor.py
  - core/reference_view.py
ftype: spec-defect
origin_plan: bp-035
route: orchestrator
resolution: null
---

# `dn-core-query-protocol` frontmatter + §3.1 are stale: the doc→doc extractor already shipped

## What

The ratified note `dn-core-query-protocol` records two facts that reality has overtaken (plan
bp-035 §4 owed this finding as its cross-reference-on-extension):

1. **Frontmatter — "reference_edges, 61k edges … code-anchored."** The live store now holds
   **~272k edges, incl. ~75k `corpus_to_corpus` (doc→doc)** — measured 2026-07-15. The graph is
   no longer code-anchored; doc→doc edges are first-class.
2. **§3 Consequence 1 / §3.1 — "the doc→doc reference extractor" named as the recommended FIRST
   graduation.** It is **already built**: `ops/code_sensor.py:427` (`_corpus_to_corpus_edges`)
   mints doc→doc edges (front-matter `design_ref`/`links`/`depends_on`/`warrant`/`supersedes`
   + inline note-citations + `[[wikilink]]`), shipped via the sensor by bp-026 — AFTER the
   note's snapshot. So the real first gap was never the extractor but the **read surface**: the
   graph was fed yet agent-unreachable (`all(target_ref=…)` had zero callers). bp-035 closes
   that gap (`core/reference_view.py`).

The note's own standing gap phrase — "code-anchored + agent-unreachable" — is now half-resolved:
the graph is doc-aware (extractor shipped) and, as of bp-035, agent-reachable (the read surface).

## Why it matters

A reader graduating future work off this note would (a) under-count the graph by ~4.5× and
mis-read it as code-only, and (b) re-graduate an already-built extractor. The bp-035 grep-oracle
(`tests/integration/test_reference_oracle.py`) measured the reconciliation directly: the note's
hand-run demo reported **doc→doc recall 0/16 = 0.000** at the 61k snapshot; the first measured
run now reports **227/228 = 0.996** on the full-path citation surface (precision 0.991,
doc→code(.py) recall 1.000). The staleness is not cosmetic — it inverts which of the note's own
Consequences (1 vs 2) is the standing work.

## Re-entry condition

None — this finding parks no bp-035 criterion (all three items completed regardless; the note is
never edited by this plan). It records an erratum for the owner. The ratified note is immutable
(CLAUDE.md A8), so the correction cannot be a silent edit: the channel is an owner-blessed
**note amendment/supersession** at the design gate (finding skill §Promotion path), warrant-linked
to this finding. On acceptance this flips `routed → promoted`.

## Routing

`spec-defect` whose fix is an owner-gated design-record amendment → **route `orchestrator`**: the
note is immutable A8, so the builder cannot resolve it against the code (the code is already
correct — it is the *note* that lags). The orchestrator batches the erratum to the owner
(`owner-questions.md`) or proposes the note amendment three-place (P = current note, P′ = amended
frontmatter/§3, warrant = this finding).
