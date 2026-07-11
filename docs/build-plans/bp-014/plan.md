---
type: build-plan
id: bp-014
status: proposed
design_ref:
  - docs/design-notes/agent-workflow.md   # the write-discipline design being RESTORED (not changed)
contract: builder
write_scope:
  - ".claude/hooks/_lib.py"
  - ".claude/hooks/*.sh"
  - "tests/**"
  - "docs/findings/**"
  - "docs/build-plans/bp-014/**"
session_budget: 1
cost:
  estimate: { model: fable, tokens: 350k }   # enforcement layer + fail-closed harness; blast-radius HIGH
  actual: null
depends_on: [bp-012, bp-013]     # SEQUENCING/SAFETY: do not modify enforcement hooks while builders run against them
parallelizable_with: []
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/findings/finding-0031.md   # origin (3 live manifestations 2026-07-11)
supersedes: null
superseded_by: null
warrant: finding-0031
---

# Build Plan — Worktree-aware ROOT resolution: make hook enforcement read the WORKTREE's active-plan pointer

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Promoted directly from `finding-0031` (worktree enforcement-state bleed) — a **codebase
bugfix, not a policy change.** The intended behavior already exists in the design:
`active_plan_path()`'s docstring states *"the pointer is worktree-local ... concurrent
worktrees never collide on enforcement state (design-note §4)"*, and `agent-workflow.md`'s
write-discipline design assumes per-plan capability. The CODE simply does not honor that
intent under worktree isolation. Because no policy changes, this is promoted as a bugfix plan
rather than through a new design note/amendment — **the owner's `proposed → ready` blessing
confirms that routing; if the owner deems the worktree-enforcement semantics a policy matter,
redirect at the gate to a design note first.**

## 1. Objective

A hook firing inside a git worktree resolves `ROOT` to **that worktree**, so it reads the
worktree's own `.claude/state/active-plan` — a delegated builder is enforced against ITS plan,
and a bare orchestrator session in the main checkout is never falsely guarded by a builder's
bled pointer. **Fail-closed:** any ambiguity resolves to the MORE restrictive scope; a stale
main-checkout pointer must never LOOSEN a worktree builder.

## 2. Context manifest

1. `docs/findings/finding-0031.md` — root cause + the 3 live manifestations (verbatim below).
2. `.claude/hooks/_lib.py` — `repo_root()` (prefers `CLAUDE_PROJECT_DIR`) → `ROOT`;
   `active_plan_path()` reads `os.path.join(ROOT, ".claude/state/active-plan")`.
3. `.claude/hooks/*.sh` — six wrappers, each: `ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse
   --show-toplevel 2>/dev/null || pwd)}"` (journal-gate, scope-guard, gate-guard,
   compaction-marker, session-brief, staleness-nudge).
4. `docs/build-plans/bp-010/journal.md` — the last hooks-layer change (A8), for the
   `_lib.py`/`--standalone` test conventions and the regression-harness shape to mirror.

## 3. Investigation & grounding

- **Q1 — why does `CLAUDE_PROJECT_DIR` win today?** Both `_lib.py:repo_root()` and every
  wrapper prefer the inherited env var; the harness sets it to the MAIN project dir even for
  worktree-isolated agents (finding-0031, confirmed 3× on 2026-07-11). So `ROOT`=main and the
  pointer read is main's.
- **Q2 — is CWD's git-toplevel the right ROOT?** In a worktree, `git rev-parse --show-toplevel`
  from the process CWD returns the WORKTREE path (each worktree is its own toplevel) — the
  correct enforcement root. The builder confirms at implementation whether the hook process's
  CWD is reliably inside the worktree (it is for tool-call hooks) — journal any case where CWD
  is ambiguous and default fail-closed.
- **Q3 — the fail-closed rule.** When CWD-toplevel and `CLAUDE_PROJECT_DIR` DISAGREE and the
  CWD-toplevel carries its own `.claude/state/`, prefer CWD-toplevel. When they agree, or the
  CWD-toplevel has no `.claude/state/`, keep current behavior. NEVER let a broad main-checkout
  pointer govern a narrow worktree write — the harness's key regression.

**Additional risks surfaced:** `.claude/state/` may be gitignored (runtime, untracked), so a
fresh worktree may lack `active-plan` until its own `/build` writes it — the resolution must
handle "worktree has no pointer yet" as *no active plan* (deny-by-absence for that worktree),
NOT fall back to main's pointer.

## 4. Reconciliation

- `_lib.py:active_plan_path()` docstring ("worktree-local ... never collide") → **banner:
  confirmation** — after this fix the docstring's claim is finally TRUE; no wording change
  needed, but add a one-line note that the ROOT resolution is what makes it hold.

## 5. Write scope

