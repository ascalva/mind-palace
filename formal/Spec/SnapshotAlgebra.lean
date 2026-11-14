module

public import Palace.SnapshotAlgebra.Defs
public import Mathlib.Data.List.Induction
public import Mathlib.Data.List.ReduceOption
public import Mathlib.Order.Lattice
public import Mathlib.Order.Lattice.Nat
public import Mathlib.Order.Sublattice

/-!
# The algebra of cuts: the statements

SNP-11 to SNP-17 (`docs/LAWS.md`, XVI): the lattice of cuts, a row's interval, the signed
difference of two cuts, the closure of the sets of rows a cut's contents generate, contents
against positions, the grant, and erasure and retire, over the model of
`Palace/SnapshotAlgebra/Defs.lean` and `Palace/Snapshot/Defs.lean`: a cut as one position a
chain, the cuts inside a store as a lattice, the rows of a chain of keyed writes kept by
generation and alive at a cut, a set of rows as an expression over the contents of cuts with
union, intersection and difference and no complement, the two sides of a signed difference and
their rows sorted by key, a family of cuts, and the interface an operator reads a cut through.
The controls that are theorems are among the statements; the other controls are refuted attacks
in `PalaceTest/SnapshotAlgebra.lean`. What they leave out: the stores' SQL and the statements a
set compiles to, the class a chain holds, the kinds of the landing log's rows beyond a row that
carries a version and one that does not, and the graph a cut stands for beyond its rows, which
stage SN-4 of dn-temporal-snapshot builds.

These are the laws of `Palace/SnapshotAlgebra.lean` as the ledger cites them, each with its
proof left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

namespace Palace.Snapshot

/-! ### A row lives on an interval -/

section Interval

variable {κ β : Type*}

/-- **SNP-12** A row is alive at a cut from its position up to, and not at, its closing stamp. -/
theorem Gen.aliveAt_iff {r : Gen κ β} {c : ℕ} :
    r.aliveAt c = true ↔ r.born ≤ c ∧ ∀ d, r.died = some d → c < d :=
  sorry

/-- **SNP-12** Contiguity: a row alive at two cuts is alive at every cut between them. A row lives
on one interval of its chain's positions. -/
theorem Gen.aliveAt_of_between {r : Gen κ β} {a b c : ℕ} (ha : r.aliveAt a = true)
    (hb : r.aliveAt b = true) (hac : a ≤ c) (hcb : c ≤ b) : r.aliveAt c = true :=
  sorry

/-- **SNP-12** What the later of two cuts holds and the earlier does not: the rows stored after the
earlier cut and alive at the later one. -/
theorem Gen.aliveAt_and_not {r : Gen κ β} {a b : ℕ} (h : a ≤ b) :
    (r.aliveAt b && !r.aliveAt a) = (decide (a < r.born) && r.aliveAt b) :=
  sorry

/-- **SNP-12** What the earlier of two cuts holds and the later does not: the rows alive at the
earlier cut whose closing stamp is at or under the later one. -/
theorem Gen.aliveAt_and_not' {r : Gen κ β} {a b : ℕ} (h : a ≤ b) :
    (r.aliveAt a && !r.aliveAt b) = (r.aliveAt a && r.died.any fun d ↦ decide (d ≤ b)) :=
  sorry

/-- **SNP-12** What two cuts both hold: the rows stored at or under the earlier cut whose closing
stamp is absent or past the later one. -/
theorem Gen.aliveAt_and {r : Gen κ β} {a b : ℕ} (h : a ≤ b) :
    (r.aliveAt a && r.aliveAt b)
      = (decide (r.born ≤ a) && r.died.all fun d ↦ decide (b < d)) :=
  sorry

/-- **SNP-12** A row is alive at every cut of a family exactly when it is alive at the family's
least cut and at its greatest. -/
theorem Gen.forall_aliveAt_iff {r : Gen κ β} {F : List ℕ} {lo hi : ℕ} (hlo : lo ∈ F)
    (hhi : hi ∈ F) (hF : ∀ c ∈ F, lo ≤ c ∧ c ≤ hi) :
    (∀ c ∈ F, r.aliveAt c = true) ↔ r.aliveAt lo = true ∧ r.aliveAt hi = true :=
  sorry

