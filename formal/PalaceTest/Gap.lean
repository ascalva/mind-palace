module

public import Palace.Gap
public import Mathlib.Testing.Plausible.Sampleable
public import PalaceTest.Attack
public meta import Palace.Gap
public meta import Mathlib.Testing.Plausible.Sampleable
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Gap`

Weyl's counts have an exact shadow: for a symmetric `3 × 3` matrix over `ℚ`, the number of
eigenvalues at most `t` is `3` minus the number of positive eigenvalues of `A − t`, which Jacobi's
rule reads off the signs of its leading principal minors when none is zero (Sylvester's law of
inertia). The attack draws `A` and a perturbation `D` with small integer entries, bounds the
perturbation by Gershgorin's `ε = maxᵢ Σⱼ |Dᵢⱼ|` (at least `‖D‖`), and checks both of Weyl's
counts at a random `t`; draws where a minor vanishes are discarded. The control drops `ε`.
-/

@[expose] public section

namespace Palace.Gap

namespace Attack

open Plausible

/-- A symmetric `3 × 3` matrix over `ℚ`, by its six entries. -/
structure Sym where
  a : ℚ
  b : ℚ
  c : ℚ
  d : ℚ
  e : ℚ
  f : ℚ
deriving Repr

/-- The entries `(i, j)` of `[[a, d, e], [d, b, f], [e, f, c]]`. -/
def Sym.minors (m : Sym) (t : ℚ) : ℚ × ℚ × ℚ :=
  let a := m.a - t
  let b := m.b - t
  let c := m.c - t
  (a, a * b - m.d ^ 2, a * (b * c - m.f ^ 2) - m.d * (m.d * c - m.f * m.e) +
    m.e * (m.d * m.f - b * m.e))

/-- Whether Jacobi's rule applies at `t`: no leading principal minor of `A − t` is zero. -/
def Sym.regular (m : Sym) (t : ℚ) : Bool :=
  let (p, q, r) := m.minors t
  p != 0 && q != 0 && r != 0

/-- The number of negative eigenvalues of `A − t`: the sign changes in `1, d₁, d₂, d₃`. -/
def Sym.neg (m : Sym) (t : ℚ) : ℕ :=
  let (p, q, r) := m.minors t
  let ch (x y : ℚ) : ℕ := if (x < 0) != (y < 0) then 1 else 0
  ch 1 p + ch p q + ch q r

/-- The number of eigenvalues at most `t`, for `t` where the rule applies: those below `t`. -/
def Sym.count (m : Sym) (t : ℚ) : ℕ := m.neg t

def Sym.add (m n : Sym) : Sym := ⟨m.a + n.a, m.b + n.b, m.c + n.c, m.d + n.d, m.e + n.e, m.f + n.f⟩

/-- Gershgorin's bound on the spectral radius: `maxᵢ Σⱼ |Dᵢⱼ|`. -/
def Sym.gersh (m : Sym) : ℚ :=
  max (|m.a| + |m.d| + |m.e|) (max (|m.d| + |m.b| + |m.f|) (|m.e| + |m.f| + |m.c|))

instance : Shrinkable Sym := ⟨fun _ ↦ []⟩

def genEntry (r : ℕ) : Gen ℚ := do
  return ((← Gen.choose Nat 0 (2 * r) (by omega)).1 : ℚ) - r

instance : Arbitrary Sym where
  arbitrary := return ⟨← genEntry 6, ← genEntry 6, ← genEntry 6, ← genEntry 6, ← genEntry 6,
    ← genEntry 6⟩

/-- A matrix, a perturbation of small entries, and a threshold in halves. -/
structure Case where
  A : Sym
  D : Sym
  t : ℚ
deriving Repr

instance : Shrinkable Case := ⟨fun _ ↦ []⟩

instance : Arbitrary Case where
  arbitrary := do
    let A ← Arbitrary.arbitrary
    let D : Sym := ⟨← genEntry 1, ← genEntry 1, ← genEntry 1, ← genEntry 1, ← genEntry 1,
      ← genEntry 1⟩
    let t := (((← Gen.choose Nat 0 40 (by omega)).1 : ℚ) - 20) / 2
    return ⟨A, D, t⟩

/-- Weyl's counts at `t` with slack `s`: `N_A(t − s) ≤ N_{A+D}(t) ≤ N_A(t + s)`. -/
def Case.weyl (k : Case) (s : ℚ) : Bool :=
  let B := k.A.add k.D
  decide (k.A.count (k.t - s) ≤ B.count k.t) && decide (B.count k.t ≤ k.A.count (k.t + s))

def Case.regular (k : Case) (s : ℚ) : Bool :=
  k.A.regular (k.t - s) && k.A.regular (k.t + s) && (k.A.add k.D).regular k.t

/- SPC-3, Weyl's inequality counted, with Gershgorin's `ε`. -/
#eval survives (∀ k : Case, k.regular k.D.gersh = true → k.weyl k.D.gersh = true) 297

/- Control: without the slack. -/
#eval refuted (∀ k : Case, k.regular 0 = true → k.weyl 0 = true) 298

end Attack

end Palace.Gap
