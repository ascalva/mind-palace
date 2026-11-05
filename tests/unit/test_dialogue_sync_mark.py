"""The dialogue sync's high-water mark (`ops/lifecycle/launcher.py` `dialogue_sync`: the library
script `door/sync_dialogue.palace` once a reader), which the heartbeat (ops/heartbeat.py) reads to
ask "anything new since the last sync?".

Proves: a reader whose plan landed leaves `<reader>.synced` with the newest change it saw; a
reader not asked for, a failing edge reader, or a landing that dies midway leaves no mark, so the
next beat retries instead of skipping the turns; a turn the writer refuses (a path's label is
fixed at its first store, R5) is kept as it was and reported, and the rest land.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from core.kernel.provenance import Provenance
from ops.heartbeat import synced_mark
from ops.lifecycle.launcher import dialogue_sync
from tests.fixtures.door import Palace, palace_at

CHATS = {
    "openwebui": [{"chat_id": "c1", "updated_at": 100,
                   "turns": [{"id": "t1", "role": "user", "content": "hi", "timestamp": 100}]},
                  {"chat_id": "c2", "updated_at": 140,
                   "turns": [{"id": "t2", "role": "user", "content": "yo", "timestamp": 140}]}],
    "opencode": [{"chat_id": "s1", "updated_at": 5000,
                  "turns": [{"id": "u1", "role": "user", "content": "hey", "timestamp": 5}]}],
}


def _edge(*, failing: str | None = None) -> Any:
    """The edge readers: each writes its handoff file where the palace's table says it is."""
    def run(argv: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        source = "openwebui" if "edge.openwebui" in argv else "opencode"
        if source == failing:
            return subprocess.CompletedProcess(argv, 1, "", "podman: no such container")
        out = Path(argv[argv.index("--out") + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"source": source, "chats": CHATS[source]}))
        return subprocess.CompletedProcess(argv, 0, "", "")
    return run


@pytest.fixture
def palace(tmp_path: Path) -> Palace:
    return palace_at(tmp_path)


def _sync(p: Palace, **kw: Any) -> int:
    return dialogue_sync(p.cfg, p.root, stores=p.stores, **kw)


def _paths(p: Palace) -> list[str]:
    return sorted(e.source_path for e in p.stores.catalog.active_entries())


def test_a_full_landing_leaves_the_mark_for_its_reader_only(palace, monkeypatch):
    monkeypatch.setattr(subprocess, "run", _edge())
    assert _sync(palace, only={"openwebui"}) == 0
    assert _paths(palace) == ["dialogue/openwebui/c1/t1", "dialogue/openwebui/c2/t2"]
    assert synced_mark(palace.data, "openwebui") == 140           # the newest change it saw
    assert synced_mark(palace.data, "opencode") == 0              # not asked for


def test_a_failing_reader_leaves_no_mark(palace, monkeypatch):
    monkeypatch.setattr(subprocess, "run", _edge(failing="openwebui"))
    assert _sync(palace) == 1
    assert synced_mark(palace.data, "openwebui") == 0
    assert synced_mark(palace.data, "opencode") == 5000           # the other reader still landed
    assert _paths(palace) == ["dialogue/opencode/s1/u1"]


def test_a_landing_that_dies_midway_leaves_no_mark(palace, monkeypatch):
    monkeypatch.setattr(subprocess, "run", _edge())
    real = palace.stores.catalog.record

    def record(path: str, *a: Any, **k: Any) -> Any:
        if path.endswith("/t2"):
            raise RuntimeError("disk full")
        return real(path, *a, **k)

    monkeypatch.setattr(palace.stores.catalog, "record", record)
    assert _sync(palace, only={"openwebui"}) == 1
    assert synced_mark(palace.data, "openwebui") == 0             # retried next beat, not skipped


def test_a_refused_turn_is_kept_and_the_rest_land(palace, monkeypatch, capsys):
    """A turn whose path already holds another label (the writer refuses it, R5: an observed turn
    never supersedes the owner's words, nor the reverse) is kept as it was and reported; the sync
    goes on, and the mark is written, since a retry would refuse it again."""
    monkeypatch.setattr(subprocess, "run", _edge())
    palace.stores.catalog.record("dialogue/openwebui/c1/t1", "d", "kept",
                                 provenance=Provenance.OBSERVED)
    assert _sync(palace, only={"openwebui"}) == 0
    held = palace.stores.catalog.get("dialogue/openwebui/c1/t1")
    assert held is not None and held.digest == "d" and str(held.provenance) == "observed"
    assert palace.stores.catalog.get("dialogue/openwebui/c2/t2") is not None
    assert synced_mark(palace.data, "openwebui") == 140
    assert "'refused': 1" in capsys.readouterr().out
