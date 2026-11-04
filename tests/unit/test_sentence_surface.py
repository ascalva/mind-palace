"""QL-3, the surface (dn-query-sentence-algebra §3): `palace query` (`core/sentence/surface.py`),
the query log as a sensor, the Ambassador's `query` tool behind `[query] sentences`, the web
manifest following the switch, and the resolution ledger's file against its executable mirror.
Hermetic: the toy universe of test_sentence_execute, a log under tmp_path, no store opened."""

from __future__ import annotations

import io
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from core.query import AMBASSADOR, AMBASSADOR_OVERLAY
from core.sentence import surface
from core.sentence.ast import Rel
from core.sentence.execute import Relation, Universe
from core.sentence.precedents import DEFAULT
from core.sentence.surface import Entry, QueryLog, run_query, summarize

ROOT = Path(__file__).resolve().parents[2]


def _universe() -> Universe:
    # a — b — c on the backbone, d isolated; a cites b, b cites c; the query is near a
    notes = [
        {"source_path": "a.md", "title": "A", "digest": "da", "provenance": "authored_solo"},
        {"source_path": "b.md", "title": "B", "digest": "db", "provenance": "authored_solo"},
        {"source_path": "c.md", "title": "C", "digest": "dc", "provenance": "authored_solo"},
        {"source_path": "d.md", "title": "D", "digest": "dd", "provenance": "authored_solo"},
    ]
    weights = np.array([
        [0.0, 0.9, 0.0, 0.0],
        [0.9, 0.0, 0.8, 0.0],
        [0.0, 0.8, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
    ])
    edges = {Rel.F: {"a.md": {"b.md"}, "b.md": {"c.md"}}, Rel.D: {}, Rel.C: {}}

    def embed(text: str) -> np.ndarray:
        return np.array([0.9, 0.3, 0.0, 0.0])

    def history(atom: str) -> list[tuple[str, int, str, str]]:
        return []

    def witness(edge: str) -> Mapping[str, object] | None:
        return None

    return Universe(notes, np.eye(4), weights, edges, [Relation("da", "db", 1, "supports", 1.0)],
                    embed, history, witness)


def _run(argv: list[str], log: QueryLog, grant: Any = None) -> tuple[int, str]:
    out = io.StringIO()
    rc = run_query(argv, out=out, universe=_universe(), log=log, grant=grant)
    return rc, out.getvalue()


# ── `palace query` ──────────────────────────────────────────────────────────────────────────────


def test_the_cli_answers_with_the_plan_and_logs_the_sentence(tmp_path: Path) -> None:
    log = QueryLog(tmp_path / "q.jsonl")
    rc, text = _run(['near "q"'], log)
    assert rc == 0
    assert text.splitlines()[0] == 'near "q"'
    assert "sort: field · modes: semantic · Inv" in text
    assert "plan (field):" in text and "clauses:" in text          # the plan rides with the answer
    assert re.search(r"hits \(2\):\n  0\.9487  a\.md — A  \[authored_solo\]", text)
    assert "notes:" in text and "the 5 best scores are shown" in text
    (e,) = log.entries()
    assert (e.surface, e.role, e.outcome, e.hits, e.hyp) == ("cli", "cli", "answered", 2, False)
    assert (e.sort, e.modes, e.strata) == ("field", ("semantic",), ("mirror_authored",))
    assert _run(['reach F from "a.md"'], log)[0] == 0
    assert log.entries()[-1].strata == ("reference", "reference_repo")   # the closed Σ
    assert e.refusal == "" and e.ms >= 0 and e.at

    rc, text = _run(['top 1 near "q"', "--no-plan", "--as", "orchestrator"], log)
    assert rc == 0 and "plan (" not in text and "hits (1):" in text
    assert log.entries()[-1].role == "orchestrator"

    rc, text = _run(["--json", 'reach F from "a.md" depth 2'], log)
    assert rc == 0
    d = json.loads(text)
    assert d["sort"] == "region" and [h["ref"] for h in d["hits"]] == ["b.md", "c.md"]
    assert d["plan"].startswith("plan (region):")


def test_an_empty_answer_is_an_outcome_of_its_own(tmp_path: Path) -> None:
    log = QueryLog(tmp_path / "q.jsonl")
    rc, text = _run(['reach F from "c.md" forward'], log)      # c cites nothing
    assert rc == 0 and "hits: none" in text
    assert log.entries()[-1].outcome == "empty"


@pytest.mark.parametrize(
    ("sentence", "cls"),
    [
        ('nearby "q"', "parse"),
        ('not near "q"', "sort"),
        ('assume S "a.md" "d.md" +0.5 in near "q"', "scope"),      # the base grant: no overlay
        ('near "q" over nowhere', "ambiguous"),
        ('reach F from "zz.md"', "lookup"),
        ('near "q" as of "deadbeef"', "unsupported"),              # a toy universe has no cut
    ],
)
def test_a_refusal_is_a_question_back_logged_by_class(tmp_path: Path, sentence: str,
                                                      cls: str) -> None:
    log = QueryLog(tmp_path / "q.jsonl")
    rc, text = _run([sentence], log, AMBASSADOR)
    assert rc == 1 and text.startswith(f"refused ({cls}): ")
    (e,) = log.entries()
    assert (e.outcome, e.refusal, e.sentence) == ("refused", cls, sentence)
    assert e.reason and e.reason in text
    rc, text = _run([sentence, "--json"], log, AMBASSADOR)
    assert rc == 1 and json.loads(text)["refused"] == cls


def test_the_owners_overlay_grant_answers_a_hypothetical_as_a_hyp(tmp_path: Path) -> None:
    """The surfaces' default grant is `sentence_grant()`: the Ambassador's with the overlay while
    `[query] hypotheticals` is on (the committed default), so `assume` answers — as a `Hyp`
    beside the actual hits, never as an `Inv` — where the base grant refuses it."""
    from core.kernel.config.loader import _DEFAULTS, load_config
    from core.sentence.surface import sentence_grant

    assert load_config(_DEFAULTS).query.hypotheticals is True
    assert sentence_grant() in (AMBASSADOR_OVERLAY, AMBASSADOR)      # the live switch's value
    log = QueryLog(tmp_path / "q.jsonl")
    rc, text = _run(['assume S "a.md" "d.md" +0.9 in top 3 diffuse S from "a.md"'], log,
                    AMBASSADOR_OVERLAY)
    assert rc == 0 and "· Hyp" in text and "under the assumptions:" in text
    assert "hits assumed (3):" in text and "d.md — D" in text
    assert "every effective resistance falls or holds" in text
    (e,) = log.entries()
    assert (e.outcome, e.hyp, e.hits) == ("answered", True, 3)
    rc, text = _run(['assume S "a.md" "d.md" +0.9 in top 3 diffuse S from "a.md"', "--json"], log,
                    AMBASSADOR_OVERLAY)
    d = json.loads(text)
    assert [h["ref"] for h in d["hyp"]["hits"]] == ["b.md", "c.md", "d.md"]
    assert d["hyp"]["assumptions"] == ["S 'a.md' 'd.md' +0.9"] and "Hyp" in d["plan"]


def test_a_scope_refusal_still_records_the_strata_it_wanted(tmp_path: Path) -> None:
    log = QueryLog(tmp_path / "q.jsonl")
    _run(['assume S "a.md" "d.md" +0.5 in near "q"'], log, AMBASSADOR)
    (e,) = log.entries()
    assert e.strata == ("hypothetical", "mirror_authored") and e.sort == ""
    _run(['nearby "q"'], log)                                      # no parse: no shape at all
    assert log.entries()[-1].strata == () and log.entries()[-1].modes == ()


def test_usage_is_refused_with_the_usage_line(tmp_path: Path) -> None:
    log = QueryLog(tmp_path / "q.jsonl")
    for argv in ([], ["--log", 'near "q"'], ["--bogus", 'near "q"'], ['near "q"', "--as"]):
        rc, text = _run(argv, log)
        assert rc == 2 and text.startswith("usage: palace query")
    assert log.entries() == []


# ── the sensor ──────────────────────────────────────────────────────────────────────────────────


def test_the_log_is_a_sensor_of_strata_by_role_and_failed_translations(tmp_path: Path) -> None:
    log = QueryLog(tmp_path / "q.jsonl")
    _run(['near "q"', "--as", "orchestrator"], log)
    _run(['near "q" within reach F from "a.md"', "--as", "orchestrator"], log)
    _run(['reach F from "c.md" forward', "--as", "builder"], log)
    _run(['near "q" over nowhere', "--as", "builder"], log)
    _run(['nearby "q"', "--as", "builder"], log)
    s = summarize(log.entries())
    assert s["asked"] == 5
    assert s["outcomes"] == {"answered": 2, "empty": 1, "refused": 2}
    # strata are the clauses' closed Σ (reference closes to its repo refinement); an unknown
    # stratum has no shape at all, so the two builder refusals share the empty key
    assert s["served"] == {
        "builder · reference,reference_repo": {"empty": 1},
        "builder · ∅": {"refused": 2},
        "orchestrator · mirror_authored": {"answered": 1},
        "orchestrator · mirror_authored,reference,reference_repo": {"answered": 1},
    }
    assert s["refusals"] == {"ambiguous": 1, "parse": 1}
    assert [f["why"].split(":")[0] for f in s["failed"]] == ["empty", "ambiguous", "parse"]

    rc, text = _run(["--log"], log)
    assert rc == 0
    assert text.splitlines()[0] == "asked: 5  answered 2  empty 1  refused 2"
    assert "served (role · strata):" in text and "refusals: ambiguous 1, parse 1" in text
    assert "failed translations (last 10):" in text and 'nearby "q"' in text
    rc, text = _run(["--log", "--json"], log)
    assert rc == 0 and json.loads(text) == s


def test_the_log_holds_no_note_text_and_survives_an_unwritable_path(tmp_path: Path,
                                                                     capsys: Any) -> None:
    log = QueryLog(tmp_path / "q.jsonl")
    _run(['near "q"'], log)
    line = (tmp_path / "q.jsonl").read_text(encoding="utf-8")
    assert "a.md" not in line and '"hits": 2' in line                 # counted, never named
    blocked = QueryLog(tmp_path / "q.jsonl" / "not-a-dir" / "q.jsonl")  # a file in the way
    rc, text = _run(['near "q"'], blocked)
    assert rc == 0 and "hits (2):" in text                             # the instrument answered
    assert "query log not written" in capsys.readouterr().err
    assert blocked.entries() == []
    assert QueryLog(tmp_path / "absent.jsonl").entries() == []


def test_entries_ignore_fields_a_later_schema_adds(tmp_path: Path) -> None:
    p = tmp_path / "q.jsonl"
    row = {"at": "2026-11-04T00:00:00", "surface": "cli", "role": "owner", "sentence": 'near "x"',
           "outcome": "answered", "hits": 1, "modes": ["semantic"], "strata": ["mirror_authored"],
           "verdict": "sufficient"}
    p.write_text(json.dumps(row) + "\n\n", encoding="utf-8")
    (e,) = QueryLog(p).entries()
    assert e == Entry(at="2026-11-04T00:00:00", surface="cli", role="owner", sentence='near "x"',
                      outcome="answered", hits=1, modes=("semantic",), strata=("mirror_authored",))


# ── the Ambassador's `query` tool: the one read ────────────────────────────────────────────────


def _names(server: Any) -> set[str]:
    reply = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    return {t["name"] for t in reply["result"]["tools"]}


def _call(server: Any, sentence: str) -> dict[str, Any]:
    reply = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                           "params": {"name": "query", "arguments": {"sentence": sentence}}})
    assert reply is not None
    return reply


