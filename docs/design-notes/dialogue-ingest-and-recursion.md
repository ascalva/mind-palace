---
type: design-note
id: dn-dialogue-ingest-and-recursion
status: draft
implementation: present-not-wired   # corpus-audit 2026-07 verification
created: 2026-07-04
updated: 2026-07-04
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Dialogue Ingest, Correction Semantics, and Bounded Recursion

**Status:** DRAFT — pending codebase reconciliation and owner ratification
**Origin:** Design dialogue, July 2026
**Boundary:** Inbound channel — ingestion (semantic layer). Governed by the
sacred-boundary principle (`the-sacred-boundary.md`). Builds directly on the
identity model in `ingest-identity-and-amendment.md`: corrections are
supersession, not new facts.
**Reconciles with:** `recursive-strata.md` (this is its concrete ingest-operation
instantiation), `live-adoption-and-longitudinal-harness.md` (the closed-loop
study), `ambassador-as-reasoning-agent.md`.

---

## 1. Note and dialogue are different epistemic objects

- A **note** is a *conclusion* — a claim, naked.
- A **dialogue** is a *derivation* — a claim plus its warrant: the objection
  raised, the compromise that answered it, the reason the final position beat the
  initial one.

These are different data types and must enter as different types. Ingesting only
the note, when wrong, teaches a wrong claim with full authored authority and no
attached defeater. Ingesting the dialogue supplies the claim *with its support
structure*.

What transfers from watching two professors argue is the **shape of the move**
(this kind of objection defeats that kind of claim), not merely the verdict.
That dictates what a dialogue ingest stores: the reasoning pattern, not just the
winning proposition.

## 2. Failure to avoid — corrections as peer assertions

If a dialogue's correction enters as a **peer assertion**, the graph holds both
X and X′ at the authored layer, both content-addressed, disagreeing, neither
aware of the other. This reproduces the false-density artifact from
`ingest-identity-and-amendment.md` **and** makes the frustration complex light up
a contradiction where there is only a changed mind. There is no real
contradiction: X′ **supersedes** X. The graph cannot see supersession because the
correction was fed as an addition.

## 3. Correct pipeline — the dialogue acts on the note

- The note enters as an authored claim at some confidence.
- The dialogue enters as a **reasoning artifact** whose output is a set of
  **operations on existing claims**, not a peer node.
- The active graph re-projects: X′ is what the reasoning complex sees; X and its
  defeat live in the historical layer as provenance.

The dialogue does not add a node beside the note; it **acts on** the note.

## 4. Proposed operation vocabulary (starter set — to be ratified)

This is the actual interface between "I had a thought" and "the graph changed."
Everything above is only as real as this list is precise.

- `supersede(claim C, claim C′, warrant W)` — C′ replaces C in the active
  projection; C is retained in history with W as the reason.
- `attach_defeater(claim C, defeater D)` — records that C is contested and how.
- `record_warrant(warrant W, links {C, C′})` — the reasoning linking initial and
  final positions.

Open for the builder to assess against real exported dialogues: whether
`retract`, `split`, `merge`, and `confidence_adjust` are also required, and
whether warrant is a first-class node or an edge annotation.

**Distinct from version-supersession.** This claim-level `supersede(C, C′, W)` —
warrant-bearing, a reasoning act — is a different relation from the note-version
`supersedes(v1, v2)` in `ingest-identity-and-amendment.md` §4A (no warrant, a
file edit). They are orthogonal and must be distinct rel-types in distinct
structures; they must not share the same edge type or store. Separating version
history out of the balance-fed semantic edge store (that note's Constraint 2) is
a prerequisite for implementing this vocabulary without collision.

The full treatment of these operations as **reasoning paths** — three-place,
warrant-bearing, built on a fiber substrate, typed by assertion authority — is in
`the-edge-model.md`; their **dynamics** — proposed→certified states, the
authored-content gate, grounding maintenance, and the depth / γ^d decay math — are
in `supersession-lifecycle.md`. Note in particular that the committed
`derived_from=[C]` is corrected there (§4.2): a revision grounds on its warrant's
anchors, not on the claim it replaces.

## 5. Recursion and its governor

The loop is the `recursive-strata.md` fixed-point iteration: ingest → dream →
derived insight re-enters the complex → the next dream studies a graph containing
its own prior conclusions (Kₙ = K₀ ∪ S₁ ∪ … ∪ Sₙ₋₁).

The governor that makes this *safe recursion* rather than feedback explosion is
the existing typed-strata + verdict-gate commitment: derived strata are typed as
derived, at a depth, and **never silently acquire authored authority**.
Promotion toward authored authority happens **only through an owner verdict**,
never by the mere fact that a dream produced an insight and the next dream
consumed it.

Without the governor, "always learning / reframing" is indistinguishable from
"always drifting, with provenance laundered behind it." From inside the loop,
**learning to reason and drifting-while-erasing-evidence look identical**; only
the typed strata plus the verdict gate distinguish them from outside.

The operations of §4 create edges that fall into the existing typed edge-budget
categories (grounding / lateral / cross-stratum), and derived dialogue
conclusions remain subject to the population damper (I5) and the confidence
damper (γ^d). The builder must confirm the operations compose with those
invariants rather than bypassing them — see **Q2**.

## 6. The study this enables

Stripped down: a longitudinal experiment. Hold a corpus; perturb it in two
distinct modes — **ingest events** (new authored material) and **sleep events**
(derived reasoning re-entering); measure how the complex evolves under the
alternation. This is **Track L with the recursive loop closed**; the graph's
trajectory through those two perturbation types is the object of study.

Precondition: the **verdict store**. "Study how the graph changes" yields signal
only if the changes can be labeled (this reframing was insight, that one was
drift; this supersession was correct, that one lost a distinction the owner cared
about). Without the verdict stream it is evolution with no readable fitness
function. Ordering (see `the-sacred-boundary.md` §4):
**verdict store → close the recursive loop → run the longitudinal study.**

## 7. Open questions (require reading the code)

- **Q2.** What operations, if any, does dialogue ingest emit today? Cite. Assess
  the starter vocabulary {`supersede`, `attach_defeater`, `record_warrant`}
  against real exported dialogues in the corpus if any exist; recommend additions
  only if justified by an actual case, and cite it. State whether warrant is a
  node or an edge today. Confirm composition with the I5 population damper, the
  γ^d confidence damper, and the typed edge budgets — cite each enforcement
  point.
- **Q6 (shared).** Status of the two Track L prerequisites — provenance migration
  `--apply` and self-knowledge ingest — on which closing this loop depends.

## 8. Reconciliation

This is the concrete ingest-operation instantiation of `recursive-strata.md`;
the study is the closed-loop form of `live-adoption-and-longitudinal-harness.md`;
the Ambassador's role connects to `ambassador-as-reasoning-agent.md`. Builder to
propose cross-references or partially-superseded banners per repository
discipline.
