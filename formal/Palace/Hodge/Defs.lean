module

public import Mathlib.Combinatorics.SimpleGraph.Basic
public import Mathlib.Data.Matrix.ColumnRowPartitioned
public import Mathlib.Algebra.Order.Star.Real
public import Mathlib.LinearAlgebra.Matrix.Charpoly.Basic
public import Mathlib.LinearAlgebra.Matrix.PosDef
public import Mathlib.LinearAlgebra.Matrix.Rank

/-!
# The Hodge 1-Laplacian: LAP-7 to LAP-11, the definitions

The definitions the laws of `Palace/Hodge.lean` are stated over. With `Spec/Hodge.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

open Matrix

namespace Palace.Hodge

/-! ### The flag complex -/

section Complex

variable {V : Type*} [LinearOrder V] [Fintype V] (G : SimpleGraph V) [DecidableRel G.Adj]

/-- The edges, each oriented from its smaller end (`edge_index`). -/
abbrev Edge := {p : V × V // p.1 < p.2 ∧ G.Adj p.1 p.2}

/-- The filled triangles: the graph's 3-cliques, as ascending triples (`flag_triangles`). -/
abbrev Tri :=
  {t : V × V × V // t.1 < t.2.1 ∧ t.2.1 < t.2.2 ∧ G.Adj t.1 t.2.1 ∧ G.Adj t.2.1 t.2.2 ∧
    G.Adj t.1 t.2.2}

variable {G}

/-- A triangle's edge `ij`. -/
def edgeIJ (t : Tri G) : Edge G := ⟨(t.1.1, t.1.2.1), t.2.1, t.2.2.2.1⟩

/-- A triangle's edge `ik`. -/
def edgeIK (t : Tri G) : Edge G := ⟨(t.1.1, t.1.2.2), t.2.1.trans t.2.2.1, t.2.2.2.2.2⟩

/-- A triangle's edge `jk`. -/
def edgeJK (t : Tri G) : Edge G := ⟨(t.1.2.1, t.1.2.2), t.2.2.1, t.2.2.2.2.1⟩

variable (G)

/-- `∂₁ e_ij = δ_j − δ_i` (`boundary_1`). -/
def d1 (R : Type*) [Ring R] : Matrix V (Edge G) R :=
  fun v e ↦ (Pi.single e.1.2 1 - Pi.single e.1.1 1 : V → R) v

/-- `∂₂ t_ijk = e_jk − e_ik + e_ij` (`boundary_2`). -/
def d2 (R : Type*) [Ring R] : Matrix (Edge G) (Tri G) R :=
  fun e t ↦ (if e = edgeJK t then 1 else 0) - (if e = edgeIK t then 1 else 0) +
    (if e = edgeIJ t then 1 else 0)

end Complex

/-! ### The Hodge Laplacian of any complex -/

section Hodge

variable {V E T : Type*} [Fintype V] [Fintype E] [Fintype T]

/-- `L₁ = ∂₁ᵀ ∂₁ + ∂₂ ∂₂ᵀ` (`hodge_laplacian_1`). -/
def lap1 {R : Type*} [CommRing R] (B₁ : Matrix V E R) (B₂ : Matrix E T R) : Matrix E E R :=
  B₁ᵀ * B₁ + B₂ * B₂ᵀ

end Hodge

end Palace.Hodge
