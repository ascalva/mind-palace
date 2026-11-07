module

public import Palace.Dynamics
public import PalaceTest.Retrieval
public meta import Palace.Dynamics
public meta import PalaceTest.Retrieval

/-!
# Attacks on `Palace.Dynamics`

The Plausible attacks and negative controls for the design theorems of `Palace/Dynamics.lean`,
on exact shadows over ℚ (seeds 330 to 344): nonnegative matrices on `Fin 5` whose rows sum to
less than `1`, their walk sums by Gauss–Jordan elimination against the Neumann partial sums;
HodgeRank on the ten edges of `K₅` with weights in `{0, ¼, ½, ¾, 1}`, the pseudo-inverse by the
shadow `(L + P)⁻¹ − P`; the quotient of a Laplacian by a random partition into three blocks; the
ripple carried across a permutation and across a merge; the velocity of a value over a window of
cuts; and RSP-5 read block by block at `β = 1`. The heat kernel and the modes are exponentials and
eigenvectors, which do not run; their laws are proved, not attacked. They run when this module
builds (`lake test`).
-/

@[expose] public section

open Matrix Finset Palace.Attack Palace.Retrieval.Attack

namespace Palace.Dynamics.Attack

/-! ## DYN-2 The Neumann resolvent -/

/-- A nonnegative matrix on `Fin 5` whose rows sum to less than `1`: `a_ij / (1 + Σ_j a_ij)`. -/
def subq (as : List ℕ) : Matrix (Fin 5) (Fin 5) ℚ := fun i j ↦
  ((as.getD (5 * i.val + j.val) 0 : ℕ) : ℚ) /
    (1 + ∑ k : Fin 5, ((as.getD (5 * i.val + k.val) 0 : ℕ) : ℚ))

/-- A matrix of either sign whose rows sum to less than `1` in absolute value. -/
def sgnq (as : List ℤ) : Matrix (Fin 5) (Fin 5) ℚ := fun i j ↦
  ((as.getD (5 * i.val + j.val) 0 : ℤ) : ℚ) /
    (1 + ∑ k : Fin 5, |((as.getD (5 * i.val + k.val) 0 : ℤ) : ℚ)|)

