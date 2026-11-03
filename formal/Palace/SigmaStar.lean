module

public import Palace.SigmaStar.Defs

/-!
# σ*, the abstraction ultrametric: SIG-1 to SIG-4

`σ*(A, B) = sup{σ : A ∼ B in G_σ}`, the strictest threshold at which two thoughts still share a
component (`core/graph/sigma_star.py`, connectivity-instruments CN-2), and the claim that one
maximum spanning forest, built once, yields it for every pair.

The model takes the graph as a list of weighted edges `(u, v, w)` over any linear order of
weights. Nothing here does arithmetic on weights, only comparisons, so the statements hold of the
code's float64 cosines as they are (NaN aside). Kruskal's loop is modeled with component labels
in place of union-find's parent array (quick-find): all the loop asks is whether two endpoints
share a component, and the labels answer exactly that (`connected_iff`). The path the code walks
is not modeled: in a forest, the least edge on the unique path between two vertices is the largest
of the forest's weights at which they stay connected, which is how `bottleneck` is defined here.
`_grid_snap`'s `1e-12` tolerance is left out, the model's weights being exact, and so is its
answer below the grid, `grid[0]`, which the code never reaches: it builds the forest at `grid[0]`.
A vertex's path to itself has no edge; its least edge is `+∞` (`min(..., default=inf)`), which
snaps to the strictest grid point, as the union-find oracle has it: every σ links a vertex to
itself.
-/

@[expose] public section

open Relation

namespace Palace.SigmaStar

variable {V W : Type*}

/-! ## Thresholds -/

section Threshold

variable [LinearOrder W]

theorem conn_equivalence (L : List (Edge V W)) (σ : W) : Equivalence (Conn L σ) :=
  EqvGen.is_equivalence _

/-- A lower threshold keeps every edge a higher one keeps. -/
theorem Conn.anti {L : List (Edge V W)} {σ τ : W} (h : σ ≤ τ) {a b : V} (hab : Conn L τ a b) :
    Conn L σ a b :=
  EqvGen.mono (fun _ _ ⟨w, hw, hτ⟩ ↦ ⟨w, hw, h.trans hτ⟩) a b hab

theorem Conn.sub {L L' : List (Edge V W)} (h : ∀ e ∈ L, e ∈ L') {σ : W} {a b : V}
    (hab : Conn L σ a b) : Conn L' σ a b :=
  EqvGen.mono (fun _ _ ⟨w, hw, hσ⟩ ↦ ⟨w, h _ hw, hσ⟩) a b hab

/-- **SIG-3** The ultrametric inequality at the level of thresholds: two links that hold at `x`
and at `y` compose at `min x y`. -/
theorem Conn.ultra {L : List (Edge V W)} {x y : W} {a b c : V} (hab : Conn L x a b)
    (hbc : Conn L y b c) : Conn L (min x y) a c :=
  (conn_equivalence L _).trans (hab.anti (min_le_left x y)) (hbc.anti (min_le_right x y))

/-- Two distinct vertices linked at `σ` have an edge at `σ` between them somewhere. -/
theorem Conn.exists_adj {L : List (Edge V W)} {σ : W} {a b : V} (h : Conn L σ a b) :
    a ≠ b → ∃ x y w, (x, y, w) ∈ L ∧ σ ≤ w := by
  induction h with
  | rel x y hr => obtain ⟨w, hw, hσ⟩ := hr; exact fun _ ↦ ⟨x, y, w, hw, hσ⟩
  | refl => exact fun h ↦ absurd rfl h
  | symm x y _ ih => exact fun h ↦ ih (Ne.symm h)
  | trans x y z _ _ ih₁ ih₂ =>
    intro h
    by_cases hxy : x = y
    · subst hxy; exact ih₂ h
    · exact ih₁ hxy

/-- The maximum of a filtered list is at least each member that passes the filter. -/
theorem exists_max?_filter {xs : List W} {p : W → Bool} {g : W} (hg : g ∈ xs) (hp : p g = true) :
    ∃ x, (xs.filter p).max? = some x ∧ g ≤ x := by
  have hmem : g ∈ xs.filter p := List.mem_filter.2 ⟨hg, hp⟩
  cases h : (xs.filter p).max? with
  | none => rw [List.max?_eq_none_iff] at h; simp [h] at hmem
  | some x => exact ⟨x, rfl, (List.max?_eq_some_iff.1 h).2 g hmem⟩