/-- **SNP-12** A well-formed row is alive at some cut of a range of positions exactly when it was
stored at or under the range's end and not closed at or under its start. -/
theorem Gen.exists_aliveAt_iff {r : Gen κ β} (hr : r.Proper) {lo hi : ℕ} (h : lo ≤ hi) :
    (∃ c, lo ≤ c ∧ c ≤ hi ∧ r.aliveAt c = true)
      ↔ r.born ≤ hi ∧ ∀ d, r.died = some d → lo < d :=
  sorry

/-- **SNP-15** What two cuts both hold is what their meet and their join both hold. -/
theorem Gen.aliveAt_and_eq_inf_sup (r : Gen κ β) (a b : ℕ) :
    (r.aliveAt a && r.aliveAt b) = (r.aliveAt (a ⊓ b) && r.aliveAt (a ⊔ b)) :=
  sorry

/-- **SNP-15** What either of two cuts holds is what their join holds and what was closed between
their meet and their join. -/
theorem Gen.aliveAt_or_eq_sup (r : Gen κ β) (a b : ℕ) :
    (r.aliveAt a || r.aliveAt b)
      = (r.aliveAt (a ⊔ b) || (r.aliveAt (a ⊓ b) && !r.aliveAt (a ⊔ b))) :=
  sorry

/-- **SNP-15** A row that is never closed is alive at the join of two cuts exactly when it is alive
at one of them. -/
theorem Gen.aliveAt_sup_of_open {r : Gen κ β} (hr : r.died = none) (a b : ℕ) :
    r.aliveAt (a ⊔ b) = (r.aliveAt a || r.aliveAt b) :=
  sorry

/-- **SNP-15** And at their meet exactly when it is alive at both. -/
theorem Gen.aliveAt_inf_of_open {r : Gen κ β} (hr : r.died = none) (a b : ℕ) :
    r.aliveAt (a ⊓ b) = (r.aliveAt a && r.aliveAt b) :=
  sorry

end Interval

/-! ### Sets of rows, named and not read -/

section Expressions

variable {κ β γ : Type*} {pos : γ → ℕ}

namespace Held

/-- **SNP-14** The union read is the union of the reads. -/
theorem mem_rows_union {p q : Held γ} {rs : List (Gen κ β)} {r : Gen κ β} :
    r ∈ (p.union q).rows pos rs ↔ r ∈ p.rows pos rs ∨ r ∈ q.rows pos rs :=
  sorry

/-- **SNP-14** The intersection read is the intersection of the reads. -/
theorem mem_rows_inter {p q : Held γ} {rs : List (Gen κ β)} {r : Gen κ β} :
    r ∈ (p.inter q).rows pos rs ↔ r ∈ p.rows pos rs ∧ r ∈ q.rows pos rs :=
  sorry

/-- **SNP-14** The difference read is the difference of the reads. -/
theorem mem_rows_diff {p q : Held γ} {rs : List (Gen κ β)} {r : Gen κ β} :
    r ∈ (p.diff q).rows pos rs ↔ r ∈ p.rows pos rs ∧ r ∉ q.rows pos rs :=
  sorry

/-- **SNP-14** What exactly one of two sets holds is what either holds and not both. -/
theorem has_symm (p q : Held γ) (r : Gen κ β) :
    (symm p q).has pos r = ((p.union q).diff (p.inter q)).has pos r :=
  sorry

/-- **SNP-14** Intersection distributes over union. -/
theorem has_inter_union (p q t : Held γ) (r : Gen κ β) :
    (p.inter (q.union t)).has pos r = ((p.inter q).union (p.inter t)).has pos r :=
  sorry

/-- **SNP-14** A set less what it holds and another does not is what both hold. -/
theorem has_diff_diff (p q : Held γ) (r : Gen κ β) :
    (p.diff (p.diff q)).has pos r = (p.inter q).has pos r :=
  sorry

