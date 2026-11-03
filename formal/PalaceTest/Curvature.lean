module

public import Palace.Curvature
public import Mathlib.Testing.Plausible.Sampleable
public import PalaceTest.Laplacian
public meta import Palace.Curvature
public meta import Mathlib.Testing.Plausible.Sampleable
public meta import PalaceTest.Laplacian

/-!
# Attacks on `Palace.Curvature`

The Plausible attacks and negative controls for the laws of `Palace/Curvature.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Finset

namespace Palace

/-! ## Attacks

CRV-1 is attacked against a transcription of `forman`'s matrix computation on random weighted
graphs on `Fin 5`: the code reads triangles off `(B @ B)[i, j]` and degrees off row sums of `B`, the
support without its diagonal. CRV-2 is checked on every edge of the family for clique sizes 1 to 8.
CRV-3 is attacked against a transcription of `most_negative_edges` on the same random graphs.
-/

namespace Attack

instance (A : Matrix (Fin 5) (Fin 5) ℚ) : DecidableRel (support A).Adj :=
  fun i j ↦ inferInstanceAs (Decidable (i ≠ j ∧ (A i j ≠ 0 ∨ A j i ≠ 0)))

/-- `forman`'s computation, transcribed: `B` the support without its diagonal, the degrees its row
sums, the triangles through `i — j` the entry `(B @ B)[i, j]`. -/
def formanCode (A : Matrix (Fin 5) (Fin 5) ℚ) (i j : Fin 5) : ℤ :=
  let B : Fin 5 → Fin 5 → ℤ := fun a b ↦ if a ≠ b ∧ A a b ≠ 0 then 1 else 0
  4 - ∑ b, B i b - ∑ b, B j b + 3 * ∑ k, B i k * B k j

/-- CRV-1 agrees with the code on every edge of the support. -/
def formanAgrees (A : Matrix (Fin 5) (Fin 5) ℚ) : Bool :=
  (List.finRange 5).all fun i ↦ (List.finRange 5).all fun j ↦
    !decide ((support A).Adj i j) || decide (forman (support A) i j = formanCode A i j)

/-- Every vertex of the two-cliques graph. -/
def vertices (m : ℕ) : List (Fin (m + 1) ⊕ Fin (m + 1)) :=
  (List.finRange (m + 1)).map .inl ++ (List.finRange (m + 1)).map .inr

/-- CRV-2 on one clique size: the bridge's value, and every other edge strictly above it. -/
def bridgeIsStrictMin (m : ℕ) : Bool :=
  let G := twoCliques m
  let b := forman G (.inl (Fin.last m)) (.inr 0)
  decide (b = 4 - 2 * ((m : ℤ) + 1)) &&
    (vertices m).all fun x ↦ (vertices m).all fun y ↦
      !decide (G.Adj x y) || (x == .inl (Fin.last m) && y == .inr 0) ||
        (x == .inr 0 && y == .inl (Fin.last m)) || decide (b < forman G x y)

/- CRV-1: the definition is what the code computes, on symmetric weights of either sign. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℤ), formanAgrees (ofEdges es) = true) 71

/- CRV-1 control: asymmetric weights, where row sums and `B @ B` are no longer the support
graph's degrees and triangles. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ), formanAgrees (ofArcs es) = true) 72

/- CRV-2: the bridge is the strict unique minimum, for clique sizes 1 to 8. -/
#eval survives (∀ m : Fin 8, bridgeIsStrictMin m.val = true) 73

/- CRV-2: the bridge is negative exactly from clique size 3. -/
#eval survives (∀ m : Fin 8,
  (forman (twoCliques m.val) (.inl (Fin.last m.val)) (.inr 0) < 0 ↔ 3 ≤ m.val + 1)) 74

/- CRV-2 control, the test's threshold: negative exactly from clique size 4. -/
#eval refuted (∀ m : Fin 8,
  (forman (twoCliques m.val) (.inl (Fin.last m.val)) (.inr 0) < 0 ↔ 4 ≤ m.val + 1)) 75

/-- `most_negative_edges`, transcribed: the `(i, j, κ)` triples over `forman`'s keys (`i < j`,
`A[i, j] ≠ 0`), the `κ ≤ 0` ones or else those at the minimum, sorted by `(κ, i, j)`, the first
`top_k`. `fallback := false` drops the minimum rule; `swap` breaks ties by `(κ, j, i)`. -/
def mostNegativeCode (fallback swap : Bool) (A : Matrix (Fin 5) (Fin 5) ℚ) (k : ℕ) :
    List (Fin 5 × Fin 5) :=
  let curv := (List.finRange 5).flatMap fun i ↦
    ((List.finRange 5).filter fun j ↦ i < j ∧ A i j ≠ 0).map fun j ↦ (i, j, formanCode A i j)
  match (curv.map (·.2.2)).min? with
  | none => []
  | some lo =>
    let neg := curv.filter (·.2.2 ≤ 0)
    let cands := if neg.isEmpty && fallback then curv.filter (·.2.2 = lo) else neg
    let key (e : Fin 5 × Fin 5 × ℤ) : ℤ ×ₗ (Fin 5 ×ₗ Fin 5) :=
      if swap then toLex (e.2.2, toLex (e.2.1, e.1)) else toLex (e.2.2, toLex (e.1, e.2.1))
    ((cands.mergeSort fun a b ↦ decide (key a ≤ key b)).take k).map fun e ↦ (e.1, e.2.1)

/- CRV-3: the emission rule is what the code emits, on symmetric weights of either sign. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ k : Fin 5,
  mostNegative (support (ofEdges es)) k = mostNegativeCode true false (ofEdges es) k) 76

/- CRV-3 control, no minimum rule: a graph whose edges are all positive emits nothing. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ k : Fin 5,
  mostNegative (support (ofEdges es)) k = mostNegativeCode false false (ofEdges es) k) 77

/- CRV-3 control, ties broken by `(κ, j, i)`. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ k : Fin 5,
  mostNegative (support (ofEdges es)) k = mostNegativeCode true true (ofEdges es) k) 78

end Attack

end Palace
