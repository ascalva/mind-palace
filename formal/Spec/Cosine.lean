module

public import Palace.Cosine.Defs

/-!
# Vectors stored in float16: the cosine error bound and the margin certificate, the statements

VEC-1 (`docs/LAWS.md`, XIII). The vector store holds each float32 vector `y` the embedder returns
as `round16 y`, every coordinate rounded to binary16 (dn-vector-membership-store A4), and LanceDB
scores a query against that column by rounding the query to float16 as well, then computing
`1 − cosine` in float32 (both measured on this machine, lancedb 0.33.0). The statements cover the
two roundings, through the binary16 model `rn16 = rnf 11 (-24)` that the attacks in
`PalaceTest/Format.lean` check bit for bit against this machine's float16. The float32 arithmetic
of LanceDB's distance kernel is not modelled: its error is the hypothesis `γ` of `top_unchanged`,
which `core/kernel/margin.py` sets from the summation bound `2 (d + 4) 2⁻²⁴` and its falsifier
checks against the kernel's measured error. The norm floor `ν` is a hypothesis about the corpus:
the embedder's vectors are unit length, and the store takes `ν = 1/2`.

These are the laws of `Palace/Cosine.lean` as the ledger cites them, each with its proof left as
`sorry`. `lake comparator` checks that the `Palace` library proves each one exactly as stated
here, from the standard axioms alone.
-/

@[expose] public section

namespace Palace.Cosine

open Palace.Format

/-- **VEC-1** Rounding to binary16 moves a real number by at most `2⁻¹¹ · max |x| 2⁻¹⁴`: relative
error `2⁻¹¹` in the normal range, half the subnormal spacing `2⁻²⁴` below it. -/
theorem abs_rn16_sub_le (x : ℝ) : |rn16 x - x| ≤ u16 * max |x| tau16 :=
  sorry

/-- **VEC-1** Float16 storage moves a vector in `d` dimensions by at most
`2⁻¹¹ √(‖x‖² + d · 2⁻²⁸)`. -/
theorem norm_round16_sub_le {ι : Type*} [Fintype ι] (x : EuclideanSpace ℝ ι) :
    ‖round16 x - x‖ ≤ u16 * √(‖x‖ ^ 2 + Fintype.card ι * tau16 ^ 2) :=
  sorry

/-- **VEC-1** Moving either vector from `x` to `y` moves a cosine by at most
`2 ‖x − y‖ / (‖x‖ + ‖y‖)`: Cauchy and Schwarz, and the inner-product form of Dunkl and Williams'
inequality `‖x/‖x‖ − y/‖y‖‖ ≤ 2 ‖x − y‖ / (‖x‖ + ‖y‖)`. -/
theorem abs_cosine_sub_le {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] (q x y : F) :
    |cosine q x - cosine q y| ≤ 2 * ‖x - y‖ / (‖x‖ + ‖y‖) :=
  sorry

/-- **VEC-1** Scoring with `q'` in place of the query `q` moves a cosine by at most
`betaQuery q q'`; the store computes it from the query and its float16 rounding. -/
theorem abs_cosine_sub_query {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F]
    (x q q' : F) : |cosine q' x - cosine q x| ≤ betaQuery q q' :=
  sorry

/-- **VEC-1** Float16 storage moves the cosine between any query and a vector of norm at least `ν`
by at most `betaStore d ν = 2η / (2 − η)`, `η = 2⁻¹¹ √(1 + d · 2⁻²⁸ / ν²)`. -/
theorem abs_cosine_round16_sub_le {ι : Type*} [Fintype ι] (q x : EuclideanSpace ℝ ι) {ν : ℝ}
    (hν : 0 < ν) (hx : ν ≤ ‖x‖) (hη : eta (Fintype.card ι) ν < 2) :
    |cosine q (round16 x) - cosine q x| ≤ betaStore (Fintype.card ι) ν :=
  sorry

/-- **VEC-1** The margin certificate. If every score `s j` is within `β` of the true score `t j`,
and the members of `S` beat every non-member by more than `2β`, then under the true scores every
member still beats every non-member, and `S` is their only top set of its size. -/
theorem top_eq_of_margin {κ : Type*} {s t : κ → ℝ} {β : ℝ} (h : ∀ j, |s j - t j| ≤ β)
    {S : Finset κ} (hm : ∀ i ∈ S, ∀ j ∉ S, s j + 2 * β < s i) :
    (∀ i ∈ S, ∀ j ∉ S, t j < t i) ∧ ∀ T : Finset κ, T.card = S.card → IsTop t T → T = S :=
  sorry

/-- **VEC-1** The certificate the store computes. Let each stored vector be the float16 rounding
of a float32 vector `y j` of norm at least `ν`, let the store score with `q'` in place of the
query `q`, and let each computed score `s j` be within `γ` of the cosine of `q'` and the stored
vector. When the members of `S` beat every non-member by more than
`2 (betaStore d ν + betaQuery q q' + γ)`, the exact cosines between `q` and the `y j` rank `S`
strictly above the rest, and `S` is their only top set of its size: float16 storage cannot have
changed it. -/
theorem top_unchanged {ι : Type*} [Fintype ι] {κ : Type*} {y : κ → EuclideanSpace ℝ ι}
    {q q' : EuclideanSpace ℝ ι} {s : κ → ℝ} {γ ν : ℝ} (hν : 0 < ν) (hy : ∀ j, ν ≤ ‖y j‖)
    (hη : eta (Fintype.card ι) ν < 2) (hs : ∀ j, |s j - cosine q' (round16 (y j))| ≤ γ)
    {S : Finset κ}
    (hm : ∀ i ∈ S, ∀ j ∉ S,
      s j + 2 * (betaStore (Fintype.card ι) ν + betaQuery q q' + γ) < s i) :
    (∀ i ∈ S, ∀ j ∉ S, cosine q (y j) < cosine q (y i)) ∧
      ∀ T : Finset κ, T.card = S.card → IsTop (fun j ↦ cosine q (y j)) T → T = S :=
  sorry

end Palace.Cosine
