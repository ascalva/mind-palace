module

public import Palace.Dynamics
public import Palace.Gap
public import Palace.Utility.Defs

/-!
# The utility field

The laws of `docs/design-notes/dn-utility-field.md`, proved before any code computes the field.
The field is a value per site (node, edge, declared path) that each tick decays toward a baseline
`b` by the rate `lam` and then receives this tick's use, clamped to `[−c, c]`; the structural
weights are nudged by the factor `1 + η (u − b)`, whose margin is `θ = η c / lam`.

* UTL-1, boundedness: the box `[b − c/lam, b + c/lam]` is invariant under every tick and every
  log of uses, its floor is positive when `c < b · lam`, and it is the least such box.
* UTL-2, decay: an idle site returns to the baseline geometrically, within `ε` once
  `lam · n ≥ log (c / (lam ε))`; arcs fade on that window and form at a heat spot held at the cap.
* UTL-3, no localization: the nudge keeps the support exactly (no edge erased, none created), a
  node's stationary mass under the nudged walk is at most `(1 + θ)/(1 − θ)` times its structural
  mass, the two stationary distributions are within `θ/(1 − θ)` in total variation, and a
  spectral gap `γ` of the backbone is a gap `(1 − θ) γ` of the nudged graph.
* UTL-4, derivation: the field after a log is the fold of the ticks over the log, and at the
  baseline the effective weights are the structural ones.
* UTL-5, the bounded nudge: the field moves the Laplacian's quadratic form by at most `θ` times
  the structural form, so the nudged Laplacian is within `2 θ d` of the structural one and Weyl's
  counts (SPC-3) bound every eigenvalue's move; two weights whose ratio exceeds
  `(1 + θ)/(1 − θ)` keep their order under every field state.
* UTL-6, no self-reinforcing loop: when this tick's use is a `K`-Lipschitz function of the field
  with `K < lam`, the closed loop is a contraction of the sup metric by `1 − lam + K`, so it has
  one stationary field and the iterates converge to it geometrically; with `K ≥ lam` the loop
  `use = K (u − b)` holds the ceiling fixed beside the baseline.
* The controls: reinforcement without decay exceeds every bound; in the two-site mean field a
  superlinear exponent drives the ratio of the sites apart, a linear one holds it and a sublinear
  one draws it to one; the greedy walk, which always takes its heaviest edge and reinforces it,
  never leaves two nodes of a three-node path, so its empirical measure gives the far node none of
  the quarter the structural walk gives it and stays at least `1/8` from the structural stationary
  distribution in total variation.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Utility

/-! ### UTL-1 Boundedness: the field stays in its box -/

section Box

variable {ι K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K]

omit [IsStrictOrderedRing K] in
/-- The saturated increment is at least `−c`. -/
theorem neg_le_sat (c x : K) : -c ≤ sat c x := le_max_left _ _

/-- The saturated increment is at most `c`, for `0 ≤ c`. -/
theorem sat_le {c : K} (hc : 0 ≤ c) (x : K) : sat c x ≤ c :=
  max_le (by linarith) (min_le_left _ _)

/-- No use, no increment. -/
theorem sat_zero {c : K} (hc : 0 ≤ c) : sat c 0 = 0 := by
  unfold sat
  rw [min_eq_right hc, max_eq_right (by linarith)]

omit [IsStrictOrderedRing K] in
/-- A use within the cap passes through unchanged. -/
theorem sat_of_mem {c x : K} (hx : -c ≤ x) (hxc : x ≤ c) : sat c x = x := by
  unfold sat
  rw [min_eq_right hxc, max_eq_right hx]

/-- A use at or past the cap saturates. -/
theorem sat_of_le {c x : K} (hc : 0 ≤ c) (hx : c ≤ x) : sat c x = c := by
  unfold sat
  rw [min_eq_left hx, max_eq_right (by linarith)]

/-- The clamp moves two inputs no farther apart: it is 1-Lipschitz. -/
theorem abs_sat_sub_sat_le (c x y : K) : |sat c x - sat c y| ≤ |x - y| := by
  unfold sat
  calc |max (-c) (min c x) - max (-c) (min c y)|
      ≤ max |-c - -c| |min c x - min c y| := abs_max_sub_max_le_max _ _ _ _
    _ = |min c x - min c y| := by rw [sub_self, abs_zero, max_eq_right (abs_nonneg _)]
    _ ≤ max |c - c| |x - y| := abs_min_sub_min_le_max _ _ _ _
    _ = |x - y| := by rw [sub_self, abs_zero, max_eq_right (abs_nonneg _)]

/-- **UTL-1** One tick keeps the field in its box: the decay toward the baseline and the
saturated increment together never leave `[b − c/lam, b + c/lam]`. -/
theorem step_mem_box {b lam c : K} (hlam : 0 < lam) (hlam1 : lam ≤ 1) (hc : 0 ≤ c)
    {u : ι → K} (hu : InBox b lam c u) (use : ι → K) : InBox b lam c (step b lam c u use) := by
  intro e
  obtain ⟨h1, h2⟩ := hu e
  have hs1 := neg_le_sat c (use e)
  have hs2 := sat_le hc (use e)
  have hne := hlam.ne'
  have hcl : lam * (c / lam) = c := by field_simp
  have hl : 0 ≤ 1 - lam := by linarith
  simp only [floor, ceiling] at h1 h2 ⊢
  have hlo := mul_le_mul_of_nonneg_left (show -(c / lam) ≤ u e - b by linarith) hl
  have hhi := mul_le_mul_of_nonneg_left (show u e - b ≤ c / lam by linarith) hl
  have e1 : b + (1 - lam) * -(c / lam) + -c = b - c / lam := by linear_combination hcl
  have e2 : b + (1 - lam) * (c / lam) + c = b + c / lam := by linear_combination (-1 : K) * hcl
  simp only [step]
  constructor <;> linarith

/-- **UTL-1** The field stays in its box along any log of uses. -/
theorem evolve_mem_box {b lam c : K} (hlam : 0 < lam) (hlam1 : lam ≤ 1) (hc : 0 ≤ c)
    {u₀ : ι → K} (hu : InBox b lam c u₀) (log : List (ι → K)) :
    InBox b lam c (evolve b lam c u₀ log) := by
  induction log generalizing u₀ with
  | nil => simpa [evolve] using hu
  | cons use rest ih =>
    simp only [evolve, List.foldl_cons]
    exact ih (step_mem_box hlam hlam1 hc hu use)

/-- **UTL-1** The floor is positive when `c < b · lam`: every effective weight stays positive, so
no edge is erased by the field. -/
theorem floor_pos {b lam c : K} (hlam : 0 < lam) (h : c < b * lam) : 0 < floor b lam c := by
  unfold floor
  rw [sub_pos, div_lt_iff₀ hlam]
  exact h

