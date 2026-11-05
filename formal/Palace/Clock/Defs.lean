module

public import Mathlib.Data.ENat.Lattice
public import Mathlib.Logic.Relation
public import Mathlib.Order.RelSeries

/-!
# The global event clock: C1, C2, cuts and proper time, the definitions

The definitions the laws of `Palace/Clock.lean` are stated over. With `Spec/Clock.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
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

end Fibers

/-! ### Cuts -/

section Cuts

variable {E : Type*} (g : E → E → Prop)

/-- A cut of `N`: a down-set of `≼` (§2.4, a consistent cross-stratum instant). -/
def IsCut (S : Set E) : Prop := ∀ a b, ReflTransGen g a b → b ∈ S → a ∈ S

/-- What the cut falsifier searches for: a generator edge reading into `S` from outside it. -/
def Crossed (S : Set E) : Prop := ∃ a b, g a b ∧ b ∈ S ∧ a ∉ S

variable {g}

variable {K : Type*} (store : E → K) (pos : E → ℕ)

/-- The cut at frontier `f`: the events below their store's frontier position (§2.4, the vector
of per-store chain positions). -/
def frontierCut (f : K → ℕ) : Set E := {e | pos e < f (store e)}

end Cuts

/-! ### Proper time -/

section ProperTime

variable {E : Type*} [PartialOrder E]

/-- **Proper time** (GC-N6): the length of the longest strict chain from `a` to `b`, and `0`
when `a ≰ b` (there is none). -/
noncomputable def properTime (a b : E) : ℕ∞ :=
  ⨆ s : LTSeries E, ⨆ _ : s.head = a ∧ s.last = b, (s.length : ℕ∞)

open scoped Classical in
/-- **Proper time as the code reports it** (`core/temporal/spine.py::Spine.proper_time`, its first
component): the same longest chain counted in events, not steps, so one more than `properTime`
for a comparable pair, in either order, and `0` when `a` and `b` are concurrent. -/
noncomputable def eventCount (a b : E) : ℕ∞ :=
  if a ≤ b then properTime a b + 1 else if b ≤ a then properTime b a + 1 else 0

end ProperTime

/-! ### `≼` is a partial order -/

section Order

variable {E : Type*} {g : E → E → Prop}

/-- **CLK-4** The partial order `≼` of acyclic generators (`Spine.derive`'s topological sort):
antisymmetry is the one field acyclicity is needed for. -/
@[instance_reducible]
def spineOrder (h : ∀ a, ¬ TransGen g a a) : PartialOrder E where
  le := ReflTransGen g
  le_refl _ := ReflTransGen.refl
  le_trans _ _ _ := ReflTransGen.trans
  le_antisymm a b hab hba := by
    rcases reflTransGen_iff_eq_or_transGen.1 hab with h1 | h1
    · exact h1.symm
    rcases reflTransGen_iff_eq_or_transGen.1 hba with h2 | h2
    · exact h2
    exact absurd (h1.trans h2) (h a)

end Order

end Palace.Clock
