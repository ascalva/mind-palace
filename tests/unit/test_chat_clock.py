"""Unit falsifiers for CS-4 (bp-064) — the chat clock: per-session g1 chains, observed stratum.

dn-chat-sensor CS-4: the `chatlog` store enrolls in the spine as a g1-chained source (chain-key =
session id, position = turn index) in the `observed` stratum, with a session-close (TROUGH) cut
certificate. These are the primary falsifiers (the crossing-edge tooth on a seeded chat chain also
rides in `tests/integrity/test_cut_soundness.py`). All in-memory seeded — no `data/`.

Falsifiers (plan §7):
  * per-session chains keyed `chatlog:<session_id>`, position = the LATEST turn index;
  * a cut over `frozenset({"observed"})` with a quiescent trough composes exactly {TROUGH} and has
    NO crossing edge (an utterance mints/consumes nothing cross-store);
  * ordering is TURN INDEX, never the ts_bookmark wall time (Law C4) — the falsifier seeds
    ts_bookmark DESCENDING against ascending turn index, and the order still follows the turns;
  * positions within a session are contiguous;
  * enrolling chat does NOT reshape another store's frontier (additive, not a reshape).
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from core.scope import Clock, Window
from core.stores.chatlog import ChatlogStore, ChatUtterance
from core.stores.versions import VersionStore
from core.temporal.atlas import SpineAtlas
from core.temporal.spine import (
    Certificate,
    CutCertificateError,
    CutSources,
    Order,
    Spine,
    SpineSources,
    TroughState,
)

_MEM = Path(":memory:")
_QUIESCENT = TroughState(queued=0, running=0, trough_id="trough-chat")


def _seeded_chatlog() -> ChatlogStore:
    """Two sessions: s-alpha (turns 0,1,2), s-beta (turns 0,1). ts_bookmark is seeded DESCENDING
    against ascending turn index — so code that ordered by wall time would invert the chain."""
    store = ChatlogStore(_MEM)
    store.add_batch([
        ChatUtterance("s-alpha", 0, "owner", "a0", "dig", ts_bookmark="2026-07-17T12:00:03"),
        ChatUtterance("s-alpha", 1, "agent", "a1", "dig", ts_bookmark="2026-07-17T12:00:02"),
        ChatUtterance("s-alpha", 2, "owner", "a2", "dig", ts_bookmark="2026-07-17T12:00:01"),
        ChatUtterance("s-beta", 0, "owner", "b0", "dig", ts_bookmark="2026-07-17T12:00:09"),
        ChatUtterance("s-beta", 1, "agent", "b1", "dig", ts_bookmark="2026-07-17T12:00:08"),
    ])
    return store


def _chat_spine(*, trough: TroughState | None = _QUIESCENT) -> Spine:
    return Spine.derive(SpineSources(chatlog=_seeded_chatlog()),
                        cut_sources=CutSources(trough=trough))


# ── per-session g1 chains ────────────────────────────────────────────────────────────────────────


def test_frontier_has_one_chain_per_session_at_the_latest_turn() -> None:
    frontier = _chat_spine().frontier()
    assert frontier["chatlog:s-alpha"] == 2          # latest turn index on s-alpha's chain
    assert frontier["chatlog:s-beta"] == 1
    # exactly the two chat chains (no cross-session collapse, no stray key)
    chat_keys = {k for k in frontier if k.startswith("chatlog:")}
    assert chat_keys == {"chatlog:s-alpha", "chatlog:s-beta"}


def test_positions_within_a_session_are_contiguous_turn_indices() -> None:
    spine = _chat_spine()
    by_id = {e.event_id: e for e in spine.events()}
    for pos in (0, 1, 2):
        assert by_id[f"chatlog:s-alpha:{pos}"].position == pos
    assert by_id["chatlog:s-alpha:2"].stratum == "observed"


def test_order_follows_turn_index_not_wall_time() -> None:
    """Law C4: the chain order is turn index. ts_bookmark descends as turn index ascends, so an
    order read from wall time would put turn 0 after turn 2 — the falsifier. Order is by turn."""
    spine = _chat_spine()
    assert spine.order("chatlog:s-alpha:0", "chatlog:s-alpha:2") is Order.BEFORE
    assert spine.order("chatlog:s-alpha:2", "chatlog:s-alpha:0") is Order.AFTER
    # different sessions never share a chain ⇒ concurrent (no cross-session g1 edge)
    assert spine.order("chatlog:s-alpha:0", "chatlog:s-beta:0") is Order.CONCURRENT


# ── the observed cut: TROUGH certificate, no crossing ────────────────────────────────────────────


def test_observed_cut_composes_trough_and_has_no_crossing() -> None:
    spine = _chat_spine()
    cut = spine.cut_at(strata=frozenset({"observed"}))
    assert cut.certificates == frozenset({Certificate.TROUGH})
    assert any("trough-chat" in e for e in cut.evidence)   # scheduler's own trough id, not wall
    assert spine.crossing_edges(cut) == []                 # utterance consumes nothing cross-store
    # the cut's frontier covers both session chains
    assert {k for k, _ in cut.frontier} == {"chatlog:s-alpha", "chatlog:s-beta"}


def test_observed_cut_refuses_without_a_quiescent_trough() -> None:
    """No fabricated certificate: an observed cut with no trough source REFUSES (never silent)."""
    spine = _chat_spine(trough=None)
    with pytest.raises(CutCertificateError, match="trough certificate absent"):
        spine.cut_at(strata=frozenset({"observed"}))


# ── the chat frontier is atlas-reachable, and enrollment reshapes nothing (§3 Q4, §4) ────────────


def test_chat_frontier_is_atlas_reachable() -> None:
    """§3 Q4: the chat store's frontier is store-scoped (read via `frontier_at`), and the read-clock
    machinery resolves through the existing atlas with NO change. A False here would be a real GC-4
    gap ⇒ a codebase finding, not a silent patch."""
    spine = _chat_spine()
    assert spine.frontier_at("chatlog") == 2               # latest chat position (atlas-borrowable)
    atlas = SpineAtlas(spine)
    assert atlas.has(Clock.N_S) is True                    # read-clock resolves; no atlas change
    # chat events participate in the pullback (pullback is typed Hashable; frozenset[str] runtime)
    pulled = cast("frozenset[str]", atlas.pullback(Clock.N_S, Window.all()))
    assert "chatlog:s-alpha:2" in pulled


def test_enrolling_chat_does_not_reshape_another_stores_frontier() -> None:
    """Additive, not a reshape (§4): a spine over versions+chat has the SAME versions frontier as a
    versions-only spine — chat enrollment perturbs no other chain."""
    vs = VersionStore(_MEM)
    vs.record("docA", "a1")
    vs.record("docA", "a2")
    versions_only = Spine.derive(SpineSources(versions=vs)).frontier()

    vs2 = VersionStore(_MEM)
    vs2.record("docA", "a1")
    vs2.record("docA", "a2")
    with_chat = Spine.derive(SpineSources(versions=vs2, chatlog=_seeded_chatlog())).frontier()

    assert with_chat["versions:docA"] == versions_only["versions:docA"] == 2
    assert "chatlog:s-alpha" in with_chat and "chatlog:s-alpha" not in versions_only
