---
type: design-note
id: dn-utility-field
track: dynamics
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: design-only    # nothing built in the store; the laws are machine-checked in formal/Palace/Utility.lean and the simulator eval/utility_field.py runs on synthetic graphs
created: 2026-11-08
updated: 2026-11-08
links:
  - papers/2026-11-08-utility-field/paper.tex             # the article: the same theorems, with proof sketches and the references
  - docs/experiments/utility-field-2026-11-08.md          # the measurements on synthetic graphs
  - docs/design-notes/dn-graph-dynamics.md                # DYN-1 to DYN-6: the resolvent, the Hodge potential, the heat kernel, the gap
  - docs/design-notes/dn-scale-and-attribution.md         # SCL-1 the window and effective samples; SCL-3 attribution, a source that can be switched off
  - docs/design-notes/dn-prediction-ledger.md             # the ledger: resolved questions and the log-score advantage, the currency of value
  - docs/design-notes/dn-corpus-instance.md               # the instance the build is measured on first
  - docs/design-notes/dn-query-sentence-algebra.md        # the sorts and verbs the field nudges; §2.9 what is not in the universe
  - docs/design-notes/dn-mathematical-foundations.md      # the ladder; the ledger's rows
  - formal/Palace/Utility.lean                            # the theorems (formal/Palace/Utility/Defs.lean the model; PalaceTest/Utility.lean the attacks)
supersedes: null
superseded_by: null
warrant: null
---

# The utility field: computed, evolving weights above the structural backbone

> Composed on the utility session (Fable 5.1, 2026-11-08), on the standing direction that the
> design and its proofs come first and the build follows a licence given at the merge.
> Agent-drafted, filed `draft` on a branch; the merge is ratification. Nothing is built in the
> store: `core/` is untouched, and no store was read. Every nontrivial claim carries a grade:
> `[THEOREM]` is machine-checked in `formal/Palace/Utility.lean` and names its declaration;
> `[ESTABLISHED]` is Mathlib's, a ratified note's or a cited result's; `[DERIVED]` is argued here
> from those; `[MEASURED]` is a figure from `docs/experiments/utility-field-2026-11-08.md`, on
> synthetic graphs; `[INFERENCE]` is a design call with a named falsifier; `[HYPOTHESIS]` is a
> claim the palace cannot check today, with what would check it named. Code claims were read on
> `origin/main` at `950514b1`. The article `papers/2026-11-08-utility-field/paper.tex` states the
> same theorems with proof sketches and the references.

## 1. Purpose and scope

### 1.1 The requirement

The store's relations are structural: the explicit edges (citations, hyperlinks, version chains,
replies), the lexical similarities, the semantic backbone `S`. They say what is connected to
what. They do not say what is used, nor what its use produced. A store that is kept over time
should carry a second kind of value: a field over the graph that records how much each node,
edge and path is used and how much value its use produced; that evolves, so the relationships
evolve with utility; in which high-value paths become shortcuts, arcs, that form at heat spots
and fade when unused, so the field has temporal context; that nudges ranking in a favourable
direction, which is the system's learning and reinforcement cycle; that holds the histograms of
token and vector popularity; and whose mathematics keeps the structural backbone primary, so that
the graph can never collapse into a few hubs or a self-reinforcing loop. This note designs that
field, proves what keeps it from being steered into a nonsensical state, and says in what order
to build it.

### 1.2 Decisions

1. **The field is one value per site, a site being a node, an edge or a declared path, updated
   once a tick by one rule (§3.2):** decay toward a baseline `b` by a rate `lam`, then the
   saturated increment of the tick's use, clamped to `[−c, c]`. Three declared numbers, one
   derived box. `[THEOREM: UTL-1, UTL-2]`
2. **The field enters ranking as a multiplicative nudge of the structural weights within a
   margin (§3.3):** an effective weight is the structural weight times `1 + η (u − b)`, so it
   lies within `θ = η c / lam` of the structural one, never zero, never new. `[THEOREM: UTL-3,
   UTL-5]`
3. **Use is counted in realized value, not in bare popularity (§3.6):** a retrieval's use is
   credited when it led to a resolved question's log-score advantage (GRW-1's currency) or to a
   citation that was followed; a retrieval that produced nothing is credited a fraction; the
   popularity histograms are kept beside the field as base rates and never enter the nudge
   directly. `[INFERENCE, falsifier UFF-3]`
4. **An arc is a reading, not an edge (§3.4):** a declared path whose field stands a declared
   height above the baseline; it forms at a heat spot on a closed-form window and fades on the
   decay window; it materializes a path's walk sum for cheap reading and adds no edge to any
   graph. `[THEOREM: UTL-2; DERIVED]`
5. **The design sits in the benign regime of reinforcement, provably (§2.2, §6):** the
   increment is bounded and decayed (a normalized reinforcement), the nudge is bounded by the
   margin, and the loop in which the nudge changes what is used next is a contraction when its
   gain is below the rate; linear reinforcement without decay and superlinear reinforcement are
   the refuted controls. `[THEOREM: UTL-1, UTL-3, UTL-6; ESTABLISHED]`
6. **The field is derived and provenanced (§3.1, §4):** it is the fold of its update over the
   use log, carries the identity of each use, never alters authored content or labels, and is a
   source that an ablation arm can switch off, at which point the effective weights are the
   structural ones exactly. `[THEOREM: UTL-4]`
7. **The build is licensed in four units, measured on the corpus instance first (§7).**
   `[INFERENCE, falsifier UFF-1]`

### 1.3 Out of scope

