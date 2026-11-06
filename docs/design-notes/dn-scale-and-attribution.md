---
type: design-note
id: dn-scale-and-attribution
track: dynamics
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: design-only    # nothing built; the theorems are machine-checked in formal/Palace/Scale.lean
created: 2026-11-07
updated: 2026-11-07
links:
  - papers/2026-11-07-scale-and-attribution/paper.tex   # the article: the same theorems, with proof sketches and the references
  - docs/design-notes/dn-graph-dynamics.md               # DYN-1 to DYN-6: the modes, the gap, the heat kernel and the lazy walk this builds on
  - docs/design-notes/dn-prediction-ledger.md            # the ledger G1 to G8: forward only, pre-registered, the controls, the sign-flip test, the growth readout
  - docs/design-notes/scored-beliefs-and-earned-entitlement.md  # BL-3 the attribution replay this note designs the reading of
  - docs/tracks/deployed-instances.md                    # DI-2: a corpus of its own runs in an instance of its own
  - docs/design-notes/dn-mathematical-foundations.md     # the ladder; design theorems enter the ledger when code relies on them
  - formal/Palace/Scale.lean                             # the theorems (formal/Palace/Scale/Defs.lean the model; PalaceTest/Scale.lean the attacks)
supersedes: null
superseded_by: null
warrant: null
---

# Scale and attribution: when macro behaviour can be studied, and how progress is attributed

> Composed on the scale session (Fable 5.1, 2026-11-07), on the standing direction that the
> design and its proofs come first and the build follows a licence given at the merge.
> Agent-drafted, filed `draft` on a branch; the merge is ratification. Nothing is built: `core/`
> and `eval/` are untouched. Every nontrivial claim carries a grade: `[THEOREM]` is
> machine-checked in `formal/Palace/Scale.lean` and names its declaration; `[ESTABLISHED]` is
> Mathlib's, a ratified note's or a cited result's; `[DERIVED]` is argued here from those;
> `[INFERENCE]` is a design call with a named falsifier; `[HYPOTHESIS]` is a claim the palace
> cannot check today, with what would check it named. The live instance's figures are the
> read-only measurements of 2026-11-04 and 2026-11-07 recorded in `dn-graph-dynamics` §2.1 and
> §5.4. The article `papers/2026-11-07-scale-and-attribution/paper.tex` states the same theorems
> with proof sketches and the references.

## 1. Purpose and scope

### 1.1 The questions

A store that builds context from many sources should be able to say, with evidence, which
sources, which context windows and which analysis tools improve its results. That needs two
things, and this note takes them in order.

1. **Scale.** Data at a scale where the macro quantities are stable: where a spectral gap, an
   eigengap, a time average of an observable can be measured and will be found again tomorrow,
   rather than fluctuating with every note added. What thresholds of scale can be proved, and
   what can be predicted from cited results?
2. **Attribution.** A continuous evaluation whose outcomes can be attributed to each source or
   tool: an experiment that never ends, in which the store's own future labels its present, every
   configuration forecasts the same questions, and the advantage of one configuration over another
   is read in a common currency with a pre-registered bar. What loop makes attribution sound, and
   what does a sound attribution mean when sources are redundant?

### 1.2 Decisions

1. **The estimation threshold is the relaxation time (§2.1).** Under the diffusion a mean-zero
   observable's time average over a window of `T` steps has energy at most `‖f‖² / (T ε γ)²`, so
   the window must span many relaxation times `1/(ε γ)`; for an observable sampled along the walk
   the sampled form bounds the variance by `2σ² / (ε γ T)`, at least `T ε γ / 2` effective
   samples (in diffusion time `T_c = εT`: `2σ² / (γ T_c)` and `T_c γ / 2`). SCL-1.
2. **The scale separation is the eigengap at the cut (§2.2).** With a gap `g` between the kept
   and the dropped eigenvalues, the dropped part's share of the energy falls as `e^{−2gt}`, so a
   `k`-mode macro description explains all but `η` of what remains once `t ≥ log(R/η) / (2g)`;
   without a gap no time does. SCL-2.
3. **Spectra stop fluctuating at a logarithmic minimum degree (§2.3).** Cited, not proved: the
   normalized Laplacian's eigenvalues concentrate once the minimum expected degree `d_min`
   exceeds a constant times `log N`, within `O(√(log N / d_min))` of their expectation. The
   sibling study measures where that happens on real data.
4. **The loop is a prediction ledger whose questions the store generates about its own future
   (§3).** Forward only, pre-registered, each configuration an arm, the full system and the system
   with one source, one context window or one analysis tool removed, resolved by a later cut.
5. **The currency is the log-score advantage over a reference arm (§3.3).** It is additive over
   questions and it is exactly the growth of the proportional stake (GRW-1), so one number serves
   the decision rule, the growth readout and the attribution.
6. **Attribution is two readings, and the proof says when they disagree (§3.4).** Per ablation,
   the sign-flip test on the paired differences, which is leave-one-out; over the sources, the
   Shapley value, the unique efficient, symmetric, null-respecting, additive attribution, by
   permutation sampling with its variance when the source count makes enumeration expensive.
   Leave-one-out confirms necessity and not contribution: two redundant sources both read zero
   while each carries half. SCL-3.
7. **The bar is the ledger's power calculation (§3.5).** SCL-4, the number of independent
   resolved units to detect an effect `Δ` at `α` and power `1 − β`, is `required_clusters`;
   derived here from the normal approximation, not formalized.
