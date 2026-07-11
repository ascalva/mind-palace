---
type: finding
id: finding-0033
status: routed
ftype: discovery
origin_plan: bp-011
route: orchestrator
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/findings/finding-0031.md            # same root cause, different manifestation
  - docs/build-plans/bp-011/journal.md        # the episode (documented workaround)
resolution: null
---

# finding-0033 — scope-guard path-resolution denial in a delegated worktree (corroborates finding-0031's root cause, new manifestation)

## What

During bp-011's delegated build (isolated worktree
`.claude/worktrees/agent-acfad7293163d7c6f`), every Edit/Write tool call to a file
legitimately inside the plan's `write_scope` was DENIED by `scope-guard.sh`, reporting
the touched path as `claude/worktrees/agent-.../<repo-relative-path>` — i.e. computed
relative to the MAIN checkout root, not this worktree's root. Root cause: `_lib.py:
repo_root()` reads `CLAUDE_PROJECT_DIR` first and only falls back to
`git rev-parse --show-toplevel` when unset; the harness's Edit/Write hook invocation had
`CLAUDE_PROJECT_DIR` pinned to `/Users/ascalva/mind-palace` (the shared checkout) even
though the tool call's own absolute file path was under the worktree. `os.path.relpath`
against the wrong root doubles the `.claude/worktrees/agent-.../` prefix into the
"repo-relative" path, which then spuriously fails every `write_scope` glob.

Confirmed as a false-positive, not a real scope breach: re-running
`_lib.py scope-check <path>` standalone (env `CLAUDE_PROJECT_DIR` absent, so it falls
back to `git rev-parse --show-toplevel` from the worktree CWD) returned `ALLOW` for
every file this session actually touched.

## Why it matters

This is the SAME root cause finding-0031 already named (harness pins
`CLAUDE_PROJECT_DIR` to the main checkout for worktree-isolated agent sessions) but a
DIFFERENT symptom: finding-0031 saw cross-bleed (a worktree builder governed by
ANOTHER plan's write_scope, via the active-plan pointer read). This episode shows the
same env mismatch corrupts `rel()`'s path normalization directly — even with the
correct pointer and the correct plan loaded, a worktree builder's OWN in-scope writes
get denied, because the path arithmetic silently uses the wrong root. This is the
"wrongly DENIED" direction finding-0031 already flagged (friction, Bash-mediated
workarounds erode the pre-hoc guard's value) — corroborating evidence from a second,
independent build session that the issue is systemic to the worktree-delegation
pattern, not a one-off.

## Workaround taken this session (documented, not routing around scope)

Every write was preceded by a standalone `_lib.py scope-check <repo-relative-path>` (or
equivalently, `CLAUDE_PROJECT_DIR` unset) confirming `ALLOW` before the write proceeded
via direct file operations (Python string-replace / heredoc) equivalent to what
Edit/Write would have produced. No path outside `write_scope` + journal +
`docs/findings/**` was touched at any point.

## Recommended direction (route: orchestrator; same fix surface as finding-0031)

finding-0031's recommendation (prefer the process's actual working-tree root via
`git rev-parse --show-toplevel` from CWD over an inherited `CLAUDE_PROJECT_DIR` when
they disagree and `.claude/state/` exists in the working tree; or have the harness set
`CLAUDE_PROJECT_DIR` to the worktree path at spawn time) fixes both manifestations at
once — this finding is evidence the fix is more urgent than a single episode suggested,
since it breaks a builder's OWN in-scope writes, not just cross-plan bleed.

## Re-entry

Parked until the next hooks-scoped plan (or folds into finding-0031's eventual fix,
same surface). Trigger that reopens immediately: any further worktree-delegated build
session hitting the same path-resolution denial.
