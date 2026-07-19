"""The docket — the derived awaiting-the-owner view (bp-072 Item 1).

Proves the view is EXACTLY the owner-awaiting set and nothing else: proposed plans,
draft notes, and open owner-questions surface; `ready` plans, ratified/superseded
notes, and answered/swept oqs are excluded (the agent-actionable states). Sort order
is blocking-oq -> proposed-plan -> draft-note -> non-blocking-oq, oldest-first within
class. The three CLI modes (render / --count / --write) each behave. The DRY falsifier
is guarded structurally: docket imports `_lib`'s front-matter parser rather than
re-deriving one, and never imports `core`.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import docket  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _plan(root: Path, pid: str, status: str, created: str) -> None:
    _write(
        root / "docs" / "build-plans" / pid / "plan.md",
        f"---\ntype: build-plan\nid: {pid}\nstatus: {status}\ncreated: {created}\n---\n\n# Build Plan — {pid} the thing\n",
    )


def _note(root: Path, stem: str, status: str, created: str = "") -> None:
    c = f"created: {created}\n" if created else ""
    # trailing comment on the status line mirrors the live tree — docket must normalize it
    _write(
        root / "docs" / "design-notes" / f"{stem}.md",
        f"---\ntype: design-note\nstatus: {status}               # draft -> ratified is owner-only\n{c}---\n\n# {stem} note\n",
    )


def _oqs(root: Path, body: str) -> None:
    _write(root / "docs" / "inbox" / "owner-questions.md", "# Owner questions\n\n---\n\n" + body)


def _fixture_tree(root: Path) -> None:
    _plan(root, "bp-100", "proposed", "2026-07-10")
    _plan(root, "bp-101", "proposed", "2026-07-05")  # older -> sorts before bp-100
    _plan(root, "bp-102", "ready", "2026-07-01")      # EXCLUDED (agent-actionable)
    _plan(root, "bp-103", "complete", "2026-06-01")   # EXCLUDED
    _note(root, "alpha", "draft", "2026-07-08")
    _note(root, "beta", "ratified")                    # EXCLUDED
    _oqs(root, (
        "## oq-0001 — a non-blocking question\n- status: open\n- blocking: false\n\n---\n\n"
        "## oq-0002 — a BLOCKING question\n- status: open\n- blocking: true\n\n---\n\n"
        "## oq-0003 — already handled\n- status: answered\n- blocking: false\n\n---\n\n"
        "## oq-0004 — swept away\n- status: swept\n- blocking: true\n"
    ))


def test_view_is_exactly_the_owner_awaiting_set(tmp_path):
    _fixture_tree(tmp_path)
    rows = docket.scan_docket(tmp_path)
    ids = [r.id for r in rows]
    # included: two proposed plans, one draft note, two open oqs
    assert set(ids) == {"bp-100", "bp-101", "alpha", "oq-0001", "oq-0002"}
    # excluded: ready/complete plans, ratified note, answered/swept oqs
    assert "bp-102" not in ids and "bp-103" not in ids
    assert "beta" not in ids
    assert "oq-0003" not in ids and "oq-0004" not in ids


def test_sort_order_classes_and_oldest_first(tmp_path):
    _fixture_tree(tmp_path)
    ids = [r.id for r in docket.scan_docket(tmp_path)]
    # blocking oq first, then proposed plans (oldest created first), then draft note,
    # then non-blocking oq last.
    assert ids == ["oq-0002", "bp-101", "bp-100", "alpha", "oq-0001"]


def test_blocking_oq_flagged_in_action(tmp_path):
    _fixture_tree(tmp_path)
    rows = {r.id: r for r in docket.scan_docket(tmp_path)}
    assert "BLOCKING" in rows["oq-0002"].action
    assert rows["oq-0001"].action == "answer"
    assert rows["bp-100"].action == "bless proposed->ready"
    assert rows["alpha"].action.startswith("ratify")


def test_count_mode_prints_one_integer(tmp_path, monkeypatch, capsys):
    _fixture_tree(tmp_path)
    monkeypatch.setattr(docket, "ROOT", tmp_path)
    rc = docket.main(["--count"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert out == "5"
    assert int(out) == 5  # exactly one integer, nothing else


def test_write_mode_emits_the_landing_buffer(tmp_path, monkeypatch, capsys):
    _fixture_tree(tmp_path)
    monkeypatch.setattr(docket, "ROOT", tmp_path)
    rc = docket.main(["--write"])
    capsys.readouterr()
    dest = tmp_path / ".claude" / "state" / "docket.md"
    assert rc == 0 and dest.exists()
    body = dest.read_text()
    assert "5 awaiting the owner" in body
    assert "oq-0002" in body and "bp-100" in body
    assert "Guide, not gate" in body


def test_empty_tree_is_inbox_zero(tmp_path):
    (tmp_path / "docs" / "build-plans").mkdir(parents=True)
    rows = docket.scan_docket(tmp_path)
    assert rows == []
    assert "Inbox zero" in docket.render(rows)


def test_dry_no_core_import_and_reuses_lib():
    """The DRY + no-core falsifiers, enforced by static inspection of the source."""
    src = (REPO / "scripts" / "docket.py").read_text()
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name.split(".")[0])
    assert "core" not in imported, "docket must never import core (repo-workflow tooling)"
    assert "_lib" in imported, "docket must reuse _lib's front-matter parser, not re-derive one"
    # and no local YAML parser sneaking in
    assert "yaml" not in imported
