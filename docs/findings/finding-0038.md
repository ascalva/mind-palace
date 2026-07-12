---
type: finding
id: finding-0038
status: routed
ftype: direction
origin_plan: bp-014
route: orchestrator
created: 2026-07-12
updated: 2026-07-12
links:
  - .claude/skills/delegate/SKILL.md          # "Ratchet green locally before merge" — the rule to sharpen
  - .github/workflows/ci.yml                   # the type-gate job (argless-mypy exact-69 + ops.type_gate)
  - docs/build-plans/bp-014/plan.md            # the episode
resolution: null
---

# finding-0038 — "Ratchet green locally" must mean the FULL attestable-green gate, not just ruff + pytest

## What

The bp-014 delegated builder reported "ruff clean; `uv run pytest` green" and declared the work
ready-for-merge. The orchestrator's merge-time re-verification ran the same two (ruff + full
pytest, 824 passed) and merged. **CI then went red on `type-gate`** (run 29184913514): the
builder's new `tests/integration/test_worktree_enforcement.py` introduced one mypy error
(`Missing type arguments for generic type "CompletedProcess"` — needed `CompletedProcess[str]`),
pushing the argless `uv run mypy` count from the pinned **69** (finding-0029 `tests/` baseline) to
70. Neither `ruff check` nor `pytest` sees this — only the type-gate's argless-mypy assertion does.
Fixed forward in one line (`d23e0d6`); the witness worked as designed.

## Why it matters

"Attestable green" = **five** jobs (bp-015 seal): `ratchet` · `type-gate` · `vault-axis` ·
`gitleaks` · `semgrep`(report-only). A builder (and the supervising merge check) that runs only
`ruff` + `pytest` is validating **one** of them (`ratchet`) and silently skipping `type-gate`'s
two extra teeth: (1) the argless `uv run mypy` pinned at exactly 69 over `[tool.mypy].files`
(which includes `tests/`), and (2) `uv run python -m ops.type_gate`. Any new `tests/**` file — the
normal output of a build with a regression harness — can shift the count and red the pipeline.
**This will recur on the bp-016 ∥ bp-017 lane** (both touch typed source and/or workflows), so
close it before that lane opens.

## Recommended direction (route: orchestrator)

1. **Sharpen the delegate skill's "ratchet green locally before merge"** into a concrete
   pre-merge command set the builder AND the orchestrator run — minimally:
   `uv run ruff check . && uv run mypy core agents eval ops scheduler scripts && uv run mypy &&
   uv run python -m ops.type_gate && uv run pytest -q` — and assert the argless-mypy tail equals
   the recorded baseline (69 today). The argless `uv run mypy` is the load-bearing, easily-missed
   one.
2. **Put the exact expected mypy baseline where a builder sees it** (the delegate skill or a
   `scripts/` gate wrapper), so "did I hold 69?" is a checkable fact, not tribal knowledge.
3. Consider a single `scripts/attestable_green.sh` that runs the local mirror of all five CI jobs
   (as far as they can run without live services) — one command a delegated builder invokes to
   self-certify, closing the ruff+pytest-only gap structurally.

## Re-entry

Promote at /triage into the delegate skill (SKILL.md). **Immediate carry (before it promotes):**
the bp-016 ∥ bp-017 delegation prompts must instruct each builder to run the full gate above —
especially the argless `uv run mypy` baseline — before declaring green. Trigger that reopens: any
future CI red on a gate the builder's local check didn't cover.
