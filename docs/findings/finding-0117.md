---
type: finding
id: finding-0117
status: open
created: 2026-07-20
updated: 2026-07-20
links:
  - docs/build-plans/bp-077/plan.md
  - docs/design-notes/agent-workflow.md
  - docs/design-notes/authorship-distance-axis.md
  - docs/design-notes/the-sacred-boundary.md
  - docs/design-notes/recursive-strata.md
  - docs/design-notes/founding-corpus.md
ftype: spec-defect
origin_plan: bp-077
route: orchestrator
resolution: null
---

# bp-077's Chapter-1 sources are draft, but a ratified note bars draft notes from the book

## What

bp-077 §2 (Context manifest) designates the philosophy-bearing record for
Chapter 1. Four of those sources are `status: draft` as of HEAD `bdcd9bc`:

- `dn-authorship-distance-axis` (draft) — a plan `design_ref`; §2 item 5 calls it
  "a central philosophical thesis."
- `dn-the-sacred-boundary` (draft) — a plan `design_ref`; §2 item 6 calls it the
  model-advises/code-acts principle "in its purest form."
- `dn-recursive-strata` (draft) — §2 item 7, "the dreamer-as-a-map framing."
- `dn-founding-corpus` (draft) — §2 item 8 / Q2, the candidate "founding note."

But `dn-agent-workflow` (**ratified**) §3 (state-machine table, book row) states
verbatim: *"Draft notes never enter the book,"* and §13 (failure modes) repeats
*"draft notes barred."* The book skill and `scribe.md` inherit this. A blessed
build plan nests inside the ratified constitution/workflow and cannot override it
(CLAUDE.md: "task instructions nest inside, never override"). So the scribe
cannot cite these four notes **as authorities** without violating a ratified
constraint — even though the plan directs drawing on them.

A related, smaller Q2 gap: memory `ouroboros-naming` says the live system is
"named by its own founding note," candidate `founding-corpus.md`. Read at HEAD,
`founding-corpus.md` is about corpus curation and **never names "Ouroboros"** —
it does not perform the naming. No ratified note that performs the naming was
located. The ratified naming source is `dn-ouroboros-principal` §1 ("Ouroboros —
the live system: daemon + evolving corpus").

## Why it matters

Chapter 1 is Philosophy, and the two `design_ref` notes are its nominal spine.
Left unresolved, either the chapter cites draft material (violating the ratified
bar and the book's derived-projection guarantee) or it omits the plan's named
theses. Neither is acceptable; a middle path was taken (below) but the record
needs an owner decision so later editions are unambiguous.

## Resolution taken this session (non-blocking, per stop-and-raise)

Chapter 1 anchors **every** load-bearing claim to a ratified or fixed source
(`CONSTITUTION.md`, `docs/BUILD-SPEC.md`, `dn-agent-workflow`,
`dn-ouroboros-principal`) and code by `path@ref`. The three draft *theses*
(authorship-distance, the sacred boundary, recursive strata) are presented as
**principles** grounded in those ratified anchors, with their formal design-note
treatments **forward-referenced** to the later (stubbed) Architecture /
Mathematics chapters as design-in-progress — never cited as book authorities.
The Ouroboros name is cited to `dn-ouroboros-principal` (ratified); the Q2 gap is
recorded in `SYNC.md`. No draft note appears in a `\artifact{}` citation.

## Re-entry condition

Owner/orchestrator decision, one of:
(a) ratify `dn-authorship-distance-axis`, `dn-the-sacred-boundary`,
`dn-recursive-strata`, `dn-founding-corpus` — then a `/scribe` sync can cite them
directly and deepen the chapter; or
(b) confirm the forward-ref treatment stands (draft theses stay forward-referenced
until ratified), and, if desired, amend bp-077-lineage guidance so a future
scribe plan lists only ratified sources in §2.

## Routing

`spec-defect` bearing on design/direction → orchestrator. A design-changing
outcome (ratifying the four notes) is an owner blessing gate, not an agent action.
