---
type: build-plan
id: bp-082
track: sync-diac-dreamers
status: complete
design_ref:
  - docs/design-notes/synchronic-diachronic-dreamer.md
contract: builder
write_scope:
  - core/graph/influence.py
  - core/dreaming/conditioning.py
  - tests/unit/test_influence.py
  - tests/unit/test_conditioning_law.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 280k
  actual:
    model: opus            # claude-opus-4-8, tier verified on return
    tokens: 269887
    tool_calls: 78
    duration_min: 26
    ratio: 0.96            # well-pinned; Q3 stop-and-raise did NOT fire (derived_from carries the mark)
    session_delta: "post-reset pool; ran parallel with the fable synthesis pass"
depends_on: [bp-079, bp-081]
parallelizable_with: []
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/synchronic-diachronic-dreamer.md
  - docs/design-notes/connectivity-instruments.md
  - docs/brainstorms/clock-curvature.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — H-2: influence v1 + the conditioning law

> Graduated from ratified `dn-synchronic-diachronic-dreamer` (§2.7 SD-7; §3 H-2). The
> conditioning law is the note's load-bearing new law — the anti-laundering tooth; it fails
> closed. Addition-only overlays (SD-e parks removals).

## 0. Mode & provenance

Investigation and planning produced this; implementation proceeds item-by-item on owner
approval. `proposed → ready` stays owner-only, by hand. Gated on the cross-strata G-gates for
any grant touching non-mirror strata (note §3).

## 1. Objective

The influence of a staged overlay is the per-instrument with/without differential — perturbative
where valid, exact where not — with CN-3 leave-one-out attribution, and the same differential
marks every conditioned dream artifact with hypothesis provenance that TTL-inherits.

## 2. Context manifest

1. `docs/design-notes/synchronic-diachronic-dreamer.md` — §2.7 verbatim (the definition, the
   two families, the one-sided laws, the conditioning law's four clauses, F-SD7a/F-SD7b), §2.6
   (generations; what a conditioned reading pins).
2. `docs/design-notes/connectivity-instruments.md` — CN-3 (the attribution law this
   generalizes: every claim names the Δ-elements it verified leave-one-out), CN-7 (refusal
   posture).
3. `core/graph/composed.py` (as extended by bp-081) — the overlay assembly influence reads over.
4. `core/graph/{sigma_star,conductance}.py` — the instruments diffed; conductance's CN-4 weight
   (`conductance.py:47`) and the Laplacian surface for ΔL.
5. `core/stores/staging.py` (bp-081) — generations, staged digests.
6. `docs/build-plans/bp-079/plan.md` — the charter/budget the influence dispatch runs under.
7. `docs/brainstorms/graph-at-a-past-cut.md` — D5 (growth monotonicity, the one-sided law's
   ground).

## 3. Investigation & grounding

- **Q1 — is there an existing with/without diff to reuse?** CN-3's reconnection attribution is
  the shape (leave-one-out over a Δ-set, verified per claim) — reused as law, not as code; the
  builder reads CN-3's implementation home at HEAD and reuses its helpers where importable
  (DRY: audit before re-implementing).
- **Q2 — what surface exposes ΔL for the smooth family?** The conductance family's Laplacian
  (`core/graph/conductance.py`; CN-4 weights at :47). The overlay's ΔL is the staged class's
  weight contribution at assembly. The builder confirms the exact matrix surface at HEAD; if
  the Laplacian is not exposed in a form admitting a Δ decomposition, that is a finding, not an
  inline refactor of `conductance.py` (out of write_scope, deliberately).
- **Q3 — where do dream artifacts record provenance/derives tails today?** The builder reads
  the dreamer's report/derives shape at HEAD (`core/dreaming/dreamer.py`, the DerivedStore
  write path) BEFORE implementing clause 1 — the conditioning record must ride the existing
  provenance shape, not invent a parallel one. The code was not read at graduation for this
  seam: **the code does not settle clause-1's exact field placement; the builder cites it at
  build start** and stops if the derives shape cannot carry tails without schema change
  (finding, not improvisation).
- **Q4 — the second-order bound for F-SD7a.** The note flags the perturbation mathematics
  `[FROM MEMORY — verify]`. The builder verifies the first-order form against a numerical
  fixture FIRST (finite difference on a small synthetic Laplacian) and treats the analytic
  citation as unverified until the external-grounding sweep clears it — the fixture, not the
  citation, is the acceptance ground.

