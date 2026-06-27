"""DuckDB telemetry store: vitals round-trip and scoped (write-only / read-only) access."""

from core.stores.telemetry import TelemetryReader, TelemetryStore, TelemetryWriter


def test_writer_records_reader_reads(tmp_path):
    store = TelemetryStore(tmp_path / "t.duckdb")
    try:
        store.writer().record_vital("mem.available_gb", 12.5, unit="GB", source="test")
        r = store.reader()
        assert r.count("mem.available_gb") == 1
        assert r.latest("mem.available_gb") == 12.5
    finally:
        store.close()


def test_scoped_access_is_structural():
    # Scoped access enforced in code (CONVENTIONS): the wrong access is impossible.
    assert not hasattr(TelemetryWriter, "latest")
    assert not hasattr(TelemetryWriter, "window")
    assert not hasattr(TelemetryReader, "record_vital")


def test_window_filters_by_metric(tmp_path):
    store = TelemetryStore(tmp_path / "w.duckdb")
    try:
        w = store.writer()
        w.record_vital("cpu.percent", 1.0)
        w.record_vital("cpu.percent", 2.0)
        w.record_vital("mem.used_pct", 9.0)
        rows = store.reader().window("cpu.percent", seconds=3600)
        assert [v for _, v in rows] == [1.0, 2.0]
    finally:
        store.close()
