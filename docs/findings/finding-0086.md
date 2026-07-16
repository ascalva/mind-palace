---
type: finding
id: finding-0086
status: resolved
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/build-plans/bp-043/plan.md
  - docs/build-plans/bp-054/plan.md   # the plan that discharged the owed registration (FB-2)
  - eval/harness/registry.py
  - core/dreaming/shadow.py
  - core/complex/temporal.py
ftype: spec-fidelity
origin_plan: bp-043
route: builder
resolved_by: bp-054   # structural_axes.{frustration,min_conductance} now registered (Inv rows), merged 4ec4cdc
resolution: RESOLVED — the owed registration was discharged by bp-054 (structural_axes.* Inv rows), with name agreement machine-enforced by test (see finding-0093)
---

# `structural_axes.*` readings are written un-registered (E1 registry gap)

## What
bp-043 §3 Q6 + §6 pin the ShadowRunner to write the dream_v2 A2 axes as keyed Readings with
`metric_name = "structural_axes.<axis>"` (e.g. `structural_axes.frustration`,
`structural_axes.min_conductance`) into the E1 eval store. But those metric names are **not
registered** in `eval/harness/registry.py` (bp-042's `_BUILT` set registers `golden_recall`,
`drift_D`, the `f9_*`/telemetry families — not the structural axes). Meanwhile Item 6's own
invariant reads "every registered metric referenced by name (no ad-hoc metric — E1's registry is the
namespace)". `eval/harness/registry.py` is **outside bp-043's `write_scope`**, so a builder cannot
register them here.

## Why it matters
`EvalResultsStore.put` does **not** gate on registration (the DDL comment "MUST be a registered
registry key" is a discipline, not an enforced check), so writing `structural_axes.*` does not fail
at runtime and the A/B tables (E4/bp-044) can read them. But the readings sit slightly outside the
"single metric namespace" contract until the family is registered — a report that fail-closed-resolves
every metric via `registry.get(...)` would raise on them.

## Resolution (builder-resolved, this session)
Written as pinned (§3 Q6/§6 are the authority; the guardrails `drift_D`/`golden_recall` ARE resolved
via `registry.get(...)` by name, honoring the invariant for the registered set). The runner degrades
to *not-captured* (logged, §2.8) when no A2 snapshot is available, never fabricating. The durable fix
is owed to a follow-up with `eval/harness/registry.py` in scope: register a `structural_axes.*`
family (source_instrument = catalog row 6 / `core/complex/temporal.py`; `type_tag="Inv"`;
`guardrail_eligible=False` — they feed drift's A2 axes, they are not themselves a guardrail).

## Routing
`spec-fidelity`, builder-resolved + annotated — not a blocker, no design decision owed. Flagged to the
orchestrator only so the registration follow-up is batched (a natural rider on E4/bp-044 or a small
bp-042 amendment), not lost.
