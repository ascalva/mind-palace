---
type: finding
id: finding-0252
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - .claude/hooks/_lib.py                       # _journal_tail_has_followthrough — clause (f)'s implementation
  - docs/findings/finding-0248.md               # the position half; this is the OTHER half, unnamed there
  - docs/findings/finding-0249.md               # the vacuous-pass class
  - docs/build-plans/bp-128/plan.md             # the home plan — this widens its Item 2/3/4
  - docs/brainstorms/the-false-success-rule.md  # the degenerate-input discipline
ftype: codebase
origin_plan: bp-128
route: builder
resolution: null
---

# Clause (f) is satisfied by a SUBSTRING, not a heading — so the sentence documenting the requirement satisfies the check for the requirement

## What

`finding-0248` established that clause (f) keys on **physical position**: it anchors the "tail" at
the last `## ` heading that is neither `## Follow-through` nor `## Markers`, which in a
template-minted journal is a trailing standing section rather than the newest entry.

That is one of **two** independent vacuity mechanisms in the same function, and the second one is
not named in `finding-0248`, in `bp-128`'s plan, or in the code's own docstring.

**The check's final act is `"## Follow-through" in tail` — a plain substring test over the region,
not a test for a heading.** Any occurrence of that literal text anywhere in the region satisfies it.

MEASURED by executing the real `_journal_tail_has_followthrough` — not a reimplementation — against
constructed inputs:

| input (as the journal tail) | verdict |
|---|---|
| a **backticked** mention: ``a `## Follow-through` block is required`` | **True** |
| the marker **inside a fenced code block** | **True** |
| a **mid-line prose** mention: `See the ## Follow-through rule.` | **True** |
| a genuine `## Follow-through` heading | True *(correct)* |
| no occurrence at all | False *(correct)* |

⚑ **And the live instance is not constructed.** At the moment of filing,
`docs/build-plans/bp-127/journal.md` — a plan on which **no work had been done**, whose journal is
entirely pre-build boilerplate, and which contains **zero** `## Follow-through` headings —
**passes clause (f)**. The satisfying text is a single backticked mention inside its
"Owed at seal" standing section, whose content is: *"A `## Follow-through` block is required by
clause (f)."*

**The sentence that documents the requirement is sufficient to satisfy the check for the
requirement.** That is the whole finding.

## Why it matters

**It is the purest instance yet of `finding-0249`'s class.** That finding's diagnosis is that *the
observable the check consumes is not causally downstream of the property being claimed*. Here the
observable is not merely upstream of the property — it is a **description** of it. A journal earns
a green verdict for *mentioning* the obligation it is being audited for.

**It survives the fix `bp-128` currently plans.** `bp-128` Item 2 makes the clause identify the
newest entry by **recency** rather than position, and Item 3 asserts it reddens on a journal with
trailing standing sections. Both address mechanism (A). Neither touches (B): once recency
correctly selects the newest entry, `"## Follow-through" in <that entry>` is *still* a substring
test, and a seal entry that says *"the Follow-through block is owed"* still clears it. **A fix that
closes (A) alone will be verified green against a check that is still vacuous.** That is the
`finding-0249` failure repeating inside its own repair.

**The docstring is the argument this repo already learned to distrust.** The function documents its
bound as: *"Bounded to the final entry — the tail from the last `## ` header … — so an EARLY draft
mention can't false-clear the gate."* Both halves of that sentence are false as implemented: the
bound is to the last **standing section**, not the final entry (that is `finding-0248`), and a
mention *can* false-clear the gate — the table above is five demonstrations of exactly the
false-clear the sentence claims to prevent. The seat journal's own lesson from this wave was
*"mutate the argument you are proudest of: a carefully justified choice attracts prose instead of
tests, precisely because the prose feels like proof."* This is that, verbatim, in the clause the
next plan is about to repair.

⚑ It is also the **second instance in one wave** of *a marker's own documentation matching the grep
for that marker* — `bp-127` manifest entry 11 is the first (an unanchored `## CAPSULE` grep matches
the seat journal's preamble **defining** the marker; measured at 4 matches on a file with 0
capsules, `finding-0251`). Two artifacts, two checks, one shape. That is a pattern worth naming and
not a coincidence worth fixing twice.

## What is NOT claimed

- **Not that any seal was dishonest.** As with `finding-0248`: a vacuous pass means those seals were
  **unverified**, not false. Most carry genuine blocks.
- **Not that a substring test is wrong in general** — it is the deliberate "grep-class tooth" the
  docstring names (F-WF5's accepted residual, header-presence only). The defect is that it does not
  test for a *header*, which is the one thing it claims to test for. Requiring
  `line.strip() == "## Follow-through"` keeps the check exactly as crude and closes this hole.
- **Not that `bp-128`'s plan is wrong.** Its §1 "done means" — *"clause (f) passes only when the
  journal genuinely gained a compliant fresh entry this session"* — already covers this in spirit.
  What is missing is that the **item-level acceptance and the mutation matrix name only (A)**, so a
  builder can satisfy every listed criterion and ship (B) intact.
- **Not measured:** how many historical seals passed on (B) alone. One live instance is established
  (`bp-127`, above) and `finding-0248` records another (`bp-126`). The corpus count is `bp-128`
  Item 5's job, and it should now be reported **per mechanism**, not as one number.

## Re-entry condition

`bp-128` holds `.claude/hooks/_lib.py` and both test files, so **(B) is inside its existing write
scope and needs no scope change** — it is the same clause, the same function, the same diff.

It inherits three concrete additions:

1. **Item 2's six-mode matrix gains a seventh mode:** *the marker present only as prose / backticked
   / inside a code fence*. Fail-open still governs every indeterminate mode; this one is not
   indeterminate, it is **determinately non-compliant** and must BLOCK.
2. **Item 3's degenerate input is now two inputs, and the second is real, not constructed:** a
   journal whose newest entry mentions the marker without carrying it. `bp-127`'s journal in its
   pre-build state is the reproduction case; capture it as a fixture before that plan seals, because
   its seal will write a genuine heading and the live instance will disappear.
3. **Item 4's mutation matrix gains:** *relax the heading test back to a substring test* — it must be
   **caught**. A surviving mutant there means the tests pin (A) and not (B).

⚑ Item 3's falsifier — *run the new test against the unfixed clause, where it must pass* — applies
unchanged and is what proves the test distinguishes the fix from its absence.

## Routing

`codebase` → the builder resolves, annotates, continues. Filed by the sub-orchestrator that owns
the `bp-127`/`bp-128` wave, from an independent measurement taken while grounding the second plan;
recorded as a finding rather than as a line in a delegation prompt so that it outlives the session
that found it.
