"""The heartbeat: `palace tick`, every 15 minutes (`com.mind-palace.tick`, installed by `stack up`).

Phase 1 of docs/brainstorms/ambassador-agent-loop.md (the loop's gaps: dn-agentic-loop), built to
one rule: **the tick never loads a model to decide whether to load one.** Plain code reads the
machine and the ledger, a decision table turns the readings into actions, and only an action the
table picks can wake a model. In phase 1 the only one that can is the dialogue sync, which wakes
the small embedder for new turns only. Nothing here wakes the chat model: no phase-1 work needs
reasoning, and the Ambassador speaks when the owner expects it (dn-ambassador-as-reasoning-agent).

Patterns, by name, for whoever debugs or extends this:
- Sense, decide, act (a control loop): `sense` reads, `decide` chooses, `tick` acts and records.
- Functional core, imperative shell: `decide` is a pure function of the readings; every effect
  (subprocesses, HTTP, files, notifications) lives in the shell and is injectable, so tests swap
  them out (ports and adapters).
- Decision table: each action has one outcome for every combination of readings, and the tests
  walk the whole grid (decision-table testing) plus generated inputs (property-based testing).
- Fail-safe defaults: a reading that failed blocks the work it guards (power, heat, disk, the
  embedder); the one that only costs speed (is the chat model mid-answer?) fails open.
- High-water mark: a dialogue source is pending when its newest change is past the mark its last
  *successful* sync left (`<source>.synced`), so a failed sync is retried, never skipped.
- Scatter-gather: the dialogue sources are asked at once, each in its own process.
- Circuit breaker with exponential backoff (Nygard, *Release It!*): after 3 failed heartbeat syncs
  in a row it opens for 1 hour, doubling per further failure up to 8; then it half-opens: one try,
  and a success closes it. Derived from the ledger, so it keeps no state of its own.
- Reconciliation loop: a job the ledger calls running whose process is gone is closed as failed.
- At-least-once delivery: a due item is marked pushed only after its push succeeded.
- Kill switch with expiry (a time-boxed feature flag): `palace tick pause 2h` stops everything
  until then (7 days at most); `palace tick resume` lifts it; `[tick] actions` turns rows off.
- Single-instance lock (flock) and atomic writes (a temp file, then a rename).
- Watchdog: `last_tick` calls a beat older than two intervals stale, and the bridge drops notices
  older than 3 hours, so a dead heartbeat never passes old news off as current.
- Lazy loading: the launcher (and duckdb behind it, ~190 ms) is imported only when a sync runs.

Every input the table reads is exact (a percentage, a time, a pid), so code decides it. A local
decision model (Ollama's `/v1/systemone`, Jev's wire format) earns a row once the heartbeat reads
language: mail and calendar (phase 2), commitments in new turns, sensor events. Jev stays for the
harder judgments and research, under the owner's ruling. Liveness in general (a wedged daemon) is
docs/design-notes/dn-supervision-and-liveness.md; this tick is an outside view, run by launchd.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any

from core.kernel.config import REPO_ROOT, Config
from core.stores.tasks import (
    Item,
    TaskStore,
    now_local,
    open_task_store,
    parse_when,
    run_as_job,
    write_notices,
)

TICK_FILE, LOCK_FILE, PAUSE_FILE = "tick.json", "tick.lock", "tick.pause"
ACTIONS = ("notify", "sync-dialogue")
EDGE_READERS = {"openwebui": "edge.openwebui", "opencode": "edge.opencode_sessions"}
SYNC_JOB = "dialogue sync"
PUSH_PER_TICK = 5               # a burst of due items goes out over the next beats, not as a flood
MAX_PAUSE = timedelta(days=7)   # "temporarily": every pause ends
BREAKER_AFTER = 3               # failed heartbeat syncs in a row before the breaker opens
BREAKER_MAX_HOURS = 8
_PALACE_COMMANDS = ("scripts/palace.py", "scripts/curate_local.py", "eval/")
_READ_ONLY = re.compile(r"scripts/palace\.py\s+(status|queue|tick)\b")   # quick reads, not work
_NOTIFY_SCRIPT = ("osascript", "-e", "on run argv",
                  "-e", "display notification (item 3 of argv) with title (item 1 of argv) "
                        "subtitle (item 2 of argv)",
                  "-e", "end run")

Runner = Callable[[Sequence[str]], str]
Notifier = Callable[[str, str, str], bool]


def _run(argv: Sequence[str]) -> str:
    """A fixed argv, no shell, a deadline; a failure reads as empty output."""
    try:
        return subprocess.run(list(argv), capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def _atomic_write(path: Path, doc: Any) -> None:
    """Atomic write: a reader sees the old file or the new one, never half of one."""
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


# ── policy and the kill switch ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Policy:
    """config/stack.toml [tick]."""

    interval_s: int = 900
    min_battery_pct: int = 40          # on battery below this, models stay asleep
    min_free_gb: float = 10.0          # below this nothing writes, and the owner hears of it
    chat_key_file: str = ""            # lmtune's API key file: its /props and /slots need it
    actions: tuple[str, ...] = ACTIONS  # a row left out never runs (a feature flag per action)


def load_policy(stack_toml: Path | None = None) -> Policy:
    path = stack_toml or REPO_ROOT / "config" / "stack.toml"
    t = tomllib.loads(path.read_text()).get("tick", {}) if path.exists() else {}
    kw: dict[str, Any] = {k: t[k] for k in ("interval_s", "min_battery_pct", "min_free_gb",
                                            "chat_key_file") if k in t}
    if "actions" in t:
        unknown = sorted(set(t["actions"]) - set(ACTIONS))
        if unknown:   # a typo must not silently turn a row off
            raise ValueError(f"[tick] actions: unknown {unknown}; known: {list(ACTIONS)}")
        kw["actions"] = tuple(t["actions"])
    return Policy(**kw)


def chat_key(policy: Policy) -> str:
    """lmtune's API key for its loopback probes: read from its 0600 file, never printed."""
    path = Path(policy.chat_key_file).expanduser() if policy.chat_key_file else None
    return path.read_text().strip() if path and path.is_file() else ""


