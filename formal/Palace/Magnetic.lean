module

public import Palace.Magnetic.Defs
public import Palace.Laplacian
public import Palace.Balance
public import Mathlib.LinearAlgebra.Matrix.PosDef
public import Mathlib.LinearAlgebra.Matrix.Charpoly.Coeff
public import Mathlib.LinearAlgebra.Matrix.ToLinearEquiv

/-!
# The magnetic Laplacian: the design theorems of dn-magnetic-laplacian

`docs/design-notes/magnetic-laplacian.md` formalizes graph direction as a U(1) connection and
defers building the operator. Its results are proved here before any code, so a wrong one is
caught while it is cheap to fix:

* §2.1: `L^θ` is Hermitian and positive semidefinite, its form the twisted Dirichlet energy
  `Σ w_{uv} |x_u − e^{iθ(u,v)} x_v|²`; `θ = 0` gives the Laplacian; a gauge transform conjugates
  `L^θ` by a diagonal unitary, so the spectrum depends only on the fluxes; flux-trivial, gauge-
  trivial, a zero eigenvalue and the undirected spectrum are one condition on a connected support
  (the kernel theorem); the charge-`q` holonomy of a closed walk is `e^{2πiq·w}` with `w` its
  circulation, additive along walks; spectra are even in `q`; with sign data the `q = ½` fiber is
  the signed Laplacian.
* §2.2: `d₁^θ d₀^θ` is multiplication by `1 − e^{iF}`, so the twisted pair is a complex exactly
  on flat triangles; a triangle of one-way edges has odd circulation, so no charge in `(0, 1)`
  flattens a transitive one; a covering relation has no triangles.
* §2.3 and §2.4: a diamond's flux is `2πq(ℓ₁ − ℓ₂)`, zero when balanced; a coherent shortcut
  carries flux `2πq`; on a graded digraph every charge is gauge-trivial, so `L^{(q)}` has the
  undirected spectrum.

BRG-7 is the part the code relies on: the code's `laplacian` and `signed_laplacian` are the
`θ = 0` and sign fibers, and LAP-5's balance theorem is the kernel theorem with structure group
ℤ/2.
-/

@[expose] public section

open Matrix Finset Complex SimpleGraph
open scoped ComplexOrder

namespace Palace.Magnetic

variable {V : Type*}

/-! ## Transport -/

section Transport

theorem star_exp_mul_I (r : ℝ) : star (exp (r * I)) = exp ((-r : ℝ) * I) := by
  rw [star_def, ← exp_conj, map_mul, conj_ofReal, conj_I]
  push_cast
  ring_nf

theorem norm_transport (θ : V → V → ℝ) (u v : V) : ‖transport θ u v‖ = 1 :=
  norm_exp_ofReal_mul_I _

theorem transport_ne_zero (θ : V → V → ℝ) (u v : V) : transport θ u v ≠ 0 := exp_ne_zero _

