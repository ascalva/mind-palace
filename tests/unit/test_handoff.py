"""The handoff — the DERIVED per-scope rendering (bp-124, dn-role-state-and-scoped-handoff §2.9).

Proves the four properties the rest of the family rests on:

  * **F1a / the idempotence pin** — two renders of an unchanged tree are byte-equal, the committed
    file equals a fresh render, and the rendering is independent of *its own* prior content. It
    embeds no HEAD sha and no generation timestamp, so a freshness gate keyed on regeneration
    converges in one step instead of re-arming forever.
  * **F1c / availability** — with no `data/queue.sqlite` (a fresh worktree, nothing running) the
    generator exits 0 and renders `queue: unavailable in this checkout`; it opens the queue with a
    `file:…?mode=ro` URI and can therefore never create or mutate it (single-writer,
    `scheduler/queue.py:17-18`).
  * **F2's mechanical half** — `--json` emits `unit_in_flight` / `next_action` derived from the
    tree, byte-identical across invocations, and agreeing with the document.
  * **The DRY / no-core falsifiers**, structurally: handoff reuses `board`'s scanners and `_lib`'s
    parser rather than re-deriving either, and never imports `core`.
"""

from __future__ import annotations

import ast
import json
import re
import sqlite3
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import board  # type: ignore[import-not-found]  # noqa: E402
import handoff  # type: ignore[import-not-found]  # noqa: E402

# A word-bounded hex-shaped token: a commit sha, the class of fact the pin evicts (§2.9).
_HEXISH = re.compile(r"\b[0-9a-f]{7,40}\b")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture(root: Path) -> None:
    """A minimal but complete artifact tree: two tracks, plans across the status ladder, a note,
    findings, owner questions (one blocking), and the orchestrator seat's readings log."""
    _write(root / "docs" / "tracks" / "alpha.md",
           "---\ntype: track\nslug: alpha\ntitle: Alpha — the alpha track\nstatus: active\n"
           "warrant: null\naudit_refs: []\ndod:\nbacklog_deskcheck: null\nlinks: []\n---\n"
           "# Track — Alpha\n")
    _write(root / "docs" / "tracks" / "beta.md",
           "---\ntype: track\nslug: beta\ntitle: Beta — the beta track\nstatus: active\n"
           "warrant: null\naudit_refs: []\ndod:\nbacklog_deskcheck: null\nlinks: []\n---\n"
           "# Track — Beta\n")
    for pid, track, status in (("bp-201", "alpha", "complete"), ("bp-202", "alpha", "ready"),
                               ("bp-203", "alpha", "in-progress"), ("bp-204", "beta", "proposed")):
        _write(root / "docs" / "build-plans" / pid / "plan.md",
               f"---\ntype: build-plan\nid: {pid}\ntrack: {track}\nstatus: {status}\n---\n"
               f"\n# Build Plan — {pid} the thing\n")
    _write(root / "docs" / "design-notes" / "dn-alpha.md",
           "---\ntype: design-note\ntrack: alpha\nstatus: draft\n---\n\n# dn-alpha\n")
    _write(root / "docs" / "findings" / "finding-0001.md",
           "---\ntype: finding\nid: finding-0001\nstatus: open\n---\n\n# a finding\n")
    _write(root / "docs" / "inbox" / "owner-questions.md",
           "# Owner questions\n\n---\n\n## oq-0001 — a blocking one\n- status: open\n"
           "- blocking: true\n\n---\n\n## oq-0002 — an answered one\n- status: answered\n"
           "- blocking: false\n")
    _write(root / "docs" / "roles" / "orchestrator" / "readings.md",
           "| timestamp | command | result |\n|---|---|---|\n"
           "| 2026-07-01T00:00Z | uv run pytest -q | 1 failed / 10 passed (stale) |\n"
           "| 2026-07-02T00:00Z | uv run pytest -q | 0 failed / 11 passed |\n")


def _queue(root: Path) -> Path:
    """A fixture queue file shaped like the real `jobs` table's relevant columns."""
    path = root / "data" / "queue.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE jobs (id INTEGER PRIMARY KEY, kind TEXT, state TEXT, "
                 "lease_expires_at TEXT)")
    conn.executemany("INSERT INTO jobs (id, kind, state, lease_expires_at) VALUES (?, ?, ?, ?)",
                     [(1, "embed", "queued", None), (2, "embed", "queued", None),
                      (3, "dream", "running", "2026-07-02T01:00:00")])
    conn.commit()
    conn.close()
    return path


