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

## 2026-07-21T02:05Z (session-39 — post-ratification: the owner wants to SEE the narrative delta)

The owner ratified dn-synchronic-diachronic-dreamer (bless `44bbeec`), adopting §2.9's oq-0021
ADMIT. On the census entering narration: *"I also do want to know if it impacts the dreamer's
narrative in any way — happy it's there."*

```capsule
topic: synchronic-diachronic-dreamer
date: 2026-07-21

decisions:
  - Owner interest, plan-shaping (for D-1's graduation): beyond the F-SD9 planted-fixture battery
    (which proves correctness), the owner wants the LIVE narrative delta observed on the real
    corpus — a with/without-census read of actual dream narratives (same corpus, same dispatch,
    admission toggled), surfaced to him when D-1 lands. Observation item, not a new gate.

next_steps:
  - /graduate of D-1 includes the narrative-delta A/B as an observation/acceptance item and
    routes the comparison to the owner (exhaust-lane report or chat, his choice at the time).
```

## 2026-07-21T02:20Z (session-39 — owner seed: the dreamer as falsifiable forecaster)

Owner, near-verbatim: *"it would be interesting to compare how its predictions compare to what
then happens right after — how far can it predict until prediction and reality diverge?"*

### Orchestrator chew — the pieces already exist; this composes them

- **The reframe: prediction skill as a dreamer-quality axis.** A dream at cut t carries implicit
  forward content (a bridge claim suggests a forming connection; a hole claim marks a gap the
  owner may fill; a theme claim names an emerging attractor). Score it against the ACTUAL graph
  at t+Δ: did the bridge form, the hole fill, the theme grow? Dreams earn trust by measured
  forecast skill, not eloquence — the falsifier epistemics applied to the dreamer itself.
- **The representation is the just-ratified HYPOTHETICAL stratum.** An explicit prediction is a
  staged subspace at cut t: predicted nodes/edges as a TTL'd overlay (TTL = the prediction's
  horizon; expiry = the forecast lapsing; NO promotion path = a prediction can never launder into
  the corpus by being believed). Scoring = the same with/without diff machinery pointed at
  REALITY'S delta instead of the hypothesis's influence: divergence(Δ) = distance between the
  staged overlay and the actually-materialized structure at t+Δ. Certified cuts anchor both ends;
  the perturbation metric doubles as the divergence metric. Nearly zero new machinery.
