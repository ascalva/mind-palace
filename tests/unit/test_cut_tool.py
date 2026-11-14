"""The `cut` tool's handler, called as the MCP server calls it (dn-temporal-snapshot §7.5, SN-1b).

The server opens the catalog's file to only read, decodes a call's arguments from JSON and passes
both to the handler, and writes the answer back as JSON (`agents/ambassador/mcp.py`,
`Ambassador.cut`, `Server.handle`); `ask` does the same around
`agents/ambassador/cut_tool.py::cut`. The property, the tenth of §12's list for SN-1b: every
operator answers by its name; an operand may be a call, and the whole call is one expression,
which reads the heads when it starts, the horizon of a chain once when a position under its head
is named, and then one statement for its outermost operator; the head is read once a call, so
writes that land while a call runs change nothing in its answer; a set, a signed difference or a
number given where a cut is expected is refused by its type; a call whose sets would name more
than `TERMS` cuts is refused before any statement is written, and a nested symmetric difference
grows the statement by its operands only; a position past a chain's head is refused with the
head; a chain the grant does not read is refused in the words used for one that does not exist;
and the note says that the head was read where no cut was named, which chain was read below each
position asked, that a cut can split a change of class, how many rows of the ranges read are
holes, and that edges and graph mathematics at a cut arrive with SN-4. The registration in the
server is `tests/unit/test_ambassador_surface.py`'s.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

import pytest

from agents.ambassador import cut_tool
from core.kernel.provenance import Provenance
from core.stores.catalog import VaultCatalog
from core.stores.cuts import CutError, Evaluation, read_only

SOLO, CURATED = Provenance.AUTHORED_SOLO, Provenance.CURATED
BOTH = ["authored-solo", "curated"]
START = "SELECT chain, class, (SELECT max(seq) FROM landings"      # the heads, when a call starts


def ask(cat: VaultCatalog, classes: Iterable[str] = BOTH, seen: list[str] | None = None,
        **arguments: Any) -> dict[str, Any]:
    """A call as the server makes it: over a connection that only reads the catalog's file, the
    arguments through JSON, the answer back through it. `seen` collects the statements the call
    runs."""
    conn = read_only(cat.path)
    if seen is not None:
        conn.set_trace_callback(seen.append)
    try:
        answer = cut_tool.cut(conn, classes, json.loads(json.dumps(arguments)))
    finally:
        conn.close()
    text = json.dumps(answer, ensure_ascii=False)            # plain JSON: no default needed
    out: dict[str, Any] = json.loads(text)
    return out


@pytest.fixture
def cat(tmp_path: Path) -> Iterator[VaultCatalog]:
    """A chain of authored-solo notes, land.1, and one of curated papers, land.2, in a file the
    calls read through their own connection. land.1: the genesis and the horizon at 1 and 2, a.md
    and b.md at 3 and 4; then a.md edited at 5, b.md retired at 6 and c.md landed at 7. land.2:
    x.md at 3."""
    c = VaultCatalog(tmp_path / "catalog.sqlite")
    c.record("a.md", "d1", "A", provenance=SOLO)
    c.record("b.md", "d2", "B", provenance=SOLO)
    c.record("x.md", "dx", "X", provenance=CURATED)
    c.record("a.md", "d3", "A", provenance=SOLO)
    c.tombstone("b.md")
    c.record("c.md", "d4", "C", provenance=SOLO)
    assert c.chains(SOLO) == [1] and c.chains(CURATED) == [2]
    yield c
    c.close()


A = "land.1@4"                      # a.md at d1, b.md at d2
SOLO_ONLY = {"over": ["authored-solo"]}


def test_every_operator_answers_by_its_name(cat: VaultCatalog) -> None:
    head = "land.1@7 land.2@3"
    assert ask(cat, op="head")["cut"] == head
    assert ask(cat, op="bottom")["cut"] == "land.1@0 land.2@0"
    assert ask(cat, op="join", a=A, b="land.2@3")["cut"] == "land.1@4 land.2@3"
    assert ask(cat, op="meet", a=A, b="head")["cut"] == "land.1@4 land.2@0"
    assert ask(cat, op="order", a=A, b="head")["order"] == "before"
    assert ask(cat, op="order", a=A, b="land.2@3")["order"] == "unordered"
    between = ask(cat, op="between", a=A, list=True, **SOLO_ONLY)
    assert (between["type"], between["count"]) == ("events", 3)
    assert [(r["seq"], r["kind"], r["path"]) for r in between["rows"]] == [
        (5, "store", "a.md"), (6, "retire", "b.md"), (7, "store", "c.md")]
    held = ask(cat, op="held", a=A, list=True)
    assert (held["type"], held["count"]) == ("set", 2)
    assert [(r["path"], r["digest"], r["identity"], r["title"]) for r in held["rows"]] == [
        ("a.md", "d1", "a.md", "A"), ("b.md", "d2", "b.md", "B")]
    sets = {op: ask(cat, op=op, a=A, b="head", **SOLO_ONLY)["count"]
            for op in ("union", "intersection", "difference", "symmetric_difference")}
    assert sets == {"union": 4, "intersection": 0, "difference": 2, "symmetric_difference": 4}
    delta = ask(cat, op="delta", a=A, **SOLO_ONLY)
    assert (delta["type"], delta["removed"], delta["added"], delta["replaced"]) == \
        ("delta", 1, 1, 1)
    applied = ask(cat, op="apply", a=A, b={"op": "delta", "a": A}, list=True, **SOLO_ONLY)
    assert [r["digest"] for r in applied["rows"]] == ["d3", "d4"]
    composed = ask(cat, op="compose", a={"op": "delta", "a": "bottom", "b": A},
                   b={"op": "delta", "a": A}, **SOLO_ONLY)
    assert (composed["removed"], composed["added"], composed["replaced"]) == (0, 2, 0)
    assert ask(cat, op="persisted", cuts=[A, "head"], **SOLO_ONLY)["count"] == 0
    assert ask(cat, op="existed", cuts=[A, "head"], **SOLO_ONLY)["count"] == 4
    count = ask(cat, op="count", a=A)
    assert (count["type"], count["value"]) == ("number", 2)
    counted = ask(cat, op="in_how_many", cuts=[A, "land.1@5", "head"],
                  a={"op": "existed", "cuts": [A, "head"]}, **SOLO_ONLY)
    assert [(r["path"], r["digest"], r["cuts_holding"]) for r in counted["rows"]] == [
        ("a.md", "d1", 1), ("b.md", "d2", 2), ("a.md", "d3", 2), ("c.md", "d4", 1)]
    assert counted["held_by_every_cut"] == 0
    seen: list[str] = []
    first = ask(cat, seen=seen, op="in_how_many", cuts=["land.1@5", "head"],
                a={"op": "existed", "cuts": ["land.1@5", "head"]}, limit=1, **SOLO_ONLY)
    assert [(r["digest"], r["cuts_holding"]) for r in first["rows"]] == [("d2", 1)]
    assert (first["count"], first["truncated"], first["held_by_every_cut"]) == (3, True, 1)
    assert sum(q.endswith("LIMIT 1)") for q in seen) == 1            # the rows listed, and no more
    series = ask(cat, op="measure", cuts=["bottom", A, "head"], of="count", **SOLO_ONLY)
    assert [(s["cut"], s["value"]) for s in series["series"]] == [
        ("land.1@0", 0), ("land.1@4", 2), ("land.1@7", 2)]
    table = ask(cat, op="pairwise", cuts=[A, "head"], **SOLO_ONLY)["table"]
    assert table == {"cuts": ["land.1@4", "land.1@7"], "sizes": [[0, 2], [2, 0]]}
    assert set(cut_tool.OPERATORS) == {
        "head", "bottom", "join", "meet", "order", "between", "held", "union", "intersection",
        "difference", "symmetric_difference", "delta", "apply", "compose", "persisted",
        "existed", "count", "in_how_many", "measure", "pairwise"}


def test_the_two_meanings_of_union_differ_by_name_and_type(cat: VaultCatalog) -> None:
    """`join` is the union on positions and returns a cut, whose contents hold the later version
    of a.md alone; `union` is the union on contents and returns a set holding both versions."""
    joined = ask(cat, op="held", a={"op": "join", "a": A, "b": "head"}, list=True, **SOLO_ONLY)
    united = ask(cat, op="union", a=A, b="head", list=True, **SOLO_ONLY)
    assert [r["digest"] for r in joined["rows"]] == ["d3", "d4"]
    assert [r["digest"] for r in united["rows"]] == ["d1", "d2", "d3", "d4"]
    assert ask(cat, op="join", a=A, b="head")["type"] == "cut"
    assert united["type"] == "set"


def test_a_call_reads_the_heads_a_horizon_once_and_one_statement_for_its_result(
        cat: VaultCatalog) -> None:
    """The union of two differences is one call with a `difference` in `a` and another in `b`:
    the whole is one expression. Every statement the call runs, in order: the heads, when it
    starts; the horizon of land.1, once though land.1@4 is named twice, since a position under a
    chain's head is served from the chain's horizon on (§7.1); and the one statement that counts
    the union. An operator on positions reads what its names need and nothing more, and `head`
    and `bottom` need nothing."""
    seen: list[str] = []
    answer = ask(cat, seen=seen, op="union", a={"op": "difference", "a": "head", "b": A},
                 b={"op": "difference", "a": A, "b": "head"}, **SOLO_ONLY)
    assert answer["count"] == 4
    assert [c["read"] for c in answer["cuts"]] == ["land.1@7", "land.1@4"]
    assert len(seen) == 3, seen
    assert seen[0].startswith(START)
    assert "kind = 'horizon'" in seen[1] and "seq <= 4 " in seen[1]
    assert re.match(r"SELECT coalesce\(sum\(n\), 0\), coalesce\(sum\(h\), 0\) FROM", seen[2])
    for args, n in (({"op": "order", "a": A, "b": "land.1@5"}, 2),
                    ({"op": "join", "a": A, "b": "land.1@3"}, 2),
                    ({"op": "order", "a": "head", "b": "bottom"}, 1)):
        seen.clear()
        ask(cat, seen=seen, **args, **SOLO_ONLY)
        assert len(seen) == n and seen[0].startswith(START), (args, seen)


def test_the_head_is_read_once_a_call_whatever_lands_while_it_runs(
        cat: VaultCatalog, monkeypatch: pytest.MonkeyPatch) -> None:
    """Writes that land after a call has read the heads change nothing in its answer: an operand
    left out is the head the call read when it started, in a signed difference, a set, a join and
    a family alike, and so is the cut the `head` operator names; the answer's cuts, its note and
    its counts are those of that head (D27, SNF-19). The writes land from the catalog's own
    connection right after the call's evaluation reads the heads, two a call."""

    class Racing(Evaluation):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            n = cat.head(1)
            cat.record("d.md", f"d{n}", "D")
            cat.record("a.md", f"e{n}", "A")

    monkeypatch.setattr(cut_tool, "Evaluation", Racing)

    def said(head: str) -> str:
        return f"No cut was named for an operand, so the head was read, once for the whole " \
               f"call: {head}."

    delta = ask(cat, op="delta", a="bottom", **SOLO_ONLY)          # read at 7; 8 and 9 land
    assert (delta["removed"], delta["added"], delta["replaced"]) == (0, 2, 0)
    assert delta["cuts"] == [{"read": "land.1@0"}, {"read": "land.1@7"}]
    assert delta["note"].startswith(said("land.1@7"))
    held = ask(cat, op="held", list=True, **SOLO_ONLY)             # read at 9; 10 and 11 land
    assert [(r["seq"], r["digest"]) for r in held["rows"]] == [(7, "d4"), (8, "d7"), (9, "e7")]
    assert held["cuts"] == [{"read": "land.1@9"}] and held["note"].startswith(said("land.1@9"))
    joined = ask(cat, op="join", a=A, **SOLO_ONLY)                 # read at 11; 12 and 13 land
    assert joined["cut"] == "land.1@11" and joined["note"].startswith(said("land.1@11"))
    assert joined["cuts"] == [{"read": "land.1@4"}, {"read": "land.1@11"}]
    series = ask(cat, op="measure", **SOLO_ONLY)                   # read at 13; 14 and 15 land
    assert [(s["cut"], s["value"]) for s in series["series"]] == [("land.1@13", 3)]
    assert series["cuts"] == [{"read": "land.1@13"}]
    assert series["note"].startswith(said("land.1@13"))
    named = ask(cat, op="head", **SOLO_ONLY)                       # read at 15; 16 and 17 land
    assert named["cut"] == "land.1@15" and named["cuts"] == [{"read": "land.1@15"}]
    assert cat.head(1) == 17


