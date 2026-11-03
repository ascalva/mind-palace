module

public import Palace.Cut.Defs
public import Palace.Laplacian

/-!
# Conductance: CUT-1

`Φ(S) = w(∂S) / min(vol S, vol S̄)` with the conventions of `core/complex/cut.py`, `conductance`
(dn-mathematical-foundations §2.2, seed table III): `0` when `S` is empty or everything, and `0`
when either side has zero volume.
-/

@[expose] public section

open Matrix Finset

namespace Palace

variable {V R : Type*} [Fintype V] [DecidableEq V]

section Bounds

variable [Field R] [LinearOrder R] [IsStrictOrderedRing R]

/-- The boundary is part of the volume of `S`. -/
theorem boundary_le_vol (A : Matrix V V R) (hw : ∀ i j, 0 ≤ A i j) (S : Finset V) :
    boundary A S ≤ vol A S :=
  sum_le_sum fun i _ ↦ sum_le_sum_of_subset_of_nonneg (subset_univ _) fun j _ _ ↦ hw i j

/-- For symmetric `A`, the boundary is also part of the volume of the rest. -/
theorem boundary_le_vol_compl (A : Matrix V V R) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (S : Finset V) : boundary A S ≤ vol A Sᶜ := by
  rw [boundary, sum_comm (f := fun i j ↦ A i j)]
  refine sum_le_sum fun j _ ↦ ?_
  have hs (i : V) : A i j = A j i := (hA.apply i j).symm
  simp only [hs]
  exact sum_le_sum_of_subset_of_nonneg (subset_univ _) fun i _ _ ↦ hw j i

theorem boundary_nonneg (A : Matrix V V R) (hw : ∀ i j, 0 ≤ A i j) (S : Finset V) :
    0 ≤ boundary A S :=
  sum_nonneg fun i _ ↦ sum_nonneg fun j _ ↦ hw i j

omit [DecidableEq V] in
theorem vol_nonneg (A : Matrix V V R) (hw : ∀ i j, 0 ≤ A i j) (S : Finset V) : 0 ≤ vol A S :=
  sum_nonneg fun i _ ↦ sum_nonneg fun j _ ↦ hw i j

/-- **CUT-1** `Φ(S) ∈ [0, 1]` for symmetric `A` with nonnegative entries, degenerate `S`
included. -/
theorem conductance_mem_Icc (A : Matrix V V R) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (S : Finset V) : conductance A S ∈ Set.Icc 0 1 := by
  unfold conductance
  split_ifs with h1 h2
  · exact ⟨le_rfl, zero_le_one⟩
  · exact ⟨le_rfl, zero_le_one⟩
  · simp only [not_or] at h2
    have hs := lt_of_le_of_ne (vol_nonneg A hw S) (Ne.symm h2.1)
    have hc := lt_of_le_of_ne (vol_nonneg A hw Sᶜ) (Ne.symm h2.2)
    have hm : 0 < min (vol A S) (vol A Sᶜ) := lt_min hs hc
    refine ⟨div_nonneg (boundary_nonneg A hw S) hm.le, (div_le_one hm).2 ?_⟩
    exact le_min (boundary_le_vol A hw S) (boundary_le_vol_compl A hA hw S)

/-- **CUT-1** `Φ(S) = 0` iff no weight crosses from `S` to the rest (the docstring's "0 ⇔ S is
disconnected from the rest"), under the code's conventions. -/
theorem conductance_eq_zero_iff (A : Matrix V V R) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (S : Finset V) : conductance A S = 0 ↔ boundary A S = 0 := by
  have hb := boundary_nonneg A hw S
  unfold conductance
  split_ifs with h1 h2
  · rcases h1 with rfl | rfl <;> simp [boundary]
  · refine ⟨fun _ ↦ ?_, fun _ ↦ rfl⟩
    rcases h2 with h | h
    · exact le_antisymm (h ▸ boundary_le_vol A hw S) hb
    · exact le_antisymm (h ▸ boundary_le_vol_compl A hA hw S) hb
  · simp only [not_or] at h2
    have hm : min (vol A S) (vol A Sᶜ) ≠ 0 :=
      (lt_min (lt_of_le_of_ne (vol_nonneg A hw S) (Ne.symm h2.1))
        (lt_of_le_of_ne (vol_nonneg A hw Sᶜ) (Ne.symm h2.2))).ne'
    exact div_eq_zero_iff.trans (or_iff_left hm)

end Bounds

end Palace
