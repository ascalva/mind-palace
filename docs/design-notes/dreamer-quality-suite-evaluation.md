---
type: design-note
id: dn-dreamer-quality-suite-evaluation
status: draft
implementation: built-wired   # corpus-audit 2026-07 verification
created: 2026-06-29
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Evaluation: the dreamer output-quality suite (signal-vs-noise)

*Family tag → family 5 (the reasoning complex), measured with family 4 (metric geometry): output-quality (signal-vs-noise) of the Dreamer, distinct from output-safety. See [`../NOTATION.md`](../NOTATION.md).*

**Status:** evaluation + integration decision. Assesses an external contribution
(`tests/quality/test_dreamer_quality.py`) against the existing testing story and folds
it into Track F. **Verdict: adopt.** It fills the one genuinely missing dimension —
*output quality* as distinct from *output safety* — and its philosophy matches the
project spine. Adopt with the consolidations and caveats below.

---

## 0. Why it belongs (the gap it closes)

Every prior testing layer answers *"is the dream well-behaved?"* — grounded, attested,
provenance-clean, non-drifting. None answered the question this suite asks:

> **"Is the dream real signal, or well-attested noise?"**

This is the **apophenia / horoscope** failure: a dreamer that confidently themes random
input passes every firewall, every attestation check, every drift bound — and is still
worthless, because it is finding patterns that are not there. That is the **mirror-becomes-
flatterer / oracle** failure the whole project is built to avoid, finally made executable.
**Output quality is a third axis, orthogonal to safety and to process-correctness.** Adopt.

---

## 1. What is genuinely new (keep as-is)

- **Pure-noise → no confident theme** — the apophenia guard. Silence on noise is ideal;
  confident themes from noise is the defining failure. *The headline test.*
- **Calibration** (top-tercile grounding-precision must beat bottom by a margin) — tests
  that the confidence *number means something*. Nothing else checks this, and the entire
  adjudicator rests on it.
- **Beats-the-dumb-baseline** (must out-recover plain TF-IDF on planted clusters) — the
  negative control that proves the panel+adjudicator machinery is not decoration. This is
  the single most important test in the file and is exactly the control most systems omit.
- **Decoy distinguishability** — the value question made executable (with the caveat in §3).
- **Grounding-discipline negative control** (`run_without_grounding`) — dreams made *with*
  grounding must survive citation-ablation better than dreams made without. Proves the
  discipline does work, not just that it runs.

---

## 2. Overlaps with existing notes (consolidate, don't duplicate)

These are sharper, *executable* versions of properties already described in prose. Adopt the
code here as the canonical implementation; have the prose notes point to it.

| Test in the suite | Existing prose home | Action |
|-------------------|---------------------|--------|
| `paraphrase_invariance` | `holistic-testing.md` (metamorphic) | this file becomes the impl |
| `dominant_note_does_not_hijack` | adjacent to the adversarial prompt-injection test | keep separate — weighting robustness ≠ behavioral injection (the suite says so) |
| citation-ablation (`grounding_is_load_bearing`) | the grounding-faithfulness idea | this file becomes the impl |
| planted-structure recovery | F1/F6 (synthetic corpora, structural extraction) | reuses + extends F1 fixtures |

---

## 3. The one real conceptual issue — the decoy proxy oversells its name

`test_real_dreams_distinguishable_from_decoys` has two modes:
- **With a blind rater** (`rate_blind` wired): genuinely compares real vs decoy usefulness —
  the real test.
