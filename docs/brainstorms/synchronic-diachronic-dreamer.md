# Brainstorm — the synchronic/diachronic dreamer: scoped dreaming with the algebra as tools

> Captured by the orchestrator from owner chat (2026-07-20, session-39, fable). Owner's seed,
> near-verbatim: *"the other next track I want to work on, so might need one last fable pass: the
> synchronic vs diachronic dreamer, dreamer scopes, algebra as the tools, connectivity, etc."*
> Third capture of the session (after hypothetical-subspace and the book-pedagogy addendum);
> queued as the fable pass AFTER dn-inner-outer-core.

## 2026-07-20T21:44Z (session-39)

### The seed

Four ingredients, owner-named, one track:

1. **Synchronic vs diachronic dreamer** — dreaming over the graph *at a cut* (structure-space:
   clusters, fibers, connectivity now) vs dreaming over the graph's *history* (trajectories, how
   ideas moved, drift/velocity). The diachronic dreamer is the known parked thread under
   dn-agent-taxonomy — blocked on the global-event-clock (G3).
2. **Dreamer scopes** — dream dispatch parameterized by the capability-scope algebra: which
   strata, which fibers, which time window, which instruments a given dreamer may read.
3. **Algebra as the tools** — the dreamer wields the query language/scope algebra; it is a client
   of the algebra, not the algebra (the inner/outer-core refinement, verbatim).
4. **Connectivity** — the instruments (σ-sweep, spectral family, the pending magnetic-Laplacian
   graduation) as the dreamer's senses.

### Orchestrator scrutiny (chat-side — connections offered, not decided)

- **The candidate unification: a dreamer = a scope-parameterized dispatch.** dn-agent-taxonomy
  already says role = scope signature; this track would make the dreamer the *worked example at
  full depth* — the dream dispatch scope carrying (strata selection, fiber selection, a
  time/world parameter, instrument grants). Under that reading, synchronic vs diachronic is not
  two agent kinds but **one axis of the scope**: the world-parameter says *which graph state(s)
  the dream sees*.
- **The same axis may absorb the hypothetical subspace.** Present read, past-cut read
  (graph-at-a-past-cut), and counterfactual read (graph ∪ TTL-subspace) are three values of the
  same world-parameter; diachronic = a read *across* cuts. If that holds, the subspace's design
  questions fold into this pass rather than needing their own note — one fable pass, as the owner
  suspects ("one last"). To be tested in the pass, not assumed.
- **Dependency shape.** (i) dn-inner-outer-core (in flight) supplies the vocabulary — the dreamer
  is outer-core, its tools inner-core; (ii) the diachronic *execution* half stays gated on G3
  (the pass can design the axis and park execution with a re-entry, honoring the existing park);
  (iii) the σ-sweep run (oq-0024, un-blocked) would give the instrument-as-senses claims real
  corpus readings to ground on — cheap to run before or alongside.
- **The magnetic Laplacian is tied in — three ways (owner asked mid-capture).** (i) *Directly, via
  an already-open decision:* dn-magnetic-laplacian's owner decision 2 (the parked oq-0021 "dream
  vocab") asks whether the arrow-aware census claim family — directed influence cycles,
  revision-effort asymmetry, retro-citations — enters the **dreamer's narration**, and with what
  language; it was parked "costs nothing until a lens plan exists." This pass IS the lens plan
  arriving, so it is the natural place that decision gets grounded for the owner to rule. (ii) *As
  a sense, with gate-honesty:* the direction-aware layer a dreamer may consume TODAY is the
  **combinatorial census** (gauge-immune invariants, rides the already-licensed Thread-C sweep);
  the operator build stays deferred behind ML-a's three gates — ratified, not to be relitigated.
  But the dreamer is a candidate **gate-opener**: if its directional needs demonstrably exceed the
  census, that is ML-a gate (ii) (census-insufficiency) opening honestly. (iii) *Conceptually, for
  the diachronic half:* direction is time's residue in the synchronic graph — a directed edge
  (supersession, citation, derivation) is a frozen record of a temporal event — so arrow-aware
  reads at a single cut are the candidate **clock-free v1 of diachronic dreaming** while G3 stays
  parked. Caution from the note itself: the diamond conjecture is REFUTED (no abelian/spectral
  object closes TA-c) — spectral direction-reading has proven limits; don't oversell it.
