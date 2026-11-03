module

public import Mathlib.Data.ENat.Lattice
public import Mathlib.Logic.Relation
public import Mathlib.Order.RelSeries

/-!
# The global event clock: C1, C2, cuts and proper time

Statements of the clock laws of `docs/design-notes/global-event-clock.md` (§2.3, §2.4), the
order the Dreamer's diachronic instruments read. `N = (Ev, ≼)`, with `≼` the reflexive-transitive
closure of the generator edges of §2.2 (per-store append chains, reads-from references, recorded
program order). A clock is a map `p : Ev → I`.

* C2 is not a law of its own. A clock monotone along `≼` (C1) into a partial order has convex
  fibers, whatever `≼` is. C2 fails without C1 failing only when ticks are compared by a preorder
  that is not antisymmetric (`convex_needs_antisymm`), and C1 needs checking only on the generator
  edges.
* A cut (§2.4) is a down-set of `≼`. A set is one exactly when no generator edge reads into it
  from outside, which is the cut falsifier's search, with no closure to compute. Cuts are closed
  under intersection and union; a frontier cut (a vector of per-store chain positions) needs only
  its cross-store edges checked; certificates compose by the pointwise minimum and maximum of
  their frontiers.
* Proper time (GC-N6) is the length of the longest chain. It is 0 at a point, at least 1 across a
  strict step, finite on a finite `N`, satisfies the reverse triangle inequality along causally
  ordered events, and is bounded by the tick difference of any strictly monotone clock: a
  cardinal reading must declare its grain.

C3 and C4 (read-clocks borrow the write frontier; wall time is no clock of `Ev`) say what may be
registered as a clock, with nothing to prove.
-/

@[expose] public section

open Relation

namespace Palace.Clock

/-! ### C1 and C2 -/

section Fibers

variable {E I : Type*}

/-- **C1**: the clock `p` is monotone along `R`. -/
def MonotoneAlong [Preorder I] (R : E → E → Prop) (p : E → I) : Prop := ∀ a b, R a b → p a ≤ p b

/-- **C2**: every tick's fiber is convex in `R`: no event outside a tick lies between two events
inside it (a commit is a range of `N`). -/
def ConvexFibers (R : E → E → Prop) (p : E → I) : Prop :=
  ∀ a b c, R a b → R b c → p a = p c → p b = p a

/-- **CLK-1, C1 ⇒ C2**: into a partial order, a monotone clock has convex fibers, along any
relation. -/
theorem convexFibers_of_monotone [PartialOrder I] {R : E → E → Prop} {p : E → I}
    (h : MonotoneAlong R p) : ConvexFibers R p :=
  fun a b c hab hbc hac ↦ le_antisymm ((h b c hbc).trans_eq hac.symm) (h a b hab)

/-- **CLK-1** C1 needs checking only on the generator edges: monotone along them is monotone along
`≼`. -/
theorem MonotoneAlong.closure [Preorder I] {g : E → E → Prop} {p : E → I}
    (h : MonotoneAlong g p) : MonotoneAlong (ReflTransGen g) p := by
  intro a b hab
  induction hab with
  | refl => exact le_rfl
  | tail _ hbc ih => exact ih.trans (h _ _ hbc)

/-- Ticks compared by a preorder that is not antisymmetric: every tick is below every other. -/
def Coarse : Type := Bool

instance : Preorder Coarse where
  le _ _ := True
  le_refl _ := trivial
  le_trans _ _ _ _ _ := trivial

/-- Without antisymmetry C1 does not give C2: a monotone clock whose fiber over `false` has `1`
between `0` and `2`. -/
theorem convex_needs_antisymm :
    ∃ p : Fin 3 → Coarse, MonotoneAlong (· ≤ ·) p ∧ ¬ConvexFibers (· ≤ ·) p := by
  refine ⟨![false, true, false], fun _ _ _ ↦ trivial, fun h ↦ ?_⟩
  have : (true : Bool) = false := h 0 1 2 (by decide) (by decide) rfl
  exact Bool.noConfusion this

/-- Nor does C2 give C1: a clock that runs backwards has singleton fibers. -/
theorem monotone_not_of_convex :
    ∃ p : Fin 2 → ℕ, ConvexFibers (· ≤ ·) p ∧ ¬MonotoneAlong (· ≤ ·) p := by
  refine ⟨![1, 0], ?_, fun h ↦ by simpa using h 0 1 (by decide)⟩
  unfold ConvexFibers
  decide

end Fibers

/-! ### Cuts -/

section Cuts

variable {E : Type*} (g : E → E → Prop)

/-- A cut of `N`: a down-set of `≼` (§2.4, a consistent cross-stratum instant). -/
def IsCut (S : Set E) : Prop := ∀ a b, ReflTransGen g a b → b ∈ S → a ∈ S

/-- What the cut falsifier searches for: a generator edge reading into `S` from outside it. -/
def Crossed (S : Set E) : Prop := ∃ a b, g a b ∧ b ∈ S ∧ a ∉ S

