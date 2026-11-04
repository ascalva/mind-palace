module

public import Mathlib.Algebra.BigOperators.Group.Finset.Basic
public import Mathlib.Data.Fintype.Card
public import Mathlib.Data.Matrix.Mul
public import Mathlib.Basic.Real.Basic
public import Mathlib.LinearAlgebra.Matrix.Notation

/-!
# The transports along a supersession: σ_* and σ^*, the definitions

A supersession `D` induces a note correspondence `σ : A → B` from the active view at one time to
the next (temporal-retrieval-algebra §2.3). A cochain on the target pulls back along `σ`; a chain
on the source pushes forward. Results 4 and 5 of that note reason about their norms; the laws of
`Palace/Transport.lean` say what the norms are, and refute one claim (the limits program L3,
`docs/brainstorms/limits-of-the-algebra.md`).
-/

@[expose] public section

open Finset Matrix

namespace Palace.Transport

variable {A B : Type*} [Fintype A] [Fintype B] [DecidableEq B]

/-- The pullback `σ^*`: `(σ^* f) a = f (σ a)`. -/
def pull (σ : A → B) (f : B → ℝ) : A → ℝ := fun a ↦ f (σ a)

/-- The push-forward `σ_*`: `(σ_* g) b = ∑_{σ a = b} g a`, the mass of the fiber. -/
def push (σ : A → B) (g : A → ℝ) : B → ℝ := fun b ↦ ∑ a ∈ univ.filter (fun a ↦ σ a = b), g a

/-- The fiber size `|σ⁻¹ b|`: how many notes merged into `b`. -/
def fiber (σ : A → B) (b : B) : ℕ := (univ.filter fun a ↦ σ a = b).card

/-- The largest fiber: the width of the widest merge. -/
def maxFiber (σ : A → B) : ℕ := univ.sup (fiber σ)

/-- The fiber-weighted inner product on the target, `⟨f, g⟩_σ = ∑_b |σ⁻¹ b| f b g b` — the
weighted inner product PD-b asks for, read off the merge. -/
def wdot (σ : A → B) (f g : B → ℝ) : ℝ := ∑ b, (fiber σ b : ℝ) * (f b * g b)

/-- The merge of two notes into one, the smallest merge. -/
def merge2 : Fin 2 → Fin 1 := fun _ ↦ 0

end Palace.Transport
