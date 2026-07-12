---
type: finding
id: finding-0045
status: resolved
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/build-plans/bp-017/plan.md
ftype: spec-defect
origin_plan: bp-017
route: orchestrator
resolution: "2026-07-12, orchestrator — `public/` added to .gitignore (one line + comment), same session as the bp-017 merge"
---

# `.gitignore` does not cover the `public/` mkdocs build output directory

## What

bp-017 §"Add `public/` build output nowhere in git" required checking `.gitignore`
coverage before running the §6(a) build. It does not cover it: after running
`uvx --with mkdocs-material --with "mkdocstrings[python]" mkdocs build --site-dir
public` locally, `git status --short` shows `public/` as untracked (would be
`git add`-able by an incautious `git add -A`/`git add .`, which CONVENTIONS and
CLAUDE.md both warn against, but the safety net should not rely solely on
operator discipline).

The GitLab `pages` job never risked this because GitLab Pages' `artifacts: paths:
[public]` mechanism uploads and discards the directory outside the working tree
checkout's git-tracked state in the same way — but a local `mkdocs build` run
(exactly what this plan's acceptance test requires, and what a future contributor
will run to preview the site) leaves `public/` sitting in the worktree,
untracked and un-ignored.

## Why it matters

Low severity, but real: an accidental `git add -A` after a local docs build would
commit ~330 rendered HTML modules (multiple MB) into the tracked tree. `.gitignore`
is not in bp-017's `write_scope` (`.github/workflows/pages.yml`, `mkdocs.yml`,
`docs/findings/**`, `docs/build-plans/bp-017/**` only), so this builder cannot make
the one-line fix without routing around the write-scope capability — which CLAUDE.md
explicitly forbids ("a denial means narrow the scope or file a finding — never route
around").

## Re-entry condition

Not parked against any acceptance criterion — both of bp-017's items (12, 13) are
otherwise unblocked and proceed independently of this fix. Re-entry: whenever an
orchestrator or a builder with `.gitignore` in scope adds one line:

```
public/
```

(alongside the existing `data/`, `*.duckdb`, etc. block, or its own line near the
OS/packaging-cruft section) — trivial, no design judgment required.

## Routing

`spec-defect` / `codebase` in nature (mechanical gap, not a design question) — but
routed to `orchestrator` rather than self-resolved because the fix requires writing
to `.gitignore`, which sits outside this plan's `write_scope`. The orchestrator (or
a future plan with `.gitignore` in scope) applies the one-line addition; no design
note or owner decision is implicated.
