---
type: finding
id: finding-0198
status: resolved
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/build-plans/bp-105/plan.md
  - docs/findings/finding-0186.md
  - ops/lifecycle/launcher.py
  - core/typedshims/psutil.py
ftype: spec-fidelity
origin_plan: bp-105
route: builder
resolution: "Built the governing rule (positive disproof), not the illustrative one. Two disproofs — process postdates the row (D1), process is not a Python interpreter (D2) — refuse otherwise. Shim hand-off left open below."
---

# bp-105's pinned identity rule is inverted: as written it builds a guard that never fires

## What

bp-105 §6 and finding-0186's trap section both pin the recycled-pid discriminator as:

> *"A process created BEFORE its own run row cannot be that run's supervisor."*

The implication is backwards. `Launcher.start()` writes its row with
`runs.open_run(..., pid=os.getpid(), ...)` (`ops/lifecycle/launcher.py:517`), evaluated from
*inside* the supervisor process — so the supervisor necessarily exists **before** its own row.
Measured on the live tree:

```
create_time epoch: 1784999058.294983  -> 2026-07-25T17:04:18.294
started_at (runs.py:106, timespec="seconds"): 2026-07-25T17:04:18
```

Implemented literally, `_supervisor_alive` returns **False for every genuine live supervisor**.
`start` would never refuse, Item 2's hazard (finding-0186) would stay open, and named
falsifier A would be unreachable. bp-105 §7 Item 2's falsifier B carries the same inversion
("whose process predates the run row; assert `start` **proceeds**").

A second-order defect in the same sentence: `started_at` is truncated to whole seconds, so a
genuine supervisor's `create_time` can read up to ~1 s *later* than its own row. Any
comparison without slack misclassifies on truncation alone.

## Why it matters

This is the falsifier↔test gap the ops-wave audit named as a doctrine-level defect class,
appearing one layer earlier — in the *plan*, where the falsifier is authored. A builder
implementing the pinned interface faithfully would have shipped a no-op guard with a green
test asserting the no-op, and the audit's own remedy would have reproduced the audit's own
finding. The plan's governing sentence is correct and survives — *"the recycled-pid carve-out
fires only when identity is positively disproven"* — which is what the build followed.

## Resolution (builder, per CLAUDE.md routing: `spec-fidelity` → builder resolves)

`_supervisor_alive(run)` is `_pid_alive(run.pid)` AND not positively disproven. Disproof is
either:

- **D1** — `create_time > started_at + 5 s`: the process postdates the row and cannot have
  written it. The 5 s absorbs the whole-second truncation above; a real recycle requires the
  pid counter to wrap (~99k spawns) and is never seconds away.
- **D2** — the process is not a Python interpreter. The supervisor always is
  (`com.mind-palace.palace.plist:26-33` runs `uv run scripts/palace.py start`).
  `psutil.Process(pid).name()` is readable without privilege even for root-owned foreign
  processes on macOS (measured: `pid 1 -> 'launchd'`, while `cmdline()` raises `AccessDenied`).

Everything else refuses. D2 is required, not decorative: D1 alone cannot clear a stale row
whose pid wrapped onto a long-lived process such as `launchd`/`systemd`, which is the exact
self-inflicted brick finding-0186's trap section exists to prevent.

## Open hand-off — the raw `psutil` touch is in the wrong module

`core/typedshims/psutil.py` is the ONE place the repo touches raw `psutil`
(type-system-as-core-audit §2.5; `core/vitals.py:19` and `ops/lifecycle/launcher.py:291,1003`
both go through it). `process_create_time` / `process_name` belong there. That file is **not in
bp-105's `write_scope`**, so the probe lives behind one narrow helper in
`ops/lifecycle/launcher.py` with an inline warrant pointing here, rather than routing around
the scope boundary. **Follow-up: move both accessors into the shim and have the launcher import
them** — a mechanical move, one plan, no behaviour change.

Instance of finding-0191 in miniature: the write_scope did not partition the change.
