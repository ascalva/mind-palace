module

public import Palace.Derived.Defs

/-!
# Two-phase ingestion: the laws

dn-two-phase-ingestion, family XII continued, on the model of `Palace/Derived/Defs.lean`. ING-19:
a landing writes an item's structure and key and no atom and no mark; the drain changes neither
the keys nor the structures, so a structural query answers the same before and after it, and the
drain under one identity leaves every other identity's atoms and marks alone, so re-embedding
after a model change is the same drain under a new identity. ING-20: an item's derivation is
idempotent and commutes with another item's and with a later landing of another item; the drain is
idempotent; after the drain nothing keyed is pending and every keyed item's field is its
structure's image; from any interleaving of landings and embed steps, stopped anywhere, the drain's
field is the field the landings alone followed by the drain would give; the code's drain, over the
pending items alone, reaches the drain's field from any sound and truthful state; every prefix of
the key-last derivation keeps soundness, and every run keeps truthfulness; the mark-first order
breaks soundness and the code's drain never repairs it (the controls). ING-21: a structural query,
any function of the keyed items and their structures, is invariant under every run of embed steps;
a pending item's field is `none`; a field that reports a vector reports its own structure's image;
and reading a pending vector as zero gives an answer the embedding changes (the control). All
three are the ledger's (`Spec/Derived.lean`, judged by the comparator).
-/

@[expose] public section

open Finset

namespace Palace.Derived

variable {I S V E : Type*} [DecidableEq I] [DecidableEq S] [DecidableEq E]

/-! ### The steps, unfolded -/

theorem run_nil (f : E → S → V) (s : State I S V E) : run f [] s = s := rfl

theorem run_cons (f : E → S → V) (a : Step I S E) (w : List (Step I S E)) (s : State I S V E) :
    run f (a :: w) s = run f w (a.apply f s) := rfl

theorem run_append (f : E → S → V) (w₁ w₂ : List (Step I S E)) (s : State I S V E) :
    run f (w₁ ++ w₂) s = run f w₂ (run f w₁ s) := by
  unfold run; rw [List.foldl_append]

theorem writeAtom_keyed (f : E → S → V) (e : E) (i : I) (s : State I S V E) :
    (writeAtom f e i s).keyed = s.keyed := by
  unfold writeAtom; split_ifs <;> rfl

theorem writeAtom_struct (f : E → S → V) (e : E) (i : I) (s : State I S V E) :
    (writeAtom f e i s).struct = s.struct := by
  unfold writeAtom; split_ifs <;> rfl

omit [DecidableEq S] in
theorem writeMark_keyed (e : E) (i : I) (s : State I S V E) :
    (writeMark (V := V) e i s).keyed = s.keyed := by
  unfold writeMark; split_ifs <;> rfl

omit [DecidableEq S] in
theorem writeMark_struct (e : E) (i : I) (s : State I S V E) :
    (writeMark (V := V) e i s).struct = s.struct := by
  unfold writeMark; split_ifs <;> rfl

/-- Two states agree on what the landing writes: the keys and the structures. -/
def Agree (s t : State I S V E) : Prop := s.keyed = t.keyed ∧ s.struct = t.struct

omit [DecidableEq I] [DecidableEq S] [DecidableEq E] in
theorem Agree.refl (s : State I S V E) : Agree s s := ⟨rfl, rfl⟩

omit [DecidableEq I] [DecidableEq S] [DecidableEq E] in
theorem Agree.trans {s t u : State I S V E} (h₁ : Agree s t) (h₂ : Agree t u) : Agree s u :=
  ⟨h₁.1.trans h₂.1, h₁.2.trans h₂.2⟩

/-- Every step's effect on the keys and the structures is a function of the keys and the
structures: a landing writes them from themselves, an embed step leaves them. -/
theorem Agree.apply (f : E → S → V) (a : Step I S E) {s t : State I S V E} (h : Agree s t) :
    Agree (a.apply f s) (a.apply f t) := by
  obtain ⟨h1, h2⟩ := h
  cases a with
  | land i σ => exact ⟨by simp [Step.apply, land, h1], by simp [Step.apply, land, h2]⟩
  | atom e i =>
    exact ⟨(writeAtom_keyed f e i s).trans (h1.trans (writeAtom_keyed f e i t).symm),
           (writeAtom_struct f e i s).trans (h2.trans (writeAtom_struct f e i t).symm)⟩
  | mark e i =>
    exact ⟨(writeMark_keyed e i s).trans (h1.trans (writeMark_keyed e i t).symm),
           (writeMark_struct e i s).trans (h2.trans (writeMark_struct e i t).symm)⟩

