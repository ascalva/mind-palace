module

public import Palace.Scale
public import PalaceTest.Attack
public meta import Palace.Scale
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Scale`

The Plausible attacks and negative controls for the design theorems of `Palace/Scale.lean`, on
exact shadows over ℚ (seeds 350 to 367). The spectral gap is an eigenvalue, which does not run,
so SCL-1 is attacked where the spectrum is rational: on complete bipartite graphs with a uniform
weight, whose Laplacian has eigenvalues `0`, `w·a`, `w·b` and `w·(a + b)`, so the gap is
`w·min(a, b)` exactly; the lazy walk and its time average are matrix arithmetic over ℚ. SCL-2's
discrete twin is attacked on diagonal operators, whose modes are the coordinates. SCL-3 is
attacked on games over three sources with values from a list, the six orderings enumerated; its
controls are the attributions that satisfy three of the four axioms (the equal split, the
uniform average over configurations) and the leave-one-out, which is not efficient. They run when
this module builds (`lake test`).
-/

@[expose] public section

open Matrix Finset Palace.Scale

namespace Palace.Scale.Attack

/-! ## SCL-1 The estimation threshold, on complete bipartite graphs -/

/-- The side of each vertex: `true` on the left. -/
def side (bs : List Bool) (v : Fin 4) : Bool := bs.getD v.val false

/-- The number of vertices on the left. -/
def nLeft (bs : List Bool) : ℕ := (List.finRange 4).countP fun v ↦ side bs v

/-- The complete bipartite graph on the two sides with the uniform weight `w + 1`. -/
def bip (bs : List Bool) (w : ℕ) : Matrix (Fin 4) (Fin 4) ℚ := fun i j ↦
  if side bs i != side bs j then (w + 1 : ℚ) else 0

/-- The spectral gap of its Laplacian, `(w + 1) · min(a, b)`. -/
def gapQ (bs : List Bool) (w : ℕ) : ℚ := (w + 1) * min (nLeft bs : ℚ) (4 - nLeft bs)

/-- The largest eigenvalue, `(w + 1) · 4`. -/
def topQ (w : ℕ) : ℚ := (w + 1) * 4

/-- The lazy step `ε = 1 / λ_max`, so that `ε λ_j ≤ 1` on every eigenvalue. -/
def epsQ (w : ℕ) : ℚ := 1 / topQ w

/-- A field from a list, centered so that it is orthogonal to the constants. -/
def centered (xs : List ℤ) : Fin 4 → ℚ := fun v ↦
  ((xs.getD v.val 0 : ℤ) : ℚ) - (∑ u : Fin 4, ((xs.getD u.val 0 : ℤ) : ℚ)) / 4

/-- A field from a list, as it comes. -/
def raw (xs : List ℤ) : Fin 4 → ℚ := fun v ↦ ((xs.getD v.val 0 : ℤ) : ℚ)

/-- The lazy walk `1 − εL` on the bipartite graph. -/
def lazy (bs : List Bool) (w : ℕ) : Matrix (Fin 4) (Fin 4) ℚ := 1 - epsQ w • lap (bip bs w)

/-- Both sides nonempty: the support is connected and the gap is positive. -/
def bothSides (bs : List Bool) : Bool := 0 < nLeft bs && nLeft bs < 4

/-- `(T ε γ)² ‖avg‖² ≤ ‖x‖²` over a window of `T` steps, for `γ` the rate given. -/
def windowOk (bs : List Bool) (w : ℕ) (x : Fin 4 → ℚ) (γ : ℚ) (T : ℕ) : Bool :=
  let avg := timeAverage (lazy bs w) T x
  decide ((T * (epsQ w * γ)) ^ 2 * (avg ⬝ᵥ avg) ≤ x ⬝ᵥ x)

/-- `‖avg‖² ≤ ((1/T) Σ_{n<T} (1 − εγ)^n)² ‖x‖²`, the sharper form, for `γ` the rate given. -/
def geomOk (bs : List Bool) (w : ℕ) (x : Fin 4 → ℚ) (γ : ℚ) (T : ℕ) : Bool :=
  let avg := timeAverage (lazy bs w) T x
  decide (avg ⬝ᵥ avg ≤ (1 / (T : ℚ) * ∑ n ∈ range T, (1 - epsQ w * γ) ^ n) ^ 2 * (x ⬝ᵥ x))

/- SCL-1: the time average of a centered field over `T` steps has energy at most
`‖x‖² / (T ε γ)²`, with `γ` the gap. -/
#eval survives (∀ bs : List Bool, ∀ w : ℕ, ∀ xs : List ℤ, ∀ T : Fin 8,
  (bothSides bs && 0 < T.val) = true →
    windowOk bs w (centered xs) (gapQ bs w) T = true) 350

/- SCL-1: and at most the geometric sum's square times `‖x‖²`, the form the proof passes
through. -/
#eval survives (∀ bs : List Bool, ∀ w : ℕ, ∀ xs : List ℤ, ∀ T : Fin 8,
  (bothSides bs && 0 < T.val) = true →
    geomOk bs w (centered xs) (gapQ bs w) T = true) 351

/- SCL-1 control: the largest eigenvalue in place of the gap claims a faster average than the
slow modes allow. -/
#eval refuted (∀ bs : List Bool, ∀ w : ℕ, ∀ xs : List ℤ, ∀ T : Fin 8,
  (bothSides bs && 0 < T.val) = true →
    geomOk bs w (centered xs) (topQ w) T = true) 352

/- SCL-1 control: a field with a mean does not average out; its mean is conserved, so the window
bound fails once the window spans more than one relaxation time. -/
#eval refuted (∀ bs : List Bool, ∀ w : ℕ, ∀ xs : List ℤ, ∀ T : Fin 8,
  (bothSides bs && 0 < T.val) = true →
    windowOk bs w (raw xs) (gapQ bs w) T = true) 353

/-! ## SCL-2 Scale separation, discrete, on diagonal operators -/

/-- Eigenvalues from a list. -/
def eig (ds : List ℕ) : Fin 4 → ℚ := fun v ↦ (ds.getD v.val 0 : ℚ)

/-- The largest eigenvalue. -/
def eigMax (ds : List ℕ) : ℚ := (List.finRange 4).foldl (fun m v ↦ max m (eig ds v)) 0

/-- The lazy step `1 / (1 + λ_max)`, so that every multiplier `1 − ε λ_j` lies in `(0, 1]`. -/
def epsD (ds : List ℕ) : ℚ := 1 / (1 + eigMax ds)

/-- The lazy walk on the diagonal operator: multiplier `1 − ε λ_v` on the coordinate `v`. -/
def lazyD (ds : List ℕ) : Matrix (Fin 4) (Fin 4) ℚ := 1 - epsD ds • diagonal (eig ds)

/-- The kept modes, chosen by a list of bits, independently of the eigenvalues: a cut that need
not fall in a gap. -/
def kept (ks : List Bool) (v : Fin 4) : Bool := ks.getD v.val false

/-- The projection onto the kept coordinates. -/
def projD (ks : List Bool) (f : Fin 4 → ℚ) : Fin 4 → ℚ := fun v ↦ if kept ks v then f v else 0

/-- The multiplier of a coordinate, in `(0, 1]`. -/
def mult (ds : List ℕ) (v : Fin 4) : ℚ := 1 - epsD ds * eig ds v

/-- The largest multiplier among the dropped modes (the slowest dropped mode), `0` when none is
dropped. -/
def dropRate (ds : List ℕ) (ks : List Bool) : ℚ :=
  ((List.finRange 4).filter fun v ↦ !kept ks v).foldl (fun m v ↦ max m (mult ds v)) 0

/-- The smallest multiplier among the dropped modes (the fastest dropped mode): the control's
rate. -/
def dropFast (ds : List ℕ) (ks : List Bool) : ℚ :=
  ((List.finRange 4).filter fun v ↦ !kept ks v).foldl (fun m v ↦ min m (mult ds v)) 1

/-- The smallest multiplier among the kept modes (the fastest kept mode), `1` when none is
kept. -/
def keepRate (ds : List ℕ) (ks : List Bool) : ℚ :=
  ((List.finRange 4).filter fun v ↦ kept ks v).foldl (fun m v ↦ min m (mult ds v)) 1

/-- `ρ₂^{2n} ‖N^n (f − Pf)‖² ‖Pf‖² ≤ ρ₁^{2n} ‖f − Pf‖² ‖N^n Pf‖²` with the rates `ρ₁` on the dropped
modes and `ρ₂` on the kept. -/
def sepOk (ds : List ℕ) (ks : List Bool) (f : Fin 4 → ℚ) (ρ₁ ρ₂ : ℚ) (n : ℕ) : Bool :=
  let P := projD ks f
  let D := f - P
  let ND := lazyD ds ^ n *ᵥ D
  let NP := lazyD ds ^ n *ᵥ P
  decide (ρ₂ ^ (2 * n) * (ND ⬝ᵥ ND * (P ⬝ᵥ P)) ≤ ρ₁ ^ (2 * n) * (D ⬝ᵥ D * (NP ⬝ᵥ NP)))

/-- The dropped share strictly falls after `n ≥ 1` steps, when both parts are nonzero. -/
def shareFalls (ds : List ℕ) (ks : List Bool) (f : Fin 4 → ℚ) (n : ℕ) : Bool :=
  let P := projD ks f
  let D := f - P
  let ND := lazyD ds ^ n *ᵥ D
  let NP := lazyD ds ^ n *ᵥ P
  !(0 < n && 0 < D ⬝ᵥ D && 0 < P ⬝ᵥ P) || decide (ND ⬝ᵥ ND * (P ⬝ᵥ P) < D ⬝ᵥ D * (NP ⬝ᵥ NP))

/- SCL-2, discrete: for any set of kept modes, the dropped share falls by at least
`(ρ₁ / ρ₂)²` a step, `ρ₁` the slowest dropped mode's multiplier and `ρ₂` the fastest kept one's. -/
#eval survives (∀ ds : List ℕ, ∀ ks : List Bool, ∀ fs : List ℤ, ∀ n : Fin 5,
  sepOk ds ks (raw fs) (dropRate ds ks) (keepRate ds ks) n = true) 354

/- SCL-2 control: without a gap there is no such time. The share "always falls" is refuted where
the eigenvalues straddling the cut coincide: then it does not move. -/
#eval refuted (∀ ds : List ℕ, ∀ ks : List Bool, ∀ fs : List ℤ, ∀ n : Fin 5,
  shareFalls ds ks (raw fs) n = true) 355

/- SCL-2 control: the fastest dropped mode's rate in place of the slowest's claims a separation
the slow dropped mode does not deliver. -/
#eval refuted (∀ ds : List ℕ, ∀ ks : List Bool, ∀ fs : List ℤ, ∀ n : Fin 5,
  sepOk ds ks (raw fs) (dropFast ds ks) (keepRate ds ks) n = true) 356

/-! ## SCL-3 Attribution, on three sources -/

/-- The index of a configuration, `Σ_{i ∈ S} 2^i`. -/
def idx (S : Finset (Fin 3)) : ℕ := ∑ i ∈ S, 2 ^ i.val

/-- A score from a list, one value per configuration. -/
def game (vs : List ℤ) : Finset (Fin 3) → ℚ := fun S ↦ ((vs.getD (idx S) 0 : ℤ) : ℚ)

/-- A score that depends on the size of the configuration only: every source symmetric. -/
def symGame (vs : List ℤ) : Finset (Fin 3) → ℚ := fun S ↦ ((vs.getD S.card 0 : ℤ) : ℚ)

/-- A score with the source `0` null. -/
def nullGame (vs : List ℤ) : Finset (Fin 3) → ℚ := fun S ↦ game vs (S.erase 0)

/-- An additive score: each source adds its own value whatever the others. -/
def addGame (as : List ℤ) : Finset (Fin 3) → ℚ := fun S ↦ ∑ i ∈ S, ((as.getD i.val 0 : ℤ) : ℚ)

/-- The equal split: efficient and symmetric, blind to who contributes. -/
def equalSplit (v : Finset (Fin 3) → ℚ) (_ : Fin 3) : ℚ := (v univ - v ∅) / 3

/-- The uniform average of the marginal contributions over every configuration of the others
(the Banzhaf weights): symmetric, null-respecting and additive, not efficient. -/
def uniformAvg (v : Finset (Fin 3) → ℚ) (i : Fin 3) : ℚ :=
  (∑ S ∈ (univ.erase i).powerset, marginal v S i) / 4

/-- The dividend formula without its `1 / |T|`. -/
def dividendsUnsplit (v : Finset (Fin 3) → ℚ) (i : Fin 3) : ℚ :=
  ∑ T ∈ univ.filter (fun T ↦ i ∈ T), harsanyi v T

/- SCL-3: efficiency. -/
#eval survives (∀ vs : List ℤ,
  ∑ i, shapley (game vs) i = game vs univ - game vs ∅) 357

/- SCL-3: additivity. -/
#eval survives (∀ vs ws : List ℤ, ∀ i : Fin 3,
  shapley (game vs + game ws) i = shapley (game vs) i + shapley (game ws) i) 358

/- SCL-3: a null source is attributed nothing. -/
#eval survives (∀ vs : List ℤ, shapley (nullGame vs) 0 = 0) 359

/- SCL-3: symmetric sources are attributed the same. -/
#eval survives (∀ vs : List ℤ,
  shapley (symGame vs) 0 = shapley (symGame vs) 1 ∧ shapley (symGame vs) 1 = shapley (symGame vs) 2)
  360

/- SCL-3: every score is the combination of the unanimity games with its Harsanyi dividends. -/
#eval survives (∀ vs : List ℤ,
  decide (∀ S : Finset (Fin 3), ∑ T, harsanyi (game vs) T * unanimity T S = game vs S) = true) 361

/- SCL-3: the Shapley value is the dividend formula `Σ_{T ∋ i} c_T / |T|`. -/
#eval survives (∀ vs : List ℤ, ∀ i : Fin 3,
  shapley (game vs) i = ∑ T ∈ univ.filter (fun T ↦ i ∈ T), harsanyi (game vs) T / T.card) 362

/- SCL-3: leave-one-out agrees with the Shapley value on an additive score. -/
#eval survives (∀ as : List ℤ, ∀ i : Fin 3, loo (addGame as) i = shapley (addGame as) i) 363

/- SCL-3 control: the equal split is efficient and symmetric and is not the Shapley value: it
pays a null source. -/
#eval refuted (∀ vs : List ℤ, ∀ i : Fin 3, equalSplit (game vs) i = shapley (game vs) i) 364

/- SCL-3 control: leave-one-out is not efficient. -/
#eval refuted (∀ vs : List ℤ, ∑ i, loo (game vs) i = game vs univ - game vs ∅) 365

/- SCL-3 control: the uniform average over configurations is symmetric, null-respecting and
additive, and is not the Shapley value: it is not efficient. -/
#eval refuted (∀ vs : List ℤ, ∀ i : Fin 3, uniformAvg (game vs) i = shapley (game vs) i) 366

/- SCL-3 control: the dividends without their `1 / |T|` over-attribute shared value. -/
#eval refuted (∀ vs : List ℤ, ∀ i : Fin 3, dividendsUnsplit (game vs) i = shapley (game vs) i) 367

end Palace.Scale.Attack
