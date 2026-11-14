---
type: finding
id: finding-0273
status: resolved
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/build-plans/bp-136/plan.md
  - docs/build-plans/bp-135/plan.md
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
  - scripts/autopilot_halt.py
ftype: spec-fidelity
origin_plan: bp-136
route: builder
resolution: conservative fallback applied and stated in bp-136 (gate identity as the layer, `serious` halts immediately); the residual gap needs a `layer:` key in bp-135 §6's schema or one clarifying sentence in §2.5
---

# H2's "intent-level vs mechanism-level" is only half-determinable from `bp-135` §6's audit record

## What

`bp-136` Item 11's named falsifier asked whether H2's intent-vs-mechanism distinction can be
made from an audit record's fields. Drilled against `bp-135` §6's pinned schema. The answer is
**a split**, not a yes or a no:

**Determinable.** The record carries `gate: A | B`, and §2.5's table *defines* Gate A as the
**intent-fidelity** gate and Gate B as the **mechanism** gate. So a Gate A dissent is
intent-level by the gate's own definition — that is a field of the record, not a guess.

**Not determinable.** §2.5's Gate B clause reads: *"A second CONCERNS, **or any intent-level
CONCERNS** (work exceeds the capsule), halts."* That asks for a layer distinction **within**
Gate B, and no field of `bp-135` §6's front matter carries it. `verdict_artifact` says
`clean|concerns|serious`; `verdict_record` says `accurate|overstated|misleading`. Neither says
*at what layer*.

The consequence is that §2.5's "one remediation cycle" rule cannot be implemented exactly as
specified: an auditor who finds at Gate B that the work exceeds the capsule has an intent-level
concern that the record renders indistinguishable from a mechanism-level one, and the
classifier would grant it the remediation cycle §2.5 says it must not have.

## Why it matters

The remediation cycle is the one place §2.5 lets an unattended run *continue past a dissent*.
Getting its boundary wrong is the difference between "autopilot fixes a mechanism nit and
carries on" and "autopilot remediates its own misreading of the owner's intent" — which is goal
origination (non-goal 3), the thing the whole design is arranged to prevent.

## Resolution (builder, `bp-136` Item 11) — the conservative fallback, stated not guessed

Per `bp-136` §10, the fallback is applied and **stated**, never a guess at layer:

| record | classifier |
|---|---|
| Gate A, any non-clean verdict | **H2 immediately** — intent-level by the gate's definition |
| any gate, `verdict_artifact: serious` | **H2 immediately** — a `serious` verdict is not a one-remediation-cycle matter under the ruled two-axis vocabulary |
| Gate B, `verdict_artifact: concerns` | **H2 iff `remediation_cycles_used >= 1`** — the first is the one cycle §2.5 grants |
| any record with an illegible `gate` or `verdict_artifact` | **H0** — an illegible verdict is an undetermined one |

Two residual gaps, recorded rather than papered over:

1. **An intent-level `concerns` raised at Gate B still gets the remediation cycle.** The
   `serious` route is the only escape hatch, and it depends on the auditor choosing `serious`
   rather than `concerns` for a capsule-exceeded finding. That is a convention, not a mechanism.
2. **`verdict_record` is not consumed by any halt condition.** `bp-136` Item 11's acceptance
   names `verdict_artifact` only, so a record verdict of `misleading` beside an artifact verdict
   of `clean` currently does **not** halt — arguably wrong, since "the record misrepresents what
   was audited" is exactly the kind of thing an unattended run must not proceed past.

## Re-entry condition

Either of, whichever lands first:

- **`bp-135` §6's schema gains a `layer: intent | mechanism` key** (required, no default), and
  H2 reads it directly. This is the mechanical fix and it is cheap — one front-matter key and
  one body prompt in the audit-record template; or
- **§2.5 gains one clarifying sentence** saying that a Gate B auditor who finds the work exceeds
  the capsule must record `serious`, not `concerns` — which turns gap 1 from a convention into
  a stated rule that the record's own vocabulary enforces.

Whichever lands should also rule on gap 2 (whether `verdict_record` participates in H2).

## Routing

`spec-fidelity` → the builder resolved for `bp-136`'s purposes (the fallback is implemented and
tested: `test_h2_fires_immediately_on_a_gate_a_dissent`,
`test_h2_permits_the_one_gate_b_remediation_cycle`, `test_h2_halts_on_a_second_gate_b_concerns`,
`test_h2_halts_immediately_on_a_gate_b_serious_verdict`, `test_an_illegible_audit_record_is_h0`),
annotated here and in the journal, and continued. The schema change itself belongs to `bp-135`
or its successor — `scripts/audit_record.py` and the audit template are outside `bp-136`'s
write_scope.
