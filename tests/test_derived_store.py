"""Derived store for INTERPRETED artifacts (BUILD-SPEC §8).

Proves: dreams + findings persist and read back; the store writes INTERPRETED and nothing
else (the §8 firewall is structural — `add` has no provenance parameter); ids are
content-derived so re-runs are idempotent; reset() makes it regenerable.
"""

import inspect

from core.provenance import Provenance
from core.stores.derived import DREAM, FINDING, DerivedStore


def _store(tmp_path):
    return DerivedStore(tmp_path / "derived.sqlite")


def test_add_and_read_back_dream_and_finding(tmp_path):
    s = _store(tmp_path)
    s.add(kind=DREAM, summary="a theme", subjects=["note-a", "note-b"], data={"k": 1})
    s.add(kind=FINDING, subkind="near_duplicate", summary="dup", subjects=["x", "y"])
    assert s.count() == 2
    assert s.count(kind=DREAM) == 1
    dream = s.all(kind=DREAM)[0]
    assert dream.summary == "a theme"
    assert dream.subjects == ("note-a", "note-b")
    assert dream.data == {"k": 1}
    assert s.all(kind=FINDING, subkind="near_duplicate")[0].subjects == ("x", "y")


def test_everything_stored_is_interpreted(tmp_path):
    s = _store(tmp_path)
    s.add(kind=DREAM, summary="t", subjects=["a"])
    assert all(art.provenance is Provenance.INTERPRETED for art in s.all())


def test_add_has_no_provenance_parameter(tmp_path):
    # Structural firewall (§8): the derived store cannot be told to write authored truth,
    # because there is no provenance argument to set — not "checked then refused".
    assert "provenance" not in inspect.signature(DerivedStore.add).parameters


def test_ids_are_content_derived_so_reruns_are_idempotent(tmp_path):
    s = _store(tmp_path)
    a = s.add(kind=FINDING, subkind="near_duplicate", summary="v1", subjects=["a", "b"])
    b = s.add(kind=FINDING, subkind="near_duplicate", summary="v2", subjects=["b", "a"])
    assert a.id == b.id            # same kind+subkind+subjects -> same id (order-insensitive)
    assert s.count() == 1          # second add replaced the first, not duplicated
    assert s.all()[0].summary == "v2"


def test_reset_makes_it_regenerable(tmp_path):
    s = _store(tmp_path)
    s.add(kind=DREAM, summary="t", subjects=["a"])
    s.reset()
    assert s.count() == 0
