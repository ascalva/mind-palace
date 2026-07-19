"""readmap — quickfix emission of a seal's read-map block (bp-072 Item 2).

Proves: with two ```read-map blocks in a journal the LAST is emitted verbatim; a journal
with no block exits 1 with the legacy-prose message (never guesses at prose); a listed
path that no longer exists warns to stderr but the line is STILL emitted. Live: the real
bp-073 seal is prose, so `readmap.py bp-073` exits 1 — honest.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import readmap  # noqa: E402


def _journal(root: Path, plan_id: str, text: str) -> None:
    d = root / "docs" / "build-plans" / plan_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "journal.md").write_text(text, encoding="utf-8")


TWO_BLOCKS = """\
# Journal

## SEAL (first)
```read-map
old/path.py:10: the first seal's map — should NOT be emitted
```

## SEAL (second, current)
```read-map
scripts/docket.py:1: the derived view entry point
scripts/readmap.py:1: this very tool
```
"""

PROSE_ONLY = """\
# Journal

## SEAL
**Read map (concept-bearing lines):** `foo.py` the thing, `bar.py` the other thing.
"""


def test_last_block_emitted_verbatim(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(readmap, "ROOT", tmp_path)
    _journal(tmp_path, "bp-999", TWO_BLOCKS)
    rc = readmap.main(["bp-999"])
    out = capsys.readouterr().out
    assert rc == 0
    # only the LAST block's lines, verbatim
    assert "scripts/docket.py:1: the derived view entry point" in out
    assert "scripts/readmap.py:1: this very tool" in out
    assert "old/path.py" not in out


def test_no_block_exits_one_with_legacy_message(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(readmap, "ROOT", tmp_path)
    _journal(tmp_path, "bp-998", PROSE_ONLY)
    rc = readmap.main(["bp-998"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "no structured read-map block" in err
    assert "legacy prose seal" in err


def test_missing_path_warns_but_line_kept(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(readmap, "ROOT", tmp_path)
    (tmp_path / "present.py").write_text("x\n", encoding="utf-8")  # a path that DOES exist
    block = "# J\n```read-map\ndoes/not/exist.py:5: gone but recorded\npresent.py:1: present\n```\n"
    _journal(tmp_path, "bp-997", block)
    rc = readmap.main(["bp-997"])
    cap = capsys.readouterr()
    assert rc == 0
    assert "does/not/exist.py:5: gone but recorded" in cap.out  # line STILL emitted
    assert "present.py:1: present" in cap.out
    assert "does/not/exist.py no longer exists" in cap.err       # the missing one warned
    # exactly ONE warning — the present path does not warn
    assert cap.err.count("no longer exists") == 1


def test_missing_journal_exits_one(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(readmap, "ROOT", tmp_path)
    rc = readmap.main(["bp-nope"])
    assert rc == 1
    assert "no journal" in capsys.readouterr().err


def test_extract_block_returns_none_without_fence():
    assert readmap.extract_block("no fence here at all") is None
    assert readmap.extract_block("```read-map\na.py:1: hi\n```")[0] == "a.py:1: hi"


def test_live_bp073_is_prose_exit_one(capsys):
    """The real bp-073 seal is prose — readmap must say so and exit 1, not guess (Q4)."""
    if not (REPO / "docs" / "build-plans" / "bp-073" / "journal.md").exists():
        return  # bp-073 absent in this checkout — nothing to assert
    rc = readmap.main(["bp-073"])
    assert rc == 1
    assert "no structured read-map block" in capsys.readouterr().err
