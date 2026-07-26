---
type: finding
id: finding-0228
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/build-plans/bp-110/plan.md                    # §6 pins `job_budget_s: float = 0.0`
  - scheduler/queue.py                                 # JobQueue.job_budgets: Mapping[str, float]
  - docs/design-notes/dn-supervision-and-liveness.md   # §4 Wiring — "per-kind overrides"
  - docs/findings/finding-0225.md                      # the hand-off this discharges
  - core/kernel/config/loader.py                       # SchedulerConfig, as landed
ftype: spec-defect
origin_plan: bp-110
route: builder
resolution: null
---

# bp-110 §6 pins the job budget as a SCALAR, but the field bp-109 built is PER-KIND — landed
# per-kind, because a scalar cannot be expressed in the consumer that already exists

## What

bp-110 §6 pins the `[scheduler]` schema with a scalar:

```python
job_budget_s: float = 0.0          # 0 = no budget (finding-0178's status quo)
```

bp-109 landed the consumer four hours earlier, and it is a map (`scheduler/queue.py:296`):

```python
job_budgets: Mapping[str, float] = field(default_factory=dict)
```

used at `:435` inside `claim()`:

```python
budget = self.job_budgets.get(chosen.kind)
deadline = None if budget is None else _plus_seconds(started, budget)
```

The lookup is **by kind**. A scalar has no expression in it: a single number would have to be
either fanned out over every kind at construction (requiring the config layer to know the full
kind vocabulary, which it does not and should not) or merged with a per-kind map by whichever plan
wires it — and that second source is exactly the "parallel budget source" finding-0225 was filed to
prevent, in the same breath as naming `JobQueue.job_budgets` as the reuse target.

**The design note agrees with the code, not with §6.** `dn-supervision-and-liveness` §4 Wiring
reads: "`job_budget_s` **per-kind overrides**". So the scalar in §6 is a drafting slip in the plan,
not a design position — §6 carried the note's *key name* while dropping its *arity*.

## Resolution taken by bp-110 (`[banner: correction]`)

`SchedulerConfig` landed with

```python
job_budgets: dict[str, float] = field(default_factory=dict)  # kind -> seconds; {} = no budget
```

mapping 1:1 onto `JobQueue.job_budgets`, with `[scheduler.job_budgets]` as its TOML table. The
correction is recorded at the dataclass (`core/kernel/config/loader.py`) and in
`config/defaults.toml`'s section comment, so the next reader meets it where the decision lives
rather than only here.

The scalar was **not** additionally shipped as a global default. That was considered and rejected:
an unconsumable key is an inert knob that *looks* live, and a knob that looks applied but never
took is the precise failure mode the whole "schema the section" requirement exists to prevent
(bp-102 / finding-0174, quoted in the note's own §4). Landing both would also re-create the
two-sources problem on day one. If a global default is ever wanted, it should arrive deliberately,
with a measured value, in the plan that enforces budgets.

Empty map remains the default, so every claim stamps a NULL deadline and behaviour is
byte-for-byte today's — finding-0178's status quo, preserved exactly. bp-110 consumes none of it
(§9: "This plan *defines* their config keys and consumes none of them").

**This discharges the wiring half of finding-0225**: the enable path now exists end to end —
`config/defaults.toml` → `SchedulerConfig.job_budgets` → `JobQueue(job_budgets=…)`. The last link
(the `build_components` construction site in `ops/lifecycle/launcher.py`) is out of bp-110's
write_scope by §5 and remains bp-111/bp-112's, exactly as finding-0225's re-entry condition says.

## Why it matters

Left as pinned, a builder following §6 literally would have shipped `job_budget_s: float`, and the
first plan to actually enforce a budget would have found the key it inherited unusable by the field
it was supposed to feed. The likely repair at that point is the wrong one — add a second budget
source rather than change a key another plan already shipped — which is the duplication class the
owner treats as a defect, arriving by exactly the route finding-0225 predicted.

It is also a small instance of a general hazard worth naming: **§6's job is to pin shapes so a
builder never infers design, which means a §6 pin that contradicts already-built code is more
dangerous than no pin at all** — it converts "check the consumer" into "copy this verbatim". Here
the plan and the code were written within a day of each other by different sessions, and the plan
could not have known.

## Re-entry condition

Nothing is parked. Re-enter when **bp-111 or bp-112 wires the budget** — that plan should take
`SchedulerConfig.job_budgets` as landed and pass it straight to `JobQueue(job_budgets=…)` at the
`build_components` site, and must NOT introduce a second budget source or a scalar fallback
without deliberately superseding this finding. The VALUE remains a parked decision with its own
re-entry condition (bp-109 §11: a measured per-kind p50, never a guess).

If the orchestrator would rather the plan text match what shipped, the §6 block in
`docs/build-plans/bp-110/plan.md` is the one line to correct — a builder may not edit a plan's
pinned interfaces after the fact, so that edit is the orchestrator's.

## Routing

`spec-fidelity` → **builder**. The builder settled it against the code and the design note, which
agree with each other and disagree only with the plan's §6 — no owner input is needed and no design
question is open. Recorded rather than silently redefined because §6 is a *pinned interface* that
bp-111/bp-112 will read, and a pin that changed without a record is how the next plan inherits a
shape nobody chose.