theorem Agree.run (f : E → S → V) (w : List (Step I S E)) {s t : State I S V E}
    (h : Agree s t) : Agree (run f w s) (run f w t) := by
  induction w generalizing s t with
  | nil => exact h
  | cons a w ih => exact ih (h.apply f a)

/-- An embed step leaves the keys and the structures as they were. -/
theorem agree_apply_of_not_land (f : E → S → V) (a : Step I S E) (ha : a.isLand = false)
    (s : State I S V E) : Agree (a.apply f s) s := by
  cases a with
  | land _ _ => simp [Step.isLand] at ha
  | atom e i => exact ⟨writeAtom_keyed f e i s, writeAtom_struct f e i s⟩
  | mark e i => exact ⟨writeMark_keyed e i s, writeMark_struct e i s⟩

/-- A run of embed steps alone changes neither the keys nor the structures. -/
theorem agree_run_of_no_land (f : E → S → V) (w : List (Step I S E))
    (hw : ∀ a ∈ w, a.isLand = false) (s : State I S V E) : Agree (run f w s) s := by
  induction w generalizing s with
  | nil => exact Agree.refl s
  | cons a w ih =>
    rw [run_cons]
    exact (ih (fun b hb ↦ hw b (List.mem_cons_of_mem a hb)) _).trans
      (agree_apply_of_not_land f a (hw a List.mem_cons_self) s)

/-! ### ING-19 Completeness without the vector -/

omit [DecidableEq S] [DecidableEq E] in
/-- **ING-19** A landing writes no atom: the vector is not part of the item. -/
theorem land_atom (i : I) (σ : S) (s : State I S V E) : (land i σ s).atom = s.atom := rfl

omit [DecidableEq S] [DecidableEq E] in
/-- **ING-19** A landing moves no mark: the drain's key is the drain's alone. -/
theorem land_mark (i : I) (σ : S) (s : State I S V E) : (land i σ s).mark = s.mark := rfl

omit [DecidableEq S] [DecidableEq E] in
/-- **ING-19** A landed item is complete: its key is written, whatever its vector. -/
theorem complete_land (i : I) (σ : S) (s : State I S V E) : complete (land i σ s) i :=
  mem_insert_self i s.keyed

/-- **ING-19** The drain changes neither the keys nor the structures: a structural query, any
function of the keyed items and their structures, answers the same before and after it. -/
theorem structural_invariant_drain {α : Type*} (Q : Finset I → (I → Option S) → α)
    (f : E → S → V) (e : E) (s : State I S V E) :
    Q (drain f e s).keyed (drain f e s).struct = Q s.keyed s.struct := rfl

/-- **ING-19** The drain under one identity leaves another identity's atoms as they were:
re-embedding after a model change is the same drain under the new identity, and the old field is
neither read nor moved by it. -/
theorem drain_other_atom (f : E → S → V) {e e' : E} (h : e' ≠ e) (s : State I S V E) :
    (drain f e s).atom e' = s.atom e' := by
  funext τ
  simp [drain, h]

/-- **ING-19** The drain under one identity leaves another identity's marks as they were. -/
theorem drain_other_mark (f : E → S → V) {e e' : E} (h : e' ≠ e) (s : State I S V E) (j : I) :
    (drain f e s).mark j e' = s.mark j e' := by
  simp [drain, h]

/-! ### ING-20 The drain converges and is idempotent -/

/-- An item's derivation, written out: the atom of its structure under `e`, then its mark. -/
theorem run_derive (f : E → S → V) (e : E) (i : I) (s : State I S V E) (hi : i ∈ s.keyed) :
    run f (derive e i) s =
      ⟨s.keyed, s.struct,
       fun e' τ ↦ if e' = e ∧ s.struct i = some τ then some (f e τ) else s.atom e' τ,
       fun j e' ↦ if j = i ∧ e' = e then s.struct i else s.mark j e'⟩ := by
  simp [derive, run, Step.apply, writeAtom, writeMark, hi]

