---
type: design-note
id: dn-recursive-dreaming-bounded-by-grounding
status: draft
implementation: partial   # corpus-audit 2026-07 verification
created: 2026-06-26
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Recursive dreaming: compounding interpretation, bounded by grounding

*Family tag → family 2 (regenerable derivation): the recursion-decay bound c ≤ γ^d·g that keeps compounding interpretation from amplifying — the acyclic derivation DAG with authored leaves (I10). See [`../NOTATION.md`](../NOTATION.md).*

**Status:** design only; extends `dreaming-v2-interpreter-panel.md` and the Phase 7 dreamer.
The **highest-risk** dreaming feature — the one place the system's own outputs feed back as
its own inputs. Build it **last** among dreaming features and **only after** the drift gauge
(Phase 11/§15) exists to watch it. Does not change Phases 0–10 scope.

## The idea (owner)
Dreams build on memories produced by *other* dream cycles — compounding interpretation within
the core graph (provenance preserved) — ranked by utility in day-to-day tasks, with telemetry
used to understand the alignment produced by interpretation and reinterpretation. "A graph
observing itself, recursive in nature, over time."

## Why this is the dangerous one
Every prior subsystem holds one property: the system's outputs never become its own inputs.
Dreams read the AUTHORED corpus; they do not read each other. Recursive dreaming **closes that
loop**, and a model running inference over its own prior inferences is the textbook setup for
**self-amplifying drift** — model collapse (ML), echo chambers (networks), rumination
(psychology). It is the §15 boiling-frog problem operating **inside the interpretation layer**,
where no anchor was specced. Each generation can drift from what was actually written toward a
self-reinforcing narrative, every step looking reasonable. Failure is **silent**.

## The four rules that make it safe
1. **Grounding terminates in AUTHORED evidence, every generation.** A higher-order dream that
   synthesizes across lower-order dreams must still cite the **authored notes** underneath, not
   the prior dreams. Prior dreams are *scaffolding* (where to look), never *evidence* (what is
   true). Extend `core/selfcheck.py`: the citation chain **cannot loop within INTERPRETED** — it
   must bottom out in authored ground truth. This single rule anchors the recursion.
2. **Confidence decays with interpretation-depth; it never compounds.** Tag each dream with its
   generation/order. Naive recursion grows more certain each layer — that is the failure.
   **Correct recursion compounds skepticism:** distance from authored evidence lowers
   confidence. A 5th-order abstraction is visibly more speculative than a 1st.
3. **Confidence and utility are separate axes — never collapsed.** Utility (did surfacing this
   help the owner) and grounding (is it evidence-anchored) are different. Collapsing them
   selects for *pleasing over true* — the mirror becomes a flatterer (true-but-melancholic =
   low utility; shallow-but-resonant = high utility). **Utility decides what to surface;
   grounding decides what to believe.** Track both, never as one number.
4. **The authored floor + frozen baselines remain the fixed point.** Recursive dreams never
   become ground truth; promotion to authored stays a deliberate human act. The "self" the
   graph observes must always include the immutable authored floor, not just its own prior
   observations.

## The telemetry insight (what makes it safe, realized)
Recursion is dangerous *blind* but can be **instrumented**. Specific drift signatures become
alarms on the Phase-11 gauge, measured against the authored floor:
- the ratio of **dreams-citing-dreams vs dreams-citing-authored** climbing;
- **utility rising while grounding falls** (the flatterer signal);
- **confidence rising with interpretation-depth** (the echo-chamber signal).
A graph observing itself is safe **because it is watched**. Deterioration becomes a visible
curve with a human tolerance band and a rollback trigger (§14/§15) — not a silent rot. This is
the right realization of "use telemetry to understand alignment through reinterpretation."

## Build order
Do **not** build recursion until (a) single-generation dreaming-v2 (panel + grounded
adjudication) is solid, and (b) its drift telemetry exists to watch the recursion. Recursion
without the gauge is flying blind into the exact failure mode. When built: cap depth, make the
confidence-decay function explicit, define the utility signal so it can't be trivially gamed.

## Framing (kept honest, per the consciousness thread)
"A graph observing itself" is a real and useful operation **and** a real risk surface —
computational recursion over derived outputs, not emergent self-awareness. The poetry stays out
of the logs; the logs cite authored evidence or they don't ship.

## Open questions
- Depth cap and the shape of the confidence-decay function.
- A utility signal that reflects genuine help, not agreement/engagement (anti-gaming).
- How the owner reviews compounded interpretations (the Phase-11 view).
- Whether a high-confidence higher-order dream ever does more than display (default: no — only
  via the Phase-10 gate).
