"""The stratified universe (`core/sentence/universe.py`, dn-query-sentence-algebra §2.9): the
seeds a sentence names, the support built from the mirror, the dialogue, the curated index, the
code index resolved through the memberships, and the citation graph at the cut — with the newest-cut
fallback, the support bound, `over` as a mask and `read` of a repo file. Hermetic: store fakes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import pytest

from core.kernel.config import get_config
from core.kernel.scope import Stratum
from core.query import AMBASSADOR_OVERLAY, QueryEngine
from core.sentence import compile_sentence, execute
from core.sentence.ast import Rel
from core.sentence.precedents import DEFAULT, Precedents
from core.sentence.universe import build, is_repo_path, seeds_of
from core.stores.memberships import Membership

DIM = int(get_config().embedding.dim)


def _vec(*hot: int) -> list[float]:
    v = np.zeros(DIM)
    for h in hot:
        v[h] = 1.0
    return list(v / np.linalg.norm(v))


@dataclass
class _Edge:
    source_ref: str
    target_ref: str
    commit_sha: str
    source_kind: str = "corpus"
    target_kind: str = "corpus"


class _Refs:
    def __init__(self, edges: list[_Edge]) -> None:
        self.edges = edges

    def for_commit(self, sha: str) -> list[_Edge]:
        return [e for e in self.edges if e.commit_sha == sha]

    def latest_commit(self) -> str | None:
        return max((e.commit_sha for e in self.edges), default=None)   # c1 is newer than c0

    def commits_like(self, prefix: str) -> list[str]:
        return sorted({e.commit_sha for e in self.edges if e.commit_sha.startswith(prefix)})[:2]

    def all(self, *, source_ref: str | None = None, target_ref: str | None = None,
            commit_sha: str | None = None, **_: Any) -> list[_Edge]:
        return [e for e in self.edges
                if (source_ref is None or e.source_ref == source_ref)
                and (target_ref is None or e.target_ref == target_ref)
                and (commit_sha is None or e.commit_sha == commit_sha)]


class _Vectors:
    def __init__(self, dialogue: list[dict[str, Any]], atoms: list[dict[str, Any]]) -> None:
        self.dialogue, self.atoms, self.searches = dialogue, atoms, 0

    def all_rows(self, *, clearance: Any, **_: Any) -> list[dict[str, Any]]:
        return list(self.dialogue)

    def search(self, vector: list[float], *, k: int, clearance: Any,
               **_: Any) -> list[dict[str, Any]]:
        self.searches += 1
        q = np.asarray(vector)
        scored = [(1 - float(q @ np.asarray(r["vector"])), r) for r in self.atoms]
        return [{**r, "_distance": d} for d, r in sorted(scored, key=lambda t: t[0])[:k]]


class _Curated:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows, self.searches = rows, 0

    def search(self, vector: list[float], *, k: int, clearance: Any,
               **_: Any) -> list[dict[str, Any]]:
        self.searches += 1
        q = np.asarray(vector)
        scored = [(1 - float(q @ np.asarray(r["vector"])), r) for r in self.rows]
        return [{**r, "_distance": d} for d, r in sorted(scored, key=lambda t: t[0])[:k]]

    def rows_for_source(self, src: str, *, clearance: Any) -> list[dict[str, Any]]:
        return [r for r in self.rows if r["source_path"] == src]


class _Memberships:
    def __init__(self, places: dict[str, list[tuple[str, str, int, int]]]) -> None:
        self.places = places

    def occupancies(self, cid: str, *, include_superseded: bool = False) -> list[Membership]:
        return [Membership(path=p, blob_sha="b", layer="L1", chunk_index=0, content_id=cid, slot=s,
                           slot_line_start=a, slot_line_end=b, current=True)
                for p, s, a, b in self.places.get(cid, [])]


class _Engine:
    def __init__(self, *, refs: _Refs, vectors: _Vectors, curated: _Curated,
                 memberships: _Memberships, embed: Mapping[str, list[float]]) -> None:
        self.config = get_config()
        self._cache: dict[str, Any] = {
            "references": refs, "vectors": vectors, "curated": curated, "memberships": memberships,
            "embedder": type("E", (), {"embed_query": staticmethod(lambda t: embed[t])})(),
            "edges": type("R", (), {"all": staticmethod(lambda: [])})(),
            "catalog": type("C", (), {"get": staticmethod(lambda a: None),
                                     "doc_id_for": staticmethod(lambda a: a)})(),
            "versions": type("V", (), {"history": staticmethod(lambda d: [])})(),
            "causal": object(),
        }

    def _get(self, name: str) -> Any:
        return self._cache[name]

    def _note_graph(self) -> tuple[list[dict[str, Any]], np.ndarray, np.ndarray]:
        notes = [{"source_path": "/v/a.md", "title": "A", "digest": "da",
                  "provenance": "authored-solo"},
                 {"source_path": "/v/b.md", "title": "B", "digest": "db",
                  "provenance": "authored-solo"}]
        mat = np.asarray([_vec(0), _vec(1)])
        return notes, mat, np.zeros((2, 2))


@pytest.fixture
def engine(monkeypatch: pytest.MonkeyPatch) -> _Engine:
    import core.reference_view as rv

    monkeypatch.setattr(rv, "_resolve_default_commit", lambda cfg: "headhead")   # no edges here
    refs = _Refs([_Edge("docs/a.md", "core/x.py", "c1"), _Edge("core/x.py", "core/y.py", "c1"),
                  _Edge("core/y.py", "core/z.py", "c1"), _Edge("docs/old.md", "core/x.py", "c0")])
    vectors = _Vectors(
        dialogue=[{"source_path": "dialogue/c/t1", "title": "turn 1", "digest": "dt1",
                   "provenance": "observed", "vector": _vec(2)}],
        atoms=[{"id": "atom1", "provenance": "code", "source_path": "", "digest": "",
                "qualname": "", "vector": _vec(3), "text": "def f(): ..."},
               {"id": "atom2", "provenance": "code", "source_path": "", "digest": "",
                "qualname": "", "vector": _vec(4), "text": "class G: ..."}])
    curated = _Curated([
        {"source_path": "reference:p1", "title": "Paper 1", "digest": "p1", "provenance": "curated",
         "chunk_index": 0, "vector": _vec(5), "text": "c0"},
        {"source_path": "reference:p1", "title": "Paper 1", "digest": "p1", "provenance": "curated",
         "chunk_index": 1, "vector": _vec(5, 6), "text": "c1"},
        {"source_path": "reference:p2", "title": "Paper 2", "digest": "p2", "provenance": "curated",
         "chunk_index": 0, "vector": _vec(7), "text": "d0"}])
    memberships = _Memberships({"atom1": [("core/x.py", "f", 10, 20)],
                                "atom2": [("core/y.py", "G", 1, 9), ("core/w.py", "G", 1, 9)]})
    embed = {"q": _vec(0), "paper": _vec(5), "code": _vec(3), "x": _vec(9)}
    return _Engine(refs=refs, vectors=vectors, curated=curated, memberships=memberships,
                   embed=embed)


def _build(e: _Engine, plan: Any, **kw: Any) -> Any:
    return build(cast(QueryEngine, e), plan, **kw)


def _refs(u: Any) -> list[str]:
    return [n["source_path"] for n in u.notes]


# ── the seeds ───────────────────────────────────────────────────────────────────────────────────


def test_seeds_follow_over_as_of_and_the_verbs_radii() -> None:
    s = seeds_of(compile_sentence(
        '(near "q" and near "p" over curated) and top 3 diffuse S from "n" within '
        'reach F from "core/x.py" depth 2').term)
    assert s.texts == [("q", frozenset({Stratum.MIRROR_AUTHORED})),
                       ("p", frozenset({Stratum.CURATED}))]
    assert s.anchors == [("n", 1), ("core/x.py", 2)] and s.cut is None
    s = seeds_of(compile_sentence('walk from "a" to "b" via F+ as of "c1"').term)
    assert s.anchors == [("a", DEFAULT.walk_depth), ("b", 0)] and s.cut == "c1"
    s = seeds_of(compile_sentence('assume sever F "a" "b" in reach F from "a"').term)
    assert s.anchors == [("a", 0), ("b", 0), ("a", DEFAULT.depth)]
    assert is_repo_path("core/x.py") and is_repo_path("docs/a.md")
    assert not is_repo_path("/v/a.md") and not is_repo_path("dialogue/c/t1")
    assert not is_repo_path("reference:p1") and not is_repo_path("../etc/passwd")


# ── the support ─────────────────────────────────────────────────────────────────────────────────


def test_a_mirror_sentence_loads_the_mirror_and_the_dialogue_and_no_index(engine: _Engine) -> None:
    plan = compile_sentence('near "q"')
    u = _build(engine, plan)
    assert _refs(u) == ["/v/a.md", "/v/b.md", "dialogue/c/t1"]
    assert [n["stratum"] for n in u.notes] == ["mirror", "mirror", "dialogue"]
    assert engine._get("curated").searches == 0 and engine._get("vectors").searches == 0
    assert u.cut == "c1"                                       # the newest cut the store holds
    assert any("newest cut the store holds" in m for m in u.missing)
    answer = execute(plan, u)
    assert [h.ref for h in answer.hits] == ["/v/a.md"]
    assert u.in_strata(["mirror"]) == frozenset({0, 1})
    assert u.in_strata(["dialogue"]) == frozenset({2})


def test_near_over_curated_seeds_papers_from_the_index_and_masks_to_them(engine: _Engine) -> None:
    plan = compile_sentence('top 5 near "paper" over curated', AMBASSADOR_OVERLAY)
    u = _build(engine, plan, precedents=Precedents(support=2))
    assert engine._get("curated").searches == 2        # the seeding, then p1's degree census
    assert "reference:p1" in _refs(u) and "reference:p2" not in _refs(u)     # support 2 chunks → p1
    assert u.degrees is not None and u.degrees[_refs(u).index("reference:p1")] == 0.0
    node = u.notes[_refs(u).index("reference:p1")]
    assert node["stratum"] == "curated" and node["detail"]["chunks_hit"] == 2
    answer = execute(plan, u, precedents=Precedents(support=2))
    assert [h.ref for h in answer.hits] == ["reference:p1"]                   # the mask: no notes
    assert any("curated: 1 papers from the 2 nearest chunks" in m for m in u.missing)
    # the same text without `over` never touches the index; its hits are the notes'
    plain = compile_sentence('near "paper"')
    assert execute(plain, _build(engine, plain)).hits == () and engine._get("curated").searches == 2


def test_near_over_reference_resolves_code_atoms_to_files(engine: _Engine) -> None:
    plan = compile_sentence('top 5 near "code" over reference', AMBASSADOR_OVERLAY)
    u = _build(engine, plan)
    assert engine._get("vectors").searches == 1
    files = [n for n in u.notes if n["stratum"] == "reference"]
    assert {n["source_path"] for n in files} == {"core/x.py", "core/y.py", "core/w.py"}
    x = next(n for n in files if n["source_path"] == "core/x.py")
    assert x["detail"] == {"qualname": "f", "lines": "10–20"} and x["provenance"] == "code"
    answer = execute(plan, u)
    assert answer.hits[0].ref == "core/x.py" and answer.hits[0].detail["qualname"] == "f"
    assert u.edges[Rel.F] == {"core/x.py": {"core/y.py"}}   # wired at the cut, on the support


def test_reach_walks_the_citation_graph_at_the_newest_cut_and_as_of_picks_one(
        engine: _Engine) -> None:
    plan = compile_sentence('reach F from "core/x.py" depth 2')
    u = _build(engine, plan)
    answer = execute(plan, u)
    assert sorted(h.ref for h in answer.hits) == ["core/y.py", "core/z.py", "docs/a.md"]
    assert u.cut == "c1" and u.edges[Rel.F]["docs/a.md"] == {"core/x.py"}
    old = compile_sentence('reach F from "core/x.py" depth 2 as of "c0"')
    uo = _build(engine, old)
    assert uo.cut == "c0" and [h.ref for h in execute(old, uo).hits] == ["docs/old.md"]
    assert u.cut is not None
    nope = compile_sentence('reach F from "core/x.py" as of "nope"')
    with pytest.raises(NotImplementedError, match="no edges at that cut"):
        execute(nope, _build(engine, nope))
    # a short sha resolves as git does; an ambiguous one is refused, never silently the newest
    short = compile_sentence('reach F from "core/x.py" depth 2 as of "c0"')
    assert [h.ref for h in execute(short, _build(engine, short)).hits] == ["docs/old.md"]
    from core.sentence import AmbiguousSentence
    with pytest.raises(AmbiguousSentence, match="write more of the sha"):
        _build(engine, compile_sentence('reach F from "core/x.py" as of "c"'))
    walk = compile_sentence('walk from "docs/a.md" to "core/z.py" via F+ depth 3')
    assert [h.ref for h in execute(walk, _build(engine, walk)).hits] == \
        ["docs/a.md →F→ core/x.py →F→ core/y.py →F→ core/z.py"]


def test_the_support_bound_truncates_a_neighbourhood_and_says_so(engine: _Engine) -> None:
    plan = compile_sentence('reach F from "core/x.py" depth 3')
    u = _build(engine, plan, precedents=Precedents(support=2))
    assert any("cut at the support of 2 nodes" in m for m in u.missing)
    assert len([n for n in u.notes if n["stratum"] == "reference"]) == 2


def test_a_curated_anchor_seeds_its_neighbourhood(engine: _Engine) -> None:
    plan = compile_sentence('top 3 diffuse S from "reference:p1"', AMBASSADOR_OVERLAY)
    u = _build(engine, plan, precedents=Precedents(support=3))
    refs = _refs(u)
    assert "reference:p1" in refs and "reference:p2" in refs
    assert u.notes[refs.index("reference:p1")]["detail"]["chunks"] == 2


def test_read_of_a_repo_file_and_of_an_escape(engine: _Engine) -> None:
    plan = compile_sentence('read "core/sentence/precedents.py"', AMBASSADOR_OVERLAY)
    u = _build(engine, plan)
    (hit,) = execute(plan, u).hits
    assert hit.text is not None and hit.text.startswith('"""The resolution ledger')
    assert hit.stratum == "reference"
    assert hit.provenance == "code"
    # a repo path must stay inside the repo: an escape resolves to nothing
    bad = compile_sentence('read "docs/../../etc/passwd"', AMBASSADOR_OVERLAY)
    with pytest.raises(LookupError):
        execute(bad, _build(engine, bad))
