---
type: finding
id: finding-0266
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/plans/bp-128.md
  - docs/findings/finding-0246.md
  - docs/findings/finding-0248.md
  - docs/findings/finding-0252.md
ftype: spec-fidelity
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# A close-gate clause whose only resolution is owner-only fires unboundedly while the owner is away — it must latch

## What

The Stop gate reports each unsatisfied clause **once per turn**. For a clause an agent can
discharge, that is correct and cheap: the agent does the one act, and the clause goes quiet.

⚑ **For a clause whose _only_ resolution is an owner act, there is no such act available from inside
the session.** The clause is therefore re-evaluated, found unsatisfied, and re-reported on every
subsequent turn, for as long as the session runs — each firing costing a turn's worth of context and
attention, and none of them able to change the outcome.

This has now been observed on two different clauses:

- **`(b2)`** — repeated firings within a single session. **Derived (primary):** against the chat
  store, `Stop hook feedback` rows carrying the literal `(b2)` marker cluster **6 in one session**
  (turn indices 109–297), 4 in a second, 1 in a third. ⚑ That is a **lower bound**, not the figure:
  the store's coverage ends at `2026-07-25T03:44Z` because the ingest lane is wedged, so every
  firing after that date is simply absent from it.
- **`(e)`** — the stale-resume-brief clause, over roughly eight days.

⚑ **Marked hop — not re-derived.** The larger figures reported to this seat (**~15+ consecutive
firings on `(b2)` in one session**, and **108 on `(e)` over eight days**) are **secondary**: they
come from session transcript, and they postdate the chat store's coverage window, so they could not
be re-derived here. They are recorded as a hop, not as measurements. The derivable lower bound above
is consistent with them and is the number this finding stands on.

Corroboration for the `(e)` half is independently recorded in `docs/brainstorms/owner-intent-audit.md`
(L-4): the owner gave permission to wipe the resume brief on `2026-07-26T03:16:25Z`; it was not acted
on; clause `(e)` fired **at least seventeen more times** over the following ~24h, until he re-issued
the instruction three times in thirty minutes.

## Why it matters

⚑ **The clause was _correct_ both times.** That is the whole point, and it is what makes this a
design defect rather than a bug report:

> **A correct gate and an incorrect one cost the same when neither can be cleared from inside the
> session.**

The gate's report-rate is therefore **decoupled from its usefulness**. A clause that is right, and a
clause that is wrong, impose an identical unbounded tax the moment the owner steps away — and
"stepping away" is the normal operating mode this system is built for. The cost falls hardest
exactly when the system is supposed to be running unattended, which inverts the intent.

There is a second-order harm worth naming: **a channel that fires constantly gets ignored.** The
same argument the purity lint makes about crying wolf (`a lint that cries wolf gets suppressed —
worse than no lint`) applies to the close gate. Unbounded repetition of a correct clause trains its
reader to skim past clauses that are *not* yet satisfied but *are* dischargeable.

## Candidate remedy

**Latch.** Report once per session, or once per **state change** — not once per turn. A clause that
has been reported, and whose inputs have not changed since, is already known to the session; the
second report carries no information. Concretely, the shapes worth considering:

- latch per clause per session, with the report re-armed only when the clause's own inputs change;
- or a two-tier report: dischargeable clauses keep the current behaviour, owner-only clauses latch.

⚑ This interacts with `finding-0246` (an ordinary nested invocation silently rewrites the marker the
gate reads) and must not be designed independently of it: a latch keyed on session identity inherits
whatever weakness that key already has. If the baseline is not session-scoped, a latch built on it
will silently un-latch for the same reason the gate silently disarms today.

## Re-entry condition

Reopens when the clause-(f) repair is designed — this is **live input to whatever replaces clause
(f)**, and should be read alongside `finding-0248` and `finding-0252`, which give the other two
directions of the same clause family being wrong. Also reopens if any session measures a clause
firing more than three times without an intervening state change. Nothing is blocked today; the
cost is paid in context, not in correctness.

## Routing

`spec-fidelity` → routed to the **orchestrator** rather than to a builder, deliberately. The defect
is in what the gate's specification asks for, not in an implementation's fidelity to it, and no
active plan owns the close-gate clause set. `bp-128` is the nearest home but its charter is the
recency/anchoring defect, not the report-rate; this should inform that plan's successor rather than
be folded into it silently.
