# temporal-clocks-and-strata — how the corpus tells time

> Brainstorm thread (owner ⇄ orchestrator, 2026-07-15). The thesis, in the owner's words:
> **"everything has a sense of time, but time can be interpreted differently in different local
> regions."** This works out what that means for the *time parameter* of the temporal algebra — the
> anchor/index against which `‖[d,τ]‖` citation-coherence and every diachronic instrument is measured —
> and lands on a striking convergence: the owner's clock intuition re-derives, from scratch, the
> **superconnection curvature `[d,τ]`** the fable pass already established, and points *beyond* it to a
> genuinely new object (a locally-clocked transport whose time-step varies across space).

## 2026-07-15T16:02:27Z — the logical clock, per-stratum sub-clocks, relativity, and curvature

### 1. Time is a logical (event-count) clock; a commit is only its label
A `commit_sha` is the *time-label* the reference store happens to key snapshots on — not the tick.
The sensor re-projects the WHOLE corpus→corpus graph at each commit (a full snapshot, not a delta), so
commits are a **coarse, lumpy clock**: a live probe (2026-07-15) found the **6 most-recent commits are
ONE identical 217-pair citation snapshot** — they added doc *files* but changed no which-note-cites-which.
The clean clock is the **append-only ledger position**: each atomic mutation is one tick. This is a
Lamport logical clock, and it is **already the system's spine** — the `op-seq` strict order
(`supersession-lifecycle` §4A) and the **ledger-as-isometric-dilation** (`dn-temporal-retrieval-algebra`
§2.5: *"the append-only ledger is the space in which nothing was ever destroyed"*, Sz.-Nagy). The
event-clock is not a new mechanism; it is the dilation space, read as an index.

