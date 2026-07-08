---
type: design-note
id: dn-the-sacred-boundary
status: draft
implementation: design-only   # corpus-audit 2026-07 (N/A-design-only)
created: 2026-07-04
updated: 2026-07-04
links: []
supersedes: null
superseded_by: null
warrant: null
---

# The Sacred Boundary — Writes to the Core

**Status:** DRAFT — pending codebase reconciliation and owner ratification
**Origin:** Design dialogue, July 2026 (owner principle + architect synthesis)
**Role:** Spine note. States the principle that governs every write crossing the
core's boundary, and indexes the five subsystem notes that instantiate it.

---

## 1. The principle

The core has exactly three channels that cross its boundary. Two write **into**
the core; one writes **out** to the world. All three are sacred — meaning every
design at these boundaries is held to the same four properties, without
exception.

| Channel | Direction | Carrier | Home note |
| --- | --- | --- | --- |
| **Verdict authorization** | into core | owner judgment → promotion / supersession | `verdict-authority.md` |
| **Ingestion** | into core | content → authored strata | `ingest-identity-and-amendment.md`, `dialogue-ingest-and-recursion.md`, `founding-corpus.md` |
| **Effects** | out of core | core decision → the world | `effector-risk-computation.md` |

The inbound channels and the outbound channel are **symmetric** — the same
boundary discipline read in two directions. This is the EffectView / MirrorView
symmetry made into a governance rule: MirrorView reads the world into the store
under provenance; EffectView writes the core into the world under gating.

**"Sacred" does not mean "privileged."** The opposite: a privileged
mutate-the-core capability is exactly what these designs remove. Sanctity is the
property that the four invariants below hold and cannot be bypassed — achieved by
dissolving the dangerous capability, not by guarding it. See §3.

## 2. The four properties every boundary write must satisfy

1. **Attributable.** Every write carries provenance.
   - Verdict: an Ed25519 signature over the canonical verdict payload — owner-
     attributable, non-repudiable, content-bound.
   - Ingestion: content-hash identity plus an occurrence / version log entry.
   - Effect: the decision record that authorized it.

2. **Append-only / non-destructive.** No mutate-the-immutable operation exists.
   Corrections are supersession edges plus re-projection of the derived view,
   never in-place edits. (An effect on the world cannot be append-only, but the
   *decision to effect* is logged append-only, and irreversibility is precisely
   what the outbound gate protects.)

3. **Typed and promotion-gated.** Derived material never silently becomes
   authored; promotion toward authored authority happens only through an owner
   verdict. Inbound content is typed by stratum and depth; outbound effects are
   typed by blast radius. This typing extends to **edges**: an edge carries the
   authority entitled to assert it (`geometry` / `dreamer-proposed` /
   `verdict-certified`), so the graph types its nodes by stratum and its edges by
   who may draw them (`the-edge-model.md`).

4. **Un-purchasable by expected value.** Bright lines bound the feasible set;
   no outcome, however large, buys past a gate. This governs the outbound
   irreversibility gate and the promotion gate alike — including the rule that
   auto-optimizing over verdicts is a separate self-modification requiring its
   own gate.

## 3. The method — the capability-dissolution test

Each subsystem was designed by the same move. A first pass reaches for a
dangerous general capability — a component that can *verify* (and therefore
forge) a verdict, an optimizer in which outcome-value can *purchase* any action,
a privilege to *mutate the immutable*. The correct design **removes the need**
for the capability rather than granting it under controls. Stated as an
acceptance test:

> **If a design still requires the dangerous permission, the boundary is in the
> wrong place. Keep moving the boundary until the permission is unnecessary.**

This is *how* sanctity (§1–§2) is achieved. Where each subsystem passes the test:

- Verdict verifier that could forge → replaced by an asymmetric public-key check
  that cannot forge. (`verdict-authority.md`)
- Value-optimizer that could buy past a bright line → bounded by hard
  constraints on the feasible set. (`effector-risk-computation.md`)
- Mutate-the-immutable privilege → dissolved into append + re-project; no
  privileged mutation exists anywhere. (`ingest-identity-and-amendment.md`)
- Correction as a peer claim that corrupts density → an operation that acts on
  existing claims via supersession. (`dialogue-ingest-and-recursion.md`)
- "Train" as weight modification that launders provenance → founding-condition
  *authoring* by ingest, weights fixed. (`founding-corpus.md`)

## 4. Cross-cutting ordering constraint

One dependency spans several notes and must not be violated by any build
sequence:

> **verdict store → close the recursive loop → run the longitudinal study.**

The recursion study (`dialogue-ingest-and-recursion.md` §5) and the founding
corpus (`founding-corpus.md`) both depend on labeled verdicts to have any
readable fitness signal, and both depend on the two named Track L prerequisites:
provenance migration `--apply` and self-knowledge ingest (open question **Q6**).
Do not sequence dependent work ahead of these.

## 5. The subsystem notes

- `docs/design-notes/verdict-authority.md` — owner verdict authentication
  (inbound channel: verdict). Threat B; Ed25519; MFA on key custody.
- `docs/design-notes/ingest-identity-and-amendment.md` — ingest identity, dedup,
  amendment (inbound channel: ingestion, structural layer).
- `docs/design-notes/dialogue-ingest-and-recursion.md` — dialogue as reasoning
  operations, bounded recursion (inbound channel: ingestion, semantic layer).
- `docs/design-notes/founding-corpus.md` — authoring the initial condition
  (inbound channel: ingestion, origin case).
- `docs/design-notes/effector-risk-computation.md` — risk under gating (outbound
  channel: effects).

Cross-cutting, added after the supersession-edge work:

- `docs/design-notes/the-edge-model.md` — edge taxonomy and assertion authority
  (statics): knowledge/fiber edges vs reasoning-path/supersession edges, which
  edges feed the balance math.
- `docs/design-notes/supersession-lifecycle.md` — supersession dynamics: proposed
  → certified states, the authored-content gate, grounding maintenance, and the
  depth / γ^d decay math.

Build plan and reconciliation live in the builder prompt that accompanies this
set (`builder-prompt.md`, and `builder-prompt-edge-and-supersession.md` for the
edge-model / lifecycle phase).
