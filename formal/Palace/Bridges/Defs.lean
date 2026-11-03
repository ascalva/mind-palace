module

public import Mathlib.Order.Defs.Unbundled
public import Palace.Clock.Defs
public import Palace.Hodge.Defs
public import Palace.Laplacian.Defs
public import Palace.Plane.Defs
public import Palace.Scope.Defs
public import Palace.Spectral.Defs

/-!
# Bridges between the families, the definitions

The two definitions the bridges need beyond the families' own: reachability as a preorder, and
scope's refinement step as a relation. With `Spec/Bridges.lean` they are what a reader checks
against `docs/LAWS.md`: `lake comparator` ensures the library proves exactly the statements there,
so no other file can change what is proved.
-/

@[expose] public section

open Relation

namespace Palace.Bridges

/-- `≼`, reachability along the generators `g`, as a preorder. -/
@[instance_reducible]
def reach {E : Type*} (g : E → E → Prop) : Preorder E where
  le := ReflTransGen g
  le_refl _ := .refl
  le_trans _ _ _ := .trans

/-- Scope's refinement step: `c` refines `p`, `exhaust` aside (the steps `IsDown` closes under). -/
def Refines (c p : CQ.Stratum) : Prop := c ≠ .exhaust ∧ c.parent = some p

end Palace.Bridges