**Grain caveat (the one sharp edge in the arithmetic).** The owner's `n = 2 commits + 1 note + 3
observations + 1 dream-edge = 7` is clean **as an ordinal** (ordering/indexing events) but slippery **as
a distance**: a commit is a *coarse bundle* that can CONTAIN the note ingestion (double-count risk), and
"1 commit" ≠ "1 edge" in amount of change. Fix: fix ONE atomic grain (ledger appends); a commit is then a
**range** of the clock, not a tick — a commit that ingests 3 notes and adds 5 edges advances `n` by 8.

### 2. One global clock, many per-stratum sub-clocks (the multi-rate reconciliation)
`N` = the global event count; `N_s` = the per-stratum count (only the events that touch stratum `s`);
`N_s ≤ N`, a **projection**. Strata — and even sources within a stratum — accumulate at different rates,
so `dN_s/dN < 1` and is stratum-specific. The owner's example maps exactly: the global tick is 7, but
the **corpus-citation** stratum advances only on citation-changing events (the note ingestion iff it
added a citation — not the 3 observations, which touch the observed plane; not the dream edge, which
touches the INTERPRETED layer). This **reconciles the earlier tension** (single-stratum scoping vs a
unified counter): *one absolute order, many sampling rates.* "Everything has a sense of time" = every
stratum has its `N_s`; "interpreted differently in different local regions" = the `N_s` run at different
rates and there is no absolute cross-stratum "now."

### 3. "Scrubbing patterns" = reparametrizations of one trajectory
git-time, wall-time, global-event-time `N`, and per-stratum `N_s` are all **monotone clocks on the same
append-only trajectory** (the ledger's causal order). An instrument must therefore declare its clock and
know its type:
- **reparametrization-INVARIANT** (topological): *did a citation sever, yes/no* — `‖[d,τ]‖` as a count is
  invariant to which clock you scrub with.
- **reparametrization-DEPENDENT** (a rate): *severings per tick*, a velocity — this is only defined
  relative to a chosen clock, and the answer changes with the clock.
This directly sharpens the velocity work (`edge-dynamics-vector-field.md`, the R-ladder / VF-*): "velocity
`ẇ`" is `dW/d(which clock?)` — the choice of clock *is part of the object*, not a detail.

### 4. The relativity parallel — apt, then it breaks, and the tighter physics home
The owner: *local clocks move at different rates; the rate of information addition affects the local
clock (I digested 1 note in a day while Ouroboros consumed 5 commits = 20 changes).* Assessment:
- **APT — the deep true part:** (a) **no universal "now"** — two strata's "current snapshots" sit at
  different `N_s` and are never absolutely simultaneous (this is **relativity of simultaneity**, the
  strongest part of the analogy); (b) **proper time vs coordinate time** — each stratum's `N_s` is its
  proper time, wall-clock is a coordinate none of them measures directly, and comparing two strata needs a
  transformation between their clocks; (c) **local rate is set by a local quantity** — `dτ/dt ∼ velocity`
  in SR, `dN_s/dt ∼ information-throughput` here.
- **WHERE IT BREAKS (be honest):** (a) **direction is inverted** — SR velocity *dilates* (SLOWS) proper
  time via `√(1−v²/c²)`; here more information *ACCELERATES* the local clock (monotone accumulation).
  (b) **no `c`, no Lorentz invariant, no `ds² = c²dt² − dx²`** coupling space and time. (c) **no
  frame-reciprocity** — there IS a preferred frame (the ledger's absolute append order), so this is *not*
  relativistic in the no-preferred-frame sense; it is closer to **Newtonian absolute time with variable
  local sampling.**
- **THE TIGHTER FIT:** **causal set theory** (spacetime as a discrete causal order; proper time along a
  worldline ≈ the length of the maximal chain of events between two points) and **Lamport logical clocks**
  (the distributed-systems native form of relativity-of-simultaneity: causal order, no global now). "Proper
  time = count of events along your worldline" is almost literally the causal-set construction. *These* are
  the rigorous homes — SR/GR is the evocative shell; causal sets is the load-bearing frame.

### 5. Curvature — the convergence (owner: "curvature territory, smooth/discrete transitions of rates along space")
This is the sharpest move and it is **precisely right**, with one distinction that turns it from metaphor
into the actual object:
- **A rate that VARIES across space is a FIELD (a connection), not yet curvature.** A uniformly-varying
  rate (a pure gradient) is FLAT — you can reparametrize each region's clock to align it away (an
  accelerating frame is still Minkowski). **Curvature is the part you CANNOT gauge away** — the
  non-integrability, the failure of parallel transport to commute around a loop (holonomy, the Riemann
  tensor `[∇,∇]`).
- **The convergence:** the algebra ALREADY carries exactly this object. The superconnection `𝔸 = d + τ`
  has curvature `[d,τ]` — the commutator of the **space-derivative** `d` (the citation coboundary) and the
  **time-transport** `τ` (supersession). `[d,τ]` measures *how the time-transport changes as you move
  through space* — the covariant derivative of the clock along the graph. **Non-flatness `[d,τ] ≠ 0` IS
  "the space-varying time-rate that cannot be gauged away"** — supported exactly on severed citations
  (the fable pass, Result 2). The owner re-derived `[d,τ]` from the clock intuition. It is the **first
  obstruction**, not a metric curvature — homotopy-repairable if the class is exact.
- **Two curvatures, do NOT conflate** (Result 3, *"same word, different tensors"*): the **static
  Forman–Ricci** curvature of the graph-*space* at one slice (`core/complex/curvature.py`) is NOT the
  **superconnection** curvature `[d,τ]` of the space×time *coupling*. The owner's intuition is about the
  latter (time-rate varying across space), not the former (edges bending at fixed time).
- **Smooth vs discrete:** we live in the **discrete** regime — a graph, integer event-counts — so the
  natural curvature is combinatorial (the discrete superconnection `[d,τ]`), not a smooth Riemann tensor.
  A "smooth transition of rates" would be a **continuum / coarse-grained (hydrodynamic) limit** of the
  discrete object — meaningful only if the corpus grows dense enough to coarse-grain (a real research
  direction, gated on sample depth).

### 6. The genuinely-NEW object the intuition points beyond (novel, fable-grade)
The current `[d,τ]` is computed between two **global** snapshots at one shared time-step. The owner's
"**local** rate varies across space" is *richer*: it asks for a **locally-clocked transport** — each
region transported over its OWN number of events (`N_region`), so the time-step is a field over space. The
curvature is then the **holonomy of a loop that crosses regions of different clock-rate** — go around a
cycle through a fast region and a slow region and see whether the citation structure comes back to itself.
That is a **new object** beyond the current two-global-snapshot `[d,τ]`: a *space-varying-time-step
superconnection*, whose flatness is a much stronger coherence condition. It also unifies with the velocity
work: `ẇ` (velocity 1-cochain) is the infinitesimal generator, and its spatial variation is this curvature.

---

```capsule
topic: temporal-clocks-and-strata
date: 2026-07-15

