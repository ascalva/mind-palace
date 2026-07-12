---
type: design-note
id: dn-edge-dynamics
status: ratified # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only # the degree-0 floor exists (laplacian/spectral/topology/balance/temporal/curvature); nothing at degree 1 is built
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/brainstorms/edge-dynamics-and-continuum.md # the charter seed this note consumes whole
  - docs/design-notes/self-sensing.md # the substrate Lane B waits on; §2.4 erasure test, PD-f
  - docs/design-notes/code-observation-projection.md # §2.5 — the data boundary this note does NOT move
  - docs/design-notes/dreaming-v2-interpreter-panel.md # the lens contract Lane A instantiates
  - docs/REASONING-COMPLEX-BUILD.md # companion III — the degree-0 derivations Lane A lifts
supersedes: null
superseded_by: null
warrant: null
---

# Edge dynamics — the 1-form lift and the continuum discipline

> Filed by the orchestrator as `draft` (2026-07-12, Fable/xhigh design session).
> Ratification is a hand edit by the owner — no command performs it, and `gate-guard`
> denies any agent attempt. `/graduate` refuses this note until `status: ratified`.
> Consumes `docs/brainstorms/edge-dynamics-and-continuum.md` whole (the five owner
> capsules of 2026-07-12, consolidated); the physics dictionary and the verified
> code-reference table live there and are not repeated here.

## 1. Purpose and scope

This note decides **how the edge-dynamics program enters the system**: what is licensed
to build now, what is named but gated, and the methodological rule every future
continuous reading of the record must obey. It is the design pass the brainstorm's §7
queue calls P1.

Three decisions:

1. **The two-lane split** (§2.1) — mirror-side structure now, observed-side dynamics
   when the substrate and the samples exist.
2. **Lane A pinned to buildable precision** (§2.2–§2.4) — the degree-1 lift of the
   existing complex machinery, entering through the existing dreamer-lens contract.
3. **The inversion as a standing invariant** (§2.5) — the discrete record is the
   reality; every continuous object is a versioned interpretation of it, falsified
   against exact discrete invariants and admitted rung-by-rung on sample depth.

Out of scope, explicitly:

- **Moving the data boundary.** Cross-stratum and observed edges stay out of
  `build_complex`/`A_geom` (ratified `code-observation-projection` §2.5). Nothing here
  seeks that supersession; Lane B is designed to *not need it*.
- **Licensing the weaving consumer.** Lane B's charter (what it reads, what it
  proposes, its authority) belongs to Track D's design pass. This note pins only its
  entry gates (§2.6).
- **Any back-action.** Everything licensed here measures and narrates; nothing steers.
  The system stays erasure-invariant (`dn-self-sensing` §2.4) until a gated consumer is
  separately designed, owner-ratified, and audited.
- **Effectors, scheduling, model changes** — untouched.

## 2. Principles / decision

### 2.1 The two-lane split (the central decision)

The brainstorm's mathematics divides cleanly by *which data exists*:

- **Lane A — mirror-side, data exists today.** The authored reasoning complex
  (`ReasoningComplex`, built from `MirrorView`) already carries nodes, a weighted
  similarity backbone `A`, and a signed overlay. The degree-1 lift — Hodge 1-Laplacian,
  harmonic threads, strength-filtration persistence, curvature refinements — is *exact
  structure on a snapshot*, needs zero history, and enters as new **dreamer lenses**
  under the interpreter-panel contract: deterministic, model-free, mirror-not-oracle,
  claims with authored support. Licensed to graduate on ratification (P4).
- **Lane B — observed-side, data accumulates.** Edge *dynamics* — trajectories,
  spectra, fitted operators, the weaving hypothesis across cost/documentation/scope
  planes — are functionals of the versioned history that `dn-self-sensing`'s B-a/B-b
  create (supersession chains, edge-strength series; ledger-class, reset-guarded).
  Correlator-class: reads `ObservedView`, emits INTERPRETED proposals, dreamer-proposed
  authority. Named here, gated in §2.6, designed under Track D.

