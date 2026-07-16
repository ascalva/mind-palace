# Cross-strata & multi-scale dreamers

> Brainstorm topic: should some dreamer see the graph *as a whole* — across all strata, at multiple
> scales and clocks — and thereby build the connections that unify the strata? Seeded 2026-07-16 by
> the owner off the back of the first live dual-dreamer A/B RUN (dream_v2 over **13 authored notes /
> 4 edges** — a small authored substrate while the sensor strata grow constantly). Awaiting a **fable
> design pass** to graduate into a design note (full design, scope, goals; the firewall reconciliation
> made explicit). Design only; no build authorized by this brainstorm.

## 2026-07-16T15:31:54Z

```capsule
topic: cross-strata-and-multiscale-dreamers
date: 2026-07-16

decisions:
  - The idea splits into TWO threads that land very differently against the mirror firewall, and
    separating them is the point. IDEA A (multi-scale dreamers over the AUTHORED graph — local
    dreamers finding micro-patterns on a local clock, macro dreamers finding macro-patterns on a
    global clock) is FIREWALL-COMPATIBLE and a near-term thread; it is pure scope/scale on authored
    data. IDEA B (a dreamer that sees the WHOLE STRATA and builds connections BETWEEN layers to unify
    them) is the ambitious direction and hits the mirror firewall head-on; it needs a deliberate
    firewall-scope decision and must travel the artifact chain, never a casual build.
  - Idea A is expressible with machinery that already exists — the synchronic/diachronic axis is the
    design's spine (dream_v2 = synchronic/topological over one snapshot; DD-1 = diachronic across
    time, a different clock); "local vs global clock" IS Rule CLOCK (a Rate(κ) carries its clock in
    its type, capability-scope-algebra §2.3); "local vs macro scope" is expressible via the scope
    algebra's meet/join. So the multi-scale/multi-clock dreamer family is a NEW-DREAMERS question,
    not a new-boundary question.
  - The firewall-reconciliation PRINCIPLE for Idea B (the load-bearing insight): the mirror firewall
    (MIRROR_READABLE = {authored-solo, authored-dialogue}) protects WHAT GETS REFLECTED BACK AS
    AUTHORED INSIGHT — not necessarily what a subsystem may READ. A cross-strata / macro dreamer is
    therefore a DISTINCT `interpreted`-tier subsystem (NOT the mirror's reflective dreamer): it reads
    a COMPOSED / union scope (ObservedView ⊕ ReferenceView ⊕ … , not MirrorView), and everything it
    emits is `interpreted`-provenance, structurally unforgeable as authored (firewall ideal
    `s ⊓ ι = ⊥`). The strata get UNIFIED the safe way: the cross-strata dreamer PROPOSES connections
    as candidates; the ONLY sanctioned crossing into authored/mirror is OWNER RATIFICATION
    (observed/interpreted → owner authors → mirror). The system finds the connections; the owner
    decides which are actually part of their thought. This is a feature, not a limitation — it keeps
    the mirror trustworthy (a dream can never launder machine/third-party exhaust into what looks
    like the owner's insight, I5/I6) while still letting the whole strata inform discovery.
  - Owner intent (2026-07-16): capture the full spirit + rigor now; a FABLE PASS later to fully work
    out design, scope, and goals (design/gates tier per context-economy); then continue the harness
    build in the next session.

parked:
  - decision: The firewall-scope fork — does the mirror firewall forbid observed/non-authored data
      from seeding ANY dream, or ONLY the MIRROR dreamer's dreams (leaving room for a distinct
      cross-strata `interpreted`-tier dreamer)?
    default: the current firewall stands as written — MIRROR_READABLE = {authored-solo,
      authored-dialogue}; the mirror/reflective dreamer + contradiction scan are authored-only
      (core/mirror.py; "third-party observed exhaust can never seed a dream").
    re_entry: the fable design-note pass decides it deliberately and logs it — this sits NEAR an
      inviolable non-negotiable (the mirror firewall / fixed points are sacred), so the decision is
      human-only, deliberate, and recorded, not slipped into a build.

open_questions:
  - Is a COMPOSED cross-strata scope (a "union View" over authored ⊕ observed ⊕ reference ⊕ …)
    expressible under the scope algebra's firewall ideals, or does composing authored ⊕ observed
    collapse to ⊥ (`s ⊓ ι = ⊥`)? This grounds the whole feasibility of a cross-strata READ — the
    fable pass must settle it against capability-scope-algebra + core/scope.py.
  - What is the clock taxonomy for multi-scale dreamers — how do "local clock" and "global clock" map
    onto Rate(κ), and how do local-scope and macro-scope dreamers compose (do a local dreamer's
    micro-findings roll up as inputs to a macro dreamer, or are they independent lenses)?
  - How do cross-strata candidate-links surface for owner RATIFICATION? Is this the correlator's
    channel (Track D, ObservedView seam), the review-probe channel (E6/bp-048), or a new one? Is the
    macro/cross-strata dreamer a GENERALIZATION of the correlator, or a distinct subsystem beside it?
  - Does `authored-dialogue` actually flow into the mirror the dreamer reads TODAY? It is
    mirror-readable, so capturing owner↔Ambassador dialogue into the mirror is a firewall-RESPECTING
    substrate-growth lever available now — the φ_conversation-sensor brainstorm is exactly this thread.
  - Relationship to the existing dreamer roadmap: synchronic (dream_v2, built), diachronic (DD-1,
    design-only) — where do "local/macro scope" and "cross-strata" sit as axes alongside
    synchronic/diachronic? Is the full family a 3-axis space (temporal: synchronic/diachronic ×
    scope: local/macro × strata: mirror-only/cross-strata)?

next_steps:
  - A FABLE design pass (claude-fable-5, design/gates tier) to graduate this brainstorm into a design
    note: define the multi-scale / cross-strata dreamer FAMILY; state the firewall reconciliation
    explicitly (union-scope reads, `interpreted` output, ratification as the only authored crossing);
    resolve the firewall-scope fork; ground the scope-algebra feasibility; relate to the ratified
    notes (evaluation-harness, capability-scope-algebra, velocity-instruments, temporal-geometry,
    observed-data-and-the-assistant-tier, recursive-strata) and the correlator (Track D).
  - MEANWHILE (this is why the brainstorm is captured, not built): continue the harness build — the
    blessed build wave (bp-047 E3a-2 + bp-048 E6), then graduate E3a-1 (bp-046) against the resolved
    σ-fork. Idea A's multi-scale-over-authored thread is a near-term candidate once the harness lands
    (it measures dreamers; a new dreamer family wants the harness to evaluate it).

references:
  - core/mirror.py — MirrorView, the π_MR projection, the structural authored-only firewall ("the
    wrong state cannot be built"); the dreamer's current substrate.
  - core/provenance.py — the six provenance classes; MIRROR_READABLE = {authored-solo,
    authored-dialogue}; curated / interpreted / derived-stratum / observed all EXCLUDED.
  - core/sensing.py (ObservedView), core/reference_view.py (ReferenceView), core/temporal_view.py
    (TemporalView), core/dreams_view.py, core/ops_view.py — the sibling typed Views over other strata.
  - core/scope.py + docs/design-notes/capability-scope-algebra.md — scope meet/join, firewall ideals
    (`s ⊓ ι = ⊥`), Rule CLOCK (Rate(κ) carries its clock) — the algebra a union-scope must satisfy.
  - docs/design-notes/velocity-instruments.md, docs/design-notes/temporal-geometry-and-drives.md —
    Rate(κ)+clock; the diachronic frame (local vs global clock).
  - docs/design-notes/evaluation-harness.md — synchronic dream_v2; DD-1 (diachronic, consumes catalog
    instruments); the harness that would evaluate any new dreamer family.
  - docs/design-notes/observed-data-and-the-assistant-tier.md — the provenance-spectrum growth path
    (§1); the observed/assistant-tier boundary.
  - docs/design-notes/recursive-strata.md — DERIVED_STRATUM; depth-carrying derived; owner-verdict as
    the firewall crossing.
  - Track D correlator (ObservedView seam) — the existing "reads observed strata" subsystem the
    cross-strata dreamer may generalize; φ_conversation-sensor brainstorm — authored-dialogue capture.
  - The first live dual-dreamer A/B RUN (data/reports/2026-07-16-dreamer-ab/): dream_v2 over 13
    authored nodes / 4 edges — the concrete motivation (small authored substrate; sensor strata grow).
```