def test_a_call_is_bounded_by_the_cuts_its_statement_names(cat: VaultCatalog) -> None:
    """A symmetric difference names each operand once, so thirty-one nested in one call make a
    statement that names thirty-two cuts, where writing each as two differences would double it
    at every level. A call whose sets would name more than `TERMS` cuts, counted each time the
    statement names one, is refused with the bound, and nothing but the heads is read."""
    names = [A, "land.1@5", "head"]
    nested: dict[str, Any] = {"op": "held", "a": names[0]}
    for i in range(1, cut_tool.DEPTH):
        nested = {"op": "symmetric_difference", "a": nested, "b": names[i % 3]}
    rows = {n: {(r["chain"], r["seq"]) for r in
                ask(cat, op="held", a=n, list=True, **SOLO_ONLY)["rows"]} for n in names}
    want = rows[names[0]]
    for i in range(1, cut_tool.DEPTH):
        want = want ^ rows[names[i % 3]]
    seen: list[str] = []
    answer = ask(cat, seen=seen, op="count", a=nested, **SOLO_ONLY)
    assert answer["value"] == len(want)
    assert seen[-1].count("closed_at IS NULL OR closed_at >") <= cut_tool.DEPTH + 1
    family = ["head"] * cut_tool.FAMILY
    big: dict[str, Any] = {"op": "existed", "cuts": family}
    for _ in range(cut_tool.TERMS // cut_tool.FAMILY):
        big = {"op": "union", "a": big, "b": {"op": "existed", "cuts": family}}
    seen.clear()
    with pytest.raises(CutError, match=rf"a call's sets name at most {cut_tool.TERMS} cuts, "
                                       rf".* and this call's name "
                                       rf"{cut_tool.TERMS + cut_tool.FAMILY}$"):
        ask(cat, seen=seen, op="count", a=big, **SOLO_ONLY)
    assert len(seen) == 1 and seen[0].startswith(START)


def test_a_set_or_a_difference_or_a_number_where_a_cut_is_expected_is_refused_by_type(
        cat: VaultCatalog) -> None:
    refusals: list[tuple[dict[str, Any], str]] = [
        ({"op": "join", "a": {"op": "held"}, "b": "head"},
         "join takes a cut as a, and a set of versions was given"),
        ({"op": "delta", "a": {"op": "count"}},
         "delta takes a cut as a, and a number was given"),
        ({"op": "held", "a": {"op": "delta", "a": A}},
         "held takes a cut as a, and a signed difference was given"),
        ({"op": "apply", "a": A, "b": "head"},
         "apply takes a signed difference as b, and a cut was given"),
        ({"op": "union", "a": {"op": "between", "a": A}, "b": "head"},
         "union takes a set of versions or a cut as a, and the events between two cuts"),
        ({"op": "persisted", "cuts": [A, {"op": "held"}]},
         "persisted takes a cut as a member of cuts, and a set of versions was given"),
        ({"op": "meet", "a": {"op": "order", "a": A}, "b": "head"},
         "meet takes a cut as a, and an order was given"),
    ]
    for args, said in refusals:
        with pytest.raises(CutError, match=said):
            ask(cat, **args)


def test_a_position_past_the_head_is_refused_with_the_head(cat: VaultCatalog) -> None:
    with pytest.raises(CutError, match=r"land.1@8 is past the chain's head, land.1@7"):
        ask(cat, op="held", a="land.1@8")
    with pytest.raises(CutError, match=r"land.2@4 is past the chain's head, land.2@3"):
        ask(cat, op="delta", a="bottom", b="land.1@7 land.2@4")


def test_a_chain_the_grant_does_not_read_is_refused_as_one_that_does_not_exist(
        cat: VaultCatalog) -> None:
    """Under a grant that reads authored-solo alone, land.2 is refused in the words used for
    land.9, which no catalog has; the answer names land.1 alone; and `over` cannot name a class
    the grant does not read."""
    with pytest.raises(CutError) as unread:
        ask(cat, ["authored-solo"], op="held", a="land.2@1")
    with pytest.raises(CutError) as absent:
        ask(cat, ["authored-solo"], op="held", a="land.9@1")
    assert str(unread.value).replace("land.2", "land.N") == \
        str(absent.value).replace("land.9", "land.N") == \
        "there is no chain land.N; the chains read here are land.1"
    assert ask(cat, ["authored-solo"], op="head")["cut"] == "land.1@7"
    with pytest.raises(CutError, match="over names a class this grant does not read: curated"):
        ask(cat, ["authored-solo"], op="head", over=["curated"])


def test_the_note_says_the_head_the_horizon_the_holes_and_what_waits_for_sn4(
        tmp_path: Path) -> None:
    """With no cut named the note says the head was read, once for the call, and names it. A
    position under a chain's horizon, inside its genesis, is read at 0, and the note and the cuts
    read say so. The holes a purge left in the ranges read are counted. And every note ends by
    saying the result is of versions, and that edges and graph mathematics wait for SN-4."""
    db = tmp_path / "catalog.sqlite"
    import sqlite3
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE vault_files (source_path TEXT PRIMARY KEY, digest TEXT NOT "
                     "NULL, title TEXT NOT NULL, provenance TEXT NOT NULL DEFAULT "
                     "'authored-solo', active INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT "
                     "NULL, doc_id TEXT)")
        conn.executemany("INSERT INTO vault_files VALUES (?, ?, ?, 'authored-solo', 1, "
                         "'2026-11-01', ?)", [("v/a.md", "da", "A", "v/a.md"),
                                              ("v/b.md", "db", "B", "v/b.md")])
    cat = VaultCatalog(db)                  # the genesis: land.1@1 to land.1@4, the horizon
    cat.record("v/a.md", "da2", "A")        # land.1@5 closes v/a.md's genesis row
    answer = ask(cat, ["authored-solo"], op="delta")
    assert answer["note"].startswith("No cut was named for an operand, so the head was read, "
                                     "once for the whole call: land.1@5.")
    assert answer["note"].endswith(cut_tool.GRAPH)
    assert answer["cuts"] == [{"read": "land.1@5"}]
    under = ask(cat, ["authored-solo"], op="held", a="land.1@2")
    assert under["count"] == 0
    assert under["cuts"] == [{"read": "land.1@0", "asked": "land.1@2"}]
    assert "land.1 was read at 0, below the position asked, 2: the positions under a chain's " \
           "horizon are its genesis" in under["note"]
    assert ask(cat, ["authored-solo"], op="held", a="land.1@4")["count"] == 2
    assert "No row of the ranges read is a hole." in under["note"]
    both = ask(cat, ["authored-solo"], op="union", a="land.1@2", b="land.1@3")
    assert both["cuts"] == [{"read": "land.1@0", "asked": "land.1@2"},
                            {"read": "land.1@0", "asked": "land.1@3"}]
    assert "below the position asked, 2:" in both["note"]
    assert "below the position asked, 3:" in both["note"]
    assert cat.active_refs("da") == 0
    cat.remove_digest("da")                 # v/a.md's first version, a hole from now on
    purged = ask(cat, ["authored-solo"], op="held", a="land.1@4")
    assert purged["count"] == 1
    assert "1 row of the ranges read is a hole: versions a purge emptied, which no set holds." \
        in purged["note"]
    for a in (ask(cat, ["authored-solo"], op=op) for op in ("head", "between", "measure")):
        assert a["note"].endswith(cut_tool.GRAPH)
    cat.close()


def test_a_cut_that_splits_a_change_of_class_is_read_as_asked_and_the_note_says_so(
        tmp_path: Path) -> None:
    """A change of class writes a `leave` in the chain the path leaves and then a `store` in the
    chain of its new class. A cut that holds the `store` and not the `leave` holds the path in
    both chains, and one that holds the `leave` and not the `store` in neither; no reference of
    §3.5 lowers either, so each is read as asked, and the note says that such a cut can split a
    change of class (§7.5). The head, a cut of one chain and an answer that reads no contents
    say nothing of it."""
    cat = VaultCatalog(tmp_path / "catalog.sqlite")
    cat.record("a.md", "d1", "A", provenance=SOLO)       # land.1: genesis, horizon, a.md at 3
    cat.record("b.md", "d2", "B", provenance=CURATED)    # land.2: genesis, horizon, b.md at 3
    cat.record("a.md", "d1", "A", provenance=CURATED)    # land.1@4 its leave, land.2@4 a.md
    twice = ask(cat, op="held", a="land.1@3 land.2@4", list=True)
    assert [(r["chain"], r["path"]) for r in twice["rows"]] == [
        (1, "a.md"), (2, "b.md"), (2, "a.md")]
    assert twice["cuts"] == [{"read": "land.1@3 land.2@4"}]
    assert cut_tool.SPLIT in twice["note"]
    neither = ask(cat, op="held", a="land.1@4 land.2@3", list=True)
    assert [r["path"] for r in neither["rows"]] == ["b.md"]
    assert cut_tool.SPLIT in neither["note"]
    for quiet in (ask(cat, op="held"), ask(cat, ["curated"], op="held", a="land.2@3"),
                  ask(cat, op="join", a="land.1@3 land.2@4", b="bottom")):
        assert cut_tool.SPLIT not in quiet["note"]
    cat.close()


def test_list_returns_the_rows_and_says_when_the_limit_cut_them(cat: VaultCatalog) -> None:
    one = ask(cat, op="held", list=True, limit=1, **SOLO_ONLY)
    assert one["count"] == 2 and len(one["rows"]) == 1 and one["truncated"] is True
    assert "rows" not in ask(cat, op="held", **SOLO_ONLY)
    listed = ask(cat, op="delta", a=A, list=True, **SOLO_ONLY)["rows"]
    assert [r["path"] for r in listed["removed"]] == ["b.md"]
    assert [r["path"] for r in listed["added"]] == ["c.md"]
    assert [(p["from"]["digest"], p["to"]["digest"]) for p in listed["replaced"]] == \
        [("d1", "d3")]
    assert set(listed["removed"][0]) == {"chain", "seq", "path", "identity", "digest", "title",
                                         "version"}


def test_the_same_call_with_the_positions_printed_is_the_same_answer_later(
        cat: VaultCatalog) -> None:
    """An answer prints the head it read by its positions; asked again with them after further
    writes, the call gives the same answer, where the head itself has moved (D27)."""
    first = ask(cat, op="delta", a=A, **SOLO_ONLY)
    printed = first["cuts"][-1]["read"]
    cat.record("d.md", "d5", "D")
    cat.record("a.md", "d6", "A")
    again = ask(cat, op="delta", a=A, b=printed, **SOLO_ONLY)
    moved = ask(cat, op="delta", a=A, **SOLO_ONLY)
    keys = ("removed", "added", "replaced")
    assert [again[k] for k in keys] == [first[k] for k in keys] == [1, 1, 1]
    assert [moved[k] for k in keys] == [1, 2, 1]


def test_what_the_tool_does_not_take_is_refused(cat: VaultCatalog) -> None:
    refusals: list[tuple[dict[str, Any], str]] = [
        ({"op": "nope"}, "op is one of head"),
        ({"op": "held", "sentence": "x"}, "no argument sentence"),
        ({"op": "held", "a": {"op": "held", "over": ["curated"]}},
         "are arguments of the outermost call"),
        ({"op": "head", "a": A}, "head takes no operand, and was given a"),
        ({"op": "held", "b": A}, "held takes a, and was given b"),
        ({"op": "held", "limit": 0}, "limit is a whole number from 1 to 1000"),
        ({"op": "held", "list": "yes"}, "list is true or false"),
        ({"op": "held", "a": 3}, "an operand is a cut's name or a call"),
        ({"op": "held", "a": "land.1@2 land.1@3"}, "land.1 is named twice"),
        ({"op": "held", "a": "yesterday"}, "'yesterday' is not a position"),
        ({"op": "measure", "of": "degree"}, "the one measure at this stage is count"),
        ({"op": "persisted", "cuts": ["head"] * 65}, "a family has at most 64 cuts"),
        ({"op": "compose", "a": {"op": "delta", "a": A}, "b": {"op": "delta", "a": A}},
         "compose through the cut they share"),
        ({"op": "compose", "a": {"op": "delta", "a": "bottom", "b": "head"},
          "b": {"op": "delta", "a": "head", "b": A}}, "not between"),
    ]
    for args, said in refusals:
        with pytest.raises(CutError, match=said):
            ask(cat, **args)
    deep: dict[str, Any] = {"op": "held"}
    for _ in range(40):
        deep = {"op": "union", "a": deep, "b": "head"}
    with pytest.raises(CutError, match="a call nests at most 32 calls"):
        ask(cat, **deep)


def test_the_schema_names_every_operator_and_argument() -> None:
    assert cut_tool.SCHEMA["required"] == ["op"]
    assert cut_tool.SCHEMA["properties"]["op"]["enum"] == sorted(cut_tool.OPERATORS)
    assert set(cut_tool.SCHEMA["properties"]) == set(cut_tool.ARGUMENTS)