def pause(data_dir: Path, duration: str, *, reason: str = "",
          now: datetime | None = None) -> str:
    """Kill switch with expiry: stop every action for `duration` (30m, 2h, 1d) or until a local
    time (2026-10-30T09:00), 7 days at most. Returns when the pause ends."""
    now = now or now_local()
    spec = duration if duration[:1] == "+" or "T" in duration or "-" in duration else f"+{duration}"
    try:
        until = datetime.fromisoformat(parse_when(spec, now=now))
    except ValueError:
        raise ValueError(f"{duration!r}: use 30m, 2h, 1d or a local time like "
                         "2026-10-30T09:00") from None
    if until <= now:
        raise ValueError("a pause must end in the future")
    if until - now > MAX_PAUSE:
        raise ValueError("a pause lasts 7 days at most: the heartbeat carries the reminders")
    data_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write(data_dir / PAUSE_FILE, {"until": until.isoformat(timespec="minutes"),
                                          "set_at": now.isoformat(timespec="seconds"),
                                          "reason": reason[:200]})
    return until.isoformat(timespec="minutes")


def resume(data_dir: Path) -> bool:
    try:
        (data_dir / PAUSE_FILE).unlink()   # our own control file, not the owner's data
    except FileNotFoundError:
        return False
    return True


