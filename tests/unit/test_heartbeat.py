"""The heartbeat (ops/heartbeat.py): plain-code sensing, a pure decision table, effects at the edge.

Proves: the `pmset` and `ps` readings parse (desktop, laptop, Low Power, thermal caps, wrappers that
are not the command); the model probe reads `/slots` only for an awake model, so it never wakes a
sleeping one, and sends lmtune's key; the decision table holds over its whole input grid
(decision-table testing against an independent statement of the rules); the kill switch pauses,
expires, refuses over-long or past pauses and ignores a broken file; the circuit breaker opens
after 3 failed syncs, backs off 1, 2, 4 … 8 hours, half-opens, and closes on a success; a full beat
pushes a due item once (at-least-once: a failed push is retried), caps a burst, syncs only the
pending sources under a heartbeat job, never runs while paused or while another beat holds the
lock, records an error and re-raises it, and never writes lmtune's key anywhere.
"""

from __future__ import annotations

import fcntl
import http.server
import itertools
import json
import os
import threading
from collections.abc import Iterator, Sequence
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from core.stores import tasks as tasks_module
from core.stores.tasks import Item, TaskStore, now_local
from ops import heartbeat as hb

AC = ("Now drawing from 'AC Power'\n -InternalBattery-0 (id=1)\t100%; charged; 0:00 remaining "
      "present: true\n")
BATTERY_23 = ("Now drawing from 'Battery Power'\n -InternalBattery-0 (id=1)\t23%; discharging; "
              "1:12 remaining present: true\n")
DESKTOP = "Now drawing from 'AC Power'\n"
SETTINGS = "System-wide power settings:\n lowpowermode         0\n sleep                1\n"
THERM_OK = ("Note: No thermal warning level has been recorded\n"
            "Note: No performance warning level has been recorded\n")
KEY_SENTINEL = "sk-SENTINEL-never-written"


def _runner(*, batt: str = AC, settings: str = SETTINGS, therm: str = THERM_OK, ps: str = "",
            calls: list[list[str]] | None = None) -> hb.Runner:
    def run(argv: Sequence[str]) -> str:
        argv = list(argv)
        if calls is not None:
            calls.append(argv)
        if argv[0] == "ps":
            return ps
        return {"batt": batt, "therm": therm}.get(argv[-1], settings)
    return run


# ── readings ────────────────────────────────────────────────────────────────────────────────────


def test_power_readings():
    assert hb.read_power(_runner()) == hb.Power("ac", 100, False)
    assert hb.read_power(_runner(batt=BATTERY_23)) == hb.Power("battery", 23, False)
    assert hb.read_power(_runner(batt=DESKTOP)) == hb.Power("ac", None, False)
    assert hb.read_power(_runner(batt="")) == hb.Power("unknown", None, False)
    assert hb.read_power(_runner(settings=" lowpowermode 1\n")).low_power
    assert hb.read_power(_runner(settings=" powermode 1\n")).low_power        # newer Macs
    assert not hb.read_power(_runner(settings=" powermode 2\n")).low_power    # High Power


def test_thermal_readings():
    assert hb.read_thermal(_runner()) is False
    assert hb.read_thermal(_runner(therm="")) is None
    assert hb.read_thermal(_runner(therm="CPU_Scheduler_Limit = 100\nCPU_Speed_Limit = 70\n"))
    assert hb.read_thermal(_runner(therm="CPU_Speed_Limit = 100\n")) is False
    assert hb.read_thermal(_runner(therm="Thermal warning level set to 1.\n"))


def test_palace_processes_counts_commands_not_their_wrappers():
    me, parent = os.getpid(), os.getppid()
    ps = "\n".join([
        f"  501 {parent} 01:00 /bin/zsh -c uv run python scripts/curate_local.py m.json",
        "  502 501 01:00 /usr/bin/time -p uv run python scripts/curate_local.py m.json",
        "  503 502 01:00 /opt/homebrew/bin/uv run python scripts/curate_local.py m.json",
        "  504 503 01:00 /repo/.venv/bin/python scripts/curate_local.py m.json",
        "  600 1 00:05 /repo/.venv/bin/python scripts/palace.py dream",
        "  601 600 00:05 /repo/.venv/bin/python -m some.child",
        f"  {me} {parent} 00:01 /repo/.venv/bin/python scripts/palace.py tick",
        f"  {parent} 1 00:01 /opt/homebrew/bin/uv run python scripts/palace.py tick",
        "  700 1 10:00 /usr/bin/python3 -m http.server",
        "  800 1 00:02 /repo/.venv/bin/python /repo/scripts/palace.py status",
        "  801 1 00:02 /repo/.venv/bin/python scripts/palace.py queue",
        "garbage line",
    ])
    found = hb.palace_processes(_runner(ps=ps), skip={600})
    assert [p["what"] for p in found] == ["scripts/curate_local.py m.json"]
    assert found[0]["pid"] == "503"


