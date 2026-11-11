module

public import Palace.Snapshot.Defs
public import Palace.Clock
public import Mathlib.Data.List.Induction
public import Mathlib.Data.List.ReduceOption
public import Mathlib.Order.Lattice
public import Mathlib.Order.Lattice.Nat
public import Mathlib.Order.Sublattice

/-!
# The temporal snapshot: the laws of a read at a cut

Design theorems of `docs/design-notes/dn-temporal-snapshot.md`, proved before any code reads a
store at a cut, on the model of `Palace/Snapshot/Defs.lean`: a store is a family of append chains,
a cut a prefix length for each. Cited from the note, not from the ledger.

* SNP-1, append invariance: a read at a cut inside the store, a read between two such cuts and
  every derived view of them are the same after any growth of the store (`readAt_grow`,
  `readAt_of_extends`, `readBetween_grow`, `appendInvariant_view`). The control is the reader that
  ignores the cut (`Witness.present_not_appendInvariant`).
* SNP-2, monotonicity: the read at an earlier cut is a prefix of the read at a later one, and a
  cut of a cut is the meet (`readAt_mono`, `readAt_readAt`, `head_readAt`).
* SNP-3, composition: the read at `a` followed by the read between `a` and `b` is the read at
  `b`, and two adjacent reads-between compose (`readAt_append_readBetween`,
  `readBetween_append`); so a fold continued from a checkpoint over the events since is the fold
  of the whole prefix (`foldAt_readBetween`, `stateAt_eq_foldl`): a job's checkpoint is a cut.
  An event read at the later cut was read at the earlier one or lies in the delta, a pair of
  events likewise, and a key the delta does not write has one state at both cuts
  (`mem_readAt_iff`, `pair_readAt`, `stateAt_eq_of_not_written`).
* SNP-4, idempotence: the read at the head cut is the store, and every derived view at it is
  the derivation of the present (`readAt_head`, `view_head`, `genRead_gens_length`).
* SNP-5, a derived view is a function of the prefixes: a reader is append invariant exactly when
  it reads only the prefixes, exactly when it is a derived view
  (`appendInvariant_iff_prefixOnly`, `appendInvariant_iff_exists_view`). For a store of keyed
  writes the three ways of holding it agree: the generational store read at a cut is the state
  recomputed from the prefix (`genRead_gens`), it is the last write inside the prefix
  (`stateAt_eq_lastWrite`), and at most one generation of a key is alive at a cut
  (`length_filter_selects_le_one`). The store rewritten in place determines no read at a past
  cut (`Witness.stateOf_forgets`).
* SNP-6, grant restriction: a narrower grant's snapshot is the restriction of a wider one's, a
  snapshot reads only the chains the grant names and the cut on them, and it is append
  invariant (`snapshot_narrow`, `snapshot_congr`, `snapshot_grow`). Restricting to chains commutes
  with the cut; filtering events before the cut does not, and a cut's positions count the events
  a filter hides (`restrict_readAt`, `Witness.filter_before_cut`, `Witness.position_channel`).
  The grant and the erasure applied to one read keep these laws (`shown_narrow`, `shown_grow`,
  `not_erased_of_mem_shown`). The cut read on the chains a grant names is a function of those
  chains when they read from no chain outside them (`ResolvesIn.eq_on_of_closed`); the control
  is a named chain that reads an unnamed one (`Witness.resolution_reads_unnamed`).
* SNP-7, erasure dominance: no erased event is visible at any cut, a larger erasure shows a
  sublist, the store with holes keeps every position, and two stores that differ only in erased
  events give every derived view the same reading at every cut (`not_erased_of_mem_visible`,
  `visible_sublist`, `redact_readAt`, `erased_invisible`); a kept derived row is served only when
  none of its sources is erased (`mem_serve_iff`); a key retired after a cut is served at no
  earlier cut, and growth of the chain changes a served value only by removing it
  (`servedAt_append_of_retire`, `servedAt_append_of_no_retire`, `servedAt_of_append`); the looser
  seal, under which a key is withheld only while it is not live, serves everything the stricter
  one serves and is lifted by a later landing (`servedNow_of_servedAt`,
  `Witness.servedNow_restores`). The seal covers the key's versions as it covers its value: the
  history served at a cut ends at the value served there, and at every cut after a retire, the
  head included, it holds only versions landed after that retire (`getLast?_historyAt`,
  `historyAt_append_of_retire`, `historyAt_of_retire_inside`, `sinceRetire_append_retire`). The
  control is the erasure that deletes rows (`Witness.compact_moves`). For a keyed chain whose
  holes keep their keys, the read of a key at a cut is its last write at or under the cut, a
  hole when that write is erased, and the three reads agree on it (`stateAt_holes`,
  `stateAt_holes_of_erased`, `not_erased_of_stateAt_holes`, `genRead_gens_holes`, `lastWrite_holes`); the control is the hole that loses its key, which
  returns a superseded version or one from after the cut (`Witness.keyless_hole`).
* SNP-8, resolution: the consistent cuts are the clock's cuts, CLK-2, among the frontier cuts
  (`consistent_iff_isCut`), so their closure under meet and join is CLK-2's, read through that
  equivalence (`Consistent.inf`, `Consistent.sup`, `consistentCuts`). What this law adds is
  resolution: every frontier resolves to exactly one greatest consistent cut under it,
  monotonically (`exists_resolves`, `Resolves.unique`, `Resolves.mono`); a consistent cut stays
  consistent as the store grows (`Consistent.of_grown`); and a cut consistent for a recorded
  bound on the references is consistent for the true ones (`Consistent.of_bound`).
* SNP-9, certified cuts: the certificate of a cut verifies on every extension of the store, two
  stores that verify one certificate under a collision-free digest have the same read at its cut
  and so the same derived views, a certificate extends over the events since an earlier one, the
  meet and the join of two certified cuts are certified from the two certificates alone, and an
  erasure that keeps commitments keeps every certificate (`verifies_certify_of_extends`,
  `Verifies.readAt_eq`, `Verifies.view_eq`, `certify_digest_readBetween`, `certify_inf`,
  `certify_sup`, `verifies_purge`). A certificate over commitments attests no erasure
  (`verifies_purge_iff`); under a binding commitment it pins the events, so two stores that
  verify it read the same store with holes under one erasure
  (`Verifies.readAt_eq_of_committed`, `Verifies.contents_eq`, `contents_purge_committed`,
  `Verifies.shown_eq`). The controls: a digest with collisions (`Witness.digest_collides`), a
  seal written after the cut (`Witness.seal_not_certified`), a renamed chain
  (`Witness.rename_breaks_certificate`).
* SNP-10, the horizon: a generational store that drops the rows closed at or under a horizon
  reads, at every cut from the horizon on, the state recomputed from the whole prefix; under the
  horizon it is never wrong and reads what it lost as absent; horizons compose to the later one
  (`genRead_prune`, `genRead_prune_gens`, `stateAt_of_genRead_prune`, `prune_prune`). Where the
  chains serve only some positions, every frontier resolves to exactly one greatest consistent
  cut among them, which rises with what is served and never passes the cut asked
  (`exists_resolvesIn`, `ResolvesIn.unique`, `ResolvesIn.mono`, `ResolvesIn.le_resolves`,
  `resolvesIn_univ`). A chain that no other chain reads is lowered alone, every other chain
  read as asked (`Consistent.update_of_unread`, `resolvesIn_update_of_unread`), and retention
  commutes with growth (`prune_landGen`). The controls: the pruned store read under its horizon,
  which cannot tell a lost key from one never written (`Witness.prune_forgets`,
  `Witness.prune_indistinct`); a record on a chain that content reads, which drags every reader
  down (`Witness.record_drags`); served sets that shrink, under which the cut read falls
  (`Witness.served_set_shrinks`).
-/

@[expose] public section

namespace Palace.Snapshot

/-! ### SNP-1 to SNP-4 Reads -/

section Reads

variable {K α β : Type*}

theorem extends_grow (s t : Store K α) : Extends s (grow s t) := fun _ ↦ List.prefix_append _ _