- **Reconciliation surface is large:** cross-strata-dreamer, sigma-fibers-and-multiscale-dreaming,
  recursive-dreaming-bounded-by-grounding, dreaming-on-curated-graphs, dream-phase-rnd-charter
  all speak about dreaming. The pass must say per-note extend/supersede — a supersession-lifecycle
  job, not a green field.

### Addendum (same session): laziness as a design principle for the whole machinery

Owner, near-verbatim: *"the use of algebra, edge compositions, temporal navigation via cuts — all
this machinery I would think could benefit from being lazy; the graph will grow, in size and time,
so efficient operations are necessary."*

Orchestrator scrutiny (offered, not decided):

- **The scope algebra is already the natural vehicle for laziness.** A scope expression is a
  *description* of a view, not the view — if expressions compose symbolically (meet/join/restrict/
  time-shift) and materialize only at the instrument boundary where an actual number is demanded,
  composition costs O(expression), not O(graph). The algebra becomes a query planner: build the
  tree, fuse/simplify algebraically, materialize once at the leaf. (The relational-algebra /
  lazy-DAG move; inner core holds the symbolic algebra, outer core holds the evaluators — clean
  ring alignment.)
- **Edge composition lazily = never materialize transitive closure.** A composed relation (e.g. a
  C-fiber chain action→commit→file→doc) stays an unevaluated composition; only the restriction
  actually demanded ("the chain through THIS node") evaluates. Eager closure on a growing graph is
  the quadratic trap.
- **Cuts want persistence, not copies.** "Graph at cut t" as a full rebuild is O(history) per
  read. Lazy = an append-only delta log with cuts as pointers and structure shared across views
  (persistent-data-structure discipline). The hypothetical subspace then falls out for free: an
  OVERLAY view (graph ∪ subspace) is the same mechanism as a cut view — cheap, composable,
  discardable. The diachronic dreamer walking cuts = sliding a window over the log, incremental.
- **Instruments need INCREMENTALITY on top of laziness.** A lazy view doesn't help if the leaf
  evaluation is a full eigensolve each time. Known moves: warm-started/perturbative spectral
  updates (few edges changed ⇒ perturbation theory, not recompute), locality (polynomial/k-hop
  approximations), digest-keyed caching of materialized views (the sourceset group-by-digest
  precedent). Sharp special case: subspace INFLUENCE is literally a perturbation problem — the
  with/without instrument diff IS the first-order perturbation term; computing it that way is both
  the efficient and the mathematically honest formulation.
- **The fable-level candidate unification: the lazy view IS the capability.** Materialization-on-
  demand through a scope means the scope check happens at the only place data becomes real — a
  scoped dreamer holding a lazy view structurally *cannot* read outside its scope. Laziness and
  the View-firewall (MirrorView/ObservedView kin) would be one mechanism, not two: the
  materialization boundary is the authorization boundary. If this holds, efficiency is not a
  bolt-on — it is the same design as the sacred-boundary enforcement. To be tested in the pass.
- **Laziness has costs — demand a cost model at the boundary.** Thunk buildup, latency spikes at
  materialization, cache invalidation. The honest counterweight: an unevaluated expression can be
  COST-ESTIMATED and refused *before* running (the memory-ceiling scheduler refusal, rule #8,
  extended to views) — an eager operation has already paid by the time you know. Laziness makes
  the refusal gate checkable; that is an argument FOR it, stated with its falsifier.