The split is not sequencing convenience — it is the firewall expressed as a work plan.
Lane A never reads observed data; Lane B never touches the mirror-side dream path. The
two lanes share *mathematics* (the same L₁, the same decomposition — §2.7's shared-
pattern rule from `dn-self-sensing` applies: shared methodology, never shared state).

### 2.2 Lane A — the complex at degree 1, pinned

The degree-0 floor (`core/complex/laplacian.py`: L, L_sym, signed L̄, all PSD, Dirichlet
energy xᵀLx = ‖δx‖²) lifts one degree. Definitions pinned for the builder:

- **The complex.** 1-skeleton: the edges of the existing backbone `A` (post
  `sim_floor`). 2-simplices: the **3-cliques of that 1-skeleton** (the flag/clique
  complex). This choice is forced by consistency: `topology.py`'s persistence is a
  Vietoris–Rips filtration over cosine distances, and Rips at scale t *is* the flag
  complex of the distance-t graph — so the persistent H₁ already computed and the
  kernel of the L₁ built here describe the same object at matching scale
  (`distance = 1 − similarity`). Derivation hyperedges (`ReasoningComplex.hyper`) are
  directed B-arcs, not symmetric 2-simplices; they stay out, deferred with the
  sheaf/general-transport members `laplacian.py` already names as not-built.
- **Orientation.** Each edge {i, j} oriented i→j by ascending node index
  (`ReasoningComplex.idx` order); each triangle {i, j, k} by ascending index triple.
  Convention only — every quantity below is orientation-invariant.
- **Boundary operators.** `∂₁ : C₁ → C₀` (edges to nodes, the signed incidence matrix)
  and `∂₂ : C₂ → C₁` (triangles to edges, signs from orientation). Coboundaries are
  transposes (real coefficients throughout).
- **The Hodge 1-Laplacian.** `L₁ = ∂₁ᵀ ∂₁ + ∂₂ ∂₂ᵀ` (down-term + up-term). PSD by
  construction, sparse, deterministic — same house invariants as the degree-0 family
  (scipy.sparse only; no model, no network).
- **The Hodge decomposition.** `C₁ = im ∂₁ᵀ ⊕ im ∂₂ ⊕ ker L₁` — every edge vector
  (1-cochain) splits uniquely into **gradient** (induced by node potentials), **curl**
  (circulation around filled triangles), and **harmonic** (the remainder), the three
  components mutually orthogonal. `dim ker L₁ = β₁` of the flag complex: **the harmonic
  subspace is spanned by the threads, and the threads orbit exactly the holes the
  `hole` lens already reports.** In mechanics vocabulary (brainstorm §1): the harmonic
  cochains are the zero-frequency normal modes of edge flow — the DC components.
- **Degree-1 Fourier.** The eigenbasis of L₁ is the Fourier basis for edge flows
  (low eigenvalue = smooth large-scale circulation), the degree-1 counterpart of
  `spectral.py`'s eigenbasis. Provided by the same module; consumed by later rungs.
- **v1 is combinatorial.** Unweighted L₁ at the pinned scale: the kernel *dimension*
  is topological (invariant under positive reweighting), and v1's deliverable is the
  thread structure, not flow geometry. Strength-weighted inner products are parked
  (§4) — they sharpen harmonic representatives, they do not change what exists.

**The built-in falsifier (cross-validation across independent implementations):** at
matching scale, `dim ker L₁` must equal the H₁ bar count that `topology.py`'s ripser
machinery reports. Two independent computations of β₁ — incidence algebra vs persistent
homology — that must agree exactly. Any Lane A plan carries this as an acceptance
criterion, not a hope.

### 2.3 Lane A — entry through the lens contract, not beside it

The interpreter panel (`core/dreaming/interpreters.py`) is the only door into dreams:
`φ_i : G_MR → 2^K`, each lens a thin adapter over a `core/complex/` function, emitting
`Claim(statement, support ⊆ authored notes)`, model-free, adjudication elsewhere. Lane A
adds — same shape, same registry, no new authority:

