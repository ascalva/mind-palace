---
type: finding
id: finding-0018
status: open
created: 2026-07-06
updated: 2026-07-06
links:
  - docs/audits/corpus-state-audit-2026-07.md
  - docs/audits/corpus-state-audit-2026-07-verification.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# finding-0018 — The corpus audit ran with a directory-scope defect and at least one rigor error; the audit procedure must derive its scope empirically

## What
The corpus-state audit (`docs/audits/corpus-state-audit-2026-07.md`) was produced with
two procedural defects, both surfaced by the 2026-07-06 verification pass:

1. **Directory-scope defect.** The audit checked implementation reality primarily
   against `core/`, `scripts/`, `tests/` and **never walked `cloud/`** (and covered
   `agents/` only partially). Empirically the repo's source dirs are `agents/`, `bin/`,
   `cloud/`, `config/`, `core/`, `edge/`, `eval/`, `ops/`, `scheduler/`, `scripts/`,
   `tests/`, `.claude/` + root config — the audit's effective search set was a subset.
   Consequently a whole built + AWS-deployed subsystem (the research airlock; see
   finding-0019) was invisible to it, and EXISTS-as-IaC evidence for three notes
   (observed-iot, secrets-management-evolution, vault-runtime-auth) was missed.
2. **Rigor error.** At least one positive verdict — `the-edge-model.md` marked
   **BUILT & WIRED** — rested on a mis-traced call chain: it claimed `build_complex`
   runs live via the dream cron, but `build_complex`'s only caller
   (`core/dreaming/interpreters.py:249`) is reachable only from the flag-off
   `dream_v2`/`run_panel` path (`require_rnd_enabled`), never the live `dreamer.dream()`
   (`scheduler/cron.py:33`). The verification downgrades it to PRESENT-BUT-NOT-WIRED.
   This was a cross-cluster contradiction (one auditor said "wired", two said "flag-off")
   that the synthesis failed to reconcile.

Notably, the scope defect produced **zero spurious findings and zero wrong negatives**
(all 23 not-built/partial/PNW verdicts were re-confirmed across every dir) — it damaged
*completeness*, not *correctness*. The one status error was independent (rigor).

## Why it matters
An audit that silently bounds its own search scope reads as comprehensive when it is
not; a "wired" verdict resting on a broken call chain enters the completed-format
proposal (§4) and could ratify a note whose subsystem never runs on the live path.

## Re-entry condition
The audit procedure must, going forward: (a) **derive its source-dir set empirically** —
enumerate every top-level entry and classify each SOURCE/NOISE, never accept a fixed
directory allowlist (including a prompt's); and (b) **reconcile cross-cluster
contradictions** (especially flag-off vs live) before assigning a WIRED verdict. The
verification report (`corpus-state-audit-2026-07-verification.md`) applies both and
should be read alongside the original.

## Routing
`discovery` (process/direction) → orchestrator. A correction to audit methodology, not
a system code defect.
