module

public import Palace.SnapshotAlgebra.Defs
public import Palace.Snapshot

/-!
# The algebra of cuts

The laws of dn-temporal-snapshot §4.4, on the model of `Palace/SnapshotAlgebra/Defs.lean`: a cut
as a value that stands for what the store held as of it, the operators on its positions, and the
operators on its contents, the rows of the generational store (`gens`) alive at it. SNP-11 to
SNP-17 are the ledger's (`docs/LAWS.md`, XVI): each declaration a row cites carries its law in
bold and is stated in `formal/Spec/SnapshotAlgebra.lean`.

* SNP-11, the lattice of cuts: the cuts inside a store are a distributive lattice under the
  pointwise meet and join, with the empty cut at the bottom and the head at the top, and no cut
  leaves it as the store grows (`cutsIn`, `bot_mem_cutsIn`, `head_mem_cutsIn`, `cutsIn_mono`,
  `readAt_inf_sup`). The read at the join is, chain by chain, the later of the two reads, and at
  the meet the earlier (`readAt_sup`, `readAt_inf`). The difference of two cuts on positions is
  the events between them, read from their meet or to their join, and the symmetric difference
  the events between their meet and their join (`readBetween_inf_left`, `readBetween_sup_right`,
  `readBetween_inf_sup`); it is a function of the two reads (`readBetween_eq_combine`). The meet
  and the join of two cuts that are read as asked are read as asked, the consistency by CLK-2
  (`resolvesIn_sup`, `resolvesIn_inf`).
* SNP-12, a row lives on an interval: a row is alive from its position up to its closing stamp
  (`Gen.aliveAt_iff`), so a row alive at two cuts is alive at every cut between them
  (`Gen.aliveAt_of_between`). What the later of two cuts holds and the earlier does not, what
  the earlier holds and the later does not and what both hold are each one range of positions
  and stamps (`Gen.aliveAt_and_not`, `Gen.aliveAt_and_not'`, `Gen.aliveAt_and`); a row is alive
  at every cut of a family exactly when it is alive at the least and at the greatest
  (`Gen.forall_aliveAt_iff`), and at some cut of a range exactly when it was stored by its end
  and not closed by its start (`Gen.exists_aliveAt_iff`). On the generations of a chain a row
  records the chain's event at its position, its stamp is the position of its key's next event,
  and a cut holds each key's state once (`getElem?_of_mem_gens`, `exists_next_of_mem_gens`,
  `proper_of_mem_gens`, `map_val_filter_key_contentAt`, `eq_of_key_eq_of_mem_contentAt`). The
  control is a value, which has no interval (`Witness.value_not_contiguous`).
* SNP-13, the signed difference: its two sides are range reads (`Held.has_come`,
  `Held.has_gone`); applied to what the first cut holds it gives what the second holds
  (`Held.has_cut_eq_apply`); differences compose along cuts in order, a row that came and went
  on the way cancelling, and a row gone across two steps is gone in one of them
  (`Held.has_come_trans`, `Held.has_gone_trans`, `Held.has_trans_of_transient`,
  `Held.has_gone_triangle`); a sum over the rows, a count among them, walks the difference
  (`Held.sum_rows_delta`, `Held.length_rows_delta`); its rows sort by key into removed, added
  and replaced (`mem_gone_iff`, `not_replacedOf_of_removedOf`, `mem_come_iff`); and every row
  of it belongs to a key the events between the two cuts name (`key_mem_of_mem_delta`). The
  controls: a composition through a cut outside the two, and a key the events name that the
  difference does not hold (`Witness.delta_through_outside`, `Witness.changed_not_delta`).
* SNP-14, closure: a set of rows is an expression over the contents of cuts, closed under
  union, intersection and difference, and a set read is the set operation on the reads
  (`Held.mem_rows_union`, `Held.mem_rows_inter`, `Held.mem_rows_diff`, `Held.has_symm`,
  `Held.has_inter_union`, `Held.has_diff_diff`). Whether a row is in a set is a function of its
  position and its stamp (`Held.has_eq_of_interval`); a set lies inside the contents of the cuts
  it names (`Held.exists_atom_of_has`); a row's own test commutes with it (`Held.rows_filter`);
  and it is append invariant, a derived view of the read at its cuts (`Held.rows_gens_append`,
  `Held.rows_gens_take`). What every cut of a family holds is what its least and greatest cuts
  both hold, one range read (`Held.has_all`, `Held.has_all_eq_kept`, `Held.has_kept`), what
  some cut holds and in how many are read off the same intervals (`Held.has_any`,
  `countIn_pos_iff`, `countIn_eq_length_iff`), and a function of two reads, a measure at each
  cut and a fold over a family are append invariant (`combine_grow`, `series_grow`,
  `foldOver_grow`). The control is the complement, which grows with the store
  (`Witness.complement_grows`).
* SNP-15, contents against positions: what either of two cuts holds is what their join holds
  with the rows closed between their meet and their join, and what both hold is what their meet
  and their join both hold (`Gen.aliveAt_or_eq_sup`, `Gen.aliveAt_and_eq_inf_sup`,
  `Held.has_union_cut`, `Held.has_inter_cut`); for a row that is never closed the two meanings
  agree (`Gen.aliveAt_sup_of_open`, `Gen.aliveAt_inf_of_open`). The control is one key written
  twice (`Witness.union_ne_join`).
* SNP-16, the grant: every set commutes with the grant's restriction, reads only the chains
  the grant names and the cuts' positions on them, is under a narrower grant the restriction of
  a wider grant's, and names no other chain (`Held.across_restrict`, `Held.across_congr`,
  `restrict_narrow`, `Held.across_narrow`, `Held.across_of_not`); the events between two cuts
  commute with a grant of whole chains (`restrict_readBetween`). The control is a row's test
  applied before the generations are computed (`Witness.filter_before_gens`).
* SNP-17, erasure and retire: the closing stamps are a function of the keys alone, so a hole
  that keeps its key moves no position and no stamp (`gens_map`); no row of a chain with holes
  carries an erased value, and an erasure takes its own rows out of every set and changes no
  other (`not_erased_of_mem_gens_holes`, `Held.rows_gens_holes`); a retire is a removal in the
  signed difference that spans it (`removed_of_retire`).
-/

@[expose] public section

namespace Palace.Snapshot

/-! ### A row lives on an interval -/

section Interval

variable {κ β : Type*}

/-- **SNP-12** A row is alive at a cut from its position up to, and not at, its closing stamp. -/
theorem Gen.aliveAt_iff {r : Gen κ β} {c : ℕ} :
    r.aliveAt c = true ↔ r.born ≤ c ∧ ∀ d, r.died = some d → c < d := by
  unfold Gen.aliveAt
  cases r.died with
  | none => simp
  | some d => simp

/-- A row is not alive at a cut before its position, and from its closing stamp on. -/
theorem Gen.aliveAt_eq_false_iff {r : Gen κ β} {c : ℕ} :
    r.aliveAt c = false ↔ c < r.born ∨ ∃ d, r.died = some d ∧ d ≤ c := by
  unfold Gen.aliveAt
  cases r.died with
  | none => simp
  | some d => simp; omega

/-- **SNP-12** Contiguity: a row alive at two cuts is alive at every cut between them. A row lives
on one interval of its chain's positions. -/
theorem Gen.aliveAt_of_between {r : Gen κ β} {a b c : ℕ} (ha : r.aliveAt a = true)
    (hb : r.aliveAt b = true) (hac : a ≤ c) (hcb : c ≤ b) : r.aliveAt c = true := by
  rw [Gen.aliveAt_iff] at ha hb ⊢
  exact ⟨ha.1.trans hac, fun d hd ↦ lt_of_le_of_lt hcb (hb.2 d hd)⟩

/-- **SNP-12** What the later of two cuts holds and the earlier does not: the rows stored after the
earlier cut and alive at the later one. -/
theorem Gen.aliveAt_and_not {r : Gen κ β} {a b : ℕ} (h : a ≤ b) :
    (r.aliveAt b && !r.aliveAt a) = (decide (a < r.born) && r.aliveAt b) := by
  unfold Gen.aliveAt
  rw [Bool.eq_iff_iff]
  cases r.died <;> simp <;> omega

/-- **SNP-12** What the earlier of two cuts holds and the later does not: the rows alive at the
earlier cut whose closing stamp is at or under the later one. -/
theorem Gen.aliveAt_and_not' {r : Gen κ β} {a b : ℕ} (h : a ≤ b) :
    (r.aliveAt a && !r.aliveAt b) = (r.aliveAt a && r.died.any fun d ↦ decide (d ≤ b)) := by
  unfold Gen.aliveAt
  rw [Bool.eq_iff_iff]
  cases r.died <;> simp <;> omega

/-- **SNP-12** What two cuts both hold: the rows stored at or under the earlier cut whose closing
stamp is absent or past the later one. -/
theorem Gen.aliveAt_and {r : Gen κ β} {a b : ℕ} (h : a ≤ b) :
    (r.aliveAt a && r.aliveAt b)
      = (decide (r.born ≤ a) && r.died.all fun d ↦ decide (b < d)) := by
  unfold Gen.aliveAt
  rw [Bool.eq_iff_iff]
  cases r.died <;> simp <;> omega

