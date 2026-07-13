# core-query-protocol

Owner direction (2026-07-13, chat): every agent — orchestrator, ambassador, sensors, and a
proposed new reference agent — is a **scoped client of the core**, and what's missing is the
shared, typed **query language they are all clients of**. Two threads emerged: (A) the
protocol + the client-scope model + a new deterministic single-stratum agent archetype;
(B) a math observation — removing the time dimension collapses the edge vector field's
gradient part to a scalar, which is the Hodge gradient/harmonic split seen from the time
axis (a feed for `edge-dynamics` Lane B). Captured together, threads kept separate.

## 2026-07-13T05:01:27Z (captured)

```capsule
topic: core-query-protocol
date: 2026-07-13

decisions:
  - The reference substrate already exists and is live: data/reference_edges.sqlite,
    ~61,380 edges, indexed on corpus_ref/code_path/commit_sha, ref_type ∈
    {note-citation, path-mention, symbol-mention, design-ref}, with source_line. A
    "where/how-many references to doc X" query runs TODAY (code↔corpus).
  - It is CODE-ANCHORED: only corpus_to_code / code_to_corpus edges. There is NO
    corpus_to_corpus (doc→doc) edge — a plan's design_ref citing a note, a finding's
    links/[[name]] — which is exactly the finding-0059 pain (a note's stale count cited
    by two plans, with no visible citation graph). Closing it is a bounded extractor
    addition over docs/**.
  - The librarian is a DIFFERENT tool than a reference lookup: semantic RAG over the
    authored mirror (MIRROR_READABLE firewall, budgeter, selfcheck) — reasoning, not a
    deterministic graph query. "Test the librarian" is a separate axis; the real synthesis
    is (i) the reference graph as a retrieval signal for the librarian, and (ii) a distinct
    deterministic reference surface for the agent-bookkeeping need.

thread_A_the_protocol_and_the_archetype:
  - Reframing (owner, corrects an earlier false View-vs-agent split): agents are NOT of
    different kinds; they are all CLIENTS OF THE CORE that must speak a precise interaction
    protocol. The orchestrator itself is "an agent that knows how to properly interact with
    the core." What differs is CAPABILITY SCOPE: which strata a client may read, and whether
    it may only-read / read+propose / write.
  - The new archetype: a DETERMINISTIC SINGLE-STRATUM QUERY SERVER — the read-side dual of a
    sensor. Not a sensor (writes nothing), not the ambassador (no model, no cross-plane).
    Because it touches ONE stratum only (lateral edges, never cross-stratum), it drops the
    ambassador's ENTIRE governance stack: no cross-stratum budget, no firewall question, no
    model, no hallucination surface. Every answer is a verifiable query result, attestable
    exactly like a sensor's projection. "No model" is correct, not a compromise — reference
    lookup is deterministic.
  - The missing artifact (point 3): a STANDARD TYPED QUERY ALGEBRA over the core's strata.
    The existing MirrorView / ObservedView / OpsView / EffectView are already PARTIAL,
    capability-scoped sentences in that language, not yet unified. The single-stratum
    reference agent is its simplest well-typed sentence: read(one stratum, fibers, no time).
    The ambassador is a long sentence: read(mirror+curated+ops), reason, propose. Same
    grammar, different scope.
  - Edge taxonomy grounding (recursive-strata-amendment): FIBERS = warrant/citation edges
    (budgeted lateral OR cross-stratum by where they land; the cross-stratum ones are "the
    tower's building material"). SUPERSESSION lines are a SEPARATE class — "dispositional
    edges" — which the grounding-ratio walk MUST NOT traverse. The time dimension lives on
    the dispositional class, held apart from citation geometry on purpose.

thread_B_time_collapse_math_LaneB_feed:
  - Owner intuition: the edge model is a vector field (strength + direction); the direction
    comes from direction in TIME (the supersession/dispositional edges carry time); remove
    the time dimension (d → d-1) and the vector field collapses to a scalar.
  - Grounding (edge-dynamics.md): the edge model IS a 1-form (1-cochain). The Helmholtz/
    Hodge decomposition splits it uniquely+orthogonally into GRADIENT (= d₀φ, induced by a
    NODE POTENTIAL φ, a scalar field on states), CURL (triangle circulation), and HARMONIC
    (= ker L₁, dim = β₁ — the THREADS).
  - The precise mapping: the GRADIENT part IS a vector field whose whole content is a scalar
    φ on states; its direction is ∇φ, and if φ is a time-coordinate (or authorship-distance)
    the direction IS time-direction. Strip the time-potential and the gradient part
    COLLAPSES to φ — the owner's "d-1 → scalar," correct FOR THE GRADIENT PART.
  - The sharpening (the payoff): it is correct ONLY for the gradient part. The HARMONIC part
    has, by definition, NO scalar potential — it cannot be written as ∇φ — so it does not
    collapse; it is precisely what SURVIVES the collapse, and it is the β₁ threads the THREAD
    lens keeps. So Helmholtz already names time-derived (gradient/potential) vs
    time-invariant (harmonic loops). The owner's morning vector-field intuition and the
    existing hole/thread instrument are the same object from two sides.
  - Why it matters for the roadmap: Lane A samples STATIC snapshots (the d-1 slices) and
    measures β₁ / harmonic-persistence per slice — exactly the part that survives the
    collapse. The genuine TIME flow (how slices connect, direction on dispositional edges)
    is the parked Lane B / continuum. This framing sits right on that seam.

parked:
  - decision: graduate this brainstorm to a design note (brainstorm → design)
    default: stays a brainstorm; no design note yet
    re_entry: THE OWNER OPENS A FABLE-TIER DESIGN SESSION. The brainstorm→design pass is
      fable work (open architecture, unpinned interfaces, a cross-plane boundary ruling, and
      a math framing that feeds Lane B) — NOT to be drafted at opus/sonnet. This is the
      owner-requested fable-guard on the brainstorm→design process (2026-07-13).
  - decision: one design note or two
    default: undecided — likely TWO (an architecture note: the core-query protocol +
      client-scope model, with the reference archetype as its simplest case; and a math
      note / Lane B feed: the time→gradient collapse framing)
    re_entry: the fable design session decides the split at graduation
  - decision: shared live substrate vs. a build-time reference index
    default: undecided — "it's already live, make it useful for us" wants the workflow to
      query the daemon's stratum directly (max dogfooding, crosses the sacred boundary); the
      safe alternative is a separate build-time index (no crossing, duplicates the sensor)
    re_entry: the design pass rules on the-sacred-boundary question below
  - decision: does the sacred boundary permit build-time query of the live reference stratum
    default: PLAUSIBLY clean — the reference graph is corpus-STRUCTURAL (who-cites-what), not
      observed exhaust (not the mirror, not private interaction data) — but this needs an
      EXPLICIT ruling, expressed as a capability SCOPE, not a special case
    re_entry: the fable design session, referencing docs/design-notes/the-sacred-boundary.md

open_questions:
  - What are the query primitives of the core-query algebra, and how is capability-scope
    expressed (which strata × {read | read+propose | write})?
  - Is the reference agent a ReferenceView (library object a caller constructs) or a
    request-addressable service across the process boundary? "Takes requests, responds back"
    leans service; the single-stratum discipline holds either way.
  - Should the doc→doc extractor land first (retires finding-0059/0061's class immediately),
    independent of the larger protocol design?
  - Does the time-collapse framing change how Lane B models the flow (gradient = the
    time-potential channel to model; harmonic = the invariant to hold fixed)?

next_steps:
  - HOLD for a fable design session (the fable-guard above). Until then this brainstorm +
    finding-0062 carry the thread; no design-note edit, no build.
  - The doc→doc extractor MAY be split out as a small independent plan if the owner wants the
    finding-0059/0061 class retired before the full protocol is designed.

references:
  - docs/findings/finding-0062.md  # the direction finding this brainstorm expands
  - docs/findings/finding-0059.md  # the doc→doc-blindness instance
  - docs/findings/finding-0061.md  # the stale-baseline class the reference graph would guard
  - core/stores/reference_edges.py # the live substrate (61k edges) + its minimal query API
  - core/librarian/librarian.py    # the semantic-RAG tool (a different axis)
  - agents/ambassador/agent.py     # the heavy read-side client (the long sentence)
  - core/mirror.py, core/sensing.py, core/ops_view.py, ops/effects.py # the existing partial Views
  - docs/design-notes/recursive-strata-amendment.md # fibers vs dispositional edges; edge_budget types
  - docs/design-notes/edge-dynamics.md # the 1-form lift, Helmholtz split, THREAD lens, Lane A/B seam
  - docs/design-notes/the-sacred-boundary.md # the plane-crossing ruling this needs
```
