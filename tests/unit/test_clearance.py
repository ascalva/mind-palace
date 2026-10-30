"""The clearance lattice at runtime (core/kernel/clearance.py; dn-vector-membership-store A3.4).

Owner ruling 2026-10-29: "accessible records without the correct permission should be
unrepresentable". Proves the runtime half: nothing outside the authorities can mint a clearance or
a cleared record, a record of a class the clearance does not admit cannot be constructed, cleared
rows cannot be edited in place, and every named grant's runtime classes equal the members of its
static label (so a grant cannot say one thing to mypy and another to the store). The static half
is tests/integrity/test_clearance_types.py.
"""

from __future__ import annotations

import pickle
import typing

import pytest

from core.kernel import clearance as cl
from core.kernel.clearance import (
    CODE_READ,
    CURATED_READ,
    DIALOGUE_READ,
    MAINTENANCE_READ,
    MIRROR_READ,
    OBSERVED_READ,
    Clearance,
    ClearanceForgery,
    ClearanceViolation,
    Occupancy,
    PlaneHit,
    Row,
    classes_of,
    narrow_hit,
    narrow_row,
)
from core.kernel.provenance import MIRROR_READABLE, Provenance
from core.kernel.scope import Stratum

SOLO, DIALOGUE, OBSERVED = (Provenance.AUTHORED_SOLO, Provenance.AUTHORED_DIALOGUE,
                            Provenance.OBSERVED)


def _occ[L: Provenance](c: Clearance[L], prov: Provenance, atom: str = "prose:a") -> Occupancy[L]:
    return Occupancy(c, atom_id=atom, source_path="n.md", digest="d" * 64, chunk_index=0,
                     title="t", provenance=prov, current=True, mint=cl._MINT)


# ── minting ────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("forged", [None, object(), "mint"])
def test_nothing_outside_the_authorities_can_mint(forged):
    with pytest.raises(ClearanceForgery):
        Clearance({SOLO}, "me", mint=forged)  # type: ignore[arg-type]  # the forgery under test
    with pytest.raises(ClearanceForgery):
        Row(MIRROR_READ, {"provenance": "authored-solo"}, mint=forged)  # type: ignore[arg-type]
    with pytest.raises(ClearanceForgery):
        Occupancy(MIRROR_READ, atom_id="a", source_path="p", digest="d", chunk_index=0, title="",
                  provenance=SOLO, current=True, mint=forged)  # type: ignore[arg-type]


def test_a_clearance_is_immutable_and_equal_by_classes():
    with pytest.raises(AttributeError):
        MIRROR_READ._classes = frozenset(Provenance)  # type: ignore[misc]  # the write under test
    assert cl._mint(MIRROR_READABLE, "someone else") == MIRROR_READ
    assert hash(cl._mint(MIRROR_READABLE, "x")) == hash(MIRROR_READ)


@pytest.mark.parametrize(("grant", "alias"), [
    (MIRROR_READ, cl.MirrorClass), (CURATED_READ, cl.CuratedClass), (CODE_READ, cl.CodeClass),
    (DIALOGUE_READ, cl.DialogueClass), (OBSERVED_READ, cl.ObservedClass)])
def test_every_grant_says_the_same_thing_to_the_store_and_to_mypy(grant, alias):
    assert grant.classes == frozenset(typing.get_args(alias.__value__))


def test_maintenance_is_every_class_and_the_mirror_is_exactly_mr():
    assert MAINTENANCE_READ.classes == frozenset(Provenance)
    assert MIRROR_READ.classes == MIRROR_READABLE


def test_admits_is_fail_closed_on_anything_that_is_not_a_class():
    assert MIRROR_READ.admits("authored-solo") and MIRROR_READ.admits(SOLO)
    for junk in (None, "", "authored", "AUTHORED-SOLO", 3, OBSERVED, "observed"):
        assert not MIRROR_READ.admits(junk)


def test_meet_only_narrows():
    m = DIALOGUE_READ.meet(MIRROR_READ)
    assert m.classes == frozenset({DIALOGUE})
    assert MIRROR_READ.meet(CODE_READ).classes == frozenset()       # disjoint → reads nothing


def test_strata_map_to_the_classes_their_rows_carry():
    assert classes_of([Stratum.MIRROR_AUTHORED]) == MIRROR_READABLE
    assert classes_of([Stratum.DIALOGUE]) == frozenset({DIALOGUE, OBSERVED})
    assert classes_of([Stratum.REFERENCE, Stratum.CURATED]) == frozenset(
        {Provenance.CODE, Provenance.CURATED})
    assert classes_of([Stratum.OPS, Stratum.WORLD]) == frozenset()


