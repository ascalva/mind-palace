# Brainstorm — the hypothetical subspace: a TTL'd strata appendage for what-if reads

> Captured by the orchestrator from owner chat (2026-07-20, session-39, fable). Owner's seed,
> near-verbatim: *"a temporary subspace, a strata layer where items have a TTL, used as a strata
> layer appendage to temporarily see how a set of nodes and edges would connect to the knowledge
> graph … dispatch outer core agent to reason and 'dream' about how the subspace items relate or
> change overall graph behavior, detect influence … a hypothetical read on data."* One of the two
> brainstorms the owner queued for a fable pass (the other is the book-pedagogy rigor capsule,
> captured same session).

## 2026-07-20T21:28Z (session-39)

### The seed

Three moving parts, all owner-stated:

1. **A temporary subspace** — a strata-layer *appendage* whose items carry a **TTL**. You stage a
   candidate set of nodes and edges beside the durable graph to temporarily see how they *would*
   connect to the knowledge graph, without admitting them to the corpus.
2. **A dispatched outer-core agent** — reason/"dream" over graph ∪ subspace: how do the staged
   items relate to the whole, how do they change overall graph behavior — **detect influence**.
   (Leans directly on the inner/outer-core vocabulary: the dreamer is an outer-core agent, a
   client of the algebra.)
3. **The framing: a hypothetical read on data** — the operation is a *read* under a hypothesis,
   not a write to the corpus. Expiry is built in (the TTL); durability is not the default.

### Orchestrator scrutiny (chat-side, this session — connections, not decisions)

- **This is the counterfactual sibling of `graph-at-a-past-cut`.** That brainstorm reads the graph
  under a *temporal* hypothesis ("as of cut t"); this one reads it under a *counterfactual*
  hypothesis ("as if these items were in it"). Both are instances of one operation shape: evaluate
  the instruments over a hypothetical graph state without mutating durable state.
- **"Detect influence" has an obvious candidate metric already built:** the connectivity
  instruments (dn-connectivity-instruments; σ-sweep, spectral family). Influence ≈ the
  differential of instrument readings with-vs-without the subspace. The dreamer's report would
  then be grounded in measured deltas, not vibes.
- **Isolation smells like a View-firewall job.** A hypothetical read must be provably unable to
  contaminate durable state — kin to `MirrorView`/`ObservedView` seams. This is what makes it a
  clean first *consumer* of the outer ring: the machinery (staging store, TTL sweep, dispatch) is
  outer; the algebra it calls (graph math, instruments) is inner.

```capsule
topic: hypothetical-subspace
date: 2026-07-20

decisions:
  - The seed itself (owner): a TTL'd temporary subspace as a strata appendage; an outer-core agent
    dispatched to dream over graph ∪ subspace and detect influence; the whole framed as a
    HYPOTHETICAL READ on data. Seed only — no design decisions taken in this capture.

parked:
  - decision: whether this graduates into its own design note
    default: yes, but AFTER dn-inner-outer-core exists — it consumes the outer-core vocabulary
    re_entry: dn-inner-outer-core reaches draft; owner picks the next design slot

open_questions:
  - Where does the subspace live relative to the existing strata — a new stratum, or an overlay
    keyed to any stratum? Do flat/grouped retrieval see it by default, opt-in, or never?
  - What is "influence", operationally? Candidate: the diff of connectivity-instrument readings
    (σ-sweep, spectral) with vs without the subspace — a differential read.
  - Admission and expiry semantics: can a subspace item ever graduate into a durable stratum, and
    through which gate? What clock does the TTL run on (wall clock vs event clock — the
    global-event-clock G3 park is adjacent)?
  - Isolation mechanism: does the hypothetical read need its own View-firewall variant so
    contamination of durable state is structurally impossible, not conventionally avoided?

next_steps:
  - Hand to the dn-inner-outer-core design pass as the FIRST CONCRETE CONSUMER of the outer ring —
    ground the ring boundary against it; do NOT design the subspace there.
  - Its own design pass (fable) once inner/outer-core lands.

references:
  - docs/brainstorms/inner-outer-core.md                      # the vocabulary this consumes
  - docs/brainstorms/graph-at-a-past-cut.md                   # the temporal sibling of the same read-shape
  - docs/brainstorms/cross-strata-and-multiscale-dreamers.md  # dreamer dispatch patterns
  - docs/design-notes/agent-taxonomy.md                       # the dreamer as (outer-)core-resident agent
  - docs/design-notes/connectivity-instruments.md             # candidate influence metric (instrument diff)
  - docs/brainstorms/temporal-clocks-and-strata.md            # strata + TTL-clock adjacency
```
