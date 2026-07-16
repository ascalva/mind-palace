"""The harness cost ledger (bp-044 Item 10) — an ADDITIVE telemetry table.

Falsifier (plan §7 Item 10): an existing telemetry read/write breaks (the DDL change was not
additive), OR the cost appendix reports a cell count contradicting the store's `cells_completed`.
The additive-DDL proof also lives in `tests/integration/test_telemetry.py` — those tests stay green
UNMODIFIED (asserted here by re-exercising the vitals path against a v3 store).
"""

from __future__ import annotations

from core.stores.telemetry import SCHEMA_VERSION, TelemetryReader, TelemetryStore, TelemetryWriter


def test_schema_version_is_three_and_migration_row_written(tmp_path) -> None:
    store = TelemetryStore(tmp_path / "t.duckdb")
    try:
        assert SCHEMA_VERSION == 3
        row = store._conn.execute(
            "SELECT count(*) FROM schema_migrations WHERE version = 3").fetchone()
        assert row is not None and row[0] == 1                  # the v3 migration row is recorded
    finally:
        store.close()


def test_record_harness_cost_round_trips(tmp_path) -> None:
    store = TelemetryStore(tmp_path / "t.duckdb")
    try:
        store.writer().record_harness_cost("run-1", wall_clock_s=12.5, models_resident=2,
                                           cells_completed=40, cells_skipped=3, note="nightly")
        rows = store.reader().harness_costs()
        assert len(rows) == 1
        r = rows[0]
        assert r["run_id"] == "run-1"
        assert r["wall_clock_s"] == 12.5
        assert r["models_resident"] == 2
        assert r["cells_completed"] == 40
        assert r["cells_skipped"] == 3
        assert r["note"] == "nightly"
        assert store.reader().harness_cost_count() == 1
    finally:
        store.close()


def test_harness_costs_filter_by_run_id_and_are_ordered(tmp_path) -> None:
    store = TelemetryStore(tmp_path / "t.duckdb")
    try:
        w = store.writer()
        w.record_harness_cost("run-a", wall_clock_s=1.0, models_resident=1,
                              cells_completed=1, cells_skipped=0)
        w.record_harness_cost("run-b", wall_clock_s=2.0, models_resident=1,
                              cells_completed=2, cells_skipped=0)
        assert len(store.reader().harness_costs("run-a")) == 1
        assert store.reader().harness_costs("run-a")[0]["run_id"] == "run-a"
        assert len(store.reader().harness_costs()) == 2
    finally:
        store.close()


def test_additive_ddl_leaves_vitals_and_context_usage_intact(tmp_path) -> None:
    """The additive-DDL falsifier: adding `harness_cost` at v3 must not disturb the existing tables
    — the pre-existing vitals + context_usage read/write paths still behave exactly as before."""
    store = TelemetryStore(tmp_path / "t.duckdb")
    try:
        w = store.writer()
        w.record_vital("mem.available_gb", 11.0, unit="GB", source="test")
        r = store.reader()
        assert r.count("mem.available_gb") == 1
        assert r.latest("mem.available_gb") == 11.0
        assert r.context_usage_count() == 0                    # untouched, still queryable
        # scoped access is still structural (the write-only / read-only split is unchanged)
        assert not hasattr(TelemetryWriter, "latest")
        assert not hasattr(TelemetryReader, "record_vital")
        assert not hasattr(TelemetryReader, "record_harness_cost")
        assert not hasattr(TelemetryWriter, "harness_costs")
    finally:
        store.close()
