"""The corpus bulk path (dn-corpus-instance §5.2): `sync_corpus.palace` lands a stream a batch past
its cursor through the ingress, a stage at a time across the batch, and converges.

The laws it is checked against: ING-5 (a re-fetched text embeds nothing), ING-7 (the key last),
ING-9 and ING-11 (a batch on distinct identities cut off anywhere lands the uninterrupted batch
when run again), ING-15 (the corpus role writes its own space alone); and the design's CIF-6 (a
batch interrupted and re-run that lands a different state is a defect in the lander).
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from core.ingest import stream
from core.ingest.readers import PalaceView
from core.ingest.table import build_table
from core.ingest.writer import batchable
from core.kernel.clearance import OBSERVED_READ as EVERY_OBSERVED
from core.sentence.interpret import Content, Naming, ScriptError, StoreEff
from edge.corpus.stream import StreamWriter
from tests.fixtures.ingress import Palace, palace_at, state_of


def _corpus(p: Palace) -> Palace:
    """The palace with two corpus streams, `alpha` and `beta`, under its root."""
    corpus = replace(p.cfg.ingestion.corpus, enabled=True, root=p.root / "sources",
                     sources=("alpha", "beta"))
    p.cfg = replace(p.cfg, ingestion=replace(p.cfg.ingestion, corpus=corpus))
    return p


def _fill(p: Palace, name: str, n: int, *, start: int = 0, part_bytes: int = 400,
          text: str = "item {i} of {name}: a paragraph of open text, long enough to chunk."
          ) -> None:
    w = StreamWriter(p.root / "sources" / name, part_bytes=part_bytes)
    for i in range(start, start + n):
        w.append(f"{name}-{i}", f"{name} {i}", text.format(i=i, name=name) * 3,
                 meta={"date": f"2020-01-{1 + i % 28:02d}"})
    w.close()


def _sync(p: Palace, name: str, batch: int, *, batched: bool = True) -> dict[str, Any]:
    from core.ingest import ingress
    from core.sentence import ast
    from core.sentence.plan import compile_sentence

    text = f'do sync_corpus(name: "{name}", batch: {batch})'
    plan = compile_sentence(text, ingress.grant_for("corpus"), role="corpus")
    assert isinstance(plan.term, ast.Do)
    view = PalaceView(build_table(p.cfg), "corpus", p.stores.catalog, refresh=False)
    return ingress.perform(plan.term, p.cfg, "corpus", stores=p.stores, view=view, batch=batched)


@pytest.fixture
def palace(tmp_path: Path) -> Palace:
    return _corpus(palace_at(tmp_path))


def test_a_stream_lands_a_batch_past_its_cursor_and_the_cursor_follows(palace):
    _fill(palace, "alpha", 7)
    d = palace.root / "sources" / "alpha"
    assert stream.last_seq(d) == 7 and stream.cursor(d) == 0
    assert _sync(palace, "alpha", 3)["effects"] == {"landed": 3}
    assert stream.cursor(d) == 3
    assert _sync(palace, "alpha", 3)["effects"] == {"landed": 3}
    assert _sync(palace, "alpha", 3)["effects"] == {"landed": 1}
    assert stream.cursor(d) == 7
    assert _sync(palace, "alpha", 3)["effects"] == {}            # drained: nothing read
    paths = {e.source_path for e in palace.stores.catalog.active_entries()}
    assert paths == {f"corpus/alpha/alpha-{i}" for i in range(7)}
    assert {str(e.provenance) for e in palace.stores.catalog.active_entries()} == {"observed"}


def test_the_batched_landing_lands_what_the_effect_by_effect_landing_lands(tmp_path):
    a, b = _corpus(palace_at(tmp_path, "a")), _corpus(palace_at(tmp_path, "b"))
    for p in (a, b):
        _fill(p, "alpha", 6)
        _fill(p, "beta", 4, text="{name} {i}: the same shared sentence in every item.")
    for name in ("alpha", "beta"):
        assert _sync(a, name, 10, batched=True)["effects"] == \
            _sync(b, name, 10, batched=False)["effects"]
    assert state_of(a) == state_of(b)


@pytest.mark.parametrize("stage", ["derive", "index", "attest", "key"])
def test_a_batch_cut_off_at_any_stage_lands_the_uninterrupted_batch_when_run_again(
        tmp_path, monkeypatch, stage):
    """CIF-6 on the code: the batch dies inside each of its stages (after the first raw object,
    in the plane's landing, at a store's attestation step, at its third key), and the request run
    again lands exactly what an uninterrupted run lands, the cursor moving only then."""
    whole, cut = _corpus(palace_at(tmp_path, "whole")), _corpus(palace_at(tmp_path, "cut"))
    for p in (whole, cut):
        _fill(p, "alpha", 5)
    _sync(whole, "alpha", 5)
    from core.ingest import writer as writer_mod

    calls = {"n": 0}

    def dies(after: int) -> Any:
        def boom(*a: Any, **k: Any) -> Any:
            calls["n"] += 1
            if calls["n"] > after:
                raise RuntimeError(f"killed in {stage}")
            return real(*a, **k)
        return boom
    if stage == "derive":
        real = writer_mod.ingest_note
        monkeypatch.setattr(writer_mod, "ingest_note", dies(1))
    elif stage == "index":
        real = cut.stores.plane.add
        monkeypatch.setattr(cut.stores.plane, "add", dies(0))
    elif stage == "attest":
        assert cut.stores.attestor is not None
        real = cut.stores.attestor.emit
        monkeypatch.setattr(cut.stores.attestor, "emit", dies(1))
    else:
        real = cut.stores.catalog.record
        monkeypatch.setattr(cut.stores.catalog, "record", dies(2))
    with pytest.raises(RuntimeError):
        _sync(cut, "alpha", 5)
    d = cut.root / "sources" / "alpha"
    assert stream.cursor(d) == 0, "the cursor moves only once the batch has landed"
    monkeypatch.undo()
    _sync(cut, "alpha", 5)
    assert state_of(cut) == state_of(whole)
    assert stream.cursor(d) == 5
    assert _sync(cut, "alpha", 5)["effects"] == {}


def test_a_text_the_plane_holds_embeds_nothing_again(palace, monkeypatch):
    """ING-5: an item re-fetched under a new id with a text the plane holds costs no embed."""
    _fill(palace, "alpha", 3, text="one fixed text that every item carries")
    texts: list[str] = []
    real = palace.stores.embedder.embed_documents

    def counted(ts: list[str]) -> list[list[float]]:
        texts.extend(ts)
        return real(ts)
    monkeypatch.setattr(palace.stores.embedder, "embed_documents", counted)
    _sync(palace, "alpha", 10)
    first = len(texts)
    _fill(palace, "alpha", 2, start=3, text="one fixed text that every item carries")
    _sync(palace, "alpha", 10)
    assert first == 1 and len(texts) == first, "the shared chunk was embedded once"


def test_the_corpus_role_writes_its_own_space_and_no_other(palace):
    """ING-15: the corpus role's prefix is `corpus/` in the observed place; a store elsewhere or
    in another place is refused by its rule, and the rest of the plan lands."""
    from core.ingest.ingress import grant_for
    from core.sentence import ast
    from core.sentence.plan import compile_sentence

    _fill(palace, "alpha", 1)
    text = ('do { for it in items(source("corpus/" + "alpha")) { store it.content in "observed" '
            'at "dialogue/ingress/corpus/x" } }')
    plan = compile_sentence(text, grant_for("corpus"), role="corpus")
    assert isinstance(plan.term, ast.Do)
    from core.ingest import ingress
    view = PalaceView(build_table(palace.cfg), "corpus", palace.stores.catalog, refresh=False)
    out = ingress.perform(plan.term, palace.cfg, "corpus", stores=palace.stores, view=view,
                          batch=True)
    assert out["effects"] == {"refused": 1}
    assert out["changed"][0]["why"].startswith("R3")
    assert stream.cursor(palace.root / "sources" / "alpha") == 0, \
        "an item the plan did not store at its own path keeps the cursor where it was"


def test_only_a_stream_takes_a_batch_and_a_batch_is_bounded(palace):
    _fill(palace, "alpha", 2)
    with pytest.raises(ScriptError, match="batch"):
        _sync(palace, "alpha", 0)
    from core.ingest.ingress import grant_for
    from core.sentence.plan import compile_sentence

    with pytest.raises(ScriptError, match="integer"):
        compile_sentence('do { for it in items(source("corpus/" + "alpha"), batch: "x") '
                         '{ store it.content in "observed" } }', grant_for("corpus"),
                         role="corpus")
    with pytest.raises(ScriptError, match="takes no argument"):
        compile_sentence('do { for it in files(source("corpus/" + "alpha"), batch: 2) '
                         '{ store it.content in "observed" } }', grant_for("corpus"),
                         role="corpus")


def test_batchable_is_stores_of_their_own_identities_on_distinct_paths():
    c = Content(b"x", "observed", None)
    own = Naming("own")
    a = StoreEff("p/a", c, "observed", own, "a")
    b = StoreEff("p/b", c, "observed", own, "b")
    assert batchable([a, b])
    assert not batchable([a, a])                                   # one path twice
    assert not batchable([a, replace(b, naming=Naming("named", "p/b"))])
    assert not batchable([])


def test_the_lander_reads_only_whole_parts_and_the_edge_writer_resumes_after_them(tmp_path):
    d = tmp_path / "s"
    w = StreamWriter(d, part_bytes=10**9)
    w.append("a", "A", "first")
    w.close_part()
    w.append("b", "B", "second")             # an open part: written, not yet named
    w._fh.flush()
    assert [x["id"] for x in stream.read_items(d)] == ["a"]
    w2 = StreamWriter(d)                       # a reader cut off mid-part resumes
    assert w2.ids == {"a"} and w2.next_seq == 2
    w2.append("b", "B", "second")
    w2.close()
    assert [x["id"] for x in stream.read_items(d, after=1)] == ["b"]
    lines = (d / "meta" / "items.jsonl").read_text().splitlines()
    meta = [json.loads(line)["id"] for line in lines]
    assert meta == ["a", "b"]
    with pytest.raises(ValueError):
        w3 = StreamWriter(d)
        w3.append("a", "A", "again")           # an id the stream holds is refused


def test_the_cursor_moves_only_forward(tmp_path):
    d = tmp_path / "s"
    d.mkdir()
    stream.write_cursor(d, 3)
    with pytest.raises(stream.StreamError):
        stream.write_cursor(d, 2)
    assert stream.cursor(d) == 3


def _sync_structural(p: Palace, name: str, batch: int) -> dict[str, Any]:
    from core.ingest import ingress
    from core.sentence import ast
    from core.sentence.plan import compile_sentence

    plan = compile_sentence(f'do sync_corpus(name: "{name}", batch: {batch})',
                            ingress.grant_for("corpus"), role="corpus")
    assert isinstance(plan.term, ast.Do)
    view = PalaceView(build_table(p.cfg), "corpus", p.stores.catalog, refresh=False)
    return ingress.perform(plan.term, p.cfg, "corpus", stores=p.stores, view=view, batch=True,
                           vectors=False)


def test_the_structural_phase_lands_keys_and_the_vector_phase_adds_the_rows(tmp_path):
    """Two phases (the structural phase lands every item's raw object, attestation and key and
    embeds nothing; the vector phase derives the plane rows from the raw store) end where one
    landing ends; between them the plane holds no row of the landed items, so a reader that needs
    a vector finds them pending, never guessed."""
    from core.ingest.index import index_from_raw
    from core.kernel.provenance import Provenance

    one, two = _corpus(palace_at(tmp_path, "one")), _corpus(palace_at(tmp_path, "two"))
    for p in (one, two):
        _fill(p, "alpha", 6)
    _sync(one, "alpha", 10)
    embedded: list[str] = []
    real = two.stores.embedder.embed_documents

    def counted(ts: list[str]) -> list[list[float]]:
        embedded.extend(ts)
        return real(ts)
    two.stores.embedder.embed_documents = counted     # type: ignore[method-assign]
    assert _sync_structural(two, "alpha", 10)["effects"] == {"landed": 6}
    assert embedded == [], "the structural phase embeds nothing"
    keyed = [(e.source_path, e.digest, e.title) for e in two.stores.catalog.active_entries()]
    assert len(keyed) == 6
    assert not any(two.stores.plane.holds_current(path, digest, clearance=EVERY_OBSERVED)
                   for path, digest, _ in keyed), "no row before the vector phase: pending"
    assert _sync_structural(two, "alpha", 10)["effects"] == {}       # the cursor moved
    index_from_raw(keyed, two.stores.raw, two.stores.embedder, two.stores.plane,
                   provenance=Provenance.OBSERVED)
    assert state_of(two) == state_of(one)
