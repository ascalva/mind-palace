---
type: finding
id: finding-0271
status: resolved
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/build-plans/bp-136/plan.md
  - docs/findings/finding-0193.md
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
  - docs/templates/finding.md
  - scripts/autopilot_halt.py
ftype: spec-fidelity
origin_plan: bp-136
route: builder
resolution: resolved in bp-136 — H1's builder-lane allowlist is `{codebase, spec-fidelity, spec-defect}` over an explicit `route: builder`; carried forward to whichever plan implements oq-0047
---

# H1's pass set: `bp-136` §7 Item 10's two acceptance clauses are not literally consistent

## What

Item 10's acceptance carries two clauses that cannot both be read literally:

1. *"**H1** fires for any such finding … whose `ftype`/`route` pair is not unambiguously
   `codebase | spec-fidelity`"* — the note §2.4 conservative reading, quoted verbatim into
   `bp-136` §6.
2. *"**H1 does not fire** for a finding explicitly `route: builder` with `ftype: spec-defect`."*

`spec-defect` is not a member of `{codebase, spec-fidelity}`, so clause 1 read literally
reddens clause 2. A builder implementing only clause 1 ships a halt list that fires on the
single most-used finding type in the corpus; a builder implementing only clause 2 has no idea
where the boundary is.

## Why it matters

This is the load-bearing leg of the halt list — H1 is what stops an unattended run that has
wandered out of the low-stakes envelope. A predicate whose specification is self-contradictory
gets implemented by guess, and the guess is invisible afterwards.

## Resolution (builder, `bp-136` Item 10)

Implemented as the **union of the builder-side lane names across both live vocabularies**,
gated on an explicit route:

> H1 does **not** fire iff `route == builder` **and**
> `ftype ∈ {codebase, spec-fidelity, spec-defect}`. Everything else halts — an absent `route`,
> an absent `ftype`, and any unrecognised value included.

The justification is `finding-0193`'s own census: the two vocabularies are **disjoint names for
the same two lanes**, not two taxonomies. `docs/templates/finding.md:9` calls the builder lane
`spec-defect` (54 uses, joint-most-used); `CLAUDE.md:51-54` calls it `codebase | spec-fidelity`.
Admitting the template's synonym is not a widening of §2.4 — the pass set stays a **closed**
three-name allowlist keyed on an explicit `route: builder`, and every ambiguity still halts.

Pinned in `scripts/autopilot_halt.BUILDER_FTYPES` with the reasoning inline, and tested in both
directions (`test_h1_does_not_fire_for_an_explicitly_builder_routed_finding`,
`test_h1_fires_on_a_non_builder_ftype_even_when_routed_builder`).

## Re-entry condition

The plan that implements `oq-0047` (*"YES — `ftype` BECOMES THE ROUTING AXIS. Option (b)."*)
inherits this reconciliation rather than re-deriving it: when the template and `CLAUDE.md`
carry **one** authoritative set, `BUILDER_FTYPES` collapses to that set's builder side and this
finding's three-name union is retired. `bp-136` §9 non-goal 4 forbids sweeping the template
here, so nothing about that ruling is implemented by this plan.

## Routing

`spec-fidelity` → the builder resolved, annotated here and in
`docs/build-plans/bp-136/journal.md`, and continued.
