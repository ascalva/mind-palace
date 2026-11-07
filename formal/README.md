# formal

Rung L1 of the Lean ladder (`docs/design-notes/dn-mathematical-foundations.md` §2.4): statements of
the ledger's laws as Lean specs over exact arithmetic, each attacked by Plausible before anyone
proves it. A sibling lake package with zero import coupling with `core/` in either direction: Lean
states and proves laws over ℚ and ℝ, Hypothesis tests the floats in Python, and the law id joins
the two. Rung L3 enters one claim at a time: float64 claims proved over a model of binary64
rounding that is itself attacked against this machine's arithmetic.

The ledger, `docs/LAWS.md`, gives each law one row: its statement, structure, code anchor, label
and Python falsifier, and the declarations here that state it. Each declaration it cites carries
the law id in bold at the head of its docstring (`/-- **LAP-1** …`), and `check.sh` checks the two
sides against each other.

## From a row to a proof

Each family comes in three parts:

- `Palace/X/Defs.lean`, the model: the definitions its laws are stated over, mirroring the code.
- `Spec/X.lean`, the statements: every theorem the ledger cites, its proof left as `sorry`, under
  the family's scope note (what the statements cover of the code, and what they leave out). It
  imports the model and nothing else of ours.
- `Palace/X.lean`, the proofs.

`lake comparator` judges the proofs against the statements (`comparator.json`): each theorem in
`Spec/` is proved in `Palace` with exactly the same statement, from the standard axioms, and
everything the statements reach passes Lean's kernel and five independent checkers. A proof file
therefore cannot change what the ledger's laws state: only `Spec/` and the model can. The design
theorems (Sever, Frustration, Leak, Transport, and the parts of Magnetic and NegativeType no row
cites) have no `Spec/` statements yet: the kernel replays their proofs, but their statements live
in the proof files, which can change them, until code relies on them and a row cites them. Whether a statement says
what its row says stays a reader's judgment, and the reading is now confined to those two places;
`scripts/check_laws_xref.py` makes sure each cited theorem is in `Spec/` under its row's law id, and
the comparator makes sure `Spec/` is what the library proves. The arrangement is the one OpenAI's
`lean/ComparatorChallenges` uses for its results: a trusted copy of the definitions, the statements
over them, and the library judged against both.

## Layout

The families, each a model, statements and proofs as above (Binary64's laws are cited through
Roundoff and FloatModel, so it has no statements of its own):

- `Laplacian`: LAP-1, LAP-2 and LAP-3 (`core/kernel/complex/laplacian.py`).
- `Memberships`: the membership relation (`core/stores/memberships.py`) as a finite
  partial function on coordinate space, and MEM-1 to MEM-5.
- `Spectral`: `L_sym` and LAP-4 (`laplacian_sym`), and the pseudo-inverse `L⁺` that
  `core/graph/conductance.py` takes for effective resistance (CND-1).
- `Balance`: signed balance, LAP-5 and LAP-6 (`core/kernel/complex/balance.py`).
- `Cut`: conductance, CUT-1 (`core/complex/cut.py`).
- `Curvature`: Forman curvature, CRV-1 and CRV-2, and CRV-3, the emission rule of
  `most_negative_edges` that the Dreamer's bridge lens reads (`core/kernel/complex/curvature.py`).
- `Clock`: the clock laws of the global event clock (`global-event-clock.md` §2.3,
  §2.4): C1 and C2, cuts and their certificates, and proper time (GC-N6).
- `Hodge`: the Hodge 1-Laplacian (`core/kernel/complex/hodge.py`), LAP-7 to LAP-11: the
  flag complex and `∂₁ ∂₂ = 0`; for any complex, `L₁` PSD, the three-way split, the Betti number
  and orientation.
- `Heat`: the heat kernel `e^{−tL}` and the diffusion distance, CND-4
  (`core/graph/conductance.py`).
- `Rayleigh`: Rayleigh's monotonicity law, CND-2, and the leave-one-out attribution of
  the reconnection rider (`core/graph/conductance.py`, `reconnection_scan`).
- `Binary64`: rung L3's substrate, a model of IEEE 754 binary64 rounding to nearest,
  ties to even (`rn`), its laws, and attacks that check it bit for bit against this machine's
  float64.
- `FloatModel`: the bridge from Lean core's logical model of `Float` to `rn`: Lean's
  `Float` `+`, `*`, `/` and `Nat.toFloat` round as `rn` does, so the two entries hold of Lean's own
  `Float`; its attacks check the compiled C operators against that logical model.
- `Roundoff`: two L3 entries over the model: CND-6's exact comparisons of `chi_s` with
  `1.0`, and LAP-1's route agreement between two association orders of a degree sum.
- `Plane`: the shared prose plane (`core/stores/plane.py`, A3): no-leak, noninterference
  (A3.5), the search loop, the `held` cache and purge (A3.7).
- `Scope`: the capability-scope algebra (`core/kernel/scope.py`, dn-capability-scope),
  with the query engine's grants and required scopes (`core/query.py`), the role signatures
  (`core/kernel/agent_scope.py`) and the strata-to-classes table (`core/kernel/clearance.py`):
  the lattice laws, monotone delegation and where it fails, the tier, the firewalls and the zone
  law.
- `SigmaStar`: σ*, the abstraction ultrametric (`core/graph/sigma_star.py`, connectivity-
  instruments CN-2), SIG-1 to SIG-4: Kruskal's forest keeps every threshold's components, it is a
  forest, σ* is an ultrametric, and σ* read off the forest is the union-find sweep over the graph.
- `Retrieval`: the β-curve of `core/query.py`'s `free_energy_distances` (temporal-retrieval-
  algebra §2.1, Theorem A1), RSP-1 to RSP-4: the walk sum well posed under the γ-ceiling, `Z ≥ 0`
  and positive exactly on reachable pairs; the kernel `G_β = (D − z·w∘w^β)⁻¹` positive definite for
  every β with `Z = G_β D`; `e^{−β d}` the normalized kernel, so HYBRID's `K_struct` is positive
  definite at the default `β = 1`; the free energy a quasi-metric through the path product. The
  general facts beneath, for any nonnegative matrix whose rows sum to at most `s < 1`, are proved by
  extremal principles: a vertex where a vector is largest or least.
- `NegativeType`: §2.6 of temporal-retrieval-algebra, before any code computes β*: negative type
  is closed, so when `d_β → d_∞` and `d_∞` is not of negative type, `{β : d_β of negative type}`
  is bounded above, the direction the note's argument proves; cut metrics and their nonnegative
  combinations are of negative type, so the cycles `C₄` to `C₈` are (their cut decompositions are
  checked by `decide`), against the note's criterion that an isometric cycle of length 4 or more
  breaks it; `K₂,₃` is not. Cited from the note, not the ledger.
- `Magnetic`: the magnetic Laplacian of `docs/design-notes/magnetic-laplacian.md`, proved before
  any code builds it (the note defers the build). §2.1: `L^θ` Hermitian and positive semidefinite,
  its form the twisted Dirichlet energy, gauge covariance, flux-trivial as gauge-trivial, the
  kernel theorem, the undirected spectrum exactly on flux-trivial connections, the circulation
  homomorphism, evenness in `q`; §2.2: `d₁^θ d₀^θ = 1 − e^{iF}`, the parity obstruction, no
  triangle in a covering relation; §2.3–§2.4: a diamond's flux and graded digraphs. BRG-7 is the
  part the code relies on: the `θ = 0` and sign fibers are `laplacian` and `signed_laplacian`, and
  LAP-5 is the kernel theorem at ℤ/2. The rest is cited from the note, not the ledger: no code
  relies on it yet, so the comparator does not judge it, though the kernel checkers replay it.
