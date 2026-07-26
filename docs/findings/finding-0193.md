---
type: finding
id: finding-0193
status: routed
created: 2026-07-25
updated: 2026-07-26
links:
  - docs/audits/ops-wave-2026-07-25.md
  - docs/templates/finding.md
  - CLAUDE.md
  - .claude/skills/finding/SKILL.md
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: routed → owner (oq-0047); the corpus has settled on the UNION of two disjoint vocabularies, and nothing validates it
---

# The ftype vocabulary in the finding template and CLAUDE.md are disjoint sets

> **Triage 2026-07-26 (session-52) — batched to `oq-0047`.** Exactly as filed, and the corpus has
> settled on the **union** rather than either set. `docs/templates/finding.md:9` declares
> `blocker | spec-defect | question | discovery`; `CLAUDE.md:51-54` — the routing rule binding every
> session — routes on `design | math | direction | codebase | spec-fidelity`; the `finding` skill
> prints both side-by-side (`SKILL.md:12-23` vs `:25-32`) without reconciling them, **disjoint within
> one file**.
> **Census over all 182 findings:** `discovery` 54 · `spec-defect` 54 · `spec-fidelity` 23 ·
> `direction` 24 · `design` 13 · `math` 5 · `codebase` 5 · `question` 3 · `blocker` 1 — a live 9-value
> union. `grep ftype .claude/hooks/ scripts/` → **zero**: no mechanical check exists, so "correctly
> typed and routed" is undecidable.
> **Downstream blockage is real and cited:** `dn-autopilot-and-delegated-blessing:97` (§2.4 blocked)
> and two Parked rows (`:535,:538`) whose re-entry is literally *"finding-0193 resolved by owner
> ruling"*. **Time `oq-0047` with the autopilot superseding note.**

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
