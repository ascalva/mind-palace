---
type: design-note
id: dn-weaving-consumer-charter
status: draft # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only # nothing built; the consumer is GATED behind four entry conditions
created: 2026-07-14
updated: 2026-07-14
links:
  - docs/brainstorms/edge-dynamics-lane-b-fable-pass.md # the fable warrant (deliverable D)
  - docs/design-notes/edge-dynamics.md # §2.6 named this consumer + its three gates (Lane B)
  - docs/design-notes/temporal-retrieval-algebra.md # the math this consumer reads; the A7 gate
  - docs/design-notes/core-query-protocol.md # §2.7 the diachronic interpreter (this is its Lane-B tier)
  - docs/design-notes/self-sensing.md # the B-a/B-b observed substrate (gate 1); the erasure line
  - docs/design-notes/supersession-lifecycle.md # §3 the blessing gate a promotion routes through
supersedes: null
superseded_by: null
warrant: docs/brainstorms/edge-dynamics-lane-b-fable-pass.md
---

# The weaving consumer — Track D's Lane B charter (gated, not licensed)

> Composed by the orchestrator (**Opus 4.8/xhigh**, 2026-07-14) from the verified Fable pass
> (`docs/brainstorms/edge-dynamics-lane-b-fable-pass.md`, deliverable D). `dn-edge-dynamics`
> §2.6 named this consumer, pinned three entry gates, and deferred its charter to "a Track D
> design pass … a separate note the owner ratifies." This is that note.
>
> **This charter LICENSES NOTHING.** It fixes *what the weaving consumer would be* and *the gates
> it must clear* — so the shape is decided once, in the open, and no build begins until all four
> gates are green and the owner ratifies. It is the Lane-B tier of the diachronic interpreter
> ruled in `dn-core-query-protocol` §2.7.
>
> Ratification is a hand edit by the owner; `/graduate` refuses this note until `status:
> ratified` — and even then graduation is gated on §2.3 below, not on ratification alone.

## 1. Purpose and scope

The **weaving hypothesis** (owner, 2026-07-12): as the system accumulates history, threads weave
through the **cost**, **documentation**, and **scope-of-change** planes — *"see what the dreamer
can reason about that."* It is empirical and falsifiable, not theoretical (`dn-edge-dynamics`
§2.6). This note decides:

1. **What the consumer reads, emits, and how it is adjudicated** (§2.1) — correlator-class,
   INTERPRETED-only, dreamer-proposed authority.
2. **The four entry gates** (§2.2) — the three from `dn-edge-dynamics` §2.6 **plus a fourth the
   fable pass adds**: the A7 signal-vs-noise discriminator, without which the consumer is an
   apophenia engine.
3. **The first-rung deliverable and its razor** (§2.3) — R1 splines, not R4 actions; no build
   before the gates.

**Out of scope:** the temporal *mathematics* (that is `dn-temporal-retrieval-algebra`); the
*synchronic* dreamer and its lenses (unchanged); the mirror-side dream path (the firewall forbids
this consumer from touching it); any back-action (this consumer measures and proposes, never
steers). Moving the data boundary is **not** sought — the consumer reads the observed strata and
`X_cite`, never `𝔎|_MR`.

## 2. Principles / decision

### 2.1 The consumer — reads, emits, adjudication (charter)

`[capsule D; edge-dynamics §2.1/§2.6; self-sensing §5; supersession-lifecycle §3; provenance.py]`
The weaving consumer is **correlator-class** — the Lane-B tier of the diachronic interpreter
(`dn-core-query-protocol` §2.7):

- **READS:** `ObservedView` (the cost `φ_self`, documentation, and scope-of-change/churn planes);
  the versioned edge-strength series (`self-sensing` B-a chains); the supersession/version chains
  (the ledger); and — the corpus-structural tier — `X_cite` (repo-derivable, mirror-safe per
  `dn-core-query-protocol` C1). It reads the **dynamics** (trajectories). It **NEVER** touches the
  mirror-side dream path, authored payload, or any `MIRROR_READABLE` row.
- **EMITS:** INTERPRETED proposals **only** — each a `Claim(statement, support ⊆ authored notes)`
  with **dreamer-proposed authority**, landing as a `derives` hyperedge
  (`provenance='interpreted'`, INTERPRETED ∉ MIRROR_READABLE). Claims are diachronic: *"this thread
  consolidates across the cost and documentation planes"*; *"this fiber is strengthening —
  content-addressed, survived the A7 discriminator."* **Zero back-action; erasure-invariant.** A
  claim becomes authored only through `core/provenance.py` `promote()` — an **owner verdict**, never
  a silent belief.
- **ADJUDICATION:** the **same R1 adjudicator** as the synchronic panel (no self-blessing);
  diagnostic / mirror-not-oracle. A proposal touching *blessed* content routes through the
  `supersession-lifecycle` §3 blessing gate (an owner verdict to demote/supersede). A weaving claim
  stays in the dream lane — it **never** side-channels into the artifact chain as a
  design/direction finding (the finding-routing rule is unchanged).

### 2.2 The four entry gates (the §2.6 three + the A7 fourth)

The consumer is built only when **ALL** of:

1. **Substrate exists** — `self-sensing` B-a (interpreter-version supersession) and B-b
   (`AgentObservationStore` + `φ_self`) are built and attested; the observed planes it would weave
   actually accumulate. `[edge-dynamics §2.6]`
