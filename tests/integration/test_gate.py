"""The human gate seam (BUILD-SPEC §10, §14; Invariant 5)."""

from ops.gate import GateStatus, HumanGate


def test_submit_records_a_pending_request():
    g = HumanGate()
    r = g.submit("privileged_mint", "needs shell access")
    assert r.id == 1 and r.status is GateStatus.PENDING
    assert g.pending() == [r]


def test_requests_increment_and_carry_agent():
    g = HumanGate()
    g.submit("a", "x")
    r2 = g.submit("out_of_scope_tool", "y", agent="coder")
    assert r2.id == 2 and r2.agent == "coder"
    assert len(g.all()) == 2 and len(g.pending()) == 2
