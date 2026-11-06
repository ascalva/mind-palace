module

public import Palace.Lineage.Defs

/-!
# The code lineage reader: chain members and the ledger's versions (#50)

Design theorems about `ops/code_lineage.py`, cited from `dn-vector-membership-store`'s errata and
the reader's docstring, not from the ledger: no law the code relies on rests on them.

D4/F3 said a path's chain members are a strict subset of its ledger versions, a side branch's
versions sitting on no chain. Measured on the live ledger they are equal (1,663 = 1,663, issue
#50), and `mem_chain_iff` proves why: the ledger lists every ancestor of HEAD, so it holds every
first parent of its commits, and each commit is diffed against its own first parent, so walking a
version's first-parent ancestry back to the commit that last changed the path finds a diff that
introduced it. The strict subset is HEAD's first-parent line (`Witness.side_chain`). The chain is
linear, a list, but it lists the versions in the ledger's order, so where two lines changed one
path its consecutive pairs include pairs no commit's diff joins (the same witness).
-/

@[expose] public section

namespace Palace.Lineage

variable {C P B : Type*} [DecidableEq B]

theorem mem_step_of_mem {acc : List B} {x : Option B × Option B} {b : B} (hb : b ∈ acc) :
    b ∈ step acc x := by
  have h0 : acc ≠ [] := List.ne_nil_of_mem hb
  obtain ⟨o, _ | n⟩ := x
  · simpa only [step, h0, ↓reduceIte] using hb
  · simp only [step, h0, ↓reduceIte]
    split_ifs
    · exact hb
    · exact List.mem_append_left _ hb

theorem mem_step_new {acc : List B} {o : Option B} {n : B} : n ∈ step acc (o, some n) := by
  simp only [step]
  split_ifs <;>
    first
    | exact List.mem_of_getLast? ‹_›
    | exact List.mem_append_right _ (List.mem_singleton_self n)

theorem mem_of_mem_step {acc : List B} {o nw : Option B} {b : B} (hb : b ∈ step acc (o, nw)) :
    b ∈ acc ∨ nw = some b ∨ o = some b := by
  by_cases h0 : acc = []
  · subst h0
    cases nw with
    | none =>
      simp only [step, ↓reduceIte] at hb
      exact Or.inr (Or.inr (by simpa using hb))
    | some n =>
      simp only [step, ↓reduceIte] at hb
      split_ifs at hb
      · exact Or.inr (Or.inr (by simpa using hb))
      · rcases List.mem_append.1 hb with hb | hb
        · exact Or.inr (Or.inr (by simpa using hb))
        · exact Or.inr (Or.inl (by simp_all))
  · cases nw with
    | none =>
      simp only [step, h0, ↓reduceIte] at hb
      exact Or.inl hb
    | some n =>
      simp only [step, h0, ↓reduceIte] at hb
      split_ifs at hb
      · exact Or.inl hb
      · rcases List.mem_append.1 hb with hb | hb
        · exact Or.inl hb
        · exact Or.inr (Or.inl (by simp_all))

theorem mem_foldl_of_mem {rs : List (Option B × Option B)} {acc : List B} {b : B}
    (hb : b ∈ acc) : b ∈ rs.foldl step acc := by
  induction rs generalizing acc with
  | nil => exact hb
  | cons x rs ih => exact ih (mem_step_of_mem hb)

theorem mem_foldl_new {rs : List (Option B × Option B)} {acc : List B} {o : Option B} {n : B}
    (hx : (o, some n) ∈ rs) : n ∈ rs.foldl step acc := by
  induction rs generalizing acc with
  | nil => simp at hx
  | cons x rs ih =>
    rcases List.mem_cons.1 hx with rfl | hx
    · exact mem_foldl_of_mem (rs := rs) (acc := step acc (o, some n)) mem_step_new
    · exact ih hx

theorem mem_of_mem_foldl {rs : List (Option B × Option B)} {acc : List B} {b : B}
    (hb : b ∈ rs.foldl step acc) : b ∈ acc ∨ ∃ x ∈ rs, x.2 = some b ∨ x.1 = some b := by
  induction rs generalizing acc with
  | nil => exact Or.inl hb
  | cons x rs ih =>
    rcases ih hb with h | ⟨y, hy, hyb⟩
    · obtain ⟨o, nw⟩ := x
      rcases mem_of_mem_step h with h | h | h
      · exact Or.inl h
      · exact Or.inr ⟨(o, nw), List.mem_cons_self, Or.inl h⟩
      · exact Or.inr ⟨(o, nw), List.mem_cons_self, Or.inr h⟩
    · exact Or.inr ⟨y, List.mem_cons_of_mem _ hy, hyb⟩

namespace History

theorem mem_rows {h : History C P B} {L : List C} {p : P} {x : Option B × Option B} :
    x ∈ h.rows L p ↔ ∃ c ∈ L, h.before c p ≠ h.tree c p ∧ x = (h.before c p, h.tree c p) := by
  simp only [rows, List.mem_filterMap]
  constructor
  · rintro ⟨c, hc, hx⟩
    split_ifs at hx with hd
    · exact ⟨c, hc, hd, (Option.some.inj hx).symm⟩
  · rintro ⟨c, hc, hd, rfl⟩
    exact ⟨c, hc, by simp [hd]⟩

/-- Every version is the new blob of some row: walk the version's first-parent ancestry back to
the commit that last changed the path, where its diff introduced the blob (a root diffs against
the empty tree). -/
theorem new_of_version (h : History C P B) {L : List C}
    (closed : ∀ c ∈ L, ∀ c', h.parent c = some c' → c' ∈ L) (r : C → ℕ)
    (hr : ∀ c c', h.parent c = some c' → r c' < r c) (p : P) :
    ∀ n, ∀ c ∈ L, r c = n → ∀ b, h.tree c p = some b → ∃ o, (o, some b) ∈ h.rows L p := by
  intro n
  induction n using Nat.strongRecOn with
  | _ n ih =>
    intro c hc hrc b hb
    by_cases hd : h.before c p = h.tree c p
    · rw [hb] at hd
      obtain ⟨c', hpc, hc'⟩ := Option.bind_eq_some_iff.1 hd
      exact ih (r c') (hrc ▸ hr c c' hpc) c' (closed c hc c' hpc) rfl b hc'
    · exact ⟨h.before c p, mem_rows.2 ⟨c, hc, hd, by rw [hb]⟩⟩

/-- **The claim that holds** (#50): when the ledger lists every first parent of its commits (as
`rev-list HEAD` lists every ancestor) and every commit's diff is captured, the root's against the
empty tree, a path's chain members are exactly its versions in the ledger. -/
theorem mem_chain_iff (h : History C P B) {L : List C}
    (closed : ∀ c ∈ L, ∀ c', h.parent c = some c' → c' ∈ L) (r : C → ℕ)
    (hr : ∀ c c', h.parent c = some c' → r c' < r c) (p : P) (b : B) :
    b ∈ h.chain L p ↔ h.Version L p b := by
  constructor
  · intro hb
    rcases mem_of_mem_foldl hb with hb | ⟨x, hx, hxb⟩
    · simp at hb
    · obtain ⟨c, hc, -, rfl⟩ := mem_rows.1 hx
      rcases hxb with hxb | hxb
      · exact ⟨c, hc, hxb⟩
      · obtain ⟨c', hpc, hc'⟩ := Option.bind_eq_some_iff.1 hxb
        exact ⟨c', closed c hc c' hpc, hc'⟩
  · rintro ⟨c, hc, hb⟩
    obtain ⟨o, hx⟩ := new_of_version h closed r hr p (r c) c hc rfl b hb
    exact mem_foldl_new hx

end History

namespace Witness

/-- The side branch meets `mem_chain_iff`'s hypotheses: the ledger holds every first parent, and a
commit's index ranks it above its first parent. -/
theorem side_closed : (∀ c ∈ ledger, ∀ c', side.parent c = some c' → c' ∈ ledger) ∧
    ∀ c c', side.parent c = some c' → c'.val < c.val := by
  decide

/-- **What fails** (#50). On the side branch the chain is every version, in the ledger's order;
HEAD's first-parent line holds three of the five, so it is the strict subset; and the chain joins
`s1` to `m2`, a pair no commit's diff joins (nor do its next two pairs): a chain's consecutive pairs
are supersessions only where no two lines changed the path. -/
theorem side_chain :
    side.chain ledger () = [0, 1, 2, 3, 4] ∧
      (side.line 5 4).filterMap (side.tree · ()) = [4, 2, 0] ∧
      (some 1, some 2) ∉ side.rows ledger () ∧ (some 2, some 3) ∉ side.rows ledger () ∧
      (some 3, some 4) ∉ side.rows ledger () := by
  decide

end Witness

end Palace.Lineage
