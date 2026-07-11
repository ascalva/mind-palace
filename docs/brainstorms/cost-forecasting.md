# cost-forecasting

Owner direction (2026-07-11, chat): cost tracking should grow into FORECASTING — "like
real JIRA with epics, features, and stories, we can optimize based on estimated cost and
based on models used."

## 2026-07-11T19:30:00Z (captured)

```capsule
topic: cost-forecasting
date: 2026-07-11

decisions:
  - Actuals first (already ruled): every delegated build's measured usage (tokens, tool
    calls, duration, model) is recorded in its SEAL entry (delegate + context-economy
    skills, encoded 2026-07-11).

open_questions:
  - Estimates: should the build-plan template gain an estimated-cost field (tokens by
    tier) set at graduation, so seals produce estimate-vs-actual calibration?
  - Hierarchy mapping: design note ≈ epic; build plan ≈ story; item ≈ task. Does the
    forecast roll up at the note level (what did the type plane COST end to end)?
  - Model-mix optimization: with per-plan actuals by model tier, choose the cheapest
    tier whose falsifier-pass rate holds — measurable after ~2 weeks of seals.
  - Reporting surface: /triage monthly cost table? The site's what's-new? PROGRESS?

parked:
  - decision: template change (estimated-cost field)
    default: seals-only actuals accumulate; no template change yet
    re_entry: two weeks of seal data exist, or the next /graduate wants to estimate

next_steps:
  - Accumulate seal actuals (bp-008 onward — first seal under the rule).
  - At re-entry: propose the template field + a tiny cost report generator (reads seals).

references:
  - .claude/skills/context-economy/SKILL.md
  - .claude/skills/delegate/SKILL.md
```

---

## 2026-07-11 — cross-layer parallel: estimate-vs-actual as ONE calibration primitive (owner insight)

Owner observation: the orchestrator's per-plan cost ledger (`cost: {estimate, actual}` on
build plans — first live pair: bp-011 = **0.47×** a 350k-token estimate) and the CORE's own
context/complexity estimation (the scheduler's pre-admission resource estimate; Track H
reasoning-complexity) are the **same primitive at two layers** — a self-calibrating cost
model: *predict → execute → measure → update the predictor.* Different models, but both now
accumulate estimate-vs-actual over time, so both can learn best practices from the history.

**What transfers vs what doesn't:**
- *Transfers* — the LOOP and its methodology: binning predictions by task-SHAPE
  (grind / core-discipline / design), the sample threshold before recalibrating, regime-shift
  detection, and the discipline of NOT retro-tuning off a single point (the bp-011 seal
  explicitly refused to retune from one 0.47× datapoint).
- *Does NOT transfer* — the units / cost-function: LLM tokens (orchestrator) vs
  memory-GB / context-windows / compute (core). Same loop, different objective.

**Concrete hooks for a design pass:**
1. Make the **graduate skill's session-SIZING heuristic data-driven from seal history** — the
   orchestrator's plan-sizing LEARNS from its own ledger, exactly as the core's scheduler
   learns from its estimates. Today sizing is a static rubric; ~2 weeks of seals (the parked
   cost-forecasting report generator is the seed) could make it empirical.
2. Both planes feed the **evolution study's economics axis**: bp-011/012/013 make CODE
   observable-as-data; the cost ledger makes WORK observable-as-data; finding-0034 adds a CI
   cost-plane. The system accruing estimate-vs-actual across multiple planes is the Ouroboros
   pattern (self-observation) made literal.
3. Open question: should the two estimators share MACHINERY (one calibration lib, parametrized
   by cost-function) or just the PATTERN (independent impls, common methodology)? Sharing
   machinery risks coupling the workflow layer to core; sharing only the pattern keeps them
   decoupled but duplicates. **Weigh against non-negotiable #2/#3 — the workflow layer must not
   reach into sealed core.** Likely answer: share the pattern, not the code.

Status: design-tier idea, parked for a Fable/xhigh design session (surfaced during supervision).

---

## 2026-07-11 — the calibration data as a SELF-SENSOR: proprioception for the observing agent (owner)

Owner leap: the estimate-vs-actual data isn't only calibration input — it's a **sensor
stream**, and what it senses is the AGENT ITSELF over time. So the sensor taxonomy gains an
axis:
- **exteroceptive** sensors — biometric (the owner's body), code (bp-011/012's φ_code):
  sensing the WORLD.
- **interoceptive / proprioceptive** sensor — the agent sensing its OWN operation (cost,
  estimation-error, tool-use patterns, session shapes) over time.

**Why it's elegant, not a bolt-on:** it rides the EXACT seam bp-012 is building right now
(`SensingHandoff → collect → OBSERVED store`). A self/operational sensor is the THIRD instance
through that seam (biometric, code, self) — which VALIDATES bp-012's core bet that the seam is
sensor-agnostic. The design note should note the seam was built to generalize; the self-sensor
is its confirming third case.

**Why "over time" is load-bearing:** self-sensing is the MECHANISM behind the previous
capsule's "learn best practices over time." Longitudinal self-observation IS how the estimator
recalibrates — the agent watches its own competence evolve. Direct tie to the evolution study
(the system studying its own evolution — the Ouroboros name made literal).

**The discipline that keeps it safe (no runaway self-reference):**
- The OBSERVED stratum is passive / write-side — the daemon does NOT consume observations yet
  (finding-0020 honesty). Self-observations ACCUMULATE as data without an automatic feedback
  loop; recalibration stays a deliberate, gated step. That's what prevents observing-the-
  observing regress.
- Same firewall as any observation: OBSERVED provenance, mirror-opaque, corpus-side (reset
  target). "Model advises, code acts" — the self-sensor is CODE projecting telemetry, not the
  model introspecting unboundedly.

**Open design questions:** own store (`agent_observations`) vs a payload type on the existing
seam? What exactly is observed (start narrow — the cost ledger already exists as structured
data — then tool-use histograms, session shapes, Stop-gate/finding rates)? Where's the precise
line between healthy self-observation and infinite regress (the passive-stratum answer is the
first cut)?

Status: design-tier; generalizes the cost-forecasting thread into a sensor-architecture
question. Cross-ref: `code-observation-projection.md` (the seam), the evolution study. Park for
a Fable/xhigh design session.