2. **Sample depth clears the rung** — the `dn-edge-dynamics` §2.5 ladder applies to observed series
   exactly as to mirror ones; **the consumer's first rung is R1** (splines/GP per edge series →
   measured momentum `p`), **not R4** (learned action). No Hamiltonian on five commits of ledger.
   `[edge-dynamics §2.6]`
3. **This charter is ratified** — the owner ratifies this note; `dn-edge-dynamics` §2.5's inversion
   discipline binds every fit by reference. `[edge-dynamics §2.6]`
4. **[ADDED by the 2026-07-14 fable pass] The A7 signal-vs-noise discriminator is implemented and
   enforced.** `[capsule A7/D; `dn-temporal-retrieval-algebra` §2.5]` The consumer must subtract
   interpreter-artifact (re-embed) drift and read only content-addressed / exact-invariant-moving
   evolution: a drift claim is admissible only when `‖Δ_content‖ ≫ ‖Δ_interpreter‖`, and the
   consumer **returns nothing** on interpreter-artifact-dominated change (the `change_point`
   honest-seam, lifted). **Without this gate the weaving consumer is an apophenia engine** — this is
   the pass's material addition to §2.6.

### 2.3 The first-rung deliverable and its razor

The first buildable unit (once all four gates are green) is **R1 splines over the observed
edge-strength series → the phase point `(q, p)`** (position from snapshots, momentum from the
B-a chains). Its three-clause razor:

- **Measures:** whether threads genuinely weave across the observed planes (cost / documentation /
  scope-of-change) as history accumulates.
- **Valid when:** the A7 discriminator holds and the trajectory clears R1's sample-count gate.
- **Fails its keep if:** the weave is embedding noise (A7 subtracts it) or no cross-plane thread has
  persistence.

**This charter grants no build** until all four gates are green and the owner ratifies.

## 3. Consequences — what this note licenses (on ratification + gates)

- **Track D's build lane** opens *only* behind the four gates: first R1 splines (§2.3), then up the
  `dn-edge-dynamics` §2.5 ladder one data-earned rung at a time, each rung a small owner-visible
  plan whose acceptance is the inversion's exact-invariant falsifier.
- **The diachronic interpreter's Lane-B tier** (`dn-core-query-protocol` §2.7) is realized here; its
  earlier *corpus-structural* tier (over `X_cite`, mirror-safe) may graduate ahead of this charter,
  under the synchronic-panel contract.
- **No back-action is licensed** — the system stays erasure-invariant (`self-sensing` §2.4) until a
  *separate*, owner-ratified, audited consumer deliberately introduces path-dependence.

## Parked decisions

| id | decision | default recorded | re-entry condition |
| --- | --- | --- | --- |
| WC-a | which observed planes weave first | cost + documentation + scope-of-change (the owner's three) | B-b makes a plane's series actually accumulate; add planes as they earn depth |
| WC-b | the corpus-structural tier vs the observed-weaving tier ordering | the `X_cite` structural tier (mirror-safe) may ship first; the observed-weaving tier waits on gate 1 | the substrate (B-a/B-b) is attested |
| WC-c | the persistence threshold for a "thread that weaves" | rank-by-persistence, no hard cut (inherits `dn-edge-dynamics` PD-f / `dn-self-sensing` durability) | dreamer-quality-suite evidence a distinct threshold is needed |

## Open questions / OWNER DECISIONS

- **✓ Substrate prerequisite (owner ruled 2026-07-14).** This consumer's gate 1 is `self-sensing`
  B-a/B-b (not yet built) and its A6 identity prerequisite — **rename-stable identity, which the
  owner ruled a HARD prerequisite to prioritize BEFORE the diachronic reader graduates**
  (`dn-temporal-retrieval-algebra` §2.4 / rulings). It cannot graduate before that upstream work.
- Whether the weaving claim's narration needs new dream-prompt vocabulary (a taste question, costs
  nothing until the first build) — inherits `dn-edge-dynamics` §5's narration open question.

## Cross-references

- `docs/brainstorms/edge-dynamics-lane-b-fable-pass.md` — the **warrant** (deliverable D + the A7
  gate derivation).
- `docs/design-notes/edge-dynamics.md` — §2.6 (the three gates, the weaving hypothesis, Lane B as
  vocabulary), §2.7 (diagnostic-not-dynamical, back-action opt-in).
- `docs/design-notes/temporal-retrieval-algebra.md` — the math this consumer reads (`σ_*`/`X_cite`
  dynamics) and the A7 discriminator (§2.5) that gate 4 enforces.
- `docs/design-notes/core-query-protocol.md` — §2.7 the diachronic interpreter (this is its Lane-B
  tier); C1 (why `X_cite` is mirror-safe).
- `docs/design-notes/self-sensing.md` — the B-a/B-b substrate (gate 1); §2.4 the erasure test this
  consumer keeps passing.
- `docs/design-notes/supersession-lifecycle.md` — §3 the blessing gate a promotion routes through.
- code: `core/sensing.py` (`ObservedView`), `core/provenance.py` (`promote()` — owner-verdict gate;
  the `NotImplementedError` stub at :156), `core/dreaming/interpreters.py` (the lens contract),
  `core/mirror.py` (`MIRROR_READABLE` — the firewall this consumer stays outside).
