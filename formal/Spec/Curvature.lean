module

public import Palace.Curvature.Defs

/-!
# Forman–Ricci curvature: CRV-1, CRV-2 and CRV-3, the statements

`Ric_F(u, v) = 4 − deg u − deg v + 3·|△(u, v)|` on the binarized support (`curvature.py`,
`forman`; dn-mathematical-foundations §2.2, seed table IV), the planted-bridge law on the family
of `test_planted_bridge_is_negative_and_clique_edges_positive`, and the emission rule of
`most_negative_edges`, which the Dreamer's bridge lens reads (`core/dreaming/interpreters.py`).
Exact, over ℤ.

These are the laws of `Palace/Curvature.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

open Finset

namespace Palace

/-! ### CRV-2: two cliques and a bridge -/

section TwoCliques

variable (m : ℕ)

open SimpleGraph Function

/-- **CRV-2** The bridge's curvature is `4 − 2(m + 1)`: `m + 1` neighbours at each end, and no
triangle. -/
theorem forman_bridge :
    forman (twoCliques m) (.inl (Fin.last m)) (.inr 0) = 4 - 2 * ((m : ℤ) + 1) :=
  sorry

/-- **CRV-2** The bridge is the strict unique minimum: every other edge is curved more. -/
theorem forman_bridge_lt {x y : Fin (m + 1) ⊕ Fin (m + 1)} (hxy : (twoCliques m).Adj x y)
    (hb : ¬ (x = .inl (Fin.last m) ∧ y = .inr 0)) (hb' : ¬ (x = .inr 0 ∧ y = .inl (Fin.last m))) :
    forman (twoCliques m) (.inl (Fin.last m)) (.inr 0) < forman (twoCliques m) x y :=
  sorry

/-- **CRV-2** The bridge is negatively curved exactly when each clique has at least three vertices
(`m + 1 ≥ 3`). -/
theorem forman_bridge_neg_iff :
    forman (twoCliques m) (.inl (Fin.last m)) (.inr 0) < 0 ↔ 3 ≤ m + 1 :=
  sorry

/-- **CRV-2** Off the bridge every edge is positively curved once each clique has two vertices:
at least `m` against the bridge's `2 − 2m`. -/
theorem forman_pos {x y : Fin (m + 1) ⊕ Fin (m + 1)} (hm : 1 ≤ m) (hxy : (twoCliques m).Adj x y)
    (hb : ¬ (x = .inl (Fin.last m) ∧ y = .inr 0)) (hb' : ¬ (x = .inr 0 ∧ y = .inl (Fin.last m))) :
    0 < forman (twoCliques m) x y :=
  sorry

end TwoCliques

/-! ### CRV-3: the bridge lens's emission rule -/

section Emission

variable {V : Type*} [Fintype V] [LinearOrder V] (G : SimpleGraph V) [DecidableRel G.Adj]

/-- **CRV-3** When some edge is curved `≤ 0`, only such edges are emitted. -/
theorem kappa_nonpos {k : ℕ} {e : V × V} (h : e ∈ mostNegative G k)
    (h0 : ∃ e' ∈ edgesLt G, kappa G e' ≤ 0) : kappa G e ≤ 0 :=
  sorry

/-- **CRV-3** When every edge is positive, only edges at the minimum are emitted. -/
theorem kappa_min {k : ℕ} {e : V × V} (h : e ∈ mostNegative G k)
    (h0 : ∀ e' ∈ edgesLt G, 0 < kappa G e') : ∀ e' ∈ edgesLt G, kappa G e ≤ kappa G e' :=
  sorry

/-- **CRV-3** The emission is in strictly increasing `(κ, i, j)` order, so reproducible. -/
theorem mostNegative_pairwise (k : ℕ) :
    (mostNegative G k).Pairwise fun a b ↦ emitKey G a < emitKey G b :=
  sorry

/-- **CRV-3** At most `top_k` edges: `min(top_k, |candidates|)` of them. -/
theorem length_mostNegative (k : ℕ) : (mostNegative G k).length = min k (candidates G).card :=
  sorry

/-- **CRV-3** A larger `top_k` extends the emission and never reorders it. -/
theorem mostNegative_prefix {k k' : ℕ} (h : k ≤ k') : mostNegative G k <+: mostNegative G k' :=
  sorry

end Emission

end Palace