Any `core/` change (code is licensed at the merge); any change to the structural relations, the
embedder, the plane or the ledger; the probabilistic analysis of the reinforced walk as a
stochastic process (what is proved is deterministic: the walk's stationary law under any field
state, and the mean field of the exponent; the almost-sure localization theorems are cited); a
field on the private instance before the corpus instance has measured it (§7); any reading of
the field by a model as an instruction (it is data, ranked with the rest).

### 1.4 What is proved, what is cited, what is measured, what is open

Proved on this branch, in `formal/Palace/Utility.lean` over `formal/Palace/Utility/Defs.lean`,
attacked in `formal/PalaceTest/Utility.lean` (seeds 402 to 424: twelve attacks and eleven
negative controls), stated in `formal/Spec/Utility.lean` and judged by the comparator: UTL-1 to UTL-6,
named in §4 and listed in the README's Utility paragraph; the controls as theorems: linear
reinforcement is unbounded, the exponent's three regimes on the two-site mean field, the greedy
walk's localization. The window and the fixed point need a logarithm and a complete metric, which
do not run, so UTL-2's window, UTL-5's eigenvalue counts and UTL-6's fixed point are proved and
not attacked; the algebra each rests on is.

Cited: the resistor-network reading of weights and potentials (Doyle and Snell); the Hodge
potential (DYN-3) and the walk sum (DYN-1, DYN-2); edge-reinforced random walk as a mixture of
reversible chains (Diaconis and Freedman; Diaconis; Keane and Rolles; Rolles; Merkl and Rolles;
Sabot and Tarrès); vertex-reinforced random walk's localization (Pemantle; Pemantle and Volkov;
Volkov; Tarrès; Benaïm and Tarrès); the attracting edge of strongly reinforced walks (Davis;
Limic and Tarrès); the exponent's phase transition in urns with feedback (Drinea, Frieze and
Mitzenmacher; Oliveira; Pemantle's survey); the exponentially weighted moving average (Roberts);
SCL-1's window and effective samples; inverse document frequency (Spärck Jones; Robertson) and
mutual information (Church and Hanks; Cover and Thomas); Weyl's inequality in SPC-3's counted
form and the Laplacian's largest eigenvalue (Anderson and Morley); the free energy of the walk
sum (temporal-retrieval A1; dn-graph-dynamics §5.4).

Measured, on synthetic graphs only: every bound of §4 against the field under a query load, the
arcs forming and fading, the learning and its forgetting, and the controls' localization
(`docs/experiments/utility-field-2026-11-08.md`).

Open, stated where it bites: the sharp total-variation constant (§4, UTL-3: `θ/(1 − θ)` is proved,
not tight); the gain of a real load's loop (§6: the contraction is proved for a declared gain, and
the load's gain is a measurement); the choice of the three numbers on a real corpus (§7).

## 2. The theory, stated precisely

### 2.1 Conductance and potential

In the resistor-network reading an edge weight is a conductance, a field on the nodes is a
potential, and the effective resistance `R_eff(i, j) = L⁺_ii + L⁺_jj − 2 L⁺_ij` says how easily
current passes between two nodes: a high-potential shortcut is a low-resistance path, and adding
conductance anywhere lowers every effective resistance or holds it (Rayleigh's law, CND-2).
`[ESTABLISHED: Doyle and Snell; CND-1, CND-2]` The field of this note lives on the edges as a
multiplier of conductance (§3.3): where the field is high the conductance is up to `1 + θ` times
the structural one, where it is low down to `1 − θ`, and every effective resistance moves within
those factors (`R_eff' ∈ [R_eff/(1 + θ), R_eff/(1 − θ)]`, by Rayleigh's law applied to the two
bounding networks). `[DERIVED from CND-2 and UTL-3's bounds]`

Read on the nodes, the field is a potential, and a potential has a gradient and no curl: the
edge field `d u` it induces is orthogonal to every circulation (DYN-1's `coboundary_velocity`,
`grad_velocity_dot_curl`). Read on the edges as a flow, the field's Hodge decomposition (DYN-3,
LAP-9) has a gradient part, which is the least-squares ranking of the nodes by use (who is
reached from whom), a curl part, which is local circulation (use that goes around a triangle),
and a harmonic part, circulation around the holes of the complex. The potential of the use flow
is the ranking the field carries; its inconsistency is how much use no ranking explains.
`[ESTABLISHED: DYN-3, LAP-9]` The walk sums (DYN-1, DYN-2) are what the nudge changes: a ranking
by `diffuse` is a resolvent `(1 − zP)⁻¹` of the walk on the effective weights, and the field
enters it only through those weights, so every bound on the weights (§2.5) is a bound on the
ranking.

### 2.2 Reinforcement and its pathologies

A walk that reinforces what it uses is the model of a store whose ranking feeds on its own use,
and the literature says exactly when that is benign.

- **Edge-reinforced random walk with linear reinforcement** (the walk crosses an edge with
  probability proportional to its weight, and adds one to the weight it crossed) is, on a finite
  graph, a mixture of reversible Markov chains: partially exchangeable, so by de Finetti's theorem
  for Markov chains a mixture of chains, and the mixing measure is explicit (the random
  environment). Reinforcement by use is equivalent to a random environment: the walk behaves, for
  all time, like a walk on fixed weights drawn once at random. `[ESTABLISHED: Diaconis and
  Freedman 1980; Diaconis 1988; Keane and Rolles 2000; Rolles 2003; Merkl and Rolles 2005; Sabot
  and Tarrès 2015]` This is the benign regime: nothing collapses, the environment is just not the
  structural one.
- **Vertex-reinforced random walk** (the probability proportional to the visit count of the
  target node) localizes: on `ℤ` it eventually visits five points forever, and on bounded-degree
  graphs it localizes with positive probability on a complete multipartite subgraph with its
  boundary. `[ESTABLISHED: Pemantle 1992; Pemantle and Volkov 1999; Volkov 2001; Tarrès 2004;
  Benaïm and Tarrès 2011]` This is the nonsensical state: the walk visits a few nodes forever.
