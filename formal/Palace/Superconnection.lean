module

public import Mathlib.LinearAlgebra.Basis.VectorSpace
public import Mathlib.LinearAlgebra.Isomorphisms
public import Mathlib.Logic.Relation
public import Mathlib.Tactic.FinCases
public import Palace.Superconnection.Defs
public import Palace.Transport

/-!
# The superconnection along a chain of times: Results 3 and 4

temporal-retrieval-algebra §2.3 Results 3 and 4, machine-checked as design theorems on the objects
of `Palace/Transport.lean`: the coboundary `d` is `coboundary` read on the citations, the transport
`τ` along a note map is `pull` on notes and `pullEdge` on citations, and their bracket `[d, τ]` is
TRN-5's `curvature` (`dC_tC_sub`), so Results 1, 2 and 3 speak of one curvature.

Result 3. On the nerve of the times (a transport on every pair, the transitive closure H2), with `d`
signed by the time degree and `τ` the Čech differential with the transports as its coefficients,
`𝔸 = d + τ` has `𝔸² = [d, τ] + τ²` (TRN-10: `d² = 0`, and the nerve's own `face² = 0`, H0); `[d, τ]`
is the curvature on every pair and `τ²` the composition defect on every triangle (TRN-11). `𝔸` is
flat iff it is a bicomplex iff F1 holds on every pair and, on every triangle, F2 with no citation
restored (TRN-13, Result 1 in full); on citation complexes without loops, iff F1 and F2, as the note
says. Two corrections to the note. τ²-coherence is not F2 alone: a citation severed at the middle
time and restored at the last breaks it while the notes compose (TRN-12). And the correction has the
wrong sign: when `[d, h] = [d, τ]`, it is `d + τ − h` that loses the curvature, while `d + τ + h`
has the bracket `2 [d, τ]` (TRN-14). `d + τ − h` is then flat iff the corrected transports compose
on every triangle, which the class does not give (`corrections_not_compose`); a chain of two times
has no triangle, and there it is flat (`correction_sign`). The class: a correction that keeps the
note correspondence exists iff every citation's ends stay in one component of the target's citations
(`exists_correction_iff`); unconstrained, `h = τ` always serves and discards the transport. The
diamond: the theorems hold on any preorder of times, so on a flat chain the two routes around a
diamond agree (`diamond_routes_agree`); the twisted complex the note defers, in which they agree
only up to a homotopy, is not modeled.

Result 4. `δ` is `div`, the adjoint of the coboundary under the counting inner products (TRN-15). A
chain map isometric in TRN-3's sense on notes and on citations commutes with `δ` (`pull_div_eq_div`;
the principle, for matrices, `mul_transpose_eq_of_chainMap`), and then with the edge Laplacian, so
it carries harmonic cochains to harmonic ones (`pullEdge_laplacian`). The inclusion is strict: a new
citation (`new_citation_not_metric`) and a merge (`merge_not_metric`) give chain maps that do not
commute with `δ`. The merge's pullback is an isometry under TRN-3's fiber-weighted inner product,
and no inner product on the target repairs it: TRN-3's isometry, the dilation's, is not the one
Result 4 needs. Nor is a bijection: the six-cycle wound twice around the three-cycle merges every
note and still commutes with `δ` (`wind_metric`), each note's citations going one to one onto its
image's. The isometry Result 4 asks for is local.

These are design theorems (Palace and this file only; no Spec rows): no code builds the
superconnection.
-/

@[expose] public section

open Finset

namespace Palace.Transport

/-! ### TRN-10 The square of a superconnection -/

/-- TRN-10 In any ring, once `d² = 0`, the square of the superconnection `𝔸 = d + τ` is
`𝔸² = [d, τ] + τ²`, the bracket `d τ + τ d` the graded commutator of two odd operators. -/
theorem superconnection_sq {R : Type*} [Ring R] {d : R} (hd : d * d = 0) (τ : R) :
    (d + τ) * (d + τ) = (d * τ + τ * d) + τ * τ := by
  rw [add_mul, mul_add, mul_add, hd]
  abel

variable {A B C : Type*}

/-- The coboundary of a citation complex squares to zero. -/
theorem dC_dC (X : A → A → Prop) [DecidableRel X] (c : Cochain A) : dC X (dC X c) = 0 := by
  refine Prod.ext rfl (funext fun u ↦ funext fun v ↦ ?_)
  simp [dC, mask, coboundary]

/-- TRN-11 The bracket `[d, τ] = d τ − τ d` on the cochains of a pair of times is TRN-5's
`curvature`, read on the source's citations; it sees only the note part of the cochain. -/
theorem dC_tC_sub (σ : A → B) (X : A → A → Prop) [DecidableRel X] (X' : B → B → Prop)
    [DecidableRel X'] (c : Cochain B) :
    dC X (tC σ X X' c) - tC σ X X' (dC X' c) = (0, mask X (curvature σ X' c.1)) := by
  refine Prod.ext (funext fun a ↦ ?_) (funext fun u ↦ funext fun v ↦ ?_)
  · simp [dC, tC, pull]
  · simp only [dC, tC, LinearMap.coe_mk, AddHom.coe_mk, Prod.snd_sub, Pi.sub_apply, mask,
      curvature, pullEdge]
    split_ifs <;> simp [coboundary, pull]

/-- TRN-11 The transport commutes with the coboundary iff every citation of the source carries
forward or collapses: `[d, τ] = 0` is F1, TRN-5's `curvature_eq_zero_iff`. -/
theorem dC_comp_tC_eq_iff (σ : A → B) (X : A → A → Prop) [DecidableRel X] (X' : B → B → Prop)
    [DecidableRel X'] :
    dC X ∘ₗ tC σ X X' = tC σ X X' ∘ₗ dC X' ↔ ∀ u v, X u v → σ u = σ v ∨ X' (σ u) (σ v) := by
  rw [← curvature_eq_zero_iff σ X X']
  constructor
  · intro h φ u v huv
    have h1 := dC_tC_sub σ X X' (φ, 0)
    rw [← LinearMap.comp_apply, h, LinearMap.comp_apply, sub_self] at h1
    have h2 := congrFun (congrFun (congrArg Prod.snd h1) u) v
    simpa [mask, huv] using h2.symm
  · intro h
    refine LinearMap.ext fun c ↦ ?_
    rw [LinearMap.comp_apply, LinearMap.comp_apply, ← sub_eq_zero, dC_tC_sub]
    refine Prod.ext rfl (funext fun u ↦ funext fun v ↦ ?_)
    by_cases huv : X u v
    · simp [mask, huv, h c.1 u v huv]
    · simp [mask, huv]

/-- TRN-12 Two transports compose to a third, `τ_{01} τ_{12} = τ_{02}`, iff the notes compose (F2)
and no citation is restored: every citation that `σ₀₂` carries forward to the last time was
carried to the middle one. -/
theorem tC_comp_eq_iff (σ₀₁ : A → B) (σ₁₂ : B → C) (σ₀₂ : A → C) (XA : A → A → Prop)
    [DecidableRel XA] (XB : B → B → Prop) [DecidableRel XB] (XC : C → C → Prop)
    [DecidableRel XC] :
    tC σ₀₁ XA XB ∘ₗ tC σ₁₂ XB XC = tC σ₀₂ XA XC ↔
      (∀ a, σ₁₂ (σ₀₁ a) = σ₀₂ a) ∧ ∀ u v, XA u v → XC (σ₀₂ u) (σ₀₂ v) → XB (σ₀₁ u) (σ₀₁ v) := by
  classical
  constructor
  · intro h
    refine ⟨fun a ↦ ?_, fun u v huv hC ↦ ?_⟩
    · have h1 := congrFun (congrArg Prod.fst
        (LinearMap.congr_fun h (fun c ↦ if c = σ₀₂ a then 1 else 0, 0))) a
      by_contra hne
      simp [tC, pull, hne] at h1
    · have h1 := congrFun (congrFun (congrArg Prod.snd
        (LinearMap.congr_fun h (0, fun c c' ↦ if c = σ₀₂ u ∧ c' = σ₀₂ v then 1 else 0)))
        u) v
      by_contra hB
      simp [tC, mask, pullEdge, huv, hC, hB] at h1
  · rintro ⟨h2, hr⟩
    refine LinearMap.ext fun c ↦ Prod.ext (funext fun a ↦ ?_) (funext fun u ↦ funext fun v ↦ ?_)
    · simp [tC, pull, h2]
    · by_cases huv : XA u v
      · by_cases hC : XC (σ₀₂ u) (σ₀₂ v)
        · simp [tC, mask, pullEdge, h2, huv, hC, hr u v huv hC]
        · simp [tC, mask, pullEdge, h2, huv, hC]
      · simp [tC, mask, huv]

/-- TRN-12 F1 on the first pair and F2 rule out a restoration, when the citations of the last
time have no loops: a citation the first transport collapses cannot reappear. -/
theorem noRestore_of_F1 {σ₀₁ : A → B} {σ₁₂ : B → C} {σ₀₂ : A → C} {XA : A → A → Prop}
    {XB : B → B → Prop} {XC : C → C → Prop}
    (hF1 : ∀ u v, XA u v → σ₀₁ u = σ₀₁ v ∨ XB (σ₀₁ u) (σ₀₁ v)) (h2 : ∀ a, σ₁₂ (σ₀₁ a) = σ₀₂ a)
    (hC : ∀ c, ¬ XC c c) : ∀ u v, XA u v → XC (σ₀₂ u) (σ₀₂ v) → XB (σ₀₁ u) (σ₀₁ v) := by
  intro u v huv hXC
  rcases hF1 u v huv with heq | hB
  · rw [← h2 u, ← h2 v, heq] at hXC
    exact absurd hXC (hC _)
  · exact hB

/-! ### TRN-10 to TRN-13 The total complex of a chain -/

variable {T : Type*} [Preorder T] {V : T → Type*}

/-- TRN-10 The coboundary of the total complex squares to zero. -/
theorem dTot_mul_self (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)] :
    dTot X * dTot X = 0 := by
  refine LinearMap.ext fun x ↦
    Prod.ext (funext fun t ↦ ?_) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_)) <;>
    simp [dTot, dC_dC]

/-- TRN-10 The nerve's own coboundary squares to zero (Result 1's H0, the poset's nerve): the faces
of a triangle cancel. -/
theorem face_mul_self : (face : Module.End ℝ (Tot V)) * face = 0 := by
  refine LinearMap.ext fun x ↦
    Prod.ext (funext fun t ↦ ?_) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_)) <;>
    simp [face]