def paused_until(data_dir: Path, *, now: datetime | None = None) -> str | None:
    """When the pause ends, while one holds. An expired, unreadable or over-long pause counts as
    none: a broken switch must not silence the reminders for good."""
    try:
        doc = json.loads((data_dir / PAUSE_FILE).read_text(encoding="utf-8"))
        until = datetime.fromisoformat(doc["until"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    now = now or now_local()
    if until <= now or until - now > MAX_PAUSE:
        return None
    return until.isoformat(timespec="minutes")


# ── sense ───────────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Power:
    source: str            # "ac" | "battery" | "unknown" (pmset said nothing)
    percent: int | None    # None on a Mac without a battery
    low_power: bool


@dataclass(frozen=True)
class Sensed:
    at: str
    power: Power
    thermal_warning: bool | None          # None: unreadable
    chat_model: str                       # busy | loaded | asleep | down | unknown
    embedder: str
    jobs: list[str]                       # palace work running now, ledger or bare process
    to_notify: list[Item]                 # due, not pushed yet
    pending: dict[str, bool | None]       # source -> changed since its last sync (None: unread)
    breaker: str                          # "" while closed; else why the sync is held off
    free_gb: float


def read_power(run: Runner = _run) -> Power:
    batt = run(["pmset", "-g", "batt"])
    if "drawing from" not in batt:
        return Power("unknown", None, False)
    m = re.search(r"(\d+)%;", batt)
    settings = run(["pmset", "-g"])
    low = re.search(r"^\s*lowpowermode\s+(\d+)", settings, re.M)
    mode = re.search(r"^\s*powermode\s+(\d+)", settings, re.M)   # newer Macs: 1 = Low Power
    return Power(source="battery" if "'Battery Power'" in batt else "ac",
                 percent=int(m.group(1)) if m else None,
                 low_power=bool(low and low.group(1) != "0") or bool(mode and mode.group(1) == "1"))


def read_thermal(run: Runner = _run) -> bool | None:
    """True when macOS recorded a thermal or performance warning or caps the CPU; None when
    `pmset` said nothing."""
    out = run(["pmset", "-g", "therm"])
    if not out.strip():
        return None
    cap = re.search(r"CPU_Speed_Limit\s*=\s*(\d+)", out)
    if cap and int(cap.group(1)) < 100:
        return True
    return any("warning level" in ln and "No " not in ln for ln in out.splitlines())


def model_state(port: int, *, key: str = "", timeout: float = 2.0) -> str:
    """A llama-server on loopback: busy (mid-request), loaded, asleep, down, or unknown (it
    refused or is starting). `/slots` is read only when `/props` says the model is awake."""

    def get(path: str) -> Any:
        req = urllib.request.Request(f"http://127.0.0.1:{port}{path}",
                                     headers={"Authorization": f"Bearer {key}"} if key else {})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())

    try:
        props = get("/props")
    except urllib.error.HTTPError:
        return "unknown"
    except (OSError, ValueError):
        return "down"
    if isinstance(props, dict) and props.get("is_sleeping"):
        return "asleep"
    try:
        slots = get("/slots")
    except (OSError, ValueError):
        return "loaded"
    busy = isinstance(slots, list) and any(isinstance(s, dict) and s.get("is_processing")
                                           for s in slots)
    return "busy" if busy else "loaded"


def palace_processes(run: Runner = _run, *, skip: set[int] | None = None) -> list[dict[str, str]]:
    """Long palace commands running now, ledger or not: one entry per command (a `uv run` parent
    and its python child are one), leaving out `skip` pids, their parents, and this process."""
    rows = []
    for line in run(["ps", "-Ao", "pid=,ppid=,etime=,command="]).splitlines():
        parts = line.strip().split(None, 3)
        if len(parts) == 4 and parts[0].isdigit() and parts[1].isdigit():
            rows.append((int(parts[0]), int(parts[1]), parts[2], parts[3]))
    skip = set(skip or ()) | {os.getpid(), os.getppid()}
    parents = {ppid for pid, ppid, _, _ in rows if pid in skip}
    found: dict[str, dict[str, str]] = {}
    for pid, _, etime, command in rows:
        exe = os.path.basename(command.split(None, 1)[0])
        if pid in skip or pid in parents or not (exe.startswith("python") or exe == "uv"):
            continue   # a shell or `time` wrapping a palace command is not the command
        if ("python" in command and any(c in command for c in _PALACE_COMMANDS)
                and not _READ_ONLY.search(command)):
            what = command.split("python", 1)[-1].strip()[:120]
            found.setdefault(what, {"pid": str(pid), "elapsed": etime, "what": what})
    return list(found.values())


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)   # signal 0: a liveness probe that delivers nothing
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def synced_mark(data_dir: Path, source: str) -> int:
    """High-water mark: the newest change the last successful sync of `source` captured."""
    try:
        doc = json.loads((data_dir / "handoff" / "dialogue" / f"{source}.synced").read_text())
        return int(doc["latest"])
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def sources_latest(*, repo_root: Path = REPO_ROOT, timeout: float = 60.0) -> dict[str, int | None]:
    """Scatter-gather: every source's edge reader starts at once (each its own process, as in the
    sync itself), then the answers are gathered under one deadline. A reader that fails, hangs
    or answers nonsense reads as None."""
    procs: dict[str, subprocess.Popen[str] | None] = {}
    for source, module in EDGE_READERS.items():
        try:
            procs[source] = subprocess.Popen([sys.executable, "-m", module, "--latest"],
                                             cwd=repo_root, stdout=subprocess.PIPE,
                                             stderr=subprocess.DEVNULL, text=True)
        except OSError:
            procs[source] = None
    out: dict[str, int | None] = {}
    deadline = time.monotonic() + timeout
    for source, proc in procs.items():
        if proc is None:
            out[source] = None
            continue
        try:
            stdout, _ = proc.communicate(timeout=max(0.1, deadline - time.monotonic()))
            out[source] = int(json.loads(stdout)["latest"]) if proc.returncode == 0 else None
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            out[source] = None
        except (ValueError, KeyError, TypeError):
            out[source] = None
    return out


