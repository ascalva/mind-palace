"""Tools as object-capability handles (BUILD-SPEC §10, §11; skills-and-scope).

Out-of-scope is *unreachable* (the dispatcher has no handle), not "checked then refused".
"""

import pytest

from core.factory.tools import (
    ToolNotInScopeError,
    ToolRegistry,
    ToolSpec,
    build_default_registry,
    dispatcher_for,
)
from core.sandbox.spec import ExecResult


def _echo_tool() -> ToolSpec:
    return ToolSpec("echo", "echo back", lambda args: {"echo": args.get("v")})


def test_registry_register_get_contains():
    reg = ToolRegistry()
    reg.register(_echo_tool())
    assert "echo" in reg and reg.get("echo").id == "echo" and reg.ids() == frozenset({"echo"})


def test_dispatcher_holds_only_in_scope_handles_and_runs_them():
    reg = ToolRegistry()
    reg.register(_echo_tool())
    d = dispatcher_for(frozenset({"echo"}), reg)
    assert d.can_invoke("echo")
    assert d.invoke("echo", {"v": 7}).data == {"echo": 7}


def test_out_of_scope_tool_is_unreachable():
    reg = ToolRegistry()
    reg.register(_echo_tool())
    d = dispatcher_for(frozenset(), reg)            # empty scope
    assert not d.can_invoke("echo")
    with pytest.raises(ToolNotInScopeError):
        d.invoke("echo", {})


def test_dispatcher_skips_tools_absent_from_registry():
    d = dispatcher_for(frozenset({"missing"}), ToolRegistry())
    assert d.scope == frozenset()


class _FakeBroker:
    def __init__(self):
        self.calls = []

    def run(self, spec):
        self.calls.append(spec)
        return ExecResult("hi", "", 0)


def test_default_registry_run_python_routes_through_broker():
    broker = _FakeBroker()
    reg = build_default_registry(broker)
    assert "run_python" in reg
    res = dispatcher_for(frozenset({"run_python"}), reg).invoke("run_python", {"code": "print(1)"})
    assert res.data["stdout"] == "hi" and broker.calls[0].code == "print(1)"


def test_default_registry_has_no_tools_without_a_broker():
    assert build_default_registry(None).ids() == frozenset()
