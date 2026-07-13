"""Unit tests for the OBSERVED-only agent-observation store (bp-019 Item 5, note B-b).

Proves: double-insert on the identity key (commit_sha, stream, subject_id, key) under the
SAME interpreter is idempotent (the B-b falsifier, inverted); a DIFFERENT interpreter
archives-then-replaces into the history sidecar (store='agent') with the chain queryable;
a superseding write with no history store raises; NO API surface in the module accepts a
provenance value (the Item 5 falsifier, ruled out mechanically over every public callable);
a reader filtered to OBSERVED sees all rows and any other filter sees none; `to_row()`
hardcodes `observed` so `ObservedView` admits the rows and `MirrorView` refuses them
(§2.6 — mirror-opacity, both directions).

finding-0057: `core/stores/observation_history.py`'s `IDENTITY_KEYS` dict does not yet carry
an `"agent"` entry (bp-019's write_scope does not grant that file — a one-line, spec-fidelity
gap, filed and routed to the orchestrator). The supersession/chain tests below register
`IDENTITY_KEYS["agent"]` locally via monkeypatch so they exercise the REAL
`ObservationHistoryStore.archive()`/`chain()` code paths end-to-end rather than mocking
them — once the real one-line registration lands, these tests need no change.
"""

from __future__ import annotations

import inspect
from typing import Any, cast

import pytest

import core.stores.agent_observations as mod
import core.stores.observation_history as history_mod
from config.loader import Config
from core.mirror import MirrorView, NonMirrorRowError
from core.provenance import MIRROR_READABLE, Provenance
from core.sensing import ObservedView
from core.stores.agent_observations import (
    AgentObservation,
    AgentObservationStore,
    MissingHistoryError,
    batch_content_hash,
)
from core.stores.observation_history import ObservationHistoryStore


@pytest.fixture(autouse=True)
def _register_agent_identity_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """finding-0057 workaround: register the 'agent' identity key locally so tests exercise
    the real archive()/chain() paths. Drop this fixture once the real one-line registration
    lands in core/stores/observation_history.py."""
    keys = dict(history_mod.IDENTITY_KEYS)
    keys["agent"] = ("commit_sha", "stream", "subject_id", "key")
    monkeypatch.setattr(history_mod, "IDENTITY_KEYS", keys)


def _store(tmp_path: Any) -> AgentObservationStore:
    return AgentObservationStore(tmp_path / "agent_observations.sqlite")


def _history(tmp_path: Any) -> ObservationHistoryStore:
    return ObservationHistoryStore(tmp_path / "observation_history.sqlite")


def _obs(key: str = "estimate", **kw: Any) -> AgentObservation:
    base: dict[str, Any] = dict(commit_sha="c1", stream="cost", subject_id="bp-011", key=key,
                                payload={"model": "sonnet", "tokens": 350000})
    base.update(kw)
    return AgentObservation(**base)


# --- identity key + same-interpreter idempotency ---------------------------------------------
def test_double_insert_is_idempotent(tmp_path: Any) -> None:
    s = _store(tmp_path)
    batch = [_obs("estimate"), _obs("actual", payload={"model": "sonnet", "tokens": 163000})]
    assert s.add_batch(batch, interpreter="1.0.0") == (2, 0)
    # second projection under the SAME worldview changes NOTHING (B-b falsifier):
    assert s.add_batch(batch, interpreter="1.0.0") == (0, 0)
    assert s.count() == 2


def test_reinsert_never_mutates_the_first_reading(tmp_path: Any) -> None:
    s = _store(tmp_path)
    s.add_batch([_obs("estimate", payload={"model": "sonnet", "tokens": 100})],
                interpreter="1.0.0")
    # same identity key, same interpreter — ignored, not replaced:
    s.add_batch([_obs("estimate", payload={"model": "sonnet", "tokens": 999})],
                interpreter="1.0.0")
    assert s.count() == 1
    assert s.rows_for("c1")[0]["payload"]["tokens"] == 100


# --- versioned supersession, archive-then-replace (the B-a/B-b pattern) -----------------------
def test_bumped_interpreter_archives_replaces_and_chains(tmp_path: Any) -> None:
    """The falsifier, inverted: a re-projection under a bumped version neither mutates in
    place silently (the old generation survives, archived) nor is ignored (the new reading
    lands)."""
    s, h = _store(tmp_path), _history(tmp_path)
    s.add_batch([_obs("estimate", payload={"tokens": 100})], interpreter="1.0.0")
    added, superseded = s.add_batch([_obs("estimate", payload={"tokens": 200})],
                                    interpreter="2.0.0", history=h)
    assert (added, superseded) == (0, 1)
    assert s.count() == 1                                    # latest-per-identity, by construction
    current = s.rows_for("c1")[0]
    assert current["payload"]["tokens"] == 200 and current["interpreter"] == "2.0.0"
    assert h.count("agent") == 1                              # the old generation is archived…
    chain = s.chain_for("c1", "cost", "bp-011", "estimate", history=h)
    assert [(g["interpreter"], g["payload"]["tokens"]) for g in chain] == [
        ("1.0.0", 100), ("2.0.0", 200)]                       # …and the chain reads oldest→current


