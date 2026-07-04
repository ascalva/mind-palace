"""Founding-corpus ingest — build plan Item 3 (founding-corpus.md).

The founding corpus is a DATED, SUPERSESSION-LINKED sequence ingested through the SAME steady-state
path as vault ingest (no bespoke writer — §4/Q3), as AUTHORED_SOLO (the mirror's ground truth), kept
mechanically distinct from the Track-L control corpus (§2.3). Deterministic; offline embedder.
"""

from __future__ import annotations

import pytest

from core.ingest.founding import (
    ForwardSupersession,
    FoundingItem,
    UndatedFoundingItem,
    ingest_founding,
)
from core.ingest.index import index_records, semantic_search
from core.ingest.logseq import parse_text
from core.ingest.pipeline import ingest_note
from core.provenance import MIRROR_READABLE, Provenance
from core.recursion_ops import ClaimOpStore
from core.stores.catalog import VaultCatalog
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from tests.fixtures.embedding import DIM, FakeEmbedder


def _stores(tmp_path):
    return (RawStore(tmp_path / "raw"), VectorStore(tmp_path / "v.lance", dim=DIM),
            VaultCatalog(tmp_path / "cat.sqlite"), ClaimOpStore(tmp_path / "ops.sqlite"))


def _items():
    return [
        FoundingItem("m/1", "early view", "beekeeping needs a top-bar hive", "2019-03-15"),
        FoundingItem("m/2", "revised view", "beekeeping is better with a Langstroth hive",
                     "2021-07-02", supersedes="m/1"),
    ]


def test_founding_ingests_through_the_shared_path_as_authored_solo(tmp_path):
    raw, store, catalog, ops = _stores(tmp_path)
    report = ingest_founding(_items(), raw, store, FakeEmbedder(), catalog, ops_store=ops)
    assert report.ingested == 2 and report.chunks >= 2

    # AUTHORED_SOLO + mirror-readable + retrievable — the shared path, not a bespoke writer.
    rows = store.all_rows(provenances=MIRROR_READABLE)
    assert rows and all(r["provenance"] == Provenance.AUTHORED_SOLO.value for r in rows)
    hits = semantic_search("Langstroth hive", FakeEmbedder(), store)
    assert any("Langstroth" in h["text"] for h in hits)

    # No bespoke writer: the stored digest is exactly what `ingest_note` produces for the same text.
    text = "date:: 2019-03-15\n\nbeekeeping needs a top-bar hive"
    parsed = parse_text(text, source_path="m/1", title="early view", raw_bytes=text.encode())
    expected = ingest_note(parsed, RawStore(tmp_path / "raw2")).digest
    assert any(r["digest"] == expected for r in store.all_rows())


def test_dates_land_in_the_raw_note_permanently(tmp_path):
    raw, store, catalog, ops = _stores(tmp_path)
    ingest_founding(_items()[:1], raw, store, FakeEmbedder(), catalog, ops_store=ops)
    # The date is recorded IN the content-addressed raw blob — re-parsing it recovers the date.
    entry = catalog.active_entries()[0]
    reparsed = parse_text(raw.get(entry.digest).decode(), source_path="x", title="x", raw_bytes=b"")
    assert reparsed.properties["date"] == "2019-03-15"


def test_supersession_is_recorded_between_authored_musings(tmp_path):
    raw, store, catalog, ops = _stores(tmp_path)
    ingest_founding(_items(), raw, store, FakeEmbedder(), catalog, ops_store=ops)
    # m/2 supersedes m/1 → m/1's digest is superseded in the ClaimOpStore (a RELATION, authored).
    d1 = next(e.digest for e in catalog.active_entries() if e.source_path == "m/1")
    assert d1 in ops.superseded() and ops.count() == 1


def test_undated_item_is_refused(tmp_path):
    raw, store, catalog, _ = _stores(tmp_path)
    with pytest.raises(UndatedFoundingItem):
        ingest_founding([FoundingItem("m/x", "t", "body", "  ")], raw, store,
                        FakeEmbedder(), catalog)


def test_forward_supersession_is_refused(tmp_path):
    raw, store, catalog, ops = _stores(tmp_path)
    bad = [FoundingItem("m/1", "t", "body", "2019-01-01", supersedes="m/future")]
    with pytest.raises(ForwardSupersession):
        ingest_founding(bad, raw, store, FakeEmbedder(), catalog, ops_store=ops)


def test_founding_is_mechanically_distinct_from_a_curated_control(tmp_path):
    # §2.3: founding is AUTHORED_SOLO (mirror); a control corpus is CURATED (never the mirror). One
    # store holds both, provenance-separated — so founding can never double as the control.
    raw, store, catalog, ops = _stores(tmp_path)
    ingest_founding(_items(), raw, store, FakeEmbedder(), catalog, ops_store=ops)
    ctrl = ingest_note(parse_text("a literary probe passage", source_path="ctrl/1", title="ctrl",
                                  raw_bytes=b"a literary probe passage"),
                       raw, provenance=Provenance.CURATED)
    index_records([ctrl], FakeEmbedder(), store)
    mirror = store.all_rows(provenances=MIRROR_READABLE)
    assert mirror and all(r["provenance"] == Provenance.AUTHORED_SOLO.value for r in mirror)
    assert not any(r["provenance"] == Provenance.CURATED.value for r in mirror)   # control ∉ mirror