def test_the_query_tool_is_the_one_read_of_the_mcp(monkeypatch: pytest.MonkeyPatch,
                                                  tmp_path: Path) -> None:
    from agents.ambassador import mcp
    from agents.ambassador.handoff import WEB_TOOLS, web_manifest

    server = mcp.Server()
    names = _names(server)
    assert "query" in names and "query" in WEB_TOOLS
    assert names.isdisjoint({"search", "neighbors", "hybrid", "history", "related", "reach",
                             "origin", "read"})
    assert "query" in {t["name"] for t in web_manifest()["tools"]}

    # the call runs under `sentence_grant()` against the live universe (faked here) and is logged
    import core.sentence.universe as universe_mod

    monkeypatch.setattr(universe_mod, "build",
                        lambda engine, plan, precedents, trace=None: _universe())
    monkeypatch.setattr(surface, "default_log", lambda: QueryLog(tmp_path / "q.jsonl"))
    monkeypatch.setattr(surface, "sentence_grant", lambda: AMBASSADOR_OVERLAY)
    reply = _call(server, 'top 1 near "q"')
    assert reply["result"]["isError"] is False
    body = json.loads(reply["result"]["content"][0]["text"])
    assert [h["ref"] for h in body["hits"]] == ["a.md"] and body["plan"].startswith("plan (")
    (e,) = QueryLog(tmp_path / "q.jsonl").entries()
    assert (e.surface, e.role, e.outcome) == ("mcp", "ambassador", "answered")
    # a hypothetical answers as a Hyp under the owner's grant
    reply = _call(server, 'assume sever S "a.md" "b.md" in top 3 diffuse S from "a.md"')
    body = json.loads(reply["result"]["content"][0]["text"])
    assert reply["result"]["isError"] is False and "hyp" in body
    # a refusal is an error result naming its cause, not a crash — and it is logged
    reply = _call(server, 'not near "q"')
    assert reply["result"]["isError"] is True
    assert "SortError" in reply["result"]["content"][0]["text"]
    assert QueryLog(tmp_path / "q.jsonl").entries()[-1].refusal == "sort"


