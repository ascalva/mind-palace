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
