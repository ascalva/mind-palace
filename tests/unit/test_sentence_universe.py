"""The stratified universe (`core/sentence/universe.py`, dn-query-sentence-algebra §2.9): the
seeds a sentence names, the support built from the mirror, the dialogue, the curated index, the
code index resolved through the memberships, and the citation graph at the cut — with the newest-cut
fallback, the support bound, `over` as a mask and `read` of a repo file. Hermetic: store fakes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from core.kernel.config import REPO_ROOT, get_config
from core.kernel.scope import Stratum
from core.query import AMBASSADOR_OVERLAY, QueryEngine
from core.sentence import compile_sentence, execute
from core.sentence.ast import Rel
from core.sentence.precedents import DEFAULT, Precedents
from core.sentence.universe import build, is_repo_path, seeds_of
from core.stores.memberships import Membership

DIM = int(get_config().embedding.dim)
VAULT = str(Path(str(get_config().ingestion.vault.path)).expanduser())
C_NOTE = f"{VAULT}/c.md"                      # a mirror note at the configured vault path


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

    def edge(self, edge_id: str) -> _Edge | None:
        return None                       # no reference edge bears a causal edge's id

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


class _Causal:
    """The causal store's readers: one content-free row per proven edge."""

    def __init__(self, edges: list[dict[str, Any]]) -> None:
        self.edges = edges

    def all_edges(self) -> list[dict[str, Any]]:
        return [dict(e) for e in self.edges]

    def edge(self, edge_id: str) -> dict[str, Any] | None:
        return next((dict(e) for e in self.edges if e["edge_id"] == edge_id), None)


class _Chatlog:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.clearances: list[Any] = []

    def utterance(self, session_id: str, turn_index: int, *,
                  clearance: Any) -> dict[str, Any] | None:
        self.clearances.append(clearance)
        return next((dict(r) for r in self.rows if r["session_id"] == session_id
                     and r["turn_index"] == turn_index), None)


def _cedge(edge_id: str, session: str, turn: int, dst: str, dst_type: str = "file",
           order: int = 0) -> dict[str, Any]:
    """A proven edge whose action the utterance `turn` produced: the event projector stamps the
    action with the index the next utterance takes, `turn + 1` (core/chat_events.py)."""
    return {"edge_id": edge_id, "session_id": session, "event_order": order, "kind": "C",
            "dst_type": dst_type, "dst": dst, "witness_digest": "wd", "witness_turn": turn + 1,
            "pair_cut_sha": ""}


class _Memberships:
    def __init__(self, places: dict[str, list[tuple[str, str, int, int]]]) -> None:
        self.places = places

    def occupancies(self, cid: str, *, include_superseded: bool = False) -> list[Membership]:
        return [Membership(path=p, blob_sha="b", layer="L1", chunk_index=0, content_id=cid, slot=s,
                           slot_line_start=a, slot_line_end=b, current=True)
                for p, s, a, b in self.places.get(cid, [])]


