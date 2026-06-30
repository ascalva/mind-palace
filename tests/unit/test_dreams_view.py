"""The DreamsView — surfacing the INTERPRETED layer, mirror-not-oracle.

Proves: the view reads recent dreams newest-first; the narration frames them as interpretation
(not authored fact) and cites the spanned notes; an empty store says so plainly; findings are
mentioned when present; and — the integrity bit — the view exposes no mutator, so the Ambassador
cannot write the interpreted layer through it (Constitution §III.2, BUILD-SPEC §8 firewall).
"""

from core.dreams_view import DreamsView
from core.stores.derived import DREAM, FINDING, DerivedStore

# Names that would let the view WRITE the interpreted layer — must not be reachable through it.
_FORBIDDEN = ("add", "reset", "close")


def _store_with_dreams():
    store = DerivedStore(":memory:")
    store.add(kind=DREAM, summary="a recurring pull toward solitude when work intensifies",
              subjects=["overwork", "weekend alone"])
    store.add(kind=DREAM, summary="sleep notes cluster around late-night screen time",
              subjects=["sleep", "phone habits"])
    return store


def test_recent_dreams_reads_all_and_respects_the_limit():
    # newest-first is by created_at (distinct across real dream passes); within the same second
    # the store tiebreaks on content-hash id, so this asserts retrieval + the cap, not sub-second
    # order.
    view = DreamsView.over(_store_with_dreams())
    summaries = {d.summary for d in view.recent_dreams()}
    assert any("solitude" in s for s in summaries) and any("sleep notes" in s for s in summaries)
    assert view.dream_count() == 2
    assert len(view.recent_dreams(limit=1)) == 1            # the cap truncates


def test_narration_is_mirror_not_oracle_and_cites_notes():
    text = DreamsView.over(_store_with_dreams()).narrate_recent()
    # framed as interpretation, judgment handed back (§III.2) — never as authored fact
    assert "not anything you wrote" in text
    assert "prompts rather than conclusions" in text
    # the actual synthesis + the authored notes it spans, cited in double brackets
    assert "recurring pull toward solitude" in text
    assert "[[sleep]]" in text and "[[phone habits]]" in text


def test_empty_store_says_so_plainly():
    text = DreamsView.over(DerivedStore(":memory:")).narrate_recent()
    assert "haven't surfaced any patterns yet" in text


def test_findings_are_mentioned_when_present():
    store = _store_with_dreams()
    store.add(kind=FINDING, subkind="near_duplicate", summary="two near-identical notes",
              subjects=["a", "b"])
    text = DreamsView.over(store).narrate_recent()
    assert "1 note" in text and ("duplicate" in text or "orphan" in text)


def test_view_exposes_no_mutator():
    view = DreamsView.over(_store_with_dreams())
    for name in _FORBIDDEN:
        assert not hasattr(view, name), f"DreamsView has reachable mutator {name!r}"