def test_the_hypotheticals_switch_defaults_on_and_reads_from_the_toml(tmp_path: Path) -> None:
    from core.kernel.config.loader import _DEFAULTS, load_config

    assert load_config(_DEFAULTS).query.hypotheticals is True          # the owner's grant
    text = _DEFAULTS.read_text(encoding="utf-8")
    assert text.count("\nhypotheticals = true\n") == 1
    off = tmp_path / "off.toml"
    off.write_text(text.replace("\nhypotheticals = true\n", "\nhypotheticals = false\n"),
                   encoding="utf-8")
    assert load_config(off).query.hypotheticals is False


# ── the resolution ledger: the file and its mirror change together ──────────────────────────────


def test_the_precedents_file_mirrors_the_code() -> None:
    doc = (ROOT / "docs" / "query" / "precedents.md").read_text(encoding="utf-8")
    rows = re.finditer(r"^\| ([^|]+) \| ([^|]+) \|", doc, re.M)
    table = {m.group(1).strip(): m.group(2) for m in rows}
    expected = {
        "`diffuse … beta`": str(DEFAULT.beta),
        "`reach … depth`": str(DEFAULT.depth),
        "`walk … depth`": str(DEFAULT.walk_depth),
        "`walk`'s most chains": str(DEFAULT.walk_limit),
        "`diffuse` with no relation": DEFAULT.diffuse_rel.value,
        "`reach` with no relation": DEFAULT.reach_rel.value,
        "`reach` with no direction": DEFAULT.reach_direction.value,
        "`trace` with no direction": DEFAULT.trace_direction.value,
        "`near` with no `over`": ",".join(s.value for s in DEFAULT.strata),
        "a field as the whole sentence": str(DEFAULT.k),
        "`read` with no `chunk`": str(DEFAULT.read_chunk),
        "`read`'s window": str(DEFAULT.read_window),
        "the support an indexed stratum contributes": str(DEFAULT.support),
    }
    for dial, value in expected.items():
        assert dial in table, f"{dial} has no row in docs/query/precedents.md"
        first = re.search(r"`([^`]+)`", table[dial])
        assert first is not None and first.group(1) == value, (dial, table[dial], value)