decisions:
  - Corpus time is a LOGICAL (event-count) clock, not wall/git time; the append-only ledger position is
    the canonical global clock N — identical to the op-seq strict order and the Sz.-Nagy dilation space
    already in the algebra (dn-temporal-retrieval-algebra §2.5; supersession-lifecycle §4A).
  - ONE global clock N + per-stratum sub-clocks N_s (projections onto the events touching each stratum,
    N_s ≤ N) reconciles "strata/sources move at different rates" with a single absolute causal order.
    Thesis: everything has a sense of time; different local regions interpret it at different rates.
  - Event counts are clean as an ORDINAL index; as a CARDINAL distance they need a fixed atomic grain
    (ledger appends), with a commit treated as a RANGE of the clock, not a single tick (avoids
    double-counting a note-ingestion that rode in on a commit).
  - Clocks (git / wall / global-N / per-stratum-N_s) are REPARAMETRIZATIONS of one trajectory; every
    instrument must declare its clock and whether it is reparametrization-invariant (a count, e.g. ‖[d,τ]‖)
    or reparametrization-dependent (a rate, e.g. a velocity).
  - The owner's "rate-varies-across-space = curvature" re-derives the SUPERCONNECTION curvature [d,τ]
    (the commutator of the citation coboundary d and the supersession transport τ) — non-flatness is the
    space-varying time-rate that cannot be gauged away. This is the FIRST obstruction, NOT the static
    Forman–Ricci curvature (Result 3, "same word, different tensors").
  - bp-038 is UNCHANGED by all of this: coherence_to(other) is anchor-agnostic; git-commit anchoring is
    the first instance, and event-clock / per-stratum / distinct-snapshot anchoring layer on top (§11).

parked:
  - decision: A materialized GLOBAL event index (a unified N across strata)
    default: none — version_seq is per-doc, RunLedger is per-run, op-seq is supersession-only; no single N
    re_entry: a consumer needs cross-stratum event-time (event-anchored coherence, or the φ_coh stream)
  - decision: Per-stratum sub-clock projections N_s (corpus / observed / dream / code, each at its rate)
    default: not built (bp-038 uses git-commit distinct-snapshots for the corpus stratum only)
    re_entry: per-stratum diachronic instruments ship (DD-1 and beyond)
  - decision: Reparametrization-invariance CLASSIFICATION of instruments (invariant count vs rate)
    default: unclassified — ‖[d,τ]‖ is treated as a count; velocity is left undefined pending a clock
    re_entry: the R-ladder velocity or the φ_coh stream is formalized (needs a chosen clock)
  - decision: Causal-set / proper-time formalization (proper time ≈ maximal-chain length; the CST frame)
    default: analogy only, not formalized; SR/GR is the evocative shell, causal sets the load-bearing home
    re_entry: a Fable pass (post Jul-17 reset) formalizes the time-index into dn-temporal-retrieval-algebra
  - decision: The LOCALLY-CLOCKED superconnection (space-varying time-step; curvature = cross-region loop
      holonomy) — the novel object the curvature intuition points BEYOND the current global-snapshot [d,τ]
    default: not specified; the current [d,τ] uses one shared global time-step between two snapshots
    re_entry: a Fable pass, after per-stratum N_s exists and the velocity 1-cochain (R1) has data
  - decision: Curvature↔clock-rate coupling as a GR-adjacent claim (does local structure warp local time?)
    default: NOT a claim — event-RATE (change) and curvature (structure) are DIFFERENT fields (a dense but
      STABLE region has high curvature, low event-rate); the GR gravitational-dilation direction is inverted
    re_entry: a Fable pass tests whether local curvature and local event-rate have any principled relation

