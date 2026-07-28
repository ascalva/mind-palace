# bp-142 — journal

## Pre-build notes for whoever picks this up

- ⚑ **`export --write` on the shipped state MUST be a no-op.** The registry is empty until
  bp-143 migrates. If `git status --porcelain` is non-empty after an export, stop (§10) —
  the plan has silently become the migration.

- ⚑ **A vacuously-green ratchet is the real risk.** With an empty snapshot, Item 14 passes
  trivially and would keep passing forever. The test MUST also build a non-empty synthetic
  registry, perturb one file, and observe the check go RED. A ratchet never seen red is not
  a ratchet.

- ⚑ **`write_scope` globs are emitted BARE, always.** An entry containing ` #` is a hard
  error, not a quoted escape — `_lib.py:218 _scalar` strips trailing comments only from
  *quoted* scalars, so quoting a glob silently changes what `scope-guard` matches. This is
  the bp-066 footgun and the export is the place it would become systemic.

- **Prove "no clock" with an AST scan, not by inspection.** Item 13's falsifier scans
  `ops/registry/export.py` for `datetime`/`time`/`now`/`uuid`/`random`/`os.environ`/
  `subprocess`. Same shape as `scripts/check_imports.py`'s scans.

- **Do not change `_lib.py` behaviour.** A docstring cross-reference is the only edit
  allowed there, and `_lib.py` is not even in `write_scope` — if a behaviour change looks
  necessary, that is a `codebase` finding and a stop.

- **First act of Item 11:** `grep -rlU $'\r' docs/` and record the result. Byte-exact
  comparison plus an unnoticed CRLF is a whole afternoon.

- **The failure message is a UI.** Print the unified diff AND the literal
  `uv run scripts/registry.py export --write`. The pin exists so the gate is dischargeable
  by one mechanical command (`scripts/handoff.py:18-27`).

- **Local gate before sealing:** ruff · `scripts/check_imports.py` · mypy (scripts floor 0,
  tests baseline 69) · `ops.type_gate` · pytest with the standard deselects. Also re-run
  `tests/unit/test_board.py` and `tests/unit/test_handoff_purity.py` — a shared-parser
  regression surfaces there first.

## Entries

_(none yet — this plan is `proposed`; the first entry is written by the build session)_