# ── the model probe, against a fake llama-server ────────────────────────────────────────────────


class _FakeLlama(http.server.BaseHTTPRequestHandler):
    state: dict[str, Any] = {}

    def do_GET(self) -> None:   # noqa: N802 (http.server's name)
        st = type(self).state
        st["seen"].append((self.path, self.headers.get("Authorization")))
        if st.get("key") and self.headers.get("Authorization") != f"Bearer {st['key']}":
            self.send_response(401)
            self.end_headers()
            return
        body = {"/props": {"is_sleeping": st["asleep"]},
                "/slots": [{"id": 0, "is_processing": st["busy"]}]}.get(self.path)
        self.send_response(200 if body is not None else 404)
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *args: Any) -> None:
        pass


@pytest.fixture
def llama() -> Iterator[tuple[int, dict[str, Any]]]:
    state: dict[str, Any] = {"asleep": False, "busy": False, "key": "", "seen": []}
    handler = type("Handler", (_FakeLlama,), {"state": state})
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv.server_port, state
    srv.shutdown()
    srv.server_close()


def test_the_probe_never_wakes_a_sleeping_model(llama):
    port, st = llama
    st["asleep"] = True
    assert hb.model_state(port) == "asleep"
    assert [p for p, _ in st["seen"]] == ["/props"]


def test_the_probe_tells_busy_from_loaded_and_sends_the_key(llama):
    port, st = llama
    st.update(busy=True, key="k1")
    assert hb.model_state(port) == "unknown"                     # refused without the key
    assert hb.model_state(port, key="k1") == "busy"
    st["busy"] = False
    assert hb.model_state(port, key="k1") == "loaded"
    assert ("/slots", "Bearer k1") in st["seen"]


def test_a_closed_port_is_down():
    import socket

    with socket.socket() as s:   # a port that was free a moment ago
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    assert hb.model_state(port, timeout=0.5) == "down"


# ── the decision table ──────────────────────────────────────────────────────────────────────────


def _item(n: int = 1, kind: str = "reminder") -> Item:
    stamp = "2026-10-29T12:00:00"
    return Item(n, kind, f"item {n}", "", "open", "2026-10-29T11:00", "owner", stamp, stamp,
                None, None, "", "")


def _sensed(**kw: Any) -> hb.Sensed:
    base: dict[str, Any] = dict(at="2026-10-29T12:00:00", power=hb.Power("ac", 100, False),
                                thermal_warning=False, chat_model="asleep", embedder="asleep",
                                jobs=[], to_notify=[], pending={"openwebui": False,
                                                                "opencode": False},
                                breaker="", free_gb=100.0)
    return hb.Sensed(**{**base, **kw})


_POWER = [hb.Power("ac", 100, False), hb.Power("ac", None, False), hb.Power("battery", 80, False),
          hb.Power("battery", 40, False), hb.Power("battery", 39, False),
          hb.Power("battery", None, False), hb.Power("unknown", None, False),
          hb.Power("ac", 100, True)]
_GRID = itertools.product(
    _POWER, (False, True, None), ("busy", "loaded", "asleep", "unknown", "down"),
    ("loaded", "asleep", "busy", "unknown", "down"), ([], ["#3 re-embed"]), (100.0, 9.9),
    ({"openwebui": False, "opencode": False}, {"openwebui": True, "opencode": False},
     {"openwebui": None, "opencode": None}),
    ("", "open after 3 failed syncs in a row; next try 13:00"),
    (hb.ACTIONS, ("notify",), ("sync-dialogue",)), ([], [_item()]))