/-- **CLK-2, the cut criterion**: `S` is a cut iff no generator edge crosses it, so the falsifier
never computes the closure. -/
theorem isCut_iff_not_crossed {S : Set E} : IsCut g S ↔ ¬Crossed g S := by
  constructor
  · rintro h ⟨a, b, hab, hb, ha⟩
    exact ha (h a b (.single hab) hb)
  · intro h a b hab hb
    induction hab using ReflTransGen.head_induction_on with
    | refl => exact hb
    | head hac _ ih =>
      by_contra ha
      exact h ⟨_, _, hac, ih, ha⟩

variable {g}

/-- **CLK-2** Cuts are closed under intersection. -/
theorem IsCut.inter {S T : Set E} (hS : IsCut g S) (hT : IsCut g T) : IsCut g (S ∩ T) :=
  fun a b hab hb ↦ ⟨hS a b hab hb.1, hT a b hab hb.2⟩

/-- **CLK-2** And under union. -/
theorem IsCut.union {S T : Set E} (hS : IsCut g S) (hT : IsCut g T) : IsCut g (S ∪ T) :=
  fun a b hab hb ↦ hb.imp (hS a b hab) (hT a b hab)

theorem isCut_iInter {ι : Sort*} {S : ι → Set E} (h : ∀ i, IsCut g (S i)) :
    IsCut g (⋂ i, S i) :=
  fun a b hab hb ↦ Set.mem_iInter.2 fun i ↦ h i a b hab (Set.mem_iInter.1 hb i)

theorem isCut_iUnion {ι : Sort*} {S : ι → Set E} (h : ∀ i, IsCut g (S i)) :
    IsCut g (⋃ i, S i) := fun a b hab hb ↦ by
  obtain ⟨i, hi⟩ := Set.mem_iUnion.1 hb
  exact Set.mem_iUnion.2 ⟨i, h i a b hab hi⟩

variable {K : Type*} (store : E → K) (pos : E → ℕ)

/-- The cut at frontier `f`: the events below their store's frontier position (§2.4, the vector
of per-store chain positions). -/
def frontierCut (f : K → ℕ) : Set E := {e | pos e < f (store e)}

/-- **CLK-2, frontier cuts** need only their cross-store edges checked, when every in-store
generator edge runs forward (g1, the per-store append chains). -/
theorem isCut_frontierCut_iff (hg : ∀ a b, g a b → store a = store b → pos a ≤ pos b)
    (f : K → ℕ) :
    IsCut g (frontierCut store pos f) ↔ ∀ a b, g a b → store a ≠ store b →
      b ∈ frontierCut store pos f → a ∈ frontierCut store pos f := by
  rw [isCut_iff_not_crossed]
  constructor
  · intro h a b hab _ hb
    by_contra ha
    exact h ⟨a, b, hab, hb, ha⟩
  · rintro h ⟨a, b, hab, hb, ha⟩
    by_cases hs : store a = store b
    · refine ha ?_
      change pos a < f (store a)
      rw [hs]
      exact (hg a b hab hs).trans_lt hb
    · exact ha (h a b hab hs hb)

