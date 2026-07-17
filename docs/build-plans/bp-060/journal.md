# Journal — bp-060 (the (σ,t) conductance profile + reconnection)

## 2026-07-17 — graduated (proposed), not yet started
Minted by /graduate from RATIFIED `dn-connectivity-instruments` CN-3 + CN-4. Status `proposed` — awaits
the owner's `proposed → ready` blessing. **Depends on bp-059** (imports its module surface).

**Grounding carried in the plan:**
- Signs are LAW (D1 retired): series churn impedes (−s_seq), lateral conducts (+s_lat); only the
  `CONDUCTANCE_THRESH` magnitudes tune, shipped at 0. No `ops/levers.py`.
- `χ_s` + depth budget grounded in `spine.n_s`/`events`/`proper_time`; finding-0090 (proper-time erratum)
  does NOT block — CN-4 uses N_s *counts*, not the metric's exactness.
- Reconnection is synthetic-verified (leave-one-out) for v1; the real-corpus historical scan inherits
  bp-059's `MirrorView` cut-restriction gap → partial, parked.
- Degeneracy self-diagnostic `corr(R_eff, 1/d_A+1/d_B)` on EVERY profile (von Luxburg).

**Next when built:** item 4 (profile + self-diag) → 5 (churn/χ_s/depth-budget) → 6 (reconnection + entry).
Estimate opus/200k.
