"""Unit tests for the OBSERVED-only chatlog store (bp-063 Item 1, dn-chat-sensor CS-2).

Proves: a `ChatUtterance` round-trips through `add_batch`/`all_rows`; `to_row()` hardcodes
`observed`; `add_batch` is idempotent by the identity key (session_id, turn_index) (a re-add
writes 0 — a frozen session re-ingested is a no-op); `ObservedView(_rows=store.all_rows())`
constructs and `MirrorView(_rows=tuple(store.all_rows()))` RAISES `NonMirrorRowError`
(mirror-opacity, structural, both directions); NO API surface in the module accepts a
provenance value (the item-1 falsifier, ruled out mechanically); and provenance is NEVER
derived from `speaker` (both owner and agent utterances land `observed`).
"""

from __future__ import annotations

import inspect
from typing import Any

import core.stores.chatlog as mod
from core.mirror import MirrorView, NonMirrorRowError
from core.provenance import MIRROR_READABLE, Provenance
from core.sensing import NonObservedRowError, ObservedView
from core.stores.chatlog import ChatlogStore, ChatUtterance


def _store() -> ChatlogStore:
    return ChatlogStore(mod.Path(":memory:"))


def _utt(turn_index: int = 0, speaker: str = "owner", **kw: Any) -> ChatUtterance:
    base: dict[str, Any] = dict(session_id="s1", turn_index=turn_index, speaker=speaker,
                                text=f"utterance {turn_index}", transcript_digest="deadbeef",
                                ts_bookmark="2026-07-17T00:00:00Z")
    base.update(kw)
    return ChatUtterance(**base)


# --- round-trip + identity-key idempotence ---------------------------------------------------
def test_utterance_round_trips_through_add_batch_and_all_rows() -> None:
    s = _store()
    assert s.add_batch([_utt(0, "owner"), _utt(1, "agent")]) == 2
    rows = s.all_rows()
    assert len(rows) == 2
    assert [r["turn_index"] for r in rows] == [0, 1]
    assert [r["speaker"] for r in rows] == ["owner", "agent"]
    assert rows[0]["text"] == "utterance 0"
    assert rows[0]["transcript_digest"] == "deadbeef"
    assert rows[0]["ts_bookmark"] == "2026-07-17T00:00:00Z"


def test_add_batch_is_idempotent_by_session_and_turn() -> None:
    s = _store()
    batch = [_utt(0), _utt(1), _utt(2)]
    assert s.add_batch(batch) == 3
    # a re-add of the same identity keys writes 0 — a frozen session re-ingested (Q4):
    assert s.add_batch(batch) == 0
    # even with DIFFERENT text at the same key, the first write wins (INSERT OR IGNORE):
    assert s.add_batch([_utt(0, text="mutated")]) == 0
    assert s.count() == 3
    assert s.rows_for("s1")[0]["text"] == "utterance 0"


def test_turn_index_and_sessions_reads() -> None:
    s = _store()
    s.add_batch([_utt(0, session_id="s1"), _utt(0, session_id="s2"), _utt(1, session_id="s1")])
    assert s.sessions() == ["s1", "s2"]
    assert [r["turn_index"] for r in s.rows_for("s1")] == [0, 1]
    assert s.count() == 3


# --- to_row hardcodes observed; speaker is NEVER a provenance input --------------------------
def test_to_row_hardcodes_observed_for_both_speakers() -> None:
    assert _utt(0, "owner").to_row()["provenance"] == Provenance.OBSERVED.value
    assert _utt(1, "agent").to_row()["provenance"] == Provenance.OBSERVED.value
    # the wire payload carries no forgeable label:
    assert "provenance" not in _utt(0).to_dict()


def test_stored_rows_are_all_observed_regardless_of_speaker() -> None:
    s = _store()
    s.add_batch([_utt(0, "owner"), _utt(1, "agent")])
    assert {r["provenance"] for r in s.all_rows()} == {Provenance.OBSERVED.value}


# --- the falsifier: no provenance parameter exists anywhere ----------------------------------
def test_no_public_api_surface_accepts_a_provenance_value() -> None:
    """Item-1 falsifier, ruled out mechanically: every public callable in the module —
    functions, and methods of both public classes — is inspected; none may name a parameter
    that could carry a provenance/class label (the code_observations precedent, verbatim)."""
    surfaces: list[tuple[str, Any]] = []
    for name, fn in inspect.getmembers(mod, inspect.isfunction):
        if not name.startswith("_"):
            surfaces.append((f"{mod.__name__}.{name}", fn))
    for cls in (ChatUtterance, ChatlogStore):
        for name, fn in inspect.getmembers(cls, inspect.isfunction):
            if not name.startswith("_") or name == "__init__":
                surfaces.append((f"{cls.__name__}.{name}", fn))
    assert surfaces                                       # the sweep actually swept
    for label, fn in surfaces:
        params = set(inspect.signature(fn).parameters)
        assert not params & {"provenance", "provenances_write", "tier", "label", "speaker_class"}, (
            f"{label} accepts a provenance-like parameter — the wrong-class row "
            f"must be unrepresentable at this boundary")


def test_source_never_derives_provenance_from_speaker() -> None:
    """A grep-style backstop: no line in the module maps `speaker` into a provenance decision.
    The only place `speaker` and a provenance value could co-occur is `to_dict`/`to_row`,
    where provenance is a hardcoded literal, not a function of `speaker`."""
    src = inspect.getsource(mod)
    # provenance is only ever the hardcoded observed literal — never conditioned on speaker.
    assert "Provenance.OBSERVED.value" in src
    for line in src.splitlines():
        if "speaker" in line and "Provenance" in line:
            raise AssertionError(f"speaker co-occurs with Provenance (laundering risk): {line!r}")


# --- mirror-opacity: ObservedView admits, MirrorView refuses (both directions) ---------------
def test_observed_view_admits_chat_rows() -> None:
    s = _store()
    s.add_batch([_utt(0, "owner"), _utt(1, "agent")])
    view = ObservedView(_rows=tuple(s.all_rows()))
    assert len(view) == 2
    assert all(r["provenance"] == Provenance.OBSERVED.value for r in view.rows())


def test_mirror_view_refuses_chat_rows() -> None:
    s = _store()
    s.add_batch([_utt(0, "owner")])
    try:
        MirrorView(_rows=tuple(s.all_rows()))
    except NonMirrorRowError:
        pass
    else:
        raise AssertionError("MirrorView accepted an observed chat row — mirror-opacity breached")


def test_a_hand_forged_authored_chat_row_is_still_refused_by_observed_view() -> None:
    """The dual: an ObservedView refuses a non-observed row, so a laundered authored row can
    never masquerade into the assistant tier either."""
    forged = {**_utt(0).to_row(), "provenance": Provenance.AUTHORED_SOLO.value}
    try:
        ObservedView(_rows=(forged,))
    except NonObservedRowError:
        pass
    else:
        raise AssertionError("ObservedView admitted a non-observed row")


# --- reader provenance filter (the RowSource contract) ---------------------------------------
def test_reader_filtered_to_observed_sees_all_rows() -> None:
    s = _store()
    s.add_batch([_utt(0), _utt(1)])
    assert len(s.all_rows(provenances=[Provenance.OBSERVED])) == 2
    assert len(s.all_rows()) == 2
    assert s.all_rows(provenances=MIRROR_READABLE) == []   # nothing here is mirror-readable
