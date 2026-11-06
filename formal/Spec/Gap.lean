module

public import Palace.Gap.Defs

/-!
# The spectral-gap lemma: when a tolerance tells zero from nonzero, the statements

SPC-3 (`docs/LAWS.md`, II). The statements are over symmetric operators and operators on a
finite-dimensional real inner product space, so they cover a real symmetric matrix and a real
square matrix acting on `EuclideanSpace ℝ (Fin n)`. NumPy's backward stability is the hypothesis
they take: a symmetric eigensolver's values are the exact eigenvalues of a `B` with
`Near A B ε`, an SVD's the exact singular values of an `M'` with `‖(M' − M) x‖ ≤ ε ‖x‖`. What they
leave out: the float64 arithmetic the code does after the decomposition, and the rise threshold's
condition, which rests on Wedin's bound for the pseudo-inverse, cited in the row and not proved.

These are the laws of `Palace/Gap.lean` as the ledger cites them, each with its proof left as
`sorry`. `lake comparator` checks that the `Palace` library proves each one exactly as stated
here, from the standard axioms alone.
-/

@[expose] public section

namespace Palace.Gap

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E]
  {n : ℕ}

/-- **SPC-3** Weyl's inequality, counted: a perturbation within `ε` keeps at most `t` every
eigenvalue that was at most `t − ε`. -/
theorem count_sub_le {A B : E →ₗ[ℝ] E} (hA : A.IsSymmetric) (hB : B.IsSymmetric)
    (hn : Module.finrank ℝ E = n) {ε : ℝ} (h : Near A B ε) (t : ℝ) :
    count hA hn (t - ε) ≤ count hB hn t :=
  sorry

/-- **SPC-3** Weyl's inequality, counted the other way: a perturbation within `ε` brings at most
`t` only eigenvalues that were at most `t + ε`. -/
theorem count_le_add {A B : E →ₗ[ℝ] E} (hA : A.IsSymmetric) (hB : B.IsSymmetric)
    (hn : Module.finrank ℝ E = n) {ε : ℝ} (h : Near A B ε) (t : ℝ) :
    count hB hn t ≤ count hA hn (t + ε) :=
  sorry

/-- **SPC-3** The spectral-gap lemma for a symmetric eigensolver: if every nonzero eigenvalue of
`A` is at least `g`, the eigenvalues of `B`, within `ε` of `A`, at most a cut `θ` with `ε ≤ θ` and
`θ + ε < g` are exactly as many as `A`'s zero eigenvalues: the cut tells zero from nonzero. -/
theorem count_eq_of_gap {A B : E →ₗ[ℝ] E} (hA : A.IsSymmetric) (hB : B.IsSymmetric)
    (hn : Module.finrank ℝ E = n) {ε θ g : ℝ} (h : Near A B ε)
    (hgap : ∀ i, hA.eigenvalues hn i ≠ 0 → g ≤ hA.eigenvalues hn i)
    (hε : 0 ≤ ε) (hθ : ε ≤ θ) (hθg : θ + ε < g) :
    count hB hn θ = count hA hn 0 :=
  sorry

/-- **SPC-3** Weyl's inequality for singular values (Mirsky), counted: a perturbation of norm
at most `ε` keeps at most `t` every singular value that was at most `t − ε`. -/
theorem countSV_sub_le {M M' : E →ₗ[ℝ] E} (hn : Module.finrank ℝ E = n) {ε t : ℝ}
    (h : ∀ x, ‖(M' - M) x‖ ≤ ε * ‖x‖) (ht : ε ≤ t) :
    countSV M hn (t - ε) ≤ countSV M' hn t :=
  sorry

/-- **SPC-3** And the other way: it brings at most `t` only singular values that were at most
`t + ε`. -/
theorem countSV_le_add {M M' : E →ₗ[ℝ] E} (hn : Module.finrank ℝ E = n) {ε t : ℝ}
    (h : ∀ x, ‖(M' - M) x‖ ≤ ε * ‖x‖) (hε : 0 ≤ ε) (ht : 0 ≤ t) :
    countSV M' hn t ≤ countSV M hn (t + ε) :=
  sorry

/-- **SPC-3** The spectral-gap lemma for an SVD: if every nonzero singular value of `M` is at
least `g`, the singular values of `M'`, within `ε` of `M` in norm, at most a cut `θ` with
`ε ≤ θ` and `θ + ε < g` are exactly as many as `M`'s zero singular values. -/
theorem countSV_eq_of_gap {M M' : E →ₗ[ℝ] E} (hn : Module.finrank ℝ E = n) {ε θ g : ℝ}
    (h : ∀ x, ‖(M' - M) x‖ ≤ ε * ‖x‖)
    (hgap : ∀ i, (LinearMap.isSymmetric_adjoint_mul_self M).eigenvalues hn i ≠ 0 →
      g ^ 2 ≤ (LinearMap.isSymmetric_adjoint_mul_self M).eigenvalues hn i)
    (hε : 0 ≤ ε) (hθ : ε ≤ θ) (hθg : θ + ε < g) :
    countSV M' hn θ = countSV M hn 0 :=
  sorry

end Palace.Gap
