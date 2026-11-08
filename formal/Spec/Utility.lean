module

public import Palace.Utility.Defs

/-!
# The utility field: the statements

UTL-1 to UTL-6 (`docs/LAWS.md`, XV). The statements are over the model of
`Palace/Utility/Defs.lean`: a field over the sites of a graph, its tick (decay toward the
baseline, then the saturated increment), its box, arcs, the nudge of the structural weights by
the field with its margin, the stationary distribution of the walk on a weight matrix, total
variation, and the closed loop. Over any linearly ordered field where the law is algebraic, over
`ℝ` where it needs a logarithm, a metric or a spectrum. What they leave out: the float64
arithmetic of the simulator, and any store, since no code in the store computes the field.

These are the laws of `Palace/Utility.lean` as the ledger cites them, each with its proof left
as `sorry`. `lake comparator` checks that the `Palace` library proves each one exactly as stated
here, from the standard axioms alone.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Utility

section Box

variable {ι K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K]

/-- **UTL-1** One tick keeps the field in its box: the decay toward the baseline and the
saturated increment together never leave `[b − c/lam, b + c/lam]`. -/
theorem step_mem_box {b lam c : K} (hlam : 0 < lam) (hlam1 : lam ≤ 1) (hc : 0 ≤ c)
    {u : ι → K} (hu : InBox b lam c u) (use : ι → K) : InBox b lam c (step b lam c u use) :=
  sorry

/-- **UTL-1** The field stays in its box along any log of uses. -/
theorem evolve_mem_box {b lam c : K} (hlam : 0 < lam) (hlam1 : lam ≤ 1) (hc : 0 ≤ c)
    {u₀ : ι → K} (hu : InBox b lam c u₀) (log : List (ι → K)) :
    InBox b lam c (evolve b lam c u₀ log) :=
  sorry

/-- **UTL-1** The floor is positive when `c < b · lam`: every effective weight stays positive, so
no edge is erased by the field. -/
theorem floor_pos {b lam c : K} (hlam : 0 < lam) (h : c < b * lam) : 0 < floor b lam c :=
  sorry

omit [IsStrictOrderedRing K] in
/-- **UTL-4** The field after a log is a function of the log alone, read left to right: appending
uses continues the fold from where the log left it. -/
theorem evolve_append (b lam c : K) (u₀ : ι → K) (l₁ l₂ : List (ι → K)) :
    evolve b lam c u₀ (l₁ ++ l₂) = evolve b lam c (evolve b lam c u₀ l₁) l₂ :=
  sorry

end Box

section Decay

variable {ι K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K]

/-- **UTL-2** The field left alone decays geometrically to the baseline:
`u_n = b + (1 − lam)^n (u₀ − b)`. -/
theorem idle_apply {b lam c : K} (hc : 0 ≤ c) (u : ι → K) (n : ℕ) (e : ι) :
    idle b lam c u n e = b + (1 - lam) ^ n * (u e - b) :=
  sorry

/-- **UTL-2** From inside the box, an idle site is within `(1 − lam)^n · c/lam` of the baseline
after `n` ticks. -/
theorem idle_sub_le {b lam c : K} (hlam1 : lam ≤ 1) (hc : 0 ≤ c)
    {u : ι → K} (hu : InBox b lam c u) (n : ℕ) (e : ι) :
    |idle b lam c u n e - b| ≤ (1 - lam) ^ n * (c / lam) :=
  sorry

/-- **UTL-2** Arcs fade: once `(1 − lam)^n · c/lam < a`, an idle site is no arc of height `a`. -/
theorem not_isArc_idle {b lam c : K} (hlam1 : lam ≤ 1) (hc : 0 ≤ c)
    {u : ι → K} (hu : InBox b lam c u) {a : K} {n : ℕ} (hn : (1 - lam) ^ n * (c / lam) < a)
    (e : ι) : ¬ IsArc b a (idle b lam c u n) e :=
  sorry

/-- **UTL-2** Arcs form: a site held at the cap for `n` ticks from at least the baseline is an arc
of height `a` once `(c/lam)(1 − (1 − lam)^n) ≥ a`. -/
theorem isArc_steady {b lam c : K} (hlam : 0 < lam) (hlam1 : lam ≤ 1) (hc : 0 ≤ c)
    {u : ι → K} {e : ι} (hu : b ≤ u e) {a : K} {n : ℕ}
    (hn : a ≤ c / lam * (1 - (1 - lam) ^ n)) : IsArc b a (steady b lam c c u n) e :=
  sorry