- **Strong edge reinforcement** (the weight a function `w(n)` of the crossing count with
  `Σ 1/w(n) < ∞`, superlinear powers included) has an attracting edge: almost surely the walk
  eventually crosses one edge back and forth forever. `[ESTABLISHED: Davis 1990; Limic and Tarrès
  2007]`
- **The exponent decides.** In a generalized urn with feedback, the probability of a site is its
  weight to the power `α`: for `α > 1` one site eventually takes all but finitely many of the
  increments (monopoly); at `α = 1` the shares converge to a random limit; for `α < 1` the shares
  equalize. The phase transition is at `α = 1`. `[ESTABLISHED: Drinea, Frieze and Mitzenmacher
  2002; Oliveira 2009; Pemantle 2007 §4]` The two-site mean field shows the transition at the
  integer exponents: the ratio of the sites moves apart for `α ≥ 2`, is constant at `α = 1`, and moves to one at
  `α = 0` (`polya_ratio_lt`, `polya_ratio_eq`, `polya_ratio_gt`). `[THEOREM]` The greedy walk,
  which always takes its heaviest edge and reinforces it (the `α → ∞` limit), never leaves two
  nodes of a three-node path, so its empirical measure stays at least `1/8` from the structural
  stationary distribution in total variation at every horizon (`greedy_pos_ne_two`,
  `greedy_tv_ge`). `[THEOREM]`

The design must sit in the benign regime, and it does so by three means, each a theorem: the
increment is bounded and the field decays, so no site's weight is ever a power of its count
(UTL-1, UTL-2); the field enters the walk only through a bounded multiplier of the structural
weights, so the walk's stationary distribution is within a declared divergence of the structural
one whatever the field's state (UTL-3); and the loop by which the nudge changes what is used
next is a contraction when its gain is below the rate (UTL-6). §6 sets the three against the
regimes above.

### 2.3 Forgetting as a window

