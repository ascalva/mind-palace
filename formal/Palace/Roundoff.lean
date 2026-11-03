module

public import Mathlib.Algebra.BigOperators.Group.List.Basic
public import Palace.Binary64
public meta import Mathlib.Algebra.BigOperators.Group.List.Basic
public meta import Palace.Binary64

/-!
# Two float64 claims of the laws ledger, machine-checked: CND-6 and LAP-1

L3 enters one claim at a time, where a design claim demands a machine-checked ε-bound
(dn-mathematical-foundations §2.4, non-goal 2). The note's §2.5 makes two claims about what float64
arithmetic computes. Both are settled here over the binary64 model `rn` of `Palace/Binary64.lean`,
and `Palace/FloatModel.lean` carries them to Lean's own `Float`.

**CND-6.** `chi_s` (`core/graph/conductance.py:390`) is one true division `chain / n_s` of two
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
-/

@[expose] public section

namespace Palace.Binary64

variable {K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K]

section Chi

theorem rn_half : rn (1 / 2 : K) = 1 / 2 :=
  rn_isFloat ⟨1, -1, by norm_num, by norm_num, by norm_num⟩

/-- Below `1 − 2⁻⁵⁴`, the midpoint between `1` and its predecessor `1 − 2⁻⁵³`, `rn` stays below
`1`. -/
theorem rn_lt_one {x : K} (hx : x < 1 - 2 ^ (-54 : ℤ)) : rn x < 1 := by
  rcases lt_or_ge x (1 / 2) with h | h
  · calc rn x ≤ rn (1 / 2) := rn_mono h.le
      _ = 1 / 2 := rn_half
      _ < 1 := by norm_num
  · have h1 : (2 : K) ^ (-1 : ℤ) ≤ x := by norm_num; linarith
    have h2 : x < 2 ^ (-1 + 1 : ℤ) := by norm_num at hx ⊢; linarith
    rw [rn_of_binade h1 h2 (by norm_num)]
    have hz : rne (x / 2 ^ (-1 - 52 : ℤ)) ≤ 2 ^ 53 - 1 := by
      apply rne_le_of_lt_add_half
      rw [div_lt_iff₀ (by positivity)]
      norm_num at hx ⊢; linarith
    calc (rne (x / 2 ^ (-1 - 52 : ℤ)) : K) * 2 ^ (-1 - 52 : ℤ)
        ≤ ((2 ^ 53 - 1 : ℤ) : K) * 2 ^ (-1 - 52 : ℤ) := by gcongr
      _ < 1 := by norm_num

/-- **CND-6** `chain / n_s` rounds to `1.0` exactly when the chain spans the stratum, for every
stratum of fewer than `2^54` events. -/
theorem rn_div_eq_one_iff {k n : ℕ} (hk : k ≤ n) (hn : n < 2 ^ 54) (h0 : 0 < n) :
    rn ((k : K) / n) = 1 ↔ k = n := by
  refine ⟨fun h ↦ ?_, fun h ↦ by rw [h, div_self (by positivity), rn_one]⟩
  by_contra hne
  have hk1 : (k : K) + 1 ≤ n := by exact_mod_cast lt_of_le_of_ne hk hne
  have hn0 : (0 : K) < n := by exact_mod_cast h0
  have hn' : (n : K) * 2 ^ (-54 : ℤ) < 1 := by
    rw [show (2 : K) ^ (-54 : ℤ) = 1 / 2 ^ 54 by norm_num, mul_one_div,
      div_lt_one (by positivity)]
    exact_mod_cast hn
  have : (k : K) / n < 1 - 2 ^ (-54 : ℤ) := by
    rw [div_lt_iff₀ hn0]; linarith
  exact (rn_lt_one this).ne h

