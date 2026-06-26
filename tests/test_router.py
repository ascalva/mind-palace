"""Rules-first router + watchdog (BUILD-SPEC §9, §13; roadmap §8)."""

from config.loader import load_config
from core.stores.telemetry import TelemetryStore
from scheduler.queue import (
    PRIORITY_BACKGROUND,
    PRIORITY_INTERACTIVE,
    PRIORITY_REACTIVE,
)
from scheduler.router import Router, Watchdog


def test_router_maps_kinds_to_tiers():
    r = Router(load_config())
    assert r.tier_for("librarian") == "routine"
    assert r.tier_for("dream") == "synthesis"
    assert r.tier_for("route") == "router"          # the pinned tier
    assert r.tier_for("unrecognized") == "routine"  # safe default


def test_router_plan_sets_window_and_priority():
    cfg = load_config()
    r = Router(cfg)
    p = r.plan("librarian")
    assert p.tier == "routine" and p.num_ctx == cfg.model_for_tier("routine").num_ctx
    assert p.priority == PRIORITY_INTERACTIVE
    assert r.plan("dream").priority == PRIORITY_BACKGROUND
    assert r.plan("route").priority == PRIORITY_REACTIVE
    assert r.plan("librarian", priority=PRIORITY_REACTIVE).priority == PRIORITY_REACTIVE


def test_watchdog_flags_low_memory(tmp_path):
    store = TelemetryStore(tmp_path / "t.duckdb")
    try:
        store.writer().record_vital("mem.available_gb", 1.0, unit="GB")
        flags = Watchdog(store.reader(), min_available_gb=2.0).check()
        assert len(flags) == 1 and flags[0].metric == "mem.available_gb"
    finally:
        store.close()


def test_watchdog_quiet_when_healthy(tmp_path):
    store = TelemetryStore(tmp_path / "t2.duckdb")
    try:
        store.writer().record_vital("mem.available_gb", 12.0, unit="GB")
        assert Watchdog(store.reader(), min_available_gb=2.0).check() == []
    finally:
        store.close()