open_questions:
  - Is the right global clock the raw ledger-append position, or a coarser DISTINCT-SNAPSHOT index (dedup
    byte-identical states)? bp-038 uses distinct-snapshots for the corpus stratum; is that the general rule?
  - Relativity of simultaneity across strata: how do you DEFINE a consistent cross-stratum "slice" (a cut)
    when strata sit at different N_s? (causal-set analog: a maximal antichain / a spacelike hypersurface.)
  - Does any instrument WANT reparametrization-dependence (a genuine rate), and measured against WHICH clock?
  - Is there a principled curvature→clock-rate relation, or is the GR reading purely evocative? (default: evocative.)
  - Does the locally-clocked superconnection reduce to the current [d,τ] when all region-clocks are equal
    (the flat/global limit)? (expected: yes — a consistency check for the generalization.)

next_steps:
  - Keep the clock model as the ANCHOR-generalization frame for bp-038's build — no code change; the §11
    affordances already record per-stratum / event-clock / corpus-time as layer-on-top schemes.
  - A Fable session (post Jul-17 reset), sequenced AFTER CQ-scope: formalize the time-index / causal-set
    framing into dn-temporal-retrieval-algebra §2 (the anchor question), and scope the locally-clocked
    superconnection as a candidate successor object.
  - When φ_coh (the longitudinal coherence stream) is graduated, decide its clock explicitly: global N vs
    per-stratum N_corpus vs distinct-snapshot index.
  - VERIFY the external citations below against primary sources before any design note or book chapter
    cites them (the external-grounding discipline, dn-core-query-protocol §1.3 item 6 — these are from memory).

references:
  - docs/build-plans/bp-038/plan.md  # §3 Q4/Q6 snapshot semantics; §11 generalization affordances
  - docs/design-notes/temporal-retrieval-algebra.md  # §2.5 ledger as Sz.-Nagy isometric dilation; §2.3 [d,τ] Result 2/3
  - docs/design-notes/supersession-lifecycle.md  # §4A op-seq strict order (the causal spine)
  - docs/brainstorms/edge-dynamics-vector-field.md  # the velocity 1-cochain / R-ladder — "velocity per which clock"
  - docs/design-notes/edge-dynamics.md  # the 1-form lift, the space side of the space×time bicomplex
  - core/temporal/superconnection.py  # [d,τ] curvature (the object the clock intuition re-derives)
  - core/stores/versions.py  # version_seq (per-doc sub-clock); ops/lifecycle/runs.py RunLedger (per-run)
  - external [FROM MEMORY — verify]: Lamport, "Time, Clocks, and the Ordering of Events in a Distributed
    System" (CACM 1978); Bombelli–Lee–Meyer–Sorkin, "Space-time as a causal set" (PRL 1987); the
    causal-set proper-time ≈ maximal-chain-length relation.
