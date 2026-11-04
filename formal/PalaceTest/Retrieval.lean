module

public import Palace.Retrieval
public import PalaceTest.Laplacian
public import PalaceTest.Spectral
public meta import Palace.Retrieval
public meta import PalaceTest.Laplacian
public meta import PalaceTest.Spectral

/-!
# Attacks on `Palace.Retrieval`

The Plausible attacks and negative controls for the retrieval curve of `Palace/Retrieval.lean`.
They run when this module builds (`lake test`); the library itself runs no code at build time.

The curve's powers, logarithms and square roots do not run, but at `β = 1` the killed walk is
`z (w_ij / d_i) w_ij`, rational for rational weights, so its laws are attacked exactly there: `Z`
and `G` by Gauss–Jordan elimination over ℚ (the shadow of the `L⁺` attacks), `z = ½` as the code's
`γ`, on `Fin 5` with weights in `{0, ¼, ½, ¾, 1}`. RSP-3's identity is attacked squared, where it
has no root: `(z_ij / z_jj)(z_ji / z_ii) = G_ij² / (G_ii G_jj)`.
-/

@[expose] public section

open Matrix Finset Palace.Attack

namespace Palace.Retrieval.Attack

/-- Symmetric weights on `Fin 5` in `{0, ¼, ½, ¾, 1}`, no loops: one list entry per unordered
pair, `dflt` past its end (`0` gives sparse graphs, `1` complete ones). -/
def wq (dflt : ℕ) (bs : List ℕ) : Matrix (Fin 5) (Fin 5) ℚ := fun i j ↦
  if i = j then 0 else ((bs.getD (5 * min i.val j.val + max i.val j.val) dflt % 5 : ℕ) : ℚ) / 4

/-- The killed walk at `β = 1`, `z (w_ij / d_i) w_ij`. -/
def killedQ (w : Matrix (Fin 5) (Fin 5) ℚ) (z : ℚ) : Matrix (Fin 5) (Fin 5) ℚ :=
  fun i j ↦ z * (w i j / ∑ k, w i k) * w i j

/-- `Z = (I − W)⁻¹`, or `none` when singular. -/
def zq (w : Matrix (Fin 5) (Fin 5) ℚ) (z : ℚ) : Option Rows := invR (rows (1 - killedQ w z))

/-- `D − z w∘w`, the matrix whose inverse is the kernel at `β = 1`. -/
def nq (w : Matrix (Fin 5) (Fin 5) ℚ) (z : ℚ) : Matrix (Fin 5) (Fin 5) ℚ :=
  diagonal (fun i ↦ ∑ k, w i k) - z • (of fun i j ↦ w i j * w i j : Matrix (Fin 5) (Fin 5) ℚ)

/-- `G = (D − z w∘w)⁻¹`, or `none` when singular. -/
def gq (w : Matrix (Fin 5) (Fin 5) ℚ) (z : ℚ) : Option Rows := invR (rows (nq w z))

/-- Every degree is positive. -/
def degPos (w : Matrix (Fin 5) (Fin 5) ℚ) : Bool :=
  (List.finRange 5).all fun i ↦ decide (0 < ∑ k, w i k)

/-- A check at every pair. -/
def allPairs (p : Fin 5 → Fin 5 → Bool) : Bool :=
  (List.finRange 5).all fun i ↦ (List.finRange 5).all fun j ↦ p i j

/-! ### Attacks -/

/- RSP-1: `I − W` is invertible at `z = ½`, `Z ≥ 0`, `z_ii ≥ 1`, and `z_ij > 0` exactly when `j`
is reachable from `i`. -/
#eval survives (∀ bs : List ℕ, (match zq (wq 0 bs) (1 / 2) with
  | some Z => allPairs fun i j ↦ decide (0 ≤ entry Z i j) && decide (i = j → 1 ≤ entry Z i j) &&
      (decide (0 < entry Z i j) == ((reach (wq 0 bs))[i.val]!)[j.val]!)
  | none => false) = true) 207

/- RSP-1 control: without the killing, `z = 1`, a component whose weights are all `1` makes
`I − W` singular: the γ-ceiling is load-bearing. -/
#eval refuted (∀ bs : List ℕ, (zq (wq 0 bs) 1).isSome = true) 208

/- RSP-2: `D − z w∘w` is positive definite when every degree is positive. -/
#eval survives (∀ bs : List ℕ, ∀ xs : List ℤ, degPos (wq 1 bs) = true → vec xs ≠ 0 →
  0 < vec xs ⬝ᵥ (nq (wq 1 bs) (1 / 2) *ᵥ vec xs)) 209

/- RSP-2: `Z = G D`, every degree positive. -/
#eval survives (∀ bs : List ℕ, degPos (wq 1 bs) = true →
  (match zq (wq 1 bs) (1 / 2), gq (wq 1 bs) (1 / 2) with
  | some Z, some G => allPairs fun i j ↦ entry Z i j == entry G i j * ∑ k, wq 1 bs j k
  | _, _ => false) = true) 210

/- RSP-2 control: the degrees on the other side, `Z = D G`. -/
#eval refuted (∀ bs : List ℕ, degPos (wq 1 bs) = true →
  (match zq (wq 1 bs) (1 / 2), gq (wq 1 bs) (1 / 2) with
  | some Z, some G => allPairs fun i j ↦ entry Z i j == (∑ k, wq 1 bs i k) * entry G i j
  | _, _ => false) = true) 211

/- RSP-3, squared: `z_ij z_ji G_ii G_jj = G_ij² z_ii z_jj`, every degree positive. -/
#eval survives (∀ bs : List ℕ, degPos (wq 1 bs) = true →
  (match zq (wq 1 bs) (1 / 2), gq (wq 1 bs) (1 / 2) with
  | some Z, some G => allPairs fun i j ↦
      entry Z i j * entry Z j i * (entry G i i * entry G j j) ==
        entry G i j ^ 2 * (entry Z i i * entry Z j j)
  | _, _ => false) = true) 212

/- RSP-3 control: the free energy one way, unsymmetrized, is not the normalized kernel. -/
#eval refuted (∀ bs : List ℕ, degPos (wq 1 bs) = true →
  (match zq (wq 1 bs) (1 / 2), gq (wq 1 bs) (1 / 2) with
  | some Z, some G => allPairs fun i j ↦
      entry Z i j ^ 2 * (entry G i i * entry G j j) == entry G i j ^ 2 * entry Z j j ^ 2
  | _, _ => false) = true) 213

/- RSP-4: first passage `z_ij ≤ z_jj` and the path product `z_ij z_jk ≤ z_ik z_jj`. -/
#eval survives (∀ bs : List ℕ, (match zq (wq 0 bs) (1 / 2) with
  | some Z => allPairs fun i j ↦ decide (entry Z i j ≤ entry Z j j) &&
      (List.finRange 5).all fun k ↦ decide (entry Z i j * entry Z j k ≤ entry Z i k * entry Z j j)
  | none => false) = true) 214

/- RSP-4 control: without `z_jj`, the unnormalized `−log z_ij` breaks the triangle inequality. -/
#eval refuted (∀ bs : List ℕ, (match zq (wq 0 bs) (1 / 2) with
  | some Z => allPairs fun i j ↦
      (List.finRange 5).all fun k ↦ decide (entry Z i j * entry Z j k ≤ entry Z i k)
  | none => false) = true) 215

end Palace.Retrieval.Attack