class _Engine:
    def __init__(self, *, refs: _Refs, vectors: _Vectors, curated: _Curated,
                 memberships: _Memberships, embed: Mapping[str, list[float]],
                 causal: _Causal, chatlog: _Chatlog) -> None:
        self.config = get_config()
        self._cache: dict[str, Any] = {
            "references": refs, "vectors": vectors, "curated": curated, "memberships": memberships,
            "embedder": type("E", (), {"embed_query": staticmethod(lambda t: embed[t])})(),
            "edges": type("R", (), {"all": staticmethod(lambda: [])})(),
            "catalog": type("C", (), {"get": staticmethod(lambda a: None),
                                     "doc_id_for": staticmethod(lambda a: a)})(),
            "versions": type("V", (), {"history": staticmethod(lambda d: [])})(),
            "causal": causal, "chatlog": chatlog,
        }

    def _get(self, name: str) -> Any:
        return self._cache[name]

    def note_graph(self) -> tuple[list[dict[str, Any]], np.ndarray, np.ndarray]:
        notes = [{"source_path": "/v/a.md", "title": "A", "digest": "da",
                  "provenance": "authored-solo"},
                 {"source_path": "/v/b.md", "title": "B", "digest": "db",
                  "provenance": "authored-solo"},
                 {"source_path": C_NOTE, "title": "C", "digest": "dc",
                  "provenance": "authored-solo"}]
        mat = np.asarray([_vec(0), _vec(1), _vec(8)])
        return notes, mat, np.zeros((3, 3))


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
    # six proven edges from two transcripts: a checkout path, a worktree path, a scratch path
    # outside the repo, a vault note, an artifact id, and a second turn on the same file
    causal = _Causal([
        _cedge("e1", "s1", 3, f"{REPO_ROOT}/core/x.py", order=1),
        _cedge("e2", "s1", 3, f"{REPO_ROOT}/.claude/worktrees/wt/docs/a.md", order=2),
        _cedge("e3", "s1", 5, "/private/tmp/scratch/out.txt", order=3),
        _cedge("e4", "s2", 1, C_NOTE, order=1),
        _cedge("e5", "s2", 1, "recursive-strata.md", dst_type="doc", order=2),
        _cedge("e6", "s2", 2, f"{REPO_ROOT}/core/x.py", order=3),
    ])
    chatlog = _Chatlog([
        {"session_id": "s1", "turn_index": 3, "speaker": "owner", "text": "please write x",
         "transcript_digest": "td1", "provenance": "observed"},
        {"session_id": "s1", "turn_index": 5, "speaker": "agent", "text": "done",
         "transcript_digest": "td1", "provenance": "observed"},
        {"session_id": "s2", "turn_index": 1, "speaker": "agent", "text": "noting",
         "transcript_digest": "td2", "provenance": "observed"},
    ])
    return _Engine(refs=refs, vectors=vectors, curated=curated, memberships=memberships,
                   embed=embed, causal=causal, chatlog=chatlog)


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
    assert not is_repo_path("transcript/s1/3")


def test_seeds_record_the_moves_the_verbs_walk() -> None:
    assert seeds_of(compile_sentence('reach C from "core/x.py" back').term).moves == {Rel.C}
    assert seeds_of(compile_sentence('walk from "a" via S*C').term).moves == {Rel.S, Rel.C}
    assert seeds_of(compile_sentence('reach F from "a" and near "q"').term).moves == {Rel.F}
    assume = compile_sentence('assume C "a" "b" in walk from "a" via C', AMBASSADOR_OVERLAY)
    assert seeds_of(assume.term).moves == {Rel.C}


# ── the support ─────────────────────────────────────────────────────────────────────────────────


def test_a_mirror_sentence_loads_the_mirror_alone_and_no_index(engine: _Engine) -> None:
    """The universe holds what the sentence's admitted clauses read and nothing else: `near` with
    no `over` reads the owner's words, so the observed dialogue is never loaded (admission bounds
    the read, the review of 2026-11-05); `over dialogue` loads it."""
    plan = compile_sentence('near "q"')
    u = _build(engine, plan)
    assert _refs(u) == ["/v/a.md", "/v/b.md", C_NOTE]
    assert [n["stratum"] for n in u.notes] == ["mirror", "mirror", "mirror"]
    assert engine._get("curated").searches == 0 and engine._get("vectors").searches == 0
    assert u.cut == "c1"                                       # the newest cut the store holds
    assert any("newest cut the store holds" in m for m in u.missing)
    answer = execute(plan, u)
    assert [h.ref for h in answer.hits] == ["/v/a.md"]
    assert u.in_strata(["mirror"]) == frozenset({0, 1, 2})
    assert u.edges[Rel.C] == {}                 # no causal edge is read unless the sentence walks C
    over = compile_sentence('near "q" over dialogue')
    ud = _build(engine, over)
    assert _refs(ud) == ["dialogue/c/t1"] and ud.in_strata(["dialogue"]) == frozenset({0})
    both = compile_sentence('near "q" or near "q" over dialogue')
    assert _refs(_build(engine, both)) == ["/v/a.md", "/v/b.md", C_NOTE, "dialogue/c/t1"]


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


# ── the causal moves ────────────────────────────────────────────────────────────────────────────


