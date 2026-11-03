module

public import Palace.SigmaStar
public import Mathlib.Testing.Plausible.Sampleable
public import PalaceTest.Attack
public meta import Palace.SigmaStar
public meta import Mathlib.Testing.Plausible.Sampleable
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.SigmaStar`

The Plausible attacks and negative controls for the laws of `Palace/SigmaStar.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

namespace Palace.SigmaStar

/-! ### Attacks

On random edge lists over five vertices with weights in `Fin 4`, so ties, repeated edges and
self-loops all occur, and Kruskal's tie-break is exercised. Connectivity is computed by the
labels, which decide it (`connected_iff`). -/

namespace Attack

/-- The loop run in ascending order of weight: a minimum spanning forest, the control for SIG-1. -/
def kruskalMin (L : List (Edge (Fin 5) (Fin 4))) : List (Edge (Fin 5) (Fin 4)) :=
  ((L.mergeSort fun e f ↦ e.2.2 ≤ f.2.2).foldl step ([], id)).1

/-- The loop with every edge kept: no forest, the control for SIG-2. -/
def keepAll (L : List (Edge (Fin 5) (Fin 4))) : List (Edge (Fin 5) (Fin 4)) × (Fin 5 → Fin 5) :=
  (L, (L.foldl step ([], id)).2)

/-- The heaviest edge between two vertices, if any: the raw similarity, the control for SIG-3. -/
def direct (L : List (Edge (Fin 5) (Fin 4))) (a b : Fin 5) : Option (Fin 4) :=
  ((L.filter fun e ↦ (e.1 = a ∧ e.2.1 = b) ∨ (e.1 = b ∧ e.2.1 = a)).map (·.2.2)).max?

/-- The ultrametric inequality on optional values: wherever both legs exist, so does the third,
at least as strict as the weaker leg. -/
def Ultra (ab bc ac : Option (Fin 4)) : Prop :=
  match ab, bc with
  | some x, some y => ∃ z, ac = some z ∧ min x y ≤ z
  | _, _ => True

instance (ab bc ac : Option (Fin 4)) : Decidable (Ultra ab bc ac) := by
  unfold Ultra; split <;> infer_instance

/-- `_grid_snap` rounding the wrong way: the least grid point at or above `x`, the control for
SIG-4. -/
def snapUp (grid : List (Fin 4)) (x : Fin 4) : Option (Fin 4) := (grid.filter (x ≤ ·)).min?

/- SIG-1: the forest and the graph have the same components at every threshold. -/
#eval survives (∀ L : List (Edge (Fin 5) (Fin 4)), ∀ σ : Fin 4, ∀ a b : Fin 5,
  connected (kruskal L).1 σ a b = connected L σ a b) 181

/- SIG-1 control: a minimum spanning forest loses components at high thresholds. -/
#eval refuted (∀ L : List (Edge (Fin 5) (Fin 4)), ∀ σ : Fin 4, ∀ a b : Fin 5,
  connected (kruskalMin L) σ a b = connected L σ a b) 182

/- SIG-2: kept edges and components number the vertices. -/
#eval survives (∀ L : List (Edge (Fin 5) (Fin 4)),
  (kruskal L).1.length + (Finset.univ.image (kruskal L).2).card = 5) 183

/- SIG-2 control: keeping every edge closes cycles. -/
#eval refuted (∀ L : List (Edge (Fin 5) (Fin 4)),
  (keepAll L).1.length + (Finset.univ.image (keepAll L).2).card = 5) 184

/- SIG-3: σ* is an ultrametric, over random grids. -/
#eval survives (∀ L : List (Edge (Fin 5) (Fin 4)), ∀ grid : List (Fin 4), ∀ a b c : Fin 5,
  Ultra (sigmaStar L grid a b) (sigmaStar L grid b c) (sigmaStar L grid a c)) 185

/- SIG-3 control: the raw similarity is not, even between distinct ends. -/
#eval refuted (∀ L : List (Edge (Fin 5) (Fin 4)), ∀ a b c : Fin 5,
  a ≠ c → Ultra (direct L a b) (direct L b c) (direct L a c)) 186

/- SIG-4: σ* read off the forest is the union-find sweep over the graph. -/
#eval survives (∀ L : List (Edge (Fin 5) (Fin 4)), ∀ grid : List (Fin 4), ∀ a b : Fin 5,
  a ≠ b → sigmaStarForest (kruskal L).1 grid a b = sigmaStar L grid a b) 187

/- SIG-4 control: snapping up instead of down. -/
#eval refuted (∀ L : List (Edge (Fin 5) (Fin 4)), ∀ grid : List (Fin 4), ∀ a b : Fin 5,
  a ≠ b → (bottleneck (kruskal L).1 a b).bind (snapUp grid) = sigmaStar L grid a b) 188

end Attack

end Palace.SigmaStar
