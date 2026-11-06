---
type: design-note
id: dn-graph-dynamics
track: dynamics
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: design-only    # nothing built; the first theorems are machine-checked in formal/Palace/Dynamics.lean
created: 2026-11-06
updated: 2026-11-07
links:
  - papers/2026-11-07-graph-dynamics/paper.tex          # the article: the same theorems, with proof sketches and the references
  - docs/design-notes/edge-dynamics.md                  # RATIFIED: the 1-form lift, the inversion, the R-ladder; Lane B parked on sample depth
  - docs/design-notes/temporal-retrieval-algebra.md     # RATIFIED: the walk sum (A1), the transports (§2.2), the superconnection (§2.3)
  - docs/design-notes/temporal-geometry-and-drives.md   # RATIFIED: the clock, the churn field J and its potential L⁺J, TG-e (no continuum limit)
  - docs/design-notes/magnetic-laplacian.md             # RATIFIED: direction as a phase; proved, not built
  - docs/design-notes/dn-query-sentence-algebra.md      # the language this asks sorts and verbs of; §2.9 what is not in the universe
  - docs/brainstorms/limits-of-the-algebra.md           # L3 (the transports), L5 (the leak), L7 (the snapshot)
  - docs/design-notes/dn-mathematical-foundations.md    # the ladder; design theorems enter the ledger when code relies on them
  - formal/Palace/Dynamics.lean                         # the theorems (formal/Palace/Dynamics/Defs.lean the model; PalaceTest/Dynamics.lean the attacks)
supersedes: null
superseded_by: null
warrant: null
---

# The dynamics of an evolving graph: velocity, flows, ripples, and the macro regime

> Composed on the dynamics session (Fable 5.1, 2026-11-06 and 2026-11-07), on the standing
> direction that the design and its proofs come first and the build follows a licence given at
> the merge. Agent-drafted, filed `draft` on a branch; the merge is ratification. Nothing is
> built: `core/` is untouched. Every nontrivial claim carries a grade: `[THEOREM]` is
> machine-checked in `formal/Palace/Dynamics.lean` and names its declaration; `[ESTABLISHED]` is
> Mathlib's or a ratified note's; `[DERIVED]` is argued here from those; `[INFERENCE]` is a
> design call with a named falsifier; `[HYPOTHESIS]` is a claim the palace cannot check today,
> with what would check it named. Code claims were read at `f65f73f`; the live instance was
> measured read-only on 2026-11-07. The article `papers/2026-11-07-graph-dynamics/paper.tex`
> states the same theorems with proof sketches and the references.

## 1. Purpose and scope

### 1.1 The questions

A knowledge graph that is kept over time is not one graph but a sequence of them: notes are
written and rewritten, citations are added and severed, weights drift. Six questions arise about
such a graph, and this note takes them in order.

1. When a value changes behind a fixed identity, what are the objects? An identity is a box; the
   value it holds is a pointer's target, re-recorded at each cut; the embedding of the value moves
   when the value does while the identity stays. What is the box's direction and magnitude, and
   in which space?
2. Do path sums matter here, and what do they cost? A state reached by walks on the graph seems
   to ask for a sum over every walk, which sounds too expensive.
3. Is there a vector field among the nodes and another among the edges, when values and weights
   change over time, and what do such fields say? This is the direction edge-dynamics Lane B
   set out in and parked.
4. How is a flow on the edges to be read? Through its decomposition into a gradient, a curl and
   a harmonic part: what each part means, and what each part's size measures.
5. Can macro behaviour be built from micro fluctuations, as fluid dynamics and statistical
   physics build a macro regime that is smooth though the micro motions are not? Which parts of
   that analogy are theorems on a finite graph, and which are hypotheses?
6. Can the query language express any of this, and what would it need?

This note answers each from what is proved (§2 to §7), and §8 gives each answer in one
paragraph, plainly. The theorems are design theorems in the sense of `formal/README.md`: proved
and replayed by the kernel checkers, cited from here, entering the ledger as rows when code relies
on them.

Six decisions:

1. **The objects (§2).** An identity with a version chain is the box; its versions are the
   pointer's targets; a value's velocity over a window of cuts is a 0-cochain per pair of cuts;
   the vector field among the edges is a 1-cochain, and it is a different thing from a change of
   weights, which is a scalar per unordered edge.
2. **The sum over walks is a resolvent (§3).** It is never enumerated: one sparse solve, or `n`
   terms with a tail of `s^n / (1 − s)`; the ripple of a shock along a relation is the resolvent
   applied to the shock; across a transport it is path-independent exactly when the transport
   intertwines the relations.
3. **A flow is read through the Hodge decomposition (§4).** Its potential is the least-squares
   ranking of the nodes; its residual's energy is the inconsistency; the projections are exact on
   the whole complex and do not commute with a mask.
4. **The macro regime is the span of the low modes (§5).** The kept modes evolve exactly by their
   eigenvalues, the dropped part decays at the gap's rate, coarse-graining by a partition is exact
   on block fields and never lowers the gap, and a block read on its own under-estimates nearness.
   The statistical-physics analogy holds where it is a theorem and is named a hypothesis where it
   is not.
5. **The language (§6).** A Flow sort and the verbs `gradient`, `curl`, `harmonic`, `potential`,
   `ripple`, the adjectives `at scale` and `coarse by`, and `velocity of`, each with the laws it
   needs before code, in the order to build them.
6. **What can be known (§7).** The propagation of a known shock is exact; the shocks are not
   predicted by anything here; the regime question 5 names is a theorem on a fixed graph and a
   hypothesis about the graph's own evolution.

### 1.2 Out of scope

Any `core/` change (code is licensed at the merge); the observed-side series a velocity would be
measured on (edge-dynamics Lane B stays parked on its sample depth, §2.5 of that note); the
magnetic operator's build (ML-a); the diachronic reader; any back-action on the graph (everything
here measures and reads); a continuum limit (temporal-geometry TG-e stands: the record is
discrete, and §5.4 says why it stays so).

### 1.3 What is proved, what is cited, what is open

Proved on this branch, in `formal/Palace/Dynamics.lean` over `formal/Palace/Dynamics/Defs.lean`,
attacked in `formal/PalaceTest/Dynamics.lean` (seeds 330 to 344, each attack with a negative
control): six families, DYN-1 to DYN-6, named in the sections below and listed in the README's
Dynamics paragraph. The heat kernel and the modes are exponentials and eigenvectors, which do not
run, so DYN-4 and DYN-6 are proved and not attacked; everything else is attacked on an exact
shadow over ℚ.

