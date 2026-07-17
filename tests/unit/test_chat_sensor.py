"""Unit tests for the chat sensor pipeline (bp-063 Items 2 & 3, dn-chat-sensor CS-1/CS-3).

Item 2 (verbatim retention + tool-strip extraction): a fixture transcript is stored in the
rawstore BYTE-FOR-BYTE BEFORE extraction; `parse_transcript` yields only `text`-block
utterances (planted `tool_use`/`tool_result`/`thinking` content appears in NO row);
`turn_index` is contiguous per session; `speaker` maps user→owner / assistant→agent; a
bare-string `message.content` (legacy shape) yields one text utterance; every row's text is
recoverable from its `transcript_digest`.

Item 3 (secret backstop + backfill + active exclusion): a planted AWS/`sk-`/private-key
secret is REFUSED (`SecretInUtteranceError`, session id named) and NEVER stored; a clean
corpus backfills and a second `backfill()` writes 0 (idempotent); the `active_session_id`
transcript is excluded; every stored row is `observed`; the report names refused/skipped
sessions (no silent cap).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from core.provenance import Provenance
from core.stores.chatlog import ChatlogStore
from core.stores.rawstore import RawStore
from ops.chat_sensor import (
    ChatSecretGuard,
    ChatSensor,
    SecretInUtteranceError,
    parse_transcript,
)


# --- fixture builders ------------------------------------------------------------------------
def _rec(rtype: str, content: Any, *, session_id: str = "sess-a",
         ts: str = "2026-07-17T00:00:00Z") -> dict[str, Any]:
    """One transcript record. `content` is `message.content` (a string or a block list)."""
    role = {"user": "user", "assistant": "assistant"}.get(rtype)
    rec: dict[str, Any] = {"type": rtype, "sessionId": session_id, "timestamp": ts,
                           "uuid": "u", "parentUuid": None}
    if role is not None:
        rec["message"] = {"role": role, "content": content}
    return rec


def _text(s: str) -> dict[str, Any]:
    return {"type": "text", "text": s}


def _jsonl(records: list[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(r) for r in records) + "\n"


def _write_transcript(dirp: Path, session_id: str, records: list[dict[str, Any]]) -> Path:
    # In real transcripts every record's `sessionId` equals the filename stem (measured, Q1).
    # Mirror that here so the stored session_id and the filename-stem-based skip/active logic
    # agree, exactly as they do in production.
    for r in records:
        if "sessionId" in r:
            r["sessionId"] = session_id
    p = dirp / f"{session_id}.jsonl"
    p.write_text(_jsonl(records), encoding="utf-8")
    return p


def _sensor(tmp_path: Any, *, active: str | None = None) -> ChatSensor:
    tdir = tmp_path / "transcripts"
    tdir.mkdir()
    return ChatSensor(
        transcripts_dir=tdir,
        rawstore=RawStore(tmp_path / "raw"),
        store=ChatlogStore(Path(":memory:")),
        guard=ChatSecretGuard(),
        active_session_id=active,
    )


# --- Item 2: parse_transcript — tool-strip, grain, legacy shape ------------------------------
def test_parse_keeps_only_text_blocks_stripping_tool_and_thinking() -> None:
    text = _jsonl([
        _rec("user", [_text("owner question")]),
        _rec("assistant", [
            {"type": "thinking", "thinking": "SECRET_THOUGHT internal monologue"},
            {"type": "text", "text": "agent answer"},
            {"type": "tool_use", "name": "Bash", "input": {"command": "SECRET_TOOL_CMD"}},
        ]),
        _rec("user", [
            {"type": "tool_result", "content": "SECRET_TOOL_OUTPUT quoting a.py"},
        ]),
    ])
    utts = parse_transcript(text)
    joined = " ".join(u.text for u in utts)
    assert [u.text for u in utts] == ["owner question", "agent answer"]
    for leaked in ("SECRET_THOUGHT", "SECRET_TOOL_CMD", "SECRET_TOOL_OUTPUT"):
        assert leaked not in joined                       # tool/thinking stripped structurally


def test_turn_index_contiguous_and_speaker_mapping() -> None:
    text = _jsonl([
        _rec("user", "owner one"),
        _rec("assistant", [_text("agent one"), _text("agent two")]),
        _rec("user", [_text("owner two")]),
    ])
    utts = parse_transcript(text)
    assert [u.turn_index for u in utts] == [0, 1, 2, 3]    # contiguous, per-session
    assert [u.speaker for u in utts] == ["owner", "agent", "agent", "owner"]
    assert all(s in ("owner", "agent") for s in (u.speaker for u in utts))


def test_bare_string_content_is_one_text_utterance() -> None:
    text = _jsonl([_rec("user", "a legacy bare-string message")])
    utts = parse_transcript(text)
    assert len(utts) == 1
    assert utts[0].text == "a legacy bare-string message"
    assert utts[0].speaker == "owner"


def test_non_dialogue_records_and_empty_text_are_skipped() -> None:
    text = _jsonl([
        {"type": "system", "sessionId": "s", "timestamp": "t", "content": "boot"},
        {"type": "file-history-snapshot", "sessionId": "s"},
        _rec("assistant", [_text("   "), _text("real")]),   # whitespace-only dropped
    ])
    utts = parse_transcript(text)
    assert [u.text for u in utts] == ["real"]


def test_session_id_and_bookmark_carried_from_records() -> None:
    text = _jsonl([_rec("user", "hi", session_id="sess-x", ts="2026-07-17T12:00:00Z")])
    u = parse_transcript(text)[0]
    assert u.session_id == "sess-x"
    assert u.ts_bookmark == "2026-07-17T12:00:00Z"


# --- Item 2: verbatim retention BEFORE extraction; recoverability ----------------------------
def test_transcript_retained_byte_for_byte_and_utterances_recoverable(tmp_path: Any) -> None:
    s = _sensor(tmp_path)
    records = [_rec("user", "hello"), _rec("assistant", [_text("hi there")])]
    p = _write_transcript(s.transcripts_dir, "sess-a", records)
    source_bytes = p.read_bytes()
    report = s.backfill()
    # CS-1: the raw is stored byte-for-byte and is retrievable by digest.
    digest = s.store.rows_for("sess-a")[0]["transcript_digest"]
    assert s.rawstore.exists(digest)
    assert s.rawstore.get(digest) == source_bytes         # byte-verbatim
    assert report.transcripts_retained == 1
    # every stored utterance is recoverable from its transcript_digest (the raw contains it).
    raw_text = s.rawstore.get(digest).decode("utf-8")
    for row in s.store.all_rows():
        assert row["text"] in raw_text


def test_retention_precedes_extraction_even_when_a_session_is_refused(tmp_path: Any) -> None:
    """CS-1 is unconditional: even a secret-refused session's raw is retained (re-ingest after
    guard tuning recovers it) — the raw archive never depends on extraction succeeding."""
    s = _sensor(tmp_path)
    _write_transcript(s.transcripts_dir, "sess-secret",
                      [_rec("user", "my key is AKIA1234567890ABCDEF")])
    report = s.backfill()
    assert report.refused_sessions == ["sess-secret"]
    assert s.store.count() == 0                           # nothing extracted-stored
    # …but the raw WAS retained (CS-1 before CS-3):
    from ops.chat_sensor import _transcript_digest
    raw_text = (s.transcripts_dir / "sess-secret.jsonl").read_text(encoding="utf-8")
    assert s.rawstore.exists(_transcript_digest(raw_text))


# --- Item 3: the secret guard, fail-closed ---------------------------------------------------
@pytest.mark.parametrize("secret", [
    "here is AKIA1234567890ABCDEF for you",                       # AWS access key id
    "sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123",               # sk- api key
    "-----BEGIN RSA PRIVATE KEY-----",                           # PEM header
    "api_key = 0123456789abcdef0123456789abcdef01",             # keyword-bound 32+ token
    "aws_secret_access_key=abcdEFGH1234ijklMNOP5678qrst",        # named aws secret
])
def test_secret_bearing_utterance_is_refused_whole(tmp_path: Any, secret: str) -> None:
    s = _sensor(tmp_path)
    _write_transcript(s.transcripts_dir, "sess-bad",
                      [_rec("user", "clean line"), _rec("assistant", [_text(secret)])])
    report = s.backfill()
    assert report.refused_sessions == ["sess-bad"]        # named, no silent cap
    assert s.store.count() == 0                           # whole session refused, nothing stored
    # the guard itself signals via a named exception carrying the session id (never the value):
    with pytest.raises(SecretInUtteranceError) as ei:
        s._ingest(s.transcripts_dir / "sess-bad.jsonl", report)
    assert "sess-bad" in str(ei.value)
    assert secret not in str(ei.value)                    # the caught secret is never logged


def test_guard_scan_is_clean_on_ordinary_prose() -> None:
    g = ChatSecretGuard()
    for clean in ["let's formalize the connectivity instrument",
                  "the digest is 552f885 and the plan is bp-063",
                  "I think the key insight is the ultrametric"]:
        assert g.scan(clean) is False
        assert g.matched_pattern(clean) is None


def test_one_refused_session_does_not_abort_the_pass(tmp_path: Any) -> None:
    s = _sensor(tmp_path)
    _write_transcript(s.transcripts_dir, "sess-1", [_rec("user", "clean one")])
    _write_transcript(s.transcripts_dir, "sess-bad",
                      [_rec("assistant", [_text("token: 0123456789abcdef0123456789abcdef99")])])
    _write_transcript(s.transcripts_dir, "sess-2", [_rec("user", "clean two")])
    report = s.backfill()
    assert report.refused_sessions == ["sess-bad"]
    assert set(s.store.sessions()) == {"sess-1", "sess-2"}   # clean sessions still ingested
    assert report.sessions_ingested == 2


# --- Item 3: backfill idempotence, active exclusion, all-observed ----------------------------
def test_backfill_is_idempotent(tmp_path: Any) -> None:
    s = _sensor(tmp_path)
    _write_transcript(s.transcripts_dir, "s1", [_rec("user", "a"), _rec("assistant", [_text("b")])])
    _write_transcript(s.transcripts_dir, "s2", [_rec("user", "c")])
    first = s.backfill()
    assert first.utterances_added == 3
    assert first.transcripts_retained == 2
    second = s.backfill()
    assert second.utterances_added == 0                   # identity-keyed store: no dupes
    assert second.transcripts_retained == 0               # rawstore dedup
    assert s.store.count() == 3


def test_active_session_is_excluded(tmp_path: Any) -> None:
    s = _sensor(tmp_path, active="sess-open")
    _write_transcript(s.transcripts_dir, "sess-open", [_rec("user", "mid-append, do not ingest")])
    _write_transcript(s.transcripts_dir, "sess-closed", [_rec("user", "closed, ingest me")])
    report = s.backfill()
    assert report.skipped_active == "sess-open"
    assert s.store.sessions() == ["sess-closed"]


def test_every_stored_row_is_observed(tmp_path: Any) -> None:
    s = _sensor(tmp_path)
    _write_transcript(s.transcripts_dir, "s1",
                      [_rec("user", "owner prose"), _rec("assistant", [_text("agent prose")])])
    s.backfill()
    assert {r["provenance"] for r in s.store.all_rows()} == {Provenance.OBSERVED.value}


def test_sync_skips_already_ingested_sessions(tmp_path: Any) -> None:
    s = _sensor(tmp_path)
    _write_transcript(s.transcripts_dir, "s1", [_rec("user", "first")])
    assert s.sync().sessions_ingested == 1
    # a second sync sees s1 as known and processes nothing new:
    report = s.sync()
    assert report.sessions_ingested == 0
    assert report.utterances_added == 0


def test_report_str_is_informative(tmp_path: Any) -> None:
    s = _sensor(tmp_path)
    _write_transcript(s.transcripts_dir, "s1", [_rec("user", "x")])
    txt = str(s.backfill())
    assert "chat-sensor" in txt and "utterances=1" in txt
