---
type: finding
id: finding-0211
status: routed
created: 2026-07-26
updated: 2026-07-26
links:
  - ops/lifecycle/launcher.py                        # _process_identity / _supervisor_alive (D2)
  - tests/unit/test_restart_trustworthy.py           # the host-coupled test that caught it
  - .github/workflows/ci.yml                         # the ratchet job that is red
  - docs/build-plans/bp-105/plan.md                  # the plan that introduced it (`2add267`)
  - docs/findings/finding-0186.md                    # the owner ruling D2 implements
  - docs/findings/finding-0198.md                    # the psutil-shim hand-off this probe is quarantined under
ftype: codebase
origin_plan: bp-105
route: builder
resolution: null
---

# `_supervisor_alive`'s D2 interpreter probe is platform-fragile: CI has been red on every push for ~13 hours

## What

**CI's `ratchet` job has failed on every push since `2026-07-25T18:36Z` — 55 consecutive failures.**
Last green was `0206043` (2026-07-25T16:59Z). The breaking change is `2add267`
(`build(bp-105): the restart is trustworthy`), which introduced `_supervisor_alive`.

Three tests in `tests/unit/test_restart_trustworthy.py` fail **only on the Linux runner**:

- `test_this_very_process_reads_as_a_live_supervisor` — `assert False is True`
- `test_start_refuses_over_a_live_supervisor_without_opening_a_run_or_sweeping` — `assert 0 == 1`
- the `force=True` sibling — `assert 0 == 1`

All three are one root cause: `_supervisor_alive` returns `False` for a live Python process on Linux.
Locally the same file is **32 passed** (verified this session).

**The mechanism, narrowed to one branch.** `_supervisor_alive` (`ops/lifecycle/launcher.py:176-221`)
has exactly two disproofs, and the CI log's own values exclude the first:

- **D1** (`created > opened + _CLOCK_SLACK_S`) — logged `RunRecord(started_at='2026-07-26T06:28:31',
  pid=2268)`; the runner clock is UTC so `.replace(tzinfo=UTC)` is accidentally correct there, and the
  pytest process was created at ~06:27 — *before* the row. D1 cannot fire.
- ⇒ **D2** (`if name is not None and "python" not in name.lower()`) is what fires. `name` comes from
  `psutil.Process(pid).name()` (`:167-172`), which on Linux resolves the **console-script** name for a
  `uv run pytest` invocation rather than the interpreter, so it contains no `"python"`. On macOS the
  same call returns `'Python'` (measured this session: `name()` = `'Python'`, `exe()` =
  `…/Python.app/Contents/MacOS/Python`).

**The premise is right; the probe answers a different question.** D2 wants to know *"is this process a
Python interpreter?"*. `name()` answers *"what is this process's `comm`/argv0 basename?"* — which
varies with how the interpreter was invoked (console script vs `python -m` vs a framework build).
`exe()` answers the intended question directly, and the existing docstring already establishes it is
safe in the deployed foreign-owner case: *"on macOS `cmdline()` raises AccessDenied for a foreign owner
… while `name()`/`exe()` read fine"* (`:168-170`). So the robust probe was already known to be
available and the fragile one was chosen.

**The failing test is not the defect — it is the only thing that caught it.** It is deliberately the
one test that probes a real host process (the docstring at `:206-209` explains that both probes are
injected precisely so *other* tests can pin shapes the host cannot have). It should keep existing.

## Why it matters

1. **The authoritative gate has been dark for ~13 hours.** GitHub Actions is the canonical CI
   (oq-0014 D4(i)). Every push in that window — including four docs-only commits — reports failure, so
   the ratchet job has been measuring nothing and any *other* regression landing in that window is
   unobserved.
2. **⚑ Deploy is hard-blocked.** `mind-palace deploy` is the one owner-in-loop gate and its witness
   requires an attestable green HEAD. The code-ingest deploy the owner already owes (keep-and-link;
   until deployed the live daemon still delete+replaces on every commit) cannot proceed while CI is
   red — so this bug is silently gating a data-correctness fix.
3. **It is a fail-*open* direction on a fail-closed guard.** `_supervisor_alive` exists to make
   `start` refuse over a live supervisor (owner ruling finding-0186: *on ambiguity, refuse*). A
   wrongly-`False` answer means `start` proceeds and **rewrites a live worker's rows** — precisely
   what finding-0186 was filed to prevent. Today that misfire is confined to Linux, so the deployed
   macOS daemon is not exposed; the exposure is that the guard's correctness rests on a platform
   accident.

## Re-entry condition

D2 probes the interpreter via `exe()` (basename), falling back to `name()`, so the answer no longer
depends on invocation style; `tests/unit/test_restart_trustworthy.py` keeps its host-coupled test; and
**CI's `ratchet` job is green on the runner** — the acceptance is the remote run, not a local pass,
since a local pass is exactly what hid this.

Closes when `gh run list --workflow=ci` shows success on a HEAD containing the fix.

## Routing

`codebase` → builder. Bounded, mechanical, and the fix site is inside bp-105's original
`write_scope`. Carried by **bp-121**. Note the sibling process defect (a seal attests the *local* gate
while the *authoritative* gate is red) is **finding-0212**, routed to the orchestrator — do not fold
them: one is a probe, one is a duty.