/-- **SNP-12** A row is alive at every cut of a family exactly when it is alive at the family's
least cut and at its greatest. -/
theorem Gen.forall_aliveAt_iff {r : Gen κ β} {F : List ℕ} {lo hi : ℕ} (hlo : lo ∈ F)
    (hhi : hi ∈ F) (hF : ∀ c ∈ F, lo ≤ c ∧ c ≤ hi) :
    (∀ c ∈ F, r.aliveAt c = true) ↔ r.aliveAt lo = true ∧ r.aliveAt hi = true :=
  ⟨fun h ↦ ⟨h lo hlo, h hi hhi⟩,
    fun h c hc ↦ Gen.aliveAt_of_between h.1 h.2 (hF c hc).1 (hF c hc).2⟩

/-- **SNP-12** A well-formed row is alive at some cut of a range of positions exactly when it was
stored at or under the range's end and not closed at or under its start. -/
theorem Gen.exists_aliveAt_iff {r : Gen κ β} (hr : r.Proper) {lo hi : ℕ} (h : lo ≤ hi) :
    (∃ c, lo ≤ c ∧ c ≤ hi ∧ r.aliveAt c = true)
      ↔ r.born ≤ hi ∧ ∀ d, r.died = some d → lo < d := by
  constructor
  · rintro ⟨c, hlo, hhi, hc⟩
    rw [Gen.aliveAt_iff] at hc
    exact ⟨hc.1.trans hhi, fun d hd ↦ lt_of_le_of_lt hlo (hc.2 d hd)⟩
  · rintro ⟨hb, hd⟩
    refine ⟨max r.born lo, le_max_right _ _, max_le hb h, ?_⟩
    rw [Gen.aliveAt_iff]
    exact ⟨le_max_left _ _, fun d hdd ↦ max_lt (hr d hdd) (hd d hdd)⟩

/-- **SNP-15** What two cuts both hold is what their meet and their join both hold. -/
theorem Gen.aliveAt_and_eq_inf_sup (r : Gen κ β) (a b : ℕ) :
    (r.aliveAt a && r.aliveAt b) = (r.aliveAt (a ⊓ b) && r.aliveAt (a ⊔ b)) := by
  rcases le_total a b with h | h
  · rw [inf_of_le_left h, sup_of_le_right h]
  · rw [inf_of_le_right h, sup_of_le_left h, Bool.and_comm]

/-- **SNP-15** What either of two cuts holds is what their join holds and what was closed between
their meet and their join. -/
theorem Gen.aliveAt_or_eq_sup (r : Gen κ β) (a b : ℕ) :
    (r.aliveAt a || r.aliveAt b)
      = (r.aliveAt (a ⊔ b) || (r.aliveAt (a ⊓ b) && !r.aliveAt (a ⊔ b))) := by
  rcases le_total a b with h | h
  · rw [inf_of_le_left h, sup_of_le_right h]
    cases r.aliveAt a <;> cases r.aliveAt b <;> rfl
  · rw [inf_of_le_right h, sup_of_le_left h]
    cases r.aliveAt a <;> cases r.aliveAt b <;> rfl

/-- **SNP-15** A row that is never closed is alive at the join of two cuts exactly when it is alive
at one of them. -/
theorem Gen.aliveAt_sup_of_open {r : Gen κ β} (hr : r.died = none) (a b : ℕ) :
    r.aliveAt (a ⊔ b) = (r.aliveAt a || r.aliveAt b) := by
  rcases le_total a b with h | h
  · rw [sup_of_le_right h]
    unfold Gen.aliveAt
    rw [Bool.eq_iff_iff, hr]
    simp
    omega
  · rw [sup_of_le_left h]
    unfold Gen.aliveAt
    rw [Bool.eq_iff_iff, hr]
    simp
    omega

/-- **SNP-15** And at their meet exactly when it is alive at both. -/
theorem Gen.aliveAt_inf_of_open {r : Gen κ β} (hr : r.died = none) (a b : ℕ) :
    r.aliveAt (a ⊓ b) = (r.aliveAt a && r.aliveAt b) := by
  rcases le_total a b with h | h
  · rw [inf_of_le_left h]
    unfold Gen.aliveAt
    rw [Bool.eq_iff_iff, hr]
    simp
    omega
  · rw [inf_of_le_right h]
    unfold Gen.aliveAt
    rw [Bool.eq_iff_iff, hr]
    simp
    omega

end Interval

/-! ### Sets of rows, named and not read -/

section Expressions

variable {κ β γ : Type*} {pos : γ → ℕ}

namespace Held

theorem rows_cut (c : γ) (rs : List (Gen κ β)) : (cut c).rows pos rs = contentAt rs (pos c) :=
  rfl

/-- A set read on a chain is a sublist of the chain's rows. -/
theorem rows_sublist (e : Held γ) (rs : List (Gen κ β)) : (e.rows pos rs).Sublist rs :=
  List.filter_sublist

/-- **SNP-14** The union read is the union of the reads. -/
theorem mem_rows_union {p q : Held γ} {rs : List (Gen κ β)} {r : Gen κ β} :
    r ∈ (p.union q).rows pos rs ↔ r ∈ p.rows pos rs ∨ r ∈ q.rows pos rs := by
  simp only [rows, has, List.mem_filter, Bool.or_eq_true, and_or_left]

/-- **SNP-14** The intersection read is the intersection of the reads. -/
theorem mem_rows_inter {p q : Held γ} {rs : List (Gen κ β)} {r : Gen κ β} :
    r ∈ (p.inter q).rows pos rs ↔ r ∈ p.rows pos rs ∧ r ∈ q.rows pos rs := by
  simp only [rows, has, List.mem_filter, Bool.and_eq_true]
  tauto

/-- **SNP-14** The difference read is the difference of the reads. -/
theorem mem_rows_diff {p q : Held γ} {rs : List (Gen κ β)} {r : Gen κ β} :
    r ∈ (p.diff q).rows pos rs ↔ r ∈ p.rows pos rs ∧ r ∉ q.rows pos rs := by
  simp only [rows, has, List.mem_filter, Bool.and_eq_true, Bool.not_eq_true', not_and,
    Bool.not_eq_true]
  tauto

/-- **SNP-14** What exactly one of two sets holds is what either holds and not both. -/
theorem has_symm (p q : Held γ) (r : Gen κ β) :
    (symm p q).has pos r = ((p.union q).diff (p.inter q)).has pos r := by
  simp only [symm, has]
  cases p.has pos r <;> cases q.has pos r <;> rfl

theorem has_union_comm (p q : Held γ) (r : Gen κ β) :
    (p.union q).has pos r = (q.union p).has pos r :=
  Bool.or_comm _ _

theorem has_inter_comm (p q : Held γ) (r : Gen κ β) :
    (p.inter q).has pos r = (q.inter p).has pos r :=
  Bool.and_comm _ _

theorem has_union_assoc (p q t : Held γ) (r : Gen κ β) :
    ((p.union q).union t).has pos r = (p.union (q.union t)).has pos r :=
  Bool.or_assoc _ _ _

theorem has_inter_assoc (p q t : Held γ) (r : Gen κ β) :
    ((p.inter q).inter t).has pos r = (p.inter (q.inter t)).has pos r :=
  Bool.and_assoc _ _ _

theorem has_union_self (p : Held γ) (r : Gen κ β) : (p.union p).has pos r = p.has pos r :=
  Bool.or_self _

theorem has_inter_self (p : Held γ) (r : Gen κ β) : (p.inter p).has pos r = p.has pos r :=
  Bool.and_self _

/-- Absorption: a set united with its intersection with another is itself. -/
theorem has_union_inter_self (p q : Held γ) (r : Gen κ β) :
    (p.union (p.inter q)).has pos r = p.has pos r := by
  simp only [has]
  cases p.has pos r <;> cases q.has pos r <;> rfl

/-- Absorption: a set intersected with its union with another is itself. -/
theorem has_inter_union_self (p q : Held γ) (r : Gen κ β) :
    (p.inter (p.union q)).has pos r = p.has pos r := by
  simp only [has]
  cases p.has pos r <;> cases q.has pos r <;> rfl

/-- **SNP-14** Intersection distributes over union. -/
theorem has_inter_union (p q t : Held γ) (r : Gen κ β) :
    (p.inter (q.union t)).has pos r = ((p.inter q).union (p.inter t)).has pos r := by
  simp only [has]
  cases p.has pos r <;> cases q.has pos r <;> cases t.has pos r <;> rfl

/-- Union distributes over intersection. -/
theorem has_union_inter (p q t : Held γ) (r : Gen κ β) :
    (p.union (q.inter t)).has pos r = ((p.union q).inter (p.union t)).has pos r := by
  simp only [has]
  cases p.has pos r <;> cases q.has pos r <;> cases t.has pos r <;> rfl

/-- A set less itself holds nothing. -/
theorem has_diff_self (p : Held γ) (r : Gen κ β) : (p.diff p).has pos r = false :=
  Bool.and_not_self _

/-- **SNP-14** A set less what it holds and another does not is what both hold. -/
theorem has_diff_diff (p q : Held γ) (r : Gen κ β) :
    (p.diff (p.diff q)).has pos r = (p.inter q).has pos r := by
  simp only [has]
  cases p.has pos r <;> cases q.has pos r <;> rfl

/-- A difference distributes over the union it is taken from. -/
theorem has_union_diff (p q t : Held γ) (r : Gen κ β) :
    ((p.union q).diff t).has pos r = ((p.diff t).union (q.diff t)).has pos r := by
  simp only [has]
  cases p.has pos r <;> cases q.has pos r <;> cases t.has pos r <;> rfl