def _role(root: Path) -> handoff.Scope:
    return handoff.resolve(root, "role", "orchestrator")


# ── F1a: the idempotence pin ────────────────────────────────────
def test_two_renders_of_an_unchanged_tree_are_byte_equal(tmp_path):
    """Item 2's falsifier: if these differ, clause (e′) can never be discharged."""
    _fixture(tmp_path)
    assert handoff.handoff_text(tmp_path, _role(tmp_path)) == \
        handoff.handoff_text(tmp_path, _role(tmp_path))


def test_rendering_is_independent_of_its_own_prior_content(tmp_path):
    """The "excluding itself" half of the pin — otherwise the artifact is its own input and the
    fixed point does not exist."""
    _fixture(tmp_path)
    before = handoff.handoff_text(tmp_path, _role(tmp_path))
    dest = tmp_path / "docs" / "roles" / "orchestrator" / "handoff.md"
    _write(dest, before + "\nHAND-EDITED GARBAGE\n")
    assert handoff.handoff_text(tmp_path, _role(tmp_path)) == before


def test_no_sha_and_no_generation_timestamp_in_the_committed_rendering(tmp_path):
    _fixture(tmp_path)
    text = handoff.handoff_text(tmp_path, _role(tmp_path))
    assert not _HEXISH.findall(text), "the rendering must cite no commit sha (§2.9)"
    # A reading's OWN timestamp is data and is expected; a *generation* timestamp is not, so the
    # committed rendering must contain no clock read the generator itself performed.
    assert "2026-07-02T00:00Z" in text  # the reading's timestamp, carried as data
    assert " ago" not in text, "an age is a clock read — live view only"


def test_committed_file_equals_a_fresh_render_and_check_agrees(tmp_path, monkeypatch, capsys):
    _fixture(tmp_path)
    monkeypatch.setattr(handoff, "ROOT", tmp_path)
    assert handoff.main(["--role", "orchestrator", "--write"]) == 0
    dest = tmp_path / "docs" / "roles" / "orchestrator" / "handoff.md"
    first = dest.read_text(encoding="utf-8")
    assert handoff.main(["--role", "orchestrator", "--write"]) == 0
    assert dest.read_text(encoding="utf-8") == first
    capsys.readouterr()
    assert handoff.main(["--role", "orchestrator", "--check"]) == 0
    # A hand-edit makes --check fail loudly rather than silently re-render.
    dest.write_text(first + "drift\n", encoding="utf-8")
    assert handoff.main(["--role", "orchestrator", "--check"]) == 1


def test_generated_banner_and_row_width(tmp_path):
    _fixture(tmp_path)
    text = handoff.handoff_text(tmp_path, _role(tmp_path))
    assert text.startswith(handoff.GENERATED_BANNER)
    for ln in text.splitlines():
        if ln.startswith("|"):
            assert len(ln) <= board.MAX_ROW, f"row exceeds the owner ≤190 rule: {ln!r}"


def test_long_title_is_capped(tmp_path):
    _fixture(tmp_path)
    _write(tmp_path / "docs" / "build-plans" / "bp-299" / "plan.md",
           "---\ntype: build-plan\nid: bp-299\ntrack: alpha\nstatus: ready\n---\n"
           f"\n# Build Plan — {'x ' * 200}\n")
    rows = [ln for ln in handoff.handoff_text(tmp_path, _role(tmp_path)).splitlines()
            if ln.startswith("| bp-299 |")]
    assert rows and len(rows[0]) <= board.MAX_ROW and rows[0].rstrip().endswith("… |")


# ── the derivation ──────────────────────────────────────────────
def test_next_action_and_unit_are_derived_from_the_tree(tmp_path):
    """V1's subject: both fields fall out of plan statuses, hand-written nowhere."""
    _fixture(tmp_path)
    ans = handoff.derive(tmp_path, _role(tmp_path))
    assert ans.unit_in_flight == "bp-203"          # the in-progress plan wins the ladder
    assert ans.next_action == "/resume bp-203"
    # Remove it and the ladder falls through to the ready rung — still derived, not hand-set.
    (tmp_path / "docs" / "build-plans" / "bp-203" / "plan.md").unlink()
    ans2 = handoff.derive(tmp_path, _role(tmp_path))
    assert ans2.unit_in_flight == "bp-202" and ans2.next_action == "/build bp-202"


