"""The research driver — emit → collect → rank → surface, wired end-to-end (bp-028 Item 23).

Cold: a FAKE airlock (canned `collect_one` result) + a real `rank_literature` over a tiny
faked embedder + a stubbed note retrieval. Pins the transient contract (nothing is written to
any store), the outbound firewall (emit is called with a de-identified `ResearchCriteria`), the
ranked return, graceful degradation when no result is back yet, and the request round-trip.
"""

from __future__ import annotations

from typing import cast

import core.research.rank as rank_mod
from core.ingest.embed import Embedder
from core.research.airlock import ResearchResult
from core.research.criteria import Paper, ResearchCriteria, deidentify
from core.stores.vectorstore import VectorStore
from scheduler.research import (
    criteria_from_request,
    render_ranked,
    research_driver,
    run_research,
)


class FakeEmbedder:
    """3-dim one-hot by keyword so cosine relationships are controllable (mirrors the rank test)."""

    def _vec(self, text: str) -> list[float]:
        t = text.lower()
        if "migraine" in t:
            return [1.0, 0.0, 0.0]
        if "cooking" in t:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)


class FakeAirlock:
    """Records the emitted criteria + returns a canned result keyed to it (the fetcher stand-in)."""

    def __init__(self, result: ResearchResult | None):
        self._result = result
        self.emitted: list[ResearchCriteria] = []

    def emit(self, criteria: ResearchCriteria) -> str:
        criteria.assert_clean()          # the real airlock re-asserts here; keep the firewall clean
        self.emitted.append(criteria)
        return criteria.id

    def collect_one(self, criteria_id: str, *, consume: bool = True) -> ResearchResult | None:
        if self._result is None or self._result.criteria_id != criteria_id:
            return None
        return self._result


class FakeLibrarian:
    """Only the outbound seam the driver needs: de-identify a query into a FIXED criteria (so the
    test can key the airlock's canned result to the same id the driver will emit)."""

    def __init__(self, criteria: ResearchCriteria):
        self._criteria = criteria

    def research_criteria(self, query: str, **_kw: object) -> ResearchCriteria:
        return self._criteria


class ExplodingStore:
    """FAILS the test if the driver ever writes (the never-pollute-the-mirror / transient guard)."""

    def add(self, *_a: object, **_k: object) -> None:  # pragma: no cover - must never be called
        raise AssertionError("the research driver must never write to a store (transient contract)")


def _emb() -> Embedder:
    return cast(Embedder, FakeEmbedder())


def _store() -> VectorStore:
    return cast(VectorStore, ExplodingStore())


def _paper(pid: str, title: str, *, type: str = "review", is_preprint: bool = False) -> Paper:
    return Paper(source="openalex", id=pid, title=title, abstract="abstract", year=2020,
                 venue="V", type=type, doi="10.1/x", url="https://doi.org/10.1/x",
                 is_preprint=is_preprint)


def _result(criteria_id: str) -> ResearchResult:
    return ResearchResult(
        criteria_id=criteria_id,
        papers=(_paper("rel", "Migraine prophylaxis review"),
                _paper("irrel", "Cooking techniques overview")),
        sources_queried=("openalex",),
        ts="2026-07-13T00:00:00",
    )


def test_driver_emits_deidentified_and_returns_ranked(monkeypatch):
    monkeypatch.setattr(rank_mod, "semantic_search",
                        lambda *a, **k: [{"text": "my notes on migraine triggers"}])
    criteria = deidentify("migraine prophylaxis", ["migraine prophylaxis", "migraine"])
    lib = FakeLibrarian(criteria)
    airlock = FakeAirlock(_result(criteria.id))

    ranked = research_driver("does riboflavin help MY migraines since March 2019?",
                             librarian=lib, airlock=airlock, embedder=_emb(),
                             store=_store())

    # Ranked, most-relevant first; nothing written to the store (ExplodingStore would have raised).
    assert [r.paper.id for r in ranked] == ["rel", "irrel"]
    assert ranked[0].relevance > ranked[1].relevance
    # The outbound request is de-identified: emit saw a ResearchCriteria whose to_request()
    # carries only topic/terms/filters — no free-text query, no "March", no year, no first person.
    assert len(airlock.emitted) == 1
    wire = airlock.emitted[0].to_request()
    assert set(wire) == {"id", "topic", "terms", "filters"}
    blob = f"{wire['topic']} {' '.join(wire['terms'])}".lower()
    assert "march" not in blob and "2019" not in blob and "riboflavin help my" not in blob


def test_driver_returns_empty_when_no_result_yet(monkeypatch):
    monkeypatch.setattr(rank_mod, "semantic_search", lambda *a, **k: [])
    criteria = deidentify("migraine prophylaxis", ["migraine prophylaxis"])
    airlock = FakeAirlock(None)          # the fetcher has not responded (or is absent)
    ranked = research_driver("migraine prophylaxis", librarian=FakeLibrarian(criteria),
                             airlock=airlock, embedder=_emb(), store=_store())
    assert ranked == []                  # graceful degrade — emitted the request, no crash
    assert len(airlock.emitted) == 1     # the request WAS emitted (a later collect will surface it)


def test_run_research_from_prebuilt_criteria(monkeypatch):
    monkeypatch.setattr(rank_mod, "semantic_search", lambda *a, **k: [{"text": "migraine notes"}])
    criteria = deidentify("migraine", ["migraine"])
    airlock = FakeAirlock(_result(criteria.id))
    ranked = run_research(criteria, airlock, _emb(), _store())
    assert ranked and ranked[0].paper.id == "rel"


def test_collect_one_is_keyed_no_cross_criteria_bleed(monkeypatch):
    # A result keyed to a DIFFERENT criteria id must NOT be collected by this request.
    monkeypatch.setattr(rank_mod, "semantic_search", lambda *a, **k: [{"text": "migraine notes"}])
    criteria = deidentify("migraine", ["migraine"])
    airlock = FakeAirlock(_result("some-other-criteria-id"))
    assert run_research(criteria, airlock, _emb(), _store()) == []


def test_criteria_round_trips_through_request_form():
    c = deidentify("migraine prophylaxis", ["migraine prophylaxis"], from_year=2015,
                   publication_types=["meta-analysis"], max_results=25)
    back = criteria_from_request(c.to_request())
    assert back.topic == c.topic and back.terms == c.terms
    assert back.from_year == 2015 and back.publication_types == ("meta-analysis",)
    assert back.max_results == 25 and back.id == c.id


def test_render_ranked_is_plain_and_flags_evidence(monkeypatch):
    monkeypatch.setattr(rank_mod, "semantic_search", lambda *a, **k: [{"text": "migraine notes"}])
    criteria = deidentify("migraine", ["migraine"])
    airlock = FakeAirlock(_result(criteria.id))
    ranked = run_research(criteria, airlock, _emb(), _store())
    text = render_ranked(ranked)
    assert "Migraine prophylaxis review" in text
    assert "evidence" in text.lower()
    assert render_ranked([]).lower().startswith("i looked")
