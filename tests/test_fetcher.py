"""The cloud fetcher (Zone C Lambda) — broad public aggregation (§16).

Cold: a fake `fetch` returns canned OpenAlex / Europe PMC / arXiv responses (no network), a
fake S3 client captures the written result. Pins dedup, evidence ordering, preprint flagging,
dropping unresolvable identifiers, and the S3 read→aggregate→write event flow.

`cloud/fetcher` is deployed flat at the Lambda zip root, so its modules use bare imports
(`from sources import ...`); add that dir to sys.path to import them here, mirroring Lambda.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

FETCHER_DIR = Path(__file__).resolve().parent.parent / "cloud" / "fetcher"
sys.path.insert(0, str(FETCHER_DIR))

import aggregate as agg  # noqa: E402
import handler as handler_mod  # noqa: E402

OPENALEX = json.dumps({
    "results": [
        {
            "id": "https://openalex.org/W1", "display_name": "A systematic review of migraine",
            "publication_year": 2021, "type": "review", "doi": "https://doi.org/10.1/dup",
            "abstract_inverted_index": {"Migraine": [0], "review.": [1]},
            "primary_location": {"source": {"display_name": "Headache"}},
        },
        {
            "id": "https://openalex.org/W2", "display_name": "Migraine preprint",
            "publication_year": 2024, "type": "preprint", "doi": "",
            "abstract_inverted_index": {"New": [0], "findings": [1]},
            "primary_location": {"source": {"display_name": "bioRxiv"}},
        },
        {  # no doi AND no usable url-ish id once doi empty? id present → resolvable; keep.
            "id": "https://openalex.org/W3", "display_name": "Has id only",
            "publication_year": 2019, "type": "journal-article", "doi": "",
            "abstract_inverted_index": {"X": [0]},
            "primary_location": {"source": {"display_name": "J"}},
        },
    ]
}).encode()

EUROPEPMC = json.dumps({
    "resultList": {"result": [
        {  # same DOI as OpenAlex W1 → must dedup to one record.
            "id": "PMID1", "pmid": "111", "title": "Dup via DOI", "abstractText": "a",
            "pubYear": "2021", "journalTitle": "J", "pubType": "journal article",
            "doi": "10.1/dup", "source": "MED",
        },
    ]}
}).encode()

ARXIV = (
    b'<feed xmlns="http://www.w3.org/2005/Atom">'
    b"<entry>"
    b"<id>http://arxiv.org/abs/2401.00001v1</id>"
    b"<title>Arxiv migraine paper</title>"
    b"<summary>Some summary</summary>"
    b"<published>2024-01-02T00:00:00Z</published>"
    b"</entry>"
    b"</feed>"
)


def fake_fetch(url: str) -> bytes:
    if "openalex.org" in url:
        return OPENALEX
    if "europepmc" in url:
        return EUROPEPMC
    if "arxiv.org" in url:
        return ARXIV
    raise AssertionError(f"unexpected url {url}")


CRITERIA = {"id": "req1", "topic": "migraine", "terms": ["migraine"],
            "filters": {"max_results": 50, "from_year": 2015, "publication_types": []}}


def test_aggregate_dedups_and_orders_by_evidence():
    result = agg.aggregate(CRITERIA, fake_fetch)
    papers = result["papers"]
    titles = [p["title"] for p in papers]

    # The DOI-shared OpenAlex review and EuropePMC record collapse to ONE.
    dup = [p for p in papers if (p.get("doi") or "").lower() == "10.1/dup"]
    assert len(dup) == 1
    # The systematic review ranks first (highest evidence); arXiv preprint last.
    assert "systematic review" in titles[0].lower()
    assert papers[-1]["is_preprint"] is True
    assert set(result["sources_queried"]) == {"openalex", "europepmc", "arxiv"}


def test_unresolvable_records_are_dropped():
    # W2 has no doi and no url? Its url falls back to its OpenAlex id → resolvable, kept.
    # Build a criteria where a source yields a truly id-less record to prove the drop.
    def only_bad(url):
        if "openalex" in url:
            return json.dumps({"results": [
                {"display_name": "no ids", "type": "review", "doi": "",
                 "abstract_inverted_index": {"x": [0]}},
            ]}).encode()
        return json.dumps({"resultList": {"result": []}}).encode()

    result = agg.aggregate(CRITERIA, only_bad, sources=["openalex", "europepmc"])
    assert result["papers"] == []  # no doi, no url → unresolvable → dropped (honesty §III.1)


def test_one_failing_source_does_not_sink_the_gather():
    def flaky(url):
        if "openalex" in url:
            raise RuntimeError("boom")
        if "europepmc" in url:
            return EUROPEPMC
        return ARXIV
    result = agg.aggregate(CRITERIA, flaky)
    assert "openalex" not in result["sources_queried"]
    assert result["papers"]  # europepmc + arxiv still returned


class FakeS3:
    def __init__(self, request_obj):
        self.objects = {"requests/req1.json": json.dumps(request_obj).encode()}
        self.puts: dict[str, bytes] = {}

    def get_object(self, *, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key])}

    def put_object(self, *, Bucket, Key, Body, **kw):
        self.puts[Key] = Body


def test_handle_event_reads_request_and_writes_results():
    s3 = FakeS3(CRITERIA)
    event = {"Records": [{"s3": {
        "bucket": {"name": "b"}, "object": {"key": "requests/req1.json"},
    }}]}
    written = handler_mod.handle_event(event, s3, fake_fetch)
    assert written == ["results/req1.json"]
    out = json.loads(s3.puts["results/req1.json"])
    assert out["criteria_id"] == "req1"
    assert out["papers"]
    assert "ts" in out


@pytest.fixture(autouse=True)
def _cleanup_syspath():
    yield
    if str(FETCHER_DIR) in sys.path:
        sys.path.remove(str(FETCHER_DIR))
