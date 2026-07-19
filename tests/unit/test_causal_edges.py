"""Unit tests for the C-fiber causal-edge store (bp-071 Item 1).

One row = one proven cross-strata edge (a DIALOGUE action → its produced endpoint). The store is
witness-keyed (a content-derived `edge_id` over (digest, event_order, dst_type, dst)) and
replace-per-session-digest (the landed L1 pattern) — so re-integrating an unchanged session is a
byte-identical no-op, and a grown session re-mints cleanly. The closed vocabularies (fiber,
dst_type) are validated at mint — a typo is unrepresentable.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.stores.causal_edges import CausalEdge, CausalEdgeStore, _edge_id


def _edge(*, session: str = "sess-a", digest: str = "d0", order: int = 0, dst_type: str = "commit",
          dst: str = "abc123", turn: int = 0, pair_cut_sha: str = "abc123") -> CausalEdge:
    return CausalEdge.mint(session_id=session, event_order=order, kind="C", dst_type=dst_type,
                           dst=dst, witness_digest=digest, witness_turn=turn,
                           pair_cut_sha=pair_cut_sha)


# --- mint validation -------------------------------------------------------------------------
def test_mint_rejects_unknown_fiber() -> None:
    with pytest.raises(ValueError, match="kind must be one of"):
        CausalEdge.mint(session_id="s", event_order=0, kind="D", dst_type="commit", dst="x",
                        witness_digest="d", witness_turn=0)


def test_mint_rejects_unknown_dst_type() -> None:
    with pytest.raises(ValueError, match="dst_type must be one of"):
        CausalEdge.mint(session_id="s", event_order=0, kind="C", dst_type="symbol", dst="x",
                        witness_digest="d", witness_turn=0)


def test_edge_id_is_content_derived_and_stable() -> None:
    """Same witness-keyed tuple → same id (idempotency); a different endpoint → a different id."""
    assert _edge(order=1, dst="s1").edge_id == _edge(order=1, dst="s1").edge_id
    assert _edge(order=1, dst="s1").edge_id != _edge(order=1, dst="s2").edge_id
    assert _edge(order=1, dst="s1").edge_id != _edge(order=2, dst="s1").edge_id
    # the id is exactly the content hash over the witness-keyed tuple
    assert _edge(order=1, dst="s1").edge_id == _edge_id("d0", 1, "commit", "s1")


# --- store: replace-per-session-digest -------------------------------------------------------
def test_replace_session_writes_edges_and_digest() -> None:
    store = CausalEdgeStore(Path(":memory:"))
    n = store.replace_session("sess-a", [_edge(order=0, dst="s1"), _edge(order=1, dst="s2")], "d0")
    assert n == 2
    assert store.count() == 2
    assert store.digest_for("sess-a") == "d0"
    assert [e["dst"] for e in store.edges_for("sess-a")] == ["s1", "s2"]


def test_replace_session_is_idempotent_at_same_digest() -> None:
    """Re-integrating the same session (same edges) leaves the count and ids unchanged."""
    store = CausalEdgeStore(Path(":memory:"))
    edges = [_edge(order=0, dst="s1"), _edge(order=1, dst="s2")]
    store.replace_session("sess-a", edges, "d0")
    ids_before = {e["edge_id"] for e in store.all_edges()}
    store.replace_session("sess-a", edges, "d0")
    assert store.count() == 2
    assert {e["edge_id"] for e in store.all_edges()} == ids_before


def test_replace_session_remints_on_grown_digest() -> None:
    """A grown session (new digest) wipes the old edge set and rewrites — no stale rows survive."""
    store = CausalEdgeStore(Path(":memory:"))
    store.replace_session("sess-a", [_edge(order=0, dst="s1")], "d0")
    store.replace_session("sess-a", [_edge(order=0, dst="s1"), _edge(order=1, dst="s2")], "d1")
    assert store.count() == 2
    assert store.digest_for("sess-a") == "d1"


def test_digest_for_absent_is_none() -> None:
    store = CausalEdgeStore(Path(":memory:"))
    assert store.digest_for("nope") is None


def test_sessions_with_edges() -> None:
    store = CausalEdgeStore(Path(":memory:"))
    store.replace_session("sess-a", [_edge(session="sess-a", digest="d0")], "d0")
    store.replace_session("sess-b", [_edge(session="sess-b", digest="d1")], "d1")
    assert store.sessions_with_edges() == ["sess-a", "sess-b"]


def test_replace_session_rejects_foreign_session_edges() -> None:
    """A mismatched edge session_id fails loudly (it would orphan a row past the keyed DELETE)."""
    store = CausalEdgeStore(Path(":memory:"))
    with pytest.raises(ValueError, match="other sessions"):
        store.replace_session("sess-a", [_edge(session="sess-b")], "d0")
