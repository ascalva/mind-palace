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

/-- The coboundary of a vertex cochain: `(dφ)(u, v) = φ v − φ u`, the drop across a citation. -/
def coboundary {A : Type*} (φ : A → ℝ) : A → A → ℝ := fun u v ↦ φ v - φ u

/-- The pullback of an edge cochain along `σ`, through the citations `X'` of the target: a
citation `u → v` of the source reads `ψ (σ u) (σ v)` when `σ u → σ v` is a citation of the
target, and `0` when the citation was severed. -/
def pullEdge {A B : Type*} (σ : A → B) (X' : B → B → Prop) [DecidableRel X'] (ψ : B → B → ℝ) :
    A → A → ℝ :=
  fun u v ↦ if X' (σ u) (σ v) then ψ (σ u) (σ v) else 0

/-- The curvature `[d, τ]` of the superconnection `d + τ` on a vertex cochain of the target
(temporal-retrieval §2.3 Result 3): pull back then differentiate, less differentiate then pull
back. -/
def curvature {A B : Type*} (σ : A → B) (X' : B → B → Prop) [DecidableRel X'] (φ : B → ℝ) :
    A → A → ℝ :=
  fun u v ↦ coboundary (fun a ↦ φ (σ a)) u v - pullEdge σ X' (coboundary φ) u v

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

/-- The inverse-fiber-weighted inner product on the target, `⟨f, g⟩_{1/σ} = ∑_b f_b g_b / |σ⁻¹ b|`;
Lean's `0⁻¹ = 0` drops the notes nothing was merged into. -/
noncomputable def wdotInv (σ : A → B) (f g : B → ℝ) : ℝ := ∑ b, (fiber σ b : ℝ)⁻¹ * (f b * g b)

end Palace.Transport