# ── cleared rows ───────────────────────────────────────────────────────────────────────────────

def test_a_row_of_an_uncleared_class_cannot_exist():
    with pytest.raises(ClearanceViolation):
        Row(MIRROR_READ, {"provenance": "observed", "text": "the model's words"}, mint=cl._MINT)
    with pytest.raises(ClearanceViolation):
        Row(MIRROR_READ, {"text": "no class at all"}, mint=cl._MINT)


def test_a_cleared_row_reads_like_a_mapping_and_cannot_be_edited():
    r = Row(MIRROR_READ, {"provenance": "authored-solo", "text": "mine", "chunk_index": 2},
            mint=cl._MINT)
    assert r["text"] == "mine" and r.get("missing") is None and len(r) == 3
    assert r == {"provenance": "authored-solo", "text": "mine", "chunk_index": 2}
    assert r.provenance is SOLO
    with pytest.raises(TypeError):
        r["provenance"] = "observed"  # type: ignore[index]  # the relabel under test
    with pytest.raises(TypeError):
        r |= {"provenance": "observed"}  # type: ignore[operator]
    with pytest.raises(AttributeError):
        r._fields = {}  # type: ignore[misc]
    copy = dict(r)
    copy["text"] = "a new value, unlabelled"
    assert type(copy) is dict and r["text"] == "mine"


def test_a_row_pickles_as_a_plain_unlabelled_dict():
    r = Row(MIRROR_READ, {"provenance": "authored-solo"}, mint=cl._MINT)
    back = pickle.loads(pickle.dumps(r))
    assert type(back) is dict and back == {"provenance": "authored-solo"}


def test_the_fields_a_row_was_built_from_cannot_reach_it_later():
    src = {"provenance": "authored-solo", "text": "before"}
    r = Row(MIRROR_READ, src, mint=cl._MINT)
    src["provenance"] = "observed"
    assert r["provenance"] == "authored-solo"


# ── occupancies and hits ───────────────────────────────────────────────────────────────────────

def test_an_uncleared_occupancy_cannot_exist():
    with pytest.raises(ClearanceViolation):
        _occ(MIRROR_READ, OBSERVED)
    assert _occ(MIRROR_READ, SOLO).provenance is SOLO


def test_a_hit_needs_a_cleared_occupancy_of_its_own_atom():
    with pytest.raises(ClearanceViolation):
        PlaneHit(MIRROR_READ, atom_id="prose:a", text="x", distance=0.1, vector=None,
                 occupancies=[], mint=cl._MINT)
    with pytest.raises(ClearanceViolation):
        PlaneHit(MIRROR_READ, atom_id="prose:a", text="x", distance=0.1, vector=None,
                 occupancies=[_occ(MIRROR_READ, SOLO, atom="prose:b")], mint=cl._MINT)
    # an occupancy minted under a WIDER clearance still cannot ride a mirror hit
    wide = _occ(MAINTENANCE_READ, OBSERVED)
    with pytest.raises(ClearanceViolation):
        PlaneHit(MIRROR_READ, atom_id="prose:a", text="x", distance=0.1, vector=None,
                 occupancies=[wide], mint=cl._MINT)  # type: ignore[list-item]


def test_records_are_immutable():
    o = _occ(MIRROR_READ, SOLO)
    with pytest.raises(AttributeError):
        o._provenance = OBSERVED  # type: ignore[misc]


# ── narrowing: the only checked way down ───────────────────────────────────────────────────────

def test_narrowing_keeps_what_the_narrow_clearance_admits_and_nothing_else():
    wide = Row(MAINTENANCE_READ, {"provenance": "observed"}, mint=cl._MINT)
    assert narrow_row(wide, MIRROR_READ) is None
    solo = Row(MAINTENANCE_READ, {"provenance": "authored-solo"}, mint=cl._MINT)
    got = narrow_row(solo, MIRROR_READ)
    assert got is not None and got.provenance is SOLO

    hit = PlaneHit(MAINTENANCE_READ, atom_id="prose:a", text="x", distance=0.2, vector=None,
                   occupancies=[_occ(MAINTENANCE_READ, SOLO), _occ(MAINTENANCE_READ, OBSERVED)],
                   mint=cl._MINT)
    mirror = narrow_hit(hit, MIRROR_READ)
    assert mirror is not None and [o.provenance for o in mirror.occupancies] == [SOLO]
    assert narrow_hit(hit, CODE_READ) is None
