module

public import Palace.Sentence.Defs
public import Palace.Rayleigh
public import Palace.Balance
public import Palace.Scope
public import Mathlib.Analysis.Matrix.Order
public import Mathlib.LinearAlgebra.Matrix.NonsingularInverse

/-!
# The query sentence algebra: the composition laws

`docs/design-notes/dn-query-sentence-algebra.md` proves its design before any code parses a
sentence. The laws, each the licence for one rule of the grammar or one rewrite of the planner:

* QSA-1, the connectives on kernels: `and` is the Schur product and `or` the sum, both inside the
  positive semidefinite cone (Mathlib's `PosSemidef.hadamard`, `PosSemidef.add`).
* QSA-2, the adjective: `within S` is a congruence by a projection, so it keeps the cone;
  it distributes over `and` and `or`, and adjectives stack by intersection. The planner's pushdown.
* QSA-3, the anchor: the field of `and` at an anchor is the pointwise product of the fields, and
  of `within` the masked field. HYBRID's score is a product of two columns, never an `n × n`
  Schur product.
* QSA-4, the one non-rewrite: a threshold commutes with `within`; the top-`k` does not. Ranking is
  last.
* QSA-5, admissibility is clause-wise: a sentence is admissible under a grant iff each clause is;
  `assume` needs a granted plane that names the overlay, which the Ambassador's does not.
* QSA-6, noninterference composes: when each clause reads only its strata, a sentence reads only
  their union, and a store's overlay is invisible to a sentence outside the modality.
* QSA-7, the chain language: a chain is admissible iff the product walk reaches an accepting
  state, pruning at a dead state loses no admissible chain, the set `E` is the one-state
  automaton, and a hypothetical edge only adds admissible chains.
* QSA-8, the mode table: `mode_of ∘ required`, verb by verb, as the code has it.
* QSA-9, the response to a hypothetical edge: a rank-one update of the Laplacian along
  `e_u − e_v`, of the signed Laplacian along `e_u − σ e_v`; adding weight lowers every effective
  resistance and removing it raises every one (CND-2 both ways); a contradiction is consistent
  exactly when its sign matches the camps, and otherwise lifts the zero mode (LAP-5, LAP-6);
  the inverse's exact response is Sherman–Morrison.

The laws are design theorems: no code relies on them yet, so the ledger has no rows and the
comparator does not judge them; the kernel checkers replay them.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Query

/-! ## QSA-1, QSA-2: the cone under the connectives and the adjective -/

section Kernels

variable {V : Type*}

/-- **QSA-1** `and` keeps the cone: the Schur product theorem. -/
theorem and_posSemidef {A B : Matrix V V ℝ} (hA : A.PosSemidef) (hB : B.PosSemidef) :
    (A ⊙ B).PosSemidef :=
  hA.hadamard hB

/-- **QSA-1** `or` keeps the cone. -/
theorem or_posSemidef {A B : Matrix V V ℝ} (hA : A.PosSemidef) (hB : B.PosSemidef) :
    (A + B).PosSemidef :=
  hA.add hB

/-- `within S` is the congruence by the projection onto the region. -/
theorem mask_eq_diagonal_mul_mul [Fintype V] [DecidableEq V] {R : Type*} [CommRing R]
    (S : Finset V) (K : Matrix V V R) :
    mask S K = diagonal (ind S) * K * diagonal (ind S) := by
  ext i j
  simp only [mask, of_apply, mul_diagonal, diagonal_mul, ind]
  by_cases hi : i ∈ S <;> by_cases hj : j ∈ S <;> simp [hi, hj]

/-- **QSA-2** `within` keeps the cone. -/
theorem posSemidef_mask [Finite V] [DecidableEq V] {K : Matrix V V ℝ} (hK : K.PosSemidef)
    (S : Finset V) : (mask S K).PosSemidef := by
  have := Fintype.ofFinite V
  rw [mask_eq_diagonal_mul_mul]
  have h := hK.conjTranspose_mul_mul_same (diagonal (ind S))
  rwa [conjTranspose_eq_transpose_of_trivial, diagonal_transpose] at h

variable [DecidableEq V] {R : Type*}

/-- **QSA-2** `within` distributes over `or`. -/
theorem mask_add [AddZeroClass R] (S : Finset V) (A B : Matrix V V R) :
    mask S (A + B) = mask S A + mask S B := by
  ext i j
  by_cases h : i ∈ S ∧ j ∈ S <;> simp [mask, h]

/-- **QSA-2** `within` distributes over `and`. -/
theorem mask_hadamard [MulZeroClass R] (S : Finset V) (A B : Matrix V V R) :
    mask S (A ⊙ B) = mask S A ⊙ mask S B := by
  ext i j
  by_cases h : i ∈ S ∧ j ∈ S <;> simp [mask, h]

/-- **QSA-2** adjectives stack by intersection. -/
theorem mask_mask [Zero R] (S T : Finset V) (A : Matrix V V R) :
    mask S (mask T A) = mask (S ∩ T) A := by
  ext i j
  by_cases hi : i ∈ S <;> by_cases hj : j ∈ S <;> by_cases hi' : i ∈ T <;> by_cases hj' : j ∈ T <;>
    simp [mask, hi, hj, hi', hj']

/-- `within` everything is nothing. -/
theorem mask_univ [Fintype V] [Zero R] (A : Matrix V V R) : mask univ A = A := by
  ext i j
  simp [mask]

/-- `within` commutes with a scalar. -/
theorem mask_smul [MulZeroClass R] (S : Finset V) (c : R) (A : Matrix V V R) :
    mask S (c • A) = c • mask S A := by
  ext i j
  by_cases h : i ∈ S ∧ j ∈ S <;> simp [mask, h]

end Kernels

/-! ## QSA-3, QSA-4: the anchor's field, the threshold and the top-`k` -/

section Fields

variable {V R : Type*}

/-- **QSA-3** the field of `and` at an anchor is the product of the fields: HYBRID's score. -/
theorem fieldAt_hadamard [Mul R] (A B : Matrix V V R) (a : V) :
    fieldAt (A ⊙ B) a = fieldAt A a * fieldAt B a := by
  ext j
  simp [fieldAt, hadamard_apply]

/-- **QSA-3** the field of `or` at an anchor is the sum of the fields. -/
theorem fieldAt_add [Add R] (A B : Matrix V V R) (a : V) :
    fieldAt (A + B) a = fieldAt A a + fieldAt B a := by
  ext j
  simp [fieldAt]

/-- **QSA-3** the field of `within S` at an anchor inside the region is the masked field; at an
anchor outside it is nothing. -/
theorem fieldAt_mask [DecidableEq V] [Zero R] (S : Finset V) (K : Matrix V V R) (a : V) :
    fieldAt (mask S K) a = if a ∈ S then maskF S (fieldAt K a) else 0 := by
  ext j
  by_cases ha : a ∈ S <;> by_cases hj : j ∈ S <;> simp [fieldAt, mask, maskF, ha, hj]

/-- The field is the kernel applied to the anchor's indicator. -/
theorem fieldAt_eq_mulVec [Fintype V] [DecidableEq V] [NonAssocSemiring R] (K : Matrix V V R)
    (a : V) : fieldAt K a = K *ᵥ Pi.single a 1 := by
  rw [mulVec_single_one]
  rfl

/-- **QSA-4** a positive threshold commutes with `within`: masks may pass it. -/
theorem thresh_maskF [Fintype V] [DecidableEq V] [LinearOrder R] [Zero R] {t : R} (ht : 0 < t)
    (S : Finset V) (f : V → R) : thresh t (maskF S f) = S ∩ thresh t f := by
  ext i
  simp only [thresh, mem_filter, mem_univ, true_and, mem_inter]
  by_cases hi : i ∈ S
  · simp [maskF, hi]
  · simp [maskF, hi, not_le.mpr ht]

/-- **QSA-4** the top-`k` does not commute with `within`: on `(3, 2, 1)`, the best inside `{1, 2}`
is `1`, but the best overall is `0`, outside the region. Ranking is last. -/
theorem topk_maskF_ne :
    topk 1 (maskF ({1, 2} : Finset (Fin 3)) ![(3 : ℤ), 2, 1]) ≠
      ({1, 2} : Finset (Fin 3)) ∩ topk 1 ![(3 : ℤ), 2, 1] := by
  decide

end Fields

/-! ## QSA-5: admissibility is clause-wise -/

namespace Sentence

variable {Rg H : Type*} {g : List CQ.Scope}

/-- **QSA-5** `and` is admissible iff both halves are: the scope check is clause-wise. -/
theorem admissible_and {s t : Sentence Rg H} :
    Admissible g (.and s t) ↔ Admissible g s ∧ Admissible g t := by
  simp only [Admissible, reqs, List.forall_mem_append]

theorem admissible_or {s t : Sentence Rg H} :
    Admissible g (.or s t) ↔ Admissible g s ∧ Admissible g t := by
  simp only [Admissible, reqs, List.forall_mem_append]

theorem admissible_seq {s t : Sentence Rg H} :
    Admissible g (.seq s t) ↔ Admissible g s ∧ Admissible g t := by
  simp only [Admissible, reqs, List.forall_mem_append]

theorem admissible_within {r : Rg} {s : Sentence Rg H} :
    Admissible g (.within r s) ↔ Admissible g s :=
  Iff.rfl

/-- QSA-5 the type checker is local: a sentence is admissible iff each clause's required scope
is admitted, with the overlay stratum added to the clauses under `assume`. -/
theorem admissible_iff_clauses {s : Sentence Rg H} :
    Admissible g s ↔ ∀ r ∈ s.reqs, CQ.admits g r :=
  Iff.rfl

/-- The overlay does not change a scope's mode. -/
theorem modeOf_withOverlay (r : CQ.Scope) : modeOf (withOverlay r) = modeOf r := rfl

/-- A sentence has a clause, so requires a scope. -/
theorem reqs_ne_nil (s : Sentence Rg H) : s.reqs ≠ [] := by
  induction s with
  | clause c => simp [reqs]
  | and s t hs _ | or s t hs _ | seq s t hs _ => simp [reqs, hs]
  | within r s hs => simpa [reqs] using hs
  | assume h s hs => simpa [reqs] using hs

/-- **QSA-5** `assume` needs a granted plane that names the overlay stratum. -/
theorem admissible_assume_overlay {h : H} {s : Sentence Rg H} (ha : Admissible g (.assume h s)) :
    ∃ p ∈ g, CQ.Stratum.hypothetical ∈ p.sigma := by
  obtain ⟨r, hr⟩ := List.exists_mem_of_ne_nil _ (reqs_ne_nil s)
  obtain ⟨p, hp, hle⟩ := ha (withOverlay r) (List.mem_map_of_mem hr)
  exact ⟨p, hp, hle.1 (mem_insert_self _ _)⟩

/-- The Ambassador's three planes name the overlay on none. -/
theorem ambassador_no_overlay : ∀ p ∈ CQ.ambassador, CQ.Stratum.hypothetical ∉ p.sigma := by
  decide

/-- **QSA-5** so the Ambassador's grant admits no hypothetical. -/
theorem ambassador_no_assume (h : H) (s : Sentence Rg H) :
    ¬ Admissible CQ.ambassador (.assume h s) := by
  intro ha
  obtain ⟨p, hp, hmem⟩ := admissible_assume_overlay ha
  exact ambassador_no_overlay p hp hmem

/-- A result is `Inv` iff both halves of a connective are. -/
theorem isInv_and {s t : Sentence Rg H} : IsInv (.and s t) ↔ IsInv s ∧ IsInv t := by
  simp [IsInv, hyps]

/-- **QSA-5** a result under `assume` is never `Inv`: the hypothesis is in its type. -/
theorem not_isInv_assume (h : H) (s : Sentence Rg H) : ¬ IsInv (.assume h s) := by
  simp [IsInv, hyps]

/-- The hypotheses of a connective are both halves' in order. -/
theorem hyps_and {s t : Sentence Rg H} : (Sentence.and s t).hyps = s.hyps ++ t.hyps := rfl

end Sentence

/-! ## QSA-6: noninterference composes -/

namespace Model

variable {Rg H D R : Type*}

/-- QSA-6 a sentence reads only what its clauses read: two stores that agree there evaluate
alike, under the modality or outside it. -/
theorem eval_noninterference {M : Model Rg H D R} (hL : M.Local) (hO : M.Overlay) :
    ∀ (ov : Bool) (s : Sentence Rg H) (σ τ : Store D),
      (∀ st ∈ s.reads ov, σ st = τ st) → M.eval ov s σ = M.eval ov s τ
  | ov, .clause c, σ, τ, h => by
    refine hL c ov σ τ (fun st hst ↦ h st ?_) fun hov ↦ h _ ?_
    · cases ov <;> simp [Sentence.reads, hst]
    · subst hov
      simp [Sentence.reads]
  | ov, .and s t, σ, τ, h => by
    simp only [eval]
    rw [eval_noninterference hL hO ov s σ τ fun st hst ↦ h st (by simp [Sentence.reads, hst]),
      eval_noninterference hL hO ov t σ τ fun st hst ↦ h st (by simp [Sentence.reads, hst])]
  | ov, .or s t, σ, τ, h => by
    simp only [eval]
    rw [eval_noninterference hL hO ov s σ τ fun st hst ↦ h st (by simp [Sentence.reads, hst]),
      eval_noninterference hL hO ov t σ τ fun st hst ↦ h st (by simp [Sentence.reads, hst])]
  | ov, .seq s t, σ, τ, h => by
    simp only [eval]
    rw [eval_noninterference hL hO ov s σ τ fun st hst ↦ h st (by simp [Sentence.reads, hst]),
      eval_noninterference hL hO ov t σ τ fun st hst ↦ h st (by simp [Sentence.reads, hst])]
  | ov, .within r s, σ, τ, h => by
    simp only [eval]
    rw [eval_noninterference hL hO ov s σ τ fun st hst ↦ h st (by simpa [Sentence.reads] using hst)]
  | _, .assume hy s, σ, τ, h => by
    simp only [eval]
    refine eval_noninterference hL hO true s _ _ fun st hst ↦ ?_
    by_cases hst' : st = .hypothetical
    · subst hst'
      exact hO.2 hy σ τ (h _ (by simpa [Sentence.reads] using hst))
    · rw [hO.1 hy σ st hst', hO.1 hy τ st hst']
      exact h st (by simpa [Sentence.reads] using hst)

/-- Outside the modality a sentence reads the overlay only if a clause declares it. -/
theorem hypothetical_notMem_reads {s : Sentence Rg H} (hinv : s.IsInv)
    (hc : ∀ c ∈ s.clauses, CQ.Stratum.hypothetical ∉ c.reads) :
    CQ.Stratum.hypothetical ∉ s.reads false := by
  induction s with
  | clause c => simpa [Sentence.reads] using hc c (by simp [Sentence.clauses])
  | and s t hs ht | or s t hs ht | seq s t hs ht =>
    simp only [Sentence.IsInv, Sentence.hyps, List.append_eq_nil_iff] at hinv
    simp only [Sentence.clauses, List.mem_append] at hc
    simp only [Sentence.reads, mem_union, not_or]
    exact ⟨hs hinv.1 fun c h ↦ hc c (Or.inl h), ht hinv.2 fun c h ↦ hc c (Or.inr h)⟩
  | within r s hs => exact hs hinv hc
  | assume h s _ => exact absurd hinv (Sentence.not_isInv_assume h s)

/-- QSA-6 the firewall: a store's overlay is invisible to a sentence outside the modality whose
clauses do not read it. Whatever a hypothesis wrote there, an `Inv` result does not see it. -/
theorem eval_perturb_of_isInv {M : Model Rg H D R} (hL : M.Local) (hO : M.Overlay)
    {s : Sentence Rg H} (hinv : s.IsInv) (hc : ∀ c ∈ s.clauses, CQ.Stratum.hypothetical ∉ c.reads)
    (h : H) (σ : Store D) : M.eval false s (M.perturb h σ) = M.eval false s σ := by
  refine eval_noninterference hL hO false s _ _ fun st hst ↦ hO.1 h σ st ?_
  rintro rfl
  exact hypothetical_notMem_reads hinv hc hst

end Model

/-! ## QSA-7: the chain language and the product walk -/

section Chains

variable {V Q : Type*} [DecidableEq V] [DecidableEq Q]

namespace Auto

omit [DecidableEq V] [DecidableEq Q] in
theorem run_append (A : Auto Q) (q : Q) (w₁ w₂ : List Move) :
    A.run q (w₁ ++ w₂) = A.run (A.run q w₁) w₂ := by
  induction w₁ generalizing q with
  | nil => rfl
  | cons m w ih => simp [run, ih]

end Auto

omit [DecidableEq V] [DecidableEq Q] in
theorem signature_append (c d : List (Move × V)) :
    signature (c ++ d) = signature c ++ signature d :=
  List.map_append ..

/-- The walk and the run, together: from any vertex and state. -/
theorem chainOk_run_iff (G : TGraph V) (A : Auto Q) :
    ∀ (c : List (Move × V)) (u : V) (q : Q),
      (chainOk G u c = true ∧ A.accept (A.run q (signature c)) = true) ↔
        ∃ v q', prodOk G A (u, q) c (v, q') = true ∧ A.accept q' = true
  | [], u, q => by simp [chainOk, signature, Auto.run, prodOk]
  | (m, v) :: rest, u, q => by
    simp only [chainOk, Bool.and_eq_true, signature, List.map_cons, Auto.run, prodOk]
    constructor
    · rintro ⟨⟨he, hc⟩, hacc⟩
      obtain ⟨v', q', hp, hq⟩ := (chainOk_run_iff G A rest v (A.step q m)).1 ⟨hc, hacc⟩
      exact ⟨v', q', ⟨he, hp⟩, hq⟩
    · rintro ⟨v', q', ⟨he, hp⟩, hq⟩
      obtain ⟨hc, hacc⟩ := (chainOk_run_iff G A rest v (A.step q m)).2 ⟨v', q', hp, hq⟩
      exact ⟨⟨he, hc⟩, hacc⟩