Exponential forgetting makes the field a time-weighted average. With no use the field obeys
`u_n − b = (1 − lam)^n (u_0 − b)` (UTL-2, `idle_apply`), and under a sequence of increments
`x_1, x_2, …` it is `b + Σ_k (1 − lam)^{n−k} x_k`: the exponentially weighted moving average of
the increments with factor `1 − lam`, Roberts's geometric moving average. `[ESTABLISHED: Roberts
1959]` Its effective window is `W = 2/lam − 1` ticks: the normalized average
`lam Σ_k (1 − lam)^{n−k} x_k` of independent increments of variance `σ²` has variance
`σ² lam / (2 − lam)` in the limit, the variance of a plain average over `W` ticks, so the field at
any tick is one reading of a window of `W` ticks, and it returns to within
`ε` of the baseline `log(c/(lam ε))/lam` ticks after use stops (`idle_window`). `[THEOREM for
the window; DERIVED for the variance]`

SCL-1 says when such an average is a stable macro quantity: a time average on a graph with gap
`γ` needs a window of many relaxation times `1/(εγ)`, and a window of `T` lazy steps carries at
most about `Tεγ/2` effective samples. Read on the field: a site's field is noise unless the
forgetting window `2/lam − 1` spans several relaxation times of the walk whose use it records,
and the number of uses that count in it is the window in relaxation times, not the number of
uses. The temporal context of the field is therefore one declared number, `lam`, with an upper
bound set by the graph's gap: the window spans `k` relaxation times when `2/lam − 1 ≥ k/(εγ)`,
that is when `lam ≤ 2εγ/(k + εγ)`. `[DERIVED from SCL-1]` The design declares `lam` per instance, and the corpus instance measures
`γ` first (§7).

### 2.4 Popularity against surprise

A token's popularity histogram is a base rate. Zipf's law says the rank-frequency curve of tokens
is a power law and Heaps's law that the vocabulary grows as a power of the text, so the most
popular tokens carry the least information about any document: inverse document frequency weights
a term by the log of the inverse of its document rate, which is the surprise of seeing it, and
that is why it works. `[ESTABLISHED: Zipf 1949; Heaps 1978; Spärck Jones 1972; Robertson 2004]`
What a path adds is measured the same way: the mutual information `I(X; Y) = Σ p(x, y) log
(p(x, y) / (p(x) p(y)))` between the anchor and what the path reaches, the pointwise form of
which is the association score of two tokens, counts the co-occurrence against the product of
the base rates and not the co-occurrence alone. `[ESTABLISHED: Church and Hanks 1990; Cover and
Thomas 2006]` SCL-3's reading is the same at the level of sources: a source's contribution is
its marginal, what the configuration with it scores over the configuration without, never its
popularity.

So the field rewards realized value over bare popularity (§3.6): a use adds to the field an
increment that is the value the use produced, the log-score advantage of a resolved question
(GRW-1's currency, which adds across questions) or a followed citation, discounted by the base rate of the site (the popularity
histogram). A site used a thousand times that never produced value stays at the baseline; a
site used twice whose uses resolved two questions rises. The histograms are kept because they
are the base rates the discount needs, and because `near`'s vocabulary and the embedder's
neighbourhoods have popularity curves of their own that a reader wants to see. `[INFERENCE,
falsifier UFF-3]`

### 2.5 The nudge, bounded

The field enters ranking as a bounded perturbation of the structural weights,
`A'_ij = A_ij (1 + η (u_ij − b))`, with `|u − b| ≤ c/lam` (UTL-1), so `A'_ij ∈ [(1 − θ) A_ij,
(1 + θ) A_ij]` with `θ = η c/lam` the margin (`nudge_le`, `le_nudge`). Three consequences, each
a theorem:

- The Dirichlet form moves by at most `θ` times itself: `|xᵀ (L' − L) x| ≤ θ xᵀ L x`
  (`abs_dotProduct_lap_sub_le`), so by Courant and Fischer every nonzero eigenvalue of `L'` lies
  in `[(1 − θ) λ_k, (1 + θ) λ_k]` of the structural one `[DERIVED]`, and in SPC-3's counted
  form, with `xᵀ L x ≤ 2 d_max ‖x‖²` (`dotProduct_lap_le_degree`, Anderson and Morley's bound as a
  form), the nudged Laplacian is within `2 θ d_max` of the structural one as a quadratic form
  (`near_lap_nudge`), and Weyl's inequality counted says an eigenvalue at most `t − 2θd_max`
  stays at most `t` and one at most `t` was at most `t + 2θd_max` (`count_lap_nudge_sub_le`,
  `count_lap_nudge_le_add`). `[THEOREM]`
- A spectral gap `γ` of the backbone is a gap `(1 − θ) γ` of the nudged graph, in DYN-6's
  Poincaré form (`hasSpectralGapAtLeast_nudge`), so every nonzero eigenvalue of `L'` is at least
  `(1 − θ) γ` (`le_eigenvalue_nudge`), and by DYN-6's contraction a weight change propagates under
  the lazy walk on the nudged graph at the rate `1 − ε(1 − θ)γ` a step: within the margin of the
  structural rate. `[THEOREM]`
- The structural order is kept beyond the margin: two weights whose ratio exceeds
  `(1 + θ)/(1 − θ)` keep their order under every field state (`nudge_lt_nudge_of_margin`), the
  field reorders only within that ratio, and at the baseline the effective weights are the
  structural ones exactly (`nudge_baseline`): removing the field recovers the structural order
  and the structural spectrum. No edge is erased and none is created, since an effective weight
  is zero exactly when the structural one is (`nudge_eq_zero_iff`, `support_nudge`).
  `[THEOREM]`

This is the bound that keeps the backbone primary: the field is a perturbation of declared
norm, and everything downstream of the weights, the walk sums, the potentials, the heat kernel,
the modes, inherits a bound of the same order through the theorems that already govern them
(DYN-2's tail, DYN-4's modes, DYN-6's gap). `[DERIVED]`

### 2.6 Energy

The walk sum is a partition function: `z_ij` sums `e^{−β E(path)}` over the killed walks from
`i` to `j`, with the energy of a path the sum of its edges' energies `E_e = −(1/β) log w_e`, and
the free energy `φ_ij = −(1/β) log(z_ij / z_jj)` is the distance `diffuse` ranks by (temporal-
retrieval A1; dn-graph-dynamics §5.4). `[ESTABLISHED]` The field shifts every edge's energy by
`ΔE_e = −(1/β) log(1 + η (u_e − b))`, which lies in `[−(1/β) log(1 + θ), −(1/β) log(1 − θ)]`: a
used path has lower energy by at most `(|P|/β) log(1 + θ)` and is reached by more of the walk's
weight, which is "lower energy states" made exact. `[DERIVED]` The forgetting rate plays the part
of a temperature: a low `lam` keeps the energy shifts for a long window, so the landscape the walk
sees is carved by the past; a high `lam` returns every shift to zero quickly, so the walk sees
the structural landscape with a short memory. The phase transition that a reinforced system can
have is the one §2.2 names and UTL-6 bounds: when the gain of the loop (how much a lower energy
raises the use that lowers it further) exceeds the rate, the mean-field equation
`lam (u − b) = sat(K (u − b))` has a second solution at the ceiling, a self-sustaining hot state
beside the structural one (`Witness.bistable`), and the field freezes into it: a symmetry
breaking in which the store prefers one of two equivalent paths forever. Below the rate there is
one solution and it is approached geometrically (`loop_existsUnique_fixedPoint`,
`loop_iterate_tendsto`). The transition is at `K = lam`, and the design declares `K < lam` by
bounding the gain (§6). `[THEOREM for the two fixed points and the contraction; the physical
reading DERIVED]`

## 3. The field

### 3.1 Sites, uses and provenance

A **site** is a node of the universe (an identity, a token of the lexical index, a vector of the
plane), an edge of a relation (a citation, a similarity above the threshold, a reply), or a
**declared path**: a chain the sentence algebra walked (`via`, `reach`, `trace`) recorded as a
unit. The field is one value per site, in the box of §3.2.

A **use** is a record `(site, tick, principal, kind, value, witness)`: the site, the tick of the
field's clock (one tick per round of the ledger or per housekeeping run, declared per instance),
the principal whose action produced it, the kind (a retrieval returned it, a chain traversed it,
a citation was followed to it, a resolved question credited it), the value (§3.6) and a witness
(the sentence, the question id). The use log is append-only and lives beside the ledger, in the
instance's own stores; the field is the fold of the update rule over it (`evolve`,
`evolve_append`), so two stores with the same log have the same field, a field can be rebuilt
from its log, and every value in it traces to the uses that built it. The log is observed data
with the principal as origin (ING-13); it never alters authored content, labels, identities or
relations, which the field reads and does not write. `[THEOREM: UTL-4 for the fold; the frame
DERIVED from ING-13, ING-17]`

### 3.2 The update rule and the three numbers

Per instance, three declared numbers: the baseline `b > 0`, the forgetting rate `lam ∈ (0, 1]`,
the cap `c ≥ 0` with `c < b · lam`. One tick:

```
u'(s) = b + (1 − lam) (u(s) − b) + sat_c(use(s)),      sat_c(x) = max(−c, min(c, x)),
```

with `use(s)` the sum of this tick's increments at `s`. The derived box is
`[b − c/lam, b + c/lam]`, its floor positive by `c < b lam`; the field starts at `b` everywhere
and never leaves the box (UTL-1). The ceiling is the geometric sum of increments at the cap, and
it is the least invariant ceiling: a site held at the cap climbs past every level below it
(`exists_steady_gt`). The closed forms: idle, `u_n = b + (1 − lam)^n (u_0 − b)`; held at a
constant use `r ∈ [−c, c]`, `u_n = b + (1 − lam)^n (u_0 − b) + (r/lam)(1 − (1 − lam)^n)`
(`steady_apply`). `[THEOREM]`

### 3.3 The nudge and the margin

The field enters every ranking through the effective weights `A' = A ∘ (1 + η (u − b))` on the
edges of the relation the sentence walks, with `η ≥ 0` the fourth declared number and
`θ = η c/lam < 1` the margin it implies. `near`, `diffuse`, `reach` and `walk` run on `A'` as
they run on `A` today; the universe's support, its degrees for RSP-5 and its components are
`A`'s, which `A'` shares (`support_nudge`). A node's field enters as the geometric mean of the
field on its incident edges' sites when a verb reads nodes (`top k` of a field), so that the node
nudge is a reordering within the same margin. §2.5 gives the bounds, and §4 the laws. An ablation
arm that reads the structural weights is the arm with `η = 0`, or with the field at `b`, the same
thing (`nudge_baseline`). `[THEOREM; the verbs' use of `A'` an INFERENCE, falsifier UFF-2]`

### 3.4 Arcs

An arc is a declared path whose field stands at least `a` above the baseline, `IsArc b a u P`,
with `a < c/lam` declared. It forms at a heat spot: a path used at the cap every tick is an arc
after `n` ticks once `(c/lam)(1 − (1 − lam)^n) ≥ a` (`isArc_steady`); it fades: left alone it is
no arc once `(1 − lam)^n c/lam < a` (`not_isArc_idle`), which is a window of
`log(c/(lam a))/lam` ticks. `[THEOREM]` What an arc does: the path's walk sum on the effective
weights is materialized (its resolvent entry cached, its chain kept as a unit), so a sentence
that reaches its end from its start pays one lookup rather than a solve, and the field on the
path's edges is what lifts the end in the start's ranking, each of its weights moved only within
the margin. An arc adds no edge: the support is the structural one at every tick (UTL-3), and the
weights the arc's end is reached through move by at most the factor `(1 + θ)/(1 − θ)` (UTL-5). When it fades, the cache is dropped; nothing else
changes. The list of current arcs, with each one's uses, is the field's own report of where the
heat is. `[DERIVED; the cache an INFERENCE, falsifier UFF-4]`

### 3.5 Histograms

Two histograms live beside the field, with the same clock and the same forgetting rate: the
popularity of tokens (how often each term of the lexical index was matched by a query or landed
in an item) and of vectors (how often each atom of the plane was returned by `near`). Each is a
field in the sense of §3.2 with `η = 0`: it decays and is capped, so it is a windowed count, and
it never nudges a ranking directly. Its two uses are the base rate of §3.6 and the report: the
rank-frequency curve of a window, read against Zipf's, is a diagnostic of the vocabulary, and
the vector histogram is the crowding diagnostic of dn-corpus-instance CI-1, read on what is
returned rather than on what exists. `[INFERENCE, falsifier UFF-3]`

### 3.6 Value against popularity: the increment

The increment a use adds at a site is `value · surprise`, `value` in `[−1, 1]` and `surprise` in
`[0, 1]` before the cap:

- `value` is `1` for a resolved question whose arm read the site and whose log-score advantage
  over the reference arm was positive at resolution (GRW-1's currency), the advantage clipped to `[0, 1]` by the protocol's bound; `1` for a citation
  followed from a result to its target; `ν ∈ (0, 1)` declared (the popularity credit) for a
  retrieval that returned the site and resolved nothing; `−1` for a resolved question whose arm
  read the site and whose advantage was negative, so that a site that misleads is pushed below
  the baseline, within the box.
- `surprise` is `1 − h(s)` with `h(s)` the site's popularity histogram normalized to `[0, 1]`
  over the window: a site everyone reaches earns little from one more reach, a rare site that
  produced value earns the full increment, the inverse-document-frequency shape of §2.4.

Both factors are bounded, so the increment is, and the cap `c` is the most any tick can add.
Nothing of the increment is a function of the field itself except through the ranking (§6).
`[INFERENCE, falsifier UFF-3]`

## 4. The laws

Each law is graded, with its falsifier and its control; the Lean names are in
`formal/Palace/Utility.lean`, the attacks in `formal/PalaceTest/Utility.lean`, and the rows in
`docs/LAWS.md` XV anchor the simulator's transcription (`eval/utility_field.py`), the one code
that computes the field today, with its tests as the Python falsifiers.

- **UTL-1 boundedness.** Every field value lies in the declared box `[b − c/lam, b + c/lam]`
  after any tick from inside it and after any log of uses, and the floor is positive when
  `c < b lam`: no weight is erased and none becomes infinite (`step_mem_box`, `evolve_mem_box`,
  `floor_pos`). Control: reinforcement without decay exceeds every bound (`linear_unbounded`;
  the attack at seed 404 leaves the box within 11 instances), and the box with ceiling `b + c` in
  place of `b + c/lam` is not invariant (seed 405). `[THEOREM]` Falsifier:
  `tests/unit/test_utility_field.py::test_the_box_is_invariant_under_any_use`.
- **UTL-2 decay.** With no use the field returns to the baseline geometrically,
  `u_n = b + (1 − lam)^n (u_0 − b)`, within `(1 − lam)^n c/lam` of it from anywhere in the box,
  and within a declared `ε` once `lam n ≥ log(c/(lam ε))` (`idle_apply`, `idle_sub_le`,
  `idle_window`); arcs fade on that window and form at a heat spot on the closed form
  (`not_isArc_idle`, `isArc_steady`). Control: a residual use of half the cap holds the field off
  the baseline past the idle bound (seed 407), and an arc left alone does not stay an arc (seed
  410). `[THEOREM]` Falsifiers: `test_an_idle_site_returns_within_epsilon_on_the_declared_window`,
  `test_arcs_form_at_a_heat_spot_and_fade_when_it_cools`.
- **UTL-3 no localization.** The reinforcement is normalized (bounded and decayed, UTL-1), the
  nudge keeps the support exactly (`nudge_eq_zero_iff`, `support_nudge`), no node's stationary
  mass under the nudged walk exceeds `(1 + θ)/(1 − θ)` times its structural mass and none falls
  under `(1 − θ)/(1 + θ)` of it (`statDist_nudge_le`, `le_statDist_nudge`), the two stationary
  distributions are within `θ/(1 − θ)` in total variation (`tv_statDist_nudge_le`), and a gap `γ`
  of the backbone is a gap `(1 − θ) γ` of the nudged graph (`hasSpectralGapAtLeast_nudge`,
  `le_eigenvalue_nudge`): no collapse into hubs, for every field state in the box, at every
  time. Controls: the additive nudge creates edges (seed 412); a field outside the box breaks
  the bound (seed 414); the greedy walk, strong reinforcement's limit, never leaves two nodes and
  its empirical measure stays `1/8` from the structural law (`greedy_pos_ne_two`,
  `greedy_tv_ge`, seeds 423 and 424). `[THEOREM]` Falsifier:
  `test_the_stationary_distribution_stays_within_the_margin_bound`.
- **UTL-4 derivation and provenance.** The field is the fold of the update over the use log
  (`evolve_append`), so it is observed and derived, rebuilt from the log, with each value traced
  to the uses that built it; it never alters authored content or labels, which it does not
  write; and it is a source that attribution can switch off (SCL-3): at the baseline the
  effective weights are the structural ones (`nudge_baseline`). `[THEOREM for the fold and the
  baseline; the frame DERIVED]` Falsifier:
  `test_the_field_is_a_fold_over_the_log_and_switches_off_at_baseline`.
- **UTL-5 the bounded nudge.** The ranking perturbation's norm is at most the declared margin:
  `|xᵀ (L' − L) x| ≤ θ xᵀ L x` (`abs_dotProduct_lap_sub_le`), the nudged Laplacian is within
  `2θ d_max` of the structural one (`near_lap_nudge`), and by Weyl's inequality counted every
  eigenvalue moves by at most that (`count_lap_nudge_sub_le`, `count_lap_nudge_le_add`); two
  weights whose ratio exceeds `(1 + θ)/(1 − θ)` keep their order (`nudge_lt_nudge_of_margin`), so
  the structural order is recovered when the field is removed. Control: a field outside the box
  moves the form past the margin (seed 416), and the largest degree alone does not bound the
  form (seed 418). `[THEOREM]` Falsifiers: `test_the_laplacian_eigenvalues_move_within_the_bound`,
  `test_order_is_kept_beyond_the_margin`.
- **UTL-6 no self-reinforcing loop.** When this tick's use is a `K`-Lipschitz function of the
  field with `K < lam`, the closed loop contracts the sup distance by `1 − lam + K` a tick
  (`loop_dist_le`), has exactly one stationary field (`loop_existsUnique_fixedPoint`), and its
  iterates converge to it geometrically (`loop_iterate_tendsto`). Control: at `K ≥ lam` the loop
  `use = K (u − b)` holds the ceiling fixed beside the baseline (`Witness.bistable`,
  `Witness.not_unique`; seed 420). `[THEOREM]` Falsifiers:
  `test_the_closed_loop_contracts_below_the_rate`,
  `test_control_at_the_rate_the_ceiling_is_a_second_fixed_point`.

## 5. Measurements on synthetic graphs

The simulator drove the model on a two-community graph of 24 nodes and 76 edges under a
rank-frequency load that moves between the communities, at `b = 1`, `lam = 0.05`, `c = 0.02`,
`η = 5/6`, so `θ = 1/3` (`docs/experiments/utility-field-2026-11-08.md`). `[MEASURED]`

- The box held at every one of 360 ticks. The first arc formed at tick 31 on the hot edge,
  the one edge from the hottest anchor to its answer (the closed form predicts 28 ticks for a
  site at the cap every tick); the hot edge peaked at 1.381 against the ceiling 1.4; the arcs were
  gone by the sixth tick after the load moved (UTL-2's bound from anywhere in the box), and 74
  ticks after it, the declared window for `ε = 0.01`, the hot edge stood at 1.0081.
- The total variation between the nudged and the structural stationary distributions never
  exceeded 0.012 against the bound 0.5; the largest eigenvalue move was 0.367 against 4.76; the
  gap never fell under 0.18303 against the bound 0.122. UTL-5's order law is not exercised here:
  no two of the graph's weights are more than the factor 2 apart (the largest ratio is 1.97), so
  the unit test checks it on a graph and a margin where some are.
- The learning: the planted answers' mean rank fell from 2.00 to 1.75 while their load was hot,
  returned to 2.00 when it left, and fell to 1.50 when it returned; the share ranked first went
  0, 0.25, 0, 0.5; the live load's first-result hit rate rose from 0 to 0.26 in the first phase.
  The laws bound how far each weight moves, not which of two walk sums is the larger, so they do
  not say which answers rise; the run does not separate why two of the four stayed second.
- The controls: reinforcement without decay or cap at exponent 2 localized within 20,000 steps
  (0.999 of the steps on one edge, 8 of 24 nodes visited, total variation 0.91 from the
  structural law); at exponent 1 it visited every node and concentrated on no edge but sat 0.48
  from the structural law, the random environment; at exponent 0.5 it sat at 0.06; the bounded
  field, under the same walk, at 0.028, with 0.02 of the steps on its most used edge. The two-site
  mean field's leader held 0.996 of the mass after 2,000 steps at exponent 2, exactly `6/11` at
  exponent 1, and 0.502 at exponent 0.5. The loop contracted at exactly `1 − lam + K` for
  `K/lam ∈ {0.25, 0.5, 0.9}` and expanded at `1.5`, where the baseline, the ceiling and the floor
  were all fixed.

## 6. The regime

| scheme | what reinforces | decay | bound | regime | source |
|---|---|---|---|---|---|
| vertex-reinforced walk | the node's visit count, linearly | none | none | localizes on a finite set (nonsensical) | Pemantle; Volkov; Tarrès; Benaïm and Tarrès |
| edge-reinforced walk, superlinear | the edge's count to a power above one | none | none | an attracting edge (nonsensical) | Davis; Limic and Tarrès; the greedy control |
| edge-reinforced walk, linear | the edge's count | none | none | a random environment: a mixture of reversible chains, no collapse, a stationary law that is not the structural one | Diaconis and Freedman; Keane and Rolles; Rolles; Sabot and Tarrès |
| urn with feedback, sublinear | the count to a power below one | none | none | equalizes | Drinea, Frieze and Mitzenmacher; Oliveira |
| **this design** | the value a use produced, discounted by popularity | `lam` a tick | `[−c, c]` a tick, the box, the margin `θ` | the stationary law within `θ/(1 − θ)` of the structural one at every time; one stationary field when the loop's gain is below `lam` | UTL-1, UTL-3, UTL-6 |

The design is sublinear-and-normalized in the exponent's terms: an increment never grows with
the site's own weight, the field is a windowed average rather than a count, and the walk's
weights are the structural ones within a margin. The one way it could leave the regime is
through the loop: if the nudge raised a site's use enough to raise its nudge further, with gain
`K ≥ lam`, the hot state would sustain itself (UTL-6's control). The design keeps the gain small:
a nudge moves each weight only within the margin (UTL-3, UTL-5), so it raises a site's use only as
far as reweighting its edges by at most `(1 + θ)/(1 − θ)` can, and the increment counts value,
which the nudge does not produce (a resolved question resolves by the world, not by the
ranking). The declared
`K < lam` is a measurement the corpus instance makes (§7): the use a site receives against the
field it carries, read on the log, which is the loop's gain. `[DERIVED; the measured gain a
HYPOTHESIS, falsifier UFF-5]`

## 7. The build order

Nothing is built by this note. What the merge licenses, in order, each unit measured on the
corpus instance (dn-corpus-instance, its own stores and its own ledger) before anything runs on
the default instance, which keeps `η = 0` until the measurements say otherwise:

- **UF-1 the use log and the field.** A store of use records beside the ledger, the tick, the
  update rule with its three numbers in the instance's configuration, the fold on housekeeping,
  the box asserted (UTL-1 as a property test on the code), the histograms of §3.5. No ranking
  reads it. Measured: the field's distribution and the forgetting window against SCL-1's
  relaxation time on the corpus instance's graphs.
- **UF-2 the nudge.** `A'` behind a switch, `η` declared, the verbs reading `A'` where they read
  `A`, the arm with `η = 0` registered in the ledger (SCL-3: the field is a source). Measured: the
  ablation's log-score advantage at the ledger's bar, and UTL-3 and UTL-5 as property tests
  against the code's own spectra.
- **UF-3 arcs.** Declared paths as sites, the arc list, the cached walk sums, the fade. Measured:
  arcs formed and faded on the corpus load against the closed forms.
- **UF-4 value.** The increment of §3.6 wired to the ledger's resolutions and to followed
  citations, the popularity discount. Measured: the loop's gain (§6) on the log, and whether the
  value-weighted field's arm beats the popularity-weighted one at the bar.

Each unit transcribes its laws and property-tests the transcription against the Lean statements;
the ledger rows of family XV move their anchors from the simulator to `core/` as the code lands
(dn-mathematical-foundations §2.4). `[INFERENCE, falsifier UFF-1]`

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| UF-a | the three numbers on a real instance | `b = 1`, `lam` from the measured gap (§2.3), `c = b lam / 2`, `η` so that `θ ≤ 1/3` | the corpus instance's UF-1 measurement |
| UF-b | the tick | one per ledger round on an instance with a ledger; one per housekeeping run otherwise | an instance whose rounds are far apart against its load |
| UF-c | a node's nudge | the geometric mean of its incident edges' factors | a verb whose node reading the edges cannot carry |
| UF-d | the popularity credit `ν` | `0.1` | UF-4's comparison of the two arms |
| UF-e | the arc height `a` | `3/4` of the box's half-height | the corpus instance's arc list, too long or empty |
| UF-f | a field on the vector plane's atoms as sites | the histogram only (no nudge of `near`'s cosine) | a measured gain in the ablation |

## Falsifiers

- **UFF-1 (a transcription lies):** a built unit whose property test against a Lean statement
  fails. A transcription defect; the unit does not land until it agrees.
- **UFF-2 (a verb cannot read `A'`):** a verb of the algebra whose law (QSA-1 to QSA-10) fails on
  the nudged weights. UTL-3 says the support, the symmetry and the nonnegativity are kept, so the
  laws' hypotheses hold; a failure is a hypothesis the laws state that this note missed.
- **UFF-3 (value does not beat popularity):** on the corpus instance the arm with the
  value-weighted field has no advantage over the popularity-weighted one at the bar. Then §3.6's
  increment retires to the histogram and the design keeps the structure of §3 with `value = ν`.
- **UFF-4 (arcs do not pay):** cached walk sums slower than the solve, or arcs that never form at
  the declared height on a real load. Then the cache is dropped and arcs stay a report.
- **UFF-5 (the gain is not below the rate):** a measured loop gain `K ≥ lam` on the corpus
  instance. Then `η` is lowered until it is, which the margin allows, or the field is switched
  off; UTL-6's control is the state that would otherwise be seen.
- **UFF-6 (a bound is violated in float64):** a measured total variation above `θ/(1 − θ)` or an
  eigenvalue move above `2θ d_max` on the code's own spectra. The theorems say this cannot happen
  over the reals; a float instance that does is a rung L3 finding, not a refutation.

## Open questions

- Should the field's clock be the event clock's cut (CLK-2), so that a field "as of c" is exact,
  or a coarser tick? The fold is a function of the log either way.
- Does a node field on the vector plane's atoms nudge `near`'s cosine, which is not a walk, or
  only the walks that follow it? UF-f keeps it to the histogram until measured.
- What is the right divergence to declare for UTL-3 on an instance: total variation, as proved,
  or the ratio bound `(1 + θ)/(1 − θ)`, which is per node and sharper?
- Is the mean-field gain of §6 the right reading of a real load's loop, or does the sampled form
  of SCL-1 (the effective samples in a window) bound it better?

## Cross-references

**Formal (this branch):** `formal/Palace/Utility/Defs.lean` (`sat`, `step`, `evolve`, `ceiling`,
`floor`, `InBox`, `idle`, `steady`, `IsArc`, `loop`, `linearStep`, `nudge`, `margin`, `statDist`,
`tv`, `isSymm_nudge`, `isSymmetric_toEuclideanLin_lap`, `polyaStep`, `Greedy`, `greedyStep`,
`greedyWalk`, `greedyVisits`, `greedyEmp`, `path3`); `formal/Palace/Utility.lean` (UTL-1
`step_mem_box`, `evolve_mem_box`, `floor_pos`, `inBox_const_baseline`, `exists_steady_gt`,
`linearStep_iterate`, `linear_unbounded`; UTL-2 `idle_apply`, `idle_sub_le`, `one_sub_pow_le_exp`,
`idle_window`, `not_isArc_idle`, `steady_apply`, `isArc_steady`; UTL-3 `nudge_factor_mem`,
`nudge_eq_zero_iff`, `nudge_le`, `le_nudge`, `nudge_nonneg`, `degree_nudge_le`,
`le_degree_nudge`, `statDist_nonneg`, `sum_statDist`, `statDist_nudge_le`, `le_statDist_nudge`,
`tv_statDist_nudge_le`, `hasSpectralGapAtLeast_nudge`, `le_eigenvalue_nudge`, `support_nudge`;
UTL-4 `evolve_append`, `nudge_baseline`; UTL-5 `dotProduct_lap_nudge_le`,
`le_dotProduct_lap_nudge`, `abs_dotProduct_lap_sub_le`, `dotProduct_lap_le_degree`,
`near_lap_nudge`, `count_lap_nudge_sub_le`, `count_lap_nudge_le_add`, `nudge_lt_nudge_of_margin`;
UTL-6 `loop_dist_le`, `loop_existsUnique_fixedPoint`, `loop_iterate_tendsto`,
`Witness.bistable`, `Witness.not_unique`; the regimes `polya_ratio_lt`, `polya_ratio_eq`,
`polya_ratio_gt`, `greedy_invariant`, `greedy_pos_ne_two`, `greedyVisits_two`,
`statDist_path3_two`, `greedy_tv_ge`); `formal/Spec/Utility.lean` (the twenty statements the
ledger cites); `formal/PalaceTest/Utility.lean` (seeds 402 to 424); the families cited:
`Palace/Dynamics.lean` (DYN-1, DYN-3, DYN-6), `Palace/Gap.lean` (SPC-3), `Palace/Laplacian.lean`
(LAP-2's Dirichlet identity), `Palace/Spectral.lean` (CND-1), `Palace/Rayleigh.lean` (CND-2),
`Palace/Growth.lean` (GRW-1), `Palace/Scale.lean` (SCL-1, SCL-3).

**Code (read at `950514b1`, unchanged):** `core/query.py` (`free_energy_distances`, the walk
sum the nudge would enter), `core/sentence/execute.py` and `core/sentence/universe.py` (the
universe, its support and degrees), `core/graph/conductance.py` (the heat kernel and the
pseudo-inverse), `eval/predictions/scoring.py` (`growth`, the currency), `core/ingest/lexical.py`
(the tokens the histogram would count); `eval/utility_field.py` (the simulator, new);
`tests/unit/test_utility_field.py` (the falsifiers, new).

**Design:** dn-graph-dynamics §3 (the resolvent), §4 (the Hodge reading), §5.3 and §5.4 (the
gap, the free energy); dn-scale-and-attribution §2.1 (SCL-1), §3.3 and §3.4 (the currency,
SCL-3); dn-prediction-ledger G1 to G8; dn-corpus-instance §2.1 (crowding), §3 (the instance);
dn-query-sentence-algebra §2.2 and §2.9; dn-ingress-language ING-13, ING-17;
dn-mathematical-foundations §2.2 and §2.4; `papers/2026-11-08-utility-field/paper.tex`.
