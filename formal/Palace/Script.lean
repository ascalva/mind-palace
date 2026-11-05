module

public import Palace.Door
public import Palace.Script.Defs

/-!
# The door's language: the laws

dn-door-language §E9, on the model of `Palace/Script/Defs.lean`. DOR-13: a value's label and
origin are its item's under projections and the observed label and none otherwise, and its bytes
are its item's under its views, so no expression raises a label. DOR-14, the firewall: an
admitted store whose label is not the observed one lands an item a source yields, under views, at
the item's own path, with the item's label; over a plan, every active row not observed is the row
held before or such a store's. DOR-15, confinement: a plan changes a path only by an admitted
effect on it, in the role's namespace for the effect's place. DOR-16: a plan's stores are the
first form's commands with the key last, so stores on distinct paths stopped anywhere converge
under re-run (DOR-11) and leave a state a reader that trusts the key may read without a lock
(DOR-12). DOR-17: a held path keeps its label and its identity under an admitted store; a new
path's identity is its own, one read off the very item stored, or one held at a path its source
no longer has with the same bytes; and an admitted retire of content that came from a source is
of a path the source no longer has. Design theorems: the ledger takes them up when code relies on
them.
-/

@[expose] public section

namespace Palace.Script

variable {B L P I W K Rl : Type*}

/-! ### DOR-13 Labels are the palace's -/

/-- DOR-13 A value's label is its item's under projections, and the observed label otherwise. -/
theorem label_eval (view : W → B → B) (observed : L) (e : Expr B L P W) :
    (eval view observed e).label = (e.root.map Item.label).getD observed := by
  induction e with
  | item i => rfl
  | proj w e ih => simpa only [eval, Expr.root] using ih
  | make b => rfl

/-- DOR-13 A value's origin is its item's path under projections, and none otherwise. -/
theorem origin_eval (view : W → B → B) (observed : L) (e : Expr B L P W) :
    (eval view observed e).origin = e.root.map Item.path := by
  induction e with
  | item i => rfl
  | proj w e ih => simpa only [eval, Expr.root] using ih
  | make b => rfl

/-- DOR-13 A projection's bytes are its item's under its views. -/
theorem bytes_eval (view : W → B → B) (observed : L) {e : Expr B L P W} {i : Item B L P}
    (h : e.root = some i) : (eval view observed e).bytes = applyViews view e.views i.bytes := by
  induction e with
  | item j =>
    simp only [Expr.root, Option.some.injEq] at h
    subst h
    rfl
  | proj w e ih =>
    simp only [Expr.root] at h
    simp only [eval, Expr.views, applyViews, ih h]
  | make b => simp [Expr.root] at h

/-- DOR-13 No expression raises a label: a label other than the observed one is an item's,
carried to the value by projections alone. -/
theorem root_of_label_ne (view : W → B → B) (observed : L) (e : Expr B L P W)
    (h : (eval view observed e).label ≠ observed) :
    ∃ i, e.root = some i ∧ i.label = (eval view observed e).label := by
  have hl := label_eval view observed e
  cases hr : e.root with
  | none =>
    rw [hr] at hl
    exact absurd hl h
  | some i =>
    rw [hr] at hl
    exact ⟨i, rfl, hl.symm⟩

/-! ### DOR-14 The firewall -/

variable [DecidableEq B] [DecidableEq L] [DecidableEq P]

/-- The writer's admission of a store, as propositions: its items are the sources', its place
accepts its label, its path is in the role's namespace, content with an origin lands at it, a
path in a source's space takes only content with an origin, a held path keeps its label, a new
path's identity is admitted. -/
theorem okStore_spec {T : Table B L P I W K Rl} {r : Rl} {h : Held P B L I} {p : P}
    {n : Naming P I} {e : Expr B L P W} {k : K} (hok : okStore T r h p n e k = true) :
    (∀ i, e.root = some i → T.yields i = true) ∧
      T.accepts k (eval T.view T.observed e).label = true ∧ T.ns r k p = true ∧
      (∀ a, (eval T.view T.observed e).origin = some a → a = p) ∧
      (T.owned p = true → (eval T.view T.observed e).origin.isSome = true) ∧
      (∀ row, h p = some row → row.label = (eval T.view T.observed e).label) ∧
      (h p = none → (resolve T h (eval T.view T.observed e) p n).isSome = true) := by
  simp only [okStore, Bool.and_eq_true] at hok
  obtain ⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h8⟩, h5⟩ := hok
  refine ⟨fun i hi ↦ ?_, h2, h3, fun a ha ↦ ?_, fun ho ↦ ?_, fun row hr ↦ ?_, fun hn ↦ ?_⟩
  · rw [hi] at h1
    exact h1
  · rw [ha] at h4
    simpa using h4
  · simpa [ho] using h8
  · rw [hr] at h5
    simpa using h5
  · rw [hn] at h5
    exact h5