- **`THREAD`** — the harmonic lens. Extracts a basis of `ker L₁`, localizes each
  harmonic class to its carrying cycle of notes, and claims the *circulating structure*:
  a closed loop of pairwise-related notes enclosing a gap — "you orbit this without
  stating it." Support = the notes on the carrying cycle. Routing class: **gap-family,
  never contradiction** — a thread is the flow *around* a `hole`, and the routed split
  (dissonance ≠ hole, `balance.py` vs `topology.py`) extends verbatim: tension stays
  with the signed machinery.
- **Durability via strength filtration.** Each thread carries its H₁ bar length under
  the strength filtration (birth/death in similarity scale — machinery `topology.py`
  already runs; the lens reads persistence, it does not recompute it). Long bar = a
  structural thread; short bar = filtration noise. This is the **principled durability
  measure** `dn-self-sensing` PD-f's re-entry condition asks for, arriving on the
  mirror side first: rank-by-persistence, never a hard threshold baked into code
  (constant lives in `DreamRnDConfig`, sibling of `hole_min_persistence`).
- **Temporal snapshots gain degree-1 invariants.** `temporal.py`'s exact-invariant
  series (the "system watching its own structure evolve," detection-only) adds
  `dim ker L₁` and total harmonic persistence per snapshot. This is Lane A's only
  time-axis touch: exact invariants sampled at snapshot times — measurements, not fits.
- **The honest-seam pattern binds.** Like the registered-but-deferred `change_point`
  lens, anything here that lacks its input *returns nothing rather than fake it* — a
  degenerate complex (no triangles, or β₁ = 0) yields zero THREAD claims, silently and
  correctly.

Firewall inheritance is structural, not asserted: the lens consumes `MirrorView`
(AUTHORED only, Invariant 6), its claims land as INTERPRETED artifacts through the
existing dream path, `core.selfcheck` runs pre-return. Nothing new touches observed
data, the network, or a model.

### 2.4 Lane A — curvature stays diagnostic; flow candidates stay candidates

