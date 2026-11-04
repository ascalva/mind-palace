module

public import Palace.Sentence
public import PalaceTest.Attack
public meta import Palace.Sentence
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Sentence`

The Plausible attacks and negative controls for the laws of `Palace/Sentence.lean`, on exact
shadows: kernels over ℚ on `Fin 3` (Gram matrices `Bᵀ B` for the cone, `B + Bᵀ` for either
sign), regions from three bits, chains over typed graphs on three vertices run against the
grounding automaton `S* · (C | D)`, hypothetical edges on weights over ℚ, and Sherman–Morrison on
`Fin 2` with the explicit inverse. They run when this module builds (`lake test`).
-/

@[expose] public section

open Matrix Finset

namespace Palace.Query.Attack

/-! ## Kernels, fields and regions -/

/-- A `3 × 3` matrix over ℚ from a list of ints, row-major. -/
def mat (xs : List ℤ) : Matrix (Fin 3) (Fin 3) ℚ :=
  of fun i j ↦ (xs.getD (3 * i.val + j.val) 0 : ℚ)

/-- A Gram matrix `Bᵀ B`: in the cone by construction. -/
def gram (xs : List ℤ) : Matrix (Fin 3) (Fin 3) ℚ := (mat xs)ᵀ * mat xs

/-- A symmetric matrix of either sign. -/
def symm (xs : List ℤ) : Matrix (Fin 3) (Fin 3) ℚ := mat xs + (mat xs)ᵀ

/-- A vector. -/
def vec (xs : List ℤ) : Fin 3 → ℚ := fun i ↦ (xs.getD i.val 0 : ℚ)

/-- A region from three bits. -/
def region (c : Fin 8) : Finset (Fin 3) := univ.filter fun i ↦ c.val.testBit i.val

/-- The energy of a matrix on a vector. -/
def energy (K : Matrix (Fin 3) (Fin 3) ℚ) (x : Fin 3 → ℚ) : ℚ := x ⬝ᵥ (K *ᵥ x)

/-- Two matrices agree entrywise. -/
def same (A B : Matrix (Fin 3) (Fin 3) ℚ) : Bool :=
  (List.finRange 3).all fun i ↦ (List.finRange 3).all fun j ↦ A i j == B i j

/- QSA-1: `and` keeps the cone. -/
#eval survives (∀ bs ds xs : List ℤ, 0 ≤ energy (gram bs ⊙ gram ds) (vec xs)) 219

/- Control: the Schur product of two symmetric matrices of either sign. -/
#eval refuted (∀ bs ds xs : List ℤ, 0 ≤ energy (symm bs ⊙ symm ds) (vec xs)) 220

/- QSA-2: `within` keeps the cone. -/
#eval survives (∀ (bs xs : List ℤ) (c : Fin 8),
  0 ≤ energy (mask (region c) (gram bs)) (vec xs)) 221

/- Control: `within` on a symmetric matrix of either sign. -/
#eval refuted (∀ (bs xs : List ℤ) (c : Fin 8),
  0 ≤ energy (mask (region c) (symm bs)) (vec xs)) 222

/- QSA-2: `within` distributes over `or` and `and`, and adjectives stack by intersection. -/
#eval survives (∀ (as bs : List ℤ) (c d : Fin 8),
  (same (mask (region c) (mat as + mat bs)) (mask (region c) (mat as) + mask (region c) (mat bs)) &&
   same (mask (region c) (mat as ⊙ mat bs)) (mask (region c) (mat as) ⊙ mask (region c) (mat bs)) &&
   same (mask (region c) (mask (region d) (mat as))) (mask (region c ∩ region d) (mat as))) =
    true) 223

/- Control: `within` does not distribute over the matrix product. -/
#eval refuted (∀ (as bs : List ℤ) (c : Fin 8),
  same (mask (region c) (mat as * mat bs)) (mask (region c) (mat as) * mask (region c) (mat bs)) =
    true) 224

/- QSA-3: the field of `and` at an anchor is the product of the fields. -/
#eval survives (∀ (as bs : List ℤ) (a : Fin 3),
  fieldAt (mat as ⊙ mat bs) a = fieldAt (mat as) a * fieldAt (mat bs) a) 225

/- Control: the field of the matrix product is not. -/
#eval refuted (∀ (as bs : List ℤ) (a : Fin 3),
  fieldAt (mat as * mat bs) a = fieldAt (mat as) a * fieldAt (mat bs) a) 226

/- QSA-4: a positive threshold commutes with `within`. -/
#eval survives (∀ (xs : List ℤ) (c : Fin 8) (t : ℕ),
  thresh ((t : ℚ) + 1) (maskF (region c) (vec xs)) = region c ∩ thresh ((t : ℚ) + 1) (vec xs)) 227

/- Control, the non-rewrite: the top-`k` does not. -/
#eval refuted (∀ (xs : List ℤ) (c : Fin 8) (k : Fin 4),
  topk k.val (maskF (region c) (vec xs)) = region c ∩ topk k.val (vec xs)) 228

/-! ## Chains and the grounding automaton -/

/-- The move with a given index. -/
def mv (m : Fin 4) : Move :=
  match m.val with
  | 0 => .S
  | 1 => .F
  | 2 => .D
  | _ => .C

/-- The index of a move. -/
def idx : Move → ℕ
  | .S => 0
  | .F => 1
  | .D => 2
  | .C => 3

/-- A set of moves from four bits. -/
def moves (c : Fin 16) : Finset Move := univ.filter fun m ↦ c.val.testBit (idx m)

/-- The typed graph with the listed edges `(move, from, to)`. -/
def graph (es : List (Fin 4 × Fin 3 × Fin 3)) : TGraph (Fin 3) :=
  ⟨fun m u v ↦ decide (∃ e ∈ es, mv e.1 = m ∧ e.2.1 = u ∧ e.2.2 = v)⟩

/-- A chain from codes: the move taken and the vertex reached. -/
def chain (cs : List (Fin 4 × Fin 3)) : List (Move × Fin 3) := cs.map fun c ↦ (mv c.1, c.2)

/-- The listed edges and a chain's own from `u`: the chain is a chain of this graph. -/
def graphWith (es : List (Fin 4 × Fin 3 × Fin 3)) (u : Fin 3) (cs : List (Fin 4 × Fin 3)) :
    TGraph (Fin 3) :=
  graph (es ++ (List.zip (u :: cs.map Prod.snd) cs).map fun p ↦ (p.2.1, p.1, p.2.2))

/-- A chain the grounding production accepts, by construction: `k` resemblance moves, then a
witness (`C`, or `D` when `b` is false), through the listed vertices. -/
def grounded (k : Fin 4) (b : Bool) (vs : List (Fin 3)) : List (Fin 4 × Fin 3) :=
  ((List.range k.val).map fun i ↦ ((0 : Fin 4), vs.getD i 0)) ++
    [(if b then 3 else 2, vs.getD k.val 0)]

/- QSA-7: a chain is admissible iff the product walk reaches an accepting state. -/
#eval survives (∀ (es : List (Fin 4 × Fin 3 × Fin 3)) (u : Fin 3) (cs : List (Fin 4 × Fin 3)),
  decide (Admissible (graphWith es u cs) grounding u (chain cs)) =
    decide (∃ v q, prodOk (graphWith es u cs) grounding (u, grounding.start) (chain cs) (v, q) =
      true ∧ grounding.accept q = true)) 229

/- Control: the set `{S, C, D}` in place of the grammar, on a witness followed by resemblance:
order-blind, the set admits `CS` and `DS`, which the grammar rejects. -/
#eval refuted (∀ (es : List (Fin 4 × Fin 3 × Fin 3)) (u : Fin 3) (b : Bool) (v w : Fin 3),
  decide (Admissible (graphWith es u [(if b then 3 else 2, v), (0, w)]) grounding u
      (chain [(if b then 3 else 2, v), (0, w)])) =
    decide (Admissible (graphWith es u [(if b then 3 else 2, v), (0, w)]) (ofSet {.S, .C, .D}) u
      (chain [(if b then 3 else 2, v), (0, w)]))) 230

/- QSA-7: every prefix of an admissible chain leaves the automaton live, off its dead state. -/
#eval survives (∀ (k : Fin 4) (b : Bool) (vs : List (Fin 3)) (n : ℕ),
  grounding.run grounding.start (signature (chain ((grounded k b vs).take n))) ≠ 2) 231

/- Control: every chain's prefix is live. -/
#eval refuted (∀ cs : List (Fin 4 × Fin 3),
  grounding.run grounding.start (signature (chain cs)) ≠ 2) 232

/- QSA-7: the set is the one-state automaton: accepted iff every letter is in the set. -/
#eval survives (∀ (ws : List (Fin 4)) (c : Fin 16),
  decide ((ofSet (moves c)).Accepts (ws.map mv)) = decide (∀ m ∈ ws.map mv, m ∈ moves c)) 233

/- Control: some letter in the set, on a nonempty word. -/
#eval refuted (∀ (ws : List (Fin 4)) (c : Fin 16), ws ≠ [] →
  decide ((ofSet (moves c)).Accepts (ws.map mv)) = decide (∃ m ∈ ws.map mv, m ∈ moves c)) 234

/- QSA-7: a hypothetical edge only adds admissible chains. -/
#eval survives (∀ (es : List (Fin 4 × Fin 3 × Fin 3)) (k : Fin 4) (b : Bool) (vs : List (Fin 3))
    (u : Fin 3) (m : Fin 4) (a c : Fin 3),
  Admissible ((graphWith es u (grounded k b vs)).assume (mv m) a c) grounding u
    (chain (grounded k b vs))) 235

/- Control: the same chain over the listed edges alone, without its own: the edges it needs are
what the assumption supplied. -/
#eval refuted (∀ (es : List (Fin 4 × Fin 3 × Fin 3)) (k : Fin 4) (b : Bool) (vs : List (Fin 3))
    (u : Fin 3),
  Admissible (graph es) grounding u (chain (grounded k b vs))) 236

/-! ## Hypothetical edges on weights -/

/-- The weights with one assumed arc, `u → v` alone: the one-sided update. -/
def assumeArc (A : Matrix (Fin 3) (Fin 3) ℚ) (u v : Fin 3) (δ : ℚ) : Matrix (Fin 3) (Fin 3) ℚ :=
  of fun i j ↦ A i j + if i = u ∧ j = v then δ else 0

/-- The matrix with no edge between `u` and `v`. -/
def without (A : Matrix (Fin 3) (Fin 3) ℚ) (u v : Fin 3) : Matrix (Fin 3) (Fin 3) ℚ :=
  of fun i j ↦ if (i = u ∧ j = v) ∨ (i = v ∧ j = u) then 0 else A i j

/- QSA-9: a hypothetical edge is a rank-one update of the Laplacian along `e_u − e_v`. -/
#eval survives (∀ (as : List ℤ) (u v : Fin 3) (d : ℤ), u ≠ v →
  same (lap (assumeEdge (mat as) u v d))
    (lap (mat as) + (d : ℚ) • vecMulVec (dvec u v 1) (dvec u v 1)) = true) 237

/- Control: one arc alone is no such update. -/
#eval refuted (∀ (as : List ℤ) (u v : Fin 3) (d : ℤ), u ≠ v →
  same (lap (assumeArc (mat as) u v d))
    (lap (mat as) + (d : ℚ) • vecMulVec (dvec u v 1) (dvec u v 1)) = true) 238

/- QSA-9: a new signed edge is a rank-one update of the signed Laplacian along `e_u − σ e_v`. -/
#eval survives (∀ (as : List ℤ) (u v : Fin 3) (d : ℕ) (b : Bool), u ≠ v →
  same (signedLap (assumeEdge (without (symm as) u v) u v ((if b then 1 else -1) * d)))
    (signedLap (without (symm as) u v) +
      (d : ℚ) • vecMulVec (dvec u v (if b then 1 else -1)) (dvec u v (if b then 1 else -1))) =
    true) 239

/- Control: on a present edge of the other sign the absolute values do not add. -/
#eval refuted (∀ (as : List ℤ) (u v : Fin 3) (d : ℕ) (b : Bool), u ≠ v →
  same (signedLap (assumeEdge (symm as) u v ((if b then 1 else -1) * d)))
    (signedLap (symm as) +
      (d : ℚ) • vecMulVec (dvec u v (if b then 1 else -1)) (dvec u v (if b then 1 else -1))) =
    true) 240

/-- Camps from three bits. -/
def camps (c : Fin 8) : Fin 3 → ℚ := fun i ↦ if c.val.testBit i.val then 1 else -1

/-- A signed matrix balanced by the camps `s`, `|a_ij| s_i s_j`, with no edge between `u`, `v`. -/
def balancedBy (s : Fin 3 → ℚ) (as : List ℤ) (u v : Fin 3) : Matrix (Fin 3) (Fin 3) ℚ :=
  without (of fun i j ↦ |symm as i j| * s i * s j) u v

/-- Balanced by the given camps: the witness form of `Balanced`. -/
def balancedWith (s : Fin 3 → ℚ) (A : Matrix (Fin 3) (Fin 3) ℚ) : Bool :=
  (List.finRange 3).all fun i ↦ (List.finRange 3).all fun j ↦ decide (0 ≤ A i j * s i * s j)

/- QSA-9: a new edge whose sign agrees with the camps keeps the graph balanced by them. -/
#eval survives (∀ (c : Fin 8) (as : List ℤ) (u v : Fin 3) (d : ℕ),
  balancedWith (camps c)
    (assumeEdge (balancedBy (camps c) as u v) u v (camps c u * camps c v * d)) = true) 241

/- Control: the other sign, a contradiction between allies or support between foes. -/
#eval refuted (∀ (c : Fin 8) (as : List ℤ) (u v : Fin 3) (d : ℕ), u ≠ v →
  balancedWith (camps c)
    (assumeEdge (balancedBy (camps c) as u v) u v (-(camps c u * camps c v) * (d + 1))) = true) 242

/-! ## Sherman–Morrison on `Fin 2` -/

/-- A `2 × 2` matrix over ℚ from a list of ints. -/
def mat2 (xs : List ℤ) : Matrix (Fin 2) (Fin 2) ℚ :=
  of fun i j ↦ (xs.getD (2 * i.val + j.val) 0 : ℚ)

/-- A vector on `Fin 2`. -/
def vec2 (xs : List ℤ) : Fin 2 → ℚ := fun i ↦ (xs.getD i.val 0 : ℚ)

/-- The determinant of a `2 × 2` matrix. -/
def det2 (M : Matrix (Fin 2) (Fin 2) ℚ) : ℚ := M 0 0 * M 1 1 - M 0 1 * M 1 0

/-- The explicit inverse of a `2 × 2` matrix, for a nonzero determinant. -/
def inv2 (M : Matrix (Fin 2) (Fin 2) ℚ) : Matrix (Fin 2) (Fin 2) ℚ :=
  (1 / det2 M) • !![M 1 1, -M 0 1; -M 1 0, M 0 0]

/- QSA-9, Sherman–Morrison: the updated matrix times the formula is the identity. -/
#eval survives (∀ (ms us vs : List ℤ) (c : ℤ),
  (det2 (mat2 ms) ≠ 0 ∧ 1 + (c : ℚ) * (vec2 vs ⬝ᵥ (inv2 (mat2 ms) *ᵥ vec2 us)) ≠ 0) →
    (mat2 ms + (c : ℚ) • vecMulVec (vec2 us) (vec2 vs)) *
      (inv2 (mat2 ms) - ((c : ℚ) / (1 + c * (vec2 vs ⬝ᵥ (inv2 (mat2 ms) *ᵥ vec2 us)))) •
        vecMulVec (inv2 (mat2 ms) *ᵥ vec2 us) (vec2 vs ᵥ* inv2 (mat2 ms))) = 1) 243

/- Control: the correction added instead of subtracted. -/
#eval refuted (∀ (ms us vs : List ℤ) (c : ℤ),
  (det2 (mat2 ms) ≠ 0 ∧ 1 + (c : ℚ) * (vec2 vs ⬝ᵥ (inv2 (mat2 ms) *ᵥ vec2 us)) ≠ 0) →
    (mat2 ms + (c : ℚ) • vecMulVec (vec2 us) (vec2 vs)) *
      (inv2 (mat2 ms) + ((c : ℚ) / (1 + c * (vec2 vs ⬝ᵥ (inv2 (mat2 ms) *ᵥ vec2 us)))) •
        vecMulVec (inv2 (mat2 ms) *ᵥ vec2 us) (vec2 vs ᵥ* inv2 (mat2 ms))) = 1) 244

end Palace.Query.Attack