/-- A stochastic matrix: every row sums to exactly `1` (an empty row is the identity's). -/
def stochq (as : List ℕ) : Matrix (Fin 5) (Fin 5) ℚ := fun i j ↦
  let row := fun k : Fin 5 ↦ ((as.getD (5 * i.val + k.val) 0 : ℕ) : ℚ)
  if ∑ k, row k = 0 then (if i = j then 1 else 0) else row j / ∑ k, row k

/-- The largest row sum. -/
def rowMax (M : Matrix (Fin 5) (Fin 5) ℚ) : ℚ :=
  (List.finRange 5).foldl (fun m i ↦ max m (∑ j, M i j)) 0

/-- `M^n` on stored rows. -/
def powR (M : Rows) : ℕ → Rows
  | 0 => rows 1
  | n + 1 => mulR (powR M n) M

/-- The Neumann partial sum `Σ_{k<n} M^k` on stored rows. -/
def neumannR (M : Rows) : ℕ → Rows
  | 0 => rows 0
  | n + 1 => addR (neumannR M n) (powR M n)

/-- The tail after `n` terms lies in `[0, s^n / (1 − s)]` entrywise, `s` the largest row sum. -/
def tailOk (M : Matrix (Fin 5) (Fin 5) ℚ) (n : ℕ) : Bool :=
  match invR (rows (1 - M)) with
  | none => false
  | some Z =>
    let s := rowMax M
    let S := neumannR (rows M) n
    allPairs fun i j ↦ decide (0 ≤ entry Z i j - entry S i j) &&
      decide (entry Z i j - entry S i j ≤ s ^ n / (1 - s))

/-- The tail after `n` terms lies in `[0, s^n]`: the control's bound, without `1 / (1 − s)`. -/
def tailTight (M : Matrix (Fin 5) (Fin 5) ℚ) (n : ℕ) : Bool :=
  match invR (rows (1 - M)) with
  | none => false
  | some Z =>
    let s := rowMax M
    let S := neumannR (rows M) n
    allPairs fun i j ↦ decide (0 ≤ entry Z i j - entry S i j) &&
      decide (entry Z i j - entry S i j ≤ s ^ n)

/-- The partial sums approach the walk sum from below. -/
def fromBelow (M : Matrix (Fin 5) (Fin 5) ℚ) (n : ℕ) : Bool :=
  match invR (rows (1 - M)) with
  | none => false
  | some Z =>
    let S := neumannR (rows M) n
    allPairs fun i j ↦ decide (0 ≤ entry Z i j - entry S i j)

/- DYN-2: the walk sum exists, and after `n` terms, `n` up to `3`, what is left is nonnegative and
at most `s^n / (1 − s)`. -/
#eval survives (∀ as : List ℕ, (List.range 4).all (fun n ↦ tailOk (subq as) n) = true) 330

/- DYN-2 control: without the factor `1 / (1 − s)` the bound fails (`M = ½` alone leaves `2 · ½^n`
after `n` terms). -/
#eval refuted (∀ as : List ℕ, (List.range 4).all (fun n ↦ tailTight (subq as) n) = true) 331

/- DYN-2 control: with entries of either sign the partial sums overshoot. -/
#eval refuted (∀ as : List ℤ, (List.range 4).all (fun n ↦ fromBelow (sgnq as) n) = true) 332

/- DYN-2 control: with every row summing to `1`, an eigenvalue of `1`, `1 − M` is singular. -/
#eval refuted (∀ as : List ℕ, (invR (rows (1 - stochq as))).isSome = true) 333

/-! ## DYN-3 HodgeRank on `K₅` -/

/-- The ten edges of `K₅`, each oriented from its smaller end. -/
def edges5 : List (Fin 5 × Fin 5) :=
  (List.finRange 5).flatMap fun i ↦
    (List.finRange 5).filterMap fun j ↦ if i < j then some (i, j) else none

/-- The edge `e`. -/
def edge (e : Fin 10) : Fin 5 × Fin 5 := edges5.getD e (0, 0)

/-- `∂₁` of `K₅`: `+1` at an edge's larger end, `−1` at its smaller, as `d1`. -/
def B5 : Matrix (Fin 5) (Fin 10) ℚ := fun v e ↦
  (if v = (edge e).2 then 1 else 0) - (if v = (edge e).1 then 1 else 0)

/-- Edge weights in `{0, ¼, ½, ¾, 1}` from a list; `0` is an absent edge. -/
def wE (bs : List ℕ) : Fin 10 → ℚ := fun e ↦ ((bs.getD e 0 % 5 : ℕ) : ℚ) / 4

/-- The weighted adjacency the edge weights define. -/
def adjW (bs : List ℕ) : Matrix (Fin 5) (Fin 5) ℚ := fun i j ↦
  ∑ e : Fin 10, if edge e = (i, j) ∨ edge e = (j, i) then wE bs e else 0

/-- A flow on the edges from a list. -/
def flowE (ys : List ℤ) : Fin 10 → ℚ := fun e ↦ (ys.getD e 0 : ℤ)

/-- The weighted inner product on the edges, over ℚ. -/
def wdotQ (w a b : Fin 10 → ℚ) : ℚ := ∑ e, w e * (a e * b e)

/-- `L_w⁺` by the shadow `(L_w + P)⁻¹ − P`, `P` the projector onto the components of the support,
whose indicators span the kernel of `L_w` for positive weights (the Spectral attack checks the
shadow against Penrose's equations). -/
def pinvW (bs : List ℕ) : Option Rows :=
  (invR (addR (rows (B5 * diagonal (wE bs) * B5ᵀ)) (projR (adjW bs)))).map fun Y ↦
    subR Y (projR (adjW bs))

/-- A stored matrix applied to a vector. -/
def applyR (X : Rows) (v : Fin 5 → ℚ) : Fin 5 → ℚ := fun i ↦ ∑ k : Fin 5, entry X i k * v k

/-- HodgeRank on `K₅`: the residual of `s = L_w⁺ ∂₁ (w ∘ Y)` is divergence-free, and its weighted
energy is at most the residual energy of any other potential `x`. -/
def hodgeOk (bs : List ℕ) (ys xs : List ℤ) : Bool :=
  match pinvW bs with
  | none => false
  | some X =>
    let w := wE bs
    let Y := flowE ys
    let s := applyR X (B5 *ᵥ (w * Y))
    let r := Y - B5ᵀ *ᵥ s
    (B5 *ᵥ (w * r) == 0) &&
      decide (wdotQ w r r ≤ wdotQ w (Y - B5ᵀ *ᵥ vec xs) (Y - B5ᵀ *ᵥ vec xs))

/-- The control: the potential of the unweighted divergence, `L_w⁺ ∂₁ Y`. -/
def hodgeUnweighted (bs : List ℕ) (ys : List ℤ) : Bool :=
  match pinvW bs with
  | none => false
  | some X =>
    let w := wE bs
    let Y := flowE ys
    let s := applyR X (B5 *ᵥ Y)
    B5 *ᵥ (w * (Y - B5ᵀ *ᵥ s)) == 0

/- DYN-3: the least-squares potential, its residual divergence-free. -/
#eval survives (∀ bs : List ℕ, ∀ ys xs : List ℤ, hodgeOk bs ys xs = true) 334

/- DYN-3 control: the divergence must carry the weights; without them the residual is not
divergence-free. -/
#eval refuted (∀ bs : List ℕ, ∀ ys : List ℤ, hodgeUnweighted bs ys = true) 335

/-! ## DYN-5 Coarse-graining by a partition -/

/-- A partition of `Fin 5` into three blocks from a list. -/
def part (ps : List ℕ) : Fin 5 → Fin 3 := fun v ↦ ⟨ps.getD v 0 % 3, Nat.mod_lt _ (by norm_num)⟩

/-- A `5 × 5` matrix over ℚ from a list of ints, row-major, of either sign and no symmetry. -/
def matq (xs : List ℤ) : Matrix (Fin 5) (Fin 5) ℚ := fun i j ↦ (xs.getD (5 * i.val + j.val) 0 : ℤ)

/-- A block field from a list. -/
def vec3 (hs : List ℤ) : Fin 3 → ℚ := fun b ↦ (hs.getD b 0 : ℤ)

/-- The block-constant lift of a block field, `Transport.pull` over ℚ. -/
def pullQ (π : Fin 5 → Fin 3) (h : Fin 3 → ℚ) : Fin 5 → ℚ := fun v ↦ h (π v)

instance {m n α : Type*} [Fintype m] [Fintype n] [DecidableEq α] : DecidableEq (Matrix m n α) :=
  inferInstanceAs (DecidableEq (m → n → α))

/- DYN-5: `Pᵀ L P = L_π` for any matrix and any partition. -/
#eval survives (∀ ps : List ℕ, ∀ xs : List ℤ,
  (indicator (part ps))ᵀ * lap (matq xs) * indicator (part ps) =
    lap (quot (part ps) (matq xs))) 336

/- DYN-5 control: lifted back to the fine graph, `P Pᵀ L P Pᵀ` is not the Laplacian of
`P Pᵀ A P Pᵀ`: the block sums of the degrees land off the diagonal. -/
#eval refuted (∀ ps : List ℕ, ∀ xs : List ℤ,
  indicator (part ps) * (indicator (part ps))ᵀ * lap (matq xs) *
      (indicator (part ps) * (indicator (part ps))ᵀ) =
    lap (indicator (part ps) * (indicator (part ps))ᵀ * matq xs *
      (indicator (part ps) * (indicator (part ps))ᵀ))) 337

