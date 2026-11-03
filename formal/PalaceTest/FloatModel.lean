module

public import Palace.FloatModel
public import PalaceTest.Roundoff
public meta import Palace.FloatModel
public meta import PalaceTest.Roundoff

/-!
# Attacks on `Palace.FloatModel`

The Plausible attacks and negative controls for the laws of `Palace/FloatModel.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Float.Model (UnpackedFloat Format totalExponent)
open Float.Model.UnpackedFloat (ExtendedMantissa Accuracy Sign)

namespace Palace.Binary64

/-! ## Attacks: the compiled operators against the logical model

The theorems above are about `Float`'s logical model, which defines `a + b`. A compiled program
runs C's `+` instead (`@[extern "lean_float_add"]`). Lean trusts the two to agree, and every
theorem here about a running program inherits that trust. These attacks test it on this machine:
the operands `Palace/Binary64.lean` draws (ties, carries, subnormals) go through the C operator and
through the model's own Lean code, which nothing replaces at compile time, and must give the same
bits. The control compares `+` with the model's `-`.
-/

namespace Attack

open Palace.Binary64.Attack (Pair)

/-- The compiled operator `op` and the model's `model` give the same bits. -/
def sameBits (op : Float → Float → Float) (model : Float.Model → Float.Model → Float.Model)
    (p : Pair) : Bool :=
  let a := Float.ofBits p.a
  let b := Float.ofBits p.b
  (op a b).toBits == (Float.ofModel (model a.toModel b.toModel)).toBits

/- `+`, `*` and `/` compiled agree with the logical model. -/
#eval survives (∀ p : Pair, sameBits (· + ·) Float.Model.add p = true) 141
#eval survives (∀ p : Pair, sameBits (· * ·) Float.Model.mul p = true) 142
#eval survives (∀ p : Pair, sameBits (· / ·) Float.Model.div p = true) 143

/- Control: `+` against the model's `-`. -/
#eval refuted (∀ p : Pair, sameBits (· + ·) Float.Model.sub p = true) 144

end Attack

end Palace.Binary64
