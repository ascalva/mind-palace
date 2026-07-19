"""Wiring + instruments for the integrator (bp-071 Item 2).

The integrator is wired as a pinned, model-less trough job (like `chat_events`/`chat_sync`): it
plans onto the pinned tier, the daemon runs it on the housekeeping tick, and it ships two
instruments — the C-coverage gauge (honest partial coverage) and the resolution-parity gauge
(every L1 ref accounted, never silently dropped). Proves the daemon path, gauges, and pinned tier.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

from config.loader import load_config
from core.chat_events import ChatEvent
from core.integrator import Integrator, coverage_gauge
from core.stores.causal_edges import CausalEdgeStore
from core.stores.chat_events import ChatEventStore
from ops.code_snapshot import open_snapshot_db
from scheduler.cron import INTEGRATE_KIND, enqueue_integrate, integrate_handler
from scheduler.queue import Job, JobQueue
from scheduler.router import Router

FULL_SHA = "abc1234def5678901234567890abcdef01234567"


def _seeded_integrator() -> Integrator:
    """A D+C fixture: one resolvable commit, one direct doc write, one unresolvable commit."""
    events = ChatEventStore(Path(":memory:"))
    events.replace_session("sess-a", [
        ChatEvent("sess-a", 0, "agent", "commit", "abc1234", 0),
        ChatEvent("sess-a", 1, "agent", "build_plan", "bp-071", 1),
        ChatEvent("sess-a", 2, "agent", "commit", "deadbee", 2),
        ChatEvent("sess-a", 3, "owner", "prompt", "3", 3),
    ], "digest-a")
    ledger = open_snapshot_db(Path(":memory:"))
    ledger.execute("INSERT INTO snapshots (commit_sha, committed_at, taken_at, files, loc, "
                   "functions, classes) VALUES (?, ?, ?, 0, 0, 0, 0)",
                   [FULL_SHA, "2026-07-19T00:00:00", "2026-07-19T00:00:00"])
    ledger.commit()
    return Integrator(events=events, ledger=ledger, edges=CausalEdgeStore(Path(":memory:")))


# --- pinned tier -----------------------------------------------------------------------------
def test_integrate_plans_onto_the_pinned_tier() -> None:
    """Model-less file work → the pinned tier (ensure_tier is a no-op; never evicts a slot)."""
    cfg = load_config()
    assert Router(cfg).plan(INTEGRATE_KIND).tier == cfg.pinned_model.tier


def test_integrate_is_pinned_and_background(tmp_path: Path) -> None:
    """The daemon enqueue path: the job lands on the pinned tier at background priority."""
    cfg = load_config()
    queue = JobQueue(tmp_path / "queue.sqlite")
    job = enqueue_integrate(queue, Router(cfg))
    assert job.tier == cfg.pinned_model.tier


# --- the daemon handler ----------------------------------------------------------------------
def test_handler_runs_integrate_and_summarizes() -> None:
    integ = _seeded_integrator()
    handler = integrate_handler(integ, max_per_pass=50)
    # The handler ignores its Job arg (see scheduler/cron.py) — a bare placeholder, cast per the
    # test_cron precedent ("this never matters here").
    result = handler(cast(Job, SimpleNamespace()))

    assert result is not None
    assert "integrate: 1 session(s)" in result and "unknown-sha" in result
    # one resolved commit edge + one direct doc edge = 2 edges landed
    assert integ.edges.count() == 2


# --- the instruments -------------------------------------------------------------------------
def test_coverage_gauge_computes_over_a_seeded_fixture() -> None:
    """C-coverage: 3 integrable D-events (2 commit + 1 write), 2 witnessed → coverage 2/3."""
    integ = _seeded_integrator()
    integ.integrate(max_sessions=50)
    gauge = coverage_gauge(integ.events, integ.edges)
    assert gauge.integrable == 3 and gauge.witnessed == 2
    assert gauge.unwitnessed == 1
    assert abs(gauge.coverage - 2 / 3) < 1e-9


def test_parity_gauge_accounts_every_l1_ref() -> None:
    """Resolution parity: every integrable ref is resolved or NAMED unresolvable — no drop."""
    integ = _seeded_integrator()
    report = integ.integrate(max_sessions=50)
    assert report.is_fully_accounted()
    assert report.commit_events == 2 and report.commit_resolved == 1
    assert report.unresolved == {"unknown-sha": 1}
    assert report.write_events == 1 and report.non_integrable == 1
