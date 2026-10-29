"""Curated literature in the Ambassador's reach (dn-external-grounding §2.2).

The literature lives in its OWN store, physically apart from the mirror. Proves: a sentence whose
Σ admits CURATED reads that store too, merged with the main store by distance; a mirror-only
sentence never touches it; and `read` of a `reference:` ref returns a window of the paper around
the hit's chunk — a whole paper would not fit a model's context.
"""

from __future__ import annotations

from typing import Any

import pytest

from agents.ambassador.mcp import _READ_WINDOW, Ambassador
from core.kernel.provenance import Provenance
from core.kernel.scope import Stratum
from core.query import AMBASSADOR, Query, QueryEngine, Verb

PAPER = "reference:openai-math:Local-smoothing"


class _Store:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows, self.calls = rows, 0

    def search(self, vector: list[float], *, k: int = 5, provenances: Any = None,
               include_superseded: bool = False) -> list[dict[str, Any]]:
        self.calls += 1
        allowed = None if provenances is None else {Provenance(p).value for p in provenances}
        hits = [r for r in self.rows if allowed is None or r["provenance"] in allowed]
        return sorted(hits, key=lambda r: r["_distance"])[:k]

    def rows_for_source(self, source_path: str) -> list[dict[str, Any]]:
        return [r for r in self.rows if r["source_path"] == source_path]


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


def test_reading_a_paper_returns_a_window_around_the_hit():
    amb = Ambassador()
    amb.engine._cache["curated"] = _Store(
        [_row(PAPER, "curated", chunk=i, text=f"c{i}") for i in reversed(range(20))])
    out = amb.read(PAPER, chunk=10)
    assert out["text"].split("\n") == [f"c{i}" for i in range(8, 8 + _READ_WINDOW)]
    assert out["chunks"] == f"8–{8 + _READ_WINDOW - 1} of 20" and out["provenance"] == "curated"
    assert amb.read(PAPER)["text"].startswith("c0\nc1")


def test_note_graph_verbs_refuse_a_paper_and_say_where_to_go():
    """A paper's ref handed to a verb over the owner's notes is refused with directions, before
    any store opens; never a bare LookupError, never an empty "0 hits" that reads as no history."""
    from agents.ambassador.mcp import Ambassador
    from core.query import OutOfScopeTarget

    amb = Ambassador()
    ref = "reference:openai-math:A-counterexample-to-Hadwigers-conjecture-September-23-2026"
    calls = (lambda: amb.related(ref), lambda: amb.history(ref),
             lambda: amb.neighbors(ref, beta=1.0, k=5), lambda: amb.hybrid("x", ref, beta=1.0, k=5))
    for call in calls:
        with pytest.raises(OutOfScopeTarget, match=r'strata \["curated"\]'):
            call()
    assert amb.engine._cache == {}                       # refused before any store opened