def test_the_decision_table_over_its_whole_grid():
    """Decision-table testing: the rules restated independently of the code, then every
    combination of readings checked against them (8·3·5·5·2·2·3·2·3·2 = 86,400 rows)."""
    rows = 0
    for power, thermal, chat, emb, jobs, free, pending, breaker, actions, due in _GRID:
        s = _sensed(power=power, thermal_warning=thermal, chat_model=chat, embedder=emb, jobs=jobs,
                    free_gb=free, pending=pending, breaker=breaker, to_notify=due)
        notify, sync, agent = hb.decide(s, hb.Policy(actions=actions))
        assert (notify.action, sync.action, agent.action) == ("notify", "sync-dialogue",
                                                              "wake-agent")
        assert notify.go == ("notify" in actions and bool(due))
        power_ok = (power.source == "ac" or (power.source == "battery"
                                             and (power.percent or 0) >= 40))
        moment_ok = (power_ok and not power.low_power and thermal is False and emb != "down"
                     and chat != "busy" and not jobs and free >= 10)
        # A product of ten axes is past typeshed's typed overloads (six), so each element types as
        # `object`; the pending axis is these dicts by construction (`_GRID`, above).
        flags = cast(dict[str, bool | None], pending)
        assert sync.go == ("sync-dialogue" in actions and any(flags.values())
                           and not breaker and moment_ok), (s, sync)
        assert agent.go is False
        assert notify.reason and sync.reason and agent.reason
        rows += 1
    assert rows == 86_400


def test_a_deferred_sync_says_every_reason():
    s = _sensed(power=hb.Power("battery", 12, True), thermal_warning=True, chat_model="busy",
                embedder="down", jobs=["a", "b"], free_gb=3.0, pending={"opencode": True})
    sync = hb.decide(s, hb.Policy())[1]
    for words in ("battery at 12%", "Low Power", "thermal", "embedder is not running",
                  "chat model is answering", "2 palace job(s)", "disk nearly full"):
        assert words in sync.reason


def test_the_policy_refuses_an_unknown_action(tmp_path):
    toml = tmp_path / "stack.toml"
    toml.write_text('[tick]\nactions = ["notify", "sync-dialog"]\n')
    with pytest.raises(ValueError, match="sync-dialog"):
        hb.load_policy(toml)
    toml.write_text('[tick]\nactions = ["notify"]\nmin_battery_pct = 60\n')
    assert hb.load_policy(toml) == hb.Policy(min_battery_pct=60, actions=("notify",))
    assert hb.load_policy(tmp_path / "absent.toml") == hb.Policy()


# ── the kill switch ─────────────────────────────────────────────────────────────────────────────


def test_the_kill_switch_pauses_expires_and_lifts(tmp_path):
    now = now_local()
    until = hb.pause(tmp_path, "90m", reason="benchmark", now=now)
    assert until == (now + timedelta(minutes=90)).isoformat(timespec="minutes")
    assert hb.paused_until(tmp_path, now=now) == until
    assert hb.paused_until(tmp_path, now=now + timedelta(minutes=91)) is None   # expired
    assert hb.resume(tmp_path) and not hb.resume(tmp_path)
    assert hb.paused_until(tmp_path, now=now) is None
    assert hb.pause(tmp_path, (now + timedelta(days=1)).isoformat(timespec="minutes"), now=now)
    for bad in ("8d", "0m", "tomorrow", "-1h", (now - timedelta(hours=1)).isoformat()):
        with pytest.raises(ValueError):
            hb.pause(tmp_path, bad, now=now)


def test_a_broken_or_forged_pause_never_silences_the_heartbeat(tmp_path):
    f = tmp_path / hb.PAUSE_FILE
    now = now_local()
    for content in ("", "{", "[]", '{"until": 5}', '{"until": "soon"}',
                    json.dumps({"until": (now + timedelta(days=30)).isoformat()})):
        f.write_text(content)
        assert hb.paused_until(tmp_path, now=now) is None, content


# ── the circuit breaker ─────────────────────────────────────────────────────────────────────────


def _sync_job(store: TaskStore, ok: bool) -> None:
    j = store.start_job(hb.SYNC_JOB, pid=1, created_by="heartbeat")
    store.finish_job(j.id, ok=ok, summary="" if ok else "embedder down")


