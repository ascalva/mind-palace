---
type: design-note
id: dn-observed-stratum-spike
status: draft
implementation: design-only   # spike; nothing built. Note authored post-dates the 2026-07 corpus audit.
created: 2026-07-08
updated: 2026-07-08
links:
  - docs/design-notes/observed-data-and-the-assistant-tier.md
  - docs/design-notes/observed-iot-and-cross-source-synthesis.md
  - docs/design-notes/the-sacred-boundary.md
  - docs/design-notes/the-edge-model.md
  - docs/design-notes/supersession-lifecycle.md
  - docs/design-notes/recursive-strata.md
  - docs/design-notes/live-adoption-and-longitudinal-harness.md
supersedes: null
superseded_by: null
warrant: null
---

# SPIKE — The Observed Stratum: Interpreted Observations Inside the Reasoning Complex

*Family tag → family 1 (labelings & flow) + family 5 (cross-source synthesis): investigation of a typed, Dreamer-readable layer of interpreted observations carrying observed lineage. See [`../NOTATION.md`](../NOTATION.md).*

**Status:** DRAFT — **SPIKE / investigation. Not a decision. Not ratifiable. Amends nothing.**
This note records a design direction, its motivating argument, its defects, and the questions a builder must answer against the code before any of it can become doctrine. It confers no license to build.

**⚠️ Divergence notice.** This note explores a direction **materially different from — and in literal conflict with — the existing doctrine** in `observed-data-and-the-assistant-tier.md` and `observed-iot-and-cross-source-synthesis.md`. Those two notes are **authoritative wherever this note conflicts with them**, and remain so unless and until the owner ratifies a change with a warrant finding. Nothing here supersedes them; `supersedes` is deliberately `null`. A future reader should treat this as *"here is what we thought about, and what we'd have to answer first"* — not as the system's position.

**Origin:** Design dialogue, 2026-07-08. Owner intent: raw sensor data and the agents that read it stay **outside** the core; the *interpreted results* of that data are ingested into a typed layer the Dreamer may read and reason over.

**Boundary:** Inbound — ingestion. Would introduce a provenance-typed layer inside the core. Governed by `the-sacred-boundary.md` §2.

**Re-entry condition:** observed-data work is taken up in earnest, **and** Track L has gone live (§3). Until then this note is inert reference material.

---

## 1. Purpose and scope

**The question this spike investigates:** can the Dreamer reason over interpreted observations derived from observed data, without reintroducing the masquerade failure the authored/observed firewall exists to prevent?

**The direction sketched:** an **observed layer** — a typed layer of the reasoning complex holding *interpreted observations* derived from observed data, readable by the Dreamer as reasoning input. **Raw observed data is never ingested**; only already-derived, aggregated observations produced outside the core.

**Producers stay outside, unchanged.** Sensor-agents and the cross-source **correlator** (`observed-iot-and-cross-source-synthesis.md` §2) run outside the core, over the observed pool, exactly as those notes specify. This spike concerns only (a) a typed landing zone *inside* the core for their interpreted outputs, and (b) the Dreamer's read-scope over it.

**Out of scope:** raw observed ingestion (prohibited, and this spike does not question that); the assistant tier's outward actions; promotion of observed-lineage material to authored (prohibited, §2); the effects/Hands channel — an observed-layer node is a reasoning *input*, never an effect trigger.

**⚠️ Terminology.** "Stratum" in `recursive-strata.md` means a **Dreamer-cycle emission Sₙ** carrying a mint-time depth `d`. The layer proposed here is **not** an Sₙ — no Dreamer cycle produces it. The name "observed stratum" therefore **overloads an existing term**, and that overload is upstream of OQ-1 below. A builder should assume these are different objects and consider proposing a distinct name (e.g. *observed layer*).

## 2. Principles / decision

**No decision is made here.** What follows is the argument as it stood, with its load-bearing parts marked.

**The argument.** The firewall's target is **masquerade** — algorithmic exhaust reflected back as if it were the owner's authored psyche (`observed-data-and-the-assistant-tier.md`: "a silent, hard-to-detect failure"). Its current implementation is *exclusion* (`observed ∉ MIRROR_READABLE`). The direction explored here would replace exclusion with **typing**: the Dreamer may read observed-derived observations *because* they are permanently typed as observed-lineage and therefore structurally cannot be promoted to authored and cannot feed the self-model. The protection would be carried by the **type**, not the **wall** — the capability-dissolution move of `the-sacred-boundary.md` §3.

Whether that substitution is sound is exactly what this spike does **not** settle.

### Preserved from the firewall (non-negotiable in any version of this direction)

1. **Raw exhaust never enters.** Only interpreted/aggregated observations are ingest-eligible. The concentrated raw stream stays outside; the surveillance-dossier concern is untouched.
2. **No promotion to authored.** Observed-lineage material is never relabeled authored. No verdict path grants it authored authority.
3. **Excluded from the self-model.** Behavioral baselines and Constitution-conformance read **authored only**. Dreamer *synthesis* may read the observed layer; the *self-model / conformance* layer may not.

### The single relaxation under investigation

