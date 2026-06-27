"""System vitals flow into DuckDB (Phase 0 gate: 'vitals flow')."""

from core.stores.telemetry import TelemetryStore
from core.vitals import VitalsCollector, collect_system_vitals


def test_collect_returns_core_metrics():
    metrics = {r.metric for r in collect_system_vitals()}
    assert "mem.available_gb" in metrics
    assert "cpu.percent" in metrics


def test_vitals_flow_into_duckdb(tmp_path):
    store = TelemetryStore(tmp_path / "v.duckdb")
    try:
        readings = VitalsCollector(store.writer()).collect_once()
        assert readings
        r = store.reader()
        assert r.count() >= len(readings)
        assert r.latest("mem.available_gb") is not None
    finally:
        store.close()
