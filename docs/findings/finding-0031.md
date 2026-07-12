---
type: finding
id: finding-0031
status: resolved
ftype: discovery
origin_plan: bp-007
route: orchestrator
created: 2026-07-11
updated: 2026-07-12
links:
  - docs/build-plans/bp-007/journal.md      # the episode (documented workaround)
  - .claude/skills/delegate/SKILL.md        # the mode this infrastructure serves
  - docs/build-plans/bp-014/plan.md         # the fix
resolution: FIXED by bp-014 (sealed 2026-07-12, CI green run 29185014622) — worktree-aware ROOT in `_lib.py:repo_root()` + all six hook wrappers; two-worktree regression harness red→green with the fail-closed case (c) non-vacuous. Promoted 2026-07-11 → bp-014, owner-directed.
---

# finding-0031 — Enforcement state bleeds across worktrees: the active-plan pointer is not worktree-local in practice

## What

During the first PARALLEL delegated builds (bp-007 building while the orchestrator ran
bp-010 in the main checkout), bp-007's builder found its Edit/Write tool calls being
denied against **bp-010's** write_scope: the main checkout's `.claude/state/active-plan`
pointer governed the WORKTREE session's enforcement. Root cause: hook wrappers resolve
`ROOT` as `${CLAUDE_PROJECT_DIR:-git toplevel}`, and the harness sets
`CLAUDE_PROJECT_DIR` to the MAIN project directory even for worktree-isolated agents —
so `active_plan_path()` reads main's pointer, not the worktree's. The design intent
("the pointer is worktree-local … concurrent worktrees never collide on enforcement
state", `_lib.py` docstring) holds for the file layout but not for the env resolution.

The builder worked around it via Bash-mediated writes (in-scope by eye, documented in
its journal); the condition self-resolved when the orchestrator's bp-010 session
cleared the pointer.

## Why it matters

The delegate mode (owner rule 2026-07-11) makes parallel worktree builders the normal
case. Cross-bleed means: (a) a builder can be wrongly DENIED (this episode — friction,
Bash workarounds erode the pre-hoc layer's value), and (b) potentially wrongly ALLOWED
(a main-checkout pointer with a broad scope would loosen a worktree builder — the unsafe
direction). The pre-hoc guard's per-plan capability model silently degrades to
whichever checkout wrote the pointer last.

## Recommended direction (route: orchestrator)

Make ROOT resolution worktree-aware in the hook wrappers: prefer the PROCESS's actual
working tree (`git rev-parse --show-toplevel` from CWD) over the inherited
`CLAUDE_PROJECT_DIR` when they disagree AND `.claude/state/` exists in the working tree;
or have the Agent-tool spawn set `CLAUDE_PROJECT_DIR` to the worktree path. Small,
hooks-scoped fix (bp-010's surface family); verify with a two-worktree harness case.

## Re-entry

Parked until the next hooks-scoped plan (or fold into A7's implementation plan). Trigger
that reopens immediately: any parallel-builder denial or allowance traceable to a
pointer outside its own worktree.

## Promotion (2026-07-11) — owner-directed, -> bp-014

The owner directed this be handled ("you keep bringing it up, so it must be important").
**Three live manifestations on 2026-07-11**, all one root cause (hooks resolve `ROOT` to
`CLAUDE_PROJECT_DIR` = the MAIN checkout even for worktree agents, so `active_plan_path()`
reads main's pointer, not the worktree's):
1. **bp-007 builder** — its in-scope Edit/Write DENIED against another plan's scope (original).
2. **Orchestrator Stop-gate FALSE-GUARD** — a running builder's `/build` set MAIN's pointer,
   so the bare orchestrator session's `journal-gate` guarded a plan it wasn't building (~5×
   this session; the recurring mtime-touch tax).
3. **bp-011 builder** — its OWN in-scope writes denied by `scope-guard` (builder's finding-0033),
   worked around via standalone-check-then-write.

**Promoted to `bp-014` (status `proposed`)** — a codebase bugfix restoring the stated
worktree-local design (`active_plan_path()` docstring + design-note §4), changing no policy.
The fix is pinned there (worktree-aware ROOT: prefer the CWD `git rev-parse --show-toplevel`
over `CLAUDE_PROJECT_DIR` when they differ and the CWD-toplevel has its own `.claude/state/`),
with a two-worktree regression harness whose critical case is the **fail-closed / unsafe**
direction (a broad main pointer must NOT loosen a narrow worktree builder).

**Sequencing:** bp-014 `depends_on: [bp-012, bp-013]` — enforcement hooks must not change
while delegated builders are running against them. First unit after the current queue clears.
**Owner action to approve:** the `proposed -> ready` blessing by hand (owner-only gate).

## Resolution (2026-07-12, /triage) — FIXED, verified

bp-014 landed and sealed 2026-07-12: `_lib.py:repo_root()` (and all six wrappers, lock-step)
now prefers the CWD git-worktree toplevel over `CLAUDE_PROJECT_DIR` when they differ AND the
CWD-toplevel carries its own `.claude/state/` — realpath-normalized both sides, fail-closed.
All three 2026-07-11 manifestations are covered, and the two-worktree regression harness
(`tests/integration/test_worktree_enforcement.py`, 4 cases) proved red→green with the UNSAFE
direction (a broad main pointer loosening a narrow worktree builder) pinned non-vacuously.
CI five-job attestable green: run 29185014622. A delegated builder is now enforced against ITS
OWN worktree plan; the bp-016 ∥ bp-017 lane opens on sound enforcement, not diff-scrutiny alone.
Corroborating manifestation finding-0033 closes with this same fix.
