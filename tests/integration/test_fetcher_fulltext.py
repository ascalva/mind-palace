"""Open-access full-text fetch (bp-029 Item 27) — the licence gate at the fetch boundary (Zone C).

Cold: a fake `fetch` returns canned search + `fullTextXML` responses (no network). Pins that
Europe PMC open-access records get their JATS full text, that NON-open-access records are never
even asked for full text (the Item-27 falsifier — no fetch outside the gate), that arXiv/OpenAlex
stay DISTILLED-only, that a bad full-text response fails CLOSED, and that `full_text` rides the
aggregate payload into the core `Paper.from_dict`.

Flat Lambda-zip layout: cloud/fetcher uses bare imports; add it to sys.path (mirrors test_fetcher).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

FETCHER_DIR = Path(__file__).resolve().parents[2] / "cloud" / "fetcher"
sys.path.insert(0, str(FETCHER_DIR))

import aggregate as agg  # type: ignore[import-not-found]  # noqa: E402
import sources as src  # type: ignore[import-not-found]  # noqa: E402

from core.research.criteria import Paper  # noqa: E402

FULLTEXT_XML = (
    b"<article><front><article-meta><title-group>"
    b"<article-title>T</article-title></title-group></article-meta></front>"
    b"<body><sec><p>The reproducing kernel is the crux of the argument.</p></sec></body>"
    b"</article>"
)

CRITERIA = {"id": "r", "topic": "kernels", "terms": ["kernels"], "filters": {"max_results": 50}}


def _epmc_search(*, is_oa: bool, pmcid: str = "PMC900") -> bytes:
    return json.dumps({"resultList": {"result": [{
        "id": "PMID9", "pmid": "999", "title": "OA paper", "abstractText": "abs",
        "pubYear": "2020", "journalTitle": "J", "pubType": "review", "doi": "10.9/x",
        "source": "MED", "isOpenAccess": ("Y" if is_oa else "N"), "pmcid": pmcid,
    }]}}).encode()


def test_europepmc_open_access_gets_full_text():
    calls: list[str] = []

    def fetch(url: str) -> bytes:
        calls.append(url)
        if "fullTextXML" in url:
            return FULLTEXT_XML
        if "europepmc" in url:
            return _epmc_search(is_oa=True)
        raise AssertionError(url)

    rec = src.europepmc(CRITERIA, fetch)[0]
    assert rec["open_access"] is True
    assert rec["full_text"] and "reproducing kernel" in rec["full_text"]
    assert any("fullTextXML" in u and "PMC900" in u for u in calls)  # gate opened for OA


def test_non_open_access_full_text_is_never_fetched():
    # The Item-27 falsifier: a record NOT flagged open-access must not trigger a full-text fetch.
    calls: list[str] = []

    def fetch(url: str) -> bytes:
        calls.append(url)
        if "fullTextXML" in url:
            raise AssertionError("full text fetched for a NON-open-access record (licence breach)")
        return _epmc_search(is_oa=False)

    rec = src.europepmc(CRITERIA, fetch)[0]
    assert rec["open_access"] is False
    assert rec["full_text"] is None
    assert not any("fullTextXML" in u for u in calls)  # gate stayed shut


def test_full_text_fetch_fails_closed():
    # A malformed / failed full-text response keeps the record DISTILLED-only — never crash/guess.
    def fetch(url: str) -> bytes:
        if "fullTextXML" in url:
            return b"<not-xml"          # ET.fromstring raises → None (fail closed)
        return _epmc_search(is_oa=True)

    rec = src.europepmc(CRITERIA, fetch)[0]
    assert rec["open_access"] is True
    assert rec["full_text"] is None


def test_arxiv_and_openalex_stay_distilled_only():
    arxiv_feed = (
        b'<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
        b"<id>http://arxiv.org/abs/2401.1v1</id><title>P</title>"
        b"<summary>s</summary><published>2024-01-01T00:00:00Z</published>"
        b"</entry></feed>"
    )
    arec = src.arxiv(CRITERIA, lambda u: arxiv_feed)[0]
    assert arec["open_access"] is True and arec["full_text"] is None  # PDF-only → deferred

    openalex_json = json.dumps({"results": [{
        "id": "https://openalex.org/W1", "display_name": "P", "publication_year": 2020,
        "type": "review", "doi": "10.1/z", "abstract_inverted_index": {"x": [0]},
        "open_access": {"is_oa": True},
    }]}).encode()
    orec = src.openalex(CRITERIA, lambda u: openalex_json)[0]
    assert orec["full_text"] is None  # OA flag honest, but no stdlib-fetchable full text


def test_full_text_rides_aggregate_payload_into_paper():
    def fetch(url: str) -> bytes:
        if "fullTextXML" in url:
            return FULLTEXT_XML
        return _epmc_search(is_oa=True)

    result = agg.aggregate(CRITERIA, fetch, sources=["europepmc"])
    paper = Paper.from_dict(result["papers"][0])
    assert paper.open_access is True
    assert paper.full_text and "reproducing kernel" in paper.full_text