/-- The Koszul sign makes the coboundary anticommute with the faces. -/
theorem dTot_face (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)] :
    dTot X * face + face * dTot X = 0 := by
  refine LinearMap.ext fun x ↦
    Prod.ext (funext fun t ↦ ?_) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_)) <;>
    simp [dTot, face]

/-- TRN-11 The bracket of the coboundary with the transports, component by component: on a pair,
minus the transport's bracket `[d, Θ]` at the cochain of the later time; on a triangle, the bracket
of its first face at the cochain on its last face. -/
theorem bracket_first_apply (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (Θ : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1)) (x : Tot V) :
    (dTot X * first Θ + first Θ * dTot X) x =
      (0, fun e ↦ -(dC (X e.1.1) (Θ e (x.1 e.1.2)) - Θ e (dC (X e.1.2) (x.1 e.1.2))),
        fun s ↦ dC (X s.1.1) (Θ s.e01 (x.2.1 s.e12)) - Θ s.e01 (dC (X s.1.2.1) (x.2.1 s.e12))) := by
  refine Prod.ext (funext fun t ↦ ?_) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_))
  · simp [dTot, first]
  · simp [dTot, first]
    abel
  · simp [dTot, first, sub_eq_add_neg]

/-- TRN-11 `τ²` is the composition defect of each triangle:
`(τ² c)(s, t, u) = (Θ_{st} Θ_{tu} − Θ_{su}) c_u`. -/
theorem cech_mul_self_apply (Θ : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1))
    (x : Tot V) :
    (cech Θ * cech Θ) x =
      (0, 0, fun s ↦ Θ s.e01 (Θ s.e12 (x.1 s.1.2.2)) - Θ s.e02 (x.1 s.1.2.2)) := by
  refine Prod.ext (funext fun t ↦ ?_) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_))
  · simp [cech, first, face]
  · simp [cech, first, face]
  · simp [cech, first, face]
    abel

/-- The faces drop out of the bracket: `[d, τ] = [d, first]`. -/
theorem bracket_cech (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (Θ : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1)) :
    dTot X * cech Θ + cech Θ * dTot X = dTot X * first Θ + first Θ * dTot X := by
  simp only [cech, mul_add, add_mul]
  rw [add_add_add_comm, dTot_face X, add_zero]

/-- TRN-11 The square of `𝔸 = d + τ` on the chain, component by component: nothing on a time;
`−[d, Θ]` on a pair; `[d, Θ]` of the first face plus the composition defect on a triangle. -/
theorem sq_apply (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (Θ : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1)) (x : Tot V) :
    ((dTot X + cech Θ) * (dTot X + cech Θ)) x =
      (0, fun e ↦ -(dC (X e.1.1) (Θ e (x.1 e.1.2)) - Θ e (dC (X e.1.2) (x.1 e.1.2))),
        fun s ↦ (dC (X s.1.1) (Θ s.e01 (x.2.1 s.e12)) - Θ s.e01 (dC (X s.1.2.1) (x.2.1 s.e12))) +
          (Θ s.e01 (Θ s.e12 (x.1 s.1.2.2)) - Θ s.e02 (x.1 s.1.2.2))) := by
  rw [superconnection_sq (dTot_mul_self X), bracket_cech, LinearMap.add_apply, bracket_first_apply,
    cech_mul_self_apply]
  refine Prod.ext (by simp) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_)) <;> simp

