---
type: finding
id: finding-0194
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/audits/ops-wave-2026-07-25.md
  - ops/lifecycle/snapshot.py
  - ops/lifecycle/launcher.py
  - tests/unit/test_status_incident_oracle.py
  - tests/unit/test_status_cost_bound.py
ftype: spec-defect
origin_plan: orchestrator
route: builder
resolution: null
---

# Every citation to bp-102's own two findings points at the wrong document

## What
The bp-102 seal renumbered `0175 -> 0178` and `0176 -> 0179`, but only in the finding files
and the plan's `cost.actual`. Source and tests still cite the pre-renumber ids at ten sites:
`snapshot.py:46,124,233,319`; `launcher.py:486,1038,1066`;
`test_status_incident_oracle.py:20,158`; `test_status_cost_bound.py:222`.

Both wrong ids resolve to REAL, UNRELATED findings:

| cited | code means | finding actually is |
|---|---|---|
| finding-0174 (x6) | "there is no job-level timeout" | the memory ceiling is enforced over an incomplete accounting |
| finding-0178 (x4) | "two read surfaces have no cheap query" | there is no job timeout — the "~75-minute budget" never existed |

Correct ids: job-timeout = 0178; read-surfaces = 0179.

## Why it matters
A reader is MISLED rather than 404'd, which is strictly worse. In an artifact-chain repo
where code comments are the primary route from mechanism back to warrant, a mis-citation
that silently resolves is a real defect. Renumbering-at-integration is a known recurring
hazard (finding-0182) that does not propagate into code comments — worth a citation sweep
in the seal gate.