/-- The baseline field lies in the box. -/
theorem inBox_const_baseline {b lam c : K} (hlam : 0 < lam) (hc : 0 ≤ c) :
    InBox b lam c (fun _ : ι ↦ b) := by
  intro e
  have : 0 ≤ c / lam := div_nonneg hc hlam.le
  simp only [floor, ceiling]
  constructor <;> linarith

omit [IsStrictOrderedRing K] in
/-- **UTL-4** The field after a log is a function of the log alone, read left to right: appending
uses continues the fold from where the log left it. -/
theorem evolve_append (b lam c : K) (u₀ : ι → K) (l₁ l₂ : List (ι → K)) :
    evolve b lam c u₀ (l₁ ++ l₂) = evolve b lam c (evolve b lam c u₀ l₁) l₂ := by
  simp [evolve, List.foldl_append]

end Box

/-! ### UTL-2 Decay: an unused site returns to the baseline, arcs fade and form -/

section Decay

variable {ι K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K]

/-- **UTL-2** The field left alone decays geometrically to the baseline:
`u_n = b + (1 − lam)^n (u₀ − b)`. -/
theorem idle_apply {b lam c : K} (hc : 0 ≤ c) (u : ι → K) (n : ℕ) (e : ι) :
    idle b lam c u n e = b + (1 - lam) ^ n * (u e - b) := by
  induction n with
  | zero => simp [idle]
  | succ n ih =>
    have h : idle b lam c u (n + 1) = step b lam c (idle b lam c u n) 0 := by
      simp only [idle, Function.iterate_succ_apply']
    rw [h]
    simp only [step, Pi.zero_apply, sat_zero hc, ih]
    ring

/-- **UTL-2** From inside the box, an idle site is within `(1 − lam)^n · c/lam` of the baseline
after `n` ticks. -/
theorem idle_sub_le {b lam c : K} (hlam1 : lam ≤ 1) (hc : 0 ≤ c)
    {u : ι → K} (hu : InBox b lam c u) (n : ℕ) (e : ι) :
    |idle b lam c u n e - b| ≤ (1 - lam) ^ n * (c / lam) := by
  rw [idle_apply hc, add_sub_cancel_left, abs_mul, abs_of_nonneg (pow_nonneg (by linarith) n)]
  refine mul_le_mul_of_nonneg_left ?_ (pow_nonneg (by linarith) n)
  obtain ⟨h1, h2⟩ := hu e
  simp only [floor, ceiling] at h1 h2
  rw [abs_le]
  constructor <;> linarith

/-- **UTL-2** Arcs fade: once `(1 − lam)^n · c/lam < a`, an idle site is no arc of height `a`. -/
theorem not_isArc_idle {b lam c : K} (hlam1 : lam ≤ 1) (hc : 0 ≤ c)
    {u : ι → K} (hu : InBox b lam c u) {a : K} {n : ℕ} (hn : (1 - lam) ^ n * (c / lam) < a)
    (e : ι) : ¬ IsArc b a (idle b lam c u n) e := by
  intro h
  have hb := idle_sub_le hlam1 hc hu n e
  have := (abs_le.1 hb).2
  unfold IsArc at h
  linarith

/-- A heat spot's closed form: `n` ticks of a constant use `r` within the cap give
`u_n = b + (1 − lam)^n (u₀ − b) + (r/lam)(1 − (1 − lam)^n)`. -/
theorem steady_apply {b lam c r : K} (hlam : 0 < lam) (hr : -c ≤ r) (hrc : r ≤ c) (u : ι → K)
    (n : ℕ) (e : ι) :
    steady b lam c r u n e =
      b + (1 - lam) ^ n * (u e - b) + r / lam * (1 - (1 - lam) ^ n) := by
  have hne := hlam.ne'
  have hcl : r / lam * lam = r := by field_simp
  induction n with
  | zero => simp [steady]
  | succ n ih =>
    have h : steady b lam c r u (n + 1) = step b lam c (steady b lam c r u n) fun _ ↦ r := by
      simp only [steady, Function.iterate_succ_apply']
    rw [h]
    simp only [step, sat_of_mem hr hrc, ih]
    linear_combination (-1 : K) * hcl

/-- **UTL-2** Arcs form: a site held at the cap for `n` ticks from at least the baseline is an arc
of height `a` once `(c/lam)(1 − (1 − lam)^n) ≥ a`. -/
theorem isArc_steady {b lam c : K} (hlam : 0 < lam) (hlam1 : lam ≤ 1) (hc : 0 ≤ c)
    {u : ι → K} {e : ι} (hu : b ≤ u e) {a : K} {n : ℕ}
    (hn : a ≤ c / lam * (1 - (1 - lam) ^ n)) : IsArc b a (steady b lam c c u n) e := by
  unfold IsArc
  rw [steady_apply hlam (by linarith) le_rfl u n e]
  have hp : 0 ≤ (1 - lam) ^ n * (u e - b) :=
    mul_nonneg (pow_nonneg (by linarith) n) (by linarith)
  linarith

end Decay

section Linear

variable {ι K : Type*} [Field K]

/-- The control, reinforcement without decay: the field grows linearly in the number of uses. -/
theorem linearStep_iterate (u r : ι → K) (n : ℕ) (e : ι) :
    (fun v ↦ linearStep v r)^[n] u e = u e + n * r e := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [Function.iterate_succ_apply']
    change linearStep ((fun v ↦ linearStep v r)^[n] u) r e = _
    rw [linearStep, Pi.add_apply, ih]
    push_cast
    ring

end Linear

section DecayReal

variable {ι : Type*}

/-- `(1 − lam)^n ≤ e^{−lam·n}` for `0 ≤ lam ≤ 1`. -/
theorem one_sub_pow_le_exp {lam : ℝ} (h1 : lam ≤ 1) (n : ℕ) :
    (1 - lam) ^ n ≤ Real.exp (-(lam * n)) := by
  have h := Real.add_one_le_exp (-lam)
  calc (1 - lam) ^ n ≤ Real.exp (-lam) ^ n :=
        pow_le_pow_left₀ (by linarith) (by linarith) n
    _ = Real.exp (-(lam * n)) := by
        rw [← Real.exp_nat_mul]
        congr 1
        ring

/-- **UTL-2** The declared window: once `lam · n ≥ log (c / (lam ε))`, an idle site is within `ε`
of the baseline. The window is the forgetting rate's reciprocal times the log of the box's height
over the tolerance. -/
theorem idle_window {b lam c : ℝ} (hlam : 0 < lam) (hlam1 : lam ≤ 1) (hc : 0 < c)
    {u : ι → ℝ} (hu : InBox b lam c u) {ε : ℝ} (hε : 0 < ε) {n : ℕ}
    (hn : Real.log (c / (lam * ε)) ≤ lam * n) (e : ι) : |idle b lam c u n e - b| ≤ ε := by
  have hb := idle_sub_le hlam1 hc.le hu n e
  have hpos : 0 < lam * ε / c := by positivity
  have hexp : Real.exp (-(lam * n)) ≤ lam * ε / c := by
    rw [← Real.exp_log hpos]
    apply Real.exp_le_exp.2
    have : Real.log (lam * ε / c) = -Real.log (c / (lam * ε)) := by
      rw [← Real.log_inv, inv_div]
    linarith
  have hcl : 0 < c / lam := by positivity
  have hne := hc.ne'
  have hne' := hlam.ne'
  calc |idle b lam c u n e - b| ≤ (1 - lam) ^ n * (c / lam) := hb
    _ ≤ Real.exp (-(lam * n)) * (c / lam) :=
        mul_le_mul_of_nonneg_right (one_sub_pow_le_exp hlam1 n) hcl.le
    _ ≤ lam * ε / c * (c / lam) := mul_le_mul_of_nonneg_right hexp hcl.le
    _ = ε := by field_simp

/-- The box is the least invariant box: from the baseline, a site held at the cap climbs past
every level below the ceiling. -/
theorem exists_steady_gt {b lam c : ℝ} (hlam : 0 < lam) (hc : 0 < c)
    {M : ℝ} (hM : M < ceiling b lam c) (e : ι) :
    ∃ n, M < steady b lam c c (fun _ ↦ b) n e := by
  have hsub : 0 < ceiling b lam c - M := sub_pos.2 hM
  have hδ : 0 < (ceiling b lam c - M) * lam / c := by positivity
  obtain ⟨n, hn⟩ := exists_pow_lt_of_lt_one hδ (show 1 - lam < 1 by linarith)
  refine ⟨n, ?_⟩
  rw [steady_apply hlam (by linarith) le_rfl]
  have hne := hc.ne'
  have hne' := hlam.ne'
  have h2 : (1 - lam) ^ n * (c / lam) < ceiling b lam c - M := by
    have := mul_lt_mul_of_pos_right hn (show 0 < c / lam by positivity)
    calc (1 - lam) ^ n * (c / lam) < (ceiling b lam c - M) * lam / c * (c / lam) := this
      _ = ceiling b lam c - M := by field_simp
  have h3 : c / lam * (1 - (1 - lam) ^ n) = c / lam - (1 - lam) ^ n * (c / lam) := by ring
  unfold ceiling at h2
  simp only [sub_self, mul_zero, add_zero]
  linarith

/-- The control: without decay or a cap the field exceeds every bound. -/
theorem linear_unbounded (u r : ι → ℝ) {e : ι} (hr : 0 < r e) (M : ℝ) :
    ∃ n : ℕ, M < (fun v ↦ linearStep v r)^[n] u e := by
  obtain ⟨n, hn⟩ := exists_nat_gt ((M - u e) / r e)
  refine ⟨n, ?_⟩
  rw [linearStep_iterate]
  rw [div_lt_iff₀ hr] at hn
  linarith

end DecayReal

/-! ### UTL-3 and UTL-5 The nudge: support, stationary mass, total variation, the margin -/

section NudgePointwise

variable {V K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K]

omit [LinearOrder K] [IsStrictOrderedRing K] in
/-- The effective weight, written out. -/
theorem nudge_apply (η b : K) (A : Matrix V V K) (u : V → V → K) (i j : V) :
    nudge η b A u i j = A i j * (1 + η * (u i j - b)) := rfl

omit [LinearOrder K] [IsStrictOrderedRing K] in
/-- **UTL-4** At the baseline the effective weights are the structural ones: switching the field
off recovers the backbone exactly. -/
theorem nudge_baseline (η b : K) (A : Matrix V V K) : nudge η b A (fun _ _ ↦ b) = A := by
  ext i j
  simp [nudge]

/-- The margin is nonnegative. -/
theorem margin_nonneg {η lam c : K} (hη : 0 ≤ η) (hlam : 0 < lam) (hc : 0 ≤ c) :
    0 ≤ margin η lam c :=
  mul_nonneg hη (div_nonneg hc hlam.le)

/-- A field in the box nudges each weight by a factor in `[1 − θ, 1 + θ]`. -/
theorem nudge_factor_mem {η b lam c : K} (hη : 0 ≤ η) {u : V → V → K} {i j : V}
    (hu : floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) :
    1 - margin η lam c ≤ 1 + η * (u i j - b) ∧ 1 + η * (u i j - b) ≤ 1 + margin η lam c := by
  obtain ⟨h1, h2⟩ := hu
  simp only [floor, ceiling] at h1 h2
  have hlo := mul_le_mul_of_nonneg_left (show -(c / lam) ≤ u i j - b by linarith) hη
  have hhi := mul_le_mul_of_nonneg_left (show u i j - b ≤ c / lam by linarith) hη
  rw [mul_neg] at hlo
  unfold margin
  constructor <;> linarith

/-- **UTL-3** The nudge keeps the support: with the margin below one, an effective weight is zero
exactly when the structural weight is. No edge is erased and none is created. -/
theorem nudge_eq_zero_iff {η b lam c : K} (hη : 0 ≤ η) (hθ : margin η lam c < 1)
    {A : Matrix V V K} {u : V → V → K} {i j : V}
    (hu : floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) :
    nudge η b A u i j = 0 ↔ A i j = 0 := by
  have hf := (nudge_factor_mem hη hu).1
  have hpos : 0 < 1 + η * (u i j - b) := by linarith
  rw [nudge_apply, mul_eq_zero, or_iff_left hpos.ne']

/-- The effective weight is at most `(1 + θ)` times the structural one. -/
theorem nudge_le {η b lam c : K} (hη : 0 ≤ η) {A : Matrix V V K} {u : V → V → K} {i j : V}
    (hA : 0 ≤ A i j) (hu : floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) :
    nudge η b A u i j ≤ (1 + margin η lam c) * A i j := by
  rw [nudge_apply, mul_comm]
  exact mul_le_mul_of_nonneg_right (nudge_factor_mem hη hu).2 hA

/-- The effective weight is at least `(1 − θ)` times the structural one. -/
theorem le_nudge {η b lam c : K} (hη : 0 ≤ η) {A : Matrix V V K} {u : V → V → K} {i j : V}
    (hA : 0 ≤ A i j) (hu : floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) :
    (1 - margin η lam c) * A i j ≤ nudge η b A u i j := by
  rw [nudge_apply, mul_comm]
  exact mul_le_mul_of_nonneg_left (nudge_factor_mem hη hu).1 hA

/-- The effective weights are nonnegative when the margin is at most one. -/
theorem nudge_nonneg {η b lam c : K} (hη : 0 ≤ η) (hθ : margin η lam c ≤ 1) {A : Matrix V V K}
    {u : V → V → K} {i j : V} (hA : 0 ≤ A i j)
    (hu : floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) : 0 ≤ nudge η b A u i j :=
  le_trans (mul_nonneg (by linarith) hA) (le_nudge hη hA hu)

/-- **UTL-5** The field reorders only within the margin: two structural weights whose ratio
exceeds `(1 + θ)/(1 − θ)` keep their order under every field state in the box. -/
theorem nudge_lt_nudge_of_margin {η b lam c : K} (hη : 0 ≤ η) {A : Matrix V V K}
    {u : V → V → K} {i j k l : V} (hkl : 0 ≤ A k l) (hij : 0 ≤ A i j)
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c)
    (h : (1 + margin η lam c) * A k l < (1 - margin η lam c) * A i j) :
    nudge η b A u k l < nudge η b A u i j :=
  lt_of_le_of_lt (nudge_le hη hkl (hu k l)) (lt_of_lt_of_le h (le_nudge hη hij (hu i j)))

end NudgePointwise

section NudgeSums

variable {V K : Type*} [Fintype V] [Field K] [LinearOrder K] [IsStrictOrderedRing K]

/-- Degrees move within the margin, from above. -/
theorem degree_nudge_le {η b lam c : K} (hη : 0 ≤ η) {A : Matrix V V K} (hA : ∀ i j, 0 ≤ A i j)
    {u : V → V → K} (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) (i : V) :
    degree (nudge η b A u) i ≤ (1 + margin η lam c) * degree A i := by
  unfold degree
  rw [Finset.mul_sum]
  exact sum_le_sum fun j _ ↦ nudge_le hη (hA i j) (hu i j)

/-- Degrees move within the margin, from below. -/
theorem le_degree_nudge {η b lam c : K} (hη : 0 ≤ η) {A : Matrix V V K} (hA : ∀ i j, 0 ≤ A i j)
    {u : V → V → K} (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) (i : V) :
    (1 - margin η lam c) * degree A i ≤ degree (nudge η b A u) i := by
  unfold degree
  rw [Finset.mul_sum]
  exact sum_le_sum fun j _ ↦ le_nudge hη (hA i j) (hu i j)

/-- The volume moves within the margin, from above. -/
theorem sum_degree_nudge_le {η b lam c : K} (hη : 0 ≤ η) {A : Matrix V V K}
    (hA : ∀ i j, 0 ≤ A i j) {u : V → V → K}
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) :
    ∑ i, degree (nudge η b A u) i ≤ (1 + margin η lam c) * ∑ i, degree A i := by
  rw [Finset.mul_sum]
  exact sum_le_sum fun i _ ↦ degree_nudge_le hη hA hu i

/-- The volume moves within the margin, from below. -/
theorem le_sum_degree_nudge {η b lam c : K} (hη : 0 ≤ η) {A : Matrix V V K}
    (hA : ∀ i j, 0 ≤ A i j) {u : V → V → K}
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) :
    (1 - margin η lam c) * ∑ i, degree A i ≤ ∑ i, degree (nudge η b A u) i := by
  rw [Finset.mul_sum]
  exact sum_le_sum fun i _ ↦ le_degree_nudge hη hA hu i

/-- The stationary distribution is nonnegative. -/
theorem statDist_nonneg {A : Matrix V V K} (hA : ∀ i j, 0 ≤ A i j) (hvol : 0 < ∑ j, degree A j)
    (i : V) : 0 ≤ statDist A i :=
  div_nonneg (sum_nonneg fun j _ ↦ hA i j) hvol.le

omit [LinearOrder K] [IsStrictOrderedRing K] in
/-- The stationary distribution sums to one. -/
theorem sum_statDist {A : Matrix V V K} (hvol : ∑ j, degree A j ≠ 0) :
    ∑ i, statDist A i = 1 := by
  unfold statDist
  rw [← Finset.sum_div, div_self hvol]

/-- **UTL-3** No hub: a node's stationary mass under the nudged walk is at most
`(1 + θ)/(1 − θ)` times its structural mass, whatever the field's state in its box. -/
theorem statDist_nudge_le {η b lam c : K} (hη : 0 ≤ η) (hlam : 0 < lam) (hc : 0 ≤ c)
    (hθ : margin η lam c < 1) {A : Matrix V V K} (hA : ∀ i j, 0 ≤ A i j)
    (hvol : 0 < ∑ j, degree A j) {u : V → V → K}
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) (i : V) :
    statDist (nudge η b A u) i ≤ (1 + margin η lam c) / (1 - margin η lam c) * statDist A i := by
  have hθ0 := margin_nonneg hη hlam hc
  have hdi : 0 ≤ degree A i := sum_nonneg fun j _ ↦ hA i j
  unfold statDist
  rw [div_mul_div_comm]
  exact div_le_div₀ (mul_nonneg (by linarith) hdi) (degree_nudge_le hη hA hu i)
    (mul_pos (by linarith) hvol) (le_sum_degree_nudge hη hA hu)