/-- TRN-11 `τ² = 0` iff the transports compose on every triangle. -/
theorem cech_mul_self_eq_zero_iff (Θ : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1)) :
    cech Θ * cech Θ = 0 ↔ ∀ s : TTri T, Θ s.e01 ∘ₗ Θ s.e12 = Θ s.e02 := by
  classical
  constructor
  · intro h s
    refine LinearMap.ext fun c ↦ ?_
    have h1 := congrFun (congrArg (fun y : Tot V ↦ y.2.2)
      (LinearMap.congr_fun h (Pi.single s.1.2.2 c, 0, 0))) s
    rw [cech_mul_self_apply] at h1
    simpa [sub_eq_zero] using h1
  · intro h
    have h' : ∀ (s : TTri T) c, Θ s.e01 (Θ s.e12 c) = Θ s.e02 c :=
      fun s c ↦ LinearMap.congr_fun (h s) c
    refine LinearMap.ext fun x ↦ ?_
    rw [cech_mul_self_apply]
    refine Prod.ext rfl (Prod.ext rfl (funext fun s ↦ ?_))
    simp [h']

/-- TRN-13 Flat iff a bicomplex, for any transports: `𝔸² = 0` iff every pair's transport commutes
with the coboundary and the transports compose on every triangle. -/
theorem flat_iff_general (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (Θ : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1)) :
    (dTot X + cech Θ) * (dTot X + cech Θ) = 0 ↔
      (∀ e, dC (X e.1.1) ∘ₗ Θ e = Θ e ∘ₗ dC (X e.1.2)) ∧
        ∀ s : TTri T, Θ s.e01 ∘ₗ Θ s.e12 = Θ s.e02 := by
  classical
  constructor
  · intro h
    refine ⟨fun e ↦ LinearMap.ext fun c ↦ ?_, fun s ↦ LinearMap.ext fun c ↦ ?_⟩
    · have h1 := congrFun (congrArg (fun y : Tot V ↦ y.2.1)
        (LinearMap.congr_fun h (Pi.single e.1.2 c, 0, 0))) e
      rw [sq_apply] at h1
      exact (by simpa [sub_eq_zero] using h1 :
        Θ e (dC (X e.1.2) c) = dC (X e.1.1) (Θ e c)).symm
    · have h1 := congrFun (congrArg (fun y : Tot V ↦ y.2.2)
        (LinearMap.congr_fun h (Pi.single s.1.2.2 c, 0, 0))) s
      rw [sq_apply] at h1
      simpa [sub_eq_zero] using h1
  · rintro ⟨hd, hc⟩
    have hd' : ∀ e c, dC (X e.1.1) (Θ e c) = Θ e (dC (X e.1.2) c) :=
      fun e c ↦ LinearMap.congr_fun (hd e) c
    have hc' : ∀ (s : TTri T) c, Θ s.e01 (Θ s.e12 c) = Θ s.e02 c :=
      fun s c ↦ LinearMap.congr_fun (hc s) c
    refine LinearMap.ext fun x ↦ ?_
    rw [sq_apply]
    refine Prod.ext rfl (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_))
    · simp [hd']
    · simp only [hc', sub_self, add_zero]
      exact sub_eq_zero.2 (hd' s.e01 _)

/-- TRN-13 Flat iff a bicomplex (Result 3's "flat ⟺ bicomplex"): `𝔸² = 0` iff `[d, τ] = 0` and
`τ² = 0`, the three bidegrees of `𝔸²` vanishing separately, `d² = 0` being free. -/
theorem flat_iff_bicomplex (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (Θ : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1)) :
    (dTot X + cech Θ) * (dTot X + cech Θ) = 0 ↔
      dTot X * cech Θ + cech Θ * dTot X = 0 ∧ cech Θ * cech Θ = 0 := by
  constructor
  · intro h
    obtain ⟨hd, hc⟩ := (flat_iff_general X Θ).1 h
    refine ⟨?_, (cech_mul_self_eq_zero_iff Θ).2 hc⟩
    have hd' : ∀ e c, dC (X e.1.1) (Θ e c) = Θ e (dC (X e.1.2) c) :=
      fun e c ↦ LinearMap.congr_fun (hd e) c
    refine LinearMap.ext fun x ↦ ?_
    rw [bracket_cech, bracket_first_apply]
    refine Prod.ext rfl (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_))
    · simp [hd']
    · exact sub_eq_zero.2 (hd' s.e01 _)
  · rintro ⟨hb, hc⟩
    rw [superconnection_sq (dTot_mul_self X), hb, hc, add_zero]

/-! ### TRN-12, TRN-13 The transports of a chain: F1 and F2 -/

/-- TRN-12 Result 3's τ²-coherence, on the transports of a chain: `τ² = 0` iff on every triangle
of times the notes compose (F2) and no citation is restored, a hypothesis the note does not name:
F2 alone does not give it (`tau_sq_ne_zero_of_restored`). -/
theorem tau_sq_eq_zero_iff (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (σ : ∀ e : TEdge T, V e.1.1 → V e.1.2) :
    cech (trans X σ) * cech (trans X σ) = 0 ↔ ∀ s : TTri T,
      (∀ a, σ s.e12 (σ s.e01 a) = σ s.e02 a) ∧
        ∀ u v, X s.1.1 u v → X s.1.2.2 (σ s.e02 u) (σ s.e02 v) →
          X s.1.2.1 (σ s.e01 u) (σ s.e01 v) := by
  rw [cech_mul_self_eq_zero_iff]
  exact forall_congr' fun s ↦ tC_comp_eq_iff _ _ _ _ _ _

/-- TRN-13 Result 3 (and Result 1) on the chain: `𝔸 = d + τ` is flat iff every transport is a
chain map (F1: each citation carries forward or collapses) and on every triangle the notes compose
(F2) with no citation restored. -/
theorem flat_iff (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (σ : ∀ e : TEdge T, V e.1.1 → V e.1.2) :
    (dTot X + cech (trans X σ)) * (dTot X + cech (trans X σ)) = 0 ↔
      (∀ e : TEdge T, ∀ u v, X e.1.1 u v → σ e u = σ e v ∨ X e.1.2 (σ e u) (σ e v)) ∧
        ∀ s : TTri T, (∀ a, σ s.e12 (σ s.e01 a) = σ s.e02 a) ∧
          ∀ u v, X s.1.1 u v → X s.1.2.2 (σ s.e02 u) (σ s.e02 v) →
            X s.1.2.1 (σ s.e01 u) (σ s.e01 v) := by
  rw [flat_iff_general]
  refine and_congr (forall_congr' fun e ↦ dC_comp_tC_eq_iff _ _ _)
    (forall_congr' fun s ↦ tC_comp_eq_iff _ _ _ _ _ _)

/-- TRN-13 On citation complexes without loops (a note does not cite itself), Result 1 and
Result 3 as the note states them: flat iff bicomplex iff F1 and F2. -/
theorem flat_iff_of_loopless (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (hX : ∀ t (c : V t), ¬ X t c c) (σ : ∀ e : TEdge T, V e.1.1 → V e.1.2) :
    (dTot X + cech (trans X σ)) * (dTot X + cech (trans X σ)) = 0 ↔
      (∀ e : TEdge T, ∀ u v, X e.1.1 u v → σ e u = σ e v ∨ X e.1.2 (σ e u) (σ e v)) ∧
        ∀ s : TTri T, ∀ a, σ s.e12 (σ s.e01 a) = σ s.e02 a := by
  rw [flat_iff]
  constructor
  · rintro ⟨h1, h2⟩
    exact ⟨h1, fun s ↦ (h2 s).1⟩
  · rintro ⟨h1, h2⟩
    exact ⟨h1, fun s ↦ ⟨h2 s, noRestore_of_F1 (h1 s.e01) (h2 s) (hX s.1.2.2)⟩⟩

/-- TRN-11 On the transports of a chain, `[d, τ]` is TRN-5's curvature on every pair: its component
on `s < t` is minus the curvature of `σ_{st}` at the note cochain of `t`, read on the citations of
`s`. -/
theorem bracket_trans_apply (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (σ : ∀ e : TEdge T, V e.1.1 → V e.1.2) (x : Tot V) (e : TEdge T) :
    ((dTot X * cech (trans X σ) + cech (trans X σ) * dTot X) x).2.1 e =
      -(0, mask (X e.1.1) (curvature (σ e) (X e.1.2) (x.1 e.1.2).1)) := by
  rw [bracket_cech, bracket_first_apply]
  exact congrArg Neg.neg (dC_tC_sub (σ e) (X e.1.1) (X e.1.2) (x.1 e.1.2))

/-- TRN-13 Result 3 in the note's order: once `τ² = 0`, `𝔸² = [d, τ]`, the curvature, and `𝔸` is
flat iff every transport is a chain map (F1). -/
theorem flat_iff_F1_of_tau_sq (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (σ : ∀ e : TEdge T, V e.1.1 → V e.1.2) (h : cech (trans X σ) * cech (trans X σ) = 0) :
    (dTot X + cech (trans X σ)) * (dTot X + cech (trans X σ)) =
        dTot X * cech (trans X σ) + cech (trans X σ) * dTot X ∧
      ((dTot X + cech (trans X σ)) * (dTot X + cech (trans X σ)) = 0 ↔
        ∀ e : TEdge T, ∀ u v, X e.1.1 u v → σ e u = σ e v ∨ X e.1.2 (σ e u) (σ e v)) := by
  refine ⟨by rw [superconnection_sq (dTot_mul_self X), h, add_zero], ?_⟩
  rw [flat_iff]
  exact ⟨fun h' ↦ h'.1, fun h' ↦ ⟨h', (tau_sq_eq_zero_iff X σ).1 h⟩⟩

/-- TRN-13 The diamond, strictly: the theorems hold on any preorder of times, so when `s < t₁ < u`
and `s < t₂ < u`, with `t₁` and `t₂` unordered, a flat `𝔸` carries every note the same way along
both routes, each equal to the transport along `s < u`: the diamond's holonomy is trivial. -/
theorem diamond_routes_agree (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (σ : ∀ e : TEdge T, V e.1.1 → V e.1.2)
    (hflat : (dTot X + cech (trans X σ)) * (dTot X + cech (trans X σ)) = 0) {s t₁ t₂ u : T}
    (h₁ : s < t₁) (h₁' : t₁ < u) (h₂ : s < t₂) (h₂' : t₂ < u) (a : V s) :
    σ ⟨(t₁, u), h₁'⟩ (σ ⟨(s, t₁), h₁⟩ a) = σ ⟨(t₂, u), h₂'⟩ (σ ⟨(s, t₂), h₂⟩ a) := by
  have hF2 := ((flat_iff X σ).1 hflat).2
  calc σ ⟨(t₁, u), h₁'⟩ (σ ⟨(s, t₁), h₁⟩ a) = σ ⟨(s, u), lt_trans h₁ h₁'⟩ a :=
        (hF2 ⟨(s, t₁, u), h₁, h₁'⟩).1 a
    _ = σ ⟨(t₂, u), h₂'⟩ (σ ⟨(s, t₂), h₂⟩ a) := ((hF2 ⟨(s, t₂, u), h₂, h₂'⟩).1 a).symm

/-! ### TRN-12 F2 without τ²-coherence -/

/-- Three times and one citation `0 → 1`, present at times 0 and 2, severed at time 1. -/
def restoredX (t : Fin 3) (u v : Fin 2) : Prop := t ≠ 1 ∧ u = 0 ∧ v = 1

instance (t : Fin 3) : DecidableRel (restoredX t) :=
  fun _ _ ↦ inferInstanceAs (Decidable (_ ∧ _ ∧ _))

/-- The notes carried by the identity between any two times. -/
def idTrans {T : Type*} [Preorder T] {N : Type*} : ∀ _ : TEdge T, N → N := fun _ ↦ id

/-- TRN-12 F2 does not give τ²-coherence: with the notes carried by the identity, so that F2 holds
on every triangle, a citation severed at the middle time and restored at the last makes `τ² ≠ 0`
(the hypothesis Result 3 does not name). -/
theorem tau_sq_ne_zero_of_restored :
    (∀ (s : TTri (Fin 3)) (a : Fin 2), idTrans s.e12 (idTrans s.e01 a) = idTrans s.e02 a) ∧
      cech (V := fun _ ↦ Fin 2) (trans restoredX idTrans) *
        cech (V := fun _ ↦ Fin 2) (trans restoredX idTrans) ≠ 0 := by
  refine ⟨fun _ _ ↦ rfl, fun h ↦ ?_⟩
  have h1 := ((tau_sq_eq_zero_iff (V := fun _ ↦ Fin 2) restoredX idTrans).1 h
    ⟨(0, 1, 2), by decide, by decide⟩).2 0 1 (by decide) (by decide)
  exact absurd h1 (by decide)

/-! ### TRN-14 The correction: its sign, its class, and what flatness still asks -/

/-- TRN-14 The correction's sign, in any ring: when `[d, h] = [d, τ]`, the corrected `d + τ − h`
has square `(τ − h)²`. -/
theorem sub_correction_sq {R : Type*} [Ring R] {d τ h : R} (hd : d * d = 0)
    (hh : d * h + h * d = d * τ + τ * d) :
    (d + (τ - h)) * (d + (τ - h)) = (τ - h) * (τ - h) := by
  rw [superconnection_sq hd, mul_sub, sub_mul,
    show d * τ - d * h + (τ * d - h * d) = (d * τ + τ * d) - (d * h + h * d) by abel, hh,
    sub_self, zero_add]

/-- TRN-14 The note's sign, in any ring: when `[d, h] = [d, τ]`, `d + τ + h` has square
`2 [d, τ] + (τ + h)²`, so it is flat only where `d + τ` already had no curvature. -/
theorem add_correction_sq {R : Type*} [Ring R] {d τ h : R} (hd : d * d = 0)
    (hh : d * h + h * d = d * τ + τ * d) :
    (d + (τ + h)) * (d + (τ + h)) = 2 * (d * τ + τ * d) + (τ + h) * (τ + h) := by
  rw [superconnection_sq hd, mul_add, add_mul,
    show d * τ + d * h + (τ * d + h * d) = (d * τ + τ * d) + (d * h + h * d) by abel, hh, two_mul]

/-- The transport part of the Čech differential is linear in the transports. -/
theorem first_add (Θ h : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1)) :
    first (Θ + h) = first Θ + first h := by
  refine LinearMap.ext fun x ↦
    Prod.ext (funext fun t ↦ ?_) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_)) <;>
    simp [first]

theorem first_sub (Θ h : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1)) :
    first (Θ - h) = first Θ - first h := by
  refine LinearMap.ext fun x ↦
    Prod.ext (funext fun t ↦ ?_) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_)) <;>
    simp [first]

/-- TRN-14 With corrections whose brackets are the transports' (`[d, h_e] = [d, Θ_e]` on every
pair), the corrected `d + τ − h` is flat iff the corrected transports compose on every triangle, a
condition the brackets do not give (`corrections_not_compose`). On a chain of two times there is no
triangle, and `d + τ − h` is flat. -/
theorem sub_correction_flat_iff (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (Θ h : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1))
    (hh : ∀ e, dC (X e.1.1) ∘ₗ h e - h e ∘ₗ dC (X e.1.2) =
      dC (X e.1.1) ∘ₗ Θ e - Θ e ∘ₗ dC (X e.1.2)) :
    (dTot X + (cech Θ - first h)) * (dTot X + (cech Θ - first h)) = 0 ↔
      ∀ s : TTri T, (Θ s.e01 - h s.e01) ∘ₗ (Θ s.e12 - h s.e12) = Θ s.e02 - h s.e02 := by
  have hc : cech Θ - first h = cech (Θ - h) := by
    rw [cech, cech, first_sub]
    abel
  rw [hc, flat_iff_general]
  have hb : ∀ e, dC (X e.1.1) ∘ₗ (Θ - h) e = (Θ - h) e ∘ₗ dC (X e.1.2) := by
    intro e
    rw [Pi.sub_apply, LinearMap.comp_sub, LinearMap.sub_comp, sub_eq_sub_iff_sub_eq_sub,
      ← hh e]
  exact ⟨fun h' ↦ h'.2, fun h' ↦ ⟨hb, h'⟩⟩

/-- TRN-14 The note's sign fails on the chain: with `[d, h_e] = [d, Θ_e]` on every pair,
`d + τ + h` is not flat as soon as one transport does not commute with `d`, since its bracket
there is `2 [d, Θ_e]`. -/
theorem add_correction_not_flat (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (Θ h : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1))
    (hh : ∀ e, dC (X e.1.1) ∘ₗ h e - h e ∘ₗ dC (X e.1.2) =
      dC (X e.1.1) ∘ₗ Θ e - Θ e ∘ₗ dC (X e.1.2))
    (e : TEdge T) (he : dC (X e.1.1) ∘ₗ Θ e ≠ Θ e ∘ₗ dC (X e.1.2)) :
    (dTot X + (cech Θ + first h)) * (dTot X + (cech Θ + first h)) ≠ 0 := by
  have hc : cech Θ + first h = cech (Θ + h) := by
    rw [cech, cech, first_add]
    abel
  rw [hc]
  intro hflat
  have h1 := ((flat_iff_general X (Θ + h)).1 hflat).1 e
  rw [Pi.add_apply, LinearMap.comp_add, LinearMap.add_comp] at h1
  apply he
  have h2 : (dC (X e.1.1) ∘ₗ Θ e - Θ e ∘ₗ dC (X e.1.2)) +
      (dC (X e.1.1) ∘ₗ Θ e - Θ e ∘ₗ dC (X e.1.2)) = 0 := by
    nth_rewrite 2 [← hh e]
    rw [show dC (X e.1.1) ∘ₗ Θ e - Θ e ∘ₗ dC (X e.1.2) +
        (dC (X e.1.1) ∘ₗ h e - h e ∘ₗ dC (X e.1.2)) =
        (dC (X e.1.1) ∘ₗ Θ e + dC (X e.1.1) ∘ₗ h e) -
          (Θ e ∘ₗ dC (X e.1.2) + h e ∘ₗ dC (X e.1.2)) by abel, h1, sub_self]
  have h3 : dC (X e.1.1) ∘ₗ Θ e - Θ e ∘ₗ dC (X e.1.2) = 0 := by
    rw [← one_smul ℝ (dC (X e.1.1) ∘ₗ Θ e - Θ e ∘ₗ dC (X e.1.2)),
      ← inv_mul_cancel₀ (two_ne_zero : (2 : ℝ) ≠ 0), mul_smul, two_smul, h2, smul_zero]
  exact sub_eq_zero.1 h3

/-- TRN-14 Unconstrained, the class is always exact: `h = τ` itself has the transport's bracket,
and `d + τ − τ = d + face` is flat, the transport discarded. The class says something only of
corrections that keep the note correspondence (`exists_correction_iff`). -/
theorem flat_sub_first_self (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (Θ : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1)) :
    (dTot X + (cech Θ - first Θ)) * (dTot X + (cech Θ - first Θ)) = 0 := by
  rw [cech, add_sub_cancel_left, superconnection_sq (dTot_mul_self X), dTot_face, face_mul_self,
    add_zero]

omit [Preorder T] in
/-- A cochain locally constant on the citations is constant on their components. -/
theorem eq_of_eqvGen {X' : B → B → Prop} {φ : B → ℝ} (hφ : ∀ b b', X' b b' → φ b = φ b')
    {b b' : B} (h : Relation.EqvGen X' b b') : φ b = φ b' := by
  induction h with
  | rel x y hxy => exact hφ x y hxy
  | refl => rfl
  | symm x y _ ih => exact ih.symm
  | trans x y z _ _ ih1 ih2 => exact ih1.trans ih2

/-- A linear map vanishing on the kernel of another factors through it, over a field. -/
theorem exists_comp_eq_of_ker_le {K U W Y : Type*} [Field K] [AddCommGroup U] [Module K U]
    [AddCommGroup W] [Module K W] [AddCommGroup Y] [Module K Y] (f : U →ₗ[K] W) (g : U →ₗ[K] Y)
    (h : LinearMap.ker f ≤ LinearMap.ker g) : ∃ k : W →ₗ[K] Y, k ∘ₗ f = g := by
  obtain ⟨k, hk⟩ := LinearMap.exists_extend
    (f.rangeRestrict.liftOfSurjective (LinearMap.surjective_rangeRestrict f)
      ⟨g, by rwa [LinearMap.ker_rangeRestrict]⟩)
  refine ⟨k, LinearMap.ext fun u ↦ ?_⟩
  have h1 := LinearMap.congr_fun hk (f.rangeRestrict u)
  rw [LinearMap.equivOfSurjective_apply] at h1
  exact h1

/-- TRN-14 The class of the curvature, Result 3's "the true invariant is the class": a correction
that keeps the note correspondence (zero on note cochains) with the transport's bracket,
`[d, h] = [d, τ]`, exists iff every citation's ends stay in one component of the target's
citations, so that a severed citation can be routed around through the target. -/
theorem exists_correction_iff (σ : A → B) (X : A → A → Prop) [DecidableRel X]
    (X' : B → B → Prop) [DecidableRel X'] :
    (∃ h : Cochain B →ₗ[ℝ] Cochain A, (∀ c, (h c).1 = 0) ∧
        dC X ∘ₗ h - h ∘ₗ dC X' = dC X ∘ₗ tC σ X X' - tC σ X X' ∘ₗ dC X') ↔
      ∀ u v, X u v → Relation.EqvGen X' (σ u) (σ v) := by
  classical
  constructor
  · rintro ⟨h, h0, hh⟩ u v huv
    by_contra hne
    set φ : B → ℝ := fun b ↦ if Relation.EqvGen X' b (σ v) then 1 else 0 with hφ
    have hloc : ∀ b b', X' b b' → φ b = φ b' := by
      intro b b' hbb'
      have hiff : Relation.EqvGen X' b (σ v) ↔ Relation.EqvGen X' b' (σ v) :=
        ⟨fun hb ↦ (Relation.EqvGen.symm _ _ (Relation.EqvGen.rel _ _ hbb')).trans _ _ _ hb,
          fun hb ↦ (Relation.EqvGen.rel _ _ hbb').trans _ _ _ hb⟩
      simp only [hφ, hiff]
    have hd0 : dC X' (φ, 0) = 0 := by
      refine Prod.ext rfl (funext fun b ↦ funext fun b' ↦ ?_)
      by_cases hbb : X' b b'
      · simp [dC, mask, coboundary, hbb, hloc b b' hbb]
      · simp [dC, mask, hbb]
    have hL : dC X (h (φ, 0)) = 0 := by
      refine Prod.ext rfl (funext fun x ↦ funext fun y ↦ ?_)
      simp [dC, mask, coboundary, h0]
    have h1 : dC X (tC σ X X' (φ, 0)) - tC σ X X' (dC X' (φ, 0)) = 0 := by
      have h1 := LinearMap.congr_fun hh (φ, 0)
      simp only [LinearMap.sub_apply, LinearMap.comp_apply] at h1
      rw [← h1, hd0, map_zero, hL, sub_zero]
    rw [dC_tC_sub] at h1
    have h2 := congrFun (congrFun (congrArg Prod.snd h1) u) v
    have hnot : ¬ X' (σ u) (σ v) := fun h ↦ hne (Relation.EqvGen.rel _ _ h)
    simp [mask, huv, curvature_eq, hnot, hφ, hne, Relation.EqvGen.refl] at h2
  · intro hc
    let f : (B → ℝ) →ₗ[ℝ] (B → B → ℝ) := LinearMap.snd ℝ _ _ ∘ₗ dC X' ∘ₗ LinearMap.inl ℝ _ _
    let g : (B → ℝ) →ₗ[ℝ] (A → A → ℝ) :=
      LinearMap.snd ℝ _ _ ∘ₗ (dC X ∘ₗ tC σ X X' - tC σ X X' ∘ₗ dC X') ∘ₗ LinearMap.inl ℝ _ _
    have hg : ∀ φ, g φ = mask X (curvature σ X' φ) := fun φ ↦ by
      simp only [g, LinearMap.comp_apply, LinearMap.sub_apply, LinearMap.inl_apply, dC_tC_sub,
        LinearMap.snd_apply]
    have hker : LinearMap.ker f ≤ LinearMap.ker g := by
      intro φ hφ
      rw [LinearMap.mem_ker] at hφ ⊢
      have hloc : ∀ b b', X' b b' → φ b = φ b' := fun b b' hbb ↦ by
        have h1 := congrFun (congrFun hφ b) b'
        simp only [f, LinearMap.comp_apply, LinearMap.inl_apply, LinearMap.snd_apply, dC,
          LinearMap.coe_mk, AddHom.coe_mk, mask, hbb, ↓reduceIte, coboundary, Pi.zero_apply,
          sub_eq_zero] at h1
        exact h1.symm
      rw [hg]
      funext u v
      by_cases huv : X u v
      · simp [mask, huv, curvature_eq, eq_of_eqvGen hloc (hc u v huv)]
      · simp [mask, huv]
    obtain ⟨k, hk⟩ := exists_comp_eq_of_ker_le f g hker
    refine ⟨LinearMap.inr ℝ _ _ ∘ₗ (-k) ∘ₗ LinearMap.snd ℝ _ _, fun c ↦ rfl, ?_⟩
    refine LinearMap.ext fun c ↦ ?_
    simp only [LinearMap.sub_apply, LinearMap.comp_apply]
    rw [dC_tC_sub, ← hg, ← hk]
    refine Prod.ext ?_ (funext fun u ↦ funext fun v ↦ ?_)
    · simp [dC]
    · simp [dC, mask, coboundary, f]

/-! ### TRN-14 The two counterexamples -/

/-- Two times: at time 0 the citations `0 → 1`, `1 → 2` and `0 → 2`; at time 1 the last severed,
its ends still joined through note 1. -/
def severedX (t : Fin 2) (u v : Fin 3) : Prop :=
  (u = 0 ∧ v = 1) ∨ (u = 1 ∧ v = 2) ∨ (t = 0 ∧ u = 0 ∧ v = 2)

instance (t : Fin 2) : DecidableRel (severedX t) :=
  fun _ _ ↦ inferInstanceAs (Decidable (_ ∨ _ ∨ _))

/-- TRN-14 Result 3's correction has the wrong sign: on two times with one citation severed and
its ends still joined, the class is exact, a correction `h` that keeps the notes exists, and
`d + τ − h` is flat while the note's `d + τ + h` is not. -/
theorem correction_sign : ∃ h : ∀ _ : TEdge (Fin 2), Cochain (Fin 3) →ₗ[ℝ] Cochain (Fin 3),
    (dTot (V := fun _ ↦ Fin 3) severedX + (cech (trans severedX idTrans) - first h)) *
        (dTot severedX + (cech (trans severedX idTrans) - first h)) = 0 ∧
      (dTot (V := fun _ ↦ Fin 3) severedX + (cech (trans severedX idTrans) + first h)) *
        (dTot severedX + (cech (trans severedX idTrans) + first h)) ≠ 0 := by
  have hcon : ∀ u v, severedX 0 u v → Relation.EqvGen (severedX 1) (id u) (id v) := by
    intro u v huv
    by_cases h02 : u = 0 ∧ v = 2
    · obtain ⟨rfl, rfl⟩ := h02
      exact (Relation.EqvGen.rel 0 1 (by decide)).trans _ _ _ (Relation.EqvGen.rel 1 2 (by decide))
    · refine Relation.EqvGen.rel _ _ ?_
      simp only [severedX] at huv ⊢
      tauto
  obtain ⟨h, -, hh⟩ := (exists_correction_iff id (severedX 0) (severedX 1)).2 hcon
  have he : ∀ e : TEdge (Fin 2), e = ⟨(0, 1), by decide⟩ := by
    rintro ⟨⟨a, b⟩, hab⟩
    fin_cases a <;> fin_cases b <;> first | rfl | exact absurd hab (by decide)
  refine ⟨fun _ ↦ h, ?_, ?_⟩
  · refine (sub_correction_flat_iff (V := fun _ ↦ Fin 3) severedX _ _ fun e ↦ ?_).2 fun s ↦ ?_
    · rw [he e]
      exact hh
    · obtain ⟨⟨a, b, c⟩, h1, h2⟩ := s
      fin_cases a <;> fin_cases b <;> fin_cases c <;>
        first | exact absurd h1 (by decide) | exact absurd h2 (by decide)
  · refine add_correction_not_flat (V := fun _ ↦ Fin 3) severedX _ _ (fun e ↦ ?_)
      ⟨(0, 1), by decide⟩ ?_
    · rw [he e]
      exact hh
    · intro hcomm
      have h1 := (dC_comp_tC_eq_iff id (severedX 0) (severedX 1)).1 hcomm 0 2 (by decide)
      revert h1
      decide

/-- The triangle `0 → 1`, `1 → 2`, `0 → 2`, the same complex at every time. -/
def triX (_t : Fin 3) (u v : Fin 3) : Prop := (u = 0 ∧ v = 1) ∨ (u = 1 ∧ v = 2) ∨ (u = 0 ∧ v = 2)

instance (t : Fin 3) : DecidableRel (triX t) := fun _ _ ↦ inferInstanceAs (Decidable (_ ∨ _ ∨ _))

/-- A correction that touches the transport only through the circulation around the triangle: it
reads `ψ 0 1 + ψ 1 2 − ψ 0 2` into the citation `0 → 2`, and kills every coboundary. -/
def circ : Cochain (Fin 3) →ₗ[ℝ] Cochain (Fin 3) where
  toFun c := (0, fun u v ↦ if u = 0 ∧ v = 2 then c.2 0 1 + c.2 1 2 - c.2 0 2 else 0)
  map_add' c c' := by
    refine Prod.ext (by simp) (funext fun u ↦ funext fun v ↦ ?_)
    simp only [Prod.snd_add, Pi.add_apply]
    split_ifs <;> ring
  map_smul' r c := by
    refine Prod.ext (by simp) (funext fun u ↦ funext fun v ↦ ?_)
    simp only [Prod.smul_snd, Pi.smul_apply, smul_eq_mul, RingHom.id_apply]
    split_ifs <;> ring

/-- The corrections: `circ` on the long pair `0 < 2`, none on the others. -/
def circCorr : ∀ _ : TEdge (Fin 3), Cochain (Fin 3) →ₗ[ℝ] Cochain (Fin 3) :=
  fun e ↦ if e.1 = (0, 2) then circ else 0

/-- TRN-14 The class does not make the corrected differential flat: on three times carrying the
same triangle, `d + τ` is flat, every correction of `circCorr` has the transport's bracket (both
zero), and yet `d + τ − h` is not flat, because the corrected transports no longer compose. -/
theorem corrections_not_compose :
    (dTot (V := fun _ ↦ Fin 3) triX + cech (trans triX idTrans)) *
        (dTot triX + cech (trans triX idTrans)) = 0 ∧
      (∀ e : TEdge (Fin 3), dC (triX e.1.1) ∘ₗ circCorr e - circCorr e ∘ₗ dC (triX e.1.2) =
        dC (triX e.1.1) ∘ₗ trans (V := fun _ ↦ Fin 3) triX idTrans e -
          trans triX idTrans e ∘ₗ dC (triX e.1.2)) ∧
      (dTot (V := fun _ ↦ Fin 3) triX + (cech (trans triX idTrans) - first circCorr)) *
        (dTot triX + (cech (trans triX idTrans) - first circCorr)) ≠ 0 := by
  have hflat : (dTot (V := fun _ ↦ Fin 3) triX + cech (trans triX idTrans)) *
      (dTot triX + cech (trans triX idTrans)) = 0 := by
    refine (flat_iff_of_loopless (V := fun _ ↦ Fin 3) triX (fun _ c ↦ ?_) idTrans).2
      ⟨fun e u v huv ↦ Or.inr huv, fun _ _ ↦ rfl⟩
    simp only [triX]
    revert c
    decide
  have hT : ∀ e : TEdge (Fin 3), dC (triX e.1.1) ∘ₗ trans (V := fun _ ↦ Fin 3) triX idTrans e -
      trans triX idTrans e ∘ₗ dC (triX e.1.2) = 0 := fun e ↦
    sub_eq_zero.2 (((flat_iff_general (V := fun _ ↦ Fin 3) triX _).1 hflat).1 e)
  have hcirc : dC (triX 0) ∘ₗ circ - circ ∘ₗ dC (triX 0) = 0 := by
    refine LinearMap.ext fun c ↦ Prod.ext ?_ (funext fun u ↦ funext fun v ↦ ?_)
    · simp [dC, circ]
    · simp [dC, circ, mask, coboundary, triX]
  have hh : ∀ e : TEdge (Fin 3), dC (triX e.1.1) ∘ₗ circCorr e - circCorr e ∘ₗ dC (triX e.1.2) =
      dC (triX e.1.1) ∘ₗ trans (V := fun _ ↦ Fin 3) triX idTrans e -
        trans triX idTrans e ∘ₗ dC (triX e.1.2) := by
    intro e
    rw [hT e]
    by_cases he : e.1 = (0, 2)
    · simp only [circCorr, he, ↓reduceIte]
      exact hcirc
    · simp [circCorr, he]
  refine ⟨hflat, hh, fun hc ↦ ?_⟩
  let s : TTri (Fin 3) := ⟨(0, 1, 2), by decide, by decide⟩
  have hcomp := (sub_correction_flat_iff (V := fun _ ↦ Fin 3) triX _ circCorr hh).1 hc s
  have hT2 := ((flat_iff_general (V := fun _ ↦ Fin 3) triX _).1 hflat).2 s
  have h01 : circCorr s.e01 = 0 := by simp [s, circCorr]
  have h12 : circCorr s.e12 = 0 := by simp [s, circCorr]
  have h02 : circCorr s.e02 = circ := by simp [s, circCorr]
  rw [h01, h12, h02, sub_zero, sub_zero, hT2] at hcomp
  have hc0 : circ = 0 := sub_eq_self.mp hcomp.symm
  have h1 := congrFun (congrFun (congrArg Prod.snd
    (LinearMap.congr_fun hc0 (0, fun u v ↦ if u = 0 ∧ v = 1 then 1 else 0))) 0) 2
  simp [circ] at h1

/-! ### TRN-15 Result 4: topological coherence is strictly weaker than metric coherence -/

section Metric

variable [Fintype A] [Fintype B]

/-- TRN-15 `div` is the adjoint `δ` of the coboundary under the counting inner products, the edge
pairing read on the citations: `⟨d φ, ψ⟩ = ⟨φ, δ ψ⟩`. -/
theorem sum_mask_coboundary_mul (X : A → A → Prop) [DecidableRel X] (φ : A → ℝ)
    (ψ : A → A → ℝ) : ∑ u, ∑ v, mask X (coboundary φ) u v * ψ u v = ∑ a, φ a * div X ψ a := by
  have h1 : ∀ u v, mask X (coboundary φ) u v * ψ u v =
      (if X u v then φ v * ψ u v else 0) - (if X u v then φ u * ψ u v else 0) := by
    intro u v
    simp only [mask, coboundary]
    split_ifs <;> ring
  have h2 : ∀ a, φ a * div X ψ a = ∑ x, (if X x a then φ a * ψ x a else 0) -
      ∑ x, (if X a x then φ a * ψ a x else 0) := by
    intro a
    simp only [div, mask, mul_sum, ← sum_sub_distrib]
    refine sum_congr rfl fun x _ ↦ ?_
    split_ifs <;> ring
  simp only [h1, h2, sum_sub_distrib]
  rw [sum_comm (f := fun a x ↦ if X x a then φ a * ψ x a else 0)]

/-- TRN-15 The principle, for matrices under the counting inner products (a weighted inner product
is the counting one after the square roots of its weights): a chain map, `τ₁ d' = d τ₀`, whose note
part is a co-isometry, `τ₀ τ₀ᵀ = 1`, and whose citation part is an isometry, `τ₁ᵀ τ₁ = 1`, commutes
with the adjoints, `τ₀ d'ᵀ = dᵀ τ₁`. -/
theorem mul_transpose_eq_of_chainMap {R : Type*} [CommRing R] {n n' m m' : Type*} [Fintype n]
    [Fintype n'] [Fintype m] [Fintype m'] [DecidableEq n] [DecidableEq m'] {d : Matrix m n R}
    {d' : Matrix m' n' R} {t₀ : Matrix n n' R} {t₁ : Matrix m m' R} (h : t₁ * d' = d * t₀)
    (h₀ : t₀ * t₀.transpose = 1) (h₁ : t₁.transpose * t₁ = 1) :
    t₀ * d'.transpose = d.transpose * t₁ := by
  calc t₀ * d'.transpose = t₀ * d'.transpose * (t₁.transpose * t₁) := by rw [h₁, Matrix.mul_one]
    _ = t₀ * (t₁ * d').transpose * t₁ := by
        rw [Matrix.transpose_mul]
        simp only [Matrix.mul_assoc]
    _ = t₀ * (d * t₀).transpose * t₁ := by rw [h]
    _ = t₀ * t₀.transpose * d.transpose * t₁ := by
        rw [Matrix.transpose_mul]
        simp only [Matrix.mul_assoc]
    _ = d.transpose * t₁ := by rw [h₀, Matrix.one_mul]

variable [DecidableEq B]

omit [Fintype B] in
/-- A transport isometric on notes in TRN-3's sense, every fiber one note (`pull_isometry_iff`), is
a bijection of the notes. -/
theorem bijective_of_fiber_eq_one {σ : A → B} (hσ : ∀ b, fiber σ b = 1) :
    Function.Bijective σ := by
  refine ⟨fun a a' h ↦ ?_, fun b ↦ ?_⟩
  · obtain ⟨x, hx⟩ := card_eq_one.1 (hσ (σ a))
    have ha : a ∈ univ.filter (fun y ↦ σ y = σ a) := by simp
    have ha' : a' ∈ univ.filter (fun y ↦ σ y = σ a) := by simp [h]
    rw [hx] at ha ha'
    exact (mem_singleton.1 ha).trans (mem_singleton.1 ha').symm
  · obtain ⟨x, hx⟩ := card_eq_one.1 (hσ b)
    have : x ∈ univ.filter (fun y ↦ σ y = b) := by
      rw [hx]
      exact mem_singleton_self x
    exact ⟨x, (mem_filter.1 this).2⟩

/-- TRN-15 Result 4's positive direction: a transport that commutes with `d` (F1) and is isometric
in TRN-3's sense on notes (every fiber one note, `pull_isometry_iff`) and on citations (each
citation between images is the image of one of the source's) commutes with `δ` too:
`σ^* δ' = δ σ^*`. -/
theorem pull_div_eq_div {σ : A → B} (hσ : ∀ b, fiber σ b = 1) (X : A → A → Prop)
    [DecidableRel X] (X' : B → B → Prop) [DecidableRel X']
    (hF1 : ∀ u v, X u v → σ u = σ v ∨ X' (σ u) (σ v)) (hiso : ∀ u v, X' (σ u) (σ v) → X u v)
    (ψ : B → B → ℝ) : pull σ (div X' ψ) = div X (mask X (pullEdge σ X' ψ)) := by
  have hb := bijective_of_fiber_eq_one hσ
  funext a
  simp only [pull, div]
  refine (Fintype.sum_bijective σ hb _ _ fun x ↦ ?_).symm
  by_cases hxa : x = a
  · subst hxa
    simp
  · have h1 : X x a ↔ X' (σ x) (σ a) :=
      ⟨fun h ↦ (hF1 x a h).resolve_left fun he ↦ hxa (hb.1 he), hiso x a⟩
    have h2 : X a x ↔ X' (σ a) (σ x) :=
      ⟨fun h ↦ (hF1 a x h).resolve_left fun he ↦ hxa (hb.1 he).symm, hiso a x⟩
    simp only [mask, pullEdge, h1, h2]
    split_ifs <;> rfl

omit [DecidableEq B] in
/-- TRN-15 What metric coherence buys: a transport that commutes with `d` (F1) and with `δ`
commutes with the edge Laplacian `Δ₁ = d δ` (the complex has no cells above its citations), so it
carries harmonic edge cochains to harmonic ones. A chain map alone need not
(`new_citation_not_metric`). -/
theorem pullEdge_laplacian {σ : A → B} (X : A → A → Prop) [DecidableRel X] (X' : B → B → Prop)
    [DecidableRel X'] (hF1 : ∀ u v, X u v → σ u = σ v ∨ X' (σ u) (σ v))
    (hδ : ∀ ψ, pull σ (div X' ψ) = div X (mask X (pullEdge σ X' ψ))) (ψ : B → B → ℝ) :
    mask X (pullEdge σ X' (mask X' (coboundary (div X' ψ)))) =
      mask X (coboundary (div X (mask X (pullEdge σ X' ψ)))) := by
  rw [← hδ]
  funext u v
  by_cases huv : X u v
  · have hc := (curvature_eq_zero_iff σ X X').2 hF1 (div X' ψ) u v huv
    rw [curvature_eq] at hc
    simp only [mask, huv, ↓reduceIte, pullEdge, coboundary, pull]
    split_ifs with h <;> simp_all
  · simp [mask, huv]

end Metric

/-! ### TRN-15 The two counterexamples: a new citation and a merge -/

/-- The path `0 → 1 → 2`. -/
def pathX (u v : Fin 3) : Prop := (u = 0 ∧ v = 1) ∨ (u = 1 ∧ v = 2)

instance : DecidableRel pathX := fun _ _ ↦ inferInstanceAs (Decidable (_ ∨ _))

/-- The cycle around the triangle `0 → 1 → 2 → 0` on the triangle's citations (`triX`): `1` along
`0 → 1` and `1 → 2`, `−1` along `0 → 2`. -/
def cycle (u v : Fin 3) : ℝ := if u = 0 ∧ v = 2 then -1 else 1

/-- TRN-15 Strictness, by a new citation: at the later time the citation `0 → 2` closes the path
into a triangle. The identity carries every citation forward (F1), so it is a chain map and
transports the cohomology classes; the cycle around the triangle is harmonic there (on a graph the
harmonic edge cochains are `ker δ`), its pullback to the path is not, and `σ^* δ' ≠ δ σ^*`: the
chain map transports homology but not the kernel. -/
theorem new_citation_not_metric :
    (∀ u v, pathX u v → id u = id v ∨ triX 0 (id u) (id v)) ∧ div (triX 0) cycle = 0 ∧
      div pathX (mask pathX (pullEdge id (triX 0) cycle)) ≠ 0 ∧
      pull id (div (triX 0) cycle) ≠ div pathX (mask pathX (pullEdge id (triX 0) cycle)) := by
  have h0 : div (triX 0) cycle = 0 := by
    funext a
    fin_cases a <;> simp [div, mask, triX, cycle, Fin.sum_univ_three]
  have h1 : div pathX (mask pathX (pullEdge id (triX 0) cycle)) ≠ 0 := by
    intro h
    have h2 := congrFun h 0
    simp [div, mask, pullEdge, pathX, triX, cycle] at h2
  refine ⟨fun u v h ↦ Or.inr ?_, h0, h1, ?_⟩
  · simp only [pathX, triX, id] at h ⊢
    tauto
  · rw [h0]
    exact fun h ↦ h1 h.symm

/-- The merge of notes 0 and 1 into one note, note 2 carried to the other. -/
def mergeσ : Fin 3 → Fin 2 := ![0, 0, 1]

/-- Before the merge, note 0 cites note 2 and note 1 cites nothing. -/
def mergeX (u v : Fin 3) : Prop := u = 0 ∧ v = 2

instance : DecidableRel mergeX := fun _ _ ↦ inferInstanceAs (Decidable (_ ∧ _))

/-- After the merge, the merged note cites the other. -/
def mergeX' (u v : Fin 2) : Prop := u = 0 ∧ v = 1

instance : DecidableRel mergeX' := fun _ _ ↦ inferInstanceAs (Decidable (_ ∧ _))

/-- The unit flow along the merged citation. -/
def unitFlow (u v : Fin 2) : ℝ := if u = 0 ∧ v = 1 then 1 else 0

/-- TRN-15 Strictness, by a merge, and the isometry Result 4 needs is not TRN-3's: merging notes 0
and 1, of which only 0 cited note 2, is a chain map (F1), and its pullback is an isometry under
TRN-3's fiber-weighted inner product (`pull_isometry_wdot`); yet `δ` of the pulled-back unit flow
is `−1` at note 0 and `0` at note 1, while every pullback is constant on the merged pair, so no
inner product on the target, fiber-weighted or any other, gives `σ^* δ' = δ σ^*`. -/
theorem merge_not_metric :
    (∀ u v, mergeX u v → mergeσ u = mergeσ v ∨ mergeX' (mergeσ u) (mergeσ v)) ∧
      (∀ f : Fin 2 → ℝ, pull mergeσ f ⬝ᵥ pull mergeσ f = wdot mergeσ f f) ∧
      ∀ g : Fin 2 → ℝ,
        pull mergeσ g ≠ div mergeX (mask mergeX (pullEdge mergeσ mergeX' unitFlow)) := by
  refine ⟨fun u v h ↦ Or.inr ?_, fun f ↦ pull_isometry_wdot mergeσ f, fun g h ↦ ?_⟩
  · obtain ⟨rfl, rfl⟩ := h
    decide
  · have h0 : g 0 = -1 := by
      simpa [pull, mergeσ, div, mask, pullEdge, mergeX, mergeX', unitFlow, Fin.sum_univ_three]
        using congrFun h 0
    have h1 : g 0 = 0 := by
      simpa [pull, mergeσ, div, mask, pullEdge, mergeX, mergeX', unitFlow, Fin.sum_univ_three]
        using congrFun h 1
    linarith

/-- The directed six-cycle `i → i + 1`. -/
def cyc6 (u v : Fin 6) : Prop := v = u + 1

instance : DecidableRel cyc6 := fun _ _ ↦ inferInstanceAs (Decidable (_ = _))

/-- The directed three-cycle `j → j + 1`. -/
def cyc3 (u v : Fin 3) : Prop := v = u + 1

instance : DecidableRel cyc3 := fun _ _ ↦ inferInstanceAs (Decidable (_ = _))

/-- The six-cycle wound twice around the three-cycle: notes `i` and `i + 3` merged. -/
def wind : Fin 6 → Fin 3 := ![0, 1, 2, 0, 1, 2]

/-- TRN-15 The isometry Result 4 needs is local: winding the six-cycle twice around the three-cycle
merges every note with another, so its pullback is no isometry under the counting inner products
(`pull_isometry_iff`), yet it is a chain map that commutes with `δ`, because each note's citations
go one to one onto its image's (a covering of the citation graphs). -/
theorem wind_metric :
    (∀ u v, cyc6 u v → wind u = wind v ∨ cyc3 (wind u) (wind v)) ∧ fiber wind 0 = 2 ∧
      ∀ ψ : Fin 3 → Fin 3 → ℝ,
        pull wind (div cyc3 ψ) = div cyc6 (mask cyc6 (pullEdge wind cyc3 ψ)) := by
  refine ⟨fun u v h ↦ Or.inr ?_, by decide, fun ψ ↦ funext fun a ↦ ?_⟩
  · simp only [cyc6] at h
    subst h
    revert u
    decide
  · fin_cases a <;> simp [pull, div, mask, pullEdge, cyc6, cyc3, wind, Fin.sum_univ_succ]

end Palace.Transport
