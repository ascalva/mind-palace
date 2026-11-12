module

public import Palace.Snapshot.Defs
public import Mathlib.Data.List.Induction
public import Mathlib.Data.List.ReduceOption
public import Mathlib.Order.Lattice
public import Mathlib.Order.Lattice.Nat
public import Mathlib.Order.Sublattice

/-!
# The temporal snapshot: the statements

SNP-1 to SNP-5 (`docs/LAWS.md`, XVI): append invariance, monotonicity, composition, idempotence,
and a derived view as a function of the prefixes, over the model of `Palace/Snapshot/Defs.lean`: a
store as a family of append chains, a cut as a prefix length for each chain, the read at a cut and
between two cuts, a derived view as a derivation of the prefixes, a chain of keyed writes held
three ways (rewritten in place, recomputed from the prefix, kept by generation with a closing
stamp), the grant and the erasure applied to one read, the history of a key with and without a
seal, the identity a landing at a retired path takes (`lives`), and the filtered read of the
references a resolver does not follow (`Kept`). Each law's controls are among its statements. What
they leave out: the stores' SQL, the hash and the commitment of a row (SNP-9's, not stated here),
the class a chain holds and the relabel that rewrites it, and the identity's name in the code;
`core/stores/landings.py` is the transcription these laws are tested against
(`tests/property/test_landing_log.py`).

SNP-6 to SNP-10 are not stated here: they are design theorems of `Palace/Snapshot.lean`, cited from
the note until a stage of dn-temporal-snapshot §12 builds what relies on them.

These are the laws of `Palace/Snapshot.lean` as the ledger cites them, each with its proof left as
`sorry`. `lake comparator` checks that the `Palace` library proves each one exactly as stated
here, from the standard axioms alone.
-/

@[expose] public section

namespace Palace.Snapshot

section Reads

variable {K α β : Type*}

/-- **SNP-1** Append invariance: the read at a cut inside the store does not change when the store
grows. -/
theorem readAt_grow {s : Store K α} (t : Store K α) {c : Cut K} (h : c ≤ head s) :
    readAt (grow s t) c = readAt s c :=
  sorry

/-- **SNP-1** The same over every extension: a later state of an append-only store reads, at a cut
of an earlier state, what the earlier state read. -/
theorem readAt_of_extends {s s' : Store K α} {c : Cut K} (h : Extends s s') (hc : c ≤ head s) :
    readAt s' c = readAt s c :=
  sorry

/-- **SNP-1** The read between two cuts inside the store does not change when the store grows. -/
theorem readBetween_grow {s : Store K α} (t : Store K α) (a : Cut K) {b : Cut K}
    (h : b ≤ head s) : readBetween (grow s t) a b = readBetween s a b :=
  sorry

/-- **SNP-1** Every derived view is append invariant. -/
theorem appendInvariant_view (D : Store K α → β) : AppendInvariant (view D) :=
  sorry

/-- **SNP-2** Monotonicity: the read at an earlier cut is a prefix, chain by chain, of the read at a
later one. -/
theorem readAt_mono (s : Store K α) {c d : Cut K} (h : c ≤ d) :
    Extends (readAt s c) (readAt s d) :=
  sorry

/-- **SNP-2** An event read at a cut is read at every later cut. -/
theorem mem_readAt_of_le {s : Store K α} {c d : Cut K} (h : c ≤ d) {k : K} {a : α}
    (ha : a ∈ readAt s c k) : a ∈ readAt s d k :=
  sorry

/-- **SNP-2** A cut of a cut is the meet of the two. -/
theorem readAt_readAt (s : Store K α) (c d : Cut K) :
    readAt (readAt s c) d = readAt s (d ⊓ c) :=
  sorry

/-- **SNP-2** The head of the read at a cut is the meet of the cut and the store's head. -/
theorem head_readAt (s : Store K α) (c : Cut K) : head (readAt s c) = c ⊓ head s :=
  sorry

/-- **SNP-4** A cut at or past the head reads the store. -/
theorem readAt_of_head_le {s : Store K α} {c : Cut K} (h : head s ≤ c) : readAt s c = s :=
  sorry

/-- **SNP-4** Idempotence: the read at the head cut is the store. -/
theorem readAt_head (s : Store K α) : readAt s (head s) = s :=
  sorry

