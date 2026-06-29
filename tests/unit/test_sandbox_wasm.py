"""The WASM substrate + the routing runner (BUILD-SPEC §11 / roadmap E2).

WASM execution needs an owner-placed WASI python (`python.wasm`); these assert the structure
around it: `available()` is fail-closed without the artifact, and the RoutingRunner falls back
to the verified Podman substrate when WASM isn't available (the live default) — never a silent
wrong-substrate run.
"""

import pytest

from core.sandbox import (
    ExecSpec,
    PodmanRunner,
    RoutingRunner,
    WasmRunner,
    WasmUnavailableError,
    build_runner,
)
from core.sandbox.spec import Network


def test_wasm_unavailable_without_a_module():
    assert WasmRunner().available() is False                    # no module configured
    assert WasmRunner(wasm_module="/no/such/python.wasm").available() is False
    with pytest.raises(WasmUnavailableError):
        WasmRunner().run_once(ExecSpec(code="print(1)"), policy=None)


def test_build_runner_constructs_each_substrate():
    assert isinstance(build_runner("podman"), PodmanRunner)
    assert isinstance(build_runner("wasm"), WasmRunner)
    assert isinstance(build_runner("routing"), RoutingRunner)
    with pytest.raises(ValueError):
        build_runner("nonsense")


class _FakeWasm:
    def __init__(self, available):
        self._a = available
        self.ran = False

    def available(self):
        return self._a

    def run_once(self, spec, policy):
        self.ran = True
        return "WASM"


class _FakePodman:
    def __init__(self):
        self.ran = False

    def available(self):
        return True

    def run_once(self, spec, policy):
        self.ran = True
        return "PODMAN"


def test_routing_prefers_wasm_for_pure_compute_python_when_available():
    wasm, pod = _FakeWasm(available=True), _FakePodman()
    r = RoutingRunner(wasm=wasm, podman=pod)
    assert r.run_once(ExecSpec(code="print(1)"), policy=None) == "WASM"   # python + no-net → wasm
    assert wasm.ran and not pod.ran


def test_routing_falls_back_to_podman_when_wasm_unavailable():
    wasm, pod = _FakeWasm(available=False), _FakePodman()
    r = RoutingRunner(wasm=wasm, podman=pod)
    assert r.run_once(ExecSpec(code="print(1)"), policy=None) == "PODMAN"  # the live default
    assert pod.ran and not wasm.ran


def test_routing_uses_podman_for_non_python_even_if_wasm_is_up():
    wasm, pod = _FakeWasm(available=True), _FakePodman()
    r = RoutingRunner(wasm=wasm, podman=pod)
    assert r.run_once(ExecSpec(code="echo hi", language="bash"), policy=None) == "PODMAN"
    # and warm-pool ops always go to podman (wasm has no persistent containers)
    assert r._pick(ExecSpec(code="x", network=Network.NONE, language="bash")) is pod
