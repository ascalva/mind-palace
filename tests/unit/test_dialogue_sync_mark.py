"""The dialogue sync's high-water mark (ops/lifecycle/launcher.py `dialogue_sync_now`), which the
heartbeat (ops/heartbeat.py) reads to ask "anything new since the last sync?".

Proves: a source captured in full leaves `<source>.synced` with the newest change it saw; a source
not asked for, a failing edge reader, or a capture that dies midway leaves no mark, so the next
beat retries instead of skipping the turns.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from ops.heartbeat import synced_mark

CHATS = {
    "openwebui": [{"chat_id": "c1", "updated_at": 100,
                   "turns": [{"id": "t1", "role": "user", "content": "hi", "timestamp": 100}]},
                  {"chat_id": "c2", "updated_at": 140,
                   "turns": [{"id": "t2", "role": "user", "content": "yo", "timestamp": 140}]}],
    "opencode": [{"chat_id": "s1", "updated_at": 5000,
                  "turns": [{"id": "u1", "role": "user", "content": "hey", "timestamp": 5}]}],
}


class _Capture:
    def __init__(self, fail_on: str | None = None) -> None:
        self.turns: list[str] = []
        self.fail_on = fail_on

    def capture_turn(self, text: str, *, conversation: str, turn_id: str, role: str,
                     at: str | None) -> tuple[str, bool]:
        if turn_id == self.fail_on:
            raise RuntimeError("embedder down")
        self.turns.append(turn_id)
        return f"dialogue/{conversation}/{turn_id}", True


def _edge(*, failing: str | None = None) -> Any:
    def run(argv: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        source = "openwebui" if "edge.openwebui" in argv else "opencode"
        if source == failing:
            return subprocess.CompletedProcess(argv, 1, "", "podman: no such container")
        out = Path(argv[argv.index("--out") + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"source": source, "chats": CHATS[source]}))
        return subprocess.CompletedProcess(argv, 0, "", "")
    return run


def _sync(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capture: _Capture, **kw: Any) -> int:
    from ops.lifecycle.launcher import Launcher

    monkeypatch.setattr("core.ingest.dialogue.build_dialogue_capture", lambda cfg: capture)
    launcher = Launcher(cfg=SimpleNamespace(paths=SimpleNamespace(data_dir=tmp_path)),  # type: ignore[arg-type]
                        runs=SimpleNamespace(last=lambda: None),  # type: ignore[arg-type]
                        repo_root=tmp_path)
    return launcher.dialogue_sync_now(**kw)


def test_a_full_capture_leaves_the_mark_for_its_source_only(tmp_path, monkeypatch):
    monkeypatch.setattr(subprocess, "run", _edge())
    cap = _Capture()
    assert _sync(tmp_path, monkeypatch, cap, only={"openwebui"}) == 0
    assert cap.turns == ["t1", "t2"]
    assert synced_mark(tmp_path, "openwebui") == 140              # the newest change it saw
    assert synced_mark(tmp_path, "opencode") == 0                 # not asked for


def test_a_failing_reader_leaves_no_mark(tmp_path, monkeypatch):
    monkeypatch.setattr(subprocess, "run", _edge(failing="openwebui"))
    assert _sync(tmp_path, monkeypatch, _Capture()) == 1
    assert synced_mark(tmp_path, "openwebui") == 0
    assert synced_mark(tmp_path, "opencode") == 5000              # the other source still landed


def test_a_capture_that_dies_midway_leaves_no_mark(tmp_path, monkeypatch):
    monkeypatch.setattr(subprocess, "run", _edge())
    with pytest.raises(RuntimeError):
        _sync(tmp_path, monkeypatch, _Capture(fail_on="t2"), only={"openwebui"})
    assert synced_mark(tmp_path, "openwebui") == 0                # retried next beat, not skipped
