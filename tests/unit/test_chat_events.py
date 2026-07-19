"""Unit tests for the L1 action log — the dialogue sensor's delayed rate (bp-069 Item 3).

`extract_events` reduces a raw transcript to its ordered, typed ACTION LOG (prompt → response →
commit(sha) → file_edit(path) → build_plan(id) → …), model-free, structural refs ONLY. The projector
re-extracts iff a session's transcript digest changed (incremental, replace-per-session). The sensor
is BORN SCOPED: its handle inventory ⊑ `DIALOGUE_SENSOR_SCOPE` (the D2 conformance check), and a
smuggled handle (a stratum outside DIALOGUE, or an edge-fiber write) is rejected.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from config.loader import load_config
from core.agent_scope import ConformanceError, Handle, assert_conforms
from core.chat_events import ChatEventProjector, extract_events
from core.scope import Stratum
from core.stores.chat_events import ChatEventStore
from core.stores.chatlog import ChatlogStore, ChatUtterance
from core.stores.rawstore import RawStore
from ops.chat_sensor import DIALOGUE_SENSOR_SCOPE
from scheduler.cron import CHAT_EVENTS_KIND
from scheduler.router import Router


# --- fixtures --------------------------------------------------------------------------------
def _jsonl(records: list[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(r) for r in records) + "\n"


def _user_text(text: str) -> dict[str, Any]:
    return {"type": "user", "sessionId": "sess-a",
            "message": {"role": "user", "content": [{"type": "text", "text": text}]}}


def _assistant(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "assistant", "sessionId": "sess-a",
            "message": {"role": "assistant", "content": blocks}}


def _tool_result(tool_use_id: str, text: str) -> dict[str, Any]:
    return {"type": "user", "sessionId": "sess-a",
            "message": {"role": "user",
                        "content": [{"type": "tool_result", "tool_use_id": tool_use_id,
                                     "content": text}]}}


# --- extraction: the exact ordered typed sequence --------------------------------------------
def test_extract_events_exact_ordered_typed_sequence() -> None:
    """prompt → response → Bash git commit(+result) → Edit → Write(build-plan): the EXACT ordered
    typed sequence, with structural refs (sha/path/plan-id) and the L0 turn backpointers."""
    raw = _jsonl([
        _user_text("wire the sensor"),
        _assistant([{"type": "text", "text": "on it"}]),
        _assistant([{"type": "tool_use", "id": "t1", "name": "Bash",
                     "input": {"command": "git commit -m 'wire the chat sensor'"}}]),
        _tool_result("t1", "[main abc1234] wire the chat sensor\n 1 file changed"),
        _assistant([{"type": "tool_use", "id": "t2", "name": "Edit",
                     "input": {"file_path": "core/foo.py", "old_string": "SECRET"}}]),
        _assistant([{"type": "tool_use", "id": "t3", "name": "Write",
                     "input": {"file_path": "docs/build-plans/bp-069/plan.md",
                               "content": "SECRET PLAN BODY"}}]),
    ])
    events = extract_events("sess-a", raw)
    assert [(e.actor, e.kind, e.ref) for e in events] == [
        ("owner", "prompt", "0"),
        ("agent", "response", "1"),
        ("agent", "commit", "abc1234"),
        ("agent", "file_edit", "core/foo.py"),
        ("agent", "build_plan", "bp-069"),
    ]
    assert [e.order for e in events] == [0, 1, 2, 3, 4]          # dense per-session order
    assert [e.turn_index for e in events] == [0, 1, 2, 2, 2]     # L0 backpointers (2 text turns)
    # no verbatim content leaks into a ref (the falsifier):
    for e in events:
        assert "SECRET" not in e.ref
        assert "git commit" not in e.ref and "wire the sensor" not in e.ref


def test_unknown_tool_is_recorded_as_generic_tool_use() -> None:
    """Fail-open: an unrecognised tool is RECORDED as `tool_use(name)`, never dropped."""
    raw = _jsonl([
        _assistant([{"type": "tool_use", "id": "g1", "name": "Grep",
                     "input": {"pattern": "SECRET_QUERY"}}]),
    ])
    events = extract_events("sess-a", raw)
    assert [(e.actor, e.kind, e.ref) for e in events] == [("agent", "tool_use", "Grep")]
    assert "SECRET_QUERY" not in events[0].ref


def test_finding_and_design_note_writes_are_typed() -> None:
    raw = _jsonl([
        _assistant([{"type": "tool_use", "id": "f1", "name": "Write",
                     "input": {"file_path": "docs/findings/finding-0110.md"}}]),
        _assistant([{"type": "tool_use", "id": "d1", "name": "Edit",
                     "input": {"file_path": "docs/design-notes/agent-taxonomy.md"}}]),
    ])
    events = extract_events("sess-a", raw)
    assert [(e.kind, e.ref) for e in events] == [
        ("finding", "finding-0110"),
        ("design_note", "agent-taxonomy.md"),
    ]


def test_torn_line_is_tolerated() -> None:
    raw = _jsonl([_user_text("clean")]) + '{"type":"assistant","message":{"conte'
    events = extract_events("sess-a", raw)                       # must not raise
    assert [(e.kind, e.ref) for e in events] == [("prompt", "0")]


# --- the projector: incremental, replace-per-session -----------------------------------------
def _seed(chatlog: ChatlogStore, rawstore: RawStore, session_id: str, raw: str) -> str:
    """Retain `raw` and register one chatlog row pointing at its digest (what the sensor does), so
    the projector reads the session's OWN raw via `transcript_digest`."""
    digest, _ = rawstore.add_text(raw)
    chatlog.add_batch([ChatUtterance(session_id=session_id, turn_index=0, speaker="owner",
                                     text="x", transcript_digest=digest)])
    return digest