def test_reach_c_back_names_the_turns_that_wrote_a_file(engine: _Engine) -> None:
    from core.sentence.trace import Trace

    plan = compile_sentence('reach C from "core/x.py" depth 1 back', AMBASSADOR_OVERLAY)
    t = Trace()
    u = _build(engine, plan, trace=t)
    answer = execute(plan, u)
    assert sorted(h.ref for h in answer.hits) == ["transcript/s1/3", "transcript/s2/2"]
    owner = next(h for h in answer.hits if h.ref == "transcript/s1/3")
    assert owner.stratum == "transcript" and owner.provenance == "observed"
    assert owner.title == "transcript/s1/3 (owner)"
    assert owner.detail["session"] == "s1" and owner.detail["turn"] == "3"
    assert owner.detail["speaker"] == "owner" and owner.detail["hops"] == 1
    other = next(h for h in answer.hits if h.ref == "transcript/s2/2")
    assert "speaker" not in other.detail                 # the chatlog has no row for that turn
    x = u.notes[_refs(u).index("core/x.py")]
    assert x["detail"]["witness"] == "e1"                # the first proven edge into the file
    assert u.edges[Rel.C] == {"transcript/s1/3": {"core/x.py"},
                              "transcript/s2/2": {"core/x.py"}}
    assert any("causal: 2 proven edges from 2 transcript turns to 1 endpoints" in m
               for m in u.missing)
    assert any("2 causal edges wired" in str(step) for step in t.steps)
    # `over dialogue` keeps the transcript turns (the clearances' classes), `over reference` not
    turns = {_refs(u).index("transcript/s1/3"), _refs(u).index("transcript/s2/2")}
    assert turns <= u.in_strata(["dialogue"]) and turns <= u.in_strata(["dialogue_transcript"])
    assert not turns & u.in_strata(["reference"])


def test_a_turns_endpoints_map_to_the_checkout_the_worktree_the_vault_and_outside(
        engine: _Engine) -> None:
    plan = compile_sentence('reach C from "transcript/s1/3" depth 2', AMBASSADOR_OVERLAY)
    u = _build(engine, plan)
    hits = {h.ref: h for h in execute(plan, u).hits}
    assert set(hits) == {"core/x.py", "docs/a.md", "transcript/s2/2"}
    assert hits["core/x.py"].stratum == "reference" and hits["core/x.py"].detail["witness"] == "e1"
    assert hits["docs/a.md"].detail["worktree"] == "wt" and hits["docs/a.md"].provenance == "corpus"
    assert hits["transcript/s2/2"].detail["hops"] == 2    # the other turn on the same file
    scratch = compile_sentence('reach C from "transcript/s1/5" depth 1', AMBASSADOR_OVERLAY)
    us = _build(engine, scratch)
    (out,) = execute(scratch, us).hits
    assert out.ref == "/private/tmp/scratch/out.txt" and out.stratum == "transcript"
    assert out.detail["endpoint"] == "outside the repo and the vault"
    assert any("1 endpoints are commits, ids, or paths outside" in m for m in us.missing)
    noted = compile_sentence('reach C from "transcript/s2/1" depth 1', AMBASSADOR_OVERLAY)
    un = _build(engine, noted)
    got = {h.ref: h for h in execute(noted, un).hits}
    assert got[C_NOTE].stratum == "mirror" and got[C_NOTE].title == "C"   # the mirror's own node
    assert got["recursive-strata.md"].detail["endpoint"] == "a doc's id, not a path"
    assert got["recursive-strata.md"].stratum == "transcript"
    assert len(un.notes) == 4 + 2                          # the mirror, the dialogue, the two


def test_walk_via_c_then_f_crosses_from_a_turn_to_what_its_file_cites(engine: _Engine) -> None:
    plan = compile_sentence('walk from "transcript/s1/3" via CF depth 2', AMBASSADOR_OVERLAY)
    u = _build(engine, plan)
    hits = execute(plan, u).hits
    # the turn wrote two files; each cites one more at the cut (the worktree write of docs/a.md
    # is the reference graph's docs/a.md, which cites core/x.py)
    assert sorted(h.ref for h in hits) == ["transcript/s1/3 →C→ core/x.py →F→ core/y.py",
                                           "transcript/s1/3 →C→ docs/a.md →F→ core/x.py"]
    # a chain is labelled by every stratum it runs through, in order
    assert {h.stratum for h in hits} == {"transcript+reference"}
    assert hits[0].detail["word"] == "CF"


