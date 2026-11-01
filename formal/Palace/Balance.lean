import Palace.Spectral

/-!
# Signed balance: LAP-5 and LAP-6

Statements of the ledger's balance laws (dn-mathematical-foundations §2.2, seed table II),
mirroring `core/kernel/complex/balance.py`. A signed graph is balanced when its vertices split into
two camps, every positive edge inside a camp and every negative edge across.
-/

open Matrix Finset

namespace Palace

variable {V R : Type*} [Fintype V] [DecidableEq V]

/-- Balanced: a camp `sᵢ = ±1` for every vertex with `Aᵢⱼ sᵢ sⱼ ≥ 0` for every pair. -/
def Balanced [Ring R] [LinearOrder R] (A : Matrix V V R) : Prop :=
  ∃ s : V → R, (∀ i, s i = 1 ∨ s i = -1) ∧ ∀ i j, 0 ≤ A i j * s i * s j

/-- A camp read off a Boolean: `true` is the camp `1`, `false` the camp `−1`. -/
def camp [Ring R] (b : Bool) : R := if b then 1 else -1

/-- `Balanced` with the camps as Booleans, which makes it decidable on a finite vertex set. -/
def BalancedB [Ring R] [LinearOrder R] (A : Matrix V V R) : Prop :=
  ∃ b : V → Bool, ∀ i j, 0 ≤ A i j * camp (b i) * camp (b j)

omit [Fintype V] [DecidableEq V] in
/-- The Boolean form is the same predicate. -/
theorem balanced_iff_balancedB [Ring R] [LinearOrder R] [IsStrictOrderedRing R]
    (A : Matrix V V R) : Balanced A ↔ BalancedB A := by
  constructor
  · rintro ⟨s, hs, h⟩
    have e (k : V) : camp (decide (s k = 1)) = s k := by
      rcases hs k with hk | hk <;> simp [camp, hk]
      norm_num
    exact ⟨fun k ↦ decide (s k = 1), fun i j ↦ by rw [e, e]; exact h i j⟩
  · rintro ⟨b, h⟩
    refine ⟨fun k ↦ camp (b k), fun k ↦ ?_, h⟩
    beta_reduce
    cases b k <;> simp [camp]

/-! ### LAP-6: a triangle is frustrated iff it carries an odd number of negative edges -/

/-- The triangle with weights `a` on `0–1`, `b` on `1–2` and `c` on `0–2`. -/
def triangle [Ring R] (a b c : R) : Matrix (Fin 3) (Fin 3) R := !![0, a, c; a, 0, b; c, b, 0]

/-- A two-colouring of the triangle from the camps of vertices 1 and 2 (vertex 0 in camp `1`). -/
private theorem balanced_triangle_of [Field R] [LinearOrder R] [IsStrictOrderedRing R]
    {a b c s₁ s₂ : R} (h₁ : s₁ = 1 ∨ s₁ = -1) (h₂ : s₂ = 1 ∨ s₂ = -1) (h01 : 0 ≤ a * s₁)
    (h12 : 0 ≤ b * s₁ * s₂) (h02 : 0 ≤ c * s₂) : Balanced (triangle a b c) := by
  refine ⟨![1, s₁, s₂], fun i ↦ ?_, fun i j ↦ ?_⟩
  · fin_cases i
    · exact Or.inl rfl
    · exact h₁
    · exact h₂
  · fin_cases i <;> fin_cases j <;> simp [triangle] <;> nlinarith

