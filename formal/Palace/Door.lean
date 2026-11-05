module

public import Palace.Door.Defs

/-!
# The door: the laws

dn-ingest-door §3.9, family XII, on the keyed model of `Palace/Door/Defs.lean`. DOR-1: a command
is admissible iff a granted plane above its scope carries the write bit, so a read-only grant
admits no command, and the Ambassador's grant as written admits a projection-event command and
refuses a commit-clock one. DOR-2: ingestion is extensive, idempotent, and monotone on the rows
of sound states; a chain only grows. DOR-3: commands on distinct identities commute, and a batch
of them lands the same state in any order, and lands nothing when run again. DOR-5: a re-ingest
of held content embeds nothing; two commands sharing an atom pay once; a batch of fresh commands
on distinct identities embeds its distinct new atoms. DOR-6: the receipt names what landed, the
rows added and the digest that is the chain's new head, and nothing else. DOR-7: with the key
written last, a fresh run interrupted after any step converges under re-run, in the model's
stage order and in any order of the steps before the key, the code's among them; a key written
while some of the command's rows are not held is never repaired, the control that is the audit's
defect 1. DOR-8: fresh commands on one identity land in the order of their chain, and the two
orders give two chains. DOR-9: the steps of fresh commands on distinct identities run to the
batch's state in any order, which is what lets the queue dispatch non-conflicting commands in
parallel. DOR-10: conflict-equivalence is state-equivalence, so a schedule of a batch's steps
that orders each identity's landings and keys as the list does lands the batch, repeated
identities allowed, when each command is fresh at its turn; with the guard, the commands that
land are the ones fresh at their turn, and a schedule of theirs lands the whole list; a
permutation alone does not (the control). DOR-11: if each command of a batch of fresh commands on
distinct identities has run a prefix of its own steps, in any global order, the batch run again
lands the uninterrupted batch, every crash point of every parallel run; with repeated
identities, a serial run stopped inside a command converges when what runs again is that command
and the ones after it, and not when the whole batch does (the control). DOR-12: every state a
key-last run passes through is sound for its own command, and a batch on distinct identities
stopped anywhere, in any global order, is sound for each of its commands when the state before
was, so a reader that trusts the key sees a version whole or not at all and needs no lock; with
the key first it would see rows that are not there (the control).

The model is the ledger's grain: the rows, the chains and the keys. The stores readers go through
(the catalog's upsert, the plane's `current` flag and its `held` cache) are not modelled
(dn-ingest-door D5), so DOR-12 is soundness at that grain. DOR-9 and DOR-11 take every command
fresh, where a sync pass is mostly UNCHANGED commands; DOR-10's `landsOf` form covers those.
DOR-1 and DOR-7 are the ledger's (`Spec/Door.lean`, judged by the comparator):
`core/sentence/types.py` and the landing order are written to them. The others are design
theorems until code relies on them.
-/

@[expose] public section

open Finset

namespace Palace.Door

variable {R D G : Type*} [DecidableEq R] [DecidableEq D] [DecidableEq G]

/-! ### The chain -/

/-- Appending always leaves the digest at the head. -/
theorem appendIfNew_getLast? (c : List G) (g : G) : (appendIfNew c g).getLast? = some g := by
  unfold appendIfNew
  split_ifs with h
  · exact h
  · simp

/-- Appending the head again changes nothing. -/
theorem appendIfNew_idem (c : List G) (g : G) :
    appendIfNew (appendIfNew c g) g = appendIfNew c g := by
  rw [appendIfNew, appendIfNew_getLast?]
  simp

/-- A chain is a prefix of its extension. -/
theorem prefix_appendIfNew (c : List G) (g : G) : c <+: appendIfNew c g := by
  unfold appendIfNew
  split_ifs
  · exact List.prefix_rfl
  · exact List.prefix_append c [g]

/-! ### The guard -/

/-- A keyed command lands nothing. -/
theorem ingest_of_keyed {x : Source R D G} {s : State R D G}
    (h : s.key x.ident = some x.digest) : ingest x s = s := by
  simp [ingest, h]

/-- A fresh command lands. -/
theorem ingest_of_fresh {x : Source R D G} {s : State R D G} (h : Fresh x s) :
    ingest x s = land x s := by
  unfold Fresh at h
  simp [ingest, h]

/-- Landing sets the key. -/
theorem land_key (x : Source R D G) (s : State R D G) : (land x s).key x.ident = some x.digest := by
  simp [land]

/-- Landing touches no other identity's key. -/
theorem land_key_other (x : Source R D G) (s : State R D G) {d : D} (h : d ≠ x.ident) :
    (land x s).key d = s.key d := by
  simp [land, h]

/-- Ingesting touches no other identity's key. -/
theorem ingest_key_other (x : Source R D G) (s : State R D G) {d : D} (h : d ≠ x.ident) :
    (ingest x s).key d = s.key d := by
  unfold ingest
  split_ifs
  · rfl
  · exact land_key_other x s h

/-- After a command, its key names its digest, landed or not. -/
theorem ingest_key (x : Source R D G) (s : State R D G) :
    (ingest x s).key x.ident = some x.digest := by
  unfold ingest
  split_ifs with h
  · exact h
  · exact land_key x s

/-! ### DOR-2 Ingestion is a closure operator -/

/-- DOR-2 Extensive: nothing is removed. -/
theorem ingest_extensive (x : Source R D G) (s : State R D G) : s.rows ⊆ (ingest x s).rows := by
  unfold ingest
  split_ifs
  · exact subset_rfl
  · exact subset_union_left

/-- DOR-2 Extensive on the chains: a chain only grows. -/
theorem chain_prefix_ingest (x : Source R D G) (s : State R D G) (d : D) :
    s.chain d <+: (ingest x s).chain d := by
  unfold ingest land
  split_ifs
  · exact List.prefix_rfl
  · dsimp only
    split_ifs
    · exact prefix_appendIfNew _ _
    · exact List.prefix_rfl

/-- DOR-2 Monotone on the rows, between sound states: a larger state before gives a larger
state after. -/
theorem ingest_monotone (x : Source R D G) {s t : State R D G} (h : s.rows ⊆ t.rows)
    (ht : Sound x t) : (ingest x s).rows ⊆ (ingest x t).rows := by
  have hs : (ingest x s).rows ⊆ s.rows ∪ x.rows := by
    unfold ingest
    split_ifs
    · exact subset_union_left
    · exact subset_rfl
  refine hs.trans ?_
  unfold ingest
  split_ifs with hk
  · exact union_subset h (ht hk)
  · exact union_subset_union_left h

/-- DOR-2 Idempotent: running a command again changes nothing, since its key names its digest. -/
theorem ingest_idempotent (x : Source R D G) (s : State R D G) :
    ingest x (ingest x s) = ingest x s :=
  ingest_of_keyed (ingest_key x s)

/-! ### DOR-3 Commands on distinct identities commute -/

/-- Two landings on distinct identities commute. -/
theorem land_comm (x y : Source R D G) (hxy : x.ident ≠ y.ident) (s : State R D G) :
    land x (land y s) = land y (land x s) := by
  refine State.ext ?_ (funext fun d ↦ ?_) (funext fun d ↦ ?_)
  · change s.rows ∪ y.rows ∪ x.rows = s.rows ∪ x.rows ∪ y.rows
    rw [union_right_comm]
  · simp only [land]
    by_cases hx : d = x.ident
    · subst hx
      simp [hxy]
    · by_cases hy : d = y.ident
      · subst hy
        simp [hx]
      · simp [hx, hy]
  · simp only [land]
    by_cases hx : d = x.ident
    · subst hx
      simp [hxy]
    · by_cases hy : d = y.ident
      · subst hy
        simp [hx]
      · simp [hx, hy]