```

## 2026-07-15T16:43:50Z — the curvature clarified: activity-RATE deforms the stratum, and that IS local time (the GR closure, and its departure)

**What "curvature" meant (owner clarification).** Not the Ricci tensor, not Forman–Ricci ("the ricci
stuff"), and not (directly) the superconnection `[d,τ]`. It is the **general-relativity picture**:
compute a local **density** at every point of a stratum → a smooth scalar field → that field **deforms
the geometry** ("the space is deformed by density"), and the deformation **sets local time**. The
parallel the owner drew: *information distorts space, which impacts local time* — GR's
`mass → curvature → time-dilation`, read on the corpus. This is a **third, distinct curvature** in the
thread, and it is the GR-gravitational one, not the tensor-calculus one.

**The refinement (the departure from GR).** The owner then sharpened the source: **it is not the
standing density but the RATE of information addition that actually distorts the space.** This is the
crux, and it is a genuine departure from GR:
- GR is sourced by **standing, conserved** mass-energy `T_μν` (`∇·T = 0`). A dense STATIC mass curves
  spacetime whether or not anything changes.
- Here the source is the **information-addition RATE** `J(x)` — a flux/current, and **non-conserved**
  (the append-only ledger *creates* mass). A dense-but-STATIC region (the frozen founding corpus)
  sources **nothing** — no ongoing distortion. Only where information is *being added* does the
  geometry warp.

So this is not vacuum GR. It is closer to: **(a)** a field sourced by a **current** — the
*magnetic/radiative* side of a gauge theory (a moving/changing source, not a standing charge), which is
exactly why the parked **magnetic Laplacian** (`dn-magnetic-laplacian`, sourced by edge-flux /
directedness) is the natural operator here, not the ordinary mass-sourced Laplacian; and **(b)** a
**matter-creation cosmology** (a growing space with sources), not a static-mass spacetime.

**Definitional vs substantive — untangling the apparent loop.** `J(x) = dN_x/dt_wall` (events per
wall-second at region `x`) IS, by definition, the local logical-clock rate — the per-region sub-clock
ticks once per event. So "rate = local time" is *definitional*, not circular. The **substantive,
testable** claim is the second half: `J(x)` does not only set `x`'s own clock — **it deforms the
geometric relationships in `x`'s neighbourhood** (a fast-growing topic bends the retrieval/similarity
geometry toward itself, changing effective distances to other notes). That is the "mass bends
spacetime" analog, with **activity-rate as the mass** — a real, measurable hypothesis.

**Computable, with machinery already in the system.** Give the activity field a potential by solving the
graph Poisson equation `∇²Φ = J` ⇒ `Φ = L⁺ J` — the **graph Green's function** of the activity field,
i.e. exactly the `(L_F)⁺` Mode-1b object (`dn-core-query-protocol` §2.2). Then the deformation/curvature
is `∇²Φ = J` (Poisson), geodesics in `Φ` bend toward high-activity regions, and a posited coupling
`clock-rate = f(Φ)` closes the loop. None of this is out of reach: `L⁺`, kernel activity-estimation, and
diffusion geometry are built or specified. And **diffusion maps already carry the density knob** — the
Coifman–Lafon `α`-parameter tunes *how much local density deforms the diffusion geometry* — so a
rate-weighted diffusion is the concrete first instrument.

**The smoothness question, resolved.** Earlier the orchestrator objected: "we're discrete; a smooth
field needs a continuum limit." The owner's construction dissolves that — kernel-smoothing the discrete
activity into a field `J(x)` gives smoothness **directly** (a KDE over the point cloud), no continuum
required. Caveat: on the **young corpus (~113 nodes)** the smoothing is sampling-limited — the field is
only as trustworthy as the sample density — so this is gated on corpus growth (the same *sample-depth*
root the whole R-ladder hangs from).

**The closure with an established result.** The temporal algebra already proved the active-view transport
is a strict **γ-contraction except at owner promotions** — *"the owner is the only energy source in the
dynamics"* (`dn-temporal-retrieval-algebra` §2.5). Fuse that with the activity-source model and a clean
statement falls out: **the owner's additions are the gravitational source that curves the corpus
geometry; everything else is dissipation (flat, contracting).** The fixed founding corpus (non-negotiable
#9) exerts no ongoing pull — consistent, because a fixed anchor has zero addition-rate, hence zero
curvature. The living geometry is bent only by live authoring.

**Four curvatures, kept distinct (no conflation):**
1. **Forman–Ricci** — static combinatorial edge-curvature of one snapshot ("the ricci stuff," set aside).
2. **Superconnection `[d,τ]`** — the space×time *transport* obstruction (severed citations); the
   time-evolution coupling.
3. **Activity-conformal curvature (THIS)** — the **rate-of-CHANGE** field `|ẇ|` (the velocity 1-cochain
   magnitude — see the coda) deforming the stratum geometry and setting local time; the GR-gravitational
   analog, sourced by a *rate of change*, not a standing mass.
4. **Ollivier–Ricci (bridge)** — if you want the discrete, computable form of "density/mass deforms
   space," optimal-transport curvature is its home (it *is* "how the local mass-ball transports"); a
   different object than the Ricci tensor of #1, and the rigorous landing spot for the intuition.

**Is the relativity parallel fair? (the xhigh verdict.)** Yes — and this version is *tighter* than the
earlier special-relativity one, because it invokes the RIGHT half of relativity: GR's
`source → curvature → time-dilation`, plus geodesics bending toward the source (which diffusion retrieval
literally does). It remains an **analogy, not a derivation**: there is no Einstein field equation (no
`G = 8πT` fixing the source→curvature coupling — we *posit* `∇²Φ = J`), the clock coupling `f(Φ)` is
chosen/measured not derived, and — the owner's own flag — the source is a **non-conserved rate**, not
standing conserved mass-energy, so it is a *different theory* (a driven / creation geometry). The causal
backbone (the ledger / op-seq order = a **causal set**) gives it a genuine Lorentzian-flavoured causal
structure, which is why the analogy runs deeper than surface. Honest one-liner: **an activity-conformal
geometry on a causal-set skeleton — GR-shaped, but current-sourced and non-conservative.**

```capsule
topic: temporal-clocks-and-strata
date: 2026-07-15

