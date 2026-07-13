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


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
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


# --------------------------------------------------------------------------- #
# bp-024 (warrant finding-0051 fix 2): cmd_stop_audit's (d) cross-checkout state
# bleed check. A worktree builder's Bash write can reach MAIN's own
# `.claude/state/active-plan` (finding-0051's observed bleed: bp-022's builder
# set both its own worktree pointer AND main's pointer to "bp-022"). scope-guard
# is pre-hoc and structurally can't see a Bash write to an absolute cross-
# checkout path; only a post-hoc Stop-gate audit can flag it. This is that check.
# --------------------------------------------------------------------------- #
@pytest.fixture
def bleed_fixture(tmp_path: Path):
    """A self-contained MAIN repo + one worktree, each with their OWN
    ``.claude/state/active-plan``. Returns a ``run`` helper that invokes
    ``_lib.py stop-audit`` from the worktree with ``CLAUDE_PROJECT_DIR`` set to
    MAIN (the exact condition a delegated builder runs under)."""
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-q", "-b", "main")
    _git(main, "config", "user.email", "t@t")
    _git(main, "config", "user.name", "t")

    (main / ".claude" / "hooks").mkdir(parents=True)
    for f in _HOOKS_SRC.glob("*.py"):
        shutil.copy(f, main / ".claude" / "hooks" / f.name)

    plans = main / "docs" / "build-plans"
    (plans / "bp-024").mkdir(parents=True)
    (plans / "bp-024" / "plan.md").write_text(_plan("bp-024", ["edge/**"]))
    (plans / "bp-024" / "journal.md").write_text("# journal\n")
    (plans / "bp-other").mkdir(parents=True)
    (plans / "bp-other" / "plan.md").write_text(_plan("bp-other", ["core/**"]))
    (plans / "bp-other" / "journal.md").write_text("# journal\n")

    (main / ".claude" / "state").mkdir(parents=True)
    (main / ".claude" / "state" / "active-plan").write_text("")  # orchestrator posture
    _git(main, "add", "-A")
    _git(main, "commit", "-qm", "fixture: bp-024 + bp-other + hooks")

    wt = tmp_path / "wt"
    _git(main, "worktree", "add", "-q", "-b", "br-wt", str(wt))
    (wt / ".claude" / "state").mkdir(parents=True, exist_ok=True)
    (wt / ".claude" / "state" / "active-plan").write_text("bp-024")
    # Journal is fresh (mtime after HEAD) so (a) staleness never fires and
    # muddies the (d)-only assertions below.
    (wt / "docs" / "build-plans" / "bp-024" / "journal.md").write_text(
        "# journal\n- fresh\n"
    )

    def run(main_pointer_val: str, in_worktree: bool = True) -> str:
        """Set MAIN's pointer to `main_pointer_val`, run `_lib.py stop-audit`
        from `wt` (or from `main` itself if `in_worktree` is False — the
        env-top == cwd-top control), with CLAUDE_PROJECT_DIR=main. Returns
        stdout (the ALLOW/BLOCK decision line)."""
        (main / ".claude" / "state" / "active-plan").write_text(main_pointer_val)
        cwd = wt if in_worktree else main
        env = dict(os.environ)
        env["CLAUDE_PROJECT_DIR"] = str(main)
        r = subprocess.run(
            ["python3", str(cwd / ".claude" / "hooks" / "_lib.py"), "stop-audit"],
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
        )
        return r.stdout

    return {"main": main, "wt": wt, "run": run}


@pytest.mark.integration
def test_stop_audit_flags_main_checkout_pointer_bleed(bleed_fixture):
    """THE positive case: main's active-plan pointer names THIS worktree's OWN
    plan (bp-024) — the exact finding-0051 bleed signature. `(d)` must fire."""
    out = bleed_fixture["run"]("bp-024")
    assert "(d) cross-checkout state bleed" in out, (
        f"expected the (d) bleed reason in BLOCK output, got: {out!r}"
    )


@pytest.mark.integration
def test_stop_audit_bleed_control_1_empty_main_pointer(bleed_fixture):
    """Control 1: main's pointer is EMPTY (orchestrator posture, the common
    case) -> no (d) reason."""
    out = bleed_fixture["run"]("")
    assert "(d)" not in out, f"empty main pointer must never trip (d), got: {out!r}"


@pytest.mark.integration
def test_stop_audit_bleed_control_2_different_plan_no_false_positive(bleed_fixture):
    """Control 2 (zero-false-positive guarantee, §3 Q3): main's pointer names a
    DIFFERENT plan than this worktree's own -> no (d) reason. An orchestrator
    legitimately holding a different main-checkout plan must not be flagged."""
    out = bleed_fixture["run"]("bp-other")
    assert "(d)" not in out, (
        f"a main pointer naming a DIFFERENT plan must never trip (d) (zero "
        f"false positives), got: {out!r}"
    )


@pytest.mark.integration
def test_stop_audit_bleed_control_3_not_a_worktree_byte_identical(bleed_fixture):
    """Control 3: NOT running in a worktree (env-top == cwd-top, i.e. running
    from MAIN itself) -> byte-identical, no (d) reason, even if main's own
    pointer happens to equal the value under test."""
    out = bleed_fixture["run"]("bp-024", in_worktree=False)
    assert "(d)" not in out, (
        f"running from the main checkout itself (env-top == cwd-top) must "
        f"never trip (d), got: {out!r}"
    )