/-- DOR-3 Two commands on distinct identities commute. -/
theorem ingest_comm (x y : Source R D G) (hxy : x.ident ≠ y.ident) (s : State R D G) :
    ingest x (ingest y s) = ingest y (ingest x s) := by
  by_cases hx : s.key x.ident = some x.digest <;> by_cases hy : s.key y.ident = some y.digest
  · rw [ingest_of_keyed hy, ingest_of_keyed hx, ingest_of_keyed hy]
  · rw [ingest_of_keyed hx, ingest_of_fresh hy, ingest_of_keyed]
    rwa [land_key_other y s hxy]
  · rw [ingest_of_keyed hy, ingest_of_fresh hx, ingest_of_keyed]
    rwa [land_key_other x s (Ne.symm hxy)]
  · rw [ingest_of_fresh hx, ingest_of_fresh hy, ingest_of_fresh, ingest_of_fresh, land_comm x y hxy]
    · change (land x s).key y.ident ≠ some y.digest
      rwa [land_key_other x s (Ne.symm hxy)]
    · change (land y s).key x.ident ≠ some x.digest
      rwa [land_key_other y s hxy]

/-- A batch, one command at a time. -/
theorem batch_cons (x : Source R D G) (l : List (Source R D G)) (s : State R D G) :
    batch (x :: l) s = batch l (ingest x s) := rfl

/-- DOR-3 A batch of commands on pairwise distinct identities lands the same state in any
order. -/
theorem ingest_batch_perm {l₁ l₂ : List (Source R D G)} (hp : l₁.Perm l₂) :
    ∀ s : State R D G, (l₁.map Source.ident).Nodup → batch l₁ s = batch l₂ s := by
  induction hp with
  | nil => intro s _; rfl
  | cons x p ih =>
    intro s hn
    simp only [List.map_cons, List.nodup_cons] at hn
    simp only [batch_cons]
    exact ih _ hn.2
  | swap x y l =>
    intro s hn
    simp only [List.map_cons, List.nodup_cons, List.mem_cons, not_or] at hn
    simp only [batch_cons]
    rw [ingest_comm x y (Ne.symm hn.1.1)]
  | trans p₁ p₂ ih₁ ih₂ =>
    intro s hn
    rw [ih₁ s hn, ih₂ s ((p₁.map Source.ident).nodup_iff.1 hn)]

/-- A command on an identity none of a batch's commands touch commutes with the batch. -/
theorem ingest_batch_comm (x : Source R D G) (l : List (Source R D G))
    (h : ∀ y ∈ l, x.ident ≠ y.ident) (s : State R D G) :
    ingest x (batch l s) = batch l (ingest x s) := by
  induction l generalizing s with
  | nil => rfl
  | cons y l ih =>
    simp only [batch_cons]
    rw [ih (fun z hz ↦ h z (List.mem_cons_of_mem y hz)) (ingest y s),
      ingest_comm x y (h y (List.mem_cons_self ..))]

/-- DOR-3 A batch on pairwise distinct identities, run again, lands nothing: what the queue's
coalescing relies on. -/
theorem batch_idempotent (l : List (Source R D G)) (hn : (l.map Source.ident).Nodup)
    (s : State R D G) : batch l (batch l s) = batch l s := by
  induction l generalizing s with
  | nil => rfl
  | cons x l ih =>
    simp only [List.map_cons, List.nodup_cons, List.mem_map] at hn
    have hx : ∀ y ∈ l, x.ident ≠ y.ident := fun y hy heq ↦ hn.1 ⟨y, hy, heq.symm⟩
    simp only [batch_cons]
    rw [ingest_batch_comm x l hx, ingest_idempotent, ih hn.2]

/-! ### DOR-8 One identity: the chain is the serial order -/

/-- DOR-8 Two fresh commands on one identity land in their order on the chain. -/
theorem same_identity_orders_the_chain (x y : Source R D G) (h : x.ident = y.ident)
    (hd : x.digest ≠ y.digest) (s : State R D G) (hy : s.key x.ident ≠ some y.digest) :
    (ingest x (ingest y s)).chain x.ident
      = appendIfNew (appendIfNew (s.chain x.ident) y.digest) x.digest := by
  have hy' : Fresh y s := by rwa [Fresh, ← h]
  have hx' : Fresh x (land y s) := by
    change (land y s).key x.ident ≠ some x.digest
    rw [h, land_key]
    exact fun e ↦ hd (Option.some.inj e).symm
  rw [ingest_of_fresh hy', ingest_of_fresh hx']
  unfold land
  dsimp only
  simp [h]

/-- DOR-8 The control: on one identity with two digests, the two orders give two chains, so
commands on one identity do not commute and must be ordered by the queue. -/
theorem same_identity_not_comm (x y : Source R D G) (h : x.ident = y.ident)
    (hd : x.digest ≠ y.digest) (s : State R D G) (hx : s.key x.ident ≠ some x.digest)
    (hy : s.key x.ident ≠ some y.digest) :
    (ingest x (ingest y s)).chain x.ident ≠ (ingest y (ingest x s)).chain x.ident := by
  intro heq
  have h1 := congrArg List.getLast? heq
  rw [same_identity_orders_the_chain x y h hd s hy, appendIfNew_getLast?, h,
    same_identity_orders_the_chain y x h.symm hd.symm s (by rwa [← h]),
    appendIfNew_getLast?] at h1
  exact hd (Option.some.inj h1)

/-! ### DOR-7 Crash convergence: the key last -/

/-- The rows of a prefix of the stages lie among the rows. -/
theorem foldr_union_take_subset (l : List (Finset R)) (k : ℕ) :
    (l.take k).foldr (· ∪ ·) ∅ ⊆ l.foldr (· ∪ ·) ∅ := by
  induction l generalizing k with
  | nil => simp
  | cons a l ih =>
    cases k with
    | zero => simp
    | succ k =>
      simp only [List.take_succ_cons, List.foldr_cons]
      exact union_subset_union_right (ih k)

/-- A run, one step at a time. -/
theorem run_cons (a : Step R D G) (w : List (Step R D G)) (s : State R D G) :
    run (a :: w) s = run w (a.apply s) := rfl

/-- A run splits at a concatenation. -/
theorem run_append (w₁ w₂ : List (Step R D G)) (s : State R D G) :
    run (w₁ ++ w₂) s = run w₂ (run w₁ s) := by
  unfold run
  exact List.foldl_append ..

/-- The rows steps of a list of stages add their union and touch nothing else. -/
theorem run_rows (l : List (Finset R)) (t : State R D G) :
    run (l.map Step.rows) t = ⟨t.rows ∪ l.foldr (· ∪ ·) ∅, t.chain, t.key⟩ := by
  induction l generalizing t with
  | nil => simp [run]
  | cons a l ih =>
    rw [List.map_cons, run_cons, ih]
    refine State.ext ?_ rfl rfl
    change t.rows ∪ a ∪ l.foldr (· ∪ ·) ∅ = t.rows ∪ (a ∪ l.foldr (· ∪ ·) ∅)
    rw [union_assoc]

/-- A command's steps, run in order, are its landing. -/
theorem run_steps (x : Source R D G) (s : State R D G) : run x.steps s = land x s := by
  unfold Source.steps
  rw [run_append, run_rows]
  rfl

/-- Landing on a state that holds some of the rows already, with the chain and the key as they
were, is landing on the state before. -/
theorem land_rows_prefix (x : Source R D G) (s : State R D G) {T : Finset R} (hT : T ⊆ x.rows) :
    land x ⟨s.rows ∪ T, s.chain, s.key⟩ = land x s := by
  refine State.ext ?_ rfl rfl
  change s.rows ∪ T ∪ x.rows = s.rows ∪ x.rows
  rw [union_assoc, union_eq_right.2 hT]

/-- Landing on a state that landed already, with the key as it was, is landing on the state
before: the rows are held and the head is the digest. -/
theorem land_after_land (x : Source R D G) (s : State R D G) :
    land x ⟨(land x s).rows, (land x s).chain, s.key⟩ = land x s := by
  refine State.ext ?_ (funext fun d ↦ ?_) rfl
  · change s.rows ∪ x.rows ∪ x.rows = s.rows ∪ x.rows
    rw [union_assoc, union_self]
  · simp only [land]
    by_cases h : d = x.ident
    · subst h
      simp [appendIfNew_idem]
    · simp [h]