/-- A set reads of the cuts it names only their positions: two readings of the positions that
agree on its cuts give one set. -/
theorem has_congr {pos' : γ → ℕ} {e : Held γ} (h : ∀ c ∈ e.atoms, pos c = pos' c)
    (r : Gen κ β) : e.has pos r = e.has pos' r := by
  induction e with
  | cut c => simp only [has, h c (by simp [atoms])]
  | union p q ihp ihq =>
    simp only [has, ihp fun c hc ↦ h c (by simp [atoms, hc]),
      ihq fun c hc ↦ h c (by simp [atoms, hc])]
  | inter p q ihp ihq =>
    simp only [has, ihp fun c hc ↦ h c (by simp [atoms, hc]),
      ihq fun c hc ↦ h c (by simp [atoms, hc])]
  | diff p q ihp ihq =>
    simp only [has, ihp fun c hc ↦ h c (by simp [atoms, hc]),
      ihq fun c hc ↦ h c (by simp [atoms, hc])]

/-- **SNP-14** Whether a row is in a set is a function of the row's position and its closing stamp:
two rows with one interval, whatever their keys and values, are in the same sets. Combining sets
reads no row. -/
theorem has_eq_of_interval {κ' β' : Type*} (e : Held γ) {r : Gen κ β} {r' : Gen κ' β'}
    (hb : r.born = r'.born) (hd : r.died = r'.died) : e.has pos r = e.has pos r' := by
  induction e with
  | cut c => simp only [has, Gen.aliveAt, hb, hd]
  | union p q ihp ihq => simp only [has, ihp, ihq]
  | inter p q ihp ihq => simp only [has, ihp, ihq]
  | diff p q ihp ihq => simp only [has, ihp, ihq]

/-- **SNP-14** A set lies inside the contents of the cuts it names: a row in it is alive at one of
them. There is no complement. -/
theorem exists_atom_of_has {e : Held γ} {r : Gen κ β} (h : e.has pos r = true) :
    ∃ c ∈ e.atoms, r.aliveAt (pos c) = true := by
  induction e with
  | cut c => exact ⟨c, by simp [atoms], h⟩
  | union p q ihp ihq =>
    rcases Bool.or_eq_true_iff.1 h with h | h
    · obtain ⟨c, hc, ha⟩ := ihp h
      exact ⟨c, by simp [atoms, hc], ha⟩
    · obtain ⟨c, hc, ha⟩ := ihq h
      exact ⟨c, by simp [atoms, hc], ha⟩
  | inter p q ihp _ =>
    obtain ⟨c, hc, ha⟩ := ihp (Bool.and_eq_true_iff.1 h).1
    exact ⟨c, by simp [atoms, hc], ha⟩
  | diff p q ihp _ =>
    obtain ⟨c, hc, ha⟩ := ihp (Bool.and_eq_true_iff.1 h).1
    exact ⟨c, by simp [atoms, hc], ha⟩

/-- A closing stamp written past every cut a set names changes nothing in the set: a row that
was open, and is closed later at a position past those cuts, is in the set exactly when it
was. -/
theorem has_of_closed_later {e : Held γ} {r r' : Gen κ β} (hb : r'.born = r.born)
    (hd : r'.died = r.died ∨ (r.died = none ∧ ∃ d, r'.died = some d ∧ ∀ c ∈ e.atoms, pos c < d)) :
    e.has pos r' = e.has pos r := by
  induction e with
  | cut c =>
    rcases hd with hd | ⟨hn, d, hd, hlt⟩
    · simp only [has, Gen.aliveAt, hb, hd]
    · have hc : pos c < d := hlt c (by simp [atoms])
      simp [has, Gen.aliveAt, hb, hd, hn, hc]
  | union p q ihp ihq =>
    simp only [has, ihp (hd.imp_right fun ⟨hn, d, h1, h2⟩ ↦ ⟨hn, d, h1, fun c hc ↦
      h2 c (by simp [atoms, hc])⟩), ihq (hd.imp_right fun ⟨hn, d, h1, h2⟩ ↦ ⟨hn, d, h1,
      fun c hc ↦ h2 c (by simp [atoms, hc])⟩)]
  | inter p q ihp ihq =>
    simp only [has, ihp (hd.imp_right fun ⟨hn, d, h1, h2⟩ ↦ ⟨hn, d, h1, fun c hc ↦
      h2 c (by simp [atoms, hc])⟩), ihq (hd.imp_right fun ⟨hn, d, h1, h2⟩ ↦ ⟨hn, d, h1,
      fun c hc ↦ h2 c (by simp [atoms, hc])⟩)]
  | diff p q ihp ihq =>
    simp only [has, ihp (hd.imp_right fun ⟨hn, d, h1, h2⟩ ↦ ⟨hn, d, h1, fun c hc ↦
      h2 c (by simp [atoms, hc])⟩), ihq (hd.imp_right fun ⟨hn, d, h1, h2⟩ ↦ ⟨hn, d, h1,
      fun c hc ↦ h2 c (by simp [atoms, hc])⟩)]

/-- **SNP-14** A row's own test, one that does not depend on a cut, commutes with every set: the
rows of a set that pass the test are the set read on the rows that pass it. -/
theorem rows_filter (e : Held γ) (p : Gen κ β → Bool) (rs : List (Gen κ β)) :
    (e.rows pos rs).filter p = e.rows pos (rs.filter p) := by
  simp only [rows, List.filter_filter]
  exact List.filter_congr fun r _ ↦ Bool.and_comm _ _

end Held

end Expressions

/-! ### The signed difference of two cuts, and a family of cuts -/

section Delta

variable {κ β γ : Type*} {pos : γ → ℕ}

namespace Held

/-- The two sides of a signed difference exchange when the two cuts do. -/
theorem gone_swap (a b : γ) : gone b a = come a b := rfl

/-- A cut differs from itself by nothing. -/
theorem has_gone_self (a : γ) (r : Gen κ β) : (gone a a).has pos r = false :=
  Bool.and_not_self _

/-- **SNP-13** What the later cut holds and the earlier does not, as one range read: the rows stored
after the earlier cut and alive at the later one. -/
theorem has_come {a b : γ} (h : pos a ≤ pos b) (r : Gen κ β) :
    (come a b).has pos r = (decide (pos a < r.born) && r.aliveAt (pos b)) :=
  Gen.aliveAt_and_not h

/-- **SNP-13** What the earlier cut holds and the later does not, as one range read: the rows alive
at the earlier cut whose closing stamp is at or under the later one. -/
theorem has_gone {a b : γ} (h : pos a ≤ pos b) (r : Gen κ β) :
    (gone a b).has pos r = (r.aliveAt (pos a) && r.died.any fun d ↦ decide (d ≤ pos b)) :=
  Gen.aliveAt_and_not' h

/-- **SNP-14** What both cuts hold, as one range read: the rows stored at or under the earlier cut
and not closed at or under the later one. -/
theorem has_kept {a b : γ} (h : pos a ≤ pos b) (r : Gen κ β) :
    (kept a b).has pos r
      = (decide (r.born ≤ pos a) && r.died.all fun d ↦ decide (pos b < d)) :=
  Gen.aliveAt_and h

/-- **SNP-13** The signed difference applied: what the second cut holds is what the first holds,
less the rows gone, with the rows come. The result of a difference is an operand again. -/
theorem has_cut_eq_apply (a b : γ) (r : Gen κ β) :
    (cut b).has pos r = (((cut a).diff (gone a b)).union (come a b)).has pos r := by
  simp only [gone, come, has]
  cases r.aliveAt (pos a) <;> cases r.aliveAt (pos b) <;> rfl

/-- **SNP-13** Signed differences compose along cuts in order: the rows come from `a` to `c` are the
rows come from `a` to `b` that did not go from `b` to `c`, with the rows come from `b` to `c`. It
holds when `b` lies between `a` and `c` on the chain, in either direction. -/
theorem has_come_trans {a b c : γ}
    (h : (pos a ≤ pos b ∧ pos b ≤ pos c) ∨ (pos c ≤ pos b ∧ pos b ≤ pos a)) (r : Gen κ β) :
    (come a c).has pos r = (((come a b).diff (gone b c)).union (come b c)).has pos r := by
  have hB : r.aliveAt (pos a) = true → r.aliveAt (pos c) = true → r.aliveAt (pos b) = true := by
    intro ha hc
    rcases h with h | h
    · exact Gen.aliveAt_of_between ha hc h.1 h.2
    · exact Gen.aliveAt_of_between hc ha h.1 h.2
  revert hB
  simp only [gone, come, has]
  generalize r.aliveAt (pos a) = A
  generalize r.aliveAt (pos b) = B
  generalize r.aliveAt (pos c) = C
  intro hB
  cases A <;> cases B <;> cases C <;>
    first | rfl | exact absurd (hB rfl rfl) Bool.false_ne_true

/-- **SNP-13** And the rows gone from `a` to `c` are the rows gone from `a` to `b`, with the rows
gone from `b` to `c` that had not come from `a` to `b`. -/
theorem has_gone_trans {a b c : γ}
    (h : (pos a ≤ pos b ∧ pos b ≤ pos c) ∨ (pos c ≤ pos b ∧ pos b ≤ pos a)) (r : Gen κ β) :
    (gone a c).has pos r = ((gone a b).union ((gone b c).diff (come a b))).has pos r := by
  have hB : r.aliveAt (pos a) = true → r.aliveAt (pos c) = true → r.aliveAt (pos b) = true := by
    intro ha hc
    rcases h with h | h
    · exact Gen.aliveAt_of_between ha hc h.1 h.2
    · exact Gen.aliveAt_of_between hc ha h.1 h.2
  revert hB
  simp only [gone, come, has]
  generalize r.aliveAt (pos a) = A
  generalize r.aliveAt (pos b) = B
  generalize r.aliveAt (pos c) = C
  intro hB
  cases A <;> cases B <;> cases C <;>
    first | rfl | exact absurd (hB rfl rfl) Bool.false_ne_true

