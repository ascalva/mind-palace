"""B5 — agent-judged retrieval WITHIN the budgeter ceiling (Track B).

The Ambassador chooses what to put in the context (how many chunks, how much history); the §13
budgeter is the one and only thing that enforces the window. An oversized choice is trimmed (or
escalated), never silently overflowed.
"""

from pathlib import Path

from agents.ambassador import Ambassador
from core.attestation.store import AttestationStore
from core.librarian import Librarian, Retrieval
from core.ops_view import OpsView
from ops.ledger import ProposalLedger
from scheduler.budget import Budgeter
from tests.fixtures.fakes import HashingEmbedder, ReplyServer


def _bare_ambassador(window: int, reserve: int) -> Ambassador:
    store_att = AttestationStore(Path(":memory:"))
    return Ambassador(
        server=ReplyServer(),
        librarian=Librarian(server=ReplyServer(), embedder=HashingEmbedder(8), store=None, k=5),
        ops_view=OpsView.over(store_att, ProposalLedger(Path(":memory:"))),
        budgeter=Budgeter(window=window, reserve=reserve),
        tier="router",
    )


def _chunks(n: int, size: int) -> list[Retrieval]:
    return [Retrieval(title=f"n{i}", source_path=f"/n{i}", text="word " * size, distance=0.1,
                      provenance="authored-solo", digest=f"d{i}") for i in range(n)]


def test_oversized_retrieval_is_trimmed_to_fit_never_overflows():
    amb = _bare_ambassador(window=3000, reserve=256)
    amb._history["default"] = [{"role": "user", "content": "history " * 200}]
    budgeted = amb._assemble("a question", _chunks(40, 80), "default")
    report = budgeted.report
    budget = report.window - report.reserve
    # the agent's oversized choice did NOT silently overflow:
    if report.fits:
        assert report.used_tokens <= budget
        assert report.retrieved_dropped > 0 or report.history_dropped > 0   # trimming happened
    else:
        assert report.escalate            # even the mandatory frame won't fit → route larger


def test_a_modest_choice_fits_without_trimming():
    amb = _bare_ambassador(window=8192, reserve=1024)
    budgeted = amb._assemble("a short question", _chunks(3, 10), "default")
    report = budgeted.report
    assert report.fits and report.retrieved_dropped == 0 and report.history_dropped == 0


def test_assembled_context_is_constitution_first():
    amb = _bare_ambassador(window=8192, reserve=1024)
    budgeted = amb._assemble("q", _chunks(2, 5), "default")
    # Constitution outermost (Invariant 6), query last (the §13 order the budgeter assembles).
    assert "CONSTITUTION" in budgeted.messages[0]["content"].upper()
    assert budgeted.messages[-1] == {"role": "user", "content": "q"}
