"""Unit tests for the typed/signed EdgeStore (H1; companion III §1.2).

Proves: an edge round-trips with its polarity (EdgeSign); ids are content-derived so re-asserting
is idempotent; the sign is a closed ±1 set (out-of-set values rejected at the boundary); negative
strength is refused (polarity lives in `sign`, not `w`).
"""

import pytest

from core.kernel.complex_types import EdgeSign
from core.stores.edges import CONTRADICTS, SUPPORTS, EdgeStore


def _store(tmp_path):
    return EdgeStore(tmp_path / "edges.sqlite")


def test_add_and_read_back(tmp_path):
    s = _store(tmp_path)
    e = s.add("a", "b", sign=EdgeSign.CONTRADICT, rel_type=CONTRADICTS, w=0.8)
    assert e.sign is EdgeSign.CONTRADICT
    got = s.all()[0]
    assert (got.u, got.v, got.rel_type, got.w) == ("a", "b", CONTRADICTS, 0.8)
    assert got.sign is EdgeSign.CONTRADICT           # polarity survives the round-trip as the enum


def test_ids_are_content_derived_so_reassertion_is_idempotent(tmp_path):
    s = _store(tmp_path)
    s.add("a", "b", sign=EdgeSign.SUPPORT, rel_type=SUPPORTS)
    s.add("a", "b", sign=EdgeSign.SUPPORT, rel_type=SUPPORTS, w=2.0)   # same (u,v,rel) → replace
    assert s.count() == 1
    assert s.all()[0].w == 2.0


def test_reset_is_regenerable(tmp_path):
    s = _store(tmp_path)
    s.add("a", "b", sign=EdgeSign.SUPPORT, rel_type=SUPPORTS)
    s.reset()
    assert s.count() == 0


def test_negative_strength_is_refused(tmp_path):
    s = _store(tmp_path)
    with pytest.raises(ValueError):
        s.add("a", "b", sign=EdgeSign.CONTRADICT, rel_type=CONTRADICTS, w=-1.0)


def test_sign_is_a_closed_set(tmp_path):
    s = _store(tmp_path)
    with pytest.raises(ValueError):
        s.add("a", "b", sign=3, rel_type=CONTRADICTS)    # not ±1 → EdgeSign rejects it


def test_a_note_does_not_relate_to_itself(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """A self loop is refused at the store (the review of 2026-11-05): the Lean's balance counts a
    negative loop as frustration and the code's test skips loops, so the store holds none for the
    two to disagree on. The MCP `link` naming one note twice, by path and by title, lands here."""
    store = _store(tmp_path)
    with pytest.raises(ValueError, match="two distinct notes"):
        store.add("da", "da", sign=EdgeSign.CONTRADICT, rel_type="contradicts")
    assert store.count() == 0
