---
type: finding
id: finding-0183
status: routed
created: 2026-07-25
updated: 2026-07-26
links:
  - docs/build-plans/bp-104/plan.md
  - docs/book/chapters/01-philosophy.tex
  - docs/book/chapters/02-architecture.tex
  - docs/design-notes/the-sacred-boundary.md
  - docs/design-notes/agent-workflow.md
  - docs/findings/finding-0117.md
ftype: spec-defect
origin_plan: bp-104
route: orchestrator
resolution: routed → owner (oq-0044a); dn-the-sacred-boundary still draft, so the three-channel taxonomy has no ratified home
---

# Chapter 1 forward-promised a taxonomy that only a DRAFT note carries — Chapter 2 cannot deliver it

> **Triage 2026-07-26 (session-52) — batched to `oq-0044` part (a).**
> `docs/design-notes/the-sacred-boundary.md:4` is still `status: draft` (untouched since `66c3e6f`,
> no 2026-07 commit), and `verdict-authority.md:4` is also `draft` — so the three-channel taxonomy
> (verdict authorization · ingestion · effects) still has **no ratified home**, and five subsystem
> notes hang off an unblessed spine. bp-104's interim repair is holding:
> `01-philosophy.tex:99` uses `\fwdthesis{the sacred boundary}{ch:architecture}` and `SYNC.md:100-104`
> carries the `forward-referenced:` row.

## What

`docs/book/chapters/01-philosophy.tex` (published at edition `bdcd9bc`, bp-077)
promises the reader, in §"The sacred boundary":

> "The full taxonomy of the three channels that cross the core's boundary is
> architecture; \autoref{ch:architecture} gives it."

That taxonomy — **verdict authorization** (into core) · **ingestion** (into core)
· **effects** (out of core), with the inbound/outbound symmetry read as one
discipline — exists in exactly one place in the record:
`docs/design-notes/the-sacred-boundary.md` §1, which is **`status: draft` at
`009b726`** (verified this session).

`dn-agent-workflow` §3 bars draft notes from the book. So Chapter 2, written under
this plan, **cannot** keep Chapter 1's promise. This is the same defect class as
finding-0117 (bp-077 listed four draft notes as Chapter-1 sources), one step
downstream: 0117 caught the *sources*; this catches a *published forward
reference* that the barred source was silently backing.

Two further facts make the gap sharper, not softer:

1. The ratified record carries a **partial** of the same idea and no more.
   `dn-capability-scope` §2.1 splits authority into `A = P × W_Σ × W_world`
   (advisory ladder × projection-write × effector blast radius) and states
   explicitly that "the seed's single *write* rung conflated sensor projection and
   effector mutation — two capabilities the architecture already separates
   structurally." That is the ingestion/effects distinction, ratified. **The
   verdict-authorization channel has no ratified home** (`verdict-authority.md` is
   also draft), and the *three-channel closure claim* ("the core has exactly
   three") is nowhere ratified.
2. `dn-plane-principals` (ratified) cites `dn-the-sacred-boundary` under
   "Kinship" for the capability-dissolution reading. A ratified note gestures at
   a draft one; the book may follow neither the gesture nor the target.

**What bp-104 did instead (recorded so the decision is inspectable):**

- Chapter 1's sentence was repaired in place from an assertion-of-delivery to a
  `\fwdthesis{}` forward reference — the macro that names a draft thesis without
  citing it. No claim was retracted; a promise was downgraded to a pointer.
- Chapter 2 §2.7 gives the **ratified partial only** (`dn-capability-scope`'s
  authority product) and says in the text that the fuller taxonomy is an argument
  being developed.
- `docs/book/SYNC.md` gained a `forward-referenced:` block listing every draft
  thesis the book names but does not cite, with the chapter each lands in on
  ratification.

## Why it matters

Left unresolved, two costs compound. First, the book has a **structural hole at
its centre**: the sacred-boundary principle is the one Chapter 1 calls "the
discipline that protects the purpose," and the manual can state it only as a
principle, never as the mechanism the owner asked to be able to re-read. Second,
the hole is *invisible* — a reader sees a chapter that discusses boundaries
thoroughly and has no way to know that the organizing taxonomy was withheld. The
`\fwdthesis` repair makes it visible, which is the correct interim state, not the
correct end state.

There is also a live-system stake beyond the book. `dn-the-sacred-boundary` is a
**spine note** by its own header ("indexes the five subsystem notes that
instantiate it"). Five design notes hang off an unratified spine; anything that
graduates from one of them inherits an unblessed frame.

## Proposal

Ratify `dn-the-sacred-boundary` — or, if its §1 table has drifted from what the
system now is (the plane split and the ring split both landed after it was
written, 2026-07-04), supersede it with a note that states the channel taxonomy
against the current mechanism. Either outcome unblocks the chapter; the second is
likelier to be right.

The owner's blessing is the only thing that can do this: `draft → ratified` is an
owner-only hand edit and no agent may perform it (`dn-agent-workflow` §10).

## Re-entry condition

The owner ratifies `dn-the-sacred-boundary` (or ratifies a successor stating the
channel taxonomy). At that point a `/scribe` run amends Chapter 2 with the full
taxonomy, restores Chapter 1's sentence from `\fwdthesis` to a citation, and
removes the id from `SYNC.md`'s `forward-referenced:` block.

## Routing

`spec-defect` bearing on **design** → the orchestrator. Owner input is required
(only the owner ratifies), so this batches to `docs/inbox/owner-questions.md`.
The scribe wrote around the gap and did not block; nothing in bp-104 is parked on
this finding.