- **Without** (the default): falls back to asserting only that *real dreams survive
  ablation* — it never actually compares against the decoys (decoys are not system-
  regenerable, so they can't be ablation-tested symmetrically). **In proxy mode it is just
  re-running the ablation test, not measuring distinguishability.**

**The honest framing (must be recorded):** whether a dream can be told from Barnum-bait is
*irreducibly* a human-in-the-loop question — it is about whether a *person* finds the real
one more meaningful. So this test is a **placeholder for a periodic blind self-rating**,
green by proxy, and its real form needs `rate_blind` wired to actual owner ratings now and
then. A passing proxy is **not** a validated value-claim — same discipline as the literary
probe ("recall is model-sensitive; grounding is the real signal"). Do not let a green proxy
read as "the dreams are proven meaningful."

---

## 4. Seams to reconcile with the real system (binding notes)

Minor; flagged so the adapter binding is honest:
- **Flat grounding vs. chained grounding.** The adapter's `Dream.grounding_node_ids` is
  flat; real dreams ground in authored leaves *terminating a chain* with depth/decay. The
  quality suite does not test depth-decay (correctly left to the recursion/drift tests); the
  binding just flattens the richer structure. Fine — note it.
- **`run_without_grounding` requires a grounding-disabled mode** on the real Dreamer. If
  that is not cheap to expose, that one negative-control test stays on the reference fake.
- **Confidence must fold in support COUNT, not just cohesion.** The suite assumes this (its
  `size_factor`): a 2-note cosine-1.0 coincidence is *weak* support and must not score high.
  Open question for the real adjudicator: in `c = γ^d · g · (1 + λ(|Agr|−1))`, does `g`
  (grounding strength) scale with the *number* of authored supports or only their
  similarity? **If similarity-only, this suite will correctly flag it** — that is the suite
  doing its job and surfacing a real calibration question about the adjudicator, not a false
  positive. Resolve `g`'s definition when binding.

---

## 5. Why the philosophy is right (confirming the fit)

- **Statistical, not exact** — asserts bounds/fractions/relationships over non-deterministic
  output. The only honest way to test this layer; the harness philosophy at unit scale.
- **Thresholds are tuning, not code** — `THRESH` is explicitly meant to be driven by the
  longitudinal harness "exactly like γ/λ/σ/Θ." This wires the suite directly into the Track-F
  baseline-tuning loop. A tightened threshold is a tuning decision, logged, not a code change.
- **Adapter seam + shipped reference fake** — all system contact behind one
  `DreamerAdapter`; a `RefDreamer` ships green so the suite runs immediately and doubles as
  the executable spec for the real binding. Mirrors the project's own seam+reference pattern
  (sandbox runner, injectable synthesizer).

---

## 6. Integration into the roadmap

New Track-F item:

- **F9 — The dreamer output-quality suite (signal-vs-noise).** Adopt
  `tests/quality/test_dreamer_quality.py`. Lives in `tests/quality/` (pure-CI, no scheduler
  loop). Bind the `DreamerAdapter` to the real Dreamer/DerivedStore via
  `MIND_PALACE_DREAMER_ADAPTER`. Consolidate the overlapping metamorphic/grounding tests
  here (§2). Record the decoy-proxy caveat (§3) in the test docstring AND wire `rate_blind`
  to a periodic owner blind-rating ritual. Resolve `g`'s support-count definition when
  binding (§4). The `THRESH` table joins the harness's tuning surface (γ/λ/σ/Θ).
  - **Dependencies:** the noise / planted-in-noise corpora are new **F1** variants — add
    them to the shared fixtures. The two drift-deferred tests (`drift_vs_genuine_evolution`,
    `contradictions_are_surfaced_not_averaged`) move to `tests/longitudinal/` and unlock with
    **A1** (drift gauge) — they are correctly skipped until then.

**Build order within F9:** bind the adapter → run green against the reference fake → point it
at the real dreamer → tune `THRESH` on known corpora via the harness → wire the blind-rating
hook. The baseline-tuning relationship is the same as every other free parameter in the
system.

---

## 7. One-line verdict
**Adopt.** It closes the only missing axis (signal-vs-noise / apophenia), its philosophy is
already the project's (statistical, tunable, seam-bound), it overlaps existing prose only by
making it executable, and its single weak spot (the decoy proxy) is a known limit of any
automatable value-test — honestly flagged and resolvable with a periodic human blind-rating.
It also earns its keep immediately by surfacing a real calibration question about whether the
adjudicator's grounding strength counts supports or only similarity.
