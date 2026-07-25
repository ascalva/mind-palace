"""bp-102 Item 2 — the acceptance ORACLE: replay 2026-07-25 and demand every row read anomalous.

The plan's §6 table is the contract. It lists, for the 90-minute incident the owner watched
`status` fail to describe, what the command SHOWED against what was TRUE:

| shown then              | true then                                    |
|-------------------------|----------------------------------------------|
| `queue depth: 1714`     | growing ~2/min, **zero drain**               |
| `code_backfill running` | 74 of 75 min of budget spent                 |
| `lifetime: 300,239 done`| unchanged for an hour ⇒ **zero throughput**  |
| (absent)                | 1 job failed 15 min earlier                  |
| `running HEAD`          | **the process was dead**                     |

So the fixture below is not a synthetic scenario — it is that state, reconstructed in a temporary
`queue.sqlite` written against the real `jobs` schema (`scheduler/queue.py:62+`), and each test
asserts the corresponding row now renders with a visibly anomalous reading.

One row is answered differently from the plan's wording, deliberately: "74 of 75 min of budget"
does not exist, because **no job-level timeout exists anywhere in the system** (bp-102 Q4 →
finding-0174 — the observed `TimeoutError` was the `[ollama] request_timeout_s` socket timeout on
one embed call). Status therefore reports the elapsed and says plainly that there is no enforced
budget, rather than inventing a denominator.
"""

import dataclasses
import os
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from config.loader import load_config
from ops.lifecycle.launcher import Launcher
from ops.lifecycle.preflight import Check, Preflight
from ops.lifecycle.runs import RunLedger
from ops.lifecycle.snapshot import read_queue_stats

# The incident clock (UTC, as the queue records it) — 03:45:07 on 2026-07-25, the moment the
# owner sampled `status` and it reported nothing wrong. The fixture is generated RELATIVE to an
# anchor so the same rows can be replayed against a fixed clock (the unit assertions) or against
# the wall clock (the end-to-end `status` render, which reads `datetime.now`).
NOW = datetime(2026, 7, 25, 3, 45, 7)
DEAD_PID = 2 ** 22          # far above the pid ceiling → ProcessLookupError → not alive


def _at(anchor: datetime, **delta) -> str:
    return (anchor - timedelta(**delta)).isoformat(timespec="seconds")

_DDL = """
CREATE TABLE IF NOT EXISTS jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,
    tier        TEXT NOT NULL,
    num_ctx     INTEGER NOT NULL,
    priority    INTEGER NOT NULL,
    state       TEXT NOT NULL,
    payload     TEXT,
    result      TEXT,
    error       TEXT,
    attempts    INTEGER NOT NULL DEFAULT 0,
    checkpoint  TEXT,
    created_at  TEXT NOT NULL,
    started_at  TEXT,
    finished_at TEXT
);
"""


