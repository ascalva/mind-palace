module

public import Palace.Magnetic
public import PalaceTest.Balance
public meta import Palace.Magnetic
public meta import PalaceTest.Balance

/-!
# Attacks on `Palace.Magnetic`

The Plausible attacks and negative controls for `Palace/Magnetic.lean`. They run when this module
builds (`lake test`); the library itself runs no code at build time.

The operator is complex and its transports are exponentials, which do not run. The executable
instance of each law therefore fixes the transports at their exact values, `e^{i·0} = 1` and
`e^{iπ} = −1` (the values the BRG-7 fibers rest on), or tests the combinatorial content: the sign
of every cycle, circulations, covering relations and clocks.
-/

@[expose] public section

open Matrix Finset Palace.Attack

namespace Palace.Magnetic.Attack

/-- The magnetic operator with its transports given as exact values, on `Fin 5` over ℚ. -/
def magLapQ (w : Matrix (Fin 5) (Fin 5) ℚ) (t : Fin 5 → Fin 5 → ℚ) : Matrix (Fin 5) (Fin 5) ℚ :=
  diagonal (degree w) - of fun u v ↦ w u v * t u v

/-- Every simple cycle of the support, of length three or more, has a positive product of
weights: the sign connection's holonomy is `1` on each, so on every closed walk. -/
def cyclesPositive (A : Matrix (Fin 5) (Fin 5) ℚ) : Bool :=
  ((List.finRange 5).sublists.filter (3 ≤ ·.length)).all fun s ↦
    s.permutations.all fun c ↦
      let steps := c.zip (c.rotate 1)
      !(steps.all fun e ↦ A e.1 e.2 != 0) || decide (0 < (steps.map fun e ↦ A e.1 e.2).prod)

/-- No self-loop is negative. -/
def loopsNonneg (A : Matrix (Fin 5) (Fin 5) ℚ) : Bool :=
  (List.finRange 5).all fun u ↦ decide (0 ≤ A u u)

/-- A digraph on `Fin 5` from bits, no loops. -/
def dig (es : List Bool) (u v : Fin 5) : Prop := es.getD (5 * u.val + v.val) false = true ∧ u ≠ v

instance (es : List Bool) : DecidableRel (dig es) := fun _ _ ↦ inferInstanceAs (Decidable (_ ∧ _))

/-- The circulation of a walk given by its vertices. -/
def circ (es : List Bool) (l : List (Fin 5)) : ℤ :=
  ((l.zip l.tail).map fun e ↦ arrow (dig es) e.1 e.2).sum

/-- The strict order of a random DAG on `Fin 5`: arcs only upward, then closed under paths. -/
def ltOf (es : List Bool) : Fin 5 → Fin 5 → Bool := Id.run do
  let mut r : Fin 5 → Fin 5 → Bool := fun u v ↦ decide (u < v) && es.getD (5 * u.val + v.val) false
  for k in List.finRange 5 do
    r := fun u v ↦ r u v || (r u k && r k v)
  return r

/-- The covering relation of `ltOf`. -/
def covOf (es : List Bool) (u v : Fin 5) : Bool :=
  ltOf es u v && !(List.finRange 5).any fun w ↦ ltOf es u w && ltOf es w v

/-- Levels `ℓ` in `{0, 1, 2}` from a list. -/
def lvl (ls : List ℕ) (u : Fin 5) : ℤ := (ls.getD u 0 % 3 : ℕ)

/-- The arcs of a graded digraph from bits, on consecutive levels only. -/
def gradedDig (es : List Bool) (ls : List ℕ) (u v : Fin 5) : Prop :=
  dig es u v ∧ lvl ls v = lvl ls u + 1

instance (es : List Bool) (ls : List ℕ) : DecidableRel (gradedDig es ls) :=
  fun _ _ ↦ inferInstanceAs (Decidable (_ ∧ _))

/-- Arcs on every rising pair of levels, not only consecutive ones: not graded. -/
def risingDig (es : List Bool) (ls : List ℕ) (u v : Fin 5) : Prop :=
  dig es u v ∧ lvl ls u < lvl ls v

instance (es : List Bool) (ls : List ℕ) : DecidableRel (risingDig es ls) :=
  fun _ _ ↦ inferInstanceAs (Decidable (_ ∧ _))

/-! ### Attacks -/

