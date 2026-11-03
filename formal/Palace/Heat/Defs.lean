module

public import Mathlib.Analysis.InnerProductSpace.PiL2
public import Mathlib.Analysis.SpecialFunctions.Exp
public import Palace.Spectral.Defs

/-!
# The heat kernel and the diffusion distance: CND-4, the definitions

The definitions the laws of `Palace/Heat.lean` are stated over. With `Spec/Heat.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

open Matrix

namespace Palace

variable {V : Type*} [Fintype V] [DecidableEq V]

/-- The heat kernel `e^{−tM}` of a real symmetric matrix, by the functional calculus. -/
noncomputable def heat (M : Matrix V V ℝ) (t : ℝ) : Matrix V V ℝ :=
  cfc (fun x ↦ Real.exp (-t * x)) M

/-- The vertex `i` seen from time `t`: column `i` of the heat kernel, `H_t eᵢ`, as a point of
Euclidean space. -/
noncomputable def heatPoint (M : Matrix V V ℝ) (t : ℝ) (i : V) : EuclideanSpace ℝ V :=
  WithLp.toLp 2 (heat M t *ᵥ Pi.single i 1)

/-- **CND-4** `_diffusion_distances`: `√(G_ii + G_jj − 2G_ij)` with `G = H_{2t}`. -/
noncomputable def diffusionDist (M : Matrix V V ℝ) (t : ℝ) (i j : V) : ℝ :=
  Real.sqrt (rEff (heat M (2 * t)) i j)

end Palace