/-- DOR-14 The firewall, one store: an admitted store whose label is not the observed one lands
the bytes of an item a source yields, under the expression's views, at the item's own path,
with the item's label. -/
theorem firewall_store (T : Table B L P I W K Rl) (r : Rl) (h : Held P B L I) (p : P)
    (n : Naming P I) (e : Expr B L P W) (k : K) (hok : okStore T r h p n e k = true)
    (hl : (eval T.view T.observed e).label ≠ T.observed) :
    ∃ i, T.yields i = true ∧ i.path = p ∧ i.label = (eval T.view T.observed e).label ∧
      (eval T.view T.observed e).bytes = applyViews T.view e.views i.bytes := by
  obtain ⟨hy, -, -, ho, -, -, -⟩ := okStore_spec hok
  obtain ⟨i, hi, hlab⟩ := root_of_label_ne T.view T.observed e hl
  refine ⟨i, hy i hi, ho _ ?_, hlab, bytes_eval T.view T.observed hi⟩
  rw [origin_eval, hi]
  rfl

/-- DOR-14 The firewall over a plan: every active row of the landed state whose label is not the
observed one is the row held before at its path, or the bytes of an item a source yields, under
views, at the item's own path, with the item's label. -/
theorem firewall_plan (T : Table B L P I W K Rl) (r : Rl) (plan : List (Effect B L P I W K))
    (h₀ : Held P B L I) (p : P) (row : Row B L I) (hp : landPlan T r plan h₀ p = some row)
    (hl : row.label ≠ T.observed) (ha : row.active = true) :
    h₀ p = some row ∨ ∃ i ws, T.yields i = true ∧ i.path = p ∧ i.label = row.label ∧
      row.bytes = applyViews T.view ws i.bytes := by
  induction plan generalizing h₀ with
  | nil => exact Or.inl hp
  | cons ef plan ih =>
    have hp' : landPlan T r plan (step T r h₀ ef) p = some row := hp
    rcases ih (step T r h₀ ef) hp' with h1 | h1
    · cases ef with
      | store q n e k =>
        simp only [step] at h1
        split_ifs at h1 with hok
        · by_cases hqp : p = q
          · subst hqp
            simp only [landStore, Function.update_self, Option.some.injEq] at h1
            subst h1
            right
            obtain ⟨i, hy, hpath, hlab, hb⟩ := firewall_store T r h₀ p n e k hok hl
            exact ⟨i, e.views, hy, hpath, hlab, hb⟩
          · left
            simpa [landStore, Function.update_of_ne hqp] using h1
        · exact Or.inl h1
      | retire q k =>
        simp only [step] at h1
        split_ifs at h1 with hok
        · by_cases hqp : p = q
          · subst hqp
            simp only [landRetire, Function.update_self] at h1
            cases h0 : h₀ p with
            | none => simp [h0] at h1
            | some r0 =>
              simp only [h0, Option.map_some, Option.some.injEq] at h1
              subst h1
              simp at ha
          · left
            simpa [landRetire, Function.update_of_ne hqp] using h1
        · exact Or.inl h1
    · exact Or.inr h1

/-! ### DOR-15 Confinement -/

