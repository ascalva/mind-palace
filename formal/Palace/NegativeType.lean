module

public import Mathlib.Topology.Algebra.Monoid
public import Mathlib.Topology.Instances.Real.Lemmas
public import Mathlib.Topology.Order.OrderClosed
public import Mathlib.Order.Filter.AtTopBot.Basic
public import Mathlib.Algebra.BigOperators.Fin

/-!
# Negative type, and §2.6's β*

`docs/design-notes/temporal-retrieval-algebra.md` §2.6 (A8) defines `β* = sup{β : d_β is of
negative type}` for the free-energy distances `d_β` and claims: β* is finite iff the
shortest-path metric `d_∞` is not of negative type, which holds whenever the graph has an
isometric cycle `C_{≥4}`. This file proves what of that holds, before any code computes β*:

* the direction the note's argument proves: when `d_β → d_∞` and `d_∞` is not of negative type,
  `d_β` is not of negative type for every large β, so `{β : d_β of negative type}` is bounded above
  (negative type is a closed condition);
* nonnegative combinations of cut metrics are of negative type, and the shortest-path metrics of the
  cycles `C₄` to `C₈` are such combinations, so they are of negative type: an isometric cycle does
  not break negative type, and the note's criterion is wrong;
* `K₂,₃`'s shortest-path metric is not of negative type.

The converse direction is not proved by the note's argument; `docs/design-notes` records it as open
(the measured free-energy family keeps negative type on the even cycles, whose shortest-path metric
sits on the boundary).
-/

@[expose] public section

open Finset Filter Topology

namespace Palace.NegativeType

variable {V : Type*} [Fintype V]

/-- Negative type: `Σ_ij x_i x_j d_ij ≤ 0` whenever `Σ_i x_i = 0` (Schoenberg: then `e^{−s d}` is
positive semidefinite for every `s > 0`). -/
def NegType (d : V → V → ℝ) : Prop :=
  ∀ x : V → ℝ, ∑ i, x i = 0 → ∑ i, ∑ j, x i * x j * d i j ≤ 0

/-- The quadratic form a vector reads off a distance. -/
def form (x : V → ℝ) (d : V → V → ℝ) : ℝ := ∑ i, ∑ j, x i * x j * d i j

theorem continuous_form (x : V → ℝ) : Continuous (form x) := by
  unfold form
  fun_prop

/-- §2.6, the direction the note proves: if `d_β → d_∞` entrywise and `d_∞` is not of negative
type, then `d_β` is not of negative type for every large β. -/
theorem eventually_not_negType {d : ℝ → V → V → ℝ} {dinf : V → V → ℝ}
    (hlim : ∀ i j, Tendsto (fun β ↦ d β i j) atTop (𝓝 (dinf i j))) (hnot : ¬NegType dinf) :
    ∀ᶠ β in atTop, ¬NegType (d β) := by
  simp only [NegType, not_forall, not_le, exists_prop] at hnot
  obtain ⟨x, hx, hpos⟩ := hnot
  have hd : Tendsto d atTop (𝓝 dinf) := tendsto_pi_nhds.mpr fun i ↦ tendsto_pi_nhds.mpr (hlim i)
  have hf : Tendsto (fun β ↦ form x (d β)) atTop (𝓝 (form x dinf)) :=
    ((continuous_form x).tendsto dinf).comp hd
  filter_upwards [hf.eventually_const_lt hpos] with β hβ hneg
  exact absurd (hneg x hx) (not_le.mpr hβ)

/-- §2.6: so `β* = sup{β : d_β is of negative type}` is finite: the set is bounded above. -/
theorem bddAbove_negType {d : ℝ → V → V → ℝ} {dinf : V → V → ℝ}
    (hlim : ∀ i j, Tendsto (fun β ↦ d β i j) atTop (𝓝 (dinf i j))) (hnot : ¬NegType dinf) :
    BddAbove {β | NegType (d β)} := by
  obtain ⟨B, hB⟩ := eventually_atTop.mp (eventually_not_negType hlim hnot)
  refine ⟨B, fun β hβ ↦ ?_⟩
  by_contra hlt
  exact hB β (le_of_lt (not_le.mp hlt)) hβ

/-- A squared line metric `(f_i − f_j)²` is of negative type: its form is `−2 (Σ x_i f_i)²`. -/
theorem negType_sq_sub (f : V → ℝ) : NegType fun i j ↦ (f i - f j) ^ 2 := by
  intro x hx
  have e : ∑ i, ∑ j, x i * x j * (f i - f j) ^ 2 =
      (∑ i, x i * f i ^ 2) * (∑ j, x j) + (∑ i, x i) * (∑ j, x j * f j ^ 2) -
        2 * ((∑ i, x i * f i) * (∑ j, x j * f j)) := by
    simp only [sum_mul, mul_sum, ← sum_add_distrib, ← sum_sub_distrib]
    exact sum_congr rfl fun i _ ↦ sum_congr rfl fun j _ ↦ by ring
  rw [e, hx, mul_zero, zero_mul, zero_add, zero_sub]
  nlinarith [mul_self_nonneg (∑ i, x i * f i)]

/-- Negative type is closed under nonnegative combinations: the distances of negative type form a
convex cone. -/
theorem NegType.add {d e : V → V → ℝ} (hd : NegType d) (he : NegType e) :
    NegType fun i j ↦ d i j + e i j := by
  intro x hx
  have h := add_nonpos (hd x hx) (he x hx)
  simp only [mul_add, sum_add_distrib]
  linarith