/-- An extension of a store is the store grown: append is all that happened. -/
theorem Extends.exists_grow {s s' : Store K α} (h : Extends s s') : ∃ t, s' = grow s t :=
  ⟨fun k ↦ (s' k).drop (s k).length, funext fun k ↦ (List.prefix_iff_eq_append.1 (h k)).symm⟩

theorem Extends.head_le {s s' : Store K α} (h : Extends s s') : head s ≤ head s' :=
  fun k ↦ (h k).length_le

/-- SNP-1 Append invariance: the read at a cut inside the store does not change when the store
grows. -/
theorem readAt_grow {s : Store K α} (t : Store K α) {c : Cut K} (h : c ≤ head s) :
    readAt (grow s t) c = readAt s c :=
  funext fun k ↦ List.take_append_of_le_length (h k)

/-- SNP-1 The same over every extension: a later state of an append-only store reads, at a cut
of an earlier state, what the earlier state read. -/
theorem readAt_of_extends {s s' : Store K α} {c : Cut K} (h : Extends s s') (hc : c ≤ head s) :
    readAt s' c = readAt s c := by
  obtain ⟨t, rfl⟩ := h.exists_grow
  exact readAt_grow t hc

/-- SNP-1 The read between two cuts inside the store does not change when the store grows. -/
theorem readBetween_grow {s : Store K α} (t : Store K α) (a : Cut K) {b : Cut K}
    (h : b ≤ head s) : readBetween (grow s t) a b = readBetween s a b :=
  funext fun k ↦ congrArg (List.drop (a k)) (List.take_append_of_le_length (h k))

/-- SNP-1 Every derived view is append invariant. -/
theorem appendInvariant_view (D : Store K α → β) : AppendInvariant (view D) :=
  fun _ t _ h ↦ congrArg D (readAt_grow t h)

theorem readAt_extends (s : Store K α) (c : Cut K) : Extends (readAt s c) s :=
  fun k ↦ List.take_prefix (c k) (s k)

/-- SNP-2 Monotonicity: the read at an earlier cut is a prefix, chain by chain, of the read at a
later one. -/
theorem readAt_mono (s : Store K α) {c d : Cut K} (h : c ≤ d) :
    Extends (readAt s c) (readAt s d) :=
  fun k ↦ List.take_prefix_take_left (h k)

/-- SNP-2 An event read at a cut is read at every later cut. -/
theorem mem_readAt_of_le {s : Store K α} {c d : Cut K} (h : c ≤ d) {k : K} {a : α}
    (ha : a ∈ readAt s c k) : a ∈ readAt s d k :=
  (readAt_mono s h k).subset ha

/-- SNP-2 A cut of a cut is the meet of the two. -/
theorem readAt_readAt (s : Store K α) (c d : Cut K) :
    readAt (readAt s c) d = readAt s (d ⊓ c) :=
  funext fun _ ↦ List.take_take

theorem head_readAt (s : Store K α) (c : Cut K) : head (readAt s c) = c ⊓ head s :=
  funext fun _ ↦ List.length_take

theorem head_readAt_of_le {s : Store K α} {c : Cut K} (h : c ≤ head s) :
    head (readAt s c) = c := by
  rw [head_readAt, inf_of_le_left h]

/-- SNP-4 A cut at or past the head reads the store. -/
theorem readAt_of_head_le {s : Store K α} {c : Cut K} (h : head s ≤ c) : readAt s c = s :=
  funext fun k ↦ List.take_of_length_le (h k)

/-- SNP-4 Idempotence: the read at the head cut is the store. -/
theorem readAt_head (s : Store K α) : readAt s (head s) = s := readAt_of_head_le le_rfl

/-- SNP-4 Every derived view at the head cut is the derivation of the present: `as of` the
current cut is no `as of`. -/
theorem view_head (D : Store K α → β) (s : Store K α) : view D s (head s) = D s :=
  congrArg D (readAt_head s)

theorem drop_take_append_drop (l : List α) {a b : ℕ} (h : a ≤ b) :
    (l.take b).drop a ++ l.drop b = l.drop a := by
  conv_rhs => rw [← List.take_append_drop b l, List.drop_append]
  congr 1
  rcases Nat.le_total b l.length with hb | hb
  · rw [List.length_take, Nat.min_eq_left hb, Nat.sub_eq_zero_of_le h, List.drop_zero]
  · rw [List.drop_of_length_le hb, List.drop_nil]

/-- SNP-3 Composition: the read at `a` followed by the read between `a` and `b` is the read at
`b`. -/
theorem readAt_append_readBetween (s : Store K α) {a b : Cut K} (h : a ≤ b) :
    grow (readAt s a) (readBetween s a b) = readAt s b := by
  funext k
  have h1 : (s k).take (a k) = ((s k).take (b k)).take (a k) := by
    rw [List.take_take, Nat.min_eq_left (h k)]
  change (s k).take (a k) ++ ((s k).take (b k)).drop (a k) = (s k).take (b k)
  rw [h1, List.take_append_drop]

/-- SNP-3 Two adjacent reads-between compose. -/
theorem readBetween_append (s : Store K α) {a b c : Cut K} (hab : a ≤ b) (hbc : b ≤ c) :
    grow (readBetween s a b) (readBetween s b c) = readBetween s a c := by
  funext k
  have h1 : (s k).take (b k) = ((s k).take (c k)).take (b k) := by
    rw [List.take_take, Nat.min_eq_left (hbc k)]
  change ((s k).take (b k)).drop (a k) ++ ((s k).take (c k)).drop (b k)
    = ((s k).take (c k)).drop (a k)
  rw [h1]
  exact drop_take_append_drop _ (hab k)

/-- The read between the empty cut and a cut is the read at it. -/
theorem readBetween_zero (s : Store K α) (b : Cut K) :
    readBetween s (fun _ ↦ 0) b = readAt s b := rfl

/-- The read between a cut and itself is empty. -/
theorem readBetween_self (s : Store K α) (a : Cut K) : readBetween s a a = fun _ ↦ [] := by
  funext k
  refine List.drop_of_length_le ?_
  rw [List.length_take]
  exact Nat.min_le_left _ _

/-- The read between a cut and the head is what the store appended since the cut. -/
theorem readBetween_head (s : Store K α) (a : Cut K) :
    readBetween s a (head s) = fun k ↦ (s k).drop (a k) := by
  funext k
  change ((s k).take (s k).length).drop (a k) = (s k).drop (a k)
  rw [List.take_length]

/-- SNP-3 The journal: a fold of the prefixes at a later cut is the fold at an earlier cut
continued over the events between the two. A job that keeps its state and the cut it stopped at
reads only the delta. -/
theorem foldAt_readBetween (f : β → α → β) (init : K → β) (s : Store K α) {a b : Cut K}
    (h : a ≤ b) (k : K) :
    foldAt f init s b k = (readBetween s a b k).foldl f (foldAt f init s a k) :=
  calc foldAt f init s b k
      = ((s k).take (a k) ++ ((s k).take (b k)).drop (a k)).foldl f (init k) :=
        congrArg (fun l ↦ l.foldl f (init k)) (congrFun (readAt_append_readBetween s h) k).symm
    _ = _ := List.foldl_append

/-- SNP-3 An event read at the later cut was read at the earlier cut or lies in the delta. -/
theorem mem_readAt_iff {s : Store K α} {a b : Cut K} (h : a ≤ b) {k : K} {x : α} :
    x ∈ readAt s b k ↔ x ∈ readAt s a k ∨ x ∈ readBetween s a b k := by
  rw [← readAt_append_readBetween s h]
  exact List.mem_append

/-- SNP-3 The delta rule for a job that joins two chains: a pair of events read at the later
cut was read at the earlier cut, or one of the two lies in the delta. So a job that kept the
pairs of its checkpoint has only the pairs with a new member left to visit. -/
theorem pair_readAt {s : Store K α} {a b : Cut K} (h : a ≤ b) {k k' : K} {x y : α}
    (hx : x ∈ readAt s b k) (hy : y ∈ readAt s b k') :
    (x ∈ readAt s a k ∧ y ∈ readAt s a k') ∨ x ∈ readBetween s a b k ∨
      y ∈ readBetween s a b k' := by
  rcases (mem_readAt_iff h).1 hx with hx | hx
  · rcases (mem_readAt_iff h).1 hy with hy | hy
    · exact Or.inl ⟨hx, hy⟩
    · exact Or.inr (Or.inr hy)
  · exact Or.inr (Or.inl hx)

/-- SNP-5 A derived view reads only the prefixes. -/
theorem prefixOnly_view (D : Store K α → β) : PrefixOnly (view D) := fun s c _ ↦ by
  change D (readAt s c) = D (readAt (readAt s c) c)
  rw [readAt_readAt, inf_idem]

/-- SNP-5 Two stores with the same prefixes at a cut give every derived view the same
reading. -/
theorem view_congr (D : Store K α → β) {s s' : Store K α} {c : Cut K}
    (h : readAt s c = readAt s' c) : view D s c = view D s' c := congrArg D h

/-- SNP-5 A reader is append invariant exactly when it reads only the prefixes. -/
theorem appendInvariant_iff_prefixOnly (F : Store K α → Cut K → β) :
    AppendInvariant F ↔ PrefixOnly F := by
  constructor
  · intro h s c hc
    obtain ⟨t, ht⟩ := (readAt_extends s c).exists_grow
    have hc' : c ≤ head (readAt s c) := le_of_eq (head_readAt_of_le hc).symm
    calc F s c = F (grow (readAt s c) t) c := by rw [← ht]
      _ = F (readAt s c) c := h _ t c hc'
  · intro h s t c hc
    rw [h (grow s t) c (hc.trans (extends_grow s t).head_le), readAt_grow t hc, ← h s c hc]

/-- SNP-5 A reader is append invariant exactly when it is a derived view: on cuts inside the
store, a function of the prefixes alone. -/
theorem appendInvariant_iff_exists_view (F : Store K α → Cut K → β) :
    AppendInvariant F ↔ ∃ D : Store K α → β, ∀ s c, c ≤ head s → F s c = view D s c := by
  rw [appendInvariant_iff_prefixOnly]
  constructor
  · intro h
    refine ⟨fun t ↦ F t (head t), fun s c hc ↦ ?_⟩
    change F s c = F (readAt s c) (head (readAt s c))
    rw [head_readAt_of_le hc]
    exact h s c hc
  · rintro ⟨D, hD⟩ s c hc
    have hc' : c ≤ head (readAt s c) := le_of_eq (head_readAt_of_le hc).symm
    rw [hD s c hc, hD (readAt s c) c hc']
    exact prefixOnly_view D s c hc

end Reads

/-! ### SNP-5 A derived store, three ways -/

section Generations

variable {κ β : Type*} [DecidableEq κ]

theorem stateOf_append_singleton (l : List (κ × β)) (e : κ × β) :
    stateOf (l ++ [e]) = Function.update (stateOf l) e.1 (some e.2) := by
  simp only [stateOf, List.foldl_append, List.foldl_cons, List.foldl_nil]

theorem stateAt_length (l : List (κ × β)) : stateAt l l.length = stateOf l := by
  unfold stateAt
  rw [List.take_length]

theorem stateAt_of_length_le {l : List (κ × β)} {c : ℕ} (h : l.length ≤ c) :
    stateAt l c = stateOf l := by
  unfold stateAt
  rw [List.take_of_length_le h]

/-- SNP-1 The state at a cut inside the chain does not change when the chain grows. -/
theorem stateAt_append {l : List (κ × β)} (t : List (κ × β)) {c : ℕ} (h : c ≤ l.length) :
    stateAt (l ++ t) c = stateAt l c := by
  unfold stateAt
  rw [List.take_append_of_le_length h]

/-- SNP-3 The journal of the keyed state: the state at a later cut is the state at an earlier
cut with the writes between the two applied in order. -/
theorem stateAt_eq_foldl (l : List (κ × β)) {a b : ℕ} (h : a ≤ b) :
    stateAt l b = ((l.take b).drop a).foldl
      (fun (m : κ → Option β) (e : κ × β) ↦ Function.update m e.1 (some e.2)) (stateAt l a) := by
  have h1 : l.take a = (l.take b).take a := by rw [List.take_take, Nat.min_eq_left h]
  unfold stateAt stateOf
  rw [h1, ← List.foldl_append, List.take_append_drop]

theorem foldl_update_of_ne {t : List (κ × β)} {m : κ → Option β} {x : κ}
    (ht : ∀ e ∈ t, e.1 ≠ x) :
    (t.foldl (fun (m : κ → Option β) (e : κ × β) ↦ Function.update m e.1 (some e.2)) m) x
      = m x := by
  induction t generalizing m with
  | nil => rfl
  | cons e t ih =>
    rw [List.foldl_cons, ih fun e' he' ↦ ht e' (List.mem_cons_of_mem _ he')]
    exact Function.update_of_ne (Ne.symm (ht e List.mem_cons_self)) _ _

/-- SNP-3 The delta bounds the change: a key the writes between two cuts do not name has the
same state at both. What changed between two cuts is found among the keys of the delta. -/
theorem stateAt_eq_of_not_written (l : List (κ × β)) {a b : ℕ} (h : a ≤ b) {x : κ}
    (hx : ∀ e ∈ (l.take b).drop a, e.1 ≠ x) : stateAt l b x = stateAt l a x := by
  have h1 := congrFun (stateAt_eq_foldl l h) x
  rw [h1]
  exact foldl_update_of_ne hx

theorem stateOf_eq_find? (l : List (κ × β)) (x : κ) :
    stateOf l x = (l.reverse.find? fun e ↦ decide (e.1 = x)).map Prod.snd := by
  induction l using List.reverseRecOn with
  | nil => rfl
  | append_singleton l e ih =>
    rw [stateOf_append_singleton, List.reverse_append, List.reverse_singleton,
      List.singleton_append]
    by_cases hx : e.1 = x
    · simp [hx]
    · simp [hx, Function.update_of_ne (Ne.symm hx), ih]

/-- SNP-5 The state at a cut is the last write of the key inside the prefix: one seek on an
index of (key, position). -/
theorem stateAt_eq_lastWrite (l : List (κ × β)) (c : ℕ) (x : κ) :
    stateAt l c x = lastWrite l c x :=
  stateOf_eq_find? _ x

theorem closeAt_key (x : κ) (p : ℕ) (r : Gen κ β) : (closeAt x p r).key = r.key := by
  unfold closeAt
  split_ifs <;> rfl

theorem closeAt_val (x : κ) (p : ℕ) (r : Gen κ β) : (closeAt x p r).val = r.val := by
  unfold closeAt
  split_ifs <;> rfl

theorem closeAt_of_ne {x : κ} {r : Gen κ β} (h : r.key ≠ x) (p : ℕ) : closeAt x p r = r := by
  simp only [closeAt, h, false_and, ↓reduceIte]

/-- Closing a row at a position past the cut changes nothing the cut selects. -/
theorem selects_closeAt_of_lt (x y : κ) {c p : ℕ} (h : c < p) (r : Gen κ β) :
    selects c x (closeAt y p r) = selects c x r := by
  unfold closeAt
  split_ifs with hr
  · simp [selects, Gen.aliveAt, hr.2, h]
  · rfl

/-- Closing the rows of one key changes nothing a read of another key selects. -/
theorem selects_closeAt_of_ne {x y : κ} (h : x ≠ y) (c p : ℕ) (r : Gen κ β) :
    selects c x (closeAt y p r) = selects c x r := by
  by_cases hr : r.key = y
  · have hx : r.key ≠ x := fun h' ↦ h (h'.symm.trans hr)
    simp [selects, closeAt_key, hx]
  · rw [closeAt_of_ne hr]

/-- A row of the key closed at a position inside the cut is not selected, when every earlier
closing stamp lies under that position. -/
theorem selects_closeAt_self {y : κ} {n c : ℕ} (hc : n + 1 ≤ c) {r : Gen κ β}
    (hr : ∀ d, r.died = some d → d ≤ n) : selects c y (closeAt y (n + 1) r) = false := by
  unfold closeAt
  split_ifs with h
  · simp [selects, Gen.aliveAt, Nat.not_lt.2 hc]
  · by_cases hk : r.key = y
    · obtain ⟨d, hd⟩ := Option.ne_none_iff_exists'.1 fun h0 ↦ h ⟨hk, h0⟩
      have hcd : ¬c < d := by have := hr d hd; omega
      simp [selects, Gen.aliveAt, hd, hcd]
    · simp [selects, hk]

theorem gens_nil : gens ([] : List (κ × β)) = [] := rfl

/-- The generational store is appended to, and one closing stamp is written: the landing of a
write closes the key's open row and opens its own. -/
theorem gens_append_singleton (l : List (κ × β)) (e : κ × β) :
    gens (l ++ [e]) = landGen (gens l) (l.length + 1) e := by
  simp [gens, gensRev]

theorem died_le_of_mem_gens {l : List (κ × β)} {r : Gen κ β} (hr : r ∈ gens l) :
    ∀ d, r.died = some d → d ≤ l.length := by
  induction l using List.reverseRecOn generalizing r with
  | nil => simp [gens_nil] at hr
  | append_singleton l e ih =>
    rw [gens_append_singleton] at hr
    intro d hd
    rw [List.length_append, List.length_singleton]
    rcases List.mem_append.1 hr with hr | hr
    · obtain ⟨r', hr', rfl⟩ := List.mem_map.1 hr
      unfold closeAt at hd
      split_ifs at hd with h
      · have h1 : l.length + 1 = d := Option.some.inj hd
        omega
      · exact (ih hr' d hd).trans (Nat.le_succ _)
    · rw [List.mem_singleton.1 hr] at hd
      exact absurd hd (by simp)

theorem find?_landGen_of_stable {rs : List (Gen κ β)} {p : ℕ} {e : κ × β}
    {q : Gen κ β → Bool} (hq : ∀ r, q (closeAt e.1 p r) = q r)
    (hnew : q ⟨e.1, e.2, p, none⟩ = false) :
    ((landGen rs p e).find? q).map Gen.val = (rs.find? q).map Gen.val := by
  have hcomp : q ∘ closeAt e.1 p = q := funext hq
  unfold landGen
  rw [List.find?_append, List.find?_map, hcomp, List.find?_singleton, hnew]
  simp [Function.comp_def, closeAt_val]

theorem find?_landGen_of_new {rs : List (Gen κ β)} {p : ℕ} {e : κ × β} {q : Gen κ β → Bool}
    (hq : ∀ r ∈ rs, q (closeAt e.1 p r) = false) (hnew : q ⟨e.1, e.2, p, none⟩ = true) :
    (landGen rs p e).find? q = some ⟨e.1, e.2, p, none⟩ := by
  have hnone : (rs.map (closeAt e.1 p)).find? q = none := by
    rw [List.find?_eq_none]
    intro r hr
    obtain ⟨r', hr', rfl⟩ := List.mem_map.1 hr
    simp [hq r' hr']
  simp only [landGen, List.find?_append, hnone, Option.none_or, List.find?_singleton, hnew,
    ↓reduceIte]

/-- SNP-5 Generations are recomputation: the generational store read at a cut is the state
recomputed from the chain's prefix, at every cut. -/
theorem genRead_gens (l : List (κ × β)) (c : ℕ) (x : κ) :
    genRead (gens l) c x = stateAt l c x := by
  induction l using List.reverseRecOn with
  | nil => simp [genRead, gens_nil, stateAt, stateOf]
  | append_singleton l e ih =>
    rw [gens_append_singleton]
    unfold genRead at ih ⊢
    rcases Nat.lt_or_ge c (l.length + 1) with hc | hc
    · rw [find?_landGen_of_stable (rs := gens l) (p := l.length + 1) (e := e) (q := selects c x)
        (fun r ↦ selects_closeAt_of_lt x e.1 hc r)
        (by simp [selects, Gen.aliveAt, Nat.not_le.2 hc]), ih,
        stateAt_append [e] (Nat.le_of_lt_succ hc)]
    · have hlen : (l ++ [e]).length ≤ c := by simpa using hc
      rw [stateAt_of_length_le hlen, stateOf_append_singleton]
      by_cases hx : x = e.1
      · subst hx
        rw [find?_landGen_of_new (rs := gens l) (p := l.length + 1) (e := e)
          (q := selects c e.1) (fun r hr ↦ selects_closeAt_self hc (died_le_of_mem_gens hr))
          (by simp [selects, Gen.aliveAt, hc])]
        simp only [Option.map_some, Function.update_self]
      · rw [find?_landGen_of_stable (rs := gens l) (p := l.length + 1) (e := e)
          (q := selects c x) (fun r ↦ selects_closeAt_of_ne hx c _ r)
          (by simp [selects, Ne.symm hx]), ih, Function.update_of_ne hx,
          stateAt_of_length_le (Nat.le_of_succ_le hc)]

/-- SNP-4 At the head cut the generational store reads the store rewritten in place. -/
theorem genRead_gens_length (l : List (κ × β)) (x : κ) :
    genRead (gens l) l.length x = stateOf l x := by
  rw [genRead_gens, stateAt_length]

/-- SNP-1 The generational store read at a cut inside the chain does not change when the chain
grows, though the growth writes closing stamps into it. -/
theorem genRead_gens_append {l : List (κ × β)} (t : List (κ × β)) {c : ℕ} (h : c ≤ l.length)
    (x : κ) : genRead (gens (l ++ t)) c x = genRead (gens l) c x := by
  rw [genRead_gens, genRead_gens, stateAt_append t h]

theorem length_filter_landGen_of_stable {rs : List (Gen κ β)} {p : ℕ} {e : κ × β}
    {q : Gen κ β → Bool} (hq : ∀ r, q (closeAt e.1 p r) = q r)
    (hnew : q ⟨e.1, e.2, p, none⟩ = false) :
    ((landGen rs p e).filter q).length = (rs.filter q).length := by
  have hcomp : q ∘ closeAt e.1 p = q := funext hq
  unfold landGen
  rw [List.filter_append, List.filter_map, hcomp]
  simp [hnew]

theorem length_filter_landGen_of_new {rs : List (Gen κ β)} {p : ℕ} {e : κ × β}
    {q : Gen κ β → Bool} (hq : ∀ r ∈ rs, q (closeAt e.1 p r) = false)
    (hnew : q ⟨e.1, e.2, p, none⟩ = true) : ((landGen rs p e).filter q).length = 1 := by
  have hnil : (rs.map (closeAt e.1 p)).filter q = [] := by
    rw [List.filter_eq_nil_iff]
    intro r hr
    obtain ⟨r', hr', rfl⟩ := List.mem_map.1 hr
    simp [hq r' hr']
  unfold landGen
  rw [List.filter_append, hnil]
  simp [hnew]

/-- SNP-5 At most one generation of a key is alive at a cut: the snapshot of a keyed store is a
transversal of its chains. -/
theorem length_filter_selects_le_one (l : List (κ × β)) (c : ℕ) (x : κ) :
    ((gens l).filter (selects c x)).length ≤ 1 := by
  induction l using List.reverseRecOn with
  | nil => simp [gens_nil]
  | append_singleton l e ih =>
    rw [gens_append_singleton]
    rcases Nat.lt_or_ge c (l.length + 1) with hc | hc
    · exact (length_filter_landGen_of_stable (rs := gens l) (p := l.length + 1) (e := e)
        (q := selects c x) (fun r ↦ selects_closeAt_of_lt x e.1 hc r)
        (by simp [selects, Gen.aliveAt, Nat.not_le.2 hc])).le.trans ih
    · by_cases hx : x = e.1
      · subst hx
        exact (length_filter_landGen_of_new (rs := gens l) (p := l.length + 1) (e := e)
          (q := selects c e.1) (fun r hr ↦ selects_closeAt_self hc (died_le_of_mem_gens hr))
          (by simp [selects, Gen.aliveAt, hc])).le
      · exact (length_filter_landGen_of_stable (rs := gens l) (p := l.length + 1) (e := e)
          (q := selects c x) (fun r ↦ selects_closeAt_of_ne hx c _ r)
          (by simp [selects, Ne.symm hx])).le.trans ih

/-- A row a cut selects is kept by every horizon at or under the cut. -/
theorem keeps_of_selects {h c : ℕ} (hc : h ≤ c) {x : κ} {r : Gen κ β}
    (hr : selects c x r = true) : (r.died.all fun d ↦ decide (h < d)) = true := by
  have h2 : (r.died.all fun d ↦ decide (c < d)) = true := by
    simp only [selects, Gen.aliveAt, Bool.and_eq_true] at hr
    exact hr.2.2
  cases hd : r.died with
  | none => rfl
  | some d =>
    rw [hd] at h2
    simp only [Option.all_some, decide_eq_true_eq] at h2 ⊢
    omega

theorem find?_prune {h c : ℕ} (hc : h ≤ c) (rs : List (Gen κ β)) (x : κ) :
    (prune h rs).find? (selects c x) = rs.find? (selects c x) := by
  induction rs with
  | nil => rfl
  | cons r rs ih =>
    by_cases hk : (r.died.all fun d ↦ decide (h < d)) = true
    · have e : prune h (r :: rs) = r :: prune h rs := by simp [prune, hk]
      rw [e, List.find?_cons, List.find?_cons, ih]
    · have hs : ¬selects c x r = true := fun hs ↦ hk (keeps_of_selects hc hs)
      have e : prune h (r :: rs) = prune h rs := by simp [prune, hk]
      rw [e, List.find?_cons_of_neg hs, ih]

/-- SNP-10 Retention is exact from the horizon on: dropping the generations closed at or under
a horizon changes no read at a cut at or past it. -/
theorem genRead_prune {h c : ℕ} (hc : h ≤ c) (rs : List (Gen κ β)) (x : κ) :
    genRead (prune h rs) c x = genRead rs c x := by
  unfold genRead
  rw [find?_prune hc]

/-- SNP-10 So the pruned generational store read at a cut from the horizon on is the state
recomputed from the whole prefix, though the prefix is no longer held. -/
theorem genRead_prune_gens {h c : ℕ} (hc : h ≤ c) (l : List (κ × β)) (x : κ) :
    genRead (prune h (gens l)) c x = stateAt l c x := by
  rw [genRead_prune hc, genRead_gens]

/-- SNP-10 Under the horizon the pruned store is never wrong: a value it returns at a cut is the
value the key held at the cut. What it has lost it reads as absent. -/
theorem stateAt_of_genRead_prune {h c : ℕ} {l : List (κ × β)} {x : κ} {v : β}
    (hv : genRead (prune h (gens l)) c x = some v) : stateAt l c x = some v := by
  rw [← genRead_gens]
  unfold genRead at hv ⊢
  obtain ⟨r, hr, rfl⟩ := Option.map_eq_some_iff.1 hv
  have hsel : selects c x r = true := List.find?_some hr
  have hmem : r ∈ gens l := List.mem_of_mem_filter (List.mem_of_find?_eq_some hr)
  have hfil : r ∈ (gens l).filter (selects c x) := List.mem_filter.2 ⟨hmem, hsel⟩
  have hlen := length_filter_selects_le_one l c x
  have heq : (gens l).filter (selects c x) = [r] := by
    rcases hf : (gens l).filter (selects c x) with _ | ⟨a, _ | ⟨b, t⟩⟩
    · rw [hf] at hfil
      exact absurd hfil List.not_mem_nil
    · rw [hf] at hfil
      rw [List.mem_singleton.1 hfil]
    · rw [hf] at hlen
      simp at hlen
  rw [← List.head?_filter, heq]
  rfl

omit [DecidableEq κ] in
/-- SNP-10 Horizons compose: pruning at two horizons is pruning at the later one, so a horizon
only ever advances. -/
theorem prune_prune (h h' : ℕ) (rs : List (Gen κ β)) :
    prune h (prune h' rs) = prune (max h h') rs := by
  unfold prune
  rw [List.filter_filter]
  refine List.filter_congr fun r _ ↦ ?_
  cases r.died with
  | none => rfl
  | some d => simp [max_lt_iff]

/-- SNP-10 Retention commutes with growth: a store pruned at a horizon and then landed on, past
the horizon, is the landed store pruned at the horizon. -/
theorem prune_landGen {h p : ℕ} (hp : h < p) (rs : List (Gen κ β)) (e : κ × β) :
    prune h (landGen rs p e) = landGen (prune h rs) p e := by
  have hq : (fun r : Gen κ β ↦ r.died.all fun d ↦ decide (h < d)) ∘ closeAt e.1 p
      = fun r ↦ r.died.all fun d ↦ decide (h < d) := by
    funext r
    simp only [Function.comp_apply, closeAt]
    split_ifs with hr
    · simp [hr.2, hp]
    · rfl
  unfold landGen prune
  rw [List.filter_append, List.filter_map, hq]
  simp

/-- SNP-4 At the head cut nothing is sealed: a chain of landings and retires serves what the
store rewritten in place holds live. -/
theorem servedAt_length (l : List (κ × Option β)) (x : κ) :
    servedAt l l.length x = (stateOf l x).join := by
  simp [servedAt, sealedAt, stateAt_length]

/-- SNP-7 What is served at a cut is what the key held at the cut: the seal only withholds. -/
theorem stateAt_of_servedAt {l : List (κ × Option β)} {c : ℕ} {x : κ} {v : β}
    (h : servedAt l c x = some v) : stateAt l c x = some (some v) := by
  by_cases hs : sealedAt l c x = true
  · simp [servedAt, hs] at h
  · simp only [servedAt, hs] at h
    exact Option.join_eq_some_iff.1 h

theorem sealedAt_append {l : List (κ × Option β)} (t : List (κ × Option β)) {c : ℕ}
    (hc : c ≤ l.length) (x : κ) :
    sealedAt (l ++ t) c x = (sealedAt l c x || t.any fun e ↦ decide (e.1 = x) && e.2.isNone) := by
  unfold sealedAt
  rw [List.drop_append_of_le_length hc, List.any_append]

/-- SNP-7 Erasure dominance for a retire: once the chain retires a key, no cut before the
retire serves the key. -/
theorem servedAt_append_of_retire {l t : List (κ × Option β)} {c : ℕ} {x : κ}
    (hc : c ≤ l.length) (h : (x, none) ∈ t) : servedAt (l ++ t) c x = none := by
  have hs : sealedAt (l ++ t) c x = true := by
    rw [sealedAt_append t hc, Bool.or_eq_true]
    exact Or.inr (List.any_eq_true.2 ⟨(x, none), h, by simp⟩)
  simp only [servedAt, hs, ↓reduceIte]

/-- SNP-7 Append invariance under the seal: growth that does not retire the key changes nothing
served of it at a cut inside the chain. -/
theorem servedAt_append_of_no_retire {l t : List (κ × Option β)} {c : ℕ} {x : κ}
    (hc : c ≤ l.length) (h : (x, none) ∉ t) : servedAt (l ++ t) c x = servedAt l c x := by
  have ht : (t.any fun e ↦ decide (e.1 = x) && e.2.isNone) = false := by
    rw [Bool.eq_false_iff]
    intro h'
    obtain ⟨⟨e1, e2⟩, he, hq⟩ := List.any_eq_true.1 h'
    simp only [Bool.and_eq_true, decide_eq_true_eq, Option.isNone_iff_eq_none] at hq
    obtain ⟨rfl, rfl⟩ := hq
    exact h he
  unfold servedAt
  rw [sealedAt_append t hc, ht, Bool.or_false, stateAt_append t hc]

/-- SNP-7 Growth of the chain changes a served value only by removing it. -/
theorem servedAt_of_append {l t : List (κ × Option β)} {c : ℕ} {x : κ} {v : β}
    (hc : c ≤ l.length) (h : servedAt (l ++ t) c x = some v) : servedAt l c x = some v := by
  by_cases ht : (x, none) ∈ t
  · rw [servedAt_append_of_retire hc ht] at h
    exact absurd h (by simp)
  · rwa [servedAt_append_of_no_retire hc ht] at h

theorem isSome_join_foldl {t : List (κ × Option β)} {m : κ → Option (Option β)} {x : κ}
    (hm : ((m x).join).isSome = true) (ht : ∀ e ∈ t, e.1 = x → e.2.isSome = true) :
    (((t.foldl (fun (m : κ → Option (Option β)) (e : κ × Option β) ↦
      Function.update m e.1 (some e.2)) m) x).join).isSome = true := by
  induction t generalizing m with
  | nil => exact hm
  | cons e t ih =>
    refine ih ?_ fun e' he' ↦ ht e' (List.mem_cons_of_mem _ he')
    change ((Function.update m e.1 (some e.2) x).join).isSome = true
    by_cases hx : e.1 = x
    · have he := ht e List.mem_cons_self hx
      rw [← hx, Function.update_self]
      simpa using he
    · rw [Function.update_of_ne (Ne.symm hx)]
      exact hm

/-- SNP-7 Under the looser seal too, a key that is not live now is served at no cut. -/
theorem servedNow_of_not_live {l : List (κ × Option β)} {x : κ}
    (h : (stateOf l x).join = none) (c : ℕ) : servedNow l c x = none := by
  simp [servedNow, h]

/-- SNP-4 At the head cut the looser seal serves what the store rewritten in place holds
live. -/
theorem servedNow_length (l : List (κ × Option β)) (x : κ) :
    servedNow l l.length x = (stateOf l x).join := by
  unfold servedNow
  rw [stateAt_length]
  cases (stateOf l x).join <;> rfl

/-- SNP-7 The two seals are ordered: what the seal that a retire closes for good serves, the
seal that a later landing lifts serves too. Whichever is chosen, the other bounds it. -/
theorem servedNow_of_servedAt {l : List (κ × Option β)} {c : ℕ} {x : κ} {v : β}
    (h : servedAt l c x = some v) : servedNow l c x = some v := by
  have hstate := stateAt_of_servedAt h
  have hseal : ∀ e ∈ l.drop c, e.1 = x → e.2.isSome = true := by
    intro e he hx
    by_contra hnone
    have hs : sealedAt l c x = true :=
      List.any_eq_true.2 ⟨e, he, by simpa [hx] using hnone⟩
    simp [servedAt, hs] at h
  have hfold := stateAt_eq_foldl l (Nat.le_max_left c l.length)
  rw [stateAt_of_length_le (Nat.le_max_right c l.length),
    List.take_of_length_le (Nat.le_max_right c l.length)] at hfold
  have hlive : ((stateOf l x).join).isSome = true := by
    rw [hfold]
    exact isSome_join_foldl (by rw [hstate]; rfl) hseal
  have hnot : ((stateOf l x).join).isNone = false := by
    cases hj : (stateOf l x).join with
    | none => rw [hj] at hlive; exact absurd hlive (by simp)
    | some w => rfl
  simp only [servedNow, hnot, Bool.false_eq_true, ↓reduceIte, hstate, Option.join_some]

theorem sinceRetire_append_singleton (l : List (κ × Option β)) (e : κ × Option β) (x : κ) :
    sinceRetire (l ++ [e]) x
      = if e.1 = x then (e.2.elim [] fun v ↦ sinceRetire l x ++ [v]) else sinceRetire l x := by
  simp only [sinceRetire, List.foldl_append, List.foldl_cons, List.foldl_nil]

theorem foldl_sinceRetire_of_retire (t : List (κ × Option β)) (x : κ) (acc : List β) :
    ((x, none) :: t).foldl
        (fun acc e ↦ if e.1 = x then (e.2.elim [] fun v ↦ acc ++ [v]) else acc) acc
      = sinceRetire t x := by
  simp [sinceRetire]

/-- SNP-7 A retire closes the key's history: the versions landed before a retire of the key
are in no later history. -/
theorem sinceRetire_append_retire (l t : List (κ × Option β)) (x : κ) :
    sinceRetire (l ++ (x, none) :: t) x = sinceRetire t x := by
  unfold sinceRetire
  rw [List.foldl_append]
  exact foldl_sinceRetire_of_retire t x _

/-- The last version of a key's present life is the value the key holds live. -/
theorem getLast?_sinceRetire (l : List (κ × Option β)) (x : κ) :
    (sinceRetire l x).getLast? = (stateOf l x).join := by
  induction l using List.reverseRecOn with
  | nil => rfl
  | append_singleton l e ih =>
    rw [sinceRetire_append_singleton, stateOf_append_singleton]
    by_cases hx : e.1 = x
    · subst hx
      rw [Function.update_self]
      cases e.2 <;> simp
    · rw [Function.update_of_ne (Ne.symm hx)]
      simpa [hx] using ih

/-- SNP-7 The history served at a cut ends at the value served there: the seal that withholds
a key's value withholds its versions with it. -/
theorem getLast?_historyAt (l : List (κ × Option β)) (c : ℕ) (x : κ) :
    (historyAt l c x).getLast? = servedAt l c x := by
  unfold historyAt servedAt
  split_ifs
  · rfl
  · exact getLast?_sinceRetire _ x

/-- SNP-7 Once the chain retires a key, no cut before the retire serves any version of it. -/
theorem historyAt_append_of_retire {l t : List (κ × Option β)} {c : ℕ} {x : κ}
    (hc : c ≤ l.length) (h : (x, none) ∈ t) : historyAt (l ++ t) c x = [] := by
  have hs : sealedAt (l ++ t) c x = true := by
    rw [sealedAt_append t hc, Bool.or_eq_true]
    exact Or.inr (List.any_eq_true.2 ⟨(x, none), h, by simp⟩)
  simp only [historyAt, hs, ↓reduceIte]

/-- SNP-7 At every cut after a retire of a key, the head included, the history served of the
key holds only versions landed after that retire: a new item under a retired identity does not
bring the retired item's versions with it. -/
theorem historyAt_of_retire_inside (l t : List (κ × Option β)) (x : κ) {c : ℕ}
    (hc : l.length + 1 ≤ c) :
    historyAt (l ++ (x, none) :: t) c x
      = if sealedAt (l ++ (x, none) :: t) c x then []
        else sinceRetire (t.take (c - (l.length + 1))) x := by
  unfold historyAt
  split_ifs
  · rfl
  · have h1 : (l ++ (x, none) :: t).take c
        = l ++ (x, none) :: t.take (c - (l.length + 1)) := by
      rw [List.take_append, List.take_of_length_le (by omega),
        show c - l.length = (c - (l.length + 1)) + 1 by omega, List.take_succ_cons]
    rw [h1, sinceRetire_append_retire]

/-- SNP-4 At the head cut the history served is the key's present life. -/
theorem historyAt_length (l : List (κ × Option β)) (x : κ) :
    historyAt l l.length x = sinceRetire l x := by
  simp [historyAt, sealedAt]

omit [DecidableEq κ] in
theorem holes_append (E : κ × β → Bool) (l t : List (κ × β)) :
    holes E (l ++ t) = holes E l ++ holes E t :=
  List.map_append

/-- The store rewritten in place, with holes: each key's last write, erased or not. -/
theorem stateOf_holes (E : κ × β → Bool) (l : List (κ × β)) (x : κ) :
    stateOf (holes E l) x = (stateOf l x).map fun v ↦ if E (x, v) then none else some v := by
  induction l using List.reverseRecOn with
  | nil => rfl
  | append_singleton l e ih =>
    rw [holes_append]
    change stateOf (holes E l ++ [(e.1, if E e then none else some e.2)]) x = _
    rw [stateOf_append_singleton, stateOf_append_singleton]
    by_cases hx : e.1 = x
    · subst hx
      simp
    · rw [Function.update_of_ne (Ne.symm hx), Function.update_of_ne (Ne.symm hx)]
      exact ih

/-- SNP-7 The keyed read under an erasure: on a chain whose holes keep their keys, the read of
a key at a cut is its last write at or under the cut, as a hole when that write is erased. It is
never an earlier write of the key and never a later one. -/
theorem stateAt_holes (E : κ × β → Bool) (l : List (κ × β)) (c : ℕ) (x : κ) :
    stateAt (holes E l) c x = (stateAt l c x).map fun v ↦ if E (x, v) then none else some v := by
  unfold stateAt
  rw [holes, ← List.map_take]
  exact stateOf_holes E _ x

/-- SNP-7 A key whose head at the cut is erased reads as erased at that cut. -/
theorem stateAt_holes_of_erased {E : κ × β → Bool} {l : List (κ × β)} {c : ℕ} {x : κ} {v : β}
    (h : stateAt l c x = some v) (hE : E (x, v) = true) :
    stateAt (holes E l) c x = some none := by
  rw [stateAt_holes, h, Option.map_some, hE]
  rfl

/-- SNP-7 No keyed read at any cut returns an erased value. -/
theorem not_erased_of_stateAt_holes {E : κ × β → Bool} {l : List (κ × β)} {c : ℕ} {x : κ}
    {v : β} (h : stateAt (holes E l) c x = some (some v)) :
    stateAt l c x = some v ∧ E (x, v) = false := by
  rw [stateAt_holes] at h
  cases hs : stateAt l c x with
  | none => rw [hs] at h; exact absurd h (by simp)
  | some w =>
    rw [hs, Option.map_some] at h
    cases hE : E (x, w)
    · rw [hE] at h
      simp only [Bool.false_eq_true, ↓reduceIte, Option.some.injEq] at h
      exact ⟨by rw [h], by rw [← h]; exact hE⟩
    · rw [hE] at h
      simp at h

/-- SNP-7 The three reads agree on a chain with holes: the generational store of the chain with
holes, read at a cut, is the keyed read under the erasure. -/
theorem genRead_gens_holes (E : κ × β → Bool) (l : List (κ × β)) (c : ℕ) (x : κ) :
    genRead (gens (holes E l)) c x
      = (stateAt l c x).map fun v ↦ if E (x, v) then none else some v := by
  rw [genRead_gens, stateAt_holes]

/-- SNP-7 And so is the seek by key: the last row of the key at or under the cut, hole or
not. -/
theorem lastWrite_holes (E : κ × β → Bool) (l : List (κ × β)) (c : ℕ) (x : κ) :
    lastWrite (holes E l) c x
      = (stateAt l c x).map fun v ↦ if E (x, v) then none else some v := by
  rw [← stateAt_eq_lastWrite, stateAt_holes]

end Generations

/-! ### SNP-6 The grant -/

section Grant

variable {K α : Type*}

/-- SNP-6 A snapshot under a grant is append invariant. -/
theorem snapshot_grow (G : K → Prop) [DecidablePred G] (p : α → Bool) {s : Store K α}
    (t : Store K α) {c : Cut K} (h : c ≤ head s) :
    snapshot G p (grow s t) c = snapshot G p s c := by
  unfold snapshot
  rw [readAt_grow t h]

/-- Restricting twice is restricting to the chains both grants name and the events both
let through. -/
theorem restrict_restrict (G G' : K → Prop) [DecidablePred G] [DecidablePred G']
    (p p' : α → Bool) (t : Store K α) :
    restrict G p (restrict G' p' t) = restrict (fun k ↦ G k ∧ G' k) (fun a ↦ p a && p' a) t := by
  funext k
  by_cases h : G k <;> by_cases h' : G' k <;> simp [restrict, h, h', List.filter_filter]

/-- SNP-6 Grant restriction: a narrower grant's snapshot is the restriction of a wider one's,
at every cut. What a wider grant was shown at a cut bounds what a narrower one is shown there. -/
theorem snapshot_narrow {G G' : K → Prop} [DecidablePred G] [DecidablePred G']
    {p p' : α → Bool} (hG : ∀ k, G k → G' k) (hp : ∀ a, p a = true → p' a = true)
    (s : Store K α) (c : Cut K) :
    snapshot G p s c = restrict G p (snapshot G' p' s c) := by
  funext k
  by_cases h : G k
  · have h' := hG k h
    simp only [snapshot, restrict, h, h', ↓reduceIte, List.filter_filter]
    refine List.filter_congr fun a _ ↦ ?_
    cases hpa : p a
    · rfl
    · simp [hp a hpa]
  · simp [snapshot, restrict, h]

/-- SNP-6 Noninterference: a snapshot under a grant reads only the chains the grant names, and
of the cut only its positions on them. Two stores that agree on those chains, at two cuts that
agree on them, are one snapshot. -/
theorem snapshot_congr (G : K → Prop) [DecidablePred G] (p : α → Bool) {s s' : Store K α}
    {c c' : Cut K} (hs : ∀ k, G k → s k = s' k) (hc : ∀ k, G k → c k = c' k) :
    snapshot G p s c = snapshot G p s' c' := by
  funext k
  by_cases h : G k
  · simp [snapshot, restrict, readAt, h, hs k h, hc k h]
  · simp [snapshot, restrict, h]

/-- SNP-4 At the head cut a snapshot is the grant's restriction of the store. -/
theorem snapshot_head (G : K → Prop) [DecidablePred G] (p : α → Bool) (s : Store K α) :
    snapshot G p s (head s) = restrict G p s := by
  unfold snapshot
  rw [readAt_head]

/-- SNP-6 Restricting to chains commutes with the cut: a grant that names whole chains may be
applied before the read or after it. -/
theorem restrict_readAt (G : K → Prop) [DecidablePred G] (s : Store K α) (c : Cut K) :
    restrict G (fun _ ↦ true) (readAt s c) = readAt (restrict G (fun _ ↦ true) s) c := by
  funext k
  by_cases h : G k <;> simp [restrict, readAt, h]

/-- SNP-1 for the composite reader: what an asker is shown at a cut inside the store is the
same after any growth. -/
theorem shown_grow (G : K → Prop) [DecidablePred G] (p E : α → Bool) {s : Store K α}
    (t : Store K α) {c : Cut K} (h : c ≤ head s) :
    shown G p E (grow s t) c = shown G p E s c :=
  snapshot_grow G _ t h

/-- SNP-7 for the composite reader: no erased event is shown at any cut, under any grant. -/
theorem not_erased_of_mem_shown {G : K → Prop} [DecidablePred G] {p E : α → Bool}
    {s : Store K α} {c : Cut K} {k : K} {a : α} (h : a ∈ shown G p E s c k) : E a = false := by
  unfold shown snapshot restrict at h
  split_ifs at h
  · exact (by simpa using (List.mem_filter.1 h).2 : p a = true ∧ E a = false).2
  · simp at h

/-- SNP-6 for the composite reader: under a narrower grant and a larger erasure, what is shown
is the restriction of what the wider grant is shown under the smaller erasure. -/
theorem shown_narrow {G G' : K → Prop} [DecidablePred G] [DecidablePred G']
    {p p' E E' : α → Bool} (hG : ∀ k, G k → G' k) (hp : ∀ a, p a = true → p' a = true)
    (hE : ∀ a, E' a = true → E a = true) (s : Store K α) (c : Cut K) :
    shown G p E s c = restrict G (fun a ↦ p a && !E a) (shown G' p' E' s c) :=
  snapshot_narrow hG (fun a ha ↦ by
    rw [Bool.and_eq_true] at ha ⊢
    refine ⟨hp a ha.1, ?_⟩
    cases h : E' a
    · rfl
    · have := hE a h
      simp [this] at ha) s c

/-- SNP-4 for the composite reader: at the head cut it is the grant's restriction of the store
without the erased events. -/
theorem shown_head (G : K → Prop) [DecidablePred G] (p E : α → Bool) (s : Store K α) :
    shown G p E s (head s) = restrict G (fun a ↦ p a && !E a) s :=
  snapshot_head G _ s

end Grant

/-! ### SNP-7 The erasure -/

section Erasure

variable {K α β C : Type*}

/-- SNP-7 The store with holes keeps every position. -/
theorem head_redact (E : α → Bool) (s : Store K α) : head (redact E s) = head s :=
  funext fun _ ↦ List.length_map _

/-- SNP-7 Erasing with holes commutes with the cut: the positions of the events that stay are
the positions they had. -/
theorem redact_readAt (E : α → Bool) (s : Store K α) (c : Cut K) :
    readAt (redact E s) c = redact E (readAt s c) :=
  funext fun _ ↦ List.map_take.symm

theorem reduceOption_map_hole (E : α → Bool) (l : List α) :
    (l.map fun a ↦ if E a then none else some a).reduceOption = l.filter fun a ↦ !E a := by
  induction l with
  | nil => rfl
  | cons a l ih =>
    cases h : E a
    · simp [h, List.reduceOption_cons_of_some, ih]
    · simp [h, List.reduceOption_cons_of_none, ih]

/-- SNP-7 What is visible at a cut is the store with holes read at the cut, the holes dropped. -/
theorem visible_eq_reduceOption (E : α → Bool) (s : Store K α) (c : Cut K) (k : K) :
    visible E s c k = (readAt (redact E s) c k).reduceOption := by
  rw [redact_readAt]
  exact (reduceOption_map_hole E _).symm

/-- SNP-7 Erasure dominance: no erased event is visible at any cut. -/
theorem not_erased_of_mem_visible {E : α → Bool} {s : Store K α} {c : Cut K} {k : K} {a : α}
    (h : a ∈ visible E s c k) : E a = false := by
  simpa using (List.mem_filter.1 h).2

/-- SNP-7 A larger erasure shows a sublist of what a smaller one shows, at every cut. -/
theorem visible_sublist {E E' : α → Bool} (h : ∀ a, E a = true → E' a = true)
    (s : Store K α) (c : Cut K) (k : K) : (visible E' s c k).Sublist (visible E s c k) := by
  refine List.monotone_filter_right _ fun a ha ↦ ?_
  cases hE : E a
  · rfl
  · simp [h a hE] at ha

/-- SNP-2 under an erasure: what is visible at an earlier cut is a prefix of what is visible
at a later one. -/
theorem visible_mono (E : α → Bool) (s : Store K α) {c d : Cut K} (h : c ≤ d) (k : K) :
    visible E s c k <+: visible E s d k :=
  (List.take_prefix_take_left (h k)).filter _

/-- SNP-4 under an erasure: at the head cut what is visible is the store without the erased
events. -/
theorem visible_head (E : α → Bool) (s : Store K α) : visible E s (head s) = compact E s :=
  funext fun _ ↦ congrArg (List.filter fun a ↦ !E a) List.take_length

/-- SNP-1 under an erasure: growth of the store changes nothing visible at a cut inside it. -/
theorem visible_grow (E : α → Bool) {s : Store K α} (t : Store K α) {c : Cut K}
    (h : c ≤ head s) : visible E (grow s t) c = visible E s c :=
  funext fun k ↦ congrArg (List.filter fun a ↦ !E a) (List.take_append_of_le_length (h k))

/-- SNP-7 Two stores that differ only in erased events show the same at every cut. -/
theorem visible_congr {E : α → Bool} {s s' : Store K α} (h : redact E s = redact E s')
    (c : Cut K) : visible E s c = visible E s' c := by
  funext k
  rw [visible_eq_reduceOption, visible_eq_reduceOption, h]

/-- SNP-7 So erased content is an argument of no read: every derivation of what is visible at
a cut is the same on two stores that differ only in erased events. -/
theorem erased_invisible (D : Store K α → β) {E : α → Bool} {s s' : Store K α}
    (h : redact E s = redact E s') (c : Cut K) : D (visible E s c) = D (visible E s' c) :=
  congrArg D (visible_congr h c)

/-- SNP-7 A kept derived row is served exactly when none of its sources is erased. -/
theorem mem_serve_iff {E : α → Bool} {rows : List (List α × β)} {r : List α × β} :
    r ∈ serve E rows ↔ r ∈ rows ∧ ∀ a ∈ r.1, E a = false := by
  simp [serve, List.mem_filter]

/-- SNP-7 A larger erasure serves a sublist of the kept rows. -/
theorem serve_sublist {E E' : α → Bool} (h : ∀ a, E a = true → E' a = true)
    (rows : List (List α × β)) : (serve E' rows).Sublist (serve E rows) := by
  refine List.monotone_filter_right _ fun r hr ↦ ?_
  rw [List.all_eq_true] at hr ⊢
  intro a ha
  have h1 := hr a ha
  cases hE : E a
  · rfl
  · simp [h a hE] at h1

/-- SNP-9 An erasure on a committed store keeps every commitment in its place. -/
theorem commitments_purge (E : α → Bool) (t : Store K (C × Option α)) :
    commitments (purge E t) = commitments t := by
  funext k
  simp [commitments, purge, Function.comp_def]

/-- SNP-9 What a reader reads of a committed store after an erasure is the store with holes. -/
theorem contents_purge_committed (commit : α → C) (E : α → Bool) (s : Store K α) :
    contents (purge E (committed commit s)) = redact E s := by
  funext k
  simp only [contents, purge, committed, redact, List.map_map]
  refine List.map_congr_left fun a _ ↦ ?_
  cases h : E a <;> simp [h]

end Erasure

/-! ### SNP-8 Consistent cuts -/

section Consistency

variable {K : Type*} {R : K → ℕ → K → ℕ → Prop}

/-- The empty cut is consistent. -/
theorem consistent_zero : Consistent R fun _ ↦ 0 := fun _ _ _ _ _ h ↦ absurd h (Nat.not_lt_zero _)

/-- SNP-8 The consistent cuts are the clock's cuts (CLK-2) among the frontier cuts: a cut is
consistent exactly when the events under its frontier are a down-set of the order the append
chains and the reads-from references generate. -/
theorem consistent_iff_isCut (R : K → ℕ → K → ℕ → Prop) (c : Cut K) :
    Consistent R c ↔ Clock.IsCut (generator R) (Clock.frontierCut Prod.fst Prod.snd c) := by
  rw [Clock.isCut_iff_not_crossed]
  constructor
  · rintro h ⟨a, b, hab, hb, ha⟩
    have hb' : b.2 < c b.1 := hb
    rcases hab with ⟨h1, h2⟩ | hR
    · refine ha ?_
      change a.2 < c a.1
      rw [h1]
      exact lt_trans h2 hb'
    · exact ha (h _ _ _ _ hR hb')
  · intro h k i k' j hR hi
    by_contra hj
    exact h ⟨(k', j), (k, i), Or.inr hR, hi, hj⟩

/-- Closure under the meet is CLK-2's: the frontier cut of a pointwise minimum is the
intersection of the two cuts (`Clock.IsCut.frontier_inf`), read here through
`consistent_iff_isCut`. -/
theorem Consistent.inf {c d : Cut K} (hc : Consistent R c) (hd : Consistent R d) :
    Consistent R (c ⊓ d) :=
  (consistent_iff_isCut R _).2
    (Clock.IsCut.frontier_inf Prod.fst Prod.snd ((consistent_iff_isCut R c).1 hc)
      ((consistent_iff_isCut R d).1 hd))

/-- And under the join, CLK-2's again (`Clock.IsCut.frontier_sup`). -/
theorem Consistent.sup {c d : Cut K} (hc : Consistent R c) (hd : Consistent R d) :
    Consistent R (c ⊔ d) :=
  (consistent_iff_isCut R _).2
    (Clock.IsCut.frontier_sup Prod.fst Prod.snd ((consistent_iff_isCut R c).1 hc)
      ((consistent_iff_isCut R d).1 hd))

/-- The consistent cuts as a sublattice of the cuts, so a distributive lattice: CLK-2's
closure, packaged. -/
def consistentCuts (R : K → ℕ → K → ℕ → Prop) : Sublattice (Cut K) where
  carrier := {c | Consistent R c}
  supClosed' := fun _ hc _ hd ↦ Consistent.sup hc hd
  infClosed' := fun _ hc _ hd ↦ Consistent.inf hc hd

/-- A frontier resolves to at most one cut. -/
theorem Resolves.unique {f c c' : Cut K} (h : Resolves R f c) (h' : Resolves R f c') : c = c' :=
  le_antisymm (h'.2.2 c h.1 h.2.1) (h.2.2 c' h'.1 h'.2.1)

/-- SNP-8 Resolution is monotone: a later frontier resolves to a later cut. -/
theorem Resolves.mono {f f' c c' : Cut K} (hf : f ≤ f') (h : Resolves R f c)
    (h' : Resolves R f' c') : c ≤ c' :=
  h'.2.2 c h.1 (h.2.1.trans hf)

/-- A consistent frontier resolves to itself. -/
theorem resolves_self {f : Cut K} (h : Consistent R f) : Resolves R f f :=
  ⟨h, le_rfl, fun _ _ hd ↦ hd⟩

/-- SNP-8 Every frontier resolves: among the consistent cuts under it there is a greatest. -/
theorem exists_resolves (R : K → ℕ → K → ℕ → Prop) (f : Cut K) : ∃ c, Resolves R f c := by
  have hne : ∀ k, (reached R f k).Nonempty := fun k ↦
    ⟨0, fun _ ↦ 0, consistent_zero, fun _ ↦ Nat.zero_le _, rfl⟩
  have hbdd : ∀ k, BddAbove (reached R f k) := fun k ↦
    ⟨f k, by rintro n ⟨d, -, hd, rfl⟩; exact hd k⟩
  refine ⟨fun k ↦ sSup (reached R f k), ?_, ?_, ?_⟩
  · intro k i k' j hR hi
    obtain ⟨d, hd, hdf, hdk⟩ := Nat.sSup_mem (hne k) (hbdd k)
    have hj : j < d k' := hd k i k' j hR (by rw [hdk]; exact hi)
    exact lt_of_lt_of_le hj (le_csSup (hbdd k') ⟨d, hd, hdf, rfl⟩)
  · intro k
    exact csSup_le (hne k) (by rintro n ⟨d, -, hd, rfl⟩; exact hd k)
  · intro d hd hdf k
    exact le_csSup (hbdd k) ⟨d, hd, hdf, rfl⟩

/-- SNP-8 Consistency is append invariant: when the references a store gains by growing all
start at events at or past its old head, a cut inside the old head that was consistent stays
consistent. -/
theorem Consistent.of_grown {R' : K → ℕ → K → ℕ → Prop} {h c : Cut K}
    (hR : ∀ k i k' j, R' k i k' j → R k i k' j ∨ h k ≤ i) (hc : c ≤ h)
    (hcons : Consistent R c) : Consistent R' c := fun k i k' j hr hi ↦
  (hR k i k' j hr).elim (fun h0 ↦ hcons k i k' j h0 hi)
    fun hle ↦ absurd (lt_of_lt_of_le hi (hc k)) (not_lt.2 hle)

/-- SNP-10 Every frontier resolves among the positions the chains serve, when every chain serves
its empty prefix: among the consistent cuts under the frontier with every position served there
is a greatest. This is the cut a read is taken at when a store cannot serve the cut asked. -/
theorem exists_resolvesIn (R : K → ℕ → K → ℕ → Prop) {S : K → Set ℕ} (h0 : ∀ k, 0 ∈ S k)
    (f : Cut K) : ∃ c, ResolvesIn R S f c := by
  have hne : ∀ k, (reachedIn R S f k).Nonempty := fun k ↦
    ⟨0, fun _ ↦ 0, consistent_zero, fun k' ↦ h0 k', fun _ ↦ Nat.zero_le _, rfl⟩
  have hbdd : ∀ k, BddAbove (reachedIn R S f k) := fun k ↦
    ⟨f k, by rintro n ⟨d, -, -, hd, rfl⟩; exact hd k⟩
  refine ⟨fun k ↦ sSup (reachedIn R S f k), ?_, ?_, ?_, ?_⟩
  · intro k i k' j hR hi
    obtain ⟨d, hd, hS, hdf, hdk⟩ := Nat.sSup_mem (hne k) (hbdd k)
    have hj : j < d k' := hd k i k' j hR (by rw [hdk]; exact hi)
    exact lt_of_lt_of_le hj (le_csSup (hbdd k') ⟨d, hd, hS, hdf, rfl⟩)
  · intro k
    obtain ⟨d, -, hS, -, hdk⟩ := Nat.sSup_mem (hne k) (hbdd k)
    change sSup (reachedIn R S f k) ∈ S k
    rw [← hdk]
    exact hS k
  · intro k
    exact csSup_le (hne k) (by rintro n ⟨d, -, -, hd, rfl⟩; exact hd k)
  · intro d hd hS hdf k
    exact le_csSup (hbdd k) ⟨d, hd, hS, hdf, rfl⟩

/-- A frontier resolves among the served positions to at most one cut. -/
theorem ResolvesIn.unique {S : K → Set ℕ} {f c c' : Cut K} (h : ResolvesIn R S f c)
    (h' : ResolvesIn R S f c') : c = c' :=
  le_antisymm (h'.2.2.2 c h.1 h.2.1 h.2.2.1) (h.2.2.2 c' h'.1 h'.2.1 h'.2.2.1)

/-- SNP-10 The cut read rises with what is served and with the frontier: a store that gains a
past, or a later cut asked, never lowers the cut read. -/
theorem ResolvesIn.mono {S S' : K → Set ℕ} {f f' c c' : Cut K} (hS : ∀ k, S k ⊆ S' k)
    (hf : f ≤ f') (h : ResolvesIn R S f c) (h' : ResolvesIn R S' f' c') : c ≤ c' :=
  h'.2.2.2 c h.1 (fun k ↦ hS k (h.2.1 k)) (h.2.2.1.trans hf)

/-- When every position is served the cut read is the resolution of the frontier. -/
theorem resolvesIn_univ {f c : Cut K} :
    ResolvesIn R (fun _ ↦ Set.univ) f c ↔ Resolves R f c := by
  constructor
  · rintro ⟨h1, -, h3, h4⟩
    exact ⟨h1, h3, fun d hd hdf ↦ h4 d hd (fun _ ↦ Set.mem_univ _) hdf⟩
  · rintro ⟨h1, h2, h3⟩
    exact ⟨h1, fun _ ↦ Set.mem_univ _, h2, fun d hd _ hdf ↦ h3 d hd hdf⟩

/-- SNP-10 The cut read is never past the cut asked: it lies under the resolution of the
frontier, so a read under `as of` holds no event from after the cut it names. -/
theorem ResolvesIn.le_resolves {S : K → Set ℕ} {f c c' : Cut K} (h : ResolvesIn R S f c)
    (h' : Resolves R f c') : c ≤ c' :=
  h'.2.2 c h.1 h.2.2.1

/-- A consistent frontier every position of which is served is read as asked. -/
theorem resolvesIn_self {S : K → Set ℕ} {f : Cut K} (h : Consistent R f)
    (hS : ∀ k, f k ∈ S k) : ResolvesIn R S f f :=
  ⟨h, hS, le_rfl, fun _ _ _ hd ↦ hd⟩

/-- SNP-8 A recorded bound is sound: when every true source of an event lies at or under a
recorded one on its chain, a cut consistent for the recorded references is consistent for the
true ones. So a resolver may work from the head a row recorded at its writing. -/
theorem Consistent.of_bound {R' : K → ℕ → K → ℕ → Prop}
    (hb : ∀ k i k' j, R k i k' j → ∃ j', j ≤ j' ∧ R' k i k' j') {c : Cut K}
    (h : Consistent R' c) : Consistent R c := fun k i k' j hr hi ↦ by
  obtain ⟨j', hj, hr'⟩ := hb k i k' j hr
  exact lt_of_le_of_lt hj (h k i k' j' hr' hi)

/-- SNP-10 A chain that no other chain reads can be lowered alone: a consistent cut stays
consistent when its position on such a chain is lowered, the chain's own references pointing
backward. -/
theorem Consistent.update_of_unread [DecidableEq K] {c : Cut K} {x : K} {p : ℕ}
    (hc : Consistent R c) (hp : p ≤ c x) (hx : ∀ k i j, R k i x j → k = x ∧ j ≤ i) :
    Consistent R (Function.update c x p) := fun k i k' j hr hi ↦ by
  have hik : i < c k := by
    by_cases hk : k = x
    · subst hk
      rw [Function.update_self] at hi
      exact lt_of_lt_of_le hi hp
    · rwa [Function.update_of_ne hk] at hi
  by_cases hk' : k' = x
  · subst hk'
    obtain ⟨rfl, hji⟩ := hx k i j hr
    rw [Function.update_self] at hi ⊢
    exact lt_of_le_of_lt hji hi
  · rw [Function.update_of_ne hk']
    exact hc k i k' j hr hik

/-- SNP-10 The local lowering: when the cut asked is consistent and every chain but one serves
its position, and no other chain reads that one, the cut read is the cut asked with that chain
at the greatest position it serves at or under the one asked. Every other chain is read as
asked. The control is a chain that others read (`Witness.record_drags`). -/
theorem resolvesIn_update_of_unread [DecidableEq K] {S : K → Set ℕ} {f : Cut K} {x : K} {p : ℕ}
    (hf : Consistent R f) (hS : ∀ k, k ≠ x → f k ∈ S k)
    (hx : ∀ k i j, R k i x j → k = x ∧ j ≤ i) (hp : p ∈ S x) (hpf : p ≤ f x)
    (hmax : ∀ q ∈ S x, q ≤ f x → q ≤ p) : ResolvesIn R S f (Function.update f x p) := by
  refine ⟨hf.update_of_unread hpf hx, fun k ↦ ?_, fun k ↦ ?_, fun d _ hdS hdf k ↦ ?_⟩
  · by_cases hk : k = x
    · subst hk
      rwa [Function.update_self]
    · rw [Function.update_of_ne hk]
      exact hS k hk
  · by_cases hk : k = x
    · subst hk
      rwa [Function.update_self]
    · rw [Function.update_of_ne hk]
  · by_cases hk : k = x
    · subst hk
      rw [Function.update_self]
      exact hmax _ (hdS k) (hdf k)
    · rw [Function.update_of_ne hk]
      exact hdf k

theorem ResolvesIn.le_on_of_closed {R' : K → ℕ → K → ℕ → Prop} {S S' : K → Set ℕ}
    {f f' c c' : Cut K} (G : K → Prop)
    (hclosed : ∀ k i k' j, G k → R' k i k' j → G k')
    (hR : ∀ k i k' j, G k → R' k i k' j → R k i k' j) (hS : ∀ k, G k → S k ⊆ S' k)
    (h0 : ∀ k, 0 ∈ S' k) (hf : ∀ k, G k → f k ≤ f' k) (h : ResolvesIn R S f c)
    (h' : ResolvesIn R' S' f' c') : ∀ k, G k → c k ≤ c' k := by
  classical
  have hcons : Consistent R' fun k ↦ if G k then c k else 0 := by
    intro k i k' j hr hi
    by_cases hk : G k
    · have hk' := hclosed k i k' j hk hr
      simp only [hk, ↓reduceIte] at hi
      simp only [hk', ↓reduceIte]
      exact h.1 k i k' j (hR k i k' j hk hr) hi
    · simp [hk] at hi
  have hserved : ∀ k, (if G k then c k else 0) ∈ S' k := by
    intro k
    by_cases hk : G k
    · simp only [hk, ↓reduceIte]
      exact hS k hk (h.2.1 k)
    · simp only [hk, ↓reduceIte]
      exact h0 k
  have hle : (fun k ↦ if G k then c k else 0) ≤ f' := by
    intro k
    by_cases hk : G k
    · simp only [hk, ↓reduceIte]
      exact (h.2.2.1 k).trans (hf k hk)
    · simp only [hk, ↓reduceIte]
      exact Nat.zero_le _
  intro k hk
  simpa [hk] using h'.2.2.2 _ hcons hserved hle k

/-- SNP-6 The cut read on the chains a grant names is a function of those chains when they
read from no chain outside them: two stores of references, served positions and frontiers that
agree on such a set of chains resolve to cuts that agree on it. The control is a named chain
that reads an unnamed one (`Witness.resolution_reads_unnamed`). -/
theorem ResolvesIn.eq_on_of_closed {R' : K → ℕ → K → ℕ → Prop} {S S' : K → Set ℕ}
    {f f' c c' : Cut K} (G : K → Prop)
    (hclosed : ∀ k i k' j, G k → R k i k' j → G k')
    (hR : ∀ k i k' j, G k → (R k i k' j ↔ R' k i k' j)) (hS : ∀ k, G k → S k = S' k)
    (h0 : ∀ k, 0 ∈ S k) (h0' : ∀ k, 0 ∈ S' k) (hf : ∀ k, G k → f k = f' k)
    (h : ResolvesIn R S f c) (h' : ResolvesIn R' S' f' c') : ∀ k, G k → c k = c' k :=
  fun k hk ↦ le_antisymm
    (h.le_on_of_closed G (fun a i b j ha hr ↦ hclosed a i b j ha ((hR a i b j ha).2 hr))
      (fun a i b j ha hr ↦ (hR a i b j ha).2 hr) (fun a ha ↦ (hS a ha).subset) h0'
      (fun a ha ↦ (hf a ha).le) h' k hk)
    (h'.le_on_of_closed G hclosed (fun a i b j ha hr ↦ (hR a i b j ha).1 hr)
      (fun a ha ↦ (hS a ha).superset) h0 (fun a ha ↦ (hf a ha).ge) h k hk)

end Consistency

/-! ### SNP-9 Certified cuts -/

section Certified

variable {K α C H : Type*} {step : H → α → H} {h₀ : H}

theorem verifies_certify {s : Store K α} {c : Cut K} (h : c ≤ head s) :
    Verifies step h₀ (certify step h₀ s c) s :=
  ⟨h, fun _ ↦ rfl⟩

/-- SNP-9 A certificate is append invariant: the certificate of a cut of a store verifies on
every extension of the store. -/
theorem verifies_certify_of_extends {s s' : Store K α} {c : Cut K} (h : Extends s s')
    (hc : c ≤ head s) : Verifies step h₀ (certify step h₀ s c) s' :=
  ⟨hc.trans h.head_le,
    fun k ↦ congrArg (chainDigest step h₀) (congrFun (readAt_of_extends h hc) k)⟩

theorem chainDigest_append_singleton (step : H → α → H) (h₀ : H) (l : List α) (a : α) :
    chainDigest step h₀ (l ++ [a]) = step (chainDigest step h₀ l) a := by
  simp only [chainDigest, List.foldl_append, List.foldl_cons, List.foldl_nil]

/-- Under a collision-free step, two chains of one length with one digest are one chain. -/
theorem eq_of_chainDigest_eq (hstep : CollisionFree step) {l l' : List α}
    (hlen : l.length = l'.length)
    (h : chainDigest step h₀ l = chainDigest step h₀ l') : l = l' := by
  induction l using List.reverseRecOn generalizing l' with
  | nil => exact (List.length_eq_zero_iff.1 hlen.symm).symm
  | append_singleton l a ih =>
    rcases List.eq_nil_or_concat l' with rfl | ⟨m, b, rfl⟩
    · simp at hlen
    · rw [List.concat_eq_append] at hlen h
      rw [chainDigest_append_singleton, chainDigest_append_singleton] at h
      obtain ⟨h1, rfl⟩ := hstep _ _ _ _ h
      rw [List.concat_eq_append, ih (by simpa using hlen) h1]

/-- SNP-9 A certificate pins the read: under a collision-free digest, two stores that verify
one certificate have the same read at its cut. -/
theorem Verifies.readAt_eq (hstep : CollisionFree step) {z : Certificate K H}
    {s s' : Store K α} (h : Verifies step h₀ z s) (h' : Verifies step h₀ z s') :
    readAt s z.cut = readAt s' z.cut := by
  funext k
  refine eq_of_chainDigest_eq hstep ?_ ((h.2 k).trans (h'.2 k).symm)
  have hk : z.cut k ≤ (s k).length := h.1 k
  have hk' : z.cut k ≤ (s' k).length := h'.1 k
  change ((s k).take (z.cut k)).length = ((s' k).take (z.cut k)).length
  rw [List.length_take, List.length_take, Nat.min_eq_left hk, Nat.min_eq_left hk']

/-- SNP-9 So a snapshot is reproducible and checkable: every derived view at a certified cut
is the same on every store that verifies the certificate. -/
theorem Verifies.view_eq {β : Type*} (hstep : CollisionFree step) (D : Store K α → β)
    {z : Certificate K H} {s s' : Store K α} (h : Verifies step h₀ z s)
    (h' : Verifies step h₀ z s') : view D s z.cut = view D s' z.cut :=
  congrArg D (h.readAt_eq hstep h')

/-- SNP-9 A certificate extends: the digest at a later cut is the digest at an earlier cut
continued over the events between the two, so certifying costs the delta. -/
theorem certify_digest_readBetween (s : Store K α) {a b : Cut K} (h : a ≤ b) (k : K) :
    (certify step h₀ s b).digest k
      = chainDigest step ((certify step h₀ s a).digest k) (readBetween s a b k) :=
  foldAt_readBetween step (fun _ ↦ h₀) s h k

/-- SNP-9 The meet of two certified cuts is certified from the two certificates alone: on each
chain, the digest of the one that is earlier there. -/
theorem certify_inf (s : Store K α) (c d : Cut K) (k : K) :
    (certify step h₀ s (c ⊓ d)).digest k
      = if c k ≤ d k then (certify step h₀ s c).digest k else (certify step h₀ s d).digest k := by
  by_cases h : c k ≤ d k
  · simp only [h, ↓reduceIte]
    change chainDigest step h₀ ((s k).take (c k ⊓ d k)) = chainDigest step h₀ ((s k).take (c k))
    rw [inf_of_le_left h]
  · simp only [h, ↓reduceIte]
    change chainDigest step h₀ ((s k).take (c k ⊓ d k)) = chainDigest step h₀ ((s k).take (d k))
    rw [inf_of_le_right (not_le.1 h).le]

/-- SNP-9 And the join: on each chain, the digest of the one that is later there. -/
theorem certify_sup (s : Store K α) (c d : Cut K) (k : K) :
    (certify step h₀ s (c ⊔ d)).digest k
      = if c k ≤ d k then (certify step h₀ s d).digest k else (certify step h₀ s c).digest k := by
  by_cases h : c k ≤ d k
  · simp only [h, ↓reduceIte]
    change chainDigest step h₀ ((s k).take (c k ⊔ d k)) = chainDigest step h₀ ((s k).take (d k))
    rw [sup_of_le_right h]
  · simp only [h, ↓reduceIte]
    change chainDigest step h₀ ((s k).take (c k ⊔ d k)) = chainDigest step h₀ ((s k).take (c k))
    rw [sup_of_le_left (not_le.1 h).le]

/-- SNP-9 Erasure keeps the certificate: a certificate over the commitments of a committed
store verifies after any erasure of contents. -/
theorem verifies_purge {step : H → C → H} {z : Certificate K H} {t : Store K (C × Option α)}
    (E : α → Bool) (h : Verifies step h₀ z (commitments t)) :
    Verifies step h₀ z (commitments (purge E t)) := by
  rwa [commitments_purge]

/-- SNP-9 And only the commitments: a store verifies a certificate after an erasure exactly
when it did before, so a certificate attests no erasure. A copy taken before a purge verifies
every certificate the purged store verifies. -/
theorem verifies_purge_iff {step : H → C → H} {z : Certificate K H}
    {t : Store K (C × Option α)} (E : α → Bool) :
    Verifies step h₀ z (commitments (purge E t)) ↔ Verifies step h₀ z (commitments t) := by
  rw [commitments_purge]

/-- SNP-9 Under a binding commitment a certificate over commitments pins the events: two
committed stores that verify one certificate, each after an erasure of its own, were made from
the same events at its cut. -/
theorem Verifies.readAt_eq_of_committed {step : H → C → H} (hstep : CollisionFree step)
    {commit : α → C} (hcommit : Function.Injective commit) {z : Certificate K H}
    {s s' : Store K α} (E E' : α → Bool)
    (h : Verifies step h₀ z (commitments (purge E (committed commit s))))
    (h' : Verifies step h₀ z (commitments (purge E' (committed commit s')))) :
    readAt s z.cut = readAt s' z.cut := by
  rw [commitments_purge] at h h'
  funext k
  have hk := congrFun (h.readAt_eq hstep h') k
  simp only [readAt, commitments, committed, List.map_map] at hk
  have hfun : (Prod.fst ∘ fun a : α ↦ (commit a, some a)) = commit := rfl
  rw [hfun, ← List.map_take, ← List.map_take] at hk
  exact List.map_injective_iff.2 hcommit hk

/-- SNP-9 So what is read at a certified cut is pinned up to the erasure: two committed stores
that verify one certificate read, at its cut and under one erasure, the same store with holes. -/
theorem Verifies.contents_eq {step : H → C → H} (hstep : CollisionFree step)
    {commit : α → C} (hcommit : Function.Injective commit) (E : α → Bool)
    {z : Certificate K H} {s s' : Store K α}
    (h : Verifies step h₀ z (commitments (purge E (committed commit s))))
    (h' : Verifies step h₀ z (commitments (purge E (committed commit s')))) :
    readAt (contents (purge E (committed commit s))) z.cut
      = readAt (contents (purge E (committed commit s'))) z.cut := by
  rw [contents_purge_committed, contents_purge_committed, redact_readAt, redact_readAt,
    Verifies.readAt_eq_of_committed hstep hcommit E E h h']

/-- SNP-9 for the composite reader: two stores that verify one certificate show the same at
its cut under one grant and one erasure. The grant and the erasure are not in the certificate. -/
theorem Verifies.shown_eq (hstep : CollisionFree step) (G : K → Prop) [DecidablePred G]
    (p E : α → Bool) {z : Certificate K H} {s s' : Store K α} (h : Verifies step h₀ z s)
    (h' : Verifies step h₀ z s') : shown G p E s z.cut = shown G p E s' z.cut := by
  unfold shown snapshot
  rw [h.readAt_eq hstep h']

end Certified

namespace Witness

/-- The control for SNP-1: the reader that ignores the cut, which is what a verb reads of a
store rewritten in place, is not append invariant. -/
theorem present_not_appendInvariant :
    ¬AppendInvariant (present fun s : Store Unit ℕ ↦ (s ()).length) := by
  intro h
  have h1 := h (fun _ ↦ []) (fun _ ↦ [0]) (fun _ ↦ 0) (fun _ ↦ le_rfl)
  simp [present, grow] at h1

/-- The control for SNP-5: the store rewritten in place determines no read at a past cut. Two
chains leave one head state and had different states at the first cut. -/
theorem stateOf_forgets :
    ¬∃ G : (Unit → Option ℕ) → ℕ → Unit → Option ℕ,
      ∀ (l : List (Unit × ℕ)) (c : ℕ), stateAt l c = G (stateOf l) c := by
  rintro ⟨G, hG⟩
  have h1 := congrFun (hG [((), 0), ((), 1)] 1) ()
  have h2 := congrFun (hG [((), 1)] 1) ()
  have e : stateOf [((), 0), ((), 1)] = stateOf [((), 1)] := by
    funext u
    simp [stateOf]
  rw [e, ← h2] at h1
  simp [stateAt, stateOf] at h1

/-- The control for SNP-6: an event filter applied before the cut reads another thing than the
snapshot, since it moves the positions. -/
theorem filter_before_cut :
    ∃ (s : Store Unit Bool) (c : Cut Unit),
      readAt (restrict (fun _ ↦ True) id s) c ≠ snapshot (fun _ ↦ True) id s c := by
  refine ⟨fun _ ↦ [false, true], fun _ ↦ 1, fun h ↦ ?_⟩
  have h1 := congrFun h ()
  simp [readAt, restrict, snapshot] at h1

/-- The control for SNP-6: a cut's positions count the events an event filter hides. Two stores
that agree on every admitted event have different snapshots at one cut, so within a chain a
position tells how many hidden events came before: what must be hidden in number is hidden by
chain. -/
theorem position_channel :
    ∃ (s s' : Store Unit Bool) (c : Cut Unit), (∀ k, (s k).filter id = (s' k).filter id) ∧
      snapshot (fun _ ↦ True) id s c ≠ snapshot (fun _ ↦ True) id s' c := by
  refine ⟨fun _ ↦ [false, true], fun _ ↦ [true], fun _ ↦ 1, fun _ ↦ rfl, fun h ↦ ?_⟩
  have h1 := congrFun h ()
  simp [readAt, restrict, snapshot] at h1

/-- The control for SNP-7: an erasure that deletes rows moves the later ones up, so a read at a
cut then holds an event from after the cut. -/
theorem compact_moves :
    ∃ (E : ℕ → Bool) (s : Store Unit ℕ) (c : Cut Unit) (a : ℕ),
      a ∈ readAt (compact E s) c () ∧ a ∉ readAt s c () := by
  refine ⟨fun n ↦ n == 0, fun _ ↦ [0, 1], fun _ ↦ 1, 1, ?_, ?_⟩ <;> simp [readAt, compact]

/-- The control for SNP-7's stricter seal: the looser seal is lifted by a later landing, so
under it growth of the chain brings a retired key's past back to a cut inside the chain. -/
theorem servedNow_restores :
    ∃ (l t : List (Unit × Option ℕ)) (c : ℕ), c ≤ l.length ∧
      servedNow l c () = none ∧ servedNow (l ++ t) c () = some 0 := by
  refine ⟨[((), some 0), ((), none)], [((), some 1)], 1, by decide, ?_, ?_⟩ <;>
    simp [servedNow, stateAt, stateOf]

/-- The control for SNP-10: under the horizon the pruned store reads a key as absent where it
held a value. So the horizon is recorded, and a cut under it is not served. -/
theorem prune_forgets :
    ∃ (l : List (Unit × ℕ)) (h c : ℕ), c < h ∧
      genRead (prune h (gens l)) c () = none ∧ stateAt l c () = some 0 := by
  refine ⟨[((), 0), ((), 1)], 2, 1, by decide, ?_, ?_⟩
  · decide
  · decide

/-- The control for SNP-9: a digest that is not collision free pins nothing. Under addition two
chains of one length and one digest differ. -/
theorem digest_collides :
    ∃ l l' : List ℕ, l.length = l'.length ∧
      chainDigest (· + ·) 0 l = chainDigest (· + ·) 0 l' ∧ l ≠ l' :=
  ⟨[1, 2], [2, 1], rfl, rfl, by decide⟩

/-- The control for SNP-10, in its stronger form: nothing in the rows that remain tells a lost
key from a key that was never there. Two chains have the same pruned store, and at one cut under
the horizon a key held a value in the first and had never been written in the second. -/
theorem prune_indistinct :
    ∃ (l l' : List (ℕ × ℕ)) (h c : ℕ), c < h ∧
      (prune h (gens l)).map (fun r ↦ (r.key, r.val, r.born, r.died))
        = (prune h (gens l')).map (fun r ↦ (r.key, r.val, r.born, r.died)) ∧
      stateAt l c 1 = some 0 ∧ stateAt l' c 1 = none :=
  ⟨[(0, 0), (1, 0), (0, 1), (1, 1)], [(0, 0), (0, 2), (0, 1), (1, 1)], 4, 2, by decide,
    by decide, by decide, by decide⟩

/-- The control for SNP-7's keyed read: a hole that loses its key. Path `()` lands versions 1,
2 and 3 and version 2 is erased. With the key kept, the read at cut 2 is a hole. A seek over the
rows of the prefix that still carry the key returns version 1, which was superseded at the cut;
a seek over the chain with the holes deleted returns version 3, which landed after it. -/
theorem keyless_hole :
    ∃ (l : List (Unit × ℕ)) (E : Unit × ℕ → Bool) (c : ℕ),
      stateAt (holes E l) c () = some none ∧
        stateOf ((l.take c).filter fun e ↦ !E e) () = some 1 ∧
        lastWrite (l.filter fun e ↦ !E e) c () = some 3 :=
  ⟨[((), 1), ((), 2), ((), 3)], fun e ↦ e.2 == 2, 2, by decide, by decide, by decide⟩

/-- The control for SNP-9: a certificate attests no seal. A chain and its growth by a retire
verify the certificate of one cut, under every digest, and serve different things at it. -/
theorem seal_not_certified :
    ∃ (l t : List (Unit × Option ℕ)) (c : ℕ),
      (∀ (step : ℕ → Unit × Option ℕ → ℕ) (h₀ : ℕ),
        Verifies step h₀ (certify step h₀ (fun _ : Unit ↦ l) fun _ ↦ c) fun _ ↦ l ++ t) ∧
      servedAt l c () = some 5 ∧ servedAt (l ++ t) c () = none := by
  refine ⟨[((), some 5)], [((), none)], 1, fun step h₀ ↦ ?_, by decide, by decide⟩
  exact verifies_certify_of_extends (extends_grow (fun _ ↦ [((), some 5)]) fun _ ↦ [((), none)])
    fun _ ↦ le_rfl

/-- The control for SNP-9's fixed chain keys: a renamed chain is not an extension. The
certificate of a cut does not verify on the store with its two chains exchanged, under any
digest, so a chain is keyed by an id that a relabel does not change. -/
theorem rename_breaks_certificate :
    ∃ (s s' : Store Bool ℕ) (c : Cut Bool), c ≤ head s ∧ (∀ k, s' k = s (!k)) ∧
      ∀ (step : ℕ → ℕ → ℕ) (h₀ : ℕ), ¬Verifies step h₀ (certify step h₀ s c) s' := by
  refine ⟨fun k ↦ if k then [7] else [], fun k ↦ if k then [] else [7],
    fun k ↦ if k then 1 else 0, fun k ↦ ?_, fun k ↦ ?_, ?_⟩
  · cases k <;> simp [head]
  · cases k <;> rfl
  · rintro step h₀ ⟨h, -⟩
    have := h true
    simp [certify, head] at this

/-- The control for SNP-10's local lowering: a record on a chain that content reads. Chain 0 is
a landing log, chain 1 the attestations, chain 2 a chain `X`. The first attestation is a recorded
cut that certifies the first event of `X`; the landing reads its own attestation, the second.
The frontier asked is consistent, and the landing log and the attestations serve every position.
`X` serves its empty prefix and the positions from 2 on. Then every cut the frontier resolves to
among the served positions reads the landing log and the attestations at their empty prefixes:
one chain read low drags down every chain that reads the chain the record sits on. -/
theorem record_drags :
    ∃ (R : ℕ → ℕ → ℕ → ℕ → Prop) (S : ℕ → Set ℕ) (f : Cut ℕ),
      Consistent R f ∧ (∀ k, k ≠ 2 → S k = Set.univ) ∧
        ∀ c, ResolvesIn R S f c → c 0 = 0 ∧ c 1 = 0 := by
  refine ⟨fun k i k' j ↦ (k = 1 ∧ i = 0 ∧ k' = 2 ∧ j = 0) ∨ (k = 0 ∧ i = 0 ∧ k' = 1 ∧ j = 1),
    fun k ↦ if k = 2 then {p | p = 0 ∨ 2 ≤ p} else Set.univ,
    fun k ↦ if k = 0 then 1 else if k = 1 then 2 else 1, ?_, fun k hk ↦ by simp [hk], ?_⟩
  · rintro k i k' j (⟨rfl, rfl, rfl, rfl⟩ | ⟨rfl, rfl, rfl, rfl⟩) _ <;> decide
  · rintro c ⟨hc, hS, hcf, -⟩
    have hX : c 2 = 0 := by
      have h2 : c 2 = 0 ∨ 2 ≤ c 2 := by simpa using hS 2
      have h1 : c 2 ≤ 1 := by simpa using hcf 2
      omega
    have hatt : c 1 = 0 := by
      by_contra h
      have := hc 1 0 2 0 (Or.inl ⟨rfl, rfl, rfl, rfl⟩) (Nat.pos_of_ne_zero h)
      omega
    have hland : c 0 = 0 := by
      by_contra h
      have := hc 0 0 1 1 (Or.inr ⟨rfl, rfl, rfl, rfl⟩) (Nat.pos_of_ne_zero h)
      omega
    exact ⟨hland, hatt⟩

/-- The control for SNP-6's closed set of chains: the cut read on a chain a grant names depends
on what a chain it reads serves. One relation and one frontier, served positions that agree on
the named chain, and two different cuts read on it. -/
theorem resolution_reads_unnamed :
    ∃ (R : Bool → ℕ → Bool → ℕ → Prop) (S S' : Bool → Set ℕ) (f c c' : Cut Bool),
      S true = S' true ∧ ResolvesIn R S f c ∧ ResolvesIn R S' f c' ∧ c true ≠ c' true := by
  refine ⟨fun k i k' j ↦ k = true ∧ i = 0 ∧ k' = false ∧ j = 0, fun _ ↦ Set.univ,
    fun k ↦ if k then Set.univ else {0}, fun _ ↦ 1, fun _ ↦ 1, fun _ ↦ 0, by simp, ?_, ?_,
    by simp⟩
  · refine resolvesIn_self (fun k i k' j h _ ↦ ?_) fun _ ↦ Set.mem_univ _
    obtain ⟨-, -, -, rfl⟩ := h
    exact Nat.one_pos
  · refine ⟨consistent_zero, fun k ↦ ?_, fun _ ↦ Nat.zero_le _, fun d hd hS _ k ↦ ?_⟩
    · cases k <;> simp
    · have h0 : d false = 0 := by simpa using hS false
      have h1 : d true = 0 := by
        by_contra h
        have := hd true 0 false 0 ⟨rfl, rfl, rfl, rfl⟩ (Nat.pos_of_ne_zero h)
        omega
      cases k
      · exact h0.le
      · exact h1.le

/-- The control for SNP-10's monotonicity: it needs the served sets to grow. A store that keeps
no past serves its empty prefix and its head, and loses its old head when it grows. Asked at 5
while the head is 5 the cut read is 5; asked again at 5 after the head moved to 7 it is 0. -/
theorem served_set_shrinks :
    ∃ (S S' : Unit → Set ℕ) (f : Cut Unit),
      ResolvesIn (fun _ _ _ _ ↦ False) S f f ∧
        ResolvesIn (fun _ _ _ _ ↦ False) S' f fun _ ↦ 0 := by
  refine ⟨fun _ ↦ {0, 5}, fun _ ↦ {0, 7}, fun _ ↦ 5, ?_, ?_⟩
  · exact resolvesIn_self (fun _ _ _ _ h ↦ h.elim) fun _ ↦ by simp
  · refine ⟨consistent_zero, fun _ ↦ by simp, fun _ ↦ Nat.zero_le _, fun d _ hS hdf u ↦ ?_⟩
    have h1 : d u = 0 ∨ d u = 7 := by simpa using hS u
    have h2 : d u ≤ 5 := hdf u
    change d u ≤ 0
    omega

end Witness

end Palace.Snapshot
