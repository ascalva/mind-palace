---
type: finding
id: finding-0160
status: resolved         # open → routed → resolved | promoted
created: 2026-07-22
updated: 2026-07-22
links:
  - tests/unit/test_provenance_tags.py
  - docs/build-plans/bp-098/plan.md      # surfaced by bp-098's green-gate run (NOT its cause)
ftype: spec-defect       # a test-harness robustness defect (NOT a type-guard regression — see resolution)
origin_plan: bp-098
route: orchestrator
resolution: fixed in `2e851ff`-successor — `_run_mypy` now passes `--no-color-output`; root cause was ANSI-colorized mypy output under FORCE_COLOR, NOT a mypy 2.2.0 provenance-guard regression. The MIRROR guard is intact.
---

# The provenance-tag type-error tests are fragile to FORCE_COLOR (ANSI breaks the mypy-output parse)

## What

Three tests in `tests/unit/test_provenance_tags.py`
(`test_promotion_without_capability_is_a_type_error`, `test_subclass_laundering_is_a_type_error`,
`test_mirror_bypass_is_a_type_error`) failed **when the suite runs inside this session's
environment**, each reporting "0 errors" where it expected its `# E:`-marked set.

**Root cause (diagnosed 2026-07-22, session-43):** NOT a type-system regression. The harness
`_run_mypy` shells out to `mypy` and parses stdout with the substring filter `": error:" in line`.
The session environment sets **`FORCE_COLOR=3`** (the Claude Code harness), and **mypy honors
`FORCE_COLOR` even when its stdout is a pipe** — so every diagnostic comes out ANSI-colorized:
`provenance_fixture.py:14: ␛[1m␛[31merror:␛[0m …`. The escape codes sit between the `: ` and
`error:`, so the literal `": error:"` substring never matches → `reported == []` → the exact-count
assertion fails with "0 errors", even though mypy printed the correct errors (visible in the
assertion's `{proc.stdout}` dump).

**Proven, both directions:**
- `mypy … <fixture> | grep -c ': error:'` → **0** with color forced (this env), **2** with
  `--no-color-output`.
- Running mypy directly on the mirror-bypass snippet emits BOTH expected `arg-type` errors (lines
  14, 15). **The `Authored[T]` / `Derived[T]` MIRROR guard is fully intact** — a `Derived[Row]` or
  raw `dict` row still cannot be passed where `Sequence[Authored[Row]]` is demanded. No firewall
  weakening; the scary "mirror-bypass no longer flagged" reading was a parsing artifact.

**Correction to this finding's original claim:** it first read as "the deploy gate is RED on main
under mypy 2.2.0, possible MIRROR-guard regression." That was overstated. The redness is
**environment-specific to FORCE_COLOR** (this agent's session). A launchd `palace deploy` or GitHub
CI run has no `FORCE_COLOR`, so mypy detects the non-TTY pipe, emits plain text, and the tests pass
— the real deploy gate was never red for this reason. The full-suite run that flagged it (bp-098's
gate) executed inside this session, which is why it surfaced here.

## Why it matters

Low functional severity (no guard regression, real gate unaffected), but a real **test-robustness**
defect: any color-forcing environment (FORCE_COLOR / CLICOLOR_FORCE / a future CI that sets it)
silently turns these type-level assertions into false failures — and, worse, could mask a genuine
regression the same way (a real guard break would also parse as "0 errors" and be indistinguishable
from this artifact). A harness that asserts on tool output must neutralize ambient formatting.

## Resolution

`_run_mypy` now passes **`--no-color-output`** to mypy, so the output is plain text regardless of
`FORCE_COLOR`/TTY. Verified: all 7 `test_provenance_tags.py` tests pass in this FORCE_COLOR=3
session, and still pass with `FORCE_COLOR=1` explicitly set. One-line, mechanical, reversible
(low-stakes; orchestrator-resolved + logged per the finding routing). `--no-color-output` addresses
the root (don't let the ambient env colorize) more directly than stripping ANSI in the parser.

## Routing

`spec-defect`, orchestrator-resolved (codebase-mechanical, no design surface). No owner action
needed. Filed + fixed same session; kept as a record of the FORCE_COLOR-vs-subprocess-parsing trap
for any future "tests green standalone but red under the agent" puzzle.
