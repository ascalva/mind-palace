---
type: finding
id: finding-0010
status: open
created: 2026-07-06
updated: 2026-07-06
links:
  - docs/design-notes/verdict-authority.md
  - docs/design-notes/vault-runtime-auth.md
  - docs/design-notes/skills-and-scope.md
  - docs/design-notes/attestation-layer.md
  - docs/design-notes/the-edge-model.md
  - docs/design-notes/the-sacred-boundary.md
  - docs/audits/corpus-state-audit-2026-07.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# finding-0010 — A cohort of design notes carry stale self-status that understates built + wired reality

## What
Multiple design notes carry a self-declared status ("design only", "not
implemented", or "DRAFT — pending codebase reconciliation and owner ratification")
that badly understates code which is in fact built, tested, and in several cases
wired into the live path. Confirmed by the 2026-07 corpus audit:

- `verdict-authority.md` ("DRAFT") — BUILT & WIRED: `core/verdict/payload.py`,
  `core/stores/verdicts.py`, `core/verdict/apply.py`, live via `scripts/verdict.py`
  and the Ambassador verdict-receiver (`agents/ambassador/__init__.py:88`).
- `vault-runtime-auth.md` ("design only") — built + tested (`config/secrets_backend.py`,
  `core/factory/factory.py:61-80`), though undriven (see finding-0016).
- `skills-and-scope.md` ("design only, not implemented") — capability half built +
  tested (`core/factory/roles.py`, `core/factory/tools.py`).
- `attestation-layer.md` ("design only") — records layer built + wired
  (`core/attestation/*`, assembled `ops/lifecycle/launcher.py:121-127`).
- `the-edge-model.md`, `the-sacred-boundary.md` ("DRAFT — pending reconciliation") —
  their reconciliation build plans were executed and owner-approved.

This is the same drift that `wasm-sandbox-runtime.md` already corrected for itself in
its 2026-07-03 header ("the original 'design only' header was stale").

## Why it matters
A reader — human or agent — triaging the corpus by self-status will mis-prioritize:
treating wired subsystems as unstarted, or letting a DRAFT label block work that is
already done. `/graduate` refuses any note that is not `ratified`, so notes whose
work is complete cannot advance through the artifact chain until their status is
corrected by hand.

## Re-entry condition
Owner reviews §4 of `docs/audits/corpus-state-audit-2026-07.md` (proposed
completed-format front-matter for the BUILT & WIRED cohort) and applies
`ratified`/`updated` status by hand at the blessing gate (owner-only, §10). No
in-session status flip is performed.

## Routing
`direction` → orchestrator. A status-hygiene sweep; the constructive fix is the
Step-4 front-matter proposals in the audit. Not a code defect.
