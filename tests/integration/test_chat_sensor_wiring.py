"""The chat sensor wired to RUN — the daemon job path + the `palace ingest-chat` verb (bp-068 §7.2).

Two integration seams, both deterministic (warm=False, no Ollama; temp stores; local files only):
  1. A real `Supervisor` with the `chat_sync` handler registered drains an `enqueue_chat_sync` job
     on the always-pinned tier and the OBSERVED chatlog store gains rows (the daemon's ingest path —
     the sensor bp-063 built but nothing invoked, now invoked).
  2. `Launcher.ingest_chat()` (the `palace ingest-chat` verb) builds the sensor and runs one sync,
     printing the report and returning 0 — the owner's manual first-ingest trigger.

The launcher REGISTERS `CHAT_SYNC_KIND` and enqueues it at catch-up + housekeeping
(build_components, launcher.py); that wiring is exercised structurally here via the same handler +
enqueue the launcher uses, without standing up the full model stack.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

from config.loader import load_config
from core.models.loader import TwoSlotLoader
from core.models.ollama_client import OllamaClient
from core.models.registry import Registry
from core.stores.chatlog import ChatlogStore
from core.stores.rawstore import RawStore
from ops.chat_sensor import ChatSecretGuard, ChatSensor
from ops.lifecycle.launcher import build_launcher
from scheduler.chat_sync import CHAT_SYNC_KIND, chat_sync_handler, enqueue_chat_sync
from scheduler.presence import Presence
from scheduler.queue import DONE, JobQueue
from scheduler.router import Router
from scheduler.supervisor import Supervisor


def _seeded_sensor(tmp_path: Path) -> ChatSensor:
    """A real sensor over a temp transcripts dir (one seeded session), tmp raw, in-memory store."""
    transcripts = tmp_path / "transcripts"
    transcripts.mkdir()
    lines = [
        {"type": "user", "sessionId": "sess-a", "timestamp": "2026-07-18T00:00:00Z",
         "message": {"role": "user",
                     "content": [{"type": "text", "text": "wire the chat sensor"}]}},
        {"type": "assistant", "sessionId": "sess-a", "timestamp": "2026-07-18T00:00:01Z",
         "message": {"role": "assistant",
                     "content": [{"type": "text", "text": "on it"}]}},
    ]
    (transcripts / "sess-a.jsonl").write_text(
        "\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")
    return ChatSensor(transcripts_dir=transcripts, rawstore=RawStore(tmp_path / "raw"),
                      store=ChatlogStore(Path(":memory:")), guard=ChatSecretGuard())


def _loader(cfg: Any) -> TwoSlotLoader:
    return TwoSlotLoader(config=cfg, client=OllamaClient(cfg.ollama), registry=Registry(cfg))


# --- 1. the daemon path: enqueue + drain + rows land -------------------------------------------
def test_daemon_runs_a_chat_sync_job_and_the_store_gains_rows(tmp_path: Path) -> None:
    cfg = load_config()
    sensor = _seeded_sensor(tmp_path)
    queue = JobQueue(tmp_path / "q.db")
    sup = Supervisor(
        queue=queue, loader=_loader(cfg),
        handlers={CHAT_SYNC_KIND: chat_sync_handler(sensor)},
        presence=Presence(idle_probe=lambda: 10_000.0),   # owner idle → nothing gated
        warm=False,
    )
    sup.loader.ensure_pinned(warm=False)                  # pinned tier resident, no Ollama call

    job = enqueue_chat_sync(queue, Router(cfg))
    assert job.kind == CHAT_SYNC_KIND
    assert job.tier == cfg.pinned_model.tier              # model-less job on the always-warm tier

    assert sup.run() == 1                                 # the supervisor drains the chat_sync job
    assert queue.get(job.id).state == DONE
    assert sensor.store.sessions() == ["sess-a"]          # OBSERVED rows landed
    assert len(sensor.store.rows_for("sess-a")) == 2


# --- 2. the `palace ingest-chat` verb runs the sensor in-process -------------------------------
def test_ingest_chat_verb_runs_the_sensor(tmp_path: Path, monkeypatch, capsys) -> None:
    sensor = _seeded_sensor(tmp_path)
    # The verb builds the sensor via ops.chat_sensor.build_chat_sensor (reused, finding-0108);
    # inject the temp-store sensor so the ingest is hermetic (no read of the real ~/.claude dir).
    monkeypatch.setattr("ops.chat_sensor.build_chat_sensor", lambda config=None, **kw: sensor)
    cfg = dataclasses.replace(
        load_config(), paths=dataclasses.replace(load_config().paths, data_dir=tmp_path))
    launcher = build_launcher(config=cfg)               # opens the run ledger under tmp — hermetic

    assert launcher.ingest_chat() == 0
    assert sensor.store.sessions() == ["sess-a"]         # the manual trigger ingested the session
    assert "chat ingest:" in capsys.readouterr().out     # the report is printed
