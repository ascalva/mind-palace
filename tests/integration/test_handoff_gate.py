"""Session-handoff gate — cmd_stop_audit clause (e) (dn-session-handoff-gate).

Clause (e) refuses to close an ORCHESTRATOR session (no active plan) that
committed work this session but left ``.claude/state/resume-brief.md`` stale or
missing. The pinned block condition (design-note §2.2, plan bp-074 §6):

    BLOCK  iff  HEAD != content(.claude/state/session-baseline)   # commits this session
           and  mtime(.claude/state/resume-brief.md) < last-commit %ct

with: a missing ``resume-brief.md`` = infinitely stale (blocks whenever commits
happened); a missing/unreadable ``session-baseline`` = skip, fail-open (§2.5);
the clause guarded by ``plan is None`` (orchestrator posture only — builders
carry an active plan and are governed by (a)).

Mirrors ``test_worktree_enforcement.py``'s pattern: a self-contained throwaway
git repo, ``_lib.py stop-audit`` invoked with ``CLAUDE_PROJECT_DIR`` set, asserting
on the ``ALLOW``/``BLOCK:`` decision line. Six cases (plan bp-074 Item 2):
  (1) block on commits + stale brief
  (2) block on commits + missing brief
  (3) allow on no-commits (baseline == HEAD, brief stale)
  (4) allow on fresh brief (mtime > last commit)
  (5) fail-open allow on missing baseline
  (6) silent under an active plan (decided by (a)-(d) only)

No test reads the real repo's ``.claude/state/**``; every fixture is under
``tmp_path``. ``.claude/state/`` is gitignored in the fixture (as in the real
repo) so runtime state never enters the (b) out-of-scope audit.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

# The code under test: this worktree's own hooks (same convention as
# test_worktree_enforcement.py). Only ``_lib.py`` is needed — we invoke it
# directly, exactly as the bleed_fixture there does.
_HOOKS_SRC = Path(__file__).resolve().parents[2] / ".claude" / "hooks"


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
def handoff_repo(tmp_path: Path):
    """A self-contained git repo in orchestrator posture (empty active-plan
    pointer). ``.claude/state/`` is gitignored so runtime files never appear in
    the (b) out-of-scope audit. Returns control helpers + a ``run`` invoking
    ``_lib.py stop-audit`` with ``CLAUDE_PROJECT_DIR`` set to the repo root."""
    root = tmp_path / "main"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@t")
    _git(root, "config", "user.name", "t")

    (root / ".claude" / "hooks").mkdir(parents=True)
    for f in _HOOKS_SRC.glob("*.py"):
        shutil.copy(f, root / ".claude" / "hooks" / f.name)
    (root / ".claude" / "state").mkdir(parents=True)
    (root / ".claude" / "state" / "active-plan").write_text("")  # orchestrator posture
    (root / ".gitignore").write_text(".claude/state/\n")
    (root / "seed.txt").write_text("seed\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "seed")

    state = root / ".claude" / "state"

    def last_commit_epoch() -> int:
        return int(_git(root, "log", "-1", "--format=%ct").stdout.strip())

    def set_baseline_to_head() -> None:
        (state / "session-baseline").write_text(
            _git(root, "rev-parse", "HEAD").stdout.strip()
        )

    def commit(msg: str = "work") -> None:
        n = len(list(root.glob("w-*.txt")))
        (root / f"w-{n}.txt").write_text("x\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", msg)

    def write_brief(*, fresh: bool) -> None:
        b = state / "resume-brief.md"
        b.write_text("# resume brief\n")
        lc = last_commit_epoch()
        ts = lc + 100 if fresh else lc - 100
        os.utime(b, (ts, ts))

    def run() -> str:
        env = dict(os.environ)
        env["CLAUDE_PROJECT_DIR"] = str(root)
        r = subprocess.run(
            ["python3", str(root / ".claude" / "hooks" / "_lib.py"), "stop-audit"],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
        )
        return r.stdout

    return {
        "root": root,
        "state": state,
        "run": run,
        "set_baseline_to_head": set_baseline_to_head,
        "commit": commit,
        "write_brief": write_brief,
    }


@pytest.mark.integration
def test_e_block_on_commits_and_stale_brief(handoff_repo):
    """(1) commits landed this session + a stale brief -> BLOCK with (e)."""
    h = handoff_repo
    h["set_baseline_to_head"]()  # session start
    h["commit"]()  # a unit of work this session -> HEAD != baseline
    h["write_brief"](fresh=False)  # brief older than the last commit
    out = h["run"]()
    assert out.startswith("BLOCK:"), f"expected BLOCK, got: {out!r}"
    assert "(e)" in out, f"expected the (e) reason, got: {out!r}"


@pytest.mark.integration
def test_e_block_on_commits_and_missing_brief(handoff_repo):
    """(2) commits landed this session + no brief at all (infinitely stale)
    -> BLOCK with (e)."""
    h = handoff_repo
    h["set_baseline_to_head"]()
    h["commit"]()
    # deliberately never write resume-brief.md
    out = h["run"]()
    assert out.startswith("BLOCK:"), f"expected BLOCK, got: {out!r}"
    assert "(e)" in out, f"expected the (e) reason, got: {out!r}"


@pytest.mark.integration
def test_e_allow_when_no_commits_this_session(handoff_repo):
    """(3) baseline == HEAD (a pure chat/design session — no commits) -> ALLOW,
    even with a stale brief. The content guard keeps commit-less sessions from
    ever blocking."""
    h = handoff_repo
    h["commit"]()  # commit BEFORE capturing the baseline
    h["set_baseline_to_head"]()  # baseline == HEAD -> no session commits
    h["write_brief"](fresh=False)  # a stale brief must not matter
    out = h["run"]()
    assert out.strip() == "ALLOW", f"expected ALLOW, got: {out!r}"
    assert "(e)" not in out, f"(e) must not fire with no session commits: {out!r}"


@pytest.mark.integration
def test_e_allow_on_fresh_brief(handoff_repo):
    """(4) commits landed but the brief is fresher than the last commit
    (the natural ceremony: seal commits first, brief last) -> ALLOW."""
    h = handoff_repo
    h["set_baseline_to_head"]()
    h["commit"]()
    h["write_brief"](fresh=True)  # mtime after the last commit
    out = h["run"]()
    assert out.strip() == "ALLOW", f"expected ALLOW, got: {out!r}"
    assert "(e)" not in out, f"a fresh brief must clear (e): {out!r}"


@pytest.mark.integration
def test_e_fail_open_on_missing_baseline(handoff_repo):
    """(5) commits landed and no brief, but session-baseline is absent (first
    session / cleaned state) -> fail-open ALLOW. The signal cannot be evaluated,
    so (e) skips (§2.5)."""
    h = handoff_repo
    # fixture never writes session-baseline; assert it truly isn't there.
    assert not (h["state"] / "session-baseline").exists()
    h["commit"]()
    out = h["run"]()
    assert out.strip() == "ALLOW", f"missing baseline must fail-open ALLOW: {out!r}"
    assert "(e)" not in out, f"(e) must skip on an unevaluable signal: {out!r}"


@pytest.mark.integration
def test_e_silent_under_active_plan(handoff_repo):
    """(6) with an active plan (builder posture), (e) is silent — the session is
    governed by (a)-(d). Commits landed and the brief is deliberately stale, yet
    (e) never fires; a fresh journal keeps (a) quiet so the decision is ALLOW."""
    h = handoff_repo
    root = h["root"]
    plandir = root / "docs" / "build-plans" / "bp-xx"
    plandir.mkdir(parents=True)
    (plandir / "plan.md").write_text(_plan("bp-xx", ["edge/**"]))
    (plandir / "journal.md").write_text("# journal\n")
    (h["state"] / "active-plan").write_text("bp-xx")  # builder posture

    h["set_baseline_to_head"]()
    h["commit"]()  # commits this session
    h["write_brief"](fresh=False)  # a stale brief that (e) would block on, if it ran
    os.utime(plandir / "journal.md", None)  # journal fresh -> (a) stays quiet

    out = h["run"]()
    assert "(e)" not in out, f"(e) must be silent under an active plan: {out!r}"
    assert out.strip() == "ALLOW", (
        f"fresh journal + in-scope tree under an active plan -> ALLOW: {out!r}"
    )
