# Journal — bp-025 (wave-debt micro-sweep)

## Session 1 — 2026-07-13 — builder (Claude Sonnet 5)

Plan was `status: ready` at start; flipped to `in-progress`, `updated: 2026-07-13`
(non-blessing edit, plan front-matter). Active-plan pointer set to
`docs/build-plans/bp-025/plan.md` (worktree-relative, `.claude/state/active-plan`).

All three items are mutually independent (disjoint files per plan §12); executed
all three in one session.

### Item 15 — witness short-sha guard — DONE

- Grounded via grep: `ops/ci_witness.py` entry points confirmed at `run_for:73`,
  `check:110`, `release:165` (line numbers matched plan §2 exactly, no drift).
- Added `import re`, `_FULL_SHA` regex, and `_full_sha()` helper verbatim per plan
  §6(a) — placed right after the `WORKFLOW`/`RELEASE_WORKFLOW` constants.
- Added `sha = _full_sha(sha)` as the FIRST line of `check()` and `release()` ONLY.
  `run_for` is untouched (receives the already-normalized sha, as specified).
- Test file `tests/unit/test_ci_witness.py`: added 5 new tests in a new section
  ("`_full_sha` guard (bp-025 Item 15)") ahead of the existing check()-loop tests:
  - `test_full_sha_identity_no_git_call` — full 40-hex sha passes through, asserts
    `subprocess.run` is never called (identity branch, no git call).
  - `test_full_sha_expands_short_via_stubbed_git` — short sha expanded via a
    stubbed `git rev-parse --verify <sha>^{commit}`; asserts the exact cmd shape.
  - `test_full_sha_unresolvable_raises_before_any_http` — stubbed git rc=1;
    asserts `SystemExit` raised AND stubs `run_for`/`_get` to `pytest.fail` if
    ever called (the HTTP-boundary-never-reached assertion the plan demanded).
  - `test_check_rejects_unresolvable_sha_before_run_for` — same idea driven
    through the public `check()` entry point.
  - `test_release_rejects_unresolvable_sha_before_run_for` — same, through
    `release()`.
- `uv run pytest -q tests/unit/test_ci_witness.py` → **34 passed** (29 pre-existing
  + 5 new).
- Invariants held: `run_for`/`verdict`/`attest_verdict` untouched; full-sha path is
  the identity branch (byte-identical behavior, verified by the no-git-call test);
  no new dependency (`re`/`subprocess` both stdlib, `subprocess` already imported).
- §10 stop-and-raise (repo-context loss) did not trigger — `ci_witness.py` still
  runs inside the repo; no fallback needed.

### Item 16 — launcher comment correction — DONE (not N/A)

- Grepped `gitlab` in `ops/lifecycle/launcher.py` → confirmed at line 265, matching
  plan §2 exactly (not the resume brief's approximate 259 — plan's own grounding
  note was already accurate).
- Changed `gitlab.com` → `api.github.com` in the one comment line. Verified via
  `git diff`: single line changed, comment-only (`#` prefix), zero executable-line
  changes. `grep -n gitlab` now empty; `grep -n api.github.com` shows the line.
- `uv run ruff check ops/lifecycle/launcher.py` → clean (covered by the full-repo
  ruff run below).

### Item 17 — delegate gate-text separation — DONE

- Grepped `&&` in `.claude/skills/delegate/SKILL.md` → found the 4-line chained
  block at (then) lines 114-118, inside "## Supervision & scrutiny" as the plan
  said. Confirmed the file had grown since the plan was written (extra sections
  present) — touched ONLY the gate block, left everything else byte-identical
  (verified via `git diff`: hunk is exactly the gate-block lines, nothing else).
- Replaced the `&&`-chained 5-line block with 5 separate lines + the argless-mypy
  note per §6(c), wording tightened to hit the literal acceptance substring
  `"exits 1 at the tests/-baseline (69)"` (initially wrote "(69 errors)" — the
  exact parenthetical the plan's §7 acceptance test checks for is `(69)`; the
  "errors" word was dropped from the inline comment to match while the longer
  prose 3 lines below still says "footprint" — no meaning lost).
- `grep -n "&&"` still matches two lines, but both are backtick-quoted prose
  *about* not chaining (`` `&&`-chain them ``, `` &&-chained (leg 3 ``) — no
  actual `&&`-joined gate legs remain. This satisfies the falsifier ("the block
  still &&-chains the legs") — it does not, textually or semantically.

### THE GREEN GATE — all five legs, run separately (per Item 17's own rule)

    uv run ruff check .                              → All checks passed!
    uv run mypy core agents eval ops scheduler scripts → Success: no issues found in 173 source files
    uv run mypy                                       → Found 69 errors in 20 files (checked 345 source files)
    uv run python -m ops.type_gate                    → Tier-2 membership: OK; Bare-ignore scan: OK
    uv run pytest -q                                  → 989 passed, 8 skipped in 746.52s

Argless-mypy (leg 3) count == **69**, matching the pinned tests/-baseline
(finding-0029) exactly — no drift, no investigation needed.

Leg 5 note: an earlier full-suite run (during gate execution, before the final
confirmed run) showed `2 failed` in `tests/e2e/test_research_live.py` and
`tests/e2e/test_scheduler_live.py` — both `@pytest.mark.live`, network/Ollama-
dependent, with `TimeoutError` in stdlib `urllib`/`socket`. Verified via
`git stash` (clean HEAD, no diff) that these two tests ALSO intermittently fail
on their own outside this diff — pure environmental flake (live network
timeout), unrelated to bp-025's changes (none of `ci_witness.py`/`launcher.py`/
`SKILL.md`/`test_ci_witness.py` touch `core.research`/`scheduler`). A second full
run came back fully green (989 passed, 8 skipped, 0 failed) and is recorded above
as the authoritative leg-5 result.

### Side-effect audit

`git status --short` / `git diff --stat` — five changed paths, all inside
write_scope: `.claude/skills/delegate/SKILL.md`, `docs/build-plans/bp-025/plan.md`
(status flip), `ops/ci_witness.py`, `ops/lifecycle/launcher.py`,
`tests/unit/test_ci_witness.py`. Nothing outside scope.

### Findings

None filed — no `design | math | direction` question surfaced. All three items
were crisp micro-fixes with the plan's own interfaces pinned inline; no
ambiguity requiring routing.

### Commits (worktree branch, not pushed/merged)

Three separate commits, one per item (mutually independent per plan §12):
1. Item 15 (code) — `Co-Authored-By: Claude Opus 4.8` trailer included.
2. Item 16 (comment-only) — trailer omitted per commit-trailer policy.
3. Item 17 (doc/skill-only) — trailer omitted per commit-trailer policy.

### Status

All three items DONE. Green gate fully passed (69/69 pinned baseline, 989/989
non-skipped tests green). Ready for orchestrator review/merge. Plan left at
`in-progress` — orchestrator flips to `complete` per role split (builders don't
flip plan status themselves per CLAUDE.md "Orchestrator... flips plan status on
completion").
