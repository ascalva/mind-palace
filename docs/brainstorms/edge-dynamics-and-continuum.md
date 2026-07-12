# Brainstorm — Edge dynamics: phase space, Hodge threads, and the continuum bridge

> Spun out of `self-sensing.md` on 2026-07-12 (owner + orchestrator, Fable/xhigh design
> session) — consolidates the five owner-dialogue capsules of that date into one document,
> per the owner's instruction: *"make sure that all this theory, intuition, the parallels
> between continuous and discrete space, the process, the math, physics, the machinery is
> fully captured, in spirit and rigor."* Charter vocabulary for Track D's design pass.
> Code references verified in-session 2026-07-12; nothing here licenses build work.

## The arc, in one line

The system's edges — reference edges, supersession chains, correlator-proposed relations —
form a state with both position and momentum; their interaction is Hodge theory on the
existing complex one degree up; their threads are its harmonic part; their durability is
persistence; and every continuous reading of them (spline, spectrum, fitted Hamiltonian)
is an *interpretation of an exact discrete record*, never the other way around.

## 1. The physics dictionary (intuition ↔ structure ↔ house machinery)

The owner's physics background (classical mechanics: Lagrangians, Hamiltonians, action,
phase space) is not an analogy bolted on — each intuition has a precise discrete
counterpart, most already built:

| owner intuition | formal structure | house object (verified) |
|---|---|---|
| state / position | configuration q | the current snapshot (stores at HEAD) |
| direction / momentum | p — measurable only as differences across the record | supersession chains + edge-strength series (B-a creates; ledger-class per 2026-07-12 ruling) |
| "position and direction are part of the equation" | the phase point (q, p); classical dynamics is a flow on phase space, never on configuration space alone | snapshot + history; the erasure test = keep q, zero out *measured* p |
| smart vs wise | trajectory as a function of state vs a **functional of the path** | erasure-invariance line (dn-self-sensing §2.4) |
| measuring without disturbing | zero back-action observation | the passive stratum: reading the system does not steer it; each gated consumer introduces back-action deliberately |
| a set of edge vectors | a **1-cochain** (discrete 1-form; one value per edge) | reference edges exist (`core/stores/reference_edges.py`); flows over them are Track-D future |
| edges interacting / influencing | the **Hodge 1-Laplacian** L₁ (coupling via shared nodes and shared triangles) | `core/complex/laplacian.py` builds the degree-0 family L = δ*δ and *names* the general-transport (sheaf) members as deferred |
| threads weaving through the data | the **harmonic component** of the Hodge decomposition: gradient ⊕ curl ⊕ harmonic; dim(harmonic) = β₁ | `core/complex/topology.py` computes persistent H₁ — the *holes* the harmonic flows orbit ("you orbit this without stating it") |
| durable as utility increases | **persistence** — bar length under the strength filtration | the ripser machinery (topology.py); PD-f's principled measure |
| energy / disagreement | Dirichlet energy xᵀLx = ‖δx‖² | stated verbatim in `laplacian.py`'s docstring — the natural first potential V |
| Fourier (in space) | the Laplacian eigenbasis | `core/complex/spectral.py`: "the bottom eigenvectors … are the graph Fourier basis" |
| contradiction vs gap | signed balance / frustration (λ_min(L̄), odd triangles) vs topological holes | `balance.py` / `topology.py` — the routed split (dissonance ≠ hole) |
| watching structure evolve | time series of exact structural invariants | `core/complex/temporal.py` — "the system watching its own structure evolve"; detection only |

The classical-mechanics parallel runs deeper than vocabulary: with the Dirichlet energy as
potential, the Lagrangian **L(x, ẋ) = ½‖ẋ‖² − ½ xᵀLx** describes coupled oscillators on
the graph whose normal modes *are* the graph Fourier basis — the spectral machinery and
the mechanics are the same mathematics. One degree up (L → L₁), the same statement holds
for edge flows, and the harmonic subspace is the set of **zero-frequency modes**: the
threads are, precisely, the DC components of edge flow.

## 2. Two discretenesses, disentangled (terminology)

"Continuous vs discrete" enters twice, independently — conflating them muddies the
program:

- **Space.** The system lives on a discrete complex (nodes, edges, triangles), not a
  manifold. Node data are **0-forms/0-cochains**; edge data are **1-forms/1-cochains**.
  (The owner's "discrete 0-form space we encompass" is the right instinct with the degree
  off by one: the exact machinery currently operates at degree 0 — Laplacians, balance,
  spectral — and the edge-vector program is the lift to degree 1. Both degrees are
  discrete-exact.)
- **Time.** Readings land at commit times — discrete, *irregularly* sampled. The
  continuous trajectory between readings is not data; it is a modeling choice.

Continuum methods address the two axes with different tools, below.

## 3. The continuum bridge (Fourier, splines, and up the ladder)

