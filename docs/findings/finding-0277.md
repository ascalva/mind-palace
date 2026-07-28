---
type: finding
id: finding-0277
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/brainstorms/study-not-product.md
  - docs/design-notes/dn-typed-workflow-registry.md
  - eval/effector_drift.py
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The drift instrument is act-based: it cannot distinguish a warranted change from decay

## What

The system measures drift as a defect signal (the A1 drift gauge, `eval/effector_drift.py`,
the blast-radius axis): "the thing moved away from where it should be." But drift has no
sign. The instrument measures the *magnitude* of change and has no notion of whether a
**warrant** accompanied the change — so a deliberate owner ruling and an unauthorized decay
read identically [GROUNDED docs/brainstorms/study-not-product.md:236-268; the owner flagged
the gap himself: "a drift, if you will (only being cheeky with 'drift', but it has future
impact)"]. The 2026-07-27 reframe (act-based → sign-based, `dn-typed-workflow-registry`)
was assumed to govern *enforcement*; this finding is that it reaches the **measurement**
layer too: the drift gauge is act-based — it observes that state changed, exactly as a hook
observed that an act occurred.

[INFERENCE — the gauge's current semantics were read from its purpose, not from its source
this pass; verify against the implementation before building anything.]

## Why it matters

An instrument that cannot see warrants produces its loudest false alarms exactly when the
project is most alive — during a deliberate reframe — and will keep reporting the owner's
best decisions as defects. Its silence is equally uninformative, since a system nobody is
thinking about does not drift either.

The fix direction is the night's fix applied one layer up: **warrant-aware drift**
distinguishes degradation from decision. The machinery already exists — `supersedes` /
`superseded_by`, the `warrant` frontmatter field, the erratum relation (`bp-129`), and,
once `dn-typed-workflow-registry` lands, a signed transition log recording who authorized
what, when. Drift against a warranted baseline is *change*; drift against an unwarranted
one is *decay*.

Question owed to the design layer: what does the gauge do when the baseline itself was
deliberately moved?

## Re-entry condition

Not parked against a criterion; routes at the next `/triage`. Re-enters design when the
owner rules on whether warrant-awareness amends the drift gauge's spec (a design-note
supersession or a revision under `dn-typed-workflow-registry` §2.10) or mints a new
instrument.

## Routing

`discovery`, bearing on design → orchestrator. Design-changing: proposes an amendment to
the drift instrument's semantics, warrant-linked to this finding.