def breaker_state(store: TaskStore, *, now: datetime | None = None) -> str:
    """Circuit breaker with exponential backoff, read off the ledger: "" while closed or
    half-open (one try allowed), else why the heartbeat's sync is held off and until when."""
    streak = 0
    recent = store.recent_jobs(title=SYNC_JOB, created_by="heartbeat", limit=BREAKER_AFTER + 8)
    for job in recent:   # newest first
        if job.status != "failed":
            break
        streak += 1
    if streak < BREAKER_AFTER:
        return ""
    hours = min(2 ** (streak - BREAKER_AFTER), BREAKER_MAX_HOURS)
    retry = datetime.fromisoformat(recent[0].finished_at or recent[0].updated_at) + timedelta(
        hours=hours)
    if (now or now_local()) >= retry:
        return ""   # half-open
    return f"open after {streak} failed syncs in a row; next try {retry:%H:%M}"


def sense(cfg: Config, store: TaskStore, policy: Policy, *, run: Runner = _run,
          latest: Callable[[], dict[str, int | None]] = sources_latest) -> Sensed:
    running = store.select(kinds=("job",), statuses=("running",))
    procs = palace_processes(run, skip={j.pid for j in running if j.pid})
    data = cfg.paths.data_dir
    pending = {src: (None if at is None else at > synced_mark(data, src))
               for src, at in latest().items()}
    return Sensed(
        at=now_local().isoformat(),
        power=read_power(run),
        thermal_warning=read_thermal(run),
        chat_model=model_state(cfg.runtime.port_for("routine") or 8080, key=chat_key(policy)),
        embedder=model_state(cfg.runtime.port_for("embedding") or 8081),
        jobs=[f"#{j.id} {j.title}" for j in running] + [p["what"] for p in procs],
        to_notify=store.to_notify(),
        pending=pending,
        breaker=breaker_state(store),
        free_gb=shutil.disk_usage(data).free / 1e9,
    )


# ── decide (pure) ───────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Decision:
    action: str     # notify | sync-dialogue | wake-agent
    go: bool
    reason: str


