---
type: finding
id: finding-0064
status: open
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/build-plans/bp-026/plan.md
  - tests/unit/test_interpreter_versions.py
  - tests/unit/test_code_sensor.py
  - ops/code_sensor.py
ftype: spec-defect
origin_plan: bp-026
route: builder
resolution: null
---

# bp-026's write_scope excludes two files the Item 20 version bump breaks

## What

`tests/unit/test_interpreter_versions.py` (bp-018's interpreter-version ratchet, dn-self-sensing
§3.2 V2) pins, for `phi_code`, a `(version, sha256)` pair over `(ops/code_sensor.py,
ops/code_snapshot.py)`. bp-026 Item 20 adds `_corpus_to_corpus_edges` (a new sensing
capability — φ_code now emits `corpus_to_corpus` reference edges, a reading it never
produced before) plus supporting helpers to `ops/code_sensor.py`, which IS in this plan's
`write_scope`. This changes the file's source bytes without changing `INTERPRETER_VERSION`,
which the ratchet's own doctrine treats as exactly the failure mode it exists to catch: "an
unbumped source change is a RED ratchet test... never silent" (module docstring,
`ops/code_sensor.py:69` pre-fix).

`docs/build-plans/bp-026/plan.md` is silent on `INTERPRETER_VERSION`/the ratchet entirely —
no §2 manifest entry, no §6 interface note, no §11 parked-decision row mentions it. This is a
genuine spec gap: Item 20's acceptance test never anticipated this file existing.

## Why it matters

