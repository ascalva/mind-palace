"""Unit tests for the OBSERVED-only code-observation store (bp-012 Item 3, note B-b).

Proves: double-insert on the identity key (commit_sha, path, qualname) is idempotent;
NO API surface in the module accepts a provenance value (the Item 3 falsifier, ruled out
mechanically over every public callable); a reader filtered to OBSERVED sees all rows and
any other filter sees none; `to_row()` hardcodes `observed` so `ObservedView` admits the
rows and `MirrorView` refuses them (§2.6 — mirror-opacity, both directions).
"""

from __future__ import annotations

import inspect
from typing import cast

import pytest

import core.stores.code_observations as mod
from config.loader import Config
from core.mirror import MirrorView, NonMirrorRowError
from core.provenance import MIRROR_READABLE, Provenance
from core.sensing import ObservedView
from core.stores.code_observations import (
    CodeObservation,
    CodeObservationStore,
    batch_content_hash,
)


def _store(tmp_path) -> CodeObservationStore:
    return CodeObservationStore(tmp_path / "code_observations.sqlite")


def _obs(qualname="f", **kw) -> CodeObservation:
    base = dict(commit_sha="c1", path="a.py", qualname=qualname, kind="function",
                signature="(x)", docstring="does f")
    base.update(kw)
    return CodeObservation(**base)


# --- identity key + idempotency -------------------------------------------------------------
def test_double_insert_is_idempotent(tmp_path):
    s = _store(tmp_path)
    batch = [_obs("f"), _obs("g"), _obs("", kind="module", signature="")]
    assert s.add_batch(batch) == 3
    assert s.add_batch(batch) == 0            # second projection changes NOTHING (B-b falsifier)
    assert s.count() == 3


def test_reinsert_never_mutates_the_first_reading(tmp_path):
    s = _store(tmp_path)
    s.add_batch([_obs("f", docstring="first")])
    s.add_batch([_obs("f", docstring="second")])  # same identity key — IGNOREd, not replaced
    assert s.count() == 1
    assert s.rows_for("c1")[0]["docstring"] == "first"


# --- the falsifier: no provenance parameter exists anywhere ---------------------------------
def test_no_public_api_surface_accepts_a_provenance_value():
    """Item 3 falsifier, ruled out mechanically: every public callable in the module —
    functions, and methods of both public classes — is inspected; none may name a
    parameter that could carry a provenance/class label."""
    surfaces = []
    for name, fn in inspect.getmembers(mod, inspect.isfunction):
        if not name.startswith("_"):
            surfaces.append((f"{mod.__name__}.{name}", fn))
    for cls in (CodeObservation, CodeObservationStore):
        for name, fn in inspect.getmembers(cls, inspect.isfunction):
            if not name.startswith("_") or name == "__init__":
                surfaces.append((f"{cls.__name__}.{name}", fn))
    assert surfaces                                       # the sweep actually swept
    for label, fn in surfaces:
        params = set(inspect.signature(fn).parameters)
        assert not params & {"provenance", "provenances_write", "tier", "label"}, (
            f"{label} accepts a provenance-like parameter — the wrong-class row "
            f"must be unrepresentable at this boundary")


def test_rows_are_minted_observed_with_no_parameter(tmp_path):
    s = _store(tmp_path)
    s.add_batch([_obs("f")])
    assert {r["provenance"] for r in s.all_rows()} == {Provenance.OBSERVED.value}
    assert _obs("f").to_row()["provenance"] == Provenance.OBSERVED.value
    assert "provenance" not in _obs("f").to_dict()        # the wire payload carries no label


# --- reads ----------------------------------------------------------------------------------
def test_reader_filtered_to_observed_sees_all_rows(tmp_path):
    s = _store(tmp_path)
    s.add_batch([_obs("f"), _obs("g")])
    assert len(s.all_rows(provenances=[Provenance.OBSERVED])) == 2
    assert len(s.all_rows()) == 2
    assert s.all_rows(provenances=MIRROR_READABLE) == []  # nothing here is mirror-readable


def test_references_out_round_trips_as_typed_json(tmp_path):
    s = _store(tmp_path)
    ref = {"type": "note-citation", "target": "docs/design-notes/x.md", "source_line": 3}
    s.add_batch([_obs("f", references_out=(ref,))])
    assert s.rows_for("c1")[0]["references_out"] == [ref]


# --- §2.6 firewall: ObservedView admits, MirrorView refuses ---------------------------------
def test_observed_view_admits_and_mirror_view_refuses(tmp_path):
    s = _store(tmp_path)
    s.add_batch([_obs("f")])
    rows = tuple(s.all_rows())
    assert len(ObservedView(_rows=rows)) == 1             # the observed tier's typed container
    with pytest.raises(NonMirrorRowError):
        MirrorView(_rows=rows)                            # OBSERVED is mirror-opaque, structurally


# --- projection bookkeeping + batch hash ----------------------------------------------------
def test_projection_marks_are_idempotent(tmp_path):
    s = _store(tmp_path)
    assert not s.is_projected("c1")
    s.mark_projected("c1", "hash-a")
    s.mark_projected("c1", "hash-b")                      # re-mark is a no-op, first mark wins
    assert s.is_projected("c1")


def test_batch_content_hash_is_deterministic_and_order_free():
    a, b = _obs("f"), _obs("g")
    assert batch_content_hash([a, b]) == batch_content_hash([b, a])
    assert batch_content_hash([a]) != batch_content_hash([b])


def test_open_helper_lands_beside_the_other_sibling_stores(tmp_path):
    class _Paths:
        data_dir = tmp_path

    class _Cfg:
        paths = _Paths()

    s = mod.open_code_observation_store(cast(Config, _Cfg()))
    s.add_batch([_obs("f")])
    assert (tmp_path / "code_observations.sqlite").exists()
