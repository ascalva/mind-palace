"""The Ambassador's task tools (agents/ambassador/mcp.py) and the heartbeat's LaunchAgent
(scripts/stack.py), against a temporary ledger: no store, model or launchd of this machine.

Proves: remind / task_add / task_list / task_update round-trip through the ledger and stamp `now`;
a finished item leaves the open list but stays reachable with `include_done`; a time the ledger
cannot read is refused, never guessed; every write refreshes the notices; the LaunchAgent runs
`palace tick` at the configured interval as a background process and carries no secret.
"""

from __future__ import annotations

import importlib.util
import json
import plistlib
from pathlib import Path

import pytest

from core.stores import tasks as tasks_module
from core.stores.tasks import TaskStore

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def ambassador(tmp_path, monkeypatch):
    from agents.ambassador.mcp import Ambassador

    monkeypatch.setattr(tasks_module, "open_task_store",
                        lambda config=None: TaskStore(tmp_path / "tasks.sqlite"))
    monkeypatch.setattr(tasks_module, "notices_path", lambda: tmp_path / "notices.json")
    return Ambassador()


def test_the_task_tools_round_trip(ambassador, tmp_path):
    r = ambassador.remind("call the dentist", "+1h")
    assert r["reminder"]["kind"] == "reminder" and r["reminder"]["due_at"] and r["now"]
    t = ambassador.task_add("file taxes", detail="by Friday", due="2026-11-02T17:00")
    assert t["added"]["due_at"] == "2026-11-02T17:00"
    assert {i["title"] for i in ambassador.task_list()["items"]} == {"call the dentist",
                                                                     "file taxes"}
    u = ambassador.task_update(t["added"]["id"], status="done", note="filed")
    assert u["updated"]["status"] == "done" and u["updated"]["last_note"].endswith("filed")
    assert {i["title"] for i in ambassador.task_list()["items"]} == {"call the dentist"}
    done = ambassador.task_list(include_done=True)["items"]
    assert any(i["title"] == "file taxes" and i["status"] == "done" for i in done)
    assert json.loads((tmp_path / "notices.json").read_text())["lines"] == []   # nothing due


def test_a_time_the_ledger_cannot_read_is_refused(ambassador):
    with pytest.raises(ValueError):
        ambassador.remind("x", "tomorrow-ish")
    with pytest.raises(ValueError):
        ambassador.task_add("x", due="next week")
    assert ambassador.task_list()["items"] == []


def test_a_reminder_already_due_reaches_the_notices(ambassador, tmp_path):
    ambassador.remind("stretch", "+0m")
    (line,) = json.loads((tmp_path / "notices.json").read_text())["lines"]
    assert "stretch" in line and "reminder due" in line


def test_the_heartbeat_agent_runs_the_tick_quietly_and_holds_no_secret():
    spec = importlib.util.spec_from_file_location("stack_script", ROOT / "scripts" / "stack.py")
    assert spec and spec.loader
    stack = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stack)
    plist = stack._tick_plist()
    assert plist["ProgramArguments"][-2:] == ["scripts/palace.py", "tick"]
    assert plist["StartInterval"] == stack.CFG["tick"]["interval_s"] == 900
    assert plist["ProcessType"] == "Background" and plist["LowPriorityIO"] is True
    assert "KeepAlive" not in plist                       # a beat, not a daemon
    text = plistlib.dumps(plist).decode()
    assert "api-key" not in text and "Bearer" not in text
