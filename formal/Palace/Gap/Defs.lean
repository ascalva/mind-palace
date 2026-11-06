module

public import Mathlib.Analysis.InnerProductSpace.Spectrum

/-!
# The spectral-gap lemma: when a tolerance tells zero from nonzero, the definitions

The definitions the laws of `Palace/Gap.lean` are stated over. With `Spec/Gap.lean` they are what
a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library proves exactly the
statements there, so no other file can change what is proved.
-/

@[expose] public section

namespace Palace.Gap

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E]
  {n : ℕ}

/-- The number of eigenvalues of a symmetric operator at most `t`, with multiplicity. -/
noncomputable def count {T : E →ₗ[ℝ] E} (hT : T.IsSymmetric) (hn : Module.finrank ℝ E = n)
    (t : ℝ) : ℕ :=
  (Finset.univ.filter fun i ↦ hT.eigenvalues hn i ≤ t).card

/-- `B` lies within `ε` of `A` as a quadratic form, `|⟪x, (B − A) x⟫| ≤ ε ‖x‖²`, which
`‖B − A‖ ≤ ε` gives: the backward error of a symmetric eigensolver. -/
def Near (A B : E →ₗ[ℝ] E) (ε : ℝ) : Prop := ∀ x, |inner ℝ x ((B - A) x)| ≤ ε * ‖x‖ ^ 2

/-- The number of singular values of `M` at most `t`, with multiplicity: the eigenvalues of
`M† M` at most `t²`. -/
noncomputable def countSV (M : E →ₗ[ℝ] E) (hn : Module.finrank ℝ E = n) (t : ℝ) : ℕ :=
  count (LinearMap.isSymmetric_adjoint_mul_self M) hn (t ^ 2)

end Palace.Gap
