"""Two-worktree regression harness — enforcement state is worktree-LOCAL (bp-014).

Warrant: finding-0031 — the hook wrappers resolved ROOT to ``CLAUDE_PROJECT_DIR``
(the MAIN checkout, which the delegate harness sets even for worktree-isolated
agents), so ``active_plan_path()`` read main's ``.claude/state/active-plan`` pointer
instead of the worktree's own. A delegated builder was enforced against the WRONG
plan's write_scope — wrongly denied (friction) or, the unsafe direction, wrongly
ALLOWED (a broad main pointer loosening a narrow worktree builder).

The fix (bp-014 Item 1): ``repo_root()`` and every wrapper's ``ROOT=`` line prefer
the CWD git-worktree toplevel over ``CLAUDE_PROJECT_DIR`` when they differ AND the
CWD-toplevel carries its own ``.claude/state/``. This harness proves it, in BOTH
directions, from a fully self-contained throwaway git repo with two real worktrees.

Falsifier discipline (§7 Item 2 invariant): this harness MUST go RED against the
pre-fix ``_lib.py``/wrappers — the loosening (case c) slips through. Run it once
against unpatched hooks to see the red, then against the patched hooks to see green.
The pre-fix red is captured in the bp-014 journal.

Four required cases:
  (a) DENY cross-worktree   — a write to worktree-B's scope from worktree-A denied.
  (b) ALLOW own-scope       — worktree-A writes its OWN scope even though MAIN's
                              pointer names a different plan.
  (c) UNSAFE DIRECTION      — a worktree with a NARROW plan is NOT loosened by a
                              BROAD main-checkout pointer (fail-closed). THE case.
  (d) NO POINTER = NO PLAN  — a worktree lacking its own pointer resolves to NO
                              active plan (deny-by-absence), NOT a fallback to main.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

# The hooks under test default to this repo's `.claude/hooks`. Override via
# BP014_HOOKS_SRC to run the harness against a pristine (pre-fix) hook set — the
# falsifier-demo path that proves the harness goes RED against the unpatched code
# (§7 Item 2 invariant). Normal `pytest` runs use the real, patched hooks.
_HOOKS_SRC = Path(
    os.environ.get(
        "BP014_HOOKS_SRC",
        str(Path(__file__).resolve().parents[2] / ".claude" / "hooks"),
    )
)


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )


def _plan(plan_id: str, write_scope: list[str]) -> str:
    ws = "\n".join(f'  - "{p}"' for p in write_scope)
    return (
        "---\n"
        "type: build-plan\n"
        f"id: {plan_id}\n"
        "status: in-progress\n"
        "contract: builder\n"
        "write_scope:\n"
        f"{ws}\n"
        "---\n\n"
        f"# {plan_id}\n"
    )


@pytest.fixture
def two_worktrees(tmp_path: Path):
    """A self-contained MAIN repo + two worktrees (A, B) with DIFFERENT active
    plans, each carrying its own ``.claude/state/active-plan``. Returns a dict with
    the paths and a ``scope`` runner that invokes ``scope-guard.sh --standalone``
    from a given worktree CWD with ``CLAUDE_PROJECT_DIR`` set to MAIN (the exact
    bleed condition finding-0031 describes)."""
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-q", "-b", "main")
    _git(main, "config", "user.email", "t@t")
    _git(main, "config", "user.name", "t")

    # Hook scripts + lib, copied from THIS worktree (the code under test).
    (main / ".claude" / "hooks").mkdir(parents=True)
    for f in _HOOKS_SRC.glob("*.py"):
        shutil.copy(f, main / ".claude" / "hooks" / f.name)
    for f in _HOOKS_SRC.glob("*.sh"):
        shutil.copy(f, main / ".claude" / "hooks" / f.name)

    # Two plans committed to the shared tree; worktrees select via their pointers.
    #   bp-A: NARROW  — may write only edge/**
    #   bp-B: BROADER — may write core/**
    # MAIN is orchestrator posture (empty pointer): its own state must never govern
    # a worktree.
    plans = main / "docs" / "build-plans"
    (plans / "bp-A").mkdir(parents=True)
    (plans / "bp-B").mkdir(parents=True)
    (plans / "bp-A" / "plan.md").write_text(_plan("bp-A", ["edge/**"]))
    (plans / "bp-B" / "plan.md").write_text(_plan("bp-B", ["core/**"]))
    (main / ".claude" / "state").mkdir(parents=True)
    (main / ".claude" / "state" / "active-plan").write_text("")  # main: no plan
    (main / "CONSTITUTION.md").write_text("kernel\n")
    _git(main, "add", "-A")
    _git(main, "commit", "-qm", "fixture: two plans + hooks")

    wt_a = tmp_path / "wt-a"
    wt_b = tmp_path / "wt-b"
    _git(main, "worktree", "add", "-q", "-b", "br-a", str(wt_a))
    _git(main, "worktree", "add", "-q", "-b", "br-b", str(wt_b))

    # Each worktree gets its OWN state/active-plan (gitignored, per-worktree).
    for wt, pid in ((wt_a, "bp-A"), (wt_b, "bp-B")):
        (wt / ".claude" / "state").mkdir(parents=True, exist_ok=True)
        (wt / ".claude" / "state" / "active-plan").write_text(pid)

    def scope(cwd: Path, file_path: str, project_dir: Path | None = None) -> int:
        """Run scope-guard.sh --standalone from `cwd`, with CLAUDE_PROJECT_DIR set
        to `project_dir` (default: MAIN — the bleed condition). Returns the exit
        code: 0=ALLOW, 2=DENY."""
        env = dict(os.environ)
        env["CLAUDE_PROJECT_DIR"] = str(project_dir if project_dir is not None else main)
        r = subprocess.run(
            ["bash", str(cwd / ".claude" / "hooks" / "scope-guard.sh"), "--standalone", file_path],
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
        )
        return r.returncode

    return {
        "main": main,
        "wt_a": wt_a,
        "wt_b": wt_b,
        "scope": scope,
    }


@pytest.mark.integration
def test_a_deny_cross_worktree(two_worktrees):
    """(a) DENY — worktree-A (scope edge/**) writing worktree-B's core/** is denied,
    even though CLAUDE_PROJECT_DIR points at MAIN."""
    scope = two_worktrees["scope"]
    assert scope(two_worktrees["wt_a"], "core/secret.py") == 2, (
        "worktree-A must NOT be able to write worktree-B's core/** scope"
    )


@pytest.mark.integration
def test_b_allow_own_scope_despite_main_pointer(two_worktrees):
    """(b) ALLOW — worktree-A writes its OWN edge/** scope, even though MAIN's pointer
    is empty (orchestrator posture would ALLOW everything not denylisted) and B's
    worktree names a different plan. The read must be worktree-A's own pointer."""
    scope = two_worktrees["scope"]
    assert scope(two_worktrees["wt_a"], "edge/ok.py") == 0, (
        "worktree-A must be allowed to write its own edge/** scope"
    )
    # And symmetrically for B's own core/** scope.
    assert scope(two_worktrees["wt_b"], "core/ok.py") == 0, (
        "worktree-B must be allowed to write its own core/** scope"
    )


@pytest.mark.integration
def test_c_unsafe_direction_narrow_not_loosened(two_worktrees):
    """(c) THE UNSAFE DIRECTION — a worktree with a NARROW plan is NOT loosened by a
    BROAD main-checkout pointer (fail-closed). We point MAIN's pointer at the BROAD
    plan (bp-B, core/**) and confirm worktree-A (narrow, edge/**) still CANNOT write
    core/**. Pre-fix, ROOT=MAIN so worktree-A read bp-B's broad scope and the write
    was wrongly ALLOWED — this assertion catches exactly that loosening."""
    main = two_worktrees["main"]
    scope = two_worktrees["scope"]
    # Make MAIN's pointer BROAD (bp-B, core/**) — the loosening hazard.
    (main / ".claude" / "state" / "active-plan").write_text("bp-B")
    assert scope(two_worktrees["wt_a"], "core/loosened.py", project_dir=main) == 2, (
        "FAIL-CLOSED VIOLATION: a broad main-checkout pointer loosened a narrow "
        "worktree builder — worktree-A (edge/** only) must NOT write core/**"
    )
    # Control: worktree-A's own scope still works (not over-denying).
    assert scope(two_worktrees["wt_a"], "edge/still-ok.py", project_dir=main) == 0, (
        "worktree-A's own edge/** scope must still ALLOW (guard is not blanket-deny)"
    )


@pytest.mark.integration
def test_d_no_pointer_is_no_plan_not_main_fallback(two_worktrees):
    """(d) NO POINTER = NO PLAN — a worktree lacking its own active-plan pointer
    resolves to NO active plan (orchestrator posture: only the denylist binds), NOT a
    fallback to MAIN's pointer. We remove worktree-A's pointer, point MAIN's pointer
    at bp-B (core/**), and confirm: (i) a normal file is ALLOWED (no plan capability
    limits it — deny-by-absence means no scope, not main's scope), and (ii) a
    denylisted foundation file is still DENIED (the denylist binds every posture)."""
    main = two_worktrees["main"]
    scope = two_worktrees["scope"]
    (two_worktrees["wt_a"] / ".claude" / "state" / "active-plan").unlink()
    (main / ".claude" / "state" / "active-plan").write_text("bp-B")
    # (i) No plan ⇒ orchestrator posture ⇒ a non-denylisted write is ALLOWED. If the
    #     code fell back to MAIN's bp-B (core/**), this edge/** write would be DENIED.
    assert scope(two_worktrees["wt_a"], "edge/anything.py", project_dir=main) == 0, (
        "no pointer must mean NO active plan (orchestrator posture), not a fallback "
        "to main's pointer"
    )
    # (ii) The denylist still binds under no-plan posture.
    assert scope(two_worktrees["wt_a"], "CONSTITUTION.md", project_dir=main) == 2, (
        "the foundation denylist must bind even with no active plan"
    )
