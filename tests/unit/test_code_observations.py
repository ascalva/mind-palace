"""Unit tests for the OBSERVED-only code-observation store (bp-012 Item 3, note B-b;
interpreter-version supersession bp-018 Item 3, dn-self-sensing B-a).

Proves: double-insert on the identity key (commit_sha, path, qualname) under the SAME
interpreter is idempotent; a DIFFERENT interpreter archives-then-replaces into the
history sidecar with the chain queryable (the B-a falsifier, inverted: neither in-place
mutation nor a silent skip); a superseding write with no history store raises; both
on-open migrations heal pre-bp-018 fixture files idempotently; NO API surface in the
module accepts a provenance value (the bp-012 Item 3 falsifier, ruled out mechanically
over every public callable); a reader filtered to OBSERVED sees all rows and any other
filter sees none; `to_row()` hardcodes `observed` so `ObservedView` admits the rows and
`MirrorView` refuses them (§2.6 — mirror-opacity, both directions).
"""

from __future__ import annotations

import inspect
import sqlite3
from pathlib import Path
from typing import Any, cast

import pytest

import core.stores.code_observations as mod
from config.loader import Config
from core.mirror import MirrorView, NonMirrorRowError
from core.provenance import MIRROR_READABLE, Provenance
from core.sensing import ObservedView
from core.stores.code_observations import (
    CodeObservation,
    CodeObservationStore,
    MissingHistoryError,
    batch_content_hash,
)
from core.stores.observation_history import ObservationHistoryStore


def _store(tmp_path: Any) -> CodeObservationStore:
    return CodeObservationStore(tmp_path / "code_observations.sqlite")


def _history(tmp_path: Any) -> ObservationHistoryStore:
    return ObservationHistoryStore(tmp_path / "observation_history.sqlite")


def _obs(qualname: str = "f", **kw: Any) -> CodeObservation:
    base: dict[str, Any] = dict(commit_sha="c1", path="a.py", qualname=qualname,
                                kind="function", signature="(x)", docstring="does f")
    base.update(kw)
    return CodeObservation(**base)


# --- identity key + same-interpreter idempotency ---------------------------------------------
def test_double_insert_is_idempotent(tmp_path: Any) -> None:
    s = _store(tmp_path)
    batch = [_obs("f"), _obs("g"), _obs("", kind="module", signature="")]
    assert s.add_batch(batch, interpreter="1.0.0") == (3, 0)
    # second projection under the SAME worldview changes NOTHING (B-b falsifier):
    assert s.add_batch(batch, interpreter="1.0.0") == (0, 0)
    assert s.count() == 3


def test_reinsert_never_mutates_the_first_reading(tmp_path: Any) -> None:
    s = _store(tmp_path)
    s.add_batch([_obs("f", docstring="first")], interpreter="1.0.0")
    # same identity key, same interpreter — ignored, not replaced:
    s.add_batch([_obs("f", docstring="second")], interpreter="1.0.0")
    assert s.count() == 1
    assert s.rows_for("c1")[0]["docstring"] == "first"


# --- bp-018 (i)-(iii): versioned supersession, archive-then-replace ---------------------------
def test_bumped_interpreter_archives_replaces_and_chains(tmp_path: Any) -> None:
    """The B-a falsifier, inverted: a re-projection under a bumped version neither
    mutates in place silently (the old generation survives, archived) nor is ignored
    (the new reading lands)."""
    s, h = _store(tmp_path), _history(tmp_path)
    s.add_batch([_obs("f", docstring="v1 reading")], interpreter="1.0.0")
    added, superseded = s.add_batch([_obs("f", docstring="v2 reading")],
                                    interpreter="2.0.0", history=h)
    assert (added, superseded) == (0, 1)
    assert s.count() == 1                                   # latest-per-identity, by construction
    current = s.rows_for("c1")[0]
    assert current["docstring"] == "v2 reading" and current["interpreter"] == "2.0.0"
    assert h.count("code") == 1                             # the old generation is archived…
    chain = s.chain_for("c1", "a.py", "f", history=h)
    assert [(g["interpreter"], g["docstring"]) for g in chain] == [
        ("1.0.0", "v1 reading"), ("2.0.0", "v2 reading")]   # …and the chain reads oldest→current


