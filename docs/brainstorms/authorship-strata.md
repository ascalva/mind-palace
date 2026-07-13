# authorship-strata

Owner realization (2026-07-13, chat, out of the bp-026 / core-query-protocol reference-graph
work): the system's data layers aren't a flat set of "kinds" — they **sit naturally in the
stratum model as a derivation-depth climb**, and the **artifact chain IS that stratification**.
"Authored are MY thoughts, my intuition; dialogue are curated discussions we've had, sits on
top; then observed, which is the code." Design notes and brainstorms — long treated loosely as
"the corpus" — are really the **dialogue** layer: agent-synthesized syntheses of owner↔agent
discussion, NOT the owner's verbatim notes. This capsule is the durable home for the
realization; finding-0068 is its reference-graph-specific routing into the dn-core-query-protocol
fable-vet.

## 2026-07-13T15:55:47Z (captured)

```capsule
topic: authorship-strata
date: 2026-07-13

the_realization:
  - The data layers form a DERIVATION-DEPTH stratification, and the artifact chain (brainstorm →
    design note → build plan → journal, findings looping back) is literally that climb:
      workflow  (build-plans, journals)       depth 2  — derived from dialogue: plans GRADUATE from notes
         ↑ graduate            ↓ findings
      dialogue  (design-notes, findings, brainstorms)  depth 1  — curated owner↔agent discussions, ON TOP of authored
         ↑ brainstorm
      authored / mirror  (the owner's vault)  depth 0  — K₀; the owner's thoughts, intuition, VERBATIM
      -----
      observed  (code)  — the ORTHOGONAL axis: not derived from the owner's mind, SENSED from the
                          codebase; firewalled from authored (the mirror boundary); referenced by all layers.

provenance_grounding:
  - The layers are the existing PROVENANCE model made structural: authored/mirror = AUTHORED_SOLO
    (the vault, MIRROR_READABLE — the owner's verbatim notes); dialogue = the "authored-DIALOGUE"
    category (owner ruling 2026-07-11: "code, comments, and documentation are NOT authored-dialogue
    corpus"); observed = sensed exhaust (code_observations). workflow is a fourth: agent-authored
    narration of work-motion (build-plane artifacts, CLAUDE.md's "how work moves" layer).
  - KEY correction this surfaced: the reference graph's current `corpus` kind is DIALOGUE (docs/
    design-notes|findings|brainstorms), NOT the owner's authored mirror. The vault (true corpus/
    mirror) is not in the graph yet — reference_edges reserves `corpus_kind='digest'` for it.

what_it_buys:
  - The reference-graph node-kind vocabulary `{code, mirror, dialogue, workflow}` FALLS OUT of the
    stratification — it's this picture read as node kinds, which is why it feels natural not arbitrary.
  - It predicts WEIGHTING: recursive-strata's γ^d damps derived nodes by depth. The owner's raw
    thoughts (depth 0) weigh most in reasoning; a build-plan's citation (depth 2) least. The stack
    is a PRIORITY ORDER, not just a taxonomy.
  - The mirror firewall gets sharper: it's the authored↔observed boundary; dialogue sits between,
    and keeping the layers typed (not one flat "corpus") preserves the seam the firewall protects.

the_open_tension_stratum_overload:
  - "Stratum" ALREADY has a precise meaning: the Dreamer's auto-derived layers Sₙ over K₀
    (recursive-strata.md §2 — derivation depth of the AGENT's autonomous synthesis, γ^d-damped).
  - The owner's authored/dialogue/workflow climb is STRUCTURALLY the same shape (derived-on-top,
    depth-damped) but is an AUTHORSHIP / PROVENANCE-depth axis, not the Dreamer's synthesis depth.
  - OPEN: are these ONE mechanism (authorship depth and Dreamer depth are the same γ-graded tower)
    or TWO parallel axes (a note authored at dialogue-depth 1 can ALSO be Dreamer-elaborated to
    stratum Sₙ)? This is the crux the fable-vet must rule — probably two axes that compose (a
    provenance depth × a derivation depth), but that needs the real formalism.

open_questions:
  - Does the vault (mirror) enter the reference graph (digest-addressed corpus), making `mirror` a
    live node kind — and if so, is a mirror-note→dialogue-note citation even meaningful/extractable?
  - Do findings (which loop workflow → dialogue) get their own placement, or are they dialogue?
  - Does workflow subdivide (plans vs journals vs PROGRESS) by depth, or is it one layer?
  - How does this authorship axis interact with edge-dynamics' fibers (citation) vs dispositional
    (supersession) edge classes — is a "graduate" edge (dialogue→workflow) a fiber, a cross-stratum
    edge, or a new kind?

parked:
  - decision: graduate this to a design note (its own, or a section of the recursive-strata /
    provenance family)
    default: stays a brainstorm; the reference-graph slice is handled via finding-0068 →
      dn-core-query-protocol's fable-vet (the node-kind vocabulary)
    re_entry: an owner-opened FABLE session — this is foundational taxonomy/provenance design
      touching the mirror firewall + recursive-strata + the artifact chain; NOT opus/sonnet work.
      Likely feeds/becomes a design note broader than dn-core-query-protocol alone.

next_steps:
  - The dn-core-query-protocol fable-vet folds `{code, mirror, dialogue, workflow}` into its §2.1/
    2.4/3.1 scope grammar (finding-0068). If the realization proves broader than the reference
    graph (the weighting axis, the firewall sharpening), it earns its own design note.

references:
  - docs/findings/finding-0068.md   # the reference-graph-specific routing of this realization
  - docs/findings/finding-0065.md   # the workflow-kind ruling this refines
  - docs/design-notes/core-query-protocol.md  # draft; the node-kind vocabulary lands in its §2.1
  - docs/brainstorms/core-query-protocol.md   # where the reference-graph thread lives
  - docs/design-notes/recursive-strata.md + recursive-strata-amendment.md  # the Sₙ / γ^d meaning of "stratum"
  - docs/design-notes/observed-data-and-the-assistant-tier.md  # the mirror firewall (authored↔observed)
  - docs/design-notes/code-observation-projection.md  # the 2026-07-11 "not authored-dialogue corpus" owner ruling
  - core/provenance.py (AUTHORED_SOLO / authored-dialogue / observed); core/stores/reference_edges.py (corpus_kind='digest' reserved for the vault)
```