/-- DOR-15 Confinement: a plan changes a path only through an effect on it that the writer
admitted, in the role's namespace for the effect's place. -/
theorem confined (T : Table B L P I W K Rl) (r : Rl) (plan : List (Effect B L P I W K))
    (h₀ : Held P B L I) (p : P) (hne : landPlan T r plan h₀ p ≠ h₀ p) :
    ∃ ef ∈ plan, ef.path = p ∧ T.ns r ef.place p = true := by
  induction plan generalizing h₀ with
  | nil => exact absurd rfl hne
  | cons ef plan ih =>
    have hne' : landPlan T r plan (step T r h₀ ef) p ≠ h₀ p := hne
    by_cases hrest : landPlan T r plan (step T r h₀ ef) p = step T r h₀ ef p
    · have h1 : step T r h₀ ef p ≠ h₀ p := fun heq ↦ hne' (hrest.trans heq)
      refine ⟨ef, List.mem_cons_self, ?_⟩
      cases ef with
      | store q n e k =>
        simp only [step] at h1
        split_ifs at h1 with hok
        · by_cases hqp : p = q
          · subst hqp
            exact ⟨rfl, (okStore_spec hok).2.2.1⟩
          · exact absurd (by simp [landStore, Function.update_of_ne hqp]) h1
        · exact absurd rfl h1
      | retire q k =>
        simp only [step] at h1
        split_ifs at h1 with hok
        · by_cases hqp : p = q
          · subst hqp
            refine ⟨rfl, ?_⟩
            simp only [okRetire] at hok
            split at hok
            · simp only [Bool.and_eq_true] at hok
              exact hok.1
            · simp at hok
          · exact absurd (by simp [landRetire, Function.update_of_ne hqp]) h1
        · exact absurd rfl h1
    · obtain ⟨ef', hmem, hpath, hns⟩ := ih (step T r h₀ ef) hrest
      exact ⟨ef', List.mem_cons_of_mem ef hmem, hpath, hns⟩

/-! ### DOR-17 Labels fixed, identities with their bytes, retire reconciles -/

/-- DOR-17 A held path keeps its label and its identity under an admitted store. -/
theorem label_fixed (T : Table B L P I W K Rl) (r : Rl) (h : Held P B L I) (p : P)
    (n : Naming P I) (e : Expr B L P W) (k : K) (row : Row B L I) (hp : h p = some row)
    (hok : okStore T r h p n e k = true) :
    ∃ row', landStore T h p n e p = some row' ∧ row'.label = row.label ∧
      row'.ident = row.ident := by
  refine ⟨⟨(eval T.view T.observed e).bytes, (eval T.view T.observed e).label, row.ident,
    (eval T.view T.observed e).origin.isSome, true⟩, ?_, ?_, rfl⟩
  · simp [landStore, hp]
  · exact ((okStore_spec hok).2.2.2.2.2.1 row hp).symm

