"""The `cut` tool: the algebra of cuts on the palace's MCP surface (dn-temporal-snapshot §7.5).

One tool, `cut`, over the engine (`core/stores/cuts.py`). A call names an operator, `op`, and its
operands: `a` and `b`, each a cut's name or a call of the tool written as an object with its own
`op`, whose result is the operand, and `cuts`, a family of them. So a result is an operand again,
and a whole call composes to one expression. What a call reads, in order: the heads of the chains
when it starts; the horizon of a chain, once, when a position under the chain's head is named on
it (§7.1); and then what its outermost operator needs, a set of any depth by one statement. A cut
is named `head`, `bottom`, or by its positions, `land.<chain>@<seq>` one a chain, separated by
spaces, a chain left out standing at 0; every answer prints the cuts it read that way, so a cut is
copied from an answer into a question. An operand left out is the head, read once when the call
starts, and every operand that is the head is that one cut (D27). `over` names the provenance
classes whose chains are read, every class the asker's grant reads by default; `list` returns the
rows beside the counts, the first `limit` of them.

Union and intersection have both meanings under different names (D22, D26): `join` and `meet`
take cuts and return a cut, `union` and `intersection` take sets and return a set. A cut given
where a set is expected is the set it holds; a set, a signed difference or a number given where a
cut is expected is refused, and the refusal names what was given and what the operator takes.

The answer is one object: `op` and `type`, `cuts` (every cut the call read, in the order the
expression names them, each by its positions on the chains read, and once beside each cut asked
for it where the two differ), the result, `rows` when `list` is set, and `note`. A position past a
chain's head is refused with the head; a chain the grant does not read is refused in the words used
for a chain that does not exist; a position under a chain's horizon is read at the chain's empty
prefix, and the note says so. A cut over two chains or more that is neither the head nor the
bottom can split a change of class, which writes a `leave` in one chain and the `store` in
another, and the note says that too (§3.5). A call's sets name at most `TERMS` cuts, counted each
time their statement names one, so a short call cannot ask for a statement of any size. The
handler reads through the connection it is given, which the server opens to only read
(`core.stores.cuts.read_only`): it takes no lock a writer waits on and writes nothing. It is not
yet the graph: edges and graph mathematics at a cut arrive with SN-4.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from core.stores.cuts import (
    BOTTOM,
    Columns,
    Cut,
    CutError,
    Delta,
    Evaluation,
    Events,
    Series,
    Table,
    Versions,
)

# What each operator takes, by argument: "cut", "set" (a cut is the set it holds), "delta", or
# "family" (a list of cuts in `cuts`). An operand an operator does not take is refused.
OPERATORS: dict[str, dict[str, str]] = {
    "head": {}, "bottom": {},
    "join": {"a": "cut", "b": "cut"}, "meet": {"a": "cut", "b": "cut"},
    "order": {"a": "cut", "b": "cut"}, "between": {"a": "cut", "b": "cut"},
    "held": {"a": "cut"},
    "union": {"a": "set", "b": "set"}, "intersection": {"a": "set", "b": "set"},
    "difference": {"a": "set", "b": "set"}, "symmetric_difference": {"a": "set", "b": "set"},
    "delta": {"a": "cut", "b": "cut"},
    "apply": {"a": "set", "b": "delta"}, "compose": {"a": "delta", "b": "delta"},
    "persisted": {"cuts": "family"}, "existed": {"cuts": "family"},
    "count": {"a": "set"},
    "in_how_many": {"cuts": "family", "a": "set"},
    "measure": {"cuts": "family", "of": "measure"},
    "pairwise": {"cuts": "family"},
}
ARGUMENTS = ("op", "a", "b", "cuts", "of", "over", "list", "limit")
OUTER = ("over", "list", "limit")         # arguments of the call, not of an operand
MEASURES = ("count",)                     # SN-4 adds the measures of a graph
DEPTH = 32                                # calls nested in one call, at most
FAMILY = 64                               # cuts in a family, at most
LIMIT = 1000                              # rows listed, at most
# Cuts a call's sets name, counted each time their statement names one (`Versions.terms`), at
# most: the bound on the statement's size, which DEPTH does not give, since an operator that
# repeats an operand, as a composition of differences does, makes the expression larger than the
# call that asks for it.
TERMS = 256
LISTED = ("source_path", "doc_id", "digest", "title", "version")
GRAPH = ("The result is of the versions the landing log holds. It is not yet the graph: edges "
         "and graph mathematics at a cut arrive with SN-4.")
# Said when a result of what cuts hold read two chains or more at a cut that is neither the head
# nor the bottom (dn-temporal-snapshot §3.5, §7.5): such a cut is read as asked, and it can split
# the two rows a change of class writes.
SPLIT = ("A cut that is neither the head nor the bottom can split a change of class, which "
         "writes a leave in the chain a path leaves and then a store in the chain of its new "
         "class: read at such a cut, a path that changed class there is held in both chains or "
         "in neither.")

_OPERAND = {"type": ["string", "object"],
            "description": "a cut: head, bottom, or land.<chain>@<seq> one a chain; or a call "
                           "{op, a, b, cuts, of}, whose result is the operand. Left out: the head"}
DESCRIPTION = (
    "The algebra of cuts: a cut is the palace as of one position a landing chain, read only when "
    "an operator needs it. Name a cut head, bottom, or by its positions, land.<chain>@<seq> "
    "separated by spaces (a chain left out stands at 0), as every answer prints it; an operand "
    "left out is the head, read once a call. Operators: head, bottom; join and meet of two cuts "
    "(a cut: the union and intersection on positions); order; between (the events after a and "
    "up to b); held (the versions a cut holds); union, intersection, difference and "
    "symmetric_difference of two sets (a cut is the set it holds: the union on contents keeps "
    "both versions of an edited note, where join keeps the later); delta (the signed "
    "difference: removed, added, replaced); apply (a set and a delta); compose (two deltas that "
    "share a cut between them); persisted and existed over cuts; count; in_how_many; measure "
    "(of: count) and pairwise over cuts. An operand may be a call written as an object. list: "
    "true lists the rows. The versions only: edges and graph mathematics at a cut arrive later.")
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "op": {"enum": sorted(OPERATORS)},
        "a": _OPERAND,
        "b": _OPERAND,
        "cuts": {"type": "array", "items": _OPERAND, "maxItems": FAMILY},
        "of": {"enum": list(MEASURES)},
        "over": {"type": "array", "items": {"type": "string"},
                 "description": "the provenance classes read; every class the grant reads "
                                "by default"},
        "list": {"type": "boolean", "description": "list the rows beside the counts"},
        "limit": {"type": "integer", "minimum": 1, "maximum": LIMIT},
    },
    "required": ["op"],
}


@dataclass
class _Call:
    """One call's evaluation: the engine's evaluation, which read the head once, and what the
    answer says of the cuts it read."""

    ev: Evaluation
    # each cut read, in the order the expression names them, with every cut asked for it that
    # is not the cut itself: two names lowered to one cut are both kept
    read: dict[Cut, list[Cut]] = field(default_factory=dict)
    lowered: list[tuple[int, int]] = field(default_factory=list)
    headed: bool = False                                          # an operand was left out

    def saw(self, c: Cut, asked: Cut | None = None) -> Cut:
        names = self.read.setdefault(c, [])
        if asked is not None and asked != c and asked not in names:
            names.append(asked)
        return c


@dataclass(frozen=True)
class _Count:
    """A count of a set, asked and not yet read: a number, and no operand of any operator."""

    of: Versions


@dataclass(frozen=True)
class _Counted:
    """In how many cuts of a family each row of a set is held, asked and not yet read: the rows
    are read when the answer is written, the first `limit` of them."""

    of: Versions
    cuts: tuple[Cut, ...]


def _bounded(v: object) -> object:
    """`v`, refused when its sets name more than `TERMS` cuts: checked on every value a call
    builds, before a statement is written."""
    match v:
        case Versions():
            n = v.terms
        case Delta():
            n = v.gone.terms + v.come.terms
        case _Count() | _Counted():
            n = v.of.terms
        case _:
            return v
    if n > TERMS:
        raise CutError(f"a call's sets name at most {TERMS} cuts, counted each time the statement "
                       f"they run as names one, and this call's name {n}")
    return v


def _kind(v: object) -> str:
    match v:
        case Cut():
            return "a cut"
        case Versions():
            return "a set of versions"
        case Delta():
            return "a signed difference"
        case Events():
            return "the events between two cuts"
        case Series():
            return "a series"
        case Table():
            return "a table"
        case _Counted():
            return "rows counted over a family"
        case _Count():
            return "a number"
        case str():
            return "an order"
        case int():
            return "a number"
    return type(v).__name__


def _operand(call: _Call, x: object, depth: int) -> object:
    """An operand's value: the head for none, a cut for a name, a call's result for an object."""
    if x is None:
        call.headed = True
        return call.saw(call.ev.head)
    if isinstance(x, str):
        asked = call.ev.named(x)
        read, lowered = call.ev.served(asked)
        call.lowered += [w for w in lowered if w not in call.lowered]
        return call.saw(read, asked)
    if isinstance(x, Mapping):
        return _evaluate(call, x, depth + 1)
    raise CutError(f"an operand is a cut's name or a call written as an object, not "
                   f"{type(x).__name__}")


def _cut(op: str, which: str, v: object) -> Cut:
    if isinstance(v, Cut):
        return v
    raise CutError(f"{op} takes a cut as {which}, and {_kind(v)} was given")


def _set(call: _Call, op: str, which: str, v: object) -> Versions:
    if isinstance(v, Cut):
        return call.ev.held(v)
    if isinstance(v, Versions):
        return v
    raise CutError(f"{op} takes a set of versions or a cut as {which}, and {_kind(v)} was given")


def _delta(op: str, which: str, v: object) -> Delta:
    if isinstance(v, Delta):
        return v
    raise CutError(f"{op} takes a signed difference as {which}, and {_kind(v)} was given")


def _evaluate(call: _Call, args: Mapping[str, Any], depth: int = 0) -> object:
    """One call's result, lazy where it is a cut, a set, a signed difference or events, and
    refused when its sets name more than `TERMS` cuts."""
    return _bounded(_value(call, args, depth))


def _value(call: _Call, args: Mapping[str, Any], depth: int) -> object:
    if depth > DEPTH:
        raise CutError(f"a call nests at most {DEPTH} calls")
    op = args.get("op")
    if not isinstance(op, str) or op not in OPERATORS:
        raise CutError(f"op is one of {', '.join(OPERATORS)}, not {op!r}")
    unknown = [k for k in args if k not in ARGUMENTS]
    if unknown:
        raise CutError(f"no argument {', '.join(map(str, unknown))}; a call takes "
                       f"{', '.join(ARGUMENTS)}")
    if depth and any(k in args for k in OUTER):
        raise CutError(f"{', '.join(OUTER)} are arguments of the outermost call, not of an "
                       "operand")
    takes = OPERATORS[op]
    extra = [k for k in ("a", "b", "cuts", "of") if k in args and args[k] is not None
             and k not in takes]
    if extra:
        raise CutError(f"{op} takes {', '.join(takes) or 'no operand'}, and was given "
                       f"{', '.join(extra)}")
    if op == "head":
        return call.saw(call.ev.head)
    if op == "bottom":
        return call.saw(BOTTOM)
    if "cuts" in takes:
        fam = _family(call, op, args.get("cuts"), depth)
        if op == "persisted":
            return call.ev.persisted(fam)
        if op == "existed":
            return call.ev.existed(fam)
        if op == "pairwise":
            return call.ev.pairwise(fam)
        if op == "measure":
            of = args.get("of") or "count"
            if of not in MEASURES:
                raise CutError(f"the one measure at this stage is count, not {of!r}; the "
                               "measures of a graph arrive with SN-4")
            return call.ev.count_series(fam)
        return _Counted(_set(call, op, "a", _operand(call, args.get("a"), depth)), tuple(fam))
    a = _operand(call, args.get("a"), depth)
    if op == "held":
        return call.ev.held(_cut(op, "a", a))
    if op == "count":
        return _Count(_set(call, op, "a", a))
    b = _operand(call, args.get("b"), depth)
    if takes["a"] == "cut":
        x, y = _cut(op, "a", a), _cut(op, "b", b)
        if op == "join":
            return call.saw(x.join(y))
        if op == "meet":
            return call.saw(x.meet(y))
        if op == "order":
            return x.order(y)
        if op == "between":
            return call.ev.between(x, y)
        return call.ev.delta(x, y)
    if op == "apply":
        return _delta(op, "b", b).apply(_set(call, op, "a", a))
    if op == "compose":
        return _delta(op, "a", a).then(_delta(op, "b", b))
    p, q = _set(call, op, "a", a), _set(call, op, "b", b)
    return {"union": p | q, "intersection": p & q, "difference": p - q,
            "symmetric_difference": p ^ q}[op]


def _family(call: _Call, op: str, cuts: object, depth: int) -> list[Cut]:
    if cuts is None or cuts == []:
        call.headed = True
        return [call.saw(call.ev.head)]
    if not isinstance(cuts, list):
        raise CutError(f"{op} takes cuts as a list of cuts")
    if len(cuts) > FAMILY:
        raise CutError(f"a family has at most {FAMILY} cuts, and {len(cuts)} were given")
    return [_cut(op, "a member of cuts", _operand(call, x, depth)) for x in cuts]


def _row(cols: Columns, i: int) -> dict[str, object]:
    """One row as the answer lists it: its chain and position, path, identity, digest, title,
    version number, and its kind for an event."""
    raw = cols.row(i)
    names = {"source_path": "path", "doc_id": "identity"}
    return {names.get(k, k): v for k, v in raw.items()
            if k in ("chain", "seq", "kind", *LISTED)}


def _rows(cols: Columns, limit: int) -> list[dict[str, object]]:
    return [_row(cols, i) for i in range(min(len(cols), limit))]


def _answer(call: _Call, value: object, listing: bool,
            limit: int) -> tuple[dict[str, Any], int | None]:
    """The result's part of the answer, and the holes in the ranges it read (`None` where it
    read no range)."""
    out: dict[str, Any] = {}
    holes: int | None = None
    chains = call.ev.chains
    if isinstance(value, Cut):
        out["type"], out["cut"] = "cut", value.name(chains)
    elif isinstance(value, str):
        out["type"], out["order"] = "order", value
    elif isinstance(value, Events):
        out["type"] = "events"
        out["count"], holes = value.tally()
        if listing:
            cols = value.columns("kind", *LISTED, limit=limit)
            out["rows"], out["truncated"] = _rows(cols, limit), out["count"] > limit
    elif isinstance(value, _Count):
        out["type"] = "number"
        out["value"], holes = value.of.tally()
    elif isinstance(value, Versions):
        n, holes = value.tally()
        out["type"], out["count"] = "set", n
        if listing:
            cols = value.columns(*LISTED, limit=limit)
            out["rows"], out["truncated"] = _rows(cols, limit), n > limit
    elif isinstance(value, Delta):
        counts = value.counts()
        holes = counts.holes
        out["type"] = "delta"
        out["removed"], out["added"], out["replaced"] = (counts.removed, counts.added,
                                                         counts.replaced)
        if listing:
            s = value.sorted(*LISTED, limit=limit)
            old, new = s.replaced
            out["rows"] = {"removed": _rows(s.removed, limit), "added": _rows(s.added, limit),
                           "replaced": [{"from": _row(old, i), "to": _row(new, i)}
                                        for i in range(len(old))]}
            out["truncated"] = max(counts.removed, counts.added, counts.replaced) > limit
    elif isinstance(value, _Counted):
        out["type"] = "rows"
        n, holes = value.of.tally()
        out["count"] = n
        counted = call.ev.in_how_many(value.of, value.cuts, names=LISTED, limit=limit)
        out["rows"] = [{**_row(counted.rows, i), "cuts_holding": int(counted.counts[i])}
                       for i in range(len(counted.rows))]
        out["truncated"] = n > limit
        out["held_by_every_cut"] = (value.of & call.ev.persisted(value.cuts)).count()
    elif isinstance(value, Series):
        out["type"] = "series"
        out["series"] = [{"cut": c.name(chains), "value": v}
                         for c, v in zip(value.cuts, value.values, strict=True)]
        holes = call.ev.existed(list(value.cuts)).holes()
    elif isinstance(value, Table):
        out["type"] = "table"
        out["table"] = {"cuts": [c.name(chains) for c in value.cuts],
                        "sizes": [list(r) for r in value.sizes]}
        holes = call.ev.existed(list(value.cuts)).holes()
    return out, holes


# The results that read what cuts hold, and so can show a change of class split (SPLIT).
CONTENTS = (Versions, Delta, _Count, _Counted, Series, Table)


def cut(conn: sqlite3.Connection, classes: Iterable[str], arguments: Mapping[str, Any]
        ) -> dict[str, Any]:
    """The `cut` tool's answer to one call, read through `conn`, a connection to the catalog's
    file that the server opens to only read (`core.stores.cuts.read_only`), under a grant that
    reads `classes`: the arguments as the server's dispatch passes them, decoded from the call's
    JSON."""
    unknown = [k for k in arguments if k not in ARGUMENTS]
    if unknown:
        raise CutError(f"no argument {', '.join(map(str, unknown))}; the tool takes "
                       f"{', '.join(ARGUMENTS)}")
    readable = sorted({str(c) for c in classes})
    over = arguments.get("over")
    if over is None:
        over = readable
    elif not isinstance(over, list) or not all(isinstance(c, str) for c in over):
        raise CutError("over is a list of provenance classes")
    elif any(c not in readable for c in over):
        unread = ", ".join(sorted(set(over) - set(readable)))
        raise CutError(f"over names a class this grant does not read: {unread}; it reads "
                       f"{', '.join(readable)}")
    listing = arguments.get("list", False)
    if not isinstance(listing, bool):
        raise CutError("list is true or false")
    limit = arguments.get("limit", 50)
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= LIMIT:
        raise CutError(f"limit is a whole number from 1 to {LIMIT}")
    op = str(arguments.get("op"))
    call = _Call(Evaluation(conn, over))
    value = _evaluate(call, arguments)
    result, holes = _answer(call, value, listing, limit)
    chains = call.ev.chains
    answer: dict[str, Any] = {
        "op": op, "type": result.pop("type"),
        "cuts": [{"read": c.name(chains), **({"asked": a.name(chains)} if a is not None else {})}
                 for c, asked in call.read.items() for a in (asked or (None,))],
        **result,
    }
    note = []
    if call.headed:
        note.append(f"No cut was named for an operand, so the head was read, once for the "
                    f"whole call: {call.ev.head.name(chains)}.")
    for k, p in call.lowered:
        note.append(f"land.{k} was read at 0, below the position asked, {p}: the positions under "
                    "a chain's horizon are its genesis, which is not history, and are not "
                    "served.")
    if (len(chains) > 1 and isinstance(value, CONTENTS)
            and any(c not in (call.ev.head, BOTTOM) for c in call.read)):
        note.append(SPLIT)
    if holes is not None:
        note.append("No row of the ranges read is a hole." if holes == 0 else
                    f"{holes} {'row' if holes == 1 else 'rows'} of the ranges read "
                    f"{'is a hole' if holes == 1 else 'are holes'}: versions a purge emptied, "
                    "which no set holds.")
    note.append(GRAPH)
    answer["note"] = " ".join(note)
    return answer
