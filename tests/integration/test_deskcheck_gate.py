"""The deskcheck gate — the third owner-only transition (dn-track-board-and-
deskcheck-gate D3/D5/D6, plan bp-097).

Three enforcement teeth, all exercised against a self-contained throwaway git
repo (the ``test_handoff_gate.py`` / ``test_worktree_enforcement.py`` pattern:
copy the real ``_lib.py`` into the fixture, invoke a subcommand with
``CLAUDE_PROJECT_DIR`` set, assert on the ``ALLOW``/``DENY:``/``BLOCK:`` line):

  Item 2 — pre-hoc: ``gate-check`` / ``gate-check-hook`` DENY a verdict flip off
           ``pending``; ``pending`` and non-deskcheck files pass; the two
           existing blessing gates still DENY (no regression).
  Item 3 — post-hoc: ``stop-audit`` BLOCKs a Bash-mediated verdict flip citing
           (c) with the D6 YIELD posture; a committed verdict self-clears; a
           dc minted directly at ``approved`` (untracked) BLOCKs.
  Item 4 — ``stop-audit`` clause (f): a plan sealed to ``complete`` whose journal
           tail lacks ``## Follow-through`` BLOCKs; adding the block clears it.
           And the (b2) owner-staged YIELD: an additive front-matter edit of a
           ratified note earns the yield message (still BLOCK), a BODY edit hard-
           blocks with no yield.

No test reads the real repo's state; every fixture is under ``tmp_path``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

_HOOKS_SRC = Path(__file__).resolve().parents[2] / ".claude" / "hooks"


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True
    )


def _dc(verdict: str = "pending", *, track: str = "workflow") -> str:
    return (
        "---\n"
        "type: deskcheck\n"
        "id: dc-001\n"
        f"track: {track}\n"
        "date: 2026-07-21\n"
        "items: [bp-097]\n"
        "audit_refs: []\n"
        f"verdict: {verdict}\n"
        "send_back: null\n"
        "links: []\n"
        "---\n"
        "# Deskcheck — workflow\n"
    )


def _note(status: str, *, body: str = "The note body.\n") -> str:
    return (
        "---\n"
        "type: design-note\n"
        "id: dn-x\n"
        f"status: {status}\n"
        "---\n"
        f"# dn-x\n{body}"
    )


def _plan(status: str, plan_id: str = "bp-xx") -> str:
    return (
        "---\n"
        "type: build-plan\n"
        f"id: {plan_id}\n"
        f"status: {status}\n"
        "contract: builder\n"
        "write_scope:\n"
        '  - "edge/**"\n'
        "---\n"
        f"# {plan_id}\n"
    )


@pytest.fixture
def repo(tmp_path: Path):
    """A throwaway git repo with the real hooks copied in and an empty active-plan
    pointer (orchestrator posture by default). Returns helpers that invoke the
    three ``_lib.py`` subcommands the deskcheck gate lives in."""
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
    for d in ("docs/deskchecks", "docs/design-notes", "docs/build-plans"):
        (root / d).mkdir(parents=True)
    (root / "seed.txt").write_text("seed\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "seed")

    lib = str(root / ".claude" / "hooks" / "_lib.py")

    def _run(*args: str, stdin: str | None = None) -> str:
        env = dict(os.environ)
        env["CLAUDE_PROJECT_DIR"] = str(root)
        return subprocess.run(
            ["python3", lib, *args],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            input=stdin,
        ).stdout

    def write(rel: str, text: str) -> None:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def commit(msg: str = "c") -> None:
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", msg)

    def gate_check(rel: str, value: str) -> str:
        return _run("gate-check", rel, value)

    def gate_check_hook(rel: str, blob: str) -> str:
        ev = {"tool_input": {"file_path": rel, "new_string": blob}}
        return _run("gate-check-hook", stdin=json.dumps(ev))

    def stop_audit() -> str:
        return _run("stop-audit")

    return {
        "root": root,
        "write": write,
        "commit": commit,
        "gate_check": gate_check,
        "gate_check_hook": gate_check_hook,
        "stop_audit": stop_audit,
    }


# --------------------------------------------------------------------------- #
# Item 2 — pre-hoc verdict denial
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_prehoc_verdict_flip_denied(repo):
    """A dc at verdict: pending on disk — an intended approved|needs-work DENIES,
    pending ALLOWS (the only agent-legal value)."""
    repo["write"]("docs/deskchecks/dc-001.md", _dc("pending"))
    assert repo["gate_check"]("docs/deskchecks/dc-001.md", "approved").startswith("DENY:")
    assert repo["gate_check"]("docs/deskchecks/dc-001.md", "needs-work").startswith("DENY:")
    assert repo["gate_check"]("docs/deskchecks/dc-001.md", "pending").strip() == "ALLOW"


@pytest.mark.integration
def test_prehoc_from_nothing_verdict_denied(repo):
    """A dc minted directly at approved (no file on disk yet) is a from-nothing
    verdict flip — denied pre-hoc."""
    assert repo["gate_check"]("docs/deskchecks/dc-999.md", "approved").startswith("DENY:")


@pytest.mark.integration
def test_prehoc_non_deskcheck_scaffolding_allowed(repo):
    """The store's README.md (no dc- prefix) is not a record — never gated."""
    assert repo["gate_check"]("docs/deskchecks/README.md", "approved").strip() == "ALLOW"


