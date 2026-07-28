# bp-143 — journal

## Pre-build notes for whoever picks this up

- ⚑⚑ **The artifact tree is NOT in `write_scope`, and that is the plan.** The migration
  changes the log, never the tree. If you find yourself wanting to edit a `plan.md`, a
  design note, or a finding to make the ratchet green — STOP. Ratified/superseded notes are
  agent-immutable (A8) and a repair is a finding, never an edit. Success is measured by
  `git status --porcelain -uall docs/` being **empty** after `migrate --apply`.

- ⚑ **`front_matter_raw` is the mechanism that makes this possible, and it is also the
  mechanism that could launder drift.** Clause 2 of §6.3 — raw replay only while the parsed
  fields still equal the entity's fields — is load-bearing. Item 17's falsifier is exactly
  the test that it holds. Do not "optimize" the equality check away.

- ⚑ **Do not write a second tree importer.** `ops/registry/recover.py::import_tree` (bp-141)
  is the one. If bp-141 has not landed, stop and raise (§10) rather than duplicating — the
  owner treats duplicated implementations as defects, not nits.

- ⚑ **Do not write a fifth tree scanner.** `scripts/board.py:174-233` has `scan_plans`,
  `scan_notes`, `scan_findings`, `scan_oqs`, `_scan_deskchecks`, and `scripts/handoff.py:57-61`
  shows how to import them.

- **Measure first, record the numbers.** §3 Q1's counts are deliberately not asserted in the
  plan. Item 16's first recorded output is the real corpus census; put it in this journal.

- **Item 19 gets its own commit.** Commit everything else first, then apply, then capture
  `git status` before/after. The apply must be a clean revertible commit whose `docs/` delta
  is empty.

- **The known round-trip hazards** (§3 Q3): key order, unquoted ` #` in a value (the bp-066
  footgun — report, never quote away), and blank/comment lines inside the front-matter block
  that `_lib.py:196-197` discards. Seed the fixtures with all three so an empty
  `not_round_trippable` list is a *finding*, not a *default*.

- **Local gate before sealing:** ruff · `scripts/check_imports.py` · mypy (scripts floor 0,
  tests baseline 69) · `ops.type_gate` · pytest with the standard deselects.

## Entries

_(none yet — this plan is `proposed`; the first entry is written by the build session)_