def test_the_breaker_opens_backs_off_half_opens_and_closes(tmp_path):
    store = TaskStore(tmp_path / "t.sqlite")
    try:
        now = now_local()
        for _ in range(2):
            _sync_job(store, ok=False)
        assert hb.breaker_state(store, now=now) == ""              # 2 failures: still closed
        _sync_job(store, ok=False)
        assert "open after 3" in hb.breaker_state(store, now=now)
        assert hb.breaker_state(store, now=now + timedelta(minutes=61)) == ""   # half-open
        _sync_job(store, ok=False)                                 # the one try failed: 2 h
        assert "open after 4" in hb.breaker_state(store, now=now + timedelta(minutes=119))
        assert hb.breaker_state(store, now=now + timedelta(minutes=121)) == ""
        for _ in range(10):
            _sync_job(store, ok=False)
        assert hb.breaker_state(store, now=now + timedelta(hours=7, minutes=59)) != ""
        assert hb.breaker_state(store, now=now + timedelta(hours=8, minutes=1)) == ""  # capped
        _sync_job(store, ok=True)                                  # a success closes it
        assert hb.breaker_state(store, now=now) == ""
        other = store.start_job(hb.SYNC_JOB, pid=1, created_by="owner")   # the owner's own sync
        store.finish_job(other.id, ok=False)
        assert hb.breaker_state(store, now=now) == ""
    finally:
        store.close()


# ── whole beats, every effect faked ─────────────────────────────────────────────────────────────


class _Beat:
    """A data dir, a fake world, and the effects a beat had."""

    def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.data = tmp_path / "data"
        self.cfg: Any = SimpleNamespace(paths=SimpleNamespace(data_dir=self.data),
                                        runtime=SimpleNamespace(port_for=lambda role: 1))
        key = tmp_path / "api-key"
        key.write_text(KEY_SENTINEL)
        self.policy = hb.Policy(chat_key_file=str(key))
        self.notices = tmp_path / "handoff" / "notices.json"
        monkeypatch.setattr(tasks_module, "notices_path", lambda: self.notices)
        self.models = {1: "asleep"}
        self.keys_seen: list[str] = []

        def model_state(port: int, *, key: str = "", timeout: float = 2.0) -> str:
            self.keys_seen.append(key)
            return self.models[port]

        monkeypatch.setattr(hb, "model_state", model_state)
        self.latest: dict[str, int | None] = {"openwebui": 0, "opencode": 0}
        self.pushed: list[tuple[str, str, str]] = []
        self.push_ok = True
        self.synced: list[set[str]] = []
        self.sync_rc = 0
        self.calls: list[list[str]] = []
        self.batt = AC

    def store(self) -> TaskStore:
        return TaskStore(self.data / "tasks.sqlite")

    def notify(self, title: str, subtitle: str, body: str) -> bool:
        self.pushed.append((title, subtitle, body))
        return self.push_ok

    def sync(self, only: set[str]) -> int:
        self.synced.append(only)
        return self.sync_rc

    def run(self) -> int:
        return hb.tick(self.cfg, policy=self.policy, run=_runner(batt=self.batt, calls=self.calls),
                       latest=lambda: dict(self.latest), notify=self.notify, sync=self.sync)

    def record(self) -> dict[str, Any]:
        return json.loads((self.data / hb.TICK_FILE).read_text())


@pytest.fixture
def beat(tmp_path, monkeypatch) -> _Beat:
    b = _Beat(tmp_path, monkeypatch)
    b.data.mkdir(parents=True)
    return b


def test_a_quiet_beat_reads_everything_and_does_nothing(beat):
    assert beat.run() == 0
    rec = beat.record()
    assert [d["go"] for d in rec["decisions"]] == [False, False, False]
    assert rec["sensed"]["power"] == {"source": "ac", "percent": 100, "low_power": False}
    assert beat.pushed == [] and beat.synced == []
    assert json.loads(beat.notices.read_text())["lines"] == []


def test_a_due_item_is_pushed_once_and_a_failed_push_is_retried(beat):
    s = beat.store()
    r = s.add("reminder", "call the dentist",
              due_at=(now_local() - timedelta(minutes=1)).isoformat(timespec="minutes"))
    s.close()
    beat.push_ok = False
    assert beat.run() == 1                                       # the push failed: exit 1
    assert beat.record()["push_failed"] == 1
    beat.push_ok = True
    assert beat.run() == 0
    assert beat.pushed[-1] == ("Ouroboros", "Reminder", "call the dentist")
    assert beat.record()["pushed"] == [r.id]
    assert beat.run() == 0 and len(beat.pushed) == 2             # never pushed again
    assert any("call the dentist" in ln for ln in json.loads(beat.notices.read_text())["lines"])