@pytest.mark.integration
def test_prehoc_blessing_gates_unregressed(repo):
    """The two existing blessing gates still DENY — the third gate is additive."""
    repo["write"]("docs/design-notes/dn-x.md", _note("draft"))
    repo["write"]("docs/build-plans/bp-xx/plan.md", _plan("proposed"))
    assert repo["gate_check"]("docs/design-notes/dn-x.md", "ratified").startswith("DENY:")
    assert repo["gate_check"]("docs/build-plans/bp-xx/plan.md", "ready").startswith("DENY:")


@pytest.mark.integration
def test_prehoc_hook_mode_reads_verdict_blob(repo):
    """gate-check-hook extracts `verdict:` from the edit blob for a deskcheck file
    (not `status:`) — approved DENIES, pending ALLOWS, no verdict line ALLOWS."""
    repo["write"]("docs/deskchecks/dc-001.md", _dc("pending"))
    assert repo["gate_check_hook"](
        "docs/deskchecks/dc-001.md", "verdict: approved\n"
    ).startswith("DENY:")
    assert (
        repo["gate_check_hook"]("docs/deskchecks/dc-001.md", "verdict: pending\n").strip()
        == "ALLOW"
    )
    assert (
        repo["gate_check_hook"](
            "docs/deskchecks/dc-001.md", "## What was built\nsome prose\n"
        ).strip()
        == "ALLOW"
    )


# --------------------------------------------------------------------------- #
# Item 3 — post-hoc verdict audit + the D6 yield message (clause (c))
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_posthoc_bash_verdict_flip_blocks_with_yield(repo):
    """A tracked dc committed at pending, then Bash-flipped to approved
    (uncommitted) -> stop-audit BLOCKs citing (c) with the D6 YIELD posture."""
    repo["write"]("docs/deskchecks/dc-001.md", _dc("pending"))
    repo["commit"]("add dc at pending")
    repo["write"]("docs/deskchecks/dc-001.md", _dc("approved"))  # Bash flip, uncommitted
    out = repo["stop_audit"]()
    assert out.startswith("BLOCK:"), out
    assert "(c)" in out, out
    assert "YIELD" in out, out


@pytest.mark.integration
def test_posthoc_committed_verdict_self_clears(repo):
    """A committed verdict is accountable to its author and self-clears (HEAD-keyed,
    A1) — clean tree, no (c)."""
    repo["write"]("docs/deskchecks/dc-001.md", _dc("pending"))
    repo["commit"]("add dc")
    repo["write"]("docs/deskchecks/dc-001.md", _dc("approved"))
    repo["commit"]("owner blesses the verdict")
    out = repo["stop_audit"]()
    assert "(c)" not in out, out


@pytest.mark.integration
def test_posthoc_untracked_verdict_blocks(repo):
    """A dc minted directly at approved through Bash is untracked — invisible to
    `git diff HEAD`, caught by the untracked (c) scanner."""
    repo["write"]("docs/deskchecks/dc-777.md", _dc("approved"))  # never committed
    out = repo["stop_audit"]()
    assert out.startswith("BLOCK:"), out
    assert "(c)" in out, out


# --------------------------------------------------------------------------- #
# Item 4 — clause (f) seal follow-through
# --------------------------------------------------------------------------- #
_SEAL_NO_FT = "# journal\n\n## Entry 1 — work\ndid the thing\n\n## Entry 2 — SEAL\nsealed it\n"
_SEAL_WITH_FT = (
    "# journal\n\n## Entry 1 — work\ndid the thing\n\n## Entry 2 — SEAL\nsealed it\n\n"
    "## Follow-through\n"
    "- **Built?** yes\n"
    "- **Wired / delivered (or why dormant)?** wired\n"
    "- **Does a consumer use it?** yes\n"
    "- **Track state (what remains on this track)?** none\n"
    "- **Opened a new track/finding?** no\n"
)


