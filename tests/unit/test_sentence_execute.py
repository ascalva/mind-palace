"""The executor (`core/sentence/execute.py`) on a toy universe of four notes: each verb's value,
the connectives, and `assume` with its response classes (dn-query-sentence-algebra §2.6)."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pytest

from core.kernel.scope import Hyp
from core.query import Hit
from core.sentence import (
    AmbiguousSentence,
    Universe,
    UnsupportedSentence,
    compile_sentence,
    execute,
)
from core.sentence.ast import Rel
from core.sentence.execute import Relation


def _universe() -> Universe:
    # four notes: a — b — c a path on the backbone, d isolated; a cites b, b cites c
    notes = [
        {"source_path": "a.md", "title": "A", "digest": "da", "provenance": "authored_solo"},
        {"source_path": "b.md", "title": "B", "digest": "db", "provenance": "authored_solo"},
        {"source_path": "c.md", "title": "C", "digest": "dc", "provenance": "authored_solo"},
        {"source_path": "d.md", "title": "D", "digest": "dd", "provenance": "authored_solo"},
    ]
    vectors = np.eye(4)
    weights = np.array([
        [0.0, 0.9, 0.0, 0.0],
        [0.9, 0.0, 0.8, 0.0],
        [0.0, 0.8, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
    ])
    edges = {Rel.F: {"a.md": {"b.md"}, "b.md": {"c.md"}}, Rel.D: {}, Rel.C: {}}
    relations = [Relation("da", "db", 1, "supports", 1.0)]

    def embed(text: str) -> np.ndarray:
        # the query is near A, a little near B
        return np.array([0.9, 0.3, 0.0, 0.0])

    def history(atom: str) -> list[tuple[str, int, str, str]]:
        return [("a.md", 1, "d1", "t1"), ("a.md", 2, "d2", "t2")] if atom == "a.md" else []

    def witness(edge: str) -> Mapping[str, object] | None:
        return {"edge_id": edge, "commit": "abc"} if edge == "e1" else None

    return Universe(notes, vectors, weights, edges, relations, embed, history, witness)


def _refs(hits: tuple[Hit, ...]) -> list[str]:
    return [h.ref for h in hits]


def test_near_is_the_kernel_column_ranked() -> None:
    u = _universe()
    answer = execute(compile_sentence('near "q"'), u)
    assert _refs(answer.hits) == ["a.md", "b.md"]
    assert answer.hits[0].score == pytest.approx(0.9 / np.hypot(0.9, 0.3), abs=1e-4)
    assert answer.plan.is_inv and answer.hyp is None


def test_diffuse_reach_relate_trace_witness_and_walk() -> None:
    u = _universe()
    diffuse = execute(compile_sentence('top 3 diffuse S from "a.md"'), u)
    assert _refs(diffuse.hits) == ["b.md", "c.md"]                   # d is unreachable, a is itself
    assert execute(compile_sentence('reach F from "a.md" depth 2'), u).hits[1].ref == "c.md"
    assert _refs(execute(compile_sentence('reach F from "c.md" back'), u).hits) == ["b.md"]
    assert _refs(execute(compile_sentence('reach F from "c.md" forward'), u).hits) == []
    relate = execute(compile_sentence('relate "A"'), u)
    assert _refs(relate.hits) == ["b.md"] and relate.hits[0].detail["sign"] == 1
    trace = execute(compile_sentence('trace "a.md"'), u)
    assert _refs(trace.hits) == ["a.md@1 →D→ a.md@2"]
    witness = execute(compile_sentence('witness "e1"'), u)
    assert witness.hits[0].detail["commit"] == "abc"
    walk = execute(compile_sentence('walk from "a.md" to "c.md" via F+'), u)
    assert _refs(walk.hits) == ["a.md →F→ b.md →F→ c.md"]
    assert execute(compile_sentence('walk from "a.md" via S*C'), u).hits == ()


def test_connectives_and_adjectives() -> None:
    u = _universe()
    masked = execute(compile_sentence('near "q" within reach F from "a.md" depth 1'), u)
    assert _refs(masked.hits) == ["b.md"]                            # a is outside its own reach
    then = execute(compile_sentence('reach F from "a.md" depth 2 then diffuse S from "a.md"'), u)
    assert _refs(then.hits) == ["b.md", "c.md"]
    both = execute(compile_sentence('near "q" and far diffuse S from "a.md"'), u)
    assert both.hits[0].ref == "a.md"                 # far from a's diffusion is a itself
    union = execute(compile_sentence('reach F from "a.md" or relate "A"'), u)
    assert _refs(union.hits) == ["b.md"]
    minus = execute(compile_sentence('reach F from "a.md" depth 2 minus relate "A"'), u)
    assert _refs(minus.hits) == ["c.md"]
    assert _refs(execute(compile_sentence('top 1 near "q"'), u).hits) == ["a.md"]
    assert _refs(execute(compile_sentence('atleast 0.5 near "q"'), u).hits) == ["a.md"]


def test_assume_adds_weight_and_the_field_rises_as_a_hyp() -> None:
    u = _universe()
    answer = execute(compile_sentence('assume S "a.md" "d.md" +0.9 in diffuse S from "a.md"'), u)
    assert isinstance(answer.hyp, Hyp)
    assert answer.hyp.assumptions == ("S 'a.md' 'd.md' +0.9",)
    assert "d.md" in _refs(answer.hyp.value) and "d.md" not in _refs(answer.hits)
    assert any("adds weight" in n for n in answer.notes)
    assert any("the field moved" in n for n in answer.notes)


def test_assume_sever_shrinks_reach_and_a_contradiction_breaks_the_camps() -> None:
    u = _universe()
    sever = execute(
        compile_sentence('assume sever S "a.md" "b.md" in reach S from "a.md" depth 2'), u)
    assert sever.hyp is not None and _refs(sever.hyp.value) == []
    assert _refs(sever.hits) == ["b.md", "c.md"]
    assert any("removes weight" in n for n in sever.notes)
    contra = execute(compile_sentence('assume contradict "a.md" "b.md" in relate "A"'), u)
    assert any("are broken" in n for n in contra.notes)
    consistent = execute(compile_sentence('assume contradict "a.md" "c.md" in relate "A"'), u)
    assert any("still hold" in n for n in consistent.notes)


def test_what_this_universe_cannot_answer_is_refused_not_emptied() -> None:
    u = _universe()
    with pytest.raises(UnsupportedSentence, match="no cut"):            # a toy universe has none
        execute(compile_sentence('near "q" as of "deadbeef"'), u)
    assert execute(compile_sentence('near "q" over curated'), u).hits == ()   # a mask: none
    with pytest.raises(UnsupportedSentence, match="note grain"):
        execute(compile_sentence('assume D "a.md" "b.md" in near "q"'), u)
    with pytest.raises(LookupError):
        execute(compile_sentence('diffuse S from "nowhere"'), u)
    u.notes[3]["title"] = "A"
    with pytest.raises(AmbiguousSentence, match="2 notes"):
        execute(compile_sentence('relate "A"'), u)


def test_the_answer_carries_its_plan() -> None:
    u = _universe()
    d = execute(compile_sentence('top 2 (near "q" and diffuse S from "a.md")'), u).to_dict()
    assert d["sort"] == "region" and "semantic" in d["modes"]
    assert d["plan"].startswith("plan (region)")
    assert [h["ref"] for h in d["hits"]] == ["b.md"]


def test_read_returns_the_record_and_holds_its_stratum_to_the_clause() -> None:
    """`read`: the text rides on the hit; a record the catalog puts outside the clause's strata is
    refused as ill-scoped, an absent ref as a lookup; a paper's window carries its chunk range."""
    from core.sentence import IllScopedSentence

    records = {
        "a.md": {"ref": "a.md", "title": "A", "provenance": "authored-solo", "stratum": "mirror",
                 "text": "the body of A"},
        "turn-1": {"ref": "turn-1", "title": "", "provenance": "authored-dialogue",
                   "stratum": "dialogue", "text": "what we said"},
        "leak.md": {"ref": "leak.md", "title": "L", "provenance": "observed", "stratum": "observed",
                    "text": "exhaust"},
        "reference:p": {"ref": "reference:p", "title": "P", "provenance": "curated",
                        "stratum": "curated", "chunks": "0–4 of 9", "text": "chunk text"},
    }
    seen: list[tuple[str, int | None, int]] = []

    def text(ref: str, chunk: int | None, window: int) -> Mapping[str, object] | None:
        seen.append((ref, chunk, window))
        return records.get(ref)

    u = _universe()
    u = Universe(u.notes, u.vectors, u.weights, u.edges, u.relations, u.embed, u.history,
                 u.witness, text=text)
    (hit,) = execute(compile_sentence('read "a.md"'), u).hits
    assert (hit.ref, hit.title, hit.provenance, hit.stratum, hit.text) == \
        ("a.md", "A", "authored-solo", "mirror", "the body of A")
    assert execute(compile_sentence('read "turn-1"'), u).hits[0].text == "what we said"
    (paper,) = execute(compile_sentence('read "reference:p" chunk 3'), u).hits
    assert paper.detail == {"chunks": "0–4 of 9"} and seen[-1] == ("reference:p", 3, 5)
    with pytest.raises(IllScopedSentence, match="outside the clause"):
        execute(compile_sentence('read "leak.md"'), u)
    with pytest.raises(LookupError, match="no active note"):
        execute(compile_sentence('read "nothing.md"'), u)
    assert execute(compile_sentence('read "a.md"'), u).plan.sort.value == "text"


def test_a_hypothetical_edge_moves_the_graphs_degrees_with_it() -> None:
    """RSP-5's guard and the overlay agree: the universe's full degrees move by exactly the
    weight the hypothesis adds or removes, so `assume` on a support never trips the guard."""
    u = _universe()
    u = Universe(u.notes, u.vectors, u.weights, u.edges, u.relations, u.embed, u.history,
                 u.witness, degrees=u.weights.sum(axis=1) + 0.25)   # a leak of 0.25 everywhere
    before = u.degrees.copy() if u.degrees is not None else None
    assert before is not None
    added = execute(compile_sentence('assume S "a.md" "d.md" +0.5 in top 3 diffuse S from "a.md"'),
                    u)
    assert added.hyp is not None and [h.ref for h in added.hyp.value] == ["b.md", "c.md", "d.md"]
    severed = execute(compile_sentence('assume sever S "a.md" "b.md" in top 3 diffuse S from '
                                       '"a.md"'), u)
    assert severed.hyp is not None and [h.ref for h in severed.hyp.value] == []
    assert u.degrees is not None and np.array_equal(u.degrees, before)   # the universe untouched