/- DYN-5: the energy of a block-constant field is the quotient's energy of its block values. -/
#eval survives (∀ ps : List ℕ, ∀ xs hs : List ℤ,
  pullQ (part ps) (vec3 hs) ⬝ᵥ (lap (matq xs) *ᵥ pullQ (part ps) (vec3 hs)) =
    vec3 hs ⬝ᵥ (lap (quot (part ps) (matq xs)) *ᵥ vec3 hs)) 338

/-! ## DYN-5 The ripple across a transport -/

/-- A permutation of `Fin 5` as a product of transpositions. -/
def perm (l : List (Fin 5 × Fin 5)) : Equiv.Perm (Fin 5) := (l.map fun p ↦ Equiv.swap p.1 p.2).prod

/-- The relation relabelled along a permutation: every weight carried forward. -/
def relabel (σ : Equiv.Perm (Fin 5)) (M : Matrix (Fin 5) (Fin 5) ℚ) : Matrix (Fin 5) (Fin 5) ℚ :=
  fun b b' ↦ M (σ.symm b) (σ.symm b')

/-- The relation pushed forward along any map: the weight between two targets is the total
weight between their fibers, which merges rows where the map does. -/
def pushRel (σ : Fin 5 → Fin 5) (M : Matrix (Fin 5) (Fin 5) ℚ) : Matrix (Fin 5) (Fin 5) ℚ :=
  (indicator σ)ᵀ * M * indicator σ

