module

public import Palace.Sentence.Defs
public import Mathlib.LinearAlgebra.Matrix.PosDef
public import Mathlib.LinearAlgebra.Matrix.NonsingularInverse

/-!
# The query sentence algebra, the statements

The laws of `Palace/Sentence.lean` the ledger cites (docs/LAWS.md §XI, QSA-1 to QSA-9), each with
its proof left as `sorry`, over the model of `Palace/Sentence/Defs.lean`. `lake comparator`
checks that the `Palace` library proves each one exactly as stated here, from the standard axioms
alone. What the statements cover: the nouns' algebra on kernels, fields and regions (QSA-1 to
QSA-4) as `core/sentence/algebra.py` computes it; admissibility of a sentence as
`core/sentence/types.py` checks it (QSA-5); the chain language as `core/sentence/automaton.py`
walks it (QSA-7); the mode table of `core/query.py` (QSA-8); and the response to a hypothetical
edge as `core/sentence/execute.py`'s overlay classifies it (QSA-9). QSA-6, noninterference of the
abstract evaluation model, stays a design theorem: no code transcribes it yet.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Query

section Kernels
variable {V : Type*}
/-- **QSA-1** `and` keeps the cone: the Schur product theorem. -/
theorem and_posSemidef {A B : Matrix V V ℝ} (hA : A.PosSemidef) (hB : B.PosSemidef) :
    (A ⊙ B).PosSemidef :=
  sorry

/-- **QSA-1** `or` keeps the cone. -/
theorem or_posSemidef {A B : Matrix V V ℝ} (hA : A.PosSemidef) (hB : B.PosSemidef) :
    (A + B).PosSemidef :=
  sorry

/-- **QSA-2, QSA-10** `within` keeps the cone. -/
theorem posSemidef_mask [Finite V] [DecidableEq V] {K : Matrix V V ℝ} (hK : K.PosSemidef)
    (S : Finset V) : (mask S K).PosSemidef :=
  sorry

variable [DecidableEq V] {R : Type*}
/-- **QSA-2, QSA-10** `within` distributes over `or`. -/
theorem mask_add [AddZeroClass R] (S : Finset V) (A B : Matrix V V R) :
    mask S (A + B) = mask S A + mask S B :=
  sorry

/-- **QSA-2, QSA-10** `within` distributes over `and`. -/
theorem mask_hadamard [MulZeroClass R] (S : Finset V) (A B : Matrix V V R) :
    mask S (A ⊙ B) = mask S A ⊙ mask S B :=
  sorry

/-- **QSA-2, QSA-10** adjectives stack by intersection. -/
theorem mask_mask [Zero R] (S T : Finset V) (A : Matrix V V R) :
    mask S (mask T A) = mask (S ∩ T) A :=
  sorry

end Kernels
section Fields
variable {V R : Type*}
/-- **QSA-3** the field of `and` at an anchor is the product of the fields: HYBRID's score. -/
theorem fieldAt_hadamard [Mul R] (A B : Matrix V V R) (a : V) :
    fieldAt (A ⊙ B) a = fieldAt A a * fieldAt B a :=
  sorry

/-- **QSA-3** the field of `or` at an anchor is the sum of the fields. -/
theorem fieldAt_add [Add R] (A B : Matrix V V R) (a : V) :
    fieldAt (A + B) a = fieldAt A a + fieldAt B a :=
  sorry

/-- **QSA-3** the field of `within S` at an anchor inside the region is the masked field; at an
anchor outside it is nothing. -/
theorem fieldAt_mask [DecidableEq V] [Zero R] (S : Finset V) (K : Matrix V V R) (a : V) :
    fieldAt (mask S K) a = if a ∈ S then maskF S (fieldAt K a) else 0 :=
  sorry

/-- **QSA-4** a positive threshold commutes with `within`: masks may pass it. -/
theorem thresh_maskF [Fintype V] [DecidableEq V] [LinearOrder R] [Zero R] {t : R} (ht : 0 < t)
    (S : Finset V) (f : V → R) : thresh t (maskF S f) = S ∩ thresh t f :=
  sorry

/-- **QSA-4** the top-`k` does not commute with `within`: on `(3, 2, 1)`, the best inside `{1, 2}`
is `1`, but the best overall is `0`, outside the region. Ranking is last. -/
theorem topk_maskF_ne :
    topk 1 (maskF ({1, 2} : Finset (Fin 3)) ![(3 : ℤ), 2, 1]) ≠
      ({1, 2} : Finset (Fin 3)) ∩ topk 1 ![(3 : ℤ), 2, 1] :=
  sorry

end Fields
namespace Sentence
variable {Rg H : Type*} {g : List CQ.Scope}
/-- **QSA-5** `and` is admissible iff both halves are: the scope check is clause-wise. -/
theorem admissible_and {s t : Sentence Rg H} :
    Admissible g (.and s t) ↔ Admissible g s ∧ Admissible g t :=
  sorry

