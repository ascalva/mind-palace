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

---

## 2026-07-12T18:17:58Z (captured) — owner ruling: the edge history is the durable thing; smart vs wise; the erasure thought experiment

```capsule
topic: self-sensing
date: 2026-07-12

decisions:
  - (owner ruling — resolves V2's named escalation candidate, same-day) the edges /
    fibers / supersession chains "are important, so they also need to be durable":
    the edge-and-chain HISTORY is LEDGER-CLASS (reset-guarded), not corpus-class.
    Warrant: unlike readings (re-projectable from git), superseded chains and
    edge-strength series are not re-derivable — the old interpreters no longer exist
    at HEAD — and "the study of how they change over time is the point." Lands in
    B-a's design (dn-self-sensing §2.5/V2). No conflict with the ratified
    code-observation note: its corpus-side call was plan-level (Q4, store docstring),
    made when no chains existed; B-a is what creates them.
  - edge strength is a TIME SERIES, not a scalar: edges are not permanent, they
    fluctuate in strength over time — and the record of that fluctuation is the
    study object.
  - the smart-vs-wise frame (owner): smart = many points of knowledge without the
    subtleties of how they connect; wise = reasoning over the connections and seeing
    useful patterns arise. Structural map: readings/nodes = the knowledge points;
    edge evolution = the wisdom substrate; the weaving consumer is wisdom-hunting.

open_questions:
  - "edges start becoming more durable as utility increases" — a GRADED retention
    policy (durability proportional to demonstrated utility) vs the simple binary
    guard adopted now.
  - the erasure thought experiment (owner): reset edge HISTORY but keep the current
    edge SNAPSHOT — does the system keep flowing in time over the same direction?
    Session answer (folded into the note §2.4): today, behaviorally yes — nothing
    reads the record, but the study loses its baseline; once gated consumers close
    the loop, no — divergence begins at the first history-consuming act
    (recalibration, regime-shift detection are functionals of the record); if edge
    strengths update incrementally, the snapshot is itself compressed history —
    direction is retained but attribution and regime-shift detection are lost (dead
    reckoning: the course fossilizes because course corrections came from the
    record). Erasure-invariance is thus the OPERATIONAL smart/wise line: a merely
    smart system's trajectory is a function of its state; a wise one's is a
    functional of its path. The system as designed starts erasure-invariant and
    gains path-dependence only through deliberate gates.

parked:
  - decision: utility-graded edge durability
    default: binary — history is ledger-class, guarded (the study IS the utility)
    re_entry: a built consumer produces per-edge utility measurements worth
      weighting retention by

next_steps:
  - fold the ruling into dn-self-sensing: §2.5 reset semantics, V2 escalation
    candidate → RESOLVED, §2.4 the erasure test, PD table row (same session).

references:
  - docs/design-notes/self-sensing.md
  - docs/design-notes/code-observation-projection.md
  - core/stores/code_observations.py
```

---

## 2026-07-12T18:32:53Z (captured) — owner musing: the Heisenberg parallel and the phase-space vector

```capsule
topic: self-sensing
date: 2026-07-12

decisions: []   # none — owner musing, explicitly low-stakes; captured as vocabulary
                # for the Track-D charter seed (17:54Z capsule), not as rulings

open_questions:
  - (owner) loose Heisenberg parallel: you can't have position and momentum at once,
    yet here state AND direction are both crucial — "an odd parallel, this is a
    classical system which allows us to be precise on both." Session mapping: the
    precision is BOUGHT by the firewall — the passive stratum makes self-measurement
    ZERO BACK-ACTION by construction (reading the system does not steer it), which is
    exactly why both coordinates stay sharp. Each future gated consumer introduces
    measurement back-action DELIBERATELY: the uncertainty-like tradeoff arrives by
    choice, one gate at a time, not as a law of nature.
  - (owner) "like a vector with a starting coordinate — position and direction are
    part of the equation"; direction is what lets the system continuously update its
    knowledge graph over time. The phase-space framing: the graph's full state is the
    pair (snapshot, motion). The supersession chains / edge-strength series are the
    MOMENTUM coordinates — a lone snapshot has no derivative; velocity is only
    measurable as differences across the record. The erasure test restated: erasure
    keeps q and zeroes measured p — dead reckoning. A wise consumer integrates the
    flow from the pair (and maybe curvature: an edge's strengthening accelerating).

next_steps:
  - none now — enriches Track D's charter vocabulary when that design pass opens.

references:
  - docs/design-notes/self-sensing.md
  - docs/brainstorms/self-sensing.md (the 2026-07-12T17:54Z weaving capsule)
```

