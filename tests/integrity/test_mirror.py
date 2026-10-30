"""MirrorView — the firewall as an unrepresentable-state type (Invariant 6, gap G3).

These assert the *structural* promotion: a MirrorView holding non-authored rows cannot be
constructed (not via project, not by hand), so handing an introspective agent observed data
is a type error, not a runtime check. The Hypothesis property (observed never survives a
projection, over arbitrary mixed inputs) lives in test_properties.py.
"""

from typing import Any

import pytest

from core.kernel.clearance import Clearance
from core.kernel.mirror import MirrorView, NonMirrorRowError
from core.kernel.provenance import MIRROR_READABLE, Provenance


class FakeStore:
    def __init__(self, rows):
        self.rows = rows
        self.last_clearance: Any = "unset"

    def all_rows(self, *, clearance: Clearance[Provenance]):
        self.last_clearance = clearance
        return [r for r in self.rows if clearance.admits(r.get("provenance"))]


MIXED = [
    {"digest": "a", "title": "auth", "provenance": "authored-solo", "vector": [1.0]},
    {"digest": "b", "title": "obs", "provenance": "observed", "vector": [0.0]},
    {"digest": "c", "title": "interp", "provenance": "interpreted", "vector": [0.5]},
]


def test_project_applies_the_mirror_projection():
    store = FakeStore(list(MIXED))
    view = MirrorView.project(store)
    assert store.last_clearance.classes == MIRROR_READABLE            # read restricted to MR
    assert {r["provenance"] for r in view.rows()} == {Provenance.AUTHORED_SOLO.value}
    assert len(view) == 1


def test_direct_construction_with_a_non_authored_row_is_unrepresentable():
    # The structural guarantee: you cannot build a MirrorView holding observed data at all.
    with pytest.raises(NonMirrorRowError):
        MirrorView(_rows=({"provenance": "observed"},))
    with pytest.raises(NonMirrorRowError):
        MirrorView(_rows=({"provenance": "interpreted"},))


def test_authored_rows_construct_fine():
    view = MirrorView(_rows=({"provenance": "authored-solo", "digest": "x"},))
    assert len(view) == 1


def test_empty_view_is_valid():
    assert len(MirrorView()) == 0
    assert MirrorView().rows() == []
