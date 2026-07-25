---
type: journal
plan: bp-109
started: null
updated: 2026-07-25
---

# Journal — bp-109 (the queue's ledger stops being trusted)

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Not started.**

## Pre-build notes for whoever picks this up

- ⚑ **V6 needed no measurement — it is confirmed by reading.** `checkpoint()` leaves the token on
  a QUEUED row (`queue.py:400-402`) and the coalesce lookup never mentions the `checkpoint` column
  (`queue.py:262-264`). Item 4 is a one-clause fix and it BLOCKS bp-110.
- ⚑ **NULL means "no deadline", and every pre-existing row gets NULL.** A reader that treats NULL
  as expired mass-orphans 300k+ rows of history at migration time. This is the single most
  dangerous mistake available in this plan (§6).
- **Do NOT add the partial UNIQUE index.** `queue.py:122-126` explains why: the live file holds
  1,766 duplicate queued rows and `CREATE UNIQUE INDEX` would make the daemon unstartable.
- **Item 3 and Item 5 both require a PLANTED MUTATION to prove they work.** finding-0187's standing
  proof is that deleting bp-105's sweep call left 85/85 green. If your mutation does not redden the
  suite, you have shipped a guard whose absence is invisible — worse than shipping nothing.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.
