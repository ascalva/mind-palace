"""Derived store for INTERPRETED artifacts (BUILD-SPEC §8).

Proves: dreams + findings persist and read back; the store writes INTERPRETED and nothing
else (the §8 firewall is structural — `add` has no provenance parameter); ids are
content-derived so re-runs are idempotent; reset() makes it regenerable.
"""

import inspect

import pytest

from core.provenance import Provenance
from core.stores.derived import DREAM, FINDING, DerivationCycleError, DerivedStore


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


# --- derivation edges + acyclicity (gap G2 / Invariant 10) ----------------------

def test_derived_from_is_stored_and_read_back(tmp_path):
    s = _store(tmp_path)
    a = s.add(kind=DREAM, summary="t", subjects=["a", "b"], derived_from=["dig-a", "dig-b"])
    assert a.derived_from == ("dig-a", "dig-b")
    assert s.all(kind=DREAM)[0].derived_from == ("dig-a", "dig-b")


def test_depth_authored_leaves_are_depth_one(tmp_path):
    # A dream over authored note digests (leaves, depth 0) is itself depth 1.
    s = _store(tmp_path)
    dream = s.add(kind=DREAM, summary="t", subjects=["a"], derived_from=["dig-a"])
    assert s.depth(dream.id) == 1
    assert s.leaf_refs(dream.id) == {"dig-a"}            # bottoms out in an authored leaf


def test_depth_increases_with_a_second_order_artifact(tmp_path):
    # Recursive dreaming (a flag-OFF R&D path) would build an artifact FROM another artifact;
    # the store computes the deeper depth and keeps the support closure's authored leaf.
    s = _store(tmp_path)
    first = s.add(kind=DREAM, summary="d1", subjects=["a"], derived_from=["dig-a"])
    second = s.add(kind=DREAM, summary="d2", subjects=["meta"], derived_from=[first.id])
    assert s.depth(second.id) == 2
    assert s.leaf_refs(second.id) == {"dig-a"}           # closure still bottoms out authored


def test_cycle_is_refused_at_insert(tmp_path):
    # Build A <- B, then attempting A derived_from B (which already descends to A) is a cycle.
    s = _store(tmp_path)
    a = s.add(kind=DREAM, summary="A", subjects=["a"], derived_from=["dig-a"])
    b = s.add(kind=DREAM, summary="B", subjects=["b"], derived_from=[a.id])
    # Re-adding A with B as a parent would close the loop A -> B -> A.
    with pytest.raises(DerivationCycleError):
        s.add(kind=DREAM, summary="A", subjects=["a"], derived_from=[b.id])


def test_self_reference_is_refused(tmp_path):
    s = _store(tmp_path)
    # The id is content-derived; precompute it to feed it back as its own parent.
    from core.stores.derived import _artifact_id
    self_id = _artifact_id(DREAM, None, ("a",))
    with pytest.raises(DerivationCycleError):
        s.add(kind=DREAM, summary="loop", subjects=["a"], derived_from=[self_id])


# --- attestation_id link (attestation layer, Step 2) ----------------------------

def test_attestation_id_is_stored_and_read_back(tmp_path):
    s = _store(tmp_path)
    a = s.add(kind=DREAM, summary="t", subjects=["a"], derived_from=["dig-a"],
              attestation_id="att-123")
    assert a.attestation_id == "att-123"
    assert s.all(kind=DREAM)[0].attestation_id == "att-123"


def test_attestation_id_defaults_to_none(tmp_path):
    # A record written without an attestor (or before the layer existed) has no link.
    s = _store(tmp_path)
    assert s.add(kind=DREAM, summary="t", subjects=["a"]).attestation_id is None