end Decay

section DecayReal

variable {ι : Type*}

/-- **UTL-2** The declared window: once `lam · n ≥ log (c / (lam ε))`, an idle site is within `ε`
of the baseline. The window is the forgetting rate's reciprocal times the log of the box's height
over the tolerance. -/
theorem idle_window {b lam c : ℝ} (hlam : 0 < lam) (hlam1 : lam ≤ 1) (hc : 0 < c)
    {u : ι → ℝ} (hu : InBox b lam c u) {ε : ℝ} (hε : 0 < ε) {n : ℕ}
    (hn : Real.log (c / (lam * ε)) ≤ lam * n) (e : ι) : |idle b lam c u n e - b| ≤ ε :=
  sorry

end DecayReal

section NudgePointwise

variable {V K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K]

omit [LinearOrder K] [IsStrictOrderedRing K] in
/-- **UTL-4** At the baseline the effective weights are the structural ones: switching the field
off recovers the backbone exactly. -/
theorem nudge_baseline (η b : K) (A : Matrix V V K) : nudge η b A (fun _ _ ↦ b) = A :=
  sorry

/-- **UTL-3** The nudge keeps the support: with the margin below one, an effective weight is zero
exactly when the structural weight is. No edge is erased and none is created. -/
theorem nudge_eq_zero_iff {η b lam c : K} (hη : 0 ≤ η) (hθ : margin η lam c < 1)
    {A : Matrix V V K} {u : V → V → K} {i j : V}
    (hu : floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) :
    nudge η b A u i j = 0 ↔ A i j = 0 :=
  sorry

/-- **UTL-5** The field reorders only within the margin: two structural weights whose ratio
exceeds `(1 + θ)/(1 − θ)` keep their order under every field state in the box. -/
theorem nudge_lt_nudge_of_margin {η b lam c : K} (hη : 0 ≤ η) {A : Matrix V V K}
    {u : V → V → K} {i j k l : V} (hkl : 0 ≤ A k l) (hij : 0 ≤ A i j)
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c)
    (h : (1 + margin η lam c) * A k l < (1 - margin η lam c) * A i j) :
    nudge η b A u k l < nudge η b A u i j :=
  sorry

end NudgePointwise

section NudgeSums

variable {V K : Type*} [Fintype V] [Field K] [LinearOrder K] [IsStrictOrderedRing K]

/-- **UTL-3** No hub: a node's stationary mass under the nudged walk is at most
`(1 + θ)/(1 − θ)` times its structural mass, whatever the field's state in its box. -/
theorem statDist_nudge_le {η b lam c : K} (hη : 0 ≤ η) (hlam : 0 < lam) (hc : 0 ≤ c)
    (hθ : margin η lam c < 1) {A : Matrix V V K} (hA : ∀ i j, 0 ≤ A i j)
    (hvol : 0 < ∑ j, degree A j) {u : V → V → K}
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) (i : V) :
    statDist (nudge η b A u) i ≤ (1 + margin η lam c) / (1 - margin η lam c) * statDist A i :=
  sorry

/-- **UTL-3** The reinforced walk's stationary distribution stays within `θ/(1 − θ)` of the
structural walk's in total variation, whatever the field's state in its box: the field cannot
collapse the walk onto a few hubs. -/
theorem tv_statDist_nudge_le {η b lam c : K} (hη : 0 ≤ η) (hlam : 0 < lam) (hc : 0 ≤ c)
    (hθ : margin η lam c < 1) {A : Matrix V V K} (hA : ∀ i j, 0 ≤ A i j)
    (hvol : 0 < ∑ j, degree A j) {u : V → V → K}
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) :
    tv (statDist (nudge η b A u)) (statDist A) ≤ margin η lam c / (1 - margin η lam c) :=
  sorry

end NudgeSums

section Spectral

variable {V : Type*} [Fintype V] [DecidableEq V]

/-- **UTL-5** The bounded nudge: the field moves the Laplacian's quadratic form by at most `θ`
times the structural form, `|xᵀ (L' − L) x| ≤ θ xᵀ L x`. -/
theorem abs_dotProduct_lap_sub_le {η b lam c : ℝ} (hη : 0 ≤ η) {A : Matrix V V ℝ} (hA : A.IsSymm)
    (hA0 : ∀ i j, 0 ≤ A i j) {u : V → V → ℝ} (hus : ∀ i j, u i j = u j i)
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) (x : V → ℝ) :
    |x ⬝ᵥ ((lap (nudge η b A u) - lap A) *ᵥ x)| ≤ margin η lam c * (x ⬝ᵥ (lap A *ᵥ x)) :=
  sorry

