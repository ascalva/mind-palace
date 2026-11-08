module

public import Mathlib.Analysis.SpecialFunctions.Log.Basic
public import Mathlib.Topology.MetricSpace.Contracting
public import Palace.Gap.Defs
public import Palace.Spectral.Defs

/-!
# The utility field: the definitions

The objects of `docs/design-notes/dn-utility-field.md` and what `Palace/Utility.lean` is stated
over: a field over the sites of a graph (its nodes, its edges, its declared paths), one value per
site, that records how much the site is used and how much value its use produced; the update rule
(each tick decays the field toward a baseline and adds a saturated increment); the box the field
lives in; arcs (sites whose field stands a declared height above the baseline); the nudge of the
structural weights by the field, with its margin; the stationary distribution of the walk on a
weight matrix and the total variation between two distributions; the closed loop in which this
tick's use is a function of the field; and the models of the controls: reinforcement without
decay, the two-site mean field of a reinforcement with an exponent, and the greedy walk that
always takes the heavier edge and reinforces it. The definitions are over any linearly ordered
field so that the attacks run them over `ℚ` as they are; the theorems that need exponentials,
logarithms or a spectrum are over `ℝ`. No code in the store computes any of this; the simulator
`eval/utility_field.py` transcribes it on synthetic graphs.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Utility

/-! ### The field and its update -/

section Field

variable {ι K : Type*} [Field K] [LinearOrder K]

/-- The saturated increment: `x` clamped to `[−c, c]`. A use that produced value adds a positive
increment, one that cost value a negative one, and neither moves the field by more than the cap. -/
def sat (c x : K) : K := max (-c) (min c x)

/-- One tick of the field: every site decays toward the baseline `b` by the rate `lam`, then
receives the saturated increment of this tick's use. -/
def step (b lam c : K) (u use : ι → K) : ι → K :=
  fun e ↦ b + (1 - lam) * (u e - b) + sat c (use e)

/-- The field after a log of uses, from `u₀`: the fold of `step` over the log, so a function of
the log and the start alone. -/
def evolve (b lam c : K) (u₀ : ι → K) (log : List (ι → K)) : ι → K :=
  log.foldl (step b lam c) u₀

/-- The ceiling of the box, `b + c / lam`: the geometric sum of increments at the cap. -/
def ceiling (b lam c : K) : K := b + c / lam

/-- The floor of the box, `b − c / lam`. -/
def floor (b lam c : K) : K := b - c / lam

/-- The field lies in the declared box `[floor, ceiling]` at every site. -/
def InBox (b lam c : K) (u : ι → K) : Prop :=
  ∀ e, floor b lam c ≤ u e ∧ u e ≤ ceiling b lam c

/-- `n` ticks with no use at all: the field left alone. -/
def idle (b lam c : K) (u : ι → K) (n : ℕ) : ι → K :=
  (fun v ↦ step b lam c v 0)^[n] u

/-- `n` ticks of the constant use `r` at every site: a heat spot held hot. -/
def steady (b lam c r : K) (u : ι → K) (n : ℕ) : ι → K :=
  (fun v ↦ step b lam c v fun _ ↦ r)^[n] u

/-- An arc: a site whose field stands at least `a` above the baseline. -/
def IsArc (b a : K) (u : ι → K) (e : ι) : Prop := b + a ≤ u e

/-- The closed loop: this tick's use is a function `F` of the field itself, as it is when the
field's own nudge of the ranking changes what is used next. -/
def loop (b lam c : K) (F : (ι → K) → ι → K) (u : ι → K) : ι → K := step b lam c u (F u)

/-- The control: reinforcement without decay and without a cap. -/
def linearStep (u use : ι → K) : ι → K := u + use

end Field

/-! ### The nudge of the structural weights -/

section Nudge

variable {V K : Type*} [Fintype V] [Field K] [LinearOrder K]

/-- The effective weights: each structural weight times `1 + η (u − b)`, the field's departure
from the baseline scaled by the nudge `η`. At the baseline the effective weights are the
structural ones. -/
def nudge (η b : K) (A : Matrix V V K) (u : V → V → K) : Matrix V V K :=
  of fun i j ↦ A i j * (1 + η * (u i j - b))

