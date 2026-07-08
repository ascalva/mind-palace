---
type: design-note
id: dn-alignment-subsystem
status: draft
implementation: partial   # corpus-audit 2026-07 verification
created: 2026-06-27
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Alignment as a subsystem: seeding, detection, surgery, reset (Phase 10 expansion)

*Family tag → family 4 (metric geometry): alignment as fidelity of the regenerable layer to the frozen seed — the drift gauge D(t), the fixed points B/Θ, and the detect→surgery→reset loop. See [`../NOTATION.md`](../NOTATION.md).*

**Status:** design only; expands Phase 10 and ties together the drift gauge (§15), the
fixed points (§4), and the dream/interpreted layer (dream R&D track). Honor when Phase 10
lands. Engages the Westworld/Blade-Runner framing as **engineering, not metaphysics**.

## 0. What alignment is here (the honest floor)
Alignment = the **measurable fidelity of the *regenerable* layer to the *fixed* layer.**
- *Fixed (the seed, immutable, human-blessed):* the authored raw corpus, the Constitution, the
  frozen golden set.
- *Regenerable (what can drift):* dreams/interpretations, derived graph structure, modifiable
  parameters.
It is **not** sentience management, and there is **no autonomous "direction" the system
converges on** — it is a mirror of a fixed (slowly-growing) corpus; the only "direction" is
*what the owner actually wrote*. Alignment keeps the regenerable layer anchored to that seed and
conformant to the Constitution. It does **not** guarantee interpretations are *true* — only that
they stay **anchored**; the owner remains the final arbiter.

## 1. Seeding & initial conditions (the Westworld frame)
The anchors are the baked-in ground truth; the authored raw is the seed. **Sensitive dependence
on initial conditions is real — but scoped to the recursive dream layer**, where early
interpretations could amplify. That layer is already damped by confidence-decay $c\le\gamma^{d}g$
and grounding-terminates-in-authored (chains may not close inside `interpreted`). The "starting
parameters" worth pinning are the free params $(\gamma,\lambda,\sigma,k,h,\Theta)$ — declared
bounds (G7), human-blessed, gated to change.

## 2. Detection — the misalignment test (the Blade-Runner frame)
Three layers, all over the **interpreted/derived layer only**:
- **Behavioral (the Voigt-Kampff analog):** the drift gauge $D(t)=d(\mu(s_t),B)$ vs the *frozen*
  anchor + the Constitution-conformance audit, run periodically.
- **Structural (graph theory):**
  - **min-cut to authored anchors** — an interpreted cluster joined to ground truth by a *thin*
    cut is poorly grounded; **cut-weight ≈ grounding strength**. Thin cut ⇒ bubble.
  - **community detection** — a community that is mostly interpreted nodes with few authored
    anchors is a **self-referential echo chamber**, made structurally visible.
  - **depth/grounding distribution** — interpreted nodes with high $d$ and low $g$ are drift
    candidates.
The audit emits an **alignment report** (drift curve + structural metrics), surfaced on the
Phase-11 dashboard. Detection never alters anything.

## 3. Surgery — correction (gated, regenerable-only)
- **Prune drifted interpreted nodes/edges** (low grounding, high depth, thin cut to authored).
  The Curator already flags prune candidates; alignment-surgery extends it with the §2 metrics.
- **Only ever the regenerable layer.** The authored floor + the Constitution are **never
  surgically cut** — they are the fixed point (human-amend only, deliberate, logged).
- Every surgery is a **gated change** (propose → human-approve → code-executes → validate →
  rollback). Validation requires the cut to **reduce drift without regressing grounding or the
  golden set**.

## 4. Reset — the core restoration (the strongest guarantee)
The Westworld "reset to baked-in memories" exists **by design**: regenerate the entire
interpreted/derived layer from the **immutable authored raw** (`DerivedStore.reset()` + re-ingest;
"raw is sacred, derived is regenerable"). When drift exceeds recovery, blow away dreams/derived
structure and rebuild from ground truth + the Constitution. **Because the seed cannot be
corrupted, a clean state is always recoverable** — this is the deepest alignment guarantee in the
system. Phase-9 backups snapshot system state (gate ledger, baselines, registry) for the same
purpose.

## 5. Phase 10 expansion — modifiable parameters + alignment-steering self-modification
- **Modifiable parameter set:** $\gamma$ (decay), $\lambda$ (agreement), $\sigma$ (similarity),
  $k$ (retrieval), $h$ (headroom), $\Theta$ (drift tolerance), cron-aging, etc. — tunable **only
  through the gate**. Bounds declared (G7). **Excluded from the set** (never auto-tunable): the
  Constitution, the golden set, and the blessed tolerance band itself.
- **Self-optimization:** the system *proposes* parameter changes from telemetry; the human gates;
  validation runs against the fixed points + drift. **Never autonomous.**
- **Self-modification as alignment-steering (the new purpose):** the gate is not only for
  capability tuning. *Alignment-steering* changes — pruning bubbles, re-anchoring, re-tuning
  decay — are accepted **iff they reduce drift toward the anchors** without regressing
  grounding/golden. **"Allowed drift" = the tolerance band:** some drift is healthy
  (interpretations adapting as the corpus grows); deterioration is not. The band is human-set and
  frozen.
- **Dreams are central:** the dream/interpreted layer is simultaneously the **main source** of
  misalignment risk (recursive bubbles) and the **main diagnostic surface** (its graph structure
  reveals alignment health). The alignment subsystem watches the dream layer specifically; the
  dream-recursion params are first-class members of the modifiable set.

## 6. The apparatus (one line)
**Fixed seed** (authored + Constitution + golden) → **bounded regenerable layer** (dreams,
structure, params) → **detection** (drift gauge + graph metrics) → **gated surgery** (prune
bubbles) → **reset-from-raw** (the nuclear realignment). All correction touches only the
regenerable; the seed is sacred.

## 7. Open questions
- Thresholds for "thin cut" / bubble detection (calibrate on the real interpreted graph).
- Audit cadence; whether the alignment report ever triggers surgery proposals automatically
  (default: it proposes; the human gates).
- Surgery's validation metric (drift-reduction vs grounding-preservation tradeoff).
- Is alignment-steering self-mod *ever* allowed unattended? Default **no** — gated like all
  self-modification (the §14 last-and-most-gated rule stands).
