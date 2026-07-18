"""The chat sensor wired into the scheduler as a background `chat_sync` job (bp-068 Item 1).

Pins the scheduler integration: the enqueue lands on the always-pinned tier at BACKGROUND priority
(a model-less file scan must never force a worker load), the handler drives the idempotent
`ChatSensor.sync()` and lands OBSERVED rows, a re-run adds nothing (idempotent — the falsifier is a
double-ingest), a secret-bearing transcript is refused whole (fail-closed, the session named), and
the REUSED `ops.chat_sensor.build_chat_sensor(cfg)` is the wiring path (no duplicate builder,
finding-0108). scheduler never imports core/ops at runtime here (the sensor is injected).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from config.loader import get_config
from core.stores.chatlog import ChatlogStore
from core.stores.rawstore import RawStore
from ops.chat_sensor import ChatSecretGuard, ChatSensor, build_chat_sensor
from scheduler.chat_sync import CHAT_SYNC_KIND, chat_sync_handler, enqueue_chat_sync
from scheduler.queue import PRIORITY_BACKGROUND, Job, JobQueue
from scheduler.router import Router

# The handler ignores its Job argument entirely (see scheduler/chat_sync.py) — a bare placeholder is
# the right double (Job is a wide frozen row; the cast says "this never matters here"), mirroring
# tests/integration/test_vault_sync_wiring.py.
_JOB = cast(Job, object())


# --- fixtures (mirror tests/unit/test_chat_sensor.py: sessionId == filename stem, measured Q1) ---
def _rec(rtype: str, text: str, *, session_id: str) -> dict[str, Any]:
    return {"type": rtype, "sessionId": session_id, "timestamp": "2026-07-18T00:00:00Z",
            "message": {"role": rtype, "content": [{"type": "text", "text": text}]}}


def _write_transcript(dirp: Path, session_id: str, lines: list[dict[str, Any]]) -> None:
    (dirp / f"{session_id}.jsonl").write_text(
        "\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")


def _sensor(tmp_path: Path) -> ChatSensor:
    """A real sensor over a temp transcripts dir, tmp rawstore, in-memory chatlog store."""
    transcripts = tmp_path / "transcripts"
    transcripts.mkdir()
    return ChatSensor(
        transcripts_dir=transcripts,
        rawstore=RawStore(tmp_path / "raw"),
        store=ChatlogStore(Path(":memory:")),
        guard=ChatSecretGuard(),
    )


# --- enqueue: pinned tier, background priority (G2 — the direct-pin, no router edit) -------------
def test_enqueue_pins_to_the_always_warm_tier_at_background_priority() -> None:
    cfg = get_config()
    queue = JobQueue(Path(":memory:"))
    job = enqueue_chat_sync(queue, Router(cfg))
    assert job.kind == CHAT_SYNC_KIND
    assert job.tier == cfg.pinned_model.tier          # model-less → ensure_tier is a no-op
    assert job.priority == PRIORITY_BACKGROUND        # yields to interactive/reactive work
    assert queue.depth() == 1


# --- handler: drives sync(), lands OBSERVED rows ------------------------------------------------
def test_handler_ingests_a_seeded_transcript(tmp_path: Path) -> None:
    sensor = _sensor(tmp_path)
    _write_transcript(sensor.transcripts_dir, "sess-a",
                      [_rec("user", "hello there", session_id="sess-a"),
                       _rec("assistant", "hi back", session_id="sess-a")])
    msg = chat_sync_handler(sensor)(_JOB)
    assert msg is not None and msg.startswith("chat sync:")
    assert sensor.store.sessions() == ["sess-a"]
    assert len(sensor.store.rows_for("sess-a")) == 2


# --- falsifier: a double-ingest must add nothing (idempotent) -----------------------------------
def test_second_run_is_a_no_op(tmp_path: Path) -> None:
    sensor = _sensor(tmp_path)
    _write_transcript(sensor.transcripts_dir, "sess-a",
                      [_rec("user", "only once", session_id="sess-a")])
    handler = chat_sync_handler(sensor)
    handler(_JOB)
    before = len(sensor.store.rows_for("sess-a"))
    handler(_JOB)                                     # re-run
    assert len(sensor.store.rows_for("sess-a")) == before == 1      # no double-ingest


# --- falsifier: a secret-bearing transcript is refused WHOLE, nothing stored --------------------
def test_secret_bearing_session_is_refused_whole(tmp_path: Path) -> None:
    sensor = _sensor(tmp_path)
    _write_transcript(sensor.transcripts_dir, "sess-secret",
                      [_rec("user", "here is my key AKIA1234567890ABCDEF and more",
                            session_id="sess-secret")])
    chat_sync_handler(sensor)(_JOB)
    assert sensor.store.sessions() == []              # fail-closed: nothing landed


# --- the REUSED builder is the wiring path (no duplicate — finding-0108 G1) ---------------------
def test_build_chat_sensor_is_reused_from_ops_and_wires_the_handles() -> None:
    sensor = build_chat_sensor(get_config())
    assert isinstance(sensor, ChatSensor)
    # transcripts dir is config-derived (REPO_ROOT slug under ~/.claude/projects), not hard-coded
    assert "/.claude/projects/" in str(sensor.transcripts_dir)
    assert isinstance(sensor.guard, ChatSecretGuard)
    assert sensor.active_session_id is None           # the daemon is not a live CLI session (Q2)