def test_superseding_write_without_history_raises(tmp_path: Any) -> None:
    s = _store(tmp_path)
    s.add_batch([_obs("f")], interpreter="1.0.0")
    with pytest.raises(MissingHistoryError):
        s.add_batch([_obs("f", docstring="new view")], interpreter="2.0.0")   # history=None
    # and nothing was replaced or dropped:
    assert s.rows_for("c1")[0]["interpreter"] == "1.0.0"


def test_same_interpreter_readd_never_touches_history(tmp_path: Any) -> None:
    s, h = _store(tmp_path), _history(tmp_path)
    s.add_batch([_obs("f")], interpreter="1.0.0", history=h)
    assert s.add_batch([_obs("f")], interpreter="1.0.0", history=h) == (0, 0)
    assert h.count() == 0                                   # idempotence is not a supersession


# --- bp-018 (iv): both migrations heal on open, idempotently ----------------------------------
_PRE_BA_DDL = """
CREATE TABLE code_observations (
    commit_sha     TEXT NOT NULL,
    path           TEXT NOT NULL,
    qualname       TEXT NOT NULL DEFAULT '',
    kind           TEXT NOT NULL,
    signature      TEXT NOT NULL DEFAULT '',
    docstring      TEXT NOT NULL DEFAULT '',
    references_out TEXT NOT NULL DEFAULT '[]',
    provenance     TEXT NOT NULL,
    observed_at    TEXT NOT NULL,
    PRIMARY KEY (commit_sha, path, qualname)
);
CREATE TABLE projections (
    commit_sha   TEXT PRIMARY KEY,
    batch_hash   TEXT NOT NULL,
    projected_at TEXT NOT NULL
);
"""


def _pre_ba_fixture(path: Path) -> None:
    """A file exactly as bp-012 left it: 9-column observations, sha-keyed projections."""
    conn = sqlite3.connect(str(path))
    conn.executescript(_PRE_BA_DDL)
    with conn:
        conn.execute("INSERT INTO code_observations VALUES "
                     "('c1','a.py','f','function','(x)','does f','[]','observed','t0')")
        conn.execute("INSERT INTO code_observations VALUES "
                     "('c1','a.py','','module','','Module A.','[]','observed','t0')")
        conn.execute("INSERT INTO projections VALUES ('c1','hash-a','t0')")
    conn.close()


def test_migrations_heal_a_pre_ba_file_on_open(tmp_path: Any) -> None:
    db = tmp_path / "code_observations.sqlite"
    _pre_ba_fixture(db)
    s = CodeObservationStore(db)
    assert s.count() == 2                                   # no row lost
    assert {r["interpreter"] for r in s.all_rows()} == {"1.0.0"}   # §6(d) honest backfill
    assert s.is_projected("c1")                             # any-generation read (pre-B-a shape)
    assert s.is_projected("c1", "1.0.0")                    # the mark migrated under 1.0.0
    assert not s.is_projected("c1", "2.0.0")                # …and only under 1.0.0
    assert s.rows_for("c1")[0]["docstring"] == "Module A."  # payloads verbatim


def test_migrations_heal_a_half_migrated_file_and_reopen_is_idempotent(tmp_path: Any) -> None:
    db = tmp_path / "code_observations.sqlite"
    _pre_ba_fixture(db)
    conn = sqlite3.connect(str(db))                         # simulate a crashed §6(e) attempt:
    with conn:                                              # leftover copy target, old table intact
        conn.execute("CREATE TABLE projections_v2 (commit_sha TEXT NOT NULL, "
                     "interpreter TEXT NOT NULL, batch_hash TEXT NOT NULL, "
                     "projected_at TEXT NOT NULL, PRIMARY KEY (commit_sha, interpreter))")
    conn.close()
    s = CodeObservationStore(db)
    assert s.is_projected("c1", "1.0.0") and s.count() == 2   # healed, nothing lost
    s.close()
    s2 = CodeObservationStore(db)                           # re-open: migration must be a no-op
    assert s2.is_projected("c1", "1.0.0") and s2.count() == 2
    marks = s2._conn.execute("SELECT count(*) FROM projections").fetchone()[0]
    assert marks == 1                                       # no duplicated bookkeeping


