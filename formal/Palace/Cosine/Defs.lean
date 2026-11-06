module

public import Mathlib.Analysis.InnerProductSpace.PiL2
public import Palace.Format.Defs

/-!
# Vectors stored in float16: the cosine error bound and the margin certificate, the definitions

The definitions the laws of `Palace/Cosine.lean` are stated over. With `Spec/Cosine.lean` they are
what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library proves exactly
the statements there, so no other file can change what is proved.
-/

@[expose] public section

namespace Palace.Cosine

open Palace.Format

variable {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F]

/-- The cosine similarity the vector store ranks by, `⟪q, x⟫ / (‖q‖ ‖x‖)`: LanceDB's cosine
distance is `1 − cosine`. It is `0` when either vector is zero, by Lean's division by zero. -/
noncomputable def cosine (q x : F) : ℝ := inner ℝ q x / (‖q‖ * ‖x‖)

/-- A vector as a float16 column holds it: each coordinate rounded to binary16. -/
noncomputable def round16 {ι : Type*} (x : EuclideanSpace ℝ ι) : EuclideanSpace ℝ ι :=
  WithLp.toLp 2 fun i ↦ rn16 (x i)

/-- binary16's unit roundoff, `2⁻¹¹`. -/
noncomputable abbrev u16 : ℝ := 2 ^ (-11 : ℤ)

/-- binary16's least normal magnitude, `2⁻¹⁴`: below it the rounding error is absolute. -/
noncomputable abbrev tau16 : ℝ := 2 ^ (-14 : ℤ)

/-- How far, relative to its norm, float16 storage can move a vector in `d` dimensions whose norm
is at least `ν`: `2⁻¹¹ · √(1 + d · 2⁻²⁸ / ν²)`. -/
noncomputable def eta (d : ℕ) (ν : ℝ) : ℝ := u16 * √(1 + d * tau16 ^ 2 / ν ^ 2)

/-- The storage bound: how far float16 storage can move the cosine between any query and such a
vector, `2η / (2 − η)`. -/
noncomputable def betaStore (d : ℕ) (ν : ℝ) : ℝ := 2 * eta d ν / (2 - eta d ν)

/-- The query bound: how far scoring with `q'` in place of the query `q` can move a cosine,
`2 ‖q' − q‖ / (‖q‖ + ‖q'‖)`. -/
noncomputable def betaQuery (q q' : F) : ℝ := 2 * ‖q' - q‖ / (‖q‖ + ‖q'‖)

/-- `T` is a top set of the scores `t`: every member scores at least every non-member. -/
def IsTop {κ : Type*} (t : κ → ℝ) (T : Finset κ) : Prop := ∀ i ∈ T, ∀ j ∉ T, t j ≤ t i

end Palace.Cosine