def model_blockers(s: Sensed, p: Policy) -> list[str]:
    """Why no model may wake now; empty when one may. Fail-safe: an unreadable guard blocks."""
    why = []
    if s.power.source == "unknown":
        why.append("power state unreadable")
    elif s.power.source == "battery" and (s.power.percent or 0) < p.min_battery_pct:
        why.append(f"on battery at {s.power.percent}%")
    if s.power.low_power:
        why.append("Low Power Mode is on")
    if s.thermal_warning is None:
        why.append("thermal state unreadable")
    elif s.thermal_warning:
        why.append("the Mac is under thermal pressure")
    if s.embedder == "down":
        why.append("the embedder is not running")
    if s.chat_model == "busy":   # fails open: not knowing only costs speed
        why.append("the chat model is answering")
    if s.jobs:
        why.append(f"{len(s.jobs)} palace job(s) running")
    if s.free_gb < p.min_free_gb:
        why.append(f"disk nearly full ({s.free_gb:.0f} GB free)")
    return why


def decide(s: Sensed, p: Policy) -> list[Decision]:
    """The decision table. Pushing a due item needs no model, so only its flag stops it. The sync
    wakes the embedder, so it needs new turns, a closed breaker and a good moment. The chat
    model has no phase-1 work; that row is where scheduled runs and chartered dreams will go."""
    off = "turned off in [tick] actions"
    if "notify" not in p.actions:
        notify = Decision("notify", False, off)
    else:
        notify = Decision("notify", bool(s.to_notify), f"{len(s.to_notify)} item(s) came due"
                          if s.to_notify else "nothing came due")
    new = [src for src, changed in s.pending.items() if changed]
    unread = [src for src, changed in s.pending.items() if changed is None]
    blockers = model_blockers(s, p)
    if "sync-dialogue" not in p.actions:
        sync = Decision("sync-dialogue", False, off)
    elif not new:
        sync = Decision("sync-dialogue", False, "no new conversations"
                        + (f" ({', '.join(unread)} unreadable)" if unread else ""))
    elif s.breaker:
        sync = Decision("sync-dialogue", False, f"circuit breaker {s.breaker}")
    elif blockers:
        sync = Decision("sync-dialogue", False, "deferred: " + "; ".join(blockers))
    else:
        sync = Decision("sync-dialogue", True, "new turns in " + ", ".join(new))
    return [notify, sync, Decision("wake-agent", False, "no scheduled work needs reasoning")]


# ── act ─────────────────────────────────────────────────────────────────────────────────────────


def macos_notify(title: str, subtitle: str, body: str) -> bool:
    """Notification Center, local. The text travels as arguments to a fixed script, never as
    script, so no reminder title can inject AppleScript."""
    try:
        r = subprocess.run([*_NOTIFY_SCRIPT, title, subtitle, body[:240]], capture_output=True,
                           timeout=10)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0


def push(items: Sequence[Item], notify: Notifier = macos_notify) -> list[int]:
    """At-least-once delivery: only an item whose push succeeded is returned (and marked)."""
    sent = []
    for i in items:
        when = "Reminder" if i.kind == "reminder" else f"Due {(i.due_at or '')[11:16]}".strip()
        if notify("Ouroboros", when, i.title):
            sent.append(i.id)
    return sent


def _dialogue_sync(cfg: Config, only: set[str]) -> int:
    from ops.lifecycle.launcher import build_launcher  # lazy: duckdb and the scheduler behind it

    return int(build_launcher(cfg).dialogue_sync_now(only=only))


