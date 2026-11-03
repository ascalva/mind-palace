module

public import Palace.SigmaStar.Defs

/-!
# σ*, the abstraction ultrametric: SIG-1 to SIG-4, the statements

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
The statements are for distinct vertices: `sigma_star(forest, a, a)` raises `ValueError`, the
minimum of an empty path, and `pairwise_sigma_star`, its one caller, asks only distinct pairs.

These are the laws of `Palace/SigmaStar.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

open Relation

namespace Palace.SigmaStar

variable {V W : Type*}

section Threshold

variable [LinearOrder W]

/-- **SIG-3** The ultrametric inequality at the level of thresholds: two links that hold at `x`
and at `y` compose at `min x y`. -/
theorem Conn.ultra {L : List (Edge V W)} {x y : W} {a b c : V} (hab : Conn L x a b)
    (hbc : Conn L y b c) : Conn L (min x y) a c :=
  sorry

end Threshold

section Connected

variable [DecidableEq V] [LinearOrder W]

/-- **SIG-4** The labels decide `G_σ`'s components: σ* is computed through them. -/
theorem connected_iff (L : List (Edge V W)) (σ : W) (a b : V) :
    connected L σ a b = true ↔ Conn L σ a b :=
  sorry

/-- **SIG-3** σ* is symmetric. -/
theorem sigmaStar_symm (L : List (Edge V W)) (grid : List W) (a b : V) :
    sigmaStar L grid a b = sigmaStar L grid b a :=
  sorry

/-- **SIG-3** σ* is an ultrametric: `σ*(a, c) ≥ min(σ*(a, b), σ*(b, c))`, the link from `a` to `c`
at least as strict as the weaker of the two through `b`. -/
theorem sigmaStar_ultra {L : List (Edge V W)} {grid : List W} {a b c : V} {x y : W}
    (hab : sigmaStar L grid a b = some x) (hbc : sigmaStar L grid b c = some y) :
    ∃ z, sigmaStar L grid a c = some z ∧ min x y ≤ z :=
  sorry

/-- **SIG-4** σ* is `none` exactly when the pair shares no component at any grid point, so, the
threshold graphs shrinking as `σ` rises, exactly when it shares none at the loosest. -/
theorem sigmaStar_eq_none_iff (L : List (Edge V W)) (grid : List W) (a b : V) :
    sigmaStar L grid a b = none ↔ ∀ g ∈ grid, ¬Conn L g a b :=
  sorry

end Connected

section Kruskal

variable [LinearOrder V] [LinearOrder W]

/-- **SIG-1** One maximum spanning forest realizes every threshold: at every `σ`, `a ∼ b` in the
forest's `G_σ` exactly when `a ∼ b` in the graph's. So every pairwise σ* can be read off the one
forest (`build_max_spanning_tree`, built once per cut). -/
theorem conn_kruskal_iff (L : List (Edge V W)) (σ : W) (a b : V) :
    Conn (kruskal L).1 σ a b ↔ Conn L σ a b :=
  sorry

/-- **SIG-2** The final labels are the components of what the loop kept. -/
theorem kruskal_label_eq_iff (L : List (Edge V W)) (a b : V) :
    (kruskal L).2 a = (kruskal L).2 b ↔ Linked (kruskal L).1 a b :=
  sorry

/-- **SIG-2** What the loop keeps is a forest: its edges and its components together number the
vertices, `|F| + c(F) = |V|`, so no kept edge closes a cycle. -/
theorem kruskal_card [Fintype V] (L : List (Edge V W)) :
    (kruskal L).1.length + (Finset.univ.image (kruskal L).2).card = Fintype.card V :=
  sorry

/-- **SIG-4** σ* read off the forest is the union-find sweep over the graph: for two distinct
vertices, the forest's bottleneck snapped to the grid is the largest grid point at which they share
a component of `G_σ`, and `none` when there is none. -/
theorem sigmaStarForest_kruskal (L : List (Edge V W)) (grid : List W) {a b : V} (hab : a ≠ b) :
    sigmaStarForest (kruskal L).1 grid a b = sigmaStar L grid a b :=
  sorry

end Kruskal

end Palace.SigmaStar