/-- **CND-6** `2^54` is where it fails: `(2^54 − 1)/2^54 = 1 − 2⁻⁵⁴` is the midpoint between `1`
and its predecessor, and the tie goes to `1`, whose significand is even. -/
theorem rn_div_two_pow_54 : rn (((2 ^ 54 - 1 : ℕ) : K) / (2 ^ 54 : ℕ)) = 1 := by
  have hx : ((2 ^ 54 - 1 : ℕ) : K) / (2 ^ 54 : ℕ) = 1 - 2 ^ (-54 : ℤ) := by norm_num
  rw [hx, rn_of_binade (l := -1) (by norm_num) (by norm_num) (by norm_num)]
  have : (1 - 2 ^ (-54 : ℤ) : K) / 2 ^ (-1 - 52 : ℤ) = ((2 ^ 53 - 1 : ℤ) : K) + 1 / 2 := by
    norm_num
  rw [this, rne_tie_odd (by norm_num)]
  norm_num

/-- **CND-6** `chi_s ≤ 1` survives rounding for every `chain ≤ n_s`. -/
theorem rn_div_le_one {k n : ℕ} (hk : k ≤ n) : rn ((k : K) / n) ≤ 1 := by
  rcases Nat.eq_zero_or_pos n with rfl | h0
  · simp
  calc rn ((k : K) / n) ≤ rn 1 :=
        rn_mono (div_le_one_of_le₀ (by exact_mod_cast hk) (Nat.cast_nonneg n))
    _ = 1 := rn_one

/-- **CND-6** `chi_s > 0` survives rounding for every stratum of at most `2^1074` events: the
quotient is at least the least subnormal `2⁻¹⁰⁷⁴`. -/
theorem rn_div_pos {k n : ℕ} (h1 : 1 ≤ k) (hk : k ≤ n) (hn : n ≤ 2 ^ 1074) :
    0 < rn ((k : K) / n) := by
  have hn0 : (0 : K) < n := by exact_mod_cast (by omega : 0 < n)
  have hle : (2 : K) ^ (-1074 : ℤ) ≤ k / n := by
    rw [le_div_iff₀ hn0]
    have hn' : (n : K) ≤ 2 ^ 1074 := by exact_mod_cast hn
    have hk' : (1 : K) ≤ k := by exact_mod_cast h1
    calc 2 ^ (-1074 : ℤ) * (n : K) ≤ 2 ^ (-1074 : ℤ) * 2 ^ 1074 := by gcongr
      _ = 1 := by norm_num
      _ ≤ k := hk'
  calc (0 : K) < 2 ^ (-1074 : ℤ) := by positivity
    _ = rn ((2 : K) ^ (-1074 : ℤ)) :=
      (rn_isFloat (K := K) ⟨1, -1074, by norm_num, le_rfl, by simp⟩).symm
    _ ≤ rn ((k : K) / n) := rn_mono hle

end Chi

section Reassoc

/-- A summation order: a binary tree over the summands, each node one rounded addition. -/
inductive SumTree (K : Type*) where
  | leaf (x : K)
  | node (l r : SumTree K)

namespace SumTree

/-- The exact sum. -/
def exact : SumTree K → K
  | leaf x => x
  | node l r => l.exact + r.exact

/-- The float64 sum, rounding after each addition. -/
def fl : SumTree K → K
  | leaf x => x
  | node l r => rn (l.fl + r.fl)

/-- The summands, left to right. -/
def leaves : SumTree K → List K
  | leaf x => [x]
  | node l r => l.leaves ++ r.leaves

/-- The number of nonzero summands. -/
def nz (t : SumTree K) : ℕ := (t.leaves.filter (· ≠ 0)).length

omit [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K] in
theorem exact_eq_sum (t : SumTree K) : t.exact = t.leaves.sum := by
  induction t with
  | leaf x => simp [exact, leaves]
  | node l r ihl ihr => simp [exact, leaves, ihl, ihr]

omit [IsStrictOrderedRing K] [FloorRing K] in
theorem nz_node (l r : SumTree K) : (node l r).nz = l.nz + r.nz := by
  simp [nz, leaves, List.filter_append]

