---
type: finding
id: finding-0225
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - scheduler/queue.py                  # JobQueue.job_budgets — the switch, built and empty
  - config/defaults.toml                # where a [scheduler] section would go (out of bp-109 scope)
  - docs/design-notes/dn-supervision-and-liveness.md   # §4 Wiring — job_budget_s per-kind
  - docs/build-plans/bp-109/plan.md     # §5 write scope, §11 parked default
  - docs/findings/finding-0178.md       # no job budget exists anywhere today
ftype: question
origin_plan: bp-109
route: builder
resolution: null
---

# The lease's ON switch stops at `JobQueue(job_budgets=…)` — no config key reaches it, so nothing
# outside a test can turn a deadline on

## What

bp-109 landed the lease: `claim()` stamps `lease_expires_at = started_at + job_budgets[kind]`, and
`job_budgets` is a `JobQueue` constructor field that is **empty by default** (NULL deadline = today's
behaviour, the §11 parked default, deliberately not a guessed number — finding-0178 / §3 Q7).

The switch exists but nothing turns it. `build_components` constructs the queue as
`JobQueue(path)` and no `[scheduler]` config section exists, so on the live system every claim will
stamp NULL forever, no matter what the owner writes in `config/ouroboros.toml`. The design note's §4
Wiring names the missing piece exactly — a schema'd `[scheduler]` section carrying
`job_budget_s` per-kind overrides — and warns why it must be schema'd rather than merely read:
"unknown sections are dropped silently, bp-102/finding-0174's lesson, so the schema change is part of
the deliverable, not a follow-up".

That work is **outside bp-109's write_scope** (`config/loader.py`, `config/defaults.toml` and
`ops/lifecycle/launcher.py` are all excluded, the last explicitly, per §5), so this is a hand-off
rather than a defect in what shipped. Recording it because "wiring is part of finishing": a
capability whose enable path does not exist is a claim, not a mechanism, and this one is one config
section away from being real.

## Why it matters

Two live consequences if it is lost:

1. **The mechanism is unexercisable outside tests.** Nobody can deskcheck a real deadline, so the
   first time a budget is used in production will also be the first time the stamp is used in
   production.
2. **The next plan may re-invent it.** A builder wiring escalation who does not find `job_budgets`
   will add a second budget source — the duplication class the owner treats as a defect. The reuse
   target is named here so that cannot happen quietly.

Deliberately NOT a blocker, and deliberately not fixed by widening scope: the *value* is a parked
decision with its own re-entry condition (bp-112's escalation, with a measured budget), and wiring a
config path to a value nobody may set yet would ship an inert knob — the exact thing bp-102 dropped
its job-timeout knob to avoid.

## Re-entry condition

Whichever plan first needs a non-NULL deadline — expected to be **bp-112 (escalation)**, per §11's
row "default budget per kind | NULL (no deadline) | bp-112 lands escalation". That plan's write_scope
must include the config loader + `defaults.toml` + the `build_components` construction site, and its
§2 manifest must reuse `JobQueue.job_budgets` rather than adding a parallel budget source. The number
itself must come from measurement (per-kind p50 from the queue's own history, the note's Q3
denominator) or a cited design line — never a default dressed as a guess.

## Routing

`codebase` hand-off → **builder** (the next plan's builder resolves it as part of its own wiring).
No owner input needed: the design note already ruled on the shape (§4), and the value's re-entry
condition is already recorded in bp-109 §11.
