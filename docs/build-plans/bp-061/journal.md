# Journal — bp-061 (type-checked bridges + arc search)

## 2026-07-17 — graduated (proposed), not yet started
Minted by /graduate from RATIFIED `dn-connectivity-instruments` CN-5 + CN-7. Status `proposed` — awaits the
owner's `proposed → ready` blessing. **Depends on bp-059 + bp-060.**

**Grounding carried in the plan:**
- Load-bearing gap: idea-graph edges carry **no Scope**. v1 node→scope = `MirrorView.SCOPE` ⊓ the note's
  spine-event `TimeScope`. All nodes are `MIRROR_AUTHORED` ⇒ Σ-meet trivial; the **live axis is TIME**, and
  the atlas T-meet (`SpineAtlas.has`) is CN-5's cross-clock type-checker — an uncovered clock RAISES
  `NoCommonClockError` = the chain refuses (anti-hallucination).
- Dominance pruning is sound because `meet ⊑ self` (scopes only narrow) — search over `(node, scope)` states.
- Field guidance = bp-060's Laplacian potential (import, don't recompute). v1 deterministic = high-η
  bidirectional Dijkstra; stochastic η-growth parked.
- I1: bridges are surfacing-only — two axes (chain, conductance) NEVER fused; no weight/promotion writes.
- Atlas MUST be registered (`register_atlas(SpineAtlas(spine))`) before any T-meet.

**Next when built:** item 7 (type-check/node→scope/atlas refusal) → 8 (bidirectional search + refusal) →
9 (two-axis report + entry). Estimate opus/200k.