/-- **SNP-4** Every derived view at the head cut is the derivation of the present: `as of` the
current cut is no `as of`. -/
theorem view_head (D : Store K α → β) (s : Store K α) : view D s (head s) = D s :=
  sorry

/-- **SNP-3** Composition: the read at `a` followed by the read between `a` and `b` is the read at
`b`. -/
theorem readAt_append_readBetween (s : Store K α) {a b : Cut K} (h : a ≤ b) :
    grow (readAt s a) (readBetween s a b) = readAt s b :=
  sorry

/-- **SNP-3** Two adjacent reads-between compose. -/
theorem readBetween_append (s : Store K α) {a b c : Cut K} (hab : a ≤ b) (hbc : b ≤ c) :
    grow (readBetween s a b) (readBetween s b c) = readBetween s a c :=
  sorry

/-- **SNP-3** The journal: a fold of the prefixes at a later cut is the fold at an earlier cut
continued over the events between the two. A job that keeps its state and the cut it stopped at
reads only the delta. -/
theorem foldAt_readBetween (f : β → α → β) (init : K → β) (s : Store K α) {a b : Cut K}
    (h : a ≤ b) (k : K) :
    foldAt f init s b k = (readBetween s a b k).foldl f (foldAt f init s a k) :=
  sorry

/-- **SNP-3** An event read at the later cut was read at the earlier cut or lies in the delta. -/
theorem mem_readAt_iff {s : Store K α} {a b : Cut K} (h : a ≤ b) {k : K} {x : α} :
    x ∈ readAt s b k ↔ x ∈ readAt s a k ∨ x ∈ readBetween s a b k :=
  sorry

