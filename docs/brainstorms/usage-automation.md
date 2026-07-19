# Brainstorm — usage automation: the orchestrator self-serves the budget gate

> Captured by the orchestrator from an owner mid-session steer (2026-07-19, fable session-33, during
> the bp-072 mint). Owner's seed, verbatim: *"small thought on automation: you could also trigger a
> one-action claude code command, where the only thing is "/usage", so you can always keep tabs on
> how spend and usage is looking, which will help better with planning work and you can predict
> sizing and run the check yourself, validate, bookkeep in an automated way"* — refined: *"I mean
> that you trigger a new session where the starting command is just the usage command, record, and
> exit."*

## 2026-07-19 UTC (session-33)

### The mechanism, verified in-session

Probed live during capture: `claude -p "/usage"` (headless print mode) renders the FULL usage screen
as plain parseable text and exits 0 — current-session %, week all-models % (the gate figure), week
Fable %, reset times, plus the behavioral contribution lines. It is a built-in screen render: no
model turn runs, so the disposable one-shot session is itself ~free. This removes the one manual
step in the pre-flight budget gate — until today the owner relayed `/usage` by hand
(delegation-budget-discipline); now the orchestrator spawns the one-shot, records, and exits, on its
own schedule.

```capsule
topic: usage-automation
date: 2026-07-19

decisions:
  - The orchestrator self-serves usage checks: spawn a disposable one-shot session
    (`claude -p "/usage"`), record the figures, exit. No owner relay.
  - Where it binds (process rule, effective immediately, no build needed):
    (1) the PRE-FLIGHT BUDGET GATE before any delegation spawn — probe, pad ~1.6x,
    spawn only if it fits; (2) at SEAL time — week_delta in cost.actual becomes
    measured, not relayed; (3) sizing calibration — estimate-vs-actual validated
    against probed numbers, closing the forecasting loop.
  - Memory delegation-budget-discipline updated to the self-serve mechanism.

parked:
  - decision: scheduled usage heartbeat (cron) + a standing usage-ledger file
    default: on-demand probing at gates and seals only; bookkeeping stays in seal
      cost.actual blocks (seal-cost-fields shape)
    re_entry: on-demand probing proves insufficient for planning (e.g. a worker
      dies mid-run on a limit the gate would have caught with a mid-flight check),
      or the owner wants trend curves — then a papercut plan mints the ledger.

open_questions:
  - Does the one-shot itself consume measurable budget at scale? (Appears ~free —
    built-in render, no model turn observed; unverified over many invocations.)
  - The screen text is presentation, not schema — parsing keys on line shapes
    ("Current week (all models): N% used"). If the format shifts, the probe
    degrades; fail-closed rule: an unparseable probe means ASK the owner, never
    guess a budget.

next_steps:
  - None to build. The process rule + memory update land with this capture; the
    parked ledger waits on its re-entry.

references:
  - memory: delegation-budget-discipline    # the gate this automates (was: owner relays /usage)
  - memory: seal-cost-fields                # the bookkeeping shape the probe feeds
  - .claude/skills/context-economy/SKILL.md # session typing + the usage ledger concept
  - docs/build-plans/bp-073/plan.md         # cost.actual precedent block (the enriched shape)
```