/-- **QSA-7** a chain is admissible iff the product walk from `(u, start)` reaches an accepting
state: the regular-path-query evaluation, exact. -/
theorem admissible_iff_prodOk (G : TGraph V) (A : Auto Q) (u : V) (c : List (Move × V)) :
    Admissible G A u c ↔ ∃ v q, prodOk G A (u, A.start) c (v, q) = true ∧ A.accept q = true :=
  chainOk_run_iff G A c u A.start

omit [DecidableEq V] [DecidableEq Q] in
/-- **QSA-7** pruning at a dead state loses no admissible chain: every prefix of an admissible chain
leaves the automaton live. -/
theorem prune_sound {G : TGraph V} {A : Auto Q} {u : V} {p c : List (Move × V)}
    (h : Admissible G A u (p ++ c)) : A.Live (A.run A.start (signature p)) :=
  ⟨signature c, by
    have := h.2
    rwa [Auto.Accepts, signature_append, Auto.run_append] at this⟩

omit [DecidableEq V] [DecidableEq Q] in
/-- A chain of a graph is a chain of any graph with more edges. -/
theorem chainOk_mono {G G' : TGraph V} (hle : G.Le G') :
    ∀ (u : V) (c : List (Move × V)), chainOk G u c = true → chainOk G' u c = true
  | _, [], _ => rfl
  | u, (m, v) :: rest, h => by
    simp only [chainOk, Bool.and_eq_true] at h ⊢
    exact ⟨hle m u v h.1, chainOk_mono hle v rest h.2⟩

