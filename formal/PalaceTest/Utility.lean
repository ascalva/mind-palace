module

public import Palace.Utility
public import PalaceTest.Attack
public meta import Palace.Utility
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Utility`

The Plausible attacks and negative controls for the laws of `Palace/Utility.lean`, on exact
shadows over ℚ (seeds 402 to 424), run on the model's own definitions, which are polymorphic in
the field: fields on four sites from lists of integers, the box's parameters from naturals (a
baseline `1 + b`, a rate `1/(1 + l)`, a cap `c/4`), uses of any size and sign; symmetric
nonnegative weights on four nodes with a symmetric field on the edges and a nudge whose margin is
`t/(t + 1)`; the closed loop with a linear gain; the two-site mean field at exponents `0`, `1`
and `2`; and the greedy walk on the three-node path for forty steps. The logarithm, the metric
and the spectrum do not run, so UTL-2's window, UTL-6's fixed point and UTL-5's eigenvalue counts
are proved and not attacked; what is attacked is the algebra each rests on: the closed forms, the
sup-distance contraction, the quadratic-form bounds. They run when this module builds
(`lake test`).
-/

@[expose] public section

open Matrix Finset Palace Palace.Utility

namespace Palace.Utility.Attack

/-! ## The shadows -/

/-- The baseline from a natural: `1 + b`. -/
def bq (bn : ℕ) : ℚ := 1 + bn

/-- The forgetting rate from a natural: `1 / (1 + l)`, in `(0, 1]`. -/
def lamq (ln : ℕ) : ℚ := 1 / (1 + ln)

/-- The cap from a natural: `c / 4`. -/
def cq (cn : ℕ) : ℚ := (cn : ℚ) / 4

/-- A fraction in `[−1, 1]` from a list entry, clamped to `[−8, 8]` and divided by `8`. -/
def frac (xs : List ℤ) (k : ℕ) : ℚ := ((max (-8) (min 8 (xs.getD k 0)) : ℤ) : ℚ) / 8

/-- A field in the box from a list: the baseline plus the box's half-height times a fraction. -/
def boxed (bn ln cn : ℕ) (xs : List ℤ) : Fin 4 → ℚ := fun e ↦
  bq bn + cq cn / lamq ln * frac xs e.val

/-- A field twice as far from the baseline as the box allows: the control's. -/
def boxed2 (bn ln cn : ℕ) (xs : List ℤ) : Fin 4 → ℚ := fun e ↦
  bq bn + cq cn / lamq ln * (2 * frac xs e.val)

/-- A field in the box with ceiling `b + c` in place of `b + c/lam`: the control's wrong box. -/
def tight (bn cn : ℕ) (xs : List ℤ) : Fin 4 → ℚ := fun e ↦ bq bn + cq cn * frac xs e.val

/-- A use of any size and sign from a list. -/
def useZ (us : List ℤ) : Fin 4 → ℚ := fun e ↦ (us.getD e.val 0 : ℤ)

/-- A log of uses from a list of lists. -/
def logZ (ls : List (List ℤ)) : List (Fin 4 → ℚ) := ls.map useZ

/-- A field from a list of integers. -/
def vecZ (xs : List ℤ) : Fin 4 → ℚ := fun e ↦ (xs.getD e.val 0 : ℤ)

/-- Whether a field lies in the tight box `[b − c, b + c]`. -/
def inTight (b c : ℚ) (u : Fin 4 → ℚ) : Bool :=
  (List.finRange 4).all fun e ↦ decide (b - c ≤ u e ∧ u e ≤ b + c)

instance (b lam c : ℚ) (u : Fin 4 → ℚ) : Decidable (InBox b lam c u) :=
  inferInstanceAs (Decidable (∀ e : Fin 4, floor b lam c ≤ u e ∧ u e ≤ ceiling b lam c))

instance (b a : ℚ) (u : Fin 4 → ℚ) (e : Fin 4) : Decidable (IsArc b a u e) :=
  inferInstanceAs (Decidable (b + a ≤ u e))

/-! ## UTL-1 Boundedness -/

/- UTL-1: one tick keeps a boxed field in its box, whatever the use. -/
#eval survives (∀ bn ln cn : ℕ, ∀ xs us : List ℤ,
  InBox (bq bn) (lamq ln) (cq cn)
    (step (bq bn) (lamq ln) (cq cn) (boxed bn ln cn xs) (useZ us))) 402

/- UTL-1: and along any log of uses. -/
#eval survives (∀ bn ln cn : ℕ, ∀ xs : List ℤ, ∀ ls : List (List ℤ),
  InBox (bq bn) (lamq ln) (cq cn)
    (evolve (bq bn) (lamq ln) (cq cn) (boxed bn ln cn xs) (logZ ls))) 403

/- UTL-1 control: without the decay and the cap, one use takes the field out of the box. -/
#eval refuted (∀ bn ln cn : ℕ, ∀ xs us : List ℤ,
  InBox (bq bn) (lamq ln) (cq cn) (linearStep (boxed bn ln cn xs) (useZ us))) 404

/- UTL-1 control: the box with ceiling `b + c` in place of `b + c/lam` is not invariant. -/
#eval refuted (∀ bn ln cn : ℕ, ∀ xs us : List ℤ,
  inTight (bq bn) (cq cn) (step (bq bn) (lamq ln) (cq cn) (tight bn cn xs) (useZ us)) = true) 405

/-! ## UTL-2 Decay, arcs -/

/- UTL-2: the idle closed form, `u_n = b + (1 − lam)^n (u₀ − b)`, exactly. -/
#eval survives (∀ bn ln cn : ℕ, ∀ xs : List ℤ, ∀ n : Fin 6,
  idle (bq bn) (lamq ln) (cq cn) (boxed bn ln cn xs) n =
    fun e ↦ bq bn + (1 - lamq ln) ^ n.val * (boxed bn ln cn xs e - bq bn)) 406

/- UTL-2 control: a residual use of half the cap holds the field off the baseline, past the idle
bound. -/
#eval refuted (∀ bn ln cn : ℕ, ∀ xs : List ℤ, ∀ n : Fin 6, ∀ e : Fin 4,
  |steady (bq bn) (lamq ln) (cq cn) (cq cn / 2) (boxed bn ln cn xs) n e - bq bn| ≤
    (1 - lamq ln) ^ n.val * (cq cn / lamq ln)) 407

/- UTL-2: an arc forms at a heat spot held at the cap from the baseline, at the height the
closed form gives. -/
#eval survives (∀ bn ln cn : ℕ, ∀ n : Fin 6,
  IsArc (bq bn) (cq cn / lamq ln * (1 - (1 - lamq ln) ^ n.val))
    (steady (bq bn) (lamq ln) (cq cn) (cq cn) (fun _ : Fin 4 ↦ bq bn) n) 0) 408

/- UTL-2: arcs fade: once `(1 − lam)^n c/lam < a`, no idle site is an arc of height `a`. -/
#eval survives (∀ bn ln cn an : ℕ, ∀ xs : List ℤ, ∀ n : Fin 6, ∀ e : Fin 4,
  (1 - lamq ln) ^ n.val * (cq cn / lamq ln) < (an + 1 : ℚ) / 4 →
    ¬ IsArc (bq bn) ((an + 1 : ℚ) / 4)
      (idle (bq bn) (lamq ln) (cq cn) (boxed bn ln cn xs) n) e) 409

/- UTL-2 control: an arc left alone stays an arc. -/
#eval refuted (∀ bn ln cn an : ℕ, ∀ xs : List ℤ, ∀ n : Fin 6, ∀ e : Fin 4,
  IsArc (bq bn) ((an + 1 : ℚ) / 4) (boxed bn ln cn xs) e →
    IsArc (bq bn) ((an + 1 : ℚ) / 4)
      (idle (bq bn) (lamq ln) (cq cn) (boxed bn ln cn xs) n) e) 410

/-! ## UTL-3 The nudge: support and the stationary distribution -/

/-- Symmetric nonnegative weights on `Fin 4` from a list, each in `{0, …, 4}`, no loops. -/
def wq4 (bs : List ℕ) : Matrix (Fin 4) (Fin 4) ℚ := fun i j ↦
  if i = j then 0 else ((bs.getD (4 * min i.val j.val + max i.val j.val) 0 % 5 : ℕ) : ℚ)

/-- A symmetric field on the edges, in the box. -/
def boxedE (bn ln cn : ℕ) (xs : List ℤ) : Fin 4 → Fin 4 → ℚ := fun i j ↦
  bq bn + cq cn / lamq ln * frac xs (4 * min i.val j.val + max i.val j.val)

/-- A symmetric field on the edges twice as far from the baseline as the box allows. -/
def boxedE2 (bn ln cn : ℕ) (xs : List ℤ) : Fin 4 → Fin 4 → ℚ := fun i j ↦
  bq bn + cq cn / lamq ln * (2 * frac xs (4 * min i.val j.val + max i.val j.val))

/-- The nudge from a natural: the margin `θ = t/(t + 1)`, so `η = θ lam / c`. -/
def etaq (ln cn t : ℕ) : ℚ := (t : ℚ) / (t + 1) * (lamq ln / cq cn)

/-- The margin of that nudge. -/
def thetaq (ln cn t : ℕ) : ℚ := margin (etaq ln cn t) (lamq ln) (cq cn)

/-- The volume is positive: some edge is present. -/
def volPos (A : Matrix (Fin 4) (Fin 4) ℚ) : Bool := decide (0 < ∑ j, degree A j)

/-- The control's additive nudge, `A + η (u − b)`. -/
def addNudge (η b : ℚ) (A : Matrix (Fin 4) (Fin 4) ℚ) (u : Fin 4 → Fin 4 → ℚ) :
    Matrix (Fin 4) (Fin 4) ℚ :=
  of fun i j ↦ A i j + η * (u i j - b)

/- UTL-3: the nudge keeps the support: an effective weight is zero exactly when the structural
one is. -/
#eval survives (∀ ln cn t : ℕ, ∀ bn : ℕ, ∀ bs : List ℕ, ∀ xs : List ℤ, ∀ i j : Fin 4,
  (decide (nudge (etaq ln cn t) (bq bn) (wq4 bs) (boxedE bn ln cn xs) i j = 0) ==
    decide (wq4 bs i j = 0)) = true) 411

/- UTL-3 control: the additive nudge creates edges where there were none. -/
#eval refuted (∀ ln cn t : ℕ, ∀ bn : ℕ, ∀ bs : List ℕ, ∀ xs : List ℤ, ∀ i j : Fin 4,
  (decide (addNudge (etaq ln cn t) (bq bn) (wq4 bs) (boxedE bn ln cn xs) i j = 0) ==
    decide (wq4 bs i j = 0)) = true) 412

/- UTL-3: the stationary distributions of the nudged and the structural walks are within
`θ/(1 − θ)` in total variation. -/
#eval survives (∀ ln cn t : ℕ, ∀ bn : ℕ, ∀ bs : List ℕ, ∀ xs : List ℤ,
  volPos (wq4 bs) = true →
    tv (statDist (nudge (etaq ln cn t) (bq bn) (wq4 bs) (boxedE bn ln cn xs)))
        (statDist (wq4 bs)) ≤
      thetaq ln cn t / (1 - thetaq ln cn t)) 413

/- UTL-3 control: a field outside the box, twice the box's height, breaks the bound. -/
#eval refuted (∀ ln cn t : ℕ, ∀ bn : ℕ, ∀ bs : List ℕ, ∀ xs : List ℤ,
  volPos (wq4 bs) = true →
    tv (statDist (nudge (etaq ln cn t) (bq bn) (wq4 bs) (boxedE2 bn ln cn xs)))
        (statDist (wq4 bs)) ≤
      thetaq ln cn t / (1 - thetaq ln cn t)) 414

/-! ## UTL-5 The bounded nudge on the Laplacian -/

/-- The largest degree. -/
def dmax (A : Matrix (Fin 4) (Fin 4) ℚ) : ℚ :=
  (List.finRange 4).foldl (fun m i ↦ max m (degree A i)) 0

/- UTL-5: the field moves the Laplacian's quadratic form by at most `θ` times the structural
form. -/
#eval survives (∀ ln cn t : ℕ, ∀ bn : ℕ, ∀ bs : List ℕ, ∀ xs ys : List ℤ,
  |vecZ ys ⬝ᵥ ((lap (nudge (etaq ln cn t) (bq bn) (wq4 bs) (boxedE bn ln cn xs)) - lap (wq4 bs))
      *ᵥ vecZ ys)| ≤
    thetaq ln cn t * (vecZ ys ⬝ᵥ (lap (wq4 bs) *ᵥ vecZ ys))) 415

/- UTL-5 control: a field outside the box moves the form past the margin. -/
#eval refuted (∀ ln cn t : ℕ, ∀ bn : ℕ, ∀ bs : List ℕ, ∀ xs ys : List ℤ,
  |vecZ ys ⬝ᵥ ((lap (nudge (etaq ln cn t) (bq bn) (wq4 bs) (boxedE2 bn ln cn xs)) - lap (wq4 bs))
      *ᵥ vecZ ys)| ≤
    thetaq ln cn t * (vecZ ys ⬝ᵥ (lap (wq4 bs) *ᵥ vecZ ys))) 416

/- UTL-5: the Laplacian's form is at most twice the largest degree times the norm. -/
#eval survives (∀ bs : List ℕ, ∀ ys : List ℤ,
  vecZ ys ⬝ᵥ (lap (wq4 bs) *ᵥ vecZ ys) ≤ 2 * dmax (wq4 bs) * (vecZ ys ⬝ᵥ vecZ ys)) 417

/- UTL-5 control: the largest degree alone does not bound the form (an edge with opposite ends). -/
#eval refuted (∀ bs : List ℕ, ∀ ys : List ℤ,
  vecZ ys ⬝ᵥ (lap (wq4 bs) *ᵥ vecZ ys) ≤ dmax (wq4 bs) * (vecZ ys ⬝ᵥ vecZ ys)) 418

/-! ## UTL-6 The closed loop -/

/-- The sup distance of two fields. -/
def supDist (u v : Fin 4 → ℚ) : ℚ := (List.finRange 4).foldl (fun m e ↦ max m |u e - v e|) 0

/-- A linear gain below the rate, `K = lam · k/(k + 1)`. -/
def gainBelow (ln k : ℕ) : ℚ := lamq ln * ((k : ℚ) / (k + 1))

/-- A linear gain at or above the rate, `K = lam · (k + 1)`. -/
def gainAbove (ln k : ℕ) : ℚ := lamq ln * (k + 1)

/-- The use as a linear function of the field's departure from the baseline. -/
def linearUse (Kg b : ℚ) (u : Fin 4 → ℚ) : Fin 4 → ℚ := fun e ↦ Kg * (u e - b)

/- UTL-6: with the gain below the rate, the loop contracts the sup distance by `1 − lam + K`. -/
#eval survives (∀ bn ln cn k : ℕ, ∀ xs ys : List ℤ,
  supDist (loop (bq bn) (lamq ln) (cq cn) (linearUse (gainBelow ln k) (bq bn)) (vecZ xs))
      (loop (bq bn) (lamq ln) (cq cn) (linearUse (gainBelow ln k) (bq bn)) (vecZ ys)) ≤
    (1 - lamq ln + gainBelow ln k) * supDist (vecZ xs) (vecZ ys)) 419

/- UTL-6 control: at or above the rate the ceiling is a second fixed point beside the baseline,
so the claim that it moves is refuted at once. -/
#eval refuted (∀ bn ln cn k : ℕ,
  loop (bq bn) (lamq ln) (cq cn) (linearUse (gainAbove ln k) (bq bn))
      (fun _ ↦ ceiling (bq bn) (lamq ln) (cq cn)) ≠
    fun _ ↦ ceiling (bq bn) (lamq ln) (cq cn)) 420

/-! ## The exponent decides the regime -/

/-- Two positive weights with the first larger, from naturals. -/
def pair (y d : ℕ) : ℚ × ℚ := ((y : ℚ) + 1 + (d + 1), (y : ℚ) + 1)

/- The three regimes on one draw: at exponent `2` (superlinear) the leader's ratio grows, at `1`
(linear) it is constant, at `0` (sublinear) it moves toward one. -/
#eval survives (∀ y d : ℕ,
  (pair y d).1 * (polyaStep 2 (pair y d).1 (pair y d).2).2 <
      (polyaStep 2 (pair y d).1 (pair y d).2).1 * (pair y d).2 ∧
    (polyaStep 1 (pair y d).1 (pair y d).2).1 * (pair y d).2 =
      (pair y d).1 * (polyaStep 1 (pair y d).1 (pair y d).2).2 ∧
    (polyaStep 0 (pair y d).1 (pair y d).2).1 * (pair y d).2 <
      (pair y d).1 * (polyaStep 0 (pair y d).1 (pair y d).2).2) 421

/- Control: at exponent `2` the ratio is not constant. -/
#eval refuted (∀ y d : ℕ,
  (polyaStep 2 (pair y d).1 (pair y d).2).1 * (pair y d).2 =
    (pair y d).1 * (polyaStep 2 (pair y d).1 (pair y d).2).2) 422

/-! ## Strong reinforcement localizes -/

/-- The greedy walk started in the middle with the left edge at least as heavy. -/
def start (a d : ℕ) : Greedy ℚ := { pos := 1, w01 := (a : ℚ) + d, w12 := a }

/- The greedy walk never reaches the far node in forty steps. -/
#eval survives (∀ a d : ℕ, ∀ n : Fin 41, (greedyWalk (start a d) n).pos ≠ 2) 423

/- Control: its empirical measure is not within `1/8` of the structural stationary distribution
at any horizon. -/
#eval refuted (∀ a d : ℕ, ∀ n : Fin 41,
  tv (greedyEmp (start a d) (n.val + 1)) (statDist (path3 : Matrix (Fin 3) (Fin 3) ℚ)) < 1 / 8) 424

end Palace.Utility.Attack