4. **Dreamer read-scope** would extend from authored-only to authored + observed layer — as a **distinct, typed layer**, never by merging observed into the authored pool.

### Invariants — and which ones may carry the guarantee

> **Bright lines are hard constraints bounding the feasible set. They are never weighted terms in an objective.** A scalar penalty is precisely the mechanism expected-value reasoning rationalizes past (`the-sacred-boundary.md` §2.4). The no-masquerade guarantee must therefore rest **only** on structural, unrepresentable-if-violated constraints. This paragraph is the correction of a defect in an earlier draft of this note, which leaned on damping for protection. See §4, D2.

- **I-OS1 (lineage typing) — STRUCTURAL. Load-bearing.** Every observed-layer node carries an immutable `lineage = observed`. Lineage is un-promotable to authored, and **wrong lineage must be unrepresentable at the store boundary** — the pattern of `sensor_readings` having no provenance column and `DerivedStore` taking no provenance parameter (`observed-iot-and-cross-source-synthesis.md` §1b). If lineage can be forged, edited, or lost in any code path, the direction fails outright.
- **I-OS3 (self-model exclusion) — STRUCTURAL. Load-bearing.** Observed-layer nodes never reach baselines or Constitution-conformance. Enforced by type at the read boundary, not by convention or filtering.
- **I-OS4 (Dreamer proposes; owner certifies) — STRUCTURAL. Load-bearing.** The Dreamer may read observed-layer nodes and **propose** syntheses over them; promotion toward authored authority remains a **verdict-certified** act (`the-edge-model.md` §3; `supersession-lifecycle.md` §2). An observation's novelty or interestingness may buy it *attention* and *ingest-eligibility*; it never buys promotion (`the-sacred-boundary.md` §2.4).
- **I-OS2 (influence damping) — TUNING ONLY. NOT load-bearing. Carries no part of the guarantee.** A lineage discount that keeps observed-lineage influence below authored. This is a knob for output quality, not a protection. It is also **not currently well-defined** — see OQ-1. **A builder must not implement I-OS2 as though it enforces anything.**

*(I-OS1, I-OS3, I-OS4 are hard constraints. I-OS2 is a preference. If the three structural invariants cannot be enforced structurally, no value of I-OS2 rescues the design.)*

## 3. Consequences

**Would license** (if ever ratified): an observed-lineage tag in the provenance schema; a typed layer in the complex; a gated ingest path for correlator outputs; a Dreamer read-scope extension. **Today it licenses none of these.**

**Ordering — downstream of Track L.** Whether the layer earns its place — does Dreamer synthesis over observed-lineage nodes track insight, or import exhaust-driven drift? — is a Track-L-measured question. It inherits Track L's prerequisites: provenance migration `--apply` and self-knowledge ingest (`the-sacred-boundary.md` §4, Q6). Do not build ahead of the harness that can measure the drift this direction risks. Same restraint as the Hands, same reason.

**If pursued, formalizing requires** (owner blessing-gate acts, none performed): a warrant finding recording the divergence; owner ratification; `supersedes`/`superseded_by`/`warrant` front-matter linking this note to the specific clauses it would amend in the two firewall notes.

## 4. Known defects in this note's own reasoning

Recorded so a future reader does not rediscover them, and so the builder knows where the thinking is soft.

**D1 — the confidence envelope does not extend to observed lineage (⚠️ unverified at source).** `recursive-strata.md` bounds derived confidence as `c ≤ γ^d · g`, where `g` is the grounding ratio (fraction of support reaching K₀) and `d` is stratum depth. An observed-lineage node's support reaches **observed ground, not K₀**, so `g = 0` and the envelope pins its confidence to exactly **zero** — readable but structurally incapable of influencing anything. Separately, `d` is minted **per Dreamer cycle**; an externally-produced observation has **no defined `d`**. The envelope was correct within its domain; **this note reached outside that domain and reused it anyway.** That is a defect in this note, not in `recursive-strata.md`. Becomes OQ-1.

> **Citation caveat:** the `c ≤ γ^d · g` form and the reading of `g` as "fraction of support reaching K₀" are taken **second-hand from `supersession-lifecycle.md`'s citation** of `recursive-strata.md` Invariant 10. Invariant 10 was **not read at source** (read timed out at I3). Also note `recursive-strata-amendment.md` exists and may revise the numbering. **Verify at source before relying on D1's exact shape.** The `d`-undefined half stands on firmer ground, following from depth being minted per cycle.

**D2 — an earlier draft made a weighted term do bright-line work.** It stated the no-masquerade protection as resting partly on I-OS2's damping factor. A scalar penalty cannot bound a feasible set. Corrected in §2: the guarantee rests solely on I-OS1 + I-OS3 + I-OS4; I-OS2 is demoted to tuning. Retained here because the mistake is an easy one to re-make, and because it is the precise failure mode the un-purchasable-by-EV property (`the-sacred-boundary.md` §2.4) exists to prevent.

**D3 — unverified references.** The bare `§14` / `§15` / `§16` section references inherited from `observed-data-and-the-assistant-tier.md` were never traced to their parent document. `core/stores/telemetry.py` and `sensor_readings` are cited from that note's text, not confirmed in code.

