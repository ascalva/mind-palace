import Mathlib.Combinatorics.SimpleGraph.Finite
import Mathlib.Testing.Plausible.Sampleable
import Palace.Laplacian

/-!
# Forman–Ricci curvature: CRV-1 and CRV-2

`Ric_F(u, v) = 4 − deg u − deg v + 3·|△(u, v)|` on the binarized support (`curvature.py`,
`forman`; dn-mathematical-foundations §2.2, seed table IV), and the planted-bridge law on the family
of `test_planted_bridge_is_negative_and_clique_edges_positive`. Exact, over ℤ.
-/

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

section TwoCliques

variable (m : ℕ)

open SimpleGraph Function

@[simp] theorem twoCliques_adj (x y : Fin (m + 1) ⊕ Fin (m + 1)) :
    (twoCliques m).Adj x y ↔ twoCliquesAdj m x y = true := Iff.rfl

/-- A first-clique vertex is adjacent to the rest of its clique, and the last one to the bridge's
far end. -/
theorem neighborFinset_inl (i : Fin (m + 1)) :
    (twoCliques m).neighborFinset (.inl i) =
      (univ.erase i).map Embedding.inl ∪ if i = Fin.last m then {.inr 0} else ∅ := by
  ext x
  rcases x with j | j <;> by_cases hi : i = Fin.last m <;>
    simp only [mem_neighborFinset, hi, twoCliques_adj, twoCliquesAdj, bne_iff_ne, ne_eq, map_erase,
      Embedding.inl_apply, ↓reduceIte, union_singleton, union_empty, mem_insert, reduceCtorEq,
      mem_erase, Sum.inl.injEq, Sum.inr.injEq, mem_map, mem_univ, true_and, exists_eq, and_true,
      false_or, BEq.rfl, Bool.true_and, Bool.and_eq_true, beq_iff_eq, not_false_eq_true,
      and_false, exists_const, or_false, false_and]
  all_goals exact ne_comm

/-- A second-clique vertex is adjacent to the rest of its clique, and the first one to the bridge's
near end. -/
theorem neighborFinset_inr (j : Fin (m + 1)) :
    (twoCliques m).neighborFinset (.inr j) =
      (univ.erase j).map Embedding.inr ∪ if j = 0 then {.inl (Fin.last m)} else ∅ := by
  ext x
  rcases x with i | i <;> by_cases hj : j = 0 <;>
    simp only [mem_neighborFinset, hj, twoCliques_adj, twoCliquesAdj, bne_iff_ne, ne_eq, map_erase,
      Embedding.inr_apply, ↓reduceIte, union_singleton, union_empty, mem_insert, reduceCtorEq,
      mem_erase, Sum.inl.injEq, Sum.inr.injEq, mem_map, mem_univ, true_and, exists_eq, and_true,
      false_or, BEq.rfl, Bool.true_and, Bool.and_eq_true, beq_iff_eq, not_false_eq_true,
      and_false, exists_const, or_false, false_and]
  all_goals exact ne_comm

theorem degree_inl (i : Fin (m + 1)) :
    (twoCliques m).degree (.inl i) = m + if i = Fin.last m then 1 else 0 := by
  rw [← card_neighborFinset_eq_degree, neighborFinset_inl, card_union_of_disjoint]
  · rw [card_map, card_erase_of_mem (mem_univ _), card_univ, Fintype.card_fin,
      Nat.add_sub_cancel]
    split_ifs <;> rfl
  · split_ifs <;> simp [Finset.disjoint_left]

theorem degree_inr (j : Fin (m + 1)) :
    (twoCliques m).degree (.inr j) = m + if j = 0 then 1 else 0 := by
  rw [← card_neighborFinset_eq_degree, neighborFinset_inr, card_union_of_disjoint]
  · rw [card_map, card_erase_of_mem (mem_univ _), card_univ, Fintype.card_fin,
      Nat.add_sub_cancel]
    split_ifs <;> rfl
  · split_ifs <;> simp [Finset.disjoint_left]

/-- No vertex is adjacent to both ends of the bridge: no triangle runs through it. -/
theorem common_bridge :
    (twoCliques m).neighborFinset (.inl (Fin.last m)) ∩ (twoCliques m).neighborFinset (.inr 0) =
      ∅ := by
  rw [neighborFinset_inl, neighborFinset_inr]
  ext x
  rcases x with k | k <;> simp