omit [Fintype V] [LinearOrder K] in
/-- A symmetric field nudges symmetric weights to symmetric weights. -/
theorem isSymm_nudge {η b : K} {A : Matrix V V K} (hA : A.IsSymm) {u : V → V → K}
    (hu : ∀ i j, u i j = u j i) : (nudge η b A u).IsSymm := by
  ext i j
  simp only [transpose_apply, nudge, of_apply, hA.apply i j, hu j i]

/-- The margin `θ = η · c / lam`: the largest relative change the nudge can make to a weight. -/
def margin (η lam c : K) : K := η * (c / lam)

/-- The stationary distribution of the random walk on the weights `A`: a node's degree over the
volume. -/
def statDist (A : Matrix V V K) (i : V) : K := degree A i / ∑ j, degree A j

/-- The total variation between two distributions, `½ Σ_i |p_i − q_i|`. -/
def tv (p q : V → K) : K := 1 / 2 * ∑ i, |p i - q i|

end Nudge

/-! ### The Laplacian as an operator -/

section Operator

variable {V : Type*} [Fintype V] [DecidableEq V]

/-- The Laplacian's operator on Euclidean space is symmetric, so Weyl's counts (SPC-3) apply
to it. -/
theorem isSymmetric_toEuclideanLin_lap {A : Matrix V V ℝ} (hA : A.IsSymm) :
    (Matrix.toEuclideanLin (lap A)).IsSymmetric :=
  Matrix.isSymmetric_toEuclideanLin_iff.2 (isHermitian_lap A hA)

end Operator

/-! ### The controls' models -/

section Controls

variable {K : Type*} [Field K] [LinearOrder K]

/-- The two-site mean field of a reinforcement with the exponent `α`: each site grows by its
share of the `α`-th powers, the expected step of a generalized urn with feedback. -/
def polyaStep (α : ℕ) (x y : K) : K × K :=
  (x + x ^ α / (x ^ α + y ^ α), y + y ^ α / (x ^ α + y ^ α))

/-- The greedy reinforced walk on the path `0 − 1 − 2`: the walker's position and the weights
of the two edges. -/
structure Greedy (K : Type*) where
  /-- Where the walker stands. -/
  pos : Fin 3
  /-- The weight of the edge `0 − 1`. -/
  w01 : K
  /-- The weight of the edge `1 − 2`. -/
  w12 : K

/-- One step of the greedy walk: move along the heavier incident edge (the left one on a tie)
and reinforce the edge taken by one: the strongly reinforced limit, in which the walker always
takes the edge it has used most. -/
def greedyStep (s : Greedy K) : Greedy K :=
  if s.pos = 0 then { s with pos := 1, w01 := s.w01 + 1 }
  else if s.pos = 1 then
    if s.w01 < s.w12 then { s with pos := 2, w12 := s.w12 + 1 }
    else { s with pos := 0, w01 := s.w01 + 1 }
  else { s with pos := 1, w12 := s.w12 + 1 }

/-- The greedy walk after `n` steps. -/
def greedyWalk (s : Greedy K) (n : ℕ) : Greedy K := greedyStep^[n] s

/-- How many of the first `n` positions of the greedy walk are the node `v`. -/
def greedyVisits (s : Greedy K) (n : ℕ) (v : Fin 3) : ℕ :=
  ((List.range n).filter fun k ↦ (greedyWalk s k).pos = v).length

/-- The empirical measure of the greedy walk over its first `n` positions. -/
def greedyEmp (s : Greedy K) (n : ℕ) (v : Fin 3) : K := (greedyVisits s n v : K) / n

/-- The structural weights of the path `0 − 1 − 2` with unit edges. -/
def path3 : Matrix (Fin 3) (Fin 3) K :=
  of fun i j ↦ if i.val + 1 = j.val ∨ j.val + 1 = i.val then 1 else 0

end Controls

end Palace.Utility
