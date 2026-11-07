module

public import Palace.Script.Defs

/-!
# The ingress language, the statements

The laws of `Palace/Script.lean` the ledger cites (docs/LAWS.md §XII, ING-13 to ING-18), each
with its proof left as `sorry`, over the model of `Palace/Script/Defs.lean`. `lake comparator`
checks that the `Palace` library proves each one exactly as stated here, from the standard axioms
alone. What the statements cover: labels are the palace's, a value's label and origin its item's
under projections and observed otherwise, as `core/sentence/interpret.py` carries them (ING-13);
the writer's rules as `core/ingest/writer.py` applies them, the firewall (ING-14), confinement to
the role's namespace, the part it writes and the part it only retires (ING-15), fixed labels,
identities that move only with their bytes, paths that belong to their sources and retire as
reconciliation (ING-17); a plan's stores as the first
form's commands with the key last, so they converge and leave a state readers may read without a
lock (ING-16); and the type system's soundness for labels, as `core/sentence/script_check.py`
infers them (ING-18).
-/

@[expose] public section

namespace Palace.Script

variable {B L P I W K Rl : Type*}

/-- **ING-13** A value's label is its item's under projections, and the observed label otherwise. -/
theorem label_eval (view : W → B → B) (observed : L) (e : Expr B L P W) :
    (eval view observed e).label = (e.root.map Item.label).getD observed :=
  sorry

/-- **ING-13** A value's origin is its item's path under projections, and none otherwise. -/
theorem origin_eval (view : W → B → B) (observed : L) (e : Expr B L P W) :
    (eval view observed e).origin = e.root.map Item.path :=
  sorry

/-- **ING-13** A projection's bytes are its item's under its views. -/
theorem bytes_eval (view : W → B → B) (observed : L) {e : Expr B L P W} {i : Item B L P}
    (h : e.root = some i) : (eval view observed e).bytes = applyViews view e.views i.bytes :=
  sorry

/-- **ING-13** No expression raises a label: a label other than the observed one is an item's,
carried to the value by projections alone. -/
theorem root_of_label_ne (view : W → B → B) (observed : L) (e : Expr B L P W)
    (h : (eval view observed e).label ≠ observed) :
    ∃ i, e.root = some i ∧ i.label = (eval view observed e).label :=
  sorry

/-- **ING-18** The type system is sound for labels: if every item's label is among those its
source's rule may give, a value's label at run time is in its expression's type's set, and in any
set inference unified it into. -/
theorem label_typed [DecidableEq L] (view : W → B → B) (observed : L)
    (srcLabels : Item B L P → Finset L) (hsrc : ∀ i, i.label ∈ srcLabels i) (e : Expr B L P W) :
    (eval view observed e).label ∈ labelsOf srcLabels observed e :=
  sorry

/-- **ING-18** A set inference unified the type's set into contains the value's label. -/
theorem label_typed_of_subset [DecidableEq L] (view : W → B → B) (observed : L)
    (srcLabels : Item B L P → Finset L) (hsrc : ∀ i, i.label ∈ srcLabels i) (e : Expr B L P W)
    {T : Finset L} (hT : labelsOf srcLabels observed e ⊆ T) :
    (eval view observed e).label ∈ T :=
  sorry

variable [DecidableEq B] [DecidableEq L] [DecidableEq P]

/-- **ING-14** The firewall, one store: an admitted store whose label is not the observed one lands
the bytes of an item a source yields, under the expression's views, at the item's own path,
with the item's label. -/
theorem firewall_store (T : Table B L P I W K Rl) (r : Rl) (h : Held P B L I) (p : P)
    (n : Naming P I) (e : Expr B L P W) (k : K) (hok : okStore T r h p n e k = true)
    (hl : (eval T.view T.observed e).label ≠ T.observed) :
    ∃ i, T.yields i = true ∧ i.path = p ∧ i.label = (eval T.view T.observed e).label ∧
      (eval T.view T.observed e).bytes = applyViews T.view e.views i.bytes :=
  sorry

/-- **ING-14** The firewall over a plan: every active row of the landed state whose label is not the
observed one is the row held before at its path, or the bytes of an item a source yields, under
views, at the item's own path, with the item's label. -/
theorem firewall_plan (T : Table B L P I W K Rl) (r : Rl) (plan : List (Effect B L P I W K))
    (h₀ : Held P B L I) (p : P) (row : Row B L I) (hp : landPlan T r plan h₀ p = some row)
    (hl : row.label ≠ T.observed) (ha : row.active = true) :
    h₀ p = some row ∨ ∃ i ws, T.yields i = true ∧ i.path = p ∧ i.label = row.label ∧
      row.bytes = applyViews T.view ws i.bytes :=
  sorry

/-- **ING-15** Confinement: a plan changes a path only through an effect on it that the writer
admitted, in the role's namespace for the effect's place: its write namespace for a store, its
write or retire-only namespace for a retire. -/
theorem confined (T : Table B L P I W K Rl) (r : Rl) (plan : List (Effect B L P I W K))
    (h₀ : Held P B L I) (p : P) (hne : landPlan T r plan h₀ p ≠ h₀ p) :
    ∃ ef ∈ plan, ef.path = p ∧ inNamespace T r ef = true :=
  sorry

