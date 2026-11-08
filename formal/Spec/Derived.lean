module

public import Palace.Derived.Defs

/-!
# Two-phase ingestion, the statements

The laws of `Palace/Derived.lean` the ledger cites (docs/LAWS.md §XII, ING-19 to ING-21), each with
its proof left as `sorry`, over the model of `Palace/Derived/Defs.lean`. `lake comparator` checks
that the `Palace` library proves each one exactly as stated here, from the standard axioms alone.
What the statements cover: an item landed under lazy embedding is complete without its vector, the
landing writing no atom and no mark, the drain changing neither keys nor structures and leaving
every other identity's field alone (ING-19); an item's derivation idempotent and commuting with
other items' derivations and later landings, the drain idempotent and leaving nothing pending,
convergence of the field from any interleaving, the code's drain over the pending items reaching
the drain's field from sound truthful states, soundness kept by every key-last prefix, and the
mark-first controls (ING-20); a structural answer invariant under every embed run, a pending item's
field `none`, a reported vector the item's own structure's image, and the zero-read control
(ING-21). What they leave out: the landing's own stages and their order, which `Spec/Ingress.lean`
covers (ING-7); the plane's cache and search, which `Spec/Plane.lean` covers; and the lexical
index's arithmetic, a function of the bytes the model takes as part of the structure.
-/

@[expose] public section

open Finset

namespace Palace.Derived

variable {I S V E : Type*} [DecidableEq I] [DecidableEq S] [DecidableEq E]

omit [DecidableEq S] [DecidableEq E] in
/-- **ING-19** A landing writes no atom: the vector is not part of the item. -/
theorem land_atom (i : I) (σ : S) (s : State I S V E) : (land i σ s).atom = s.atom :=
  sorry

omit [DecidableEq S] [DecidableEq E] in
/-- **ING-19** A landing moves no mark: the drain's key is the drain's alone. -/
theorem land_mark (i : I) (σ : S) (s : State I S V E) : (land i σ s).mark = s.mark :=
  sorry

omit [DecidableEq S] [DecidableEq E] in
/-- **ING-19** A landed item is complete: its key is written, whatever its vector. -/
theorem complete_land (i : I) (σ : S) (s : State I S V E) : complete (land i σ s) i :=
  sorry

/-- **ING-19** The drain changes neither the keys nor the structures: a structural query, any
function of the keyed items and their structures, answers the same before and after it. -/
theorem structural_invariant_drain {α : Type*} (Q : Finset I → (I → Option S) → α)
    (f : E → S → V) (e : E) (s : State I S V E) :
    Q (drain f e s).keyed (drain f e s).struct = Q s.keyed s.struct :=
  sorry

/-- **ING-19** The drain under one identity leaves another identity's atoms as they were:
re-embedding after a model change is the same drain under the new identity, and the old field is
neither read nor moved by it. -/
theorem drain_other_atom (f : E → S → V) {e e' : E} (h : e' ≠ e) (s : State I S V E) :
    (drain f e s).atom e' = s.atom e' :=
  sorry

/-- **ING-19** The drain under one identity leaves another identity's marks as they were. -/
theorem drain_other_mark (f : E → S → V) {e e' : E} (h : e' ≠ e) (s : State I S V E) (j : I) :
    (drain f e s).mark j e' = s.mark j e' :=
  sorry

/-- **ING-20** An item's derivation is idempotent: run twice, it leaves the state it left once. -/
theorem derive_idem (f : E → S → V) (e : E) (i : I) (s : State I S V E) :
    run f (derive e i) (run f (derive e i) s) = run f (derive e i) s :=
  sorry

/-- **ING-20** Two items' derivations commute. -/
theorem derive_comm (f : E → S → V) (e : E) (i j : I) (s : State I S V E) :
    run f (derive e i ++ derive e j) s = run f (derive e j ++ derive e i) s :=
  sorry

/-- **ING-20** An item's derivation commutes with a later landing of another item: the drain and
the writer interleave freely on distinct items. -/
theorem derive_land_comm (f : E → S → V) (e : E) {i j : I} (hij : i ≠ j) (σ : S)
    (s : State I S V E) :
    run f (derive e i ++ [.land j σ]) s = run f ([.land j σ] ++ derive e i) s :=
  sorry

/-- **ING-20** The drain is idempotent. -/
theorem drain_idem (f : E → S → V) (e : E) (s : State I S V E) :
    drain f e (drain f e s) = drain f e s :=
  sorry

/-- **ING-20** After the drain, nothing keyed is pending. -/
theorem not_pending_drain (f : E → S → V) (e : E) (s : State I S V E) (i : I) :
    ¬ pending (drain f e s) e i :=
  sorry