def test_read_of_a_transcript_turn_holds_to_the_transcript_stratum(engine: _Engine) -> None:
    plan = compile_sentence('read "transcript/s1/3"', AMBASSADOR_OVERLAY)
    (hit,) = execute(plan, _build(engine, plan)).hits
    assert hit.text == "please write x" and hit.stratum == "transcript"
    assert hit.provenance == "observed" and hit.title == "transcript/s1/3 (owner)"
    missing = compile_sentence('read "transcript/s1/4"', AMBASSADOR_OVERLAY)
    with pytest.raises(LookupError):
        execute(missing, _build(engine, missing))


def test_witness_dereferences_a_causal_edges_own_id(engine: _Engine) -> None:
    plan = compile_sentence('witness "e2"', AMBASSADOR_OVERLAY)
    (hit,) = execute(plan, _build(engine, plan)).hits
    assert hit.ref == "e2" and hit.detail["dst"].endswith("docs/a.md")
    assert hit.detail["transcript"] == "transcript/s1/3" and hit.detail["session_id"] == "s1"
    assert "witness_digest" not in hit.detail            # a raw-store key never leaves the store
    none = compile_sentence('witness "nope"', AMBASSADOR_OVERLAY)
    assert execute(none, _build(engine, none)).hits == ()


def test_assume_a_causal_edge_adds_a_chain_as_a_hyp(engine: _Engine) -> None:
    plan = compile_sentence(
        'assume C "transcript/s1/5" "core/x.py" in walk from "transcript/s1/5" via C depth 1',
        AMBASSADOR_OVERLAY)
    u = _build(engine, plan)
    answer = execute(plan, u)
    assert answer.hyp is not None
    assert [h.ref for h in answer.hits] == ["transcript/s1/5 →C→ /private/tmp/scratch/out.txt"]
    assert [h.ref for h in answer.hyp.value] == [
        "transcript/s1/5 →C→ /private/tmp/scratch/out.txt", "transcript/s1/5 →C→ core/x.py"]
    assert answer.hyp.assumptions == ("C 'transcript/s1/5' 'core/x.py' +1",)
    assert any("adds a causal edge" in n for n in answer.notes)
    assert u.edges[Rel.C] == {"transcript/s1/5": {"/private/tmp/scratch/out.txt"}}  # untouched


def test_the_support_bound_cuts_a_causal_neighbourhood_too(engine: _Engine) -> None:
    plan = compile_sentence('reach C from "transcript/s1/3" depth 1', AMBASSADOR_OVERLAY)
    u = _build(engine, plan, precedents=Precedents(support=2))
    assert any("cut at the support of 2 nodes" in m for m in u.missing)
    assert [h.ref for h in execute(plan, u, precedents=Precedents(support=2)).hits] == ["core/x.py"]


# ── the review of 2026-11-05 ───────────────────────────────────────────────────────────────────


def _scratch_repo(tmp_path: Path) -> Path:
    """A git repo with a committed tree for the reader: docs, a foundation file, the golden set,
    a tool directory's file, a symlink into data/, a binary blob and a long file; plus what is
    never committed: data/, a local config, and an uncommitted edit to a tracked doc."""
    import subprocess

    repo = tmp_path / "repo"
    for d in ("docs", "data/raw/ab", "eval/golden", ".claude"):
        (repo / d).mkdir(parents=True)
    (repo / "docs" / "a.md").write_text("committed\n")
    (repo / "docs" / "long.md").write_text("".join(f"line {i}\n" for i in range(400)))
    (repo / "docs" / "blob.bin").write_bytes(b"\x00\x01\x02")
    (repo / "CONSTITUTION.md").write_text("the fixed point\n")
    (repo / "eval" / "golden" / "set.json").write_text("{}\n")
    (repo / ".claude" / "settings.json").write_text("{}\n")
    (repo / "data" / "raw" / "ab" / "abcd").write_text("a transcript, tool output and all\n")
    (repo / "docs" / "raw").symlink_to("../data/raw/ab/abcd")
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "init", "-q"], check=True, capture_output=True)
    subprocess.run([*git, "add", "docs", "CONSTITUTION.md", "eval", ".claude"], check=True,
                   capture_output=True)
    subprocess.run([*git, "commit", "-q", "-m", "tree"], check=True, capture_output=True)
    (repo / "local.toml").write_text("key = 'secret'\n")
    (repo / "docs" / "a.md").write_text("an uncommitted edit, a pasted key\n")
    return repo


