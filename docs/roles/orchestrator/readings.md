---
type: seat-readings
seat: orchestrator
created: 2026-07-26
updated: 2026-07-27
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

⚑ **A timestamp is READ from `date -u` at the moment of the run — never composed.** A future-dated
stamp renders a near-zero age, so the stalest row in the pane advertises itself as the freshest —
the exact impersonation the age display exists to prevent. If the moment is genuinely unrecorded,
write `unknown`: the shape supports it natively (`_age()` returns "age unknown", and
`latest_per_command` orders by file position, not by parsing a clock).

⚑ **Known caveat — this file is NOT monotonic in timestamp.** The seed block written by `bp-124`
carries stamps up to 56 minutes **ahead of the commit that introduced them**, so four of its rows
postdate their own commit and cannot have been clock-read. They are **retained unaltered**
(append-only: keep and link, never delete and replace) and `finding-0243` carries the analysis.
**File order is authoritative for "latest", not the timestamp column** — which is what
`latest_per_command` implements, so the pane is correct today. Any future consumer that sorts these
rows by timestamp must read `finding-0243` first.

| timestamp | command | result |
|---|---|---|
| 2026-07-27T03:36Z | uv sync --frozen --extra dev | ok — dev extras resolved in a fresh worktree venv |
| 2026-07-27T04:41Z | uv run ruff check . | All checks passed (rc 0) |
| 2026-07-27T04:42Z | uv run python scripts/check_imports.py | OK — import firewall + worker boundary both clean (rc 0) |
| 2026-07-27T04:44Z | uv run mypy core agents eval ops scheduler scripts | Success: no issues in 261 files — the floor holds at 0 |
| 2026-07-27T04:47Z | uv run mypy | 69 errors in 20 files of 559 — exactly the recorded tests baseline, none in new code |
| 2026-07-27T04:49Z | uv run python -m ops.type_gate | OK — tier-2 membership + bare-ignore scan clean; one parked non-fatal shim report (finding-0223) |
| 2026-07-27T04:56Z | uv run pytest -q | 2 failed / 2301 passed / 15 skipped in 356s — BOTH pre-existing: the finding-0103 core-self-containment ratchet and the finding-0226 dream-v2 live e2e. The finding-0219 scheduler-live flake passed this run |
| unknown | claude -p "/usage" | session 52% · week 43% of allowance, resetting Jul 31 20:00 ET. Migrated from the outgoing brief by bp-125, which recorded the figures but NOT when they were taken — the age is genuinely unknown, not zero. Re-probe before any spawn rather than trusting this row |
| unknown | owner-intent transcript sweep (literal command not recorded) | the obvious user-string filter sees only ~60% of the owner's words; ~86 mid-turn queue-operation rows plus structured question answers are invisible to it. Migrated by bp-125 from a sweep whose own record is still untracked; timestamp and command were both unrecorded, and are marked so rather than reconstructed |
| 2026-07-27T04:41Z | uv run ruff check . | All checks passed (rc 0) — bp-125's worktree |
| 2026-07-27T04:43Z | uv run python scripts/check_imports.py | OK (rc 0) — import firewall clean; worker boundary opens no store |
| 2026-07-27T04:47Z | uv run mypy core agents eval ops scheduler scripts | Success: no issues in 261 source files — the floor holds at 0 |
| 2026-07-27T04:50Z | uv run mypy | 69 errors in 20 files of 559 checked — EXACTLY the pinned tests/ baseline, rc 1 as expected; none in new code |
| 2026-07-27T04:44Z | uv run python -m ops.type_gate | OK (rc 0) — tier-2 membership + bare-ignore scan clean; the one parked non-fatal shim report (finding-0223) unchanged |
| 2026-07-27T04:53Z | uv run pytest -q | 2 failed / 2301 passed / 15 skipped in 234s — BOTH pre-existing and expected: the finding-0103 core-self-containment ratchet and the finding-0226 dream-v2 live e2e. The finding-0219 scheduler-live flake passed. No regressions |
| 2026-07-27T05:20Z | claude -p "/usage" | session 59% · week 49% all-models · Fable 25%; week resets Jul 31 20:00 ET. Probed at bp-125's re-seal — supersedes the migrated `unknown`-age 43% row above, which had no recorded time |
| 2026-07-27T05:20Z | uv run ruff check . | All checks passed (rc 0) — re-run after the audit fixes; clock-read stamp |
| 2026-07-27T05:20Z | uv run python scripts/check_imports.py | OK (rc 0) — import firewall + worker boundary both clean |
| 2026-07-27T05:20Z | uv run mypy core agents eval ops scheduler scripts | Success: no issues in 261 source files — the floor holds at 0 |
| 2026-07-27T05:20Z | uv run mypy | 69 errors in 20 files of 559 checked — EXACTLY the pinned tests/ baseline, rc 1 as expected |
| 2026-07-27T05:20Z | uv run python -m ops.type_gate | OK (rc 0) — tier-2 membership + bare-ignore scan clean; the parked finding-0223 shim report unchanged |
| 2026-07-27T05:24Z | uv run pytest -q | 2 failed / 2301 passed / 15 skipped in 255s — the SAME two pre-existing failures (finding-0103 ratchet, finding-0226 dream-v2 live); scheduler-live flake passed. Re-run after the audit fixes; markdown-only diff, no regressions |
