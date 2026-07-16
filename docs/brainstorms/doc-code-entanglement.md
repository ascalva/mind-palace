# doc-code-entanglement

Owner morning musings (2026-07-11, chat), restructured on append (§8, lossy capture beats
no capture). One train of thought: how meaning crosses representations — chunk grain,
docs↔code entanglement, docstrings as the Rosetta stone.

## 2026-07-11T09:30:00Z (captured)

```capsule
topic: doc-code-entanglement
date: 2026-07-11

decisions: []   # directions, not decisions — nothing ratified here

open_questions:
  - SMEAR: different chunk sizes resolve the same document differently — "a smear of
    resolution along the embedded vector space." Multi-scale embedding as an ensemble of
    grains per document. NOTE the collision: the source-set work (2026-07-03) deliberately
    confirmed single-scale-at-chunk-grain; this thought is supersession-shaped against
    that decision and needs evidence, not enthusiasm.
  - ENTANGLEMENT: theory/design docs and code reference each other — "entangled ... not in
    the same embedding region but there's a latent connection." Cosine proximity cannot
    see it; the connection is REFERENTIAL, not distributional. Which layer carries it?
  - ROSETTA: "notes and dialogue can more easily latch on to code semantics through ...
    well formed documentation wrapping the code." Docstrings as the translation layer
    between owner-language and code semantics. Standardize docstrings? Enforced how?
  - EDGES: "that might need to be edges that we help form or at least guide" — the first
    legitimate fiber-minting use case: today NOTHING mints E_geom fibers (2026-07-10
    survey; balance math runs on recomputed cosine only). Doc↔code reference edges are
    observer-independent and deterministic (AST + explicit citations), which is exactly
    the class the-edge-model.md §2 assigns to deterministic ingest, geometry authority —
    no Dreamer judgment, no blessing gate needed.

parked:
  - decision: multi-scale ("smear") embedding vs the standing single-scale-at-chunk-grain
      decision
    default: single-scale stands (2026-07-03 source-set decision; k× storage + retrieval
      fusion complexity not yet paid for)
    re_entry: a measured retrieval failure attributable to grain mismatch (query resolves
      at document grain, corpus embedded at chunk grain, or inverse) — the founding corpus
      + eval harness can run this as a CHEAP offline experiment (embed at 2-3 grains,
      measure hit overlap + rank divergence) before any store change
  - decision: docstring standard (format, required sections, why-not-what discipline)
    default: CONVENTIONS "comment the why" only; no format standard
    re_entry: the doc↔code edge experiment shows extraction quality gated on docstring
      form; or A8 lands and the orchestrator drafts the convention as a design note for
      owner ratification

next_steps:
  - Cheap, deterministic, additive — docstring extraction into the code-snapshot ledger
    (ops/code_snapshot.py already parses every AST; a docstrings column/table gives the
    Rosetta layer a queryable home + a per-commit doc-coverage metric for the evolution
    study). DEFERRED until bp-007 merges (it owns ops/** right now — collision).
  - Reference-edge inventory (read-only experiment): walk docstrings + design notes for
    explicit cross-references (path:symbol mentions, design-notes/*.md citations,
    [[note]] links) and count the latent edge set before deciding to mint any.
  - The smear experiment per the park re-entry above.
  - When drafted (post-A8 or owner hand): a design note tying this to the edge model —
    doc↔code reference edges as deterministic E_geom fibers, provenance-aware (code is a
    sensed stream per code-as-sensor-stream ruling; docstrings are its English shadow).

references:
  - docs/brainstorms/code-as-sensor-stream.md        # code = sensed stream; docstrings are its prose face
  - docs/design-notes/the-edge-model.md              # §2: deterministic ingest lays fibers
  - core/stores/sourceset.py                         # the single-scale decision this smear idea presses on
  - docs/findings/finding-0021.md                    # code as external corroboration — entanglement, evidenced
  - ops/code_snapshot.py                             # the AST walk the docstring layer rides on
  - scripts/ingest_self_knowledge.py                 # docs-as-curated; the bridge's other bank
```

## 2026-07-11T10:05:00Z (captured — continuation)

```capsule
topic: doc-code-entanglement
date: 2026-07-11

decisions:
  - Code, comments, and documentation are NOT authored-dialogue corpus (owner). They must
    never enter under an authored class — confirms and sharpens the code-as-sensor-stream
    ruling.
  - The Rosetta (docstrings) represents a STATE TRANSITION between English and code —
    the layer that connects theory/strata to code meaning.
  - The code sensor is a PROJECTION MAPPING from an agent into the OBSERVED stratum
    (owner: "it belongs as an agent that is projection mapping into the observed strata
    layer") — i.e., φ_code in the axis note's §3.7 interpreter formalism, targeting the
    observed layer (OBSERVED under the current enum; a₂ author-sensed under the axis).
  - Direction to finalize: observations ON the code should help DETANGLE semantic threads
    in the strata — code semantics as a disambiguation instrument over the corpus.

open_questions:
  - Observation schema: what does one code-observation row carry? (candidate: commit sha,
    symbol/qualname, docstring text, references-out [paths/notes/symbols], header type)
  - Same observed store as biometrics (sensor_readings, DuckDB, dormant) or its own
    table? Same handoff seam (SensingHandoff → ObservedView) either way?
  - The detangling consumer's lane split: DETERMINISTIC references (doc cites note, note
    names symbol) = geometry-authority fibers laid by ingest (the-edge-model §2) vs
    SEMANTIC disambiguation (which thread does this code support) = interpreted proposals
    at dreamer-proposed authority. Two lanes, never one.
  - Firewall compliance: OBSERVED is structurally mirror-opaque (MIRROR_READABLE) — the
    detangler must be correlator-family (reads observed + interpreted, outputs interpreted
    proposals; never writes authored). Confirm against observed-iot §2 safety rules.

parked:
  - decision: when code observations enter the corpus proper (vs the ops ledger today)
    default: ledger-only stands (PD-5 event-log default) until the projection design note
      is ratified
    re_entry: the design note (draft gated on A8 or owner hand) is ratified; or a
      detangling experiment on the ledger alone proves the value and demands the seam

next_steps:
  - Design note to draft (post-A8 or owner hand): "code-observation projection" — φ_code
    into the observed stratum, schema, handoff seam, two-lane consumer split, firewall
    compliance; written against the CURRENT ratified reality (OBSERVED/ObservedView) with
    an explicit a₂ cross-map so it survives the axis ratification.
  - The read-only reference-edge inventory (previous capsule) is now ALSO the feasibility
    probe for the deterministic lane.

references:
  - core/sensing.py                       # SensedObservation / ObservedView / SensingHandoff — the seam
  - docs/design-notes/authorship-distance-axis.md   # §3.7 φ_s formalism; a₂
  - docs/design-notes/observed-iot-and-cross-source-synthesis.md  # correlator safety rules (§2)
  - docs/brainstorms/code-as-sensor-stream.md       # the ruling this finalizes
```

