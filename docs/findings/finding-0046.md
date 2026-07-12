---
type: finding
id: finding-0046
status: open
created: 2026-07-12
updated: 2026-07-12
links:
  - tests/e2e/test_scheduler_live.py
  - docs/build-plans/bp-016/journal.md
ftype: codebase
origin_plan: bp-016
route: builder
resolution: null
---

# Live e2e test races its own clean-slate unload — flaky empty-text failure

## What

`tests/e2e/test_scheduler_live.py::test_supervisor_dispatches_a_real_job` failed twice
in a row during bp-016's gate run (worktree, 2026-07-12): the job completes (`DONE`)
but `captured["text"]` is empty — Ollama returned HTTP 200 with empty
`message.content` after ~132 s. The same test then passed on re-runs in BOTH checkouts
(main 20.7 s / 54.5 s / 5.3 s; worktree 15.8 s), and a direct probe of the identical
chat path from the failing worktree succeeded warm (2.4 s) and cold (92.1 s).

The mechanism, observed: the test's clean-slate step (`client.unload(name)` for every
`ps()` row) initiates an **asynchronous** unload — `ps()` still lists the model
immediately after — so the cold dispatch can land while Ollama is mid-swap. The test's
own comment says the cleanup exists so Ollama "isn't mid-swap when we dispatch"; the
cleanup itself creates that race. Under some daemon states the raced generation returns
empty content rather than timing out.

## Why it matters

A live-axis gate test that flakes ~consecutively costs a full re-run cycle
(~10 min/suite) and erodes trust in red. The failure shape (DONE + empty text) is also
indistinguishable from a real regression in the chat path, so it demands manual
investigation every time it fires.

Candidate fix (one line each): poll `ps()` until the unload actually completes before
dispatching, and/or retry-once on empty text with the flake documented. `tests/e2e/` is
outside bp-016's write_scope — carried as a finding instead of fixed in place.

## Re-entry condition

Any plan whose write_scope covers `tests/e2e/` (or a triage-mandated flake sweep) picks
this up. Until then: a red on this test with DONE + empty text and no chat-path diff is
the flake — re-run before investigating.

## Routing

`codebase` → builder-tier fix; annotated here and carried past bp-016 (out of its
scope). Surfaced at the next /triage.
