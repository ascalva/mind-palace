---
type: finding
id: finding-0244
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/role-state-and-scoped-handoff.md   # §2.10 — clause (e′)'s specification
  - docs/design-notes/session-handoff-gate.md            # §2.2-2.3 — the superseded clause (e)
  - docs/design-notes/trace-retrieval.md                 # Part 1 — the measurement
  - docs/build-plans/bp-126/plan.md
  - .claude/hooks/_lib.py
ftype: spec-fidelity
origin_plan: bp-126
route: builder
resolution: implemented as specified; the misattribution is carried forward knowingly and named here rather than silently fixed
---

# Clause (e′) inherits (e)'s authorship blindness: the trigger still keys on commits-in-session,
# not on who authored them — the measured defect the replacement was expected to fix

## What

The measurement that warranted this whole family says two things about clause (e). Only one of
them is addressed by clause (e′).

Verbatim, from the live brief's final revision (archived at
`docs/archive/resume-brief-final-2026-07-27.md:205-207`, and sourced to
`dn-trace-retrieval` Part 1):

> Clause (e) fired **108× raw / 99 fork-deduped** over 2026-07-19→27 across 16 sessions; peak day
> 07-26 = **36**; **302 resume-brief file ops** … All 5 firings *this* session were on the
> **sub-orchestrator's** commits — it keys on **commits-in-session, not authorship**.
> **⇒ Whatever replaces it should key on who authored the commit, or exempt paths an active plan
> holds.**

That final sentence is a stated design consequence of the measurement. **`dn-role-state-and-scoped-handoff`
§2.10 does not carry it.** §2.10 re-specifies (e′) as *"orchestrator posture, commits landed this
session"* — the trigger clause is reproduced unchanged from (e) — and then replaces only what is
*demanded once it fires*. The implementation in `bp-126` follows the note, so the shipped clause
(e′) reads:

```
plan is None  and  baseline and head_sha and head_sha != baseline  and  isdir(seat)
```

`head_sha != baseline` is true whenever HEAD moved, **regardless of who authored the commits or
what they touched**. A session that merely merges a delegated builder's branch, or commits a
brainstorm on the owner's behalf, or lands a sub-orchestrator's work, trips the trigger exactly as
a session that did the work itself does.

**So: the spec preserves the misattribution, and this finding says so rather than letting the bug
be carried forward silently.**

## Why it matters — and, honestly, why it matters *less* than it did

The two halves of the measured defect are separable, and (e′) fixes one of them completely:

| defect | mechanism under (e) | under (e′) |
|---|---|---|
| **re-arming** — every post-brief commit re-fires the gate, so one session fires it repeatedly (108 firings over 16 sessions ≈ 6.75/session, peak day 36) | mtime vs *last commit*, plus a content demand ("citing the final commit hashes") that could not be written before the commits it had to cite | **fixed, structurally.** Check 1 is a content compare with a fixed point (the §2.9 idempotence pin), so regenerate-then-commit converges in **one** step; check 2 keys on the *SessionStart baseline write*, so a late commit **cannot** re-arm it. Both proven by test, including against a mutation that keys check 2 to `last_commit` |
| **misattribution** — it fires on sessions that authored nothing and merely committed on another agent's behalf | `head_sha != baseline` | **unchanged** |

The residual harm is therefore an order of magnitude smaller but not zero: a session that authored
nothing is still asked, once, to regenerate a rendering and append a seat-journal entry. Two
observations pull in opposite directions and both deserve stating:

- **Arguably not a bug at all for check 1.** If a merge moved plan statuses, the seat's DERIVED
  rendering *is* stale — as a fact about the tree, independent of authorship. Regenerating it is
  correct work, and the *occupant of the seat at that moment* is the right party to do it.
- **Arguably still a bug for check 2.** Demanding a narrative entry from a session whose only act
  was to merge someone else's branch invites exactly the empty ceremonial entry the purity rule
  exists to prevent — "merged bp-124" is a status transition, which §2.5 forbids the narrative from
  carrying. The failure mode is not a blocked close; it is a **corpus of hollow entries**, which is
  worse, because it is invisible.

Only the second is a live concern, and it is a design question, not a code fix.

## What was NOT done, deliberately

Narrowing the trigger — by commit authorship (`%an`/`%ae`), or by exempting paths an active plan
holds — was **not** implemented. Three reasons:

1. **The load-bearing reason: §2.10 is a ratified specification and it pins the trigger.** A
   builder may not narrow a ratified predicate, and this one is not an implementation detail —
   it decides which sessions the gate governs. Everything else below is secondary to this.
2. `bp-126` §9 names *"No widening of what (e′) gates"* as a non-goal; narrowing is the same class
   of unilateral move in the other direction.
3. *(The weakest of the three, stated only for completeness — it should not be read as an
   obstacle.)* An authorship key is not in the shared `git log -1 --format=%H %ct`, so it would
   need that format string widened to `%H %ct %ae`. That is **mechanically free** — one string,
   no second `git` call, so the owner's DRY rule is not actually in tension. **If the ruling goes
   toward authorship, cost is not the objection; the spec is.**

## Re-entry condition

Not blocking; (e′) is built as specified and its tests are green. **Re-enter when either holds:**

- **(a)** a post-cutover session is observed being asked for a narrative entry when it authored
  nothing — i.e. the first hollow seat-journal entry appears. That is the failure this finding
  predicts, and it is observable in `docs/roles/orchestrator/journal.md` as an entry whose content
  is a status transition rather than judgement. The fix is a design decision on the trigger:
  extend the shared git call to `%H %ct %ae` and require authorship match, **or** rule that the
  seat's occupant owns the seat's freshness regardless of authorship and close this finding.
- **(b)** the firing count is re-measured after the cutover (the same instrument that produced the
  108/99 figures). If the per-session rate has not collapsed, the re-arming fix did not land either
  and this finding is the wrong diagnosis — look at `finding-0236` first.

**A concrete measurement is owed either way**, and it is cheap: the pre-cutover baseline is
`108 raw / 99 fork-deduped over 8 days, 16 sessions, 302 brief file-operations, peak day 36`. Any
honest claim that the cutover worked has to beat that number, not assert improvement.

## Routing

`spec-fidelity` → **builder**: resolved in place (implemented as the ratified note specifies,
divergence named rather than silently corrected), annotated here and in `bp-126`'s journal, and
the build continued. ⚑ The **re-entry half is a design question** — whether the trigger should key
on authorship — and if it is taken up, that is a design-note amendment routed to the orchestrator,
not a builder edit.