/-- **UTL-5** The nudged Laplacian lies within `2 θ d` of the structural one as a quadratic form,
`d` a bound on the degrees: the hypothesis of Weyl's inequality counted (SPC-3). -/
theorem near_lap_nudge {η b lam c : ℝ} (hη : 0 ≤ η) (hlam : 0 < lam) (hc : 0 ≤ c)
    {A : Matrix V V ℝ} (hA : A.IsSymm) (hA0 : ∀ i j, 0 ≤ A i j) {d : ℝ} (hd : ∀ i, degree A i ≤ d)
    {u : V → V → ℝ} (hus : ∀ i j, u i j = u j i)
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) :
    Gap.Near (Matrix.toEuclideanLin (lap A)) (Matrix.toEuclideanLin (lap (nudge η b A u)))
      (2 * margin η lam c * d) :=
  sorry

/-- **UTL-5** Weyl's inequality counted for the nudge, one way: a Laplacian eigenvalue at most
`t − 2θd` is still at most `t` under the nudge. -/
theorem count_lap_nudge_sub_le {η b lam c : ℝ} (hη : 0 ≤ η) (hlam : 0 < lam) (hc : 0 ≤ c)
    {A : Matrix V V ℝ} (hA : A.IsSymm) (hA0 : ∀ i j, 0 ≤ A i j) {d : ℝ} (hd : ∀ i, degree A i ≤ d)
    {u : V → V → ℝ} (hus : ∀ i j, u i j = u j i)
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) (t : ℝ) :
    Gap.count (isSymmetric_toEuclideanLin_lap hA) finrank_euclideanSpace
        (t - 2 * margin η lam c * d) ≤
      Gap.count (isSymmetric_toEuclideanLin_lap (isSymm_nudge (η := η) (b := b) hA hus))
        finrank_euclideanSpace t :=
  sorry

/-- **UTL-5** Weyl's inequality counted for the nudge, the other way: an eigenvalue at most `t`
under the nudge was at most `t + 2θd` on the backbone. So every eigenvalue moves by at most
`2θd`, and the structural spectrum is recovered when the field is removed. -/
theorem count_lap_nudge_le_add {η b lam c : ℝ} (hη : 0 ≤ η) (hlam : 0 < lam) (hc : 0 ≤ c)
    {A : Matrix V V ℝ} (hA : A.IsSymm) (hA0 : ∀ i j, 0 ≤ A i j) {d : ℝ} (hd : ∀ i, degree A i ≤ d)
    {u : V → V → ℝ} (hus : ∀ i j, u i j = u j i)
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) (t : ℝ) :
    Gap.count (isSymmetric_toEuclideanLin_lap (isSymm_nudge (η := η) (b := b) hA hus))
        finrank_euclideanSpace t ≤
      Gap.count (isSymmetric_toEuclideanLin_lap hA) finrank_euclideanSpace
        (t + 2 * margin η lam c * d) :=
  sorry

end Spectral

section Loop

variable {ι : Type*} [Fintype ι]

/-- **UTL-6** The closed loop is a contraction of the sup metric when the use's gain in the field
is below the forgetting rate: `dist (loop u) (loop v) ≤ (1 − lam + K) dist u v`. -/
theorem loop_dist_le {b lam c : ℝ} (hlam1 : lam ≤ 1)
    {F : (ι → ℝ) → ι → ℝ} {Kg : ℝ} (hK : 0 ≤ Kg) (hF : ∀ u v, dist (F u) (F v) ≤ Kg * dist u v)
    (u v : ι → ℝ) :
    dist (loop b lam c F u) (loop b lam c F v) ≤ (1 - lam + Kg) * dist u v :=
  sorry

/-- **UTL-6** With the gain below the forgetting rate the loop has exactly one stationary field:
no self-sustaining state beside it. -/
theorem loop_existsUnique_fixedPoint {b lam c : ℝ} (hlam1 : lam ≤ 1)
    {F : (ι → ℝ) → ι → ℝ} {Kg : ℝ} (hK : 0 ≤ Kg) (hKl : Kg < lam)
    (hF : ∀ u v, dist (F u) (F v) ≤ Kg * dist u v) :
    ∃! u : ι → ℝ, loop b lam c F u = u :=
  sorry

end Loop

end Palace.Utility
