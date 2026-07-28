# bp-140 — journal

## Pre-build notes for whoever picks this up

- ⚑ **This plan changes no enforcement.** Every hook stays registered; `.claude/settings.json`
  is not in `write_scope` and must not be touched. If you find yourself editing a hook, you
  have left the plan — stop and re-read §9.

- ⚑ **The store must never be an existing store.** `data/*.sqlite` are live (queue, code
  snapshots). This plan creates a NEW file at `~/.mind-palace/registry.sqlite`, and every
  test points `OUROBOROS_REGISTRY` at a scratch path. Item 6's acceptance explicitly asserts
  the env var is set — a test that silently falls back to the real path would write the
  owner's machine-level store from CI. Fail the test if the override is absent.

- **The concurrency proof must use subprocesses, not threads.** The scenario in the note is
  two parallel *worktree builders* — separate OS processes, separate connections. A
  threaded test shares a connection pool and proves nothing about SQLite's write lock.

- **Do not write a second front-matter parser.** `.claude/hooks/_lib.py:183` is the one
  parser; `scripts/board.py:34-38` shows the sys.path idiom for reusing it from repo-workflow
  tooling. Duplicating it is the exact defect finding-0101/0103 named and the owner treats it
  as a defect, not a nit.

- **Tier-2 mypy floor is zero.** `.github/workflows/ci.yml` runs
  `uv run mypy core agents eval ops scheduler scripts` and accepts no errors, so `ops/registry/**`
  and `scripts/registry.py` must be fully typed on landing. The whole-tree count is pinned at
  exactly 69 (tests/ baseline) — new test files must add zero.

- **Local gate before sealing:** ruff · `scripts/check_imports.py` · mypy (scripts floor 0,
  tests baseline 69) · `ops.type_gate` · pytest with the standard deselects. pytest alone is
  not sufficient.

- **`signature`/`signer` columns land NULL in Item 1.** They exist now precisely so bp-145
  needs no `ALTER` on an append-only table later. Do not remove them as "unused".

## Entries

_(none yet — this plan is `proposed`; the first entry is written by the build session)_
