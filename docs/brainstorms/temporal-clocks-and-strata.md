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
