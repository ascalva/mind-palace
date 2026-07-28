# bp-146 — journal

## Pre-build notes for whoever picks this up

- ⚑ **This plan retires NOTHING.** `scope-guard` keeps full teeth; `.claude/settings.json` is
  not in `write_scope`. Building a replacement is not removing the original — that split is
  what keeps the owner's ratified-note amendments off this plan's critical path (bp-149 is
  where retirement happens, and it is blocked).

- ⚑ **Import `_lib.glob_match`, `_lib.matches_any`, `_lib.DENYLIST`, `_lib._changed_files`.**
  Do NOT use `fnmatch`, `glob`, or `PurePath.match`. Item 29's falsifier is an AST scan for
  exactly that. A parity test against a *different* matcher proves the new code agrees with
  itself, not with the hook.

- ⚑ **The diff must be untracked-inclusive (`-uall`).** `agent-workflow.md` §6 (warrant
  finding-0003): a plain `git diff` omits new files, and the Bash-written untracked file is
  precisely what the pre-hoc guard cannot see. Item 31's falsifier tests this directly.

- ⚑ **Never "helpfully" strip a comment from a malformed glob.** Report it with the
  finding-0085 explanation. Silent normalization hides the defect while looking like a fix.

- ⚑ **Parity failure is a STOP, and the most consequential outcome this plan can have.** If
  `scope-guard` denies a case `land` admits, bp-149 must not start (invariant 8). Say so
  loudly in the seal.

- **Record the side-effect audit even though it comes out clean.** `cmd_scope_check`
  (`_lib.py:431-478`) prints a decision and writes nothing — verified. The build-plan skill
  requires the audit before a falsifier demo run against pre-change code; recording "audited,
  clean" is the deliverable, not skipping it.

- **Record the F7 baseline.** Count `scope-guard` denials per build wave from the existing
  journals. F7 is a post-adoption measurement and stays OPEN; the plan's job is to make it
  measurable later, not to declare it discharged.

- **Local gate before sealing:** ruff · `scripts/check_imports.py` · mypy (scripts floor 0,
  tests baseline 69) · `ops.type_gate` · pytest with the standard deselects. Also run
  `_lib`'s own tests — they must stay green and untouched.

## Entries

_(none yet — this plan is `proposed`; the first entry is written by the build session)_