/-- **DOR-7** With the key written last, a fresh run interrupted after any step converges: the next
run lands exactly the uninterrupted run's state. -/
theorem ingest_prefix_converges (x : Source R D G) (s : State R D G) (hs : Fresh x s) (k : ℕ) :
    ingest x (run (x.steps.take k) s) = ingest x s := by
  rw [ingest_of_fresh hs]
  unfold Source.steps
  rw [List.take_append, run_append, ← List.map_take, run_rows]
  rcases Nat.lt_or_ge k (x.stages.map Step.rows).length with hk | hk
  · -- within the rows: the key is untouched, the run is repeated in full
    rw [Nat.sub_eq_zero_of_le hk.le, List.take_zero, ingest_of_fresh]
    · exact land_rows_prefix x s (foldr_union_take_subset _ _)
    · exact hs
  · rw [List.length_map] at hk ⊢
    rw [List.take_of_length_le hk]
    rcases Nat.lt_or_ge (k - x.stages.length) 1 with h0 | h1
    · -- exactly the rows
      rw [Nat.lt_one_iff.1 h0, List.take_zero, ingest_of_fresh]
      · exact land_rows_prefix x s subset_rfl
      · exact hs
    · rcases Nat.lt_or_ge (k - x.stages.length) 2 with h1' | h2
      · -- the landing ran, the key did not: still fresh, the run is repeated in full
        have hm : k - x.stages.length = 1 := by omega
        rw [hm, ingest_of_fresh]
        · exact land_after_land x s
        · exact hs
      · -- the whole run: the key names the digest, nothing more lands
        have hm : ([Step.land x.ident x.digest, Step.key x.ident x.digest]
            : List (Step R D G)).take (k - x.stages.length)
            = [Step.land x.ident x.digest, Step.key x.ident x.digest] :=
          List.take_of_length_le (by simpa using h2)
        rw [hm]
        exact ingest_of_keyed (land_key x s)

/-- **DOR-7** The control at its extreme: with the key written first, a run interrupted right after
it is never repaired, since the next run reads the key and lands nothing. -/
theorem key_first_does_not_converge (x : Source R D G) (s : State R D G) (hs : Fresh x s)
    (hx : ¬ x.rows ⊆ s.rows) :
    ingest x (run (x.stepsKeyFirst.take 1) s) ≠ ingest x s := by
  intro heq
  have h1 := congrArg State.rows heq
  unfold Source.stepsKeyFirst at h1
  rw [List.take_succ_cons, List.take_zero, ingest_of_fresh hs] at h1
  have hk : (run [Step.key x.ident x.digest] s).key x.ident = some x.digest := by
    simp [run, Step.apply]
  rw [ingest_of_keyed hk] at h1
  change s.rows = s.rows ∪ x.rows at h1
  exact hx (union_eq_left.1 h1.symm)

/-- **DOR-7** The control in the audit's defect 1's own order: a key written after some steps, the
plane's rows in the defect, and before the attestation and the version row, the run interrupted
right after it, is never repaired when some of the command's rows are not yet held, since the
next run reads the key and lands nothing. -/
theorem key_early_does_not_converge (x : Source R D G) (s : State R D G) (hs : Fresh x s)
    (v : List (Step R D G)) (hx : ¬ x.rows ⊆ (run v s).rows) :
    ingest x (run (v ++ [Step.key x.ident x.digest]) s) ≠ ingest x s := by
  intro heq
  have hk : (run (v ++ [Step.key x.ident x.digest]) s).key x.ident = some x.digest := by
    rw [run_append]
    simp [run, Step.apply]
  have h1 := congrArg State.rows heq
  rw [ingest_of_keyed hk, ingest_of_fresh hs, run_append] at h1
  change (run v s).rows = s.rows ∪ x.rows at h1
  exact hx (h1 ▸ subset_union_right)

/-! ### DOR-6 The receipt -/

/-- DOR-6 The receipt is complete: a fresh command's state after is the state before plus the
receipt's rows. -/
theorem receipt_complete (x : Source R D G) (s : State R D G) (hs : Fresh x s) :
    (ingest x s).rows = s.rows ∪ (receipt x).rows := by
  rw [ingest_of_fresh hs]
  rfl

/-- DOR-6 The receipt's digest is the chain's new head. -/
theorem receipt_head (x : Source R D G) (s : State R D G) (hs : Fresh x s) :
    ((ingest x s).chain (receipt x).ident).getLast? = some (receipt x).digest := by
  rw [ingest_of_fresh hs]
  simp [land, receipt, appendIfNew_getLast?]

/-- DOR-6 The receipt never over-claims: on a sound state, every row it names is held after. -/
theorem receipt_rows_subset (x : Source R D G) (s : State R D G) (hs : Sound x s) :
    (receipt x).rows ⊆ (ingest x s).rows := by
  unfold ingest
  split_ifs with hk
  · exact hs hk
  · exact subset_union_right

/-! ### DOR-5 The serial cost is the new atoms -/

variable (IsAtom : R → Prop) [DecidablePred IsAtom]

/-- The atoms two sets add on top of a third, counted in sequence, are the atoms of their
union: a shared atom is counted once. -/
theorem atoms_split (A B S : Finset R) :
    (atomsOf IsAtom A \ S).card + (atomsOf IsAtom B \ (S ∪ A)).card
      = (atomsOf IsAtom (A ∪ B) \ S).card := by
  unfold atomsOf
  have hdisj : Disjoint (A.filter IsAtom \ S) (B.filter IsAtom \ (S ∪ A)) := by
    refine disjoint_left.2 fun r h1 h2 ↦ ?_
    simp only [mem_sdiff, mem_filter, mem_union, not_or] at h1 h2
    exact h2.2.2 h1.1.1
  rw [← card_union_eq_card_add_card.2 hdisj]
  congr 1
  ext r
  simp only [mem_union, mem_sdiff, mem_filter, not_or]
  tauto

omit [DecidableEq D] [DecidableEq G] in
/-- DOR-5 A command embeds nothing iff the plane holds its atoms. -/
theorem embeds_eq_zero_iff (x : Source R D G) (s : State R D G) :
    embeds IsAtom x s = 0 ↔ atomsOf IsAtom x.rows ⊆ s.rows := by
  unfold embeds
  rw [card_eq_zero, sdiff_eq_empty_iff_subset]

/-- DOR-5 A re-ingest of held content embeds nothing. -/
theorem embeds_ingest_twice_zero (x : Source R D G) (s : State R D G) (hs : Sound x s) :
    embeds IsAtom x (ingest x s) = 0 := by
  rw [embeds_eq_zero_iff]
  exact (filter_subset _ _).trans (receipt_rows_subset x s hs)

/-- DOR-5 Two fresh commands sharing an atom pay for it once. -/
theorem embeds_share (x y : Source R D G) (s : State R D G) (hs : Fresh x s) :
    embeds IsAtom x s + embeds IsAtom y (ingest x s)
      = (atomsOf IsAtom (x.rows ∪ y.rows) \ s.rows).card := by
  unfold embeds
  rw [receipt_complete x s hs]
  exact atoms_split IsAtom x.rows y.rows s.rows

/-- Fresh commands on distinct identities stay fresh as the batch lands. -/
theorem fresh_of_land (x y : Source R D G) (s : State R D G) (h : x.ident ≠ y.ident)
    (hy : Fresh y s) : Fresh y (land x s) := by
  unfold Fresh
  rwa [land_key_other x s (Ne.symm h)]

