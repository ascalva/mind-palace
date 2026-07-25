---
type: finding
id: finding-0187
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/audits/ops-wave-2026-07-25.md
  - ops/lifecycle/launcher.py
  - tests/integration/test_lifecycle.py
ftype: spec-defect
origin_plan: orchestrator
route: builder
resolution: null
---

# The orphan-sweep wiring has zero test coverage; deleting it leaves the suite green

## What
`ops/lifecycle/launcher.py:538` is the wave's only integration point. Mutations against
the covering set (85 tests): deleting the sweep call entirely -> 85 passed; wrong run id
-> 53 passed; moving it after `_serve()` -> 44 passed.

`_FakeQueue.swept_for` is assigned at `tests/integration/test_lifecycle.py:141` and read
NOWHERE in the repository. `be225fd`'s commit message states the fake records the run id
"so a test can assert adoption and not merely the call" — that test was never written.
`Components(...)` is constructed in four places; all three test constructions pass
`_FakeQueue`, so `Launcher.start()` is never exercised against a real `JobQueue`.

## Why it matters
`wiring is part of finishing` was satisfied in letter — the switch exists — and violated
in substance: an untested switch is a claim, not a mechanism. Any future refactor deletes
or reorders this line in silence. Ratchet: an integration test driving `Launcher.start()`
against a REAL `JobQueue` with a pre-seeded stranded RUNNING row, asserting reclamation
AND that adoption happened before the first `claim()`.