theorem star_mul_self_of_norm_eq_one {z : ℂ} (h : ‖z‖ = 1) : star z * z = 1 := by
  rw [star_def, conj_mul', h]
  norm_num

theorem mul_star_self_of_norm_eq_one {z : ℂ} (h : ‖z‖ = 1) : z * star z = 1 := by
  rw [mul_comm, star_mul_self_of_norm_eq_one h]

theorem star_transport_mul (θ : V → V → ℝ) (u v : V) :
    star (transport θ u v) * transport θ u v = 1 :=
  star_mul_self_of_norm_eq_one (norm_transport θ u v)

/-- Exactly antisymmetric phases are a connection. -/
theorem isConnection_of_antisymm {θ : V → V → ℝ} (h : ∀ u v, θ v u = -θ u v) : IsConnection θ :=
  fun u v ↦ by rw [transport, transport, star_exp_mul_I, h]

/-- In a connection a pair's transport back is the inverse of its transport. -/
theorem transport_swap_mul {θ : V → V → ℝ} (hθ : IsConnection θ) (u v : V) :
    transport θ v u * transport θ u v = 1 := by
  rw [hθ u v, star_transport_mul]

theorem isConnection_gauge {θ : V → V → ℝ} (hθ : IsConnection θ) (ψ : V → ℝ) :
    IsConnection (gauge θ ψ) := by
  intro u v
  have e (u v : V) : transport (gauge θ ψ) u v = transport θ u v * exp ((ψ v - ψ u : ℝ) * I) := by
    rw [transport, transport, gauge, ← exp_add]
    push_cast
    ring_nf
  rw [e, e, hθ u v, star_mul, star_exp_mul_I, mul_comm]
  congr 3
  ring_nf

end Transport

variable [Fintype V] [DecidableEq V]

/-! ## The operator: Hermitian, its form the twisted Dirichlet energy, positive semidefinite -/

section Operator

variable (w : Matrix V V ℝ) (θ : V → V → ℝ)

/-- Row `u` of `L^θ x` is `Σ_v w_{uv} (x_u − e^{iθ(u,v)} x_v)`. -/
theorem magLap_mulVec_apply (x : V → ℂ) (u : V) :
    (magLap w θ *ᵥ x) u = ∑ v, (w u v : ℂ) * (x u - transport θ u v * x v) := by
  rw [magLap, sub_mulVec, Pi.sub_apply, mulVec_diagonal, degree]
  simp only [mulVec, dotProduct, magAdj, Matrix.of_apply]
  push_cast
  rw [sum_mul, ← sum_sub_distrib]
  exact sum_congr rfl fun v _ ↦ by ring

/-- §2.1: `L^θ` is Hermitian, for symmetric weights and a connection. -/
theorem isHermitian_magLap (hw : w.IsSymm) (hθ : IsConnection θ) :
    (magLap w θ).IsHermitian := by
  ext u v
  simp only [conjTranspose_apply, magLap, magAdj, Matrix.sub_apply, Matrix.diagonal_apply,
    Matrix.of_apply]
  rw [hw.apply v u, hθ u v]
  by_cases h : u = v
  · subst h
    simp only [ite_true, star_sub, star_mul', Complex.star_def, Complex.conj_ofReal,
      Complex.conj_conj]
  · simp [h, Ne.symm h]

/-- §2.1, the twisted Dirichlet identity: `2 x* L^θ x = Σ_{u,v} w_{uv} |x_u − e^{iθ(u,v)} x_v|²`. -/
theorem two_mul_dotProduct_magLap (hw : w.IsSymm) (hθ : IsConnection θ) (x : V → ℂ) :
    2 * (star x ⬝ᵥ (magLap w θ *ᵥ x)) =
      ((∑ u, ∑ v, w u v * normSq (x u - transport θ u v * x v) : ℝ) : ℂ) := by
  set t := transport θ
  have row : star x ⬝ᵥ (magLap w θ *ᵥ x) =
      ∑ u, ∑ v, (w u v : ℂ) * (star (x u) * (x u - t u v * x v)) := by
    simp only [dotProduct, magLap_mulVec_apply, mul_sum, Pi.star_apply]
    exact sum_congr rfl fun u _ ↦ sum_congr rfl fun v _ ↦ by ring
  have swap : ∑ u, ∑ v, (w u v : ℂ) * (star (x v) * (x v - t v u * x u)) =
      ∑ u, ∑ v, (w u v : ℂ) * (star (x u) * (x u - t u v * x v)) := by
    rw [sum_comm]
    exact sum_congr rfl fun u _ ↦ sum_congr rfl fun v _ ↦ by rw [hw.apply u v]
  have key (u v : V) : star (x u) * (x u - t u v * x v) + star (x v) * (x v - t v u * x u) =
      (normSq (x u - t u v * x v) : ℂ) := by
    have h1 : star (t u v) * t u v = 1 := star_transport_mul θ u v
    have h2 : t v u = star (t u v) := hθ u v
    rw [normSq_eq_conj_mul_self, ← star_def, star_sub, star_mul', h2]
    linear_combination (-(star (x v) * x v)) * h1
  rw [row, two_mul]
  nth_rewrite 2 [← swap]
  rw [← sum_add_distrib]
  push_cast
  refine sum_congr rfl fun u _ ↦ ?_
  rw [← sum_add_distrib]
  exact sum_congr rfl fun v _ ↦ by rw [← key u v]; ring

/-- §2.1: `L^θ` is positive semidefinite, for symmetric nonnegative weights and a connection. -/
theorem posSemidef_magLap (hw : w.IsSymm) (hw0 : ∀ u v, 0 ≤ w u v) (hθ : IsConnection θ) :
    (magLap w θ).PosSemidef := by
  refine .of_dotProduct_mulVec_nonneg (isHermitian_magLap w θ hw hθ) fun x ↦ ?_
  have h := two_mul_dotProduct_magLap w θ hw hθ x
  have e : star x ⬝ᵥ (magLap w θ *ᵥ x) =
      (((∑ u, ∑ v, w u v * normSq (x u - transport θ u v * x v)) / 2 : ℝ) : ℂ) := by
    push_cast at h ⊢
    linear_combination h / 2
  rw [e, zero_le_real]
  exact div_nonneg (sum_nonneg fun u _ ↦ sum_nonneg fun v _ ↦
    mul_nonneg (hw0 u v) (normSq_nonneg _)) zero_le_two

end Operator

/-! ## The fibers the code builds (BRG-7): `θ = 0` is `L`, phase `π` on negatives is `L̄` -/

section Fibers

/-- **BRG-7** At `θ = 0` the magnetic Laplacian is the Laplacian `D − A`: `q = 0` is the built
operator, exactly. -/
theorem magLap_zero (w : Matrix V V ℝ) :
    magLap w (fun _ _ ↦ 0) = (lap w).map Complex.ofReal := by
  ext u v
  simp only [magLap, magAdj, transport, lap, Matrix.map_apply, Matrix.sub_apply,
    Matrix.diagonal_apply, Matrix.of_apply]
  split_ifs <;> simp

/-- **BRG-7** With weights `|A|` and phase `π` on the negative entries, the magnetic Laplacian is
the signed Laplacian `D̄ − A`: the transports are the signs. -/
theorem magLap_signPhase (A : Matrix V V ℝ) :
    magLap (A.map abs) (signPhase A) = (signedLap A).map Complex.ofReal := by
  ext u v
  simp only [magLap, magAdj, transport, signPhase, signedLap, degree, Matrix.map_apply,
    Matrix.sub_apply,
    Matrix.diagonal_apply, Matrix.of_apply]
  split_ifs with h1 h2 h2
  · subst h1
    rw [exp_pi_mul_I, abs_of_neg h2]
    push_cast
    ring
  · subst h1
    rw [abs_of_nonneg (not_lt.mp h2)]
    simp
  · rw [exp_pi_mul_I, abs_of_neg h2]
    push_cast
    ring
  · rw [abs_of_nonneg (not_lt.mp h2)]
    simp

end Fibers

/-! ## Gauge: a transform conjugates `L^θ` by a diagonal unitary -/

section Gauge

variable (w : Matrix V V ℝ) (θ : V → V → ℝ)

omit [Fintype V] in
theorem star_gaugeMatrix (ψ : V → ℝ) : star (gaugeMatrix ψ) = gaugeMatrix (-ψ) := by
  rw [gaugeMatrix, gaugeMatrix, star_eq_conjTranspose, diagonal_conjTranspose]
  congr 1
  ext u
  simp only [Pi.star_apply, Pi.neg_apply, star_exp_mul_I]

theorem gaugeMatrix_mul_star (ψ : V → ℝ) : gaugeMatrix ψ * star (gaugeMatrix ψ) = 1 := by
  rw [star_gaugeMatrix, gaugeMatrix, gaugeMatrix, diagonal_mul_diagonal, ← diagonal_one]
  congr 1
  ext u
  rw [← exp_add]
  simp

theorem star_mul_gaugeMatrix (ψ : V → ℝ) : star (gaugeMatrix ψ) * gaugeMatrix ψ = 1 := by
  rw [star_gaugeMatrix, gaugeMatrix, gaugeMatrix, diagonal_mul_diagonal, ← diagonal_one]
  congr 1
  ext u
  rw [← exp_add]
  simp

/-- §2.1, gauge covariance: the transform `x_u ↦ e^{iψ_u} x_u` takes `L^θ` to `L^{θ + d₀ψ}`,
conjugating by a diagonal unitary. -/
theorem magLap_gauge (ψ : V → ℝ) :
    magLap w (gauge θ ψ) = star (gaugeMatrix ψ) * magLap w θ * gaugeMatrix ψ := by
  ext u v
  rw [star_gaugeMatrix, gaugeMatrix, gaugeMatrix, mul_diagonal, diagonal_mul]
  simp only [magLap, magAdj, transport, gauge, Matrix.sub_apply, Matrix.diagonal_apply,
    Matrix.of_apply,
    Pi.neg_apply]
  by_cases h : u = v
  · subst h
    simp only [ite_true, mul_sub]
    have e : exp ((-ψ u : ℝ) * I) * exp (ψ u * I) = 1 := by rw [← exp_add]; simp
    rw [show θ u u + (ψ u - ψ u) = θ u u by ring]
    linear_combination (-(↑(degree w u) - ↑(w u u) * exp (↑(θ u u) * I))) * e
  · simp only [h, ite_false, zero_sub, neg_mul, mul_neg]
    rw [mul_comm (exp _) _, mul_assoc, mul_assoc, ← exp_add, ← exp_add]
    congr 3
    push_cast
    ring

/-- §2.1: the spectrum is gauge-invariant; `L^θ` and `L^{θ + d₀ψ}` share their characteristic
polynomial. -/
theorem charpoly_magLap_gauge (ψ : V → ℝ) :
    (magLap w (gauge θ ψ)).charpoly = (magLap w θ).charpoly := by
  let U : (Matrix V V ℂ)ˣ :=
    ⟨gaugeMatrix ψ, star (gaugeMatrix ψ), gaugeMatrix_mul_star ψ, star_mul_gaugeMatrix ψ⟩
  have hinv : (U : Matrix V V ℂ)⁻¹ = star (gaugeMatrix ψ) :=
    inv_eq_right_inv (gaugeMatrix_mul_star ψ)
  rw [magLap_gauge, ← charpoly_units_conj' U (magLap w θ), hinv]

/-- `L^θ` sees `θ` only through its transports on the pairs of nonzero weight. -/
theorem magLap_congr {θ θ' : V → V → ℝ}
    (h : ∀ u v, w u v ≠ 0 → transport θ u v = transport θ' u v) : magLap w θ = magLap w θ' := by
  ext u v
  simp only [magLap, magAdj, Matrix.sub_apply, Matrix.of_apply]
  by_cases hw : w u v = 0
  · simp [hw]
  · rw [h u v hw]

/-- The transpose of `L^θ` is `L^{θᵀ}` for symmetric weights. -/
theorem transpose_magLap (hw : w.IsSymm) :
    (magLap w θ)ᵀ = magLap w (fun u v ↦ θ v u) := by
  ext u v
  simp only [transpose_apply, magLap, magAdj, transport, Matrix.sub_apply, Matrix.diagonal_apply,
    Matrix.of_apply]
  rw [hw.apply u v]
  by_cases h : u = v
  · subst h; rfl
  · simp [h, Ne.symm h]

end Gauge

/-! ## Holonomy along walks; flux-trivial is gauge-trivial -/

section Holonomy

variable {G : SimpleGraph V} {θ : V → V → ℝ}

omit [Fintype V] [DecidableEq V] in
@[simp] theorem holonomy_nil (θ : V → V → ℝ) (u : V) :
    holonomy θ (Walk.nil : G.Walk u u) = 1 := by
  simp [holonomy]

omit [Fintype V] [DecidableEq V] in
@[simp] theorem holonomy_cons (θ : V → V → ℝ) {u v x : V} (h : G.Adj u v) (p : G.Walk v x) :
    holonomy θ (Walk.cons h p) = transport θ u v * holonomy θ p := by
  simp [holonomy]

omit [Fintype V] [DecidableEq V] in
theorem holonomy_append (θ : V → V → ℝ) {u v x : V} (p : G.Walk u v) (p' : G.Walk v x) :
    holonomy θ (p.append p') = holonomy θ p * holonomy θ p' := by
  simp [holonomy, Walk.darts_append]

omit [Fintype V] [DecidableEq V] in
theorem holonomy_copy (θ : V → V → ℝ) {u v u' v' : V} (p : G.Walk u v) (hu : u = u')
    (hv : v = v') : holonomy θ (p.copy hu hv) = holonomy θ p := by
  subst hu hv
  rfl

omit [Fintype V] [DecidableEq V] in
theorem holonomy_concat (θ : V → V → ℝ) {u v x : V} (p : G.Walk u v) (h : G.Adj v x) :
    holonomy θ (p.concat h) = holonomy θ p * transport θ v x := by
  rw [Walk.concat_eq_append, holonomy_append, holonomy_cons, holonomy_nil, mul_one]

omit [Fintype V] [DecidableEq V] in
theorem norm_holonomy (θ : V → V → ℝ) {u v : V} (p : G.Walk u v) : ‖holonomy θ p‖ = 1 := by
  induction p with
  | nil => simp
  | cons h p ih => rw [holonomy_cons, norm_mul, norm_transport, ih, one_mul]

omit [Fintype V] [DecidableEq V] in
theorem holonomy_ne_zero (θ : V → V → ℝ) {u v : V} (p : G.Walk u v) : holonomy θ p ≠ 0 :=
  norm_ne_zero_iff.mp (by rw [norm_holonomy]; exact one_ne_zero)

omit [Fintype V] [DecidableEq V] in
/-- Walking a walk backwards conjugates its holonomy. -/
theorem holonomy_reverse (hθ : IsConnection θ) {u v : V} (p : G.Walk u v) :
    holonomy θ p.reverse = star (holonomy θ p) := by
  induction p with
  | nil => simp
  | cons h p ih =>
    rw [Walk.reverse_cons, holonomy_append, ih, holonomy_cons, holonomy_cons, holonomy_nil,
      mul_one, hθ, star_mul', mul_comm]

omit [Fintype V] [DecidableEq V] in
/-- On a gauge-trivial connection the holonomy of a walk is `e^{i(ψ_v − ψ_u)}`. -/
theorem holonomy_eq_of_gauge {ψ : V → ℝ}
    (hψ : ∀ ⦃u v⦄, G.Adj u v → transport θ u v = exp ((ψ v - ψ u : ℝ) * I)) {u v : V}
    (p : G.Walk u v) : holonomy θ p = exp ((ψ v - ψ u : ℝ) * I) := by
  induction p with
  | nil => simp
  | cons h p ih =>
    rw [holonomy_cons, hψ h, ih, ← exp_add]
    congr 1
    push_cast
    ring

omit [Fintype V] [DecidableEq V] in
/-- §2.1: a gauge-trivial connection is flux-trivial. -/
theorem fluxTrivial_of_gaugeTrivial (h : GaugeTrivial G θ) : FluxTrivial G θ := by
  obtain ⟨ψ, hψ⟩ := h
  intro u p
  rw [holonomy_eq_of_gauge hψ p, sub_self, ofReal_zero, zero_mul, exp_zero]

omit [Fintype V] [DecidableEq V] in
theorem exp_arg_mul_I_of_norm_eq_one {z : ℂ} (hz : ‖z‖ = 1) : exp (arg z * I) = z := by
  simpa [hz] using norm_mul_exp_arg_mul_I z

omit [Fintype V] [DecidableEq V] in
/-- §2.1: a flux-trivial connection is gauge-trivial, on any graph. In each component a root is
fixed and `ψ_v` is the argument of the holonomy of a walk from it; flux-triviality makes every
walk's holonomy the same. -/
theorem gaugeTrivial_of_fluxTrivial (hθ : IsConnection θ) (h : FluxTrivial G θ) :
    GaugeTrivial G θ := by
  classical
  let r : V → V := fun v ↦ (G.connectedComponentMk v).out
  have hr (v : V) : G.Reachable (r v) v := ConnectedComponent.exact (Quot.out_eq _)
  let p : ∀ v, G.Walk (r v) v := fun v ↦ (hr v).some
  refine ⟨fun v ↦ arg (holonomy θ (p v)), fun u v huv ↦ ?_⟩
  have hruv : r v = r u := by
    simp only [r]
    rw [ConnectedComponent.eq.mpr huv.reachable]
  have hc := h (r u) (((p u).concat huv).append ((p v).reverse.copy rfl hruv))
  rw [holonomy_append, holonomy_copy, holonomy_reverse hθ, holonomy_concat] at hc
  set a := holonomy θ (p u)
  set b := holonomy θ (p v)
  have ha : star a * a = 1 := star_mul_self_of_norm_eq_one (norm_holonomy θ _)
  have hb : star b * b = 1 := star_mul_self_of_norm_eq_one (norm_holonomy θ _)
  have e : exp ((arg b - arg a : ℝ) * I) = b * star a := by
    rw [show ((arg b - arg a : ℝ) : ℂ) * I = arg b * I + ((-arg a : ℝ) : ℂ) * I by push_cast; ring,
      exp_add, ← star_exp_mul_I, exp_arg_mul_I_of_norm_eq_one (norm_holonomy θ _),
      exp_arg_mul_I_of_norm_eq_one (norm_holonomy θ _)]
  rw [e]
  linear_combination (b * star a) * hc - transport θ u v * ha -
    (transport θ u v * star a * a) * hb

end Holonomy

/-! ## The kernel theorem: a zero eigenvalue is a flux-trivial connection -/

section Kernel

variable {w : Matrix V V ℝ} {θ : V → V → ℝ}

omit [Fintype V] [DecidableEq V] in
theorem weight_ne_zero_of_adj (hw : w.IsSymm) {u v : V} (h : (support w).Adj u v) : w u v ≠ 0 := by
  rw [support, SimpleGraph.fromRel_adj] at h
  rcases h.2 with h | h
  · exact h
  · rwa [hw.apply u v] at h

omit [Fintype V] [DecidableEq V] in
theorem adj_of_weight_ne_zero {u v : V} (huv : u ≠ v) (h : w u v ≠ 0) : (support w).Adj u v := by
  rw [support, SimpleGraph.fromRel_adj]
  exact ⟨huv, Or.inl h⟩

/-- In the kernel of `L^θ`, the values across an edge of nonzero weight differ by its transport. -/
theorem eq_transport_mul_of_mulVec_eq_zero (hw : w.IsSymm) (hw0 : ∀ u v, 0 ≤ w u v)
    (hθ : IsConnection θ) {x : V → ℂ} (hx : magLap w θ *ᵥ x = 0) {u v : V} (huv : w u v ≠ 0) :
    x u = transport θ u v * x v := by
  have h := two_mul_dotProduct_magLap w θ hw hθ x
  rw [hx, dotProduct_zero, mul_zero, eq_comm, ofReal_eq_zero] at h
  have hu := (sum_eq_zero_iff_of_nonneg fun u _ ↦ sum_nonneg fun v _ ↦
    mul_nonneg (hw0 u v) (normSq_nonneg _)).mp h u (mem_univ _)
  have huv' := (sum_eq_zero_iff_of_nonneg fun v _ ↦
    mul_nonneg (hw0 u v) (normSq_nonneg _)).mp hu v (mem_univ _)
  rcases mul_eq_zero.mp huv' with h0 | h0
  · exact absurd h0 huv
  · rwa [normSq_eq_zero, sub_eq_zero] at h0

/-- Along a walk of the support, a kernel vector is carried by the holonomy. -/
theorem eq_holonomy_mul_of_mulVec_eq_zero (hw : w.IsSymm) (hw0 : ∀ u v, 0 ≤ w u v)
    (hθ : IsConnection θ) {x : V → ℂ} (hx : magLap w θ *ᵥ x = 0) {u v : V}
    (p : (support w).Walk u v) : x u = holonomy θ p * x v := by
  induction p with
  | nil => simp
  | cons h p ih =>
    rw [holonomy_cons, mul_assoc, ← ih]
    exact eq_transport_mul_of_mulVec_eq_zero hw hw0 hθ hx (weight_ne_zero_of_adj hw h)

/-- §2.1, the kernel theorem: on a connected support, `L^θ` has a zero eigenvalue iff the
connection is flux-trivial and trivial on every weighted self-loop. -/
theorem exists_mulVec_eq_zero_iff_fluxTrivial (hw : w.IsSymm) (hw0 : ∀ u v, 0 ≤ w u v)
    (hθ : IsConnection θ) (hc : (support w).Connected) :
    (∃ x ≠ 0, magLap w θ *ᵥ x = 0) ↔ FluxTrivial (support w) θ ∧ LoopTrivial w θ := by
  constructor
  · rintro ⟨x, hx0, hx⟩
    obtain ⟨v₀, hv₀⟩ : ∃ v, x v ≠ 0 := Function.ne_iff.mp hx0
    have hnz (u : V) : x u ≠ 0 := by
      obtain ⟨p⟩ := hc.preconnected u v₀
      rw [eq_holonomy_mul_of_mulVec_eq_zero hw hw0 hθ hx p]
      exact mul_ne_zero (holonomy_ne_zero θ p) hv₀
    refine ⟨fun u p ↦ ?_, fun u hu ↦ ?_⟩
    · have e := eq_holonomy_mul_of_mulVec_eq_zero hw hw0 hθ hx p
      exact mul_right_cancel₀ (hnz u) (e.symm.trans (one_mul _).symm)
    · have e := eq_transport_mul_of_mulVec_eq_zero hw hw0 hθ hx hu
      exact mul_right_cancel₀ (hnz u) (e.symm.trans (one_mul _).symm)
  · rintro ⟨hf, hl⟩
    obtain ⟨ψ, hψ⟩ := gaugeTrivial_of_fluxTrivial hθ hf
    refine ⟨fun u ↦ exp ((-ψ u : ℝ) * I), fun h0 ↦ ?_, ?_⟩
    · obtain ⟨u⟩ := hc.nonempty
      exact exp_ne_zero _ (congrFun h0 u)
    · ext u
      rw [magLap_mulVec_apply, Pi.zero_apply]
      refine sum_eq_zero fun v _ ↦ ?_
      by_cases hwv : w u v = 0
      · simp [hwv]
      by_cases huv : u = v
      · subst huv
        rw [hl u hwv, one_mul, sub_self, mul_zero]
      · rw [hψ (adj_of_weight_ne_zero huv hwv), ← exp_add]
        rw [show ((ψ v - ψ u : ℝ) : ℂ) * I + ((-ψ v : ℝ) : ℂ) * I = ((-ψ u : ℝ) : ℂ) * I by
          push_cast; ring, sub_self, mul_zero]

/-- §2.1: on a connected support, flux-trivial (with trivial loops) is gauge-equivalence to the
undirected operator: the same characteristic polynomial as the Laplacian. -/
theorem fluxTrivial_iff_charpoly_eq (hw : w.IsSymm) (hw0 : ∀ u v, 0 ≤ w u v)
    (hθ : IsConnection θ) (hc : (support w).Connected) :
    FluxTrivial (support w) θ ∧ LoopTrivial w θ ↔
      (magLap w θ).charpoly = ((lap w).map Complex.ofReal).charpoly := by
  constructor
  · rintro ⟨hf, hl⟩
    obtain ⟨ψ, hψ⟩ := gaugeTrivial_of_fluxTrivial hθ hf
    have e : magLap w θ = magLap w (gauge (fun _ _ ↦ 0) ψ) := by
      refine magLap_congr w fun u v hwv ↦ ?_
      by_cases huv : u = v
      · subst huv
        rw [hl u hwv, transport, gauge]
        simp
      · rw [hψ (adj_of_weight_ne_zero huv hwv), transport, gauge, zero_add]
    rw [e, charpoly_magLap_gauge, magLap_zero]
  · intro h
    rw [← exists_mulVec_eq_zero_iff_fluxTrivial hw hw0 hθ hc, exists_mulVec_eq_zero_iff,
      det_eq_sign_charpoly_coeff, h, ← det_eq_sign_charpoly_coeff,
      show (lap w).map Complex.ofReal = (lap w).map (Complex.ofRealHom : ℝ → ℂ) from rfl,
      ← RingHom.mapMatrix_apply, ← RingHom.map_det, ofRealHom_eq_coe, ofReal_eq_zero,
      ← exists_mulVec_eq_zero_iff]
    obtain ⟨u⟩ := hc.nonempty
    exact ⟨1, fun h1 ↦ one_ne_zero (congrFun h1 u), lap_mulVec_one w⟩

end Kernel

/-! ## LAP-5 is the kernel theorem with structure group ℤ/2 (BRG-7) -/

section Signed

variable {A : Matrix V V ℝ}

omit [Fintype V] [DecidableEq V] in
theorem isConnection_signPhase (hA : A.IsSymm) : IsConnection (signPhase A) := by
  intro u v
  simp only [transport, signPhase, hA.apply u v]
  split_ifs <;> simp [exp_pi_mul_I]

omit [Fintype V] [DecidableEq V] in
theorem support_map_abs (A : Matrix V V ℝ) : support (A.map abs) = support A := by
  ext u v
  simp [support, SimpleGraph.fromRel_adj, Matrix.map_apply]

omit [Fintype V] [DecidableEq V] in
/-- **BRG-7** LAP-5's balance theorem is the kernel theorem with structure group ℤ/2: on a
connected support, a symmetric signed matrix is balanced iff the connection with phase `π` on
its negative entries is flux-trivial and no self-loop is negative. -/
theorem balanced_iff_fluxTrivial_signPhase [Finite V] (A : Matrix V V ℝ) (hA : A.IsSymm)
    (hc : (support A).Connected) :
    Balanced A ↔ FluxTrivial (support A) (signPhase A) ∧ ∀ u, 0 ≤ A u u := by
  have := Fintype.ofFinite V
  classical
  have hwS : (A.map abs).IsSymm := by
    ext i j
    simp only [transpose_apply, Matrix.map_apply]
    rw [hA.apply j i]
  have hw0 (u v : V) : 0 ≤ (A.map abs) u v := abs_nonneg _
  have hθ := isConnection_signPhase hA
  have hc' : (support (A.map abs)).Connected := by rwa [support_map_abs]
  have hloop : LoopTrivial (A.map abs) (signPhase A) ↔ ∀ u, 0 ≤ A u u := by
    refine forall_congr' fun u ↦ ?_
    simp only [Matrix.map_apply, abs_ne_zero, transport, signPhase]
    constructor
    · intro h
      by_contra hneg
      have e := h (ne_of_lt (not_le.mp hneg))
      rw [ite_eq_left (not_le.mp hneg), exp_pi_mul_I] at e
      norm_num at e
    · intro h _
      rw [ite_eq_right (not_lt.mpr h)]
      simp
  have hpsd : ((signedLap A).map Complex.ofReal).PosSemidef := by
    rw [← magLap_signPhase]
    exact posSemidef_magLap _ _ hwS hw0 hθ
  rw [← zero_energy_iff_balanced A hA hc, ← hloop, ← support_map_abs A,
    ← exists_mulVec_eq_zero_iff_fluxTrivial hwS hw0 hθ hc', magLap_signPhase]
  constructor
  · rintro ⟨x, hx0, hx⟩
    refine ⟨fun u ↦ (x u : ℂ), fun h ↦ hx0 (funext fun u ↦ by simpa using congrFun h u), ?_⟩
    rw [← hpsd.dotProduct_mulVec_zero_iff]
    have e : star (fun u ↦ (x u : ℂ)) ⬝ᵥ ((signedLap A).map Complex.ofReal *ᵥ fun u ↦ (x u : ℂ)) =
        ((x ⬝ᵥ (signedLap A *ᵥ x) : ℝ) : ℂ) := by
      simp only [dotProduct, mulVec, Matrix.map_apply, Pi.star_apply, Complex.star_def,
        Complex.conj_ofReal]
      push_cast
      rfl
    rw [e, hx, ofReal_zero]
  · rintro ⟨z, hz0, hz⟩
    have hdet : ((signedLap A).map Complex.ofReal).det = 0 :=
      exists_mulVec_eq_zero_iff.mp ⟨z, hz0, hz⟩
    rw [show (signedLap A).map Complex.ofReal = (signedLap A).map (Complex.ofRealHom : ℝ → ℂ)
      from rfl, ← RingHom.mapMatrix_apply, ← RingHom.map_det, ofRealHom_eq_coe,
      ofReal_eq_zero] at hdet
    obtain ⟨x, hx0, hx⟩ := exists_mulVec_eq_zero_iff.mpr hdet
    exact ⟨x, hx0, by rw [hx, dotProduct_zero]⟩

end Signed

/-! ## Charge: circulation, the flux homomorphism, evenness, graded digraphs -/

section Charge

variable {G : SimpleGraph V} (a : V → V → Prop) [DecidableRel a]

omit [Fintype V] [DecidableEq V] in
theorem arrow_swap (u v : V) : arrow a v u = -arrow a u v := by
  simp only [arrow]
  ring

omit [Fintype V] [DecidableEq V] in
theorem arrow_self (u : V) : arrow a u u = 0 := by
  simp [arrow]

omit [Fintype V] [DecidableEq V] in
/-- The charge-`q` phases are exactly antisymmetric, so they are a connection. -/
theorem isConnection_chargePhase (q : ℝ) : IsConnection (chargePhase a q) :=
  isConnection_of_antisymm fun u v ↦ by
    unfold chargePhase
    rw [arrow_swap]
    push_cast
    ring

omit [Fintype V] [DecidableEq V] in
@[simp] theorem circulation_nil (u : V) : circulation a (Walk.nil : G.Walk u u) = 0 := by
  simp [circulation]

omit [Fintype V] [DecidableEq V] in
@[simp] theorem circulation_cons {u v x : V} (h : G.Adj u v) (p : G.Walk v x) :
    circulation a (Walk.cons h p) = arrow a u v + circulation a p := by
  simp [circulation]

omit [Fintype V] [DecidableEq V] in
/-- §2.1: circulation is additive along walks. -/
theorem circulation_append {u v x : V} (p : G.Walk u v) (p' : G.Walk v x) :
    circulation a (p.append p') = circulation a p + circulation a p' := by
  simp [circulation, Walk.darts_append]

omit [Fintype V] [DecidableEq V] in
/-- §2.1: walking backwards negates the circulation, so it is a homomorphism on cycles. -/
theorem circulation_reverse {u v : V} (p : G.Walk u v) :
    circulation a p.reverse = -circulation a p := by
  induction p with
  | nil => simp
  | cons h p ih =>
    rw [Walk.reverse_cons, circulation_append, ih, circulation_cons, circulation_cons,
      circulation_nil, arrow_swap]
    ring

omit [Fintype V] [DecidableEq V] in
/-- §2.1, the elementary invariant: the charge-`q` holonomy of a walk is `e^{2πiq·w}` with `w` its
circulation, `Φ_q = χ_q ∘ w`. -/
theorem holonomy_chargePhase (q : ℝ) {u v : V} (p : G.Walk u v) :
    holonomy (chargePhase a q) p = exp ((2 * Real.pi * q * circulation a p : ℝ) * I) := by
  induction p with
  | nil => simp
  | cons h p ih =>
    rw [holonomy_cons, ih, transport, chargePhase, ← exp_add, circulation_cons]
    congr 1
    push_cast
    ring

omit [Fintype V] [DecidableEq V] in
/-- A walk whose every step goes with a one-way arrow has circulation its length. -/
theorem circulation_of_forward {u v : V} (p : G.Walk u v)
    (hp : ∀ d ∈ p.darts, a d.fst d.snd ∧ ¬a d.snd d.fst) : circulation a p = p.length := by
  induction p with
  | nil => simp
  | cons h p ih =>
    rw [circulation_cons, ih fun d hd ↦ hp d (by simp [hd]), Walk.length_cons]
    have h0 := hp _ (List.mem_cons_self ..)
    simp only [arrow, ite_eq_left h0.1, ite_eq_right h0.2]
    push_cast
    ring

omit [Fintype V] [DecidableEq V] in
/-- §2.3–§2.4: a diamond of two arrow-following arms of lengths `ℓ₁` and `ℓ₂` has flux
`2πq(ℓ₁ − ℓ₂)`. -/
theorem holonomy_diamond (q : ℝ) {s t : V} (p₁ p₂ : G.Walk s t)
    (h₁ : ∀ d ∈ p₁.darts, a d.fst d.snd ∧ ¬a d.snd d.fst)
    (h₂ : ∀ d ∈ p₂.darts, a d.fst d.snd ∧ ¬a d.snd d.fst) :
    holonomy (chargePhase a q) (p₁.append p₂.reverse) =
      exp ((2 * Real.pi * q * ((p₁.length : ℤ) - p₂.length) : ℝ) * I) := by
  rw [holonomy_chargePhase, circulation_append, circulation_reverse, circulation_of_forward a p₁ h₁,
    circulation_of_forward a p₂ h₂]
  push_cast
  ring_nf

omit [Fintype V] [DecidableEq V] in
/-- §2.3: a balanced diamond, arms of equal length, carries no flux at any charge. -/
theorem holonomy_diamond_balanced (q : ℝ) {s t : V} (p₁ p₂ : G.Walk s t)
    (h₁ : ∀ d ∈ p₁.darts, a d.fst d.snd ∧ ¬a d.snd d.fst)
    (h₂ : ∀ d ∈ p₂.darts, a d.fst d.snd ∧ ¬a d.snd d.fst) (hl : p₁.length = p₂.length) :
    holonomy (chargePhase a q) (p₁.append p₂.reverse) = 1 := by
  rw [holonomy_diamond a q p₁ p₂ h₁ h₂, hl]
  simp

omit [Fintype V] [DecidableEq V] in
/-- §2.1: shifting the charge by one changes no transport, so `q` lives on the circle. -/
theorem transport_chargePhase_add_one (q : ℝ) (u v : V) :
    transport (chargePhase a (q + 1)) u v = transport (chargePhase a q) u v := by
  rw [transport, transport, chargePhase, chargePhase,
    show ((2 * Real.pi * (q + 1) * arrow a u v : ℝ) : ℂ) * I =
      ((2 * Real.pi * q * arrow a u v : ℝ) : ℂ) * I + (arrow a u v : ℤ) * (2 * Real.pi * I) by
      push_cast; ring,
    exp_add, exp_int_mul_two_pi_mul_I, mul_one]

/-- §2.1: spectra are even in `q`: `L^{(−q)}` is the transpose of `L^{(q)}`. -/
theorem charpoly_magLap_chargePhase_neg (w : Matrix V V ℝ) (hw : w.IsSymm) (q : ℝ) :
    (magLap w (chargePhase a (-q))).charpoly = (magLap w (chargePhase a q)).charpoly := by
  rw [← charpoly_transpose (magLap w (chargePhase a q)), transpose_magLap _ _ hw]
  congr 2
  funext u v
  unfold chargePhase
  rw [arrow_swap]
  push_cast
  ring

omit [Fintype V] [DecidableEq V] in
/-- §2.4 (iii): on a graded digraph, a clock `ℓ` that rises by one along every arrow, every charge
is gauge-trivial on any graph of its arrows: `θ^{(q)} = d₀(2πqℓ)`. -/
theorem gaugeTrivial_chargePhase_of_graded {ℓ : V → ℤ} (hℓ : ∀ u v, a u v → ℓ v = ℓ u + 1)
    (hG : ∀ u v, G.Adj u v → a u v ∨ a v u) (q : ℝ) : GaugeTrivial G (chargePhase a q) := by
  refine ⟨fun v ↦ 2 * Real.pi * q * ℓ v, fun u v huv ↦ ?_⟩
  have harrow : arrow a u v = ℓ v - ℓ u := by
    rcases hG u v huv with h | h
    · have hn : ¬a v u := fun h' ↦ by have := hℓ u v h; have := hℓ v u h'; omega
      simp only [arrow, ite_eq_left h, ite_eq_right hn, hℓ u v h]
      ring
    · have hn : ¬a u v := fun h' ↦ by have := hℓ u v h'; have := hℓ v u h; omega
      simp only [arrow, ite_eq_left h, ite_eq_right hn, hℓ v u h]
      ring
  rw [transport, chargePhase, harrow]
  congr 1
  push_cast
  ring

/-- §2.4 (iii): on a graded digraph `L^{(q)}` has the spectrum of the undirected Laplacian, for
every charge: the field there carries nothing the depth gradient does not. -/
theorem charpoly_magLap_chargePhase_of_graded (w : Matrix V V ℝ) {ℓ : V → ℤ}
    (hℓ : ∀ u v, a u v → ℓ v = ℓ u + 1) (hw : ∀ u v, u ≠ v → w u v ≠ 0 → a u v ∨ a v u)
    (q : ℝ) : (magLap w (chargePhase a q)).charpoly = ((lap w).map Complex.ofReal).charpoly := by
  have hG (u v : V) (h : (support w).Adj u v) : a u v ∨ a v u := by
    rw [support, SimpleGraph.fromRel_adj] at h
    rcases h.2 with h' | h'
    · exact hw u v h.1 h'
    · exact (hw v u (Ne.symm h.1) h').symm
  obtain ⟨ψ, hψ⟩ := gaugeTrivial_chargePhase_of_graded a hℓ hG q
  have e : magLap w (chargePhase a q) = magLap w (gauge (fun _ _ ↦ 0) ψ) := by
    refine magLap_congr w fun u v hwv ↦ ?_
    by_cases huv : u = v
    · subst huv
      simp [transport, chargePhase, arrow_self, gauge]
    · rw [hψ (adj_of_weight_ne_zero huv hwv), transport, gauge, zero_add]
  rw [e, charpoly_magLap_gauge, magLap_zero]

end Charge

/-! ## Magnetic Hodge (§2.2): `d₁^θ d₀^θ = 1 − e^{iF}`, the parity obstruction, covering DAGs -/

section Hodge

variable {θ : V → V → ℝ}

omit [Fintype V] [DecidableEq V] in
/-- §2.2: `d₁^θ d₀^θ` is multiplication by `1 − e^{iF}`:
`(d₁^θ d₀^θ x)(ijk) = e^{iθ(i,k)} (1 − e^{iF(ijk)}) x_i`. -/
theorem d1_d0 (hθ : IsConnection θ) (x : V → ℂ) (i j k : V) :
    d1 θ (d0 θ x) i j k = transport θ i k * (1 - triHolonomy θ i j k) * x i := by
  have h := transport_swap_mul hθ i k
  simp only [d1, d0, triHolonomy]
  linear_combination (transport θ i j * transport θ j k * x i) * h

omit [Fintype V] [DecidableEq V] in
/-- §2.2: the twisted pair is a complex on a triangle exactly when the triangle is flat. -/
theorem d1_d0_eq_zero_iff (hθ : IsConnection θ) (i j k : V) :
    (∀ x, d1 θ (d0 θ x) i j k = 0) ↔ triHolonomy θ i j k = 1 := by
  classical
  constructor
  · intro h
    have e := h (Pi.single i 1)
    rw [d1_d0 hθ, Pi.single_eq_same, mul_one] at e
    rcases mul_eq_zero.mp e with h0 | h0
    · exact absurd h0 (transport_ne_zero θ i k)
    · exact (sub_eq_zero.mp h0).symm
  · intro h x
    rw [d1_d0 hθ, h, sub_self, mul_zero, zero_mul]

/-- §2.2's coboundary transports against §2.1's form: its energy is the operator of the reversed
connection, the conjugate `L^{−θ}`, with the spectrum of `L^θ`. -/
theorem two_mul_dotProduct_magLap_swap (w : Matrix V V ℝ) (hw : w.IsSymm) (hθ : IsConnection θ)
    (x : V → ℂ) : 2 * (star x ⬝ᵥ (magLap w (fun u v ↦ θ v u) *ᵥ x)) =
      ((∑ u, ∑ v, w u v * normSq (d0 θ x u v) : ℝ) : ℂ) := by
  have hθ' : IsConnection (fun u v ↦ θ v u) := fun u v ↦ by
    change transport θ u v = star (transport θ v u)
    rw [hθ u v, star_star]
  rw [two_mul_dotProduct_magLap w _ hw hθ']
  congr 1
  refine sum_congr rfl fun u _ ↦ sum_congr rfl fun v _ ↦ ?_
  have e : x u - transport (fun u v ↦ θ v u) u v * x v =
      -transport θ v u * (x v - transport θ u v * x u) := by
    change x u - transport θ v u * x v = _
    linear_combination (-x u) * transport_swap_mul hθ u v
  rw [e, d0, normSq_mul, normSq_neg, normSq_eq_norm_sq, norm_transport, one_pow, one_mul]

variable (a : V → V → Prop) [DecidableRel a]

omit [Fintype V] [DecidableEq V] in
theorem arrow_of_xor {u v : V} (h : Xor (a u v) (a v u)) : arrow a u v = 1 ∨ arrow a u v = -1 := by
  rcases h with ⟨h1, h2⟩ | ⟨h1, h2⟩ <;> simp [arrow, h1, h2]

omit [Fintype V] [DecidableEq V] in
/-- §2.2 (b): a triangle of one-way edges has odd circulation: `±1` (transitive) or `±3`
(cyclic). -/
theorem odd_circulation_of_oneWay {i j k : V} (hij : Xor (a i j) (a j i))
    (hjk : Xor (a j k) (a k j)) (hki : Xor (a k i) (a i k)) :
    Odd (arrow a i j + arrow a j k + arrow a k i) := by
  rcases arrow_of_xor a hij with h1 | h1 <;> rcases arrow_of_xor a hjk with h2 | h2 <;>
    rcases arrow_of_xor a hki with h3 | h3 <;> rw [h1, h2, h3] <;> decide

omit [Fintype V] [DecidableEq V] in
/-- §2.2: the charge-`q` holonomy of a triangle is flat iff `q` times its circulation is an
integer. -/
theorem triHolonomy_chargePhase_eq_one_iff (q : ℝ) (i j k : V) :
    triHolonomy (chargePhase a q) i j k = 1 ↔
      ∃ n : ℤ, q * ((arrow a i j + arrow a j k + arrow a k i : ℤ) : ℝ) = n := by
  have e : triHolonomy (chargePhase a q) i j k =
      exp (((q * ((arrow a i j + arrow a j k + arrow a k i : ℤ) : ℝ) : ℝ) : ℂ) *
        (2 * Real.pi * I)) := by
    simp only [triHolonomy, transport, chargePhase, ← exp_add]
    congr 1
    push_cast
    ring
  rw [e, exp_eq_one_iff]
  constructor
  · rintro ⟨n, hn⟩
    refine ⟨n, ?_⟩
    have h2 : (2 * Real.pi * I : ℂ) ≠ 0 := by simp [Real.pi_ne_zero, I_ne_zero]
    exact_mod_cast mul_right_cancel₀ h2 hn
  · rintro ⟨n, hn⟩
    exact ⟨n, by rw [hn]; push_cast; ring⟩

omit [Fintype V] [DecidableEq V] in
/-- §2.2 (b), the parity obstruction: a transitive triangle of one-way edges, circulation `±1`,
is flat at no charge in `(0, 1)`. -/
theorem triHolonomy_ne_one_of_transitive {q : ℝ} (hq0 : 0 < q) (hq1 : q < 1) {i j k : V}
    (hw : arrow a i j + arrow a j k + arrow a k i = 1 ∨
      arrow a i j + arrow a j k + arrow a k i = -1) :
    triHolonomy (chargePhase a q) i j k ≠ 1 := by
  rw [Ne, triHolonomy_chargePhase_eq_one_iff]
  rintro ⟨n, hn⟩
  rcases hw with hw | hw <;> rw [hw] at hn <;> push_cast at hn
  · have h0 : (0 : ℝ) < n := by linarith
    have h1 : (n : ℝ) < 1 := by linarith
    have : 0 < n := by exact_mod_cast h0
    have : n < 1 := by exact_mod_cast h1
    omega
  · have h0 : (n : ℝ) < 0 := by linarith
    have h1 : (-1 : ℝ) < n := by linarith
    have : n < 0 := by exact_mod_cast h0
    have : -1 < n := by exact_mod_cast h1
    omega

/-- §2.2 (c): a covering relation has no triangle; three elements pairwise related by covering
would need a directed cycle or a covering edge across a two-step chain. -/
theorem not_covBy_triangle {α : Type*} [PartialOrder α] (i j k : α) :
    ¬((i ⋖ j ∨ j ⋖ i) ∧ (j ⋖ k ∨ k ⋖ j) ∧ (i ⋖ k ∨ k ⋖ i)) := by
  rintro ⟨h1 | h1, h2 | h2, h3 | h3⟩
  · exact h3.2 h1.lt h2.lt
  · exact lt_irrefl _ (h1.lt.trans (h2.lt.trans h3.lt))
  · exact h1.2 h3.lt h2.lt
  · exact h2.2 h3.lt h1.lt
  · exact h2.2 h1.lt h3.lt
  · exact h1.2 h2.lt h3.lt
  · exact lt_irrefl _ (h1.lt.trans (h3.lt.trans h2.lt))
  · exact h3.2 h2.lt h1.lt

end Hodge

end Palace.Magnetic