- `Sentence`: the query sentence algebra of `docs/design-notes/dn-query-sentence-algebra.md`, proved
  before any code parses a sentence (namespace `Palace.Query`). QSA-1 to QSA-4 on the nouns: `and`
  (the Schur product) and `or` keep the cone, `within` is a congruence that keeps it, distributes
  over both and stacks by intersection; the field at an anchor of `and` is the product of the
  fields, so HYBRID's score is two columns, not an `n × n` product; a threshold commutes with
  `within` and the top-`k` does not. QSA-5 and QSA-6 on sentences: admissibility is clause-wise,
  `assume` needs a granted plane naming the overlay stratum (the Ambassador's has none), a result
  under `assume` is never `Inv`, and noninterference composes: a sentence reads only what its
  clauses read and a store's overlay is invisible outside the modality. QSA-7 on chains: admissible
  iff the product walk reaches an accepting state, dead-state pruning loses nothing, the set `E` is
  the one-state automaton, a hypothetical edge only adds chains. QSA-8 the mode table of
  `core/query.py::mode_of` after `required`, verb by verb. QSA-9 the response to a hypothetical
  edge: a rank-one update of `L` along `e_u − e_v` and of `L̄` along `e_u − σ e_v`; adding weight
  raises no effective resistance and removing it lowers none (CND-2 both ways); the given camps
  balance a new signed edge iff its sign agrees with them, and a disagreeing edge between notes
  already joined by a path is frustrated for any camps and lifts the zero mode on a connected
  support (LAP-5, LAP-6); Sherman–Morrison for the inverse of an invertible matrix. The code in
  `core/sentence/` transcribes them, so QSA-1 to QSA-5 and QSA-7 to QSA-10 are the ledger's family
  XI (`Spec/Sentence.lean`, 32 statements); QSA-6 is cited from the note. The model's `within`
  takes its region as an opaque value, so QSA-5 and QSA-6 cover a sentence without the region's
  own clauses; the code admits those too, which can only add refusals.
- `Door` (XII): ingestion as the sentence `do …` (dn-ingest-door), on a keyed model: rows, each
  identity's version chain, and each identity's key, the catalog's digest the UNCHANGED check
  reads. DOR-1 a command is admissible iff a granted plane above its scope carries the write bit,
  so a read-only grant admits none, and the Ambassador's grant as written admits a
  projection-event command and refuses a commit-clock one; DOR-7 with the key written last a
  fresh run interrupted after any step converges under re-run, in the model's stage order and in
  any order of the steps before the key (the code's), and a key written while some of the
  command's rows are not held, first or after the plane's rows as the audit's defect 1 wrote it,
  is never repaired (the controls). The code of `core/sentence/types.py` and the landing order
  are written to them, so they are the ledger's family XII (`Spec/Door.lean`, 8 statements); DOR-2, 3, 5, 6 and 8 to 12 (closure,
  commutation and batch idempotence on distinct identities, the embed count, the receipt, the
  chain as the serial order, parallel dispatch, conflict-serializability with repeated
  identities and the guard's scope, crash convergence under a parallel run, readers without a
  lock) stay design theorems.
- `Script` (XII, the door's second form): ingestion as the scripts of a generic language
  (dn-door-language), on a model of content (bytes, a label, an origin), expressions as items,
  projections and constructions, effects, and the writer's checks R2 to R8 on a store and a
  state. DOR-13 a value's label and origin are its item's under projections and the observed label
  and none otherwise, so no expression raises a label; DOR-14 the firewall, an admitted store not
  observed lands an item a source yields at the item's own path with its label, and over a plan
  every active row not observed is held before or such a store's; DOR-15 confinement to the role's
  namespace; DOR-16 a plan's stores are the first form's commands with the key last, so DOR-11 and
  DOR-12 hold of every plan; DOR-17 labels and identities fixed once stored, a new path's identity
  its own, the one its item declares, or one that moves with its bytes, paths that belong to their
  sources, retire as reconciliation; DOR-18 the type system is sound for labels. `core/sentence/interpret.py`, `core/sentence/script_check.py`
  and `core/ingest/writer.py` are written to them, so they are the ledger's family XII too
  (`Spec/Script.lean`, 15 statements).
- `Dynamics`: the dynamics of an evolving graph (`docs/design-notes/dn-graph-dynamics.md`), proved
  before any code, on a model of a value's versions (the velocity over a window of cuts, a
  0-cochain per pair of cuts), edge flows with their weighted divergence and least-squares
  potential, the Neumann partial sums and the ripple of a shock (the resolvent on a relation), the
  modes of a symmetric operator, and the quotient of a graph by a partition. DYN-1 the velocity
  adds along the chain of cuts and is the sum of its steps, and a changing potential's edge field
  is a gradient, orthogonal to every curl; DYN-2 the Neumann series: in a complete normed ring
  `Σ_k x^k = (1 − x)⁻¹` when `‖x‖ < 1` (Mathlib's geometric series), for a matrix under the row-sum
  operator norm, so for every nonnegative matrix whose rows sum to at most `s < 1`, which makes the
  killed walk's fundamental matrix the sum over all walks and the ripple the sum of the damped
  steps; the tail after `n` terms is at most `s^n / (1 − s)` entrywise and the partial sums never
  overshoot; the control, a matrix with rows summing to `1` (an eigenvalue `1`), has a singular
  `1 − M` and divergent partial sums; DYN-3 HodgeRank, `s = L_w⁺ div_w Y` is a least-squares
  potential of the flow `Y` under the weights `w`, its residual divergence-free, unique up to the
  kernel of `L_w`, which on a connected graph with positive weights is the constants; DYN-4 a
  function of a symmetric matrix acts on each eigenvector by the function of its eigenvalue, so the
  heat kernel commutes with the projection onto any set of modes, the dropped part decays at least
  as `e^{−μt}` for `μ` under the dropped eigenvalues, and a field on modes above `μ` has energy at
  least `μ` times its norm (Courant–Fischer on the modes a field lives on); DYN-5 the Laplacian of
  the quotient by a partition is `Pᵀ L P`, so coarse-graining is exact on block-constant fields and
  never lowers the spectral gap, the ripple commutes with a merge-free transport that carries every
  weight forward, and RSP-5 read block by block; DYN-6 the mixing scaffold, in the shapes of the
  switch-chain family of openai/math (`lean/ComparatorChallenges/SwitchChain.lean`, Apache 2.0;
  restated over the Laplacian's modes, nothing copied): a spectral gap as a Poincaré inequality,
  which on a connected support is exactly a bound under the nonzero eigenvalues, in the variance
  form too; total variation against `L²` by `√N / 2`; the heat kernel and the lazy walk `1 − εL`
  contracting every field orthogonal to the constants geometrically at the gap's rate. Design
  theorems (Palace and PalaceTest, no Spec rows): no code computes a velocity, a potential or a
  ripple yet; `diffuse` computes the resolvent of the killed walk, which DYN-2 reads.
- `Scale`: when a store reaches a scale at which macro behaviour can be studied, and how progress
  is attributed to sources (`docs/design-notes/dn-scale-and-attribution.md`), proved before any
  code, on the Dynamics model with the time average of a field over a window of steps and a model
  of attribution (a score per configuration of sources, the orderings, the Shapley value, the
  four axioms, the unanimity games and their Harsanyi dividends, leave-one-out). SCL-1 the
  estimation threshold: under the lazy walk `1 − εL` on a connected support with gap `γ`, the time
  average of a mean-zero field over `T` steps has energy at most `((1/T) Σ_{n<T} (1 − εγ)^n)²`
  times the field's, so at most `‖x‖² / (T ε γ)²`, and precision `δ` needs `T ≥ ‖x‖ / (ε γ δ)`:
  the window must span many relaxation times; SCL-2 scale separation: with the kept modes'
  eigenvalues at most `ν` and the dropped modes' at least `μ`, the dropped part's energy relative
  to the kept part's falls by `e^{−2(μ−ν)t}` under the heat kernel (DYN-4 and its lower-bound
  twin), so with a gap `g > 0` the `k`-mode description explains all but `ε` of what remains once
  `t ≥ log(R/ε) / (2g)`, with the discrete twin under the lazy walk; the control, the identity,
  where two equal eigenvalues straddle every cut and the share never changes, so no time separates
  the scales; SCL-3 attribution: the Shapley value, the average over every ordering of a source's
  marginal contribution to the sources before it, is efficient (the marginals telescope along each
  ordering), symmetric (the swap of two sources is a bijection on orderings), attributes nothing to
  a null source and is additive; it is the only attribution with the four, since every score is
  the combination of the unanimity games with its Harsanyi dividends as coefficients (inclusion and
  exclusion between two sets) and the axioms pin an attribution on each unanimity game, which
  gives the dividend formula `Σ_{T ∋ i} c_T / |T|`; leave-one-out agrees with it on scores with
  constant marginals and, on two redundant sources, confirms neither while each Shapley value is a
  half (`Witness.loo_confirms_nothing`, the Rayleigh family's shape). Design theorems; the power
  calculation SCL-4 is the ledger's `required_clusters` and stays in the note.
- `Bridges`: theorems that join two families, so that what one proves serves the other: BRG-1
  the Laplacian as `∂₁ ∂₁ᵀ`, BRG-2 Euler and Poincaré on the flag complex, BRG-3 Thomson's
  principle on edge flows, BRG-4 the clock's cuts and scope's closed strata as lower sets, BRG-5
  delegation's noninterference through the plane, and BRG-6 Forman's curvature as the Weitzenböck
  term of `L₁`.
- `comparator.json`: what `lake comparator` judges: `Spec` against `Palace`, the cited theorems
  (248 theorems), and the three standard axioms.
- `Compare.lean`: the comparator's comparison step, run in-process where its sandbox is unavailable
  (macOS has no `bwrap`); CI runs the comparator itself. It is weaker than the comparator: it
  compares the statements' types and the definitions' values, not constructors, recursor rules or
  axioms, which is enough while both sides load the same `Defs` oleans.
- `Export.lean`: writes the export of every `Palace` declaration and everything it uses, which
  `check.sh` replays through the kernel checkers. It checks itself first: every judged theorem is
  exported, every module contributes, and only the unsafe compiler helpers are left out, and
  `check.sh` holds its count to the audit's, since a checker accepts an empty export.
- `PalaceTest/`: the attacks, one module per ledger family's `Palace` module (the design theorems
  have none, Dynamics aside), as Mathlib keeps its tests in `MathlibTest`. `lake test` builds them, which runs every attack and negative control.
  `PalaceTest/Attack.lean` holds `survives` and `refuted`, which run Plausible with a fixed seed and
  count the instances that passed their guards.
- `Audit.lean`: lists the axioms behind every `Palace` declaration and fails on anything beyond
  `propext`, `Classical.choice` and `Quot.sound`, or on more declarations resting on `sorryAx` than
  `sorry-budget` allows, which catches a `sorry` the textual count misses.
- `sorry-budget`: the ratchet. The count of `sorry` must equal it; it only goes down.
- `check.sh`: the gate. It builds the library (warnings fail it) and the statements, runs the
  attacks (`lake test`) and Batteries' environment linters (`lake lint`), checks that the root
  files import every module (Mathlib's `mk_all`), checks the budget, greps for `axiom`, `admit`
  and `native_decide`, runs the audit, replays the export through the six kernel checkers, judges
  `Spec` against `Palace`, and checks the cross-reference with `docs/LAWS.md`
  (`scripts/check_laws_xref.py`).

## Laws

| law | statement | status |
|---|---|---|
| LAP-1 | `L·1 = 0` for every `A` | proved; attack survived 500 instances |
| LAP-2 | `xᵀLx ≥ 0` and `L` PSD, for symmetric `A ≥ 0` | proved; attack survived 500 |
| LAP-2 | `xᵀL̄x ≥ 0` for symmetric `A` of any sign | proved; attack survived 500 |
| LAP-3 | `dim ker L` = components of the support, for symmetric `A ≥ 0` | proved; attacks survived 221 and 252 non-constant kernel cases |
| LAP-7 | `∂₁ ∂₂ = 0` on the flag complex of any graph, over any ring | proved; attack survived 500 random graphs |
| LAP-8 | `cᵀL₁c = ‖∂₁c‖² + ‖∂₂ᵀc‖²`, so `L₁` is PSD and `L₁ c = 0` iff `∂₁ c = 0` and `∂₂ᵀ c = 0` | proved; attack survived 500 |
| LAP-9 | gradients, curls and harmonic flows are mutually orthogonal, and every flow splits into the three uniquely | proved; orthogonality attack survived 500 |
| LAP-10 | `dim ker L₁ + rank ∂₂ = dim ker ∂₁`: `L₁ = M Mᵀ` for `M = [∂₁ᵀ \| ∂₂]`, whose blocks' ranges meet only in `0` | proved |
| LAP-11 | reorienting by signs `σ`, `τ` gives `σ L₁ σ`: the same characteristic polynomial, kernel dimension and split | proved; attack survived 500 |
| MEM-1 | the atom projection is a multiset (multiplicity = row count); `n_doc ≤ n_occ` | proved; attack survived 500 |
| MEM-2 | the version fibers are disjoint, non-empty, and their sizes sum to `\|M\|` | proved; attack survived 500 |
| MEM-3 | runs are the adjacent-collapse encoding: one edge per change of occupant, `\|edges\| = \|runs\| − 1`, edge ends differ, a revert stays visible | proved; attacks survived 500 each, one of them against a transcription of `slot_runs`' loop |
| MEM-4 | landing reconciles currency every time, so it agrees with each path's newest landing, reverts included | proved; attack survived 500 landing histories |
| MEM-5 | coherent currency selects one fiber per path; `current_any(v) ⇔ n_doc(v) > 0` | proved; attack survived 500 |
| `L_sym` PSD | for symmetric `A ≥ 0` | proved; attacked through the identities under LAP-4 |
| LAP-4 | eigenvalues of `L_sym` lie in `[0, 2]`; an isolated vertex has an identity row (eigenvalue 1); `L_sym` annihilates `D^{1/2}·1` | proved; its two identities survived 500 each |
| `L⁺` | the Moore–Penrose inverse (all four Penrose equations), symmetric, PSD for symmetric `A ≥ 0` | proved; shadow attack survived 500 |
| CND-1 | `R_eff = L⁺ᵢᵢ + L⁺ⱼⱼ − 2L⁺ᵢⱼ ≥ 0` | proved; inside the shadow attack |
| LAP-5 | on a connected support, `L̄` has a zero-energy vector (`λ_min = 0`) iff the signed graph is balanced; without connectivity it fails, which is why `signed_spectrum` takes the max over components | proved, with a witness for the failure; attacks survived 468 and 470 connected cases |
| LAP-6 | a triangle is frustrated iff the product of its signs is negative, iff it has an odd number of negative edges | proved; attack survived 495 |
| CUT-1 | `Φ(S) ∈ [0, 1]` for symmetric `A ≥ 0`, and `Φ(S) = 0` iff no weight crosses, under the code's conventions for a degenerate `S` | proved; attacks survived 500 each |
| CRV-1 | `Ric_F(u, v) = 4 − deg u − deg v + 3·\|N(u) ∩ N(v)\|` on the support | the definition; agrees with the code's `B @ B` computation on 500 graphs |
| CRV-2 | two cliques and a bridge: `Ric_F(bridge) = 4 − 2n` for cliques of `n` vertices, the strict unique minimum, negative exactly from `n = 3` | proved for every `n`; checked on every edge for `n` from 1 to 8 |
| CRV-3 | `most_negative_edges` emits the edges with `κ ≤ 0`, or, when every edge is positive, only those at the minimum, never the whole graph; in strictly increasing `(κ, i, j)` order; the `top_k` smallest candidates, `min(top_k, \|candidates\|)` of them, each `top_k` a prefix of the next | proved; attack survived 500 random graphs against a transcription of the code |
| CRV-2, CRV-3 | on two cliques and a bridge the bridge lens emits exactly the bridge, for every clique size and every `top_k ≥ 1`: by the `κ ≤ 0` rule from two vertices per clique, by the minimum rule for one | proved |
| CLK-1 (C1, C2) | a clock monotone along `≼` (C1) into a partial order has convex fibers (C2), so C2 adds nothing to C1; C1 needs checking only on the generator edges | proved, with witnesses that C2 needs antisymmetric ticks and does not give C1; attack survived 472 |
| CLK-2 (cuts) | a set is a cut (a down-set of `≼`) iff no generator edge reads into it from outside; cuts are closed under ∩ and ∪; a frontier cut needs only its cross-store edges checked; certificates compose by the pointwise minimum and maximum of their frontiers | proved; attacks survived 500 each |
| CLK-3 (GC-N6) | proper time, the longest chain in steps, is 0 at a point, at least 1 across a strict step, finite on a finite `N`, satisfies `τ(a, b) + τ(b, c) ≤ τ(a, c)` for `a ≤ b ≤ c`, and is bounded by the tick difference of any strictly monotone clock; in events, as `Spine.proper_time` counts (`eventCount`), it is 1 at a point, symmetric, 0 exactly when concurrent, and its triangle holds up to the middle event counted twice | proved; the reverse triangle survived 500 random DAGs on the longest-path recursion, and the event laws 500 on the code's own count, whose unshifted triangle is refused |
| CLK-4 | `≼` is a partial order when the generator edges have no cycle; a cycle through two events breaks antisymmetry | proved, with the witness; attack survived 500 forward-edge graphs |
| CND-4 | `H_t = e^{−tL}` is symmetric, `H_0 = 1`, `H_{s+t} = H_s H_t`; the code's `d_t = √(G_ii + G_jj − 2G_ij)` with `G = H_{2t}` is the Euclidean distance between `H_t eᵢ` and `H_t eⱼ`, so a metric that separates every two vertices for every `t`, across components too; for symmetric `A ≥ 0`, `d_t` is non-increasing in `t` | proved; its two exact steps survived 500 each |
| CND-2 | Rayleigh's law: adding weight never raises effective resistance (`∞` across components) nor lowers effective conductance (`0` across), so a rise needs a weight-increased edge; through Thomson's principle, `2vᵀx − xᵀMx ≤ vᵀM⁺v` for `v` fixed by `M M⁺`, which by the Penrose equations alone is every `v` orthogonal to `ker M` | proved; attack survived 500 |
| leave-one-out | reverting an increased edge never raises conductance; with a single increased edge every rise confirms it; a rise carried by two redundant new paths confirms neither | proved, with a witness; attack survived 500 |
| bridge | Lean's `Float` `+`, `*` and `/` (nonzero divisor) return `rn` of the exact result, for finite operands and results below `2^1024`, and `k.toFloat` is exact below `2^53`: core's logical model of `Float` rounds as `rn` does | proved; the compiled C operators matched the logical model bit for bit on 500 sums, 500 products and 500 quotients |
| CND-6 (Lean `Float`) | `k.toFloat / n.toFloat == 1` exactly when `k = n`, and the quotient is `≤ 1`, for `k ≤ n < 2^53`: on finite `Float`s `==` and `≤` compare exact values | proved over Lean's `Float` |
| LAP-1 (Lean `Float`) | two association orders, summed in Lean's `Float`, of the same at most four nonzero nonnegative finite summands (exact sum at most `2^1000`) agree within `4·eps` of either result | proved over Lean's `Float` |
| PLN-1 (A3 no-leak) | every search hit under `C` is a table atom with a cleared occupancy and carries only rows of classes in `C` that hold it, under any cache: `PlaneHit`'s checks never fire on the plane's own reads | proved; attack survived 484 traces in which any write may crash partway |
| PLN-3 (search) | `PlaneReader.search`'s widening loop returns the first `k` atoms of the exact ranking that a cleared relation holds; `\|ps\|` rounds suffice | proved; attack survived 500 |
| PLN-4 (cache) | land, retire, purge and repair keep `held`/`held_ever` coherent: `wanted ∪ freed` covers every row a land touches | proved; attack survived 500 traces |
| PLN-2 (A3.5) | noninterference: after any trace of writes that keep each path at one stratum, a reader under `C` sees, in its view and in every search, what it would see after the cleared writes, purges and repairs alone | proved by unwinding, under the hypotheses below; attack survived 480 traces with an uncleared write and a cleared hit |
| `rn` | binary64 rounding to nearest, ties to even, without overflow: it fixes binary64 numbers, is monotone and odd, lands on binary64, and moves `x` by at most half an ulp; on the grid of multiples of `2⁻¹⁰⁷⁴` (every sum of two binary64 numbers), by at most `u\|x\|`, `u = 2⁻⁵³`, subnormals included | the model; on this machine it matched 500 sums, 500 quotients and 500 quotients `k / n` bit for bit |
| CND-6 (float64) | `chi_s = rn(chain / n_s)` is `1.0` exactly when the chain spans the stratum, for every `n_s < 2^54`, and not at `2^54`; `chi_s ≤ 1` for every `n_s`, and `chi_s > 0` up to `2^1074` | proved over `rn`, with the witness; on this machine it survived 500 |
| LAP-1 (float64) | two association orders of the same at most four nonzero nonnegative binary64 summands agree within `4·eps` of either result, so the boundary test's route-agreement bound holds on every row of its fixtures; at eight summands two orders differ by five ulps, beyond the bound | proved over `rn`, with the witness; on this machine it survived 340 rows that reassociate |
| PLN-5 (A3.7) | after `purge(d)` no row or edge names `d`; every atom `d`'s rows held is deleted or still held; no atom another row holds is freed; re-running finishes a purge interrupted after its atom delete | proved; attack survived 500 |
| SCO-1 (Σ) | closure under refinement is a closure operator, and closed sets are closed under ∩ and ∪; `top()` is every stratum but `foundation`, `hypothetical` and `exhaust`, so not the top of the closed sets | proved; attack survived 500 |
| SCO-2 (windows) | `⊑` is a preorder, not antisymmetric (`pt(1)` and `[1,1]`); join is the least upper bound of any two windows; meet is a lower bound of any two and the greatest among well-formed ones, so of every window the constructor accepts; on those, meet is commutative and associative; absorption holds up to the preorder | proved, with witnesses; attacks survived 421, 206 and 500; commutativity and associativity attacked, survived 500 |
| SCO-3 (delegation) | a meet that exists lies under both inputs and is their greatest lower bound for well-formed windows; it is partial across clocks, whatever atlas is registered, and where the result trips the SLICE rule; a cut one side carries survives when the meet keeps its window | proved, with witnesses; attack survived 494 pairs |
| SCO-4 (GC-4 atlas) | the atlas completes the time meet of two covered clocks on `N`, under neither input on another clock, which is why delegation does not use it | proved, with the measured witness |
| SCO-5 (tier) | any composition of meets and joins that exists carries exactly the least tier among its inputs | proved; attack survived 329 |
| SCO-6 (firewalls, zone) | admissibility and the zone law are downward closed and survive every meet; a world-reaching scope that passes the zone law names only `world`, the denylist and the overlay, so is cleared for no class under any table that gives those three none; the zone law does not survive join | proved, with a witness; attack survived 306 |
| SCO-7 (grants) | a grant's meet skips the pairs with no meet, lies under both grants plane by plane, never trips `InadmissibleGrant`, and admits only what both admit | proved, with a witness |
| SCO-8 (`search`) | `search` never raises `SliceError`, over any strata, with or without history; over `reference` alone it builds with the single-read cut and the Ambassador's grant admits it | proved; attack survived 500 |
| SIG-1 | Kruskal's forest has, at every threshold, the graph's components: one forest yields every pairwise σ* | proved; attack survived 500 |
| SIG-2 | what the loop keeps is a forest, `\|F\| + c(F) = \|V\|`, and its labels are its components | proved; attack survived 500 |
| SIG-3 | σ* is a symmetric ultrametric | proved; attack survived 500 |
| SIG-4 | the forest's bottleneck snapped to the grid is the union-find sweep's σ*, the strictest grid point for a vertex and itself, `None` exactly when unconnected | proved; attack survived 500 |
| BRG-1 | `∂₁ ∂₁ᵀ = D − A`: the graph Laplacian is the Hodge complex's vertex end | proved; attack survived 500 |
| BRG-2 | Euler and Poincaré on the flag complex, `\|V\| − \|E\| + \|T\| = b₀ − b₁ + b₂`, and `b₀ = \|V\| − rank ∂₁` | proved |
| BRG-3 | Thomson's principle on edge flows: energy at least `vᵀ M⁺ v`, attained only by the gradient flow; the effective resistance is at most every unit flow's energy | proved |
| BRG-4 | the clock's cuts and scope's closed strata are lower sets of reachability preorders | proved |
| BRG-5 | a delegated scope is cleared for less, sees less, and noninterference holds of it | proved |
| BRG-6 | Forman's curvature is the Weitzenböck term of `L₁` | proved; attack survived 500 graphs, every edge |
| BRG-7 | the magnetic Laplacian's `θ = 0` and sign fibers are `L` and `L̄`, and LAP-5 is its kernel theorem at ℤ/2 | proved; attacks survived 500 (fibers) and 467 (kernel) |
| RSP-1 | the walk sum is well posed, `Z ≥ 0`, `z_ii ≥ 1`, and `z_ij > 0` exactly on reachable pairs | proved; attack survived 500 |
| RSP-2 | `Z = G_β D`, the kernel `G_β` positive definite for every β | proved; attacks survived 495 and 500 |
| RSP-3 | `e^{−β d}` is the normalized kernel, positive definite on a connected support; `K_struct` at `β = 1` | proved; attack (squared) survived 500 |
| RSP-4 | the free energy is a quasi-metric; the code's distance a pseudometric | proved; attack survived 500 |
| QSA-1 | `and` (the Schur product) and `or` keep the cone | proved; attack survived 500 |
| QSA-2 | `within` is a congruence, keeps the cone, distributes over `and` and `or`, stacks by intersection | proved; attacks survived 500 each |
| QSA-3 | the field at an anchor of `and` is the product of the fields, of `within` the masked field | proved; attack survived 500 |
| QSA-4 | a positive threshold commutes with `within`; the top-`k` does not | proved, with the witness; attack survived 500, the top-`k` control refuted within 5 |
| QSA-5 | admissibility is clause-wise; `assume` needs a plane naming the overlay, which the Ambassador's grant lacks; a result under `assume` is never `Inv` | proved, by `decide` and by structure |
| QSA-7 | a chain is admissible iff the product walk accepts; dead-state pruning is sound; an added edge only adds chains; the set `E` is the one-state automaton | proved; attacks survived 500 each |
| QSA-8 | `mode_of ∘ required`, verb by verb | proved |
| QSA-9 | a hypothetical edge is a rank-one update of `L` and of `L̄`; both Rayleigh directions; the given camps balance a new signed edge iff its sign agrees, and a disagreeing edge closing a path is frustrated for any camps; Sherman–Morrison for an invertible matrix | proved; attacks survived 495, 495, 500 and 484 |
| DOR-1 | a command is admissible iff a granted plane above its scope carries the write bit; a read-only grant admits none; the Ambassador's grant as written admits a projection-event command and refuses a commit-clock one | proved, by structure and by `decide` |
| DOR-7 | with the key written last, a fresh run interrupted after any step converges under re-run, in the model's stage order and in any order of the steps before the key; a key written while some of the command's rows are not held, first or after the plane's rows, is never repaired | proved; attacks survived 500 (every prefix) and 500 (two steps in either order), both controls refuted on the first instance |

The binarized forms (0/1 adjacency) reduce to Mathlib's `SimpleGraph.posSemidef_lapMatrix` and
`card_connectedComponent_eq_finrank_ker_toLin'_lapMatrix` in one line each.

Each attack has a control, a nearby false law that must be refuted. Plausible refutes the LAP-1
and LAP-2 controls within 10 to 52 instances. It did not refute LAP-3 without `A ≥ 0` or without
symmetry in 215 to 396 tested instances, because a counterexample needs weights that cancel at
every vertex. Both hypotheses are shown to be needed by proved witnesses instead
(`lap_kernel_needs_nonneg`, `lap_kernel_needs_symm`).

The membership controls are the store's known wrong readings, each refuted within 12 to 35
instances: one row per document (the set reading), fibers keyed by blob alone (a rename shares a
blob across two paths), the lifetime count in place of the current one, distinct collapse in place
of adjacent collapse (`[2, 0, 2]`), and the C1 lander that skips reconciliation when a fiber
exists, refuted on the history `[(0, 0), (0, 1), (0, 0)]`: a revert on one path.

`L_sym` and `L⁺` have no executable form here (square roots; a spectral decomposition over ℝ), so
their laws are attacked where they are exact. `L_sym`'s rest on two identities over any
commutative ring, attacked over ℚ with arbitrary weights and scalings. `L⁺`'s are attacked on the
shadow `(L + P)⁻¹ − P` over ℚ, with `P` the projector onto the component indicators; the attack
checks all four Penrose equations on it, so a passing shadow is the Moore–Penrose inverse itself.
Its control, the connected-graph formula `(L + J/n)⁻¹ − J/n` applied to every graph, fails on the
first disconnected one.

The third batch's controls: LAP-5's global reading, without connectivity, is refuted on a negative
self-loop beside isolated vertices (singular, not balanced); LAP-6 as "a balanced triangle has no
negative edge" fails on two negative edges; CUT-1 on asymmetric weights exceeds 1; CRV-1 on
asymmetric weights no longer matches the code; and CRV-2 with the test's threshold, negative from
`n = 4`, fails at `n = 3`, where the bridge is already `−2`. A mutation of CRV-1's triangle
coefficient from 3 to 2 leaves every CRV-2 proof intact (no triangle runs through the bridge) and
is caught only by the attack against the code.

The plane's noninterference (A3.5) holds under four hypotheses the plane's header does not
state. Each is stated in `Spec/Plane.lean`, and the two the model can break have proved
witnesses:

- Search is exact, with ties broken by atom id. LanceDB breaks exact distance ties by physical row
  order, and `set_held` rewrites a row to the end. So an uncleared write that changes a tied
  cleared atom's held set can swap two tied atoms across the cut (measured on lancedb 0.33.0).
  On 2026-11-01 no two live prose atoms shared a vector (72 in `vectors.lance`, 147,417 in
  `research_curated.lance`), so a tie needs a float coincidence today.
- The table is content-addressed: an atom's text and vector are a function of its id. The first
  writer's vector is the one stored, so this asks for a deterministic embedder.
- The cache is complete on `C`. A crash between a land's commit and `_refresh_held` leaves the
  atom's cache empty and a cleared search misses it (fail-closed). `_refresh_held` rewrites a
  touched atom's whole held set, so an uncleared land that shares the atom brings the hit back
  (`drift_interferes`). `repair()` restores completeness.
- Every path lives at one stratum fixed in advance (A3.6). A land whose path another class holds
  is refused, and that check reads the uncleared relations: an uncleared document at a path makes
  a cleared land of the same path fail (`stratum_interferes`).

The plane's controls: lands and retires at arbitrary classes (the stratum channel) are refuted
within 26 instances, a reader whose join reads every class (the property test's seeded leak)
within 11, cleared lands that crash before their cache step within 36, a reader that trusts the
cache in place of the cleared join within 106, `freed` without the old derivation's atoms within
17, the search loop without its `seen` set within 25 (`[0, 0]`), and a purge without its
still-held check within 10.

Outside the model: `relabel` and `reset` (each moves or forgets whole classes, a visible act for
any clearance it names), a land of several fibers in one transaction, and `known()`, which tells
the write path whether the shared table holds an atom of any class, the deduplication side channel
of Harnik, Pinkas and Shulman-Peleg (2010). Only ingest calls it (`core/ingest/index.py`).

The dreamer laws. C2, convex fibers, is not a law of its own: any clock monotone along `≼` into
partially ordered ticks has them, so a property test of C2 can fail only where one of C1 fails,
unless the ticks are compared by a preorder that is not antisymmetric. Proper time and the heat
kernel have no executable form (a supremum over chains; the exponential of a matrix): proper
time's reverse triangle is attacked on the longest-path recursion a materialized `N` would run,
and CND-4 on its two exact steps, the Gram identity for the square of a symmetric matrix and the
triangle inequality of the Gram distance of a positive semidefinite one. The controls: CRV-3
without its minimum rule is refuted within 6 instances (a lone positive edge emits nothing) and
with ties broken by `(κ, j, i)` within 50; the cut falsifier searching edges out of the set within
16; C1 into ticks compared by a preorder that is not antisymmetric within 74; the ordinary triangle
inequality for proper time within 103 (a detour longer than the path through `b`); the Gram
identity for a non-symmetric matrix within 10, and the Gram triangle for an indefinite one within
10.

Rayleigh's law (CND-2) has the same exact shadow as `L⁺`. Its reversal, that adding weight never
raises conductance, is refuted within 5 instances. Leave-one-out completeness, that every rise
confirms some increased edge, is refuted within 29, on a cycle of new edges, and fails in general
(`Witness.loo_confirms_nothing`): when the new edges are redundant, `reconnection_scan` reports a
genuine reconnection with no bridging edge. Its docstring's "never a guess" holds, but an empty
attribution does not mean the rise is spurious.

Rung L3 (§2.4) enters per claim. Its substrate, `Palace/Binary64.lean`, is written here in
Flocq's terms: FloatSpec, the Flocq port issue #48 names, pins Lean v4.34.0-rc2, an older Mathlib
and cslib (checked 2026-11-01), and Mathlib's own `FP` module is deprecated without replacement.
The model's fit to real arithmetic is attacked, not assumed. Lean's `Float` is the host's binary64,
so each attack decodes the hardware's result bit for bit and compares it with `rn` of the exact
result. Of the 500 sums seed 131 draws, 313 are exact, 120 are ties, 67 round elsewhere, 25 land in
the subnormal range and 42 round up into the next binade. Its controls, ties away from zero, a
52-bit significand and flush to zero, are each refuted by the second instance.

Lean v4.33.0 gave `Float` a logical model in core (lean4 #14079, 2026-08-10; v4.35.0 modelled
`fma`, and v4.36.0-rc2 adds only the `minimum` models; the model has no ceil, floor or round and
no bridge to the reals, by design): bit patterns, unpacked into a sign, a significand and an
exponent, with each operation rounding its exact result once through a round bit and a sticky
bit. `Palace/FloatModel.lean` proves that model's `+`, `*` and `/` are `rn`. The
proof turns on one invariant: an extended significand represents a value when it is the value's
floor and its two bits place the value against the midpoint. A right shift halves the represented
value, and core's ties-to-even choice is `rne` of it. Division also needs core's exponent estimate
to leave 53 bits of quotient, which it does for a canonical dividend. With the bridge, both entries
are theorems about Lean's `Float`, and the trust left is that the compiled C operators agree with
the logical model. That is attacked on this machine. Its control, `+` checked against the model's
`-`, is refuted on its first instance.

The two entries settle claims §2.5 makes about float64:

- CND-6. §2.5 says `(n−1)/n` rounds strictly below `1.0` "for realistic N_s". That holds for every
  `N_s < 2^54` (about 1.8·10¹⁶) and fails at `2^54`, where `1 − 2⁻⁵⁴` ties and rounds to the even
  `1.0` (`rn_div_two_pow_54`). Python divides two ints by rounding their exact quotient once (it
  matched `fractions.Fraction` on 200,000 random pairs of up to 80 bits), so `chi_s` is
  `rn(chain / n_s)`. The control, the same law in binary32, is refuted on its first instance.
- LAP-1. The route-agreement bound is a theorem for rows of at most four nonzero weights; every
  fixture row has at most three. It fails at eight (`lap1_fails`, reproduced on this machine). From
  `1 + 2u`, adding `3u` and then six `u` one at a time loses every tie and ends at `1 + 4u`; pairing
  them first wins three ties and ends at `1 + 14u`. For five to seven summands it is open, but an
  exhaustive search over every association order of one summand near `1` and the rest small
  multiples of `u/2` found no counterexample. Measured with NumPy 2.5.4 and SciPy 1.18.1 on
  2026-11-01, the two routes in the test first break the bound on a star of 37 weights, `1` and 36
  copies of a weight just under `2⁻⁵³`, by five ulps. Random rows of 8 to 3,000 weights in
  `[0.3, 1]` reached at most 0.66 of the bound. So the bound holds for short rows and for weights
  of modest range, not by construction. The control, eleven summands absorbed one at a time or
  gathered first, is refuted within 4 instances.

The scope algebra. `Palace/Scope.lean` transcribes `core/kernel/scope.py` and the parts of
`core/query.py`, `core/kernel/agent_scope.py` and `core/kernel/clearance.py` that build or read
scopes, and the transcription was checked against the Python by enumeration: which of 196 raw
windows the constructor accepts, and every pair of the 52 it does (meet, join and `⊑`); every
construction of 450 scopes (the SLICE rule, the zone law, admissibility) and every pair of the
valid ones (meet, join, `⊑`, and which error each raises); 70,756 meets of single-plane grants;
and `required()` for 43 lists of the Ambassador's strata names, with and without history, and its
five other verbs: 269,561 results, all identical (2026-11-02, against the code as fixed).

The model found six defects in the code as it was; the fixes are on the same branch, and each
witness now checks the fix (`Palace.CQ.Witness`):

- The Ambassador's `search` over `reference` alone raised `SliceError`. `required` set the
  single-read cut when given more than one name, but the slice rule counts strata after closure,
  and `reference` closes to two. The cut now follows the closed strata, and no search slices
  (`search_never_slices`).
- Two valid scopes on one clock can have no meet: `[1,5] ⊓ [5,9] = pt(5)` over two strata with
  no cut. `Grant.meet` let that `SliceError` escape; it now skips the pair, as it skips a
  cross-clock one. A meet also dropped a cut only one side carried, so an owner's point grant
  met with a dreamer template on `∗` sliced; the cut now survives when the meet keeps that side's
  window, since a consistent cut stays consistent on fewer strata.
- With a clock atlas registered (GC-4), delegation was not monotone: the cross-clock meet landed
  on `N`, under neither parent. `Scope.meet` no longer uses the atlas; `TimeScope.meet` keeps the
  completion for retrieval. The alternative, ordering scopes across clocks by their pulled-back
  event sets, would make admission depend on what the spine holds, and admit a request for
  events that do not exist yet.
- The atlas meet was not associative: `[s1,s2] ⊓ [s2,s3]` was `⊥` by `Window.meet`, while the
  atlas's `_in_window` counted an opaque interval's endpoints as members, and two `N`-windows
  carrying event sets met by equality. An opaque interval now pulls back to no event, and two
  `N`-windows meet as sets. Measured on an in-memory spine: commutative and associative over
  every triple of 18 covered scopes; the Lean model does not include the spine.
- `PRIVATE_STRATA` omitted `exhaust`, the agent-side dialogue rows (dn-agentic-loop §2.4b), so a
  grant reading only them with world reach passed `Grant`. It is now taken from the refinement
  relation, and the grant is refused (`exhaust_refused`).
- An inverted interval broke the greatest lower bound, and `top()` was documented as `R ∖ 𝔇`
  though it also omits `exhaust` and `hypothetical`. The window constructor now refuses inverted
  intervals and malformed shapes, and the docstrings say what `top()` is.

The controls: antisymmetry of the window order is refuted within 7 instances (`pt(−3)` and
`[−3,−3]`), the greatest lower bound without well-formedness within 19, the meet in place of the
join at once, commutativity over windows of any shape within 16, the atlas's time completion as a
delegation within 9, the zone law across a join within 22, the greatest tier in place of the
least within 5, every named set already closed within 6, and the old search rule within 26
(`reference`).

The Hodge batch (LAP-7 to LAP-11) is attacked over `ℤ` on random graphs of six vertices, each
graph a bit per vertex pair. Its controls: `∂₂` with every sign `+` has a boundary, refuted within
57 instances; the down term minus the up term is not positive semidefinite, within 106; gradients
are not orthogonal to the mis-signed curls, within 70; and `L₁` itself changes under reorientation,
within 30. The reorientation attack writes the products with diagonal sign matrices entrywise
(`Matrix.mul_diagonal`): as products, the interpreter re-sums them at every entry, and that one
attack took 110 s.

The σ* batch (SIG-1 to SIG-4) is attacked on random edge lists over five vertices with weights in
`Fin 4`, so ties, repeated edges and self-loops all occur. Its controls: the loop run in ascending
order, a minimum spanning forest, loses components at high thresholds, refuted within 43
instances; keeping every edge breaks the forest count within 10; the raw similarity is no
ultrametric, within 35; and snapping up to the grid in place of down, within 5.

The bridges are attacked where they compute: BRG-1 over `ℤ` on the Hodge batch's random graphs,
its control the signless Laplacian `D + A`, refuted within 19 instances; and BRG-6 on every edge
of each random graph, its control the down Laplacian `∂₁ᵀ ∂₁` alone, which misses the triangles,
refuted within 73. The others are over `ℝ`, over sets, or over the plane's traces, and
do not run.

The retrieval curve is attacked at `β = 1`, where the killed walk `z (w_ij / d_i) w_ij` is
rational, by exact Gauss–Jordan elimination on `Fin 5` with `z = ½`. Its controls: without the
killing, `z = 1`, a component of unit weights makes `I − W` singular, refuted within 34 instances;
the degrees on the wrong side, `Z = D G`, within 10; the free energy one way, unsymmetrized, is not
the normalized kernel, within 11; and without `z_jj` the path product fails, within 11.

Negative type is attacked over ℚ on `Fin 5` with vectors summing to zero: squared line metrics
survive 500 and the cycle `C₅` 500, and `K₂,₃`'s metric, the control, is refuted within 174.

The sentence algebra is attacked on exact shadows (seeds 219 to 244): kernels over ℚ on `Fin 3`,
Gram matrices `Bᵀ B` for the cone and `B + Bᵀ` for either sign, regions from three bits; typed graphs
on three vertices with a chain's own edges added so that random chains are chains, run against the
grounding automaton `S*·(C|D)`; hypothetical edges on weights over ℚ; Sherman–Morrison on `Fin 2`
with the explicit inverse, as the identity the updated matrix times the formula satisfies. Every
attack survived 500 instances, but the two Laplacian updates 495 (five pairs with `u = v`
discarded) and Sherman–Morrison 484 (sixteen singular or degenerate draws). Its
controls: the Schur product and the mask of symmetric matrices of either sign are indefinite; the
mask does not distribute over the matrix product, nor the anchor's field; the top-`k` through a mask
is the non-rewrite; the set `{S, C, D}` admits chains the grammar rejects (`CS`); not every chain's
prefix is live (`F`); "some letter in the set" in place of every letter; the grounded chain over
the listed edges alone, without the edges the assumption supplied; one arc alone is no rank-one
Laplacian update; on a present edge of the other sign the absolute values do not add; a contradiction
between allies breaks the camps; and the Sherman–Morrison correction added instead of subtracted.

The door is attacked on exact shadows (seeds 245 to 272): rows over `Fin 4` from four bits, two or
three identities, two digests, chains as lists, keys unset but in `held`, a state holding a version
under its key. Every attack survived; four tested 494 or 495 instances, the rest discarded as
draws that break their guard (two versions with one digest). Its controls, each refuted within six
instances: an ingest that always appends a version is not idempotent; on one identity the two
orders give two chains, and an interleaving lands the other order's chain; a run that writes its
key first, or after the plane's rows as the audit's defect 1 did, is never repaired; a schedule
that swaps two versions of one note lands the other chain; a command whose run is not a prefix of
its own steps is never repaired; a key-first run shows a reader rows that are not there; a revert
whose guard reads the key early lands the edit alone; two versions of one note stopped out of order
do not converge; and a serial run on one identity stopped inside a command does not converge when
the whole batch runs again.

The language is attacked on exact shadows too (seeds 273 to 287): bytes over `Fin 4`, three
labels and three paths, views as lists over `Fin 2`, a writer's state decoded from a list of
codes. Every attack survived; three tested all 500 instances, the others 156 to 487, the rest
discarded as draws that break their guard (a store the writer does not admit). Its eight
controls, each refuted within thirteen instances: a construction that keeps the label of what it
was built from; a writer without R4 that stores an authored item at another path; without R6's
condition, an identity grafted from a path its source still has; without the declaration, an
identity an item does not declare (the second form's audit found a `ref::` grafting a note onto
another's chain); without R7's condition, an item still in its source retired; a writer without
the namespace, every other rule kept, that stores an item outside the role's prefix; without R8,
a composed value squatting a source's path; and a type rule that gives a construction no
label.

The magnetic operator is complex and its transports are exponentials, which do not run, so its
attacks fix the transports at their exact values, `1` at phase `0` and `−1` at phase `π`, or test
the combinatorial content. BRG-7's controls: transport `−1` everywhere gives the signless `D + A`,
refuted within 7 instances; the sign put on the positive entries, within 6; and the kernel check
without its loop condition, refuted on the first connected graph balanced by construction with a
negative self-loop added. The design theorems' controls: a one-way triangle's circulation is not
always `±1` (a directed 3-cycle has `±3`), within 134; a DAG's order, unlike its covering
relation, has triangles, within 53; arcs across two levels break the clock, within 32; and
circulation is not reversal-invariant, within 18.

The dynamics are attacked on exact shadows (seeds 330 to 344): nonnegative matrices on `Fin 5`
whose rows sum to less than `1`, their walk sums by Gauss–Jordan elimination against the Neumann
partial sums of up to three terms, every tail in `[0, s^n / (1 − s)]` on 500 instances; HodgeRank
on the ten edges of `K₅` with weights in `{0, ¼, ½, ¾, 1}` and the pseudo-inverse by the Spectral
shadow, the residual divergence-free and its energy under every other potential's on 500; the
quotient identity `Pᵀ L P = L_π` and its energy form for any `5 × 5` integer matrix and any
partition into three blocks, 500 each; the ripple carried across a random product of
transpositions, 500; the velocity's telescoping, 500; and RSP-5 on a block at `β = 1`, 500. The
heat kernel and the modes are exponentials and eigenvectors, which do not run, so DYN-4 and
DYN-6 are proved and not attacked. The controls: the tail bound without its `1 / (1 − s)` factor
is refuted within 14 instances (`M = ½` alone leaves `2 · ½^n`); with entries of either sign the
partial sums overshoot, within 6; a stochastic matrix, an eigenvalue `1`, makes `1 − M` singular on
the first instance; the potential of the unweighted divergence leaves a residual with divergence,
within 14; the quotient lifted back to the fine graph is not a Laplacian, within 10; across a
merge the ripple is not path-independent, within 7; the sum of the steps' sizes is not the
displacement's, within 26 (a revert); and a block with its own degrees invents nearness, within
31.

Scale is attacked on exact shadows (seeds 350 to 367). The spectral gap is an eigenvalue, which
does not run, so SCL-1 is attacked where the spectrum is rational: complete bipartite graphs on
`Fin 4` with a uniform weight `w`, whose Laplacian has the eigenvalues `0`, `w·a`, `w·b` and
`w·(a + b)`, so the gap is `w·min(a, b)` exactly and the lazy step `1 / (4w)` keeps every
multiplier in `[0, 1]`; the lazy walk's time average of a centered field over windows of up to
seven steps is matrix arithmetic over ℚ. The window bound and the geometric-sum form survived 495
and 493 instances (the rest discarded as one-sided bipartitions). SCL-2's discrete twin is attacked
on diagonal operators on `Fin 4`, whose modes are the coordinates, with the kept set chosen by
bits independently of the eigenvalues, so the cut need not fall in a gap: 500. SCL-3 on games over
three sources with values from a list, the six orderings enumerated through Mathlib's `Fintype`
instance on `Fin 3 ≃ Fin 3`: efficiency, additivity, the null source, symmetry, the Harsanyi
decomposition at every configuration, the dividend formula and leave-one-out on an additive score,
500 each. The controls: the largest eigenvalue in place of the gap is refuted within 5 instances;
a field with a mean, whose mean the walk conserves, breaks the window bound within 25; the share
of the dropped modes "always falls" is refuted within 19 where the eigenvalues straddling the cut
coincide (`ds := [2, 0]`, the kept coordinate at `2` and a dropped one at `0`: the share rises);
the fastest dropped mode's rate in place of the slowest's within 24; the equal split, efficient and
symmetric, pays a null source, within 11; leave-one-out is not efficient, within 10 (`vs := [1]`,
a score of `1` on the empty configuration alone); the uniform average over configurations, the
Banzhaf weights, is not efficient, within 8; and the dividends without their `1 / |T|` within 6.

## Build

The toolchain is pinned in `lean-toolchain` (elan resolves it); Mathlib is pinned in
`lake-manifest.json`. On a fresh checkout, fetch the Mathlib cache first (several GB), then run the
gate:

```sh
lake exe cache get
./check.sh
```

The package follows Mathlib's own arrangement (`lakefile.toml`): `lake test` builds `PalaceTest`,
`lake lint` runs Batteries' `runLinter` over `Palace`, and `fixedToolchain` records that a pinned
Mathlib supports only the toolchain it is built with.

Every file is a module of Lean's module system, which Mathlib asks of the files that import it
(Lake warns otherwise). The library runs nothing while it builds, and `check.sh` refuses, before
it builds anything, a source that would (`scripts/check_formal_sources.py`: no command run at
elaboration, no macro or elaborator of its own, no `unsafe`, no `IO`, no option but the
elaboration budgets), so it imports plainly; each
attack module imports its dependencies twice, as `public import` and again as `public meta import`,
because its attacks run code while it builds. Definitions are exposed throughout
(`@[expose] public section`): the laws are about them and their proofs unfold them, often from
another module, and without it 68 proofs in seven files fail. One instance is written here:
`decide` must unfold `DecidableEq (Except ε α)`, and Batteries does not expose its instance's body
to importers (`Palace/Scope.lean`).

The kernel re-check. `Export.lean` writes every `Palace` declaration and everything it uses, from
`Init` up (46,006 declarations on the run this commit was built with), and `check.sh` replays that export from nothing through Lean's
kernel and the five independent checkers bundled with Lean: `leanchecker-paranoid`, `lean4lean` (a
kernel written in Lean), `nanoda` (one written in Rust), and `con-leche`, whose acceptance carries a
machine-checked theorem that the environment holds no proof of `False`, with `con-ron`, its port.
All six accept, in about two minutes on the owner's Mac. `leanchecker Palace`, which replays each
module on top of its imports, crashes in Lean's import loader on this layout (4.36.0-rc2); the
export route replays strictly more. The compiler's `_unsafe_rec` helpers stay out of the export:
nothing safe can mention them, and nanoda refuses them.

`lake comparator` builds and exports both sides in a `bwrap` sandbox, so it runs where `bwrap`
does, which is Linux: CI runs it with `--paranoid`, and the same five checkers replay what the
248 statements reach. Elsewhere `check.sh` runs `Compare.lean`, the comparator's
comparison step over the two environments the build left; planted, a weakened statement in the
library and a changed one in `Spec/` each fail it.

CI runs the same gate in the advisory `lean` workflow (`.github/workflows/lean.yml`): on every PR
and push to `main` whose diff touches `formal/`, the ledger, the cross-reference script or the
workflow itself, and every Monday against drift in the toolchain or the Mathlib cache. Nothing
requires it yet; that is the owner's call after four green weeks (the note's §2.4).
