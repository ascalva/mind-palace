module

public import Mathlib.Algebra.Module.LinearMap.End
public import Mathlib.Algebra.Module.Pi
public import Mathlib.Algebra.Module.Prod
public import Mathlib.Tactic.Abel
public import Mathlib.Tactic.Ring
public import Palace.Transport.Defs

/-!
# The superconnection along a chain of times, the definitions

temporal-retrieval-algebra §2.3 Result 3 writes the temporal transport as a superconnection
`𝔸 = d + τ` on the cochains of the citation complexes `X_n` of a chain of times, and Result 4 asks
whether a transport that commutes with the coboundary `d` also commutes with its adjoint `δ`. The
objects here are those of `Palace/Transport/Defs.lean`: a cochain of a citation complex is a note
cochain with an edge cochain read on the citations; `d` is `coboundary` on them, and the transport
along a note map `σ` is `pull` on notes and `pullEdge` on citations, so that the bracket `[d, τ]` is
TRN-5's `curvature` (`Palace/Superconnection.lean`).

The times form a preorder (on the linear chain, a total order), and the transports live on its
nerve, the nerve of the supersession order (H0 of Result 1): a transport on every pair of times
`s < t`, which is the transitive closure Result 1 takes (H2), with cochains of the times in time
degree 0, of the pairs in degree 1, and of the triangles `s < t < u` in degree 2. That is the
nerve to its 2-skeleton, which is where every component of `𝔸²` lives: `d²` on a time, `[d, τ]` on
a pair, `τ²` on a triangle; a component of higher time degree repeats the condition of its first
pair or first triangle. `τ` is the Čech differential of the nerve with the transports as its
coefficients: the transport on a simplex's first face (`first`) and the alternating sum of the other
faces (`face`).
-/

@[expose] public section

open Finset

namespace Palace.Transport

/-- The citations' mask: an edge cochain read on the citations of `X`, zero off them. -/
def mask {A : Type*} (X : A → A → Prop) [DecidableRel X] (ψ : A → A → ℝ) : A → A → ℝ :=
  fun u v ↦ if X u v then ψ u v else 0

/-- A cochain of a citation complex in both of its degrees: a value on each note, and a value on
each ordered pair of notes, read on the citations through `mask`. -/
abbrev Cochain (A : Type*) := (A → ℝ) × (A → A → ℝ)

/-- The coboundary `d` of the citation complex `(A, X)` on its cochains: a note cochain goes to its
drop on the citations (`coboundary`, read through the mask), an edge cochain to zero, since the
complex has no cells above its citations. -/
def dC {A : Type*} (X : A → A → Prop) [DecidableRel X] : Cochain A →ₗ[ℝ] Cochain A where
  toFun c := (0, mask X (coboundary c.1))
  map_add' c c' := by
    refine Prod.ext (by simp) (funext fun u ↦ funext fun v ↦ ?_)
    simp only [mask, coboundary, Prod.fst_add, Prod.snd_add, Pi.add_apply]
    split_ifs <;> ring
  map_smul' r c := by
    refine Prod.ext (by simp) (funext fun u ↦ funext fun v ↦ ?_)
    simp only [mask, coboundary, Prod.smul_fst, Prod.smul_snd, Pi.smul_apply, smul_eq_mul,
      RingHom.id_apply]
    split_ifs <;> ring