def test_superseding_write_without_history_raises(tmp_path: Any) -> None:
    s = _store(tmp_path)
    s.add_batch([_obs("estimate")], interpreter="1.0.0")
    with pytest.raises(MissingHistoryError):
        s.add_batch([_obs("estimate", payload={"tokens": 1})], interpreter="2.0.0")  # history=None
    # and nothing was replaced or dropped:
    assert s.rows_for("c1")[0]["interpreter"] == "1.0.0"


def test_same_interpreter_readd_never_touches_history(tmp_path: Any) -> None:
    s, h = _store(tmp_path), _history(tmp_path)
    s.add_batch([_obs("estimate")], interpreter="1.0.0", history=h)
    assert s.add_batch([_obs("estimate")], interpreter="1.0.0", history=h) == (0, 0)
    assert h.count() == 0                                    # idempotence is not a supersession


# --- the falsifier: no provenance parameter exists anywhere ---------------------------------
def test_no_public_api_surface_accepts_a_provenance_value() -> None:
    """Item 5 falsifier, ruled out mechanically: every public callable in the module —
    functions, and methods of both public classes — is inspected; none may name a
    parameter that could carry a provenance/class label."""
    surfaces: list[tuple[str, Any]] = []
    for name, fn in inspect.getmembers(mod, inspect.isfunction):
        if not name.startswith("_"):
            surfaces.append((f"{mod.__name__}.{name}", fn))
    for cls in (AgentObservation, AgentObservationStore):
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
    s.add_batch([_obs("estimate")], interpreter="1.0.0")
    assert {r["provenance"] for r in s.all_rows()} == {Provenance.OBSERVED.value}
    assert _obs("estimate").to_row()["provenance"] == Provenance.OBSERVED.value
    assert "provenance" not in _obs("estimate").to_dict()  # the wire payload carries no label
    assert "interpreter" not in _obs("estimate").to_dict()  # nor a forgeable worldview coordinate
    # …a superseding generation is minted observed too (never re-classed on replace):
    h = _history(tmp_path)
    s.add_batch([_obs("estimate", payload={"tokens": 2})], interpreter="2.0.0", history=h)
    assert {r["provenance"] for r in s.all_rows()} == {Provenance.OBSERVED.value}


# --- reads (view-compatible dict rows) --------------------------------------------------------
def test_reader_filtered_to_observed_sees_all_rows(tmp_path: Any) -> None:
    s = _store(tmp_path)
    s.add_batch([_obs("estimate"), _obs("actual")], interpreter="1.0.0")
    assert len(s.all_rows(provenances=[Provenance.OBSERVED])) == 2
    assert len(s.all_rows()) == 2
    assert s.all_rows(provenances=MIRROR_READABLE) == []  # nothing here is mirror-readable


def test_payload_round_trips_as_typed_json(tmp_path: Any) -> None:
    s = _store(tmp_path)
    payload = {"model": "sonnet", "tokens": 350000, "tool_calls": 142, "duration_min": 19,
              "raw": "{ model: sonnet, tokens: 350k }"}
    s.add_batch([_obs("estimate", payload=payload)], interpreter="1.0.0")
    assert s.rows_for("c1")[0]["payload"] == payload


# --- §2.6 firewall: ObservedView admits, MirrorView refuses -----------------------------------
def test_observed_view_admits_and_mirror_view_refuses(tmp_path: Any) -> None:
    s = _store(tmp_path)
    s.add_batch([_obs("estimate")], interpreter="1.0.0")
    rows = tuple(s.all_rows())
    assert len(ObservedView(_rows=rows)) == 1             # the observed tier's typed container
    with pytest.raises(NonMirrorRowError):
        MirrorView(_rows=rows)                            # OBSERVED is mirror-opaque, structurally


# --- projection bookkeeping + batch hash (version-keyed from birth) ---------------------------
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
    a, b = _obs("estimate"), _obs("actual")
    assert batch_content_hash([a, b]) == batch_content_hash([b, a])
    assert batch_content_hash([a]) != batch_content_hash([b])


def test_open_helper_lands_beside_the_other_sibling_stores(tmp_path: Any) -> None:
    class _Paths:
        data_dir = tmp_path

    class _Cfg:
        paths = _Paths()

    s = mod.open_agent_observation_store(cast(Config, _Cfg()))
    s.add_batch([_obs("estimate")], interpreter="1.0.0")
    assert (tmp_path / "agent_observations.sqlite").exists()
