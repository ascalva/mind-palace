---
type: finding
id: finding-0102
status: resolved
created: 2026-07-17
updated: 2026-07-18
links:
  - docs/design-notes/core-graph-instruments.md   # the P1 principle this violates (named there §2 P6, deliberately NOT folded in)
  - core/dreaming/shadow.py                        # the violating module
  - eval/drift.py                                  # the imported LOGIC (drift_from_report, load_drift_config)
  - eval/golden.py                                 # the imported golden evaluation surface
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: resolved 2026-07-18 (triage) — see the Triage resolution section below
---

# `core/dreaming/shadow.py` imports eval LOGIC — the P1 boundary's other open violation

## What
The session-26 boundary audit (performed for dn-core-graph-instruments) found that
`core/dreaming/shadow.py:50-58` imports **logic**, not just the readings sink:
`eval.drift.{DriftConfig, drift_from_report, load_drift_config}`, `eval.golden` (several
names), and `eval.harness.registry` — core depending on eval's drift computation and golden
evaluation machinery. This is distinct from the tolerated readings-**sink** imports
(`core/temporal/spine.py:97`, `core/ops_view.py:43`, `shadow.py:59,260` →
`eval.harness.store` types), which dn-core-graph-instruments §2 P6 parks as writes-out, not
math-in.

## Why it matters
Under P1 (core self-containment: core never imports eval for mathematics/logic) this is the
remaining inward arrow. Two coherent resolutions, pointing opposite directions: (a) the
drift/golden-evaluation logic is core vocabulary → relocate it core-side; or (b) `shadow.py`
is itself a mis-homed *instrument* (a grading pass living in core) → relocate it eval-side.
The symmetric ambiguity is exactly why this was NOT folded into the bp-065 re-home — it is a
different subsystem and a different design question, and touching the shadow/drift/golden
surface brushes the foundation denylist's neighborhood (golden is owner-sacred).

## Re-entry condition
Owner appetite post-bp-065: a dedicated design pass ruling (a) vs (b), graduating into its
own plan. Until then the imports stand as a documented, named exception to P1 — grandfathered,
not licensed for imitation (new code may not cite it as precedent; P6's standing rule binds).

## Routing
`design` discovery → orchestrator (owner-batched via a future oq once bp-065 lands; not
blocking anything now). Surfaced by the orchestrator's boundary audit, session-26.

## Triage resolution (2026-07-18)
SUBSUMED by finding-0103 — `shadow.py → eval.{drift,golden}` is one of the 16 machinery reaches in the core-self-containment cleanup program. The ratchet test counts it; it inverts in a bp-069+ plan. Closed as subsumed.