```capsule
topic: synchronic-diachronic-dreamer
date: 2026-07-20

decisions:
  - The seed itself (owner): this is the NEXT design track after inner/outer-core, likely the last
    fable pass of the arc — synchronic vs diachronic dreaming, dreamer scopes, the algebra as the
    dreamer's tools, connectivity as its senses. Seed only; no design decisions taken here.
  - LAZINESS as a requirement, not an optimization (owner addendum, same session): the algebra,
    edge compositions, and temporal navigation via cuts should be lazy — the graph grows in size
    AND time, so efficient operations are necessary. The design pass treats evaluation strategy as
    first-class, not an implementation detail.

parked:
  - decision: dispatch of the fable pass
    default: wait for dn-inner-outer-core to land (it supplies the outer-core vocabulary), then
      owner slots the pass
    re_entry: dn-inner-outer-core draft reviewed + committed
  - decision: diachronic EXECUTION
    default: stays gated on the global-event-clock (G3) — unchanged park from dn-agent-taxonomy
    re_entry: G3 lands, or the pass finds a clock-free v1 the owner accepts

open_questions:
  - Does the scope-parameterized-dispatch unification hold — is synchronic/diachronic (and the
    hypothetical subspace's counterfactual read) one world-parameter axis of the dream scope, or
    do the modes need structurally different dreamers?
  - Does hypothetical-subspace fold INTO this pass (one note) or stay its own graduation?
  - Per existing dreamer note (cross-strata-dreamer, sigma-fibers-and-multiscale-dreaming,
    recursive-dreaming-bounded-by-grounding, dreaming-on-curated-graphs, dream-phase-rnd-charter):
    extend or supersede?
  - Should the σ-sweep run (oq-0024) execute BEFORE the pass so the note grounds on measured
    corpus connectivity rather than expected behavior?
  - Does the pass ground dn-magnetic-laplacian's OPEN owner decision 2 (dream-narration vocabulary
    for the arrow-aware census — the parked oq-0021) for the owner to rule? And: census as the
    dreamer's directional sense, with ML-a gate (ii) as the only honest path to the operator —
    does the dreamer's need ever open it, or does the census suffice?
  - Does the lazy-view = capability-view unification hold (materialization boundary =
    authorization boundary), or do performance views and firewall Views need to stay separate
    mechanisms? What does the current store/View layer already give us (DRY audit before new
    machinery)?
  - Cuts as pointers into an append-only delta log (persistent structure-sharing): is the current
    store layout compatible, or is this a migration? Where does the cost-model/refusal gate at the
    materialization boundary live (scheduler kin, rule #8)?
  - For the instruments: which spectral quantities admit warm-start/perturbative incremental
    updates vs demand full recompute — and is subspace influence formalized AS the perturbation
    term (efficient and honest) rather than as recompute-both-and-diff?

next_steps:
  - Queue as the next fable design pass once dn-inner-outer-core lands; owner slots it.
  - Consider running oq-0024 (execution, not design) in the gap — its readings feed the pass.

references:
  - docs/brainstorms/inner-outer-core.md                      # the vocabulary this rides on
  - docs/brainstorms/hypothetical-subspace.md                 # candidate third value of the world-parameter
  - docs/brainstorms/cross-strata-and-multiscale-dreamers.md  # prior dreamer-dispatch thinking
  - docs/brainstorms/dreamer-and-graph-direction.md
  - docs/brainstorms/graph-at-a-past-cut.md                   # the temporal world-parameter value
  - docs/design-notes/agent-taxonomy.md                       # role = scope signature; the diachronic park
  - docs/design-notes/capability-scope-algebra.md             # the scope lattice the dispatch parameterizes
  - docs/design-notes/connectivity-instruments.md             # the senses
  - docs/design-notes/cross-strata-dreamer.md                 # reconciliation surface (extend/supersede)
  - docs/design-notes/sigma-fibers-and-multiscale-dreaming.md
  - docs/design-notes/recursive-dreaming-bounded-by-grounding.md
  - docs/design-notes/global-event-clock.md                   # G3 — the diachronic gate
  - docs/design-notes/magnetic-laplacian.md                   # owner decision 2 (dream vocab, oq-0021) + ML-a gates + census-as-sense
  - docs/design-notes/edge-dynamics.md                        # §5 vocabulary question this extends
```
