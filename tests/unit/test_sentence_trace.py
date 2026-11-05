"""The trace (`core/sentence/trace.py`): a sentence's proof of work — the parse, the rewrites
with their laws, the census, each clause's arithmetic, the ranking — carried only when asked for,
and never a note's text."""

from __future__ import annotations

import json
from pathlib import Path

from core.query import AMBASSADOR, AMBASSADOR_OVERLAY
from core.sentence import Trace, compile_sentence, execute
from core.sentence.surface import QueryLog, run_query
from tests.unit.test_sentence_execute import _universe


def _trace(text: str, grant=AMBASSADOR_OVERLAY) -> tuple[Trace, list[str]]:
    t = Trace()
    u = _universe()
    answer = execute(compile_sentence(text, grant, trace=t), u, trace=t)
    assert answer.trace is t
    return t, [h.ref for h in answer.hits]


def test_a_composed_sentence_shows_its_work_stage_by_stage() -> None:
    t, hits = _trace('(top 2 (near "q" and diffuse S from "a.md")) within '
                     'reach F from "a.md" depth 1')
    stages = [s.stage for s in t.steps]
    assert stages[0] == "parse" and stages[-1] == "rank"
    assert [stages.index(x) for x in ("parse", "plan", "eval", "rank")] == sorted(
        stages.index(x) for x in ("parse", "plan", "eval", "rank"))
    text = t.render()
    # the planner: the Schur product's operands ordered, the mask held above `top`
    assert "`and` ordered canonically" in text and "[QSA-1]" in text
    assert "within stays over `top`" in text and "[QSA-4]" in text
    assert "within: masked to a region of 1 nodes" in text and "[QSA-2]" in text
    # the executor: the kernel column, the killed walk with its dials, the product, the cut
    assert "near 'q': the kernel column" in text and "[QSA-3]" in text
    assert "killed walk W_β = z·D⁻¹W∘W^β" in text and "β = 1" in text and "[RSP-1, RSP-4]" in text
    assert "the Schur product f ⊙ g" in text and "×" in text
    assert "top 2:" in text and "the cut is" in text
    # the ranking, and the laws cited once each, in order of first use
    assert "rank: the region's" in text
    assert t.laws[:2] == ("QSA-8", "QSA-5") or "QSA-5" in t.laws
    assert all(t.laws.count(law) == 1 for law in t.laws)
    assert hits == ["b.md"]
    # no note's text ever enters the trace: refs and numbers only
    assert "the body" not in text


def test_a_sever_shows_the_rank_one_update_and_its_horizon() -> None:
    # a — b — c is a path: the edge a ~ b is a bridge, so severing it is the singular case
    t, _ = _trace('assume sever S "a.md" "b.md" in top 3 diffuse S from "a.md"')
    text = t.render()
    assert "a rank-one update of the backbone's Laplacian" in text and "[QSA-9]" in text
    assert "w·R_eff(u, v) = 1.0000 = 1: the edge is a bridge" in text
    assert "[SEV-3, SEV-4, SEV-5]" in text
    assert "— under the assumption:" in text and "— and without it:" in text
    # the triangle a — b — c — a is not a bridge: regular, with its denominator
    u = _universe()
    u.weights[0, 2] = u.weights[2, 0] = 0.5
    t2 = Trace()
    execute(compile_sentence('assume sever S "a.md" "b.md" in top 3 diffuse S from "a.md"',
                             AMBASSADOR_OVERLAY, trace=t2), u, trace=t2)
    assert "< 1: the response is regular, the Sherman–Morrison denominator" in t2.render()


def test_the_trace_is_absent_unless_asked_for_and_costs_the_answer_nothing() -> None:
    u = _universe()
    plan = compile_sentence('top 2 near "q"')
    plain = execute(plan, u)
    assert plain.trace is None and "trace" not in plain.to_dict()
    t = Trace()
    traced = execute(plan, u, trace=t)
    assert [h.ref for h in traced.hits] == [h.ref for h in plain.hits]
    d = traced.to_dict()
    assert d["trace"]["laws"] and d["trace"]["steps"][-1]["stage"] == "rank"
    assert all(set(s) <= {"stage", "what", "law"} for s in d["trace"]["steps"])


def test_the_cli_shows_the_work_with_the_flag(tmp_path: Path) -> None:
    import io

    log = QueryLog(tmp_path / "q.jsonl")
    u = _universe()
    out = io.StringIO()
    assert run_query(['top 2 near "q"', "--trace"], out=out, grant=AMBASSADOR, universe=u,
                     log=log) == 0
    assert "trace (the proof of work):" in out.getvalue() and "laws:" in out.getvalue()
    out = io.StringIO()
    assert run_query(['top 2 near "q"'], out=out, grant=AMBASSADOR, universe=u, log=log) == 0
    assert "trace (the proof of work)" not in out.getvalue()
    out = io.StringIO()
    assert run_query(['top 2 near "q"', "--json", "--trace"], out=out, grant=AMBASSADOR,
                     universe=u, log=log) == 0
    assert json.loads(out.getvalue())["trace"]["laws"]
    # the log is the same sensor either way: no trace content in it
    entries = log.entries()
    assert len(entries) == 3 and all("trace" not in e.__dict__ for e in entries)


def test_the_normal_form_rewrites_name_their_laws() -> None:
    t = Trace()
    compile_sentence('(near "q" and diffuse S from "a.md") within reach F from "a.md" depth 1',
                     trace=t)
    plan_steps = [s for s in t.steps if s.stage == "plan"]
    assert any("ordered canonically" in s.what and s.law == "QSA-1" for s in plan_steps)
    assert any("within pushed through `and`" in s.what and s.law == "QSA-2" for s in plan_steps)
    assert any(s.what.startswith("normal form:") for s in plan_steps)
    t2 = Trace()
    compile_sentence('near "q"', trace=t2)
    assert any("already in normal form" in s.what for s in t2.steps)
