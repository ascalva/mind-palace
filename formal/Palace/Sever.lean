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
probability one, a bridge. That direction and its converse are the open part of L1. Design
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

end Palace.Sever