## 2026-07-16T17:24:00Z — the SMEAR is one of a recurring family: scale-as-a-dimension (σ-fibers, conversation-layers, chunk-smear)

> Owner connected the parked SMEAR (multi-scale chunk embedding) to two threads seeded today —
> σ-fibers (cross-strata brainstorm) and the L0/L1/L2 conversation-sensor layering. Three arrivals at
> the same shape in one day; recording the pattern, NOT reopening the smear's parked decision (which
> stands — supersession-shaped against single-scale-at-chunk-grain, needs evidence via the offline
> grain experiment, not enthusiasm). Design musing; no build.

```capsule
topic: doc-code-entanglement (smear ↔ the multi-resolution family)
date: 2026-07-16

decisions: []   # a recurring DIRECTION observed across three brainstorms — nothing ratified

open_questions:
  - THE PATTERN: three ideas share one structure — don't commit to ONE resolution, retain a FAMILY
    indexed by a scale parameter, and treat position-in / persistence-across the family as signal.
      • σ-fibers: scale = σ (mirror-graph edge threshold); signal = a connection's persistence across σ
        (literally a filtration / persistent homology).
      • conversation-layers: scale = depth (L0 raw → L1 summary → L2 references); signal = the zoom
        itself (navigate intuition→code at the depth you need).
      • chunk-smear: scale = chunk grain; signal = a document's "smear" across the embedding space at
        multiple grains (an ensemble of resolutions per document).
    Is "scale as a first-class dimension" a pattern the system should NAME ONCE (a sensor/representation-
    agnostic stratification instrument), rather than re-deriving it per feature?
  - THE SHARED BOTTLENECK (the load-bearing observation): for all three, PRODUCING the scale-family is
    the cheap part — the machinery often already computes it (bp-049 already builds every G_σ; the
    embedder can embed at k grains; the transcripts already carry L2). The HARD part, and the real
    design object, is the FUSION / GATING instrument that makes the extra resolution net-positive
    instead of net-noise: σ-fibers needs a strength→surfacing gate, smear needs a retrieval-fusion
    rule, conversation-layers needs the privacy-gradient ordering (L2→L1→never-L0). Without the fusion
    rule, multi-scale just multiplies cost and drowns signal.
  - THE TEMPLATE ALREADY EXISTS: bp-049's §8 `select` (widest near-optimal plateau, not the knife-edge
    max) IS a fusion instrument over the σ-scale-family — it consumes a scale-curve and returns a
    robust point. It's a worked example of "how to collapse/navigate a scale-family responsibly." The
    other two fusion rules may be able to borrow its shape (robustness-over-peak, persistence-weighted).

parked:
  - decision: multi-scale ("smear") embedding vs single-scale-at-chunk-grain
    default: UNCHANGED — single-scale stands; the smear is supersession-shaped and needs the offline
      grain experiment (embed 2-3 grains, hit-overlap + rank-divergence on the founding corpus) first.
    re_entry: UNCHANGED — a measured retrieval failure attributable to grain mismatch (see the
      2026-07-11 capsule). This meta-observation does NOT lower that evidence bar.
  - decision: name "scale-as-a-dimension" as one cross-cutting pattern / instrument
    default: NOT named — three data points is a resonance, not yet an abstraction worth a design note.
    re_entry: a Fable+xhigh design pass on ANY of the three (σ-fibers is the warmest) surfaces a fusion
      rule general enough that the other two would reuse it — then lift the pattern into its own note.

next_steps:
  - No new work. When the σ-fibers / cross-strata Fable pass runs, have it ASK whether its fusion/
    strength instrument generalizes to smear-retrieval-fusion + conversation-layer-navigation before
    committing to a σ-only design — cheapest moment to notice the shared abstraction.
  - The smear's own cheap offline experiment remains the gate for THAT thread specifically.

references:
  - docs/brainstorms/cross-strata-and-multiscale-dreamers.md  # σ-fibers capsule (scale = σ)
  - docs/brainstorms/conversation-transcripts-as-latent-sensor.md  # L0/L1/L2 layering (scale = depth)
  - core/stores/sourceset.py  # the single-scale-at-chunk-grain decision the smear presses on
  - eval/harness/sweep.py §8 `select` (bp-049)  # a WORKED fusion instrument over a scale-family
```