/-- **LAP-6** A triangle with nonzero weights is frustrated (not balanced) iff the product of its
signs is negative, which is the test `frustrated_triangles` runs. -/
theorem not_balanced_triangle_iff [Field R] [LinearOrder R] [IsStrictOrderedRing R] {a b c : R}
    (ha : a ≠ 0) (hb : b ≠ 0) (hc : c ≠ 0) : ¬ Balanced (triangle a b c) ↔ a * b * c < 0 := by
  constructor
  · intro h
    by_contra hpos
    have hpos : 0 < a * b * c := lt_of_le_of_ne (not_lt.1 hpos)
      (Ne.symm (mul_ne_zero (mul_ne_zero ha hb) hc))
    apply h
    rcases ha.lt_or_gt with ha' | ha' <;> rcases hc.lt_or_gt with hc' | hc'
    · have : 0 < b := by nlinarith [mul_pos_of_neg_of_neg ha' hc']
      exact balanced_triangle_of (Or.inr rfl) (Or.inr rfl) (by nlinarith) (by nlinarith)
        (by nlinarith)
    · have : b < 0 := by nlinarith [mul_neg_of_neg_of_pos ha' hc']
      exact balanced_triangle_of (Or.inr rfl) (Or.inl rfl) (by nlinarith) (by nlinarith)
        (by nlinarith)
    · have : b < 0 := by nlinarith [mul_neg_of_pos_of_neg ha' hc']
      exact balanced_triangle_of (Or.inl rfl) (Or.inr rfl) (by nlinarith) (by nlinarith)
        (by nlinarith)
    · have : 0 < b := by nlinarith [mul_pos ha' hc']
      exact balanced_triangle_of (Or.inl rfl) (Or.inl rfl) (by nlinarith) (by nlinarith)
        (by nlinarith)
  · rintro hneg ⟨s, hs, h⟩
    have h01 := h 0 1
    have h12 := h 1 2
    have h02 := h 0 2
    simp only [triangle, of_apply, cons_val', cons_val_zero, cons_val_one, cons_val_two,
      empty_val', cons_val_fin_one] at h01 h12 h02
    have hs0 : s 0 ^ 2 = 1 := by rcases hs 0 with h | h <;> rw [h] <;> norm_num
    have hs1 : s 1 ^ 2 = 1 := by rcases hs 1 with h | h <;> rw [h] <;> norm_num
    have hs2 : s 2 ^ 2 = 1 := by rcases hs 2 with h | h <;> rw [h] <;> norm_num
    have hprod : (a * s 0 * s 1) * (b * s 1 * s 2) * (c * s 0 * s 2) = a * b * c := by
      have : (a * s 0 * s 1) * (b * s 1 * s 2) * (c * s 0 * s 2) =
          a * b * c * (s 0 ^ 2 * s 1 ^ 2 * s 2 ^ 2) := by ring
      rw [this, hs0, hs1, hs2]; ring
    have : 0 ≤ (a * s 0 * s 1) * (b * s 1 * s 2) * (c * s 0 * s 2) :=
      mul_nonneg (mul_nonneg h01 h12) h02
    linarith

/-- **LAP-6** In the ledger's words: frustrated iff the count of negative edges is odd. -/
theorem not_balanced_triangle_iff_odd [Field R] [LinearOrder R] [IsStrictOrderedRing R]
    {a b c : R} (ha : a ≠ 0) (hb : b ≠ 0) (hc : c ≠ 0) :
    ¬ Balanced (triangle a b c) ↔
      Odd ((if a < 0 then 1 else 0) + (if b < 0 then 1 else 0) + (if c < 0 then 1 else 0) : ℕ) := by
  rw [not_balanced_triangle_iff ha hb hc]
  rcases ha.lt_or_gt with ha | ha <;> rcases hb.lt_or_gt with hb | hb <;>
    rcases hc.lt_or_gt with hc | hc <;>
    simp (config := { decide := true }) only [ha, hb, hc, not_lt.2 ha.le, not_lt.2 hb.le,
      not_lt.2 hc.le, ↓reduceIte, Nat.reduceAdd, add_zero, zero_add, iff_true, iff_false, not_lt,
      odd_one, Nat.not_odd_zero, mul_nonneg_iff_of_pos_left, mul_nonneg_iff_of_pos_right,
      mul_pos_iff_of_pos_left] <;>
    first
    | nlinarith [mul_pos ha hb]
    | nlinarith [mul_pos_of_neg_of_neg ha hb]
    | nlinarith [mul_neg_of_pos_of_neg ha hb]
    | nlinarith [mul_neg_of_neg_of_pos ha hb]

/-! ### LAP-5: `λ_min(L̄) = 0` iff balanced, on a connected support -/

omit [Fintype V] [DecidableEq V] in
/-- A function constant across every edge is constant across reachability. -/
theorem eq_of_reachable {G : SimpleGraph V} {α : Type*} {f : V → α}
    (h : ∀ i j, G.Adj i j → f i = f j) {i j : V} (hr : G.Reachable i j) : f i = f j := by
  obtain ⟨p⟩ := hr
  induction p with
  | nil => rfl
  | cons hadj _ ih => exact (h _ _ hadj).trans ih

/-- A zero term of the signed energy pins its two values: equal across a positive edge, opposite
across a negative one. -/
theorem signed_term_eq_zero [CommRing R] [LinearOrder R] [IsStrictOrderedRing R] {a x y : R}
    (h : |a| * (x ^ 2 + y ^ 2) - 2 * a * x * y = 0) : (0 < a → x = y) ∧ (a < 0 → x = -y) := by
  constructor
  · intro ha
    rw [abs_of_pos ha] at h
    have e : a * (x - y) ^ 2 = 0 := by rw [← h]; ring
    exact sub_eq_zero.1 (pow_eq_zero_iff two_ne_zero |>.1 ((mul_eq_zero.1 e).resolve_left ha.ne'))
  · intro ha
    rw [abs_of_neg ha] at h
    have e : -a * (x + y) ^ 2 = 0 := by rw [← h]; ring
    have := pow_eq_zero_iff two_ne_zero |>.1 ((mul_eq_zero.1 e).resolve_left (neg_ne_zero.2 ha.ne))
    exact eq_neg_of_add_eq_zero_left this

/-- **LAP-5** Hou and Kunegis, on a connected support: `L̄` has a nonzero vector of zero energy (so
its smallest eigenvalue is `0`, `L̄` being positive semidefinite) iff the signed graph is
balanced. -/
theorem zero_energy_iff_balanced (A : Matrix V V ℝ) (hA : A.IsSymm) (hc : (support A).Connected) :
    (∃ x ≠ 0, x ⬝ᵥ (signedLap A *ᵥ x) = 0) ↔ Balanced A := by
  constructor
  · rintro ⟨x, hx, he⟩
    have hterm (i j : V) : |A i j| * (x i ^ 2 + x j ^ 2) - 2 * A i j * x i * x j = 0 := by
      have e := two_mul_dotProduct_signedLap A hA x
      rw [he, mul_zero] at e
      have hi := (sum_eq_zero_iff_of_nonneg fun i _ ↦ sum_nonneg fun j _ ↦
        signed_term_nonneg _ _ _).1 e.symm i (mem_univ _)
      exact (sum_eq_zero_iff_of_nonneg fun j _ ↦ signed_term_nonneg _ _ _).1 hi j (mem_univ _)
    have habs (i j : V) (hij : (support A).Adj i j) : |x i| = |x j| := by
      have key (u v : V) (huv : A u v ≠ 0) : |x u| = |x v| := by
        have t := signed_term_eq_zero (hterm u v)
        rcases huv.lt_or_gt with h | h
        · rw [t.2 h, abs_neg]
        · rw [t.1 h]
      rcases hij with ⟨-, hij | hji⟩
      · exact key i j hij
      · exact (key j i hji).symm
    obtain ⟨k, hk⟩ := Function.ne_iff.1 hx
    have hall (i : V) : |x i| = |x k| := eq_of_reachable habs (hc.preconnected i k)
    have hne (i : V) : x i ≠ 0 := fun h0 ↦ hk (abs_eq_zero.1 ((hall i).symm.trans (by simp [h0])))
    have hprod (i j : V) : 0 ≤ A i j * x i * x j := by
      have h := hterm i j
      have : 0 ≤ |A i j| * (x i ^ 2 + x j ^ 2) := mul_nonneg (abs_nonneg _) (by positivity)
      linarith
    refine ⟨fun i ↦ x i / |x i|, fun i ↦ ?_, fun i j ↦ ?_⟩
    · beta_reduce
      rcases (hne i).lt_or_gt with h | h
      · right; rw [abs_of_neg h, div_neg, div_self h.ne]
      · left; rw [abs_of_pos h, div_self h.ne']
    · beta_reduce
      have hd : 0 < |x i| * |x j| := mul_pos (abs_pos.2 (hne i)) (abs_pos.2 (hne j))
      have : A i j * (x i / |x i|) * (x j / |x j|) = A i j * x i * x j / (|x i| * |x j|) := by
        field_simp
      rw [this]
      exact div_nonneg (hprod i j) hd.le
  · rintro ⟨s, hs, hbal⟩
    obtain ⟨i₀⟩ := hc.nonempty
    refine ⟨s, fun h ↦ ?_, ?_⟩
    · have h0 := congrFun h i₀
      rcases hs i₀ with h1 | h1 <;> rw [h1] at h0 <;> norm_num at h0
    · have hsq (i : V) : s i ^ 2 = 1 := by rcases hs i with h | h <;> rw [h] <;> norm_num
      have habs (i : V) : |s i| = 1 := by rcases hs i with h | h <;> rw [h] <;> norm_num
      have hzero (i j : V) :
          |A i j| * (s i ^ 2 + s j ^ 2) - 2 * A i j * s i * s j = 0 := by
        have e : A i j * s i * s j = |A i j| := by
          rw [← abs_of_nonneg (hbal i j), abs_mul, abs_mul, habs, habs, mul_one, mul_one]
        rw [hsq, hsq, show 2 * A i j * s i * s j = 2 * (A i j * s i * s j) by ring, e]
        ring
      have e := two_mul_dotProduct_signedLap A hA s
      simp only [hzero, sum_const_zero] at e
      linarith

/-- LAP-5 needs a connected support, which is why `signed_spectrum` takes the max over components
of size at least 2: beside an isolated vertex, a frustrated triangle still has a zero-energy vector
(the isolated vertex's indicator) without being balanced. -/
theorem zero_energy_not_balanced :
    ∃ A : Matrix (Fin 4) (Fin 4) ℝ, A.IsSymm ∧ (∃ x ≠ 0, x ⬝ᵥ (signedLap A *ᵥ x) = 0) ∧
      ¬ Balanced A := by
  refine ⟨!![0, 1, -1, 0; 1, 0, 1, 0; -1, 1, 0, 0; 0, 0, 0, 0], ?_, ⟨![0, 0, 0, 1], ?_, ?_⟩, ?_⟩
  · ext i j; fin_cases i <;> fin_cases j <;> rfl
  · intro h; have := congrFun h 3; norm_num at this
  · simp [signedLap, dotProduct, mulVec, Fin.sum_univ_four, diagonal]
  · rintro ⟨s, hs, h⟩
    have h01 := h 0 1
    have h12 := h 1 2
    have h02 := h 0 2
    simp only [of_apply, cons_val', cons_val_zero, cons_val_one, cons_val_two, empty_val',
      cons_val_fin_one] at h01 h12 h02
    have hs0 : s 0 ^ 2 = 1 := by rcases hs 0 with h | h <;> rw [h] <;> norm_num
    have hs1 : s 1 ^ 2 = 1 := by rcases hs 1 with h | h <;> rw [h] <;> norm_num
    have hs2 : s 2 ^ 2 = 1 := by rcases hs 2 with h | h <;> rw [h] <;> norm_num
    have hprod : (1 * s 0 * s 1) * (1 * s 1 * s 2) * (-1 * s 0 * s 2) = -1 := by
      have : (1 * s 0 * s 1) * (1 * s 1 * s 2) * (-1 * s 0 * s 2) =
          -(s 0 ^ 2 * s 1 ^ 2 * s 2 ^ 2) := by ring
      rw [this, hs0, hs1, hs2]; norm_num
    have : 0 ≤ (1 * s 0 * s 1) * (1 * s 1 * s 2) * (-1 * s 0 * s 2) :=
      mul_nonneg (mul_nonneg h01 h12) h02
    linarith

/-! ## Attacks

On `Fin 5` over ℚ. `BalancedB` is decided by trying all 32 camp assignments, and it is the same
predicate as `Balanced` (`balanced_iff_balancedB`). `λ_min(L̄) = 0` is read as `L̄` singular
(`L̄` is positive semidefinite, so a zero-energy vector is a kernel vector), decided by the exact
Gauss–Jordan shadow of the `L⁺` attacks.
-/

namespace Attack

/- Decide `BalancedB` one quantifier at a time; instance search does not find the nesting. -/
instance {n : ℕ} (A : Matrix (Fin n) (Fin n) ℚ) : Decidable (BalancedB A) :=
  have (b : Fin n → Bool) (i : Fin n) :
      Decidable (∀ j, 0 ≤ A i j * camp (b i) * camp (b j)) := inferInstance
  have (b : Fin n → Bool) : Decidable (∀ i j, 0 ≤ A i j * camp (b i) * camp (b j)) :=
    Nat.decidableForallFin _
  Fintype.decidableExistsFintype

/-- `L̄` is singular. -/
def singular (A : Matrix (Fin 5) (Fin 5) ℚ) : Bool := (invR (rows (signedLap A))).isNone

/-- The support is connected. -/
def connected (A : Matrix (Fin 5) (Fin 5) ℚ) : Bool := ((reach A)[0]!).all id

/-- A balanced signed graph by construction: nonnegative weights, signed by camps. -/
def balancedOf (es : List (Fin 5 × Fin 5 × ℕ)) (bs : List Bool) : Matrix (Fin 5) (Fin 5) ℚ :=
  fun i j ↦ ofEdges (nonneg es) i j * camp (bs.getD i true) * camp (bs.getD j true)

/- LAP-6: a triangle with nonzero weights is balanced iff the product of its signs is positive
(stated positively; Plausible cannot test a negation inside an `↔`). -/
#eval survives (∀ a b c : ℤ, a ≠ 0 → b ≠ 0 → c ≠ 0 →
  (BalancedB (triangle (a : ℚ) b c) ↔ 0 < a * b * c)) 51

/- LAP-6 control: a balanced triangle has no negative edge (two negative edges are balanced). -/
#eval refuted (∀ a b c : ℤ, a ≠ 0 → b ≠ 0 → c ≠ 0 →
  BalancedB (triangle (a : ℚ) b c) → 0 < min a (min b c)) 52

/- LAP-5 on a connected support: `L̄` singular iff balanced. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℤ),
  connected (ofEdges es) = true → (singular (ofEdges es) = true ↔ BalancedB (ofEdges es))) 53

/- LAP-5 on graphs balanced by construction: connected ones are singular. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ bs : List Bool,
  connected (balancedOf es bs) = true → singular (balancedOf es bs) = true) 54

/- LAP-5 control, the global reading without connectivity (an isolated vertex or a balanced
component makes `L̄` singular while frustration sits elsewhere). -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ),
  (singular (ofEdges es) = true ↔ BalancedB (ofEdges es))) 55

end Attack

end Palace
