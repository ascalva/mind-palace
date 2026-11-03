module

public import Palace.Heat.Defs

/-!
# The heat kernel and the diffusion distance: CND-4, the statements

`core/graph/conductance.py`'s `_diffusion_distances` reads the heat kernel `H_t = e^{−tL}` of the
combinatorial Laplacian through `L = Σ λ_k φ_k φ_kᵀ`: the Gram matrix `G = Σ e^{−2tλ_k} φ_k φ_kᵀ`
and `d_t(i, j) = √(G_ii + G_jj − 2G_ij)`, CND-1's effective-resistance form applied to `G`. Here
`H_t` is the continuous functional calculus `cfc (e^{−t·}) L`, which agrees with the spectral
triple product (`Matrix.IsHermitian.cfc_eq`).

* `H_t` is symmetric, `H_0 = 1` and `H_{s+t} = H_s H_t`, so every `H_t` is invertible.
* The code's Gram matrix is `H_{2t} = H_t H_t`, and its `d_t(i, j)` is the Euclidean distance
  between the vertices' heat-kernel images `H_t eᵢ` and `H_t eⱼ`. So `d_t` is a metric on the
  vertices for every `t`: zero exactly on the diagonal, and finite and positive between vertices
  of different components, where effective resistance is `∞` (the regime split of CND-3).
* For symmetric `A ≥ 0` the distances shrink as `t` grows, since `e^{−2tλ}` decreases on the
  nonnegative spectrum.

These are the laws of `Palace/Heat.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

open Matrix

namespace Palace

variable {V : Type*} [Fintype V] [DecidableEq V]

section Heat

variable {M : Matrix V V ℝ} (hM : M.IsHermitian)

include hM

omit hM in
/-- **CND-4** The semigroup law `H_{s+t} = H_s H_t`. -/
theorem heat_add (s t : ℝ) : heat M (s + t) = heat M s * heat M t :=
  sorry

omit hM in
/-- **CND-4** The code's distance is the Euclidean distance between the vertices' heat-kernel
images. -/
theorem diffusionDist_eq (t : ℝ) (i j : V) :
    diffusionDist M t i j = dist (heatPoint M t i) (heatPoint M t j) :=
  sorry

omit hM in
/-- **CND-4** `d_t` satisfies the triangle inequality. -/
theorem diffusionDist_triangle (t : ℝ) (i j k : V) :
    diffusionDist M t i k ≤ diffusionDist M t i j + diffusionDist M t j k :=
  sorry

/-- **CND-4** `d_t` separates every two vertices, for every `t`, also across components: `H_t` is
invertible. -/
theorem diffusionDist_eq_zero_iff (t : ℝ) (i j : V) : diffusionDist M t i j = 0 ↔ i = j :=
  sorry

end Heat

/-- **CND-4** For the combinatorial Laplacian (symmetric `A ≥ 0`) diffusion distances shrink as
`t` grows: `e^{−2tλ}` decreases on the nonnegative spectrum. -/
theorem diffusionDist_antitone (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    {t t' : ℝ} (htt : t ≤ t') (i j : V) :
    diffusionDist (lap A) t' i j ≤ diffusionDist (lap A) t i j :=
  sorry

end Palace