def _projector(tmp_path: Path) -> ChatEventProjector:
    return ChatEventProjector(
        chatlog=ChatlogStore(Path(":memory:")),
        rawstore=RawStore(tmp_path / "raw"),
        store=ChatEventStore(Path(":memory:")),
    )


def test_project_extracts_then_skips_unchanged_and_reextracts_grown(tmp_path: Path) -> None:
    p = _projector(tmp_path)
    raw = _jsonl([_user_text("hi"), _assistant([{"type": "text", "text": "yo"}])])
    _seed(p.chatlog, p.rawstore, "sess-a", raw)
    assert p.project(max_sessions=10) == 1                       # first extraction
    assert [e["kind"] for e in p.store.events_for("sess-a")] == ["prompt", "response"]
    assert p.project(max_sessions=10) == 0                       # unchanged → skipped (no churn)
    # the session grows (a new, fuller raw registered under a new digest):
    grown = _jsonl([_user_text("hi"), _assistant([{"type": "text", "text": "yo"}]),
                    _assistant([{"type": "tool_use", "id": "g", "name": "Read",
                                 "input": {"file_path": "a.py"}}])])
    digest, _ = p.rawstore.add_text(grown)
    p.chatlog.add_batch([ChatUtterance(session_id="sess-a", turn_index=1, speaker="agent",
                                       text="yo", transcript_digest=digest)])
    assert p.project(max_sessions=10) == 1                       # re-extracts the grown session
    assert [e["kind"] for e in p.store.events_for("sess-a")] == ["prompt", "response", "tool_use"]


def test_project_honours_max_per_pass(tmp_path: Path) -> None:
    p = _projector(tmp_path)
    for sid in ("s1", "s2", "s3"):
        _seed(p.chatlog, p.rawstore, sid, _jsonl([_user_text("hi")]))
    assert p.project(max_sessions=2) == 2                        # capped at the batch size
    assert p.project(max_sessions=2) == 1                        # the remaining one, next pass


# --- pinned tier + the born scope (D2 conformance) -------------------------------------------
def test_chat_events_plans_onto_the_pinned_tier() -> None:
    cfg = load_config()
    assert Router(cfg).plan(CHAT_EVENTS_KIND).tier == cfg.pinned_model.tier


# The sensor's REAL handle inventory: L0 chatlog + L1 chat_events (both projection-write DIALOGUE),
# the rawstore + the transcripts dir (read). All DIALOGUE_TRANSCRIPT — within Σ = {DIALOGUE}↓.
_SENSOR_HANDLES = (
    Handle("chatlog", Stratum.DIALOGUE_TRANSCRIPT, writes_stratum=True),
    Handle("chat_events", Stratum.DIALOGUE_TRANSCRIPT, writes_stratum=True),
    Handle("rawstore", Stratum.DIALOGUE_TRANSCRIPT, writes_stratum=False),
    Handle("transcripts", Stratum.DIALOGUE_TRANSCRIPT, writes_stratum=False),
)


def test_the_sensor_is_born_scoped() -> None:
    """The D2 conformance check: the sensor's handles ⊑ `DIALOGUE_SENSOR_SCOPE` (no raise)."""
    assert_conforms(DIALOGUE_SENSOR_SCOPE, _SENSOR_HANDLES)


def test_a_handle_outside_the_dialogue_stratum_is_rejected() -> None:
    with pytest.raises(ConformanceError):
        assert_conforms(DIALOGUE_SENSOR_SCOPE,
                        (Handle("code", Stratum.OBSERVED, writes_stratum=True),))


def test_a_smuggled_edge_write_is_rejected() -> None:
    """A sensor produces nodes, never edges (E = ⊥): a handle writing a C fiber is outside scope."""
    with pytest.raises(ConformanceError):
        assert_conforms(DIALOGUE_SENSOR_SCOPE,
                        (Handle("edge", Stratum.DIALOGUE_TRANSCRIPT, writes_fiber="C"),))