/-- DOR-5 A batch of fresh commands on distinct identities embeds exactly its distinct new
atoms, whatever it shares among its commands. -/
theorem embedsBatch_eq (l : List (Source R D G)) (s : State R D G)
    (hn : (l.map Source.ident).Nodup) (hf : ∀ x ∈ l, Fresh x s) :
    embedsBatch IsAtom l s = (atomsOf IsAtom (rowsOf l) \ s.rows).card := by
  induction l generalizing s with
  | nil => simp [embedsBatch, rowsOf, atomsOf]
  | cons x l ih =>
    simp only [List.map_cons, List.nodup_cons, List.mem_map] at hn
    have hx : Fresh x s := hf x (List.mem_cons_self ..)
    have hxl : ∀ y ∈ l, x.ident ≠ y.ident := fun y hy heq ↦ hn.1 ⟨y, hy, heq.symm⟩
    have hf' : ∀ y ∈ l, Fresh y (ingest x s) := fun y hy ↦ by
      rw [ingest_of_fresh hx]
      exact fresh_of_land x y s (hxl y hy) (hf y (List.mem_cons_of_mem x hy))
    simp only [embedsBatch, rowsOf, List.foldr_cons]
    rw [ih (ingest x s) hn.2 hf', embeds, receipt_complete x s hx]
    exact atoms_split IsAtom x.rows (rowsOf l) s.rows

/-! ### DOR-9 Parallel dispatch: the steps of fresh commands on distinct identities commute -/

/-- Two steps that do not conflict commute. -/
theorem Step.apply_comm (a b : Step R D G) (h : ¬ a.Conflicts b) (s : State R D G) :
    a.apply (b.apply s) = b.apply (a.apply s) := by
  cases a with
  | rows t =>
    cases b with
    | rows u =>
      refine State.ext ?_ rfl rfl
      change s.rows ∪ u ∪ t = s.rows ∪ t ∪ u
      rw [union_right_comm]
    | land d g => rfl
    | key d g => rfl
  | land d g =>
    cases b with
    | rows u => rfl
    | key e g' => rfl
    | land e g' =>
      have hde : d ≠ e := h
      refine State.ext rfl (funext fun f ↦ ?_) rfl
      simp only [Step.apply]
      by_cases hd : f = d
      · subst hd
        simp [hde]
      · by_cases he : f = e
        · subst he
          simp [hd]
        · simp [hd, he]
  | key d g =>
    cases b with
    | rows u => rfl
    | land e g' => rfl
    | key e g' =>
      have hde : d ≠ e := h
      refine State.ext rfl rfl (funext fun f ↦ ?_)
      simp only [Step.apply]
      by_cases hd : f = d
      · subst hd
        simp [hde]
      · by_cases he : f = e
        · subst he
          simp [hd]
        · simp [hd, he]

/-- Steps that commute pairwise run to the same state in any order. -/
theorem run_perm_of_comm {w v : List (Step R D G)} (hp : w.Perm v) :
    ∀ s : State R D G, (∀ a ∈ v, ∀ b ∈ v, ∀ t, a.apply (b.apply t) = b.apply (a.apply t)) →
      run w s = run v s := by
  induction hp with
  | nil => intro s _; rfl
  | cons a p ih =>
    intro s hc
    simp only [run_cons]
    exact ih _ fun x hx y hy ↦ hc x (List.mem_cons_of_mem a hx) y (List.mem_cons_of_mem a hy)
  | swap x y l =>
    intro s hc
    simp only [run_cons]
    rw [hc x (by simp) y (by simp) s]
  | trans p₁ p₂ ih₁ ih₂ =>
    intro s hc
    rw [← ih₂ s hc]
    exact ih₁ s fun a ha b hb ↦ hc a (p₂.mem_iff.1 ha) b (p₂.mem_iff.1 hb)

/-- The steps of a batch of fresh commands on distinct identities, in order, are the batch. -/
theorem run_stepsOf (l : List (Source R D G)) (s : State R D G)
    (hn : (l.map Source.ident).Nodup) (hf : ∀ x ∈ l, Fresh x s) :
    run (stepsOf l) s = batch l s := by
  induction l generalizing s with
  | nil => rfl
  | cons x l ih =>
    simp only [List.map_cons, List.nodup_cons, List.mem_map] at hn
    have hx : Fresh x s := hf x (List.mem_cons_self ..)
    have hxl : ∀ y ∈ l, x.ident ≠ y.ident := fun y hy heq ↦ hn.1 ⟨y, hy, heq.symm⟩
    simp only [stepsOf, List.flatMap_cons, run_append, batch_cons, run_steps, ingest_of_fresh hx]
    exact ih (land x s) hn.2 fun y hy ↦
      fresh_of_land x y s (hxl y hy) (hf y (List.mem_cons_of_mem x hy))

omit [DecidableEq R] [DecidableEq D] [DecidableEq G] in
/-- A step on an identity among a batch's steps is some command's landing or key. -/
theorem ident_mem_stepsOf {l : List (Source R D G)} {a : Step R D G} {d : D}
    (ha : a ∈ stepsOf l) (hd : a.ident = some d) : ∃ x ∈ l, x.ident = d ∧
      (a = Step.land x.ident x.digest ∨ a = Step.key x.ident x.digest) := by
  simp only [stepsOf, List.mem_flatMap, Source.steps, List.mem_append, List.mem_map,
    List.mem_cons, List.not_mem_nil, or_false] at ha
  obtain ⟨x, hx, h | h | h⟩ := ha
  · obtain ⟨t, -, rfl⟩ := h
    simp [Step.ident] at hd
  · subst h
    exact ⟨x, hx, Option.some.inj hd, Or.inl rfl⟩
  · subst h
    exact ⟨x, hx, Option.some.inj hd, Or.inr rfl⟩

/-- The steps of a batch on distinct identities commute pairwise: two of them conflict only if both
land, or both key, one identity, and then they are one command's one step. -/
theorem stepsOf_comm {l : List (Source R D G)} (hn : (l.map Source.ident).Nodup)
    {a b : Step R D G} (ha : a ∈ stepsOf l) (hb : b ∈ stepsOf l) (t : State R D G) :
    a.apply (b.apply t) = b.apply (a.apply t) := by
  by_cases hab : a = b
  · subst hab; rfl
  refine Step.apply_comm a b ?_ t
  intro hc
  -- a conflict is two landings, or two keys, on one identity: from one command, so one step
  have key : ∃ d, a.ident = some d ∧ b.ident = some d ∧
      ((∃ g g', a = Step.land d g ∧ b = Step.land d g') ∨
        (∃ g g', a = Step.key d g ∧ b = Step.key d g')) := by
    cases a with
    | rows _ => exact absurd hc id
    | land d g =>
      cases b with
      | rows _ => exact absurd hc id
      | key _ _ => exact absurd hc id
      | land e g' =>
        have hde : d = e := hc
        subst hde
        exact ⟨d, rfl, rfl, Or.inl ⟨g, g', rfl, rfl⟩⟩
    | key d g =>
      cases b with
      | rows _ => exact absurd hc id
      | land _ _ => exact absurd hc id
      | key e g' =>
        have hde : d = e := hc
        subst hde
        exact ⟨d, rfl, rfl, Or.inr ⟨g, g', rfl, rfl⟩⟩
  obtain ⟨d, had, hbd, hab'⟩ := key
  obtain ⟨x, hx, hxd, hxa⟩ := ident_mem_stepsOf ha had
  obtain ⟨y, hy, hyd, hyb⟩ := ident_mem_stepsOf hb hbd
  have hxy : x = y := List.inj_on_of_nodup_map hn hx hy (hxd.trans hyd.symm)
  subst hxy
  apply hab
  rcases hab' with ⟨g, g', rfl, rfl⟩ | ⟨g, g', rfl, rfl⟩
  · rcases hxa with h1 | h1 <;> rcases hyb with h2 | h2 <;> simp_all
  · rcases hxa with h1 | h1 <;> rcases hyb with h2 | h2 <;> simp_all

/-- DOR-9 Any order of the steps of fresh commands on pairwise distinct identities, which
includes every interleaving of their stages, lands the batch's state: the queue may dispatch
non-conflicting commands in parallel. -/
theorem run_perm_of_disjoint {w : List (Step R D G)} {l : List (Source R D G)}
    (hp : w.Perm (stepsOf l)) (hn : (l.map Source.ident).Nodup) (s : State R D G)
    (hf : ∀ x ∈ l, Fresh x s) : run w s = batch l s := by
  rw [← run_stepsOf l s hn hf]
  exact run_perm_of_comm hp s fun a ha b hb t ↦ stepsOf_comm hn ha hb t

/-! ### DOR-10 Conflict-serializability: a schedule that orders each conflict as the serial one -/

omit [DecidableEq R] [DecidableEq D] [DecidableEq G] in
/-- Two steps conflict exactly when they share a class. -/
theorem Step.conflicts_iff_cls (a b : Step R D G) :
    a.Conflicts b ↔ ∃ c, a.cls = some c ∧ b.cls = some c := by
  cases a <;> cases b <;> simp [Step.Conflicts, Step.cls, eq_comm]

/-- Steps of distinct classes commute. -/
theorem Step.apply_comm_of_cls (a b : Step R D G) (h : ∀ c, a.cls = some c → b.cls ≠ some c)
    (s : State R D G) : a.apply (b.apply s) = b.apply (a.apply s) := by
  refine Step.apply_comm a b (fun hc ↦ ?_) s
  obtain ⟨c, ha, hb⟩ := (Step.conflicts_iff_cls a b).1 hc
  exact h c ha hb

/-- A step that commutes with every step before it may run first. -/
theorem run_move_front (b : Step R D G) (w₁ w₂ : List (Step R D G))
    (h : ∀ a ∈ w₁, ∀ t : State R D G, a.apply (b.apply t) = b.apply (a.apply t))
    (s : State R D G) : run (w₁ ++ b :: w₂) s = run (w₁ ++ w₂) (b.apply s) := by
  induction w₁ generalizing s with
  | nil => rfl
  | cons a w₁ ih =>
    simp only [List.cons_append, run_cons]
    rw [ih (fun x hx ↦ h x (List.mem_cons_of_mem a hx)) (a.apply s), h a List.mem_cons_self s]

/-- DOR-10 Conflict-equivalence is state-equivalence, the classical theorem of serializability
for the door's steps: a schedule that is a permutation of another and orders the steps of every
class (the landings on one identity, the keys of one identity) as the other does runs to the
same state. Steps of distinct classes commute, so each step of the other schedule can be moved
to the front past the steps before it, none of which is of its class. -/
theorem run_eq_of_cls_filter {w v : List (Step R D G)} (hp : w.Perm v)
    (hc : ∀ c, w.filter (fun a ↦ a.cls = some c) = v.filter (fun a ↦ a.cls = some c))
    (s : State R D G) : run w s = run v s := by
  induction v generalizing w s with
  | nil => rw [List.perm_nil.1 hp]
  | cons b v ih =>
    -- `b` is the first step of its class in `w`: everything before it commutes with it
    have hmove : ∃ w₁ w₂, w = w₁ ++ b :: w₂ ∧ ∀ a ∈ w₁, ∀ c, a.cls = some c → b.cls ≠ some c := by
      cases hb : b.cls with
      | none =>
        obtain ⟨w₁, w₂, h⟩ := List.append_of_mem (hp.symm.subset List.mem_cons_self)
        exact ⟨w₁, w₂, h, fun _ _ _ _ ↦ by simp⟩
      | some c₀ =>
        have h1 : w.filter (fun a ↦ a.cls = some c₀)
            = b :: v.filter (fun a ↦ a.cls = some c₀) := by
          rw [hc c₀, List.filter_cons_of_pos (by simp [hb])]
        obtain ⟨w₁, w₂, h, hw₁, -, -⟩ := List.filter_eq_cons_iff.1 h1
        refine ⟨w₁, w₂, h, fun a ha c hac hbc ↦ hw₁ a ha ?_⟩
        obtain rfl : c₀ = c := Option.some.inj hbc
        simpa using hac
    obtain ⟨w₁, w₂, rfl, hw₁⟩ := hmove
    rw [run_move_front b w₁ w₂ (fun a ha t ↦ Step.apply_comm_of_cls a b (hw₁ a ha) t) s, run_cons]
    refine ih (List.perm_middle.symm.trans hp).cons_inv (fun c ↦ ?_) (b.apply s)
    have h := hc c
    by_cases hbc : b.cls = some c
    · have h0 : w₁.filter (fun a ↦ a.cls = some c) = [] := by
        rw [List.filter_eq_nil_iff]
        intro a ha hac
        exact hw₁ a ha c (by simpa using hac) hbc
      rw [List.filter_append, List.filter_cons_of_pos (by simpa using hbc), h0,
        List.filter_cons_of_pos (by simpa using hbc)] at h
      rw [List.filter_append, h0]
      simpa using h
    · rw [List.filter_append, List.filter_cons_of_neg (by simpa using hbc),
        List.filter_cons_of_neg (by simpa using hbc), ← List.filter_append] at h
      exact h

/-- The serial schedule of a list whose every command is fresh at its turn lands the batch. -/
theorem run_stepsOf_along (l : List (Source R D G)) (s : State R D G) (h : FreshAlong l s) :
    run (stepsOf l) s = batch l s := by
  induction l generalizing s with
  | nil => rfl
  | cons x l ih =>
    obtain ⟨hx, hl⟩ : Fresh x s ∧ FreshAlong l (land x s) := h
    simp only [stepsOf, List.flatMap_cons, run_append, batch_cons, run_steps, ingest_of_fresh hx]
    exact ih (land x s) hl

/-- DOR-10 Conflict-serializability by identity, repeated identities allowed: a schedule of a
batch's steps that orders the landings on each identity, and the keys of each identity, as the
list does lands the batch, when each command is fresh at its turn. The queue that runs commands
on one identity one after another, in queue order, and anything else in parallel, schedules
nothing else. -/
theorem serializable {w : List (Step R D G)} {l : List (Source R D G)}
    (hp : w.Perm (stepsOf l))
    (hc : ∀ c, w.filter (fun a ↦ a.cls = some c) = (stepsOf l).filter (fun a ↦ a.cls = some c))
    (s : State R D G) (h : FreshAlong l s) : run w s = batch l s := by
  rw [run_eq_of_cls_filter hp hc, run_stepsOf_along l s h]

/-- One version of the one note, with no rows: the control's commands. -/
abbrev version (g : Fin 2) : Source (Fin 1) (Fin 1) (Fin 2) := ⟨[], 0, g⟩

/-- The empty state of the control. -/
abbrev empty : State (Fin 1) (Fin 1) (Fin 2) := ⟨∅, fun _ ↦ [], fun _ ↦ none⟩

/-- DOR-10 The control: a permutation alone is not enough. Two fresh commands on one identity,
their steps scheduled in the other order, land the other chain. -/
theorem serializable_needs_the_order :
    ((version 1).steps ++ (version 0).steps).Perm (stepsOf [version 0, version 1]) ∧
      FreshAlong [version 0, version 1] empty ∧
      (run ((version 1).steps ++ (version 0).steps) empty).chain 0
        ≠ (batch [version 0, version 1] empty).chain 0 := by
  refine ⟨List.perm_append_comm, ?_, ?_⟩
  · simp [FreshAlong, Fresh, land]
  · decide

/-- The guard drops a command keyed at its turn, and the batch is that of the rest. -/
theorem batch_landsOf (l : List (Source R D G)) (s : State R D G) :
    batch (landsOf l s) s = batch l s := by
  induction l generalizing s with
  | nil => rfl
  | cons x l ih =>
    by_cases h : s.key x.ident = some x.digest
    · simp only [landsOf, h, ite_true, batch_cons, ingest_of_keyed h]
      exact ih s
    · simp only [landsOf, h, ite_false, batch_cons, ingest_of_fresh h]
      exact ih (land x s)

/-- The commands that land are fresh along their own order. -/
theorem freshAlong_landsOf (l : List (Source R D G)) (s : State R D G) :
    FreshAlong (landsOf l s) s := by
  induction l generalizing s with
  | nil => trivial
  | cons x l ih =>
    by_cases h : s.key x.ident = some x.digest
    · simp only [landsOf, h, ite_true]
      exact ih s
    · simp only [landsOf, h, ite_false]
      exact ⟨h, ih (land x s)⟩

/-- DOR-10 With the guard: a schedule of the steps of the commands that land, ordering each class
as their serial order does, lands the batch of the whole list, repeated identities allowed. -/
theorem serializable_landsOf {w : List (Step R D G)} {l : List (Source R D G)} (s : State R D G)
    (hp : w.Perm (stepsOf (landsOf l s)))
    (hc : ∀ c, w.filter (fun a ↦ a.cls = some c)
      = (stepsOf (landsOf l s)).filter (fun a ↦ a.cls = some c)) :
    run w s = batch l s := by
  rw [serializable hp hc s (freshAlong_landsOf l s), batch_landsOf]

/-- The state holding version `g` of the one note: the control's start. -/
abbrev holding (g : Fin 2) : State (Fin 1) (Fin 1) (Fin 2) := ⟨∅, fun _ ↦ [g], fun _ ↦ some g⟩

/-- DOR-10 The control on the guard's moment, the second review's counterexample: holding
version 0, the batch [an edit to 1, a revert to 0] lands both, each fresh at its turn; but a revert
whose guard reads the key before the edit has written its own finds its digest there, skips, and
the note ends at the edit. The model's steps carry no read, so the moment of the guard is the
dispatcher's to fix: commands on one identity run whole, one after another. -/
theorem early_guard_skips :
    FreshAlong [version 1, version 0] (holding 0) ∧
      (batch [version 1] (ingest (version 0) (holding 0))).chain 0
        ≠ (batch [version 1, version 0] (holding 0)).chain 0 := by
  refine ⟨?_, ?_⟩
  · simp [FreshAlong, Fresh, land]
  · decide

/-! ### DOR-11 Crash convergence under a parallel run -/

/-- A run's key at an identity none of its steps keys is the key before. -/
theorem run_key_of_not_keyed (w : List (Step R D G)) (d : D)
    (h : ∀ a ∈ w, ∀ g, a ≠ Step.key d g) (s : State R D G) : (run w s).key d = s.key d := by
  induction w generalizing s with
  | nil => rfl
  | cons a w ih =>
    rw [run_cons, ih (fun b hb ↦ h b (List.mem_cons_of_mem a hb)) (a.apply s)]
    cases a with
    | rows t => rfl
    | land e g => rfl
    | key e g =>
      change (if d = e then some g else s.key d) = s.key d
      have hde : d ≠ e := by
        rintro rfl
        exact h _ List.mem_cons_self g rfl
      simp [hde]

omit [DecidableEq R] [DecidableEq D] [DecidableEq G] in
/-- A prefix's step is a step of the batch. -/
theorem prefixesOf_subset {k : Source R D G → ℕ} {l : List (Source R D G)} {a : Step R D G}
    (ha : a ∈ prefixesOf k l) : a ∈ stepsOf l := by
  simp only [prefixesOf, stepsOf, List.mem_flatMap] at ha ⊢
  obtain ⟨x, hx, hax⟩ := ha
  exact ⟨x, hx, List.take_subset _ _ hax⟩

/-- DOR-11 Crash convergence under a parallel run: if each command of a batch of fresh commands
on distinct identities has run a prefix of its own steps (its key last), in any global order,
which is every crash point of every interleaving of their runs, the batch run again lands
exactly the uninterrupted batch's state. -/
theorem batch_after_prefixes {w : List (Step R D G)} (k : Source R D G → ℕ)
    {l : List (Source R D G)} (hp : w.Perm (prefixesOf k l)) (hn : (l.map Source.ident).Nodup)
    (s : State R D G) (hf : ∀ x ∈ l, Fresh x s) : batch l (run w s) = batch l s := by
  rw [run_perm_of_comm hp s fun a ha b hb t ↦
    stepsOf_comm hn (prefixesOf_subset ha) (prefixesOf_subset hb) t]
  clear hp
  clear w
  induction l generalizing s with
  | nil => rfl
  | cons x l ih =>
    have hn' := hn
    simp only [List.map_cons, List.nodup_cons, List.mem_map] at hn
    have hx : Fresh x s := hf x List.mem_cons_self
    have hxl : ∀ y ∈ l, x.ident ≠ y.ident := fun y hy heq ↦ hn.1 ⟨y, hy, heq.symm⟩
    have hmem : ∀ a, a ∈ x.steps ∨ a ∈ prefixesOf k l → a ∈ stepsOf (x :: l) := by
      rintro a (ha | ha)
      · simp only [stepsOf, List.flatMap_cons, List.mem_append]
        exact Or.inl ha
      · simp only [stepsOf, List.flatMap_cons, List.mem_append]
        exact Or.inr (prefixesOf_subset ha)
    have hPkey : ∀ a ∈ prefixesOf k l, ∀ g, a ≠ Step.key x.ident g := by
      rintro a ha g rfl
      obtain ⟨y, hy, hyd, -⟩ := ident_mem_stepsOf (prefixesOf_subset ha) rfl
      exact hxl y hy hyd.symm
    have hfresh : Fresh x (run (prefixesOf k l) s) := by
      change (run (prefixesOf k l) s).key x.ident ≠ some x.digest
      rw [run_key_of_not_keyed _ _ hPkey]
      exact hx
    -- x's prefix may run last: its steps commute with the others'
    have hA : run (prefixesOf k (x :: l)) s
        = run (x.steps.take (k x)) (run (prefixesOf k l) s) := by
      rw [show prefixesOf k (x :: l) = x.steps.take (k x) ++ prefixesOf k l from
        List.flatMap_cons, ← run_append]
      refine run_perm_of_comm List.perm_append_comm s fun a ha b hb t ↦ stepsOf_comm hn' ?_ ?_ t
      · rcases List.mem_append.1 ha with h | h
        · exact hmem a (Or.inr h)
        · exact hmem a (Or.inl (List.take_subset _ _ h))
      · rcases List.mem_append.1 hb with h | h
        · exact hmem b (Or.inr h)
        · exact hmem b (Or.inl (List.take_subset _ _ h))
    -- x's landing commutes with the others' prefixes
    have hC : ingest x (run (prefixesOf k l) s) = run (prefixesOf k l) (ingest x s) := by
      rw [ingest_of_fresh hfresh, ingest_of_fresh hx, ← run_steps, ← run_steps, ← run_append,
        ← run_append]
      refine run_perm_of_comm List.perm_append_comm s fun a ha b hb t ↦ stepsOf_comm hn' ?_ ?_ t
      · rcases List.mem_append.1 ha with h | h
        · exact hmem a (Or.inl h)
        · exact hmem a (Or.inr h)
      · rcases List.mem_append.1 hb with h | h
        · exact hmem b (Or.inl h)
        · exact hmem b (Or.inr h)
    simp only [batch_cons]
    rw [hA, ingest_prefix_converges x _ hfresh, hC]
    refine ih hn.2 (ingest x s) fun y hy ↦ ?_
    rw [ingest_of_fresh hx]
    exact fresh_of_land x y s (hxl y hy) (hf y (List.mem_cons_of_mem x hy))

/-- DOR-11 The control on its hypothesis: two versions of one note, the second run whole before
the first starts, the run stopped there; the batch run again lands a chain the uninterrupted batch
never would. On one identity a crash point need not converge, and running such commands one after
another is not enough either (`rerun_whole_batch_diverges`): what converges is running again only
the command that was interrupted and the ones after it (`batch_after_interrupted`). -/
theorem prefixes_need_distinct_identities :
    (stepsOf [version 1]).Perm
        (prefixesOf (fun x ↦ if x.digest = 1 then 2 else 0) [version 0, version 1]) ∧
      (batch [version 0, version 1] (run (stepsOf [version 1]) empty)).chain 0
        ≠ (batch [version 0, version 1] empty).chain 0 := by
  refine ⟨List.Perm.of_eq rfl, ?_⟩
  decide

/-- A batch splits at a concatenation. -/
theorem batch_append (l₁ l₂ : List (Source R D G)) (s : State R D G) :
    batch (l₁ ++ l₂) s = batch l₂ (batch l₁ s) := by
  unfold batch
  exact List.foldl_append ..

/-- Fresh along a concatenation: along the first part, then along the second from where the
first left the state. -/
theorem freshAlong_append {l₁ l₂ : List (Source R D G)} {s : State R D G}
    (h : FreshAlong (l₁ ++ l₂) s) : FreshAlong l₁ s ∧ FreshAlong l₂ (batch l₁ s) := by
  induction l₁ generalizing s with
  | nil => exact ⟨trivial, h⟩
  | cons x l ih =>
    obtain ⟨hx, hl⟩ : Fresh x s ∧ FreshAlong (l ++ l₂) (land x s) := h
    obtain ⟨h1, h2⟩ := ih hl
    refine ⟨⟨hx, h1⟩, ?_⟩
    rw [batch_cons, ingest_of_fresh hx]
    exact h2

/-- DOR-11 With repeated identities: a serial run of commands each fresh at its turn, stopped
inside one of them, converges when what runs again is that command and the ones after it, the
ones not yet landed. The queue keeps this by skipping a request already receipted as landed. -/
theorem batch_after_interrupted (l₁ : List (Source R D G)) (x : Source R D G)
    (l₂ : List (Source R D G)) (s : State R D G) (h : FreshAlong (l₁ ++ x :: l₂) s) (k : ℕ) :
    batch (x :: l₂) (run (stepsOf l₁ ++ x.steps.take k) s) = batch (l₁ ++ x :: l₂) s := by
  obtain ⟨h1, h2⟩ := freshAlong_append h
  obtain ⟨hx, -⟩ : Fresh x (batch l₁ s) ∧ FreshAlong l₂ (land x (batch l₁ s)) := h2
  rw [run_append, run_stepsOf_along l₁ s h1, batch_cons, ingest_prefix_converges x _ hx,
    ← batch_cons, batch_append]

/-- DOR-11 The control on what runs again: one note edited, edited back and edited again, in
order, the run stopped inside the third; the whole batch run again lands another chain, since
the first command finds the second's key and lands again. -/
theorem rerun_whole_batch_diverges :
    FreshAlong [version 0, version 1, version 0] empty ∧
      (batch [version 0, version 1, version 0]
          (run (stepsOf [version 0, version 1] ++ (version 0).steps.take 1) empty)).chain 0
        ≠ (batch [version 0, version 1, version 0] empty).chain 0 := by
  refine ⟨?_, ?_⟩
  · simp [FreshAlong, Fresh, land]
  · decide

/-! ### DOR-7 in the code's order: any of a command's steps but its key, in any order -/

omit [DecidableEq D] [DecidableEq G] in
/-- A stage's rows lie among the command's rows. -/
theorem subset_foldr_union {l : List (Finset R)} {t : Finset R} (ht : t ∈ l) :
    t ⊆ l.foldr (· ∪ ·) ∅ := by
  induction l with
  | nil => simp at ht
  | cons a l ih =>
    simp only [List.foldr_cons]
    rcases List.mem_cons.1 ht with rfl | h
    · exact subset_union_left
    · exact (ih h).trans subset_union_right

/-- Landing after the landing step alone is landing: the head is the digest already. -/
theorem land_after_landStep (x : Source R D G) (s : State R D G) :
    land x ((Step.land x.ident x.digest).apply s) = land x s := by
  refine State.ext rfl (funext fun d ↦ ?_) rfl
  simp only [land, Step.apply]
  by_cases h : d = x.ident
  · subst h
    simp [appendIfNew_idem]
  · simp [h]

/-- A run of any of a command's steps but its key, in any order and any number of times, leaves
a state whose landing is the landing. -/
theorem land_run_nonkey (x : Source R D G) (w : List (Step R D G))
    (hw : ∀ a ∈ w, a = Step.land x.ident x.digest ∨ ∃ t ∈ x.stages, a = Step.rows t)
    (s : State R D G) : land x (run w s) = land x s := by
  induction w generalizing s with
  | nil => rfl
  | cons a w ih =>
    rw [run_cons, ih (fun b hb ↦ hw b (List.mem_cons_of_mem a hb)) (a.apply s)]
    rcases hw a List.mem_cons_self with rfl | ⟨t, ht, rfl⟩
    · exact land_after_landStep x s
    · exact land_rows_prefix x s (subset_foldr_union ht)

/-- **DOR-7** In the code's order: the code writes a version row before an attestation, which the
model's stage order does not; a fresh run that stopped after any of its steps but its key, in any
order and any number of times, converges under re-run all the same. The key last is all the law
needs. -/
theorem ingest_after_nonkey (x : Source R D G) (s : State R D G) (hs : Fresh x s)
    (w : List (Step R D G))
    (hw : ∀ a ∈ w, a = Step.land x.ident x.digest ∨ ∃ t ∈ x.stages, a = Step.rows t) :
    ingest x (run w s) = ingest x s := by
  have hk : (run w s).key x.ident = s.key x.ident := by
    refine run_key_of_not_keyed w x.ident (fun a ha g h ↦ ?_) s
    rcases hw a ha with rfl | ⟨t, -, rfl⟩ <;> cases h
  have hf : Fresh x (run w s) := by
    change (run w s).key x.ident ≠ some x.digest
    rw [hk]
    exact hs
  rw [ingest_of_fresh hs, ingest_of_fresh hf, land_run_nonkey x w hw s]

/-! ### DOR-12 Readers need no lock: every state the writer passes through is sound -/

/-- A run only adds rows. -/
theorem rows_subset_run (w : List (Step R D G)) (s : State R D G) : s.rows ⊆ (run w s).rows := by
  induction w generalizing s with
  | nil => exact subset_rfl
  | cons a w ih =>
    rw [run_cons]
    refine subset_trans ?_ (ih (a.apply s))
    cases a with
    | rows t => exact subset_union_left
    | land d g => exact subset_rfl
    | key d g => exact subset_rfl

/-- DOR-12 Readers need no lock: every state a key-last run passes through is sound for its
command, so a reader that reads a version only when the key names it never sees part of it. -/
theorem sound_prefix (x : Source R D G) (s : State R D G) (hs : Sound x s) (k : ℕ) :
    Sound x (run (x.steps.take k) s) := by
  unfold Source.steps
  rw [List.take_append, run_append, ← List.map_take, run_rows]
  rcases Nat.lt_or_ge (k - (x.stages.map Step.rows).length) 2 with h | h
  · -- the key has not run: it is the key before, and the rows have only grown
    have hpre : ∀ n < 2, ∀ t : State R D G,
        (run (([Step.land x.ident x.digest, Step.key x.ident x.digest] : List (Step R D G)).take n)
          t).key = t.key ∧
        (run (([Step.land x.ident x.digest, Step.key x.ident x.digest] : List (Step R D G)).take n)
          t).rows = t.rows := by
      intro n hn t
      rcases n with _ | _ | n
      · exact ⟨rfl, rfl⟩
      · exact ⟨rfl, rfl⟩
      · omega
    obtain ⟨hk, hr⟩ := hpre _ h _
    intro hkey
    rw [hk] at hkey
    rw [hr]
    exact (hs hkey).trans subset_union_left
  · -- the whole run: every stage's rows are held before the key names the digest
    rw [List.length_map] at h
    have hk : x.stages.length ≤ k := by omega
    rw [List.take_of_length_le hk, List.take_of_length_le (by simpa using h)]
    intro _
    exact subset_union_right

/-- DOR-12 The control: with the key written first, a reader that trusts the key sees a version
whose rows are not there. -/
theorem key_first_unsound (x : Source R D G) (s : State R D G) (hx : ¬ x.rows ⊆ s.rows) :
    ¬ Sound x (run (x.stepsKeyFirst.take 1) s) := by
  intro h
  apply hx
  have hk : (run (x.stepsKeyFirst.take 1) s).key x.ident = some x.digest := by
    simp [Source.stepsKeyFirst, run, Step.apply]
  exact h hk

/-- DOR-12 Readers need no lock under a parallel run: if each command of a batch on distinct
identities has run a prefix of its own steps, in any global order, from a state sound for each of
them, each is sound at that state, so a reader that trusts the keys sees each version whole or
not at all. -/
theorem sound_after_prefixes {w : List (Step R D G)} (k : Source R D G → ℕ)
    {l : List (Source R D G)} (hp : w.Perm (prefixesOf k l)) (hn : (l.map Source.ident).Nodup)
    (s : State R D G) (hs : ∀ x ∈ l, Sound x s) : ∀ x ∈ l, Sound x (run w s) := by
  rw [run_perm_of_comm hp s fun a ha b hb t ↦
    stepsOf_comm hn (prefixesOf_subset ha) (prefixesOf_subset hb) t]
  intro x hx
  obtain ⟨l₁, l₂, rfl⟩ := List.append_of_mem hx
  have hP : prefixesOf k (l₁ ++ x :: l₂)
      = prefixesOf k l₁ ++ x.steps.take (k x) ++ prefixesOf k l₂ := by
    simp [prefixesOf, List.flatMap_append, List.append_assoc]
  have hmem' : ∀ a ∈ (prefixesOf k l₁ ++ prefixesOf k l₂) ++ x.steps.take (k x),
      a ∈ stepsOf (l₁ ++ x :: l₂) := by
    intro a ha
    refine prefixesOf_subset (k := k) ?_
    rw [hP]
    simp only [List.mem_append] at ha ⊢
    tauto
  have hperm : (prefixesOf k l₁ ++ x.steps.take (k x) ++ prefixesOf k l₂).Perm
      ((prefixesOf k l₁ ++ prefixesOf k l₂) ++ x.steps.take (k x)) := by
    rw [List.append_assoc, List.append_assoc]
    exact List.Perm.append_left _ List.perm_append_comm
  have hx' : x.ident ∉ (l₁ ++ l₂).map Source.ident := by
    have h := hn
    rw [List.map_append, List.map_cons, List.nodup_middle, List.nodup_cons] at h
    rw [List.map_append]
    exact h.1
  have hnk : ∀ a ∈ prefixesOf k l₁ ++ prefixesOf k l₂, ∀ g, a ≠ Step.key x.ident g := by
    rintro a ha g rfl
    have ha' : Step.key x.ident g ∈ stepsOf (l₁ ++ l₂) := by
      apply prefixesOf_subset (k := k)
      simpa [prefixesOf, List.flatMap_append] using ha
    obtain ⟨y, hy, hyd, -⟩ := ident_mem_stepsOf ha' rfl
    exact hx' (List.mem_map.2 ⟨y, hy, hyd⟩)
  -- x's prefix may run last; before it, the others' steps leave x's key as it was
  rw [hP, run_perm_of_comm hperm s (fun a ha b hb t ↦ stepsOf_comm hn (hmem' a ha) (hmem' b hb) t),
    run_append]
  refine sound_prefix x _ (fun hkey ↦ ?_) (k x)
  rw [run_key_of_not_keyed _ _ hnk] at hkey
  exact (hs x hx hkey).trans (rows_subset_run _ _)

/-! ### DOR-1 A command needs a plane with the write bit -/

open Palace.Query in
/-- DOR-1 A command's sentence is admissible iff some granted plane admits its scope: QSA-5 at
one clause. -/
theorem command_admissible_iff {Rg H : Type*} (g : List CQ.Scope) (c : Clause) :
    Sentence.Admissible g (Sentence.clause c : Sentence Rg H) ↔ CQ.admits g c.req := by
  simp [Sentence.Admissible, Sentence.reqs]

/-- A plane above a scope with the write bit carries the write bit. -/
theorem storeWrite_of_le {r p : CQ.Scope} (hr : r.authority.storeWrite = 1) (h : r.Le p) :
    p.authority.storeWrite = 1 := by
  unfold CQ.Scope.Le CQ.Authority.Le at h
  obtain ⟨-, -, -, -, hw, -⟩ := h
  rw [hr] at hw
  revert hw
  generalize p.authority.storeWrite = b
  intro hw
  fin_cases b
  · exact absurd hw (by decide)
  · rfl

open Palace.Query in
/-- **DOR-1** A command is admissible under a grant iff a granted plane lies above its scope, at its
clock and window, and carries the write bit. -/
theorem command_admissible_iff_write {Rg H : Type*} (g : List CQ.Scope) (c : Clause)
    (hc : IsCommand c) :
    Sentence.Admissible g (Sentence.clause c : Sentence Rg H)
      ↔ ∃ p ∈ g, c.req.Le p ∧ p.authority.storeWrite = 1 := by
  rw [command_admissible_iff]
  constructor
  · rintro ⟨p, hp, hle⟩
    exact ⟨p, hp, hle, storeWrite_of_le hc hle⟩
  · rintro ⟨p, hp, hle, -⟩
    exact ⟨p, hp, hle⟩

open Palace.Query in
/-- DOR-1 The plane that admits a command covers its strata and carries the write bit. -/
theorem command_needs_a_writing_plane {Rg H : Type*} (g : List CQ.Scope) (c : Clause)
    (hc : IsCommand c) (h : Sentence.Admissible g (Sentence.clause c : Sentence Rg H)) :
    ∃ p ∈ g, c.req.sigma ⊆ p.sigma ∧ p.authority.storeWrite = 1 := by
  obtain ⟨p, hp, hle, hw⟩ := (command_admissible_iff_write g c hc).1 h
  exact ⟨p, hp, hle.1, hw⟩

open Palace.Query in
/-- **DOR-1** A read-only grant admits no command. -/
theorem readonly_admits_no_command {Rg H : Type*} (g : List CQ.Scope)
    (hg : ∀ p ∈ g, p.authority.storeWrite = 0) (c : Clause) (hc : IsCommand c) :
    ¬ Sentence.Admissible g (Sentence.clause c : Sentence Rg H) := by
  intro h
  obtain ⟨p, hp, -, hw⟩ := command_needs_a_writing_plane g c hc h
  rw [hg p hp] at hw
  exact absurd hw (by decide)

/-- **DOR-1** The Ambassador's grant as written admits a projection-event command on the mirror:
its first plane carries the write bit there (dn-ingest-door D2). -/
theorem ambassador_admits_projection_command :
    CQ.admits CQ.ambassador (commandScope {.mirrorAuthored} .projectionEvent) :=
  ⟨_, List.mem_cons_self .., by
    unfold CQ.Scope.Le CQ.Time.Le CQ.Authority.Le
    exact ⟨by decide, by decide, ⟨rfl, Or.inr (Or.inl rfl)⟩, by decide⟩⟩

/-- **DOR-1** The Ambassador's grant as written refuses a commit-clock command: its commit plane
carries no write bit, and the order is false across clocks (dn-ingest-door D2, §8). -/
theorem ambassador_refuses_commit_command :
    ¬ CQ.admits CQ.ambassador (commandScope {.reference} .commit) := by
  rintro ⟨p, hp, hle⟩
  unfold CQ.Scope.Le CQ.Time.Le CQ.Authority.Le at hle
  simp only [CQ.ambassador, List.mem_cons, List.not_mem_nil, or_false] at hp
  rcases hp with rfl | rfl | rfl
  · exact absurd hle.2.2.1.1 (by decide)
  · exact absurd hle.2.2.2.2.1 (by decide)
  · exact absurd hle.2.2.1.1 (by decide)

end Palace.Door
