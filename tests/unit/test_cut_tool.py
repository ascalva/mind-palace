"""The `cut` tool's handler, called as the MCP server calls it (dn-temporal-snapshot §7.5, SN-1b).

The server decodes a call's arguments from JSON and passes them to the handler, and writes the
answer back as JSON (`agents/ambassador/mcp.py`, `Server.handle`); `ask` does the same around
`agents/ambassador/cut_tool.py::cut`. The property, the tenth of §12's list for SN-1b: every
operator answers by its name; an operand may be a call, and the whole call is one expression read
when the outermost operator needs it; a set, a signed difference or a number given where a cut is
expected is refused by its type; a position past a chain's head is refused with the head; a chain
the grant does not read is refused in the words used for one that does not exist; and the note
says that the head was read where no cut was named, which chain was read below the position
asked, how many rows of the ranges read are holes, and that edges and graph mathematics at a cut
arrive with SN-4. The registration in the server is `tests/unit/test_ambassador_surface.py`'s.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest

from agents.ambassador import cut_tool
from core.kernel.provenance import Provenance
from core.stores.catalog import VaultCatalog
from core.stores.cuts import CutError

SOLO, CURATED = Provenance.AUTHORED_SOLO, Provenance.CURATED
BOTH = ["authored-solo", "curated"]


def ask(cat: VaultCatalog, classes: Iterable[str] = BOTH, **arguments: Any) -> dict[str, Any]:
    """A call as the server makes it: the arguments through JSON, the answer back through it."""
    answer = cut_tool.cut(cat, classes, json.loads(json.dumps(arguments)))
    text = json.dumps(answer, ensure_ascii=False)            # plain JSON: no default needed
    out: dict[str, Any] = json.loads(text)
    return out


@pytest.fixture
def cat() -> Iterable[VaultCatalog]:
    """A chain of authored-solo notes, land.1, and one of curated papers, land.2. land.1: the
    genesis and the horizon at 1 and 2, a.md and b.md at 3 and 4; then a.md edited at 5, b.md
    retired at 6 and c.md landed at 7. land.2: x.md at 3."""
    c = VaultCatalog(Path(":memory:"))
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


def test_an_operand_may_be_a_call_and_nothing_is_read_before_the_outermost_needs_it(
        cat: VaultCatalog) -> None:
    """The union of two differences is one call with a `difference` in `a` and another in `b`:
    the whole is one expression, and it is read by one statement when its count is asked."""
    seen: list[str] = []
    cat._conn.set_trace_callback(seen.append)
    answer = ask(cat, op="union", a={"op": "difference", "a": "head", "b": A},
                 b={"op": "difference", "a": A, "b": "head"}, **SOLO_ONLY)
    cat._conn.set_trace_callback(None)
    assert answer["count"] == 4
    reads = [q for q in seen if "count(salt)" in q]
    assert len(reads) == 1
    assert [c["read"] for c in answer["cuts"]] == ["land.1@7", "land.1@4"]


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
    assert cat.active_refs("da") == 0
    cat.remove_digest("da")                 # v/a.md's first version, a hole from now on
    purged = ask(cat, ["authored-solo"], op="held", a="land.1@4")
    assert purged["count"] == 1
    assert "1 row of the ranges read is a hole: versions a purge emptied, which no set holds." \
        in purged["note"]
    for a in (ask(cat, ["authored-solo"], op=op) for op in ("head", "between", "measure")):
        assert a["note"].endswith(cut_tool.GRAPH)
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
