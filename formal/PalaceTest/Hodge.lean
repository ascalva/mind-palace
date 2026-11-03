module

public import Palace.Hodge
public import Mathlib.Testing.Plausible.Sampleable
public import PalaceTest.Attack
public meta import Palace.Hodge
public meta import Mathlib.Testing.Plausible.Sampleable
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Hodge`

The Plausible attacks and negative controls for the laws of `Palace/Hodge.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Matrix

namespace Palace.Hodge

/-! ### Attacks

On random graphs of six vertices over `ℤ`, where each law has an executable instance. -/

namespace Attack

/-- The graph on six vertices whose edge `{i, j}` is present when bit `6·min + max` is set. -/
def graph (es : List Bool) : SimpleGraph (Fin 6) :=
  SimpleGraph.fromRel fun i j ↦ i < j ∧ es.getD (i.val * 6 + j.val) false = true

instance (es : List Bool) : DecidableRel (graph es).Adj :=
  fun i j ↦ inferInstanceAs (Decidable (i ≠ j ∧
    ((i < j ∧ es.getD (i.val * 6 + j.val) false = true) ∨
      (j < i ∧ es.getD (j.val * 6 + i.val) false = true))))

instance {m n α : Type*} [Fintype m] [Fintype n] [DecidableEq α] : DecidableEq (Matrix m n α) :=
  inferInstanceAs (DecidableEq (m → n → α))

/-- `∂₂` with every sign `+`: the control's mis-stated boundary. -/
def d2plus {V : Type*} [LinearOrder V] [Fintype V] (G : SimpleGraph V) [DecidableRel G.Adj] :
    Matrix (Edge G) (Tri G) ℤ :=
  fun e t ↦ (if e = edgeJK t then 1 else 0) + (if e = edgeIK t then 1 else 0) +
    (if e = edgeIJ t then 1 else 0)

/-- A node potential from a list. -/
def pot (xs : List ℤ) : Fin 6 → ℤ := fun v ↦ xs.getD v 0

/-- An edge flow from a list, read at the edge's two ends. -/
def flow (es : List Bool) (xs : List ℤ) : Edge (graph es) → ℤ :=
  fun e ↦ xs.getD (e.1.1.val * 6 + e.1.2.val) 0

/-- A triangle potential from a list. -/
def circ (es : List Bool) (ys : List ℤ) : Tri (graph es) → ℤ :=
  fun t ↦ ys.getD (t.1.1.val * 36 + t.1.2.1.val * 6 + t.1.2.2.val) 0

/-- A sign per edge from a list of bits. -/
def flipE (es : List Bool) (bs : List Bool) : Edge (graph es) → ℤ :=
  fun e ↦ if bs.getD (e.1.1.val * 6 + e.1.2.val) false then -1 else 1

/-- A sign per triangle from a list of bits. -/
def flipT (es : List Bool) (bs : List Bool) : Tri (graph es) → ℤ :=
  fun t ↦ if bs.getD (t.1.1.val * 36 + t.1.2.1.val * 6 + t.1.2.2.val) false then -1 else 1

/- LAP-7: `∂₁ ∂₂ = 0` on random graphs. -/
#eval survives (∀ es : List Bool, d1 (graph es) ℤ * d2 (graph es) ℤ = 0) 171

/- LAP-7 control: with every sign `+`, the boundary of a triangle has a boundary. -/
#eval refuted (∀ es : List Bool, d1 (graph es) ℤ * d2plus (graph es) = 0) 172

/- LAP-8: `cᵀ L₁ c ≥ 0` for every edge flow. -/
#eval survives (∀ es : List Bool, ∀ xs : List ℤ,
  0 ≤ flow es xs ⬝ᵥ lap1 (d1 (graph es) ℤ) (d2 (graph es) ℤ) *ᵥ flow es xs) 173

/- LAP-8 control: the down term minus the up term is not positive semidefinite. -/
#eval refuted (∀ es : List Bool, ∀ xs : List ℤ,
  0 ≤ flow es xs ⬝ᵥ ((d1 (graph es) ℤ)ᵀ * d1 (graph es) ℤ -
    d2 (graph es) ℤ * (d2 (graph es) ℤ)ᵀ) *ᵥ flow es xs) 174

/- LAP-9: gradients and curls are orthogonal. -/
#eval survives (∀ es : List Bool, ∀ xs ys : List ℤ,
  ((d1 (graph es) ℤ)ᵀ *ᵥ pot xs) ⬝ᵥ (d2 (graph es) ℤ *ᵥ circ es ys) = 0) 175

/- LAP-9 control: against the mis-signed boundary they are not. -/
#eval refuted (∀ es : List Bool, ∀ xs ys : List ℤ,
  ((d1 (graph es) ℤ)ᵀ *ᵥ pot xs) ⬝ᵥ (d2plus (graph es) *ᵥ circ es ys) = 0) 176

/-- `∂₁ diag σ` entrywise (`Matrix.mul_diagonal`): the interpreter re-sums a product against a
diagonal at every entry, so the attack scales instead. -/
def d1flip (es bs : List Bool) : Matrix (Fin 6) (Edge (graph es)) ℤ :=
  fun v e ↦ d1 (graph es) ℤ v e * flipE es bs e

/-- `diag σ ∂₂ diag τ` entrywise (`Matrix.diagonal_mul`, `Matrix.mul_diagonal`). -/
def d2flip (es bs cs : List Bool) : Matrix (Edge (graph es)) (Tri (graph es)) ℤ :=
  fun e t ↦ flipE es bs e * d2 (graph es) ℤ e t * flipT es cs t

/- LAP-11: reorienting conjugates `L₁` by the edge signs, `σ L₁ σ` entrywise. -/
#eval survives (∀ es bs cs : List Bool,
  lap1 (d1flip es bs) (d2flip es bs cs) =
    Matrix.of fun e e' ↦
      flipE es bs e * lap1 (d1 (graph es) ℤ) (d2 (graph es) ℤ) e e' * flipE es bs e') 177

/- LAP-11 control: `L₁` itself is not invariant, only its conjugacy class. -/
#eval refuted (∀ es bs cs : List Bool,
  lap1 (d1flip es bs) (d2flip es bs cs) = lap1 (d1 (graph es) ℤ) (d2 (graph es) ℤ)) 178

end Attack

end Palace.Hodge
