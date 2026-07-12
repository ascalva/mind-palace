"""Unit tests for the observation-history sidecar (bp-018 Item 2, dn-self-sensing §2.5).

Proves: archive → chain round-trips superseded generations oldest-first; a second
identical `archive` changes NOTHING (INSERT OR IGNORE on the (store, identity_json,
interpreter) PK — the Item 2 falsifier's second half, inverted); `count` totals per
member and family-wide; and the ledger-class invariant is STRUCTURAL — the class
surface is swept and no delete/update-shaped method exists, and no API surface accepts
a provenance value (rows are archived verbatim; provenance already rides inside
`row_json`).
"""

from __future__ import annotations

import inspect
from typing import Any, cast

import pytest

import core.stores.observation_history as mod
from config.loader import Config
from core.stores.observation_history import ObservationHistoryStore


def _store(tmp_path: Any) -> ObservationHistoryStore:
    return ObservationHistoryStore(tmp_path / "observation_history.sqlite")


def _row(docstring: str = "does f", interpreter: str = "1.0.0") -> dict[str, Any]:
    """A code-member row, verbatim shape (identity key: commit_sha, path, qualname)."""
    return {"commit_sha": "c1", "path": "a.py", "qualname": "f", "kind": "function",
            "signature": "(x)", "docstring": docstring, "references_out": [],
            "provenance": "observed", "observed_at": "2026-07-12T00:00:00",
            "interpreter": interpreter}


# --- archive → chain round-trip ---------------------------------------------------------------
def test_archive_then_chain_round_trips_generations_oldest_first(tmp_path: Any) -> None:
    s = _store(tmp_path)
    g1 = _row(docstring="v1 reading", interpreter="1.0.0")
    g2 = _row(docstring="v2 reading", interpreter="2.0.0")
    assert s.archive("code", [(g1, "1.0.0", "2.0.0")]) == 1
    assert s.archive("code", [(g2, "2.0.0", "3.0.0")]) == 1

    chain = s.chain("code", {"commit_sha": "c1", "path": "a.py", "qualname": "f"})
    assert chain == [g1, g2]                      # oldest first, rows verbatim
    assert [g["interpreter"] for g in chain] == ["1.0.0", "2.0.0"]


def test_chain_accepts_a_full_row_as_the_identity_carrier(tmp_path: Any) -> None:
    s = _store(tmp_path)
    g1 = _row()
    s.archive("code", [(g1, "1.0.0", "2.0.0")])
    assert s.chain("code", g1) == [g1]            # identity extracted from the row itself
    assert s.chain("code", _row(interpreter="9.9.9")) == [g1]   # non-key fields irrelevant


def test_chain_is_scoped_to_one_identity_key(tmp_path: Any) -> None:
    s = _store(tmp_path)
    other = dict(_row(), qualname="g")
    s.archive("code", [(_row(), "1.0.0", "2.0.0"), (other, "1.0.0", "2.0.0")])
    assert s.chain("code", {"commit_sha": "c1", "path": "a.py", "qualname": "f"}) == [_row()]
    assert s.chain("code", {"commit_sha": "c1", "path": "a.py", "qualname": "zzz"}) == []


# --- the falsifier's second half: a second identical archive changes count ---------------------
def test_rearchiving_the_same_generation_changes_nothing(tmp_path: Any) -> None:
    s = _store(tmp_path)
    assert s.archive("code", [(_row(), "1.0.0", "2.0.0")]) == 1
    assert s.archive("code", [(_row(), "1.0.0", "2.0.0")]) == 0   # crashed-replace re-run
    assert s.count() == 1
    # …and the first generation's payload is untouched (first archive wins):
    assert s.chain("code", _row())[0]["docstring"] == "does f"


def test_count_totals_per_member_and_family_wide(tmp_path: Any) -> None:
    s = _store(tmp_path)
    s.archive("code", [(_row(), "1.0.0", "2.0.0"),
                       (dict(_row(), qualname="g"), "1.0.0", "2.0.0")])
    assert s.count() == 2
    assert s.count("code") == 2
    assert s.count("agent") == 0                  # bp-019's member: empty, not an error


def test_unregistered_family_member_is_a_hard_error(tmp_path: Any) -> None:
    s = _store(tmp_path)
    with pytest.raises(KeyError):
        s.archive("dreams", [(_row(), "1.0.0", "2.0.0")])   # no identity key registered


# --- ledger-class is STRUCTURAL: no delete/update surface exists (Item 2 falsifier) -----------
def test_no_delete_or_update_method_exists_on_the_class() -> None:
    """The Item 2 falsifier, ruled out mechanically: any API path that removes or
    mutates an archived row would violate ledger-class. The class surface is swept —
    no public callable may be named like a removal/mutation."""
    forbidden = ("delete", "update", "remove", "purge", "clear", "drop", "pop",
                 "discard", "truncate", "prune", "reset", "overwrite", "replace")
    names = [n for n, _ in inspect.getmembers(ObservationHistoryStore, callable)
             if not (n.startswith("__") and n.endswith("__"))]   # dunders are Python's
    # (e.g. 3.13 dataclasses mint __replace__, a new-instance constructor — not an API
    # path into stored rows; the falsifier targets the class's OWN surface)
    assert "archive" in names                     # the sweep actually swept
    for n in names:
        assert not any(f in n.lower() for f in forbidden), (
            f"ObservationHistoryStore.{n}: a removal/mutation-shaped method exists — "
            f"append-only must be structural, not conventional")


def test_no_api_surface_accepts_a_provenance_value() -> None:
    surfaces: list[tuple[str, Any]] = []
    for name, fn in inspect.getmembers(mod, inspect.isfunction):
        if not name.startswith("_"):
            surfaces.append((f"{mod.__name__}.{name}", fn))
    for name, fn in inspect.getmembers(ObservationHistoryStore, inspect.isfunction):
        if not name.startswith("_") or name == "__init__":
            surfaces.append((f"ObservationHistoryStore.{name}", fn))
    assert surfaces
    for label, fn in surfaces:
        params = set(inspect.signature(fn).parameters)
        assert not params & {"provenance", "provenances_write", "tier", "label"}, (
            f"{label} accepts a provenance-like parameter — rows are archived verbatim; "
            f"this store mints nothing")


# --- the open helper --------------------------------------------------------------------------
def test_open_helper_lands_beside_the_other_sibling_stores(tmp_path: Any) -> None:
    class _Paths:
        data_dir = tmp_path

    class _Cfg:
        paths = _Paths()

    s = mod.open_observation_history_store(cast(Config, _Cfg()))
    s.archive("code", [(_row(), "1.0.0", "2.0.0")])
    assert (tmp_path / "observation_history.sqlite").exists()