omit [DecidableEq V] [DecidableEq Q] in
/-- QSA-7 more edges, more admissible chains: the language is monotone in the graph. -/
theorem admissible_mono {G G' : TGraph V} (hle : G.Le G') {A : Auto Q} {u : V}
    {c : List (Move × V)} (h : Admissible G A u c) : Admissible G' A u c :=
  ⟨chainOk_mono hle u c h.1, h.2⟩

omit [DecidableEq Q] in
theorem TGraph.le_assume (G : TGraph V) (m : Move) (a b : V) : G.Le (G.assume m a b) :=
  fun m' u v h ↦ by simp [TGraph.assume, h]

omit [DecidableEq Q] in
theorem TGraph.assume_edge (G : TGraph V) (m : Move) (a b : V) :
    (G.assume m a b).edge m a b = true := by
  simp [TGraph.assume]

omit [DecidableEq Q] in
/-- **QSA-7** a hypothetical edge only adds admissible chains. -/
theorem admissible_assume {G : TGraph V} {A : Auto Q} {u : V} {c : List (Move × V)}
    (h : Admissible G A u c) (m : Move) (a b : V) : Admissible (G.assume m a b) A u c :=
  admissible_mono (G.le_assume m a b) h

omit [DecidableEq V] [DecidableEq Q] in
/-- The run of the set automaton: still alive iff every letter so far is in the set. -/
theorem ofSet_run (E : Finset Move) :
    ∀ (w : List Move) (q : Bool), (ofSet E).run q w = (q && decide (∀ m ∈ w, m ∈ E))
  | [], q => by simp [Auto.run]
  | m :: w, q => by
    rw [Auto.run, ofSet_run E w]
    simp only [ofSet, List.forall_mem_cons, Bool.decide_and, Bool.and_assoc]

