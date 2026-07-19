"""Unit tests for the first full integrator (bp-071 Item 1, dn-agent-taxonomy §2.5).

`integrate` resolves the L1 action log's references into proven C-fiber edges: a `commit` event
resolves against the commit ledger by ABBREVIATED-sha prefix match (finding-0111); a `file_edit`/
`build_plan`/`finding`/`design_note` event mints its endpoint directly. Every integrable event is
resolved into an edge or NAMED unresolvable — never silently dropped. Re-runs are no-ops
(witness-keyed, replace-per-session-digest). The agent is BORN SCOPED: its handle inventory ⊑
`INTEGRATOR_SCOPE`, and a smuggled handle is rejected.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from core.agent_scope import ConformanceError, Handle, assert_conforms
from core.chat_events import ChatEvent
from core.integrator import INTEGRATOR_SCOPE, Integrator
from core.scope import Stratum
from core.stores.causal_edges import CausalEdgeStore
from core.stores.chat_events import ChatEventStore
from ops.code_snapshot import open_snapshot_db

FULL_SHA = "abc1234def5678901234567890abcdef01234567"


def _ledger(*shas: str):
    """An in-memory commit ledger with the given full shas recorded in `snapshots`."""
    db = open_snapshot_db(Path(":memory:"))
    for sha in shas:
        db.execute("INSERT INTO snapshots (commit_sha, committed_at, taken_at, files, loc, "
                   "functions, classes) VALUES (?, ?, ?, 0, 0, 0, 0)",
                   [sha, "2026-07-19T00:00:00", "2026-07-19T00:00:00"])
    db.commit()
    return db


def _l1(events: list[ChatEvent], digest: str = "digest-a",
        session: str = "sess-a") -> ChatEventStore:
    store = ChatEventStore(Path(":memory:"))
    store.replace_session(session, events, digest)
    return store


def _ev(order: int, kind: str, ref: str, *, actor: str = "agent", turn: int = 0) -> ChatEvent:
    return ChatEvent(session_id="sess-a", order=order, actor=actor, kind=kind, ref=ref,
                     turn_index=turn)


def _integrator(events: ChatEventStore, ledger) -> Integrator:
    return Integrator(events=events, ledger=ledger, edges=CausalEdgeStore(Path(":memory:")))


# --- resolution: commit events ---------------------------------------------------------------
def test_commit_event_resolves_to_ledger_commit_by_prefix() -> None:
    """An abbreviated sha (the L1 ref) prefix-matches the full ledger sha → a commit edge whose
    dst is the FULL sha and whose pair_cut_sha is the full sha (the (digest, sha) cut)."""
    events = _l1([_ev(0, "commit", "abc1234", turn=3)])
    integ = _integrator(events, _ledger(FULL_SHA))
    report = integ.integrate(max_sessions=10)

    assert report.commit_events == 1 and report.commit_resolved == 1
    (edge,) = integ.edges.edges_for("sess-a")
    assert edge["kind"] == "C" and edge["dst_type"] == "commit"
    assert edge["dst"] == FULL_SHA and edge["pair_cut_sha"] == FULL_SHA
    assert edge["witness_digest"] == "digest-a" and edge["witness_turn"] == 3


def test_unresolvable_sha_is_named_not_dropped() -> None:
    """A commit sha absent from the ledger is NAMED (`unknown-sha`), mints no edge; parity holds."""
    events = _l1([_ev(0, "commit", "deadbee")])
    integ = _integrator(events, _ledger(FULL_SHA))
    report = integ.integrate(max_sessions=10)

    assert report.commit_events == 1 and report.commit_resolved == 0
    assert report.unresolved == {"unknown-sha": 1}
    assert integ.edges.count() == 0
    assert report.is_fully_accounted()


def test_absent_ledger_table_names_every_sha_unknown() -> None:
    """A ledger with no `snapshots` table (code sensor never ran) → every commit is `unknown-sha`,
    not a crash (the daemon may integrate before the first code-sensor sync)."""
    events = _l1([_ev(0, "commit", "abc1234")])
    integ = Integrator(events=events, ledger=sqlite3.connect(":memory:"),
                       edges=CausalEdgeStore(Path(":memory:")))
    report = integ.integrate(max_sessions=10)
    assert report.unresolved == {"unknown-sha": 1} and integ.edges.count() == 0
    assert report.is_fully_accounted()


def test_empty_and_ambiguous_shas_are_named() -> None:
    events = _l1([_ev(0, "commit", ""), _ev(1, "commit", "abc")])
    integ = _integrator(events, _ledger(FULL_SHA, "abc9999999999999999999999999999999999999"))
    report = integ.integrate(max_sessions=10)

    assert report.unresolved == {"unparsed-sha": 1, "ambiguous-sha": 1}
    assert integ.edges.count() == 0
    assert report.is_fully_accounted()


# --- resolution: write events (direct endpoints) ---------------------------------------------
def test_doc_write_resolves_to_artifact() -> None:
    """A build_plan write mints a doc edge directly (dst = the artifact id, no commit anchor)."""
    events = _l1([_ev(0, "build_plan", "bp-071", turn=2)])
    integ = _integrator(events, _ledger())
    integ.integrate(max_sessions=10)

    (edge,) = integ.edges.edges_for("sess-a")
    assert edge["dst_type"] == "doc" and edge["dst"] == "bp-071"
    assert edge["pair_cut_sha"] == "" and edge["witness_turn"] == 2


def test_finding_and_design_note_are_doc_endpoints() -> None:
    events = _l1([_ev(0, "finding", "finding-0111"), _ev(1, "design_note", "agent-taxonomy.md")])
    integ = _integrator(events, _ledger())
    integ.integrate(max_sessions=10)
    assert {e["dst_type"] for e in integ.edges.edges_for("sess-a")} == {"doc"}


def test_file_edit_resolves_to_file() -> None:
    events = _l1([_ev(0, "file_edit", "core/integrator.py")])
    integ = _integrator(events, _ledger())
    integ.integrate(max_sessions=10)
    (edge,) = integ.edges.edges_for("sess-a")
    assert edge["dst_type"] == "file" and edge["dst"] == "core/integrator.py"


# --- non-integrable events -------------------------------------------------------------------
def test_prompt_response_tool_use_are_non_integrable() -> None:
    """Events that name no external endpoint are counted, not dropped, and mint no edge."""
    events = _l1([_ev(0, "prompt", "0", actor="owner"), _ev(1, "response", "1"),
                  _ev(2, "tool_use", "Bash")])
    integ = _integrator(events, _ledger())
    report = integ.integrate(max_sessions=10)
    assert report.non_integrable == 3 and integ.edges.count() == 0
    assert report.integrable_events == 0 and report.coverage == 0.0


# --- idempotency / incrementality ------------------------------------------------------------
def test_rerun_at_same_digest_is_a_noop() -> None:
    events = _l1([_ev(0, "commit", "abc1234")])
    integ = _integrator(events, _ledger(FULL_SHA))
    integ.integrate(max_sessions=10)
    second = integ.integrate(max_sessions=10)
    assert second.sessions_processed == 0 and second.sessions_skipped == 1
    assert second.edges_minted == 0 and integ.edges.count() == 1


def test_grown_session_remints() -> None:
    """A session whose L1 digest changed is re-integrated (the edge set replaced)."""
    edges_store = CausalEdgeStore(Path(":memory:"))
    events = ChatEventStore(Path(":memory:"))
    events.replace_session("sess-a", [_ev(0, "commit", "abc1234")], "digest-a")
    integ = Integrator(events=events, ledger=_ledger(FULL_SHA), edges=edges_store)
    integ.integrate(max_sessions=10)
    events.replace_session("sess-a",
                           [_ev(0, "commit", "abc1234"), _ev(1, "file_edit", "x.py")], "digest-b")
    report = integ.integrate(max_sessions=10)
    assert report.sessions_processed == 1 and integ.edges.count() == 2
    assert integ.edges.digest_for("sess-a") == "digest-b"


def test_max_sessions_bounds_the_pass() -> None:
    events = ChatEventStore(Path(":memory:"))
    events.replace_session("sess-a", [_ev(0, "file_edit", "a.py")], "da")
    events.replace_session("sess-b", [_ev(0, "file_edit", "b.py")], "db")
    integ = Integrator(events=events, ledger=_ledger(), edges=CausalEdgeStore(Path(":memory:")))
    report = integ.integrate(max_sessions=1)
    assert report.sessions_processed == 1


# --- coverage + parity gauges ----------------------------------------------------------------
def test_coverage_is_honest_partial() -> None:
    """One resolved commit + one direct write + one unresolvable commit → coverage 2/3."""
    events = _l1([_ev(0, "commit", "abc1234"), _ev(1, "file_edit", "x.py"),
                  _ev(2, "commit", "deadbee")])
    integ = _integrator(events, _ledger(FULL_SHA))
    report = integ.integrate(max_sessions=10)
    assert report.integrable_events == 3
    assert report.coverage == pytest.approx(2 / 3)
    assert report.is_fully_accounted()


# --- born scoped: conformance ----------------------------------------------------------------
def test_handle_inventory_conforms_to_integrator_scope() -> None:
    integ = _integrator(_l1([]), _ledger())
    assert_conforms(INTEGRATOR_SCOPE, integ.handle_inventory())   # does not raise


def test_smuggled_edge_fiber_is_rejected() -> None:
    """A handle writing a fiber outside {C, F} (e.g. D — the D-machinery's) is rejected."""
    with pytest.raises(ConformanceError):
        assert_conforms(INTEGRATOR_SCOPE,
                        (Handle("smuggled", Stratum.DIALOGUE, writes_fiber="D"),))


def test_smuggled_out_of_sigma_stratum_is_rejected() -> None:
    integ = _integrator(_l1([]), _ledger())
    with pytest.raises(ConformanceError):
        assert_conforms(INTEGRATOR_SCOPE,
                        (*integ.handle_inventory(), Handle("mirror", Stratum.MIRROR)))