def tick(cfg: Config, *, policy: Policy | None = None, run: Runner = _run,
         latest: Callable[[], dict[str, int | None]] = sources_latest,
         notify: Notifier = macos_notify,
         sync: Callable[[set[str]], int] | None = None) -> int:
    """One beat: sense, decide, act, record. Exit 1 when an action failed, so launchd's last exit
    status tells the truth."""
    policy = policy or load_policy()
    data = cfg.paths.data_dir
    data.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    with open(data / LOCK_FILE, "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)   # single-instance lock
        except BlockingIOError:
            print("tick: the previous beat is still running")
            return 0
        at = now_local().isoformat(timespec="seconds")
        until = paused_until(data)
        if until:   # the kill switch: nothing is read, nothing is done
            _atomic_write(data / TICK_FILE, {"at": at, "took_s": 0.0, "paused_until": until,
                                             "decisions": []})
            print(f"tick {at[11:16]} · paused until {until}")
            return 0
        store = open_task_store(cfg)
        try:
            ended = store.reconcile_jobs(pid_alive)
            s = sense(cfg, store, policy, run=run, latest=latest)
            decisions = decide(s, policy)
            do_sync = sync or partial(_dialogue_sync, cfg)
            pushed: list[int] = []
            attempted = 0
            sync_rc: int | None = None
            for d in decisions:
                if d.go and d.action == "notify":
                    batch = s.to_notify[:PUSH_PER_TICK]
                    attempted, pushed = len(batch), push(batch, notify)
                    store.mark_notified(pushed)
                elif d.go and d.action == "sync-dialogue":
                    only = {src for src, changed in s.pending.items() if changed}
                    sync_rc = run_as_job(SYNC_JOB, partial(do_sync, only),
                                         created_by="heartbeat", store=store)
            extra = ([f"disk nearly full: {s.free_gb:.0f} GB free"]
                     if s.free_gb < policy.min_free_gb else [])
            notices = write_notices(store, extra=extra)
        except Exception as e:
            _atomic_write(data / TICK_FILE, {"at": at, "took_s": round(time.monotonic() - t0, 3),
                                             "error": f"{type(e).__name__}: {e}"[:300],
                                             "decisions": []})
            raise
        finally:
            store.close()
        failed_push = attempted - len(pushed)
        record = {
            "at": at, "took_s": round(time.monotonic() - t0, 3),
            "sensed": {**{k: v for k, v in asdict(s).items() if k != "to_notify"},
                       "due": [f"#{i.id} {i.title}" for i in s.to_notify]},
            "decisions": [asdict(d) for d in decisions],
            "ended_jobs": [j.id for j in ended], "pushed": pushed, "push_failed": failed_push,
            "sync_rc": sync_rc, "notices": len(notices),
        }
        _atomic_write(data / TICK_FILE, record)
        print(f"tick {at[11:16]} {record['took_s']}s · " + " · ".join(
            f"{d.action}: {'go' if d.go else 'no'} ({d.reason})" for d in decisions))
        return 0 if sync_rc in (None, 0) and not failed_push else 1


def last_tick(data_dir: Path, *, interval_s: int = 900,
              now: datetime | None = None) -> dict[str, Any] | None:
    """The latest beat, condensed for the status tool; `stale` is the watchdog's verdict."""
    try:
        rec = json.loads((data_dir / TICK_FILE).read_text(encoding="utf-8"))
        at = datetime.fromisoformat(rec["at"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    out: dict[str, Any] = {
        "at": rec["at"][:16],
        "stale": ((now or now_local()) - at).total_seconds() > 2 * interval_s,
    }
    for key in ("paused_until", "error"):
        if rec.get(key):
            out[key] = rec[key]
    out["decided"] = [f"{d['action']}: {'yes' if d['go'] else 'no'}, {d['reason']}"
                      for d in rec.get("decisions", [])]
    return out


def main(argv: Sequence[str]) -> int:
    """`palace tick` runs one beat; `tick pause 2h [reason]`, `tick resume`, `tick status`."""
    from core.kernel.config import get_config

    cfg = get_config()
    data = cfg.paths.data_dir
    verb = argv[0] if argv else ""
    if verb == "pause":
        if len(argv) < 2:
            print("usage: palace tick pause <30m|2h|1d|2026-10-30T09:00> [reason]")
            return 2
        try:
            until = pause(data, argv[1], reason=" ".join(argv[2:]))
        except ValueError as e:
            print(f"tick pause: {e}")
            return 2
        print(f"heartbeat paused until {until} (`palace tick resume` lifts it sooner)")
        return 0
    if verb == "resume":
        print("heartbeat resumed" if resume(data) else "heartbeat was not paused")
        return 0
    if verb == "status":
        print(json.dumps(last_tick(data, interval_s=load_policy().interval_s), indent=1))
        return 0
    if verb:
        print("usage: palace tick [pause <duration> [reason] | resume | status]")
        return 2
    return tick(cfg)
