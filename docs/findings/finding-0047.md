---
type: finding
id: finding-0047
status: resolved         # open → routed → resolved | promoted
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/build-plans/bp-018/plan.md
  - tests/unit/test_code_projection.py
ftype: spec-defect
origin_plan: bp-018
route: builder           # spec-fidelity: settleable against code + plan, no design question
resolution: >
  is_projected alone deviates from the §6(c) pin — `interpreter: str | None = None`,
  None = "projected under ANY interpreter" — so the out-of-scope caller stays valid;
  add_batch/mark_projected keep interpreter required as pinned. The reopened
  forgotten-arg hazard is pinned shut by Item 4's bump→re-projects acceptance test.
---

# bp-018 Q3 caller inventory missed tests/unit/test_code_projection.py; write_scope omits it

## What

The plan's Q3 grounding ("who calls the store's write/bookkeeping API?") records
`ops/code_sensor.py` "plus the two test files", and `write_scope` grants exactly
`tests/unit/test_code_observations.py` + `tests/unit/test_code_sensor.py`. The builder's
at-HEAD re-grep (a §3 obligation) found a third caller: **`tests/unit/
test_code_projection.py:111`** — `obs.is_projected(sha)`, one-arg. The file is a test,
so this is NOT the §10 stop condition (an unmapped non-test caller); it is a scope
grant one file too narrow for the pinned signature change: `is_projected(commit_sha,
interpreter)` with `interpreter` required would break a file the builder cannot edit,
and the gate must be green.

## Why it matters

Unresolved, the builder must choose between a red gate (pinned signature, unfixable
out-of-scope caller) and routing around the write scope (forbidden absolutely). Either
corrupts the contract.

## Resolution (builder, spec-fidelity — annotated here + journal + code comment)

Minimal, semantics-honest deviation from the §6(c) pin, on ONE method only:

- `is_projected(self, commit_sha: str, interpreter: str | None = None)` — `None` means
  "projected under ANY interpreter". That is *exactly* the assertion the out-of-scope
  call site makes ("and the batch hash was recorded"), so the file stays green,
  unedited, with honest semantics rather than a compatibility shim.
- `add_batch` (keyword-only, required `interpreter`) and `mark_projected` (required
  third argument) keep the pin verbatim — their only callers are in scope.
- The hazard the default reopens — a sensor-side caller forgetting the argument and
  reproducing the silent no-op V2 exists to fix — is test-guarded: Item 4's acceptance
  test (bump the version, `backfill_observations()` re-projects, old rows archived)
  reds if any link in the sensor path drops the version key.

## Re-entry condition

None parked — resolved in-plan. If the orchestrator prefers the pin restored verbatim
at merge: add `tests/unit/test_code_projection.py` to a scope grant, change line 111 to
pass an interpreter (or assert via the sensor), and drop `is_projected`'s default; the
Item 4 test keeps guarding either way.

## Routing

`spec-fidelity` → builder resolved, annotated, continued (constitution §5 routing rule).
