module

public import Palace.Clock.Defs

/-!
# The global event clock: C1, C2, cuts and proper time, the statements

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

These are the laws of `Palace/Clock.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

open Relation

namespace Palace.Clock

/-! ### C1 and C2 -/

section Fibers

variable {E I : Type*}

/-- **CLK-1, C1 ⇒ C2**: into a partial order, a monotone clock has convex fibers, along any
relation. -/
theorem convexFibers_of_monotone [PartialOrder I] {R : E → E → Prop} {p : E → I}
    (h : MonotoneAlong R p) : ConvexFibers R p :=
  sorry

/-- **CLK-1** C1 needs checking only on the generator edges: monotone along them is monotone along
`≼`. -/
theorem MonotoneAlong.closure [Preorder I] {g : E → E → Prop} {p : E → I}
    (h : MonotoneAlong g p) : MonotoneAlong (ReflTransGen g) p :=
  sorry

end Fibers

/-! ### Cuts -/

section Cuts

variable {E : Type*} (g : E → E → Prop)

/-- **CLK-2, the cut criterion**: `S` is a cut iff no generator edge crosses it, so the falsifier
never computes the closure. -/
theorem isCut_iff_not_crossed {S : Set E} : IsCut g S ↔ ¬Crossed g S :=
  sorry

variable {g}

/-- **CLK-2** Cuts are closed under intersection. -/
theorem IsCut.inter {S T : Set E} (hS : IsCut g S) (hT : IsCut g T) : IsCut g (S ∩ T) :=
  sorry

/-- **CLK-2** And under union. -/
theorem IsCut.union {S T : Set E} (hS : IsCut g S) (hT : IsCut g T) : IsCut g (S ∪ T) :=
  sorry

variable {K : Type*} (store : E → K) (pos : E → ℕ)

/-- **CLK-2, frontier cuts** need only their cross-store edges checked, when every in-store
generator edge runs forward (g1, the per-store append chains). -/
theorem isCut_frontierCut_iff (hg : ∀ a b, g a b → store a = store b → pos a ≤ pos b)
    (f : K → ℕ) :
    IsCut g (frontierCut store pos f) ↔ ∀ a b, g a b → store a ≠ store b →
      b ∈ frontierCut store pos f → a ∈ frontierCut store pos f :=
  sorry

/-- **CLK-2, certificates compose**: the pointwise minimum of two consistent frontiers is
consistent. -/
theorem IsCut.frontier_inf {f f' : K → ℕ} (h : IsCut g (frontierCut store pos f))
    (h' : IsCut g (frontierCut store pos f')) : IsCut g (frontierCut store pos (f ⊓ f')) :=
  sorry

end Cuts

/-! ### Proper time -/

section ProperTime

variable {E : Type*} [PartialOrder E]

/-- **CLK-3** A chain from a point to itself has no step. -/
theorem properTime_self (a : E) : properTime a a = 0 :=
  sorry

/-- **CLK-3** A strict step takes proper time. -/
theorem one_le_properTime {a b : E} (h : a < b) : 1 ≤ properTime a b :=
  sorry

/-- **CLK-3, reverse triangle inequality**: along causally ordered events proper times add up to at
most the proper time of the whole, since chains concatenate. -/
theorem properTime_add_le {a b c : E} (hab : a ≤ b) (hbc : b ≤ c) :
    properTime a b + properTime b c ≤ properTime a c :=
  sorry

/-- **CLK-3** On a finite `N` every proper time is finite. -/
theorem properTime_lt_top [Finite E] (a b : E) : properTime a b < ⊤ :=
  sorry

/-- **CLK-3, the grain**: a strictly monotone clock bounds proper time by its tick difference, since
a chain of `n` steps advances it at least `n`. -/
theorem properTime_le_tick {p : E → ℕ} (hp : StrictMono p) (a b : E) :
    properTime a b ≤ ((p b - p a : ℕ) : ℕ∞) :=
  sorry

end ProperTime

/-! ### `≼` is a partial order -/

section Order

variable {E : Type*} {g : E → E → Prop}

/-- **CLK-4** Acyclic generators give a partial order: `≼`, the reflexive-transitive closure of
the generator edges, is antisymmetric when no event reaches itself along a nonempty chain. -/
theorem antisymm_of_acyclic (h : ∀ a, ¬ TransGen g a a) {a b : E} (hab : ReflTransGen g a b)
    (hba : ReflTransGen g b a) : a = b :=
  sorry

/-- **CLK-4** A cycle through two events breaks antisymmetry, which is why `derive` refuses one. -/
theorem cycle_not_antisymm :
    ∃ g : Bool → Bool → Prop, ReflTransGen g true false ∧ ReflTransGen g false true ∧
      true ≠ false :=
  sorry

end Order

end Palace.Clock