Prose mirror: `_lib.py`'s `repo_root()`/`ROOT`, the six wrapper `ROOT=` lines, a new
two-worktree regression test, findings, own dir. **Out of scope:** the enforcement POLICY
(write_scope semantics, the denylist, the blessing gates — all unchanged); any non-hook file;
the harness spawn machinery (harness-side, not ours). `.claude/hooks/**` is agent-writable
(not denylisted; bp-010 precedent) but every OTHER hook behavior stays byte-identical.

## 6. Interfaces pinned inline

Current (buggy) resolution — `_lib.py`:
```
def repo_root():
    root = os.environ.get("CLAUDE_PROJECT_DIR")
    if root: return root
    # else: git rev-parse --show-toplevel  (from CWD)
ROOT = repo_root()
```
Wrappers (×6): `ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"`

Target resolution (both `_lib.py` and wrappers, kept in lock-step): prefer the CWD git
worktree toplevel over `CLAUDE_PROJECT_DIR` **when they differ AND the CWD-toplevel contains
`.claude/state/`**; else current behavior. Shell sketch (wrappers):
```
CWD_TOP="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -n "$CWD_TOP" ] && [ "$CWD_TOP" != "$CLAUDE_PROJECT_DIR" ] && [ -d "$CWD_TOP/.claude/state" ]; then
  ROOT="$CWD_TOP"
else
  ROOT="${CLAUDE_PROJECT_DIR:-${CWD_TOP:-$(pwd)}}"
fi
```
`_lib.py:repo_root()` gets the equivalent, and stays the single source the wrappers echo.

## 7. Items

### Item 1 — worktree-aware ROOT in `_lib.py` + the six wrappers
- **Objective:** ROOT resolves to the CWD worktree per §6; `active_plan_path()` then reads the
  worktree's own pointer. `_lib.py` and wrappers kept in lock-step (identical rule).
- **Files:** `.claude/hooks/_lib.py`, the six `.claude/hooks/*.sh` wrappers.
- **Acceptance test:** every existing hook standalone still passes in the MAIN checkout
  (`bash .claude/hooks/<name>.sh --standalone ...` unchanged); `uv run pytest` hook tests green.
- **Falsifier:** in a worktree, a hook still reads the main checkout's pointer.
- **Invariant(s):** in the main checkout with `CLAUDE_PROJECT_DIR` set, behavior is
  byte-identical to today (no regression for the common case).
- **Touches stored data?** no **Parallelizable?** no **Depends on:** none

### Item 2 — the two-worktree regression harness (the fail-closed proof)
- **Objective:** an automated test creating two throwaway worktrees with DIFFERENT active plans
  and asserting enforcement is worktree-local in BOTH directions.
- **Files:** new `tests/` file (fixtures create temp worktrees + state pointers).
- **Acceptance test:** (a) DENY — a write to worktree-B's scope from worktree-A is denied;
  (b) ALLOW — a write to worktree-A's OWN scope succeeds even when main's pointer names a
  different plan; (c) **THE UNSAFE DIRECTION — a worktree with a NARROW plan is NOT loosened by
  a BROAD main-checkout pointer** (fail-closed); (d) a worktree with no pointer yet = no active
  plan (not a fallback to main).
- **Falsifier:** the harness passes while (c) is actually broken (the loosening slips through).
- **Invariant(s):** the harness itself must FAIL against the pre-fix code (prove it catches the
  bug — run it on the unpatched `_lib.py` first and show red, per the falsifier-demo discipline).
- **Touches stored data?** no (temp worktrees only) **Parallelizable?** no **Depends on:** Item 1

## 8. Math carried explicitly

N/A — no mathematical object (path resolution + a capability comparison).

## 9. Non-goals

Changing any enforcement POLICY (scope semantics, denylist, blessing gates); fixing the harness
env-var bleed itself (harness-side — we adapt to it, we don't change it); the delegate-mode A9
amendment (separate, agent-workflow.md).

## 10. Stop-and-raise conditions

The fix cannot make the unsafe direction (§7 Item 2c) provably fail-closed without changes
outside `.claude/hooks/**` (raise — enforcement must not ship half-safe); the CWD is NOT
reliably inside the worktree for tool-call hooks (Q2 assumption breaks — park, finding);
modifying the ROOT rule regresses any existing hook's main-checkout behavior (spec-defect).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
| --- | --- | --- | --- |
| resolution source | CWD `git rev-parse --show-toplevel` | env-var patch in the harness spawn (not ours to change) | harness gains a worktree-aware `CLAUDE_PROJECT_DIR` upstream |

## 12. Dependency & ordering summary

**Runs AFTER bp-012 and bp-013 have merged** — not a logical dependency but a SAFETY one: the
enforcement hooks must not change while delegated builders are running against them. Item 1 →
Item 2. First unit after the current queue clears; ideally a design-tier session given the
fail-closed blast radius.
