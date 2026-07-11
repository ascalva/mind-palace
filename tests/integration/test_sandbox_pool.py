"""Warm pool (BUILD-SPEC §11, §5): lazy warming, reuse, concurrency cap, discard-on-unhealthy.
Deterministic via a fake runner — no Podman needed."""

import pytest

from core.sandbox import Limits, SandboxBusyError, SandboxPolicy, WarmPool
from tests.fixtures.sandbox import FakeRunner


def _pool(runner, size=1):
    return WarmPool(runner=runner, policy=SandboxPolicy(), limits=Limits(), size=size)


def test_warms_lazily_then_reuses():
    r = FakeRunner()
    pool = _pool(r, size=2)
    a = pool.acquire()
    assert a == "c1" and r.started == ["c1"]
    pool.release(a)
    assert r.reset_calls == ["c1"]          # cleared, kept warm
    b = pool.acquire()
    assert b == "c1" and r.started == ["c1"]  # reused, not re-warmed


def test_caps_concurrency_at_size():
    r = FakeRunner()
    pool = _pool(r, size=1)
    pool.acquire()
    with pytest.raises(SandboxBusyError):
        pool.acquire()


def test_unhealthy_container_is_discarded_not_reused():
    r = FakeRunner()
    pool = _pool(r, size=1)
    a = pool.acquire()
    pool.release(a, healthy=False)
    assert r.destroyed == ["c1"] and r.reset_calls == []
    assert pool.acquire() == "c2"           # a fresh one is warmed


def test_prewarm_and_shutdown():
    r = FakeRunner()
    pool = _pool(r, size=2)
    pool.prewarm()
    assert pool.stats()["free"] == 2
    pool.shutdown()
    assert set(r.destroyed) == {"c1", "c2"}
    assert pool.stats() == {"free": 0, "in_use": 0, "size": 2}
