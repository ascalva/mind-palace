"""Ranking public literature against the private corpus, inside the walls (§16).

Fully cold: a fake embedder + a stubbed retrieval, so the deterministic ranking logic is
pinned without a model. Asserts personalization (relevance to the owner's notes), evidence
bias, preprint flagging, the unresolved-identifier honesty flag, and deterministic order.
"""

from __future__ import annotations

import core.research.rank as rank_mod
from core.research.criteria import Paper, deidentify
from core.research.rank import rank_literature


class FakeEmbedder:
    """Maps text to a 3-dim one-hot by keyword so cosine relationships are controllable."""

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


def _paper(pid, title, *, type="journal-article", is_preprint=False, doi="10.1/x",
           url="https://doi.org/10.1/x", abstract="abstract"):
    return Paper(source="openalex", id=pid, title=title, abstract=abstract, year=2020,
                 venue="V", type=type, doi=doi, url=url, is_preprint=is_preprint)


def _stub_notes(monkeypatch, note_texts):
    monkeypatch.setattr(
        rank_mod, "semantic_search",
        lambda *a, **k: [{"text": t} for t in note_texts],
    )


def test_relevance_to_corpus_outranks_irrelevant(monkeypatch):
    _stub_notes(monkeypatch, ["my notes on migraine triggers"])
    criteria = deidentify("migraine", ["migraine"])
    papers = [
        _paper("rel", "Migraine prophylaxis review"),
        _paper("irrel", "Cooking techniques overview"),
    ]
    ranked = rank_literature(papers, criteria, FakeEmbedder(), store=object())
    assert ranked[0].paper.id == "rel"
    assert ranked[0].relevance > ranked[1].relevance


def test_evidence_tier_and_preprint_flag(monkeypatch):
    _stub_notes(monkeypatch, ["migraine notes"])
    criteria = deidentify("migraine", ["migraine"])
    papers = [
        _paper("pre", "Migraine biomarkers", is_preprint=True),
        _paper("rev", "Migraine review", type="meta-analysis"),
    ]
    ranked = rank_literature(papers, criteria, FakeEmbedder(), store=object())
    tiers = {r.paper.id: r.evidence_tier for r in ranked}
    assert tiers["rev"] == "high"
    assert tiers["pre"] == "preprint"
    # Equal relevance (both migraine) → evidence quality breaks the tie: review first.
    assert ranked[0].paper.id == "rev"
    pre = next(r for r in ranked if r.paper.id == "pre")
    assert "preprint-not-vetted" in pre.flags


def test_unresolved_identifier_is_flagged(monkeypatch):
    _stub_notes(monkeypatch, ["migraine notes"])
    criteria = deidentify("migraine", ["migraine"])
    papers = [_paper("x", "Migraine study", doi="", url="")]
    ranked = rank_literature(papers, criteria, FakeEmbedder(), store=object())
    assert "unresolved-identifier" in ranked[0].flags


def test_falls_back_to_query_when_corpus_silent(monkeypatch):
    _stub_notes(monkeypatch, [])  # corpus has nothing on the topic
    criteria = deidentify("migraine", ["migraine"])
    papers = [_paper("a", "Migraine prophylaxis review")]
    ranked = rank_literature(papers, criteria, FakeEmbedder(), store=object())
    # Still ranks (relevance vs the topic query embedding), no crash.
    assert ranked[0].relevance > 0.0


def test_empty_input_returns_empty(monkeypatch):
    _stub_notes(monkeypatch, ["migraine notes"])
    criteria = deidentify("migraine", ["migraine"])
    assert rank_literature([], criteria, FakeEmbedder(), store=object()) == []