## 2026-07-16T17:18:05Z — σ-fibers: σ as a sensitivity knob → a multi-strength fiber bundle (Idea A, made concrete)

> Seeded by the owner off the back of shipping the sweep engine (bp-046 + bp-049, session 18). The
> sweep VARIES `dream_rnd_sigma` (the mirror-graph cosine edge threshold) across a grid to SELECT one
> value. The owner's question: *should we ever produce fibers on different σ values — different fibers
> of different strengths — treating σ as a sensitivity tool?* Owner directed this be captured HERE
> (it stems from this brainstorm's Idea A: multi-scale dreamers over the authored graph). Design only;
> no build authorized.

```capsule
topic: cross-strata-and-multiscale-dreamers (σ-fibers facet)
date: 2026-07-16

decisions:
  - σ IS a scale/sensitivity parameter, so this is Idea-A territory made concrete: FIREWALL-COMPATIBLE
    (pure scope/scale on the AUTHORED graph via MirrorView — no new boundary, no union scope). High σ
    = a sparse graph of only the strongest associations; low σ = a dense graph including loose ones.
    Sweeping σ yields a NESTED family {G_σ} — a filtration in the persistent-homology sense: as σ
    falls, edges are born; structural features (clusters, communities, bridges) acquire a birth-σ and
    a death-σ.
  - "Fibers of different strengths" = PERSISTENCE. A connection/synthesis that survives a wide σ-range
    is robust/strong; one alive only in a narrow band is weak/tentative. Persistence LENGTH is a
    principled strength scalar — strictly better than the binary "is it an edge at the chosen σ." This
    is the load-bearing reframe: strength stops being ad-hoc and becomes a structural invariant.
  - This is the DUAL of what the sweep engine does. bp-049's `select` COLLAPSES σ to one value (and,
    tellingly, already privileges σ-robustness — it picks the widest near-optimal plateau, not the
    knife-edge max). The σ-fiber idea says: don't collapse — RETAIN σ as a dimension and let each
    dream carry its strength. The grid bp-049 computes for selection is exactly the raw material for
    the fiber bundle; today we discard it after picking a value.
  - What this buys (three): (1) HONEST CONFIDENCE — a weak fiber surfaces as "a hunch," a strong one
    as "a settled link"; strength GATES trust/surfacing. Dovetails with F9 apophenia grading (low σ =
    higher apophenia risk → strength and grounding-defect are correlated axes). (2) MULTI-SCALE
    DREAMING, firewall-clean — a "tight" dreamer reads G_{high σ}, a "loose" dreamer reads G_{low σ},
    both over MirrorView; Idea A's "local vs macro scope" with σ as the concrete scale knob. (3) A
    PRINCIPLED STRUCTURAL AXIS — persistence-across-σ is an invariant that could register in the eval
    harness (like frustration) and feed drift.
  - Cheap to prototype BECAUSE of what just shipped: the marginal cost of RETAINING vs DISCARDING the
    grid is storage + the synthesis passes, not the graph builds (the sweep already builds every G_σ).

parked:
  - What IS a "fiber"? Three candidate objects, different builds: (a) a whole graph at one σ; (b) a
    single connection carrying a persistence interval [σ_birth, σ_death]; (c) a dreamer instance
    parameterized by σ. Default lean: (b) — the persistence-interval annotation is the most
    mathematically load-bearing AND the cheapest (it annotates connections, computed from the grid).
    Re-entry: the Fable design pass picks the object (it determines whether this is a storage/
    representation change or a new dreamer family).
  - Cost/memory ceiling: k live σ-fibers = k synthesis passes; the ≤2-resident-model ceiling (§8)
    bounds how many can be dreamt live → likely a batched/overnight structure, not per-interaction.
    Re-entry: the design pass sizes the fiber count against the memory ceiling + the overnight profile.
  - Corpus inflation / noise: retaining low-σ fibers multiplies syntheses and invites apophenia; the
    strength tag is what makes it SAFE, but only if strength gates surfacing (else the corpus drowns
    in weak hunches). Re-entry: the design pass pins the strength→surfacing gate before any build.

open_questions:
  - Should σ-persistence be a first-class REGISTERED structural axis (eval/harness/registry.py), and
    does it subsume or complement the existing structural_axes.* (frustration, …)?
  - Is the fiber-strength gate the SAME instrument as the sweep's admissibility/selection, or a
    distinct one? (The sweep asks "which σ is best"; the fiber model asks "how strong is each σ's
    contribution" — related but not identical.)
  - Does this fold INTO the awaited cross-strata Fable+xhigh design pass as a concrete Idea-A
    mechanism, or warrant its own design note? (Owner leans: capture here, decide at the pass.)

next_steps:
  - Fold the σ-fiber facet into the awaited Fable+xhigh design pass for this brainstorm (Idea A half);
    the pass chooses the fiber object (parked (a)/(b)/(c)) and pins the strength→surfacing gate.
  - No build authorized. The sweep engine (bp-046/bp-049) stays a SELECTOR; σ-fibers is a distinct
    design thread that must travel brainstorm → design note → build plan through the same gate.

references:
  - eval/harness/sweep.py (bp-049) — the σ-grid driver + §8 `select` (widest-plateau, the collapse
    this idea is the dual of); config/sweeps/dreamer-sigma-ab.toml — the σ grid instance.
  - ops/levers.py `dream_rnd_sigma` (bp-046) + core/dreaming/shadow.py (`MirrorGraph.build(view,
    sigma=rnd.sigma)`) — where σ enters the mirror graph.
  - docs/design-notes/dreamer-quality-suite-evaluation.md / Track F (F9 apophenia) — the signal-vs-
    noise grading that fiber-strength would gate against.
  - This brainstorm's Idea A (multi-scale dreamers over the authored graph, firewall-compatible) — the
    parent family; σ is its concrete scale parameter.
```

## 2026-07-16T17:32:23Z — σ-fibers: the two surfaces DIRECTLY impacted (harness + scope-algebra/query) — the Fable pass MUST work these rigorously

> Owner: the design connects directly to (1) the eval HARNESS and (2) the capability ALGEBRA / query
> language — those are impacted, not incidental — and the pass NEEDS TO BE RIGOROUS (formal, grounded
> to path:line, ratifiable — not a sketch). Recording the concrete seams so the Fable pass grounds,
> not hand-waves. Design only.

```capsule
topic: cross-strata-and-multiscale-dreamers (σ-fibers × harness × algebra/query)
date: 2026-07-16

decisions: []   # seams to be worked rigorously by the Fable pass; nothing ratified

open_questions:
  # ── HARNESS (eval/harness/**) ────────────────────────────────────────────────────────────────
  - The harness ALREADY keys per-σ: bp-046 made `config_fingerprint` move with σ, so the eval store
    already holds a distinct keyed series per σ cell (`EvalKey(spec_hash, corpus_ref,
    config_fingerprint, seed)`). σ-fibers therefore adds a DERIVED CONSUMER over that existing series,
    NOT a new store. Rigor bar: the pass must show the persistence metric is computable from
    `EvalResultsStore.query` alone, no schema change (the same discipline bp-049 held).
  - bp-049's §8 `select` is a SELECTION consumer of the σ-series (collapse → one value). σ-fibers needs
    a RETENTION + PERSISTENCE-SCORING consumer (keep the series → strength per connection/feature).
    Both read the same store. The pass must define persistence FORMALLY: for a feature f, its σ-support
    interval `[σ_birth(f), σ_death(f)]` over the filtration {G_σ}, and `strength(f)` = a declared
    functional of that interval (length? area-under-support? weighted by ȳ?). Three-clause falsifier
    discipline (like bp-049 §8): the observable that would falsify the strength metric.
  - σ-persistence as a REGISTERED structural axis in `eval/harness/registry.py` — `type_tag=Inv`?
    (careful: see the typing question below — persistence is σ-parametrized, so is it truly `Inv` or a
    new result class?), catalog row, `guardrail_eligible` (likely False — descriptive, not a bright
    line). Sibling of finding-0086's `structural_axes.*` registration rider.
  - F9 / apophenia (Track F) is the strength gate's EVALUATION: low σ = looser edges = higher apophenia
    risk, so the strength→surfacing gate must be VALIDATED against F9's signal-vs-noise grading in the
    harness, not asserted. The pass ties the gate's threshold to an F9-measured false-connection rate.
  # ── SCOPE ALGEBRA / QUERY LANGUAGE (core/scope.py, capability-scope-algebra.md, core-query-protocol)
  - THE LOAD-BEARING ALGEBRA QUESTION: Rule CLOCK (`capability-scope-algebra.md:116`) already makes a
    reparametrization-carrying dimension first-class — `q : s → Rate(κ)` REQUIRES `s.T.clock = κ`; a
    Rate carries its clock in its type, never a bare number. σ (and grain, and conversation-depth) is a
    SCALE/RESOLUTION parameter of exactly that shape. So: does the algebra need a FIRST-CLASS "Rule
    SCALE" — a `Res(σ)` result typing analogous to `Rate(κ)`, where a resolution-parameterized
    instrument carries its σ/grain in its type — OR is scale already expressible via the existing scope
    meet/join (the founding capsule claimed "local vs macro scope IS the scope algebra's meet/join")?
    This is the decision that determines whether σ-fibers + chunk-smear + conversation-layers are ONE
    algebra extension or three ad-hoc features. The pass must answer it FORMALLY (typing rule, not prose).
  - TYPING SUBTLETY (must be nailed, not glossed): §2.3 splits results into `Inv` (reparametrization-
    invariant: β₁, connected sets, well-foundedness) vs `Rate(κ)` (per-unit-clock). σ-persistence is
    invariant under σ-GRID reparametrization (denser grid, same interval) — arguing `Inv` — YET it is
    intrinsically about variation ALONG σ — arguing a new `Res(σ)` class. The pass must place it
    correctly; getting this wrong mis-types every downstream instrument.
  - QUERY LANGUAGE: retrieval over a multi-resolution corpus needs a RESOLUTION PARAMETER — "retrieve
    at grain g", "connections with persistence > θ", "the σ at which this cluster is born". Precedent:
    `grouped_semantic_search` (core/stores/sourceset.py) already parametrized retrieval by group-by-
    digest; scale is the next parameter on that surface. ALL THREE multi-resolution ideas press on the
    query surface IDENTICALLY → this is the strongest test of whether "scale-as-a-dimension" is one
    abstraction worth naming (see doc-code-entanglement multi-resolution capsule) or three features.

parked:
  - decision: introduce a first-class `Res(σ)` / Rule SCALE in the capability algebra
    default: NOT introduced — the pass evaluates it; a scope-algebra change is a RATIFIED-note edit
      (capability-scope-algebra.md), owner-blessed, never casual.
    re_entry: the pass shows scale is NOT faithfully expressible via meet/join (i.e. an instrument that
      needs σ-in-its-type to audit correctly) → draft the algebra extension as its own note.

next_steps:
  - The Fable+xhigh pass works BOTH surfaces to path:line rigor: (harness) the persistence metric +
    its registry row + the F9-validated gate, computable from the existing store; (algebra/query) the
    `Inv`-vs-`Res(σ)` typing verdict + the meet/join-vs-Rule-SCALE decision + the query-surface
    resolution parameter. Grounded, falsifiable, ratifiable — the bar is a note the owner CAN ratify.

references:
  - eval/harness/sweep.py §8 (bp-049) ; eval/harness/store.py (EvalKey/query) ; eval/harness/registry.py
  - core/scope.py ; docs/design-notes/capability-scope-algebra.md (§2.3 Inv/Rate(κ), :116 Rule CLOCK)
  - docs/brainstorms/core-query-protocol.md ; core/stores/sourceset.py (grouped_semantic_search precedent)
  - docs/design-notes/dreamer-quality-suite-evaluation.md / Track F (F9 — the gate's evaluation)
  - docs/brainstorms/doc-code-entanglement.md (the multi-resolution-family capsule — the query-surface test)
```
