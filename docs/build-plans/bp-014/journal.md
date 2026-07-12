# BP-014 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## 2026-07-12 — Items 1, 2, 3 all DONE (single builder session)

Builder worktree: `.claude/worktrees/agent-a6db291b0d929461f`, branch off main HEAD 8432370.
Worktree pointer set to `bp-014` (`.claude/state/active-plan`) — hygiene; live hooks resolve
from main's `CLAUDE_PROJECT_DIR` and main's pointer is empty (permissive), so my in-scope
writes flowed and my hook edits are INERT until merged (grounding note 2). All verification was
done standalone (`bash .claude/hooks/<name>.sh --standalone …`) and `uv run pytest`, never via
live hooks.

### Item 1 — worktree-aware ROOT (DONE)
- `_lib.py`: split `repo_root()` into `_cwd_toplevel()` (realpath'd CWD git-toplevel) + a
  worktree-aware `repo_root()`. Rule: prefer CWD-toplevel over `CLAUDE_PROJECT_DIR` when they
  DIFFER (both realpath-normalized) AND CWD-toplevel has `.claude/state/`; else old behavior
  (env → cwd-top → cwd). Updated `active_plan_path()` docstring per §4 reconciliation (the
  worktree-local claim now holds *because* ROOT is the worktree).
- Six wrappers: replaced the identical `ROOT="${CLAUDE_PROJECT_DIR:-…}"` line with the identical
  worktree-aware block in each (scope-guard, journal-gate, gate-guard, compaction-marker,
  session-brief, staleness-nudge). Uses `_wt_norm()` (`pwd -P`) to realpath BOTH sides so
  `/tmp`→`/private/tmp` symlink drift can't spoof the compare (grounding note 1). Kept in
  lock-step with `_lib.py`.
- **No-regression evidence (agree case, CLAUDE_PROJECT_DIR==CWD-top):** scope-guard decisions
  pristine-vs-patched byte-identical — `core/x.py`→rc0(ALLOW), `CONSTITUTION.md`→rc2(DENY),
  `eval/golden/a.txt`→rc2(DENY), `docs/other.py`→rc2(DENY) on both. Wrapper ROOT echoes
  identical in agree/unset/symlink cases. bp-010 A8 acceptance harness: 11/11 PASS.

### Item 2 — two-worktree regression harness (DONE, red→green proven)
- New `tests/integration/test_worktree_enforcement.py` (marked `integration`). Self-contained:
  builds a temp MAIN repo (2 committed plans: bp-A narrow=`edge/**`, bp-B broad=`core/**`, empty
  main pointer) + 2 real `git worktree`s each with its OWN `.claude/state/active-plan`. Runs
  `scope-guard.sh --standalone` from each worktree CWD with `CLAUDE_PROJECT_DIR`=MAIN (the exact
  finding-0031 bleed). Four cases: (a) DENY cross-worktree, (b) ALLOW own-scope despite main
  pointer, (c) THE UNSAFE DIRECTION — narrow worktree NOT loosened by broad main pointer, (d) no
  pointer = no plan (NOT main-fallback; denylist still binds).
- Hooks source is overridable via `BP014_HOOKS_SRC` env (default = repo hooks) so the same file
  runs the falsifier-demo against pristine hooks.
- **RED (pristine HEAD hooks, `BP014_HOOKS_SRC=<scratch>/pristine-hooks`):** `3 failed, 1 passed`
  — (a), (c), (d) FAIL; (b) passes vacuously (empty main pointer ⇒ orchestrator ALLOW pre-fix).
  The critical case (c) unsafe-direction goes RED, proving the harness catches the loosening.
- **GREEN (patched hooks, default):** `4 passed`.

### Item 3 — resume-brief auto-surface (DONE)
- `session-brief.sh`: added, before the `python3 "$LIB" brief` call, `_RB="$ROOT/.claude/state/
  resume-brief.md"; if [ -r "$_RB" ]; then cat "$_RB"; echo; fi`. Bash-side (cmd_brief stays
  pure), resolved under the Item-1 worktree-aware ROOT, fail-open (`-r` guard).
- **Evidence:** present → resume-brief printed ABOVE the `═══ SESSION BRIEF ═══` block; absent →
  `diff` vs pristine session-brief output = IDENTICAL; unreadable (chmod 000) → exit 0, no
  HOOK-FAILURE, brief still emits; session-baseline still recorded.
- finding-0035 annotated **partially-addressed** (rec 3 done; recs 1+2 route at /triage). Status
  left `routed`, NOT flipped to resolved. Did NOT touch `docs/templates/` or `.claude/skills/`
  (out of scope).

### Opportunistic fold (§5) — write_scope trailing-comment parser (DONE)
- `_lib.py:_scalar()`: a QUOTED scalar now honors its closing quote and discards any trailing
  inline comment (`"path"  # note` → `path`). UNQUOTED scalars keep their `#` (so `id: bp-Z #…`
  and `status: ready#x` are untouched — `_normalize_status` still owns status). Fixes the
  oq-0013 mis-parse bp-012's builder worked around. Verified: quoted-with-comment, spaces,
  unquoted, flow-list, and `#`-in-unquoted all parse correctly; bp-010 A8 (11/11) unaffected.

### Test gate
- `tests/unit` + `tests/integrity`: 348 passed. New harness: 4 passed. ruff clean; ast OK.
- Integration suite collects cleanly (390 tests incl. my 4).

### What's next
All three items + the opportunistic fold are complete and green. Nothing parked, no findings
filed (both items resolved cleanly; no design/direction question surfaced). Ready for orchestrator
diff review + merge. Commits on this branch (see below). Do NOT push — orchestrator runs CI.

---

## Markers
