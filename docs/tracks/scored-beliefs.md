---
type: track
slug: scored-beliefs
title: Scored beliefs — the belief ledger + earned entitlement
status: active
warrant: null
audit_refs: []
dod:
  - dn-scored-beliefs-and-earned-entitlement ratified (owner)
  - the belief ledger built and wired (record → resolution sweep → Σ-attribution), flag-off acceptable, ON switch existing
  - first resolution cycle scored against a later certified cut, with the two-failure split demonstrated
backlog_deskcheck: null
links:
  - docs/design-notes/scored-beliefs-and-earned-entitlement.md
  - docs/findings/finding-0217.md
  - docs/brainstorms/prediction-market-sensor-fusion.md
  - docs/brainstorms/dreamer-and-graph-direction.md
---
# Track — Scored beliefs (the ledger + earned entitlement)

The identity card for the scored-beliefs track, minted with its founding design note
(2026-07-26, at `draft` — the owner renames or rejects this coordinate at ratification).
**Scope:** the ledger of beliefs scored against later resolution — the Σ-carrying belief
record, the resolution sweep over certified cuts, the two-failure attribution
(wrong-given-Σ vs Σ-too-narrow), and the per-domain entitlement dossiers that later
gates may read. **Not in scope:** any market surface, money, `edge/`, effector wiring,
or diachronic execution (parked upstream).

**Standing dependency:** the predictors are the dreamers (dn-synchronic-diachronic-dreamer),
which are built-not-wired; the sync-diac-dreamers track's owed wire-or-accept-dormant
decision (finding-0141) is this track's precondition — a predictor that never runs cannot
be scored. This track never makes that decision; it makes the ledger ready to receive it.