omit [DecidableEq V] [DecidableEq Q] in
/-- **QSA-7** the set `E` is the one-state automaton: it accepts a word iff every letter is in `E`,
whatever the order. The set is the order-blind shadow of the language. -/
theorem ofSet_accepts (E : Finset Move) (w : List Move) :
    (ofSet E).Accepts w ↔ ∀ m ∈ w, m ∈ E := by
  rw [Auto.Accepts, ofSet_run]
  simp [ofSet]

omit [DecidableEq V] [DecidableEq Q] in
/-- The dead state has no way out. -/
theorem grounding_step_two (m : Move) : grounding.step 2 m = 2 := by
  cases m <;> rfl

omit [DecidableEq V] [DecidableEq Q] in
/-- The dead state stays dead. -/
theorem grounding_run_two : ∀ w : List Move, grounding.run 2 w = 2
  | [] => rfl
  | m :: w => by rw [Auto.run, grounding_step_two, grounding_run_two w]

omit [DecidableEq V] [DecidableEq Q] in
/-- The grounding automaton is live exactly off its dead state. -/
theorem grounding_live_iff (q : Fin 3) : grounding.Live q ↔ q ≠ 2 := by
  constructor
  · rintro ⟨w, hw⟩ rfl
    rw [grounding_run_two] at hw
    exact absurd hw (by decide)
  · intro hq
    fin_cases q
    · exact ⟨[.C], by decide⟩
    · exact ⟨[], by decide⟩
    · exact absurd rfl hq

