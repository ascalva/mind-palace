---
type: finding
id: finding-0274
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/build-plans/bp-137/plan.md
  - docs/findings/finding-0263.md
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
  - docs/templates/build-plan.md
  - scripts/autopilot_eligibility.py
ftype: spec-defect
origin_plan: bp-137
route: orchestrator
resolution: null
---

# P3's pinned regex is bullet-anchored, but 9 plans fold `**Touches stored data?**` onto another field's bullet — the flag is invisible to the check in 5 of the 25 plans it calls UNDETERMINED

## What

`bp-137` §6 pins P3's form (the `finding-0263` correction):

> For each `### Item ` heading in the plan's §7, the item body must contain exactly one line
> matching `^\s*[-*]\s*\*\*Touches stored data\?\*\*\s*(?P<value>.*)$`

The regex is **anchored at the bullet**: the flag must open its own list item. That is exactly
`docs/templates/build-plan.md:111`'s form, and it is implemented verbatim in
`scripts/autopilot_eligibility.py`. But a second authoring form exists in the tree — the flag
appended to the end of *another* field's bullet:

```
- **Invariant(s):** none touched. **Touches stored data?** no.          (bp-091:133)
- **Invariant(s):** read-only. **Touches stored data?** no. **Parallelizable?** no.   (bp-072:182)
  the env-only get_secret. **Touches stored data?** No (reads config…). (bp-067:223)
```

**Measured 2026-07-27** over all 137 `docs/build-plans/*/plan.md`, comparing the count of raw
`**Touches stored data?**` occurrences inside §7 against the count the pinned regex matches
inside `### Item ` bodies:

| plan | raw in §7 | seen by the regex | P3 verdict |
|---|---|---|---|
| bp-035 | 3 | 2 | fail |
| bp-038 | 3 | 1 | undetermined |
| bp-067 | 3 | 0 | undetermined |
| bp-068 | 2 | 0 | undetermined |
| bp-072 | 5 | 0 | undetermined |
| bp-090 | 4 | 3 | fail |
| bp-091 | 3 | 1 | undetermined |
| bp-092 | 4 | 3 | fail |
| bp-137 | 5 | 4 | pass |

Nine plans. `bp-137`'s own row is benign and worth naming so it is not read as a defect: its
fifth occurrence is a *quotation* of the flag inside Item 15's degenerate-input prose, not a
declaration, and the regex is right to ignore it.

## Why it matters

**It is safe by construction, which is why this is a `spec-defect` and not a `blocker`.** A
folded flag is never read as PASS-evidence. The item that carries it has no bullet-anchored
line, so that item is `UNDETERMINED`, and `UNDETERMINED` is absorbing under the conjunction —
the plan's overall verdict is `FAIL`. **The miss can only ever refuse; it can never produce a
false PASS**, not even on a folded `Yes`. That is the invariant-7 behaviour the whole plan is
built around, holding on a case its author did not anticipate.

What it costs is *reach*, not safety: 5 of the 25 plans P3 currently calls `UNDETERMINED` are
undetermined because of the authoring form rather than because the author hedged. `bp-137`
Item 15's named falsifier is *"the pinned regex rejects a correctly-written new plan because
of a formatting detail the template permits — then the check is enforcing a spelling, not a
property, and it will train authors to game it."*

**Verdict on the falsifier: it fires, but it does not disqualify.** The §10 stop-and-raise
condition is *"P3's `UNDETERMINED` set is **dominated** by template-legal shapes the regex
missed"*. It is not dominated — 5 of 25 (20%). The other 20 are: 5 plans with no §7 section at
all (`bp-000`–`bp-005`, which predate the template), 1 whose items are bold paragraphs rather
than `### Item ` headings and which carries the flag zero times (`bp-128`), and 14 whose items
genuinely carry no flag. And the folded form is **not** template-legal in the strict sense:
`docs/templates/build-plan.md:111` renders each field as its own bullet. So the build
continued rather than parking the criterion.

The builder deliberately did **not** widen the regex. `bp-137` §6 is the authoritative pinned
form, and §4 states that any divergence from it is *"a `spec-defect`, never a silent
re-interpretation"*. Loosening a security-relevant predicate's parse on a builder's own
authority is exactly the move that rule forbids.

## Re-entry condition

**Not blocking. `bp-137` shipped against §6 as pinned.** The choice is the owner's, and it is
the *same* choice `finding-0263` already routes to him — batch it there:

- **Option A — pin the authoring form.** Amend `docs/templates/build-plan.md:111` to state
  that the flag must open its own bullet, and leave the regex as is. Cheapest; makes the
  existing check correct-by-convention going forward; does not touch the 9 historical plans
  (a normalization sweep remains `bp-137` §9 non-goal 1).
- **Option B — widen the regex** to `(?:^|\.\s|\s{2})\*\*Touches stored data\?\*\*\s*(...)$`
  or similar, accepting a mid-line match. Reaches the 9 plans, but the "exactly one line per
  item" rule that makes a duplicated flag `UNDETERMINED` becomes harder to state, and a
  quotation of the flag in prose (as in `bp-137` itself) would start counting as a
  declaration — trading a safe under-read for an unsafe over-read.
- **Option C — the front-matter key.** Subsumes this entirely, and is already
  `finding-0263`'s parked design question (`touches_stored_data: false` as a real per-item
  machine-read field). If the owner takes C, this finding closes with it.

⚑ Whichever is chosen, the change lands in a **new plan**: `docs/templates/build-plan.md` is
outside `bp-137`'s `write_scope` and the design note is ratified and agent-immutable (A8).

## Routing

`spec-defect` → **orchestrator**. The implementation half was settled inside `bp-137` on the
builder's own authority (implement §6 verbatim, refuse rather than guess, record the census).
The template/regex half is a `design` question about an authoring convention and belongs in
the same owner batch as `finding-0263` and the `oq-0047` ftype ruling.
