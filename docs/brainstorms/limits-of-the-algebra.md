---
type: brainstorm
id: limits-of-the-algebra
track: query-language
created: 2026-11-04
status: open
links:
  - docs/design-notes/dn-query-sentence-algebra.md      # §2.6 the response, §2.9 the support
  - docs/design-notes/temporal-retrieval-algebra.md     # §2.3 Results 1–6 (Result 5: the pullback)
  - docs/design-notes/magnetic-laplacian.md             # the frustration lift
  - docs/LAWS.md                                        # RSP-3's cone boundary, CND-2, QSA-9, RSP-5
---

# Limits of the algebra — the program

> The owner, 2026-11-04: *"Penrose found so much rich math, theory, and intuition by pushing
> Einstein's theories to their limits, especially when it comes to black holes; in a similar way, I
> want you to push the limits of the system and see what we find; we can be a little reckless when
> it comes to pushing the math and theory to its limits."* This note is the program: each limit of
> the retrieval algebra where a smooth law stops being smooth, with the conjecture the limit
> suggests, the falsifier that would kill it, and what is proved or measured so far. Recklessness
> is in the conjecturing; the ledger admits only what is proved, and a refuted conjecture is a
> finding, not a loss.

## L1. The sever singularity — a bridge is a horizon

`assume sever S a b` is the rank-one update `L ↦ L − w (e_a − e_b)(e_a − e_b)ᵀ` (QSA-9), and the
inverse's exact response is Sherman–Morrison with the denominator `1 − w·rEff(a, b)`. The response
theory is regular while the denominator is positive and **singular when it vanishes**. Conjecture:
`w·rEff(a, b) ≤ 1` always (the direct edge alone has resistance `1/w`, and the rest of the graph
can only lower it — Rayleigh, CND-2), with **equality iff the edge is a bridge**: severing a bridge
disconnects, every effective resistance across it becomes infinite, and the symbolic sign rule
"removing weight raises every resistance along paths through the edge" degenerates to "to
infinity". Kirchhoff reads `w·rEff(e)` as the probability that a random spanning tree contains
`e`; the horizon is probability one. *Status — the inequality is machine-checked (Palace/Sever.lean, SEV-1 to SEV-3, design
theorems):* `pinv_unique` (Penrose's four equations determine `M⁺`, so a closed form is checked,
not computed), `lapPinv_single` (the single edge's `L⁺ = d dᵀ/4w`, `d = e_a − e_b`), `rEff_single`
(`= 1/w`), `mul_rEff_le_one` (`w·rEff_A(a, b) ≤ 1`, by `rEff_anti`, CND-2, against the single edge
lying under `A`) and `one_sub_mul_rEff_nonneg` (the Sherman–Morrison denominator never goes
negative). The bridge → equality direction is machine-checked too (SEV-4,
`mul_rEff_eq_one_of_bridge`: when `a ~ b` is the only edge across a cut, Thomson's principle with
the test potential `(1/w)·1_S` meets the bound, so `w·rEff = 1`, the sever's denominator vanishes
and the horizon is reached), and so is the converse (SEV-5, `mul_rEff_lt_one_of_reachable`: when
`a` still reaches `b` without the edge, the unit current out of `a` must leak through the detour —
by the maximum principle on the unit potential, proved here for the library, every share is
nonnegative, and a zero share would carry the source potential along the detour to the sink).
With the cut reading of a bridge (`isBridgeCut_iff_not_reachable`), the horizon is exactly the
bridges: `w·rEff = 1 ↔ IsBridgeCut` (`mul_rEff_eq_one_iff`), and `assume sever`'s denominator
vanishes precisely where severing disconnects (`one_sub_mul_rEff_eq_zero_iff`). *Measured*
(`eval/sever_horizon.py`, read-only on the live backbone): 38 notes, 38 edges, the bound holds
with its maximum exactly 1; the 11 bridges are exactly the 11 edges at the horizon, as the
theorem says, so `assume sever` of any of them is the singular case; the median `w·rEff` is 0.41,
and every other edge sits below 0.9. *Falsifier:* none left; L1 is closed both ways.

## L2. The β-limits of the retrieval curve — where the kernel freezes and where it melts

`e^{−βφ}` is positive definite for every `β` on a connected support (RSP-3). As `β → ∞` the
killed walk concentrates on the heaviest paths and `φ_β` tends to the shortest-path distance
(the known RSP limit); as `β → 0` it tends to a commute-time-like quantity. Conjecture: the
*rank* of the nearness matrix `e^{−βφ}` is full for every finite `β` but its condition number
diverges exponentially in `β` — the kernel "freezes" into a tree metric — and HYBRID's Schur
product with `K_sem` loses the cone at a finite `β*` that is a property of the graph (RSP-3's
`K₂,₃` leaves it at `β = 100`). *Status — measured 2026-11-04 on the live backbone* (38 notes, 38 edges, 12 isolated, read-only
sweep of `β ∈ [0.25, 128]`): `e^{−d_β}` **stays in the cone at every `β`** (least eigenvalue
0.94 → 0.017, positive throughout), and so does `K_sem ∘ e^{−d_β}` (0.94 → 0.027 — never below
`e^{−d_β}`'s own, as Schur's theorem with a unit-diagonal factor predicts); the condition number
grows **about linearly** in `β` (3.2 at `β = 1`, 820 at `β = 128`), not exponentially as
conjectured; and `d_β` converges to the shortest-path metric in the edge lengths `−log w`
(correlation 0.92 → 0.9992, the largest deviation 0.06 at `β = 128`, the median ratio 1.10 and
falling) — the known RSP limit, confirmed on the owner's notes. So the live backbone is NOT a
`K₂,₃`: the cone boundary RSP-3 witnesses on that graph is not reached here, and the conjecture
sharpens to a question about the graph's cycle structure (FitzGerald–Horn: a Hadamard power
`1/β < n − 2` of a correlation matrix *may* leave the cone, and does on `K₂,₃`; when must it?).
*Falsifier of the sharpened conjecture:* a backbone with no `K₂,₃` minor that leaves the cone.

