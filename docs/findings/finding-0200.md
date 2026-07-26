---
type: finding
id: finding-0200
status: routed
created: 2026-07-25
updated: 2026-07-26
links:
  - docs/build-plans/bp-105/plan.md
  - .claude/skills/delegate/SKILL.md
  - .claude/skills/context-economy/SKILL.md
ftype: spec-defect       # blocker | spec-defect | question | discovery
origin_plan: orchestrator
route: orchestrator
resolution: routed → owner (oq-0048); the filed diagnosis is TOO NARROW — deferred sealing defeats delegated builds too
---

# The cost ledger can only see delegated work — in-session builds seal with a hole

> **Triage 2026-07-26 (session-52) — batched to `oq-0048`, and the filed diagnosis is too narrow.**
> The in-session/delegated split is **not** the operative cause. **bp-108 was a delegated worktree
> builder and still sealed `tokens: unmeasured`** — because the completion notification's figure was
> never carried into the next session's resume brief (`bp-108/plan.md:23-30`). bp-115 was also
> delegated, got its token figure, and still sealed **both** deltas `unmeasured` (`:26-35`). So
> **factor 2 (deferred sealing) defeats delegated builds too**, and a fixer aimed at the in-session
> half would miss it.
> No convention has landed in either governing skill: `grep "in-session|unmeasured|session_delta|
> week_delta"` over the delegate and context-economy skills → **zero hits**; both assume the
> notification figure is available. **Seven plans now read `unmeasured`** (bp-006, 012, 105, 108, 110,
> 115, 119).
> **Why it matters:** the delegate skill's pre-flight budget gate spawns only if
> `padded_estimate ≲ available`, and the pad is calibrated from this ledger's own estimate/actual
> pairs — so the holes degrade the gate that protects every future delegation.

## What
The enriched `cost.actual` block (`model` / `tokens` / `ratio` / `session_delta` /
`week_delta`) is fed by **the completion notification's harness-measured usage**. That
notification exists only for a **delegated** agent. A plan the orchestrator builds
in-session at root produces no per-plan accounting, and `/usage` reports only
per-session and per-week *aggregates* that cannot be attributed back to a single plan.

Surfaced concretely at bp-105's seal (session-49). bp-105 was built in-session in
session-47, sealed two sessions later. By seal time the session-47 boundary reading was
gone, so `tokens`, `ratio`, `session_delta`, and `week_delta` were all recorded as
`unmeasured`. Compare bp-103 and bp-104, both delegated, both carrying exact figures
(`174,551` / `316,419` tokens, 113 / 153 tool calls, wall-clock, week deltas).

Two compounding factors, not one:
1. **No per-plan signal for in-session work** — the structural half.
2. **Deferred sealing** — even the coarse session-boundary aggregate decays once the
   session ends. A seal written in the building session could at least have bracketed
   `/usage` before and after.

## Why it matters
The `ratio` field is not decoration. The delegate skill's **pre-flight budget gate**
spawns a worker only if `padded_estimate ≲ available`, and the pad is calibrated *from
the ledger's own estimate/actual pairs* — the margin was refined from measured overruns
(bp-020 1.50×, bp-026 1.56×, later bp-103 2.18×, bp-104 1.98×). A ledger that
systematically records only delegated builds is a **biased sample**: it calibrates the
pad exclusively on the work whose shape differs most from in-session work.

The seal-cost convention also holds that `ratio` tracks **plan pinning** (well-pinned
~0.5×, loose ~1.5×, docs ~1×). That hypothesis is only falsifiable if well-pinned
in-session builds actually get measured. bp-105 was well-pinned and would have been a
data point for it; instead it is a hole.

The failure mode is quiet: an `unmeasured` seal looks like a formatting lapse, so the
tempting repair is to *estimate* the figure from the pinning heuristic. That would be
strictly worse than the hole — it would feed a **prediction back into the ledger as an
observation**, and the next pad would be calibrated against the very heuristic it is
supposed to test. bp-105 was sealed with `unmeasured` deliberately for this reason.

## Re-entry condition
Not parked — no build is blocked on it. It bears on the *next* seal of an in-session
build, whichever plan that is.

## Routing
`orchestrator` (`direction`): this is a convention/process question, not a codebase
defect. Two candidate shapes, both cheap, neither obviously right:

- **(a) Bracket at build time.** The orchestrator probes `/usage` at the start and end
  of an in-session build and records the delta. Cheap, no new machinery, but it measures
  the *session*, not the *plan* — contaminated by any other work in that session, and it
  requires the seal to be written in the building session (which bp-105's two-session
  deferral shows is not the norm).
- **(b) Declare the field N/A by construction.** Mark in-session builds `tokens: n/a
  (in-session)` as a first-class ledger category rather than a gap, and calibrate the
  delegation pad *only* from delegated pairs — which is what it is actually used for.
  Honest, zero cost, but permanently abandons the pinning-ratio hypothesis.

A third option — per-plan accounting for in-session work — is not available from inside
a session; the harness does not expose it.

Recommend **(b)** with an explicit note that the pad is delegated-calibrated, unless the
pinning-ratio hypothesis is something the owner wants kept alive, in which case **(a)**
for well-pinned in-session plans only.
