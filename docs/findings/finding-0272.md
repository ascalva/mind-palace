---
type: finding
id: finding-0272
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/build-plans/bp-136/plan.md
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
  - docs/findings/finding-0193.md
  - docs/inbox/owner-questions.md
ftype: design
origin_plan: bp-136
route: orchestrator
resolution: null
---

# Measured: the conservative H1 reading halts on 93% of recent findings — the honest cost of the `oq-0047` gap

## What

`bp-136` Item 10's named falsifier was *"H1 fires on essentially every run because real builders
file `question`/`discovery` findings routinely."* It was drilled against the **real**
`docs/findings/` corpus (read-only) using the shipped predicate
(`scripts/autopilot_halt.BUILDER_FTYPES` + explicit `route: builder`), and it **fires**:

| population | H1 would halt | rate |
|---|---|---|
| the 30 most recent findings (`finding-0241 … finding-0270`) | 28 / 30 | **93%** |
| the whole corpus (243 findings) | 199 / 243 | **82%** |

Breakdown of the 28 halting, by `(ftype, route)`: `(discovery, orchestrator)` 9 ·
`(spec-defect, orchestrator)` 6 · `(design, orchestrator)` 6 · `(codebase, orchestrator)` 4 ·
`(spec-fidelity, orchestrator)` 3. The two that pass are `finding-0244` and `finding-0252`.

⚑ **The most informative row is the last two.** Seven of the 28 carry a *builder-lane* `ftype`
(`codebase` 4, `spec-fidelity` 3) and are nonetheless routed `orchestrator`. So `route:` is
doing the work, and `ftype` and `route` disagree in ~25% of the halting cases — a direct,
measured instance of `finding-0193`'s disjointness, not a restatement of it.

## Why it matters

Three things, in descending order of importance:

1. **The rule was NOT softened**, per `bp-136` §10: *"do not soften the rule on your own
   authority. Ambiguity resolves toward stopping (invariant 7); making autopilot usable by
   loosening its halt list is exactly the drift this note exists to prevent."* The number is
   recorded so the owner rules on it with evidence rather than on a builder's convenience.
2. **93% is not automatically disqualifying, and this finding does not claim it is.** Autopilot's
   envelope is the design-inert QoL class (note §2.2/§2.4), whose runs are expected to file
   **zero** findings — `findings_since_base: []` is the normal case and yields no H1. The
   measured population is what *orchestrator and full-ceremony builds* raise, which is precisely
   the population §2.4 excludes from autopilot. What the number does establish is the sharp
   version of §2.6's own claim: **any** autopilot run that files **any** finding halts, near
   enough. The design says that is correct (*"a low-stakes run that raises a design question has
   left the low-stakes envelope by that very fact"*). The measurement says it is also
   *near-total*, which is a stronger statement than the note makes.
3. **It bounds what `oq-0047`'s implementation buys.** Since `route:` dominates, a plan that
   makes `ftype` the routing axis without also reconciling `route:` on the existing corpus will
   not move this number. Whoever graduates that plan should budget for the sweep, not just the
   template edit.

## Re-entry condition

Owner ruling on either (a) whether a ~90% halt rate over finding-raising runs is the intended
behaviour of H1 — the note's Parked row *"H1 routing vocabulary"* already anticipates this — or
(b) whether the conservative reading should be narrowed once `oq-0047` is implemented and the
corpus swept. Until one of those lands, `scripts/autopilot_halt.py` ships the rule exactly as
§2.4 specifies it, and this finding is the record that the cost was measured rather than
assumed.

## Routing

`design` → the orchestrator. Owner input is needed (this is a question about how strict a
constitutional halt condition should be), so it belongs in `docs/inbox/owner-questions.md`,
timed with `oq-0047`'s implementation plan.
