---
type: finding
id: finding-0193
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/audits/ops-wave-2026-07-25.md
  - docs/templates/finding.md
  - CLAUDE.md
  - .claude/skills/finding/SKILL.md
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The ftype vocabulary in the finding template and CLAUDE.md are disjoint sets

## What
`docs/templates/finding.md` declares `ftype: blocker | spec-defect | question | discovery`.
`CLAUDE.md` routes on `design | math | direction | codebase | spec-fidelity`. The two sets
are disjoint. `spec-defect` — the most-used value in this wave — is unrouteable under the
CLAUDE.md rule, and builders have been disambiguating in prose.

Hit independently by three of six auditors while trying to score "findings correctly typed
and routed".

## Why it matters
"Correctly typed and routed" is not decidable until the vocabularies are reconciled, so
the routing rule in CLAUDE.md — one of the few rules that binds every session — is
currently unenforceable as written. It also blocks a mechanical check: with one authoritative
set, a hook could validate `ftype`/`route` consistency at file-write time.

Needs an owner ruling on which set is authoritative, then a sweep of existing findings.
