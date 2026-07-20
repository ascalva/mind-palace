"""The exhaust lane — the ingest-invariant (dn-exhaust-lane §2.2) and the report writer (§2.4).

Two properties, one file (bp-075 Items 2 + 3):

  * The INGEST INVARIANT: no config-pinned ingest/source root may lie inside the exhaust lane —
    ingesting a system-emitted report would be recursive self-ingestion of meta-content. Proved
    against the real merged config (passes today) AND against a planted config that puts a source
    inside exhaust (the test-of-the-test: the check actually catches a violation, not vacuous).

  * The WRITER: `scripts/exhaust_report.py` places a composed HTML report at its dated name under
    `<exhaust>/reports/`, creates the dir, refuses a silent overwrite (exit 1 / --force), and never
    imports `core` (repo-workflow tooling — the docket.py AST precedent).
"""

from __future__ import annotations

import ast
import dataclasses
import sys
import types
from datetime import date
from pathlib import Path

import pytest

from config.loader import get_config

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import exhaust_report  # type: ignore[import-not-found]  # noqa: E402

# --------------------------------------------------------------------------------------------
# Item 2 — the ingest-invariant (note §2.2)
# --------------------------------------------------------------------------------------------


def _resolved(p: Path) -> Path:
    """Symlink-normalized absolute form — `~` expanded, `resolve()`d (so /tmp vs /private/tmp and
    /var vs /private/var can't create a false negative). `resolve()` is non-strict: it normalizes
    paths that don't exist yet (a fresh clone has neither the vault nor the exhaust dir on disk)."""
    return p.expanduser().resolve()


def _ingest_source_roots(cfg: object) -> list[Path]:
    """Every config-pinned root the ingest pipeline reads owner CONTENT from — the roots the
    exhaust invariant (note §2.2) forbids from lying inside the exhaust lane. Two today, each
    grep-verified against its live consumer:

      * ``cfg.vault.path`` — the authored corpus (core/ingest/*, scheduler/vault_sync.py).
      * the chat transcripts dir — the dialogue sensor's source (scheduler/chat_sync.py), resolved
        via the sensor's OWN ``_default_transcripts_dir()`` when unset (finding-0108 G1), so this
        test reuses the real resolver rather than re-deriving ``~/.claude/projects/<slug>``.

    A new ingest lane is a deliberate design act; its root is added here when one lands. This is a
    semantically-grounded enumeration of the ingest lanes, not a drift-prone list of literal paths —
    the config is the single source of truth for each root's value (note §2.2)."""
    from ops.chat_sensor import _default_transcripts_dir

    return [
        cfg.vault.path,  # type: ignore[attr-defined]
        cfg.chat.transcripts_dir or _default_transcripts_dir(),  # type: ignore[attr-defined]
    ]


def _sources_inside_exhaust(cfg: object) -> list[Path]:
    """Ingest source roots that lie equal-to-or-under the exhaust root — the invariant's offenders
    (empty == the invariant holds)."""
    exhaust = _resolved(cfg.exhaust.path)  # type: ignore[attr-defined]
    return [r for r in _ingest_source_roots(cfg) if _resolved(r).is_relative_to(exhaust)]


def test_no_ingest_root_lies_inside_exhaust() -> None:
    """The note §2.2 invariant against the REAL merged config: every configured ingest source
    resolves OUTSIDE the exhaust lane."""
    assert _sources_inside_exhaust(get_config()) == []


def test_the_invariant_check_catches_a_source_inside_exhaust(tmp_path: Path) -> None:
    """Test-of-the-test: plant a config whose vault (an ingest source) sits INSIDE exhaust and
    assert the check flags it — proving the passing case above is not vacuous."""
    cfg = get_config()
    exhaust = tmp_path / "exhaust"
    planted_source = exhaust / "reports" / "leaked-corpus"
    bad = dataclasses.replace(
        cfg,
        exhaust=dataclasses.replace(cfg.exhaust, path=exhaust),
        vault=dataclasses.replace(cfg.vault, path=planted_source),
    )
    offenders = _sources_inside_exhaust(bad)
    assert _resolved(planted_source) in offenders
    assert offenders, "the invariant check must flag a source planted inside exhaust"