/-- **QSA-5** `assume` needs a granted plane that names the overlay stratum. -/
theorem admissible_assume_overlay {h : H} {s : Sentence Rg H} (ha : Admissible g (.assume h s)) :
    ∃ p ∈ g, CQ.Stratum.hypothetical ∈ p.sigma :=
  sorry

/-- **QSA-5** so the Ambassador's grant admits no hypothetical. -/
theorem ambassador_no_assume (h : H) (s : Sentence Rg H) :
    ¬ Admissible CQ.ambassador (.assume h s) :=
  sorry

/-- **SCO-9** so the guest's grant admits no hypothetical (QSA-5). -/
theorem guest_no_assume (h : H) (s : Sentence Rg H) :
    ¬ Admissible CQ.guest (.assume h s) :=
  sorry

/-- **QSA-5** every sentence admissible under a grant is admissible under the grant with the
overlay named: the owner's grant widens, never narrows. -/
theorem admissible_overlayGrant_of_admissible {s : Sentence Rg H} (h : Admissible g s) :
    Admissible (CQ.overlayGrant g) s :=
  sorry

/-- **QSA-5** under a grant whose every plane names the overlay, `assume h s` is admissible iff
`s` is: a hypothetical costs its body's admission and nothing more. -/
theorem admissible_assume_iff_overlay (hg : ∀ p ∈ g, CQ.Stratum.hypothetical ∈ p.sigma)
    {h : H} {s : Sentence Rg H} : Admissible g (.assume h s) ↔ Admissible g s :=
  sorry

/-- **QSA-5** the owner's grant: the Ambassador's planes with the overlay accept `assume h s`
exactly when they accept `s`. -/
theorem ambassadorOverlay_admits_assume_iff {h : H} {s : Sentence Rg H} :
    Admissible CQ.ambassadorOverlay (.assume h s) ↔ Admissible CQ.ambassadorOverlay s :=
  sorry

/-- **QSA-5** the owner's grant reaches the world on no plane. -/
theorem ambassadorOverlay_no_world : ∀ p ∈ CQ.ambassadorOverlay, p.authority.world = 0 :=
  sorry

/-- **QSA-5** a result under `assume` is never `Inv`: the hypothesis is in its type. -/
theorem not_isInv_assume (h : H) (s : Sentence Rg H) : ¬ IsInv (.assume h s) :=
  sorry

end Sentence
section Chains
variable {V Q : Type*} [DecidableEq V] [DecidableEq Q]
/-- **QSA-7** a chain is admissible iff the product walk from `(u, start)` reaches an accepting
state: the regular-path-query evaluation, exact. -/
theorem admissible_iff_prodOk (G : TGraph V) (A : Auto Q) (u : V) (c : List (Move × V)) :
    Admissible G A u c ↔ ∃ v q, prodOk G A (u, A.start) c (v, q) = true ∧ A.accept q = true :=
  sorry

omit [DecidableEq V] [DecidableEq Q] in
/-- **QSA-7** pruning at a dead state loses no admissible chain: every prefix of an admissible chain
leaves the automaton live. -/
theorem prune_sound {G : TGraph V} {A : Auto Q} {u : V} {p c : List (Move × V)}
    (h : Admissible G A u (p ++ c)) : A.Live (A.run A.start (signature p)) :=
  sorry

omit [DecidableEq Q] in
/-- **QSA-7** a hypothetical edge only adds admissible chains. -/
theorem admissible_assume {G : TGraph V} {A : Auto Q} {u : V} {c : List (Move × V)}
    (h : Admissible G A u c) (m : Move) (a b : V) : Admissible (G.assume m a b) A u c :=
  sorry

omit [DecidableEq V] [DecidableEq Q] in
/-- **QSA-7** the set `E` is the one-state automaton: it accepts a word iff every letter is in `E`,
whatever the order. The set is the order-blind shadow of the language. -/
theorem ofSet_accepts (E : Finset Move) (w : List Move) :
    (ofSet E).Accepts w ↔ ∀ m ∈ w, m ∈ E :=
  sorry

end Chains
/-- **QSA-8** `mode_of ∘ required`, verb by verb: SEARCH is semantic, temporal with history;
DIFFUSE, HYBRID, RELATED and REACH are structural; HISTORY is temporal; ORIGIN is causal; CAPTURE is
semantic. The design note reads DIFFUSE, HYBRID and RELATED off this table: typed `{F}`, they
walk the similarity backbone or the relation edges, so the verb's letter is not the noun's. -/
theorem modeOf_required (v : CQ.Verb) (strata : List CQ.Stratum) (h a : Bool) {r : CQ.Scope}
    (hr : CQ.required v strata h a = .ok r) :
    modeOf r = match v with
      | .search => if h then .temporal else .semantic
      | .diffuse | .hybrid | .related | .reach => .structural
      | .history => .temporal
      | .origin => .causal
      | .capture => .semantic :=
  sorry

section Response
variable {V : Type*} [DecidableEq V]
section Generic
variable {R : Type*} [CommRing R]
/-- **QSA-9** a hypothetical edge is a rank-one update of the Laplacian along `e_u − e_v`. -/
theorem lap_assumeEdge [Fintype V] (A : Matrix V V R) {u v : V} (huv : u ≠ v) (δ : R) :
    lap (assumeEdge A u v δ) = lap A + δ • vecMulVec (dvec u v 1) (dvec u v 1) :=
  sorry

