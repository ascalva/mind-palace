---
type: finding
id: finding-0015
status: open
created: 2026-07-06
updated: 2026-07-06
links:
  - docs/design-notes/alignment-subsystem.md
  - eval/drift.py
  - docs/audits/corpus-state-audit-2026-07.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# finding-0015 — The alignment "keystone" (drift gauge) is built but largely inert on the live path

## What
`alignment-subsystem.md` §2/§7 specifies the drift gauge `D(t) = d(μ(s_t), B)` is
"run periodically" as a live alignment audit that emits an alignment report. In code
the gauge is fully built and tested — `eval/drift.py:133` `drift()`, `:210`
`measure_drift()`, fixed points in `eval/golden/baseline.json`,
`tests/unit/test_drift.py`, `tests/property/test_drift_property.py`. But its live
footprint is minimal:

- **Numeric capability-drift `D(t)` has no live caller.** `measure_drift()` is
  invoked only inside the flag-off self-mod validator (`ops/selfmod.py:215-227`).
- **The only wired conjunct is the boot-time Constitution-fingerprint trip**
  (`ops/lifecycle/preflight.py:135-137`, run on every `palace start` via
  `ops/lifecycle/launcher.py:192`) — a hard equality check on one file, not the
  numeric gauge.
- **A2 structural detection** (`core/complex/cut.py:111` `alignment_snapshot`) is
  called only from `tests/unit/test_drift.py`; the alignment report, the surgery loop
  (§3), and the reset loop (§4) are design-only. PROGRESS lists "A2 (structural
  detection + the alignment report)" as *next* (`:123`).
- **The OpsView drift-narration seam is dead** — `core/ops_view.py:109` can narrate a
  drift value, but every live caller passes `drift=None` (`scripts/talk.py`,
  `scheduler/interface.py`).

## Why it matters
Track A is the declared "keystone… makes everything else observable and safe to grow"
(`docs/ROADMAP-V1.md`). Its actual runtime story is a boot-time conformance trip only;
the ongoing drift audit the note (and A2 in PROGRESS) promise is unbuilt. A reader
could assume live drift monitoring that is not running.

## Re-entry condition
Build A2 (periodic structural detection + alignment report) and wire `measure_drift()`
into a scheduled/monitor path; feed `OpsView` a real drift value so the narration seam
is live.

## Routing
`direction` → orchestrator. The gauge library is done; the live audit loop is the
next Track-A build the owner sequences.