end Threshold

/-! ## Quick-find -/

section Labels

theorem linked_equivalence (F : List (Edge V W)) : Equivalence (Linked F) :=
  EqvGen.is_equivalence _

theorem Linked.sub {F F' : List (Edge V W)} (h : ∀ e ∈ F, e ∈ F') {a b : V} (hab : Linked F a b) :
    Linked F' a b :=
  EqvGen.mono (fun _ _ ⟨w, hw⟩ ↦ ⟨w, h _ hw⟩) a b hab

/-- Quick-find's invariant: each label is a vertex of its own class, and linked vertices share a
label. -/
structure LabelInv (F : List (Edge V W)) (lab : V → V) : Prop where
  self : ∀ x, Linked F x (lab x)
  eq : ∀ x y, Linked F x y → lab x = lab y

theorem labelInv_nil : LabelInv ([] : List (Edge V W)) id where
  self x := EqvGen.refl x
  eq x y h := by
    induction h with
    | rel x y h => obtain ⟨w, hw⟩ := h; simp at hw
    | refl => rfl
    | symm x y _ ih => exact ih.symm
    | trans x y z _ _ ih₁ ih₂ => exact ih₁.trans ih₂

theorem LabelInv.label_eq_iff {F : List (Edge V W)} {lab : V → V} (h : LabelInv F lab) (x y : V) :
    lab x = lab y ↔ Linked F x y := by
  refine ⟨fun hxy ↦ ?_, h.eq x y⟩
  have hy := h.self y
  rw [← hxy] at hy
  exact (linked_equivalence F).trans (h.self x) ((linked_equivalence F).symm hy)

variable [DecidableEq V]

theorem step_of_eq {F : List (Edge V W)} {lab : V → V} {u v : V} (w : W) (h : lab u = lab v) :
    step (F, lab) (u, v, w) = (F, lab) := by
  simp [step, h]

theorem step_of_ne {F : List (Edge V W)} {lab : V → V} {u v : V} (w : W) (h : lab u ≠ lab v) :
    step (F, lab) (u, v, w) = ((u, v, w) :: F, merge lab u v) := by
  simp [step, h]

