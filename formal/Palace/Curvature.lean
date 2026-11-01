import Mathlib.Combinatorics.SimpleGraph.Finite
import Mathlib.Combinatorics.SimpleGraph.Maps
import Mathlib.Data.Finset.Sort
import Mathlib.Logic.Equiv.Fin.Basic
import Mathlib.Order.Prod.Lex.Basic
import Mathlib.Testing.Plausible.Sampleable
import Palace.Laplacian

/-!
# Forman–Ricci curvature: CRV-1, CRV-2 and CRV-3

`Ric_F(u, v) = 4 − deg u − deg v + 3·|△(u, v)|` on the binarized support (`curvature.py`,
`forman`; dn-mathematical-foundations §2.2, seed table IV), the planted-bridge law on the family
of `test_planted_bridge_is_negative_and_clique_edges_positive`, and the emission rule of
`most_negative_edges`, which the Dreamer's bridge lens reads (`core/dreaming/interpreters.py`).
Exact, over ℤ.
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

/-- **CRV-2** Off the bridge every edge is positively curved once each clique has two vertices:
at least `m` against the bridge's `2 − 2m`. -/
theorem forman_pos {x y : Fin (m + 1) ⊕ Fin (m + 1)} (hm : 1 ≤ m) (hxy : (twoCliques m).Adj x y)
    (hb : ¬ (x = .inl (Fin.last m) ∧ y = .inr 0)) (hb' : ¬ (x = .inr 0 ∧ y = .inl (Fin.last m))) :
    0 < forman (twoCliques m) x y := by
  rcases x with i | i <;> rcases y with j | j
  · have hij : i ≠ j := by simpa [twoCliquesAdj] using hxy
    have hc := le_card_common_inl m hij
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
    rw [forman, degree_inr, degree_inr]
    split_ifs with hi hj hj
    · exact absurd (hi.trans hj.symm) hij
    all_goals omega

end TwoCliques

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

theorem emitKey_injective : Function.Injective (emitKey G) := fun a b h ↦ by
  simpa [emitKey] using congrArg (fun x ↦ ofLex (ofLex x).2) h

theorem mem_ranked {e : V × V} : e ∈ ranked G ↔ e ∈ candidates G := by
  simp only [ranked, emitKey, List.mem_map, Finset.mem_sort, Finset.mem_image]
  exact ⟨fun ⟨_, ⟨a, h, hx⟩, he⟩ ↦ by simpa [← hx, ← he] using h, fun h ↦ ⟨_, ⟨e, h, rfl⟩, by simp⟩⟩

theorem ranked_pairwise : (ranked G).Pairwise fun a b ↦ emitKey G a < emitKey G b := by
  have hs := (Finset.sortedLT_sort ((candidates G).image (emitKey G))).pairwise
  rw [ranked, List.pairwise_map]
  refine hs.imp_of_mem fun {x y} hx hy hxy ↦ ?_
  rw [Finset.mem_sort, Finset.mem_image] at hx hy
  obtain ⟨a, -, rfl⟩ := hx
  obtain ⟨b, -, rfl⟩ := hy
  simpa [emitKey] using hxy

theorem length_ranked : (ranked G).length = (candidates G).card := by
  rw [ranked, List.length_map, Finset.length_sort,
    Finset.card_image_of_injective _ (emitKey_injective G)]

theorem candidates_subset : candidates G ⊆ edgesLt G := by
  unfold candidates
  split_ifs <;> exact Finset.filter_subset _ _

/-- Every emitted edge is a candidate, so an edge of the support with `i < j`. -/
theorem mem_candidates {k : ℕ} {e : V × V} (h : e ∈ mostNegative G k) : e ∈ candidates G :=
  (mem_ranked G).1 (List.mem_of_mem_take h)

/-- **CRV-3** When some edge is curved `≤ 0`, only such edges are emitted. -/
theorem kappa_nonpos {k : ℕ} {e : V × V} (h : e ∈ mostNegative G k)
    (h0 : ∃ e' ∈ edgesLt G, kappa G e' ≤ 0) : kappa G e ≤ 0 := by
  obtain ⟨e', he', h'⟩ := h0
  have hne : ((edgesLt G).filter fun e ↦ kappa G e ≤ 0).Nonempty :=
    ⟨e', Finset.mem_filter.2 ⟨he', h'⟩⟩
  have hc := mem_candidates G h
  simp only [candidates, hne, ↓reduceIte, Finset.mem_filter] at hc
  exact hc.2

/-- **CRV-3** When every edge is positive, only edges at the minimum are emitted. -/
theorem kappa_min {k : ℕ} {e : V × V} (h : e ∈ mostNegative G k)
    (h0 : ∀ e' ∈ edgesLt G, 0 < kappa G e') : ∀ e' ∈ edgesLt G, kappa G e ≤ kappa G e' := by
  have hne : ¬((edgesLt G).filter fun e ↦ kappa G e ≤ 0).Nonempty := by
    rintro ⟨e', he'⟩
    rw [Finset.mem_filter] at he'
    exact absurd (h0 e' he'.1) (not_lt.2 he'.2)
  have hc := mem_candidates G h
  simp only [candidates, hne, ↓reduceIte, Finset.mem_filter] at hc
  exact hc.2

/-- **CRV-3** The emission is in strictly increasing `(κ, i, j)` order, so reproducible. -/
theorem mostNegative_pairwise (k : ℕ) :
    (mostNegative G k).Pairwise fun a b ↦ emitKey G a < emitKey G b :=
  (ranked_pairwise G).sublist (List.take_sublist _ _)

/-- **CRV-3** At most `top_k` edges: `min(top_k, |candidates|)` of them. -/
theorem length_mostNegative (k : ℕ) : (mostNegative G k).length = min k (candidates G).card := by
  rw [mostNegative, List.length_take, length_ranked]

/-- **CRV-3** A larger `top_k` extends the emission and never reorders it. -/
theorem mostNegative_prefix {k k' : ℕ} (h : k ≤ k') : mostNegative G k <+: mostNegative G k' := by
  have : (ranked G).take k = ((ranked G).take k').take k := by
    rw [List.take_take, Nat.min_eq_left h]
  rw [mostNegative, mostNegative, this]
  exact List.take_prefix _ _

/-- **CRV-3** The emitted edges are the `top_k` smallest candidates: a candidate left out ranks
after every emitted edge. -/
theorem emitKey_lt {k : ℕ} {e e' : V × V} (he : e ∈ mostNegative G k) (he' : e' ∈ candidates G)
    (hn : e' ∉ mostNegative G k) : emitKey G e < emitKey G e' := by
  have hp := ranked_pairwise G
  rw [← List.take_append_drop k (ranked G), List.pairwise_append] at hp
  have hd : e' ∈ (ranked G).drop k := by
    have := (mem_ranked G).2 he'
    rw [← List.take_append_drop k (ranked G), List.mem_append] at this
    exact this.resolve_left hn
  exact hp.2.2 e he e' hd

/-- A lone candidate is the whole emission, for every `top_k ≥ 1`. -/
theorem mostNegative_eq_singleton {e₀ : V × V} (h : candidates G = {e₀}) {k : ℕ} (hk : 0 < k) :
    mostNegative G k = [e₀] := by
  obtain ⟨x, hx⟩ := List.length_eq_one_iff.1 (by rw [length_ranked, h, Finset.card_singleton] :
    (ranked G).length = 1)
  have hx0 : x = e₀ := by
    have := (mem_ranked G).1 (hx ▸ List.mem_singleton_self x)
    rwa [h, Finset.mem_singleton] at this
  rw [mostNegative, hx, hx0, List.take_of_length_le (by simp; omega)]

end Emission

/-- `forman` is a graph invariant: relabelling the vertices by an equivalence keeps it. -/
theorem forman_comap {V W : Type*} [Fintype V] [DecidableEq V] [Fintype W] [DecidableEq W]
    (e : V ≃ W) (H : SimpleGraph W) [DecidableRel H.Adj] (x y : V) :
    forman (H.comap e) x y = forman H (e x) (e y) := by
  have hn : ∀ z, (H.comap e).neighborFinset z =
      (H.neighborFinset (e z)).map e.symm.toEmbedding := by
    intro z
    ext w
    simp
  simp only [forman, ← SimpleGraph.card_neighborFinset_eq_degree, hn, Finset.card_map,
    ← Finset.map_inter]

/-! ### The bridge lens on the planted-bridge family -/

section TwoCliquesFin

variable (m : ℕ)

/-- The family on the test's own vertex numbers: the first clique is `0..m`, the second
`m + 1..2m + 1`, and the bridge joins `m` to `m + 1`. -/
def twoCliquesFin : SimpleGraph (Fin ((m + 1) + (m + 1))) :=
  (twoCliques m).comap finSumFinEquiv.symm

instance : DecidableRel (twoCliquesFin m).Adj :=
  inferInstanceAs (DecidableRel ((twoCliques m).comap finSumFinEquiv.symm).Adj)

/-- The bridge, `(m, m + 1)`. -/
def bridgeFin : Fin ((m + 1) + (m + 1)) × Fin ((m + 1) + (m + 1)) :=
  (finSumFinEquiv (.inl (Fin.last m)), finSumFinEquiv (.inr 0))

theorem kappa_twoCliquesFin (x : Fin ((m + 1) + (m + 1)) × Fin ((m + 1) + (m + 1))) :
    kappa (twoCliquesFin m) x =
      forman (twoCliques m) (finSumFinEquiv.symm x.1) (finSumFinEquiv.symm x.2) :=
  forman_comap _ _ _ _

theorem bridgeFin_mem : bridgeFin m ∈ edgesLt (twoCliquesFin m) := by
  simp only [edgesLt, Finset.mem_filter, Finset.mem_univ, true_and, bridgeFin]
  refine ⟨?_, ?_⟩
  · rw [finSumFinEquiv_apply_left, finSumFinEquiv_apply_right, Fin.lt_def]
    simp
  · change (twoCliques m).Adj (finSumFinEquiv.symm (finSumFinEquiv (.inl (Fin.last m))))
      (finSumFinEquiv.symm (finSumFinEquiv (.inr 0)))
    rw [Equiv.symm_apply_apply, Equiv.symm_apply_apply]
    simp [twoCliquesAdj]

theorem kappa_bridgeFin : kappa (twoCliquesFin m) (bridgeFin m) = 4 - 2 * ((m : ℤ) + 1) := by
  rw [kappa_twoCliquesFin]
  simp only [bridgeFin, Equiv.symm_apply_apply]
  exact forman_bridge m

/-- Every other edge ranks above the bridge, and is positive once each clique has two vertices. -/
theorem kappa_other {x : Fin ((m + 1) + (m + 1)) × Fin ((m + 1) + (m + 1))}
    (hx : x ∈ edgesLt (twoCliquesFin m)) (hne : x ≠ bridgeFin m) :
    kappa (twoCliquesFin m) (bridgeFin m) < kappa (twoCliquesFin m) x ∧
      (1 ≤ m → 0 < kappa (twoCliquesFin m) x) := by
  simp only [edgesLt, Finset.mem_filter, Finset.mem_univ, true_and] at hx
  obtain ⟨hlt, hadj⟩ := hx
  have hb : ¬(finSumFinEquiv.symm x.1 = .inl (Fin.last m) ∧ finSumFinEquiv.symm x.2 = .inr 0) := by
    rintro ⟨h1, h2⟩
    rw [Equiv.symm_apply_eq] at h1 h2
    exact hne (Prod.ext h1 h2)
  have hb' : ¬(finSumFinEquiv.symm x.1 = .inr 0 ∧
      finSumFinEquiv.symm x.2 = .inl (Fin.last m)) := by
    rintro ⟨h1, h2⟩
    rw [Equiv.symm_apply_eq] at h1 h2
    rw [h1, h2, Fin.lt_def] at hlt
    simp at hlt
  have hadj' : (twoCliques m).Adj (finSumFinEquiv.symm x.1) (finSumFinEquiv.symm x.2) := hadj
  rw [kappa_bridgeFin, kappa_twoCliquesFin]
  refine ⟨?_, fun hm ↦ forman_pos m hm hadj' hb hb'⟩
  rw [← forman_bridge m]
  exact forman_bridge_lt m hadj' hb hb'

/-- The bridge is the lens's only candidate: by the `κ ≤ 0` rule from two vertices per clique,
and by the minimum rule for single-vertex cliques, where the bridge is the only edge. -/
theorem candidates_twoCliquesFin : candidates (twoCliquesFin m) = {bridgeFin m} := by
  ext x
  rcases Nat.eq_zero_or_pos m with rfl | hm
  · have hpos : ¬((edgesLt (twoCliquesFin 0)).filter fun e ↦
        kappa (twoCliquesFin 0) e ≤ 0).Nonempty := by
      rintro ⟨y, hy⟩
      rw [Finset.mem_filter] at hy
      by_cases hyb : y = bridgeFin 0
      · rw [hyb, kappa_bridgeFin] at hy
        norm_num at hy
      · have := (kappa_other 0 hy.1 hyb).1
        rw [kappa_bridgeFin] at this
        omega
    simp only [candidates, hpos, ↓reduceIte, Finset.mem_filter, Finset.mem_singleton]
    constructor
    · rintro ⟨hx, hmin⟩
      by_contra hxb
      have h1 := (kappa_other 0 hx hxb).1
      have h2 := hmin _ (bridgeFin_mem 0)
      omega
    · rintro rfl
      refine ⟨bridgeFin_mem 0, fun y hy ↦ ?_⟩
      by_cases hyb : y = bridgeFin 0
      · rw [hyb]
      · exact (kappa_other 0 hy hyb).1.le
  · have hneg : ((edgesLt (twoCliquesFin m)).filter fun e ↦
        kappa (twoCliquesFin m) e ≤ 0).Nonempty :=
      ⟨bridgeFin m, Finset.mem_filter.2 ⟨bridgeFin_mem m, by rw [kappa_bridgeFin]; omega⟩⟩
    simp only [candidates, hneg, ↓reduceIte, Finset.mem_filter, Finset.mem_singleton]
    constructor
    · rintro ⟨hx, hκ⟩
      by_contra hxb
      have := (kappa_other m hx hxb).2 hm
      omega
    · rintro rfl
      exact ⟨bridgeFin_mem m, by rw [kappa_bridgeFin]; omega⟩

/-- **CRV-2 and CRV-3** The bridge lens emits the planted bridge and nothing else, for every
clique size and every `top_k ≥ 1`. -/
theorem mostNegative_twoCliquesFin {k : ℕ} (hk : 0 < k) :
    mostNegative (twoCliquesFin m) k = [bridgeFin m] :=
  mostNegative_eq_singleton _ (candidates_twoCliquesFin m) hk

end TwoCliquesFin

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
