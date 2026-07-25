---
type: journal
plan: bp-108
started: null
updated: 2026-07-25
---

# Journal — bp-108 (the supervisor role becomes exclusive)

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Not started.**

## Pre-build notes for whoever picks this up

- **Item 1 (V8) gates everything.** If `uv run` holds the lock from a wrapper process rather than
  the python process, the mechanism is mis-tiered and §10 says STOP. Do not build Items 2-5 first
  and measure afterwards.
- ⚑ **The interim fix is SMALLER than the note implies.** `Supervisor.run` already accepts
  `max_ticks` (`scheduler/supervisor.py:99`); only the call site (`launcher.py:676`) is wrong.
  If you find yourself editing `scheduler/`, you are fixing it in the wrong place.
- ⚑ **The sleep is the other half of Item 4.** `launcher.py:694-695` sleeps unconditionally per
  iteration. Bound the drain without making the sleep conditional and 1,766 no-ops take ~29 min.
- **Do NOT delete bp-105's identity gate.** It is demoted in documentation, kept in code: the lock
  can only say no, the gate can say why (§3 Q4).
- **`scripts/watch.py` is NOT deleted.** V7 is unanswered (§3 Q6); bring it under the lock instead.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.
