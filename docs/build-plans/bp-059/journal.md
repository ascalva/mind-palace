# Journal — bp-059 (σ*/MST, the keystone)

## 2026-07-17 — graduated (proposed), not yet started
Minted by /graduate from RATIFIED `dn-connectivity-instruments` CN-1 + CN-2. Status `proposed` —
awaits the owner's `proposed → ready` blessing (owner-only, by hand).

**Grounding carried in the plan (so a fresh builder needn't re-derive):**
- `MirrorGraph.build(view, *, sigma)` takes **NO cut** (`core/dreaming/graph.py:32-40`); `MirrorView`
  has **no cut-restriction surface** (`core/mirror.py:96-105`). Resolution: v1 pins to the **latest
  cut** via `spine.cut_at(strata=frozenset({"mirror"}))`, recorded in `ConnEvidence`; historical
  cut-restriction is PARKED (§11 — a future `core/` plan).
- σ* falsifiers are structural (ultrametric inequality; MST≡union-find), **not** a recall signal —
  finding-0096 established golden_recall saturates at this scale; do NOT couple σ* to recall.
- Evidence pinning copies the `FibersEvidence` pattern (`eval/harness/fibers.py:112-133`).

**Next action when built:** item 1 (CN-1 scaffolding) → item 2 (MST/σ*) → item 3 (entry point +
quality battery). 3-item serial. Estimate opus/180k.
