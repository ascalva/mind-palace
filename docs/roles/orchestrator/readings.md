---
type: seat-readings
seat: orchestrator
created: 2026-07-26
updated: 2026-07-26
---

# Readings — orchestrator

The **MEASURED** half of the orchestrator seat's state (`dn-role-state-and-scoped-handoff` §2.5):
facts that are the result of *running* something, and that no tree-scan generator can produce — a
suite run, a usage probe, a daemon check, a drill verdict.

**Append-only, newest at the bottom.** A row is never edited to "refresh" it; a newer run appends a
newer row. `handoff.md` renders the **latest row per command** and shows how old it is, so a stale
reading advertises its age instead of impersonating a current fact. **A reading is never gated** —
you take one when the work warrants it (§2.10 check 3); the pane's job is to stop you believing an
old one.

**Row shape** — `| timestamp | command | one-line result |`. The timestamp is UTC, minute
precision. The command is the literal thing that was run, so two runs of the same thing collapse
onto one row in the pane. The result is one line: what it said, plus the *known-expected* part of
it, because a bare count invites the next reader to re-run it to find out whether it was fine.

⚑ **No commit hashes in a result cell.** These rows are rendered into the derived pane, which is
lint-checked for hash-shaped tokens. Name the artifact, not the sha — `git log` is already the
derived view of commits.

| timestamp | command | result |
|---|---|---|
| 2026-07-27T03:36Z | uv sync --frozen --extra dev | ok — dev extras resolved in a fresh worktree venv |
| 2026-07-27T04:41Z | uv run ruff check . | All checks passed (rc 0) |
| 2026-07-27T04:42Z | uv run python scripts/check_imports.py | OK — import firewall + worker boundary both clean (rc 0) |
| 2026-07-27T04:44Z | uv run mypy core agents eval ops scheduler scripts | Success: no issues in 261 files — the floor holds at 0 |
| 2026-07-27T04:47Z | uv run mypy | 69 errors in 20 files of 559 — exactly the recorded tests baseline, none in new code |
| 2026-07-27T04:49Z | uv run python -m ops.type_gate | OK — tier-2 membership + bare-ignore scan clean; one parked non-fatal shim report (finding-0223) |
| 2026-07-27T04:56Z | uv run pytest -q | 2 failed / 2301 passed / 15 skipped in 356s — BOTH pre-existing: the finding-0103 core-self-containment ratchet and the finding-0226 dream-v2 live e2e. The finding-0219 scheduler-live flake passed this run |
