# Brainstorm — Self-sensing: the agent as a sensor of itself (proprioception)

> Spun out of `cost-forecasting.md` on 2026-07-11 (owner + orchestrator, supervision session).
> The thread outgrew cost-forecasting; this is its consolidated, graduate-ready home.
> Owner's distillation: **"the projection maps FROM agents interpreting results OVER TIME."**

## The arc, in one line

The orchestrator's estimate-vs-actual cost ledger is not merely calibration data — it is the
first stream of a SELF-SENSOR: the agent observing its own operation and its own way-of-seeing,
projected onto the observed stratum, whose supersession chain records how that view evolves.

## 1. The seed — estimate-vs-actual as a calibration primitive at two layers

The orchestrator's per-plan `cost: {estimate, actual}` and the CORE's own context/complexity
estimation are the SAME primitive — a self-calibrating cost model: predict → execute → measure
→ update the predictor. The LOOP + methodology transfer (bin by task-shape, sample thresholds,
regime-shift detection, DON'T retune off one point — bp-011's 0.47× is one datum, not a
recalibration). The UNITS don't (LLM tokens vs memory-GB/compute). First live pair: bp-011.

## 2. The leap — that data is a SENSOR STREAM whose subject is the agent itself

Sensor taxonomy gains an axis:
- **exteroceptive** — biometric (the body), code (φ_code, bp-011/012): sensing the WORLD.
- **interoceptive / proprioceptive** — the agent sensing its OWN operation (cost, estimation-
  error, tool-use patterns, session shapes) over time.

## 3. The generalization — it rides the seam bp-012 is building

A self-sensor would be the THIRD stream through the exact `SensingHandoff → collect → OBSERVED
store` seam (biometric, code, self) — which VALIDATES bp-012's core bet that the seam is
sensor-agnostic. Not new infrastructure; a third instance of the one bp-012 lands.

## 4. The deep turn — projecting the WORLDVIEW, and observing its evolution

The interpreter IS the view. `code-observation-projection.md` §2.2: *re-interpretation =
versioned supersession at the same identity key.* So when the agent's way-of-seeing changes,
re-projecting the SAME source under the NEW view SUPERSEDES the old observation — and **the
supersession chain is the fossil record of the changing worldview.** The stratum then records
not "what the world was" but "how the agent SAW it, when" — an **epistemology-over-time.** For
the self-sensor: how the agent's model of ITSELF evolved. This is the owner's "projection maps
from agents interpreting results over time," exactly.

## 5. The safety argument — why self-reference does not run away

The OBSERVED stratum is passive / write-side — the daemon does NOT consume observations yet
(finding-0020 honesty). Self-observations ACCUMULATE as HISTORY, not a live feedback loop; the
supersession chain is a record, not a reflex. That passive-stratum boundary IS the line between
healthy self-observation and infinite regress. Same firewall as any sensor: OBSERVED provenance,
mirror-opaque, corpus-side; "code projects telemetry, the model doesn't introspect unboundedly."

## 6. Why it's buildable, not philosophy

It's the EXISTING interpreter/supersession primitive, not new machinery. bp-011 (docstring
ledger), bp-012 (store + sibling seam + §2.2 interpreter contract), bp-013 (reference edges)
already build the substrate. The self-sensor is a SMALL follow-on: point a proprioceptive sensor
at the cost ledger (already structured data) through the same seam.

## 7. Open design questions (for the design note)

- Own `agent_observations` store vs a payload type on the existing seam?
- What to observe first? Start narrow — the cost ledger — then tool-use histograms, session
  shapes (model/effort/duration), Stop-gate/finding rates.
- Where precisely is the regress line? (Passive-stratum is the first cut.)
- Does the orchestrator's cost ledger literally BECOME the first self-sensor stream (dogfood)?
- Calibration shared as PATTERN not machinery — non-negotiable #2/#3, the workflow layer must
  not reach into sealed core.

## Status & cross-refs

**Promoted 2026-07-12 → `docs/design-notes/self-sensing.md` (`dn-self-sensing`, `status:
draft` — ratification is the owner's hand).** The note answers open-question #1 from
bp-012's recorded Q1 precedent (sibling seam, own store), licenses the cost ledger as the
only initial stream, and names the interpreter-version supersession gap (B-a) the
worldview record requires.

Design-tier, graduate-ready → a design note ("self-sensing / proprioceptive projection").
Cross-ref: `code-observation-projection.md` (the seam + §2.2 interpreter contract),
`cost-forecasting.md` (origin + the cost-ledger half + the parked report generator), the
evolution study (add an epistemology axis alongside economics), `finding-0034` (a third
cost-plane: CI).

---

## 2026-07-12T17:54:25Z (captured) — owner read of the draft note: stateless projector, multi-stream expansion, the weaving hypothesis

```capsule
topic: self-sensing
date: 2026-07-12

decisions:
  - (owner, confirming the draft note's regress line) the sensor agent is STATELESS — it
    reads sensor data deterministically and projection-maps onto the observed stratum;
    the database is durable retention of readings ("in case we need that data in the
    future"), NOT working state the next run consumes. "The role of the agent is to
    projection map."
  - S1 stands as drafted — start with just the cost data.
  - expansion intent (owner): eventually projection-map MORE of the code structure over
    time — cost, documentation, scope-of-changes — so related planes accumulate in the
    stratum. The weaving hypothesis: "the more related data that we feed, the higher
    chance there's some thread that can be found that weaves through the data, or a set
    of these fibers and supersession edges" — and then see what the dreamer can reason
    about that.

open_questions:
  - the weaving reasoner's routing: per the standing firewall it lands as a Track-D /
    correlator-class consumer over ObservedView emitting INTERPRETED proposals
    (dreamer-proposed authority) — the mirror-side dream path cannot read observations
    (mirror-opacity stands). Confirm at Track D's design pass that this is the intended
    landing for "what the dreamer can reason about."
  - stream placement: documentation-over-time (doc-coverage precursor already in the
    snapshot ledger) and scope-of-changes/churn are φ_code-plane git/AST facts;
    session shapes / tool-use are φ_self-plane. Both planes share the commit_sha time
    coordinate — the join geometry the weaving consumer will need.

parked:
  - decision: streams beyond S1 (documentation, scope-of-changes, session shapes, …)
    default: not licensed (dn-self-sensing PD-a)
    re_entry: per stream — its facts exist as committed artifacts or git facts, plus a
      small additive plan the owner blesses
  - decision: the weaving consumer (multi-stream thread / fiber+supersession reasoning)
    default: no consumer (dn-self-sensing §1.2 — substrate only)
    re_entry: Track D's design pass; this capsule is its charter seed

next_steps:
  - fold the owner-named candidate streams + the shared-time-coordinate point into
    dn-self-sensing (§2.3/§2.6/§5) before the ratification read (same session as capture).
  - B-a needs no separate design note: V2 audits the gap; graduation pins the
    interpreter-version identity mechanics (see the session's chat answer).

references:
  - docs/design-notes/self-sensing.md
  - docs/design-notes/code-observation-projection.md
  - docs/design-notes/observed-iot-and-cross-source-synthesis.md
  - docs/findings/finding-0034.md
```