8. **The machinery is generic and belongs in the palace; a corpus belongs in its own instance
   (§6).**

### 1.3 Out of scope

Any `core/` or `eval/` change (code is licensed at the merge); the choice of a corpus (§4 lists
candidates and what each exercises; the sibling study, #76, picks and measures);
the statistical-physics reading of the evolution (dn-graph-dynamics §5.4's hypothesis stands);
BL-6's dossiers; any claim that a particular arm has an edge, which only the loop can make.

### 1.4 What is proved, what is cited, what is open

Proved on this branch, in `formal/Palace/Scale.lean` over `formal/Palace/Scale/Defs.lean`,
attacked in `formal/PalaceTest/Scale.lean` (seeds 350 to 367, each attack with a negative
control): SCL-1, SCL-2 and SCL-3, named in the sections below and listed in the README's Scale
paragraph. The spectral gap is an eigenvalue and does not run, so SCL-1 is attacked where the
spectrum is rational (complete bipartite graphs with a uniform weight), SCL-2's discrete twin on
diagonal operators, and SCL-3 on games over three sources with the six orderings enumerated.

Cited: the modes, the mode-decay bound, the spectral gap and the lazy walk's contraction
(DYN-4, DYN-6, `Palace/Dynamics.lean`); the ledger's scoring, the sign-flip test and the
growth readout (dn-prediction-ledger G5 and G8, GRW-1 to GRW-6); the concentration of random
graph spectra (Oliveira 2009; Chung and Radcliffe 2011); the asymptotic variance of a time average
along a reversible chain (Aldous and Fill; Levin and Peres); the Shapley value's uniqueness
(Shapley 1953) and its permutation-sampling estimator (Castro, Gómez and Tejada 2009; Ghorbani and
Zou 2019).

Open, stated where it bites: the sampled form of SCL-1 is derived for a chain started at
stationarity and not machine-checked (§2.1); the concentration threshold's constant is the cited
theorem's and the sibling study's to measure (§2.3); every threshold is stated for a fixed graph,
and the evolving graph's own mixing stays the hypothesis of dn-graph-dynamics §5.4 (§2.4).

## 2. The thresholds of scale

The objects are those of dn-graph-dynamics: a weighted graph `A` on `N` nodes with Laplacian
`L`, its modes `φ_j` with eigenvalues `λ_j`, the heat kernel `H_t = e^{−tL}` and the lazy walk
`N_ε = 1 − εL`, the spectral gap `γ` (the least nonzero eigenvalue on a connected support, DYN-6),
and a field on the nodes read as an observable. A macro quantity is a function of the low modes
(§5 of that note). The question here is when such a quantity can be measured.

### 2.1 SCL-1 The estimation threshold

Take an observable `x` of mean zero (`x ⬝ 1 = 0`) and read it along the diffusion: `x`, `N_ε x`,
`N_ε² x`, …, the state after each step. Its time average over a window of `T` steps,
`avg_T = (1/T) Σ_{n<T} N_ε^n x` (`timeAverage`), is the estimate of the macro observable, and the
question is how large `T` must be for the estimate to be close to its limit, which is the mean,
zero. On each mode the walk multiplies by `1 − ελ_j`, so the average multiplies by the geometric
mean sum (`timeAverage_dotProduct_mode`), and:

- SCL-1 on a connected support with gap `γ` and `ελ_j ≤ 1` on every eigenvalue, the energy of
  the time average of a mean-zero field is at most `((1/T) Σ_{n<T} (1 − εγ)^n)² ‖x‖²`
  (`lazy_timeAverage_energy_le`), so at most `‖x‖² / (T ε γ)²` (`lazy_timeAverage_energy_le_window`,
  the geometric sum under `1/(εγ)`). `[THEOREM]`
- The window a precision needs: once `T ≥ ‖x‖ / (ε γ δ)`, the time average is within `δ` of the
  mean, `‖avg_T‖² ≤ δ²` (`lazy_timeAverage_precision`). `[THEOREM]`

Read in continuous units, a window of `T` lazy steps is a span of `T_c = Tε` of diffusion time
and `1/γ` is the relaxation time, so the bound is `‖x‖² / (γ T_c)²`: the estimate is within `δ` of
the mean once the window spans `‖x‖/δ` relaxation times. The exact constant proved is `1/(γT_c)²`,
the deterministic form, in which the readings are the exact states of the diffusion.

The sampled form, for an observable read along a random walk rather than along the exact
diffusion, has the constant the question asks for. The lazy walk `1 − εL` with
`ε ≤ 1/(2 d_max)` (stochastic, and `ελ ≤ 1` on the whole spectrum since `λ_max ≤ 2 d_max`, the
hypothesis of `lazy_pow_energy_le`) is a symmetric Markov chain with the uniform stationary
distribution, and for a chain started at
stationarity the variance of `Σ_{t<T} f(X_t)` is `Σ_{s,t} ⟨f₀, P^{|s−t|} f₀⟩` with `f₀` the centered
observable; each term is at most `(1 − εγ)^{|s−t|} ‖f₀‖²` by the contraction on the modes (DYN-6,
`lazy_pow_energy_le` with Cauchy–Schwarz), so the variance of the time average is at most

```
Var(avg_T) ≤ (σ² / T) · (1 + 2 Σ_{k≥1} (1 − εγ)^k) = (σ² / T) · (2 − εγ) / (εγ) ≤ 2σ² / (εγ T),
```

with `σ² = ‖f₀‖² / N` the observable's variance under the uniform measure, and in continuous
units `2σ² / (γ T_c)` with `T_c = εT`. So `T ≥ 2σ² / (ε γ δ²)` lazy steps, that is
`T_c ≥ 2σ² / (γ δ²)` of diffusion time, suffice for a standard error of at most `δ`, and a window
of `T_c` carries at least `T_c γ / 2` **effective samples** (`σ²` over the variance of the
average): the readings within a relaxation time are one observation. `[DERIVED, for a chain started at
stationarity; the textbook form is cited: Aldous and Fill, Chapter 4; Levin and Peres,
Chapter 12]` The machine-checked part is the contraction on the modes; the chain, its
stationarity and the covariance identity are not formalized, which §1.4 records.

Both forms say the same thing in the question's terms: **a macro observable cannot be estimated
from a window shorter than the relaxation time, whatever the number of readings in it**, and the
number of readings that count is the window in relaxation times. The attack (seed 350) checks the
window bound on complete bipartite graphs, where the gap is exact, over windows of up to seven
steps; its controls, the largest eigenvalue in place of the gap (seed 352) and a field with a mean,
which the walk conserves (seed 353), are refuted within 5 and 25 instances.

### 2.2 SCL-2 Scale separation

A macro description keeps the first `k` modes, `S`, and drops the rest (DYN-4's `modeProj`).
DYN-4 says the dropped part decays at least as fast as the slowest dropped mode,
`‖H_t (f − P_S f)‖² ≤ e^{−2μt} ‖f − P_S f‖²` for `μ` under every dropped eigenvalue. The
question is when the dropped part is negligible against what the description keeps, and that
needs the other side:

- the kept part decays no faster than its fastest mode: for `ν` at least every kept eigenvalue,
  `e^{−2νt} ‖P_S f‖² ≤ ‖H_t P_S f‖²` (`heat_modeProj_energy_ge`, through `heat_energy_ge`, the
  mode-decay bound from below). `[THEOREM]`
- SCL-2 so the dropped part's energy relative to the kept part's falls by `e^{−2(μ−ν)t}`:
  `‖H_t (f − P_S f)‖² ‖P_S f‖² ≤ e^{−2(μ−ν)t} ‖f − P_S f‖² ‖H_t P_S f‖²` (`scale_separation`).
  With `S` the first `k` modes, `ν = λ_k`, `μ = λ_{k+1}` and `g = μ − ν` is the eigengap at the
  cut. `[THEOREM]`
- The time: with `g > 0` and a kept part that is not zero, once
  `t ≥ log(R / η) / (2g)` for `R = ‖f − P_S f‖² / ‖P_S f‖²` the initial ratio, the `k`-mode
  description explains all but `η` of what remains: `‖H_t (f − P_S f)‖² ≤ η ‖H_t P_S f‖²`
  (`scale_separation_time`). `[THEOREM]` In amplitude rather than energy the rate is `e^{−gt}`
  and the time `log(√R / √η) / g`, the form the question states.
- The discrete twin under any symmetric operator that multiplies the dropped modes by at most
  `ρ₁` and the kept modes by at least `ρ₂`: after `n` steps
  `ρ₂^{2n} ‖N^n (f − P_S f)‖² ‖P_S f‖² ≤ ρ₁^{2n} ‖f − P_S f‖² ‖N^n P_S f‖²`
  (`scale_separation_pow`, through `pow_energy_ge`); for the lazy walk `ρ₁ = 1 − εμ` and
  `ρ₂ = 1 − εν`. `[THEOREM]`
- The control: without a gap there is no such time. On the identity every eigenvalue is `1`
  (`eigenvalues_one`), so two equal eigenvalues straddle every cut, and the dropped share of the
  energy is the same at every time (`no_gap_no_separation`): if some time makes the dropped part
  at most `η` of the kept, it already was at time zero (`no_gap_no_time`). `[THEOREM, as the
  control]` The attack's control (seed 355), that the dropped share always falls, is refuted
  within 19 instances on a cut with a kept eigenvalue above a dropped one, where the share rises.

Read on the question: a `k`-mode macro description of the store is legitimate at the time scale
`1/g` of the eigengap at its cut, and only there. Where the spectrum has no gap near `k`, no
choice of `k` gives a macro description that the dynamics separates from the rest; the modes
near the cut exchange energy on the same time scale as the ones kept. A spectrum of `38`
eigenvalues is a list in which the gaps are the gaps of a list, not of a density
(dn-graph-dynamics §5.4), and the sibling study's first measurement is where the eigengaps of a
real citation graph stabilize as it grows. `[DERIVED]`

### 2.3 Where the spectrum stops fluctuating, cited

SCL-1 and SCL-2 are about a fixed graph. A store grows, and the graph the thresholds are measured
on is a sample: the question of scale is when the measured `γ` and `g` are properties of the
corpus rather than of the sample. For a random graph with independent edges the answer is a
theorem, cited here and not formalized:

- Oliveira (2009): for a random graph on `N` nodes with independent edges whose minimum expected
  degree is `d_min ≥ C log N`, with probability `1 − o(1)` the adjacency matrix and the normalized
  Laplacian are within `O(√(log N / d_min))` in operator norm of their expectations, so every eigenvalue
  of the normalized Laplacian is within `O(√(log N / d_min))` of the expected graph's. Chung and
  Radcliffe (2011) give the same concentration with explicit constants, for general random graphs
  with independent edges, through a matrix Chernoff bound. `[ESTABLISHED, cited]`

The prediction: the measured spectrum stops fluctuating once the minimum expected degree exceeds a
constant times `log N`, and a gap `γ` (or an eigengap `g`) of the normalized Laplacian is a stable
macro quantity once the fluctuation scale is below it, `√(log N / d_min) ≪ γ`, that is
`d_min ≫ log N / γ²`. Below that, a measured gap is noise of the sample; above it, the gap is the
corpus's and SCL-1 and SCL-2 can be sized from it. A real citation graph does not have independent
edges, so the constant and the exponent are the sibling study's to measure: it records the
eigenvalues of the normalized Laplacian of a growing dated graph at successive cuts and reports
where the gaps stop moving as a function of the minimum degree. `[HYPOTHESIS: the concentration
law's shape on real data; checked by #76]`

### 2.4 The thresholds together

| quantity | symbol | what sets it | the threshold |
|---|---|---|---|
| the gap | `γ` | the least nonzero eigenvalue of `L` on a connected support (DYN-6) | the window must span many `1/γ`: `T_c ≥ ‖x‖/(γ δ)` exact, `T_c ≥ 2σ²/(γ δ²)` sampled, `T_c = εT` (SCL-1) |
| the eigengap at the cut | `g = λ_{k+1} − λ_k` | the spectrum near the kept modes | the macro description is legitimate from `t ≥ log(R/η)/(2g)`; no gap, no time (SCL-2) |
| the effective sample size | `T_c γ / 2` | the window in relaxation times | the number of readings that count in a window (SCL-1, sampled) |
| the minimum degree | `d_min` | the sparsest node's expected degree | spectra concentrate once `d_min ≥ C log N`; a gap is stable once `d_min ≫ log N / γ²` (§2.3, cited) |
| the number of resolved units | `K` | independent clusters of resolved questions | `K ≥ ((z_{1−α/2} + z_{1−β}) s / Δ)²` to detect an effect `Δ` (SCL-4, §3.5) |

Each is a theorem or a cited theorem on a fixed graph; what they are measured on is a sequence of
graphs, and that the sequence has a stationary regime is the hypothesis of dn-graph-dynamics
§5.4, unchanged here. The thresholds do not need it: they say what a measurement on the graph at a
cut means, and the loop of §3 is what makes the sequence of cuts into evidence.

## 3. The continuous evaluation loop

### 3.1 The store's own future labels its present

The ledger (dn-prediction-ledger) scores probabilities on yes/no questions that resolve later,
forward only, under a protocol written before the first prediction. What this note adds is where
the questions come from: the store itself. At each cut `c` a generator reads the store as of `c`
and registers questions about events after `c`, each with a resolver that reads the store as of a
later cut `c' > c` and answers it. Four generators, each a function of the snapshot at the cut
(limits L7: the versions alive and the relations among them) and nothing else:

| generator | the question at cut `c` | resolved at `c'` by | what it exercises |
|---|---|---|---|
| link | will identity `a` cite identity `b` by `c'`? (for `a`, `b` not yet linked, sampled with the same rule for every arm) | the relation at `c'` | the citation graph; link prediction (Liben-Nowell and Kleinberg 2007) on the store's own history |
| supersession | will the note `a` be superseded by `c'`? | the version chain at `c'` | the version chains; the castles' forecasts (dn-prediction-castles PC-1) |
| version | will identity `a` have a new version by `c'`? | `version_seq` at `c'` | the velocity's first datum (dn-graph-dynamics §2.1) |
| confirmation | will a source arriving by `c'` confirm the answer `x` the store gives at `c`? (the answer's truth condition stated at `c`) | a resolver over the sources landed by `c'` | the answers themselves, against evidence the store did not have |

The selection rule, which questions enter, depends on no arm (G3): a seeded sample of pairs and
identities at each cut, its parameters in the protocol. Each question carries a family (the
generator) and a cluster (the identity or the pair it turns on: two questions about one note are
one observation, G1). The close time is `c'`, and a prediction recorded at or after it is late and
excluded (G5). `[INFERENCE, falsifier SAF-1]`

### 3.2 The arms are configurations

An arm is a configuration of the system: a set `S` of the sources, context windows and analysis
tools it may use, drawn from the full set `N`. The arms of a run are the full system `N` and the
ablations `N ∖ {i}` for each `i` the run attributes to; the Shapley reading (§3.4) adds the
configurations its sampled orderings run through. A source is a stratum or an origin the store
reads from; a context window is a depth of the cut the arm may read as of (dn-capability-scope's
windows: the arm with the narrow window sees less history); an analysis tool is a verb or a lens of
the query algebra the arm may call (`diffuse`, `near`, the projections when GD-1 lands). Every
arm is pinned (G6) and sees the same questions in the same rounds. The reference arm is the base
rate: the family's frequency of yes over the questions resolved before the cut, which no source
and no tool informs; the null arm is its copy (F-1). `[INFERENCE, falsifier SAF-2]`

What an arm is not: a different model. The configurations differ in what the system may read and
call, not in who answers; the model, the prompt and the tools are in every arm's `config` digest,
and a change to them is a new variant (G6).

### 3.3 The currency is the log-score advantage

Each arm's prediction on a pair is scored by Brier and by the clipped log score (G5). The
**value of a configuration** `v(S)` is its mean log-score advantage over the reference arm on the
pairs it scored, read at the protocol's `N` clusters and nowhere else (the read-once rule): on one
pair, `log L(p, o) − log L(r, o)`; over the pairs, the mean. Three reasons it is the currency:

- it is additive over pairs, so the attribution of §3.4, which needs a value function on
  configurations, has one that sums the way the questions do;
- its cumulative form is exactly the log growth of the proportional stake against the reference
  (GRW-1, `Palace/Growth.lean`), so the growth readout (G8) and the attribution read one number;
  a path to `N×` exists iff the cumulative advantage reaches `log N` (GRW-4);
- its expectation under a truth `q` is `KL(q‖r) − KL(q‖p)` (GRW-2): an arm's value is positive
  iff its forecasts are closer to the truth than the base rate, which is what an improvement means.

The decision rule stays Brier's (G5, the primary comparison, its interval and the three outcomes
at `N`); the currency serves the readings. `[DERIVED from GRW-1, GRW-2, GRW-4]`

### 3.4 Attribution: the two readings, and when they disagree

**Per ablation: the sign-flip test.** For each `i`, the primary or a secondary comparison pairs the
full arm `N` against `N ∖ {i}` on the pairs both scored and tests the pair-weighted mean of the
differences by the cluster-level sign-flip randomization test (G5's `signflip` method: exact under
exchangeability within clusters, enumerated when the clusters are few, Holm-corrected across the
secondaries). Its estimand is `v(N) − v(N ∖ {i})`: the **leave-one-out** attribution,
`loo` in `Scale/Defs.lean`.

**Over the sources: the Shapley value.** With `v` on every configuration, the Shapley value of `i`
is the average over every ordering of the sources of `i`'s marginal contribution to the sources
before it (`shapley`). It is the attribution the question asks for, by SCL-3:

- SCL-3 the Shapley value is efficient (`shapley_efficient`: the marginals telescope along each
  ordering, `sum_marginal_pred`), symmetric (`shapley_symmetric`: the swap of two sources is a
  bijection on orderings, `swapOrd`, `pred_swap`), attributes nothing to a null source
  (`shapley_nullPlayer`) and is additive (`shapley_additive`). `[THEOREM]`
- It is the only attribution with the four. Every score is the combination of the unanimity
  games with its Harsanyi dividends as coefficients, `v = Σ_T c_T u_T` with
  `c_T = Σ_{S ⊆ T} (−1)^{|T|−|S|} v(S)` (`sum_harsanyi_unanimity`, through the inclusion and
  exclusion sum between two sets, `sum_powerset_filter_neg_one_pow`); the null, symmetry and
  efficiency axioms pin an attribution on each scaled unanimity game at `c / |T|` for the members
  of `T` and `0` elsewhere (`attribution_unanimity`); additivity over the sum gives the dividend
  formula `ψ v i = Σ_{T ∋ i} c_T / |T|` for any attribution with the four
  (`attribution_eq_sum_harsanyi`), so any two agree (`eq_shapley_of_axioms`). `[THEOREM]`
- Leave-one-out agrees with the Shapley value on scores with constant marginals, where every
  source adds the same whatever the others (`loo_eq_shapley_of_marginal_const`). `[THEOREM]`
- And disagrees in general. Two sources, either sufficient (`Witness.redundant`: every nonempty
  configuration scores `1`): each has Shapley value one half (`shapley_redundant`, by symmetry
  and efficiency) and leave-one-out `0` (`loo_redundant`), and the leave-one-out values do not sum
  to what the two carry (`loo_confirms_nothing`). `[THEOREM]` This is the shape of the Rayleigh
  family's `loo_confirms_nothing`: a rise carried by two redundant paths confirms neither.

The reading, then. The sign-flip test per ablation answers whether source `i` is **necessary**:
whether removing it from the full system costs anything at the bar. It answers nothing about
redundant sources, which each read zero. The Shapley value answers what share of the system's
value source `i` **carries**, counting a redundant pair as each carrying half. Both are reported;
where they disagree, the disagreement is the finding: the sources are redundant, and the store
holds the same evidence twice. `[DERIVED from SCL-3]`

**The cost, and sampling.** The Shapley value needs `v` on `2^n` configurations for `n` sources,
each an arm that forecasts every question. For `n ≤ 5` the arms are enumerated. Beyond that, the
permutation-sampling estimator: sample `m` orderings uniformly (seeded, in the protocol), register
the configurations each ordering runs through as arms (the amendment that adds arms, G3, before
any prediction on them), and average `i`'s marginal contributions over the sampled orderings. The
estimate is unbiased, its variance is `s_i² / m` for `s_i²` the variance of `i`'s marginal
contribution across orderings, and its standard error `s_i / √m` is reported beside the estimate
(Castro, Gómez and Tejada 2009; Ghorbani and Zou 2019's Monte Carlo estimator with the same
shape). The sampling stops, in the sense of fixing `m`, when `s_i / √m` is below the bar `δ` of
the protocol for every `i`, or at the `m` the protocol declares; `m` is fixed before the first
prediction like `N`. Each sampled ordering costs `n` configurations, so the run scores `m · n`
arms plus the ablations, and that is the price of attribution over many sources. `[INFERENCE,
falsifier SAF-3]`

### 3.5 SCL-4 Power

The number of independent resolved units the loop needs is the ledger's `required_clusters`,
and its derivation is the normal approximation, stated here and not formalized. Let `d_k` be the
mean paired difference (Brier, or the advantage) over the pairs of cluster `k`, for `K`
independent clusters, with mean `Δ` and standard deviation `s` across clusters. The test
statistic is the cluster mean `d̄`, approximately `N(Δ, s²/K)` for `K` large. The two-sided test
at level `α` rejects `Δ = 0` when `|d̄| > z_{1−α/2} s / √K`. At a true effect `Δ > 0` the
probability of rejecting is `P(Z > z_{1−α/2} − Δ√K / s)` up to the negligible other tail, and
that is at least `1 − β` exactly when `Δ√K / s ≥ z_{1−α/2} + z_{1−β}`, that is

```
K ≥ ((z_{1−α/2} + z_{1−β}) · s / Δ)²,
```

the form of `required_clusters(sd, delta, alpha, power)`, rounded up, with `s` read blinded from
the pilot (G5). With `s = 0.08` and `Δ = 0.02` at `α = 0.05` and power `0.8`, `K = 126`; at
`Δ = 0.01`, `503`. `[DERIVED; the standard two-sided sample-size formula]`

Two things SCL-1 adds to it. The units must be independent, and the sign-flip test's note says
what dependence across clusters costs: an effective `K` below the count. SCL-1's effective sample
size is the same statement in the time direction: questions registered within one relaxation
time of each other, about a store whose state has not relaxed between them, are one observation,
so a window of `T_c` cuts yields at most about `T_c γ / 2` independent units of a macro
observable, and the loop's `K` is bounded by the store's own mixing. A loop that registers many
questions per cut on a slowly mixing store counts clusters it does not have; the cluster rule (one
cluster per identity or pair) catches the dependence within a cut, and the relaxation time is the
rule for dependence across cuts: **the round spacing is at least a relaxation time**. `[DERIVED
from SCL-1 and G5]`

### 3.6 The loop, in five lines

```
at each cut c:                         # a round, spaced at least a relaxation time apart
  register  Q_c  ← generators(store as of c), seeded; families, clusters, close times c' > c
  forecast  for each arm S (N, every N∖{i}, the sampled chain configurations): p_S(q) for q ∈ Q_c
  resolve   every q with close time ≤ c, by its resolver over the store as of c; late ones excluded
  attribute at N clusters, once: v(S) per arm; loo_i by the sign-flip test; shapley_i with its s_i/√m
```

Every line reads or writes the ledger and nothing else; the ledger's chain, its clock and the
protocol's bar are the ledger's (G3, G4). What the loop adds to `eval/predictions/` when it is
built: the generators and resolvers over a store as of a cut, the configuration arms, and the two
attribution readings; §6 says where each lives.

## 4. Datasets

The thresholds need an evolving graph with dates, large enough that its spectrum has
concentrated and its history long enough for many relaxation times; the loop needs events after a
cut that a snapshot before it does not contain. Five open corpora, each licensed for this use,
with what each exercises; the sibling study, #76, fetches the first:

| corpus | licence | scale | what it exercises |
|---|---|---|---|
| OpenAlex works, with `publication_date` and `referenced_works` | CC0 1.0 | hundreds of millions of works and on the order of a billion dated citation links (OpenAlex's own counts; the study records the figures of what it fetched, one concept at a time through the API's `cursor` paging) | a dated citation graph: the link generator at every cut; the gap and the eigengaps of a growing graph against the minimum degree (§2.3); concept clusters as a partition (DYN-5) |
| Wikipedia, articles with revision histories and links (the dumps) | CC BY-SA 4.0 (text; the revision metadata with it) | millions of articles, more than a billion revisions across the English edition | version chains: the supersession and version generators; links that appear and are severed; a velocity with many generations (dn-graph-dynamics §2.1) |
| commit and issue histories of public repositories | each repository's own licence for its content; the platform's terms for the metadata; mirror the metadata only | millions of repositories; on a single large repository, hundreds of thousands of commits and issues | commits as supersessions on a path's chain (the ingress's version chains, ING-7); issues citing commits as a dated relation; many sources (the repositories) for the confirmation generator |
| arXiv metadata through OAI-PMH | CC0 1.0 for the metadata | more than two million papers, each with its dated versions `v1, v2, …` | version chains with dates and no citations: the version generator on its own; a feed that the loop can register from, round by round, as the papers arrive |
| ALFRED, archival economic series with vintages | the St. Louis Fed's terms of use: free for use with attribution for most series, some third-party series restricted | hundreds of thousands of series in FRED, the vintages of the ones ALFRED archives, many decades of them | a value behind a fixed identity re-recorded at each vintage: exactly the box and the pointer of dn-graph-dynamics §2.1; the velocity of a value with its revisions; a confirmation generator whose later source is the next vintage |

What they have in common: every edge, version or value carries a date the corpus assigned, so a
cut is a date and a snapshot as of a cut is reproducible; the loop's forward-only rule (G2) holds
against a corpus that already holds the future only if the arms read snapshots as of the cut and
nothing later, which the instance enforces by what it lands (§6). `[INFERENCE, falsifier SAF-4]`

**How far below the thresholds a small private corpus is.** The live instance, measured read-only
on 2026-11-04 and 2026-11-07 (dn-graph-dynamics §2.1, §5.4): a backbone of `38` notes and `38`
edges, a relation graph of `20` edges on `12` notes, `29` identities with one version each,
recorded within one second of one rebuild. Against each threshold:

- §2.3: `N = 38`, `log N ≈ 3.6`; the backbone's mean degree is `2` and its minimum degree `1`,
  so the minimum degree is below `C log N` for any `C ≥ 1/3`, and the fluctuation scale
  `√(log N / d_min)` is about `1.9` at `d_min = 1`, above the whole range `[0, 2]` of the normalized
  Laplacian's spectrum. Every measured gap is noise of the sample.
- SCL-1 and SCL-2: there is one cut, so the window is zero relaxation times whatever `γ` is; no
  time average exists.
- SCL-4: there are no resolved questions, so `K = 0` against a required `126` at the ledger's
  pilot figures.
- The loop: one generation, so the supersession and version generators have nothing to ask, and
  the link generator's `38` edges would be exhausted in a round.

So the small corpus is below every threshold by two to four orders of magnitude, and nothing
measured on it about its macro regime is evidence. This is the plain reason the study runs on a
public corpus: the first open corpus in the table has a minimum degree, a history of decades of
cuts, and a link generator that never runs dry. The sibling study's first fetch is one OpenAlex
concept, and its report, when it lands, replaces the figures of this paragraph with measured ones.
`[DERIVED]`

## 5. The recipe

1. **Measure.** At a sequence of cuts of the corpus, the Laplacian's gap `γ` and the eigengaps
   `g_k` near the candidate cuts `k` (the normalized Laplacian too, for §2.3), the minimum degree
   `d_min`, and the sizes `N`. Report each as a function of the cut.
2. **Size.** From `γ`, the window `T_c ≥ 2σ²/(γ δ²)` a macro observable needs and the effective
   samples a history of `T_c` carries; from `g_k`, the time scale `1/g_k` at which a `k`-mode
   description is legitimate; from `d_min` and `N`, whether the spectrum has concentrated; from the
   pilot's spread, `K`.
3. **Grow.** Fetch until the thresholds are exceeded: `d_min ≫ log N / γ²`, a history of many
   relaxation times, enough clusters for `K`. Each fetch is a dated extension, so growing is adding
   cuts, not replacing the corpus.
4. **Run.** The loop of §3.6 under a protocol written first: the generators, the arms (the full
   system, the ablations, the sampled chain configurations with `m` fixed), the primary comparison
   and the bar, the round spacing at a relaxation time.
5. **Attribute.** At `N` clusters, once: the sign-flip reading per ablation and the Shapley
   reading over the sources with its standard error, and the growth readout; where the two
   readings disagree, name the redundancy.

## 6. Where it lives

The machinery is generic and belongs in the palace: the generators and resolvers are functions of
a store as of a cut, written over the sentence algebra (`as of c`, the version chains, the
relation) and so over any store; the ablation arms are grants (dn-capability-scope: an arm is a
scope that names what it may read and call); the attribution readings are functions of the ledger.
They extend `eval/predictions/` (G5's scorer and G8's readout) and nothing under `core/` imports
them (BL-4, machinery not corpus). The Lean theorems are design theorems here (Palace and
PalaceTest, no Spec rows) and enter `docs/LAWS.md` as rows when that code relies on them
(dn-mathematical-foundations §2.4).

A corpus belongs in its own instance. A public corpus of millions of nodes is not the private
store, must not land in its strata, and runs its loop against its own ledger with its own anchored
head. Instance identity (`docs/tracks/deployed-instances.md` DI-2: an `[instance]` id in the
schema and the namespaces derived from it, the one overlay a named instance reads, its own levers
path) is what makes that safe: the study's instance cannot write the private store's knobs or read
its vault, and the forward-only rule holds because the instance lands snapshots as of a cut and
nothing after it. `[INFERENCE, falsifier SAF-5]`

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| SA-a | the reference arm | the family's base rate over the questions resolved before the cut | a family in which the base rate is itself informative (a trend); then a fixed baseline |
| SA-b | the Shapley estimator | permutation sampling with `m` fixed in the protocol, the standard error reported | a run whose `s_i / √m` is never under `δ` at an `m` the budget allows; then the stratified or the antithetic estimator, pre-registered |
| SA-c | the round spacing | one relaxation time, `1/γ` measured at the previous cut | a corpus whose `γ` drifts across cuts by more than its concentration band |
| SA-d | the normalized or the combinatorial Laplacian for the concentration reading | the normalized one, where the cited theorems hold | a measured spectrum in which the two give different thresholds |
| SA-e | the first corpus | OpenAlex, one concept (the sibling study's choice) | the study's report |

## Falsifiers

- **SAF-1 (a generator leaks):** a question whose resolver reads anything an arm could see at
  the cut, or a family in which the null arm shows skill (F-1, G7's leakage family). Then the
  generator is not a function of the future and is withdrawn.
- **SAF-2 (an ablation is not an ablation):** an arm `N ∖ {i}` whose `config` digest, or whose
  trace, shows a read of source `i` or a call of tool `i`. The grant did not enforce the
  configuration; the arm's predictions are voided (F-4).
- **SAF-3 (the two readings disagree without redundancy):** a source whose leave-one-out and
  Shapley readings differ at the bar while every configuration's marginal for it is constant
  within its interval. SCL-3 says that cannot happen over the exact values; it happening on the
  estimates is a sampling defect: `m` too small, or the configurations not pinned.
- **SAF-4 (a corpus holds its future):** an arm whose snapshot as of a cut contains an edge,
  version or value dated after the cut. The landing is not a snapshot; the run is void.
- **SAF-5 (an instance writes outside itself):** a study instance that writes the private
  store's levers, strata or ledger. DI-2 is not complete; the study does not run until it is.
- **SAF-6 (the thresholds mispredict):** a corpus whose measured gaps keep moving above
  `d_min ≫ log N / γ²`, or a time average that converges in a window far shorter than `1/γ`. The
  first says the concentration law's shape on real data differs from the independent-edge one,
  which is the sibling study's finding to report; the second cannot happen over the exact
  diffusion (SCL-1 is a theorem) and on sampled readings says the observable lies on fast modes
  only.

## Open questions

- The confirmation generator needs a truth condition stated at the cut for an answer the store
  gives; which answers have one? Those the sentence algebra returns as `Inv` with a witness are
  the first candidates.
- Shapley over the sources treats a context window and an analysis tool as players too, so a
  configuration mixes kinds. Is one value function over mixed players the right reading, or one
  attribution per kind with the others fixed at the full set?
- Which `k` does the macro description keep: the eigengap's largest, or the one the application
  names? SCL-2 sizes the time for any `k`; the precedent decides the default.
- Does the round spacing follow the gap of the graph or of the quotient the arms read at (DYN-5:
  the quotient's gap is never lower)?

## Cross-references

**Formal (this branch):** `formal/Palace/Scale/Defs.lean` (`timeAverage`, `Ordering`, `pred`,
`marginal`, `shapley`, `Attribution`, `Efficient`, `NullPlayer`, `Symmetric`, `Additive`,
`unanimity`, `harsanyi`, `loo`); `formal/Palace/Scale.lean` (SCL-1 `timeAverage_dotProduct_mode`,
`timeAverage_energy_le`, `lazy_timeAverage_energy_le`, `sum_pow_le_inv_one_sub`,
`lazy_timeAverage_energy_le_window`, `lazy_timeAverage_precision`; SCL-2
`modeProj_dotProduct_mode`, `heat_energy_ge`, `heat_energy_eq`, `heat_modeProj_energy_ge`,
`scale_separation`, `scale_separation_time`, `eigenvalues_one`, `no_gap_no_separation`,
`no_gap_no_time`, `pow_energy_ge`, `scale_separation_pow`; SCL-3 `chain`, `pred_symm`,
`insert_pred_symm`, `sum_marginal_pred`, `shapley_efficient`, `shapley_nullPlayer`,
`marginal_add`, `shapley_additive`, `swapOrd`, `pred_swap`, `marginal_swap`,
`shapley_symmetric`, `unanimity_insert_of_notMem`, `attribution_unanimity_notMem`,
`attribution_unanimity_mem`, `sum_attribution_unanimity`, `attribution_unanimity`,
`sum_powerset_filter_neg_one_pow`, `sum_harsanyi_unanimity`, `eq_sum_harsanyi_smul_unanimity`,
`additive_zero`, `additive_sum`, `attribution_eq_sum_harsanyi`, `shapley_eq_sum_harsanyi`,
`eq_shapley_of_axioms`, `loo_eq_marginal`, `shapley_eq_of_marginal_const`,
`loo_eq_shapley_of_marginal_const`, `Witness.redundant`, `Witness.shapley_redundant`,
`Witness.loo_redundant`, `Witness.loo_confirms_nothing`); `formal/PalaceTest/Scale.lean` (seeds
350 to 367); the families cited: `Palace/Dynamics.lean` (DYN-4, DYN-6), `Palace/Growth.lean`
(GRW-1 to GRW-6), `Palace/Rayleigh.lean` (`loo_confirms_nothing`).

**Code (read, unchanged):** `eval/predictions/ledger.py` (G1 to G4, G6); `eval/predictions/scoring.py`
(G5: `brier`, `log_loss`, `pairs`, `cluster_bootstrap`, `cluster_signflip`,
`required_clusters`, `pilot`; G8's `growth`);
`core/stores/versions.py` (the chains the generators read); `eval/scale/fetch_openalex.py` (the
sibling study's fetcher, in #76).

**Design:** dn-graph-dynamics §2.1 (the box and the pointer), §5.1 (the modes), §5.3 (mixing),
§5.4 (no thermodynamic limit; the evolution's mixing a hypothesis); dn-prediction-ledger G1 to
G8, F-1 to F-4; scored-beliefs BL-1, BL-3, BL-4, BL-5; dn-prediction-castles PC-1, PC-3;
dn-capability-scope (arms as grants); docs/tracks/deployed-instances.md DI-2;
dn-mathematical-foundations §2.4 (the ladder); `papers/2026-11-07-scale-and-attribution/paper.tex`
(the article, with the references).

**Cited:** Oliveira, "Concentration of the adjacency matrix and of the Laplacian in random graphs
with independent edges" (2009); Chung and Radcliffe, "On the spectra of general random graphs"
(2011); Aldous and Fill, "Reversible Markov chains and random walks on graphs", Chapter 4; Levin
and Peres, "Markov chains and mixing times", 2nd ed., Chapter 12; Shapley, "A value for n-person
games" (1953); Castro, Gómez and Tejada, "Polynomial calculation of the Shapley value based on
sampling" (2009); Ghorbani and Zou, "Data Shapley" (ICML 2019); Jia et al., "Towards efficient
data valuation based on the Shapley value" (AISTATS 2019); Liben-Nowell and Kleinberg, "The
link-prediction problem for social networks" (2007).
