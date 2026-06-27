"""Content-addressed raw store: dedup, round-trip, immutability (BUILD-SPEC §8)."""

from core.stores.rawstore import RawStore


def test_content_addressed_dedup(tmp_path):
    raw = RawStore(tmp_path / "raw")
    d1, new1 = raw.add_text("hello world")
    d2, new2 = raw.add_text("hello world")
    assert d1 == d2
    assert new1 is True and new2 is False  # identical content stored once
    assert len(d1) == 64


def test_roundtrip_and_distinct_content(tmp_path):
    raw = RawStore(tmp_path / "raw")
    da, _ = raw.add_text("a")
    db, _ = raw.add_text("b")
    assert da != db
    assert raw.get(da) == b"a"
    assert raw.exists(da)
    assert not raw.exists("0" * 64)


def test_immutable_never_rewritten(tmp_path):
    raw = RawStore(tmp_path / "raw")
    d, _ = raw.add_text("x")
    p = raw._path(d)
    mtime = p.stat().st_mtime_ns
    raw.add_text("x")  # re-add is a no-op
    assert p.stat().st_mtime_ns == mtime