def _seal_plan_to_complete(repo, journal_text: str) -> None:
    """Commit a plan at in-progress + a journal, then flip the plan to complete
    (uncommitted) so the flip shows in the HEAD-keyed diff clause (f) scans."""
    repo["write"]("docs/build-plans/bp-xx/plan.md", _plan("in-progress"))
    repo["write"]("docs/build-plans/bp-xx/journal.md", journal_text)
    repo["commit"]("plan in-progress")
    repo["write"]("docs/build-plans/bp-xx/plan.md", _plan("complete"))  # seal, uncommitted


@pytest.mark.integration
def test_clause_f_blocks_seal_without_followthrough(repo):
    """A plan sealed to complete whose journal tail lacks ## Follow-through -> BLOCK (f)."""
    _seal_plan_to_complete(repo, _SEAL_NO_FT)
    out = repo["stop_audit"]()
    assert out.startswith("BLOCK:"), out
    assert "(f)" in out, out


@pytest.mark.integration
def test_clause_f_clears_with_followthrough(repo):
    """The same seal WITH a ## Follow-through block in the journal tail clears (f)."""
    _seal_plan_to_complete(repo, _SEAL_WITH_FT)
    out = repo["stop_audit"]()
    assert "(f)" not in out, out


@pytest.mark.integration
def test_clause_f_tail_bounded_ignores_early_mention(repo):
    """A ## Follow-through header in an EARLY entry does NOT clear a seal whose tail
    entry lacks it — the check is bounded to the final entry (anti-false-clear)."""
    early = (
        "# journal\n\n## Entry 1 — planning\n"
        "## Follow-through\n- **Built?** (draft, not the seal)\n\n"
        "## Entry 2 — SEAL\nsealed it, forgot the block\n"
    )
    _seal_plan_to_complete(repo, early)
    out = repo["stop_audit"]()
    assert "(f)" in out, out


# --------------------------------------------------------------------------- #
# Item 4 — the (b2) owner-staged yield
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_b2_additive_frontmatter_earns_yield(repo):
    """A ratified note with ONLY an added front-matter `track:` line -> (b2) still
    BLOCKs, but the reason carries the owner-staged YIELD posture (additive-only)."""
    repo["write"]("docs/design-notes/dn-x.md", _note("ratified"))
    repo["commit"]("ratify note")
    # owner stages a track: line into the front matter — body & status untouched.
    repo["write"](
        "docs/design-notes/dn-x.md",
        "---\ntype: design-note\nid: dn-x\nstatus: ratified\ntrack: workflow\n---\n"
        "# dn-x\nThe note body.\n",
    )
    out = repo["stop_audit"]()
    assert out.startswith("BLOCK:"), out
    assert "(b2)" in out, out
    assert "additive front matter only" in out, out
    assert "ONCE" in out, out


@pytest.mark.integration
def test_b2_body_edit_hard_blocks_no_yield(repo):
    """A ratified note whose BODY is edited hard-blocks — NO yield posture (a body
    edit must never earn the commit-inviting message)."""
    repo["write"]("docs/design-notes/dn-x.md", _note("ratified"))
    repo["commit"]("ratify note")
    repo["write"]("docs/design-notes/dn-x.md", _note("ratified", body="A TAMPERED body.\n"))
    out = repo["stop_audit"]()
    assert out.startswith("BLOCK:"), out
    assert "(b2)" in out, out
    assert "agent-immutable" in out, out
    assert "additive front matter only" not in out, out


@pytest.mark.integration
def test_b2_committed_additive_self_clears(repo):
    """Once the owner COMMITS the additive edit it is accountable — (b2) self-clears."""
    repo["write"]("docs/design-notes/dn-x.md", _note("ratified"))
    repo["commit"]("ratify note")
    repo["write"](
        "docs/design-notes/dn-x.md",
        "---\ntype: design-note\nid: dn-x\nstatus: ratified\ntrack: workflow\n---\n"
        "# dn-x\nThe note body.\n",
    )
    repo["commit"]("owner adds track: coordinate")
    out = repo["stop_audit"]()
    assert "(b2)" not in out, out