omit [IsStrictOrderedRing K] [FloorRing K] in
theorem nz_leaf_le (x : K) : (leaf x).nz ≤ 1 := by
  simp only [nz, leaves]
  exact (List.length_filter_le _ _).trans (by simp)

omit [IsStrictOrderedRing K] [FloorRing K] in
theorem eq_zero_of_nz_eq_zero {t : SumTree K} (h : t.nz = 0) : ∀ x ∈ t.leaves, x = 0 := by
  intro x hx
  by_contra hne
  have : x ∈ t.leaves.filter (· ≠ 0) := List.mem_filter.2 ⟨hx, by simpa using hne⟩
  rw [nz, List.length_eq_zero_iff] at h
  rw [h] at this
  simp at this

theorem fl_eq_zero_of_nz_eq_zero {t : SumTree K} (h : t.nz = 0) : t.fl = 0 ∧ t.exact = 0 := by
  induction t with
  | leaf x =>
    have := eq_zero_of_nz_eq_zero h x (by simp [leaves])
    simp [fl, exact, this]
  | node l r ihl ihr =>
    rw [nz_node] at h
    obtain ⟨h1, h2⟩ := ihl (by omega)
    obtain ⟨h3, h4⟩ := ihr (by omega)
    simp [fl, exact, h1, h2, h3, h4]

theorem isFloat_fl {t : SumTree K} (ht : ∀ x ∈ t.leaves, IsFloat x) : IsFloat t.fl := by
  cases t with
  | leaf x => exact ht x (by simp [leaves])
  | node l r => exact isFloat_rn _

omit [FloorRing K] in
theorem exact_nonneg {t : SumTree K} (ht : ∀ x ∈ t.leaves, 0 ≤ x) : 0 ≤ t.exact := by
  rw [exact_eq_sum]; exact List.sum_nonneg ht

theorem fl_nonneg {t : SumTree K} (ht : ∀ x ∈ t.leaves, 0 ≤ x) : 0 ≤ t.fl := by
  induction t with
  | leaf x => exact ht x (by simp [leaves])
  | node l r ihl ihr =>
    exact rn_nonneg (add_nonneg (ihl fun x hx ↦ ht x (by simp [leaves, hx]))
      (ihr fun x hx ↦ ht x (by simp [leaves, hx])))