/-- **SNP-14** Whether a row is in a set is a function of the row's position and its closing stamp:
two rows with one interval, whatever their keys and values, are in the same sets. Combining sets
reads no row. -/
theorem has_eq_of_interval {κ' β' : Type*} (e : Held γ) {r : Gen κ β} {r' : Gen κ' β'}
    (hb : r.born = r'.born) (hd : r.died = r'.died) : e.has pos r = e.has pos r' :=
  sorry

/-- **SNP-14** A set lies inside the contents of the cuts it names: a row in it is alive at one of
them. There is no complement. -/
theorem exists_atom_of_has {e : Held γ} {r : Gen κ β} (h : e.has pos r = true) :
    ∃ c ∈ e.atoms, r.aliveAt (pos c) = true :=
  sorry

/-- **SNP-14** A row's own test, one that does not depend on a cut, commutes with every set: the
rows of a set that pass the test are the set read on the rows that pass it. -/
theorem rows_filter (e : Held γ) (p : Gen κ β → Bool) (rs : List (Gen κ β)) :
    (e.rows pos rs).filter p = e.rows pos (rs.filter p) :=
  sorry

end Held

end Expressions

/-! ### The signed difference of two cuts, and a family of cuts -/

section Delta

variable {κ β γ : Type*} {pos : γ → ℕ}

namespace Held

/-- **SNP-13** What the later cut holds and the earlier does not, as one range read: the rows stored
after the earlier cut and alive at the later one. -/
theorem has_come {a b : γ} (h : pos a ≤ pos b) (r : Gen κ β) :
    (come a b).has pos r = (decide (pos a < r.born) && r.aliveAt (pos b)) :=
  sorry

/-- **SNP-13** What the earlier cut holds and the later does not, as one range read: the rows alive
at the earlier cut whose closing stamp is at or under the later one. -/
theorem has_gone {a b : γ} (h : pos a ≤ pos b) (r : Gen κ β) :
    (gone a b).has pos r = (r.aliveAt (pos a) && r.died.any fun d ↦ decide (d ≤ pos b)) :=
  sorry

/-- **SNP-14** What both cuts hold, as one range read: the rows stored at or under the earlier cut
and not closed at or under the later one. -/
theorem has_kept {a b : γ} (h : pos a ≤ pos b) (r : Gen κ β) :
    (kept a b).has pos r
      = (decide (r.born ≤ pos a) && r.died.all fun d ↦ decide (pos b < d)) :=
  sorry

/-- **SNP-13** The signed difference applied: what the second cut holds is what the first holds,
less the rows gone, with the rows come. The result of a difference is an operand again. -/
theorem has_cut_eq_apply (a b : γ) (r : Gen κ β) :
    (cut b).has pos r = (((cut a).diff (gone a b)).union (come a b)).has pos r :=
  sorry

/-- **SNP-13** Signed differences compose along cuts in order: the rows come from `a` to `c` are the
rows come from `a` to `b` that did not go from `b` to `c`, with the rows come from `b` to `c`. It
holds when `b` lies between `a` and `c` on the chain, in either direction. -/
theorem has_come_trans {a b c : γ}
    (h : (pos a ≤ pos b ∧ pos b ≤ pos c) ∨ (pos c ≤ pos b ∧ pos b ≤ pos a)) (r : Gen κ β) :
    (come a c).has pos r = (((come a b).diff (gone b c)).union (come b c)).has pos r :=
  sorry

/-- **SNP-13** And the rows gone from `a` to `c` are the rows gone from `a` to `b`, with the rows
gone from `b` to `c` that had not come from `a` to `b`. -/
theorem has_gone_trans {a b c : γ}
    (h : (pos a ≤ pos b ∧ pos b ≤ pos c) ∨ (pos c ≤ pos b ∧ pos b ≤ pos a)) (r : Gen κ β) :
    (gone a c).has pos r = ((gone a b).union ((gone b c).diff (come a b))).has pos r :=
  sorry

/-- **SNP-13** A row that came between `a` and `b` and went between `b` and `c` is on neither side
of the difference from `a` to `c`: what a composition cancels. -/
theorem has_trans_of_transient {a b c : γ} {r : Gen κ β} (h1 : (come a b).has pos r = true)
    (h2 : (gone b c).has pos r = true) :
    (come a c).has pos r = false ∧ (gone a c).has pos r = false :=
  sorry

/-- **SNP-13** The sizes of the differences obey the triangle inequality: a row gone from `a` to `c`
is gone from `a` to `b` or from `b` to `c`, whatever `b`. -/
theorem has_gone_triangle (a b c : γ) {r : Gen κ β} (h : (gone a c).has pos r = true) :
    (gone a b).has pos r = true ∨ (gone b c).has pos r = true :=
  sorry

/-- **SNP-14** What every cut of a family holds: the rows alive at each of them. -/
theorem has_all {c : γ} {F : List γ} {r : Gen κ β} :
    (all c F).has pos r = true ↔ ∀ d ∈ c :: F, r.aliveAt (pos d) = true :=
  sorry

/-- **SNP-14** What some cut of a family holds: the rows alive at one of them. -/
theorem has_any {c : γ} {F : List γ} {r : Gen κ β} :
    (any c F).has pos r = true ↔ ∃ d ∈ c :: F, r.aliveAt (pos d) = true :=
  sorry

/-- **SNP-14** What every cut of a family holds is what its least and its greatest cut both hold:
two positions, whatever the size of the family. -/
theorem has_all_eq_kept {c lo hi : γ} {F : List γ} (hlo : lo ∈ c :: F) (hhi : hi ∈ c :: F)
    (hF : ∀ d ∈ c :: F, pos lo ≤ pos d ∧ pos d ≤ pos hi) (r : Gen κ β) :
    (all c F).has pos r = (kept lo hi).has pos r :=
  sorry

/-- **SNP-13** A measure that is a sum over the rows walks the signed difference: the sum over what
the second cut holds, with the sum over the rows gone, is the sum over what the first holds, with
the sum over the rows come. A count is the case of the measure one. -/
theorem sum_rows_delta {M : Type*} [AddCommMonoid M] (w : Gen κ β → M) (a b : γ)
    (rs : List (Gen κ β)) :
    (((cut b).rows pos rs).map w).sum + (((gone a b).rows pos rs).map w).sum
      = (((cut a).rows pos rs).map w).sum + (((come a b).rows pos rs).map w).sum :=
  sorry

/-- **SNP-13** The count walks the signed difference: no set is read to count the next cut's rows
from the last cut's. -/
theorem length_rows_delta (a b : γ) (rs : List (Gen κ β)) :
    ((cut b).rows pos rs).length + ((gone a b).rows pos rs).length
      = ((cut a).rows pos rs).length + ((come a b).rows pos rs).length :=
  sorry

end Held

/-- **SNP-14** A row is alive at some cut of a family exactly when it is counted in one at least. -/
theorem countIn_pos_iff {F : List ℕ} {r : Gen κ β} :
    0 < countIn F r ↔ ∃ c ∈ F, r.aliveAt c = true :=
  sorry

/-- **SNP-14** A row is alive at every cut of a family exactly when it is counted in each. -/
theorem countIn_eq_length_iff {F : List ℕ} {r : Gen κ β} :
    countIn F r = F.length ↔ ∀ c ∈ F, r.aliveAt c = true :=
  sorry

end Delta

/-! ### The rows removed, added and replaced -/

section Classes

variable {κ β : Type*} [DecidableEq κ]

/-- **SNP-13** The first side of a signed difference is sorted in two: each of its rows is removed
or is the first of a replaced pair. -/
theorem mem_gone_iff {g c : List (Gen κ β)} {r : Gen κ β} :
    r ∈ g ↔ r ∈ removedOf g c ∨ ∃ r', (r, r') ∈ replacedOf g c :=
  sorry

