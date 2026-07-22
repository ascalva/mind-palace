"""The board — the derived tracks × phases view (WF-1, bp-096 Item 4).

Proves the generator is DERIVED and cannot drift: two renders over an unchanged tree are
byte-equal (F-WF2), every rendered table row is ≤190 chars (owner rule), `--queue-count`
prints the count of tracks owed a deskcheck (deskcheck-pending ∪ standing-backlog, the §6
queue definition), and the coordinate check surfaces a `track:` slug with no manifest
(F-WF1). The phase function matches the note D2 table. The DRY falsifier is structural:
board imports `_lib`'s parser rather than re-deriving one, and never imports `core`.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import board  # type: ignore[import-not-found]  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _manifest(
    root: Path,
    slug: str,
    *,
    status: str = "active",
    warrant: str = "null",
    dod: list[str] | None = None,
    backlog: str = "null",
    title: str | None = None,
) -> None:
    title = title or f"{slug.title()} — the {slug} track"
    lines = ["---", "type: track", f"slug: {slug}", f"title: {title}",
             f"status: {status}", f"warrant: {warrant}", "audit_refs: []", "dod:"]
    lines += [f"  - {d}" for d in (dod or [])]
    lines += [f"backlog_deskcheck: {backlog}", "links: []", "---", f"# Track — {title}"]
    _write(root / "docs" / "tracks" / f"{slug}.md", "\n".join(lines) + "\n")


def _plan(root: Path, pid: str, track: str, status: str) -> None:
    fm = f"---\ntype: build-plan\nid: {pid}\ntrack: {track}\nstatus: {status}\n---\n"
    body = fm + f"\n# Build Plan — {pid} the thing\n"
    _write(root / "docs" / "build-plans" / pid / "plan.md", body)


def _note(root: Path, stem: str, track: str, status: str) -> None:
    fm = f"---\ntype: design-note\ntrack: {track}\nstatus: {status}\n---\n"
    _write(root / "docs" / "design-notes" / f"{stem}.md", fm + f"\n# {stem}\n")


def _dc(root: Path, dcid: str, track: str, verdict: str) -> None:
    fm = f"---\ntype: deskcheck\nid: {dcid}\ntrack: {track}\nverdict: {verdict}\n---\n"
    _write(root / "docs" / "deskchecks" / f"{dcid}.md", fm + f"\n# {dcid}\n")


def _fixture(root: Path) -> None:
    # alpha: build phase (a ready plan) BUT a standing backlog ⇒ owed.
    _manifest(root, "alpha", backlog="demo the alpha wave (working, or its true state)")
    _plan(root, "bp-201", "alpha", "complete")
    _plan(root, "bp-202", "alpha", "ready")
    # beta: all plans complete, no backlog ⇒ deskcheck-pending ⇒ owed by phase.
    _manifest(root, "beta")
    _plan(root, "bp-203", "beta", "complete")
    _plan(root, "bp-204", "beta", "complete")
    # gamma: no plans, no note, null backlog ⇒ design-pass, NOT owed.
    _manifest(root, "gamma")
    # delta: dormant-by-design + confirm-only backlog ⇒ dormant, owed (confirm dormancy).
    _manifest(root, "delta", status="dormant-by-design", warrant="finding-0011",
              backlog="confirm dormancy still intended")
    # epsilon: a single ready plan, null backlog ⇒ build, NOT owed.
    _manifest(root, "epsilon")
    _plan(root, "bp-205", "epsilon", "ready")


def test_idempotent_over_unchanged_tree(tmp_path):
    """F-WF2: two renders over an unchanged tree are byte-equal (no persisted state)."""
    _fixture(tmp_path)
    assert board.board_text(tmp_path) == board.board_text(tmp_path)
    assert board.queue_text(tmp_path) == board.queue_text(tmp_path)


def test_every_rendered_row_within_190(tmp_path):
    _fixture(tmp_path)
    for doc in (board.board_text(tmp_path), board.queue_text(tmp_path)):
        for ln in doc.splitlines():
            if ln.startswith("|"):
                assert len(ln) <= board.MAX_ROW, f"row exceeds {board.MAX_ROW}: {ln!r}"


def test_long_backlog_is_capped(tmp_path):
    _manifest(tmp_path, "verbose", backlog="x " * 200)  # ~400 chars — must be truncated
    _plan(tmp_path, "bp-900", "verbose", "complete")
    rows = [ln for ln in board.queue_text(tmp_path).splitlines() if ln.startswith("| 1 |")]
    assert rows and len(rows[0]) <= board.MAX_ROW
    assert rows[0].rstrip().endswith("… |")


def test_queue_count_is_the_owed_integer(tmp_path, monkeypatch, capsys):
    _fixture(tmp_path)
    # owed = alpha (backlog) + beta (deskcheck-pending) + delta (dormant + backlog) = 3.
    assert board.queue_count(tmp_path) == 3
    monkeypatch.setattr(board, "ROOT", tmp_path)
    rc = board.main(["--queue-count"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert out == "3" and int(out) == 3  # exactly one integer, nothing else


def test_queue_lists_owed_and_excludes_unowed(tmp_path):
    _fixture(tmp_path)
    q = board.queue_text(tmp_path)
    assert "Alpha" in q and "Beta" in q and "Delta" in q
    assert "Gamma" not in q  # design-pass, not owed
    # epsilon is a build track not owed ⇒ it appears in "Owed on completion", not "Owed now".
    owed_now = q.split("## Owed on completion")[0]
    assert "Epsilon" not in owed_now


def test_orphan_report_lists_slug_with_no_manifest(tmp_path):
    """F-WF1: a `track:` value with no manifest surfaces in the coordinate check."""
    _fixture(tmp_path)
    _plan(tmp_path, "bp-299", "ghost", "ready")  # no docs/tracks/ghost.md
    b = board.board_text(tmp_path)
    assert "ghost" in b and "no docs/tracks/ghost.md manifest" in b
    tracks, dcs, orphans = board._build(tmp_path)
    assert any("ghost" in o for o in orphans)


def test_generated_banner_present(tmp_path):
    _fixture(tmp_path)
    assert board.board_text(tmp_path).startswith(board.GENERATED_BANNER)
    assert board.queue_text(tmp_path).startswith(board.GENERATED_BANNER)


def test_write_mode_emits_both_files(tmp_path, monkeypatch, capsys):
    _fixture(tmp_path)
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(board, "ROOT", tmp_path)
    rc = board.main(["--write"])
    capsys.readouterr()
    tracks_md = tmp_path / "docs" / "TRACKS.md"
    queue_md = tmp_path / "docs" / "DESKCHECK-QUEUE.md"
    assert rc == 0 and tracks_md.exists() and queue_md.exists()
    assert tracks_md.read_text().startswith(board.GENERATED_BANNER)
    # A second --write reproduces byte-for-byte (derived, no drift).
    before = tracks_md.read_text()
    board.main(["--write"])
    assert tracks_md.read_text() == before


def test_plan_phase_matches_the_note_table():
    assert board.plan_phase("complete") == "deskcheck-pending"
    assert board.plan_phase("ready") == "build"
    assert board.plan_phase("in-progress") == "build"
    assert board.plan_phase("proposed") == "graduate"


def test_track_phase_matches_the_note_table():
    def T(**kw):
        base = dict(slug="x", title="X — x", status="active", warrant="", dod=[],
                    backlog="", audit_refs=[])
        base.update(kw)
        return board.Track(**base)  # type: ignore[arg-type]

    P = board.Plan
    # a draft note ⇒ design-pass
    draft = T(note_statuses=["draft"], plans=[P("a", "x", "ready")])
    assert board.track_phase(draft, []) == "design-pass"
    # any ready/in-progress plan ⇒ build
    building = T(note_statuses=["ratified"], plans=[P("a", "x", "ready")])
    assert board.track_phase(building, []) == "build"
    # all plans complete, no approved dc ⇒ deskcheck-pending
    assert board.track_phase(T(plans=[P("a", "x", "complete")]), []) == "deskcheck-pending"
    # ratified note, a proposed plan ⇒ graduate
    grad = T(note_statuses=["ratified"], plans=[P("a", "x", "proposed")])
    assert board.track_phase(grad, []) == "graduate"
    # dormant-by-design ⇒ dormant
    assert board.track_phase(T(status="dormant-by-design"), []) == "dormant"
    # no plans, no draft note ⇒ design work owed
    assert board.track_phase(T(), []) == "design-pass"
    # an approved dc naming the track ⇒ CLOSED
    dc = board.DeskCheck(id="dc-001", track="x", verdict="approved")
    assert board.track_phase(T(plans=[P("a", "x", "complete")]), [dc]) == "CLOSED"


def test_approved_deskcheck_moves_track_to_closed(tmp_path):
    _fixture(tmp_path)
    _dc(tmp_path, "dc-001", "beta", "approved")
    b = board.board_text(tmp_path)
    closed = b.split("## Closed")[1].split("## Coordinate check")[0]
    assert "Beta" in closed and "dc-001" in closed
    # and beta is no longer owed (it is CLOSED, not deskcheck-pending)
    assert board.queue_count(tmp_path) == 2  # alpha + delta remain


def test_null_backlog_is_treated_as_absent(tmp_path):
    """`_lib` parses YAML `null` as the string "null" — board must not count it as a backlog."""
    _manifest(tmp_path, "solo", backlog="null")
    _plan(tmp_path, "bp-700", "solo", "ready")  # build phase, no real backlog
    assert board.queue_count(tmp_path) == 0
    assert board._is_absent("null") and board._is_absent("") and board._is_absent(None)
    assert not board._is_absent("wire vs dormant")


def test_dry_no_core_import_and_reuses_lib():
    """The DRY + no-core falsifiers, enforced by static inspection of the source."""
    src = (REPO / "scripts" / "board.py").read_text()
    tree = ast.parse(src)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name.split(".")[0])
    assert "core" not in imported, "board must never import core (repo-workflow tooling)"
    assert "_lib" in imported, "board must reuse _lib's front-matter parser, not re-derive one"
    assert "yaml" not in imported, "no second YAML parser"
