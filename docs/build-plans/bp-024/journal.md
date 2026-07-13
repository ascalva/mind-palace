# Journal — bp-024 (cross-checkout state bleed flag at Stop gate)

## 2026-07-13 — session start, grounding

- Confirmed `docs/build-plans/bp-024/plan.md` front-matter `status: ready` at
  session start. Set `.claude/state/active-plan` (worktree-local, relative
  path) → `docs/build-plans/bp-024/plan.md`. Flipped `status: ready →
  in-progress`, `updated: 2026-07-12 → 2026-07-13` (non-blessing edit).
- Re-grounded `_lib.py` at HEAD (plan's line numbers had drifted slightly):
  - `cmd_stop_audit` at `:554` (as pinned) — checks (a)/(b) at `:558-603`,
    (b2) at `:605-622`, (c) at `:624-644`, A3/`_untracked_blessing` at
    `:646-662`, then `if reasons:` join at `:664`.
  - `repo_root()` at `:62-87` (spec said `:62-80`; body is now 26 lines, not
    19 — no semantic change, just grew a bit since the plan was written).
  - `active_plan_path()` at `:280-298` (spec said `:280-300`, off by 2 —
    trivial drift). Confirmed its normalization: bare id `"bp-022"` →
    `docs/build-plans/bp-022/plan.md`; tolerates a path directly; does NOT
    require the path to exist on THIS worktree's ROOT before returning it
    (line 298 returns `val` either way — existence only gates a *second*
    fallback branch that isn't taken here). This matters for (d): the
    normalized form is directly comparable to a foreign-checkout's
    normalized pointer without touching this worktree's filesystem.
  - Found the existing `_cwd_toplevel()` helper at `:45-59` — already does
    exactly what the spec's `_cwd_worktree_top()` describes (realpath'd git
    toplevel of CWD, or None, on any subprocess failure). Reused it directly
    rather than adding a duplicate helper (spec §6 note: "pinned BEHAVIOR is
    what binds, not the factoring").
  - `journal-gate.sh:11-29` — confirmed `_CWD_TOP`/`_ENV_TOP` naming/
    resolution pattern (informational only; plan's write_scope explicitly
    excludes the `.sh`, and I did not touch it).

## Item 14 — the (d) cross-checkout bleed check + its falsifier test

- **Implementation** (`.claude/hooks/_lib.py`):
  - Inserted the `(d)` block verbatim per plan §6(a), between the A3
    `_untracked_blessing` block and the `if reasons:` join in
    `cmd_stop_audit`. Used the existing `_cwd_toplevel()` in place of the
    spec's placeholder name `_cwd_worktree_top()` (same behavior, already
    present in the file — avoids a duplicate).
  - Added one new private helper, `_normalize_plan_ref(val)`, placed
    immediately before `plan_write_scope()` (right after
    `active_plan_path()`). It mirrors `active_plan_path()`'s bare-id → path
    normalization (`rel()`-style separator/slash cleanup, then append
    `docs/build-plans/<id>/plan.md` if not already `.md`-suffixed) but
    **never resolves against this worktree's `ROOT`** — the value being
    normalized may name a plan in a DIFFERENT checkout (main's pointer), and
    coercing it onto this worktree's filesystem via `ROOT` would be wrong.
    This is the one deviation from "inline only" the spec allowed for
    ("plus a small private helper if cleaner") — needed because
    `active_plan_path()` itself always resolves through `ROOT`/reads from
    disk, so it can't be reused directly to normalize an arbitrary string.
  - Behavior matches §6(a) exactly: worktree-only (`env_top` present, `cwd_top`
    resolves, and they differ after realpath), read-only (opens main's
    pointer file for reading only — never writes), fail-open (bare
    `try/except Exception: pass` wrapping the whole block).
  - Verified the no-worktree byte-identical invariant manually: running
    `_lib.py stop-audit` with `CLAUDE_PROJECT_DIR=$(pwd)` (env-top == cwd-top)
    produces the exact same `(a)` reason as before the change (journal
    missing, since the journal didn't exist yet at that check-in point) — the
    `(d)` guard's `!=` comparison short-circuits and appends nothing.

- **Test** (`tests/integration/test_worktree_enforcement.py`): this file
  already existed (bp-014's two-worktree `scope-guard.sh` harness, cases
  a-d for the PRE-HOC guard — unrelated to this plan's `(d)`, just a name
  collision in lettering). Appended a new fixture (`bleed_fixture`) + 4 new
  tests for the POST-HOC `cmd_stop_audit` `(d)` check, reusing the existing
  file's `_git()`/`_plan()`/`_HOOKS_SRC` helpers:
  - `test_stop_audit_flags_main_checkout_pointer_bleed` — positive case:
    main's pointer == this worktree's own plan (`bp-024`) → `(d)` fires.
  - `test_stop_audit_bleed_control_1_empty_main_pointer` — main's pointer
    empty → no `(d)`.
  - `test_stop_audit_bleed_control_2_different_plan_no_false_positive` —
    main's pointer names a DIFFERENT plan (`bp-other`) → no `(d)` (the
    zero-false-positive guarantee, §3 Q3).
  - `test_stop_audit_bleed_control_3_not_a_worktree_byte_identical` — run
    from `main` itself (env-top == cwd-top) even though main's own pointer
    happens to equal the value under test → no `(d)`.
  - Fixture gives both plans a fresh journal.md (mtime after HEAD commit) so
    check `(a)` (journal staleness) never fires and doesn't muddy the
    `(d)`-only assertions — each test asserts only presence/absence of the
    `"(d)"` substring, not the full BLOCK/ALLOW line, so it's robust to
    unrelated reasons.
  - Result: `uv run pytest -v tests/integration/test_worktree_enforcement.py`
    → 8 passed (4 pre-existing bp-014 cases + 4 new bp-024 cases).

## Zero-false-positive predicate (§10 stop-and-raise check)

- Confirmed the predicate IS meetable: `_normalize_plan_ref()` and
  `active_plan_path()` produce the SAME normalized form
  (`docs/build-plans/<id>/plan.md`) for both a bare id and a path input, so
  `_normalize_plan_ref(main_val) == plan` is a sound, false-positive-free
  comparison. No finding needed for §10's fallback condition — the predicate
  held.

## Green gate

- `uv run ruff check .` — clean.
- `uv run mypy core agents eval ops scheduler scripts` — clean (0 errors),
  same as baseline (this plan's write_scope touches none of these dirs'
  type-checked surface — `.claude/hooks/_lib.py` and `tests/` are outside
  this leg's target list).
- `uv run mypy` (argless, leg 3) — baseline pinned error count 69
  (finding-0029); confirmed unchanged by this plan's diff (see final report).
- `uv run python -m ops.type_gate` — clean.
- `uv run pytest -q` — full suite green (see final report for count).
- `python3 .claude/hooks/_lib.py stop-audit` (from worktree root, real
  `CLAUDE_PROJECT_DIR`) — confirmed ALLOW-path behavior unaffected by the
  new `(d)` block once the journal was fresh and no out-of-scope changes
  existed; checks (a)/(b)/(b2)/(c) unchanged.

## Side-effect audit

- `git status --porcelain -uall` at completion: only
  `.claude/hooks/_lib.py`, `tests/integration/test_worktree_enforcement.py`,
  `docs/build-plans/bp-024/plan.md`, `docs/build-plans/bp-024/journal.md` —
  all inside write_scope. `.claude/state/active-plan` is worktree-local and
  gitignored (not part of the tracked diff).

## Findings

- None filed. The §10 stop-and-raise condition (predicate unmeetable) did
  not trigger — `_normalize_plan_ref`/`active_plan_path` normalize
  identically, so the zero-false-positive predicate from §3 Q3 held exactly
  as specified. No spec-fidelity or design gaps surfaced.

## Status at handoff

Item 14 (the plan's only item) is COMPLETE: implementation + falsifier test
green, green gate run in full (all 5 legs green; argless mypy = 69,
matching the pinned baseline), side-effect audit clean. Full suite
(`uv run pytest -q`): 985 passed, 4 skipped→7 skipped (env-dependent
`tests/e2e/*_live.py` require a live local Ollama server, not present in
this sandbox — pre-existing/environmental, unrelated to this plan's scope);
`--ignore=tests/e2e`: 972 passed, 4 skipped, zero failures.

Committed on the worktree branch: `ce692f0` — "feat(hooks): stop-audit (d)
— flag cross-checkout state bleed (finding-0051 fix 2)". 4 files: `_lib.py`,
`test_worktree_enforcement.py`, `bp-024/plan.md`, `bp-024/journal.md`
(new). All inside write_scope; verified via `git diff --stat` before commit.

No findings filed — the §10 stop-and-raise predicate held (see above), and
no codebase/spec-fidelity gap surfaced during grounding (only trivial line-
number drift, noted above, no semantic change).

Ready for orchestrator to flip `docs/build-plans/bp-024/plan.md`
`in-progress → complete` and finding-0051 `→ promoted`, then sequence the
merge (both out of this builder's write_scope).

## SEAL (orchestrator, 2026-07-13)

Merged into main via `--no-ff` at the wave boundary (bp-023/024/025 landed sequentially, disjoint scopes, zero conflicts). Combined green gate on the merged tree: ruff clean · targeted mypy clean · **argless mypy == 69** (finding-0038 class clear) · type_gate OK · CI-equivalent `pytest -m "not live …"` **977 passed, 0 failed**. Status flipped `in-progress → complete`. **Usage (measured, harness): sonnet, 64929 tok / 63 calls / ~22 min = 1.08×** of estimate. Item 14 (the (d) cross-checkout bleed check) landed with a rigorous 3-control falsifier over a real git worktree. Enforcement blast-radius; scrutinized hardest; no finding needed.
