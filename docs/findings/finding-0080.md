---
type: finding
id: finding-0080
status: routed
created: 2026-07-14
updated: 2026-07-14
links:
  - docs/design-notes/core-query-protocol.md
  - docs/build-plans/bp-035/plan.md
  - core/stores/reference_edges.py
  - ops/code_sensor.py
  - docs/findings/finding-0059.md
  - docs/findings/finding-0061.md
ftype: spec-fidelity
origin_plan: bp-035
route: orchestrator
---

# `dn-core-query-protocol` frontmatter + §3.1 are STALE — the doc→doc extractor already shipped (via the sensor), and the substrate is 272k edges, not 61k

## What

Ratified `dn-core-query-protocol` (2026-07-13, `implementation: design-only`) records two facts that
the live code has since overtaken:

1. **Frontmatter:** "the reference substrate (reference_edges, **61k edges**) exists but is code-anchored
   + agent-unreachable." The live store now holds **~272,819 edges** (code_to_corpus 49,817 /
   corpus_to_code 149,280 / **corpus_to_corpus 73,722**) — a 4.5× growth past the note's snapshot.
2. **§3 Consequence 1 / §3.1:** names "the doc→doc reference extractor … the recommended *first*
   graduation." But `ops/code_sensor.py:427` (`_corpus_to_corpus_edges`) **already mints doc→doc edges**
   at projection time — YAML front-matter (`design_ref`/`links`/`depends_on`/`warrant`/`supersedes`/
   `superseded_by`), inline `dn-*`/`finding-*` citations, and `[[wikilink]]` resolution — and has
   populated ~73k `corpus_to_corpus` edges. The extractor the note calls unbuilt is built.

The note's §2.6 hand-demo ("doc→doc recall 0/16") measured the store BEFORE those edges were minted; it
is not the current state.

## Why it matters

The one CORRECT half of the note's gap analysis is decisive and still open: the graph is **fed but
agent-unreachable** — `ReferenceEdgeStore.all(target_ref=…)` has zero callers outside its own docstring
(the only store readers are the writer `code_sensor` and `reset`). So the real first plan is the READ
surface, not another extractor. **bp-035 (`ReferenceView`) is graduated on exactly this corrected
reading** and re-measures the 0/16 demo against the now-populated store (its Item 3 oracle).

Left unrecorded, the stale note would send a future graduation to re-build an extractor that exists —
wasted work — and mis-state the substrate size in any book chapter or downstream design.

**MEASURED (bp-035 oracle, 2026-07-15).** The `ReferenceView` self-grading oracle put a number on the
reconciliation: doc→doc full-path recall **227/228 = 0.996** (precision 228/230 = 0.991; doc→code(.py)
recall 373/373 = 1.000; expanded bare-`finding-`/`dn-` prose surface 228/299 = 0.763 — the residual is
sensor precision-gating, not a bug). Against the note's stale hand-demo of **0/16 = 0.000**, the doc→doc
graph went from agent-invisible to 99.6%-faithful and reachable. (The delegated builder independently
re-filed this reconciliation as `finding-0081`, not knowing this one existed — a same-session duplicate;
0081 was dropped and its measured datum folded here.)

## Resolution (proposed)

The note is ratified → **immutable (A8)**; it is never hand-edited to "fix" this. The finding IS the
channel (the same discipline supersession uses — the discredited claim stays inspectable). Two acts:

1. **Orchestrator batches a note-erratum to the owner** (`owner-questions.md`): record that
   `dn-core-query-protocol` frontmatter (61k) + §3.1 (extractor-as-first-plan) are overtaken; the owner
   decides whether to annotate the ratified note (owner-only) or leave the finding as the standing
   erratum. No agent edits the note.
2. **bp-035 carries the corrected plan-of-record** (its §4 Reconciliation cites this finding). On
   bp-035's completion, its oracle number replaces the note's 0/16 demo as the live sensor-fidelity datum
   (finding-0059/0061 turn from anxiety into a measured number).

Not a defect in the code — the sensor did the right thing; the note simply predates it. `spec-fidelity`:
the design record and the built reality drifted, and the finding reconciles them without mutating either
fixed point.