/-- **QSA-9** a new signed edge is a rank-one update of the signed Laplacian along `e_u − σ e_v`:
the difference for a supporting edge, the sum for a contradiction. -/
theorem signedLap_assumeEdge [Fintype V] [LinearOrder R] [IsOrderedRing R] (A : Matrix V V R)
    {u v : V} (huv : u ≠ v) (h0 : A u v = 0) (h0' : A v u = 0) {σ δ : R} (hσ : σ = 1 ∨ σ = -1)
    (hδ : 0 ≤ δ) :
    signedLap (assumeEdge A u v (σ * δ)) =
      signedLap A + δ • vecMulVec (dvec u v σ) (dvec u v σ) :=
  sorry

end Generic
variable [Fintype V]
/-- **QSA-9** (CND-2 forward) adding weight to an edge raises no effective resistance between
vertices the support already joins: each falls or holds. -/
theorem rEff_assumeEdge_le {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) {u v : V}
    {δ : ℝ} (hδ : 0 ≤ δ) (hA' : (assumeEdge A u v δ).IsSymm) {i j : V}
    (hr : (support A).Reachable i j) :
    rEff (lapPinv (assumeEdge A u v δ) hA') i j ≤ rEff (lapPinv A hA) i j :=
  sorry

/-- **QSA-9** (CND-2 backward) removing weight from an edge lowers no effective resistance between
vertices the weakened support still joins: each rises or holds, so an assumption can raise
resistance. -/
theorem rEff_le_assumeEdge {A : Matrix V V ℝ} (hA : A.IsSymm) {u v : V} {δ : ℝ} (hδ : δ ≤ 0)
    (hA' : (assumeEdge A u v δ).IsSymm) (hw : ∀ i j, 0 ≤ assumeEdge A u v δ i j) {i j : V}
    (hr : (support (assumeEdge A u v δ)).Reachable i j) :
    rEff (lapPinv A hA) i j ≤ rEff (lapPinv (assumeEdge A u v δ) hA') i j :=
  sorry

omit [Fintype V] in
/-- **QSA-9** a new signed edge whose sign agrees with the camps keeps the graph balanced, by the
same camps (the converse for those camps is `camps_assumeEdge_iff`). -/
theorem balanced_assumeEdge {A : Matrix V V ℝ} {s : V → ℝ} (hs : ∀ i, s i = 1 ∨ s i = -1)
    (hA : ∀ i j, 0 ≤ A i j * s i * s j) {u v : V} {σ δ : ℝ} (hδ : 0 ≤ δ)
    (hσ : 0 ≤ σ * s u * s v) : Balanced (assumeEdge A u v (σ * δ)) :=
  sorry

omit [Fintype V] in
/-- **QSA-9** the camps that balance a graph still balance it with a new signed edge, on a pair
that had none, iff the edge's sign agrees with them. -/
theorem camps_assumeEdge_iff {A : Matrix V V ℝ} {s : V → ℝ} (hA : ∀ i j, 0 ≤ A i j * s i * s j)
    {u v : V} (hu : A u v = 0) {σ δ : ℝ} (hδ : 0 < δ) :
    (∀ i j, 0 ≤ assumeEdge A u v (σ * δ) i j * s i * s j) ↔ 0 ≤ σ * s u * s v :=
  sorry

omit [Fintype V] in
/-- **QSA-9** a new signed edge whose sign disagrees with the camps, between two notes the graph
already joins by a path, is frustrated: no camps balance it. Where the notes are not joined, other
camps can balance it, so the path is the hypothesis, not a convenience. -/
theorem not_balanced_assumeEdge_of_reachable {A : Matrix V V ℝ} {s : V → ℝ}
    (hs : ∀ i, s i = 1 ∨ s i = -1) (hA : ∀ i j, 0 ≤ A i j * s i * s j) {u v : V}
    (hu : A u v = 0) (hv : A v u = 0) (hr : (support A).Reachable u v) {σ δ : ℝ} (hδ : 0 < δ)
    (hσ : σ * s u * s v < 0) : ¬ Balanced (assumeEdge A u v (σ * δ)) :=
  sorry

/-- **QSA-9** Sherman–Morrison: the exact response of an inverse to a rank-one update, so of a
kernel `M⁻¹` to a hypothetical edge. -/
theorem inv_add_vecMulVec {M : Matrix V V ℝ} (hM : IsUnit M.det) (u v : V → ℝ) {c : ℝ}
    (hc : 1 + c * (v ⬝ᵥ (M⁻¹ *ᵥ u)) ≠ 0) :
    (M + c • vecMulVec u v)⁻¹ =
      M⁻¹ - (c / (1 + c * (v ⬝ᵥ (M⁻¹ *ᵥ u)))) • vecMulVec (M⁻¹ *ᵥ u) (v ᵥ* M⁻¹) :=
  sorry

end Response
end Palace.Query