/-- **ING-20** After the drain, every keyed item's field is its structure's image under the
embedder, and an unkeyed item's is `none`. -/
theorem field_drain (f : E → S → V) (e : E) (s : State I S V E) (i : I) :
    field (drain f e s) e i = if i ∈ s.keyed then (s.struct i).map (f e) else none :=
  sorry

/-- **ING-20** From any interleaving of landings and embed steps, stopped anywhere, the drain's
field is the field the landings alone, followed by the drain, would give: landing and embedding
converge to one store in any order. -/
theorem field_drain_run (f : E → S → V) (e : E) (w : List (Step I S E)) (s : State I S V E) :
    field (drain f e (run f w s)) e = field (drain f e (run f (w.filter Step.isLand) s)) e :=
  sorry

/-- **ING-20** Every run keeps the atom table truthful: an atom is written as the embedder's
vector of its structure, and nothing else writes one. -/
theorem truthful_run (f : E → S → V) (w : List (Step I S E)) {s : State I S V E}
    (ht : Truthful f s) : Truthful f (run f w s) :=
  sorry

/-- **ING-20** Every prefix of the key-last derivation keeps soundness: the atom is written before
the mark, so a derived item always has the atom its mark promises. -/
theorem sound_derive_prefix (f : E → S → V) (e : E) (i : I) {s : State I S V E}
    (hs : Sound s e) (k : ℕ) : Sound (run f ((derive e i).take k) s) e :=
  sorry

/-- **ING-20** The code's drain, over the pending items alone, reaches the drain's field from any
sound and truthful state: a derived item is not embedded again, and its atom is the one the drain
would have written. -/
theorem codeDrain_field (f : E → S → V) (e : E) {s : State I S V E} (hs : Sound s e)
    (ht : Truthful f s) : field (codeDrain f e s) e = field (drain f e s) e :=
  sorry

/-- **ING-20** The control: with the mark written first and the run interrupted after it, the
state is unsound, since the mark promises an atom the table lacks. -/
theorem mark_first_unsound (f : E → S → V) (e : E) (i : I) {s : State I S V E} {σ : S}
    (hi : i ∈ s.keyed) (hσ : s.struct i = some σ) (h0 : s.atom e σ = none) :
    ¬ Sound (run f ((deriveKeyFirst e i).take 1) s) e :=
  sorry

/-- **ING-20** The control: with the mark written first and the run interrupted after it, the
code's drain never repairs the item, since it finds it derived and embeds nothing for it, when no
other pending item shares its structure; its field stays `none` where the drain's is the vector. -/
theorem mark_first_does_not_converge (f : E → S → V) (e : E) (i : I) {s : State I S V E} {σ : S}
    (hi : i ∈ s.keyed) (hσ : s.struct i = some σ) (h0 : s.atom e σ = none)
    (halone : ∀ j ∈ s.keyed, s.struct j = some σ → j = i) :
    field (codeDrain f e (run f ((deriveKeyFirst e i).take 1) s)) e i ≠
      field (drain f e s) e i :=
  sorry

/-- **ING-21** A structural query, any function of the keyed items and their structures, is
invariant under every run of embed steps: the graph, the lexical index and the keys are what the
landing wrote, and embedding touches none of them. -/
theorem structural_invariant {α : Type*} (Q : Finset I → (I → Option S) → α) (f : E → S → V)
    (w : List (Step I S E)) (hw : ∀ a ∈ w, a.isLand = false) (s : State I S V E) :
    Q (run f w s).keyed (run f w s).struct = Q s.keyed s.struct :=
  sorry

omit [DecidableEq E] in
/-- **ING-21** A pending item's field is `none`: a semantic answer reports it, never a vector. -/
theorem pending_field_none {s : State I S V E} {e : E} {i : I} (h : pending s e i) :
    field s e i = none :=
  sorry

omit [DecidableEq E] in
/-- **ING-21** A field that reports a vector reports the item's own structure's image under the
embedder: a query never invents a vector. -/
theorem field_some_truthful (f : E → S → V) {s : State I S V E} (ht : Truthful f s) {e : E}
    {i : I} {v : V} (h : field s e i = some v) : ∃ σ, s.struct i = some σ ∧ v = f e σ :=
  sorry

/-- **ING-21** The control: a reading that takes a pending vector as zero gives an answer the
item's embedding changes, so it was an answer about the embedding's progress, not about the
item. -/
theorem zeroRead_changes (f : E → S → V) (score : V → ℤ) (e : E) (i : I) {s : State I S V E}
    {σ : S} (hi : i ∈ s.keyed) (hσ : s.struct i = some σ) (h0 : s.atom e σ = none)
    (hne : score (f e σ) ≠ 0) :
    zeroRead score (run f (derive e i) s) e i ≠ zeroRead score s e i :=
  sorry

end Palace.Derived
