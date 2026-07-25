---
type: journal
plan: bp-112
started: null
updated: 2026-07-25
---

# Journal — bp-112 (the teeth: budgets enforced and a kill that is loud)

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Not started.**

## Pre-build notes for whoever picks this up

- ⚑ **The escalation targets the WORKER, never the supervisor.** §2.4 of the note: killing the
  supervisor mid-landing is how you CREATE the partial write the oq-0035 ruling dissolves. §10
  makes an aimable-at-the-supervisor kill path a STOP; assert it structurally.
- ⚑ **Deadlines are PER-BATCH, never per-job-elapsed** (§3 Q2). A per-job deadline kills a healthy
  14-hour backfill at hour N, on schedule, every time.
- ⚑ **0 is the default and means "no budget".** A non-zero default would kill jobs on upgrade.
- **A kill with no durable record is the silent state-change the mandate forbids.** §3 Q5: whether
  `ops/ledger.py` carries a suitable shape is NOT settled by reading — read it before Item 3, and
  if it does not, STOP and file. Do not create a second incident store; do not downgrade to print.
- **Test `down` with a DEEP queue.** A one-job test passes today (§3 Q7).
- This plan closes **OPS-4**. At seal, enumerate what is still owed (bp-113/bp-114) — the
  completion-claims-honesty rule.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.
