module

public import Palace.Bridges
public import Palace.Curvature
public import Mathlib.Testing.Plausible.Sampleable
public import PalaceTest.Attack
public import PalaceTest.Hodge
public meta import Palace.Bridges
public meta import Palace.Curvature
public meta import Mathlib.Testing.Plausible.Sampleable
public meta import PalaceTest.Attack
public meta import PalaceTest.Hodge

/-!
# Attacks on `Palace.Bridges`

The Plausible attacks and negative controls for the bridges of `Palace/Bridges.lean`, and for one
bridge not yet proved, Forman's curvature as the Weitzenböck term of `L₁`. They run when this
module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Matrix Palace.Hodge Palace.Hodge.Attack

namespace Palace.Bridges

/-! ### Attacks

On random graphs of six vertices over `ℤ`, Hodge's attack graphs. -/

namespace Attack

/-- Forman's curvature as the Weitzenböck term of a Laplacian on edges: the diagonal entry less
the absolute values off the diagonal, `L e e − Σ_{e' ≠ e} |L e e'|`. -/
def weitzenbock {V : Type*} [LinearOrder V] [Fintype V] {G : SimpleGraph V} [DecidableRel G.Adj]
    (L : Matrix (Edge G) (Edge G) ℤ) (e : Edge G) : ℤ :=
  L e e - ∑ e' ∈ Finset.univ.filter (· ≠ e), |L e e'|

/- BRG-1: `∂₁ ∂₁ᵀ` is the graph Laplacian. -/
#eval survives (∀ es : List Bool,
  d1 (graph es) ℤ * (d1 (graph es) ℤ)ᵀ = (graph es).lapMatrix ℤ) 189

/- BRG-1 control: not the signless Laplacian `D + A`. -/
#eval refuted (∀ es : List Bool,
  d1 (graph es) ℤ * (d1 (graph es) ℤ)ᵀ = (graph es).degMatrix ℤ + (graph es).adjMatrix ℤ) 190

/- BRG-6 (attacked, not yet proved): on every edge, Forman's augmented curvature is the
Weitzenböck term of `L₁ = ∂₁ᵀ ∂₁ + ∂₂ ∂₂ᵀ` on the flag complex. -/
#eval survives (∀ es : List Bool, decide (∀ e : Edge (graph es),
  forman (graph es) e.1.1 e.1.2 = weitzenbock (lap1 (d1 (graph es) ℤ) (d2 (graph es) ℤ)) e) = true)
  191

/- BRG-6 control: the down Laplacian `∂₁ᵀ ∂₁` alone misses the triangles. -/
#eval refuted (∀ es : List Bool, decide (∀ e : Edge (graph es),
  forman (graph es) e.1.1 e.1.2 = weitzenbock ((d1 (graph es) ℤ)ᵀ * d1 (graph es) ℤ) e) = true)
  192

end Attack

end Palace.Bridges
