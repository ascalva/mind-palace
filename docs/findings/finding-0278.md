---
type: finding
id: finding-0278
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
  - docs/brainstorms/study-not-product.md
  - docs/design-notes/dn-typed-workflow-registry.md
ftype: question
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Autopilot's purpose statement: "spend owner attention only where identity is at stake"

## What

`dn-autopilot-and-delegated-blessing` (the ratified note that lets autopilot perform the
`proposed→ready` blessing — the flip that marks a build plan ready to build) does not state
*why* autopilot exists, and the 2026-07-27 rulings surfaced two incompatible readings of
that silence [GROUNDED docs/brainstorms/study-not-product.md:72-83]:

- Read as **"reduce owner involvement,"** autopilot drifts toward exactly what the project
  opposes — the owner being the gate is the design, not the bottleneck; every ruling that
  night made him the gate *more* deliberately, not less.
- Read as **"spend the owner's attention only where identity is at stake,"** it is the
  correct instrument: it delegates the one gate whose judgement is mechanical and
  reversible (`proposed→ready`) and permanently forecloses the one that is neither
  (`draft→ratified`).

The owner's frame that decides between them: the corpus is a self-map, so corpus integrity
is identity integrity — attention is spent where the self-model is at stake. The
distinction should be written into the autopilot note's purpose section, not left to be
inferred by every later reader.

## Why it matters

A purpose left implicit is re-derived by each session that touches the note, and the
"reduce involvement" reading is the natural-but-wrong default — it is how autopilot scope
quietly widens. A one-paragraph purpose statement forecloses the drift at the frame,
which is where this repo forecloses things.

**Recorded consequence, not a resolution:** `dn-autopilot-and-delegated-blessing` stays
ratified and authoritative; this finding proposes an owner-side edit under
`dn-typed-workflow-registry` §2.10's revision protocol (edit → warrant lapse → PR → owner
merges). `oq-0037` (the parked owner question: who holds the autopilot MFA secret) is
untouched by this finding.

## Re-entry condition

Routes at the next `/triage`; batched to `owner-questions.md` if the owner wants the
wording proposed rather than written. Re-enters when the owner authors or re-auths the
purpose paragraph.

## Routing

`question`, type `direction` → orchestrator. Owner-only close: a study's question — and an
instrument's purpose — cannot be inferred by its apparatus.
