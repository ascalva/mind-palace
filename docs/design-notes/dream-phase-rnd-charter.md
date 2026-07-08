---
type: design-note
id: dn-dream-phase-rnd-charter
status: draft
implementation: partial   # corpus-audit 2026-07 verification
created: 2026-06-26
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Dream phase R&D charter (feature-flagged OFF)

*Family tag → family 5 (the reasoning complex): the R&D charter for the interpretation engine (feature-flag OFF). See [`../NOTATION.md`](../NOTATION.md).*

**Status:** research & development track, **feature-flag OFF by default**. Not committed
spec; does not change the phased build. A detour to develop the interpretation engine; the
main build resumes at Phase 8 (airlock) afterward. Ties together and extends the Phase 7
dreamer + `dreaming-v2-interpreter-panel.md` + `recursive-dreaming-bounded-by-grounding.md`.

## Vision

The dream layer is the system's **subconscious**: deferred background sense-making that runs
in troughs, maintains the graph, and produces ranked _interpretations_ of the owner's mind —
hypotheses, never verdicts. It is where a second brain does the slow work the foreground never
has time for. It is also the highest-risk layer, because it is the one place the system reasons
over its own outputs.

## Two axes of "worker" — keep them straight (this is the crux)

The word "worker" was overloaded in discussion. There are two, on different layers:

1. **Interpreters — specialists by METHOD (this is the dream layer).** Same corpus, different
   algorithms, each emitting candidate pattern-claims + graph evidence; an adjudicator ranks by
   grounding. (See `dreaming-v2-interpreter-panel.md`.) Community detection, centrality,
   change-point, bridge detection, density clustering. Mostly model-free (the §9 deterministic
   floor); the model is earned only for narration and judging.
2. **Ingesters/Curators — specialists by SOURCE (this is NOT the dream layer).** Different data
   sources/sensors, each processed by a domain specialist into the **correct provenance pool**.
   This is the ingest + curation layer, not dreaming.

**Firewall rule (non-negotiable, this is where the trap is):** there is **no single shared
graph** that everything feeds. Source-specialists feed _their own provenance pool_ — authored
sources → the mirror; sensor/observed sources → the observed pool — **never one
undifferentiated graph**. The introspective dreamer reads the AUTHORED mirror only
(`MIRROR_READABLE`); observed exhaust can never seed an introspective dream. "Maintaining the
health of the graph" is the **Curator** (built, Phase 7), operating _within_ provenance
boundaries.

**Cross-source synthesis** (e.g. "sleep tracks the darker notes") is legitimate and valuable —
but it is an **assistant-tier read across both pools, marked `interpreted`**, not a mirror
dream. It never flows back into the authored mirror or the §15 baselines.

## Consensus vs adjudication

Agreement across independent interpreters/sources is a **confidence signal**, not a decision
**mechanism**. Feed agreement to the adjudicator as evidence strength; do not let "majority
vote" decide (groupthink = the persuasion failure). The judge decides on **grounding**;
agreement raises confidence; disagreement is information, not noise.

## The safety spine (recap — all three notes share it)

- **Grounding terminates in AUTHORED evidence**, every generation. Prior dreams are scaffolding,
  never evidence; the citation chain cannot loop within `interpreted`.
- **Confidence decays with interpretation-depth**, never compounds. Correct recursion compounds
  skepticism. Rank degrades with distance from ground truth.
- **Confidence (evidence) ≠ utility (usage).** Separate axes. Utility decides what to surface;
  grounding decides what to believe. Collapsing them makes the mirror a flatterer.
- **Instrumented.** Drift signatures (dreams-citing-dreams ratio, utility-up/grounding-down,
  confidence-up-with-depth) are alarmed on the Phase-11 gauge against the authored floor.
- **Outputs are `interpreted`**, never promoted to authored, never act except via the Phase-10
  gate.

## R&D plan for the dream track (behind the flag)

- **R0 — panel scaffold.** Generalize the single interpreter to a registry of deterministic
  interpreters over the authored mirror; each emits claims + evidence. No adjudication yet.
- **R1 — evidence-based adjudicator.** Extend `core/selfcheck.py` grounding into a ranker;
  output a confidence-ordered dream log with content-addressed evidence refs.
- **R2 — utility telemetry.** Track per-dream usage as a _separate_ axis; surface ranking uses
  both, never collapsed.
- **R3 — recursion, carefully.** Allow dreams as scaffolding input with depth tagging +
  confidence decay + the drift gauge watching. Build only after R0–R2 and the gauge exist.
- **R4 — cross-source assistant synthesis.** Reads observed + authored, marked interpreted,
  assistant-tier only. Never touches the mirror.
- **R5 — curated-graph dreaming + resonance.** Run the panel on a _curated_ corpus (a book) in its own graph (never the authored mirror); compute cross-graph resonance with the authored theme-clusters, interpreted-only. See `dreaming-on-curated-graphs.md`. Build after R0/R1.

## Open questions

- Interpreter set + how many before it is noise.
- Confidence-decay function; depth cap.
- A utility signal that reflects genuine help, not agreement (anti-gaming).
- Owner review UX for ranked / compounded interpretations (Phase-11 view).
