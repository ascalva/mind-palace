---
type: finding
id: finding-0075
status: open
created: 2026-07-14
updated: 2026-07-14
links:
  - docs/build-plans/bp-030/plan.md
  - docs/findings/finding-0071.md
  - docs/findings/finding-0072.md
ftype: spec-defect
origin_plan: bp-030
route: orchestrator
---

# bp-030 write_scope omits `tests/unit/test_monitor_server.py` (blocks Item 2's green-suite) — third recurrence of finding-0071/0072

## What

bp-030 Item 2 deletes the dead edge monitor: `edge/monitor/**` + `scripts/monitor.py`
(both in `write_scope`), and removes `MonitorConfig` / `[monitor]` / the launcher monitor-spawn
(all in scope). Its acceptance criterion requires **the full suite stays green** ("the removed
monitor tests, if any, are deleted with it").

A codebase sweep finds exactly one orphaned test:

- **`tests/unit/test_monitor_server.py`** — `from edge.monitor import MonitorApp, render_dashboard`.
  Deleting `edge/monitor/**` reds this file at COLLECTION. It must be deleted with the monitor,
  but it is **not in bp-030's `write_scope`** → `scope-guard` denies the deletion.

The plan authored its three NEW acceptance-test paths into scope (finding-0072 discipline
applied), but missed this EXISTING test that covers the code being deleted — a variant of the
same class, not caught by "list your §7 test paths" because it is a removal, not an addition.

Two things do NOT need scope changes (verified by reading the files):

- **`tests/integration/test_monitor_snapshot.py`** survives unchanged: despite its name it imports
  only `edge.interface.*` + the RETAINED `ops.lifecycle.snapshot` (`build_status`/`write_status`),
  never `edge.monitor`. Its content stays valid (it tests the retained snapshot seam + the handoff
  chat closure). Only its NAME/docstring reference "monitor" — a cosmetic staleness, not blocking;
  optionally rename in a later cleanup (out of this plan's scope).
- **`tests/unit/test_children.py`** is KEPT (children.py kept dormant per the plan); its `Child("monitor", …)`
  uses "monitor" only as a label string — unaffected by the deletion.

## Why it matters

Correcting `write_scope` is a capability-surface change to an owner-blessed, invariant-adjacent
plan — **owner-gated** per the finding-0071/0072 ruling ("never route around a scope denial; the
orchestrator does not silently expand its own capability"). All NON-orphaned Item 2 changes
(config/loader, defaults.toml, launcher spawn removal, scripts/monitor.py, edge/monitor deletion)
are in scope; but deleting `edge/monitor/**` without also deleting `test_monitor_server.py` reds
the suite, so Item 2 cannot be *completed green* until the path is added. Items 1 and 3 are
unaffected and proceed independently.

## Resolution (pending)

Owner hand-adds `tests/unit/test_monitor_server.py` to bp-030's `write_scope` (the finding-0071/0072
pattern). Then Item 2 completes green. **Standing-fix amendment:** the /graduate test-path check
(owed since 0071) must cover not just the §7 acceptance tests a plan ADDS, but also EXISTING tests
that cover code a plan DELETES — a removal orphans its coverage exactly as an addition needs its own.