/-- Two first-clique vertices share at least the other `m − 1` vertices of their clique. -/
theorem le_card_common_inl {i j : Fin (m + 1)} (h : i ≠ j) :
    m - 1 ≤ ((twoCliques m).neighborFinset (.inl i) ∩
      (twoCliques m).neighborFinset (.inl j)).card := by
  have sub : ((univ.erase i).erase j).map Embedding.inl ⊆
      (twoCliques m).neighborFinset (.inl i) ∩ (twoCliques m).neighborFinset (.inl j) := by
    intro x hx
    obtain ⟨k, hk, rfl⟩ := mem_map.1 hx
    obtain ⟨hkj, hk⟩ := mem_erase.1 hk
    rw [mem_inter, neighborFinset_inl, neighborFinset_inl]
    exact ⟨mem_union_left _ (mem_map_of_mem _ hk), mem_union_left _ (mem_map_of_mem _
      (mem_erase.2 ⟨hkj, mem_univ _⟩))⟩
  calc m - 1 = (((univ.erase i).erase j).map Embedding.inl).card := by
        rw [card_map, card_erase_of_mem (mem_erase.2 ⟨Ne.symm h, mem_univ _⟩),
          card_erase_of_mem (mem_univ _), card_univ, Fintype.card_fin]
        omega
    _ ≤ _ := card_le_card sub

/-- Two second-clique vertices share at least the other `m − 1` vertices of their clique. -/
theorem le_card_common_inr {i j : Fin (m + 1)} (h : i ≠ j) :
    m - 1 ≤ ((twoCliques m).neighborFinset (.inr i) ∩
      (twoCliques m).neighborFinset (.inr j)).card := by
  have sub : ((univ.erase i).erase j).map Embedding.inr ⊆
      (twoCliques m).neighborFinset (.inr i) ∩ (twoCliques m).neighborFinset (.inr j) := by
    intro x hx
    obtain ⟨k, hk, rfl⟩ := mem_map.1 hx
    obtain ⟨hkj, hk⟩ := mem_erase.1 hk
    rw [mem_inter, neighborFinset_inr, neighborFinset_inr]
    exact ⟨mem_union_left _ (mem_map_of_mem _ hk), mem_union_left _ (mem_map_of_mem _
      (mem_erase.2 ⟨hkj, mem_univ _⟩))⟩
  calc m - 1 = (((univ.erase i).erase j).map Embedding.inr).card := by
        rw [card_map, card_erase_of_mem (mem_erase.2 ⟨Ne.symm h, mem_univ _⟩),
          card_erase_of_mem (mem_univ _), card_univ, Fintype.card_fin]
        omega
    _ ≤ _ := card_le_card sub

/-- **CRV-2** The bridge's curvature is `4 − 2(m + 1)`: `m + 1` neighbours at each end, and no
triangle. -/
theorem forman_bridge :
    forman (twoCliques m) (.inl (Fin.last m)) (.inr 0) = 4 - 2 * ((m : ℤ) + 1) := by
  rw [forman, degree_inl, degree_inr, common_bridge]
  simp
  ring

/-- **CRV-2** The bridge is the strict unique minimum: every other edge is curved more. -/
theorem forman_bridge_lt {x y : Fin (m + 1) ⊕ Fin (m + 1)} (hxy : (twoCliques m).Adj x y)
    (hb : ¬ (x = .inl (Fin.last m) ∧ y = .inr 0)) (hb' : ¬ (x = .inr 0 ∧ y = .inl (Fin.last m))) :
    forman (twoCliques m) (.inl (Fin.last m)) (.inr 0) < forman (twoCliques m) x y := by
  rw [forman_bridge]
  rcases x with i | i <;> rcases y with j | j
  · have hij : i ≠ j := by simpa [twoCliquesAdj] using hxy
    have hc := le_card_common_inl m hij
    have hm : 1 ≤ m := by
      by_contra h0
      exact hij (Fin.ext (by omega))
    rw [forman, degree_inl, degree_inl]
    split_ifs with hi hj hj
    · exact absurd (hi.trans hj.symm) hij
    all_goals omega
  · simp only [twoCliques_adj, twoCliquesAdj, Bool.and_eq_true, beq_iff_eq] at hxy
    exact absurd ⟨by rw [hxy.1], by rw [hxy.2]⟩ hb
  · simp only [twoCliques_adj, twoCliquesAdj, Bool.and_eq_true, beq_iff_eq] at hxy
    exact absurd ⟨by rw [hxy.1], by rw [hxy.2]⟩ hb'
  · have hij : i ≠ j := by simpa [twoCliquesAdj] using hxy
    have hc := le_card_common_inr m hij
    have hm : 1 ≤ m := by
      by_contra h0
      exact hij (Fin.ext (by omega))
    rw [forman, degree_inr, degree_inr]
    split_ifs with hi hj hj
    · exact absurd (hi.trans hj.symm) hij
    all_goals omega

/-- **CRV-2** The bridge is negatively curved exactly when each clique has at least three vertices
(`m + 1 ≥ 3`). -/
theorem forman_bridge_neg_iff :
    forman (twoCliques m) (.inl (Fin.last m)) (.inr 0) < 0 ↔ 3 ≤ m + 1 := by
  rw [forman_bridge]
  omega

end TwoCliques

/-! ## Attacks

CRV-1 is attacked against a transcription of `forman`'s matrix computation on random weighted
graphs on `Fin 5`: the code reads triangles off `(B @ B)[i, j]` and degrees off row sums of `B`, the
support without its diagonal. CRV-2 is checked on every edge of the family for clique sizes 1 to 8.
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

end Attack

end Palace
