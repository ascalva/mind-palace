"""Execution broker (BUILD-SPEC §11, Invariant 4): pool routing, timeout-discards-container,
concurrency cap, and per-execution logging. Deterministic via a fake runner."""

import pytest

from core.sandbox import (
    ExecResult,
    ExecSpec,
    ExecutionBroker,
    Limits,
    SandboxBusyError,
    SandboxPolicy,
    WarmPool,
)
from tests.fixtures.sandbox import FakeRunner


def _broker(runner, *, pool=None, telemetry=None, max_concurrency=1):
    return ExecutionBroker(runner=runner, policy=SandboxPolicy(), pool=pool,
                           telemetry=telemetry, max_concurrency=max_concurrency)


def test_runs_ephemeral_when_no_pool():
    r = FakeRunner(result=ExecResult("hi", "", 0))
    res = _broker(r).run(ExecSpec(code="print('hi')"))
    assert res.ok and res.stdout == "hi" and r.started == []  # no warm container created


def test_uses_pool_for_matching_language():
    r = FakeRunner(result=ExecResult("p", "", 0))
    pool = WarmPool(runner=r, policy=SandboxPolicy(), limits=Limits(), size=1, language="python")
    res = _broker(r, pool=pool).run(ExecSpec(code="x"))
    assert res.stdout == "p"
    assert r.started == ["c1"] and r.reset_calls == ["c1"]  # acquired + released healthy


def test_timeout_result_discards_the_container():
    r = FakeRunner(result=ExecResult("", "wall-clock timeout", -1, timed_out=True))
    pool = WarmPool(runner=r, policy=SandboxPolicy(), limits=Limits(), size=1, language="python")
    res = _broker(r, pool=pool).run(ExecSpec(code="while True: pass"))
    assert res.timed_out
    assert r.destroyed == ["c1"] and r.reset_calls == []   # wedged container not reused


def test_concurrency_cap_blocks_reentrant_run():
    holder: dict[str, ExecutionBroker] = {}

    class Reentrant(FakeRunner):
        def run_once(self, spec, policy):
            return holder["b"].run(ExecSpec(code="y"))   # a second job arrives mid-execution

    b = _broker(Reentrant(), max_concurrency=1)
    holder["b"] = b
    with pytest.raises(SandboxBusyError):
        b.run(ExecSpec(code="x"))


def test_logs_each_execution_to_telemetry(tmp_path):
    from core.stores.telemetry import TelemetryStore

    store = TelemetryStore(tmp_path / "t.duckdb")
    try:
        b = _broker(FakeRunner(), telemetry=store.writer())
        b.run(ExecSpec(code="x"))
        assert store.reader().count("sandbox.exec") == 1
    finally:
        store.close()


def test_build_broker_wires_from_config():
    from core.sandbox import PodmanRunner, build_broker

    b = build_broker()
    assert isinstance(b.runner, PodmanRunner)        # configured runtime = podman
    assert b.max_concurrency == 1                     # from [sandbox] config
    assert b.pool is not None and b.pool.size == 1    # warm pool sized from config
