module

public import Palace.Spectral
public import Mathlib.Testing.Plausible.Sampleable
public import PalaceTest.Laplacian
public meta import Palace.Spectral
public meta import Mathlib.Testing.Plausible.Sampleable
public meta import PalaceTest.Laplacian

/-!
# Attacks on `Palace.Spectral`

The Plausible attacks and negative controls for the laws of `Palace/Spectral.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Matrix Finset Unitary

namespace Palace

/-! ## Attacks

`L_sym` and `L⁺` have no executable form here: one needs square roots, the other a spectral
decomposition over ℝ. Their laws are attacked where they are exact. `L_sym`'s rest on two
identities over any commutative ring, attacked over ℚ on `Fin 5` with arbitrary weights, scalings
and vectors. `L⁺`'s are attacked on an exact shadow: for a rational Laplacian with nonnegative
weights, `(L + P)⁻¹ − P` with `P` the orthogonal projector onto the component indicators. The
attack checks all four Penrose equations on it, so whenever it passes, the shadow is the
Moore–Penrose inverse itself.
-/

namespace Attack

/-- A 5 × 5 rational matrix stored as rows, for the shadow: every entry is computed once. -/
abbrev Rows := Array (Array ℚ)

/-- Store a matrix's entries. -/
def rows (M : Matrix (Fin 5) (Fin 5) ℚ) : Rows :=
  Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦ M i j

/-- Read an entry. -/
def entry (t : Rows) (i j : ℕ) : ℚ := (t[i]!)[j]!

/-- Entrywise sum on stored rows. -/
def addR (x y : Rows) : Rows := Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦
  entry x i j + entry y i j

/-- Entrywise difference on stored rows. -/
def subR (x y : Rows) : Rows := Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦
  entry x i j - entry y i j

/-- Transpose on stored rows. -/
def transR (x : Rows) : Rows := Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦ entry x j i

/-- The matrix product on stored rows. -/
def mulR (x y : Rows) : Rows := Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦
  ∑ k : Fin 5, entry x i k * entry y k j

/-- Gauss–Jordan elimination with row swaps: the inverse, or `none` when singular. -/
def invR (m : Rows) : Option Rows := Id.run do
  let mut a := m
  let mut b := rows 1
  for c in List.range 5 do
    let some r := (List.range 5).find? (fun r ↦ decide (c ≤ r) && entry a r c != 0)
      | return none
    let (ar, ac, br, bc) := (a[r]!, a[c]!, b[r]!, b[c]!)
    a := (a.setIfInBounds c ar).setIfInBounds r ac
    b := (b.setIfInBounds c br).setIfInBounds r bc
    let p := entry a c c
    a := a.setIfInBounds c (a[c]!.map (· / p))
    b := b.setIfInBounds c (b[c]!.map (· / p))
    for r' in List.range 5 do
      if r' != c then
        let f := entry a r' c
        a := a.setIfInBounds r' (Array.ofFn fun j : Fin 5 ↦ entry a r' j - f * entry a c j)
        b := b.setIfInBounds r' (Array.ofFn fun j : Fin 5 ↦ entry b r' j - f * entry b c j)
  return some b

/-- Warshall's closure: `j` is reachable from `i` along edges of nonzero weight. -/
def reach (A : Matrix (Fin 5) (Fin 5) ℚ) : Array (Array Bool) := Id.run do
  let mut r : Array (Array Bool) :=
    Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦ decide (i = j) || A i j != 0
  for k in List.range 5 do
    r := Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦
      (r[i.val]!)[j.val]! || ((r[i.val]!)[k]! && (r[k]!)[j.val]!)
  return r

/-- The orthogonal projector onto the component indicators: `1/|C|` on each component's block. -/
def projR (A : Matrix (Fin 5) (Fin 5) ℚ) : Rows :=
  let r := reach A
  Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦
    if (r[i.val]!)[j.val]! then 1 / ((r[i.val]!).count true : ℚ) else 0

/-- The laws of `L⁺` on the shadow `(L + P)⁻¹ − P`: the four Penrose equations (`L` and the shadow
commute and both are symmetric), `xᵀL⁺x ≥ 0`, and `R_eff ≥ 0` for every pair. -/
def pinvLaws (A : Matrix (Fin 5) (Fin 5) ℚ) (x : Fin 5 → ℚ) : Bool :=
  let L := rows (lap A)
  let P := projR A
  match invR (addR L P) with
  | none => false
  | some Y =>
    let X := subR Y P
    mulR (mulR L X) L == L && mulR (mulR X L) X == X && mulR L X == mulR X L &&
      transR X == X && decide (0 ≤ ∑ i : Fin 5, x i * ∑ j : Fin 5, entry X i j * x j) &&
      (List.range 5).all fun i ↦ (List.range 5).all fun j ↦
        decide (0 ≤ entry X i i + entry X j j - 2 * entry X i j)

/-- The connected-graph formula `L⁺ = (L + J/n)⁻¹ − J/n`, checked against Penrose's first two
equations on any graph. -/
def connectedFormulaLaws (A : Matrix (Fin 5) (Fin 5) ℚ) : Bool :=
  let L := rows (lap A)
  let J : Rows := Array.ofFn fun _ : Fin 5 ↦ Array.ofFn fun _ : Fin 5 ↦ (1 / 5 : ℚ)
  match invR (addR L J) with
  | none => false
  | some Y =>
    let X := subR Y J
    mulR (mulR L X) L == L && mulR (mulR X L) X == X

/- `L_sym`'s lower identity, for every `A`, scaling `s` and vector `x`. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ ss xs : List ℤ,
  vec xs ⬝ᵥ ((1 - diagonal (vec ss) * ofArcs es * diagonal (vec ss)) *ᵥ vec xs) =
    ∑ i, (1 - vec ss i ^ 2 * degree (ofArcs es) i) * vec xs i ^ 2 +
      (vec ss * vec xs) ⬝ᵥ (lap (ofArcs es) *ᵥ (vec ss * vec xs))) 41

/- Control: the identity without its diagonal remainder. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ ss xs : List ℤ,
  vec xs ⬝ᵥ ((1 - diagonal (vec ss) * ofArcs es * diagonal (vec ss)) *ᵥ vec xs) =
    (vec ss * vec xs) ⬝ᵥ (lap (ofArcs es) *ᵥ (vec ss * vec xs))) 42

/- `L_sym`'s upper identity, through the signless Laplacian. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ ss xs : List ℤ,
  vec xs ⬝ᵥ ((1 + diagonal (vec ss) * ofArcs es * diagonal (vec ss)) *ᵥ vec xs) =
    ∑ i, (1 - vec ss i ^ 2 * degree (ofArcs es) i) * vec xs i ^ 2 +
      (vec ss * vec xs) ⬝ᵥ (signless (ofArcs es) *ᵥ (vec ss * vec xs))) 43

/- The signless Laplacian is positive semidefinite on symmetric nonnegative weights. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ xs : List ℤ,
  0 ≤ vec xs ⬝ᵥ (signless (ofEdges (nonneg es)) *ᵥ vec xs)) 44

/- Control: weights of either sign. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ xs : List ℤ,
  0 ≤ vec xs ⬝ᵥ (signless (ofEdges es) *ᵥ vec xs)) 45

/- `L⁺` on the exact shadow: Penrose, symmetry, positive semidefinite, `R_eff ≥ 0`. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ xs : List ℤ,
  pinvLaws (ofEdges (nonneg es)) (vec xs) = true) 46

/- Control: the connected-graph formula applied to every graph (CND-1's "per component"). -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℕ),
  connectedFormulaLaws (ofEdges (nonneg es)) = true) 47

end Attack

end Palace