/-- No desert: a node's stationary mass under the nudged walk is at least `(1 − θ)/(1 + θ)`
times its structural mass. -/
theorem le_statDist_nudge {η b lam c : K} (hη : 0 ≤ η) (hlam : 0 < lam) (hc : 0 ≤ c)
    (hθ : margin η lam c < 1) {A : Matrix V V K} (hA : ∀ i j, 0 ≤ A i j)
    (hvol : 0 < ∑ j, degree A j) {u : V → V → K}
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) (i : V) :
    (1 - margin η lam c) / (1 + margin η lam c) * statDist A i ≤ statDist (nudge η b A u) i := by
  have hθ0 := margin_nonneg hη hlam hc
  have hdi' : 0 ≤ degree (nudge η b A u) i :=
    sum_nonneg fun j _ ↦ nudge_nonneg hη hθ.le (hA i j) (hu i j)
  have hvol' : 0 < ∑ j, degree (nudge η b A u) j :=
    lt_of_lt_of_le (mul_pos (by linarith) hvol) (le_sum_degree_nudge hη hA hu)
  unfold statDist
  rw [div_mul_div_comm]
  exact div_le_div₀ hdi' (le_degree_nudge hη hA hu i) hvol' (sum_degree_nudge_le hη hA hu)

/-- **UTL-3** The reinforced walk's stationary distribution stays within `θ/(1 − θ)` of the
structural walk's in total variation, whatever the field's state in its box: the field cannot
collapse the walk onto a few hubs. -/
theorem tv_statDist_nudge_le {η b lam c : K} (hη : 0 ≤ η) (hlam : 0 < lam) (hc : 0 ≤ c)
    (hθ : margin η lam c < 1) {A : Matrix V V K} (hA : ∀ i j, 0 ≤ A i j)
    (hvol : 0 < ∑ j, degree A j) {u : V → V → K}
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) :
    tv (statDist (nudge η b A u)) (statDist A) ≤ margin η lam c / (1 - margin η lam c) := by
  set θ := margin η lam c with hθdef
  have hθ0 : 0 ≤ θ := margin_nonneg hη hlam hc
  have h1θ : 0 < 1 - θ := by linarith
  have h1θ' : 1 - θ ≠ 0 := h1θ.ne'
  have h1θ'' : 1 + θ ≠ 0 := by positivity
  have hbound : ∀ i, |statDist (nudge η b A u) i - statDist A i| ≤
      2 * θ / (1 - θ) * statDist A i := by
    intro i
    have hπ := statDist_nonneg hA hvol i
    have hup := statDist_nudge_le hη hlam hc hθ hA hvol hu i
    have hlo := le_statDist_nudge hη hlam hc hθ hA hvol hu i
    rw [abs_sub_le_iff]
    constructor
    · have h4 : (1 + θ) / (1 - θ) * statDist A i =
          statDist A i + 2 * θ / (1 - θ) * statDist A i := by
        field_simp
        ring
      linarith
    · have h2 : statDist A i - (1 - θ) / (1 + θ) * statDist A i =
          2 * θ / (1 + θ) * statDist A i := by
        field_simp
        ring
      have h3 : 2 * θ / (1 + θ) * statDist A i ≤ 2 * θ / (1 - θ) * statDist A i := by
        apply mul_le_mul_of_nonneg_right _ hπ
        exact div_le_div_of_nonneg_left (by linarith) h1θ (by linarith)
      linarith
  unfold tv
  calc 1 / 2 * ∑ i, |statDist (nudge η b A u) i - statDist A i|
      ≤ 1 / 2 * ∑ i, 2 * θ / (1 - θ) * statDist A i :=
        mul_le_mul_of_nonneg_left (sum_le_sum fun i _ ↦ hbound i) (by norm_num)
    _ = θ / (1 - θ) := by
        rw [← Finset.mul_sum, sum_statDist hvol.ne']
        field_simp

end NudgeSums

/-! ### UTL-5 The bounded nudge on the Laplacian, and UTL-3's gap -/

section Spectral

variable {V : Type*} [Fintype V] [DecidableEq V]

/-- The Dirichlet form of the nudged weights, from above: `xᵀ L' x ≤ (1 + θ) xᵀ L x` for
symmetric nonnegative `A` and a symmetric field in the box. -/
theorem dotProduct_lap_nudge_le {η b lam c : ℝ} (hη : 0 ≤ η) {A : Matrix V V ℝ} (hA : A.IsSymm)
    (hA0 : ∀ i j, 0 ≤ A i j) {u : V → V → ℝ} (hus : ∀ i j, u i j = u j i)
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) (x : V → ℝ) :
    x ⬝ᵥ (lap (nudge η b A u) *ᵥ x) ≤ (1 + margin η lam c) * (x ⬝ᵥ (lap A *ᵥ x)) := by
  have h1 := two_mul_dotProduct_lap A hA x
  have h2 := two_mul_dotProduct_lap (nudge η b A u) (isSymm_nudge hA hus) x
  have hsum : ∑ i, ∑ j, nudge η b A u i j * (x i - x j) ^ 2 ≤
      (1 + margin η lam c) * ∑ i, ∑ j, A i j * (x i - x j) ^ 2 := by
    rw [Finset.mul_sum]
    refine sum_le_sum fun i _ ↦ ?_
    rw [Finset.mul_sum]
    refine sum_le_sum fun j _ ↦ ?_
    rw [← mul_assoc]
    exact mul_le_mul_of_nonneg_right (nudge_le hη (hA0 i j) (hu i j)) (sq_nonneg _)
  rw [← h1, ← h2] at hsum
  linarith