/-- **LAP-1** A sum of nonnegative binary64 numbers with `n` nonzero summands lies within
`(1 ± u)^(n−1)` of the exact sum, in every association order: each rounded addition errs by at most
`u` relative, and adding zero is exact. -/
theorem envelope (t : SumTree K) (ht : ∀ x ∈ t.leaves, 0 ≤ x ∧ IsFloat x) :
    (1 - u) ^ (t.nz - 1) * t.exact ≤ t.fl ∧ t.fl ≤ (1 + u) ^ (t.nz - 1) * t.exact := by
  induction t with
  | leaf x =>
    have : (leaf x).nz - 1 = 0 := by have := nz_leaf_le x; omega
    simp [this, fl, exact]
  | node l r ihl ihr =>
    have hl : ∀ x ∈ l.leaves, 0 ≤ x ∧ IsFloat x := fun x hx ↦ ht x (by simp [leaves, hx])
    have hr : ∀ x ∈ r.leaves, 0 ≤ x ∧ IsFloat x := fun x hx ↦ ht x (by simp [leaves, hx])
    obtain ⟨l1, l2⟩ := ihl hl
    obtain ⟨r1, r2⟩ := ihr hr
    have hlf : IsFloat l.fl := isFloat_fl fun x hx ↦ (hl x hx).2
    have hrf : IsFloat r.fl := isFloat_fl fun x hx ↦ (hr x hx).2
    have hEl : 0 ≤ l.exact := exact_nonneg fun x hx ↦ (hl x hx).1
    have hEr : 0 ≤ r.exact := exact_nonneg fun x hx ↦ (hr x hx).1
    have hFl : 0 ≤ l.fl := fl_nonneg fun x hx ↦ (hl x hx).1
    have hFr : 0 ≤ r.fl := fl_nonneg fun x hx ↦ (hr x hx).1
    simp only [fl, exact, nz_node]
    rcases Nat.eq_zero_or_pos l.nz with h0 | ha
    · obtain ⟨hf, he⟩ := fl_eq_zero_of_nz_eq_zero h0
      rw [hf, he, zero_add, zero_add, h0, zero_add, rn_isFloat hrf]
      exact ⟨r1, r2⟩
    rcases Nat.eq_zero_or_pos r.nz with h0 | hb
    · obtain ⟨hf, he⟩ := fl_eq_zero_of_nz_eq_zero h0
      rw [hf, he, add_zero, add_zero, h0, add_zero, rn_isFloat hlf]
      exact ⟨l1, l2⟩
    -- both sides carry nonzero summands
    have herr := abs_rn_sub_le_of_onGrid (hlf.onGrid.add hrf.onGrid)
    rw [abs_of_nonneg (add_nonneg hFl hFr), abs_le] at herr
    have hu : (0 : K) ≤ u := by positivity
    have hu1 : u ≤ (1 : K) := by norm_num [u]
    obtain ⟨a, ha⟩ : ∃ a, l.nz = a + 1 := ⟨l.nz - 1, by omega⟩
    obtain ⟨b, hb⟩ : ∃ b, r.nz = b + 1 := ⟨r.nz - 1, by omega⟩
    rw [ha, Nat.add_sub_cancel] at l1 l2
    rw [hb, Nat.add_sub_cancel] at r1 r2
    rw [ha, hb, show a + 1 + (b + 1) - 1 = a + b + 1 by omega]
    have hA : (1 + (u : K)) ^ (a + 1) ≤ (1 + u) ^ (a + b + 1) :=
      pow_le_pow_right₀ (by linarith) (by omega)
    have hB : (1 + (u : K)) ^ (b + 1) ≤ (1 + u) ^ (a + b + 1) :=
      pow_le_pow_right₀ (by linarith) (by omega)
    have hA' : (1 - (u : K)) ^ (a + b + 1) ≤ (1 - u) ^ (a + 1) :=
      pow_le_pow_of_le_one (by linarith) (by linarith) (by omega)
    have hB' : (1 - (u : K)) ^ (a + b + 1) ≤ (1 - u) ^ (b + 1) :=
      pow_le_pow_of_le_one (by linarith) (by linarith) (by omega)
    constructor
    · calc (1 - u) ^ (a + b + 1) * (l.exact + r.exact)
          = (1 - u) ^ (a + b + 1) * l.exact + (1 - u) ^ (a + b + 1) * r.exact := by ring
        _ ≤ (1 - u) ^ (a + 1) * l.exact + (1 - u) ^ (b + 1) * r.exact := by gcongr
        _ = (1 - u) * ((1 - u) ^ a * l.exact + (1 - u) ^ b * r.exact) := by ring
        _ ≤ (1 - u) * (l.fl + r.fl) := by
          have : (0 : K) ≤ 1 - u := by linarith
          gcongr
        _ ≤ rn (l.fl + r.fl) := by linarith [herr.1]
    · calc rn (l.fl + r.fl) ≤ (1 + u) * (l.fl + r.fl) := by linarith [herr.2]
        _ ≤ (1 + u) * ((1 + u) ^ a * l.exact + (1 + u) ^ b * r.exact) := by gcongr
        _ = (1 + u) ^ (a + 1) * l.exact + (1 + u) ^ (b + 1) * r.exact := by ring
        _ ≤ (1 + u) ^ (a + b + 1) * l.exact + (1 + u) ^ (a + b + 1) * r.exact := by gcongr
        _ = (1 + u) ^ (a + b + 1) * (l.exact + r.exact) := by ring

