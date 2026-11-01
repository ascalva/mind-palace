import Mathlib.Data.ENat.Lattice
import Mathlib.Logic.Relation
import Mathlib.Order.RelSeries
import Palace.Attack

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

/-- **C1 ⇒ C2**: into a partial order, a monotone clock has convex fibers, along any relation. -/
theorem convexFibers_of_monotone [PartialOrder I] {R : E → E → Prop} {p : E → I}
    (h : MonotoneAlong R p) : ConvexFibers R p :=
  fun a b c hab hbc hac ↦ le_antisymm ((h b c hbc).trans_eq hac.symm) (h a b hab)

/-- C1 needs checking only on the generator edges: monotone along them is monotone along `≼`. -/
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

/-- **The cut criterion**: `S` is a cut iff no generator edge crosses it, so the falsifier never
computes the closure. -/
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

theorem IsCut.inter {S T : Set E} (hS : IsCut g S) (hT : IsCut g T) : IsCut g (S ∩ T) :=
  fun a b hab hb ↦ ⟨hS a b hab hb.1, hT a b hab hb.2⟩

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

/-- **Frontier cuts** need only their cross-store edges checked, when every in-store generator
edge runs forward (g1, the per-store append chains). -/
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

/-- **Certificates compose**: the pointwise minimum of two consistent frontiers is consistent. -/
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

/-- A chain from a point to itself has no step. -/
theorem properTime_self (a : E) : properTime a a = 0 := by
  refine le_antisymm (iSup₂_le fun s hs ↦ ?_) zero_le
  have : s.length = 0 := by
    by_contra h0
    have hlt : s.head < s.last := s.strictMono (by simp [Fin.lt_def]; omega)
    rw [hs.1, hs.2] at hlt
    exact lt_irrefl a hlt
  simp [this]

/-- A strict step takes proper time. -/
theorem one_le_properTime {a b : E} (h : a < b) : 1 ≤ properTime a b := by
  simpa using length_le_properTime (step h)

/-- **Reverse triangle inequality**: along causally ordered events proper times add up to at
most the proper time of the whole, since chains concatenate. -/
theorem properTime_add_le {a b c : E} (hab : a ≤ b) (hbc : b ≤ c) :
    properTime a b + properTime b c ≤ properTime a c := by
  refine ENat.biSup_add_biSup_le' (exists_chain hab) (exists_chain hbc) fun s hs t ht ↦ ?_
  have := length_le_properTime (s.smash t (hs.2.trans ht.1.symm))
  simpa [hs.1, ht.2] using this

/-- On a finite `N` every proper time is finite. -/
theorem properTime_lt_top [Finite E] (a b : E) : properTime a b < ⊤ := by
  have := Fintype.ofFinite E
  exact lt_of_le_of_lt (iSup₂_le fun s _ ↦ by exact_mod_cast (LTSeries.length_lt_card s).le)
    (ENat.natCast_lt_top (Fintype.card E))

/-- **The grain**: a strictly monotone clock bounds proper time by its tick difference, since a
chain of `n` steps advances it at least `n`. -/
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

/-! ## Attacks

On random generator graphs over `Fin 6`, with `≼` decided by Warshall's closure over arrays.
Proper time has no executable form (a supremum over chains); its reverse triangle is attacked on
the longest-path recursion a materialized `N` would run, over random DAGs. Each control states a
nearby false law and must be refuted.
-/

namespace Attack

/-- `≼` decided: Warshall's reflexive-transitive closure of the generator edges. -/
def reach (es : List (Fin 6 × Fin 6)) : Array (Array Bool) := Id.run do
  let mut r : Array (Array Bool) := Array.ofFn fun a : Fin 6 ↦ Array.ofFn fun b : Fin 6 ↦
    a == b || es.contains (a, b)
  for k in List.range 6 do
    r := Array.ofFn fun a : Fin 6 ↦ Array.ofFn fun b : Fin 6 ↦
      (r[a.val]!)[b.val]! || ((r[a.val]!)[k]! && (r[k]!)[b.val]!)
  return r

/-- Is `S` a down-set of the closure, and does the falsifier find no crossing edge? With
`outward`, the falsifier searches the wrong way: edges out of `S`. -/
def cutHolds (outward : Bool) (es : List (Fin 6 × Fin 6)) (ss : List (Fin 6)) : Bool :=
  let R := reach es
  let isCut := (List.finRange 6).all fun a ↦ (List.finRange 6).all fun b ↦
    !(R[a.val]!)[b.val]! || !ss.contains b || ss.contains a
  let crossed := es.any fun e ↦
    if outward then ss.contains e.1 && !ss.contains e.2 else ss.contains e.2 && !ss.contains e.1
  isCut == !crossed

/- §2.4: a set is a cut iff no generator edge reads into it from outside. -/
#eval survives (∀ es : List (Fin 6 × Fin 6), ∀ ss : List (Fin 6), cutHolds false es ss = true) 101

/- Control, the falsifier searching edges out of the set. -/
#eval refuted (∀ es : List (Fin 6 × Fin 6), ∀ ss : List (Fin 6), cutHolds true es ss = true) 102

/-- Ticks in `Fin 4`, compared by `≤`, or with `coarse` by `x / 2 ≤ y / 2` (not antisymmetric). -/
def tickLe (coarse : Bool) (x y : Fin 4) : Bool := if coarse then x.val / 2 ≤ y.val / 2 else x ≤ y

