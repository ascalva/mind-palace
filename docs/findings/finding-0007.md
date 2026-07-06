---
type: finding
id: finding-0007
status: promoted
ftype: discovery
origin_plan: null            # surfaced in owner–orchestrator design review, not a build session
route: orchestrator
created: 2026-07-05
updated: 2026-07-05
links:
  - docs/design-notes/agent-workflow.md (promoted → amendment A4)
  - docs/templates/build-plan.md (deliverable of the installing plan)
warrant_for: A4
resolution: promoted → agent-workflow.md amendment A4
---

# finding-0007 — Build-plan template is thinner than the plans we write by hand

## Observation

A pre-existing hand-written build prompt for the supersession-edge work
(edge model, blessing gate, the `derived_from` grounding correction) was
surfaced during design review. Compared against the bootstrap-era template
(`docs/templates/build-plan.md`, as produced by BP-000), the hand-written
prompt was consistently and materially richer. It carried, by default, several
disciplines the template did not require:

- a **phased investigate → reconcile → plan** structure that grounds the plan
  before any implementation, and stops before implementing;
- **`path:line` citations** for every claim about current code state, with an
  explicit instruction to say "the code does not settle this" rather than infer;
- a **named falsifier per item**, distinct from the acceptance test (acceptance
  says "it works"; the falsifier names the observable that would show the
  approach is wrong);
- the **math carried explicitly**, each object with its three-clause field-guide
  entry (what it measures, what makes it valid, what would show it is not
  earning its place);
- **banner-on-correction / cross-reference-on-extension** discipline for doc and
  code drift — never silent replacement;
- **dependency edges and parallelizable marking** across items;
- **blast-radius ordering** (read-only sensing → reversible writes →
  irreversible effects).

The template was validated on bootstrap plans, which are unusually
self-contained and unusually well-specified (the whole design was in hand). It
was never exercised on a real domain plan, where code and notes have drifted and
must be grounded before building. The gap is therefore expected — but load-
bearing, because the immediate next work (provenance migration, then the
supersession work itself) is exactly the design-reconciliation kind the richer
form serves.

## Why it matters

The template is the load-bearing part of the design→build phase: it is the
capability a builder is handed and the artifact the owner approves. A template
thinner than what the work actually needs means either the owner hand-writes the
rigor each time (the discipline lives in transcripts, not the record — the exact
failure mode the workflow exists to kill) or the builder proceeds under-grounded.

## Open decision resolved by promotion

Two resolutions were considered:

1. **Two tiers** — a lean template for mechanical plans, a heavy
   "design-reconciliation" template for reasoning-spine work.
2. **One richer template**, with sections that do not apply marked
   `N/A — <reason>` rather than silently omitted.

Resolved to (2). A two-tier scheme forces a routing decision at graduation and
risks under-grounding a plan mistyped as trivial; N/A-marking gives the same
relief without the fork, and the explicit N/A is itself an accountability act
(the author considered the section and judged it inapplicable, on the record).

## Disposition

Promoted → `agent-workflow.md` amendment **A4** (owner-ratified at the blessing
gate). A4 upgrades the single build-plan template to the investigate → reconcile
→ plan form, upgrades the `graduate` skill to a grounded planning pass (reads
code, grounds claims with citations, proposes reconciliation, emits a `proposed`
plan approved item-by-item, implements nothing), and upgrades the `build-plan`
skill to the richer template semantics. The template file and the two skill
updates are installed by a dedicated build plan (the last plan written against
the old template; it installs the new one — self-hosting, as with BP-000).
