# bp-147 — journal

## Pre-build notes for whoever picks this up

- ⚑ **This plan retires NOTHING.** Both enforcement layers run simultaneously during the
  transition: `journal-gate`'s grep tooth AND the typed seal. `.claude/settings.json` and
  every hook are out of `write_scope`. bp-149 does the removing, and it is blocked on owner
  amendments.

- ⚑ **Six clauses is the risk.** If the session runs long, STOP after Item 37 (the parity
  harness) and leave Item 39 for a resume. Do not compress the parity work to fit — the
  parity harness IS the deliverable that makes bp-149 lawful (invariant 8).

- ⚑ **Side-effect audit before any demo run against `journal-gate`.** `cmd_stop_audit`
  (`_lib.py:820`) is read-only over git BUT appends a marker line to a journal on the
  HOOK-FAILURE path. Run the harness against a fixture repo root under `tmp_path`, never the
  real worktree. Record the audit even when it comes out clean (build-plan skill, warrant
  finding-0039 / oq-0017).

- ⚑ **Be honest about attribution.** Clause (c) is discharged by bp-143 + bp-145, not by this
  plan. Clause (e′)'s DERIVED half is parked until bp-148. Item 39's table must say so. A
  clause marked "proved" whose test is a `skip` is exactly how bp-149 gets led into an
  unlawful retirement.

- ⚑ **Item 36's falsifier is the design-level one.** If clause (b2) trips on an export-driven
  front-matter rewrite, bp-142's ratchet and bp-144's body-only hash are in conflict. STOP
  and raise; do not patch.

- **Do not grade the follow-through answers.** Presence and non-empty only. "Built but NOT
  wired" is a valid, expected answer, and grading it would make honest answers costlier than
  dishonest ones.

- **`UnitState` must be FOLDED, never cached.** A cached field recreates the resume brief's
  structural defect one layer down — the very diagnosis §2.7 makes.

- **Local gate before sealing:** ruff · `scripts/check_imports.py` · mypy (scripts floor 0,
  tests baseline 69) · `ops.type_gate` · pytest with the standard deselects. Also run `_lib`'s
  own tests and `tests/unit/test_handoff_purity.py`.

## Entries

_(none yet — this plan is `proposed`; the first entry is written by the build session)_