/- BRG-7: at transport `1` the magnetic operator is the Laplacian. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℤ),
  magLapQ (ofArcs es) (fun _ _ ↦ 1) = lap (ofArcs es)) 193

/- BRG-7 control: at transport `−1` everywhere it is the signless `D + A`, not the Laplacian. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ),
  magLapQ (ofArcs es) (fun _ _ ↦ -1) = lap (ofArcs es)) 194

/- BRG-7: weights `|A|` with transport `−1` on the negative entries give the signed Laplacian. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℤ),
  magLapQ ((ofEdges es).map abs) (fun u v ↦ if ofEdges es u v < 0 then -1 else 1) =
    signedLap (ofEdges es)) 195

/- BRG-7 control: the sign put on the positive entries instead. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ),
  magLapQ ((ofEdges es).map abs) (fun u v ↦ if 0 < ofEdges es u v then -1 else 1) =
    signedLap (ofEdges es)) 196

/- BRG-7, the kernel theorem at ℤ/2: on a connected support, balanced iff every cycle's sign
holonomy is `1` and no self-loop is negative. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℤ),
  connected (ofEdges es) = true →
    (BalancedB (ofEdges es) ↔ (cyclesPositive (ofEdges es) && loopsNonneg (ofEdges es)) = true))
  197

/- BRG-7 control: without the loop condition. A graph balanced by construction with one negative
self-loop added has every cycle positive and is not balanced. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ bs : List Bool,
  connected (balancedOf es bs) = true →
    (BalancedB (balancedOf es bs - diagonal (Pi.single 0 1)) ↔
      cyclesPositive (balancedOf es bs - diagonal (Pi.single 0 1)) = true)) 198

/- §2.2 (b): a triangle of one-way edges has odd circulation. -/
#eval survives (∀ es : List Bool, decide (∀ i j k : Fin 5, Xor (dig es i j) (dig es j i) →
  Xor (dig es j k) (dig es k j) → Xor (dig es k i) (dig es i k) →
    Odd (arrow (dig es) i j + arrow (dig es) j k + arrow (dig es) k i)) = true) 199

/- §2.2 (b) control: not always `±1`; a directed 3-cycle has circulation `±3`. -/
#eval refuted (∀ es : List Bool, decide (∀ i j k : Fin 5, Xor (dig es i j) (dig es j i) →
  Xor (dig es j k) (dig es k j) → Xor (dig es k i) (dig es i k) →
    |arrow (dig es) i j + arrow (dig es) j k + arrow (dig es) k i| = 1) = true) 200

/- §2.2 (c): the covering relation of a random DAG's order has no triangle. -/
#eval survives (∀ es : List Bool, decide (∀ i j k : Fin 5,
  ¬((covOf es i j || covOf es j i) && (covOf es j k || covOf es k j) &&
    (covOf es i k || covOf es k i)) = true) = true) 201

/- §2.2 (c) control: the order itself, its transitive closure, has triangles. -/
#eval refuted (∀ es : List Bool, decide (∀ i j k : Fin 5,
  ¬((ltOf es i j || ltOf es j i) && (ltOf es j k || ltOf es k j) &&
    (ltOf es i k || ltOf es k i)) = true) = true) 202

/- §2.4 (iii): on a graded digraph the direction of every skeleton edge is the clock's rise,
`arrow = ℓ v − ℓ u`, so every charge is a coboundary. -/
#eval survives (∀ es : List Bool, ∀ ls : List ℕ, decide (∀ u v : Fin 5,
  gradedDig es ls u v ∨ gradedDig es ls v u →
    arrow (gradedDig es ls) u v = lvl ls v - lvl ls u) = true) 203

/- §2.4 (iii) control: arcs across two levels break it. -/
#eval refuted (∀ es : List Bool, ∀ ls : List ℕ, decide (∀ u v : Fin 5,
  risingDig es ls u v ∨ risingDig es ls v u →
    arrow (risingDig es ls) u v = lvl ls v - lvl ls u) = true) 204

/- §2.1: walking backwards negates the circulation. -/
#eval survives (∀ es : List Bool, ∀ l : List (Fin 5), circ es l.reverse = -circ es l) 205

/- §2.1 control: circulation is not reversal-invariant. -/
#eval refuted (∀ es : List Bool, ∀ l : List (Fin 5), circ es l.reverse = circ es l) 206

end Palace.Magnetic.Attack