theorem NegType.smul {d : V → V → ℝ} (hd : NegType d) {c : ℝ} (hc : 0 ≤ c) :
    NegType fun i j ↦ c * d i j := by
  intro x hx
  have e : ∑ i, ∑ j, x i * x j * (c * d i j) = c * ∑ i, ∑ j, x i * x j * d i j := by
    rw [mul_sum]
    exact sum_congr rfl fun i _ ↦ by
      rw [mul_sum]
      exact sum_congr rfl fun j _ ↦ by ring
  rw [e]
  nlinarith [hd x hx]

theorem negType_zero : NegType (fun _ _ ↦ (0 : ℝ) : V → V → ℝ) := by
  intro x _
  simp

/-- A finite sum of distances of negative type is of negative type. -/
theorem negType_sum {ι : Type*} (s : Finset ι) {d : ι → V → V → ℝ}
    (h : ∀ k ∈ s, NegType (d k)) : NegType fun i j ↦ ∑ k ∈ s, d k i j := by
  classical
  induction s using Finset.induction_on with
  | empty => simpa using (negType_zero (V := V))
  | insert a s ha ih =>
    simp only [sum_insert ha]
    exact (h a (mem_insert_self a s)).add (ih fun k hk ↦ h k (mem_insert_of_mem hk))

/-- A cut metric, `1` across the cut and `0` within either side, is of negative type: it is the
squared line metric of the cut's indicator. -/
theorem negType_cut (S : V → Prop) [DecidablePred S] :
    NegType fun i j ↦ if (S i ↔ S j) then (0 : ℝ) else 1 := by
  have h := negType_sq_sub fun i ↦ if S i then (1 : ℝ) else 0
  intro x hx
  convert h x hx using 4 with i _ j _
  by_cases hi : S i <;> by_cases hj : S j <;> simp [hi, hj]

/-! ### Cycles and `K₂,₃` -/

/-- The shortest-path metric of the cycle `C_n` on `Fin n`: the shorter way round. -/
def cycDist (n : ℕ) (i j : Fin n) : ℕ := min ((j.val + n - i.val) % n) ((i.val + n - j.val) % n)

/-- The number of cuts among the `cnt` cyclic intervals of length `len` starting at `0, 1, …`
that separate `i` and `j`. -/
def cutCount (n len cnt : ℕ) (i j : Fin n) : ℕ :=
  ∑ k ∈ range cnt, if ((i.val + n - k) % n < len ↔ (j.val + n - k) % n < len) then 0 else 1

/-- A cycle's metric is of negative type once `c` times it is a count of separating cuts. -/
theorem negType_cycDist {n len cnt c : ℕ} (hc : 0 < c)
    (h : ∀ i j : Fin n, c * cycDist n i j = cutCount n len cnt i j) :
    NegType fun i j : Fin n ↦ (cycDist n i j : ℝ) := by
  have hcuts : NegType fun i j : Fin n ↦ ∑ k ∈ range cnt,
      (if ((i.val + n - k) % n < len ↔ (j.val + n - k) % n < len) then (0 : ℝ) else 1) :=
    negType_sum _ fun k _ ↦ negType_cut fun i : Fin n ↦ (i.val + n - k) % n < len
  have hs := hcuts.smul (c := (c : ℝ)⁻¹) (by positivity)
  intro x hx
  convert hs x hx using 4 with i _ j _
  have e : (c : ℝ) * cycDist n i j = cutCount n len cnt i j := by exact_mod_cast h i j
  rw [cutCount] at e
  push_cast at e
  beta_reduce
  rw [← e]
  field_simp

/-- **§2.6 corrected** `C₄`'s shortest-path metric is of negative type, though `C₄` is an isometric
cycle of length 4: two cuts. -/
theorem negType_cycle4 : NegType fun i j : Fin 4 ↦ (cycDist 4 i j : ℝ) :=
  negType_cycDist (len := 2) (cnt := 2) one_pos (by decide)

/-- `C₅`: twice the metric is the five intervals of length 2. -/
theorem negType_cycle5 : NegType fun i j : Fin 5 ↦ (cycDist 5 i j : ℝ) :=
  negType_cycDist (len := 2) (cnt := 5) two_pos (by decide)

/-- `C₆`: three cuts. -/
theorem negType_cycle6 : NegType fun i j : Fin 6 ↦ (cycDist 6 i j : ℝ) :=
  negType_cycDist (len := 3) (cnt := 3) one_pos (by decide)

/-- `C₇`: twice the metric is the seven intervals of length 3. -/
theorem negType_cycle7 : NegType fun i j : Fin 7 ↦ (cycDist 7 i j : ℝ) :=
  negType_cycDist (len := 3) (cnt := 7) two_pos (by decide)

/-- `C₈`: four cuts. -/
theorem negType_cycle8 : NegType fun i j : Fin 8 ↦ (cycDist 8 i j : ℝ) :=
  negType_cycDist (len := 4) (cnt := 4) one_pos (by decide)

/-- The shortest-path metric of `K₂,₃` on `Fin 5`, parts `{0, 1}` and `{2, 3, 4}`: `1` across,
`2` within a part. -/
def k23Dist (i j : Fin 5) : ℕ := if i = j then 0 else if (i.val < 2 ↔ j.val < 2) then 2 else 1

/-- **§2.6** `K₂,₃`'s shortest-path metric is not of negative type: `x = (3, 3, −2, −2, −2)` sums
to zero and has form `12`. -/
theorem not_negType_k23 : ¬NegType fun i j : Fin 5 ↦ (k23Dist i j : ℝ) := by
  intro h
  have := h ![3, 3, -2, -2, -2] (by simp [Fin.sum_univ_five]; norm_num)
  simp [Fin.sum_univ_five, k23Dist] at this
  norm_num at this

end Palace.NegativeType
