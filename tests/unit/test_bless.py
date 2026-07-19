"""`palace bless` — the owner-only proposed->ready flip (bp-072 Item 3).

Proves the guard order is LAW and the flip is surgical: (1) an agent session (CLAUDECODE
set) is refused BEFORE any path resolution — proven with a fake id, so zero flip risk;
(2) only status EXACTLY 'proposed' flips (ready/complete/missing -> exit 2, no force path);
(3) the flip is line-targeted — a front-matter comment on the status line and on adjacent
lines survives BYTE-IDENTICAL (no YAML round-trip). All fixtures are tmp_path — this test
NEVER touches a real plan (the Stop-gate would catch that anyway).
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import palace  # noqa: E402


def _plan(root: Path, pid: str, body: str) -> Path:
    d = root / "docs" / "build-plans" / pid
    d.mkdir(parents=True, exist_ok=True)
    p = d / "plan.md"
    p.write_text(body, encoding="utf-8")
    return p


_PROPOSED = """\
---
type: build-plan
id: bp-500
status: proposed
design_ref:
  - docs/brainstorms/thing.md      # a comment that MUST survive
created: 2026-07-01
updated: 2026-07-01
---

# Build Plan — the thing
"""


def test_flip_proposed_to_ready(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.setattr(palace, "_ROOT", tmp_path)
    p = _plan(tmp_path, "bp-500", _PROPOSED)
    rc = palace.bless("bp-500")
    assert rc == 0
    text = p.read_text()
    assert "status: ready\n" in text
    assert "status: proposed" not in text
    assert f"updated: {date.today().isoformat()}\n" in text
    assert "updated: 2026-07-01" not in text
    out = capsys.readouterr().out
    assert "bp-500: proposed -> ready" in out


def test_comment_survives_byte_identical(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.setattr(palace, "_ROOT", tmp_path)
    p = _plan(tmp_path, "bp-500", _PROPOSED)
    palace.bless("bp-500")
    text = p.read_text()
    # the design_ref comment line is untouched, verbatim
    assert "  - docs/brainstorms/thing.md      # a comment that MUST survive\n" in text
    # only two lines changed: status and updated
    assert text.count("# a comment that MUST survive") == 1


def test_status_line_trailing_comment_preserved(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.setattr(palace, "_ROOT", tmp_path)
    body = _PROPOSED.replace("status: proposed\n", "status: proposed   # was minted 07-01\n")
    p = _plan(tmp_path, "bp-500", body)
    assert palace.bless("bp-500") == 0
    text = p.read_text()
    assert "status: ready   # was minted 07-01\n" in text


def test_ready_refused(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.setattr(palace, "_ROOT", tmp_path)
    p = _plan(tmp_path, "bp-500", _PROPOSED.replace("status: proposed", "status: ready"))
    before = p.read_text()
    rc = palace.bless("bp-500")
    assert rc == 2
    assert "not 'proposed'" in capsys.readouterr().err
    assert p.read_text() == before  # untouched


def test_complete_refused(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.setattr(palace, "_ROOT", tmp_path)
    p = _plan(tmp_path, "bp-500", _PROPOSED.replace("status: proposed", "status: complete"))
    before = p.read_text()
    assert palace.bless("bp-500") == 2
    assert p.read_text() == before


def test_missing_plan_exits_two(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.setattr(palace, "_ROOT", tmp_path)
    rc = palace.bless("bp-nope")
    assert rc == 2
    assert "no such plan" in capsys.readouterr().err


def test_agent_session_refused_before_resolution(tmp_path, monkeypatch, capsys):
    """The guard fires FIRST — a fake id under CLAUDECODE yields the agent-session
    refusal, NOT 'no such plan'. This proves the check precedes path resolution."""
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setattr(palace, "_ROOT", tmp_path)
    rc = palace.bless("bp-does-not-exist")
    err = capsys.readouterr().err
    assert rc == 2
    assert "agent session detected" in err
    assert "owner-only" in err
    assert "no such plan" not in err  # never reached resolution


def test_agent_session_does_not_flip_a_real_proposed(tmp_path, monkeypatch):
    """Even with a genuinely-proposed plan present, an agent session flips nothing."""
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setattr(palace, "_ROOT", tmp_path)
    p = _plan(tmp_path, "bp-500", _PROPOSED)
    before = p.read_text()
    assert palace.bless("bp-500") == 2
    assert p.read_text() == before  # proposed, untouched
