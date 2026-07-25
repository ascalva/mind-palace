---
type: journal
plan: bp-111
started: null
updated: 2026-07-25
---

# Journal — bp-111 (the dead-man inversion)

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Not started.**

## Pre-build notes for whoever picks this up

- ⚑ **This plan genuinely needs bp-110, not just for file contention** (§3 Q2): a lease renewed
  from a loop a handler can block is a cry-wolf generator. bp-108's `max_ticks` is not enough — one
  wedged job still owns the thread for hours.
- ⚑ **`_idle` must renew too.** A recovery run IS a live supervisor (`launcher.py:634-646`). If
  only `_serve` renews, a recovery run reads DOWN and the operator is told to start a daemon that
  bp-105's gate will then refuse — a dead-end loop.
- ⚑ **Old ledgers must not read DOWN forever.** §4 of the note requires the fallback to
  `_supervisor_alive`; the render must SAY which source it used. A fallback presented as a lease is
  a weaker signal wearing a stronger one's label.
- **If V9 picks the `runs.sqlite` clock, that is a §10 RAISE, not a scope widening.**
  `ops/lifecycle/runs.py` is deliberately outside `write_scope`.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.