/-- The Dirichlet form of the nudged weights, from below: `(1 − θ) xᵀ L x ≤ xᵀ L' x`. -/
theorem le_dotProduct_lap_nudge {η b lam c : ℝ} (hη : 0 ≤ η) {A : Matrix V V ℝ} (hA : A.IsSymm)
    (hA0 : ∀ i j, 0 ≤ A i j) {u : V → V → ℝ} (hus : ∀ i j, u i j = u j i)
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) (x : V → ℝ) :
    (1 - margin η lam c) * (x ⬝ᵥ (lap A *ᵥ x)) ≤ x ⬝ᵥ (lap (nudge η b A u) *ᵥ x) := by
  have h1 := two_mul_dotProduct_lap A hA x
  have h2 := two_mul_dotProduct_lap (nudge η b A u) (isSymm_nudge hA hus) x
  have hsum : (1 - margin η lam c) * ∑ i, ∑ j, A i j * (x i - x j) ^ 2 ≤
      ∑ i, ∑ j, nudge η b A u i j * (x i - x j) ^ 2 := by
    rw [Finset.mul_sum]
    refine sum_le_sum fun i _ ↦ ?_
    rw [Finset.mul_sum]
    refine sum_le_sum fun j _ ↦ ?_
    rw [← mul_assoc]
    exact mul_le_mul_of_nonneg_right (le_nudge hη (hA0 i j) (hu i j)) (sq_nonneg _)
  rw [← h1, ← h2] at hsum
  linarith