## L3. The pullback that is not a contraction — refuting Result 5

Temporal-retrieval §2.3 Result 5 pins the ledger's dilation to the pullback `σ^*` of a
supersession map, "always a contraction".
Under a **merge** `σ : {a, b} ↦ c`, `(σ^* f)(a) = (σ^* f)(b) = f(c)`, so `‖σ^* f‖² = 2 f(c)²`:
the pullback *expands* by `√2`, and in general `‖σ^*‖ = √(max fiber)`. The push-forward `σ_*` is
the contraction; the adjoint is not. *Status — machine-checked (Palace/Transport.lean, TRN-1 to TRN-3, design theorems; the
library builds under `--wfail`, mk_all and the L1 gate pass):* `push_dotProduct` (`σ_*` is the adjoint of `σ^*`), `pull_dotProduct_self` (`‖σ^* f‖²
= ∑_b |σ⁻¹ b| f_b²`), `pull_dotProduct_self_le` (`≤ (max fiber)·‖f‖²`), `pull_not_contraction`
(the merge of two notes doubles the constant cochain's energy), and the correction
`pull_isometry_wdot` / `pull_isometry_iff`: under the fiber-weighted inner product `⟨f, g⟩_σ =
∑_b |σ⁻¹ b| f_b g_b` the pullback is an isometry, and under the counting one iff nothing merges.
Result 5's "pullback, always a contraction" is therefore false under merges and true for the
right inner product — PD-b's customer, as Result 4 predicted. The dual (TRN-4,
`push_wdotInv_le`): the push-forward is a contraction under the *inverse*-fiber-weighted inner
product on the target, by Cauchy–Schwarz on each fiber — the inner product Result 6's
γ-contraction must name once supersessions merge (issue #61). The amendment of the note is the
owner's; the finding is filed. *Falsifier:* none — it is a counterexample.

## L4. The frustration lift — how far the zero mode rises

A balanced signed graph keeps the zero mode of `L̄`; a contradiction lifts it
(`zero_energy_iff_balanced`). Conjecture: the lift is controlled by the frustration index — the
least number of edges whose sign flip restores balance — `λ_min(L̄) ≤ 4·w_max·frustration / n`
and `λ_min(L̄) > 0` iff unbalanced. The hypothetical `assume contradict a b` is then a measurement
of how far one contradiction moves the spectrum: a single frustrated edge on a dense balanced
graph barely lifts it; on a tree it is the whole story. *Status — measured, and the bound is a
theorem:* on the live instance's 20 relation edges (12 notes, one component; scratch script
`l4_frustration.py`, read-only) the graph is already unbalanced — frustration index 1, weight
`F_w = 0.831`, `λ_min(L̄) = 0.190` — and every one of the 20 single flips holds the bound (largest
ratio 0.69). The bound holds for a reason: the switching `s ∈ {±1}^V` that balances all but the
frustrated edges has `sᵀ L̄ s = Σᵢⱼ (|Aᵢⱼ| − Aᵢⱼ sᵢ sⱼ) = 4·F_w` and `sᵀ s = n`, so the Rayleigh
quotient gives `λ_min(L̄) ≤ 4·F_w / n ≤ 4·w_max·frustration / n` — the conjecture with the weighted
frustration in place of the count, which is sharper. *Machine-checked (Palace/Frustration.lean,
design theorems):* FRU-1 `dotProduct_signedLap_signing` (`sᵀ L̄ s = 2·frustrated(s)`, the frustrated
weight over ordered pairs) with `dotProduct_self_signing` and `rayleigh_signing`; Courant–Fischer's
floor `exists_eigenvalue_mul_le_dotProduct` (some eigenvalue lies under every Rayleigh quotient,
through the orthonormal eigenbasis — new to the library, and reusable for every spectral bound);
FRU-2 `exists_eigenvalue_le_frustrated` (the least eigenvalue of `L̄` is at most
`2·frustrated(s)/|V|` for every signing, so at most `4·F_w/n`). *Falsifier:* none left for the
bound; the measurement says the lift of one contradiction on this graph is 0.4–0.7 of it.