def test_empty_board_falls_through_to_the_sweep(tmp_path):
    _fixture(tmp_path)
    for pid in ("bp-202", "bp-203"):
        (tmp_path / "docs" / "build-plans" / pid / "plan.md").unlink()
    ans = handoff.derive(tmp_path, _role(tmp_path))
    assert ans.unit_in_flight == "none" and ans.next_action == "/triage"


def test_blocking_owner_questions_become_blocked_lines(tmp_path):
    _fixture(tmp_path)
    ans = handoff.derive(tmp_path, _role(tmp_path))
    assert ans.blocking_unknowns == ("BLOCKED: oq-0001 — a blocking one",)


def test_track_scope_sees_only_its_members(tmp_path):
    _fixture(tmp_path)
    ans = handoff.derive(tmp_path, handoff.resolve(tmp_path, "track", "beta"))
    # beta owns only a `proposed` plan: no rung of the ladder matches, and a blessing is an
    # owner act, never an agent's next action — so the sweep is what is owed.
    assert ans.unit_in_flight == "none" and ans.next_action == "/triage"
    text = handoff.handoff_text(tmp_path, handoff.resolve(tmp_path, "track", "beta"))
    assert "bp-204" in text and "bp-201" not in text


def test_plan_scope_reports_its_own_status(tmp_path):
    _fixture(tmp_path)
    ans = handoff.derive(tmp_path, handoff.resolve(tmp_path, "plan", "bp-201"))
    assert ans.next_action == "deskcheck owed on bp-201 — sealed, not closed"


def test_a_scope_id_must_resolve_to_an_artifact_on_disk(tmp_path):
    """Note §2.3: a scope is `(kind, id)` where the id names something real — never a free
    string, so a typo fails loudly instead of rendering a plausible empty view."""
    _fixture(tmp_path)
    for kind, ident in (("role", "builder"), ("track", "ghost"), ("plan", "bp-999")):
        with pytest.raises(handoff.ScopeError):
            handoff.resolve(tmp_path, kind, ident)


# ── F1c: the queue is an input, read-only, and its absence is a value ──
def test_absent_queue_degrades_and_creates_nothing(tmp_path, monkeypatch, capsys):
    _fixture(tmp_path)
    monkeypatch.setattr(handoff, "ROOT", tmp_path)
    rc = handoff.main(["--role", "orchestrator"])
    out = capsys.readouterr().out
    assert rc == 0, "a checkout with no queue must not be an error (F1c)"
    assert handoff.QUEUE_UNAVAILABLE in out
    assert not (tmp_path / "data" / "queue.sqlite").exists(), \
        "the generator must never create the queue — single-writer, scheduler/queue.py:17-18"


def test_present_queue_renders_its_rows(tmp_path):
    _fixture(tmp_path)
    _queue(tmp_path)
    lines = handoff.read_queue(tmp_path / "data" / "queue.sqlite")
    assert lines[0] == "queue: depth 2 · running 1"
    assert lines[1].startswith("queue: RUNNING 3 · dream · lease 2026-07-02")
    live = handoff.handoff_text(tmp_path, _role(tmp_path), live=True)
    assert "queue: depth 2 · running 1" in live
    # …and the COMMITTED artifact carries the pointer instead, so a mutating daemon can never
    # make a tree-unchanged regeneration differ (the pin, §2.9).
    assert "queue: depth" not in handoff.handoff_text(tmp_path, _role(tmp_path))


def test_the_queue_is_opened_with_a_readonly_uri(tmp_path, monkeypatch):
    _fixture(tmp_path)
    path = _queue(tmp_path)
    seen: list[object] = []
    real = sqlite3.connect

    def spy(target, *a, **kw):
        seen.append(target)
        return real(target, *a, **kw)

    monkeypatch.setattr(handoff.sqlite3, "connect", spy)
    handoff.read_queue(path)
    assert seen == [f"file:{path}?mode=ro"], "mode=ro is what makes the read structurally safe"


