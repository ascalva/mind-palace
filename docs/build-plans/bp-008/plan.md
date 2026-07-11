---
type: build-plan
id: bp-008
status: in-progress
design_ref:
  - docs/design-notes/type-system-as-core-audit.md
contract: builder
write_scope:
  - ".gitlab-ci.yml"
  - "ops/type_gate.py"
  - "tests/**"
  - "pyproject.toml"
  - "docs/findings/**"
  - "docs/build-plans/bp-008/**"
session_budget: 1
depends_on: [bp-006, bp-007]
parallelizable_with: []
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/audits/mypy-baseline-2026-07-11.md
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — B-2: wire the type gate (CI job + membership invariant + bare-ignore scan)

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated from ratified `type-system-as-core-audit.md`, B-2. **PD-1's re-entry condition
fired 2026-07-11**: CI now runs pytest/ruff (the `ratchet` job) — per the note's own PD-1
re-entry clause ("V4 shows CI … runs pytest"), CI is the live gate location. This plan
records that PD re-entry and proposes CI as the gate; the owner ratifies the location by
blessing this plan. A config nothing invokes enforces nothing (§2.6).

## 1. Objective

A red type check, a Tier-2 membership violation, or a bare `# type: ignore` blocks the
pipeline — enforced by a `type-gate` CI job plus a mechanical membership scan.

## 2. Context manifest

1. `docs/design-notes/type-system-as-core-audit.md` — §2.6, B-2 falsifiers (verbatim below).
2. `.gitlab-ci.yml` — the `ratchet` job is the pattern (image, cache, `rules:changes`).
3. `ops/import_lint.py` — the AST import-walk this plan's membership scan extends.
4. `pyproject.toml` — `[tool.mypy]` `files` list = the Tier-2 config being asserted.

## 3. Investigation & grounding

- **Q1 — is CI viable as the gate?** Yes, established 2026-07-11: `ratchet` job green at
  54–77s on shared runners; free-tier budget analysis in the commit record (`2d379af`,
  `e6d6…` series). mypy adds one cached step (~20–40s measured locally at 312 files).
- **Q2 — how is Tier-2 membership decidable?** By AST import scan (the note: "decidable
  from the AST import graph"); `ops/import_lint.py` already walks imports for core — the
  scan generalizes: _top-level package imports `core` ⇒ package ∈ `[tool.mypy].files`_.
- **Q3 — where does `mp-finish` stand?** No `mp-finish` exists in the repo (checked:
  no such script/verb) — PD-1's recorded default was aspirational; CI is the concrete
  option that exists. The code settles this in CI's favor.

**Additional risks or questions surfaced during reading:** mypy in CI must use the same
lockfile-pinned version as local (it does — dev extra), or verdicts drift.

## 4. Reconciliation

- `pyproject.toml` `[tool.mypy]` comment "Report-only until B-2 wires the gate" →
  **banner: correction** — becomes "Gated in CI (`type-gate` job) since bp-008."
- `type-system-as-core-audit.md` PD-1 row — **cross-ref: extension**: the PD re-entry
  fired; the note is NOT edited (denylisted surface) — this plan + its finding are the
  record; fold into the note at its next owner-touched revision.

## 5. Write scope

Prose mirror: the CI file, a new `ops/type_gate.py` (membership + bare-ignore scans),
its tests, pyproject comment, findings, own dir. **Out of scope:** annotation changes
anywhere (bp-006/007's), design notes, hooks.

## 6. Interfaces pinned inline

B-2 falsifiers (note §3.3, verbatim — all three must hold):
_"(i) an injected type error in a scratch commit blocks; (ii) a scratch module importing
`core` but absent from Tier-2 config blocks; (iii) a bare `# type: ignore` with no error
code blocks."_

Ratchet job shape to mirror (`.gitlab-ci.yml`): `image: ghcr.io/astral-sh/uv:python3.12-
bookworm-slim`, uv cache keyed on `uv.lock`, `rules:changes` on code paths,
`interruptible: true`.

## 7. Items

### Item 8 — `ops/type_gate.py`

- **Objective:** two scans, importable and CLI-runnable: `membership()` (imports-core ⇒
  in-config) and `bare_ignores()` (regex `type:\s*ignore(?!\[)`), each returning
  violations.
- **Files:** `ops/type_gate.py`, `tests/unit/test_type_gate.py`.
- **Acceptance test:** unit tests prove both scans on planted fixtures; ratchet green.
- **Falsifier:** falsifiers (ii)/(iii) — a planted violation the scan misses.
- **Invariant(s):** scan is read-only; no network.
- **Touches stored data?** no **Parallelizable?** no **Depends on:** bp-006, bp-007

### Item 9 — the `type-gate` CI job

- **Objective:** CI job running `mypy` + both scans; red blocks the pipeline.
- **Files:** `.gitlab-ci.yml`.
- **Acceptance test:** falsifier (i) executed live — a scratch branch... **correction:**
  scratch commits must not land on main (ingestion branch); prove via a temporary
  `allow_failure: false` dry run on a throwaway branch pipeline (branch pipelines run the
  job with `rules` adjusted for the test, then reverted) — the journal records the three
  falsifier runs with pipeline ids.
- **Falsifier:** all three of §6, live.
- **Invariant(s):** free-tier budget — job shares the uv cache; docs-only pushes skip.
- **Touches stored data?** no **Parallelizable?** no **Depends on:** Item 8

## 8. Math carried explicitly

N/A — no mathematical object implemented.

## 9. Non-goals

Changing tier flags (bp-006/007 own them); Stop-gate hook enforcement (rejected-with-
record in the note, PD-1); pyright (PD-3).

## 10. Stop-and-raise conditions

The three falsifiers cannot all be demonstrated (gate is theater — file spec-defect
against this plan); CI runtime makes per-push cost material (PD-1's other re-entry —
owner question, park).

## 11. Parked decisions

| Decision               | Default recorded | Rejected alternatives (why)                                         | Re-entry condition                                            |
| ---------------------- | ---------------- | ------------------------------------------------------------------- | ------------------------------------------------------------- |
| gate also in Stop-hook | CI only          | per-session cost, duplicate signal (note PD-1 rejected-with-record) | a type break lands between pushes and bites a builder session |

## 12. Dependency & ordering summary

bp-006 → bp-007 → this. Items 8 → 9. Nothing parallel (single small session).