omit [DecidableEq V] [DecidableEq Q] in
/-- The grounding production, on two words: resemblance twice then a witness is grounded; a
witness then resemblance is not. The set `{S, C}` accepts both: the order is the content. -/
theorem grounding_words :
    grounding.Accepts [.S, .S, .C] ∧ ¬ grounding.Accepts [.C, .S] ∧
      (ofSet {.S, .C}).Accepts [.C, .S] := by
  decide

end Chains

/-! ## QSA-8: the mode table -/

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
      | .capture => .semantic := by
  cases v <;> cases h <;> cases a <;>
    simp only [CQ.required, CQ.mkScope, Bool.false_eq_true, ↓reduceIte] at hr <;>
    obtain ⟨-, rfl⟩ := CQ.Scope.build_ok.1 hr <;> simp +decide [modeOf]

/-! ## QSA-9: the response to a hypothetical edge -/

section Response

variable {V : Type*} [DecidableEq V]

section Generic

variable {R : Type*} [CommRing R]

theorem assumeEdge_apply (A : Matrix V V R) (u v : V) (δ : R) (i j : V) :
    assumeEdge A u v δ i j = A i j + if (i = u ∧ j = v) ∨ (i = v ∧ j = u) then δ else 0 :=
  rfl

/-- The weight an assumed edge between distinct vertices adds to a row: `δ` at either end. -/
theorem sum_assumeEdge_ind [Fintype V] {u v : V} (huv : u ≠ v) (δ : R) (i : V) :
    (∑ j, if (i = u ∧ j = v) ∨ (i = v ∧ j = u) then δ else 0) =
      if i = u ∨ i = v then δ else 0 := by
  by_cases hi : i = u
  · subst hi
    simp [huv, sum_ite_eq']
  · by_cases hi' : i = v
    · subst hi'
      simp [hi, sum_ite_eq']
    · simp [hi, hi']

/-- A hypothetical edge keeps symmetry. -/
theorem isSymm_assumeEdge {A : Matrix V V R} (hA : A.IsSymm) (u v : V) (δ : R) :
    (assumeEdge A u v δ).IsSymm := by
  ext i j
  simp only [transpose_apply, assumeEdge_apply]
  rw [← hA.apply i j]
  congr 1
  simp only [or_comm, and_comm]

/-- The degree under a hypothetical edge between distinct vertices: `δ` more at each end. -/
theorem degree_assumeEdge [Fintype V] (A : Matrix V V R) {u v : V} (huv : u ≠ v) (δ : R) (i : V) :
    degree (assumeEdge A u v δ) i = degree A i + if i = u ∨ i = v then δ else 0 := by
  unfold degree
  rw [← sum_assumeEdge_ind huv δ i, ← sum_add_distrib]
  rfl

/-- **QSA-9** a hypothetical edge is a rank-one update of the Laplacian along `e_u − e_v`. -/
theorem lap_assumeEdge [Fintype V] (A : Matrix V V R) {u v : V} (huv : u ≠ v) (δ : R) :
    lap (assumeEdge A u v δ) = lap A + δ • vecMulVec (dvec u v 1) (dvec u v 1) := by
  ext i j
  unfold lap
  rw [Matrix.add_apply, Matrix.sub_apply, Matrix.sub_apply, Matrix.smul_apply, vecMulVec_apply,
    diagonal_apply, diagonal_apply, degree_assumeEdge A huv, assumeEdge_apply]
  simp only [dvec, one_mul, smul_eq_mul]
  by_cases hij : i = j
  · subst hij
    by_cases hi : i = u <;> by_cases hi' : i = v <;> subst_vars <;> simp_all <;> ring
  · by_cases hi : i = u <;> by_cases hj : j = u <;> by_cases hi' : i = v <;>
      by_cases hj' : j = v <;> subst_vars <;> simp_all <;> ring

/-- The absolute value of an entry under a new signed edge of weight `σ δ`, `σ = ±1`, `δ ≥ 0`,
where there was none: `δ` more at the two new entries. -/
theorem abs_assumeEdge [LinearOrder R] [IsOrderedRing R] (A : Matrix V V R) {u v : V}
    (h0 : A u v = 0) (h0' : A v u = 0) {σ δ : R} (hσ : σ = 1 ∨ σ = -1) (hδ : 0 ≤ δ) (i j : V) :
    |assumeEdge A u v (σ * δ) i j| =
      |A i j| + if (i = u ∧ j = v) ∨ (i = v ∧ j = u) then δ else 0 := by
  have habs : |σ * δ| = δ := by
    rcases hσ with rfl | rfl <;> simp [abs_of_nonneg hδ]
  rw [assumeEdge_apply]
  split_ifs with h
  · rcases h with ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩
    · rw [h0, zero_add, habs, abs_zero, zero_add]
    · rw [h0', zero_add, habs, abs_zero, zero_add]
  · rw [add_zero, add_zero]

/-- The signed degree under a new edge of weight `σ δ`, `σ = ±1`, `δ ≥ 0`, where there was none:
`δ` more at each end. -/
theorem signedDegree_assumeEdge [Fintype V] [LinearOrder R] [IsOrderedRing R] (A : Matrix V V R)
    {u v : V} (huv : u ≠ v) (h0 : A u v = 0) (h0' : A v u = 0) {σ δ : R} (hσ : σ = 1 ∨ σ = -1)
    (hδ : 0 ≤ δ) (i : V) :
    ∑ j, |assumeEdge A u v (σ * δ) i j| =
      (∑ j, |A i j|) + if i = u ∨ i = v then δ else 0 := by
  rw [← sum_assumeEdge_ind huv δ i, ← sum_add_distrib]
  exact sum_congr rfl fun j _ ↦ abs_assumeEdge A h0 h0' hσ hδ i j

/-- **QSA-9** a new signed edge is a rank-one update of the signed Laplacian along `e_u − σ e_v`:
the difference for a supporting edge, the sum for a contradiction. -/
theorem signedLap_assumeEdge [Fintype V] [LinearOrder R] [IsOrderedRing R] (A : Matrix V V R)
    {u v : V} (huv : u ≠ v) (h0 : A u v = 0) (h0' : A v u = 0) {σ δ : R} (hσ : σ = 1 ∨ σ = -1)
    (hδ : 0 ≤ δ) :
    signedLap (assumeEdge A u v (σ * δ)) =
      signedLap A + δ • vecMulVec (dvec u v σ) (dvec u v σ) := by
  ext i j
  unfold signedLap
  rw [Matrix.add_apply, Matrix.sub_apply, Matrix.sub_apply, Matrix.smul_apply, vecMulVec_apply,
    diagonal_apply, diagonal_apply, signedDegree_assumeEdge A huv h0 h0' hσ hδ, assumeEdge_apply]
  simp only [dvec, smul_eq_mul]
  rcases hσ with rfl | rfl
  · by_cases hij : i = j
    · subst hij
      by_cases hi : i = u <;> by_cases hi' : i = v <;> subst_vars <;> simp_all <;> ring
    · by_cases hi : i = u <;> by_cases hj : j = u <;> by_cases hi' : i = v <;>
        by_cases hj' : j = v <;> subst_vars <;> simp_all
  · by_cases hij : i = j
    · subst hij
      by_cases hi : i = u <;> by_cases hi' : i = v <;> subst_vars <;> simp_all <;> ring
    · by_cases hi : i = u <;> by_cases hj : j = u <;> by_cases hi' : i = v <;>
        by_cases hj' : j = v <;> subst_vars <;> simp_all

end Generic

variable [Fintype V]

omit [DecidableEq V] in
/-- The energy of a rank-one `b bᵀ` is a square. -/
theorem dotProduct_vecMulVec_self_mulVec (b x : V → ℝ) :
    x ⬝ᵥ (vecMulVec b b *ᵥ x) = (b ⬝ᵥ x) * (b ⬝ᵥ x) := by
  rw [vecMulVec_mulVec, dotProduct_smul, op_smul_eq_mul, dotProduct_comm x b]

/-- QSA-9 the energy never falls under an assumed positive edge: the Loewner order. -/
theorem dotProduct_lap_le_assumeEdge (A : Matrix V V ℝ) {u v : V} (huv : u ≠ v) {δ : ℝ}
    (hδ : 0 ≤ δ) (x : V → ℝ) :
    x ⬝ᵥ (lap A *ᵥ x) ≤ x ⬝ᵥ (lap (assumeEdge A u v δ) *ᵥ x) := by
  rw [lap_assumeEdge A huv, add_mulVec, dotProduct_add, smul_mulVec, dotProduct_smul, smul_eq_mul,
    dotProduct_vecMulVec_self_mulVec]
  have := mul_nonneg hδ (mul_self_nonneg (dvec u v 1 ⬝ᵥ x))
  linarith

/-- **QSA-9** (CND-2 forward) adding weight to an edge lowers every effective resistance between
vertices the support already joins. -/
theorem rEff_assumeEdge_le {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) {u v : V}
    {δ : ℝ} (hδ : 0 ≤ δ) (hA' : (assumeEdge A u v δ).IsSymm) {i j : V}
    (hr : (support A).Reachable i j) :
    rEff (lapPinv (assumeEdge A u v δ) hA') i j ≤ rEff (lapPinv A hA) i j :=
  rEff_anti hA hA' hw
    (fun i j ↦ by
      simp only [assumeEdge_apply]
      split_ifs <;> linarith) hr

/-- **QSA-9** (CND-2 backward) removing weight from an edge raises every effective resistance
between vertices the weakened support still joins: an assumption can raise resistance. -/
theorem rEff_le_assumeEdge {A : Matrix V V ℝ} (hA : A.IsSymm) {u v : V} {δ : ℝ} (hδ : δ ≤ 0)
    (hA' : (assumeEdge A u v δ).IsSymm) (hw : ∀ i j, 0 ≤ assumeEdge A u v δ i j) {i j : V}
    (hr : (support (assumeEdge A u v δ)).Reachable i j) :
    rEff (lapPinv A hA) i j ≤ rEff (lapPinv (assumeEdge A u v δ) hA') i j :=
  rEff_anti hA' hA hw
    (fun i j ↦ by
      simp only [assumeEdge_apply]
      split_ifs <;> linarith) hr

omit [Fintype V] in
/-- **QSA-9** a new signed edge is consistent with the camps iff its sign agrees with them: then the
graph stays balanced, by the same camps. -/
theorem balanced_assumeEdge {A : Matrix V V ℝ} {s : V → ℝ} (hs : ∀ i, s i = 1 ∨ s i = -1)
    (hA : ∀ i j, 0 ≤ A i j * s i * s j) {u v : V} {σ δ : ℝ} (hδ : 0 ≤ δ)
    (hσ : 0 ≤ σ * s u * s v) : Balanced (assumeEdge A u v (σ * δ)) := by
  refine ⟨s, hs, fun i j ↦ ?_⟩
  simp only [assumeEdge_apply]
  split_ifs with h
  · rcases h with ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩
    · have : (A i j + σ * δ) * s i * s j = A i j * s i * s j + δ * (σ * s i * s j) := by ring
      rw [this]
      exact add_nonneg (hA i j) (mul_nonneg hδ hσ)
    · have : (A i j + σ * δ) * s i * s j = A i j * s i * s j + δ * (σ * s j * s i) := by ring
      rw [this]
      exact add_nonneg (hA i j) (mul_nonneg hδ hσ)
  · simpa using hA i j

/-- QSA-9 a contradiction closing a supported path is frustrated: the triangle with two
supporting edges and one contradicting edge is not balanced (LAP-6). -/
theorem contradiction_frustrates : ¬ Balanced (triangle (1 : ℝ) 1 (-1)) := by
  rw [not_balanced_triangle_iff one_ne_zero one_ne_zero (by norm_num)]
  norm_num

/-- QSA-9 a frustrating assumption lifts the zero mode: on a connected support, an unbalanced
signed graph has strictly positive energy on every nonzero vector (LAP-5). -/
theorem pos_energy_of_not_balanced {A : Matrix V V ℝ} (hA : A.IsSymm) (hc : (support A).Connected)
    (hnb : ¬ Balanced A) {x : V → ℝ} (hx : x ≠ 0) : 0 < x ⬝ᵥ (signedLap A *ᵥ x) := by
  rcases (dotProduct_signedLap_nonneg A hA x).lt_or_eq with h | h
  · exact h
  · exact absurd ((zero_energy_iff_balanced A hA hc).1 ⟨x, hx, h.symm⟩) hnb

/-- **QSA-9** Sherman–Morrison: the exact response of an inverse to a rank-one update, so of a
kernel `M⁻¹` to a hypothetical edge. -/
theorem inv_add_vecMulVec {M : Matrix V V ℝ} (hM : IsUnit M.det) (u v : V → ℝ) {c : ℝ}
    (hc : 1 + c * (v ⬝ᵥ (M⁻¹ *ᵥ u)) ≠ 0) :
    (M + c • vecMulVec u v)⁻¹ =
      M⁻¹ - (c / (1 + c * (v ⬝ᵥ (M⁻¹ *ᵥ u)))) • vecMulVec (M⁻¹ *ᵥ u) (v ᵥ* M⁻¹) := by
  apply inv_eq_right_inv
  set s := v ⬝ᵥ (M⁻¹ *ᵥ u) with hs
  set γ := c / (1 + c * s) with hγ
  have hMu : M *ᵥ (M⁻¹ *ᵥ u) = u := by
    rw [mulVec_mulVec, mul_nonsing_inv M hM, one_mulVec]
  have hvec : vecMulVec u v * vecMulVec (M⁻¹ *ᵥ u) (v ᵥ* M⁻¹) =
      s • vecMulVec u (v ᵥ* M⁻¹) := by
    rw [vecMulVec_mul_vecMulVec, vecMulVec_smul, hs]
  rw [add_mul, Matrix.mul_sub, Matrix.mul_sub, mul_nonsing_inv M hM, Matrix.mul_smul,
    mul_vecMulVec, hMu, Matrix.smul_mul, Matrix.smul_mul, vecMulVec_mul, Matrix.mul_smul, hvec,
    smul_smul, smul_smul]
  have hcoef : c - c * γ * s - γ = 0 := by
    rw [hγ]
    field_simp
    ring
  have : (1 : Matrix V V ℝ) - γ • vecMulVec u (v ᵥ* M⁻¹) +
      (c • vecMulVec u (v ᵥ* M⁻¹) - (c * γ * s) • vecMulVec u (v ᵥ* M⁻¹)) =
      1 + (c - c * γ * s - γ) • vecMulVec u (v ᵥ* M⁻¹) := by
    simp only [sub_smul]
    abel
  rw [this, hcoef, zero_smul, add_zero]

end Response

end Palace.Query
