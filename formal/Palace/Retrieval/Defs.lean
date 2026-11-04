module

public import Palace.Laplacian.Defs
public import Mathlib.Analysis.SpecialFunctions.Pow.Real

/-!
# The retrieval curve: RSP-1 to RSP-4, the definitions

The β-curve of `docs/design-notes/temporal-retrieval-algebra.md` §2.1 (Theorem A1) as
`core/query.py`'s `free_energy_distances` computes it: on weights `w` in `[0, 1]`, the reference
walk `P = D⁻¹ w`, the killed walk `W_β = z·P∘w^β`, the fundamental matrix `Z = (I − W_β)⁻¹`, the
free energy `φ_ij = −log(z_ij / z_jj) / β` and its symmetrization. With `Spec/Retrieval.lean`
these are what a reader checks against `docs/LAWS.md`.

Lean's `x / 0 = 0` gives a vertex of degree `0` a zero row of `P`, as the code's
`where=deg > 0` does, and `0 ^ β = 0` for `β ≠ 0`, as its `where=weights > 0` does. The code maps
`z_ij = 0` to `+∞`; the laws here are stated where `z_ij > 0`, which RSP-1 characterizes.
-/

@[expose] public section

open Matrix

namespace Palace.Retrieval

variable {V : Type*} [Fintype V] [DecidableEq V]

/-- The killed walk `W_β = z·P∘w^β`, `P = D⁻¹ w` the reference walk: `z (w_ij / d_i) w_ij^β`
(`free_energy_distances`, `w_beta`). -/
noncomputable def killedWalk (w : Matrix V V ℝ) (β z : ℝ) : Matrix V V ℝ :=
  of fun i j ↦ z * (w i j / degree w i) * w i j ^ β

/-- The fundamental matrix `Z = (I − W_β)⁻¹`, the sum over killed walks (`zmat`). -/
noncomputable def fundamental (w : Matrix V V ℝ) (β z : ℝ) : Matrix V V ℝ :=
  (1 - killedWalk w β z)⁻¹

/-- The free energy `φ_ij = −log(z_ij / z_jj) / β` (`phi`). -/
noncomputable def freeEnergy (w : Matrix V V ℝ) (β z : ℝ) (i j : V) : ℝ :=
  -Real.log (fundamental w β z i j / fundamental w β z j j) / β

/-- The symmetrized free-energy distance `(φ_ij + φ_ji) / 2` that the code returns (`sym`). -/
noncomputable def feDist (w : Matrix V V ℝ) (β z : ℝ) (i j : V) : ℝ :=
  (freeEnergy w β z i j + freeEnergy w β z j i) / 2

/-- A walk restricted to a support `S`: the transitions among `S` as in `M`, none elsewhere — the
complement absorbs (the sentence universe's support, dn-query-sentence-algebra §2.9: the degrees
stay the full graph's, so a transition to a node outside `S` becomes a killing). -/
def restrict (M : Matrix V V ℝ) (S : Finset V) : Matrix V V ℝ :=
  of fun i j ↦ if i ∈ S ∧ j ∈ S then M i j else 0

/-- The fundamental matrix of the killed walk on the support `S`, with the full graph's degrees:
`Z_S = (I − W_β|_S)⁻¹` (`free_energy_distances(weights_S, degrees=full)`). -/
noncomputable def fundamentalOn (w : Matrix V V ℝ) (S : Finset V) (β z : ℝ) : Matrix V V ℝ :=
  (1 - restrict (killedWalk w β z) S)⁻¹

/-- The nearness `e^{−β φ_ij} = z_ij / z_jj` on the full graph — what `diffuse` scores by. -/
noncomputable def nearness (w : Matrix V V ℝ) (β z : ℝ) (i j : V) : ℝ :=
  fundamental w β z i j / fundamental w β z j j

/-- The nearness on the support `S`. -/
noncomputable def nearnessOn (w : Matrix V V ℝ) (S : Finset V) (β z : ℝ) (i j : V) : ℝ :=
  fundamentalOn w S β z i j / fundamentalOn w S β z j j

/-- The symmetric RSP kernel `G_β = (D − z·w∘w^β)⁻¹`, so that `Z = G_β D` when every degree is
positive (Theorem A1's kernel, in the code's normalization). -/
noncomputable def rspKernel (w : Matrix V V ℝ) (β z : ℝ) : Matrix V V ℝ :=
  (diagonal (degree w) - z • of fun i j ↦ w i j * w i j ^ β)⁻¹

end Palace.Retrieval
