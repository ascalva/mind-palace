"""Persist ranked open-access keepers into the curated store (bp-029 Item 29) — licence-gated.

Deterministic: a HashingEmbedder fake (no Ollama) + a temp curated store. Pins that an
open-access keeper is chunked/embedded with `provenance="curated"`, that a keeper WITHOUT a clear
open-access basis is SKIPPED (DISTILLED-only — the Item-29 falsifier), that curated rows never
enter the mirror, and that `store_ref` is content-addressed.
"""

from __future__ import annotations

from typing import cast

from core.ingest.embed import Embedder
from core.provenance import MIRROR_READABLE, Provenance
from core.research.criteria import Paper
from core.research.persist import persist_keepers
from core.research.rank import RankedPaper
from core.stores.vectorstore import VectorStore
from tests.fixtures.fakes import HashingEmbedder

DIM = 8
FULL_TEXT = "The reproducing kernel Hilbert space is the crux. " * 20  # a few sentences → chunk(s)


def _ranked(*, open_access: bool, full_text: str | None, source: str = "europepmc",
            pid: str = "p1") -> RankedPaper:
    paper = Paper(
        source=source, id=pid, title="A paper", abstract="abs", year=2020, venue="J",
        type="review", doi=f"10.1/{pid}", url="https://doi.org/x", is_preprint=False,
        open_access=open_access, full_text=full_text,
    )
    return RankedPaper(paper=paper, relevance=0.9, evidence_tier="high", score=0.9, flags=())


def _store(tmp_path) -> VectorStore:
    return VectorStore(tmp_path / "curated.lance", dim=DIM)


def _embedder() -> Embedder:
    return cast(Embedder, HashingEmbedder(DIM))


def test_open_access_keeper_is_embedded_as_curated(tmp_path):
    store = _store(tmp_path)
    records = persist_keepers([_ranked(open_access=True, full_text=FULL_TEXT)], _embedder(), store)
    assert len(records) == 1
    rec = records[0]
    assert rec.n_chunks >= 1
    assert rec.paper_source == "europepmc"        # the manifest venue
    assert rec.store_ref and len(rec.store_ref) == 64  # sha256 hex

    rows = store.all_rows()
    assert len(rows) == rec.n_chunks
    assert {row["provenance"] for row in rows} == {"curated"}
    assert all(row["source_path"] == "reference:europepmc:p1" for row in rows)
    assert all(row["digest"] == rec.store_ref for row in rows)


def test_keeper_without_open_access_full_text_is_skipped(tmp_path):
    store = _store(tmp_path)
    ranked = [
        _ranked(open_access=False, full_text=FULL_TEXT, pid="noflag"),   # text but not OA-flagged
        _ranked(open_access=True, full_text=None, pid="notext"),         # OA but no full text
        _ranked(open_access=True, full_text="   ", pid="blank"),         # OA but empty text
    ]
    records = persist_keepers(ranked, _embedder(), store)
    assert records == []                 # none clear the default-DENY licence gate
    assert store.count() == 0            # nothing embedded — all stay DISTILLED-only


def test_mixed_batch_embeds_only_the_open_access_keeper(tmp_path):
    store = _store(tmp_path)
    ranked = [
        _ranked(open_access=True, full_text=FULL_TEXT, pid="ok"),
        _ranked(open_access=False, full_text=FULL_TEXT, pid="skip"),
    ]
    records = persist_keepers(ranked, _embedder(), store)
    assert [r.paper_id for r in records] == ["ok"]
    assert all(row["source_path"] == "reference:europepmc:ok" for row in store.all_rows())


def test_curated_rows_never_enter_the_mirror(tmp_path):
    store = _store(tmp_path)
    persist_keepers([_ranked(open_access=True, full_text=FULL_TEXT)], _embedder(), store)
    assert store.all_rows(provenances=MIRROR_READABLE) == []          # firewall: curated ∉ mirror
    query = [1.0] + [0.0] * (DIM - 1)
    assert store.search(query, k=5, provenances=MIRROR_READABLE) == []
    assert store.search(query, k=5, provenances={Provenance.CURATED})  # curated query finds them


def test_store_ref_is_content_addressed(tmp_path):
    a = persist_keepers([_ranked(open_access=True, full_text=FULL_TEXT, pid="a")],
                        _embedder(), _store(tmp_path / "a"))
    b = persist_keepers([_ranked(open_access=True, full_text=FULL_TEXT, pid="b")],
                        _embedder(), _store(tmp_path / "b"))
    c = persist_keepers([_ranked(open_access=True, full_text=FULL_TEXT + " more", pid="c")],
                        _embedder(), _store(tmp_path / "c"))
    assert a[0].store_ref == b[0].store_ref       # same text → same ref (deterministic join)
    assert a[0].store_ref != c[0].store_ref       # different text → different ref
