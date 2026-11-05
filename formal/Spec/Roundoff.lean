module

public import Palace.Roundoff.Defs

/-!
# Two float64 claims of the laws ledger, machine-checked: CND-6 and LAP-1, the statements

L3 enters one claim at a time, where a design claim demands a machine-checked ε-bound
(dn-mathematical-foundations §2.4, non-goal 2). The note's §2.5 makes two claims about what float64
arithmetic computes. Both are settled here over the binary64 model `rn` of `Palace/Binary64.lean`,
and `Palace/FloatModel.lean` carries them to Lean's own `Float`.

**CND-6.** `chi_s` (`core/graph/conductance.py:397`) is one true division `chain / n_s` of two
naturals, and §2.5 calls its comparisons with `1.0` exact: `n/n = 1.0`, and `(n−1)/n` rounds
strictly below `1.0` "for realistic N_s". Python divides two ints by rounding their exact quotient
once, so `chi_s` is `rn (chain / n_s)`. It is `1.0` exactly when the chain spans the stratum, for
every stratum of fewer than `2^54` events, and `2^54` is where that fails. It lies in `(0, 1]` up to
`2^1074` events.

**LAP-1.** The route-agreement doctrine of `tests/unit/test_graph_boundary.py`, which §2.5 adopts
as the model entry for float error "bounded by construction": the two Laplacian routes sum each
degree in different association orders and agree within `4·eps·max(1, max deg)`. Any two
association orders of at most four nonzero nonnegative binary64 summands agree within `4·eps` of
either result, which covers every row of the test's fixtures, whatever orders NumPy and SciPy use.
At eight summands two orders differ by five ulps, beyond the bound. For five to seven it is neither
proved nor refuted here: an exhaustive search over every association order of one summand near `1`
and the rest small multiples of `u/2` found no counterexample. The bound holds for short rows, not
by construction.

These are the laws of `Palace/Roundoff.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

namespace Palace.Binary64

variable {K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K]

section Chi

/-- **CND-6** `chain / n_s` rounds to `1.0` exactly when the chain spans the stratum, for every
stratum of fewer than `2^54` events. -/
theorem rn_div_eq_one_iff {k n : ℕ} (hk : k ≤ n) (hn : n < 2 ^ 54) (h0 : 0 < n) :
    rn ((k : K) / n) = 1 ↔ k = n :=
  sorry

/-- **CND-6** `2^54` is where it fails: `(2^54 − 1)/2^54 = 1 − 2⁻⁵⁴` is the midpoint between `1`
and its predecessor, and the tie goes to `1`, whose significand is even. -/
theorem rn_div_two_pow_54 : rn (((2 ^ 54 - 1 : ℕ) : K) / (2 ^ 54 : ℕ)) = 1 :=
  sorry

/-- **CND-6** `chi_s ≤ 1` survives rounding for every `chain ≤ n_s`. -/
theorem rn_div_le_one {k n : ℕ} (hk : k ≤ n) : rn ((k : K) / n) ≤ 1 :=
  sorry

/-- **CND-6** `chi_s > 0` survives rounding for every stratum of at most `2^1074` events: the
quotient is at least the least subnormal `2⁻¹⁰⁷⁴`. -/
theorem rn_div_pos {k n : ℕ} (h1 : 1 ≤ k) (hk : k ≤ n) (hn : n ≤ 2 ^ 1074) :
    0 < rn ((k : K) / n) :=
  sorry

end Chi

section Reassoc

namespace SumTree

/-- **LAP-1** Two association orders of the same at most four nonzero nonnegative binary64
summands agree within `4 · eps` of either result, `eps = 2⁻⁵²`, so within the boundary test's
`4 · eps · max(1, max deg)`, whatever orders the two routes use. -/
theorem agreement {t₁ t₂ : SumTree K} (hp : t₁.leaves.Perm t₂.leaves)
    (ht : ∀ x ∈ t₂.leaves, 0 ≤ x ∧ IsFloat x) (h4 : t₂.nz ≤ 4) :
    |t₁.fl - t₂.fl| ≤ 4 * 2 ^ (-52 : ℤ) * t₂.fl :=
  sorry

/-- **LAP-1** fails at eight summands: the same eight nonnegative binary64 summands, in two
association orders, differ by five ulps of `1`, beyond `4 · eps · max(1, either result)`. -/
theorem lap1_fails :
    (∀ x ∈ (high : SumTree K).leaves, 0 ≤ x ∧ IsFloat x) ∧
      (low : SumTree K).leaves.Perm (high : SumTree K).leaves ∧ (high : SumTree K).nz = 8 ∧
      4 * 2 ^ (-52 : ℤ) * max 1 (max (low : SumTree K).fl (high : SumTree K).fl) <
        |(low : SumTree K).fl - (high : SumTree K).fl| :=
  sorry

end SumTree

end Reassoc

end Palace.Binary64
