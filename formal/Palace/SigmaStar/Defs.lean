module

public import Mathlib.Data.Fintype.Card
public import Mathlib.Logic.Relation
public import Mathlib.Order.Prod.Lex.Basic

/-!
# σ*, the abstraction ultrametric: SIG-1 to SIG-4, the definitions

The definitions the laws of `Palace/SigmaStar.lean` are stated over. With `Spec/SigmaStar.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

open Relation

namespace Palace.SigmaStar

variable {V W : Type*}

/-- An edge of the σ-graph, `(u, v, w)`: endpoints and cosine (`edges` in
`build_max_spanning_tree`). -/
abbrev Edge (V W : Type*) := V × V × W

/-- `G_σ`'s adjacency: an edge `(u, v, w)` of `L` with `σ ≤ w`. -/
def Adj [LE W] (L : List (Edge V W)) (σ : W) (a b : V) : Prop := ∃ w, (a, b, w) ∈ L ∧ σ ≤ w

/-- `a ∼ b` in `G_σ`: the components of the threshold graph. -/
def Conn [LE W] (L : List (Edge V W)) (σ : W) : V → V → Prop := EqvGen (Adj L σ)

/-- The components of the edges in `F`, whatever their weights. -/
def Linked (F : List (Edge V W)) : V → V → Prop := EqvGen fun a b ↦ ∃ w, (a, b, w) ∈ F

/-- Union, on component labels: `v`'s class takes `u`'s label. -/
def merge [DecidableEq V] (lab : V → V) (u v : V) : V → V :=
  fun x ↦ if lab x = lab v then lab u else lab x

/-- One pass of Kruskal's loop: keep the edge, and merge its endpoints' classes, iff they carry
different labels (`ri != rj`). -/
def step [DecidableEq V] (st : List (Edge V W) × (V → V)) (e : Edge V W) :
    List (Edge V W) × (V → V) :=
  if st.2 e.1 = st.2 e.2.1 then st else (e :: st.1, merge st.2 e.1 e.2.1)

/-- Kruskal's order, `key=(-w, i, j)`: descending weight, ties by the endpoints. -/
def before [LinearOrder V] [LinearOrder W] (e f : Edge V W) : Bool :=
  decide (toLex (OrderDual.toDual e.2.2, toLex (e.1, e.2.1)) ≤
    toLex (OrderDual.toDual f.2.2, toLex (f.1, f.2.1)))

/-- `build_max_spanning_tree`: the edges in Kruskal's order, then the loop from singletons. The
kept edges, the maximum spanning forest, and the final labels. -/
def kruskal [LinearOrder V] [LinearOrder W] (L : List (Edge V W)) : List (Edge V W) × (V → V) :=
  (L.mergeSort before).foldl step ([], id)

/-- `a ∼ b` in `G_σ`, computed: the labels the loop leaves over `G_σ`'s edges agree (the
union-find of `_sigma_star_via_union_find`, at one threshold). -/
def connected [DecidableEq V] [LinearOrder W] (L : List (Edge V W)) (σ : W) (a b : V) : Bool :=
  ((L.filter fun e ↦ σ ≤ e.2.2).foldl step ([], id)).2 a ==
    ((L.filter fun e ↦ σ ≤ e.2.2).foldl step ([], id)).2 b

/-- σ*(a, b) against the grid: the largest grid point at which `a ∼ b` in `G_σ`, `none` if there
is none (`_sigma_star_via_union_find`, the test suite's independent oracle). -/
def sigmaStar [DecidableEq V] [LinearOrder W] (L : List (Edge V W)) (grid : List W) (a b : V) :
    Option W :=
  (grid.filter (connected L · a b)).max?

/-- `_tree_path_bottleneck` on a forest: the largest of its weights at which `a ∼ b` in it,
`none` across components. -/
def bottleneck [DecidableEq V] [LinearOrder W] (F : List (Edge V W)) (a b : V) : Option W :=
  ((F.map (·.2.2)).filter (connected F · a b)).max?

/-- `_grid_snap`: the largest grid point at or below `x`. -/
def snap [LinearOrder W] (grid : List W) (x : W) : Option W := (grid.filter (· ≤ x)).max?

/-- `sigma_star`: the forest's bottleneck between `a` and `b`, snapped to the grid. A vertex's
path to itself has no edge, so its bottleneck is `+∞`, which snaps to the strictest grid point. -/
def sigmaStarForest [DecidableEq V] [LinearOrder W] (F : List (Edge V W)) (grid : List W)
    (a b : V) : Option W :=
  if a = b then grid.max? else (bottleneck F a b).bind (snap grid)

end Palace.SigmaStar
