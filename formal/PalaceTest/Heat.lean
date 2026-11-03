module

public import Palace.Heat
public import PalaceTest.Spectral
public meta import Palace.Heat
public meta import PalaceTest.Spectral

/-!
# Attacks on `Palace.Heat`

The Plausible attacks and negative controls for the laws of `Palace/Heat.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Matrix

namespace Palace

/-! ## Attacks

`H_t` has no executable form (it needs `exp` of a matrix), so CND-4 is attacked where it is
exact, over ℚ on `Fin 4`: the identity that makes `d_t` a Euclidean distance holds for the square
of any symmetric matrix, and the Gram form `√(G_ii + G_jj − 2G_ij)` satisfies the triangle
inequality for any positive semidefinite `G` (checked squared, without roots). Each control drops
the hypothesis the law needs and must be refuted.
-/

namespace Attack

/-- A random matrix on `Fin 4`, entries read off a list. -/
def mat (xs : List ℤ) : Matrix (Fin 4) (Fin 4) ℚ := fun i j ↦ xs.getD (4 * i.val + j.val) 0

/-- `d_t² = ‖H eᵢ − H eⱼ‖²` with `G = H H`, on every pair. -/
def gramIdentity (H : Matrix (Fin 4) (Fin 4) ℚ) : Bool :=
  let G := H * H
  (List.finRange 4).all fun i ↦ (List.finRange 4).all fun j ↦
    decide (G i i + G j j - 2 * G i j = ∑ k, (H k i - H k j) ^ 2)

/- CND-4: the Gram distance of `H²` is the Euclidean distance of `H`'s columns, for symmetric
`H`. -/
#eval survives (∀ xs : List ℤ, gramIdentity (mat xs + (mat xs).transpose) = true) 111

/- Control, `H` not symmetric. -/
#eval refuted (∀ xs : List ℤ, gramIdentity (mat xs) = true) 112

/-- The squared Gram distance `G_ii + G_jj − 2G_ij`, over ℚ. -/
def gramSq (G : Matrix (Fin 4) (Fin 4) ℚ) (i j : Fin 4) : ℚ := G i i + G j j - 2 * G i j

/-- The triangle inequality of `√(gramSq G)` on every triple, squared: with `a`, `b`, `x` the
squared sides, `a ≥ 0` and `x ≤ (√a + √b)²`, that is `x − a − b ≤ 0` or `(x − a − b)² ≤ 4ab`. -/
def gramTriangle (G : Matrix (Fin 4) (Fin 4) ℚ) : Bool :=
  (List.finRange 4).all fun i ↦ (List.finRange 4).all fun j ↦ (List.finRange 4).all fun k ↦
    let a := gramSq G i j
    let b := gramSq G j k
    let x := gramSq G i k
    decide (0 ≤ a ∧ (x - a - b ≤ 0 ∨ (x - a - b) ^ 2 ≤ 4 * a * b))

/- CND-4: the Gram distance is a metric for positive semidefinite `G = BᵀB`. -/
#eval survives (∀ xs : List ℤ, gramTriangle ((mat xs).transpose * mat xs) = true) 113

/- Control, `G` symmetric but indefinite. -/
#eval refuted (∀ xs : List ℤ, gramTriangle (mat xs + (mat xs).transpose) = true) 114

end Attack

end Palace