# --- the falsifier: no provenance parameter exists anywhere ---------------------------------
def test_no_public_api_surface_accepts_a_provenance_value() -> None:
    """Item 3 falsifier, ruled out mechanically: every public callable in the module —
    functions, and methods of both public classes — is inspected; none may name a
    parameter that could carry a provenance/class label."""
    surfaces: list[tuple[str, Any]] = []
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


def test_rows_are_minted_observed_with_no_parameter(tmp_path: Any) -> None:
    s = _store(tmp_path)
    s.add_batch([_obs("f")], interpreter="1.0.0")
    assert {r["provenance"] for r in s.all_rows()} == {Provenance.OBSERVED.value}
    assert _obs("f").to_row()["provenance"] == Provenance.OBSERVED.value
    assert "provenance" not in _obs("f").to_dict()        # the wire payload carries no label
    assert "interpreter" not in _obs("f").to_dict()       # nor a forgeable worldview coordinate
    # …a superseding generation is minted observed too (never re-classed on replace):
    h = _history(tmp_path)
    s.add_batch([_obs("f", docstring="v2")], interpreter="2.0.0", history=h)
    assert {r["provenance"] for r in s.all_rows()} == {Provenance.OBSERVED.value}


# --- reads (UNCHANGED in signature and semantics: latest-per-identity by construction) --------
def test_reader_filtered_to_observed_sees_all_rows(tmp_path: Any) -> None:
    s = _store(tmp_path)
    s.add_batch([_obs("f"), _obs("g")], interpreter="1.0.0")
    assert len(s.all_rows(provenances=[Provenance.OBSERVED])) == 2
    assert len(s.all_rows()) == 2
    assert s.all_rows(provenances=MIRROR_READABLE) == []  # nothing here is mirror-readable


def test_references_out_round_trips_as_typed_json(tmp_path: Any) -> None:
    s = _store(tmp_path)
    ref = {"type": "note-citation", "target": "docs/design-notes/x.md", "source_line": 3}
    s.add_batch([_obs("f", references_out=(ref,))], interpreter="1.0.0")
    assert s.rows_for("c1")[0]["references_out"] == [ref]


# --- §2.6 firewall: ObservedView admits, MirrorView refuses ---------------------------------
def test_observed_view_admits_and_mirror_view_refuses(tmp_path: Any) -> None:
    s = _store(tmp_path)
    s.add_batch([_obs("f")], interpreter="1.0.0")
    rows = tuple(s.all_rows())
    assert len(ObservedView(_rows=rows)) == 1             # the observed tier's typed container
    with pytest.raises(NonMirrorRowError):
        MirrorView(_rows=rows)                            # OBSERVED is mirror-opaque, structurally


# --- projection bookkeeping + batch hash (version-keyed since bp-018) ------------------------
def test_projection_marks_are_idempotent_per_worldview(tmp_path: Any) -> None:
    s = _store(tmp_path)
    assert not s.is_projected("c1")
    s.mark_projected("c1", "hash-a", "1.0.0")
    s.mark_projected("c1", "hash-b", "1.0.0")             # re-mark is a no-op, first mark wins
    assert s.is_projected("c1") and s.is_projected("c1", "1.0.0")
    assert not s.is_projected("c1", "2.0.0")              # a bump makes the sha eligible again
    s.mark_projected("c1", "hash-c", "2.0.0")             # …and the new worldview marks anew
    assert s.is_projected("c1", "2.0.0")


def test_batch_content_hash_is_deterministic_and_order_free() -> None:
    a, b = _obs("f"), _obs("g")
    assert batch_content_hash([a, b]) == batch_content_hash([b, a])
    assert batch_content_hash([a]) != batch_content_hash([b])


def test_open_helper_lands_beside_the_other_sibling_stores(tmp_path: Any) -> None:
    class _Paths:
        data_dir = tmp_path

    class _Cfg:
        paths = _Paths()

    s = mod.open_code_observation_store(cast(Config, _Cfg()))
    s.add_batch([_obs("f")], interpreter="1.0.0")
    assert (tmp_path / "code_observations.sqlite").exists()