theorem LabelInv.merge {F : List (Edge V W)} {lab : V → V} (h : LabelInv F lab) {u v : V}
    (w : W) (huv : lab u ≠ lab v) : LabelInv ((u, v, w) :: F) (merge lab u v) := by
  have hsub : ∀ a b, Linked F a b → Linked ((u, v, w) :: F) a b :=
    fun a b ↦ Linked.sub fun e he ↦ List.mem_cons_of_mem _ he
  have huv' : Linked ((u, v, w) :: F) u v := EqvGen.rel _ _ ⟨w, List.mem_cons_self⟩
  have eqv := linked_equivalence ((u, v, w) :: F)
  constructor
  · intro x
    simp only [SigmaStar.merge]
    split_ifs with hx
    · -- `x ∼ lab x = lab v ∼ v ∼ u ∼ lab u`
      have hxv : Linked F x v := (h.label_eq_iff x v).1 hx
      exact eqv.trans (hsub _ _ hxv) (eqv.trans (eqv.symm huv') (hsub _ _ (h.self u)))
    · exact hsub _ _ (h.self x)
  · intro x y hxy
    induction hxy with
    | rel x y hr =>
      obtain ⟨w', hw'⟩ := hr
      rcases List.mem_cons.1 hw' with he | he
      · simp only [Prod.mk.injEq] at he
        obtain ⟨rfl, rfl, rfl⟩ := he
        simp [SigmaStar.merge, huv]
      · simp only [SigmaStar.merge, h.eq x y (EqvGen.rel _ _ ⟨w', he⟩)]
    | refl => rfl
    | symm x y _ ih => exact ih.symm
    | trans x y z _ _ ih₁ ih₂ => exact ih₁.trans ih₂

/-- What the loop leaves, from any state satisfying the invariant: the invariant still, every
edge it held, only edges it held or was given, and every given edge's endpoints linked. -/
theorem foldl_step (L : List (Edge V W)) :
    ∀ (F : List (Edge V W)) (lab : V → V), LabelInv F lab →
      LabelInv (L.foldl step (F, lab)).1 (L.foldl step (F, lab)).2 ∧
      (∀ e ∈ F, e ∈ (L.foldl step (F, lab)).1) ∧
      (∀ e ∈ (L.foldl step (F, lab)).1, e ∈ F ∨ e ∈ L) ∧
      (∀ e ∈ L, Linked (L.foldl step (F, lab)).1 e.1 e.2.1) := by
  induction L with
  | nil => intro F lab h; simp [h]
  | cons e L ih =>
    intro F lab h
    obtain ⟨u, v, w⟩ := e
    rw [List.foldl_cons]
    by_cases huv : lab u = lab v
    · rw [step_of_eq w huv]
      obtain ⟨hinv, hkeep, honly, hcover⟩ := ih F lab h
      refine ⟨hinv, hkeep, fun f hf ↦ (honly f hf).imp_right (List.mem_cons_of_mem _), ?_⟩
      intro f hf
      rcases List.mem_cons.1 hf with rfl | hf'
      · exact Linked.sub hkeep ((h.label_eq_iff u v).1 huv)
      · exact hcover f hf'
    · rw [step_of_ne w huv]
      obtain ⟨hinv, hkeep, honly, hcover⟩ := ih _ _ (h.merge w huv)
      refine ⟨hinv, fun f hf ↦ hkeep f (List.mem_cons_of_mem _ hf), fun f hf ↦ ?_, ?_⟩
      · rcases honly f hf with hf' | hf'
        · rcases List.mem_cons.1 hf' with rfl | hf''
          · exact .inr List.mem_cons_self
          · exact .inl hf''
        · exact .inr (List.mem_cons_of_mem _ hf')
      · intro f hf
        rcases List.mem_cons.1 hf with rfl | hf'
        · exact EqvGen.rel _ _ ⟨w, hkeep _ List.mem_cons_self⟩
        · exact hcover f hf'

/-- The labels leave as many classes as vertices, less one per kept edge. -/
theorem foldl_step_card [Fintype V] (L : List (Edge V W)) :
    ∀ (F : List (Edge V W)) (lab : V → V),
      (L.foldl step (F, lab)).1.length + (Finset.univ.image (L.foldl step (F, lab)).2).card =
        F.length + (Finset.univ.image lab).card := by
  induction L with
  | nil => intro F lab; rfl
  | cons e L ih =>
    intro F lab
    obtain ⟨u, v, w⟩ := e
    rw [List.foldl_cons, ih]
    by_cases huv : lab u = lab v
    · rw [step_of_eq w huv]
    · rw [step_of_ne w huv]
      have himage : Finset.univ.image (SigmaStar.merge lab u v) =
          (Finset.univ.image lab).erase (lab v) := by
        ext y
        simp only [Finset.mem_image, Finset.mem_univ, true_and, Finset.mem_erase,
          SigmaStar.merge]
        constructor
        · rintro ⟨x, rfl⟩
          split_ifs with hx
          · exact ⟨huv, u, rfl⟩
          · exact ⟨hx, x, rfl⟩
        · rintro ⟨hy, x, rfl⟩
          exact ⟨x, by simp [hy]⟩
      have hv : lab v ∈ Finset.univ.image lab := Finset.mem_image_of_mem lab (Finset.mem_univ v)
      have hpos : 0 < (Finset.univ.image lab).card := Finset.card_pos.2 ⟨_, hv⟩
      rw [List.length_cons, himage, Finset.card_erase_of_mem hv]
      omega

end Labels

/-! ## Computed connectivity -/

section Connected

variable [DecidableEq V] [LinearOrder W]

/-- **SIG-4** The labels decide `G_σ`'s components: σ* is computed through them. -/
theorem connected_iff (L : List (Edge V W)) (σ : W) (a b : V) :
    connected L σ a b = true ↔ Conn L σ a b := by
  obtain ⟨hinv, -, honly, hcover⟩ :=
    foldl_step (L.filter fun e ↦ σ ≤ e.2.2) [] id labelInv_nil
  rw [connected, beq_iff_eq, hinv.label_eq_iff]
  constructor
  · intro h
    refine EqvGen.mono (fun x y ⟨w, hw⟩ ↦ ?_) a b h
    rcases honly _ hw with hw' | hw'
    · simp at hw'
    · obtain ⟨hwL, hσ⟩ := List.mem_filter.1 hw'
      exact ⟨w, hwL, of_decide_eq_true hσ⟩
  · intro h
    induction h with
    | rel x y hr =>
      obtain ⟨w, hw, hσ⟩ := hr
      exact hcover (x, y, w) (List.mem_filter.2 ⟨hw, decide_eq_true hσ⟩)
    | refl => exact EqvGen.refl _
    | symm x y _ ih => exact EqvGen.symm _ _ ih
    | trans x y z _ _ ih₁ ih₂ => exact EqvGen.trans _ _ _ ih₁ ih₂

/-- **SIG-3** σ* is symmetric. -/
theorem sigmaStar_symm (L : List (Edge V W)) (grid : List W) (a b : V) :
    sigmaStar L grid a b = sigmaStar L grid b a := by
  unfold sigmaStar
  congr 1
  refine List.filter_congr fun g _ ↦ ?_
  rw [Bool.eq_iff_iff, connected_iff, connected_iff]
  exact ⟨(conn_equivalence L g).symm, (conn_equivalence L g).symm⟩

theorem sigmaStar_spec {L : List (Edge V W)} {grid : List W} {a b : V} {x : W}
    (h : sigmaStar L grid a b = some x) : x ∈ grid ∧ Conn L x a b := by
  obtain ⟨hg, hc⟩ := List.mem_filter.1 (List.max?_mem h)
  exact ⟨hg, (connected_iff L x a b).1 hc⟩

theorem le_sigmaStar {L : List (Edge V W)} {grid : List W} {a b : V} {g : W} (hg : g ∈ grid)
    (hc : Conn L g a b) : ∃ x, sigmaStar L grid a b = some x ∧ g ≤ x :=
  exists_max?_filter hg ((connected_iff L g a b).2 hc)

/-- **SIG-3** σ* is an ultrametric: `σ*(a, c) ≥ min(σ*(a, b), σ*(b, c))`, the link from `a` to `c`
at least as strict as the weaker of the two through `b`. -/
theorem sigmaStar_ultra {L : List (Edge V W)} {grid : List W} {a b c : V} {x y : W}
    (hab : sigmaStar L grid a b = some x) (hbc : sigmaStar L grid b c = some y) :
    ∃ z, sigmaStar L grid a c = some z ∧ min x y ≤ z := by
  obtain ⟨hx, hcx⟩ := sigmaStar_spec hab
  obtain ⟨hy, hcy⟩ := sigmaStar_spec hbc
  refine le_sigmaStar ?_ (hcx.ultra hcy)
  rcases min_choice x y with h | h <;> rw [h] <;> assumption

/-- **SIG-4** σ* is `none` exactly when the pair shares no component at any grid point, so, the
threshold graphs shrinking as `σ` rises, exactly when it shares none at the loosest. -/
theorem sigmaStar_eq_none_iff (L : List (Edge V W)) (grid : List W) (a b : V) :
    sigmaStar L grid a b = none ↔ ∀ g ∈ grid, ¬Conn L g a b := by
  simp [sigmaStar, List.filter_eq_nil_iff, connected_iff]

/-- In any edge list, two distinct vertices are linked at `g` exactly when `g` is at most the
largest of its weights at which they are linked. -/
theorem conn_iff_le_bottleneck (F : List (Edge V W)) {a b : V} (hab : a ≠ b) (g : W) :
    Conn F g a b ↔ ∃ x, bottleneck F a b = some x ∧ g ≤ x := by
  constructor
  · intro h
    obtain ⟨x, y, w, hw, hgw⟩ := h.exists_adj hab
    -- the least of `F`'s weights at or above `g` links `a` and `b` as `g` does
    have hS : w ∈ (F.map (·.2.2)).filter (g ≤ ·) :=
      List.mem_filter.2 ⟨List.mem_map.2 ⟨(x, y, w), hw, rfl⟩, decide_eq_true hgw⟩
    cases hmin : ((F.map (·.2.2)).filter (g ≤ ·)).min? with
    | none => rw [List.min?_eq_none_iff] at hmin; simp [hmin] at hS
    | some w₀ =>
      obtain ⟨hw₀, hle⟩ := List.min?_eq_some_iff.1 hmin
      obtain ⟨hw₀F, hgw₀⟩ := List.mem_filter.1 hw₀
      have hc : Conn F w₀ a b := EqvGen.mono (fun x y ⟨w', hw', hgw'⟩ ↦ ⟨w', hw', hle w'
        (List.mem_filter.2 ⟨List.mem_map.2 ⟨(x, y, w'), hw', rfl⟩, decide_eq_true hgw'⟩)⟩) a b h
      obtain ⟨z, hz, hw₀z⟩ :=
        exists_max?_filter (p := (connected F · a b)) hw₀F ((connected_iff F w₀ a b).2 hc)
      exact ⟨z, hz, (of_decide_eq_true hgw₀).trans hw₀z⟩
  · rintro ⟨x, hx, hgx⟩
    obtain ⟨-, hc⟩ := List.mem_filter.1 (List.max?_mem hx)
    exact ((connected_iff F x a b).1 hc).anti hgx

end Connected

/-! ## SIG-1, SIG-2 and SIG-4: Kruskal's forest -/

section Kruskal

variable [LinearOrder V] [LinearOrder W]

theorem before_weight {e f : Edge V W} (h : before e f = true) : f.2.2 ≤ e.2.2 := by
  simp only [before, decide_eq_true_eq, Prod.Lex.toLex_le_toLex, OrderDual.toDual_lt_toDual,
    OrderDual.toDual_inj] at h
  rcases h with h | ⟨h, _⟩
  · exact h.le
  · exact h.ge

theorem sorted_before (L : List (Edge V W)) :
    (L.mergeSort before).Pairwise fun e f ↦ before e f = true :=
  List.pairwise_mergeSort (fun a b c hab hbc ↦ by
      simp only [before, decide_eq_true_eq] at hab hbc ⊢; exact hab.trans hbc)
    (fun a b ↦ by simp only [before, Bool.or_eq_true, decide_eq_true_eq]; exact le_total _ _) L

/-- Kruskal's loop over a list sorted by descending weight, from a forest whose every edge is at
least as heavy as every edge to come: each edge given ends up linked by forest edges at least as
heavy as itself. -/
theorem foldl_step_heavy (L : List (Edge V W)) (hL : L.Pairwise fun e f ↦ f.2.2 ≤ e.2.2) :
    ∀ (F : List (Edge V W)) (lab : V → V), LabelInv F lab → (∀ f ∈ F, ∀ e ∈ L, e.2.2 ≤ f.2.2) →
      ∀ e ∈ L, Conn (L.foldl step (F, lab)).1 e.2.2 e.1 e.2.1 := by
  induction L with
  | nil => simp
  | cons e L ih =>
    intro F lab h hheavy
    obtain ⟨u, v, w⟩ := e
    rw [List.pairwise_cons] at hL
    rw [List.foldl_cons]
    by_cases huv : lab u = lab v
    · rw [step_of_eq w huv]
      have hrest : ∀ f ∈ F, ∀ e ∈ L, e.2.2 ≤ f.2.2 :=
        fun f hf e he ↦ hheavy f hf e (List.mem_cons_of_mem _ he)
      intro f hf
      rcases List.mem_cons.1 hf with rfl | hf'
      · -- rejected: `u` and `v` were linked by forest edges, each at least as heavy
        obtain ⟨-, hkeep, -, -⟩ := foldl_step L F lab h
        have hlink := (h.label_eq_iff u v).1 huv
        exact Conn.sub hkeep (EqvGen.mono (fun a b ⟨w', hw'⟩ ↦
          ⟨w', hw', hheavy _ hw' _ List.mem_cons_self⟩) _ _ hlink)
      · exact ih hL.2 F lab h hrest f hf'
    · rw [step_of_ne w huv]
      have hrest : ∀ f ∈ (u, v, w) :: F, ∀ e ∈ L, e.2.2 ≤ f.2.2 := by
        intro f hf e he
        rcases List.mem_cons.1 hf with rfl | hf'
        · exact hL.1 e he
        · exact hheavy f hf' e (List.mem_cons_of_mem _ he)
      intro f hf
      rcases List.mem_cons.1 hf with rfl | hf'
      · obtain ⟨-, hkeep, -, -⟩ := foldl_step L _ _ (h.merge w huv)
        exact EqvGen.rel _ _ ⟨w, hkeep _ List.mem_cons_self, le_rfl⟩
      · exact ih hL.2 _ _ (h.merge w huv) hrest f hf'

/-- **SIG-1** One maximum spanning forest realizes every threshold: at every `σ`, `a ∼ b` in the
forest's `G_σ` exactly when `a ∼ b` in the graph's. So every pairwise σ* can be read off the one
forest (`build_max_spanning_tree`, built once per cut). -/
theorem conn_kruskal_iff (L : List (Edge V W)) (σ : W) (a b : V) :
    Conn (kruskal L).1 σ a b ↔ Conn L σ a b := by
  have hsorted := (sorted_before L).imp fun h ↦ before_weight h
  have hfold := foldl_step (L.mergeSort before) [] id labelInv_nil
  refine ⟨Conn.sub fun e he ↦ ?_, fun h ↦ ?_⟩
  · rcases hfold.2.2.1 e he with he' | he'
    · simp at he'
    · exact List.mem_mergeSort.1 he'
  · induction h with
    | rel x y hr =>
      obtain ⟨w, hw, hσ⟩ := hr
      exact (foldl_step_heavy _ hsorted [] id labelInv_nil (by simp) (x, y, w)
        (List.mem_mergeSort.2 hw)).anti hσ
    | refl => exact EqvGen.refl _
    | symm x y _ ih => exact EqvGen.symm _ _ ih
    | trans x y z _ _ ih₁ ih₂ => exact EqvGen.trans _ _ _ ih₁ ih₂

/-- **SIG-2** The final labels are the components of what the loop kept. -/
theorem kruskal_label_eq_iff (L : List (Edge V W)) (a b : V) :
    (kruskal L).2 a = (kruskal L).2 b ↔ Linked (kruskal L).1 a b :=
  (foldl_step (L.mergeSort before) [] id labelInv_nil).1.label_eq_iff a b

/-- **SIG-2** What the loop keeps is a forest: its edges and its components together number the
vertices, `|F| + c(F) = |V|`, so no kept edge closes a cycle. -/
theorem kruskal_card [Fintype V] (L : List (Edge V W)) :
    (kruskal L).1.length + (Finset.univ.image (kruskal L).2).card = Fintype.card V := by
  rw [kruskal, foldl_step_card]
  simp

/-- **SIG-4** σ* read off the forest is the union-find sweep over the graph: for any two
vertices, the forest's bottleneck snapped to the grid, the strictest grid point for a vertex and
itself, is the largest grid point at which they share a component of `G_σ`, and `none` when there
is none. -/
theorem sigmaStarForest_kruskal (L : List (Edge V W)) (grid : List W) (a b : V) :
    sigmaStarForest (kruskal L).1 grid a b = sigmaStar L grid a b := by
  unfold sigmaStarForest
  split_ifs with hab
  · -- every grid point links a vertex to itself
    subst hab
    unfold sigmaStar
    rw [List.filter_eq_self.2 fun g _ ↦ by simp [connected]]
  cases hx : bottleneck (kruskal L).1 a b with
  | none =>
    refine ((sigmaStar_eq_none_iff L grid a b).2 fun g _ hc ↦ ?_).symm
    obtain ⟨x, hx', -⟩ := (conn_iff_le_bottleneck _ hab g).1 ((conn_kruskal_iff L g a b).2 hc)
    rw [hx] at hx'
    cases hx'
  | some x =>
    simp only [Option.bind_some, snap, sigmaStar]
    congr 1
    refine List.filter_congr fun g _ ↦ ?_
    rw [Bool.eq_iff_iff, decide_eq_true_eq, connected_iff, ← conn_kruskal_iff L g a b,
      conn_iff_le_bottleneck _ hab, hx]
    simp

end Kruskal

end Palace.SigmaStar