## L5. The support singularity — the quantitative RSP-5

RSP-5 is one-sided only when the walk keeps the graph's degrees. With a census truncated at
`k` nearest units, the degree is under-counted by the leaked weight `ℓ_i`, and the support's walk
over-estimates transitions by `d_i / (d_i − ℓ_i)`. Conjecture: the nearness on the support is at
most `(1 + ε)^{2·depth}` times the graph's where `ε = max_i ℓ_i / (d_i − ℓ_i)` — so a census that
leaks a fraction `ε` costs a factor polynomial in the path length, never worse. *Status — machine-checked, and sharper
than the conjecture (Palace/Leak.lean, design theorems):* the cost of a leak is not a factor per
step but a reparametrization of the killing. With every degree under-counted by at most the
fraction `ε/(1+ε)` (`d_i ≤ (1+ε)(d_i − ℓ_i)`), the leaky walk lies entrywise under the graph's walk
at killing `(1+ε)·z` (LEAK-1, `leakyWalk_le`: an under-counted degree is a hotter transition), so by
RSP-5's monotonicity the leaky support's nearness at `z` is at most the full graph's nearness at
`(1+ε)·z` whenever `(1+ε)·z < 1` (LEAK-2, `nearnessLeaky_le_nearness`) — uniform in the depth. The
support singularity is `(1+ε)·z = 1`: past it the leaky walk need not converge, and no temperature
of the graph bounds its answer. The census notes how many papers were truncated, not yet how much
weight leaked — the number LEAK-2 wants. *Falsifier:* none left for the bound.

## L6. The product automaton's horizon — when `via` cannot be regular

The chain grammar is regular by decision (FG-c). Push: is there a *sound* retrieval rule that is
not regular — "a chain that returns to a note it has visited" (a context-free constraint), or
"as many citations out as in" (counting)? If every sound rule the owner states is regular, FG-c
stands as a theorem of the practice; if one is not, the automaton needs a stack. *Status:* a
question for the owner's sentences; the battery (QL-4) is where it surfaces.

## What to do first

L3 (a refutation, cheap, and it corrects a ratified note), then L1's inequality (two proved
directions and an attack for the third), then L2's measurement on the live backbone. L4, L5 and
L6 wait on the owner's taste for the next limit.