**Additional risks or questions surfaced during reading:** Q3 is the likeliest stop-and-raise;
budgeted for.

## 4. Reconciliation

- `dn-recursive-dreaming-bounded-by-grounding` rule 1 — "grounding terminates in authored
  evidence" → **cross-ref: extension** (already ruled in the ratified note §2.7-4): grounding
  terminates in authored evidence **or declared hypothesis, marked as such**. This plan
  implements the mark; the draft note's text is annotated by cross-reference at its next touch,
  never silently edited by this builder (out of write_scope).

## 5. Write scope

Two new modules — `core/graph/influence.py` (the differential, both families, one-sided
assertions) and `core/dreaming/conditioning.py` (the four-clause law over dream artifacts) —
plus their tests. Deliberately OUT: `core/graph/{sigma_star,conductance,composed}.py` (consumed,
never edited — Q2's finding path exists for a reason), `core/dreaming/dreamer.py` (Q3 reads it;
extending it is a finding if the provenance shape can't carry tails), the staging store
(bp-081's), all durable stores, all design notes.

## 6. Interfaces pinned inline

- **The definition (note §2.7, binding):** for staged perturbation Δ and instrument reading R,
  `infl_R(Δ) = R(G ∪ Δ) − R(G)`. Two families: **smooth** (Rayleigh/spectral — first-order
  `infl_λ(Δ) ≈ x*ΔL x` for a simple eigenpair, `[FROM MEMORY — verify]`, finite-difference
  checked) and **integer** (census, σ* component structure — exact recompute-diff, delta-local
  where combinatorics allow; integers do not perturb).
- **One-sided law (binding, structural):** a pure-addition overlay can only raise conductance
  and σ* (weighted Rayleigh + D5 growth monotonicity) — additive influence is signed
  non-negative structurally; a negative reading is an implementation bug, never a finding.
- **Attribution (CN-3 generalized verbatim):** the Δ-elements are exactly the staged items;
  every influence claim names the staged element(s) it verified leave-one-out.
- **The conditioning law (note §2.7, all four clauses, binding):** (1) a conditioned artifact
  records `(subspace_id, generation, staged-item digests)` and its `derives` tails include the
  staged content addresses; (2) TTL inheritance — expired subspace ⇒ its conditioned artifacts
  leave the surfacing set (retained as records); (3) per-claim leave-the-subspace-out recompute
  splits claims into corpus-grounded (bit-identical without overlay — may shed the mark) and
  conditioned (keeps it) — influence detection and taint attribution are the SAME diff; (4)
  grounding terminates in authored evidence or declared hypothesis, marked — never prior
  interpretation; the recursion bound untouched.

## 7. Items

### Item 11 — integer-family influence (exact diff) + attribution

- **Objective:** Δcensus and Δ(σ* component structure) over the overlay, delta-local, with
  CN-3 leave-one-out attribution.
- **Files:** `core/graph/influence.py`, `tests/unit/test_influence.py`
- **Acceptance test:** planted overlay fixtures — a staged bridge edge flips a two-component σ*
  from None to a reading and the influence claim names exactly that staged edge; a staged arc
  closing a directed cycle appears in Δcensus with its witness; empty overlay ⇒ zero influence.
- **Falsifier:** an influence claim naming staged elements whose leave-one-out removal does NOT
  change the reading (attribution is decorative).
- **Invariant(s):** read-only over assembly; refusal under budget (CN-7 posture) rather than
  partial materialization (L4).
- **Touches stored data?** No.
- **Parallelizable?** With Item 12. **Depends on:** bp-081 (overlay), bp-079 (charter/budget).

### Item 12 — smooth-family influence (perturbative) + the finite-difference check

- **Objective:** the Rayleigh first-order estimator with its validity check.
- **Files:** `core/graph/influence.py`, `tests/unit/test_influence.py`
- **Acceptance test:** on a synthetic Laplacian, the estimator agrees with the exact
  recompute-diff within the stated second-order bound for small Δ, and the reading declares
  "perturbative"; past the bound the implementation switches to exact and declares
  "recomputed, not perturbative"; the one-sided addition law asserted structurally (a negative
  additive influence fails the suite).
- **Falsifier:** F-SD7a — estimate vs exact diff beyond the stated bound WITHOUT the declared
  switch to recompute.
- **Invariant(s):** the `[FROM MEMORY]` analytic form is treated as unverified (Q4): the
  numerical fixture is the ground; the citation flag stays in the code comment for the
  external-grounding sweep.
- **Touches stored data?** No.
- **Parallelizable?** With Item 11. **Depends on:** bp-081, bp-079.

### Item 13 — the conditioning law

- **Objective:** the four clauses over conditioned dream artifacts; fails closed.
- **Files:** `core/dreaming/conditioning.py`, `tests/unit/test_conditioning_law.py`
- **Acceptance test:** a conditioned fixture artifact carries (subspace_id, generation, staged
  digests) with derives tails including staged content addresses; after fixture expiry the
  artifact leaves the surfacing set but remains readable as a record; the per-claim taint split
  — a claim bit-identical without the overlay sheds the mark, a delta-bearing claim keeps it —
  computed by the SAME diff as Items 11–12.
- **Falsifier:** F-SD7b, all three teeth — a "corpus-grounded" claim that changes when the
  subspace is removed; a conditioned artifact surfacing past expiry; a derives edge omitting
  staged digests. Any one observed ⇒ the law is broken; it must fail closed (block surfacing),
  never warn.
- **Invariant(s):** recursion bound untouched (dreams never cite dreams as evidence); the mark
  rides the EXISTING provenance shape (Q3 — stop if it can't).
- **Touches stored data?** Yes — conditioned artifacts in the derived/staging fixtures only;
  dry-run first; no durable-store schema change (Q3's stop condition).
- **Parallelizable?** No. **Depends on:** Items 11–12.

## 8. Math carried explicitly

- **`infl_R(Δ) = R(G ∪ Δ) − R(G)`** — *measures:* the reading differential along the overlay
  direction — influence as a measured delta, not a narrative. *valid when:* addition-only
  overlays (v1); both computation families agree where both apply. *fails its keep if:* the
  diff is dominated by numerical noise at corpus scale, or claims built on it don't survive
  leave-one-out attribution.
- **First-order eigenvalue perturbation `x*ΔL x`** `[FROM MEMORY — verify]` — *measures:* the
  smooth-family influence estimator. *valid when:* simple eigenpair, ‖ΔL‖ small vs spectral
  gaps (Weyl-bracketed, also `[FROM MEMORY — verify]`). *fails its keep if:* F-SD7a — the
  finite-difference check disagrees beyond the stated bound without a declared recompute.
- **The one-sided addition law** — *measures:* nothing; it is a structural assertion (pure
  addition ⇒ σ*/conductance non-decreasing, D5). *valid when:* v1 addition-only overlays.
  *fails its keep if:* a negative additive influence ever surfaces as a "finding" instead of
  failing the suite as a bug.

## 9. Non-goals

No edit/removal overlays (SD-e — the opposite one-sided law, its own pass); no spectral
influence upgrade (SD-f — P8-coupled); no dispatch wiring beyond the charter's existing seams;
no narration of influence claims (a later D-plan touch once H-2 readings exist); no scheduler
or sweep changes (bp-081 owns those); never a promotion path (bp-081's spine invariant binds
here identically).

## 10. Stop-and-raise conditions

Q3 fires (the derives/provenance shape can't carry tails without schema change) → finding,
park Item 13, land Items 11–12; Q2 fires (no Δ-admitting Laplacian surface) → finding, land
the exact-diff family only; the G-gates unmet for a non-mirror grant fixture → use mirror-only
fixtures and note it; a blessing → never.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| removal overlays (SD-e) | addition-only v1 | ship removals now (different math, opposite one-sided law, different falsifiers — conflation risk) | a real counterfactual question needs removal → its own small design pass |
| spectral influence (SD-f) | combinatorial + Rayleigh only | eigenvector localization now (P8/sknetwork unresolved; ML-b gauge caution) | P8 resolves AND F-SD7a shows the family needs the finer instrument |
| influence claims in narration | compute only, no narration item | narrate now (no vocabulary ruling exists for influence claims — §2.9 covered census claims only) | a design touch rules the influence vocabulary (owner) |

## 12. Dependency & ordering summary

Items 11 ∥ 12 (same module, disjoint functions) → 13 (consumes their diff). Depends on bp-081
(the overlay + staging) and bp-079 (charter/budget); nothing depends on this plan inside the
family — it is the capstone. Cross-strata G-gates bind any non-mirror-grant fixture. Family
sequencing: behind bp-069/070/071 + M0/S1 at the owner's blessing; last of the four.