/-- **UTL-5** The bounded nudge: the field moves the Laplacian's quadratic form by at most `θ`
times the structural form, `|xᵀ (L' − L) x| ≤ θ xᵀ L x`. -/
theorem abs_dotProduct_lap_sub_le {η b lam c : ℝ} (hη : 0 ≤ η) {A : Matrix V V ℝ} (hA : A.IsSymm)
    (hA0 : ∀ i j, 0 ≤ A i j) {u : V → V → ℝ} (hus : ∀ i j, u i j = u j i)
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) (x : V → ℝ) :
    |x ⬝ᵥ ((lap (nudge η b A u) - lap A) *ᵥ x)| ≤ margin η lam c * (x ⬝ᵥ (lap A *ᵥ x)) := by
  rw [sub_mulVec, dotProduct_sub, abs_sub_le_iff]
  have hle := dotProduct_lap_nudge_le hη hA hA0 hus hu x
  have hge := le_dotProduct_lap_nudge hη hA hA0 hus hu x
  have e1 : (1 + margin η lam c) * (x ⬝ᵥ (lap A *ᵥ x)) =
      x ⬝ᵥ (lap A *ᵥ x) + margin η lam c * (x ⬝ᵥ (lap A *ᵥ x)) := by ring
  have e2 : (1 - margin η lam c) * (x ⬝ᵥ (lap A *ᵥ x)) =
      x ⬝ᵥ (lap A *ᵥ x) - margin η lam c * (x ⬝ᵥ (lap A *ᵥ x)) := by ring
  constructor <;> linarith

