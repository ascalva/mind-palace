"""Minting + the scope ceiling (BUILD-SPEC §10): Constitution inheritance, scope resolution,
self-evaluation, privileged-request routing to the gate, ephemeral/persist."""

import pytest

from core.constitution import load_constitution
from core.factory import AgentFactory, build_default_registry
from core.factory.registry import AgentRegistry
from core.factory.tools import ToolNotInScopeError
from core.sandbox.spec import ExecResult
from ops.gate import GateRequest, GateStatus


class _FakeServer:
    def __init__(self, reply="ok"):
        self.reply = reply
        self.calls = []

    def chat(self, tier, messages, *, think=None):
        self.calls.append((tier, messages))
        return self.reply


class _FakeBroker:
    def run(self, spec):
        return ExecResult("42", "", 0)


def _factory(server=None, broker=None):
    return AgentFactory(server=server, tools=build_default_registry(broker))


def test_mint_returns_agent_inheriting_the_constitution():
    agent = _factory().mint("general_conversation")
    ctx = agent.build_context("hello")
    assert ctx[0]["content"] == load_constitution()          # Constitution outermost (Inv 6)
    assert any("conversational" in m["content"] for m in ctx)
    assert ctx[-1] == {"role": "user", "content": "hello"}
    assert agent.ephemeral is True


def test_mint_resolves_scope_to_role_intersect_max():
    coder = _factory(broker=_FakeBroker()).mint("coder")
    assert coder.scope == frozenset({"run_python"})
    assert coder.dispatcher.can_invoke("run_python")
    writer = _factory().mint("writer_editor")
    assert writer.scope == frozenset()
    assert not writer.dispatcher.can_invoke("run_python")


def test_minted_agent_self_evaluates_on_respond():
    agent = _factory(server=_FakeServer("a plain answer")).mint("general_conversation")
    text, check = agent.respond("hi")
    assert text == "a plain answer" and check.passed
    assert any(f.directive == "grounded-citations" for f in check.findings)
    assert agent.server.calls[0][0] == "routine"             # role's default tier


def test_privileged_request_routes_to_gate_not_a_privileged_agent():
    f = _factory()
    out = f.mint("personal_assistant", requested_tools=frozenset({"run_python"}))
    assert isinstance(out, GateRequest) and out.status is GateStatus.PENDING
    assert f.gate.pending() == [out]


def test_request_beyond_pre_declared_max_routes_to_gate():
    f = _factory(broker=_FakeBroker())
    out = f.mint("coder", requested_tools=frozenset({"deploy_aws"}))   # not in MAX at all
    assert isinstance(out, GateRequest)


def test_invoking_out_of_scope_tool_refuses_and_routes_to_gate():
    f = _factory()
    agent = f.mint("writer_editor")                            # advisory, no tools
    with pytest.raises(ToolNotInScopeError):
        agent.invoke("run_python", {"code": "x"})
    assert any(r.kind == "out_of_scope_tool" for r in f.gate.pending())


def test_unknown_role_raises():
    with pytest.raises(KeyError):
        _factory().mint("nonexistent_role")


def test_persist_records_in_the_registry(tmp_path):
    reg = AgentRegistry(tmp_path / "agents.db")
    f = AgentFactory(tools=build_default_registry(_FakeBroker()), agent_registry=reg)
    f.mint("coder", name="my-coder", persist=True)
    rec = reg.get("my-coder")
    assert rec is not None and rec.role == "coder" and rec.scope == frozenset({"run_python"})
    assert [a.name for a in reg.list()] == ["my-coder"]
