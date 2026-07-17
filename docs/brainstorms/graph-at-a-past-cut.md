# Graph at a past cut — temporal memory, the three gauges, and wall-clock bookmarks

## 2026-07-17T17:30Z

> Fable/xhigh design pass (owner-chartered mid-session: "finalize that thought… think it thoroughly
> and rigorously, based on the current system, be accurate, use the appropriate math and tools").
> Seeded by the bp-059 grounding gap (`MirrorView` has no cut restriction) and the owner's two
> questions: *"can we study two events that happened in the past, like a memory — scope the query to
> an interval that already passed?"* and *"do we decorate the global clock with wall clock — not to
> use it, but as bookmarks, so 'were these two connected 5 days ago' and 'how did that commit impact
> the connectivity between A and B' are answerable?"* Every claim below carries its label:
> **(grounded path:line)**, **(checked numerically)**, **(theorem — standard)**, or
> **(open — what would settle it)**.

```capsule
decisions:
  - id: D1-two-pasts
    text: >
      Separate the two pasts. The TEMPORAL past (event order, proper time, downsets,
      supersession chains) is fully recorded and queryable today — the spine is the history
      layer. The ASSOCIATIVE past (the σ-graph as it stood at a bygone cut) is NOT constructible
      from the built path: MirrorGraph.build(view, *, sigma) takes no cut
      (core/dreaming/graph.py:32-40) and MirrorView.project reads current store state
      (core/mirror.py:96-101). bp-059's v1 latest-cut pin is the correct near-term posture;
      everything below is about what lifts it.

  - id: D2-substrate-already-retains
    text: >
      THE discovery of this pass: retro reconstruction is a pure function of data the substrate
      ALREADY retains, by constitutional design. The chain: a certified cut's frontier pins
      (chain-key, position) per doc (CertifiedCut, core/temporal/spine.py:216-229) → the versions
      store maps (doc_id, version_seq) → digest, append-only, byte-for-byte preserved even across
      the one owner-gated rekey (core/stores/versions.py, header invariants) → the RAWSTORE maps
      digest → verbatim bytes, content-addressed, immutable, "raw is sacred"
      (core/stores/rawstore.py:1-8) → re-chunk + re-embed regenerates vectors, a path the design
      anticipates verbatim: "re-embed from the raw store if the model changes" (core/ingest/embed.py:6).
      NO git archaeology, NO new retention infrastructure, NO core schema change. The vector store
      is current-only by design (vectorstore row `digest` = "the source note's CURRENT version",
      core/stores/vectorstore.py:30) — vectors are a derived, regenerable layer; that is exactly
      why the past is recoverable.

  - id: D3-rowsource-seam
    text: >
      The reconstruction is EVAL-SIDE constructible through an existing seam: RowSource is a
      Protocol (core/mirror.py:54-60), and MirrorView.project(source) accepts any implementor —
      a HistoricalRowSource serving rows-as-of-cut (from D2's chain) passes the Invariant-6
      __post_init__ firewall check UNCHANGED. This corrects bp-059 §11's parked re-entry
      prerequisite: the named blocker was "a core/ plan adding downset restriction"; the accurate
      prerequisite is an eval-side adapter plan (finding-0100). The only genuinely new mechanism
      is deriving the frontier AT a past commit (see O1).

  - id: D4-three-gauges
    text: >
      "The graph at cut c" is not one observable but three, distinguished by gauge; an instrument
      must declare which it computes (the evidence-pinning discipline extends — the gauge
      fingerprint joins the grid and cut in every reading):
      (a) ANCHORED — today's vectors, membership-at-c: node set = chains whose first version
      event ≤ c, vectors = current. Needs NO historical content at all — membership derives from
      the versions chains alone. Monotone growing (modulo tombstones) ⇒ the (σ, cut) family is a
      genuine two-parameter filtration; buildable NOW at note grain on top of bp-059's module.
      (b) RETRO — content-at-c (frontier → digest → rawstore bytes), re-chunked/re-embedded in
      the CURRENT gauge (_config_fingerprint, core/dreaming/shadow.py:94). Faithful geometry of
      the then-corpus, in a fixed present gauge — comparable across c.
      (c) ARCHIVAL — the THEN gauge (config-at-the-time recoverable from git; model weights may
      not be). Answers "what did the palace think then" vs retro's "what does the present mind
      see in the past corpus." Gated; lowest priority.

  - id: D5-conditional-monotonicity
    text: >
      The laws of the cut direction, established and numerically checked (scratchpad
      check_cut_math.py / check_edit.py, 2026-07-17):
      (i) WEIGHTED RAYLEIGH (theorem — standard; checked: C(0,2) .5437→.5881 on a weight
      increase, →.4548 on a decrease): effective conductance is monotone non-decreasing in each
      edge WEIGHT. Under bp-060's weighted measure w = cos^α·exp(…), a conductance rise between
      cuts requires ≥1 edge-WEIGHT increase — a new edge is the 0→w special case, and an EDIT
      that moves two notes closer raises conductance with NO new edge. CN-3's "a rise requires
      new edges" is the unweighted shadow of this law → finding-0099; bp-060 item 6 amended.
      (ii) GROWTH MONOTONICITY (theorem — maximin over a superset of paths; checked: σ* equal,
      conductance .3826→.4381 under pure addition): on an edit-free interval both σ*(A,B;·) and
      conductance are non-decreasing in c.
      (iii) EDITS BREAK IT, ATTRIBUTABLY (checked: a bridge edit drops σ* .7071→0): identity
      persists (doc_id), the vector moves. Therefore a DROP in the memory curve on an interval
      is a CERTIFICATE that an edit/tombstone moved things apart — measurable forgetting/drift —
      and the attribution set for ANY cross-cut change is the enumerable Δ-elements (added
      chains, edited chains, tombstoned chains, hence weight-changed edges), each verifiable
      leave-one-out. CN-3's reconnection discipline generalizes verbatim to the signed case.

  - id: D6-note-grain-identity-solved
    text: >
      Identity transport across cuts at NOTE grain is ALREADY BUILT: doc_id is constant along a
      version chain (versions store, append-only; rename carries doc_id via the catalog,
      bp-031; the owner-gated rekey preserves rows byte-for-byte). So cross-cut pair queries
      (A,B) at note grain are well-typed today — no waiting on uuid-identity. uuid-identity
      remains the prerequisite ONLY for claim/idea grain (CN-6's π, Track D, SF-a). This softens
      the identity story materially: the memory curve at note grain has no identity gate.

  - id: D7-memory-curve-unification
    text: >
      The owner's memory questions become one object: the MEMORY CURVE σ*(A,B; c) over certified
      cuts (with its conductance companion C(A,B; σ,t,c)). "Were these two connected 5 days
      ago" = evaluate at the resolved cut(s). "Connections I forgot I had made" (CN-3's
      reconnection) = the JUMP POINTS of the curve — Δ-conductance spikes are the smooth shadow
      of the same births. "How did that commit/note impact the connectivity of A,B" = the
      EVENT-IMPACT QUERY: Δσ* and ΔC between the bracketing cuts c⁻ (event excluded) and c⁺
      (event included), attributed leave-one-out — bp-060's reconnection machinery pointed at a
      NAMED event instead of scanning for spikes. Anchored gauge is the default for all of these
      (fixed geometry ⇒ differences mean membership/structure, not embedding drift).

  - id: D8-wall-bookmarks
    text: >
      The owner's wall-clock question, answered: wall time enters as a COORDINATE CHART on the
      cut poset — bookmarks for lookup — and NEVER as an ordering key or an index coordinate
      (Law C4 intact; WALL stays atlas-uncovered and can never type-check inside an argument
      chain). The substrate already records the annotations: versions.at is a wall timestamp on
      every version row (core/stores/versions.py, Version.at), the run ledger records
      started_at, and COMMIT-certified cuts carry git committer dates. What is missing is only
      the RESOLVER: wall-range → cut interval. Its contract: INTERVAL-VALUED (a human phrase like
      "5 days ago" maps to the set of certified cuts whose bookmarks fall in the range, plus the
      bracketing pair), and AMBIGUITY-WIDENING (clock skew, DST, sparse cuts ⇒ widen the
      interval and say so — never silently pick). Wall appears in the QUERY resolver only; every
      reading's index tuple remains (σ, t, cut). Event-anchored queries ("after that commit")
      need no wall at all — they resolve causally through the spine.

  - id: D9-legality-and-refusal
    text: >
      Retro cuts must still be CERTIFIED. For the mirror stratum the certificate class is COMMIT
      (spine.py:262-267) and a past commit is exactly as atomic as the present one — the mirror
      stratum's certifiable-cut set is (essentially) the commit history, so retro cuts are
      first-class, not merely sampled. Refusal cases, fail-closed: (a) a purged rawstore blob
      (delete exists ONLY on the owner purge path, rawstore.py:51-56) ⇒ the reconstruction
      refuses-and-names the missing digest, never interpolates; (b) an uncertifiable frontier ⇒
      no reading (CN-1's tooth, unchanged); (c) archival gauge without the then-model ⇒ refuse
      archival, offer retro.

parked:
  - item: Building ANY of this (HistoricalRowSource, memory curve, resolver, event-impact)
    re_entry: the connectivity tranche lands (bp-059..061 complete) — bp-059's σ*/MST module is
      the engine every memory-curve evaluation calls; then graduate a design note from this
      capture (the normal gate; no build from a brainstorm).
  - item: memory curve v1 (anchored, note grain) as the first follow-on plan
    re_entry: same gate; candidate next-plan after the tranche — cheapest of the family (needs
      only versions-chain membership + bp-059's module; no rawstore reads, no re-embedding).
  - item: frontier-at-commit derivation (the one new mechanism)
    re_entry: the design note for this arc decides its home (eval-side digest-join vs a small
      core/temporal helper) — see O1.
  - item: RETRO gauge (re-embed content-at-c)
    re_entry: memory curve v1 ships AND a question needs then-geometry (e.g. "was this cluster
      tight before I refactored it") — retro is the first gauge that reads the rawstore.
  - item: ARCHIVAL gauge
    re_entry: an owner question genuinely needs "what did it think then" AND the then-model is
      available; config-at-SHA recovers from git, model weights may not.
  - item: claim/idea-grain memory curves
    re_entry: uuid-identity lands (π; CN-6/Track D/SF-a — the already-registered consumers).

open_questions:
  - id: O1
    q: >
      Frontier-at-a-past-commit: the versions store orders by version_seq with a wall `at`
      annotation, but no row records WHICH commit it was ingested at. Code does not settle the
      derivation. What would: digest-join (git tree at SHA → content digest per doc → find the
      chain position with that digest — exact for git-tracked sources, which the current 13-chain
      mirror corpus is), or an ingest-ledger commit column going forward (a small additive
      schema act). The design note decides; the digest-join needs zero writes.
  - id: O2
    q: >
      Tombstone semantics for anchored membership: vault deletes only TOMBSTONE (rawstore.py:54)
      — confirm authored-note tombstones are visible to the membership function so anchored
      node sets honor them (a tombstoned chain leaves the graph at its tombstone cut; the
      monotone law becomes "monotone modulo tombstones," and a tombstone is an attributable
      Δ-element like an edit).
  - id: O3
    q: >
      Wall bookmarks for TROUGH/HANDOFF-certified cuts (ops/eval strata): what annotation rides
      those certificates? COMMIT cuts have committer dates; check TroughState/handoff evidence
      when designing the resolver.
  - id: O4
    q: >
      Cut density vs query resolution: per-commit density serves the mirror stratum well; is the
      trough cadence dense enough for ops-strata memory queries, or does the resolver's
      interval-widening carry the honesty burden alone?

next_steps:
  - finding-0099 (math): the weighted-Rayleigh refinement of CN-3's attribution law; bp-060
    item 6 + §8 amended with a banner (done this session, pre-blessing).
  - finding-0100 (design): retro constructibility via the RowSource seam + rawstore retention;
    corrects bp-059 §11's named prerequisite; registers the wall-bookmark resolver contract.
  - AFTER the tranche builds: graduate this capture into a design note
    (dn-graph-at-a-past-cut / temporal-memory-instruments) — the pre-registration for the
    memory curve, the three gauges, the resolver, and the event-impact query.
  - The cross-strata sweep note (docs/brainstorms/cross-strata-substrate-sweep.md) gains a
    phase-B reader: memory curves over the PUBLIC band are the natural longitudinal instrument
    once both land.

references:
  - core/mirror.py:54-60 (RowSource Protocol — the seam), :96-101 (project reads current state)
  - core/dreaming/graph.py:32-40 (MirrorGraph.build — no cut)
  - core/stores/vectorstore.py:28-37 (row schema: id/digest-CURRENT/source_path/text/vector —
    current-only, regenerable by design)
  - core/stores/versions.py (append-only (doc_id, version_seq, digest, at); rekey preserves
    rows byte-for-byte; balance math structurally excluded)
  - core/stores/rawstore.py:1-8, 28-56 (content-addressed, immutable, dedup; delete = owner
    purge only)
  - core/ingest/embed.py:6 ("re-embed from the raw store if the model changes")
  - core/ingest/sync.py:83-119 (digest short-circuit; catalog doc_id resolution; rename adoption)
  - core/temporal/spine.py:47 (versions → per-doc chains, produces digest), :216-229
    (CertifiedCut.frontier), :262-267 (mirror → COMMIT certificate)
  - core/dreaming/shadow.py:94 (_config_fingerprint — the gauge pin)
  - dn-connectivity-instruments CN-1 (index discipline), CN-3 (reconnection + Rayleigh);
    dn-global-event-clock GC-3 (certified cuts); bp-059 §3 Q1 + §11; bp-060 item 6
  - findings: 0090 (sidestepped as before), 0096 (structural-not-recall falsifiers), 0099 +
    0100 (this session)
  - numeric checks: scratchpad check_cut_math.py (C1 weighted Rayleigh: .5437→.5881 up /
    .4548 down; C2 growth: σ* equal, conductance .3826→.4381) and check_edit.py (bridge edit:
    σ* .7071→0.0000) — deterministic, reproduce with the seeds shown
```

---
**2026-07-17 (session-26) placement amendment — orientation for any future graduation of this
pass:** the σ*/conductance modules cited above live at their NEW home `core/graph/`
(`dn-core-graph-instruments`, warrant finding-0101; bp-065 executes). `eval/harness/
connectivity.py` / `conductance.py` are thin re-exporting instruments post-bp-065 — a design
note or plan minted from this brainstorm must cite `core.graph`, and any NEW math it needs
(versions-membership σ*(A,B;c)) graduates into `core/graph/` per the P6 standing rule.