/-- The resolvents intertwine with the push-forward: `Pᵀ (1 − M)⁻¹ = (1 − M')⁻¹ Pᵀ`. -/
def intertwineOk (σ : Fin 5 → Fin 5) (M M' : Matrix (Fin 5) (Fin 5) ℚ) : Bool :=
  match invR (rows (1 - M)), invR (rows (1 - M')) with
  | some Z, some Z' => mulR (rows (indicator σ)ᵀ) Z == mulR Z' (rows (indicator σ)ᵀ)
  | _, _ => false

/- DYN-5: across a permutation that carries every weight forward, propagating then carrying
forward is carrying forward then propagating. -/
#eval survives (∀ l : List (Fin 5 × Fin 5), ∀ as : List ℕ,
  intertwineOk (perm l) (subq as) (relabel (perm l) (subq as)) = true) 339

/- DYN-5 control: across a merge, with the weights pushed forward, the ripple is not
path-independent. -/
#eval refuted (∀ l : List (Fin 5), ∀ as : List ℕ,
  intertwineOk (fun i ↦ l.getD i 0) (subq as) (pushRel (fun i ↦ l.getD i 0) (subq as)) = true) 340

/-! ## DYN-1 The velocity of a value -/

/-- A value per identity per cut, from a list of lists. -/
def traj (xs : List (List ℤ)) : ℕ → Fin 3 → ℚ := fun c v ↦ ((xs.getD c []).getD v 0 : ℤ)

/- DYN-1: the displacement over a window is the sum of its steps. -/
#eval survives (∀ xs : List (List ℤ), ∀ a n : Fin 4,
  velocity (traj xs) a (a + n) =
    ∑ k ∈ range n, velocity (traj xs) (a + k) (a + k + 1)) 341

/- DYN-1 control: the sum of the steps' sizes is not the size of the displacement (a revert). -/
#eval refuted (∀ xs : List (List ℤ), ∀ a n : Fin 4, ∀ v : Fin 3,
  ∑ k ∈ range n, |velocity (traj xs) (a + k) (a + k + 1) v| =
    |velocity (traj xs) a (a + n) v|) 342

/-! ## DYN-5 RSP-5 block by block -/

/-- The walk restricted to a block, the complement absorbing. -/
def restrictQ (M : Matrix (Fin 5) (Fin 5) ℚ) (S : Fin 5 → Bool) : Matrix (Fin 5) (Fin 5) ℚ :=
  fun i j ↦ if S i && S j then M i j else 0

/-- The weights restricted to a block, so that the block's walk has the block's own degrees. -/
def weightsOn (w : Matrix (Fin 5) (Fin 5) ℚ) (S : Fin 5 → Bool) : Matrix (Fin 5) (Fin 5) ℚ :=
  fun i j ↦ if S i && S j then w i j else 0

/-- The first-passage ratio on the block is at most the graph's, cross-multiplied. -/
def blockLe (W WS : Matrix (Fin 5) (Fin 5) ℚ) : Bool :=
  match invR (rows (1 - W)), invR (rows (1 - WS)) with
  | some Z, some ZS => allPairs fun i j ↦
      decide (entry ZS i j * entry Z j j ≤ entry Z i j * entry ZS j j)
  | _, _ => false

/- DYN-5: a block read on its own, with the graph's degrees, under-estimates nearness. -/
#eval survives (∀ bs ps : List ℕ, blockLe (killedQ (wq 0 bs) (1 / 2))
  (restrictQ (killedQ (wq 0 bs) (1 / 2)) fun v ↦ part ps v = 0) = true) 343

/- DYN-5 control: with the block's own degrees the walk renormalizes onto the kept edges, and the
block can invent nearness. -/
#eval refuted (∀ bs ps : List ℕ, blockLe (killedQ (wq 0 bs) (1 / 2))
  (killedQ (weightsOn (wq 0 bs) fun v ↦ part ps v = 0) (1 / 2)) = true) 344

end Palace.Dynamics.Attack