# --------------------------------------------------------------------------------------------
# Item 3 — the report writer, scripts/exhaust_report.py
# --------------------------------------------------------------------------------------------


def _stub_config(exhaust_root: Path) -> types.SimpleNamespace:
    """A minimal stand-in for the frozen Config, exposing only `.exhaust.path` — the one field the
    writer reads. Lets a test point the writer at a tmp exhaust root without a real toml."""
    return types.SimpleNamespace(exhaust=types.SimpleNamespace(path=exhaust_root))


def test_places_report_at_dated_name(tmp_path, monkeypatch) -> None:
    exhaust = tmp_path / "exhaust"
    monkeypatch.setattr(exhaust_report, "get_config", lambda: _stub_config(exhaust))
    src = tmp_path / "composed.html"
    src.write_text("<h1>report</h1>", encoding="utf-8")

    dest = exhaust_report.place_report(src, "bp-075", "exhaust-lane")

    expected = exhaust / "reports" / f"{date.today().isoformat()}-bp-075-exhaust-lane.html"
    assert dest == expected
    assert dest.parent.is_dir()  # reports/ created (mkdir -p)
    assert dest.read_text(encoding="utf-8") == "<h1>report</h1>"


def test_refuses_silent_overwrite_and_force_replaces(tmp_path, monkeypatch) -> None:
    exhaust = tmp_path / "exhaust"
    monkeypatch.setattr(exhaust_report, "get_config", lambda: _stub_config(exhaust))
    first = tmp_path / "a.html"
    first.write_text("first", encoding="utf-8")
    second = tmp_path / "b.html"
    second.write_text("second", encoding="utf-8")

    dest = exhaust_report.place_report(first, "bp-075", "s")
    with pytest.raises(FileExistsError):
        exhaust_report.place_report(second, "bp-075", "s")
    assert dest.read_text(encoding="utf-8") == "first"  # the refusal left the original intact

    replaced = exhaust_report.place_report(second, "bp-075", "s", force=True)
    assert replaced == dest
    assert dest.read_text(encoding="utf-8") == "second"


def test_missing_source_raises(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(exhaust_report, "get_config", lambda: _stub_config(tmp_path / "exhaust"))
    with pytest.raises(FileNotFoundError):
        exhaust_report.place_report(tmp_path / "nope.html", "bp-075", "s")


def test_main_cli_places_refuses_and_forces(tmp_path, monkeypatch, capsys) -> None:
    exhaust = tmp_path / "exhaust"
    monkeypatch.setattr(exhaust_report, "get_config", lambda: _stub_config(exhaust))
    src = tmp_path / "rep.html"
    src.write_text("<p>x</p>", encoding="utf-8")

    rc = exhaust_report.main([str(src), "--plan", "bp-075", "--slug", "abc"])
    assert rc == 0
    printed = capsys.readouterr().out.strip()
    expected = exhaust / "reports" / f"{date.today().isoformat()}-bp-075-abc.html"
    assert printed == str(expected)
    assert expected.is_file()

    # a second placement at the same dated name is refused (exit 1) — no silent clobber
    assert exhaust_report.main([str(src), "--plan", "bp-075", "--slug", "abc"]) == 1
    # --force replaces it (exit 0)
    assert exhaust_report.main([str(src), "--plan", "bp-075", "--slug", "abc", "--force"]) == 0


def test_writer_imports_stdlib_and_config_only() -> None:
    """The no-core falsifier (note §2.4, docket precedent): the writer is repo-workflow tooling —
    it imports stdlib + the `config` facade (for the exhaust root, SSOT) and NEVER `core`."""
    src = (REPO / "scripts" / "exhaust_report.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name.split(".")[0])

    assert "core" not in imported, "the writer must never import core (repo-workflow tooling)"
    assert "config" in imported, "the writer reads the exhaust root from the config facade (SSOT)"
    allowed = {"__future__", "argparse", "shutil", "sys", "datetime", "pathlib", "config"}
    assert imported <= allowed, f"unexpected imports: {imported - allowed}"
