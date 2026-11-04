module

public import Palace.Sever.Defs
public import Palace.Rayleigh
public import Palace.Sentence
public import Palace.Spectral

/-!
# The sever horizon: `w · R_eff(a, b) ≤ 1`

The limits program's L1 (`docs/brainstorms/limits-of-the-algebra.md`): the pseudo-inverse's
response to `assume sever S a b` is Sherman–Morrison with the denominator `1 − w·R_eff(a, b)`,
and the response theory is singular where it vanishes. The denominator never goes negative. The
single edge `a ~ b` of weight `w` has `L⁺ = d dᵀ / 4w` for `d = e_a − e_b` — checked against
Penrose's equations, which determine the pseudo-inverse (SEV-1) — so its resistance on its own is
`1/w` (SEV-2); any graph carrying the edge lies above it entrywise, and Rayleigh (CND-2,
`rEff_anti`) can only lower the resistance (SEV-3). Kirchhoff reads `w·R_eff(a, b)` as the
probability that a random spanning tree contains the edge; the horizon `w·R_eff = 1` is
probability one, a bridge: `w·R_eff = 1` exactly when `a ~ b` is the only edge across some cut
(SEV-4 by Thomson's principle, SEV-5 by the maximum principle on the unit potential). Design
theorems (Palace only, no Spec rows): no code severs an edge of the backbone yet; the hypothetical
overlay (QSA-9) is where it would.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Sever

variable {V : Type*} [Fintype V] [DecidableEq V]

/-! ### SEV-1 Penrose's equations determine the pseudo-inverse -/

/-- SEV-1 A matrix satisfying Penrose's four equations for a symmetric `M` is `M⁺`: the
pseudo-inverse is characterized, so a closed form can be checked instead of computed. -/
theorem pinv_unique {M X : Matrix V V ℝ} (hM : M.IsHermitian) (h1 : M * X * M = M)
    (h2 : X * M * X = X) (h3 : (M * X)ᵀ = M * X) (h4 : (X * M)ᵀ = X * M) :
    X = pinv M hM := by
  have p1 : M * pinv M hM * M = M := mul_pinv_mul hM
  have p2 : pinv M hM * M * pinv M hM = pinv M hM := pinv_mul_pinv hM
  have hMt : Mᵀ = M := transpose_eq_of_isHermitian hM
  have hPt : (pinv M hM)ᵀ = pinv M hM := transpose_eq_of_isHermitian (isHermitian_pinv hM)
  have p3 : (M * pinv M hM)ᵀ = M * pinv M hM := by
    rw [transpose_mul, hMt, hPt, mul_pinv_comm hM]
  have p4 : (pinv M hM * M)ᵀ = pinv M hM * M := by
    rw [transpose_mul, hMt, hPt, mul_pinv_comm hM]
  -- `M X = M M⁺`: both are `(M X)(M M⁺)`, through the transposes.
  have left : M * X = M * pinv M hM := by
    calc M * X = (M * X)ᵀ := h3.symm
      _ = Xᵀ * (M * pinv M hM * M)ᵀ := by rw [p1, transpose_mul]
      _ = (M * X)ᵀ * (M * pinv M hM)ᵀ := by simp only [transpose_mul, Matrix.mul_assoc]
      _ = M * X * (M * pinv M hM) := by rw [h3, p3]
      _ = M * pinv M hM := by rw [← Matrix.mul_assoc, h1]
  -- `X M = M⁺ M`: both are `(M⁺ M)(X M)`.
  have right : X * M = pinv M hM * M := by
    calc X * M = (X * M)ᵀ := h4.symm
      _ = (M * pinv M hM * M)ᵀ * Xᵀ := by rw [p1, transpose_mul]
      _ = (pinv M hM * M)ᵀ * (X * M)ᵀ := by simp only [transpose_mul, Matrix.mul_assoc]
      _ = pinv M hM * M * (X * M) := by rw [h4, p4]
      _ = pinv M hM * M := by
        rw [Matrix.mul_assoc, ← Matrix.mul_assoc M X M, h1]
  calc X = X * M * X := h2.symm
    _ = X * M * pinv M hM := by rw [Matrix.mul_assoc X M X, left, ← Matrix.mul_assoc]
    _ = pinv M hM * M * pinv M hM := by rw [right]
    _ = pinv M hM := p2

/-! ### SEV-2 The single edge: `L⁺ = d dᵀ / 4w`, so `R_eff(a, b) = 1/w` -/

omit [Fintype V] in
/-- `e_a − e_b` as a difference of basis vectors. -/
theorem dvec_eq (a b : V) : Query.dvec a b (1 : ℝ) = Pi.single a 1 - Pi.single b 1 := by
  ext i
  simp [Query.dvec, Pi.single_apply]

/-- `‖e_a − e_b‖² = 2`. -/
theorem dvec_dotProduct_self {a b : V} (hab : a ≠ b) :
    Query.dvec a b (1 : ℝ) ⬝ᵥ Query.dvec a b 1 = 2 := by
  rw [dvec_eq]
  norm_num [sub_dotProduct, single_dotProduct, Pi.single_apply, hab, hab.symm]

/-- The outer product of `d` squares to twice itself. -/
theorem vecMulVec_dvec_sq {a b : V} (hab : a ≠ b) :
    vecMulVec (Query.dvec a b (1 : ℝ)) (Query.dvec a b 1) *
      vecMulVec (Query.dvec a b 1) (Query.dvec a b 1) =
      (2 : ℝ) • vecMulVec (Query.dvec a b 1) (Query.dvec a b 1) := by
  rw [vecMulVec_mul_vecMulVec, dvec_dotProduct_self hab, vecMulVec_smul]

omit [Fintype V] in
/-- The outer product of `d` with itself is symmetric. -/
theorem transpose_vecMulVec_dvec (a b : V) :
    (vecMulVec (Query.dvec a b (1 : ℝ)) (Query.dvec a b 1))ᵀ =
      vecMulVec (Query.dvec a b 1) (Query.dvec a b 1) :=
  transpose_vecMulVec _ _

/-- SEV-2 The single edge's Laplacian is the rank-one `w d dᵀ` (QSA-9 on the empty graph). -/
theorem lap_single {a b : V} (hab : a ≠ b) (w : ℝ) :
    lap (single a b w) = w • vecMulVec (Query.dvec a b 1) (Query.dvec a b 1) := by
  unfold single
  rw [Query.lap_assumeEdge (0 : Matrix V V ℝ) hab w]
  have h0 : degree (0 : Matrix V V ℝ) = 0 := by
    funext i
    simp [degree]
  simp [lap, h0]

omit [Fintype V] in
theorem isSymm_single (a b : V) (w : ℝ) : (single a b w).IsSymm :=
  Query.isSymm_assumeEdge isSymm_zero a b w

/-- SEV-2 The single edge's pseudo-inverse is `d dᵀ / 4w`: checked against Penrose's equations
rather than computed through the spectrum. -/
theorem lapPinv_single {a b : V} (hab : a ≠ b) {w : ℝ} (hw : w ≠ 0)
    (h : (single a b w).IsSymm) :
    lapPinv (single a b w) h =
      (1 / (4 * w)) • vecMulVec (Query.dvec a b 1) (Query.dvec a b 1) := by
  unfold lapPinv
  refine (pinv_unique _ ?_ ?_ ?_ ?_).symm <;> rw [lap_single hab w]
  · simp only [Matrix.smul_mul, Matrix.mul_smul, smul_smul, vecMulVec_dvec_sq hab]
    congr 1
    field_simp
    ring
  · simp only [Matrix.smul_mul, Matrix.mul_smul, smul_smul, vecMulVec_dvec_sq hab]
    congr 1
    field_simp
    ring
  · simp only [Matrix.smul_mul, Matrix.mul_smul, smul_smul, vecMulVec_dvec_sq hab,
      transpose_smul, transpose_vecMulVec_dvec]
  · simp only [Matrix.smul_mul, Matrix.mul_smul, smul_smul, vecMulVec_dvec_sq hab,
      transpose_smul, transpose_vecMulVec_dvec]

/-- SEV-2 On its own, the edge's resistance is `1/w`. -/
theorem rEff_single {a b : V} (hab : a ≠ b) {w : ℝ} (hw : w ≠ 0) (h : (single a b w).IsSymm) :
    rEff (lapPinv (single a b w) h) a b = 1 / w := by
  rw [lapPinv_single hab hw h]
  simp [rEff, Matrix.smul_apply, vecMulVec_apply, Query.dvec, hab, hab.symm]
  field_simp
  ring

/-! ### SEV-3 The horizon: `w · R_eff(a, b) ≤ 1` -/

omit [Fintype V] in
theorem single_nonneg {a b : V} {w : ℝ} (hw : 0 ≤ w) (i j : V) : 0 ≤ single a b w i j := by
  simp only [single, Query.assumeEdge, of_apply, Matrix.zero_apply, zero_add]
  split_ifs
  · exact hw
  · exact le_rfl

omit [Fintype V] in
/-- The single edge lies under any symmetric nonnegative graph carrying it. -/
theorem single_le {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) (a b i j : V) :
    single a b (A a b) i j ≤ A i j := by
  simp only [single, Query.assumeEdge, of_apply, Matrix.zero_apply, zero_add]
  split_ifs with h
  · rcases h with ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩
    · exact le_rfl
    · exact (hA.apply _ _).ge
  · exact hw i j

omit [Fintype V] in
/-- The edge is an adjacency of its own support. -/
theorem single_reachable {a b : V} (hab : a ≠ b) {w : ℝ} (hw : w ≠ 0) :
    (support (single a b w)).Reachable a b :=
  SimpleGraph.Adj.reachable ((SimpleGraph.fromRel_adj _ _ _).2
    ⟨hab, Or.inl (by simpa [single, Query.assumeEdge] using hw)⟩)

/-- SEV-3 The horizon bound: an edge's weight times the effective resistance across it is at
most one — the single edge alone has resistance `1/w`, and the rest of the graph can only lower
it (Rayleigh, CND-2). -/
theorem mul_rEff_le_one {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) {a b : V}
    (hab : a ≠ b) : A a b * rEff (lapPinv A hA) a b ≤ 1 := by
  rcases (hw a b).lt_or_eq with hpos | hzero
  · have hS := isSymm_single a b (A a b)
    have hle := rEff_anti hS hA (single_nonneg hpos.le) (single_le hA hw a b)
      (single_reachable hab hpos.ne')
    rw [rEff_single hab hpos.ne' hS] at hle
    calc A a b * rEff (lapPinv A hA) a b ≤ A a b * (1 / A a b) :=
          mul_le_mul_of_nonneg_left hle hpos.le
      _ = 1 := mul_one_div_cancel hpos.ne'
  · rw [← hzero, zero_mul]
    exact zero_le_one

/-- SEV-3 The sever's Sherman–Morrison denominator `1 − w·R_eff(a, b)` is never negative: the
response theory of `assume sever` is regular or at its horizon, never past it. -/
theorem one_sub_mul_rEff_nonneg {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    {a b : V} (hab : a ≠ b) : 0 ≤ 1 - A a b * rEff (lapPinv A hA) a b :=
  sub_nonneg.2 (mul_rEff_le_one hA hw hab)

/-! ### SEV-4 A bridge sits on the horizon -/

omit [Fintype V] in
/-- With the edge `a ~ b` taken out, nothing crosses the cut, so the test potential `c·1_S` costs
nothing on what is left: every term of the energy's double sum vanishes. -/
theorem sub_single_mul_sq_eq_zero {A : Matrix V V ℝ} (hA : A.IsSymm) {a b : V} {S : Finset V}
    (haS : a ∈ S) (hbS : b ∉ S) (hcut : ∀ i ∈ S, ∀ j ∉ S, (i = a ∧ j = b) ∨ A i j = 0)
    (c : ℝ) (i j : V) :
    (A - single a b (A a b)) i j *
      ((if i ∈ S then c else 0) - (if j ∈ S then c else 0)) ^ 2 = 0 := by
  by_cases hi : i ∈ S <;> by_cases hj : j ∈ S
  · simp [hi, hj]
  · by_cases hab' : i = a ∧ j = b
    · rw [hab'.1, hab'.2]
      simp [single, Query.assumeEdge]
    · rcases hcut i hi j hj with h | h0
      · exact absurd h hab'
      · have hib : ¬ i = b := fun h ↦ hbS (h ▸ hi)
        simp [single, Query.assumeEdge, h0, hab', hib]
  · by_cases hba' : i = b ∧ j = a
    · rw [hba'.1, hba'.2]
      simp [single, Query.assumeEdge, hA.apply a b]
    · rcases hcut j hj i hi with h | h0
      · exact absurd ⟨h.2, h.1⟩ hba'
      · have h0' : A i j = 0 := by rwa [← hA.apply i j]
        have hia : ¬ i = a := fun h ↦ hi (h ▸ haS)
        simp [single, Query.assumeEdge, h0', hia, hba']
  · simp [hi, hj]

/-- The test potential's energy on the bridgeless rest is zero. -/
theorem dotProduct_lap_sub_single {A : Matrix V V ℝ} (hA : A.IsSymm) {a b : V} {S : Finset V}
    (haS : a ∈ S) (hbS : b ∉ S) (hcut : ∀ i ∈ S, ∀ j ∉ S, (i = a ∧ j = b) ∨ A i j = 0)
    (c : ℝ) :
    (fun i ↦ if i ∈ S then c else 0) ⬝ᵥ
      (lap (A - single a b (A a b)) *ᵥ fun i ↦ if i ∈ S then c else 0) = 0 := by
  have h := two_mul_dotProduct_lap (A - single a b (A a b)) (hA.sub (isSymm_single a b (A a b)))
    (fun i ↦ if i ∈ S then c else 0)
  have hz : ∑ i, ∑ j, (A - single a b (A a b)) i j *
      ((if i ∈ S then c else 0) - (if j ∈ S then c else 0)) ^ 2 = 0 :=
    sum_eq_zero fun i _ ↦ sum_eq_zero fun j _ ↦ sub_single_mul_sq_eq_zero hA haS hbS hcut c i j
  rw [hz] at h
  linarith

/-- SEV-4 A bridge sits on the horizon: when `a ~ b` is the only edge across some cut, the
resistance across it is exactly `1/w` and `w·R_eff(a, b) = 1` — Thomson's principle with the
test potential `(1/w)·1_S` meets SEV-3's bound. `assume sever` of a bridge is the singular case:
the Sherman–Morrison denominator vanishes, and the symbolic rule "removing weight raises every
resistance through the edge" degenerates to infinity. -/
theorem mul_rEff_eq_one_of_bridge {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    {a b : V} (hab : a ≠ b) (hpos : 0 < A a b) (hS : IsBridgeCut A a b) :
    A a b * rEff (lapPinv A hA) a b = 1 := by
  obtain ⟨S, haS, hbS, hcut⟩ := hS
  refine le_antisymm (mul_rEff_le_one hA hw hab) ?_
  have hr : (support A).Reachable a b :=
    SimpleGraph.Adj.reachable ((SimpleGraph.fromRel_adj _ _ _).2 ⟨hab, Or.inl hpos.ne'⟩)
  have hP := posSemidef_lap A hA hw
  have hv : lap A *ᵥ (lapPinv A hA *ᵥ (Pi.single a 1 - Pi.single b 1)) =
      Pi.single a 1 - Pi.single b 1 :=
    mulVec_pinv_mulVec_of_orthogonal hP.isHermitian (orthogonal_ker_lap hA hw hr)
  have ht := thomson hP hv (fun i ↦ if i ∈ S then 1 / A a b else 0)
  have hdx : (Pi.single a 1 - Pi.single b 1) ⬝ᵥ (fun i ↦ if i ∈ S then 1 / A a b else 0) =
      1 / A a b := by
    simp [sub_dotProduct, single_dotProduct, haS, hbS]
  have hsplit : lap A = lap (single a b (A a b)) + lap (A - single a b (A a b)) := by
    rw [← lap_sub_lap]
    abel
  have hxLx : (fun i ↦ if i ∈ S then 1 / A a b else 0) ⬝ᵥ
      (lap A *ᵥ fun i ↦ if i ∈ S then 1 / A a b else 0) = 1 / A a b := by
    rw [hsplit, add_mulVec, dotProduct_add, dotProduct_lap_sub_single hA haS hbS hcut, add_zero,
      lap_single hab, smul_mulVec, dotProduct_smul, Query.dotProduct_vecMulVec_self_mulVec,
      dvec_eq, hdx, smul_eq_mul]
    field_simp
  rw [hdx, hxLx] at ht
  have key : 1 / A a b ≤ (Pi.single a 1 - Pi.single b 1) ⬝ᵥ
      (lapPinv A hA *ᵥ (Pi.single a 1 - Pi.single b 1)) := by
    have e : 2 * (1 / A a b) - 1 / A a b = 1 / A a b := by ring
    rw [← e]
    exact ht
  rw [rEff_eq_dotProduct (isHermitian_lapPinv A hA)]
  calc (1 : ℝ) = A a b * (1 / A a b) := (mul_one_div_cancel hpos.ne').symm
    _ ≤ A a b * ((Pi.single a 1 - Pi.single b 1) ⬝ᵥ
        (lapPinv A hA *ᵥ (Pi.single a 1 - Pi.single b 1))) :=
      mul_le_mul_of_nonneg_left key hpos.le

/-! ### SEV-5 Off a bridge the horizon is not reached: the horizon is exactly the bridges -/

omit [Fintype V] [DecidableEq V] in
/-- An adjacency of the support is a nonzero entry. -/
theorem ne_zero_of_support_adj {A : Matrix V V ℝ} (hA : A.IsSymm) {i j : V}
    (h : (support A).Adj i j) : A i j ≠ 0 := by
  simp only [support, SimpleGraph.fromRel_adj] at h
  rcases h.2 with h0 | h0
  · exact h0
  · rwa [hA.apply i j] at h0

omit [Fintype V] [DecidableEq V] in
/-- At a vertex of `a`'s component where the potential is largest, every term of its Laplacian
row is nonnegative: a neighbour is in the component too, so it sits no higher. -/
theorem row_terms_nonneg {A : Matrix V V ℝ} (hw : ∀ i j, 0 ≤ A i j) {a : V} {x : V → ℝ}
    {w : V} (hwr : (support A).Reachable a w)
    (hmax : ∀ u, (support A).Reachable a u → x u ≤ x w) (j : V) :
    0 ≤ A w j * (x w - x j) := by
  by_cases hAj : A w j = 0
  · simp [hAj]
  · by_cases hjw : j = w
    · simp [hjw]
    · have hadj : (support A).Adj w j := by
        simp only [support, SimpleGraph.fromRel_adj]
        exact ⟨Ne.symm hjw, Or.inl hAj⟩
      exact mul_nonneg (hw w j) (sub_nonneg.2 (hmax j (hwr.trans hadj.reachable)))

/-- A harmonic vertex at the component's maximum passes the maximum to every neighbour: its row
of `L x = e_a − e_b` sums to zero with nonnegative terms, so each vanishes. -/
theorem eq_of_harmonic_max {A : Matrix V V ℝ} (hw : ∀ i j, 0 ≤ A i j) {a b : V} {x : V → ℝ}
    (hx : lap A *ᵥ x = Pi.single a 1 - Pi.single b 1) {w : V}
    (hwr : (support A).Reachable a w) (hmax : ∀ u, (support A).Reachable a u → x u ≤ x w)
    (hwa : w ≠ a) (hwb : w ≠ b) {j : V} (hAj : A w j ≠ 0) : x j = x w := by
  have hrow : ∑ j, A w j * (x w - x j) = 0 := by
    rw [← lap_mulVec_apply, hx]
    simp [hwa, hwb]
  have hzero := (sum_eq_zero_iff_of_nonneg fun j _ ↦ row_terms_nonneg hw hwr hmax j).1 hrow j
    (mem_univ j)
  rcases mul_eq_zero.1 hzero with h | h
  · exact absurd h hAj
  · exact (sub_eq_zero.1 h).symm

/-- The sink is never the component's maximum: its row of `L x = e_a − e_b` sums to `−1`. -/
theorem sink_not_max {A : Matrix V V ℝ} (hw : ∀ i j, 0 ≤ A i j) {a b : V} {x : V → ℝ}
    (hx : lap A *ᵥ x = Pi.single a 1 - Pi.single b 1) (hab : a ≠ b)
    (hbr : (support A).Reachable a b) (hmax : ∀ u, (support A).Reachable a u → x u ≤ x b) :
    False := by
  have hrow : ∑ j, A b j * (x b - x j) = -1 := by
    rw [← lap_mulVec_apply, hx]
    simp [hab.symm]
  have := sum_nonneg fun j (_ : j ∈ univ) ↦ row_terms_nonneg hw hbr hmax j
  linarith

/-- The maximum principle for the unit potential `x = L⁺(e_a − e_b)`: on `a`'s component the
potential is largest at the source. A maximum elsewhere would travel, vertex by harmonic vertex,
along a walk back to the source — and the sink cannot carry it. -/
theorem potential_le_source {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    {a b : V} (hab : a ≠ b) {x : V → ℝ} (hx : lap A *ᵥ x = Pi.single a 1 - Pi.single b 1)
    {u : V} (hu : (support A).Reachable a u) : x u ≤ x a := by
  classical
  obtain ⟨v, hvS, hv⟩ := (univ.filter fun w ↦ (support A).Reachable a w).exists_max_image x
    ⟨a, mem_filter.2 ⟨mem_univ a, SimpleGraph.Reachable.refl a⟩⟩
  have hvr : (support A).Reachable a v := (mem_filter.1 hvS).2
  have hmaxv : ∀ w, (support A).Reachable a w → x w ≤ x v :=
    fun w hw' ↦ hv w (mem_filter.2 ⟨mem_univ w, hw'⟩)
  by_contra hcon
  push Not at hcon
  have hva : x a < x v := hcon.trans_le (hmaxv u hu)
  have walk : ∀ w t, (support A).Reachable a w → x w = x v → (support A).Walk w t → t = a →
      False := by
    intro w t hwr hwv p
    revert hwr hwv
    induction p with
    | nil => intro _ hwv hta; rw [hta] at hwv; exact hva.ne hwv
    | @cons w w' t hadj p' ih =>
      intro hwr hwv hta
      have hmaxw : ∀ u, (support A).Reachable a u → x u ≤ x w :=
        fun u hu' ↦ (hmaxv u hu').trans_eq hwv.symm
      have hwa : w ≠ a := fun h ↦ hva.ne (by rw [← h]; exact hwv)
      have hwb : w ≠ b := by
        rintro rfl
        exact sink_not_max hw hx hab hwr hmaxw
      have hw' : x w' = x w :=
        eq_of_harmonic_max hw hx hwr hmaxw hwa hwb (ne_zero_of_support_adj hA hadj)
      exact ih (hwr.trans hadj.reachable) (hw'.trans hwv) hta
  obtain ⟨p⟩ := hvr.symm
  exact walk v a hvr rfl p rfl

/-- SEV-5 Off a bridge the horizon is not reached: when `a` still reaches `b` without the edge
`a ~ b`, `w·R_eff(a, b) < 1`. The unit current out of `a` splits between the edge and the other
neighbours; by the maximum principle every share is nonnegative, and if the others carried
nothing, every vertex along the detour would sit at the source potential — `b` too, and the
resistance would vanish. -/
theorem mul_rEff_lt_one_of_reachable {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    {a b : V} (hab : a ≠ b) (hpos : 0 < A a b)
    (hdetour : (support (A - single a b (A a b))).Reachable a b) :
    A a b * rEff (lapPinv A hA) a b < 1 := by
  have hA₀s : (A - single a b (A a b)).IsSymm := hA.sub (isSymm_single a b (A a b))
  have hw₀ : ∀ i j, 0 ≤ (A - single a b (A a b)) i j :=
    fun i j ↦ sub_nonneg.2 (single_le hA hw a b i j)
  have hle₀ : ∀ i j, (A - single a b (A a b)) i j ≤ A i j :=
    fun i j ↦ sub_le_self _ (single_nonneg hpos.le i j)
  have hr : (support A).Reachable a b := hdetour.mono (support_mono hw₀ hle₀)
  obtain ⟨x, hxdef⟩ : ∃ x : V → ℝ, lapPinv A hA *ᵥ (Pi.single a 1 - Pi.single b 1) = x :=
    ⟨_, rfl⟩
  have hP := posSemidef_lap A hA hw
  have hx : lap A *ᵥ x = Pi.single a 1 - Pi.single b 1 := by
    rw [← hxdef]
    exact mulVec_pinv_mulVec_of_orthogonal hP.isHermitian (orthogonal_ker_lap hA hw hr)
  have hreff : rEff (lapPinv A hA) a b = x a - x b := by
    rw [rEff_eq_dotProduct (isHermitian_lapPinv A hA), hxdef]
    simp [sub_dotProduct, single_dotProduct]
  have hmax : ∀ u, (support A).Reachable a u → x u ≤ x a :=
    fun u hu ↦ potential_le_source hA hw hab hx hu
  have hrow : ∑ j, A a j * (x a - x j) = 1 := by
    rw [← lap_mulVec_apply, hx]
    simp [hab]
  have hsplit : A a b * (x a - x b) + ∑ j ∈ univ.erase b, A a j * (x a - x j) = 1 := by
    rw [← hrow]
    exact add_sum_erase univ (fun j ↦ A a j * (x a - x j)) (mem_univ b)
  have hterm : ∀ j, 0 ≤ A a j * (x a - x j) :=
    row_terms_nonneg hw (SimpleGraph.Reachable.refl a) hmax
  have hrest : 0 < ∑ j ∈ univ.erase b, A a j * (x a - x j) := by
    refine lt_of_le_of_ne (sum_nonneg fun j _ ↦ hterm j) fun h0 ↦ ?_
    have hzero : ∀ j ∈ univ.erase b, A a j * (x a - x j) = 0 :=
      (sum_eq_zero_iff_of_nonneg fun j _ ↦ hterm j).1 h0.symm
    have hnb : ∀ j, j ≠ b → A a j ≠ 0 → x j = x a := by
      intro j hjb hAj
      rcases mul_eq_zero.1 (hzero j (mem_erase.2 ⟨hjb, mem_univ j⟩)) with h | h
      · exact absurd h hAj
      · exact (sub_eq_zero.1 h).symm
    -- along the detour the source potential travels, all the way to the sink
    have walk : ∀ w t, (support A).Reachable a w → x w = x a →
        (support (A - single a b (A a b))).Walk w t → t = b → x b = x a := by
      intro w t hwr hwa p
      revert hwr hwa
      induction p with
      | nil => intro _ hwa htb; rw [← htb]; exact hwa
      | @cons w w' t hadj p' ih =>
        intro hwr hwa htb
        have h0 : (A - single a b (A a b)) w w' ≠ 0 := ne_zero_of_support_adj hA₀s hadj
        have hw'r : (support A).Reachable a w' :=
          hwr.trans (SimpleGraph.Adj.reachable (support_mono hw₀ hle₀ hadj))
        by_cases hwb : w = b
        · rw [← hwb]; exact hwa
        refine ih hw'r ?_ htb
        by_cases hwa' : w = a
        · have hw'b : w' ≠ b := by
            rintro rfl
            apply h0
            rw [hwa']
            simp [single, Query.assumeEdge]
          have hAw' : A a w' ≠ 0 := by
            intro hz
            apply h0
            rw [hwa', Matrix.sub_apply, hz]
            simp [single, Query.assumeEdge, hw'b, hab]
          exact hnb w' hw'b hAw'
        · have hAw' : A w w' ≠ 0 := by
            intro hz
            apply h0
            rw [Matrix.sub_apply, hz]
            simp [single, Query.assumeEdge, hwa', hwb]
          exact (eq_of_harmonic_max hw hx hwr (fun u hu ↦ (hmax u hu).trans_eq hwa.symm) hwa' hwb
            hAw').trans hwa
    obtain ⟨p⟩ := hdetour
    have hxb : x b = x a := walk a b (SimpleGraph.Reachable.refl a) rfl p rfl
    have := rEff_pos hA hw hr hab
    rw [hreff, hxb, sub_self] at this
    exact lt_irrefl _ this
  rw [hreff]
  linarith

omit [Fintype V] in
/-- A bridge, read as a cut: `a ~ b` is the only edge across some cut iff `a` cannot reach `b`
without it. -/
theorem isBridgeCut_iff_not_reachable [Finite V] {A : Matrix V V ℝ} (hA : A.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) {a b : V} :
    IsBridgeCut A a b ↔ ¬ (support (A - single a b (A a b))).Reachable a b := by
  classical
  have := Fintype.ofFinite V
  constructor
  · rintro ⟨S, haS, hbS, hcut⟩ ⟨p⟩
    -- a walk without the edge never leaves `S`, so it never arrives at `b`
    have stay : ∀ w t, w ∈ S → (support (A - single a b (A a b))).Walk w t → t = b → b ∈ S := by
      intro w t hwS p
      revert hwS
      induction p with
      | nil => intro hwS htb; rw [← htb]; exact hwS
      | @cons w w' t hadj p' ih =>
        intro hwS htb
        refine ih ?_ htb
        by_contra hw'S
        have h0 : (A - single a b (A a b)) w w' ≠ 0 :=
          ne_zero_of_support_adj (hA.sub (isSymm_single a b (A a b))) hadj
        apply h0
        rw [Matrix.sub_apply]
        rcases hcut w hwS w' hw'S with ⟨rfl, rfl⟩ | hz
        · simp [single, Query.assumeEdge]
        · have h1 := single_le hA hw a b w w'
          have h2 := single_nonneg (a := a) (b := b) (hw a b) w w'
          linarith
    exact hbS (stay a b haS p rfl)
  · intro hnr
    refine ⟨univ.filter fun v ↦ (support (A - single a b (A a b))).Reachable a v,
      mem_filter.2 ⟨mem_univ a, SimpleGraph.Reachable.refl a⟩,
      fun h ↦ hnr (mem_filter.1 h).2, ?_⟩
    intro i hi j hj
    rw [mem_filter] at hi hj
    by_contra hc
    obtain ⟨h1, h2⟩ := not_or.1 hc
    have hib : i ≠ b := fun h ↦ hnr (h ▸ hi.2)
    have hij : i ≠ j := fun h ↦ hj ⟨mem_univ j, h ▸ hi.2⟩
    have h0 : (A - single a b (A a b)) i j ≠ 0 := by
      rw [Matrix.sub_apply]
      have : single a b (A a b) i j = 0 := by
        simp [single, Query.assumeEdge, h1, hib]
      rw [this, sub_zero]
      exact h2
    have hadj : (support (A - single a b (A a b))).Adj i j := by
      simp only [support, SimpleGraph.fromRel_adj]
      exact ⟨hij, Or.inl h0⟩
    exact hj ⟨mem_univ j, hi.2.trans hadj.reachable⟩

/-- SEV-5 The horizon is exactly the bridges: `w·R_eff(a, b) = 1` iff `a ~ b` is the only edge
across some cut. -/
theorem mul_rEff_eq_one_iff {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    {a b : V} (hab : a ≠ b) (hpos : 0 < A a b) :
    A a b * rEff (lapPinv A hA) a b = 1 ↔ IsBridgeCut A a b := by
  constructor
  · intro h
    by_contra hnb
    have hr : (support (A - single a b (A a b))).Reachable a b := by
      by_contra hnr
      exact hnb ((isBridgeCut_iff_not_reachable hA hw).2 hnr)
    exact (mul_rEff_lt_one_of_reachable hA hw hab hpos hr).ne h
  · exact mul_rEff_eq_one_of_bridge hA hw hab hpos

/-- SEV-5 `assume sever`'s Sherman–Morrison denominator vanishes exactly at a bridge: the
response theory of a sever is singular precisely where severing disconnects. -/
theorem one_sub_mul_rEff_eq_zero_iff {A : Matrix V V ℝ} (hA : A.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) {a b : V} (hab : a ≠ b) (hpos : 0 < A a b) :
    1 - A a b * rEff (lapPinv A hA) a b = 0 ↔ IsBridgeCut A a b := by
  rw [sub_eq_zero, eq_comm, mul_rEff_eq_one_iff hA hw hab hpos]

end Palace.Sever