def test_read_serves_the_committed_blob_and_nothing_else(tmp_path: Path,
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    """`read` of a repo path is git's blob in the tree at the commit: never an untracked file (the
    raw store's verbatim transcripts under data/, a local config), never an uncommitted edit,
    never what a symlink points at, never a case variant, a `..` climb, a tool directory or the
    foundation, whatever git tracks there."""
    import core.kernel.config as config
    from core.sentence.execute import _read_repo_file

    repo = _scratch_repo(tmp_path)
    monkeypatch.setattr(config, "REPO_ROOT", repo)

    def read(ref: str, chunk: int | None = None) -> Mapping[str, object] | None:
        return _read_repo_file(ref, chunk, window=2, cut=None)

    for ref in ("docs/a.md", "./docs/a.md"):
        got = read(ref)
        assert got is not None and got["text"] == "committed\n", ref   # the blob, not the edit
        assert got["stratum"] == "reference" and len(str(got["at"])) == 7
    refused = ("data/raw/ab/abcd", "local.toml", "./local.toml", "docs/../local.toml",
               "docs/../data/raw/ab/abcd", "docs/raw", "DOCS/a.md", "Docs/A.md", "docs/missing.md",
               "docs", "docs/", "docs//a.md", "./CONSTITUTION.md", "./constitution.md",
               "eval/golden/set.json", "Eval/Golden/set.json", ".claude/settings.json",
               "./.claude/settings.json", ".git/config", "../repo/docs/a.md")
    for ref in refused:
        assert read(ref) is None, ref
    with pytest.raises(LookupError, match="binary"):
        read("docs/blob.bin")
    # an unknown or malformed cut falls back to HEAD, never to the working tree
    fallback = _read_repo_file("docs/a.md", None, window=1, cut="--output=x")
    assert fallback is not None and fallback["text"] == "committed\n"


def test_read_of_a_repo_file_is_a_window_of_chunks(tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    """A repo file is read as a paper is: `window` chunks of REPO_CHUNK_LINES lines around the
    chunk asked for, the record saying which; a blob past the byte cap is refused by name."""
    import importlib

    import core.kernel.config as config

    ex = importlib.import_module("core.sentence.execute")   # the package exports `execute`
    repo = _scratch_repo(tmp_path)
    monkeypatch.setattr(config, "REPO_ROOT", repo)
    n = -(-400 // ex.REPO_CHUNK_LINES)
    head = ex._read_repo_file("docs/long.md", None, window=2, cut=None)
    assert head is not None and head["chunks"] == f"0–1 of {n}"
    assert str(head["text"]).splitlines()[0] == "line 0"
    assert len(str(head["text"]).splitlines()) == 2 * ex.REPO_CHUNK_LINES
    mid = ex._read_repo_file("docs/long.md", 4, window=2, cut=None)
    assert mid is not None and mid["chunks"] == f"2–3 of {n}"
    assert str(mid["text"]).splitlines()[0] == f"line {2 * ex.REPO_CHUNK_LINES}"
    monkeypatch.setattr(ex, "REPO_MAX_BYTES", 100)
    with pytest.raises(LookupError, match="cap"):
        ex._read_repo_file("docs/long.md", None, window=2, cut=None)


def test_the_foundation_is_refused_at_admission() -> None:
    """A `read` of the constitution or the golden set is typed in FOUNDATION, which no grant
    names, so the sentence is refused before anything is opened, in any spelling."""
    from core.sentence.types import IllScopedSentence

    for ref in ("./CONSTITUTION.md", "./constitution.md", "eval/golden/golden_set.json",
                "eval/golden.py", "Eval/Golden/x.md", "./eval/golden/corpus/a.md"):
        with pytest.raises(IllScopedSentence, match="foundation"):
            compile_sentence(f'read "{ref}"', AMBASSADOR_OVERLAY)
    compile_sentence('read "eval/golden_other.py"', AMBASSADOR_OVERLAY)   # a neighbour is not


def test_endpoints_map_in_both_checkout_layouts(engine: _Engine,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    """From the main checkout and from one of its worktrees, a path under either, or under a
    sibling worktree, is the reference node by its repo-relative path; another repo's worktree, a
    commit and an outside path are named in the transcript's stratum, never as reference nodes."""
    import core.kernel.config as config
    from core.sentence.universe import _Builder

    main = Path("/srv/palace")
    for here in (main, main / ".claude" / "worktrees" / "me"):
        monkeypatch.setattr(config, "REPO_ROOT", here)
        b = _Builder(engine, DEFAULT)                    # type: ignore[arg-type]
        ep = b._endpoint
        assert ep(f"{main}/core/x.py", "file").ref == "core/x.py"
        sib = ep(f"{main}/.claude/worktrees/other/docs/a.md", "file")
        assert sib.ref == "docs/a.md" and sib.stratum == "reference"
        assert sib.detail.get("worktree") == "other"
        own = ep(f"{here}/core/y.py", "file")
        assert own.ref == "core/y.py" and "worktree" not in own.detail
        foreign = ep("/elsewhere/.claude/worktrees/w/core/x.py", "file")
        assert foreign.stratum == "transcript" and foreign.ref.startswith("/elsewhere")
        sha = ep("0123456789abcdef0123456789abcdef01234567", "commit")
        assert sha.stratum == "transcript" and sha.detail["endpoint"] == "a commit, not a file"
        assert ep("not a path", "file").stratum == "transcript"


def test_a_docs_id_resolves_to_its_file_when_exactly_one_is_it(engine: _Engine) -> None:
    from core.sentence.universe import _Builder, _doc_path

    note = "docs/design-notes/dn-query-sentence-algebra.md"
    assert _doc_path("dn-query-sentence-algebra") == note
    assert _doc_path("dn-query-sentence-algebra.md") == _doc_path("dn-query-sentence-algebra")
    assert _doc_path("dn-no-such-note") is None and _doc_path("recursive-strata.md") is None
    node = _Builder(engine, DEFAULT)._endpoint("dn-query-sentence-algebra", "doc")  # type: ignore[arg-type]
    assert node.stratum == "reference" and node.detail["id"] == "dn-query-sentence-algebra"


def test_a_transcript_anchor_is_read_only_through_c_or_over_the_transcript(
        engine: _Engine) -> None:
    from core.sentence import IllScopedSentence

    s = compile_sentence('reach S from "transcript/s1/3" depth 2', AMBASSADOR_OVERLAY)
    with pytest.raises(IllScopedSentence, match="transcript turn"):
        _build(engine, s)
    c = compile_sentence('reach C from "transcript/s1/3" depth 1', AMBASSADOR_OVERLAY)
    assert "core/x.py" in {h.ref for h in execute(c, _build(engine, c)).hits}


def test_an_unknown_transcript_turn_is_a_lookup_refusal(engine: _Engine) -> None:
    for ref in ("transcript/s9/9", "transcript/s1/03", "transcript/s1"):
        plan = compile_sentence(f'reach C from "{ref}" depth 1', AMBASSADOR_OVERLAY)
        with pytest.raises(LookupError):
            _build(engine, plan)


def test_every_proven_edge_is_wired_and_counted(engine: _Engine) -> None:
    """Two edits of one file in one turn are two proven edges: both are wired, both counted."""
    engine._cache["causal"].edges.append(_cedge("e7", "s1", 3, f"{REPO_ROOT}/core/x.py", order=4))
    plan = compile_sentence('reach C from "transcript/s1/3" depth 1', AMBASSADOR_OVERLAY)
    u = _build(engine, plan)
    assert any("causal: 3 proven edges from 1 transcript turns" in m for m in u.missing)


def test_assume_sever_c_removes_the_chain(engine: _Engine) -> None:
    plan = compile_sentence(
        'assume sever C "transcript/s1/3" "core/x.py" in walk from "transcript/s1/3" via C depth 1',
        AMBASSADOR_OVERLAY)
    answer = execute(plan, _build(engine, plan))
    assert answer.hyp is not None
    assert "transcript/s1/3 →C→ core/x.py" in {h.ref for h in answer.hits}
    assert "transcript/s1/3 →C→ core/x.py" not in {h.ref for h in answer.hyp.value}



def test_read_labels_a_catalog_record_by_the_universes_table(tmp_path: Path) -> None:
    """The reader labels a catalog row by `stratum_of_provenance`, the table the universe uses: an
    observed row (the Ambassador's own capture) is a dialogue record, so `read` admits it exactly
    where `over dialogue` does; an interpreted row lands in no stratum the reader admits."""
    import dataclasses
    import importlib

    from config.loader import load_config
    from core.kernel.provenance import Provenance
    from core.kernel.stores.rawstore import RawStore
    from core.stores.catalog import VaultCatalog

    ex = importlib.import_module("core.sentence.execute")
    base = load_config()
    paths = dataclasses.replace(base.paths, raw_store=tmp_path / "raw",
                                vault_catalog=tmp_path / "cat.sqlite")
    cfg = dataclasses.replace(base, paths=paths)
    raw = RawStore(cfg.paths.raw_store)
    catalog = VaultCatalog(cfg.paths.vault_catalog)
    for ref, prov in (("dialogue/amb/capture-1", Provenance.OBSERVED),
                      ("dialogue/amb/said-1", Provenance.AUTHORED_DIALOGUE),
                      ("dialogue/amb/inferred-1", Provenance.INTERPRETED)):
        digest, _ = raw.add_text(f"the body of {ref}")
        catalog.record(ref, digest, ref, provenance=prov)

    class _Cfg:
        config = cfg

    def stratum(ref: str) -> object:
        rec = ex.read_ref(_Cfg(), ref, None, window=1, cut=None)   # type: ignore[arg-type]
        assert rec is not None and rec["text"] == f"the body of {ref}"
        return rec["stratum"]

    assert stratum("dialogue/amb/capture-1") == "dialogue"
    assert stratum("dialogue/amb/said-1") == "dialogue"
    assert stratum("dialogue/amb/inferred-1") == ""


def test_as_of_says_which_verbs_read_the_present(engine: _Engine) -> None:
    """Only the citation graph is indexed by commit: a `near` under `as of` reads today's notes,
    and the answer says so instead of passing the present off as the past (finding 9)."""
    plan = compile_sentence('near "q" as of "c1"', AMBASSADOR_OVERLAY)
    answer = execute(plan, _build(engine, plan))
    assert any("near read the present" in n for n in answer.notes)
    cited = compile_sentence('reach F from "core/x.py" as of "c1"', AMBASSADOR_OVERLAY)
    assert not any("read the present" in n for n in execute(cited, _build(engine, cited)).notes)


def test_a_notes_causal_history_is_found_by_its_title(engine: _Engine) -> None:
    """A note named by its title is found in the mirror and walked back over C to the turn that
    wrote it (the causal walk's endpoints clause reads the strata in force, the mirror, which
    covers the title); an F-only sentence from a repo anchor wires no causal edge at all (two
    mutations the first review found surviving: dropping the note's branch, and walking C from
    every repo anchor whatever the sentence walks)."""
    plan = compile_sentence('reach C from "C" depth 1 back', AMBASSADOR_OVERLAY)
    assert [c.verb for c in plan.clauses] == ["reach", "endpoints"]
    hits = execute(plan, _build(engine, plan)).hits
    assert [h.ref for h in hits] == ["transcript/s2/1"]       # the fixture turn that wrote c.md
    f_only = compile_sentence('reach F from "core/x.py" depth 1', AMBASSADOR_OVERLAY)
    assert _build(engine, f_only).edges[Rel.C] == {}