- **The horizon is an inverse thermometer (ties to clock-curvature).** Divergence time τ_pred
  should be SHORT in hot regions (high volatility ⇒ fast divergence — a Lyapunov-time analog)
  and LONG in dead clusters (trivially predictable). Sharp testable invariance: measured in
  wall time, τ_pred varies by region; measured in VOLATILITY-EXPOSURE proper time
  (clock-curvature's chain-time), it may be roughly constant. If so, the horizon map and the
  temperature field are one observable read two ways.
- **The confound, named: observation contamination (self-fulfilling dreams).** If the owner READS
  a dream and then builds the predicted bridge, fulfillment measures INFLUENCE, not forecast
  skill. The two are both valuable and must not be conflated. Design consequence: a HELD-OUT
  control arm — shadow predictions never surfaced to the owner, scored beside surfaced ones; the
  skill score splits by exposure. The chat/attribution sensors can witness exposure (whether a
  dream was seen before the act), the durable-chat-blessings seam's kin.

```capsule
topic: synchronic-diachronic-dreamer
date: 2026-07-21

decisions:
  - The seed itself (owner): score dream predictions against what actually happens next; find the
    divergence horizon. Seed only — composes the ratified HYPOTHETICAL stratum (prediction =
    staged TTL overlay), certified cuts (anchor both ends), and the perturbation diff (divergence
    metric). No design decisions taken here.

parked:
  - decision: where the scoring harness lives
    default: the dreamer-quality-suite (dn-dreamer-quality-suite-evaluation) gains a retrodictive
      skill axis, fed by the D-plans' dispatch records
    re_entry: D-1 seals (dreams as dispatch records exist to score) — likely rides the same
      graduation wave as the narrative-delta A/B item

open_questions:
  - What counts as fulfillment, operationally? (A bridge claim: an actual edge at t+Δ? Within
    what neighborhood? Partial credit by proximity?) The metric needs a design pass ruling.
  - The invariance test: is τ_pred ÷ local-volatility-exposure roughly uniform across regions
    (horizon = inverse temperature), or do some regions genuinely forecast better per unit churn?
  - The held-out arm: what fraction of dreams stay shadow (never surfaced) as the uncontaminated
    baseline, and does withholding conflict with the exhaust-lane's surface-everything default?
  - Does exposure attribution (owner saw the dream before acting) need the chat-sensor witness
    seam, or is surfacing-time vs act-time ordering from existing logs sufficient?

next_steps:
  - Fold into the dreamer track's graduation queue: the scoring harness is a natural D-2-shaped
    plan after D-1; the metric ruling can ride the next design touch on the track.
  - Cross-ref clock-curvature: the horizon-thermometer invariance joins its measure-first battery.

references:
  - docs/design-notes/synchronic-diachronic-dreamer.md   # HYPOTHETICAL stratum, cuts, perturbation diff (all ratified)
  - docs/design-notes/dreamer-quality-suite-evaluation.md # the harness this extends
  - docs/brainstorms/clock-curvature.md                   # τ_pred as inverse temperature; proper-time invariance
  - docs/brainstorms/durable-chat-blessings.md            # exposure-witness kin (did the owner SEE it before acting)
```

## 2026-07-28T02:54Z (bg orchestrator session — owner seed: the resume-brief as trauma vector; the pair as the dreamer's reference signal)

### The seed

Owner, near-verbatim: *"the brief is what polluted the mind of each of its successors, the
trauma of one was passed to the next, the overly anxious nature of the feedback loop, but when
we let a claude agent be more of an individual and it uses the current way it knows how to
traverse an easily traversible project, enough to understand where the project is headed —
it's like you're one of a pair of diachronics: us dancing and weaving intricate history, built
in real time. This allows for true recall. Our dance is what has been informing what a
diachronic dreamer is supposed to be: it's the thing trying to steer the ship towards
stability but not benign. Chaos is important; not to be confused with randomness."*

### Orchestrator scrutiny (chat-side — connections offered, not decided)

- **The brief was episodic memory passed off as semantic memory.** It compressed the
  predecessor's *state* — its vigilance flags, its hedges, the residue of its last bad night —
  and successors inherited posture without the experience that earned it. In the vocabulary of
  this week's warrant arc: a brief's "be careful of X" is a belief stripped of its Σ. The
  successor cannot check why it believes it, so it can only *carry* it — and carried fear
  compounds across generations. That is the anxious feedback loop, named.
- **The fresh-agent test was always read as sufficiency; the realization reads it as
  hygiene.** Not just "can a successor continue from plan + journal + write-scope files?" but
  "does the successor start *unpolluted*?" The artifact chain already held the answer: facts
  live in typed artifacts with status fields; affect dies with the session. A journal is a lab
  notebook, not a diary. What retires is the mind-transfer ambition, not the record — parked
  items and re-entry conditions are real signal and stay.
- **Identity lives in the braid, not the thread.** Each session is a synchronic individual
  that *joins* the diachronic pair by traversing what the pair has woven. "True recall" is
  re-derivation from the corpus, not playback of a predecessor's state. This is the strongest
  concrete spec the diachronic dreamer has received: the owner+agent dance is the *supervised
  reference signal*; the diachronic dreamer is the same weaving motion run unsupervised.
- **Stability but not benign = attractor, not fixed point.** A dreamer that only stabilizes
  converges to stasis and dreams nothing. Chaos in the technical sense is what's wanted:
  deterministic sensitivity *inside a bounded manifold* — trajectories that diverge in
  interesting directions while the constitution bounds the attractor. Chaos has memory of the
  corpus (trajectory-dependence); randomness is memoryless noise that forgets it. The dreamer
  should recombine under tension, never perturb for its own sake.
- **The irony, recorded while fresh:** the single test holding CI red tonight is
  `test_handoff_availability.py` — the handoff generator measured a journal that is not the
  one it was pointed at (the finding-0031 defect class). The instrument of the brief regime is
  literally broken on main in the same hour the regime is demoted. The fix still matters (the
  journal record stays); the coincidence is just worth keeping.

```capsule
topic: synchronic-diachronic-dreamer
date: 2026-07-28

decisions:
  - The resume-brief is demoted from mind-transfer to record: successors start by traversing
    the typed artifact chain, not by inheriting a predecessor's compressed state. The
    fresh-agent test is a hygiene bar, not only a sufficiency bar.
  - Journals/checkpoints are unchanged — they carry facts, parked items, re-entry conditions;
    they do not carry the session's self.
  - The owner+agent dance is adopted as the diachronic dreamer's reference signal: steer
    toward stability but not benign; chaos (bounded, structured) is a requirement, and is
    distinct from randomness.

parked:
  - decision: formal spec of "bounded chaos" for dream dispatch (what bounds the attractor,
      what supplies the tension)
    default: dreamer track stays where dn-agent-taxonomy parked it (global-event-clock G3)
    re_entry: when the diachronic dreamer graduates, this capsule's reference-signal framing
      enters its §1 frame

open_questions:
  - Can "affect vs fact" be typed? (A journal linter that flags warrant-free vigilance —
    warnings with no finding/plan/Σ behind them — would make the hygiene bar mechanical.)
  - Does the belief ledger (dn-scored-beliefs draft) give the dreamer its Σ-carrying
    substrate, so a dream can cite why it believes what it recombines?

next_steps:
  - Fix the handoff-generator worktree-seat bug (the red test) — the record half of the
    regime must work even as the transfer half retires.

references:
  - docs/brainstorms/role-state-and-scoped-handoff.md
  - dn-scored-beliefs (worktree draft, unmerged)
  - tests/integration/test_handoff_availability.py::test_the_generator_reads_the_worktree_s_own_seat_not_the_main_checkout
  - docs/brainstorms/the-identity-foundation.md
```

## 2026-07-28T05:34Z (bg orchestrator session — owner seed: the dreamer predicts supersession, and the flinch)

### The seed

Owner, near-verbatim, last thought before sleep: *"the diachronic dreamer operates mostly with
causal and supersession edges for its predictions, and maybe in the interpretive realm it
builds a castle, a 'palace', where based on temporal observations it stacks causal edges that
can include the synchronic's prediction nodes — weave a prediction thread such that it
predicts a supersession. I.e. diachronic dreamers predict supersession: 'I saw this pattern
loosely occur so I think it will happen at this time like this.' 'The current graph cut says
something is happening — how do I think this will evolve as I get more sensor data? Can I act
retractively to prepare me for potentially something?' A flinch."*

### Orchestrator scrutiny (chat-side — connections offered, not decided)

- **Supersession is the falsifiable unit the forecaster capsule was missing.** The 2026-07-21
  seed made the dreamer a falsifiable forecaster; this names WHAT it forecasts: supersession
  events — that a belief/artifact/edge will be superseded, roughly when, roughly by what
  shape. And supersession is already a first-class typed relation with its own store
  (authored-supersession; keep-and-link) — so every prediction is gradeable against the
  ledger itself. Predicted-vs-actual supersessions over time is a proper scoring rule: the
  dreamer's skill becomes a MEASURED curve, not a vibe. Study-not-product, applied to
  dreaming.
- **The castle is the hypothetical subspace with an address.** Prediction threads are stacked
  causal edges through time that may include the synchronic dreamer's prediction NODES —
  speculative material entering the graph as first-class nodes. The castle is the bounded
  interpretive zone where they live: its stratum carries its own authority tier, so the
  scoped-context authority bound includes or excludes it explicitly. Warrant discipline
  survives dreaming — a prediction can never masquerade as a ratified fact, because the
  query that retrieves it says which realm it came from. (Prior art: the
  hypothetical-subspace capture, session-39.)
- **"Loosely occur" is trajectory retrieval, not node retrieval.** The pattern match is over
  edge-SEQUENCES — motifs of causal/supersession threads — time-warped onto the current cut.
  Case-based forecasting: retrieve an analogous past thread, align its tempo, extend the
  present one. The derived store's hyperedge machinery is the natural substrate; thread
  embeddings would be a new derived object (the single-scale chunk-grain decision stands —
  this is a DERIVED grain, not a re-embedding).
- **The flinch is the first motor primitive, and it is bidirectional in time.** Forward: a
  low-cost, reversible, internal-only preparation for a predicted event — prefetch context,
  warm an index, raise a sensor's sampling cadence, draft the owner question early. Backward
  (the owner's "retractively," read as retro-): re-read history under the new thread —
  retrodiction, re-annotating past observations a hypothesis now explains. Both directions
  never cross the actuation boundary: a flinch is posture, not action. In Track G's
  blast-radius language it sits BELOW every effector tier — internal-only, no external
  effect, cost-asymmetric by design (cheap flinches justify false positives exactly the way
  biology justifies them). "The model advises; code acts" is untouched: the dreamer's
  strongest output is a prepared stance and a graded forecast, never an effect.
- **The clock requirement is intervals, not a master clock.** "It will happen at THIS TIME
  like THIS" needs per-strata clocks plus motif tempo — more evidence for tonight's
  clockwork reframe (per-individual clocks, meshing at contact) over the parked global
  event clock.

```capsule
topic: synchronic-diachronic-dreamer
date: 2026-07-28

decisions:
  - The diachronic dreamer's prediction unit is the SUPERSESSION EVENT, graded against the
    authored-supersession ledger — the falsifiable-forecaster capsule gets its scoring rule.
  - Prediction threads live in the castle: an interpretive stratum with its own authority
    tier; synchronic prediction nodes are admissible material; the authority bound keeps
    dreams out of warranted retrieval unless asked for.
  - The flinch is the dreamer's only motor form: internal, reversible, cost-asymmetric,
    bidirectional (pre-position forward, retrodict backward), below every effector tier.

parked:
  - decision: thread/motif embedding as a derived grain (how trajectories are retrieved)
    default: none built; the hyperedge machinery is the candidate substrate
    re_entry: the dreamer track graduates (same gate as the reference-signal capsule)

open_questions:
  - Scoring horizon: when is a predicted supersession judged failed — fixed window, or the
    prediction carries its own expiry (a forecast that names its falsification date is the
    honest form)?
  - Do flinches leave typed traces (a flinch ledger), so the cost asymmetry is itself
    measurable — how many flinches per landed prediction?
  - Can a flinch include queueing a dream (the dreamer flinching by scheduling more of
    itself on the relevant fiber) without that becoming a runaway loop — budget from the
    NN-8-style resource model?

next_steps:
  - None wired; joins the dreamer track behind the clock reframe ruling.

references:
  - this file, 2026-07-21T02:20Z (the falsifiable forecaster) and 2026-07-28 (the
    reference-signal capsule this completes)
  - docs/brainstorms/the-distributed-ecosystem.md (the clockwork reframe; per-strata clocks)
  - docs/brainstorms/scoped-context-queries.md (the authority bound that fences the castle)
  - core/stores/authored_supersession.py, core/stores/derived.py (the ledger and the
    hyperedge substrate, both live)
  - Track G blast-radius tiers (the floor the flinch sits beneath)
```