---

## 2026-07-12T18:36:02Z (captured) — "a set of edge vectors that interact — what math structure am I reaching for?"

```capsule
topic: self-sensing
date: 2026-07-12

decisions: []   # none — vocabulary ruling for the Track-D charter, verified against
                # the built house math (core/complex/, Track H) in-session

open_questions:
  - (owner) edges as vectors with position+direction that interact and influence each
    other — the named structures, ascending precision:
      1. minimal: a COUPLED DYNAMICAL SYSTEM ON EDGE SPACE — per-edge phase point
         (strength, velocity); influence topology = shared endpoints/triangles (the
         line graph); the influence matrix is the Jacobian; symmetric coupling ⇒
         gradient flow (settles), asymmetric ⇒ rotational components (cycles).
      2. the right one, given "fibers/threads": DISCRETE HODGE THEORY on the
         simplicial complex — a set of edge values IS a 1-COCHAIN (discrete 1-form);
         edge-edge interaction = the Hodge 1-Laplacian L₁ (down-coupling via shared
         nodes, up-coupling via shared triangles); the HODGE DECOMPOSITION names the
         owner's threads exactly: gradient (node-potential-explained) ⊕ curl (local
         circulation) ⊕ HARMONIC (global circulation around holes — flow no local
         structure explains: the thread that weaves). dim(harmonic) = β₁ = the hole
         count topology.py already computes — the hole is the absence, the harmonic
         flow is the thread orbiting it ("you orbit this without stating it").
      3. durability axis: PERSISTENT HOMOLOGY over the strength filtration (already
         ripser-built for H₁) — durable-as-utility = long bars; over wall-clock time,
         vineyards (temporal.py already runs the scalar-invariant version).
      4. typed influence: the SHEAF LAPLACIAN — laplacian.py's own header defers it
         ("general-transport cases, not built here"); the named next rung when edges
         carry typed data with consistency maps, not scalar strengths.
  - VERIFIED in-session: Track H already built the floor on the AUTHORED stratum —
    laplacian.py (L = δ*δ family incl. signed), balance.py (frustration), topology.py
    (flag complex + persistent H₁), temporal.py ("the system watching its own
    structure evolve" — invariant time series, detection only). The weaving consumer
    is this toolbox ONE DEGREE UP (0-forms → 1-forms) pointed at observed/cross-
    stratum edges — the math transfers; the DATA BOUNDARY is what Track D must
    license (𝔎|_MR stays authored-only; reference edges stay out of A_geom).
  - the diagnostic/dynamical line (keep it): the built machinery MEASURES structure
    ("nothing here alters anything"); edge-edge influence as a DYNAMICS is a model —
    correlator-class, INTERPRETED proposals only. The observed record supplies the
    measured trajectory; any dynamics is an interpretation of it, superseding like
    every other view.

next_steps:
  - none now — this + the phase-space capsule are Track D's charter vocabulary.

references:
  - core/complex/laplacian.py
  - core/complex/topology.py
  - core/complex/temporal.py
  - core/complex/balance.py
  - docs/design-notes/code-observation-projection.md   # §2.5 — the A_geom exclusion
  - docs/design-notes/self-sensing.md
```

---

## 2026-07-12 — math/physics thread spun out → `edge-dynamics-and-continuum.md`

The owner-dialogue arc of 2026-07-12 (phase space → Hodge threads → Fourier/splines →
the continuum bridge; the five capsules above) outgrew capsule-appends. Consolidated,
in spirit and rigor, per the owner's instruction, in
**`docs/brainstorms/edge-dynamics-and-continuum.md`** — the charter vocabulary for
Track D's design pass. This file remains the self-sensing (proprioceptive projection)
home; the design note is `docs/design-notes/self-sensing.md` (draft, awaiting the
owner's hand).