def _mkqueue(path: Path, rows) -> None:
    """Write a `jobs` table directly. We do NOT drive `JobQueue` here: its `enqueue`/`claim` stamp
    `created_at`/`finished_at` from the wall clock, and this fixture must pin them to the incident
    timeline. `scheduler/queue.py` is read-only for bp-102 (bp-101 owns it)."""
    conn = sqlite3.connect(path)
    conn.executescript(_DDL)
    conn.executemany(
        "INSERT INTO jobs (id, kind, tier, num_ctx, priority, state, error, created_at, "
        "started_at, finished_at) VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()


def incident_rows(anchor: datetime = NOW):
    """Run #35's state as of `anchor` (03:45:07 UTC), compressed to the shape the queries see.

    * 1,714 queued (883 `chat_sync` + 831 `vault_sync`) — the finding-0170 duplicate storm. Most
      were enqueued when the wedge began (02:30, outside the window); 40 land INSIDE the last
      20 minutes, giving the finding's measured **~2/min** in-rate against a zero out-rate;
    * a lifetime `done` mass, ALL of it finished long before the window (zero throughput — this
      is the `300,239 done` counter that had not moved in an hour);
    * `code_backfill` #300240 FAILED at 03:45:02, five seconds before the sample;
    * `code_sync` #300246 RUNNING since 02:30:12 — 74m55s elapsed.

    The 300,239 lifetime dones are represented by 40 rows: the windowed counts are what the rate
    block reads, and materializing 300k rows would make this test slower than the command it
    guards. `test_status_cost_bound.py` proves the cost does not grow with the table, which is
    the property that number was standing in for.
    """
    rows: list[tuple[object, ...]] = []
    jid = 1
    old = _at(anchor, hours=2)
    for _ in range(40):                     # the "lifetime done" mass — all OUTSIDE the window
        rows.append((jid, "vault_sync", "router", 8192, 100, "done", None, old, old, old))
        jid += 1
    # the backlog as it stood when the worker wedged (02:30) — outside the 20-minute window …
    for _ in range(863):
        rows.append((jid, "chat_sync", "router", 8192, 100, "queued", None,
                     _at(anchor, minutes=75), None, None))
        jid += 1
    for _ in range(811):
        rows.append((jid, "vault_sync", "router", 8192, 100, "queued", None,
                     _at(anchor, minutes=74), None, None))
        jid += 1
    # … and the 40 that arrived DURING the window: 2/min in, 0/min completed out.
    for i in range(20):
        rows.append((jid, "chat_sync", "router", 8192, 100, "queued", None,
                     _at(anchor, minutes=i, seconds=30), None, None))
        jid += 1
        rows.append((jid, "vault_sync", "router", 8192, 100, "queued", None,
                     _at(anchor, minutes=i, seconds=40), None, None))
        jid += 1
    rows.append((300240, "code_backfill", "router", 8192, 100, "failed",
                 "TimeoutError('timed out')", _at(anchor, minutes=75),
                 _at(anchor, minutes=74, seconds=55), _at(anchor, seconds=5)))
    rows.append((300246, "code_sync", "router", 8192, 100, "running", None,
                 _at(anchor, minutes=75), _at(anchor, minutes=74, seconds=55), None))
    return rows


@pytest.fixture
def incident_queue(tmp_path):
    p = tmp_path / "queue.sqlite"
    _mkqueue(p, incident_rows())
    return p


@pytest.fixture
def stats(incident_queue):
    return read_queue_stats(incident_queue, now=NOW)


# --- the §6 rows, one test each --------------------------------------------------------------
def test_row1_depth_is_reported_with_its_derivative_and_zero_drain(stats):
    """`queue depth: 1714` → depth AND d(depth)/dt, with ZERO DRAIN as a computed predicate."""
    assert stats.depth == 1714
    assert stats.in_rate_per_min == pytest.approx(2.0)    # the finding's measured ~2/min
    assert stats.out_rate_per_min == pytest.approx(0.05)  # the ONE failure leaving; nothing else
    assert stats.net_rate_per_min > 1.9                   # the backlog is GROWING
    # The predicate is keyed on COMPLETIONS, not on terminal transitions. At this exact instant a
    # job had failed five seconds earlier; had `stalled` counted that as drain it would have gone
    # quiet at precisely the moment the owner sampled the system.
    assert stats.done_in_window == 0
    assert stats.stalled is True


def test_row2_running_job_shows_elapsed_and_says_there_is_no_budget(stats):
    """`code_backfill running` → the RUNNING job with its elapsed. No budget fraction is claimed:
    Q4 established there is no job-level timeout to divide by (finding-0174)."""
    assert len(stats.running) == 1
    job = stats.running[0]
    assert job.id == 300246 and job.kind == "code_sync"
    assert job.elapsed_s is not None and job.elapsed_s > 74 * 60      # 74m55s
    assert stats.wedged is True         # running, yet nothing terminated all window


def test_row3_zero_throughput_is_visible_not_inferred(stats):
    """`lifetime: 300,239 done` (unchanged for an hour) → the WINDOWED counts are what is shown,
    and they are zero. The level alone was the thing that read as fine."""
    assert stats.done_in_window == 0
    assert stats.lifetime["done"] == 40             # the level still available, no longer alone
    assert stats.failed_in_window == 1


def test_row4_the_failure_fifteen_minutes_ago_is_surfaced(stats):
    """(absent) → the failure `status` showed six green checkmarks over."""
    f = stats.last_failure
    assert f is not None
    assert f.id == 300240 and f.kind == "code_backfill"
    assert "TimeoutError" in f.error
    assert f.age_s is not None and f.age_s < 20 * 60
    assert stats.failure_in_window is True


def test_per_kind_oldest_age_is_reported(stats):
    """The plan's per-kind oldest age — which kind is starving, and for how long."""
    kinds = {k.kind: k for k in stats.queued_by_kind}
    assert kinds["chat_sync"].count == 883
    assert kinds["vault_sync"].count == 831
    assert kinds["chat_sync"].oldest_age_s is not None
    assert kinds["chat_sync"].oldest_age_s > kinds["vault_sync"].oldest_age_s


# --- row 5 + the whole rendered block ---------------------------------------------------------
def _cfg(tmp_path):
    """Every corpus/derived/ledger path into tmp so the snapshot's read-only views are hermetic."""
    base = load_config()
    paths = dataclasses.replace(
        base.paths, data_dir=tmp_path, raw_store=tmp_path / "raw",
        vector_store=tmp_path / "v.lance", vault_catalog=tmp_path / "cat.sqlite",
        derived_store=tmp_path / "d.sqlite", attestation_store=tmp_path / "att.sqlite",
        telemetry_db=tmp_path / "t.duckdb")
    selfmod = dataclasses.replace(base.selfmod, ledger_db=tmp_path / "selfmod.sqlite")
    vault = dataclasses.replace(base.vault, path=tmp_path / "vault")
    return dataclasses.replace(base, paths=paths, selfmod=selfmod, vault=vault)


def _launcher(tmp_path, runs, *, head, monkeypatch):
    monkeypatch.setattr("ops.lifecycle.launcher.git_state", lambda _r: (head, False))
    passing = Preflight((Check("x", required=True, ok=True, detail="ok"),))
    return Launcher(cfg=_cfg(tmp_path), runs=runs, repo_root=Path(".").resolve(),
                    preflight_fn=lambda _c: passing)


def _status_out(tmp_path, monkeypatch, capsys, *, pid, incident=True):
    if incident:
        # `status` reads the WALL clock, so the incident is replayed against it: same relative
        # timeline, anchored now. This is the honest end-to-end check — no clock is stubbed.
        now = datetime.now(UTC).replace(tzinfo=None)
        _mkqueue(tmp_path / "queue.sqlite", incident_rows(now))
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="5c2222924874", dirty=False, pid=pid)
    launcher = _launcher(tmp_path, runs, head="5c2222924874", monkeypatch=monkeypatch)
    # the embedder probe is the one line that would reach Ollama; pin it so the test is hermetic.
    monkeypatch.setattr(Launcher, "_embedder_state", lambda _s, _ok: "qwen3-embedding:4b resident")
    assert launcher.status() == 0
    return capsys.readouterr().out


