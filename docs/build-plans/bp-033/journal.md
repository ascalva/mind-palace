# bp-033 journal

## 2026-07-14 — authored `proposed` (orchestrator, opus/xhigh graduation)

Graduated from `dn-temporal-retrieval-algebra` §3 Consequence 1 — the **temporal-transport half** of the
`core/temporal/` module: `π_active`, `σ_*`/`σ^*`, and the superconnection curvature `‖[d,τ]‖`. Split from
bp-032 (the topological half) because the objective carried an "and" and each half has an independent
runnable falsifier. **`depends_on: bp-032`** — consumes its `X_cite` assembler + boundary maps +
two-snapshot accessor (honored, not redesigned; an API change is a stop-and-raise → re-graduate bp-032).

**Grounded pass (citations in §3):** the operator definitions + laws come from the note §2.2–§2.3 (A2:
`π_active` = the ambient default projection, idempotent contraction, NOT a chain map; `σ_*` = the opt-in
chain map, degree 0, chain-map iff F1; `σ^*` = the pullback, always a contraction, the Sz.-Nagy dilation
pin). `‖[d,τ]‖` = the **exact** severed-citation-carry-forward count (Result 2, tight — "not a proxy"),
so the check is the operator value vs the discrete count (inversion Rule 2). σ is induced by the
supersession correspondence (`versions.supersessions`, `reference_edges.for_commit`).

**Scoped to the LINEAR CHAIN only** — fork/merge diamonds (σ not single-valued) are TA-c (SKETCH,
data-gated on measured diamond frequency); a diamond is a stop-and-raise, never a silently-averaged σ.
Combinatorial v1 (inherits bp-032's unweighted `A_cite`); asserts only the topological chain-map law, not
metric/kernel coherence (Result 4 / PD-b / TA-a, deferred).

**write_scope** = `core/temporal/**` + one NEW test path (`test_temporal_operators.py`) — clean
(finding-0075). Item numbering continues the family (9–12). Estimate opus/400k. Awaiting the owner-only
`proposed → ready` blessing; **do not build before bp-032 (and bp-031) land.** No code written.