/-- **SNP-13** A row that came between `a` and `b` and went between `b` and `c` is on neither side
of the difference from `a` to `c`: what a composition cancels. -/
theorem has_trans_of_transient {a b c : γ} {r : Gen κ β} (h1 : (come a b).has pos r = true)
    (h2 : (gone b c).has pos r = true) :
    (come a c).has pos r = false ∧ (gone a c).has pos r = false := by
  revert h1 h2
  simp only [gone, come, has]
  cases r.aliveAt (pos a) <;> cases r.aliveAt (pos b) <;> cases r.aliveAt (pos c) <;> simp

/-- **SNP-13** A row gone from `a` to `c` is gone from `a` to `b` or from `b` to `c`, whatever `b`:
the inclusion the triangle inequality of the differences' sizes follows from. -/
theorem has_gone_triangle (a b c : γ) {r : Gen κ β} (h : (gone a c).has pos r = true) :
    (gone a b).has pos r = true ∨ (gone b c).has pos r = true := by
  revert h
  simp only [gone, has]
  cases r.aliveAt (pos a) <;> cases r.aliveAt (pos b) <;> cases r.aliveAt (pos c) <;> simp

theorem has_foldl_inter (F : List γ) (e : Held γ) (r : Gen κ β) :
    (F.foldl (fun e d ↦ inter e (cut d)) e).has pos r = true
      ↔ e.has pos r = true ∧ ∀ d ∈ F, r.aliveAt (pos d) = true := by
  induction F generalizing e with
  | nil => simp
  | cons d F ih =>
    rw [List.foldl_cons, ih]
    simp only [has, Bool.and_eq_true, List.forall_mem_cons, and_assoc]

theorem has_foldl_union (F : List γ) (e : Held γ) (r : Gen κ β) :
    (F.foldl (fun e d ↦ union e (cut d)) e).has pos r = true
      ↔ e.has pos r = true ∨ ∃ d ∈ F, r.aliveAt (pos d) = true := by
  induction F generalizing e with
  | nil => simp
  | cons d F ih =>
    rw [List.foldl_cons, ih]
    simp only [has, Bool.or_eq_true, List.exists_mem_cons_iff, or_assoc]

/-- **SNP-14** What every cut of a family holds: the rows alive at each of them. -/
theorem has_all {c : γ} {F : List γ} {r : Gen κ β} :
    (all c F).has pos r = true ↔ ∀ d ∈ c :: F, r.aliveAt (pos d) = true := by
  rw [all, has_foldl_inter, List.forall_mem_cons]
  rfl

/-- **SNP-14** What some cut of a family holds: the rows alive at one of them. -/
theorem has_any {c : γ} {F : List γ} {r : Gen κ β} :
    (any c F).has pos r = true ↔ ∃ d ∈ c :: F, r.aliveAt (pos d) = true := by
  rw [any, has_foldl_union, List.exists_mem_cons_iff]
  rfl

/-- **SNP-14** What every cut of a family holds is what its least and its greatest cut both hold:
two positions, whatever the size of the family. -/
theorem has_all_eq_kept {c lo hi : γ} {F : List γ} (hlo : lo ∈ c :: F) (hhi : hi ∈ c :: F)
    (hF : ∀ d ∈ c :: F, pos lo ≤ pos d ∧ pos d ≤ pos hi) (r : Gen κ β) :
    (all c F).has pos r = (kept lo hi).has pos r := by
  rw [Bool.eq_iff_iff, has_all]
  simp only [kept, has, Bool.and_eq_true]
  exact ⟨fun h ↦ ⟨h lo hlo, h hi hhi⟩,
    fun h d hd ↦ Gen.aliveAt_of_between h.1 h.2 (hF d hd).1 (hF d hd).2⟩

theorem sum_map_filter_or {M : Type*} [AddCommMonoid M] (w : Gen κ β → M)
    (p q : Gen κ β → Bool) (rs : List (Gen κ β)) :
    ((rs.filter fun r ↦ p r || q r).map w).sum
      = ((rs.filter p).map w).sum + ((rs.filter fun r ↦ q r && !p r).map w).sum := by
  induction rs with
  | nil => simp
  | cons r rs ih =>
    cases hp : p r <;> cases hq : q r <;>
      simp [hp, hq, ih, add_assoc, add_left_comm]

/-- **SNP-13** A measure that is a sum over the rows walks the signed difference: the sum over what
the second cut holds, with the sum over the rows gone, is the sum over what the first holds, with
the sum over the rows come. A count is the case of the measure one. -/
theorem sum_rows_delta {M : Type*} [AddCommMonoid M] (w : Gen κ β → M) (a b : γ)
    (rs : List (Gen κ β)) :
    (((cut b).rows pos rs).map w).sum + (((gone a b).rows pos rs).map w).sum
      = (((cut a).rows pos rs).map w).sum + (((come a b).rows pos rs).map w).sum := by
  have h1 := sum_map_filter_or w (fun r ↦ r.aliveAt (pos b)) (fun r ↦ r.aliveAt (pos a)) rs
  have h2 := sum_map_filter_or w (fun r ↦ r.aliveAt (pos a)) (fun r ↦ r.aliveAt (pos b)) rs
  have h3 : (rs.filter fun r ↦ r.aliveAt (pos b) || r.aliveAt (pos a))
      = rs.filter fun r ↦ r.aliveAt (pos a) || r.aliveAt (pos b) :=
    List.filter_congr fun r _ ↦ Bool.or_comm _ _
  rw [h3] at h1
  exact h1.symm.trans h2

/-- **SNP-13** The count walks the signed difference: no set is read to count the next cut's rows
from the last cut's. -/
theorem length_rows_delta (a b : γ) (rs : List (Gen κ β)) :
    ((cut b).rows pos rs).length + ((gone a b).rows pos rs).length
      = ((cut a).rows pos rs).length + ((come a b).rows pos rs).length := by
  simpa using sum_rows_delta (pos := pos) (fun _ ↦ (1 : ℕ)) a b rs

end Held

/-- **SNP-14** A row is alive at some cut of a family exactly when it is counted in one at least. -/
theorem countIn_pos_iff {F : List ℕ} {r : Gen κ β} :
    0 < countIn F r ↔ ∃ c ∈ F, r.aliveAt c = true :=
  List.countP_pos_iff

/-- **SNP-14** A row is alive at every cut of a family exactly when it is counted in each. -/
theorem countIn_eq_length_iff {F : List ℕ} {r : Gen κ β} :
    countIn F r = F.length ↔ ∀ c ∈ F, r.aliveAt c = true :=
  List.countP_eq_length

end Delta

/-! ### The rows removed, added and replaced -/

section Classes

variable {κ β : Type*} [DecidableEq κ]

/-- A replaced pair is a row of the first side and a row of its key on the second. -/
theorem mem_replacedOf {g c : List (Gen κ β)} {r r' : Gen κ β} (h : (r, r') ∈ replacedOf g c) :
    r ∈ g ∧ r' ∈ c ∧ r'.key = r.key := by
  obtain ⟨a, ha, hab⟩ := List.mem_filterMap.1 h
  obtain ⟨b, hb, hpair⟩ := Option.map_eq_some_iff.1 hab
  obtain ⟨rfl, rfl⟩ := Prod.mk.inj hpair
  exact ⟨ha, List.mem_of_find?_eq_some hb, by simpa using List.find?_some hb⟩