`curvature.py` (Forman–Ricci; the Dreamer's `bridge` lens ranks ascending) is already
the static instrument. The dynamics the owner's instinct points at — **Ricci flow**
(curvature-driven edge-weight evolution; communities crystallize, bridges thin) — is a
*proposed dynamics* and therefore lives on the §2.5 ladder's top rung beside the
gradient-flow/Hamiltonian candidates, entered only at sample depth, validated against
exact invariants. Ollivier–Ricci (the principled form `curvature.py` defers) is parked
with a re-entry (§4), not smuggled in as part of the lift.

### 2.5 The inversion — the standing methodological invariant

In physics, nature is continuous and the discrete approximates it. **Here the polarity
is reversed: the discrete record is the reality — deterministic, content-addressed,
exact — and every continuous object is an approximation of it.** Three binding rules:

1. **Continuous fits are interpretations.** A spline, a spectrum, a fitted operator, a
   learned action is a *worldview over the record*: transform-attributed, versioned,
   entering an observation store under the interpreter contract (`dn-self-sensing`
   §2.2), superseding at the same identity key when the fit method changes. They are
   INTERPRETED-class, never measurements — and their version chains ride the same B-a
   supersession mechanics the self-sensing note builds. A re-fit is a supersession; the
   chain is the fossil record of the changing model.
2. **Exact discrete invariants are the falsifiers.** Any continuous model must
   reproduce the exact computations (β₀, β₁/holes, frustration, spectral gaps,
   `dim ker L₁`) within stated tolerance at the sample times. A fit that disagrees with
   the exact record is wrong *by definition* — the continuum approximates the discrete
   here, never the reverse.
3. **Model complexity is gated on sample count** — the calibration methodology's
   no-retune-off-one-point rule (bp-011 seal precedent; `dn-self-sensing` §2.7),
   generalized to a ladder with no skipped rungs:

   | rung | tool | what it earns | enters when |
   | --- | --- | --- | --- |
   | R1 | smoothing splines / GP per edge series | the continuous trajectory and its derivative — measured momentum p | enough points per series for honest cross-validation (irregular commit-time sampling is why splines, not FFT) |
   | R2 | Lomb–Scargle / least-squares spectra | periodicity under irregular sampling | R1 residuals warrant it; more depth |
   | R3 | Koopman / DMD | eigenmodes of the evolution operator — growing/decaying/oscillating edge patterns with rates | many snapshots; R2 stationarity evidence |
   | R4 | learned action (gradient flow ẇ ≈ −∇V, V = Dirichlet first; then Lagrangian/Hamiltonian; Ricci flow) | "the Hamiltonian of the knowledge graph" — the strongest continuous reading, still only a reading | the ladder below is green and deep |

   Exact per-rung sample thresholds are deliberately **not** pinned here (parked, §4):
   they are calibration constants set at each rung's entry gate, per stream, by the
   same predict→measure→update discipline — never retro-fitted to admit a wanted fit.

### 2.6 Lane B — the weaving consumer's gates (named, not licensed)

The weaving hypothesis (owner, 2026-07-12: threads weaving through cost, documentation,
scope-of-change planes as they accumulate — "see what the dreamer can reason about
that") is empirical and falsifiable, not theoretical. Its consumer enters only when ALL
of:

1. **Substrate exists** — `dn-self-sensing` B-a (interpreter-version supersession) and
   B-b (`AgentObservationStore` + φ_self) are built and attested; the observed planes it
   would weave actually accumulate.
2. **Sample depth clears the rung** — §2.5's ladder applies to observed series exactly
   as to mirror ones; the consumer's first rung is R1, not R4.
3. **A Track D design pass drafts its charter** — what it reads (`ObservedView`, never
   the mirror path), what it emits (INTERPRETED proposals, dreamer-proposed authority),
   and its adjudication — as a separate note the owner ratifies. This note's §2.5
   discipline binds that charter by reference.

Until then Lane B is vocabulary. The substrate is guaranteed by `dn-self-sensing`
(shared time coordinates, versioned chains, safe to accumulate); nothing else is built
ahead of its gate.

### 2.7 Routing and safety constants (restated because load-bearing, changed nowhere)

- **Diagnostic vs dynamical.** Everything Lane A builds measures structure and narrates
  it through the mirror contract; "nothing here alters anything" (`temporal.py`) stays
  literally true. A model of edges *driving* each other is Lane B's class, behind §2.6.
- **The data boundary is the guarded thing, not the math.** `𝔎|_MR` stays
  authored-only; cross-stratum reference edges stay out of `A_geom`/`build_complex`
  (ratified `code-observation-projection` §2.5). The mathematics lifts; the boundary
  does not move.
- **Back-action is opt-in.** Zero back-action today; the erasure test (`dn-self-sensing`
  §2.4) stays passing until a future gated consumer deliberately introduces
  path-dependence, one audited step at a time.
- **The memory ceiling and the deterministic floor.** Lane A is scipy.sparse
  incidence algebra on complexes of current corpus size — no model invocation, no
  resident-model pressure, cron/trough tier like every lens.

## 3. Consequences

- **On ratification, P4 graduates Lane A** (session-sized plans, blast-radius ordered;
  sketch below — graduation refines, never widens).
- **Lane B's charter** becomes Track D's design-pass obligation, gated per §2.6.
- **P5 rungs** enter one at a time as data clears each gate; each rung is its own small
  plan with the §2.5 falsifier rule as acceptance.
- **The book** gains a chapter debt: the physics dictionary + the inversion (the
  brainstorm is the source; the scribe plan picks it up with the other ratified notes).

### 3.1 Lane A builder items (post-ratification; refined at graduation)

- **L-a** — `core/complex/hodge.py`: oriented flag-complex assembly (3-cliques of the
  backbone), `∂₁`/`∂₂`, `L₁`, Hodge decomposition (gradient/curl/harmonic projectors),
  harmonic basis, L₁ eigenbasis. Deterministic, sparse, no model, no network.
  _Falsifier: on synthetic complexes with known topology (cycle: β₁ = 1; filled
  triangle: β₁ = 0; two independent cycles: β₁ = 2), `dim ker L₁` disagrees, or the
  three components fail orthogonality/exact reconstruction within tolerance; on the
  live complex, `dim ker L₁` ≠ the ripser H₁ count at matching scale._
- **L-b** — the `THREAD` lens: harmonic classes localized to carrying cycles, claims
  with on-cycle support, persistence-ranked; registered in the structural panel beside
  `bridge`/`hole`/`theme`; narration vocabulary for the dream prompt.
  _Falsifier: THREAD emits a claim on a complex with β₁ = 0 (a fabricated thread), or
  a claim whose support includes a note not on its carrying cycle._
- **L-c** — degree-1 invariants in `temporal.py` snapshots (`dim ker L₁`, total
  harmonic persistence) + the `DreamRnDConfig` constants.
  _Falsifier: a snapshot series recomputed from the same commits differs run-to-run
  (determinism broken), or the new fields perturb any existing invariant's value._

## 4. Parked decisions

| id   | decision                                    | default recorded                                                                       | re-entry condition                                                                    |
| ---- | ------------------------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| PD-a | 2-simplices beyond 3-cliques                | flag complex only; derivation hyperedges stay out (directed B-arcs, not simplices)     | the sheaf/general-transport members (`laplacian.py` deferral) get a design pass       |
| PD-b | weighted L₁ (strength inner products)       | combinatorial v1 (kernel dim is the deliverable; topology invariant under reweighting) | harmonic representatives prove too delocalized to narrate a legible carrying cycle    |
| PD-c | Ollivier–Ricci                              | Forman stays the instrument (already built)                                            | Lane A lands AND a P5 rung (Ricci-flow candidate) needs the principled form           |
| PD-d | per-rung sample thresholds                  | unpinned constants, set at each rung's entry gate by calibration discipline            | a rung's entry is actually proposed (each gate is its own small owner-visible act)    |
| PD-e | the first potential V for gradient-flow fits| Dirichlet energy (‖δx‖², already the house energy)                                     | R4 entry; alternatives compete as versioned interpretations, never silent swaps       |
| PD-f | THREAD claims in dream narration weighting  | equal citizen of the structural panel (adjudication unchanged)                         | dreamer-quality-suite evidence that thread claims need distinct adjudication          |

## 5. Open questions

- **Narration vocabulary**: does the dream prompt need new language for "circulating
  structure you have not stated," or does the hole vocabulary extend? (Owner taste
  question; costs nothing until L-b.)
- **Reference edges as 1-cochains**: `core/stores/reference_edges.py` rows are natural
  future inputs to the decomposition (project a reference flow onto
  gradient/curl/harmonic). Authored-side only it is Lane A-adjacent; leave to
  graduation whether it joins L-b or waits — the boundary question (§2.7) is untouched
  either way.
- **Does the evolution study adopt the phase-space axis** (q from snapshots, measured p
  from B-a's chains) formally, alongside economics and epistemology? Owner call at
  ratification; costs nothing now.

## Cross-references

Verified in-session 2026-07-12 (this session): `core/dreaming/interpreters.py` (the
panel contract, `Claim`, `StructuralContext`, the `change_point` honest-seam precedent,
method-name registry); `core/dreaming/dreamer.py` (mirror-not-oracle framing,
MIRROR_READABLE firewall, selfcheck pre-return); `core/complex/build.py`
(`ReasoningComplex`: nodes/`A`/`A_signed`/hyper/layers/created — no triangle set today);
`core/complex/laplacian.py` (degree-0 family, Dirichlet docstring, sheaf deferral);
`core/complex/topology.py` (`persistence` maxdim=1 over `cosine_distance_matrix`,
`long_lived_holes`); `core/complex/curvature.py` (`forman`, `most_negative_edges`).
Verified 2026-07-12 (prior session, recorded in the brainstorm): `spectral.py` Fourier
docstring; `temporal.py` charter line; `core/stores/reference_edges.py`. Asserted from
the design record: `edge-dynamics-and-continuum.md` (whole — dictionary, two
discretenesses, bridge ladder, inversion, Ricci addendum, §7 queue);
`dn-self-sensing` §2.2/§2.4/§2.7/PD-f (ratified 2026-07-12);
`code-observation-projection` §2.5 (ratified); `dreaming-v2-interpreter-panel`;
`REASONING-COMPLEX-BUILD.md` companion III §2.1–§2.5, §3.2.
