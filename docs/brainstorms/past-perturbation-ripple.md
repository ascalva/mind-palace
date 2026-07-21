# Past-perturbation ripple — counterfactual ablation along the graph's history

Brainstorm thread: go back in time along the graph, perturb its past, and study the ripple
forward. What type of perturbation causes what type of ripple, and how dramatic is it? Reminded by
the hypothetical-subspace topic; the owner's "fun/wacky thought."

## 2026-07-21T17:43:18Z

```capsule
topic: past-perturbation-ripple
date: 2026-07-21

decisions:
  - The idea IS the influence probe (bp-082) with a TIME ANCHOR. bp-082 stages a HYPOTHETICAL
    overlay at the present cut and reads the per-instrument with/without differential; this stages
    the perturbation at an EARLIER cut and reads the differential forward along the D-clock. Same
    machinery — E_STAGED overlay, the conditioning law, TTL inheritance, the hypothetical-subspace
    isolation story — anchored earlier. No new mechanism; the novelty is where the stage sits.
  - The perturbation taxonomy MAPS onto the fiber-geometry three layers (grammar/geometry/dynamics),
    so "what type of perturbation → what type of ripple" is answered by which layer you poke:
      * delete a node/edge (a claim/citation never existed) = a GRAMMAR/membership perturbation;
        ripple = discrete pruning (a downstream subgraph blinks out); measured by reachability count.
      * reweight an edge (a similarity was different) = a GEOMETRY perturbation; ripple = continuous
        metric shift (σ*/conductance move downstream); measured by the metric-mismatch field.
      * re-time a node (arrived earlier/later) = a DYNAMICS/clock perturbation; ripple = re-ordering
        (which nodes could cite which changes → the admissible-chain LANGUAGE shifts). [DERIVED]
  - "How dramatic" is a temporal Lyapunov/sensitivity, and clock-curvature already predicts its
    sign: a perturbation dropped in a HOT (high-churn) region AMPLIFIES as it propagates; in a
    COLD/annealed region it DAMPS; beyond a churn threshold the conductivity-horizon prediction
    says the ripple DECOUPLES (can't propagate through). Testable via G-A's M5/M7. [INFERENCE]
  - Self-map payoff: the nodes with the largest forward ablation cone are the corpus's KEYSTONES —
    "which of my past ideas were load-bearing?" as a self-knowledge instrument.

parked:
  - decision: the SUBSTITUTION ripple ("what would have existed INSTEAD")
    default: measure only ABLATION ripples ("what would NOT exist") — the forward closure over the
      provenance spine (origin(e) / the C∘derives walk graduated in AL-3), computable exactly on the
      real corpus today. Substitution is NOT computed.
    re_entry: a generative model of what the agent+owner would have done exists AND the
      records-not-causes law is honored (a C-edge witnesses a recorded production, not a re-runnable
      natural law) — i.e. only if/when a validated agent-behavior model can supply the alternative
      history without pretending the record is a physical law.

open_questions:
  - Magnitude measure: is "how dramatic" best the forward-ablation-cone size (reachability over the
    provenance spine), the bp-082 influence differential integrated forward, a temporal Lyapunov
    exponent (does the effect grow or shrink along the D-clock), or clock-curvature's volatility
    exposure? Likely several, per layer.
  - Does a real past-perturbation experiment on the corpus reproduce the hot-amplifies/cold-damps
    prediction, and is there an observable conductivity-horizon (a churn level past which early
    perturbations stop rippling)?
  - Which perturbation to pick: random ablation vs targeted (high-influence early nodes) — and does
    ablating a keystone produce a qualitatively different ripple than ablating a leaf?

next_steps:
  - Capture only (this note). NOT graduated — nothing preempts the sequenced queue; the influence
    machinery it rides (bp-082) is sealed and G-A (bp-085, in flight) produces the phase baselines
    the "how dramatic" question needs. Revisit after G-A's M5/M7 readings land.

references:
  - docs/build-plans/bp-082/plan.md (influence probe + conditioning law — the machinery, present-cut)
  - docs/build-plans/bp-081/plan.md (HYPOTHETICAL/E_STAGED staging + isolation)
  - docs/design-notes/synchronic-diachronic-dreamer.md (§2.6 counterfactual overlay; the D-clock)
  - docs/design-notes/fiber-geometry.md (§2.1 three layers; §2.4 clock-curvature; M5/M7 phase battery)
  - docs/design-notes/agentic-loop.md (§2.4b EX-2 origin(e) / provenance spine = the ablation-cone walk)
  - docs/brainstorms/hypothetical-subspace.md (the present-cut counterfactual sibling; the reminder)
  - docs/brainstorms/clock-curvature.md (hot/cold phase model; the ripple-amplitude prediction)
  - records-not-causes: dn-synchronic-diachronic-dreamer §2.9 (the substitution-ripple guardrail)
```