/-- **SNP-13** The first side of a signed difference is sorted in two: each of its rows is removed
or is the first of a replaced pair. -/
theorem mem_gone_iff {g c : List (Gen κ β)} {r : Gen κ β} :
    r ∈ g ↔ r ∈ removedOf g c ∨ ∃ r', (r, r') ∈ replacedOf g c := by
  constructor
  · intro hr
    cases hf : c.find? fun r' ↦ decide (r'.key = r.key) with
    | none =>
      refine Or.inl (List.mem_filter.2 ⟨hr, ?_⟩)
      rw [Bool.not_eq_true', Bool.eq_false_iff]
      intro hany
      obtain ⟨r', hr', hk⟩ := List.any_eq_true.1 hany
      exact absurd hk (by simpa using List.find?_eq_none.1 hf r' hr')
    | some r' => exact Or.inr ⟨r', List.mem_filterMap.2 ⟨r, hr, by rw [hf]; rfl⟩⟩
  · rintro (h | ⟨r', h⟩)
    · exact (List.mem_filter.1 h).1
    · exact (mem_replacedOf h).1

/-- **SNP-13** And not in both: a removed row is the first of no replaced pair. -/
theorem not_replacedOf_of_removedOf {g c : List (Gen κ β)} {r r' : Gen κ β}
    (h : r ∈ removedOf g c) : (r, r') ∉ replacedOf g c := by
  intro hp
  obtain ⟨-, hr', hk⟩ := mem_replacedOf hp
  have hnone := (List.mem_filter.1 h).2
  rw [Bool.not_eq_true', Bool.eq_false_iff] at hnone
  exact hnone (List.any_eq_true.2 ⟨r', hr', by simpa using hk⟩)

/-- **SNP-13** The second side is sorted in two as well, when it holds one row a key at most, as the
contents of a cut do: each of its rows is added or is the second of a replaced pair. -/
theorem mem_come_iff {g c : List (Gen κ β)}
    (hc : ∀ x ∈ c, ∀ y ∈ c, x.key = y.key → x = y) {r' : Gen κ β} :
    r' ∈ c ↔ r' ∈ addedOf g c ∨ ∃ r, (r, r') ∈ replacedOf g c := by
  constructor
  · intro hr'
    by_cases hany : (g.any fun r ↦ decide (r.key = r'.key)) = true
    · obtain ⟨r, hr, hk⟩ := List.any_eq_true.1 hany
      have hk' : r.key = r'.key := by simpa using hk
      cases hf : c.find? fun y ↦ decide (y.key = r.key) with
      | none => exact absurd hk'.symm (by simpa using List.find?_eq_none.1 hf r' hr')
      | some y =>
        have hy : y.key = r.key := by simpa using List.find?_some hf
        have hyr : y = r' := hc y (List.mem_of_find?_eq_some hf) r' hr' (hy.trans hk')
        exact Or.inr ⟨r, List.mem_filterMap.2 ⟨r, hr, by rw [hf, hyr]; rfl⟩⟩
    · exact Or.inl (List.mem_filter.2 ⟨hr', by simpa using hany⟩)
  · rintro (h | ⟨r, h⟩)
    · exact (List.mem_filter.1 h).1
    · exact (mem_replacedOf h).2.1

end Classes

/-! ### On the generations of a chain -/

section Generations

variable {κ β : Type*} [DecidableEq κ]

theorem event_closeAt (x : κ) (p : ℕ) (r : Gen κ β) : (closeAt x p r).event = r.event := by
  unfold closeAt
  split_ifs <;> rfl

theorem born_closeAt (x : κ) (p : ℕ) (r : Gen κ β) : (closeAt x p r).born = r.born := by
  unfold closeAt
  split_ifs <;> rfl

/-- A row's position is a position of its chain. -/
theorem born_of_mem_gens {l : List (κ × β)} {r : Gen κ β} (hr : r ∈ gens l) :
    1 ≤ r.born ∧ r.born ≤ l.length := by
  induction l using List.reverseRecOn generalizing r with
  | nil => simp [gens_nil] at hr
  | append_singleton l e ih =>
    rw [gens_append_singleton] at hr
    rw [List.length_append, List.length_singleton]
    rcases List.mem_append.1 hr with hr | hr
    · obtain ⟨r', hr', rfl⟩ := List.mem_map.1 hr
      rw [born_closeAt]
      have := ih hr'
      omega
    · rw [List.mem_singleton.1 hr]
      exact ⟨Nat.le_add_left _ _, le_rfl⟩

/-- **SNP-12** A row records the chain's event at its position: the rows of the generations are the
events of the chain, each with the stamp of its key's next event. -/
theorem getElem?_of_mem_gens {l : List (κ × β)} {r : Gen κ β} (hr : r ∈ gens l) :
    l[r.born - 1]? = some (r.key, r.val) := by
  induction l using List.reverseRecOn generalizing r with
  | nil => simp [gens_nil] at hr
  | append_singleton l e ih =>
    rw [gens_append_singleton] at hr
    rcases List.mem_append.1 hr with hr | hr
    · obtain ⟨r', hr', rfl⟩ := List.mem_map.1 hr
      have hb := born_of_mem_gens hr'
      rw [born_closeAt, closeAt_key, closeAt_val, List.getElem?_append_left (by omega)]
      exact ih hr'
    · rw [List.mem_singleton.1 hr]
      simp

/-- **SNP-12** The closing stamp of a row is the position of its key's next event, which lies past
the row's own. -/
theorem exists_next_of_mem_gens {l : List (κ × β)} {r : Gen κ β} (hr : r ∈ gens l) {d : ℕ}
    (hd : r.died = some d) : r.born < d ∧ ∃ r' ∈ gens l, r'.key = r.key ∧ r'.born = d := by
  induction l using List.reverseRecOn generalizing r with
  | nil => simp [gens_nil] at hr
  | append_singleton l e ih =>
    rw [gens_append_singleton] at hr ⊢
    rcases List.mem_append.1 hr with hr | hr
    · obtain ⟨r', hr', rfl⟩ := List.mem_map.1 hr
      have hb := born_of_mem_gens hr'
      by_cases hc : r'.key = e.1 ∧ r'.died = none
      · have hd' : l.length + 1 = d := by
          simpa [closeAt, hc] using hd
        subst hd'
        refine ⟨by rw [born_closeAt]; omega, ⟨e.1, e.2, l.length + 1, none⟩,
          List.mem_append_right _ (List.mem_singleton_self _), ?_, rfl⟩
        rw [closeAt_key]
        exact hc.1.symm
      · have hsame : closeAt e.1 (l.length + 1) r' = r' := by
          simp only [closeAt, hc, ↓reduceIte]
        rw [hsame] at hd ⊢
        obtain ⟨hlt, r'', hr'', hk, hbn⟩ := ih hr' hd
        exact ⟨hlt, closeAt e.1 (l.length + 1) r'',
          List.mem_append_left _ (List.mem_map_of_mem hr''), by rw [closeAt_key, hk],
          by rw [born_closeAt, hbn]⟩
    · rw [List.mem_singleton.1 hr] at hd
      simp at hd

/-- **SNP-12** A row of the generations is well formed: it is alive at its own position. -/
theorem proper_of_mem_gens {l : List (κ × β)} {r : Gen κ β} (hr : r ∈ gens l) : r.Proper :=
  fun _ hd ↦ (exists_next_of_mem_gens hr hd).1

/-- **SNP-17** The closing stamps are a function of the keys alone: a chain with its values
rewritten, key by key, has the generations of the chain with their values rewritten. An erasure that
keeps the key of a hole moves no position and no stamp. -/
theorem gens_map {β' : Type*} (f : κ × β → β') (l : List (κ × β)) :
    gens (l.map fun e ↦ (e.1, f e))
      = (gens l).map fun r ↦ ⟨r.key, f (r.key, r.val), r.born, r.died⟩ := by
  induction l using List.reverseRecOn with
  | nil => rfl
  | append_singleton l e ih =>
    rw [List.map_append, List.map_singleton, gens_append_singleton, gens_append_singleton, ih,
      List.length_map]
    simp only [landGen, List.map_append, List.map_map, List.map_singleton]
    congr 1
    refine List.map_congr_left fun r _ ↦ ?_
    simp only [Function.comp_apply, closeAt]
    split_ifs <;> rfl

theorem filter_key_contentAt (rs : List (Gen κ β)) (c : ℕ) (x : κ) :
    (contentAt rs c).filter (fun r ↦ decide (r.key = x)) = rs.filter (selects c x) := by
  unfold contentAt
  rw [List.filter_filter]
  rfl

/-- **SNP-12** What a cut holds is each key's state at the cut, once: the rows of a key alive at a
cut are the one row of its state there, or none. Every head at once is the read of every key. -/
theorem map_val_filter_key_contentAt (l : List (κ × β)) (c : ℕ) (x : κ) :
    ((contentAt (gens l) c).filter fun r ↦ decide (r.key = x)).map Gen.val
      = (stateAt l c x).toList := by
  rw [filter_key_contentAt, ← genRead_gens]
  have hlen := length_filter_selects_le_one l c x
  unfold genRead
  rw [← List.head?_filter]
  rcases hf : (gens l).filter (selects c x) with _ | ⟨r, _ | ⟨r', t⟩⟩
  · rfl
  · rfl
  · rw [hf] at hlen
    simp at hlen

/-- **SNP-12** A cut holds one row a key at most: two rows of one key alive at one cut are one row.
-/
theorem eq_of_key_eq_of_mem_contentAt {l : List (κ × β)} {c : ℕ} {r r' : Gen κ β}
    (hr : r ∈ contentAt (gens l) c) (hr' : r' ∈ contentAt (gens l) c) (hk : r.key = r'.key) :
    r = r' := by
  have hlen := length_filter_selects_le_one l c r'.key
  have h1 : r ∈ (gens l).filter (selects c r'.key) := by
    rw [← filter_key_contentAt]
    exact List.mem_filter.2 ⟨hr, by simpa using hk⟩
  have h2 : r' ∈ (gens l).filter (selects c r'.key) := by
    rw [← filter_key_contentAt]
    exact List.mem_filter.2 ⟨hr', by simp⟩
  rcases hf : (gens l).filter (selects c r'.key) with _ | ⟨a, _ | ⟨b, t⟩⟩
  · rw [hf] at h1
    exact absurd h1 List.not_mem_nil
  · rw [hf] at h1 h2
    rw [List.mem_singleton.1 h1, List.mem_singleton.1 h2]
  · rw [hf] at hlen
    simp at hlen

theorem gens_append_exists (l t : List (κ × β)) :
    ∃ (g : Gen κ β → Gen κ β) (new : List (Gen κ β)),
      gens (l ++ t) = (gens l).map g ++ new ∧
        (∀ r, (g r).event = r.event ∧
          ((g r).died = r.died ∨ (r.died = none ∧ ∃ d, (g r).died = some d ∧ l.length < d))) ∧
        ∀ r ∈ new, l.length < r.born := by
  induction t using List.reverseRecOn with
  | nil => exact ⟨id, [], by simp, fun r ↦ ⟨rfl, Or.inl rfl⟩, by simp⟩
  | append_singleton t e ih =>
    obtain ⟨g, new, hg, hprop, hnew⟩ := ih
    refine ⟨closeAt e.1 ((l ++ t).length + 1) ∘ g,
      new.map (closeAt e.1 ((l ++ t).length + 1)) ++ [⟨e.1, e.2, (l ++ t).length + 1, none⟩],
      ?_, fun r ↦ ⟨?_, ?_⟩, ?_⟩
    · rw [← List.append_assoc, gens_append_singleton, hg]
      simp [landGen, List.map_append, List.map_map]
    · rw [Function.comp_apply, event_closeAt, (hprop r).1]
    · rw [Function.comp_apply]
      by_cases hc : (g r).key = e.1 ∧ (g r).died = none
      · rcases (hprop r).2 with h | ⟨-, d, hd, -⟩
        · refine Or.inr ⟨h ▸ hc.2, (l ++ t).length + 1, by simp [closeAt, hc], ?_⟩
          rw [List.length_append]
          omega
        · rw [hd] at hc
          exact absurd hc.2 (by simp)
      · have hsame : closeAt e.1 ((l ++ t).length + 1) (g r) = g r := by
          simp only [closeAt, hc, ↓reduceIte]
        rw [hsame]
        exact (hprop r).2
    · intro r hr
      rcases List.mem_append.1 hr with hr | hr
      · obtain ⟨r', hr', rfl⟩ := List.mem_map.1 hr
        rw [born_closeAt]
        exact hnew r' hr'
      · rw [List.mem_singleton.1 hr, List.length_append]
        exact Nat.lt_succ_of_le (Nat.le_add_right _ _)

/-- **SNP-14** Append invariance for every set: a set whose cuts lie inside the chain holds, after
any growth of the chain, the events it held. The growth writes closing stamps into rows the set
holds, each past the old head, so the events are compared and not the stamps. -/
theorem Held.rows_gens_append {γ : Type*} {pos : γ → ℕ} {e : Held γ} {l : List (κ × β)}
    (t : List (κ × β)) (h : ∀ c ∈ e.atoms, pos c ≤ l.length) :
    (e.rows pos (gens (l ++ t))).map Gen.event = (e.rows pos (gens l)).map Gen.event := by
  obtain ⟨g, new, hg, hprop, hnew⟩ := gens_append_exists l t
  have hnone : new.filter (e.has pos) = [] := by
    rw [List.filter_eq_nil_iff]
    intro r hr hhas
    obtain ⟨c, hc, ha⟩ := Held.exists_atom_of_has hhas
    have h1 := (Gen.aliveAt_iff.1 ha).1
    have h2 := hnew r hr
    have h3 := h c hc
    omega
  have hsame : (e.has pos ∘ g) = e.has pos := funext fun r ↦
    Held.has_of_closed_later (congrArg (fun x ↦ x.2.2) (hprop r).1)
      ((hprop r).2.imp_right fun ⟨hn, d, hd, hlt⟩ ↦
        ⟨hn, d, hd, fun c hc ↦ lt_of_le_of_lt (h c hc) hlt⟩)
  unfold Held.rows
  rw [hg, List.filter_append, hnone, List.append_nil, List.filter_map, hsame, List.map_map]
  exact List.map_congr_left fun r _ ↦ (hprop r).1

/-- **SNP-14** So a set whose cuts lie at or under a cut inside the chain reads the prefix at that
cut and nothing after it: what a cut holds is a derived view of its read. -/
theorem Held.rows_gens_take {γ : Type*} {pos : γ → ℕ} {e : Held γ} {l : List (κ × β)} {c : ℕ}
    (hc : c ≤ l.length) (h : ∀ a ∈ e.atoms, pos a ≤ c) :
    (e.rows pos (gens l)).map Gen.event = (e.rows pos (gens (l.take c))).map Gen.event := by
  have hlen : (l.take c).length = c := by rw [List.length_take, Nat.min_eq_left hc]
  have := Held.rows_gens_append (e := e) (pos := pos) (l := l.take c) (l.drop c)
    fun a ha ↦ by rw [hlen]; exact h a ha
  rwa [List.take_append_drop] at this

theorem mem_drop_take_of_mem_gens {l : List (κ × β)} {r : Gen κ β} (hr : r ∈ gens l) {a b : ℕ}
    (ha : a < r.born) (hb : r.born ≤ b) : (r.key, r.val) ∈ (l.take b).drop a := by
  have hget := getElem?_of_mem_gens hr
  have hpos := born_of_mem_gens hr
  refine List.mem_of_getElem? (i := r.born - 1 - a) ?_
  rw [List.getElem?_drop, List.getElem?_take_of_lt (by omega),
    show a + (r.born - 1 - a) = r.born - 1 by omega]
  exact hget

/-- **SNP-13** The signed difference is sound for what did not change: every row on either side of
it belongs to a key that an event between the two cuts names. A key the events between do not name
holds at both cuts the row it held. -/
theorem key_mem_of_mem_delta {l : List (κ × β)} {a b : ℕ} (h : a ≤ b) {r : Gen κ β}
    (hr : r ∈ gens l)
    (hd : (Held.gone a b).has id r = true ∨ (Held.come a b).has id r = true) :
    r.key ∈ ((l.take b).drop a).map Prod.fst := by
  rcases hd with hd | hd
  · have hab : r.aliveAt a = true ∧ r.aliveAt b = false := by
      simpa [Held.gone, Held.has] using hd
    have hal := Gen.aliveAt_iff.1 hab.1
    rcases Gen.aliveAt_eq_false_iff.1 hab.2 with hlt | ⟨d, hdd, hle⟩
    · omega
    · obtain ⟨-, r', hr', hk, hbn⟩ := exists_next_of_mem_gens hr hdd
      have hmem := mem_drop_take_of_mem_gens hr' (a := a) (b := b)
        (by rw [hbn]; exact hal.2 d hdd) (by rw [hbn]; exact hle)
      exact List.mem_map.2 ⟨_, hmem, hk⟩
  · have hab : r.aliveAt b = true ∧ r.aliveAt a = false := by
      simpa [Held.come, Held.has] using hd
    have hbl := Gen.aliveAt_iff.1 hab.1
    rcases Gen.aliveAt_eq_false_iff.1 hab.2 with hlt | ⟨d, hdd, hle⟩
    · exact List.mem_map.2 ⟨_, mem_drop_take_of_mem_gens hr hlt hbl.1, rfl⟩
    · have := hbl.2 d hdd
      omega

/-- **SNP-17** A retire is a removal: when a key holds a version at one cut and its last event at
another is a retire, the row of the version is gone between the two, and no row of the key that came
carries a version. -/
theorem removed_of_retire {l : List (κ × Option β)} {a b : ℕ} {x : κ} {v : β}
    (ha : stateAt l a x = some (some v)) (hb : stateAt l b x = some none) :
    (∃ r ∈ gens l, r.key = x ∧ r.val = some v ∧ (Held.gone a b).has id r = true) ∧
      ∀ r ∈ gens l, r.key = x → (Held.come a b).has id r = true → r.val = none := by
  have h1 := map_val_filter_key_contentAt l a x
  have h2 := map_val_filter_key_contentAt l b x
  rw [ha] at h1
  rw [hb] at h2
  obtain ⟨ra, hra, hva⟩ := List.map_eq_singleton_iff.1 h1
  obtain ⟨rb, hrb, hvb⟩ := List.map_eq_singleton_iff.1 h2
  have hmema : ra ∈ (contentAt (gens l) a).filter fun r ↦ decide (r.key = x) := by
    rw [hra]
    exact List.mem_singleton_self _
  obtain ⟨hca, hka⟩ := List.mem_filter.1 hmema
  have hkey : ra.key = x := by simpa using hka
  have honly : ∀ r ∈ gens l, r.key = x → r.aliveAt b = true → r.val = none := by
    intro r hr hk hal
    have : r ∈ (contentAt (gens l) b).filter fun r ↦ decide (r.key = x) :=
      List.mem_filter.2 ⟨List.mem_filter.2 ⟨hr, hal⟩, by simpa using hk⟩
    rw [hrb, List.mem_singleton] at this
    rw [this, hvb]
  refine ⟨⟨ra, (List.mem_filter.1 hca).1, hkey, hva, ?_⟩, fun r hr hk hcome ↦ ?_⟩
  · have hala : ra.aliveAt a = true := (List.mem_filter.1 hca).2
    have hnb : ra.aliveAt b = false := by
      rw [Bool.eq_false_iff]
      intro hal
      have := honly ra (List.mem_filter.1 hca).1 hkey hal
      rw [hva] at this
      exact absurd this (by simp)
    simp [Held.gone, Held.has, hala, hnb]
  · have hal : r.aliveAt b = true := by
      simp only [Held.come, Held.has, id, Bool.and_eq_true] at hcome
      exact hcome.1
    exact honly r hr hk hal

/-- **SNP-17** No row of a chain with holes carries an erased value, so no set of its versions holds
one. -/
theorem not_erased_of_mem_gens_holes {E : κ × β → Bool} {l : List (κ × β)}
    {r : Gen κ (Option β)} {v : β} (hr : r ∈ gens (holes E l)) (hv : r.val = some v) :
    E (r.key, v) = false := by
  have hg := gens_map (fun e ↦ if E e then none else some e.2) l
  change gens (holes E l) = _ at hg
  rw [hg] at hr
  obtain ⟨r', -, rfl⟩ := List.mem_map.1 hr
  by_cases hE : E (r'.key, r'.val) = true
  · simp [hE] at hv
  · have hval : r'.val = v := by simpa [hE] using hv
    rw [← hval]
    simpa using hE

/-- **SNP-17** An erasure takes its own rows out of every set and changes no other: the versions a
set holds on the chain with holes are the rows it holds on the chain, less the erased ones, each at
the position it had. -/
theorem Held.rows_gens_holes {γ : Type*} {pos : γ → ℕ} (e : Held γ) (E : κ × β → Bool)
    (l : List (κ × β)) :
    ((e.rows pos (gens (holes E l))).filter Gen.isVersion).map Gen.event
      = ((e.rows pos (gens l)).filter fun r ↦ !E (r.key, r.val)).map
        fun r ↦ (r.key, some r.val, r.born) := by
  have hg := gens_map (fun e ↦ if E e then none else some e.2) l
  change gens (holes E l) = _ at hg
  unfold Held.rows
  rw [hg, List.filter_map, List.filter_map, List.map_map, List.filter_filter]
  have h1 : ∀ r : Gen κ β, r ∈ gens l →
      ((Gen.isVersion ∘ fun r : Gen κ β ↦
          (⟨r.key, if E (r.key, r.val) then none else some r.val, r.born, r.died⟩ :
            Gen κ (Option β))) r
        && (e.has pos ∘ fun r : Gen κ β ↦
          (⟨r.key, if E (r.key, r.val) then none else some r.val, r.born, r.died⟩ :
            Gen κ (Option β))) r)
      = (!E (r.key, r.val) && e.has pos r) := by
    intro r _
    have hi : e.has pos (⟨r.key, if E (r.key, r.val) then none else some r.val, r.born,
        r.died⟩ : Gen κ (Option β)) = e.has pos r :=
      Held.has_eq_of_interval e rfl rfl
    simp only [Function.comp_apply, hi, Gen.isVersion]
    cases E (r.key, r.val) <;> rfl
  rw [List.filter_congr h1, List.filter_filter]
  refine List.map_congr_left fun r hr ↦ ?_
  have hE : E (r.key, r.val) = false := by
    have := (List.mem_filter.1 hr).2
    simp only [Bool.and_eq_true, Bool.not_eq_true'] at this
    exact this.1
  simp [Gen.event, hE]

end Generations

/-! ### On a store: the grant and the positions -/

section Store

variable {K α β κ γ : Type*}

/-- **SNP-16** A narrower grant's restriction of a family of chains is its restriction of a wider
grant's. -/
theorem restrict_narrow {G G' : K → Prop} [DecidablePred G] [DecidablePred G']
    {p p' : α → Bool} (hG : ∀ k, G k → G' k) (hp : ∀ a, p a = true → p' a = true)
    (t : Store K α) : restrict G p t = restrict G p (restrict G' p' t) := by
  funext k
  by_cases h : G k
  · have h' := hG k h
    simp only [restrict, h, h', ↓reduceIte, List.filter_filter]
    refine List.filter_congr fun a _ ↦ ?_
    cases hpa : p a
    · rfl
    · simp [hp a hpa]
  · simp [restrict, h]

/-- **SNP-16** Every set commutes with the grant: read on the chains the grant shows, it is the
grant's restriction of the set read on the whole store. The grant may be applied before the
operators or after them. -/
theorem Held.across_restrict (G : K → Prop) [DecidablePred G] (p : Gen κ β → Bool)
    (pos : γ → Cut K) (e : Held γ) (R : K → List (Gen κ β)) :
    e.across pos (restrict G p R) = restrict G p (e.across pos R) := by
  funext k
  by_cases h : G k
  · simp only [Held.across, restrict, h, ↓reduceIte, List.filter_filter]
    exact List.filter_congr fun r _ ↦ Bool.and_comm _ _
  · simp [Held.across, restrict, h]

/-- **SNP-16** Noninterference for every set: under a grant a set reads only the chains the grant
names, and of its cuts only their positions on them. Two stores that agree on those chains, at cuts
that agree on them, give one answer. -/
theorem Held.across_congr (G : K → Prop) [DecidablePred G] (p : Gen κ β → Bool)
    {pos pos' : γ → Cut K} {e : Held γ} {R R' : K → List (Gen κ β)}
    (hR : ∀ k, G k → R k = R' k) (hpos : ∀ c ∈ e.atoms, ∀ k, G k → pos c k = pos' c k) :
    restrict G p (e.across pos R) = restrict G p (e.across pos' R') := by
  funext k
  by_cases h : G k
  · simp only [restrict, Held.across, h, ↓reduceIte, hR k h]
    congr 1
    exact List.filter_congr fun r _ ↦ Held.has_congr (fun c hc ↦ hpos c hc k h) r
  · simp [restrict, h]

/-- **SNP-16** A narrower grant's set is the restriction of a wider grant's. -/
theorem Held.across_narrow {G G' : K → Prop} [DecidablePred G] [DecidablePred G']
    {p p' : Gen κ β → Bool} (hG : ∀ k, G k → G' k) (hp : ∀ a, p a = true → p' a = true)
    (pos : γ → Cut K) (e : Held γ) (R : K → List (Gen κ β)) :
    restrict G p (e.across pos R) = restrict G p (restrict G' p' (e.across pos R)) :=
  restrict_narrow hG hp _

/-- **SNP-16** Under a grant a set names no chain the grant does not name. -/
theorem Held.across_of_not (G : K → Prop) [DecidablePred G] (p : Gen κ β → Bool)
    (pos : γ → Cut K) (e : Held γ) (R : K → List (Gen κ β)) {k : K} (h : ¬G k) :
    restrict G p (e.across pos R) k = [] := by
  simp [restrict, h]

/-- **SNP-16** The events between two cuts under a grant that names whole chains: restricting to the
chains commutes with the read between, as it does with the read at a cut. -/
theorem restrict_readBetween (G : K → Prop) [DecidablePred G] (s : Store K α) (a b : Cut K) :
    restrict G (fun _ ↦ true) (readBetween s a b)
      = readBetween (restrict G (fun _ ↦ true) s) a b := by
  funext k
  by_cases h : G k <;> simp [restrict, readBetween, h]

/-- **SNP-15** Contents against positions, on a store: what either of two cuts holds is what their
join holds, with the rows closed between their meet and their join. -/
theorem Held.has_union_cut (a b : Cut K) (k : K) (r : Gen κ β) :
    ((Held.cut a).union (Held.cut b)).has (fun c ↦ c k) r
      = ((Held.cut (a ⊔ b)).union (Held.gone (a ⊓ b) (a ⊔ b))).has (fun c ↦ c k) r :=
  Gen.aliveAt_or_eq_sup r (a k) (b k)

/-- **SNP-15** And what both hold is what their meet and their join both hold, the two cuts taken
chain by chain in their order. -/
theorem Held.has_inter_cut (a b : Cut K) (k : K) (r : Gen κ β) :
    ((Held.cut a).inter (Held.cut b)).has (fun c ↦ c k) r
      = (Held.kept (a ⊓ b) (a ⊔ b)).has (fun c ↦ c k) r :=
  Gen.aliveAt_and_eq_inf_sup r (a k) (b k)

/-- **SNP-11** The meet and the join of two cuts that are read as asked are read as asked: the cuts
that are consistent and served are closed under both, the consistency by CLK-2. -/
theorem resolvesIn_sup {R : K → ℕ → K → ℕ → Prop} {S : K → Set ℕ} {a b : Cut K}
    (ha : Consistent R a) (hb : Consistent R b) (hSa : a ∈ servedCuts S)
    (hSb : b ∈ servedCuts S) : ResolvesIn R S (a ⊔ b) (a ⊔ b) :=
  resolvesIn_self (ha.sup hb) ((servedCuts S).supClosed hSa hSb)

/-- **SNP-11** The same for the meet. -/
theorem resolvesIn_inf {R : K → ℕ → K → ℕ → Prop} {S : K → Set ℕ} {a b : Cut K}
    (ha : Consistent R a) (hb : Consistent R b) (hSa : a ∈ servedCuts S)
    (hSb : b ∈ servedCuts S) : ResolvesIn R S (a ⊓ b) (a ⊓ b) :=
  resolvesIn_self (ha.inf hb) ((servedCuts S).infClosed hSa hSb)

/-- **SNP-11** The read at the join of two cuts is, chain by chain, the read at the later of the
two. -/
theorem readAt_sup (s : Store K α) (a b : Cut K) (k : K) :
    readAt s (a ⊔ b) k = if a k ≤ b k then readAt s b k else readAt s a k := by
  by_cases h : a k ≤ b k
  · simp only [h, ↓reduceIte]
    change (s k).take (a k ⊔ b k) = (s k).take (b k)
    rw [sup_of_le_right h]
  · simp only [h, ↓reduceIte]
    change (s k).take (a k ⊔ b k) = (s k).take (a k)
    rw [sup_of_le_left (not_le.1 h).le]

/-- **SNP-11** The read at the meet of two cuts is, chain by chain, the read at the earlier of the
two. -/
theorem readAt_inf (s : Store K α) (a b : Cut K) (k : K) :
    readAt s (a ⊓ b) k = if a k ≤ b k then readAt s a k else readAt s b k := by
  by_cases h : a k ≤ b k
  · simp only [h, ↓reduceIte]
    change (s k).take (a k ⊓ b k) = (s k).take (a k)
    rw [inf_of_le_left h]
  · simp only [h, ↓reduceIte]
    change (s k).take (a k ⊓ b k) = (s k).take (b k)
    rw [inf_of_le_right (not_le.1 h).le]

/-- **SNP-11** The read at the empty cut is empty. -/
theorem readAt_bot (s : Store K α) : readAt s ⊥ = fun _ ↦ [] := by
  funext k
  simp [readAt]

/-- **SNP-11** The meet distributes over the join, and so do the reads: the cuts are a distributive
lattice. -/
theorem readAt_inf_sup (s : Store K α) (a b c : Cut K) :
    readAt s (a ⊓ (b ⊔ c)) = readAt s (a ⊓ b ⊔ a ⊓ c) :=
  congrArg (readAt s) (inf_sup_left a b c)

theorem readBetween_of_le (s : Store K α) {a b : Cut K} {k : K} (h : b k ≤ a k) :
    readBetween s a b k = [] := by
  refine List.drop_of_length_le ?_
  rw [List.length_take]
  exact (Nat.min_le_left _ _).trans h

/-- **SNP-11** The difference of two cuts on positions, the events the second holds and the first
does not, is the read between their meet and the second. -/
theorem readBetween_inf_left (s : Store K α) (a b : Cut K) :
    readBetween s (a ⊓ b) b = readBetween s a b := by
  funext k
  rcases le_total (a k) (b k) with h | h
  · change ((s k).take (b k)).drop (a k ⊓ b k) = ((s k).take (b k)).drop (a k)
    rw [inf_of_le_left h]
  · rw [readBetween_of_le s h]
    refine List.drop_of_length_le ?_
    change ((s k).take (b k)).length ≤ a k ⊓ b k
    rw [inf_of_le_right h, List.length_take]
    exact Nat.min_le_left _ _

/-- **SNP-11** And the read between the first and their join. -/
theorem readBetween_sup_right (s : Store K α) (a b : Cut K) :
    readBetween s a (a ⊔ b) = readBetween s a b := by
  funext k
  rcases le_total (a k) (b k) with h | h
  · change ((s k).take (a k ⊔ b k)).drop (a k) = ((s k).take (b k)).drop (a k)
    rw [sup_of_le_right h]
  · rw [readBetween_of_le s h]
    refine List.drop_of_length_le ?_
    change ((s k).take (a k ⊔ b k)).length ≤ a k
    rw [sup_of_le_left h, List.length_take]
    exact Nat.min_le_left _ _

/-- **SNP-11** The symmetric difference of two cuts on positions, the events exactly one of them
holds, is the read between their meet and their join: on each chain, one of the two differences. -/
theorem readBetween_inf_sup (s : Store K α) (a b : Cut K) (k : K) :
    readBetween s (a ⊓ b) (a ⊔ b) k = readBetween s a b k ++ readBetween s b a k := by
  rcases le_total (a k) (b k) with h | h
  · rw [readBetween_of_le s h, List.append_nil]
    change ((s k).take (a k ⊔ b k)).drop (a k ⊓ b k) = ((s k).take (b k)).drop (a k)
    rw [sup_of_le_right h, inf_of_le_left h]
  · rw [readBetween_of_le s h, List.nil_append]
    change ((s k).take (a k ⊔ b k)).drop (a k ⊓ b k) = ((s k).take (a k)).drop (b k)
    rw [sup_of_le_left h, inf_of_le_right h]

theorem mem_cutsIn {s : Store K α} {c : Cut K} : c ∈ cutsIn s ↔ c ≤ head s := Iff.rfl

/-- **SNP-11** The empty cut is inside every store: the bottom. -/
theorem bot_mem_cutsIn (s : Store K α) : (⊥ : Cut K) ∈ cutsIn s :=
  show (⊥ : Cut K) ≤ head s from bot_le

/-- **SNP-11** The head is inside the store, and every cut inside the store lies under it: the top.
-/
theorem head_mem_cutsIn (s : Store K α) : head s ∈ cutsIn s := le_refl (head s)

/-- **SNP-11** The head moves and no cut leaves: the cuts inside a store are inside every extension
of it. -/
theorem cutsIn_mono {s s' : Store K α} (h : Extends s s') : cutsIn s ≤ cutsIn s' :=
  fun _ hc ↦ le_trans hc h.head_le

/-- **SNP-14** A function of two cuts' reads is append invariant. -/
theorem combine_grow (f : Store K α → Store K α → β) {s : Store K α} (t : Store K α)
    {a b : Cut K} (ha : a ≤ head s) (hb : b ≤ head s) :
    combine f (grow s t) a b = combine f s a b := by
  unfold combine
  rw [readAt_grow t ha, readAt_grow t hb]

/-- **SNP-14** A measure at each cut of a family is append invariant. -/
theorem series_grow (D : Store K α → β) {s : Store K α} (t : Store K α) {F : List (Cut K)}
    (hF : ∀ c ∈ F, c ≤ head s) : series D (grow s t) F = series D s F :=
  List.map_congr_left fun c hc ↦ appendInvariant_view D s t c (hF c hc)

/-- **SNP-14** A fold over a family of cuts is append invariant. -/
theorem foldOver_grow (g : β → Store K α → β) (init : β) {s : Store K α} (t : Store K α)
    {F : List (Cut K)} (hF : ∀ c ∈ F, c ≤ head s) :
    foldOver g init (grow s t) F = foldOver g init s F := by
  unfold foldOver
  induction F generalizing init with
  | nil => rfl
  | cons c F ih =>
    rw [List.foldl_cons, List.foldl_cons, readAt_grow t (hF c List.mem_cons_self),
      ih _ fun d hd ↦ hF d (List.mem_cons_of_mem _ hd)]

/-- **SNP-11** The difference of two cuts on positions is a function of their two reads: the events
of the second read past the length of the first. -/
theorem readBetween_eq_combine (s : Store K α) (a b : Cut K) :
    readBetween s a b = combine (fun x y k ↦ (y k).drop (x k).length) s a b := by
  funext k
  change ((s k).take (b k)).drop (a k) = ((s k).take (b k)).drop ((s k).take (a k)).length
  rw [List.length_take]
  rcases le_total (a k) (s k).length with h | h
  · rw [Nat.min_eq_left h]
  · rw [Nat.min_eq_right h, List.drop_of_length_le ((List.length_take_le' _ _).trans h),
      List.drop_of_length_le (List.length_take_le' _ _)]

end Store

namespace Witness

/-- **SNP-15** The control for the two meanings of union: on contents it does not follow the join of
the positions. One key written twice: the union of what the two cuts hold has both rows, and the
join of the two cuts holds the later one alone. -/
theorem union_ne_join :
    ∃ (l : List (Unit × ℕ)) (a b : ℕ),
      (((Held.cut a).union (Held.cut b)).rows id (gens l)).map Gen.val = [0, 1] ∧
        ((Held.cut (a ⊔ b)).rows id (gens l)).map Gen.val = [1] :=
  ⟨[((), 0), ((), 1)], 1, 2, by decide, by decide⟩

/-- **SNP-12** The control for contiguity: it is a law of rows, and a value has none. A key that
returns to a value it held before holds it at two cuts and not between them. -/
theorem value_not_contiguous :
    ∃ l : List (Unit × ℕ),
      stateAt l 1 () = some 0 ∧ stateAt l 3 () = some 0 ∧ stateAt l 2 () = some 1 :=
  ⟨[((), 0), ((), 1), ((), 0)], by decide, by decide, by decide⟩

/-- **SNP-13** The control for the composition of signed differences: through a cut that does not
lie between the two it fails. A row alive at `a` and `c` and not at `b` is come from `b` to `c` and
is on neither side from `a` to `c`. -/
theorem delta_through_outside :
    ∃ (r : Gen Unit Unit) (a b c : ℕ),
      (Held.come a c).has id r = false ∧
        (((Held.come a b).diff (Held.gone b c)).union (Held.come b c)).has id r = true :=
  ⟨⟨(), (), 1, none⟩, 1, 0, 1, by decide, by decide⟩

/-- **SNP-16** The control for the row's own test: applied to the chain before its generations are
computed, it moves the positions, and a cut then holds an event from after it. -/
theorem filter_before_gens :
    ∃ (l : List (ℕ × ℕ)) (p : ℕ × ℕ → Bool) (c : ℕ),
      (contentAt (gens (l.filter p)) c).map Gen.val = [8] ∧
        ((contentAt (gens l) c).filter fun r ↦ p (r.key, r.val)).map Gen.val = [] :=
  ⟨[(0, 7), (1, 8)], fun e ↦ e.1 != 0, 1, by decide, by decide⟩

/-- **SNP-13** The control for the signed difference against the events between two cuts: a key
landed and retired between them is named by the events and is on neither side of the difference. -/
theorem changed_not_delta :
    ∃ (l : List (Unit × Option ℕ)) (a b : ℕ),
      () ∈ ((l.take b).drop a).map Prod.fst ∧
        ((Held.gone a b).rows id ((gens l).filter Gen.isVersion)).length = 0 ∧
        ((Held.come a b).rows id ((gens l).filter Gen.isVersion)).length = 0 :=
  ⟨[((), some 0), ((), none)], 0, 2, by decide, by decide, by decide⟩

/-- **SNP-14** The control for the missing complement: the rows a cut does not hold are not append
invariant, since every later row is among them. -/
theorem complement_grows :
    ∃ (l t : List (Unit × ℕ)) (c : ℕ), c ≤ l.length ∧
      ((gens (l ++ t)).filter fun r ↦ !r.aliveAt c).length
        ≠ ((gens l).filter fun r ↦ !r.aliveAt c).length :=
  ⟨[], [((), 0)], 0, by decide, by decide⟩

end Witness

end Palace.Snapshot
