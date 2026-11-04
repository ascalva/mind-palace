"""Curated literature in the Ambassador's reach (dn-external-grounding §2.2).

The literature lives in its OWN store, physically apart from the mirror. Proves: a sentence whose
Σ admits CURATED reads that store too, merged with the main store by distance; a mirror-only
sentence never touches it; and `read` of a `reference:` ref returns a window of the paper around
the hit's chunk — a whole paper would not fit a model's context.
"""

from __future__ import annotations

from typing import Any

import pytest

from agents.ambassador.mcp import Ambassador
from core.kernel.clearance import Clearance
from core.kernel.provenance import Provenance
from core.kernel.scope import Stratum
from core.query import AMBASSADOR, Query, QueryEngine, Verb
from core.sentence import surface
from core.sentence.precedents import DEFAULT
from core.sentence.surface import QueryLog

PAPER = "reference:openai-math:Local-smoothing"


class _Store:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows, self.calls = rows, 0

    def search(self, vector: list[float], *, k: int = 5, clearance: Clearance[Provenance],
               include_superseded: bool = False) -> list[dict[str, Any]]:
        self.calls += 1
        hits = [r for r in self.rows if clearance.admits(r["provenance"])]
        return sorted(hits, key=lambda r: r["_distance"])[:k]

    def rows_for_source(self, source_path: str, *,
                        clearance: Clearance[Provenance]) -> list[dict[str, Any]]:
        return [r for r in self.rows
                if r["source_path"] == source_path and clearance.admits(r["provenance"])]


class _Embedder:
    def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0]


def _row(src: str, prov: str, dist: float = 0.0, chunk: int = 0, text: str = "t") -> dict[str, Any]:
    return {"source_path": src, "title": src, "provenance": prov, "_distance": dist,
            "chunk_index": chunk, "text": text}


def _engine(main: list[dict[str, Any]], lit: list[dict[str, Any]]) -> tuple[QueryEngine, _Store]:
    eng, store = QueryEngine(), _Store(lit)
    eng._cache.update({"vectors": _Store(main), "curated": store, "embedder": _Embedder()})
    return eng, store


def test_a_curated_sentence_reads_the_literature_store_merged_by_distance():
    far = _row("reference:openai-math:y", "curated", 0.5)
    eng, lit = _engine([_row("note-a", "authored-solo", 0.30)], [_row(PAPER, "curated", 0.10), far])
    ans = eng.ask(Query(Verb.SEARCH, AMBASSADOR, text="kakeya", k=2,
                        strata=(Stratum.CURATED, Stratum.MIRROR_AUTHORED))).to_dict()
    assert [h["ref"] for h in ans["hits"]] == [PAPER, "note-a"]   # closest first, both stores
    assert lit.calls == 1


def test_a_mirror_sentence_never_touches_the_literature_store():
    eng, lit = _engine([_row("note-a", "authored-solo", 0.3)], [_row(PAPER, "curated", 0.1)])
    ans = eng.ask(Query(Verb.SEARCH, AMBASSADOR, text="x", k=2,
                        strata=(Stratum.MIRROR_AUTHORED,))).to_dict()
    assert [h["ref"] for h in ans["hits"]] == ["note-a"]
    assert lit.calls == 0


def test_reading_a_paper_returns_a_window_around_the_hit(monkeypatch, tmp_path):
    """`read "<paper>" chunk n` through the one command: a window of `read_window` chunks around
    the chunk, from the start when none is given; the curated store is the only store opened."""
    monkeypatch.setattr(surface, "default_log", lambda: QueryLog(tmp_path / "q.jsonl"))
    amb = Ambassador()
    amb.engine._cache["curated"] = _Store(
        [_row(PAPER, "curated", chunk=i, text=f"c{i}") for i in reversed(range(20))])
    (hit,) = amb.query(f'read "{PAPER}" chunk 10')["hits"]
    w = DEFAULT.read_window
    assert hit["text"].split("\n") == [f"c{i}" for i in range(8, 8 + w)]
    assert hit["detail"]["chunks"] == f"8–{8 + w - 1} of 20" and hit["provenance"] == "curated"
    assert amb.query(f'read "{PAPER}"')["hits"][0]["text"].startswith("c0\nc1")
    assert set(amb.engine._cache) == {"curated"}             # no note graph for a bare read


def test_note_graph_verbs_refuse_a_paper_and_say_where_to_go(monkeypatch, tmp_path):
    """A paper's ref handed to a verb over the owner's notes is refused with directions at compile
    time, before any store opens; never a bare LookupError, never an empty "0 hits" that reads as
    no history (the legacy table's `OutOfScopeTarget`, now a sort error of the sentence)."""
    from core.sentence import SortError

    monkeypatch.setattr(surface, "default_log", lambda: QueryLog(tmp_path / "q.jsonl"))
    amb = Ambassador()
    ref = "reference:openai-math:A-counterexample-to-Hadwigers-conjecture-September-23-2026"
    for sentence in (f'relate "{ref}"', f'trace "{ref}"', f'top 5 diffuse S from "{ref}"',
                     f'near "x" and diffuse S from "{ref}"', f'walk from "a" to "{ref}" via F+'):
        with pytest.raises(SortError, match="over curated"):
            amb.query(sentence)
    assert amb.engine._cache == {}                       # refused before any store opened
    assert all(e.refusal == "sort" for e in QueryLog(tmp_path / "q.jsonl").entries())