def test_row5_a_dead_pid_never_renders_as_running_head(tmp_path, monkeypatch, capsys):
    """`running HEAD` over a dead process — the false green itself. The run row is ledger-active
    and its commit IS HEAD, so the ONLY thing standing between the old code and a green banner
    was the liveness test."""
    out = _status_out(tmp_path, monkeypatch, capsys, pid=DEAD_PID)
    assert "DEAD (stale ledger row)" in out
    assert "running HEAD" not in out
    assert "is NOT alive" in out and "the daemon is DOWN" in out


def test_the_whole_incident_block_renders_every_anomaly(tmp_path, monkeypatch, capsys):
    """The end-to-end oracle: one `status` over the incident state must show all five rows."""
    out = _status_out(tmp_path, monkeypatch, capsys, pid=DEAD_PID)
    assert "queue depth: 1714" in out
    assert "ZERO DRAIN" in out                                  # row 1
    assert "net +" in out                                       # row 1: the derivative, signed
    assert "running: #300246 code_sync" in out                  # row 2
    assert "no enforced job budget" in out                      # row 2 (Q4 honesty)
    assert "throughput: 0 done, 1 failed in the last 20 min" in out   # row 3
    assert "last failure: #300240 code_backfill" in out         # row 4
    assert "TimeoutError" in out
    assert "DEAD (stale ledger row)" in out                     # row 5
    assert "waiting: chat_sync 883" in out                      # per-kind oldest age
    # the row 5 consequence, one level down: a RUNNING job with no live worker is an ORPHAN
    # (finding-0173), not work in progress — its growing "elapsed" would otherwise read as fine.
    assert "ORPHANED" in out


def test_a_running_row_under_a_LIVE_daemon_is_not_called_orphaned(tmp_path, monkeypatch, capsys):
    """The false-alarm guard for the orphan flag: with the daemon genuinely alive, the same
    running row is a long job, not an orphan, and must be flagged as such and no worse."""
    out = _status_out(tmp_path, monkeypatch, capsys, pid=os.getpid())
    assert "ORPHANED" not in out
    assert "running while NOTHING completed this window" in out


def test_a_healthy_system_raises_no_flags(tmp_path, monkeypatch, capsys):
    """The false-alarm guard for Item 2: an idle, drained queue must read CLEAN. An instrument
    that flags a healthy system will be ignored during the next incident."""
    now = datetime.now(UTC).replace(tzinfo=None)
    rows = [(1, "vault_sync", "router", 8192, 100, "done", None,
             _at(now, minutes=1), _at(now, seconds=50), _at(now, seconds=40))]
    _mkqueue(tmp_path / "queue.sqlite", rows)
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="abc123456789", dirty=False, pid=os.getpid())   # a LIVE pid
    launcher = _launcher(tmp_path, runs, head="abc123456789", monkeypatch=monkeypatch)
    monkeypatch.setattr(Launcher, "_embedder_state", lambda _s, _ok: "qwen3-embedding:4b resident")
    assert launcher.status() == 0
    out = capsys.readouterr().out
    assert "running HEAD" in out
    assert "⚠" not in out                       # no flag of any kind on a healthy system
    assert "running: (none)" in out