`uv run pytest -q` (the gate's fifth leg) reddened on `tests/unit/test_interpreter_versions.py::
test_declared_version_matches_the_pin[phi_code]` and `::test_source_hash_matches_the_pin[phi_code]`
once Item 20's code landed. **This is a worldview change, not a refactor** — per the ratchet's
own criterion ("bump ⇒ re-projection supersedes... an unbumped source change is a RED ratchet
test"): φ_doc's corpus_to_corpus edges are new sensed content, not a rewrite of existing
semantics (Item 19's code↔corpus meaning is explicitly UNCHANGED — the plan's own acceptance
bar). The correct resolution is therefore **bump, not re-pin-at-same-version**.

I bumped `ops/code_sensor.py`'s `INTERPRETER_VERSION` from `"1.0.0"` to `"1.1.0"` (minor, since
existing code↔corpus semantics are additive-only per Item 19's bar) — this IS in my
write_scope. But `tests/unit/test_interpreter_versions.py`'s `INTERPRETERS["phi_code"]` entry
(the pin itself) is **NOT** in bp-026's write_scope
(`core/stores/reference_edges.py`, `ops/code_sensor.py`, `tests/unit/test_reference_edges.py`,
`tests/integration/test_reference_edge_isolation.py` [fixtures only], `docs/build-plans/bp-026/**`,
`docs/findings/**`) — I cannot land the corresponding pin update myself.

**The exact fix needed** (computed and verified this session, at this worktree's HEAD post-Item-20):
```python
"phi_code": Interp(version_attr=("ops.code_sensor", "INTERPRETER_VERSION"),
                   sources=("ops/code_sensor.py", "ops/code_snapshot.py"),
                   version="1.1.0",
                   sha256="20be1ca5d483a51141377b23262a4b1041f7c2a94114120af20ced6abd4eab7b"),
```
(only `version` and `sha256` change; `version_attr`/`sources` unchanged). Verified via
`source_fingerprint(("ops/code_sensor.py", "ops/code_snapshot.py"))` computed against this
worktree's edited files — re-verify at merge time since the exact bytes (hence hash) will
shift slightly once this diff lands on `main` (whitespace/line-ending should be byte-identical
via a clean merge, but the orchestrator should recompute rather than trust this literal string
if the merge is non-trivial).

**A second, independent breakage from the SAME bump, same root cause, different file:**
`tests/unit/test_code_sensor.py::test_version_bump_makes_backfill_reproject_and_archive`
(bp-018's own version-bump test — it monkeypatches `INTERPRETER_VERSION` to `"2.0.0"`
mid-test to simulate a FUTURE bump, but hardcodes the literal string `"1.0.0"` twice — lines
147 and 149 — to assert the PRE-monkeypatch generation's version). Confirmed by direct run
(`uv run pytest tests/unit/test_code_sensor.py::test_version_bump_makes_backfill_reproject_and_archive -v`):
```
AssertionError: assert False
 +  where False = is_projected('77c5e7165302b22a46fe9cd824d1a5a3de842573', '1.0.0')
```
Because the REAL `INTERPRETER_VERSION` is now `"1.1.0"` (this session's bump), the
pre-monkeypatch generation lands at `"1.1.0"`, not the hardcoded `"1.0.0"` the test checks
for. **The exact fix:** replace both literal `"1.0.0"` occurrences with a reference to the
real base version — either `ops.code_sensor.INTERPRETER_VERSION` read BEFORE the
`monkeypatch.setattr` call (most robust — never drifts again on a future bump) or the literal
`"1.1.0"` (correct today, but will re-break on the NEXT bump exactly as this one did — the
same silent-drift shape the ratchet exists to prevent, just uncaught in a plain string
literal outside the ratchet's own pinned-file list). Recommend the robust form:
```python
base_version = ops.code_sensor.INTERPRETER_VERSION   # captured before the monkeypatch, top of test
...
assert obs.is_projected(sha, base_version)
...
assert [g["interpreter"] for g in chain] == [base_version, "2.0.0"]
```
This file (`tests/unit/test_code_sensor.py`) is ALSO outside bp-026's write_scope — not
touched by this session, same routing as the ratchet pin above.

**A third-order consequence, already covered by Item 21's own design — flagging for
completeness, not as new work:** a version bump technically makes every previously-projected
commit eligible for re-projection under `backfill_observations()`'s "supersedes" semantics
(bp-018, `ObservationHistoryStore` archives the superseded generation). Item 21's live
migration is ALREADY a full wipe + re-project of `reference_edges.sqlite` specifically — but
note `code_observations.sqlite` is a SEPARATE store this bump also touches (both stores are
corpus-class reset targets per `ops/lifecycle/launcher.py:519,524`). The dry-run in this
session's journal (`docs/build-plans/bp-026/journal.md`, Item 21 PREP) already exercises
`backfill_observations()` over BOTH stores together (they share the same `_project()` call),
so Item 21's existing plan already does the right thing — this is not an additional live
action, just documenting that the version bump and Item 21's wipe+reproject are the same act,
by design.

## Re-entry condition

Orchestrator lands BOTH fixes in the same merge/session as bp-026's Item 20 code:
1. `tests/unit/test_interpreter_versions.py`'s `INTERPRETERS["phi_code"]` pin update (the
   two-field diff above).
2. `tests/unit/test_code_sensor.py::test_version_bump_makes_backfill_reproject_and_archive`'s
   two hardcoded `"1.0.0"` literals (the diff above).

Neither file is in any currently-open plan's write_scope, so this is most naturally done as a
direct orchestrator hand-edit at bp-026's seal (mirroring how `docs/PROGRESS.md`/
`owner-questions.md` writes work — orchestrator, not builder). Re-verify the sha256 against the
actual merged bytes of `ops/code_sensor.py`/`ops/code_snapshot.py` on `main` rather than
trusting this finding's literal hash if the merge is non-trivial (e.g. conflicts, reordering).
Both fixes MUST land together — landing only the ratchet pin without the `test_code_sensor.py`
fix (or vice versa) leaves one of the two tests red.

## Routing

`spec-fidelity` — the builder (this session) diagnosed and partially resolved (bumped the
declaration, which IS in write_scope); the remaining two out-of-scope test fixes are routed to
the **orchestrator** to land at seal, since no active plan's write_scope currently covers
`tests/unit/test_interpreter_versions.py` or `tests/unit/test_code_sensor.py`. Not
`design | math | direction` — both are mechanical, pre-computed, small fixes with a clear
correct answer already stated above.
