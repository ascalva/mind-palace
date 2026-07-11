---
type: build-plan
id: bp-007
status: in-progress
design_ref:
  - docs/design-notes/type-system-as-core-audit.md
contract: builder
write_scope:
  - "tests/**"
  - "ops/**"
  - "agents/**"
  - "scheduler/**"
  - "scripts/**"
  - "eval/**"
  - "pyproject.toml"
  - "docs/findings/**"
  - "docs/build-plans/bp-007/**"
session_budget: 1
depends_on: [bp-006]
parallelizable_with: [bp-009]
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/audits/mypy-baseline-2026-07-11.md
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Tier-2 floor green: the callers of core stop laundering Any

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated from ratified `type-system-as-core-audit.md`. Tier-2's load-bearing requirement
(§2.5): _arguments flowing into core calls are not `Any`_. Runs after bp-006 (core
annotations settle the target signatures). Readiness blessing is the owner's, by hand.

## 1. Objective

Every measured Tier-2 package (tests, ops, scheduler, agents, scripts, eval — V1a
2026-07-11) is green under a floor decided from B-1 evidence, with the floor recorded
in `pyproject.toml`.

## 2. Context manifest

1. `docs/design-notes/type-system-as-core-audit.md` — §2.5 tiers; Open questions (floor).
2. `docs/build-plans/bp-006/journal.md` — what core's signatures became.
3. `docs/audits/mypy-baseline-2026-07-11.md` — Tier-2 baseline: tests 223, ops 27,
   agents 9, scheduler 8, scripts ~6.
4. `pyproject.toml` — the global `[tool.mypy]` block IS the Tier-2 floor today
   (`check_untyped_defs`).

## 3. Investigation & grounding

- **Q1 — Tier-2 membership (mechanical invariant).** Measured 2026-07-11: tests 103
  modules import core, scripts 14, scheduler 6, ops 5, agents 2, eval 1; **edge 0,
  cloud 0** (Tier-3 by measurement, not judgment).
- **Q2 — current floor.** Global `check_untyped_defs = true` in `pyproject.toml`
  `[tool.mypy]`; the note's candidate floor adds `disallow_any_generics` — _decide from
  B-1 evidence, not a priori_ (note, Open questions). The builder measures the delta of
  adding it and records the decision.
- **Q3 — will bp-006 shift these counts?** Yes — core signature changes re-type call
  sites. The baseline numbers are indicative, not contractual; re-measure at session start.

**Additional risks or questions surfaced during reading:** tests' 223 errors may hide
real T1s (a test asserting the wrong type that "passes" because untyped) — triage
discipline applies here too, not just annotation grind.

## 4. Reconciliation

- `pyproject.toml` global-floor comment ("GLOBAL settings are the Tier-2 interim floor")
  → **cross-ref: extension** — replace "interim" with the decided floor + the decision
  record when Q2 resolves.

## 5. Write scope

Prose mirror: the six Tier-2 packages + pyproject + findings + own dir.
**Out of scope:** `core/**` (bp-006's, already sealed by then), `.gitlab-ci.yml`
(bp-008), design notes, `edge/`/`cloud/` (Tier-3 recorded default — not debt).

## 6. Interfaces pinned inline

Tier-2 requirement (§2.5 verbatim): _"the load-bearing requirement is that arguments
flowing into core calls are not `Any`."_ Ratchet marker expression (the gate this must
keep green): `-m 'not live and not podman and not needs_vault and not needs_restic'`.
T3 ignore discipline as in bp-006 §6.

## 7. Items

### Item 5 — Re-measure and decide the floor

- **Objective:** post-bp-006 Tier-2 error counts by package; floor decision
  (`check_untyped_defs` alone vs + `disallow_any_generics`) made from the measured delta.
- **Files:** journal (table + decision), `pyproject.toml` (floor recorded).
- **Acceptance test:** journal table present; pyproject comment names the decision + date.
- **Falsifier:** the stricter floor adds only T3 friction (zero T1/T2 in the delta) —
  record and stay at the base floor.
- **Invariant(s):** none (measurement).
- **Touches stored data?** no **Parallelizable?** no **Depends on:** bp-006

### Item 6 — Non-test Tier-2 green (ops, scheduler, agents, scripts, eval)

- **Objective:** ~50 errors cleared under the decided floor; T1s filed as findings.
- **Files:** those packages, findings.
- **Acceptance test:** `uv run mypy` → 0 errors outside `tests/`; ratchet green.
- **Falsifier:** a fix that silences the checker by widening a type to `Any` — the exact
  anti-pattern; caught by re-running with `disallow_any_explicit` on the touched file.
- **Invariant(s):** scheduler/ops behavior unchanged (annotation-only unless a T1 finding
  warrants more).
- **Touches stored data?** no **Parallelizable?** with Item 7 **Depends on:** Item 5

### Item 7 — Tests green

- **Objective:** the 223 test-package errors cleared; test-hidden T1s filed.
- **Files:** `tests/**`, findings.
- **Acceptance test:** `uv run mypy` → 0 errors total; full ratchet green.
- **Falsifier:** blanket per-file ignores in tests (the checked region silently shrinks) —
  zero new `ignore_errors` overrides allowed.
- **Invariant(s):** test semantics unchanged — assertions may gain types, never lose checks.
- **Touches stored data?** no **Parallelizable?** with Item 6 **Depends on:** Item 5

## 8. Math carried explicitly

N/A — no mathematical object implemented.

## 9. Non-goals

Core changes; gate wiring; raising Tier-2 to full strict (ceiling deferred); typing
`edge/`/`cloud/`.

## 10. Stop-and-raise conditions

A Tier-2 error whose fix requires changing a core signature (bp-006's sealed surface —
file a finding, park); floor decision ambiguous after measurement (owner question, park
the criterion, continue the other package).

## 11. Parked decisions

| Decision                     | Default recorded | Rejected alternatives (why)                                                        | Re-entry condition                                                         |
| ---------------------------- | ---------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Tier-2 ceiling (full strict) | floor only       | full strict now (223-error test surface makes cost dominate before value measured) | after one month of gate history, or a laundering incident the floor missed |

## 12. Dependency & ordering summary

bp-006 → Item 5 → (Item 6 ∥ Item 7). Parallelizable with bp-009 (disjoint scope:
bp-009 owns `core/provenance.py`). Gates bp-008.