/-- **LAP-1** Two association orders of the same at most four nonzero nonnegative binary64
summands agree within `4 · eps` of either result, `eps = 2⁻⁵²`, so within the boundary test's
`4 · eps · max(1, max deg)`, whatever orders the two routes use. -/
theorem agreement {t₁ t₂ : SumTree K} (hp : t₁.leaves.Perm t₂.leaves)
    (ht : ∀ x ∈ t₂.leaves, 0 ≤ x ∧ IsFloat x) (h4 : t₂.nz ≤ 4) :
    |t₁.fl - t₂.fl| ≤ 4 * 2 ^ (-52 : ℤ) * t₂.fl := by
  have ht₁ : ∀ x ∈ t₁.leaves, 0 ≤ x ∧ IsFloat x := fun x hx ↦ ht x (hp.subset hx)
  have hS : t₁.exact = t₂.exact := by rw [exact_eq_sum, exact_eq_sum, hp.sum_eq]
  have hn : t₁.nz = t₂.nz := (hp.filter _).length_eq
  obtain ⟨a1, a2⟩ := envelope t₁ ht₁
  obtain ⟨b1, b2⟩ := envelope t₂ ht
  rw [hS, hn] at a1 a2
  have hE : 0 ≤ t₂.exact := exact_nonneg fun x hx ↦ (ht x hx).1
  generalize hm : t₂.nz - 1 = m at a1 a2 b1 b2
  have key : (1 + (u : K)) ^ m - (1 - u) ^ m ≤ 8 * u * (1 - u) ^ m := by
    have : m ≤ 3 := by omega
    interval_cases m <;> norm_num [u]
  have hd : ((1 + u) ^ m - (1 - u) ^ m) * t₂.exact ≤ 8 * u * ((1 - u) ^ m * t₂.exact) := by
    calc ((1 + u) ^ m - (1 - u) ^ m) * t₂.exact ≤ 8 * u * (1 - u) ^ m * t₂.exact := by gcongr
      _ = _ := by ring
  have hf : 8 * u * ((1 - u) ^ m * t₂.exact) ≤ 8 * u * t₂.fl := by gcongr
  rw [show (4 : K) * 2 ^ (-52 : ℤ) = 8 * u by norm_num [u], abs_le]
  constructor <;> nlinarith

/-- `n` more additions of `x` onto the order `s`, one at a time. -/
def chain (s : SumTree K) (x : K) : ℕ → SumTree K
  | 0 => s
  | n + 1 => node (chain s x n) (leaf x)