/-- A derivation of an item without a key does nothing: there is nothing to derive. -/
theorem run_derive_of_not_keyed (f : E → S → V) (e : E) (i : I) (s : State I S V E)
    (hi : i ∉ s.keyed) : run f (derive e i) s = s := by
  simp [derive, run, Step.apply, writeAtom, writeMark, hi]

theorem keyed_run_derive (f : E → S → V) (e : E) (i : I) (s : State I S V E) :
    (run f (derive e i) s).keyed = s.keyed :=
  (agree_run_of_no_land f (derive e i) (by simp [derive, Step.isLand]) s).1

/-- **ING-20** An item's derivation is idempotent: run twice, it leaves the state it left once. -/
theorem derive_idem (f : E → S → V) (e : E) (i : I) (s : State I S V E) :
    run f (derive e i) (run f (derive e i) s) = run f (derive e i) s := by
  by_cases hi : i ∈ s.keyed
  · have hi' : i ∈ (run f (derive e i) s).keyed := by rw [keyed_run_derive]; exact hi
    rw [run_derive f e i _ hi', run_derive f e i s hi]
    ext1
    · rfl
    · rfl
    · funext e' τ
      simp only
      split_ifs <;> rfl
    · funext j e'
      simp only
      split_ifs <;> rfl
  · rw [run_derive_of_not_keyed f e i s hi, run_derive_of_not_keyed f e i s hi]

/-- **ING-20** Two items' derivations commute. -/
theorem derive_comm (f : E → S → V) (e : E) (i j : I) (s : State I S V E) :
    run f (derive e i ++ derive e j) s = run f (derive e j ++ derive e i) s := by
  rw [run_append, run_append]
  by_cases hi : i ∈ s.keyed <;> by_cases hj : j ∈ s.keyed
  · have hj' : j ∈ (run f (derive e i) s).keyed := by rw [keyed_run_derive]; exact hj
    have hi' : i ∈ (run f (derive e j) s).keyed := by rw [keyed_run_derive]; exact hi
    rw [run_derive f e j _ hj', run_derive f e i _ hi', run_derive f e i s hi,
        run_derive f e j s hj]
    ext1
    · rfl
    · rfl
    · funext e' τ
      simp only
      by_cases h1 : e' = e ∧ s.struct j = some τ <;> by_cases h2 : e' = e ∧ s.struct i = some τ
        <;> simp [h1, h2]
    · funext k e'
      simp only
      by_cases hk : k = i <;> by_cases hk' : k = j <;> simp_all
  · have hj' : j ∉ (run f (derive e i) s).keyed := by rw [keyed_run_derive]; exact hj
    rw [run_derive_of_not_keyed f e j _ hj', run_derive_of_not_keyed f e j s hj]
  · have hi' : i ∉ (run f (derive e j) s).keyed := by rw [keyed_run_derive]; exact hi
    rw [run_derive_of_not_keyed f e i _ hi', run_derive_of_not_keyed f e i s hi]
  · rw [run_derive_of_not_keyed f e i s hi, run_derive_of_not_keyed f e j s hj,
        run_derive_of_not_keyed f e i s hi]

/-- **ING-20** An item's derivation commutes with a later landing of another item: the drain and
the writer interleave freely on distinct items. -/
theorem derive_land_comm (f : E → S → V) (e : E) {i j : I} (hij : i ≠ j) (σ : S)
    (s : State I S V E) :
    run f (derive e i ++ [.land j σ]) s = run f ([.land j σ] ++ derive e i) s := by
  rw [run_append, run_append]
  have hland : run f [Step.land j σ] s = land j σ s := rfl
  have hstruct : (land j σ s).struct i = s.struct i := by
    change Function.update s.struct j (some σ) i = s.struct i
    exact Function.update_of_ne hij _ _
  by_cases hi : i ∈ s.keyed
  · have hi' : i ∈ (land j σ s).keyed := mem_insert_of_mem hi
    rw [hland, run_derive f e i _ hi', run_derive f e i s hi]
    ext1
    · rfl
    · rfl
    · funext e' τ
      simp only [hstruct]
      rfl
    · funext k e'
      simp only [hstruct]
      rfl
  · have hi' : i ∉ (land j σ s).keyed := by
      rw [land, mem_insert]; exact fun h ↦ h.elim (fun h ↦ hij h) hi
    rw [run_derive_of_not_keyed f e i s hi, hland, run_derive_of_not_keyed f e i _ hi']

/-- **ING-20** The drain is idempotent. -/
theorem drain_idem (f : E → S → V) (e : E) (s : State I S V E) :
    drain f e (drain f e s) = drain f e s := by
  ext1
  · rfl
  · rfl
  · funext e' τ
    simp only [drain]
    split_ifs <;> rfl
  · funext j e'
    simp only [drain]
    split_ifs <;> rfl

/-- **ING-20** After the drain, nothing keyed is pending. -/
theorem not_pending_drain (f : E → S → V) (e : E) (s : State I S V E) (i : I) :
    ¬ pending (drain f e s) e i := by
  intro ⟨hi, hne⟩
  have hi' : i ∈ s.keyed := hi
  exact hne (by simp [drain, hi'])

/-- **ING-20** After the drain, every keyed item's field is its structure's image under the
embedder, and an unkeyed item's is `none`. -/
theorem field_drain (f : E → S → V) (e : E) (s : State I S V E) (i : I) :
    field (drain f e s) e i = if i ∈ s.keyed then (s.struct i).map (f e) else none := by
  unfold field
  by_cases hi : i ∈ s.keyed
  · simp only [drain, hi, true_and, ite_true]
    cases hσ : s.struct i with
    | none => simp
    | some σ =>
      have hex : ∃ j ∈ s.keyed, s.struct j = some σ := ⟨i, hi, hσ⟩
      simp [hex]
  · simp [drain, hi]

/-- **ING-20** From any interleaving of landings and embed steps, stopped anywhere, the drain's
field is the field the landings alone, followed by the drain, would give: landing and embedding
converge to one store in any order. -/
theorem field_drain_run (f : E → S → V) (e : E) (w : List (Step I S E)) (s : State I S V E) :
    field (drain f e (run f w s)) e = field (drain f e (run f (w.filter Step.isLand) s)) e := by
  funext i
  rw [field_drain, field_drain]
  suffices h : Agree (run f w s) (run f (w.filter Step.isLand) s) by rw [h.1, h.2]
  induction w generalizing s with
  | nil => exact Agree.refl s
  | cons a w ih =>
    cases ha : a.isLand with
    | true =>
      rw [List.filter_cons_of_pos ha, run_cons, run_cons]
      exact ih _
    | false =>
      rw [List.filter_cons_of_neg (by simp [ha]), run_cons]
      exact (ih _).trans (Agree.run f _ (agree_apply_of_not_land f a ha s))

/-- **ING-20** Every run keeps the atom table truthful: an atom is written as the embedder's
vector of its structure, and nothing else writes one. -/
theorem truthful_run (f : E → S → V) (w : List (Step I S E)) {s : State I S V E}
    (ht : Truthful f s) : Truthful f (run f w s) := by
  induction w generalizing s with
  | nil => exact ht
  | cons a w ih =>
    rw [run_cons]
    refine ih ?_
    cases a with
    | land i σ => exact ht
    | atom e i =>
      intro e' τ v hv
      by_cases hi : i ∈ s.keyed
      · simp only [Step.apply, writeAtom, hi, ite_true] at hv
        split_ifs at hv with h
        · obtain ⟨rfl, -⟩ := h
          exact (Option.some_injective _ hv).symm
        · exact ht e' τ v hv
      · simp only [Step.apply, writeAtom, hi, ite_false] at hv
        exact ht e' τ v hv
    | mark e i =>
      intro e' τ v hv
      by_cases hi : i ∈ s.keyed
      · simp only [Step.apply, writeMark, hi, ite_true] at hv
        exact ht e' τ v hv
      · simp only [Step.apply, writeMark, hi, ite_false] at hv
        exact ht e' τ v hv

/-- **ING-20** Every prefix of the key-last derivation keeps soundness: the atom is written before
the mark, so a derived item always has the atom its mark promises. -/
theorem sound_derive_prefix (f : E → S → V) (e : E) (i : I) {s : State I S V E}
    (hs : Sound s e) (k : ℕ) : Sound (run f ((derive e i).take k) s) e := by
  by_cases hi : i ∈ s.keyed
  · rcases k with _ | _ | k
    · exact hs
    · -- the atom alone: marks unchanged, the atom table only grows
      have h1 : run f ((derive e i).take 1) s = writeAtom f e i s := rfl
      rw [h1]
      intro j hj hm τ hτ
      simp only [writeAtom, hi, ite_true] at hj hm hτ ⊢
      split_ifs with h
      · rfl
      · exact hs j hj hm τ hτ
    · -- the whole derivation: the derived item's atom is its structure's, the rest as before
      have h2 : run f ((derive e i).take (k + 2)) s = run f (derive e i) s := by
        simp [derive]
      rw [h2, run_derive f e i s hi]
      intro j hj hm τ hτ
      dsimp only at hj hm hτ ⊢
      split_ifs at hm with hji
      · obtain ⟨hji, -⟩ := hji
        subst hji
        rw [hτ]
        simp
      · split_ifs with h
        · rfl
        · exact hs j hj hm τ hτ
  · -- an item without a key: every prefix of its derivation does nothing
    have hid : run f ((derive e i).take k) s = s := by
      rcases k with _ | _ | k
      · rfl
      · simp [derive, run, Step.apply, writeAtom, hi]
      · simp [derive, run, Step.apply, writeAtom, writeMark, hi]
    rw [hid]
    exact hs

/-- **ING-20** The code's drain, over the pending items alone, reaches the drain's field from any
sound and truthful state: a derived item is not embedded again, and its atom is the one the drain
would have written. -/
theorem codeDrain_field (f : E → S → V) (e : E) {s : State I S V E} (hs : Sound s e)
    (ht : Truthful f s) : field (codeDrain f e s) e = field (drain f e s) e := by
  funext i
  rw [field_drain]
  by_cases hi : i ∈ s.keyed
  · rw [ite_eq_left hi]
    have hcond : (codeDrain f e s).mark i e = (codeDrain f e s).struct i := by
      by_cases hp : s.mark i e = s.struct i <;> simp [codeDrain, hi, hp]
    cases hσ : s.struct i with
    | none =>
      unfold field
      rw [ite_eq_left ⟨hi, hcond⟩]
      change (s.struct i).bind _ = _
      rw [hσ]
      rfl
    | some σ =>
      have hatom : (codeDrain f e s).atom e σ = some (f e σ) := by
        by_cases hex : ∃ j ∈ s.keyed, s.mark j e ≠ s.struct j ∧ s.struct j = some σ
        · simp [codeDrain, hex]
        · have hnp : s.mark i e = s.struct i := by
            by_contra hp
            exact hex ⟨i, hi, hp, hσ⟩
          have hsome := hs i hi hnp σ hσ
          obtain ⟨v, hv⟩ := Option.isSome_iff_exists.1 hsome
          simp [codeDrain, hex, hv, ht e σ v hv]
      unfold field
      rw [ite_eq_left ⟨hi, hcond⟩]
      change (s.struct i).bind _ = _
      rw [hσ, Option.bind_some, Option.map_some, hatom]
  · simp [field, codeDrain, hi]

/-- The mark-first order, interrupted after the mark: the marks move, nothing else. -/
theorem run_markFirst (f : E → S → V) (e : E) (i : I) (s : State I S V E) (hi : i ∈ s.keyed) :
    run f ((deriveKeyFirst e i).take 1) s =
      ⟨s.keyed, s.struct, s.atom,
       fun j e' ↦ if j = i ∧ e' = e then s.struct i else s.mark j e'⟩ := by
  simp [deriveKeyFirst, run, Step.apply, writeMark, hi]

/-- **ING-20** The control: with the mark written first and the run interrupted after it, the
state is unsound, since the mark promises an atom the table lacks. -/
theorem mark_first_unsound (f : E → S → V) (e : E) (i : I) {s : State I S V E} {σ : S}
    (hi : i ∈ s.keyed) (hσ : s.struct i = some σ) (h0 : s.atom e σ = none) :
    ¬ Sound (run f ((deriveKeyFirst e i).take 1) s) e := by
  rw [run_markFirst f e i s hi]
  intro hs
  have := hs i hi (by simp) σ hσ
  simp [h0] at this

/-- **ING-20** The control: with the mark written first and the run interrupted after it, the
code's drain never repairs the item, since it finds it derived and embeds nothing for it, when no
other pending item shares its structure; its field stays `none` where the drain's is the vector. -/
theorem mark_first_does_not_converge (f : E → S → V) (e : E) (i : I) {s : State I S V E} {σ : S}
    (hi : i ∈ s.keyed) (hσ : s.struct i = some σ) (h0 : s.atom e σ = none)
    (halone : ∀ j ∈ s.keyed, s.struct j = some σ → j = i) :
    field (codeDrain f e (run f ((deriveKeyFirst e i).take 1) s)) e i ≠
      field (drain f e s) e i := by
  rw [run_markFirst f e i s hi, field_drain, ite_eq_left hi,
      show (s.struct i).map (f e) = some (f e σ) by rw [hσ, Option.map_some]]
  have hcond : (codeDrain f e ⟨s.keyed, s.struct, s.atom,
      fun j e' ↦ if j = i ∧ e' = e then s.struct i else s.mark j e'⟩).mark i e = s.struct i := by
    simp [codeDrain, hi]
  have hatom : (codeDrain f e ⟨s.keyed, s.struct, s.atom,
      fun j e' ↦ if j = i ∧ e' = e then s.struct i else s.mark j e'⟩).atom e σ = none := by
    change (if e = e ∧ ∃ j ∈ s.keyed,
        (if j = i ∧ e = e then s.struct i else s.mark j e) ≠ s.struct j ∧ s.struct j = some σ
      then some (f e σ) else s.atom e σ) = none
    rw [ite_eq_right, h0]
    rintro ⟨-, j, hj, hne, hjσ⟩
    rw [halone j hj hjσ] at hne
    exact hne (by simp)
  have hb : ∀ g : S → Option V, (s.struct i).bind g = g σ := fun g ↦ by rw [hσ]; rfl
  unfold field
  rw [ite_eq_left ⟨hi, hcond⟩]
  change (s.struct i).bind _ ≠ _
  rw [hb, hatom]
  exact (Option.some_ne_none (f e σ)).symm

/-! ### ING-21 Pending-report soundness -/

/-- **ING-21** A structural query, any function of the keyed items and their structures, is
invariant under every run of embed steps: the graph, the lexical index and the keys are what the
landing wrote, and embedding touches none of them. -/
theorem structural_invariant {α : Type*} (Q : Finset I → (I → Option S) → α) (f : E → S → V)
    (w : List (Step I S E)) (hw : ∀ a ∈ w, a.isLand = false) (s : State I S V E) :
    Q (run f w s).keyed (run f w s).struct = Q s.keyed s.struct := by
  obtain ⟨h1, h2⟩ := agree_run_of_no_land f w hw s
  rw [h1, h2]

omit [DecidableEq E] in
/-- **ING-21** A pending item's field is `none`: a semantic answer reports it, never a vector. -/
theorem pending_field_none {s : State I S V E} {e : E} {i : I} (h : pending s e i) :
    field s e i = none := by
  unfold field
  rw [ite_eq_right]
  exact fun h' ↦ h.2 h'.2

omit [DecidableEq E] in
/-- **ING-21** A field that reports a vector reports the item's own structure's image under the
embedder: a query never invents a vector. -/
theorem field_some_truthful (f : E → S → V) {s : State I S V E} (ht : Truthful f s) {e : E}
    {i : I} {v : V} (h : field s e i = some v) : ∃ σ, s.struct i = some σ ∧ v = f e σ := by
  unfold field at h
  split_ifs at h with hc
  obtain ⟨σ, hσ, hv⟩ := Option.bind_eq_some_iff.1 h
  exact ⟨σ, hσ, ht e σ v hv⟩

/-- **ING-21** The control: a reading that takes a pending vector as zero gives an answer the
item's embedding changes, so it was an answer about the embedding's progress, not about the
item. -/
theorem zeroRead_changes (f : E → S → V) (score : V → ℤ) (e : E) (i : I) {s : State I S V E}
    {σ : S} (hi : i ∈ s.keyed) (hσ : s.struct i = some σ) (h0 : s.atom e σ = none)
    (hne : score (f e σ) ≠ 0) :
    zeroRead score (run f (derive e i) s) e i ≠ zeroRead score s e i := by
  rw [run_derive f e i s hi]
  simp [zeroRead, hσ, h0, hne]

end Palace.Derived
