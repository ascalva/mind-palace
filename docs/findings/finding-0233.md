---
type: finding
id: finding-0233
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/design-notes/role-state-and-scoped-handoff.md   # §1.1 — the claim this finding falsifies
  - docs/design-notes/agent-workflow.md                  # the ratified note A10 would amend
  - .claude/hooks/_lib.py                                # :435-441 pre-hoc denial, :797-824 post-hoc block
  - docs/build-plans/bp-126/plan.md                      # where A10 is parked as an owner act
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Amendment A10 cannot be landed by a build plan — every lettered amendment to a ratified note is an owner hand-act

## What

`dn-role-state-and-scoped-handoff` §1.1 states, of amendment A10 to `dn-agent-workflow`:

> *"The amendment text lands via a build plan after ratification, per the A1–A9 precedent
> `[GROUNDED docs/design-notes/agent-workflow.md:276 §16; the A9 entry is the direct precedent]`."*

**Enforcement forbids exactly that.** `docs/design-notes/agent-workflow.md` carries
`status: ratified`, and the guard is unconditional and runs *before* the write-scope check:

- **Pre-hoc** — `scope-guard`'s design-note arm denies any Edit/Write to a note whose on-disk
  status is `ratified` or `superseded`, and it returns before the plan-capability check at
  `# 2. Plan write-scope capability` `[GROUNDED .claude/hooks/_lib.py:435-441]`. **Listing the
  file in a plan's `write_scope` does not help** — the status arm never consults it.
- **Post-hoc** — the Stop-gate (b2) clause blocks session close on any modification or deletion
  of a note that is ratified/superseded **at HEAD**, which is the laundering-proof path against a
  Bash write `[GROUNDED .claude/hooks/_lib.py:797-824]`.

This is A8 working exactly as designed (warrant finding-0025): *"a ratified or superseded note is
agent-immutable — content and status, Edit/Write and Bash alike."* The defect is not in the
enforcement; it is in the note's claim about what a build plan can do.

**The A1–A9 precedent does not establish otherwise.** Every amendment commit is authored by the
owner's git identity (`fc81e34 amend(agent-workflow): A9 …`), which is the repo's only committer
identity and therefore settles nothing about who *wrote* it. What is settled is the present tense:
under the enforcement in the tree today, **no agent in any posture — builder, scribe, or
orchestrator — can write that file.** Amendments A1–A6 predate A8's status guard entirely.

## Why it matters

1. **A plan carrying "land amendment A10" as a §7 item would be unbuildable.** The builder's only
   lawful moves are to file a finding and stop, or to route around the guard — and routing around
   is forbidden. The plan would strand its own acceptance criterion. This is the
   acceptance-reachability failure class (findings 0177 / 0191 / 0204), caught here at graduation
   where widening or parking costs one line rather than an owner round trip.
2. **The note's §3 Consequences lists A10 as a deliverable of this graduation.** Left uncorrected,
   the family would look incomplete forever, or a builder would try the edit and burn a session on
   a denial it cannot resolve.
3. **It generalizes.** Any future ratified note that says "the amendment lands via a build plan"
   inherits the same defect. The honest rule is: **a lettered amendment to a ratified note is an
   owner hand-act of the same class as a blessing** — an agent may *draft* the text, never land
   it. That rule is not written down anywhere today.

## Re-entry condition

The graduation parked A10 rather than stranding it: `bp-126` §11 records the default (not
attempted by any plan in the family), the rejected alternatives with reasons, and drafts the exact
A10 text into `docs/build-plans/bp-126/journal.md` for a one-paste owner landing.

**Re-entry:** the owner lands A10 by hand after `bp-126` merges — sequenced that way so the
amendment describes a clause that actually exists. The same hand-act carries the partial
supersession of `dn-session-handoff-gate` §2.2–2.3, which §1.1 of the note likewise assigns to the
owner (and deliberately does *not* express as a `superseded_by` flip, since that note is not
wholly replaced).

**Prerequisite:** `bp-126` merged.

## Routing

`design` → **orchestrator**, and thence to the owner, because the resolution is an owner act and
because the general rule it implies is a workflow-constitution question:

- **Ask 1 (immediate):** land A10 by hand after bp-126 merges — text drafted in bp-126's journal.
- **Ask 2 (general):** should the rule *"a lettered amendment to a ratified design note is an
  owner hand-act; an agent may draft it, never land it"* be written into the amendment log or the
  graduate skill, so the next ratified note does not repeat the claim? Batch to
  `docs/inbox/owner-questions.md`.

Not a `blocker`: the four plans of this family are all buildable without A10. The amendment is
documentation of a change that will already be true in the code.