The owner's question: can Fourier analysis or splines build a continuous approximation of
the edges over time, compared against the exact discrete processes? Yes — both, each in
its proper place, plus a third the question was reaching toward:

- **Time axis — splines first.** Commit-time sampling is irregular, so the honest
  trajectory tool is a smoothing spline (or Gaussian process) per edge series: it yields
  the continuous curve *and its derivative* — which is exactly how measured momentum p is
  estimated from the discrete record. Splines are local and assume no periodicity;
  vanilla FFT assumes uniform sampling and would silently lie here. For spectral content
  under irregular sampling, the right tool is **Lomb–Scargle / least-squares spectral
  analysis** (or spline-regularize first, then transform).
- **Space axis — Fourier is already built.** The graph Fourier transform at degree 0 is
  `spectral.py`'s eigenbasis. The degree-1 counterpart is the **Hodge 1-Laplacian
  eigenbasis** — the Fourier basis for edge flows — where low-frequency = smooth
  large-scale flow patterns and the kernel (frequency zero) = the harmonic threads.
- **Dynamics axis — Fourier *of the dynamics*.** To decompose not one series but the
  evolution operator itself, the modern tool is **Koopman / dynamic mode decomposition
  (DMD)**: fit a linear operator to successive snapshots of the edge configuration; its
  eigenmodes are growing/decaying/oscillating *patterns of edges* with associated rates —
  the spectral theory of "how the graph is moving."
- **The top rung — learning the action.** System identification in ascending strength:
  fit a potential V with ẇ ≈ −∇V (gradient flow; Dirichlet energy is the first candidate
  V; symmetric coupling ⇔ such a V can exist) → fit a full Lagrangian/Hamiltonian and
  check conservation vs dissipation. "Learning the Hamiltonian of the knowledge graph" is
  the strongest continuous reading of the record — and still, per §4, only a reading.

All of the above is standard, well-conditioned applied mathematics; the *speculative*
content is only whether this system's edge data will exhibit exploitable structure — the
weaving hypothesis, which is empirical and falsifiable, not theoretical.

## 4. The inversion (the load-bearing methodological rule)

In physics, nature is continuous and discretization is numerical approximation. **Here
the polarity is reversed:** the discrete record is the reality — deterministic,
content-addressed, exact — and every continuous object is an approximation *of it*. The
consequences are the discipline:

1. **Continuous fits are interpretations** — views in the §2.2 interpreter-contract
   sense: transform-attributed, versioned, superseding at the same identity key when the
   fit method changes. A spline is a worldview; a re-fit is a supersession. They are
   INTERPRETED-class objects, never measurements.
2. **The exact discrete invariants are the falsifiers.** Any continuous model must
   reproduce `temporal.py`-style exact quantities (β₀, frustration, hole count, spectral
   gaps) within stated tolerance; a fit that disagrees with the exact computation is
   wrong by definition. The discrete does not approximate the continuum here — the
   continuum approximates the discrete.
3. **Model complexity is gated on sample count** — the calibration methodology's
   no-retune-off-one-point rule, generalized: no Hamiltonian fits on five commits of
   ledger. Splines before spectra, spectra before operators, operators before actions;
   each rung earns entry by data volume.

## 5. Routing and safety constants (unchanged by any of this)

- **Diagnostic vs dynamical.** Everything built today measures structure ("nothing here
  alters anything" — temporal.py). A model of edges *driving* each other is a dynamics:
  correlator-class, reads `ObservedView`, emits INTERPRETED proposals only,
  dreamer-proposed authority — an interpretation of the measured trajectory.
- **The data boundary is the guarded thing, not the math.** 𝔎|_MR stays authored-only;
  cross-stratum reference edges stay out of `A_geom`/`build_complex` (ratified
  code-observation-projection §2.5). Lifting the toolbox to observed/cross-stratum edges
  is exactly the design act Track D must license.
- **Back-action is opt-in.** The system is born erasure-invariant (passive stratum, zero
  back-action) and acquires path-dependence one audited, owner-gated consumer at a time.

## 6. Status & cross-refs

Design-tier vocabulary, consolidated and graduate-adjacent but **not** a design note:
this file is the charter seed Track D's design pass consumes (with the weaving capsule of
2026-07-12T17:54Z). It licenses nothing; `dn-self-sensing` stays scoped to the
proprioceptive substrate.

Cross-refs: `docs/brainstorms/self-sensing.md` (the five source capsules, 2026-07-12);
`docs/design-notes/self-sensing.md` (§2.4 erasure test, §2.5 durability ruling, PD-f);
`docs/design-notes/code-observation-projection.md` (§2.5 A_geom exclusion — the
boundary); `docs/REASONING-COMPLEX-BUILD.md` + companion III (the degree-0 floor's
derivations); `docs/NOTATION.md`; code: `core/complex/{laplacian,spectral,topology,
balance,temporal}.py`, `core/stores/reference_edges.py`.