def test_a_readonly_open_of_a_missing_path_cannot_create_it(tmp_path):
    """The dry-run the plan asks for, as a standing test: `mode=ro` REFUSES a missing file rather
    than creating an empty one — which is what a plain `sqlite3.connect` would do."""
    missing = tmp_path / "data" / "queue.sqlite"
    missing.parent.mkdir(parents=True)
    with pytest.raises(sqlite3.OperationalError):
        sqlite3.connect(f"file:{missing}?mode=ro", uri=True)
    assert not missing.exists()


def test_an_unreadable_queue_is_a_value_not_an_exception(tmp_path):
    path = tmp_path / "data" / "queue.sqlite"
    path.parent.mkdir(parents=True)
    path.write_text("not a database at all", encoding="utf-8")
    assert handoff.read_queue(path)[0].startswith("queue: present but unreadable")


# ── MEASURED: latest per command, age only in the live view ─────
def test_latest_reading_per_command_is_last_in_file(tmp_path):
    _fixture(tmp_path)
    rows = handoff.latest_per_command(
        handoff.read_readings(tmp_path / "docs" / "roles" / "orchestrator" / "readings.md"))
    assert rows == [("2026-07-02T00:00Z", "uv run pytest -q", "0 failed / 11 passed")]


def test_the_live_view_shows_an_age_and_the_committed_one_shows_the_timestamp(tmp_path):
    _fixture(tmp_path)
    assert " ago |" in handoff.handoff_text(tmp_path, _role(tmp_path), live=True)
    assert "2026-07-02T00:00Z |" in handoff.handoff_text(tmp_path, _role(tmp_path))


# ── F2's mechanical half: the structured answer ─────────────────
def test_json_carries_the_probe_fields_and_is_byte_stable(tmp_path):
    _fixture(tmp_path)
    first = handoff.answer_json(tmp_path, _role(tmp_path))
    assert first == handoff.answer_json(tmp_path, _role(tmp_path))
    data = json.loads(first)
    assert data["unit_in_flight"] == "bp-203"
    assert data["next_action"] == "/resume bp-203"
    assert data["blocking_unknowns"] == ["BLOCKED: oq-0001 — a blocking one"]


def test_json_never_disagrees_with_the_document(tmp_path):
    """Both are views of ONE computation; a drift between them would make the drill's compare
    meaningless (§2.11 F2)."""
    _fixture(tmp_path)
    data = json.loads(handoff.answer_json(tmp_path, _role(tmp_path)))
    text = handoff.handoff_text(tmp_path, _role(tmp_path))
    assert f"`{data['next_action']}`" in text
    assert f"**Unit in flight:** {data['unit_in_flight']}" in text


def test_write_check_json_are_role_only(tmp_path, monkeypatch):
    _fixture(tmp_path)
    monkeypatch.setattr(handoff, "ROOT", tmp_path)
    for flag in ("--write", "--check", "--json"):
        assert handoff.main(["--track", "alpha", flag]) == 2
    assert handoff.main(["--track", "alpha"]) == 0
    assert not (tmp_path / "docs" / "roles" / "alpha").exists()


def test_write_refuses_a_seat_with_no_directory(tmp_path, monkeypatch):
    """`scheduler` is in the registry but owns no narrative artifacts (note §2.4) — writing must
    not mint a seat directory as a side effect."""
    _fixture(tmp_path)
    monkeypatch.setattr(handoff, "ROOT", tmp_path)
    assert handoff.main(["--role", "scheduler", "--write"]) == 2
    assert not (tmp_path / "docs" / "roles" / "scheduler").exists()


# ── the structural falsifiers ───────────────────────────────────
def test_dry_no_core_import_and_reuses_board_and_lib():
    src = (REPO / "scripts" / "handoff.py").read_text(encoding="utf-8")
    imported: set[str] = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name.split(".")[0])
    assert "core" not in imported, "handoff must never import core (repo-workflow tooling)"
    assert "board" in imported, "handoff must reuse board's scanners, not re-derive them"
    assert "_lib" in imported, "handoff must reuse _lib's front-matter machinery"
    assert "yaml" not in imported, "no second YAML parser"
