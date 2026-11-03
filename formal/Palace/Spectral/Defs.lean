module

public import Mathlib.Analysis.Matrix.HermitianFunctionalCalculus
public import Mathlib.Analysis.Matrix.PosDef
public import Mathlib.Analysis.Real.Sqrt
public import Mathlib.Algebra.Order.Star.Real
public import Palace.Laplacian.Defs

/-!
# The normalized Laplacian and the pseudo-inverse: LAP-4, L_sym PSD, L⁺, the definitions

The definitions the laws of `Palace/Spectral.lean` are stated over. With `Spec/Spectral.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

open Matrix Finset Unitary

namespace Palace

variable {V R : Type*} [Fintype V] [DecidableEq V]

/-! ### `L_sym` -/

/-- `D^{-1/2}`, with `0` at degree `0`: `np.where(d > 0, 1/√d, 0)` in `laplacian_sym`. -/
noncomputable def invSqrtDegree (A : Matrix V V ℝ) (i : V) : ℝ :=
  if 0 < degree A i then (√(degree A i))⁻¹ else 0

/-- The normalized Laplacian `L_sym = I − D^{-1/2} A D^{-1/2}` (`laplacian.py`, `laplacian_sym`). -/
noncomputable def lapSym (A : Matrix V V ℝ) : Matrix V V ℝ :=
  1 - diagonal (invSqrtDegree A) * A * diagonal (invSqrtDegree A)

/-! ### `L⁺` -/

/-- `L` is Hermitian whenever `A` is symmetric (over ℝ, Hermitian is symmetric). -/
theorem isHermitian_lap (A : Matrix V V ℝ) (hA : A.IsSymm) : (lap A).IsHermitian := by
  rw [IsHermitian, conjTranspose_eq_transpose_of_trivial]
  simp only [lap, transpose_sub, diagonal_transpose, hA.eq]

/-- The Moore–Penrose pseudo-inverse of a real symmetric matrix, through its spectral
decomposition: `M = U diag(λ) Uᵀ` gives `M⁺ = U diag(λ⁻¹) Uᵀ`, and Lean's `0⁻¹ = 0` is the
pseudo-inverse's own convention on the kernel. -/
noncomputable def pinv (M : Matrix V V ℝ) (hM : M.IsHermitian) : Matrix V V ℝ := hM.cfc (·⁻¹)

/-- `L⁺`, the pseudo-inverse of the Laplacian (`conductance.py`: `np.linalg.pinv(L)`). -/
noncomputable def lapPinv (A : Matrix V V ℝ) (hA : A.IsSymm) : Matrix V V ℝ :=
  pinv (lap A) (isHermitian_lap A hA)

/-- CND-1's effective resistance read off a matrix `X`: `X i i + X j j − 2 X i j`. -/
def rEff (X : Matrix V V ℝ) (i j : V) : ℝ := X i i + X j j - 2 * X i j

end Palace