theorem frontierCut_inf (f f' : K → ℕ) :
    frontierCut store pos (f ⊓ f') = frontierCut store pos f ∩ frontierCut store pos f' := by
  ext e
  simp [frontierCut, lt_min_iff]

theorem frontierCut_sup (f f' : K → ℕ) :
    frontierCut store pos (f ⊔ f') = frontierCut store pos f ∪ frontierCut store pos f' := by
  ext e
  simp [frontierCut, lt_max_iff]

/-- **CLK-2, certificates compose**: the pointwise minimum of two consistent frontiers is
consistent. -/
theorem IsCut.frontier_inf {f f' : K → ℕ} (h : IsCut g (frontierCut store pos f))
    (h' : IsCut g (frontierCut store pos f')) : IsCut g (frontierCut store pos (f ⊓ f')) := by
  rw [frontierCut_inf]
  exact h.inter h'

/-- And so is their pointwise maximum. -/
theorem IsCut.frontier_sup {f f' : K → ℕ} (h : IsCut g (frontierCut store pos f))
    (h' : IsCut g (frontierCut store pos f')) : IsCut g (frontierCut store pos (f ⊔ f')) := by
  rw [frontierCut_sup]
  exact h.union h'

end Cuts

/-! ### Proper time -/

section ProperTime

variable {E : Type*} [PartialOrder E]

/-- **Proper time** (GC-N6): the length of the longest strict chain from `a` to `b`, and `0`
when `a ≰ b` (there is none). -/
noncomputable def properTime (a b : E) : ℕ∞ :=
  ⨆ s : LTSeries E, ⨆ _ : s.head = a ∧ s.last = b, (s.length : ℕ∞)

theorem length_le_properTime (s : LTSeries E) : (s.length : ℕ∞) ≤ properTime s.head s.last :=
  le_iSup₂_of_le s ⟨rfl, rfl⟩ le_rfl

/-- The one-step chain `a < b`. -/
def step {a b : E} (h : a < b) : LTSeries E :=
  (RelSeries.singleton _ a).snoc b (by simpa using h)

@[simp] theorem step_head {a b : E} (h : a < b) : (step h).head = a := by simp [step]

@[simp] theorem step_last {a b : E} (h : a < b) : (step h).last = b := by simp [step]

@[simp] theorem step_length {a b : E} (h : a < b) : (step h).length = 1 := by simp [step]

theorem exists_chain {a b : E} (h : a ≤ b) : ∃ s : LTSeries E, s.head = a ∧ s.last = b := by
  rcases h.lt_or_eq with h | rfl
  · exact ⟨step h, by simp, by simp⟩
  · exact ⟨RelSeries.singleton _ a, by simp, by simp⟩

/-- **CLK-3** A chain from a point to itself has no step. -/
theorem properTime_self (a : E) : properTime a a = 0 := by
  refine le_antisymm (iSup₂_le fun s hs ↦ ?_) zero_le
  have : s.length = 0 := by
    by_contra h0
    have hlt : s.head < s.last := s.strictMono (by simp [Fin.lt_def]; omega)
    rw [hs.1, hs.2] at hlt
    exact lt_irrefl a hlt
  simp [this]

/-- **CLK-3** A strict step takes proper time. -/
theorem one_le_properTime {a b : E} (h : a < b) : 1 ≤ properTime a b := by
  simpa using length_le_properTime (step h)

/-- **CLK-3, reverse triangle inequality**: along causally ordered events proper times add up to at
most the proper time of the whole, since chains concatenate. -/
theorem properTime_add_le {a b c : E} (hab : a ≤ b) (hbc : b ≤ c) :
    properTime a b + properTime b c ≤ properTime a c := by
  refine ENat.biSup_add_biSup_le' (exists_chain hab) (exists_chain hbc) fun s hs t ht ↦ ?_
  have := length_le_properTime (s.smash t (hs.2.trans ht.1.symm))
  simpa [hs.1, ht.2] using this

/-- **CLK-3** On a finite `N` every proper time is finite. -/
theorem properTime_lt_top [Finite E] (a b : E) : properTime a b < ⊤ := by
  have := Fintype.ofFinite E
  exact lt_of_le_of_lt (iSup₂_le fun s _ ↦ by exact_mod_cast (LTSeries.length_lt_card s).le)
    (ENat.natCast_lt_top (Fintype.card E))

/-- **CLK-3, the grain**: a strictly monotone clock bounds proper time by its tick difference, since
a chain of `n` steps advances it at least `n`. -/
theorem properTime_le_tick {p : E → ℕ} (hp : StrictMono p) (a b : E) :
    properTime a b ≤ ((p b - p a : ℕ) : ℕ∞) := by
  refine iSup₂_le fun s hs ↦ ?_
  have key : ∀ i : Fin (s.length + 1), p (s 0) + i ≤ p (s i) := by
    intro i
    induction i using Fin.induction with
    | zero => simp
    | succ i ih =>
      have hlt : p (s i.castSucc) < p (s i.succ) := hp (by simpa using s.step i)
      simp only [Fin.val_succ, Fin.val_castSucc] at ih ⊢
      omega
  have hl := key (Fin.last _)
  rw [← hs.1, ← hs.2]
  simp only [Fin.val_last] at hl
  exact_mod_cast (by simp only [RelSeries.head, RelSeries.last]; omega)

end ProperTime

/-! ### `≼` is a partial order -/

section Order

variable {E : Type*} {g : E → E → Prop}

/-- **CLK-4** Acyclic generators give a partial order: `≼`, the reflexive-transitive closure of
the generator edges, is antisymmetric when no event reaches itself along a nonempty chain. -/
theorem antisymm_of_acyclic (h : ∀ a, ¬ TransGen g a a) {a b : E} (hab : ReflTransGen g a b)
    (hba : ReflTransGen g b a) : a = b := by
  rcases reflTransGen_iff_eq_or_transGen.1 hab with h1 | h1
  · exact h1.symm
  rcases reflTransGen_iff_eq_or_transGen.1 hba with h2 | h2
  · exact h2
  exact absurd (h1.trans h2) (h a)

/-- **CLK-4** The partial order `≼` of acyclic generators (`Spine.derive`'s topological sort). -/
@[instance_reducible]
def spineOrder (h : ∀ a, ¬ TransGen g a a) : PartialOrder E where
  le := ReflTransGen g
  le_refl _ := ReflTransGen.refl
  le_trans _ _ _ := ReflTransGen.trans
  le_antisymm _ _ := antisymm_of_acyclic h

/-- **CLK-4** A cycle through two events breaks antisymmetry, which is why `derive` refuses one. -/
theorem cycle_not_antisymm :
    ∃ g : Bool → Bool → Prop, ReflTransGen g true false ∧ ReflTransGen g false true ∧
      true ≠ false :=
  ⟨fun a b ↦ a ≠ b, ReflTransGen.single (by decide), ReflTransGen.single (by decide), by decide⟩

end Order

end Palace.Clock
