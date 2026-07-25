---
type: journal
plan: bp-110
started: null
updated: 2026-07-25
---

# Journal — bp-110 (THE INTEGRATOR: the worker protocol and the dispatch seam)

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Not started.**

## Pre-build notes for whoever picks this up

⚑ **This is the biggest and most consequential plan of the supervision wave. Read it whole before
starting.** It owns the seam and no lane; bp-113 and bp-114 consume the protocol it defines.

- ⚑ **§3 Q3 is a GAP IN THE RATIFIED NOTE, resolved here, not re-litigated by you.** The note says
  the worker is handed "never a `VectorStore`" — true for WRITES, silent on READS. Three compute
  halves need store reads (`code_corpus.py:283,321`, and the proof lane's retrieval). §6 pins a
  read-only facade; §10 makes a LEAKING facade a STOP. If the writable handle is recoverable by
  `getattr`, pickling, or a closure, the tier-2 claim in a ratified note becomes false — which is
  worse than shipping nothing, because the note would be quoted as a guarantee.
- ⚑ **Subprocess, not `multiprocessing`, and the reason is the RATCHET** (§3 Q4). Under
  `multiprocessing` the worker's import graph is the parent's, so the tier-4 backing asserts
  nothing. Item 5 is only buildable with a separate `python -m scheduler.worker` entrypoint.
- ⚑ **V4: a spawned worker starts UNSEALED.** macOS uses spawn; `core/sealing.py` is a per-process
  monkeypatch. Item 2's falsifier is the most serious failure available here and it is SILENT.
- **`ambassador_task` is the proof lane** — it already has the target shape and the supervisor
  already lands its result (`supervisor.py:94-95`). No ingest handler changes in this plan.
- **Item 1 first.** If V5 shows the loop survives a pure-CPU thread, a RATIFIED decision rests on
  a false premise: §10 STOP and raise. Do not build subprocess anyway while knowing better.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.