## 5. What a builder should investigate first

Read the code, then float these to the owner. Do not resolve them unilaterally.

1. **Grounding and depth for non-Dreamer-minted nodes (blocks everything).** Read the confidence-envelope implementation and `recursive-strata.md` Invariant 10 **at source**. Does `g` admit a non-K₀ ground? What `d`, if any, could an externally-minted node carry? Report whether the envelope can extend, must be replaced for observed lineage, or whether the layer is incompatible with it. *Falsifier: if `g` cannot be defined for observed ground, the direction is dead as sketched.*
2. **Is lineage unrepresentable-if-wrong?** Trace every write path into the derived stores. Can a node acquire or lose `lineage` outside a typed constructor? Is there any path — migration, backfill, promotion, re-projection — where lineage is defaulted rather than carried? *I-OS1 is load-bearing; a single forgeable path kills it.*
3. **Is `MIRROR_READABLE` enforced structurally or by filter?** Find where it is applied. If exclusion is a runtime filter rather than a type/store boundary, then extending it is a much larger change than this note assumes, and the firewall's current guarantee is weaker than its prose claims. *Report either way — this is worth knowing independent of this spike.*
4. **Where do baselines and Constitution-conformance read from?** Confirm I-OS3 can be enforced at a read boundary with the observed layer present.
5. **Do correlator outputs have a shape worth ingesting?** Inspect actual `DerivedStore` correlation records. If they are unstable, low-content, or high-volume, the gated-subset question (P4) is moot and the spike should be closed.

## Parked decisions

1. **Observed-layer edges in the authored signed Laplacian?** Default **no** — separate layer, typed inter-layer edges; `A_geom` stays authored-lineage-only, preserving `the-edge-model.md` §4's `E_geom` semantics. Re-entry: multilayer Laplacian construction specified **and** Track L can compare synthesis with observed edges in vs. out.
2. **Provenance representation.** Default: reuse `interpreted` with an immutable `lineage ∈ {authored, observed}` field rather than mint a new top-level class. Re-entry: the provenance-schema pass (couples to the `--apply` migration on the critical path).
3. **Naming.** Default: rename away from "stratum" to avoid the `Sₙ` overload (§1). Re-entry: resolution of OQ-1, which may make the distinction moot or essential.
4. **Ingest eligibility of correlator outputs.** Default: a **gated subset**, owner-in-loop; not all interpreted correlations auto-ingest. Interestingness buys attention and eligibility, never promotion. Re-entry: verdict-taxonomy ratification.
5. **Producer boundary.** Default: sensor-agents + correlator stay outside the core, unchanged. Re-entry: only if a producer is proposed to move inside — which reopens the firewall wholesale and is out of scope here.

## Open questions (must be answered before this direction can be ratified)

- **OQ-1 (blocking).** How are `g` and `d` defined for a node whose support terminates in observed ground and which no Dreamer cycle minted? Extend the envelope, replace it for observed lineage, or abandon the direction. *(From D1. Not a tuning choice — a well-definedness problem.)*
- **OQ-2.** Can I-OS1's lineage typing be made unrepresentable-if-violated at the store boundary, or only enforced by convention? If only by convention, the direction fails.
- **OQ-3.** Does replacing a structural exclusion (`observed ∉ MIRROR_READABLE`) with a structural *typing* preserve the no-masquerade guarantee, or merely relocate it somewhere easier to erode? This is the spike's central unanswered question and the one the owner should weigh personally.

## Cross-references

- `docs/design-notes/observed-data-and-the-assistant-tier.md` — the authored/observed firewall; provenance classes; baseline and conformance exclusions. **Authoritative; in conflict with this spike; unamended.**
- `docs/design-notes/observed-iot-and-cross-source-synthesis.md` §0, §2 — Dreamer provenance-homogeneity; the correlator and its lack of a write path to the mirror. **Authoritative; in conflict with this spike; unamended.**
- `docs/design-notes/the-sacred-boundary.md` §2.3 (typed-and-promotion-gated), §2.4 (un-purchasable by EV — the property D2 violated), §3 (capability-dissolution), §4 + Q6 (Track L ordering and prerequisites).
- `docs/design-notes/the-edge-model.md` §1.1, §3, §4 — typed edges, assertion authority, `E_geom`/`E_disp` and what feeds `L`.
- `docs/design-notes/supersession-lifecycle.md` §2 (proposed → certified), §3 (blessing gate), §4.5 + Q11 (promotion mechanics), §6.
- `docs/design-notes/recursive-strata.md` — strata as typed layers; I1 (promotion by verdict only), I2 (decay by default), I3 (bounded strata contribution); Invariant 10 (⚠️ cited second-hand, see D1). Also `recursive-strata-amendment.md`.
- `docs/design-notes/live-adoption-and-longitudinal-harness.md` — Track L as arbiter; shared prerequisites.
- `docs/research/security-planes.md` §6 — unpromoted-derived retrievability (⚠️ cited second-hand via `supersession-lifecycle.md`).
- `docs/NOTATION.md` — family tags.
