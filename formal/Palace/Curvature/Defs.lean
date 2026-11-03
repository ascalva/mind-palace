module

public import Mathlib.Combinatorics.SimpleGraph.Finite
public import Mathlib.Combinatorics.SimpleGraph.Maps
public import Mathlib.Data.Finset.Sort
public import Mathlib.Logic.Equiv.Fin.Basic
public import Mathlib.Order.Prod.Lex.Basic
public import Palace.Laplacian.Defs

/-!
# Forman–Ricci curvature: CRV-1, CRV-2 and CRV-3, the definitions

The definitions the laws of `Palace/Curvature.lean` are stated over. With `Spec/Curvature.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

open Finset

namespace Palace

/-- **CRV-1** Augmented Forman–Ricci curvature of `u — v`: `4 − deg u − deg v + 3·|N(u) ∩ N(v)|`,
the triangle count through the edge being the common-neighbour count. -/
def forman {V : Type*} [Fintype V] [DecidableEq V] (G : SimpleGraph V) [DecidableRel G.Adj]
    (u v : V) : ℤ :=
  4 - G.degree u - G.degree v + 3 * (G.neighborFinset u ∩ G.neighborFinset v).card

/-! ### CRV-2: two cliques and a bridge -/

/-- Adjacency of two `(m + 1)`-cliques joined by one bridge, from the last vertex of the first
clique to the first vertex of the second (vertices `m` and `m + 1` of the test's numbering). -/
def twoCliquesAdj (m : ℕ) : Fin (m + 1) ⊕ Fin (m + 1) → Fin (m + 1) ⊕ Fin (m + 1) → Bool
  | .inl i, .inl j => i != j
  | .inr i, .inr j => i != j
  | .inl i, .inr j => i == Fin.last m && j == 0
  | .inr i, .inl j => i == 0 && j == Fin.last m

/-- The graph of two `(m + 1)`-cliques and their bridge. -/
def twoCliques (m : ℕ) : SimpleGraph (Fin (m + 1) ⊕ Fin (m + 1)) where
  Adj x y := twoCliquesAdj m x y = true
  symm := ⟨fun x y h ↦ by
    cases x <;> cases y <;>
      simp only [twoCliquesAdj, bne_iff_ne, ne_eq, Bool.and_eq_true, beq_iff_eq] at h ⊢
    · exact Ne.symm h
    · exact ⟨h.2, h.1⟩
    · exact ⟨h.2, h.1⟩
    · exact Ne.symm h⟩
  loopless := ⟨fun x h ↦ by cases x <;> simp [twoCliquesAdj] at h⟩

instance (m : ℕ) : DecidableRel (twoCliques m).Adj :=
  fun x y ↦ inferInstanceAs (Decidable (twoCliquesAdj m x y = true))

/-! ### CRV-3: the bridge lens's emission rule -/

section Emission

variable {V : Type*} [Fintype V] [LinearOrder V] (G : SimpleGraph V) [DecidableRel G.Adj]

/-- The support's edges, each once, as `(i, j)` with `i < j`: the keys of `forman`'s result. -/
def edgesLt : Finset (V × V) := univ.filter fun e ↦ e.1 < e.2 ∧ G.Adj e.1 e.2

/-- An edge's curvature. -/
def kappa (e : V × V) : ℤ := forman G e.1 e.2

/-- The emission order's key: curvature, then the ends, `(κ, i, j)`. -/
def emitKey (e : V × V) : ℤ ×ₗ (V ×ₗ V) := toLex (kappa G e, toLex e)

/-- The edges `most_negative_edges` ranks: those with `κ ≤ 0`, or, when every edge is positive,
only those at the minimum, never the whole graph. -/
def candidates : Finset (V × V) :=
  if ((edgesLt G).filter fun e ↦ kappa G e ≤ 0).Nonempty then
    (edgesLt G).filter fun e ↦ kappa G e ≤ 0
  else (edgesLt G).filter fun e ↦ ∀ e' ∈ edgesLt G, kappa G e ≤ kappa G e'

/-- The candidates in `(κ, i, j)` order. -/
def ranked : List (V × V) :=
  (((candidates G).image (emitKey G)).sort).map fun x ↦ ofLex (ofLex x).2

/-- **CRV-3** `most_negative_edges(A, top_k)`: the first `top_k` ranked candidates. -/
def mostNegative (k : ℕ) : List (V × V) := (ranked G).take k

end Emission

end Palace