/-- The transport `τ` along a note map `σ : A → B` from the citation complex `(A, X)` to `(B, X')`:
the pullback of note cochains, and of edge cochains through the target's citations (`pullEdge`),
read on the source's. -/
def tC {A B : Type*} (σ : A → B) (X : A → A → Prop) [DecidableRel X] (X' : B → B → Prop)
    [DecidableRel X'] : Cochain B →ₗ[ℝ] Cochain A where
  toFun c := (pull σ c.1, mask X (pullEdge σ X' c.2))
  map_add' c c' := by
    refine Prod.ext (funext fun a ↦ ?_) (funext fun u ↦ funext fun v ↦ ?_)
    · simp [pull]
    · simp only [mask, pullEdge, Prod.snd_add, Pi.add_apply]
      split_ifs <;> ring
  map_smul' r c := by
    refine Prod.ext (funext fun a ↦ ?_) (funext fun u ↦ funext fun v ↦ ?_)
    · simp [pull]
    · simp only [mask, pullEdge, Prod.smul_snd, Pi.smul_apply, smul_eq_mul, RingHom.id_apply]
      split_ifs <;> ring

/-- The pairs of times `s < t`: the 1-simplices of the nerve of the order. -/
abbrev TEdge (T : Type*) [Preorder T] := {p : T × T // p.1 < p.2}

/-- The triangles of times `s < t < u`: the 2-simplices of the nerve. -/
abbrev TTri (T : Type*) [Preorder T] := {p : T × T × T // p.1 < p.2.1 ∧ p.2.1 < p.2.2}

/-- A triangle's first face, `s < t`. -/
abbrev TTri.e01 {T : Type*} [Preorder T] (s : TTri T) : TEdge T := ⟨(s.1.1, s.1.2.1), s.2.1⟩

/-- A triangle's last face, `t < u`. -/
abbrev TTri.e12 {T : Type*} [Preorder T] (s : TTri T) : TEdge T := ⟨(s.1.2.1, s.1.2.2), s.2.2⟩

/-- A triangle's long face, `s < u`. -/
abbrev TTri.e02 {T : Type*} [Preorder T] (s : TTri T) : TEdge T :=
  ⟨(s.1.1, s.1.2.2), lt_trans s.2.1 s.2.2⟩

/-- The total complex of a chain of citation complexes `(V t, X t)`, to the 2-skeleton of the nerve:
the cochains of each time (time degree 0), of each pair of times, valued at its earlier time
(degree 1), and of each triangle of times, valued at its first time (degree 2). -/
abbrev Tot {T : Type*} [Preorder T] (V : T → Type*) :=
  (∀ t, Cochain (V t)) × (∀ e : TEdge T, Cochain (V e.1.1)) × (∀ s : TTri T, Cochain (V s.1.1))

variable {T : Type*} [Preorder T] {V : T → Type*}

/-- The coboundary of the total complex: each time's `d`, with the Koszul sign `(−1)^q` of the
time degree `q`, so that the graded commutator `d τ + τ d` of the two odd operators is the bracket
`[d, τ]` (`Palace/Superconnection.lean`). -/
def dTot (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)] : Module.End ℝ (Tot V) where
  toFun x := (fun t ↦ dC (X t) (x.1 t), fun e ↦ -dC (X e.1.1) (x.2.1 e),
    fun s ↦ dC (X s.1.1) (x.2.2 s))
  map_add' x y := by
    refine Prod.ext (funext fun t ↦ ?_) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_)) <;>
      simp only [Prod.fst_add, Prod.snd_add, Pi.add_apply, map_add, neg_add]
  map_smul' r x := by
    refine Prod.ext (funext fun t ↦ ?_) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_)) <;>
      simp only [Prod.smul_fst, Prod.smul_snd, Pi.smul_apply, map_smul, smul_neg,
        RingHom.id_apply]

/-- The transport part of the Čech differential: on a pair `s < t`, the transport `Θ` of the cochain
at `t`; on a triangle `s < t < u`, the transport along `s < t` of the cochain on `t < u`. -/
def first (Θ : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1)) :
    Module.End ℝ (Tot V) where
  toFun x := (0, fun e ↦ Θ e (x.1 e.1.2), fun s ↦ Θ s.e01 (x.2.1 s.e12))
  map_add' x y := by
    refine Prod.ext (by simp) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_)) <;>
      simp only [Prod.fst_add, Prod.snd_add, Pi.add_apply, map_add]
  map_smul' r x := by
    refine Prod.ext (by simp) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_)) <;>
      simp only [Prod.smul_fst, Prod.smul_snd, Pi.smul_apply, map_smul, RingHom.id_apply]

/-- The face part of the Čech differential, the nerve's own coboundary: on a pair `s < t`, minus
the cochain at `s`; on a triangle `s < t < u`, the cochain on `s < t` less the one on `s < u`. -/
def face : Module.End ℝ (Tot V) where
  toFun x := (0, fun e ↦ -x.1 e.1.1,
    fun s ↦ (x.2.1 s.e01 : Cochain (V s.1.1)) - (x.2.1 s.e02 : Cochain (V s.1.1)))
  map_add' x y := by
    refine Prod.ext (by simp) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_))
    · simp only [Prod.fst_add, Prod.snd_add, Pi.add_apply, neg_add]
    · simp only [Prod.fst_add, Prod.snd_add, Pi.add_apply]
      abel
  map_smul' r x := by
    refine Prod.ext (by simp) (Prod.ext (funext fun e ↦ ?_) (funext fun s ↦ ?_)) <;>
      simp only [Prod.smul_fst, Prod.smul_snd, Pi.smul_apply, smul_neg, smul_sub,
        RingHom.id_apply]

/-- The Čech differential of the nerve with coefficients in the transports `Θ`:
`(τ c)(s, t) = Θ_{st} c_t − c_s` and `(τ e)(s, t, u) = Θ_{st} e_{tu} − e_{su} + e_{st}`. -/
def cech (Θ : ∀ e : TEdge T, Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1)) : Module.End ℝ (Tot V) :=
  first Θ + face

/-- The transports of a chain of citation complexes whose notes the maps `σ` carry from each time
to each later one: `tC` on every pair of times. -/
def trans (X : ∀ t, V t → V t → Prop) [∀ t, DecidableRel (X t)]
    (σ : ∀ e : TEdge T, V e.1.1 → V e.1.2) (e : TEdge T) :
    Cochain (V e.1.2) →ₗ[ℝ] Cochain (V e.1.1) :=
  tC (σ e) (X e.1.1) (X e.1.2)

/-- The divergence of an edge cochain over the citations of `X`, in-flow less out-flow: the adjoint
`δ` of the coboundary under the counting inner products (`sum_mask_coboundary_mul`). -/
def div {A : Type*} [Fintype A] (X : A → A → Prop) [DecidableRel X] (ψ : A → A → ℝ) : A → ℝ :=
  fun a ↦ ∑ x, (mask X ψ x a - mask X ψ a x)

end Palace.Transport
