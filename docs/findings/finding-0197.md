---
type: finding
id: finding-0197
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/audits/ops-wave-2026-07-25.md
  - ops/lifecycle/launcher.py
ftype: spec-defect
origin_plan: orchestrator
route: builder
resolution: null
---

# The orphan sweep runs unguarded on the critical start path, before signal handlers install

## What
`ops/lifecycle/launcher.py:538` is a bare `print(...sweep_orphans(...).render())` — no
try/except — executed BEFORE `_install_signal_handlers()`, inside a scope whose enclosing
`finally` marks the run unclean. Zero tests exercise a raising sweep.

Related: the sweep's outcome is written only to stdout — no telemetry vital, no run-ledger
note.

## Why it matters
A new sqlite operation was inserted at the top of `start` with no failure path. Any raise
marks the run unclean -> the next `start` enters recovery -> under launchd `KeepAlive` this
is a restart loop that ALSO disarms itself, because recovery never builds components and so
the sweep never runs.

The stdout-only reporting compounds it: a restart that fails 800 stranded jobs is a
significant operational event visible only in the launchd log, and per the audit the sweep's
own error string then displaces the real `last_failure` in the incident oracle.