def test_a_burst_of_due_items_goes_out_over_the_next_beats(beat):
    s = beat.store()
    for n in range(hb.PUSH_PER_TICK + 2):
        s.add("task", f"task {n}", due_at="2026-01-01T00:00")
    s.close()
    beat.run()
    assert len(beat.pushed) == hb.PUSH_PER_TICK
    beat.run()
    assert len(beat.pushed) == hb.PUSH_PER_TICK + 2
    assert beat.pushed[0][1] == "Due 00:00"


def test_new_turns_sync_only_their_source_under_a_heartbeat_job(beat):
    beat.latest = {"openwebui": 50, "opencode": None}            # opencode unreadable
    beat.models[1] = "loaded"
    assert beat.run() == 0
    assert beat.synced == [{"openwebui"}]
    s = beat.store()
    (job,) = s.recent_jobs(limit=5)
    s.close()
    assert (job.title, job.created_by, job.status) == (hb.SYNC_JOB, "heartbeat", "done")
    assert beat.record()["sync_rc"] == 0


def test_a_sync_waits_for_a_good_moment(beat):
    beat.latest = {"openwebui": 50, "opencode": 0}
    beat.batt = BATTERY_23
    beat.run()
    assert beat.synced == []
    assert "battery at 23%" in beat.record()["decisions"][1]["reason"]


def test_failing_syncs_open_the_breaker(beat):
    beat.latest = {"openwebui": 50, "opencode": 0}
    beat.sync_rc = 1
    for _ in range(3):
        assert beat.run() == 1
    assert beat.run() == 0 and len(beat.synced) == 3            # the fourth beat holds off
    assert "circuit breaker open" in beat.record()["decisions"][1]["reason"]


def test_a_paused_beat_reads_nothing_and_does_nothing(beat):
    s = beat.store()
    s.add("reminder", "x", due_at="2026-01-01T00:00")
    s.close()
    hb.pause(beat.data, "1h")
    assert beat.run() == 0
    assert beat.calls == [] and beat.pushed == [] and beat.keys_seen == []
    assert beat.record()["paused_until"]
    hb.resume(beat.data)
    beat.run()
    assert len(beat.pushed) == 1


def test_a_second_beat_never_runs_beside_the_first(beat):
    with open(beat.data / hb.LOCK_FILE, "a") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert beat.run() == 0
    assert beat.calls == [] and not (beat.data / hb.TICK_FILE).exists()


def test_an_error_is_recorded_then_raised(beat, monkeypatch):
    def broken(*a: Any, **k: Any) -> Any:
        raise RuntimeError("ps exploded")

    monkeypatch.setattr(hb, "palace_processes", broken)
    with pytest.raises(RuntimeError):
        beat.run()
    assert "ps exploded" in beat.record()["error"]


def test_the_key_is_used_but_never_written(beat, capsys):
    beat.latest = {"openwebui": 50, "opencode": 0}
    beat.models[1] = "loaded"
    beat.run()
    assert KEY_SENTINEL in beat.keys_seen                        # the chat probe got it
    written = "".join(p.read_text(errors="ignore") for p in beat.data.rglob("*") if p.is_file())
    assert KEY_SENTINEL not in written + beat.notices.read_text() + capsys.readouterr().out


def test_last_tick_is_the_watchdog(beat):
    assert hb.last_tick(beat.data) is None
    beat.run()
    fresh = hb.last_tick(beat.data, interval_s=900)
    assert fresh is not None and fresh["stale"] is False and len(fresh["decided"]) == 3
    late = hb.last_tick(beat.data, interval_s=900, now=now_local() + timedelta(minutes=31))
    assert late is not None and late["stale"] is True


# ── the notification itself ─────────────────────────────────────────────────────────────────────


def test_a_notification_carries_text_as_arguments_never_as_script(monkeypatch):
    seen: list[list[str]] = []

    def fake_run(argv: list[str], **kw: Any) -> Any:
        seen.append(argv)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(hb.subprocess, "run", fake_run)
    hostile = 'x" & (do shell script "touch /tmp/pwned") & "' + "y" * 500
    assert hb.macos_notify("Ouroboros", "Reminder", hostile)
    (argv,) = seen
    assert argv[: len(hb._NOTIFY_SCRIPT)] == list(hb._NOTIFY_SCRIPT)   # the script is constant
    assert argv[len(hb._NOTIFY_SCRIPT):] == ["Ouroboros", "Reminder", hostile[:240]]