/-- `xᵀ L x ≤ 2 d ‖x‖²` when every degree is at most `d`: the Laplacian's largest eigenvalue is at
most twice the largest degree, as a quadratic form. -/
theorem dotProduct_lap_le_degree {A : Matrix V V ℝ} (hA : A.IsSymm) (hA0 : ∀ i j, 0 ≤ A i j)
    {d : ℝ} (hd : ∀ i, degree A i ≤ d) (x : V → ℝ) :
    x ⬝ᵥ (lap A *ᵥ x) ≤ 2 * d * (x ⬝ᵥ x) := by
  have h := two_mul_dotProduct_lap A hA x
  have h1 : ∑ i, ∑ j, A i j * (x i - x j) ^ 2 ≤
      ∑ i, ∑ j, A i j * (2 * (x i ^ 2 + x j ^ 2)) :=
    sum_le_sum fun i _ ↦ sum_le_sum fun j _ ↦
      mul_le_mul_of_nonneg_left (by nlinarith [sq_nonneg (x i + x j)]) (hA0 i j)
  have h2 : ∑ i, ∑ j, A i j * (2 * (x i ^ 2 + x j ^ 2)) =
      2 * ∑ i, degree A i * x i ^ 2 + 2 * ∑ j, degree A j * x j ^ 2 := by
    have ha : ∀ i, ∑ j, A i j * (2 * (x i ^ 2 + x j ^ 2)) =
        2 * (degree A i * x i ^ 2) + 2 * ∑ j, A i j * x j ^ 2 := by
      intro i
      simp only [degree, Finset.sum_mul, Finset.mul_sum]
      rw [← Finset.sum_add_distrib]
      exact sum_congr rfl fun j _ ↦ by ring
    rw [sum_congr rfl fun i _ ↦ ha i, Finset.sum_add_distrib, ← Finset.mul_sum, ← Finset.mul_sum]
    congr 2
    rw [Finset.sum_comm]
    simp only [degree, Finset.sum_mul]
    exact sum_congr rfl fun j _ ↦ sum_congr rfl fun i _ ↦ by rw [hA.apply i j]
  have h3 : ∑ i, degree A i * x i ^ 2 ≤ d * (x ⬝ᵥ x) := by
    simp only [dotProduct, Finset.mul_sum]
    exact sum_le_sum fun i _ ↦ by nlinarith [hd i, sq_nonneg (x i)]
  linarith

