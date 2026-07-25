---
type: journal
plan: bp-113
started: null
updated: 2026-07-25
---

# Journal — bp-113 (the code lanes split)

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Not started.**

## Pre-build notes for whoever picks this up

- ⚑ **`code_sync` and `code_backfill` are one plan because they SHARE `_embed_and_land`**
  (`core/ingest/code_corpus.py:267-278`). That is the graduation-time decision; do not re-split.
- ⚑ **The batch must carry the SUPERSEDE INTENT, not just rows.** `sync()` calls
  `store.supersede_source` at `:293` and `:298` — writes inside the compute loop. Both must move
  into the landing step or a path is left with no `current=true` version (§6).
- ⚑ **Item 4's falsifier is the costliest thing here: a resumed backfill that SKIPS versions.**
  Idempotence makes re-embedding merely wasteful; skipping is silent data loss in the one store
  that cannot be rebuilt from git. Assert version-set equality, not row counts.
- **§3 Q4 is unanswered by `code_corpus.py` alone**: whether `code_backfill`'s diff capture is
  interleaved. Read `scheduler/code_sync.py` before Item 4.
- **Never run a full live backfill as an acceptance run.** Scratch store, row diff, bounded slice.
- **Read bp-110's read-only facade first.** A missing or leaking facade is a spec-defect against
  bp-110, not something to work around here.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.