/-- **SNP-13** And not in both: a removed row is the first of no replaced pair. -/
theorem not_replacedOf_of_removedOf {g c : List (Gen κ β)} {r r' : Gen κ β}
    (h : r ∈ removedOf g c) : (r, r') ∉ replacedOf g c :=
  sorry

/-- **SNP-13** The second side is sorted in two as well, when it holds one row a key at most, as the
contents of a cut do: each of its rows is added or is the second of a replaced pair. -/
theorem mem_come_iff {g c : List (Gen κ β)}
    (hc : ∀ x ∈ c, ∀ y ∈ c, x.key = y.key → x = y) {r' : Gen κ β} :
    r' ∈ c ↔ r' ∈ addedOf g c ∨ ∃ r, (r, r') ∈ replacedOf g c :=
  sorry

end Classes

/-! ### On the generations of a chain -/

section Generations

variable {κ β : Type*} [DecidableEq κ]

/-- **SNP-12** A row records the chain's event at its position: the rows of the generations are the
events of the chain, each with the stamp of its key's next event. -/
theorem getElem?_of_mem_gens {l : List (κ × β)} {r : Gen κ β} (hr : r ∈ gens l) :
    l[r.born - 1]? = some (r.key, r.val) :=
  sorry

/-- **SNP-12** The closing stamp of a row is the position of its key's next event, which lies past
the row's own. -/
theorem exists_next_of_mem_gens {l : List (κ × β)} {r : Gen κ β} (hr : r ∈ gens l) {d : ℕ}
    (hd : r.died = some d) : r.born < d ∧ ∃ r' ∈ gens l, r'.key = r.key ∧ r'.born = d :=
  sorry

/-- **SNP-12** A row of the generations is well formed: it is alive at its own position. -/
theorem proper_of_mem_gens {l : List (κ × β)} {r : Gen κ β} (hr : r ∈ gens l) : r.Proper :=
  sorry

/-- **SNP-17** The closing stamps are a function of the keys alone: a chain with its values
rewritten, key by key, has the generations of the chain with their values rewritten. An erasure that
keeps the key of a hole moves no position and no stamp. -/
theorem gens_map {β' : Type*} (f : κ × β → β') (l : List (κ × β)) :
    gens (l.map fun e ↦ (e.1, f e))
      = (gens l).map fun r ↦ ⟨r.key, f (r.key, r.val), r.born, r.died⟩ :=
  sorry

/-- **SNP-12** What a cut holds is each key's state at the cut, once: the rows of a key alive at a
cut are the one row of its state there, or none. Every head at once is the read of every key. -/
theorem map_val_filter_key_contentAt (l : List (κ × β)) (c : ℕ) (x : κ) :
    ((contentAt (gens l) c).filter fun r ↦ decide (r.key = x)).map Gen.val
      = (stateAt l c x).toList :=
  sorry

/-- **SNP-12** A cut holds one row a key at most: two rows of one key alive at one cut are one row.
-/
theorem eq_of_key_eq_of_mem_contentAt {l : List (κ × β)} {c : ℕ} {r r' : Gen κ β}
    (hr : r ∈ contentAt (gens l) c) (hr' : r' ∈ contentAt (gens l) c) (hk : r.key = r'.key) :
    r = r' :=
  sorry

/-- **SNP-14** Append invariance for every set: a set whose cuts lie inside the chain holds, after
any growth of the chain, the events it held. The growth writes closing stamps into rows the set
holds, each past the old head, so the events are compared and not the stamps. -/
theorem Held.rows_gens_append {γ : Type*} {pos : γ → ℕ} {e : Held γ} {l : List (κ × β)}
    (t : List (κ × β)) (h : ∀ c ∈ e.atoms, pos c ≤ l.length) :
    (e.rows pos (gens (l ++ t))).map Gen.event = (e.rows pos (gens l)).map Gen.event :=
  sorry

/-- **SNP-14** So a set whose cuts lie at or under a cut inside the chain reads the prefix at that
cut and nothing after it: what a cut holds is a derived view of its read. -/
theorem Held.rows_gens_take {γ : Type*} {pos : γ → ℕ} {e : Held γ} {l : List (κ × β)} {c : ℕ}
    (hc : c ≤ l.length) (h : ∀ a ∈ e.atoms, pos a ≤ c) :
    (e.rows pos (gens l)).map Gen.event = (e.rows pos (gens (l.take c))).map Gen.event :=
  sorry

/-- **SNP-13** The signed difference is sound for what did not change: every row on either side of
it belongs to a key that an event between the two cuts names. A key the events between do not name
holds at both cuts the row it held. -/
theorem key_mem_of_mem_delta {l : List (κ × β)} {a b : ℕ} (h : a ≤ b) {r : Gen κ β}
    (hr : r ∈ gens l)
    (hd : (Held.gone a b).has id r = true ∨ (Held.come a b).has id r = true) :
    r.key ∈ ((l.take b).drop a).map Prod.fst :=
  sorry

/-- **SNP-17** A retire is a removal: when a key holds a version at one cut and its last event at
another is a retire, the row of the version is gone between the two, and no row of the key that came
carries a version. -/
theorem removed_of_retire {l : List (κ × Option β)} {a b : ℕ} {x : κ} {v : β}
    (ha : stateAt l a x = some (some v)) (hb : stateAt l b x = some none) :
    (∃ r ∈ gens l, r.key = x ∧ r.val = some v ∧ (Held.gone a b).has id r = true) ∧
      ∀ r ∈ gens l, r.key = x → (Held.come a b).has id r = true → r.val = none :=
  sorry

/-- **SNP-17** No row of a chain with holes carries an erased value, so no set of its versions holds
one. -/
theorem not_erased_of_mem_gens_holes {E : κ × β → Bool} {l : List (κ × β)}
    {r : Gen κ (Option β)} {v : β} (hr : r ∈ gens (holes E l)) (hv : r.val = some v) :
    E (r.key, v) = false :=
  sorry

/-- **SNP-17** An erasure takes its own rows out of every set and changes no other: the versions a
set holds on the chain with holes are the rows it holds on the chain, less the erased ones, each at
the position it had. -/
theorem Held.rows_gens_holes {γ : Type*} {pos : γ → ℕ} (e : Held γ) (E : κ × β → Bool)
    (l : List (κ × β)) :
    ((e.rows pos (gens (holes E l))).filter Gen.isVersion).map Gen.event
      = ((e.rows pos (gens l)).filter fun r ↦ !E (r.key, r.val)).map
        fun r ↦ (r.key, some r.val, r.born) :=
  sorry

end Generations

/-! ### On a store: the grant and the positions -/

section Store

variable {K α β κ γ : Type*}

/-- **SNP-16** A narrower grant's restriction of a family of chains is its restriction of a wider
grant's. -/
theorem restrict_narrow {G G' : K → Prop} [DecidablePred G] [DecidablePred G']
    {p p' : α → Bool} (hG : ∀ k, G k → G' k) (hp : ∀ a, p a = true → p' a = true)
    (t : Store K α) : restrict G p t = restrict G p (restrict G' p' t) :=
  sorry

/-- **SNP-16** Every set commutes with the grant: read on the chains the grant shows, it is the
grant's restriction of the set read on the whole store. The grant may be applied before the
operators or after them. -/
theorem Held.across_restrict (G : K → Prop) [DecidablePred G] (p : Gen κ β → Bool)
    (pos : γ → Cut K) (e : Held γ) (R : K → List (Gen κ β)) :
    e.across pos (restrict G p R) = restrict G p (e.across pos R) :=
  sorry

/-- **SNP-16** Noninterference for every set: under a grant a set reads only the chains the grant
names, and of its cuts only their positions on them. Two stores that agree on those chains, at cuts
that agree on them, give one answer. -/
theorem Held.across_congr (G : K → Prop) [DecidablePred G] (p : Gen κ β → Bool)
    {pos pos' : γ → Cut K} {e : Held γ} {R R' : K → List (Gen κ β)}
    (hR : ∀ k, G k → R k = R' k) (hpos : ∀ c ∈ e.atoms, ∀ k, G k → pos c k = pos' c k) :
    restrict G p (e.across pos R) = restrict G p (e.across pos' R') :=
  sorry

/-- **SNP-16** A narrower grant's set is the restriction of a wider grant's. -/
theorem Held.across_narrow {G G' : K → Prop} [DecidablePred G] [DecidablePred G']
    {p p' : Gen κ β → Bool} (hG : ∀ k, G k → G' k) (hp : ∀ a, p a = true → p' a = true)
    (pos : γ → Cut K) (e : Held γ) (R : K → List (Gen κ β)) :
    restrict G p (e.across pos R) = restrict G p (restrict G' p' (e.across pos R)) :=
  sorry

/-- **SNP-16** Under a grant a set names no chain the grant does not name. -/
theorem Held.across_of_not (G : K → Prop) [DecidablePred G] (p : Gen κ β → Bool)
    (pos : γ → Cut K) (e : Held γ) (R : K → List (Gen κ β)) {k : K} (h : ¬G k) :
    restrict G p (e.across pos R) k = [] :=
  sorry

/-- **SNP-16** The events between two cuts under a grant that names whole chains: restricting to the
chains commutes with the read between, as it does with the read at a cut. -/
theorem restrict_readBetween (G : K → Prop) [DecidablePred G] (s : Store K α) (a b : Cut K) :
    restrict G (fun _ ↦ true) (readBetween s a b)
      = readBetween (restrict G (fun _ ↦ true) s) a b :=
  sorry

/-- **SNP-15** Contents against positions, on a store: what either of two cuts holds is what their
join holds, with the rows closed between their meet and their join. -/
theorem Held.has_union_cut (a b : Cut K) (k : K) (r : Gen κ β) :
    ((Held.cut a).union (Held.cut b)).has (fun c ↦ c k) r
      = ((Held.cut (a ⊔ b)).union (Held.gone (a ⊓ b) (a ⊔ b))).has (fun c ↦ c k) r :=
  sorry

/-- **SNP-15** And what both hold is what their meet and their join both hold: what their meet
holds, less the rows closed between the two. -/
theorem Held.has_inter_cut (a b : Cut K) (k : K) (r : Gen κ β) :
    ((Held.cut a).inter (Held.cut b)).has (fun c ↦ c k) r
      = (Held.kept (a ⊓ b) (a ⊔ b)).has (fun c ↦ c k) r :=
  sorry

/-- **SNP-11** The meet and the join of two cuts that are read as asked are read as asked: the cuts
that are consistent and served are closed under both, the consistency by CLK-2. -/
theorem resolvesIn_sup {R : K → ℕ → K → ℕ → Prop} {S : K → Set ℕ} {a b : Cut K}
    (ha : Consistent R a) (hb : Consistent R b) (hSa : a ∈ servedCuts S)
    (hSb : b ∈ servedCuts S) : ResolvesIn R S (a ⊔ b) (a ⊔ b) :=
  sorry

/-- **SNP-11** The same for the meet. -/
theorem resolvesIn_inf {R : K → ℕ → K → ℕ → Prop} {S : K → Set ℕ} {a b : Cut K}
    (ha : Consistent R a) (hb : Consistent R b) (hSa : a ∈ servedCuts S)
    (hSb : b ∈ servedCuts S) : ResolvesIn R S (a ⊓ b) (a ⊓ b) :=
  sorry

/-- **SNP-11** The read at the join of two cuts is, chain by chain, the read at the later of the
two. -/
theorem readAt_sup (s : Store K α) (a b : Cut K) (k : K) :
    readAt s (a ⊔ b) k = if a k ≤ b k then readAt s b k else readAt s a k :=
  sorry

/-- **SNP-11** The read at the meet of two cuts is, chain by chain, the read at the earlier of the
two. -/
theorem readAt_inf (s : Store K α) (a b : Cut K) (k : K) :
    readAt s (a ⊓ b) k = if a k ≤ b k then readAt s a k else readAt s b k :=
  sorry

/-- **SNP-11** The read at the empty cut is empty. -/
theorem readAt_bot (s : Store K α) : readAt s ⊥ = fun _ ↦ [] :=
  sorry

/-- **SNP-11** The meet distributes over the join, and so do the reads: the cuts are a distributive
lattice. -/
theorem readAt_inf_sup (s : Store K α) (a b c : Cut K) :
    readAt s (a ⊓ (b ⊔ c)) = readAt s (a ⊓ b ⊔ a ⊓ c) :=
  sorry

/-- **SNP-11** The difference of two cuts on positions, the events the second holds and the first
does not, is the read between their meet and the second. -/
theorem readBetween_inf_left (s : Store K α) (a b : Cut K) :
    readBetween s (a ⊓ b) b = readBetween s a b :=
  sorry

/-- **SNP-11** And the read between the first and their join. -/
theorem readBetween_sup_right (s : Store K α) (a b : Cut K) :
    readBetween s a (a ⊔ b) = readBetween s a b :=
  sorry

/-- **SNP-11** The symmetric difference of two cuts on positions, the events exactly one of them
holds, is the read between their meet and their join: on each chain, one of the two differences. -/
theorem readBetween_inf_sup (s : Store K α) (a b : Cut K) (k : K) :
    readBetween s (a ⊓ b) (a ⊔ b) k = readBetween s a b k ++ readBetween s b a k :=
  sorry

/-- **SNP-11** The empty cut is inside every store: the bottom. -/
theorem bot_mem_cutsIn (s : Store K α) : (⊥ : Cut K) ∈ cutsIn s :=
  sorry

/-- **SNP-11** The head is inside the store, and every cut inside the store lies under it: the top.
-/
theorem head_mem_cutsIn (s : Store K α) : head s ∈ cutsIn s :=
  sorry

/-- **SNP-11** The head moves and no cut leaves: the cuts inside a store are inside every extension
of it. -/
theorem cutsIn_mono {s s' : Store K α} (h : Extends s s') : cutsIn s ≤ cutsIn s' :=
  sorry

/-- **SNP-14** A function of two cuts' reads is append invariant. -/
theorem combine_grow (f : Store K α → Store K α → β) {s : Store K α} (t : Store K α)
    {a b : Cut K} (ha : a ≤ head s) (hb : b ≤ head s) :
    combine f (grow s t) a b = combine f s a b :=
  sorry

/-- **SNP-14** A measure at each cut of a family is append invariant. -/
theorem series_grow (D : Store K α → β) {s : Store K α} (t : Store K α) {F : List (Cut K)}
    (hF : ∀ c ∈ F, c ≤ head s) : series D (grow s t) F = series D s F :=
  sorry

/-- **SNP-14** A fold over a family of cuts is append invariant. -/
theorem foldOver_grow (g : β → Store K α → β) (init : β) {s : Store K α} (t : Store K α)
    {F : List (Cut K)} (hF : ∀ c ∈ F, c ≤ head s) :
    foldOver g init (grow s t) F = foldOver g init s F :=
  sorry

/-- **SNP-11** The difference of two cuts on positions is a function of their two reads: the events
of the second read past the length of the first. -/
theorem readBetween_eq_combine (s : Store K α) (a b : Cut K) :
    readBetween s a b = combine (fun x y k ↦ (y k).drop (x k).length) s a b :=
  sorry

end Store

namespace Witness

/-- **SNP-15** The control for the two meanings of union: on contents it does not follow the join of
the positions. One key written twice: the union of what the two cuts hold has both rows, and the
join of the two cuts holds the later one alone. -/
theorem union_ne_join :
    ∃ (l : List (Unit × ℕ)) (a b : ℕ),
      (((Held.cut a).union (Held.cut b)).rows id (gens l)).map Gen.val = [0, 1] ∧
        ((Held.cut (a ⊔ b)).rows id (gens l)).map Gen.val = [1] :=
  sorry

/-- **SNP-12** The control for contiguity: it is a law of rows, and a value has none. A key that
returns to a value it held before holds it at two cuts and not between them. -/
theorem value_not_contiguous :
    ∃ l : List (Unit × ℕ),
      stateAt l 1 () = some 0 ∧ stateAt l 3 () = some 0 ∧ stateAt l 2 () = some 1 :=
  sorry

/-- **SNP-13** The control for the composition of signed differences: through a cut that does not
lie between the two it fails. A row alive at `a` and `c` and not at `b` is come from `b` to `c` and
is on neither side from `a` to `c`. -/
theorem delta_through_outside :
    ∃ (r : Gen Unit Unit) (a b c : ℕ),
      (Held.come a c).has id r = false ∧
        (((Held.come a b).diff (Held.gone b c)).union (Held.come b c)).has id r = true :=
  sorry

/-- **SNP-16** The control for the row's own test: applied to the chain before its generations are
computed, it moves the positions, and a cut then holds an event from after it. -/
theorem filter_before_gens :
    ∃ (l : List (ℕ × ℕ)) (p : ℕ × ℕ → Bool) (c : ℕ),
      (contentAt (gens (l.filter p)) c).map Gen.val = [8] ∧
        ((contentAt (gens l) c).filter fun r ↦ p (r.key, r.val)).map Gen.val = [] :=
  sorry

/-- **SNP-13** The control for the signed difference against the events between two cuts: a key
landed and retired between them is named by the events and is on neither side of the difference. -/
theorem changed_not_delta :
    ∃ (l : List (Unit × Option ℕ)) (a b : ℕ),
      () ∈ ((l.take b).drop a).map Prod.fst ∧
        ((Held.gone a b).rows id ((gens l).filter Gen.isVersion)).length = 0 ∧
        ((Held.come a b).rows id ((gens l).filter Gen.isVersion)).length = 0 :=
  sorry

/-- **SNP-14** The control for the missing complement: the rows a cut does not hold are not append
invariant, since every later row is among them. -/
theorem complement_grows :
    ∃ (l t : List (Unit × ℕ)) (c : ℕ), c ≤ l.length ∧
      ((gens (l ++ t)).filter fun r ↦ !r.aliveAt c).length
        ≠ ((gens l).filter fun r ↦ !r.aliveAt c).length :=
  sorry

end Witness

end Palace.Snapshot