omit [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K] in
theorem leaves_chain (s : SumTree K) (x : K) (n : ℕ) :
    (chain s x n).leaves = s.leaves ++ List.replicate n x := by
  induction n with
  | zero => simp [chain]
  | succ n ih => simp [chain, leaves, ih, List.replicate_succ']

/-- Near `1` the grid spacing is `2u`, so `1 + 2j·u` is on it. -/
theorem rn_one_add_grid (j : ℕ) (hj : j < 2 ^ 51) : rn (1 + 2 * j * u : K) = 1 + 2 * j * u :=
  rn_isFloat ⟨2 ^ 52 + j, -52, by rw [abs_of_nonneg (by positivity)]; omega, by norm_num,
    by push_cast; norm_num [u]; ring⟩

/-- `1 + (2j + 1)·u` is a tie between `1 + 2j·u` and `1 + 2(j + 1)·u`; ties to even picks the
first when `j` is even and the second when `j` is odd. -/
theorem rn_one_add_tie (j : ℕ) (hj : j < 2 ^ 50) :
    rn (1 + (2 * j + 1) * u : K) = 1 + 2 * (j + j % 2 : ℕ) * u := by
  have hju : (2 * j + 1 : K) * u < 1 := by
    have : (j : K) < 2 ^ 50 := by exact_mod_cast hj
    norm_num [u]; nlinarith
  have h0 : (0 : K) ≤ (2 * j + 1) * u := by positivity
  have h1 : (2 : K) ^ (0 : ℤ) ≤ 1 + (2 * j + 1) * u := by rw [zpow_zero]; linarith
  have h2 : (1 + (2 * j + 1) * u : K) < 2 ^ (0 + 1 : ℤ) := by rw [zero_add, zpow_one]; linarith
  rw [rn_of_binade h1 h2 (by norm_num)]
  have hx : (1 + (2 * j + 1) * u : K) / 2 ^ (0 - 52 : ℤ) = ((2 ^ 52 + j : ℤ) : K) + 1 / 2 := by
    push_cast; norm_num [u]; ring
  rw [hx]
  rcases Nat.mod_two_eq_zero_or_one j with h | h
  · rw [rne_tie_even (by omega), h]; push_cast; norm_num [u]; ring
  · rw [rne_tie_odd (by omega), h]; push_cast; norm_num [u]; ring

/-- The witness's summands: `1 + 2u`, an odd point of the grid near `1`, then `3u` and six
`u`. Low: the `3u` first and then the `u`s, one at a time; every tie goes down. -/
def low : SumTree K := chain (node (leaf (1 + 2 * u)) (leaf (3 * u))) u 6

/-- High: the `u`s first, two of the pairs summed before they are added, and the `3u` late;
three ties go up. -/
def high : SumTree K :=
  node (node (node (node (node (leaf (1 + 2 * u)) (leaf u)) (node (leaf u) (leaf u))) (leaf u))
    (leaf (3 * u))) (node (leaf u) (leaf u))

theorem low_fl : (low : SumTree K).fl = 1 + 4 * u := by
  have hstep : rn (1 + 4 * u + u : K) = 1 + 4 * u := by
    rw [show (1 + 4 * u + u : K) = 1 + (2 * (2 : ℕ) + 1) * u by push_cast; ring,
      rn_one_add_tie 2 (by norm_num)]
    norm_num
  have h0 : rn (1 + 2 * u + 3 * u : K) = 1 + 4 * u := by
    rw [show (1 + 2 * u + 3 * u : K) = 1 + 4 * u + u by ring, hstep]
  have : ∀ n, (chain (node (leaf (1 + 2 * u)) (leaf (3 * u))) (u : K) n).fl = 1 + 4 * u := by
    intro n
    induction n with
    | zero => exact h0
    | succ n ih => simp only [chain, fl] at ih ⊢; rw [ih, hstep]
  exact this 6

theorem high_fl : (high : SumTree K).fl = 1 + 14 * u := by
  have h2 : rn ((u : K) + u) = 2 * u := by
    rw [rn_isFloat (x := (u : K) + u) ⟨1, -52, by norm_num, by norm_num, by norm_num [u]⟩]; ring
  have s1 : rn (1 + 2 * u + u : K) = 1 + 4 * u := by
    rw [show (1 + 2 * u + u : K) = 1 + (2 * (1 : ℕ) + 1) * u by push_cast; ring,
      rn_one_add_tie 1 (by norm_num)]
    norm_num
  have s2 : rn (1 + 4 * u + 2 * u : K) = 1 + 6 * u := by
    rw [show (1 + 4 * u + 2 * u : K) = 1 + 2 * (3 : ℕ) * u by push_cast; ring,
      rn_one_add_grid 3 (by norm_num)]
    norm_num
  have s3 : rn (1 + 6 * u + u : K) = 1 + 8 * u := by
    rw [show (1 + 6 * u + u : K) = 1 + (2 * (3 : ℕ) + 1) * u by push_cast; ring,
      rn_one_add_tie 3 (by norm_num)]
    norm_num
  have s4 : rn (1 + 8 * u + 3 * u : K) = 1 + 12 * u := by
    rw [show (1 + 8 * u + 3 * u : K) = 1 + (2 * (5 : ℕ) + 1) * u by push_cast; ring,
      rn_one_add_tie 5 (by norm_num)]
    norm_num
  have s5 : rn (1 + 12 * u + 2 * u : K) = 1 + 14 * u := by
    rw [show (1 + 12 * u + 2 * u : K) = 1 + 2 * (7 : ℕ) * u by push_cast; ring,
      rn_one_add_grid 7 (by norm_num)]
    norm_num
  simp only [high, fl, h2, s1, s2, s3, s4, s5]

/-- **LAP-1** fails at eight summands: the same eight nonnegative binary64 summands, in two
association orders, differ by five ulps of `1`, beyond `4 · eps · max(1, either result)`. -/
theorem lap1_fails :
    (∀ x ∈ (high : SumTree K).leaves, 0 ≤ x ∧ IsFloat x) ∧
      (low : SumTree K).leaves.Perm (high : SumTree K).leaves ∧ (high : SumTree K).nz = 8 ∧
      4 * 2 ^ (-52 : ℤ) * max 1 (max (low : SumTree K).fl (high : SumTree K).fl) <
        |(low : SumTree K).fl - (high : SumTree K).fl| := by
  have hu : (0 : K) < u := by positivity
  have hh : (high : SumTree K).leaves = (1 + 2 * u) :: ([u, u, u, u] ++ 3 * u :: [u, u]) := by
    simp [high, leaves]
  have hl : (low : SumTree K).leaves = (1 + 2 * u) :: 3 * u :: ([u, u, u, u] ++ [u, u]) := by
    simp [low, leaves_chain, leaves, List.replicate_succ]
  have hB : IsFloat (1 + 2 * u : K) :=
    ⟨2 ^ 52 + 1, -52, by norm_num, by norm_num, by push_cast; norm_num [u]⟩
  have h1 : IsFloat (u : K) := ⟨1, -53, by norm_num, by norm_num, by simp [u]⟩
  have h3 : IsFloat (3 * u : K) := ⟨3, -53, by norm_num, by norm_num, by simp [u]⟩
  have hpos : ∀ x ∈ (high : SumTree K).leaves, 0 < x ∧ IsFloat x := by
    rw [hh]
    intro x hx
    simp only [List.cons_append, List.nil_append, List.mem_cons, List.not_mem_nil, or_false]
      at hx
    rcases hx with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl <;>
      first | exact ⟨by positivity, hB⟩ | exact ⟨hu, h1⟩ | exact ⟨by positivity, h3⟩
  refine ⟨fun x hx ↦ ⟨(hpos x hx).1.le, (hpos x hx).2⟩, ?_, ?_, ?_⟩
  · rw [hl, hh]
    exact List.Perm.cons _ List.perm_middle.symm
  · rw [nz, List.filter_eq_self.2 fun x hx ↦ decide_eq_true (hpos x hx).1.ne', hh]
    rfl
  · rw [low_fl, high_fl]
    norm_num [u]

end SumTree

end Reassoc

/-! ## Attacks: both claims on this machine

The theorems hold over the model; these run the same statements in this machine's binary64. LAP-1:
rows of one to four nonnegative weights, summed left to right, right to left and pairwise, agree
within `4 · eps` of each result. The control draws eleven summands, `1` and ten copies of one `t`
between a quarter and a half ulp of `1`, absorbed one at a time or gathered first, and must break
the bound. CND-6: `k / n == 1.0` exactly
when `k = n`, below `2^53`. The control asks the same of binary32, whose 24-bit significand rounds
`(n − 1)/n` to `1` from `n ≈ 2^24` on.
-/

namespace Attack

open Plausible

/-- A degree's nonzero weights, as bits. -/
structure Row where
  w : List UInt64

instance : Repr Row where
  reprPrec r _ := repr (r.w.map Float.ofBits)

instance : Shrinkable Row := ⟨fun _ ↦ []⟩

/-- One to four weights with random significands, within eight binades of `1` or, one time in
eight, subnormal. -/
instance : Arbitrary Row where
  arbitrary := do
    let k := (← Gen.choose Nat 1 4 (by omega)).1
    let w ← (List.range k).mapM fun _ ↦ do
      let sub := (← Gen.choose Nat 0 7 (by omega)).1
      let e := (← Gen.choose Nat 1015 1031 (by omega)).1
      let m := (← Gen.choose Nat 0 (2 ^ 52 - 1) (by omega)).1
      return UInt64.ofNat ((if sub = 0 then 0 else e) * 2 ^ 52 + m)
    return ⟨w⟩

/-- Pairwise summation of up to four summands. -/
def pairwise : List Float → Float
  | [a, b, c, d] => (a + b) + (c + d)
  | [a, b, c] => (a + b) + c
  | xs => xs.foldl (· + ·) 0

/-- The row summed left to right, right to left and pairwise, as exact values. -/
def sums (r : Row) : List ℚ :=
  let xs := r.w.map Float.ofBits
  [xs.foldl (· + ·) 0, xs.foldr (· + ·) 0, pairwise xs].filterMap toRat?

/-- The orders do not all agree: the row reassociates. -/
def reassociates (r : Row) : Bool :=
  (sums r).any fun a ↦ (sums r).any (· != a)

/-- The three orders agree pairwise within `4 · eps` of each result. -/
def agreeWithin (r : Row) : Bool :=
  (sums r).length == 3 &&
    (sums r).all fun a ↦ (sums r).all fun b ↦ decide (|a - b| ≤ 4 * 2 ^ (-52 : ℤ) * b)

/- LAP-1: up to four summands, three orders, counting only rows that reassociate. -/
#eval survives (∀ r : Row, reassociates r = true → agreeWithin r = true) 137

/-- One `t` in `[2⁻⁵⁴, 2⁻⁵³)`, as bits. -/
structure Small where
  t : UInt64

instance : Repr Small := ⟨fun w _ ↦ repr (Float.ofBits w.t)⟩

instance : Shrinkable Small := ⟨fun _ ↦ []⟩

instance : Arbitrary Small where
  arbitrary := do
    let m := (← Gen.choose Nat 0 (2 ^ 52 - 1) (by omega)).1
    return ⟨UInt64.ofNat (969 * 2 ^ 52 + m)⟩

/-- `1` and ten `t`s, absorbed one at a time and gathered first, agree within the test's bound. -/
def elevenAgree (w : Small) : Bool :=
  let t := Float.ofBits w.t
  let absorbed := (List.replicate 10 t).foldl (· + ·) 1
  let gathered := 1 + (List.replicate 9 t).foldl (· + ·) t
  match toRat? absorbed, toRat? gathered with
  | some a, some b => decide (|a - b| ≤ 4 * 2 ^ (-52 : ℤ) * max 1 (max a b))
  | _, _ => false

/- Control, eleven summands absorbed one at a time or gathered first. -/
#eval refuted (∀ w : Small, elevenAgree w = true) 138

/-- The witness of `lap1_fails` on this machine: from `1 + 2u`, the low order gives `1 + 4u` and
the high order `1 + 14u`. -/
def lap1Witness : Bool :=
  let u : Float := 1 / 9007199254740992
  let b : Float := 1 + 2 * u
  let low := (List.replicate 6 u).foldl (· + ·) (b + 3 * u)
  let high := ((((b + u) + (u + u)) + u) + 3 * u) + (u + u)
  toRat? low == some (1 + 4 * 2 ^ (-53 : ℤ)) && toRat? high == some (1 + 14 * 2 ^ (-53 : ℤ))

#eval show Lean.CoreM Unit from do
  unless lap1Witness do throwError "the LAP-1 witness does not reproduce on this machine"
  Lean.logInfo "the LAP-1 witness reproduces on this machine"

/- CND-6: `k / n == 1.0` exactly when `k = n`, for `k ≤ n < 2^53`. -/
#eval survives (∀ r : Ratio, (r.k.toFloat / r.n.toFloat == 1) = (r.k == r.n)) 139

/- Control, the same law in binary32. -/
#eval refuted (∀ r : Ratio, (r.k.toFloat32 / r.n.toFloat32 == 1) = (r.k == r.n)) 140

end Attack

end Palace.Binary64