/-- DOR-17 Identities move only with their bytes: an admitted store at a new path gives it its
own identity, one read off the very item stored, or one held at a path its source no longer has,
holding the same bytes. -/
theorem identity_moves_with_bytes (T : Table B L P I W K Rl) (r : Rl) (h : Held P B L I) (p : P)
    (n : Naming P I) (e : Expr B L P W) (k : K) (hp : h p = none)
    (hok : okStore T r h p n e k = true) :
    ∃ row', landStore T h p n e p = some row' ∧
      (row'.ident = T.ofPath p ∨
        (∃ src i, n = .prop src i ∧ (eval T.view T.observed e).origin = some src ∧
          row'.ident = i) ∨
        (∃ q rq, n = .held q ∧ h q = some rq ∧ rq.bytes = (eval T.view T.observed e).bytes ∧
          T.has q = false ∧ row'.ident = rq.ident)) := by
  have hres := (okStore_spec hok).2.2.2.2.2.2 hp
  refine ⟨⟨(eval T.view T.observed e).bytes, (eval T.view T.observed e).label,
    (resolve T h (eval T.view T.observed e) p n).getD (T.ofPath p),
    (eval T.view T.observed e).origin.isSome, true⟩, by simp [landStore, hp], ?_⟩
  cases n with
  | own => exact Or.inl rfl
  | prop src i =>
    refine Or.inr (Or.inl ?_)
    simp only [resolve] at hres ⊢
    split_ifs at hres ⊢ with hs
    · exact ⟨src, i, rfl, hs, rfl⟩
    · simp at hres
  | held q =>
    refine Or.inr (Or.inr ?_)
    simp only [resolve] at hres ⊢
    cases hq : h q with
    | none => simp [hq] at hres
    | some rq =>
      simp only [hq] at hres ⊢
      split_ifs at hres ⊢ with hb
      · exact ⟨q, rq, rfl, hq, hb.1, hb.2, rfl⟩
      · simp at hres

/-- DOR-17 Paths belong to their sources: an admitted store at a path in a source's space lands
an item a source yields, at that very path, whatever its label, so no script squats a path a
source will write (a composed text where the owner's turn will land). -/
theorem owned_by_source (T : Table B L P I W K Rl) (r : Rl) (h : Held P B L I) (p : P)
    (n : Naming P I) (e : Expr B L P W) (k : K) (hok : okStore T r h p n e k = true)
    (howned : T.owned p = true) :
    ∃ i, e.root = some i ∧ T.yields i = true ∧ i.path = p := by
  obtain ⟨hy, -, -, ho, hown, -, -⟩ := okStore_spec hok
  have hs := hown howned
  rw [origin_eval] at hs ho
  cases hr : e.root with
  | none => simp [hr] at hs
  | some i =>
    refine ⟨i, rfl, hy i hr, ho _ ?_⟩
    rw [hr]
    rfl

omit [DecidableEq B] [DecidableEq L] [DecidableEq P] in
/-- DOR-17 Retire reconciles: an admitted retire of content that came from a source is of a
path the source no longer has, so no script retires a note still in the vault. -/
theorem retire_reconciles (T : Table B L P I W K Rl) (r : Rl) (h : Held P B L I) (p : P) (k : K)
    (row : Row B L I) (hp : h p = some row) (hs : row.sourced = true)
    (hok : okRetire T r h p k = true) : T.has p = false := by
  have h2 : T.ns r k p = true ∧ T.has p = false := by simpa [okRetire, hp, hs] using hok
  exact h2.2

/-! ### DOR-16 A plan's stores converge, and readers need no lock -/

omit [DecidableEq B] in
open Door in
/-- DOR-16 A plan's stores on distinct paths, each fresh, stopped anywhere in any global order:
run again, they land exactly the uninterrupted batch (DOR-11 for every plan). -/
theorem plan_converges {R G : Type*} [DecidableEq R] [DecidableEq G]
    (rowsOf : B → List (Finset R)) (dig : B → G) (stores : List (P × B))
    (hn : (stores.map Prod.fst).Nodup) (s : State R P G)
    (hf : ∀ x ∈ stores, Fresh (toSource rowsOf dig x.1 x.2) s) (k : Source R P G → ℕ)
    {w : List (Step R P G)}
    (hw : w.Perm (prefixesOf k (stores.map fun x ↦ toSource rowsOf dig x.1 x.2))) :
    batch (stores.map fun x ↦ toSource rowsOf dig x.1 x.2) (run w s)
      = batch (stores.map fun x ↦ toSource rowsOf dig x.1 x.2) s := by
  refine batch_after_prefixes k hw ?_ s fun x hx ↦ ?_
  · simpa [List.map_map, Function.comp_def, toSource] using hn
  · obtain ⟨y, hy, rfl⟩ := List.mem_map.1 hx
    exact hf y hy

omit [DecidableEq B] in
open Door in
/-- DOR-16 Readers need no lock under a plan: its stores on distinct paths stopped anywhere, in
any global order, from a state sound for each, leave a state sound for each (DOR-12 for every
plan). -/
theorem plan_sound {R G : Type*} [DecidableEq R] [DecidableEq G]
    (rowsOf : B → List (Finset R)) (dig : B → G) (stores : List (P × B))
    (hn : (stores.map Prod.fst).Nodup) (s : State R P G)
    (hs : ∀ x ∈ stores, Sound (toSource rowsOf dig x.1 x.2) s) (k : Source R P G → ℕ)
    {w : List (Step R P G)}
    (hw : w.Perm (prefixesOf k (stores.map fun x ↦ toSource rowsOf dig x.1 x.2))) :
    ∀ x ∈ stores, Sound (toSource rowsOf dig x.1 x.2) (run w s) := by
  have hn' : ((stores.map fun x ↦ toSource rowsOf dig x.1 x.2).map Source.ident).Nodup := by
    simpa [List.map_map, Function.comp_def, toSource] using hn
  have h := sound_after_prefixes k hw hn' s fun x hx ↦ by
      obtain ⟨y, hy, rfl⟩ := List.mem_map.1 hx
      exact hs y hy
  exact fun x hx ↦ h _ (List.mem_map.2 ⟨x, hx, rfl⟩)

end Palace.Script
