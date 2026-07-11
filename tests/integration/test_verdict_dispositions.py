"""Verdict apply (dispositions) + Ambassador transport — build plan Item 4b-apply + transport (R7).

The buildable half of 'apply': a `wrong`/`noise` verdict RETRACTS its subject from the active
projection (DreamsView stops surfacing it) while it stays in history; endorse/record are noted.
Weight promotion (recursive-strata I1) is parked and absent. The Ambassador transports a signed
verdict to the receiver but never verifies/applies it. Deterministic; no model, no network.
"""

from __future__ import annotations

import pytest

from core.dreams_view import DreamsView
from core.stores.derived import DREAM, DerivedStore
from core.verdict.apply import apply_verdict, effect_of
from core.verdict.dispositions import DispositionStore, VerdictEffect


def _dispositions(tmp_path):
    return DispositionStore(tmp_path / "disp.sqlite")


def test_effect_of_maps_categories():
    assert effect_of("wrong") is VerdictEffect.RETRACT
    assert effect_of("noise") is VerdictEffect.RETRACT
    assert effect_of("novel_useful") is VerdictEffect.ENDORSE
    assert effect_of("true_known") is VerdictEffect.RECORD
    assert effect_of("plausible") is VerdictEffect.RECORD


def test_disposition_latest_verdict_wins(tmp_path):
    d = _dispositions(tmp_path)
    d.record("claim-1", VerdictEffect.RETRACT, verdict_seq=1)
    assert d.retracted() == {"claim-1"}
    # A later verdict (higher seq) changes the owner's mind → no longer retracted; history kept.
    d.record("claim-1", VerdictEffect.ENDORSE, verdict_seq=4)
    assert d.effect_for("claim-1") is VerdictEffect.ENDORSE
    assert d.retracted() == set()
    assert d.count() == 2


def test_apply_verdict_records_the_effect(tmp_path):
    from core.stores.verdicts import VerdictRecord

    d = _dispositions(tmp_path)
    rec = VerdictRecord(seq=2, subject_id="dream-x", verdict="wrong",
                        timestamp="t", signature="s", signer="owner", recorded_at="t")
    assert apply_verdict(rec, d) is VerdictEffect.RETRACT
    assert d.retracted() == {"dream-x"}


def test_dreamsview_active_projection_excludes_retracted(tmp_path):
    store = DerivedStore(tmp_path / "derived.sqlite")
    a = store.add(kind=DREAM, summary="theme A", subjects=("n1", "n2"))
    b = store.add(kind=DREAM, summary="theme B", subjects=("n3",))
    d = _dispositions(tmp_path)

    view = DreamsView.over(store, dispositions=d)
    assert {x.id for x in view.recent_dreams()} == {a.id, b.id}       # nothing retracted yet

    d.record(a.id, VerdictEffect.RETRACT, verdict_seq=1)             # owner verdicts A `wrong`
    assert {x.id for x in view.recent_dreams()} == {b.id}    # A dropped from the active view
    assert store.count(kind=DREAM) == 2                     # ... but kept in history


def test_dreamsview_without_dispositions_is_unchanged(tmp_path):
    store = DerivedStore(tmp_path / "derived.sqlite")
    store.add(kind=DREAM, summary="theme", subjects=("n1",))
    assert len(DreamsView.over(store).recent_dreams()) == 1           # backward-compatible default


def test_ambassador_transports_but_never_applies():
    from typing import cast

    from agents.ambassador.agent import Ambassador, ChatServer
    from core.librarian import Librarian
    from core.ops_view import OpsView
    from scheduler.budget import Budgeter

    # This test exercises ONLY transport_verdict(); server/librarian/ops_view/budgeter are never
    # read on that path, so a bare `object()` placeholder is the right test double — the casts
    # say "this field's real type doesn't matter here," not "this satisfies the interface."
    placeholder = object()
    carried = []

    def _carry(s: object) -> str:
        carried.append(s)
        return "forwarded"

    amb = Ambassador(server=cast(ChatServer, placeholder), librarian=cast(Librarian, placeholder),
                     ops_view=cast(OpsView, placeholder), budgeter=cast(Budgeter, placeholder),
                     verdict_transport=_carry)
    assert amb.transport_verdict({"payload": "..."}) == "forwarded"
    assert carried == [{"payload": "..."}]           # forwarded verbatim, unexamined

    no_channel = Ambassador(server=cast(ChatServer, placeholder),
                            librarian=cast(Librarian, placeholder),
                            ops_view=cast(OpsView, placeholder),
                            budgeter=cast(Budgeter, placeholder))
    with pytest.raises(RuntimeError):        # cannot manufacture a verdict channel it lacks
        no_channel.transport_verdict({"payload": "..."})