/-- **SNP-3** The delta rule for a job that joins two chains: a pair of events read at the later
cut was read at the earlier cut, or one of the two lies in the delta. So a job that kept the
pairs of its checkpoint has only the pairs with a new member left to visit. -/
theorem pair_readAt {s : Store K α} {a b : Cut K} (h : a ≤ b) {k k' : K} {x y : α}
    (hx : x ∈ readAt s b k) (hy : y ∈ readAt s b k') :
    (x ∈ readAt s a k ∧ y ∈ readAt s a k') ∨ x ∈ readBetween s a b k ∨
      y ∈ readBetween s a b k' :=
  sorry

/-- **SNP-5** A derived view reads only the prefixes. -/
theorem prefixOnly_view (D : Store K α → β) : PrefixOnly (view D) :=
  sorry

/-- **SNP-5** Two stores with the same prefixes at a cut give every derived view the same
reading. -/
theorem view_congr (D : Store K α → β) {s s' : Store K α} {c : Cut K}
    (h : readAt s c = readAt s' c) : view D s c = view D s' c :=
  sorry

/-- **SNP-5** A reader is append invariant exactly when it reads only the prefixes. -/
theorem appendInvariant_iff_prefixOnly (F : Store K α → Cut K → β) :
    AppendInvariant F ↔ PrefixOnly F :=
  sorry

/-- **SNP-5** A reader is append invariant exactly when it is a derived view: on cuts inside the
store, a function of the prefixes alone. -/
theorem appendInvariant_iff_exists_view (F : Store K α → Cut K → β) :
    AppendInvariant F ↔ ∃ D : Store K α → β, ∀ s c, c ≤ head s → F s c = view D s c :=
  sorry

end Reads

section Generations

variable {κ β : Type*} [DecidableEq κ]

/-- **SNP-1** The state at a cut inside the chain does not change when the chain grows. -/
theorem stateAt_append {l : List (κ × β)} (t : List (κ × β)) {c : ℕ} (h : c ≤ l.length) :
    stateAt (l ++ t) c = stateAt l c :=
  sorry

/-- **SNP-3** The journal of the keyed state: the state at a later cut is the state at an earlier
cut with the writes between the two applied in order. -/
theorem stateAt_eq_foldl (l : List (κ × β)) {a b : ℕ} (h : a ≤ b) :
    stateAt l b = ((l.take b).drop a).foldl
      (fun (m : κ → Option β) (e : κ × β) ↦ Function.update m e.1 (some e.2)) (stateAt l a) :=
  sorry

/-- **SNP-3** The delta bounds the change: a key the writes between two cuts do not name has the
same state at both. What changed between two cuts is found among the keys of the delta. -/
theorem stateAt_eq_of_not_written (l : List (κ × β)) {a b : ℕ} (h : a ≤ b) {x : κ}
    (hx : ∀ e ∈ (l.take b).drop a, e.1 ≠ x) : stateAt l b x = stateAt l a x :=
  sorry

/-- **SNP-5** The state at a cut is the last write of the key inside the prefix: one seek on an
index of (key, position). -/
theorem stateAt_eq_lastWrite (l : List (κ × β)) (c : ℕ) (x : κ) :
    stateAt l c x = lastWrite l c x :=
  sorry

/-- **SNP-5** Generations are recomputation: the generational store read at a cut is the state
recomputed from the chain's prefix, at every cut. -/
theorem genRead_gens (l : List (κ × β)) (c : ℕ) (x : κ) :
    genRead (gens l) c x = stateAt l c x :=
  sorry

/-- **SNP-4** At the head cut the generational store reads the store rewritten in place. -/
theorem genRead_gens_length (l : List (κ × β)) (x : κ) :
    genRead (gens l) l.length x = stateOf l x :=
  sorry

/-- **SNP-1** The generational store read at a cut inside the chain does not change when the chain
grows, though the growth writes closing stamps into it. -/
theorem genRead_gens_append {l : List (κ × β)} (t : List (κ × β)) {c : ℕ} (h : c ≤ l.length)
    (x : κ) : genRead (gens (l ++ t)) c x = genRead (gens l) c x :=
  sorry

/-- **SNP-5** At most one generation of a key is alive at a cut: the snapshot of a keyed store is a
transversal of its chains. -/
theorem length_filter_selects_le_one (l : List (κ × β)) (c : ℕ) (x : κ) :
    ((gens l).filter (selects c x)).length ≤ 1 :=
  sorry

/-- **SNP-4** At the head cut nothing is sealed: a chain of landings and retires serves what the
store rewritten in place holds live. -/
theorem servedAt_length (l : List (κ × Option β)) (x : κ) :
    servedAt l l.length x = (stateOf l x).join :=
  sorry

/-- **SNP-4** At the head cut the looser seal serves what the store rewritten in place holds
live. -/
theorem servedNow_length (l : List (κ × Option β)) (x : κ) :
    servedNow l l.length x = (stateOf l x).join :=
  sorry

/-- **SNP-4** At the head cut the history served is the key's present life. -/
theorem historyAt_length (l : List (κ × Option β)) (x : κ) :
    historyAt l l.length x = sinceRetire l x :=
  sorry

/-- **SNP-1** With no seal the history of a key at a cut is append invariant: growth of the chain, a
retire of the key included, changes nothing in it. -/
theorem landingsAt_append {l : List (κ × Option β)} (t : List (κ × Option β)) {c : ℕ}
    (hc : c ≤ l.length) (x : κ) : landingsAt (l ++ t) c x = landingsAt l c x :=
  sorry

/-- **SNP-4** At the head cut the history with no seal is every landing of the key. -/
theorem landingsAt_length (l : List (κ × Option β)) (x : κ) :
    landingsAt l l.length x = l.filterMap fun e ↦ if e.1 = x then e.2 else none :=
  sorry

/-- **SNP-2** With no seal the history at an earlier cut is a prefix of the history at a later
one. -/
theorem landingsAt_mono (l : List (κ × Option β)) {a b : ℕ} (h : a ≤ b) (x : κ) :
    landingsAt l a x <+: landingsAt l b x :=
  sorry

/-- **SNP-1** The history of an identity at a cut inside the chain is unchanged by any growth of the
chain: a later retire or a later landing at its path closes nothing and adds nothing. -/
theorem landingsAt_lives_append {l : List (κ × Option β)} (t : List (κ × Option β)) {c : ℕ}
    (hc : c ≤ l.length) (y : κ × ℕ) :
    landingsAt (lives (l ++ t)) c y = landingsAt (lives l) c y :=
  sorry

end Generations

section Grant

variable {K α : Type*}

/-- **SNP-1** A snapshot under a grant (SNP-6) is append invariant. -/
theorem snapshot_grow (G : K → Prop) [DecidablePred G] (p : α → Bool) {s : Store K α}
    (t : Store K α) {c : Cut K} (h : c ≤ head s) :
    snapshot G p (grow s t) c = snapshot G p s c :=
  sorry

/-- **SNP-4** At the head cut a snapshot is the grant's restriction of the store. -/
theorem snapshot_head (G : K → Prop) [DecidablePred G] (p : α → Bool) (s : Store K α) :
    snapshot G p s (head s) = restrict G p s :=
  sorry

/-- **SNP-1** for the composite reader: what an asker is shown at a cut inside the store is the
same after any growth. -/
theorem shown_grow (G : K → Prop) [DecidablePred G] (p E : α → Bool) {s : Store K α}
    (t : Store K α) {c : Cut K} (h : c ≤ head s) :
    shown G p E (grow s t) c = shown G p E s c :=
  sorry

/-- **SNP-4** for the composite reader: at the head cut it is the grant's restriction of the store
without the erased events. -/
theorem shown_head (G : K → Prop) [DecidablePred G] (p E : α → Bool) (s : Store K α) :
    shown G p E s (head s) = restrict G (fun a ↦ p a && !E a) s :=
  sorry

end Grant

section Erasure

variable {K α β C : Type*}

/-- **SNP-2** under an erasure: what is visible at an earlier cut is a prefix of what is visible
at a later one. -/
theorem visible_mono (E : α → Bool) (s : Store K α) {c d : Cut K} (h : c ≤ d) (k : K) :
    visible E s c k <+: visible E s d k :=
  sorry

/-- **SNP-4** under an erasure: at the head cut what is visible is the store without the erased
events. -/
theorem visible_head (E : α → Bool) (s : Store K α) : visible E s (head s) = compact E s :=
  sorry

/-- **SNP-1** under an erasure: growth of the store changes nothing visible at a cut inside it. -/
theorem visible_grow (E : α → Bool) {s : Store K α} (t : Store K α) {c : Cut K}
    (h : c ≤ head s) : visible E (grow s t) c = visible E s c :=
  sorry

end Erasure

section Consistency

variable {K : Type*} {R : K → ℕ → K → ℕ → Prop}

section Filter

variable {ok : K → ℕ → Prop} {c : Cut K}

/-- **SNP-2** The filtered read is monotone in the cut, for a test that does not depend on the cut:
a row kept at a cut is kept at every later one. -/
theorem Kept.mono {c d : Cut K} (hcd : c ≤ d) {k : K} {i : ℕ} (h : Kept R ok c k i) :
    Kept R ok d k i :=
  sorry

/-- **SNP-1** The filtered read is append invariant: when the rows inside the old head keep the
references they had, the rows kept at a cut inside the old head are the same after the store
grows. -/
theorem kept_grown_iff {R' : K → ℕ → K → ℕ → Prop} {h : Cut K}
    (hR : ∀ k i k' j, i < h k → (R' k i k' j ↔ R k i k' j)) (hc : c ≤ h) {k : K} {i : ℕ} :
    Kept R' ok c k i ↔ Kept R ok c k i :=
  sorry

end Filter

end Consistency

namespace Witness

/-- **SNP-1** The control: the reader that ignores the cut, which is what a verb reads of a
store rewritten in place, is not append invariant. -/
theorem present_not_appendInvariant :
    ¬AppendInvariant (present fun s : Store Unit ℕ ↦ (s ()).length) :=
  sorry

/-- **SNP-5** The control: the store rewritten in place determines no read at a past cut. Two
chains leave one head state and had different states at the first cut. -/
theorem stateOf_forgets :
    ¬∃ G : (Unit → Option ℕ) → ℕ → Unit → Option ℕ,
      ∀ (l : List (Unit × ℕ)) (c : ℕ), stateAt l c = G (stateOf l) c :=
  sorry

/-- **SNP-1** The control for the retire with no seal: what the stricter seal costs. A retire
written after a cut empties the history the seal serves there, and leaves the history with no
seal as it was. -/
theorem seal_empties_history :
    ∃ (l t : List (Unit × Option ℕ)) (c : ℕ), c ≤ l.length ∧
      historyAt l c () = [5] ∧ historyAt (l ++ t) c () = [] ∧ landingsAt (l ++ t) c () = [5] :=
  sorry

end Witness

end Palace.Snapshot