/-- C1 on the generator edges, for the clock read off `ps`. -/
def monoGen (coarse : Bool) (es : List (Fin 6 × Fin 6)) (ps : List (Fin 4)) : Bool :=
  (es.take 5).all fun e ↦ tickLe coarse (ps.getD e.1.val 0) (ps.getD e.2.val 0)

/-- C1 along the whole closure, and C2. -/
def clockHolds (coarse : Bool) (es : List (Fin 6 × Fin 6)) (ps : List (Fin 4)) : Bool :=
  let R := reach (es.take 5)
  let p (e : Fin 6) : Fin 4 := ps.getD e.val 0
  let rel (a b : Fin 6) : Bool := (R[a.val]!)[b.val]!
  ((List.finRange 6).all fun a ↦ (List.finRange 6).all fun b ↦
      !rel a b || tickLe coarse (p a) (p b)) &&
    (List.finRange 6).all fun a ↦ (List.finRange 6).all fun b ↦ (List.finRange 6).all fun c ↦
      !(rel a b && rel b c && p a == p c) || p b == p a

/- C1 on the generators gives C1 on `≼`, and C1 gives C2. -/
#eval survives (∀ es : List (Fin 6 × Fin 6), ∀ ps : List (Fin 4),
  monoGen false es ps = true → clockHolds false es ps = true) 103

/- Control, ticks compared by a preorder that is not antisymmetric: C1 without C2. -/
#eval refuted (∀ es : List (Fin 6 × Fin 6), ∀ ps : List (Fin 4),
  monoGen true es ps = true → clockHolds true es ps = true) 104

/-- In-store generator edges run forward: stores are `e % 2`, positions `e / 2`. -/
def forward (es : List (Fin 6 × Fin 6)) : List (Fin 6 × Fin 6) :=
  es.filter fun e ↦ e.1.val % 2 ≠ e.2.val % 2 ∨ e.1.val / 2 ≤ e.2.val / 2

/-- Is the frontier cut a cut, decided on the closure? -/
def frontierIsCut (es : List (Fin 6 × Fin 6)) (f : Fin 2 → ℕ) : Bool :=
  let R := reach es
  let inS (e : Fin 6) : Bool := decide (e.val / 2 < f ⟨e.val % 2, by omega⟩)
  (List.finRange 6).all fun a ↦ (List.finRange 6).all fun b ↦
    !(R[a.val]!)[b.val]! || !inS b || inS a

/-- The frontier criterion (cross-store edges only) agrees with the closure, and consistent
frontiers compose by pointwise minimum and maximum. -/
def frontierHolds (es : List (Fin 6 × Fin 6)) (f0 f1 g0 g1 : Fin 4) : Bool :=
  let es := forward es
  let f : Fin 2 → ℕ := fun s ↦ if s = 0 then f0 else f1
  let f' : Fin 2 → ℕ := fun s ↦ if s = 0 then g0 else g1
  let inS (e : Fin 6) : Bool := decide (e.val / 2 < f ⟨e.val % 2, by omega⟩)
  let cross := (es.filter fun e ↦ e.1.val % 2 ≠ e.2.val % 2).all fun e ↦ !inS e.2 || inS e.1
  (frontierIsCut es f == cross) &&
    (!(frontierIsCut es f && frontierIsCut es f') ||
      (frontierIsCut es (f ⊓ f') && frontierIsCut es (f ⊔ f')))

/- §2.4: frontier cuts, their criterion and their composition. -/
#eval survives (∀ es : List (Fin 6 × Fin 6), ∀ f0 f1 g0 g1 : Fin 4,
  frontierHolds es f0 f1 g0 g1 = true) 105

/-- Longest chains in the DAG `es` (edges `i → j` with `i < j`), `-1` where `a ⋠ b`: the
recursion over `a` from the top. -/
def longest (es : List (Fin 6 × Fin 6)) : Array (Array Int) := Id.run do
  let dag := es.filter fun e ↦ e.1 < e.2
  let R := reach dag
  let mut t : Array (Array Int) := Array.replicate 6 (Array.replicate 6 (-1))
  for a' in List.range 6 do
    let a := 5 - a'
    for b in List.range 6 do
      let v : Int := if a == b then 0 else
        (List.range 6).foldl (fun acc c ↦
          if (dag.any fun e ↦ e.1.val == a && e.2.val == c) && (R[c]!)[b]! && 0 ≤ (t[c]!)[b]! then
            max acc ((t[c]!)[b]! + 1)
          else acc) (-1)
      t := t.set! a ((t[a]!).set! b v)
  return t

/-- The reverse triangle on one DAG; `forward` asks the ordinary triangle instead. -/
def triangleHolds (forward : Bool) (es : List (Fin 6 × Fin 6)) : Bool :=
  let t := longest es
  let lp (a b : Fin 6) : Int := (t[a.val]!)[b.val]!
  (List.finRange 6).all fun a ↦ (List.finRange 6).all fun b ↦ (List.finRange 6).all fun c ↦
    !(0 ≤ lp a b && 0 ≤ lp b c) ||
      if forward then lp a c ≤ lp a b + lp b c else lp a b + lp b c ≤ lp a c

/- GC-N6: proper time's reverse triangle inequality, on the longest-path recursion. -/
#eval survives (∀ es : List (Fin 6 × Fin 6), triangleHolds false es = true) 106

/- Control, the ordinary triangle inequality: a long detour beats the path through `b`. -/
#eval refuted (∀ es : List (Fin 6 × Fin 6), triangleHolds true es = true) 107

end Attack

end Palace.Clock