/-- **UTL-5** The nudged Laplacian lies within `2 θ d` of the structural one as a quadratic form,
`d` a bound on the degrees: the hypothesis of Weyl's inequality counted (SPC-3). -/
theorem near_lap_nudge {η b lam c : ℝ} (hη : 0 ≤ η) (hlam : 0 < lam) (hc : 0 ≤ c)
    {A : Matrix V V ℝ} (hA : A.IsSymm) (hA0 : ∀ i j, 0 ≤ A i j) {d : ℝ} (hd : ∀ i, degree A i ≤ d)
    {u : V → V → ℝ} (hus : ∀ i j, u i j = u j i)
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) :
    Gap.Near (Matrix.toEuclideanLin (lap A)) (Matrix.toEuclideanLin (lap (nudge η b A u)))
      (2 * margin η lam c * d) := by
  intro x
  have hθ0 := margin_nonneg hη hlam hc
  have hx : ‖x‖ ^ 2 = WithLp.ofLp x ⬝ᵥ WithLp.ofLp x := by
    rw [← real_inner_self_eq_norm_sq, EuclideanSpace.inner_eq_star_dotProduct, star_trivial]
  have key : inner ℝ x ((Matrix.toEuclideanLin (lap (nudge η b A u)) -
      Matrix.toEuclideanLin (lap A)) x) =
      WithLp.ofLp x ⬝ᵥ ((lap (nudge η b A u) - lap A) *ᵥ WithLp.ofLp x) := by
    rw [LinearMap.sub_apply, EuclideanSpace.inner_eq_star_dotProduct, star_trivial,
      WithLp.ofLp_sub, Matrix.ofLp_toLpLin, Matrix.ofLp_toLpLin, Matrix.toLin'_apply,
      Matrix.toLin'_apply, ← sub_mulVec, dotProduct_comm]
  rw [key, hx]
  calc |WithLp.ofLp x ⬝ᵥ ((lap (nudge η b A u) - lap A) *ᵥ WithLp.ofLp x)|
      ≤ margin η lam c * (WithLp.ofLp x ⬝ᵥ (lap A *ᵥ WithLp.ofLp x)) :=
        abs_dotProduct_lap_sub_le hη hA hA0 hus hu _
    _ ≤ margin η lam c * (2 * d * (WithLp.ofLp x ⬝ᵥ WithLp.ofLp x)) :=
        mul_le_mul_of_nonneg_left (dotProduct_lap_le_degree hA hA0 hd _) hθ0
    _ = 2 * margin η lam c * d * (WithLp.ofLp x ⬝ᵥ WithLp.ofLp x) := by ring

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
  Gap.count_sub_le _ _ _ (near_lap_nudge hη hlam hc hA hA0 hd hus hu) t

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
  Gap.count_le_add _ _ _ (near_lap_nudge hη hlam hc hA hA0 hd hus hu) t

/-- UTL-3 The nudged graph keeps a spectral gap: `(1 − θ) γ` is a gap of the effective weights
when `γ` is a gap of the structural ones (DYN-6's Poincaré form). -/
theorem hasSpectralGapAtLeast_nudge {η b lam c : ℝ} (hη : 0 ≤ η) {A : Matrix V V ℝ}
    (hA : A.IsSymm) (hA0 : ∀ i j, 0 ≤ A i j) {u : V → V → ℝ} (hus : ∀ i j, u i j = u j i)
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) (hθ1 : margin η lam c ≤ 1)
    {γ : ℝ} (hγ : Dynamics.HasSpectralGapAtLeast A γ) :
    Dynamics.HasSpectralGapAtLeast (nudge η b A u) ((1 - margin η lam c) * γ) := by
  intro f hf
  have h1 := hγ f hf
  have h2 := le_dotProduct_lap_nudge hη hA hA0 hus hu f
  calc (1 - margin η lam c) * γ * (f ⬝ᵥ f) = (1 - margin η lam c) * (γ * (f ⬝ᵥ f)) := by ring
    _ ≤ (1 - margin η lam c) * (f ⬝ᵥ (lap A *ᵥ f)) :=
        mul_le_mul_of_nonneg_left h1 (by linarith)
    _ ≤ f ⬝ᵥ (lap (nudge η b A u) *ᵥ f) := h2

/-- UTL-3 So every nonzero eigenvalue of the nudged Laplacian is at least `(1 − θ) γ`: a weight
change propagates, under DYN-6, at a rate within the margin of the structural one. -/
theorem le_eigenvalue_nudge {η b lam c : ℝ} (hη : 0 ≤ η) {A : Matrix V V ℝ} (hA : A.IsSymm)
    (hA0 : ∀ i j, 0 ≤ A i j) {u : V → V → ℝ} (hus : ∀ i j, u i j = u j i)
    (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) (hθ1 : margin η lam c ≤ 1)
    {γ : ℝ} (hγ : Dynamics.HasSpectralGapAtLeast A γ) {j : V}
    (hj : (isHermitian_lap (nudge η b A u) (isSymm_nudge hA hus)).eigenvalues j ≠ 0) :
    (1 - margin η lam c) * γ ≤
      (isHermitian_lap (nudge η b A u) (isSymm_nudge hA hus)).eigenvalues j :=
  Dynamics.le_eigenvalue_of_hasSpectralGapAtLeast (isSymm_nudge hA hus)
    (hasSpectralGapAtLeast_nudge hη hA hA0 hus hu hθ1 hγ) hj

omit [Fintype V] [DecidableEq V] in
/-- The support of the nudged weights is the backbone's: the field changes no edge set. -/
theorem support_nudge {η b lam c : ℝ} (hη : 0 ≤ η) (hθ : margin η lam c < 1) {A : Matrix V V ℝ}
    {u : V → V → ℝ} (hu : ∀ i j, floor b lam c ≤ u i j ∧ u i j ≤ ceiling b lam c) :
    support (nudge η b A u) = support A := by
  ext i j
  simp only [support, SimpleGraph.fromRel_adj, ne_eq, nudge_eq_zero_iff hη hθ (hu i j),
    nudge_eq_zero_iff hη hθ (hu j i)]

end Spectral

/-! ### UTL-6 The closed loop: no self-reinforcing state when the gain is below the rate -/

section Loop

variable {ι : Type*} [Fintype ι]

/-- **UTL-6** The closed loop is a contraction of the sup metric when the use's gain in the field
is below the forgetting rate: `dist (loop u) (loop v) ≤ (1 − lam + K) dist u v`. -/
theorem loop_dist_le {b lam c : ℝ} (hlam1 : lam ≤ 1)
    {F : (ι → ℝ) → ι → ℝ} {Kg : ℝ} (hK : 0 ≤ Kg) (hF : ∀ u v, dist (F u) (F v) ≤ Kg * dist u v)
    (u v : ι → ℝ) :
    dist (loop b lam c F u) (loop b lam c F v) ≤ (1 - lam + Kg) * dist u v := by
  have hd : 0 ≤ dist u v := dist_nonneg
  rw [dist_pi_le_iff (mul_nonneg (by linarith) hd)]
  intro e
  rw [Real.dist_eq]
  have h1 : |u e - v e| ≤ dist u v := by
    rw [← Real.dist_eq]
    exact dist_le_pi_dist u v e
  have h2 : |F u e - F v e| ≤ Kg * dist u v := by
    rw [← Real.dist_eq]
    exact (dist_le_pi_dist (F u) (F v) e).trans (hF u v)
  have h3 := abs_sat_sub_sat_le c (F u e) (F v e)
  have h4 := mul_le_mul_of_nonneg_left h1 (show 0 ≤ 1 - lam by linarith)
  simp only [loop, step]
  calc |b + (1 - lam) * (u e - b) + sat c (F u e) - (b + (1 - lam) * (v e - b) + sat c (F v e))|
      = |(1 - lam) * (u e - v e) + (sat c (F u e) - sat c (F v e))| := by
        congr 1
        ring
    _ ≤ |(1 - lam) * (u e - v e)| + |sat c (F u e) - sat c (F v e)| := abs_add_le _ _
    _ = (1 - lam) * |u e - v e| + |sat c (F u e) - sat c (F v e)| := by
        rw [abs_mul, abs_of_nonneg (by linarith)]
    _ ≤ (1 - lam) * dist u v + Kg * dist u v := by linarith
    _ = (1 - lam + Kg) * dist u v := by ring

/-- **UTL-6** With the gain below the forgetting rate the loop has exactly one stationary field:
no self-sustaining state beside it. -/
theorem loop_existsUnique_fixedPoint {b lam c : ℝ} (hlam1 : lam ≤ 1)
    {F : (ι → ℝ) → ι → ℝ} {Kg : ℝ} (hK : 0 ≤ Kg) (hKl : Kg < lam)
    (hF : ∀ u v, dist (F u) (F v) ≤ Kg * dist u v) :
    ∃! u : ι → ℝ, loop b lam c F u = u := by
  have hρ0 : 0 ≤ 1 - lam + Kg := by linarith
  have hρ1 : 1 - lam + Kg < 1 := by linarith
  have hcon : ContractingWith ⟨1 - lam + Kg, hρ0⟩ (loop b lam c F) := by
    refine ⟨?_, LipschitzWith.of_dist_le_mul fun u v ↦ ?_⟩
    · exact_mod_cast hρ1
    · exact loop_dist_le hlam1 hK hF u v
  exact ⟨ContractingWith.fixedPoint _ hcon, hcon.fixedPoint_isFixedPt,
    fun u hu ↦ hcon.fixedPoint_unique hu⟩

/-- The iterates of the loop converge to its stationary field geometrically, at the rate
`1 − lam + K`: how fast the field settles after the load changes. -/
theorem loop_iterate_tendsto {b lam c : ℝ} (hlam1 : lam ≤ 1)
    {F : (ι → ℝ) → ι → ℝ} {Kg : ℝ} (hK : 0 ≤ Kg) (hKl : Kg < lam)
    (hF : ∀ u v, dist (F u) (F v) ≤ Kg * dist u v) :
    ∃ ustar : ι → ℝ, loop b lam c F ustar = ustar ∧ ∀ (u : ι → ℝ) (n : ℕ),
      dist ((loop b lam c F)^[n] u) ustar ≤
        dist u (loop b lam c F u) * (1 - lam + Kg) ^ n / (1 - (1 - lam + Kg)) := by
  have hρ0 : 0 ≤ 1 - lam + Kg := by linarith
  have hρ1 : 1 - lam + Kg < 1 := by linarith
  have hcon : ContractingWith ⟨1 - lam + Kg, hρ0⟩ (loop b lam c F) := by
    refine ⟨?_, LipschitzWith.of_dist_le_mul fun u v ↦ ?_⟩
    · exact_mod_cast hρ1
    · exact loop_dist_le hlam1 hK hF u v
  exact ⟨ContractingWith.fixedPoint _ hcon, hcon.fixedPoint_isFixedPt,
    fun u n ↦ hcon.apriori_dist_iterate_fixedPoint_le u n⟩

end Loop

section LoopWitness

variable {ι : Type*}

/-- The control: with the gain at or above the forgetting rate, the loop `use = K (u − b)` holds
both the baseline and the ceiling fixed, a self-reinforcing state beside the structural one. -/
theorem Witness.bistable {b lam c Kg : ℝ} (hlam : 0 < lam) (hc : 0 ≤ c) (hK : lam ≤ Kg) :
    loop b lam c (fun u e ↦ Kg * (u e - b)) (fun _ : ι ↦ b) = (fun _ ↦ b) ∧
      loop b lam c (fun u e ↦ Kg * (u e - b)) (fun _ : ι ↦ ceiling b lam c) =
        (fun _ ↦ ceiling b lam c) := by
  have hne := hlam.ne'
  have hcl : lam * (c / lam) = c := by field_simp
  constructor
  · funext e
    simp [loop, step, sat_zero hc]
  · funext e
    have hK' : c ≤ Kg * (ceiling b lam c - b) := by
      unfold ceiling
      rw [add_sub_cancel_left]
      calc c = lam * (c / lam) := hcl.symm
        _ ≤ Kg * (c / lam) := mul_le_mul_of_nonneg_right hK (div_nonneg hc hlam.le)
    simp only [loop, step]
    rw [sat_of_le hc hK']
    simp only [ceiling]
    linear_combination (-1 : ℝ) * hcl

/-- The control, stated as the failure of UTL-6's conclusion: at or above the rate the loop has
two stationary fields when the cap is positive. -/
theorem Witness.not_unique [Nonempty ι] {b lam c Kg : ℝ} (hlam : 0 < lam) (hc : 0 < c)
    (hK : lam ≤ Kg) : ¬ ∃! u : ι → ℝ, loop b lam c (fun u e ↦ Kg * (u e - b)) u = u := by
  obtain ⟨h1, h2⟩ := Witness.bistable (ι := ι) hlam hc.le hK
  rintro ⟨u, -, huniq⟩
  have e1 := huniq _ h1
  have e2 := huniq _ h2
  have h := congrFun (e1.trans e2.symm) (Classical.arbitrary ι)
  unfold ceiling at h
  have : 0 < c / lam := div_pos hc hlam
  linarith

end LoopWitness

/-! ### The exponent decides the regime: the two-site mean field -/

section Polya

variable {K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K]

/-- The control, superlinear reinforcement: with exponent `m + 1 ≥ 2`, the ratio of the two sites'
weights moves away from one at every step, the leader leading more. -/
theorem polya_ratio_lt {m : ℕ} (hm : 0 < m) {x y : K} (hy : 0 < y) (hxy : y < x) :
    x * (polyaStep (m + 1) x y).2 < (polyaStep (m + 1) x y).1 * y := by
  have hx : 0 < x := hy.trans hxy
  have hS : 0 < x ^ (m + 1) + y ^ (m + 1) := by positivity
  have hSne := hS.ne'
  have hpow : y ^ m < x ^ m := pow_lt_pow_left₀ hxy hy.le hm.ne'
  have key : (polyaStep (m + 1) x y).1 * y - x * (polyaStep (m + 1) x y).2 =
      x * y * (x ^ m - y ^ m) / (x ^ (m + 1) + y ^ (m + 1)) := by
    simp only [polyaStep]
    field_simp
    ring
  have : 0 < x * y * (x ^ m - y ^ m) / (x ^ (m + 1) + y ^ (m + 1)) :=
    div_pos (mul_pos (mul_pos hx hy) (sub_pos.2 hpow)) hS
  linarith

/-- Linear reinforcement is neutral: with exponent one the ratio of the two sites is constant. -/
theorem polya_ratio_eq {x y : K} (hx : 0 < x) (hy : 0 < y) :
    (polyaStep 1 x y).1 * y = x * (polyaStep 1 x y).2 := by
  have hS : x ^ 1 + y ^ 1 ≠ 0 := by positivity
  simp only [polyaStep, pow_one] at hS ⊢
  field_simp

/-- Sublinear reinforcement equalizes: with exponent zero the ratio of the two sites moves toward
one at every step. -/
theorem polya_ratio_gt {x y : K} (hxy : y < x) :
    (polyaStep 0 x y).1 * y < x * (polyaStep 0 x y).2 := by
  simp only [polyaStep, pow_zero]
  norm_num
  linarith

end Polya

/-! ### Strong reinforcement localizes: the greedy walk -/

section Greedy

variable {K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K]

/-- The greedy walk's invariant: off the far node with the left edge at least as heavy, one step
keeps both. -/
theorem greedy_invariant {s : Greedy K} (h : s.pos ≠ 2 ∧ s.w12 ≤ s.w01) :
    (greedyStep s).pos ≠ 2 ∧ (greedyStep s).w12 ≤ (greedyStep s).w01 := by
  obtain ⟨pos, w01, w12⟩ := s
  obtain ⟨hp, hw⟩ := h
  fin_cases pos
  · simp [greedyStep]
    linarith
  · simp [greedyStep, not_lt.2 hw]
    linarith
  · simp at hp

/-- The control, strong reinforcement localizes: from the middle with the left edge at least as
heavy, the greedy walk never reaches the far node, at any time. -/
theorem greedy_pos_ne_two {s : Greedy K} (h : s.pos ≠ 2 ∧ s.w12 ≤ s.w01) (n : ℕ) :
    (greedyWalk s n).pos ≠ 2 := by
  have : ∀ n, (greedyWalk s n).pos ≠ 2 ∧ (greedyWalk s n).w12 ≤ (greedyWalk s n).w01 := by
    intro n
    induction n with
    | zero => simpa [greedyWalk] using h
    | succ n ih =>
      rw [greedyWalk, Function.iterate_succ_apply']
      exact greedy_invariant ih
  exact (this n).1

/-- So the far node is never visited. -/
theorem greedyVisits_two {s : Greedy K} (h : s.pos ≠ 2 ∧ s.w12 ≤ s.w01) (n : ℕ) :
    greedyVisits s n 2 = 0 := by
  unfold greedyVisits
  rw [List.length_eq_zero_iff, List.filter_eq_nil_iff]
  intro k _
  simpa using greedy_pos_ne_two h k

/-- The structural walk on the path gives the far node a quarter of its mass. -/
theorem statDist_path3_two : statDist (path3 : Matrix (Fin 3) (Fin 3) K) 2 = 1 / 4 := by
  have h0 : degree (path3 : Matrix (Fin 3) (Fin 3) K) 0 = 1 := by
    rw [degree, Fin.sum_univ_three]
    norm_num [path3]
  have h1 : degree (path3 : Matrix (Fin 3) (Fin 3) K) 1 = 2 := by
    rw [degree, Fin.sum_univ_three]
    norm_num [path3]
  have h2 : degree (path3 : Matrix (Fin 3) (Fin 3) K) 2 = 1 := by
    rw [degree, Fin.sum_univ_three]
    norm_num [path3]
  rw [statDist, Fin.sum_univ_three, h0, h1, h2]
  norm_num

/-- The greedy walk's empirical measure stays at least `1/8` from the structural stationary
distribution in total variation, at every horizon: the concentration never averages out. -/
theorem greedy_tv_ge {s : Greedy K} (h : s.pos ≠ 2 ∧ s.w12 ≤ s.w01) (n : ℕ) :
    1 / 8 ≤ tv (greedyEmp s n) (statDist (path3 : Matrix (Fin 3) (Fin 3) K)) := by
  have h2 : greedyEmp s n 2 = 0 := by simp [greedyEmp, greedyVisits_two h n]
  unfold tv
  have hterm : |greedyEmp s n 2 - statDist (path3 : Matrix (Fin 3) (Fin 3) K) 2| = 1 / 4 := by
    rw [h2, statDist_path3_two]
    norm_num
  have hle : |greedyEmp s n 2 - statDist (path3 : Matrix (Fin 3) (Fin 3) K) 2| ≤
      ∑ i, |greedyEmp s n i - statDist (path3 : Matrix (Fin 3) (Fin 3) K) i| :=
    single_le_sum (f := fun i ↦ |greedyEmp s n i - statDist (path3 : Matrix (Fin 3) (Fin 3) K) i|)
      (fun i _ ↦ abs_nonneg _) (mem_univ (2 : Fin 3))
  rw [hterm] at hle
  linarith

end Greedy

end Palace.Utility