/-- **ING-15** A retire-only namespace takes no store: a path a plan leaves holding an active row
it changed was stored there by the plan, in the role's write namespace for the store's place. -/
theorem confined_store (T : Table B L P I W K Rl) (r : Rl) (plan : List (Effect B L P I W K))
    (h₀ : Held P B L I) (p : P) (row : Row B L I) (hp : landPlan T r plan h₀ p = some row)
    (ha : row.active = true) (hne : landPlan T r plan h₀ p ≠ h₀ p) :
    ∃ n e k, Effect.store p n e k ∈ plan ∧ T.ns r k p = true :=
  sorry

/-- **ING-17** A held path keeps its label and its identity under an admitted store. -/
theorem label_fixed (T : Table B L P I W K Rl) (r : Rl) (h : Held P B L I) (p : P)
    (n : Naming P I) (e : Expr B L P W) (k : K) (row : Row B L I) (hp : h p = some row)
    (hok : okStore T r h p n e k = true) :
    ∃ row', landStore T h p n e p = some row' ∧ row'.label = row.label ∧
      row'.ident = row.ident :=
  sorry

/-- **ING-17** Identities move only with their bytes: an admitted store at a new path gives it its
own identity, the one the very item stored declares, or one held at a path its source no longer
has, holding the same bytes. -/
theorem identity_moves_with_bytes (T : Table B L P I W K Rl) (r : Rl) (h : Held P B L I) (p : P)
    (n : Naming P I) (e : Expr B L P W) (k : K) (hp : h p = none)
    (hok : okStore T r h p n e k = true) :
    ∃ row', landStore T h p n e p = some row' ∧
      (row'.ident = T.ofPath p ∨
        (∃ src i, n = .prop src i ∧ (eval T.view T.observed e).origin = some src ∧
          T.declares src i = true ∧ row'.ident = i) ∨
        (∃ q rq, n = .held q ∧ h q = some rq ∧ rq.bytes = (eval T.view T.observed e).bytes ∧
          T.has q = false ∧ row'.ident = rq.ident)) :=
  sorry

/-- **ING-17** Paths belong to their sources: an admitted store at a path in a source's space lands
an item a source yields, at that very path, whatever its label, so no script squats a path a
source will write (a composed text where the owner's turn will land). -/
theorem owned_by_source (T : Table B L P I W K Rl) (r : Rl) (h : Held P B L I) (p : P)
    (n : Naming P I) (e : Expr B L P W) (k : K) (hok : okStore T r h p n e k = true)
    (howned : T.owned p = true) :
    ∃ i, e.root = some i ∧ T.yields i = true ∧ i.path = p :=
  sorry

omit [DecidableEq B] [DecidableEq L] [DecidableEq P] in
/-- **ING-17** Retire reconciles: an admitted retire of content that came from a source is of a
path the source no longer has, so no script retires a note still in the vault. -/
theorem retire_reconciles (T : Table B L P I W K Rl) (r : Rl) (h : Held P B L I) (p : P) (k : K)
    (row : Row B L I) (hp : h p = some row) (hs : row.sourced = true)
    (hok : okRetire T r h p k = true) : T.has p = false :=
  sorry

omit [DecidableEq B] in
open Ingress in
/-- **ING-16** A plan's stores on distinct paths, each fresh, stopped anywhere in any global order:
run again, they land exactly the uninterrupted batch (ING-11 for every plan). -/
theorem plan_converges {R G : Type*} [DecidableEq R] [DecidableEq G]
    (rowsOf : B → List (Finset R)) (dig : B → G) (stores : List (P × B))
    (hn : (stores.map Prod.fst).Nodup) (s : State R P G)
    (hf : ∀ x ∈ stores, Fresh (toSource rowsOf dig x.1 x.2) s) (k : Source R P G → ℕ)
    {w : List (Step R P G)}
    (hw : w.Perm (prefixesOf k (stores.map fun x ↦ toSource rowsOf dig x.1 x.2))) :
    batch (stores.map fun x ↦ toSource rowsOf dig x.1 x.2) (run w s)
      = batch (stores.map fun x ↦ toSource rowsOf dig x.1 x.2) s :=
  sorry

omit [DecidableEq B] in
open Ingress in
/-- **ING-16** Readers need no lock under a plan: its stores on distinct paths stopped anywhere, in
any global order, from a state sound for each, leave a state sound for each (ING-12 for every
plan). -/
theorem plan_sound {R G : Type*} [DecidableEq R] [DecidableEq G]
    (rowsOf : B → List (Finset R)) (dig : B → G) (stores : List (P × B))
    (hn : (stores.map Prod.fst).Nodup) (s : State R P G)
    (hs : ∀ x ∈ stores, Sound (toSource rowsOf dig x.1 x.2) s) (k : Source R P G → ℕ)
    {w : List (Step R P G)}
    (hw : w.Perm (prefixesOf k (stores.map fun x ↦ toSource rowsOf dig x.1 x.2))) :
    ∀ x ∈ stores, Sound (toSource rowsOf dig x.1 x.2) (run w s) :=
  sorry

end Palace.Script
