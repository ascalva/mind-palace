# Journal — bp-058: the σ-sweep experiment wiring

## Status: PROPOSED (awaiting owner `proposed → ready` blessing — owner-only, by hand)

### Graduation (2026-07-17, orchestrator, opus/high)
Graduated from the RATIFIED, FROZEN pre-registration `dn-sigma-sweep-experiment` (commit `d932670`).
The note §3 licenses exactly ONE thin build item (~100–120k, eval/scripts write scope, no core); this
plan is that item, decomposed into three serial sub-items (control battery → blind sample → composite
report). All consumed interfaces are BUILT (sweep/fibers/gate/report/registry/store/CertifiedCut/the
F9 fixtures) and pinned inline in §6 verbatim from their sources — a builder infers no design.

Grounded pass complete: §3 answers Q1–Q6 with `path:line` citations; the one open definition
(tier-stability partition, Q6) is a recorded grounded decision, parked in §11, not inferred silently.
Two layering risks surfaced and mitigated in §3 (importing the `tests/quality/` fixtures into a
shipped harness module — a legitimate reuse the note V3 mandates; and no-silent-caps everywhere).

**Estimate:** opus / 150k (calibrated against bp-057: 2 items, 162k actual; this is 3 thinner
wiring items, no new math — glue + evidence rendering + tests). Blast radius: all read-only sensing;
writes only `data/reports/`.

**Next (gated on the owner):** owner reviews bp-058 item-by-item and blesses `proposed → ready` by
hand (record the bless commit). THEN `/build bp-058` — self-build or one delegated opus builder,
serial, fresh worktree off HEAD, RESERVE finding-0096, 5-leg gate (ruff · mypy targeted 0 · argless
**69** · type_gate · pytest not-live), merge, seal with cost.actual. Do NOT build before the bless.