decisions:
  - The owner's "curvature" is the GR-gravitational picture (a source field deforms the stratum
    geometry, which sets local time) — a THIRD curvature, distinct from Forman-Ricci (#1, set aside)
    and the superconnection [d,τ] (#2, time-transport).
  - The source is the RATE OF CHANGE |ẇ(x)| (the velocity 1-cochain magnitude — churn/revision/
    supersession, NOT just monotone addition), a non-conserved field, NOT standing density — the
    deliberate departure from GR. The progression was density → addition → CHANGE (settled). A static
    region (the fixed founding corpus, |ẇ|=0) sources EXACTLY ZERO curvature; only live change bends it.
  - J(x) = the local logical-clock rate BY DEFINITION (events/wall-second); the SUBSTANTIVE, testable
    claim is that J deforms the NEIGHBOURHOOD geometry (activity bends retrieval geometry toward itself).
  - Computable with existing machinery: Φ = L⁺J (the Mode-1b Green's function), curvature ∇²Φ = J
    (Poisson), diffusion-maps α as the density knob; smoothness from kernel-smoothing (no continuum
    limit needed), sampling-limited on the young corpus.
  - Closure with TRA §2.5: the owner (the only energy source) is the gravitational source; everything
    else is flat/contracting dissipation — consistent with the fixed-anchor invariant (#9).

parked:
  - decision: Formalize the activity-conformal geometry (J → Φ = L⁺J → clock = f(Φ)); pick/derive f
    default: analogy + a computable sketch; the coupling f(Φ) is posited, not derived
    re_entry: a Fable pass (post Jul-17 reset) AND the R1 rate/velocity field has data (sample depth)
  - decision: Rate-as-current ⇒ the MAGNETIC Laplacian is the operator (not the mass-sourced Laplacian)
    default: noted as the natural link; not built (ML-* parked, census gate iii not met)
    re_entry: the magnetic operator unparks (its gates) AND a rate/velocity field exists
  - decision: The SIGN of the activity→geometry coupling (does activity ATTRACT or REPEL neighbours?)
    default: undetermined — an empirical sign, unlike GR's fixed dense→slow direction
    re_entry: measure local activity-rate vs neighbourhood-geometry deformation on a grown corpus
  - decision: Ollivier-Ricci as the discrete computable form of "density/mass deforms space"
    default: named as the landing spot, not adopted (owner set aside "the ricci stuff")
    re_entry: a curvature customer wants the transport-Ricci form

open_questions:
  - Is the source the rate J = ρ̇, or a higher object (acceleration ρ̈, or the velocity 1-cochain ẇ from
    the vector-field brainstorm)? Which ORDER of change curves the space?
  - Does activity-rate empirically deform neighbourhood retrieval geometry (the substantive claim) — and
    with which sign (attract vs repel)?
  - What clock coupling f(Φ) is right — √(1+2Φ) (GR-shaped), linear, exponential — and from what principle?
  - Non-conservation: is there ANY conserved quantity (a Noether charge) in a creation geometry, or is
    the ledger's monotone growth the only invariant?
  - Does this unify with [d,τ]? (activity-curvature = spatial deformation; [d,τ] = temporal-transport
    obstruction — are they two faces of one curvature 2-form on the space×time bicomplex?)

next_steps:
  - Fold this into dn-temporal-retrieval-algebra's anchor/time-index section at the post-reset Fable pass,
    with the causal-set framing + the locally-clocked superconnection from the prior capsule.
  - When R1 (the rate/velocity 1-cochain) has data, compute a first J-field + Φ = L⁺J on the live corpus
    as a diagnostic (a diffusion-maps-α diagnostic) — gated on sample depth.
  - VERIFY the external citations below against primary sources before any design note / book cites them.

references:
  - docs/brainstorms/temporal-clocks-and-strata.md  # this file, the prior (clock/relativity) section
  - docs/design-notes/temporal-retrieval-algebra.md  # §2.2 L⁺/Mode-1b Green's function; §2.5 owner = only energy source
  - docs/design-notes/dn-magnetic-laplacian.md  # rate-as-current → the magnetic operator; PARKING-LOT ML-*
  - docs/brainstorms/edge-dynamics-vector-field.md  # the velocity 1-cochain ẇ = the rate field
  - core/complex/curvature.py  # Forman (#1); core/temporal/superconnection.py  # [d,τ] (#2)
  - external [FROM MEMORY — verify]: Coifman & Lafon, "Diffusion maps" (ACHA 2006, the α density
    parameter); Ollivier, "Ricci curvature of Markov chains on metric spaces" (2009); the causal-set
    proper-time construction; GR gravitational time dilation (g_00 = 1 + 2Φ/c²).
```

### Coda (owner, same session) — the source is the rate of CHANGE, not of addition

A final sharpening, and it matters. The progression was **density → rate of addition → rate of CHANGE**,
and *change* is the settled source. The distinction is real:

- **Addition** is monotone (`≥ 0`, append-only) — it measures *growth*. **Change** includes revision,
  re-weighting, and supersession (destruction in the active view) — it measures *churn*. A section under
  heavy revision has a **high rate of change with near-zero net addition** (edits in ≈ edits out). The
  geometry should warp where the structure is *moving*, not merely where it is *growing* — so change is
  the right source.
- The rate of change is exactly the **velocity 1-cochain `ẇ`** (`edge-dynamics-vector-field.md`, R1); the
  source field is `|ẇ(x)|`, its local magnitude. So the source already has a name and a home in the
  parked velocity work — this is not a new object, it is *that* object promoted to a gravitational source.
- It makes the fixed-anchor statement **exact**: `|ẇ| = 0` (no change) ⇒ zero curvature. The founding
  corpus is a flat region *by definition* (non-negotiable #9), cleaner than the addition reading (an
  anchor could be re-cited — a change of others *about* it — without itself changing).

**The physics upgrade.** Sourcing curvature by a *rate of change* rather than a *standing density* moves
the analogy from the **static** gravity regime (Schwarzschild — a standing mass curves space) to the
**dynamic / radiative** regime: in physics it is *changing* sources that produce induced and radiated
fields (a changing current sources a magnetic field, Ampère–Maxwell; an accelerating mass distribution
radiates gravitational waves). So the corpus's geometry **ripples where the structure is changing and
lies flat where it has settled** — a living, dynamic metric, not a frozen one. *Caveat on order:* "rate
of change" as the first derivative `ẇ` is the **induction** regime (changing source → induced field);
true gravitational *radiation* is sourced by the **second** derivative (the quadrupole `ẅ`), so "which
order of change curves the space" (`ẇ` vs `ẅ`) stays an open question (already logged). Everything else
in the prior section carries over verbatim with the source reread as `|ẇ|`: the potential `Φ = L⁺|ẇ|`,
geodesics bending toward high-churn regions, the owner-as-only-energy-source closure, and the causal-set
skeleton. **Settled one-liner: a velocity-conformal geometry on a causal-set skeleton — the corpus
curves where it is changing, and the owner's edits are the only source of change.**