Cited: the Hodge decomposition (LAP-7 to LAP-11, `Palace/Hodge.lean`); the heat kernel's
semigroup and metric (CND-4, `Palace/Heat.lean`); the walk sum's well-posedness and the support's
one-sided error (RSP-1 to RSP-5, `Palace/Retrieval.lean`); the transports and the
superconnection's curvature (TRN-1 to TRN-9, `Palace/Transport.lean`); Courant–Fischer's floor
(`Palace/Frustration.lean`); the leak (LEAK-1, LEAK-2); the sever horizon (SEV-1 to SEV-5); the
pseudo-inverse (`Palace/Spectral.lean`); the response to a hypothetical edge (QSA-9); Mathlib's
geometric series in a complete normed ring and its spectral theorem for Hermitian matrices.

Open, stated where it bites: the sharp convergence condition of the walk sum, a spectral radius
below one, is proved in its operator-norm form and cited in its spectral form (§3.1); the
non-commutation of the Hodge projections with a mask is derived with a witness and not
machine-checked (§4.3); the mixing of the graph's own evolution is a hypothesis with no series to
check it on (§5.4); the magnitude of a velocity has no data: the live versions store holds one
generation (§2.1).

## 2. The objects

### 2.1 The box and the pointer: an identity and its versions

`core/stores/versions.py` is the box and the pointer, built. An identity is a `doc_id`;
its versions are the rows `(doc_id, version_seq, digest, at)`, appended and never rewritten;
the current version is the largest `version_seq`; a revert is a new version with an old digest,
so the chain stays linear; two lineages are never merged (`RekeyRefusedError`), which is the
hypothesis under which the pullback along a supersession is a contraction (TRN-2,
`pull_contraction_iff`, the limits program's L3). The box is the identity; the pointer is the
current digest; what the pointer points at is a version's content, and the version's embedding is
a function of that content alone (the vector plane is keyed by `content_id × (model, dim)`,
MEM-8). So the picture of question 1 is exact: when a value is re-recorded, the identity is
unchanged, the digest changes, and the vector moves with the digest, never on its own.
`[ESTABLISHED]`

The value of an identity at a cut is the version alive at the cut. A cut is the event clock's
down-set (CLK-2), and on a chain a cut is a prefix, so at most one version of each identity is
alive at a cut and the snapshot is a transversal of the chains (limits L7, `[DERIVED]` there).
The model this note's theorems are stated over is that transversal read as a function: a value
per identity per cut, `x : ℕ → V → E`, with `E` the value's space, the reals for a number and
`ℝ^d` for an embedding (`Dynamics/Defs.lean`, `velocity`).

Measured read-only on the live instance, 2026-11-07: 29 identities, 29 versions, every
`version_seq` equal to `1`, all recorded within one second on 2026-10-28, the last rebuild. There
is one generation, so there is no displacement yet to measure; the first supersession the sync
records is the first datum. Everything in this note about velocity is therefore a definition with
its laws, waiting on data, which §7 says plainly.

### 2.2 The two vector fields

**Among the nodes.** The velocity of a value over a window of cuts `c₀ ≤ c₁` is the displacement
`v(i) = x_{c₁}(i) − x_{c₀}(i)`, one value per identity: a 0-cochain with values in `E`, per pair
of cuts (`velocity`). Its magnitude is `‖v(i)‖` and its direction is `v(i)` normalized, both in
the value's space, not on the graph: a graph has no tangent space at a vertex, so a box's direction
and magnitude are movement in `E` (an embedding space, a number line), read per identity. Its
laws:

- DYN-1 velocity adds along the chain of cuts, `v_{ab} + v_{bc} = v_{ac}`, and the displacement
  over a window is the sum of its steps, version to version (`velocity_add`, `velocity_eq_sum`).
  `[THEOREM]`
- The size of the displacement is at most the sum of the steps' sizes, and less whenever a step
  reverts another (the control at seed 342 is that revert). `[THEOREM, as the attack's control]`

**Among the edges.** Two different things live on the edges, and question 3 names both. A
*flow* is a 1-cochain: a number per oriented edge, antisymmetric under reversal; it is what the
Hodge decomposition reads (§4), and it is the discrete vector field: on a graph the edge space
plays the role the tangent bundle plays on a manifold. A *change of weights* is a number per
unordered edge, `Δw_e = w_e(c₁) − w_e(c₀)`, symmetric, with no orientation; it is not a flow, and
it is what weights changing over time produce. The two have different readings.
A change of weights changes the operators: the Laplacian moves by the rank-one terms of QSA-9
(one per changed edge), every effective resistance falls or holds where weight is added and rises
or holds where it is removed (CND-2 both ways), and the response of the pseudo-inverse is
Sherman–Morrison with the sever horizon SEV-3 to SEV-5 where an edge is removed; the response of
the heat kernel and of the modes to a weight change is a perturbation of the spectrum
(Courant–Fischer; the gap moves by at most the operator norm of the change, `[ESTABLISHED]`, not
stated here). A flow is read by its potential, its curl and its harmonic part (§4). `[DERIVED]`

A changing potential induces a flow. If a field `s` on the nodes changes, the drop across an edge
changes by the difference of the ends' velocities: `d(v) = d(x_{c₁}) − d(x_{c₀})`
(`coboundary_velocity`), and that edge field is a gradient, so it is orthogonal to every curl and
every harmonic flow (`grad_velocity_dot_curl`, with LAP-9): a changing potential never makes
circulation. `[THEOREM]` So the edge field induced by node velocities is the least interesting
of the three parts; circulation, if any, comes from somewhere else (§4.2).

### 2.3 What the palace already has

| object | sort (dn-query-sentence-algebra §2.2) | where | proved |
|---|---|---|---|
| a field on the nodes, `V → [0, 1]` | Field | `Hit.score`; `near`, `diffuse` | QSA-3 |
| a kernel, PSD `V × V` | Kernel | `K_sem`, `K_struct`, `e^{−tL}`, `L⁺`, `G_β` | QSA-1, QSA-2, CND-1, CND-4, RSP-2 |
| a relation, one move class | Relation | `X_cite`, the version chains, the σ-backbone | QSA-7 |
| a chain of moves | Chain | the product walk | QSA-7 |
| the Hodge 1-Laplacian and its projectors, unit weights | (no sort) | `core/kernel/complex/hodge.py` | LAP-7 to LAP-11 |
| the heat kernel and the diffusion distance | Kernel, Metric | `core/graph/conductance.py` | CND-4 |
| the walk sum and the free energy | Field, Metric | `core/query.py::free_energy_distances`, `diffuse` | RSP-1 to RSP-5, LEAK-1, LEAK-2 |
| the transports `σ_*`, `σ^*`, `π_active` | Transport | Lean only; `trace` walks a chain | TRN-1 to TRN-9 |
| the magnetic Laplacian | (no sort) | Lean only, build deferred (ML-a) | BRG-7 and the note's results |
| an identity's version chain | (no sort; `trace`) | `core/stores/versions.py` | ING-7 (the chain as the serial order) |
| the velocity of a value | none | nowhere; no data | DYN-1 |
| a flow and its potential | none | nowhere | DYN-3 |

So the palace has the machinery of diffusion at rest and the chains that would carry a velocity,
and lacks the two objects of questions 1 and 3, a velocity and a flow, as sorts. §6 is what it
would take.

## 3. Path integrals: the sum over walks is a resolvent

### 3.1 The theorem

A path sum, as question 2 poses it, is a sum over walks: a state is reached by moves on the
graph, and every walk from `i` to `j` counts, each weighted by the product of its steps' weights
and damped by `z` per step, summed over all lengths. On a finite graph that sum is a geometric
series of matrices, and a geometric series is never added up term by term:

- DYN-2 in any complete normed ring, when `‖x‖ < 1` the powers of `x` are summable and their sum
  inverts `1 − x` on both sides (`neumann_tsum`, Mathlib's `geom_series_mul_neg` and
  `mul_neg_geom_series`). For a real matrix under the row-sum operator norm,
  `(1 − M)⁻¹ = Σ_k M^k` when `‖M‖ < 1`, the powers summable entrywise (`inv_one_sub_eq_tsum`);
  a nonnegative matrix whose rows sum to at most `s < 1` has that norm at most `s`
  (`linfty_opNorm_le_of_rows`), so its walk sum is its inverse (`inv_one_sub_eq_tsum_of_rows`).
  `[THEOREM]`
- The fundamental matrix of the killed walk, what `diffuse` computes, is the sum over all killed
  walks (`fundamental_eq_tsum`, under RSP-1's hypotheses). `[THEOREM]`
- The tail: after `n` terms the walk sum is approached from below and what is left is at most
  `s^n / (1 − s)` entrywise (`neumann_tail`, through `sum_pow_le`, the rows of `M^n` sum to at
  most `s^n`, and `sum_inv_le`, the rows of `(1 − M)⁻¹` sum to at most `1 / (1 − s)`, both by the
  extremal principle of RSP-1: at the row where a sum is largest). `[THEOREM]`
- The control: when an eigenvalue is `1`, with every row summing to exactly `1` (the unkilled
  walk), `1 − M` is singular and the partial sums converge to nothing, each row of the `n`-th
  summing to `n` (`det_one_sub_eq_zero_of_rows_eq_one`, `neumann_not_tendsto`). `[THEOREM]`

The sharp condition is a spectral radius of `zA` below one: it is equivalent to the existence of
some operator norm with `‖zA‖ < 1`, and Gelfand's formula gives the radius as the limit of
`‖(zA)^n‖^{1/n}` `[ESTABLISHED]`. Mathlib at the pin proves Gelfand's formula over ℂ
(`spectrum.pow_nnnorm_pow_one_div_tendsto_nhds_spectralRadius`); the real-matrix statement is
cited here, not machine-checked. The row-sum form is the one the palace needs: the killed walk's
rows sum to at most `z` (RSP-1), and a directed relation row-normalized by its out-degree has the
same property, so every relation the language walks is covered by the proved form. `[DERIVED]`

### 3.2 The cost

The sum over paths is one sparse linear solve: `(1 − zA) Z = 1`, a factorization of a sparse
matrix of the graph's size, polynomial in the number of nodes and near-linear on sparse graphs in
practice; never an enumeration of walks, whose number grows exponentially in the length. When an
iterative answer is wanted, `n` terms give accuracy `s^n / (1 − s)`, so `n ≈ log(ε(1 − s)) / log s`
terms for accuracy `ε`, each a sparse matrix-vector product (`neumann_tail`). The answer is the
same either way; the trace's accuracy line, when `ripple` is built, is the tail bound
(§6). `[THEOREM for the bound; DERIVED for the cost]`

### 3.3 The ripple

A shock is a field `δ` on the nodes: a unit at the anchor, or the displacement of a set of
identities. Its ripple along a relation `A` with damping `z` is the resolvent applied to it,
`(1 − zA)⁻¹ δ = Σ_k z^k A^k δ` (`ripple`, `ripple_eq_tsum`): the shock after every number of
steps along the relation, each step damped by `z`, summed. The relation may be directed; nothing
in DYN-2 asks for symmetry, so a ripple along the citation graph runs with the arrows (or against
them, on the transpose), where `diffuse` is the symmetric case: the killed walk on the backbone
with the free energy's normalization. The ripple is nonnegative for a nonnegative shock, monotone
in the shock, and bounded: `‖ripple‖_∞ ≤ ‖δ‖_∞ / (1 − s)` by `sum_inv_le`. `[THEOREM; the bound
DERIVED from it]`

### 3.4 The space-time walk, and when the ripple is path-independent

On a graph evolving in time there are two orders: propagate the shock on the graph at cut `c`
and carry the result forward along the supersession `σ` to cut `c'`, or carry the shock forward
and propagate it on the graph at `c'`. They agree exactly when the transport intertwines the
relations:

- `P M = M' P` for the push-forward's matrix `P` gives `P (1 − M)⁻¹ = (1 − M')⁻¹ P`
  (`resolvent_intertwine`). `[THEOREM]`
- A merge-free transport that carries every weight forward, `M'(σ a, σ a') = M(a, a')`, with no
  new note feeding the carried ones, intertwines them (`transpose_indicator_mul`), so the ripple
  carried forward is the ripple of the carried shock (`push_ripple`). `[THEOREM]`
- Across a merge, with the weights pushed forward, it is not path-independent (the control at
  seed 340). `[THEOREM, as the control]`

The hypothesis is the chain-map condition of the superconnection, F1, read on the weights: every
citation carries forward or collapses (TRN-5, `curvature_eq_zero_iff`, flatness) and carries its
weight, and nothing new points back into the carried notes. Flatness alone is necessary and not
sufficient: a citation carried forward with a changed weight breaks `P M = M' P` on that entry
while the curvature `[d, τ]` is zero there. So the honest statement is: the ripple is
path-independent across a transport that is flat and weight-preserving, and the failure, where
there is one, is read off `P M − M' P`, whose support is the severed citations (where `[d, τ]`
lives) and the changed weights. `[DERIVED]`

### 3.5 What a path integral is not, here

Feynman's path integral sums complex amplitudes over continuous paths, and its measure is the
difficulty. The palace's sum is over walks on a finite graph with positive weights, the random-walk
(Euclidean) form, and it is finite-dimensional linear algebra. Its continuous-time form is the heat
kernel, `e^{−tL}`, the sum over walks of every length with weights `t^k / k!`
`[ESTABLISHED, the exponential series; not stated in this family]`, and its discrete-time form is
the lazy walk `(1 − εL)^n` (§5.3). The free energy `−(1/β) log(z_ij / z_jj)` is a free energy in
the statistical-physics sense: `z_ij` is a partition function over walks at inverse temperature
`β` (temporal-retrieval A1), and RSP-4's triangle inequality is the subadditivity of a free energy
through the path product. `[ESTABLISHED]` So path integrals matter exactly as far as that: the
machinery is real and already built in `diffuse`; the cost a sum over every walk seems to demand
is not paid, because the sum is a solve.

## 4. The Hodge decomposition as the reading of a flow

### 4.1 HodgeRank: the potential is the least-squares ranking

Let `Y` be a flow on the edges with weights `w ≥ 0`, `∂₁` the incidence matrix, `L_w = ∂₁ W ∂₁ᵀ`
the weighted Laplacian (the Laplacian `L` of the weighted graph; BRG-1 at unit weights), and
`div_w Y = ∂₁ (w ∘ Y)` the weighted divergence. The potential is `s = L_w⁺ div_w Y` (`potential`;
`L⁺` is the Spectral family's pseudo-inverse):

- DYN-3 the residual `Y − ∂₁ᵀ s` is divergence-free (`divergence_residual`): the normal equations
  `L_w s = div_w Y` hold because the divergence lies in the range of `L_w`, which `L_w L_w⁺`
  fixes (Rayleigh's `mulVec_pinv_mulVec_of_orthogonal`). `[THEOREM]`
- `s` is a least-squares potential: `‖Y − ∂₁ᵀ s‖²_w ≤ ‖Y − ∂₁ᵀ x‖²_w` for every `x`
  (`wdotE_residual_le`, by Pythagoras, `wdotE_sub_grad`, the residual being `w`-orthogonal to
  every gradient, `wdotE_residual_grad`). `[THEOREM]`
- It is unique up to the kernel of `L_w` (`wdotE_residual_eq_iff`), which on a connected graph
  with positive weights is the constants (`eq_of_weightedLap_mulVec_eq_zero`, on the flag complex's
  `d1`): only the differences of `s` mean anything, and they rank the nodes. `[THEOREM]`

The reading: `s(j) − s(i)` is the part of the flow across `i → j` that a global ordering
explains; the order of `s` says who leads. The residual's weighted energy `‖r‖²_w` is the
inconsistency: how much of the flow no ranking can explain, which is zero exactly when the flow is
a gradient (a transitive, cycle-free lead-lag). This is HodgeRank `[ESTABLISHED, Jiang, Lim, Yao,
Ye 2011]`, stated here over the palace's `L⁺` and attacked on `K₅` (seed 334; the control, the
potential of the unweighted divergence, seed 335).

### 4.2 The three parts

LAP-9 splits every flow uniquely into a gradient, a curl and a harmonic part, mutually
orthogonal. The gradient is `∂₁ᵀ s`, the potential's flow (§4.1). The curl, `im ∂₂`, is local
circulation around the filled triangles. The harmonic part, `ker L₁`, is global circulation: a
flow that is a cycle and a cocycle, orbiting the holes of the complex, as many dimensions as the
first Betti number (LAP-10, `finrank_harm`). In words: the gradient is what a ranking explains,
the curl is disagreement that closes locally (A leads B leads C leads A inside one triangle), the
harmonic part is disagreement that closes only around a hole, the circulating structure the
THREAD lens of edge-dynamics §2.3 narrates. A whole that is more than the sum of its parts, in
this reading, is the harmonic part: it is exactly the circulation that no node potential and no
local triangle accounts for, and its dimension is a topological invariant of the complex, not of
any node. `[DERIVED, from LAP-9 and LAP-10]`

The projections are linear, idempotent and mutually orthogonal, and they sum to the identity on
flows: linearity and idempotence follow from the uniqueness of the split (LAP-9, `hodge_unique`),
orthogonality is `grad_dot_curl`, `grad_dot_harm`, `curl_dot_harm`. `[DERIVED from LAP-9]` The
residual of §4.1 is the curl and the harmonic part together: `Y − ∂₁ᵀ s` is divergence-free, and
a divergence-free flow is a curl plus a harmonic flow (LAP-8's `lap1_mulVec_eq_zero_iff` with
the split). `[DERIVED]`

### 4.3 Masks: what commutes and what does not

QSA-2 says `within R` is a congruence on kernels, keeps the cone, distributes over `and` and `or`.
The Hodge projectors are kernels on the edge space (`P_grad = ∂₁ᵀ L⁺ ∂₁` is PSD), so masking a
projector as a kernel keeps the cone. But masking is not the projection of the masked complex:
the gradient part of a flow restricted to `R` is not the restriction of the gradient part. The
witness: a filled triangle with the unit circulation around it is pure curl, its gradient part
zero; restricted to two of its vertices it is one edge with flow one, a pure gradient. So
`gradient (Y within R) ≠ (gradient Y) within R`, and the same for `curl` and `harmonic`: a mask
changes the complex (its edges, triangles and holes), and the decomposition belongs to the
complex. The potential has the same property: `potential (Y within R)` is the least-squares
potential of a different problem. What does commute: a scalar, a sum of flows (linearity), and the
reading of a flow at a cut (`as of c` indexes the complex, then the decomposition is taken).
`[DERIVED, with the witness; not machine-checked, GDF-2 names the attack]`

## 5. Macro from micro

### 5.1 The modes

For a real symmetric `M` with eigenvalues `λ_j` and orthonormal eigenvectors `φ_j`, a function of
`M` acts on each eigenvector by the function of its eigenvalue, `f(M) φ_j = f(λ_j) φ_j`
(`cfc_mulVec_mode`, through Mathlib's spectral theorem), so its quadratic form is
`xᵀ f(M) x = Σ_j f(λ_j) ⟨x, φ_j⟩²` (`dotProduct_cfc_mulVec`) and the energy is
`xᵀ M x = Σ_j λ_j ⟨x, φ_j⟩²` (`dotProduct_mulVec_eq_sum_modes`). `[THEOREM]` The heat equation's
solution is then `f(t) = e^{−tL} f₀ = Σ_j e^{−λ_j t} ⟨f₀, φ_j⟩ φ_j`, and:

- DYN-4 the heat kernel commutes with the projection onto any set `S` of modes, and on them acts
  by their own eigenvalues: `H_t (P_S f) = Σ_{j ∈ S} e^{−λ_j t} ⟨f, φ_j⟩ φ_j = P_S (H_t f)`
  (`heat_modeProj`). The macro variables, the coefficients on the low modes, evolve exactly, each
  by its own rate, with no coupling to what was dropped. `[THEOREM]`
- The dropped part decays at least as fast as the gap below it: for `t ≥ 0` and `μ` at most every
  dropped eigenvalue, `‖H_t (f − P_S f)‖² ≤ e^{−2μt} ‖f − P_S f‖²` (`heat_sub_modeProj_le`; with
  `S` the first `k` modes, `μ = λ_{k+1}`). `[THEOREM]`
- Courant–Fischer on the modes a field lives on: when every mode `x` has weight on has eigenvalue
  at least `μ`, `μ ‖x‖² ≤ xᵀ M x` (`mul_dotProduct_self_le_of_modes`). Frustration's floor,
  some eigenvalue under every Rayleigh quotient, is the case `μ = λ_min`. `[THEOREM]`

### 5.2 Coarse-graining by a partition

A partition `π` of the nodes into blocks (the levels of σ*, SIG-1 to SIG-4; spectral clusters;
any grouping) has an indicator `P`, and the quotient graph `A_π = Pᵀ A P` whose weight between two
blocks is the total weight between their members:

- DYN-5 the Laplacian of the quotient is the quotient of the Laplacian, `Pᵀ L P = L_π`, over any
  commutative ring (`lap_quot`), so the energy of a block-constant field is the quotient's energy
  of its block values (`dotProduct_lap_pull`): coarse-graining is exact on block fields.
  `[THEOREM]`
- On a connected support, a block field orthogonal to the constants has a quotient Rayleigh
  quotient at least the fine spectral gap, `μ Σ_b |b| h_b² ≤ hᵀ L_π h` for `μ` under every
  nonzero eigenvalue of `L` (`gap_le_dotProduct_lap_quot`, through `gap_le_dotProduct_lap`): a
  partition can lose slow modes, it cannot create one; coarse-graining never slows the mixing.
  `[THEOREM]`
- A block read on its own, with the graph's degrees, under-estimates nearness and never invents
  it: RSP-5 on the block (`nearnessOn_block_le`); with the block's own degrees the walk
  renormalizes onto the kept edges and nearness can rise (the control at seed 344), which is why
  a quotient keeps the fine degrees, as the sentence universe does (dn-query-sentence-algebra
  §2.9). The leak's reparametrization, LEAK-2, says what a census that misses weight costs:
  a step of killing, `z ↦ (1 + ε) z`, uniform in the depth. `[THEOREM]`

### 5.3 Mixing: the fluctuations average out at the gap's rate

The shapes of this subsection follow the switch-chain family of openai/math
(`lean/ComparatorChallenges/SwitchChain.lean`, Apache 2.0): a spectral gap as a Poincaré
inequality between a variance and a Dirichlet form, total variation against `L²` by `√N / 2`,
geometric `L²` decay step by step. They are restated over the Laplacian's modes for any weighted
graph; nothing is copied. Mathlib at the pin has no spectral gap, no Cheeger inequality, no heat
kernel and no Markov mixing, so these are the palace's.

- DYN-6 a spectral gap of at least `γ` is the Poincaré inequality `γ ‖f‖² ≤ fᵀ L f` for every
  `f` orthogonal to the constants (`HasSpectralGapAtLeast`), and in the variance form for every
  `f` (`HasSpectralGapAtLeast.variance`). On a connected support it holds for `γ` under every
  nonzero eigenvalue (`hasSpectralGapAtLeast_of_eigenvalues`), and conversely it bounds every
  nonzero eigenvalue (`le_eigenvalue_of_hasSpectralGapAtLeast`): the gap is exactly the least
  nonzero eigenvalue. `[THEOREM]`
- Total variation is at most `√N / 2` times the `L²` distance (`half_sum_abs_le`,
  Cauchy–Schwarz). `[THEOREM]`
- The heat kernel contracts every field orthogonal to the constants, `‖H_t x‖² ≤ e^{−2γt} ‖x‖²`
  (`heat_energy_le_of_gap`), so in total variation
  `½ Σ_i |(H_t x)_i| ≤ (√N / 2) e^{−γt} ‖x‖` (`half_sum_abs_heat_le`); and the lazy walk
  `1 − εL`, for `ε λ_j ≤ 1` on every eigenvalue, contracts it by `1 − εγ` a step,
  `‖(1 − εL)^n x‖² ≤ (1 − εγ)^{2n} ‖x‖²` (`lazy_pow_energy_le`, the instance of `pow_energy_le`,
  geometric decay on the modes a field lives on). `[THEOREM]`

Read on question 5: a field on the nodes is a micro state; its component along the
constants is the macro state (the mean, conserved by the diffusion, `L 1 = 0`); everything else is
the fluctuation, and under the diffusion it averages out at least as fast as `e^{−γt}`, with the
gap `γ` the one number of the graph that sets the rate. The macro regime is not disjoint from the
micro one: it is its projection, and the projection is exact (DYN-4).

### 5.4 Where the physics holds, and where it does not

Holds, as theorems:

- The free energy is a free energy. `z_ij` is a partition function over the killed walks from
  `i` to `j` at inverse temperature `β` (A1), `φ_ij = −(1/β) log(z_ij / z_jj)` its free energy,
  positive, zero on the diagonal, subadditive along paths (RSP-4), and `e^{−βφ}` a positive
  definite kernel on a connected support (RSP-3). The temperature is a dial of the language
  (`beta`). `[ESTABLISHED; THEOREM in the Retrieval family]`
- The spectral decomposition is the coarse-graining. The low modes are the macro variables, exact
  and uncoupled (DYN-4); a partition's quotient is exact on block fields and never lowers the gap
  (DYN-5); the fluctuations relax at the gap's rate (DYN-6). The analogy with the Fourier modes of
  a diffusing fluid is exact on a finite graph, because the heat equation on a graph is a
  diffusion. `[THEOREM]`
- Ensemble averaging is the walk sum. Modelling a large set at once rather than each member is,
  on the graph, the sum over all walks with their weights, computed as one solve (DYN-2), never
  one walk at a time. `[THEOREM]`

Does not hold, or is a hypothesis:

- There is no thermodynamic limit. The live backbone has 38 notes and 38 edges (measured
  2026-11-04, limits L1), the relation graph 20 edges on 12 notes, the versions store one
  generation. A spectrum of 38 eigenvalues is a list, not a density; the smooth behaviour of a
  continuum needs `N → ∞` with a limit object (a graphon, a manifold the graph samples), and the
  palace's record is finite and exact by design (the inversion, edge-dynamics §2.5;
  temporal-geometry TG-e). The theorems above hold at every `N`, including small ones; what is
  lost at small `N` is not their truth but the smoothness a continuum would give: a 38-node
  graph's macro variables are a handful of modes, each legible, none of them a continuum.
  `[DERIVED]`
- Mixing and ergodicity of the graph's own evolution are hypotheses. DYN-6 is about diffusion on
  a fixed graph. The evolution of the graph, which identities move, which edges change, which
  notes appear, is authorship, outside the graph, and nothing here gives it a stationary law. The
  statistical-physics reading of the evolution (a steady state, a temperature of the corpus, the
  fluctuation-dissipation relation `σ² = q / (1 − γ²)` of temporal-geometry §2.2) is a model to be
  fitted on series, INTERPRETED-class under the inversion, entering by the R-ladder of
  edge-dynamics §2.5 at sample depth, with the exact discrete invariants as its falsifiers. Today
  there are no series. `[HYPOTHESIS: checkable when the versions store holds a second generation
  and the edge-strength series exist; R1 then R3]`
- The micro changes have no theorem. Predicting the next edit is not a property of the graph
  (§7.2). `[DERIVED]`
- Emergence from simple rules, small structures stacking into something greater, as in a
  cellular automaton or an operating system. The palace's rules are the operators (the walk, the
  diffusion, the projections), and what emerges under them is computable: the macro modes, the
  circulation. That stacked structures become something qualitatively new is not a theorem in
  this frame and is not refuted by it either: the harmonic part (§4.2) is the one exact instance
  of a whole that no part accounts for. `[DERIVED]`

## 6. The language

### 6.1 What the algebra lacks

The sentence algebra has Field, Kernel, Metric, Relation, Chain, Transport and Witness. For the
objects of §2 to §5 it lacks:

| construct | sort or verb | what it computes | the laws it needs before code | unit |
|---|---|---|---|---|
| **Flow** | a sort: a 1-cochain on a relation's edges, with the edge weights as its inner product | a number per oriented edge, antisymmetric | a vector space, not a cone (`+`, `c·` of either sign); `within R` restricts to the edges inside `R`; the bridges Field → Flow by the coboundary and Flow → Field by `div_w` and `potential` (DYN-1, DYN-3) | GD-1 |
| `gradient`, `curl`, `harmonic` | Flow → Flow | the three projections | LAP-9 (orthogonal, unique, so linear and idempotent), LAP-10 (`harmonic` has β₁ dimensions, zero on a tree); the mask witness of §4.3 as a refused rewrite, the way QSA-4 refuses `top k` through a mask | GD-1 |
| `potential` | Flow → Potential | HodgeRank, `L_w⁺ div_w Y` | DYN-3; a Potential is a real field defined up to a constant on each component, so not the bounded Field: its own sort, with differences and `top k` of the differences as its bridges | GD-1 |
| `inconsistency` | Flow → a number | `‖residual‖²_w`, the energy of the curl and harmonic parts | DYN-3 (`wdotE_residual_le`: no potential does better) | GD-1 |
| `ripple ⟨rel⟩ from ⟨anchor⟩ [damping z]` | Relation × Atom → Field | the resolvent of the directed relation at the shock, `(1 − zA)⁻¹ e_a`, normalized by its diagonal as nearness is (RSP-1's first passage, `z_ij ≤ z_jj`) | DYN-2 (existence when the damped rows sum under 1; the tail bound as the trace's accuracy line; nonnegative; monotone in the relation, `inv_ratio_mono`); `diffuse` is its symmetric case; under `assume` the overlay's edges enter (QSA-6, QSA-9); path-independence across `as of` only under §3.4's condition | GD-2 |
| `at scale t` | an adjective on `diffuse` and `near` over a relation | the heat kernel's column at the anchor, `e^{−tL} e_a` | CND-4 (a metric, the semigroup, antitone in `t`), DYN-4 (the modes), DYN-6 (the decay); `t` is a dial beside `beta`, with a precedent | GD-3 |
| `coarse by ⟨partition⟩` | an adjective: evaluate on the quotient `A_π` with the fine degrees | a σ* level, a spectral clustering, or a named grouping as the partition | DYN-5 (exact on block fields; the gap never lowered; RSP-5 per block; the own-degrees control, so the quotient keeps the fine degrees); SIG-1 for σ* levels | GD-3 |
| `velocity of ⟨identity⟩ [from c₀ to c₁]` | Atom × Window → a value in `E`, with its magnitude | the displacement of the value, or of its embedding, between the versions alive at the cuts | DYN-1 (additive, telescoping, its coboundary a gradient); typed `Rate(κ)`, the window's clock declared (temporal-geometry §2.1); needs the `D` moves at the node grain and the snapshot `as of c` on the chains (limits L7, not built), and a second generation in the store | GD-4 |
| `velocity of ⟨flow⟩`, `velocity of ⟨potential⟩` | the same over a window, on flows | the change of a flow or a ranking between two cuts | DYN-1 with DYN-3: the change of the gradient part is the gradient of the change; the change of the residual's energy is the change of inconsistency | GD-4 |

Typing: a projection, a potential and a ripple at a cut are `Inv` (they depend only on the window's
event set); a velocity is `Rate(κ)` and carries its clock; a ripple under `assume` is `Hyp(Δ)`
and never `Inv` (QSA-5). The mode of a `ripple` clause is the relation's (Rule NOUN): structural
on `F`, semantic on the backbone. `[DERIVED from dn-capability-scope §2.3 and QSA-5]`

### 6.2 The order to build

GD-1 first (Flow and the projections: the Hodge projectors exist at unit weights in
`hodge.py`, so this is a sort, a weighted inner product, and the transcription of DYN-3); GD-2
second (`ripple`: the resolvent `diffuse` already solves, on a directed relation, with the tail
bound in the trace); GD-3 third (`at scale t` and `coarse by`: the heat kernel exists in
`conductance.py`, the quotient is a matrix product); GD-4 last (`velocity of`: it waits on the
`D` moves at the node grain, the snapshot, and data). Each unit transcribes its laws and
property-tests the transcription against the Lean statements, and the laws enter `docs/LAWS.md`
as rows with `Spec/` statements when the code relies on them (dn-mathematical-foundations §2.4).
`[INFERENCE, falsifier GDF-1]`

## 7. What can be known

### 7.1 State, direction, magnitude

The **state** of an evolving graph at a cut is the snapshot: the versions alive at the cut (one
per identity, L7) and the relations among them at the cut. It is exact and content-addressed; the
inversion makes it the reality every continuous reading approximates.

The **direction** has two exact meanings. Per identity, the velocity of its value over a window,
in the value's space (DYN-1); it needs two generations and today there is one. Per flow, the
potential: the global order the flow is closest to, with the residual's energy as how far the flow
is from any order (DYN-3). The magnetic phase is a third, for a directed relation at a cut:
direction as the flux through cycles, proved and not built (dn-magnetic-laplacian).

The **magnitude** is a norm in each case: `‖v(i)‖` of a velocity, `‖r‖²_w` of an inconsistency,
`‖ripple‖_∞ ≤ ‖δ‖_∞ / (1 − s)` of a shock's reach (§3.3), and the gap `γ` as the rate at which
a disturbance on the nodes fades under the diffusion (DYN-6).

### 7.2 What is predictable and what is not

Predictable, exactly, from the graph at a cut: the ripple of a known shock (DYN-2); the evolution
of a known field under the diffusion, mode by mode (DYN-4); the response to a hypothetical edge
(QSA-9, with the sever horizon SEV-3 to SEV-5); the coarse-grained energy and the gap's lower bound
under any partition (DYN-5); the rate at which a disturbance averages out (DYN-6). Each is a
theorem with its hypotheses, each computable as one solve or one spectral decomposition.

Not predictable from anything here: the shocks. Which identity's value moves next, which note is
written, which citation is added or severed, is an act of authorship outside the graph, and the
graph's dynamics as proved here propagate it and do not forecast it. A model that forecasts the
shocks is a different object, INTERPRETED-class, entering by the R-ladder on series the palace
does not have yet (§5.4). The division is exact: the machinery (the propagation) is exact, and
the next micro change, with its noise and its context, is the hard part and is not machinery.
`[DERIVED]`

### 7.3 The regime, as a theorem and as a hypothesis

As a theorem, on a fixed graph: the macro regime is the span of the low modes; it evolves exactly
by its own rates; what is dropped decays at the gap's rate; a coarse-graining by blocks is exact
on block fields and never invents slowness or nearness (DYN-4, DYN-5, DYN-6). As a hypothesis,
about the graph's own evolution: that the sequence of snapshots has a stationary regime, a
temperature, a fluctuation-dissipation balance, in which the micro changes average out into
smooth macro series. The palace cannot check it today (one generation; no edge-strength series);
when it can, the check is the R-ladder's, rung by rung, against the exact invariants, and a
regime that fails to reproduce them is wrong by definition (edge-dynamics §2.5, rule 2).

## 8. The answers, in the questions' order

**Do path integrals matter, and are they too expensive?** They matter exactly as the sum over
walks, which `diffuse` already computes, and they are not expensive: the sum over all walks of
every length is the resolvent `(1 − zA)⁻¹`, one sparse solve, never an enumeration; it converges
exactly when the damped walk's spectral radius is below one (proved in the row-sum form), and `n`
terms of the sum are off by at most `s^n / (1 − s)`. The control, a walk with an eigenvalue of
one, has no resolvent and no sum.

**Is the box moving with a direction and a magnitude?** Yes, in the value's space: the identity
is the box, each version the pointer's target, and the velocity over a window of cuts is the
displacement of the value or of its embedding, a 0-cochain per pair of cuts, additive along the
chain and the sum of its steps. Its magnitude is the displacement's norm. The live store holds one
generation, so there is nothing to measure yet; the first supersession is the first datum.

**Is there a vector field among the nodes and one among the edges, and do they tell anything?**
The field among the nodes is the velocity. The field among the edges is a flow, a 1-cochain, and
it is a different object from a change of weights, which is symmetric and changes the operators
instead. A flow tells three things through its Hodge decomposition: its potential is the ranking
the flow is closest to (who leads), its residual's energy is how inconsistent the flow is, and its
harmonic part is the circulation around the holes that no ranking and no local triangle explains.
A changing potential makes no circulation.

**Can macro understanding be built from micro fluctuations, as in fluids and statistical
physics?** On a fixed graph, yes, and exactly: the macro variables are the low modes of the
Laplacian, they evolve by their own eigenvalues with no coupling to the rest, the rest decays at
the gap's rate, and a coarse-graining by blocks is exact on block fields and never invents
slowness or nearness. The free energy is a real partition function and the spectral decomposition
is the coarse-graining. What does not carry over: a graph of a few dozen notes has no
thermodynamic limit, so its macro regime is a handful of legible modes, not a continuum; and the
mixing of the graph's own evolution is a hypothesis with no series to check it on.

**Is the language expressive enough?** Not yet. It has the fields, kernels, relations and chains,
and lacks a Flow sort, the projections `gradient`, `curl`, `harmonic`, a `potential`, a `ripple`
on a directed relation, the adjectives `at scale t` and `coarse by`, and `velocity of`. Each has
its laws stated and proved in this note's family, and the order to build them is GD-1 to GD-4;
`ripple` and `at scale` reuse what `diffuse` and the heat kernel already compute.

**When a graph evolves, how much can be known about its state, direction and meaning?** The
state at a cut is exact. The direction is exact where it is a velocity of a value or a potential
of a flow, and its magnitude is a norm. What is predictable is the propagation of a known change:
a ripple, a diffusion, a response to an assumed edge, each a theorem. What is not predictable from
the graph is the change itself: acts of authorship are the shocks, and no dynamics here forecasts
them. That there is more here than meets the eye is a theorem in one exact place, the harmonic
circulation a graph can carry that none of its nodes accounts for, and a hypothesis in the other,
the regime of the graph's evolution, which the palace will be able to test once it has history.

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| GD-a | the inner product on flows | the edge weights `w` (DYN-3's `wdotE`), the weighted form edge-dynamics PD-b parked at unit weights | a flow whose natural weights are not the backbone's |
| GD-b | the damping `z` of `ripple` | the killed walk's `z` (the γ-ceiling, RSP-1), one dial with `beta` | a retrieval eval set gives `z` a falsifier (temporal-retrieval TA-b) |
| GD-c | the sharp convergence condition, spectral radius below one | cited (Gelfand over ℂ in Mathlib); the row-sum form proved and used | a relation the language walks whose rows do not sum under one after normalization |
| GD-d | the partition `coarse by` accepts | σ* levels (SIG-1) and named groupings; spectral clusters when a clustering lens exists | a consumer asks for a partition the sorts cannot name |
| GD-e | the value space `E` of a velocity | the reals for a number, `ℝ^d` for an embedding; the embedder version fixed across the window (the A7 discriminator) | a velocity across an embedder change is asked for |
| GD-f | a continuum reading of the dynamics | none (temporal-geometry TG-e); the modes are the macro variables at every `N` | corpus density supports an honest limit object |
| GD-g | the mask law for the projections | refused as a rewrite, with §4.3's witness | a machine-checked witness on `Fin 3` (GDF-2) |

## Falsifiers

- **GDF-1 (a transcription lies):** a built `gradient`, `potential`, `ripple`, `at scale` or
  `coarse by` whose answer differs from the Lean statement's on a property test. Since every rule
  is a theorem, this is a transcription defect; the unit does not land until it agrees.
- **GDF-2 (the mask witness is wrong):** an attack on `Fin 3` that fails to refute
  `gradient (Y within R) = (gradient Y) within R` on the filled triangle. Then §4.3 is wrong and
  the projections commute with masks after all; the note's table changes.
- **GDF-3 (the tail bound is loose in a way that matters):** a relation the language walks whose
  rows sum to at most `s` and whose `n`-term ripple is farther than `s^n / (1 − s)` from the
  resolvent. The theorem says this cannot happen over the reals; a float64 instance that does is a
  rung L3 finding, not a refutation.
- **GDF-4 (the regime hypothesis, when it can be tested):** series of velocities and edge
  strengths that fail every stationarity test at the ladder's rungs. Then §5.4's hypothesis is
  refuted and the macro reading of the evolution retires to vocabulary, as temporal-geometry
  retired the wave reading.
- **GDF-5 (a block invents nearness with the fine degrees):** a block of a partition on which
  `nearnessOn` exceeds the graph's nearness while the degrees are the graph's. RSP-5 says it
  cannot; a float instance that does is an L3 finding.

## Open questions

- Which relation should `ripple` default to: the citation graph with the arrows (influence
  running from the cited to the citer), or against them? The theorems cover both; a precedent
  decides.
- Does the mode table need a word for `at scale t` on the backbone, where `diffuse` is semantic
  by Rule NOUN, or is the heat kernel on `S` the same clause with a dial?
- What is the right window for a velocity: two cuts named, or a count of versions back from a
  cut (the chain's own clock, `version_seq`)? Both are `Rate(κ)`; the precedent decides the
  default.
- The magnitude of a velocity is in the embedding's units; the A7 discriminator separates a
  content change from an embedder change. Should `velocity of` refuse a window across an embedder
  version, or report the two parts?

## Cross-references

**Formal (this branch):** `formal/Palace/Dynamics/Defs.lean` (`velocity`, `wdotE`,
`divergence`, `weightedLap`, `potential`, `residual`, `neumann`, `ripple`, `mode`, `modeProj`,
`indicator`, `quot`); `formal/Palace/Dynamics.lean` (DYN-1 `velocity_add`, `velocity_eq_sum`,
`coboundary_velocity`, `grad_velocity_dot_curl`; DYN-2 `neumann_tsum`, `inv_one_sub_eq_tsum`,
`linfty_opNorm_le_of_rows`, `inv_one_sub_eq_tsum_of_rows`, `fundamental_eq_tsum`,
`ripple_eq_tsum`, `sum_pow_le`, `sum_inv_le`, `inv_sub_neumann`, `neumann_tail`,
`det_one_sub_eq_zero_of_rows_eq_one`, `neumann_not_tendsto`; DYN-3 `dotProduct_weightedLap`,
`weightedLap_mulVec_eq_zero_iff`, `divergence_residual`, `wdotE_residual_grad`,
`wdotE_sub_grad`, `wdotE_residual_le`, `wdotE_residual_eq_iff`,
`eq_of_weightedLap_mulVec_eq_zero`; DYN-4 `cfc_mulVec_mode`, `dotProduct_cfc_mulVec`,
`dotProduct_mulVec_eq_sum_modes`, `mul_dotProduct_self_le_of_modes`, `heat_mulVec_mode`,
`heat_modeProj`, `sub_modeProj_dotProduct_mode`, `heat_energy_le`, `heat_sub_modeProj_le`;
DYN-5 `lap_quot`, `dotProduct_lap_pull`, `dotProduct_mode_eq_zero`, `gap_le_dotProduct_lap`,
`gap_le_dotProduct_lap_quot`, `resolvent_intertwine`, `transpose_indicator_mul`,
`push_ripple`, `nearnessOn_block_le`; DYN-6 `HasSpectralGapAtLeast`,
`hasSpectralGapAtLeast_of_eigenvalues`, `le_eigenvalue_of_hasSpectralGapAtLeast`,
`HasSpectralGapAtLeast.variance`, `half_sum_abs_le`, `heat_energy_le_of_gap`,
`half_sum_abs_heat_le`, `dotProduct_self_mulVec_of_modes`, `pow_energy_le`,
`one_sub_smul_mulVec_mode`, `lazy_pow_energy_le`); `formal/PalaceTest/Dynamics.lean` (seeds
330 to 344); the families cited: `Palace/Hodge.lean`, `Palace/Heat.lean`,
`Palace/Retrieval.lean`, `Palace/Transport.lean`, `Palace/Frustration.lean`, `Palace/Leak.lean`,
`Palace/Sever.lean`, `Palace/Spectral.lean`, `Palace/Rayleigh.lean`, `Palace/Sentence.lean`.

**Code (read at `f65f73f`):** `core/stores/versions.py` (`VersionStore`, `record`, `history`,
`supersessions`, `migrate_rekey_doc_id`, `RekeyRefusedError`); `core/kernel/complex/hodge.py`
(the flag complex, `∂₁`, `∂₂`, `L₁`, the projectors at unit weights); `core/graph/conductance.py`
(the heat kernel, `_diffusion_distances`, `np.linalg.pinv`); `core/query.py`
(`free_energy_distances`, the walk sum `diffuse` solves); `core/sentence/universe.py` (the
support, the fine degrees); `core/stores/memberships.py` (MEM-8, the vector keyed by content and
embedder).

**Design:** dn-edge-dynamics §2.2 (the lift), §2.5 (the inversion, the R-ladder), §2.6 (Lane B,
parked); dn-temporal-retrieval-algebra §2.1 (A1, the walk sum), §2.2 (the transports), §2.3
(Results 1 to 6), §2.5 (A7); dn-temporal-geometry §2.1 (the clock), §2.2 (the energy picture, a
hypothesis here), §2.3 (`Φ = L⁺J`), TG-e; dn-magnetic-laplacian (direction as a phase);
dn-query-sentence-algebra §2.2 (the sorts), §2.5 (QSA-1 to QSA-9), §2.9 (what is not in the
universe); docs/brainstorms/limits-of-the-algebra.md L3, L5, L7; dn-mathematical-foundations §2.4
(the ladder); `papers/2026-11-07-graph-dynamics/paper.tex` (the article, with the references).
