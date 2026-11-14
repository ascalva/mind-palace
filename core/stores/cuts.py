"""The cut as a value, and its algebra over the landing log (dn-temporal-snapshot §4.4, SN-1b).

A cut is a frontier: one position a chain of the landing log (`core/stores/landings.py`), a few
integers that can be compared, hashed, stored and printed (`Cut`). It stands for what the store
held as of it, and nothing is read until an operation needs it. Every read happens inside an
`Evaluation`: the log's connection, the chains of the classes the asker reads, and the head of
each, read once when the evaluation starts. An operation that names no cut uses that head, so
every part of one answer reads one cut, and every result names the cuts it reads (D27).

**On positions** the cuts inside the log are a lattice: `Cut.join` and `Cut.meet` are the
pointwise maximum and minimum, the bottom is the empty cut, and the head is the one cut that moves
(SNP-11). The difference of two cuts on positions is the events between them (`Events`).

**On contents** a cut holds its versions: the `store` rows of the log that no purge emptied, each
alive from its position up to, and not at, its closing stamp (SNP-12). A set of versions
(`Versions`) is an expression over the contents of cuts under union, intersection and difference,
with no complement (SNP-14). Combining two sets runs no statement: whether a row is in a set is a
predicate on its position and its closing stamp, so a set of any depth is read by one statement.
A count builds no row, and the rows come back as columns, one buffer a column (`Columns`). The
signed difference of two cuts (`Delta`) is two such sets, the versions gone and the versions come,
whose statements walk what changed between the two cuts (SNP-13); read, they sort by path within a
chain into removed, added and replaced.

Union and intersection are kept in both meanings, under different names and types (D22, D26):
`Cut.join` and `Cut.meet` take cuts and return a cut, and `|` and `&` on `Versions` take sets
and return a set. The two differ: the union of the contents of two cuts holds both versions of a
note edited between them, where the contents of their join hold the later one (SNP-15).

**The interface.** An operator is a function of one cut's read (`Evaluation.apply`), of two
(`Evaluation.combine`), of each cut of a family (`Evaluation.map`), or an accumulation over a
family (`Evaluation.fold`). The named operations are written on these four, and so is any other.
A read (`Read`) is a cut with what it holds and the events up to it.

Every statement names the chains of the evaluation and no other, so a result under a grant is a
function of the chains the grant reads (SNP-16), and a row a purge emptied is in no set (SNP-17).
An evaluation needs only a connection, and one that only reads (`read_only`) takes no lock.
It is not yet the graph: edges and graph mathematics at a cut arrive with SN-4. Apart from the
cut tool (`agents/ambassador/cut_tool.py`), nothing in the palace reads this module yet.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Literal

import numpy as np
import numpy.typing as npt

type IntArray = npt.NDArray[np.int64]
type Order = Literal["equal", "before", "after", "unordered"]

# The version's own test: a landing that a purge has not emptied (§4.4). A tombstone, a `leave`,
# the genesis and the horizon carry no version; a hole is a `store` without its salt.
VERSION = "kind = 'store' AND salt IS NOT NULL"
# The columns a read of rows can ask for, by the log's own names (§3.2), and how each is read: an
# integer, the 32 bytes of a path's key, or text. An integer that is null reads -1 (positions and
# version numbers are positive); a key that is null reads 32 zero bytes; text keeps a null mask.
INTEGER = ("chain", "seq", "version", "closed_at")
KEY = ("path_key",)
TEXT = ("kind", "source_path", "doc_id", "digest", "title")
COLUMNS = (*INTEGER, *KEY, *TEXT)
_NAME = re.compile(r"land\.([0-9]+)@([0-9]+)")
_NO_KEY = "0" * 64


class CutError(ValueError):
    """A cut or an operand the algebra refuses. The message says what was given and what is
    taken, in words that are safe to show the asker."""


# --- the cut -------------------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Cut:
    """A frontier: one position a landing chain, as `(chain, position)` pairs in chain order. A
    chain the cut leaves out stands at 0, its empty prefix, so a cut keeps no zero and two equal
    cuts are one value and one key (D24). The order is the pointwise one."""

    positions: tuple[tuple[int, int], ...] = ()

    def __post_init__(self) -> None:
        chains = [k for k, _ in self.positions]
        if chains != sorted(set(chains)) or any(
                type(k) is not int or type(p) is not int or k <= 0 or p <= 0
                for k, p in self.positions):
            raise CutError("a cut is one positive position a chain, in chain order; use Cut.of")

    @classmethod
    def of(cls, positions: Mapping[int, int]) -> Cut:
        """The cut at these positions; a position of 0 is the chain's empty prefix."""
        out: list[tuple[int, int]] = []
        for k, p in sorted(positions.items()):
            if type(k) is not int or type(p) is not int or k <= 0 or p < 0:
                raise CutError(f"a cut's chain is a positive integer and its position one at "
                               f"least 0, not {k!r} at {p!r}")
            if p:
                out.append((k, p))
        return cls(tuple(out))

    @classmethod
    def parse(cls, text: str) -> Cut:
        """A cut from its positions written as an answer prints them, `land.<chain>@<seq>` one a
        chain, separated by spaces (§7.5). A chain the text leaves out stands at 0."""
        found: dict[int, int] = {}
        for word in text.split():
            m = _NAME.fullmatch(word)
            if m is None:
                raise CutError(f"{word!r} is not a position; a cut is named head, bottom, or its "
                               "positions, land.<chain>@<seq> one a chain, as land.3@412 "
                               "land.5@97")
            k, p = int(m.group(1)), int(m.group(2))
            if k in found:
                raise CutError(f"land.{k} is named twice; a cut has one position a chain")
            found[k] = p
        if not found:
            raise CutError("a cut is named head, bottom, or its positions, land.<chain>@<seq>")
        return cls.of(found)

    def at(self, chain: int) -> int:
        """The cut's position on a chain: 0 where it leaves the chain out."""
        for k, p in self.positions:
            if k == chain:
                return p
        return 0

    @property
    def chains(self) -> tuple[int, ...]:
        """The chains the cut stands above 0 on."""
        return tuple(k for k, _ in self.positions)

    def as_dict(self) -> dict[int, int]:
        return dict(self.positions)

    def join(self, other: Cut) -> Cut:
        """The union on positions: on each chain the later of the two, so everything that had
        happened by either cut (SNP-11). A cut."""
        a, b = self.as_dict(), other.as_dict()
        return Cut.of({k: max(a.get(k, 0), b.get(k, 0)) for k in a.keys() | b.keys()})

    def meet(self, other: Cut) -> Cut:
        """The intersection on positions: on each chain the earlier of the two, so everything
        that had happened by both cuts (SNP-11). A cut."""
        a, b = self.as_dict(), other.as_dict()
        return Cut.of({k: min(a.get(k, 0), b.get(k, 0)) for k in a.keys() & b.keys()})

    def __le__(self, other: Cut) -> bool:
        """Whether the cut is at or under `other` on every chain."""
        return all(p <= other.at(k) for k, p in self.positions)

    def __ge__(self, other: Cut) -> bool:
        return other <= self

    def order(self, other: Cut) -> Order:
        """How the cut stands to `other` on positions: equal, before (under it), after, or
        unordered (under it on one chain and over it on another)."""
        if self == other:
            return "equal"
        if self <= other:
            return "before"
        if other <= self:
            return "after"
        return "unordered"

    def restrict(self, chains: Iterable[int]) -> Cut:
        """The cut on the chains given and on no other."""
        keep = set(chains)
        return Cut(tuple((k, p) for k, p in self.positions if k in keep))

    def name(self, chains: Sequence[int] | None = None) -> str:
        """The cut's positions as an answer prints them (§7.5): on the chains given, zeros
        included, or on the chains it stands on; `bottom` when there is none to print."""
        ks = list(chains) if chains is not None else list(self.chains)
        return " ".join(f"land.{k}@{self.at(k)}" for k in ks) or "bottom"

    def __str__(self) -> str:
        return self.name()


BOTTOM = Cut()


def join_all(cuts: Iterable[Cut]) -> Cut:
    """The join of a family: on each chain the greatest of its positions."""
    out = BOTTOM
    for c in cuts:
        out = out.join(c)
    return out


def meet_all(cuts: Sequence[Cut]) -> Cut:
    """The meet of a family that is not empty: on each chain the least of its positions."""
    out = cuts[0]
    for c in cuts[1:]:
        out = out.meet(c)
    return out


# --- a set of versions, named and not read --------------------------------------------------------

@dataclass(frozen=True, slots=True)
class _Held:
    """What a cut holds."""

    cut: Cut
    terms: ClassVar[int] = 1


@dataclass(frozen=True, slots=True)
class _Node:
    """What either set holds, what both hold, what the first holds and the second does not, or
    what exactly one of the two holds. `terms` is how many times the statement the set runs as
    names a cut, the size of the predicate on a chain: an operand the expression shares is
    counted each time, since the statement writes it out each time."""

    op: Literal["union", "inter", "diff", "xor"]
    p: _Expr
    q: _Expr
    terms: int = field(init=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "terms", self.p.terms + self.q.terms)


type _Expr = _Held | _Node


def _atoms(e: _Expr) -> Iterator[Cut]:
    if isinstance(e, _Held):
        yield e.cut
    else:
        yield from _atoms(e.p)
        yield from _atoms(e.q)


def _predicate(e: _Expr, chain: int) -> tuple[str, list[int]] | None:
    """Whether a row of `chain` is in the set, as SQL on its position and its closing stamp and
    nothing else (`Held.has`); `None` where the set holds no row of the chain whatever the rows."""
    if isinstance(e, _Held):
        c = e.cut.at(chain)
        if c == 0:                  # nothing is alive at the empty prefix
            return None
        return "(seq <= ? AND (closed_at IS NULL OR closed_at > ?))", [c, c]
    p, q = _predicate(e.p, chain), _predicate(e.q, chain)
    if e.op in ("union", "xor"):
        if p is None or q is None:
            return p if q is None else q
        # a predicate is never null (`seq` is not, and a stamp is tested for null first), so two
        # of them differ exactly when one row is in one set: each operand is written once
        return f"({p[0]} {'OR' if e.op == 'union' else '<>'} {q[0]})", p[1] + q[1]
    if e.op == "inter":
        if p is None or q is None:
            return None
        return f"({p[0]} AND {q[0]})", p[1] + q[1]
    if p is None or q is None:
        return p
    return f"({p[0]} AND NOT {q[0]})", p[1] + q[1]


@dataclass(frozen=True, slots=True)
class _Range:
    """Bounds every row of a set on one chain lies in: its position in `(lo, hi]` and its closing
    stamp in `(died_lo, died_hi]`, `None` for no upper bound (a row still open)."""

    lo: int
    hi: int
    died_lo: int
    died_hi: int | None

    def empty(self) -> bool:
        return self.lo >= self.hi or (self.died_hi is not None and self.died_lo >= self.died_hi)


def _negated(e: _Expr) -> list[Cut]:
    """Cuts a row of `diff(p, e)` is known not to be alive at: `e`'s, when `e` is a cut or a union
    of cuts, and none otherwise (the bounds stay sound, only looser)."""
    if isinstance(e, _Held):
        return [e.cut]
    if e.op == "union":
        return _negated(e.p) + _negated(e.q)
    return []


def _range(e: _Expr, chain: int) -> _Range | None:
    """The bounds of a set on one chain, from the intervals (SNP-12): a row alive at `c` has
    `seq <= c < closed_at`, so the rows come between two cuts are a range of positions and the
    rows gone a range of closing stamps, which the statement then reads by the primary key or by
    `landings_closed`. `None` where the bounds hold no row."""
    if isinstance(e, _Held):
        c = e.cut.at(chain)
        return _Range(0, c, c, None) if c else None
    p, q = _range(e.p, chain), _range(e.q, chain)
    if e.op in ("union", "xor"):            # what exactly one holds lies inside what either does
        if p is None or q is None:
            return p if q is None else q
        hi = None if p.died_hi is None or q.died_hi is None else max(p.died_hi, q.died_hi)
        return _Range(min(p.lo, q.lo), max(p.hi, q.hi), min(p.died_lo, q.died_lo), hi)
    if e.op == "inter":
        if p is None or q is None:
            return None
        his = [h for h in (p.died_hi, q.died_hi) if h is not None]
        r = _Range(max(p.lo, q.lo), min(p.hi, q.hi), max(p.died_lo, q.died_lo),
                   min(his) if his else None)
        return None if r.empty() else r
    if p is None:
        return None
    r = p
    for cut in _negated(e.q):
        c = cut.at(chain)
        if c == 0:                  # a row is never alive at the empty prefix: nothing to learn
            continue
        lo, died_hi = r.lo, r.died_hi
        if r.died_lo >= c:          # alive past `c` and not alive at it: stored after it
            lo = max(lo, c)
        if r.hi <= c:               # stored by `c` and not alive at it: closed by it
            died_hi = c if died_hi is None else min(died_hi, c)
        r = _Range(lo, r.hi, r.died_lo, died_hi)
        if r.empty():
            return None
    return r


def _where(e: _Expr, chain: int) -> tuple[str, list[int]] | None:
    """The statement's condition for the rows of `chain` in the set, the version's test aside:
    the chain, the bounds as ranges an index can take, and the predicate itself."""
    pred, rng = _predicate(e, chain), _range(e, chain)
    if pred is None or rng is None:
        return None
    sql = ["chain = ?", "seq <= ?"]
    args: list[int] = [chain, rng.hi]
    if rng.lo > 0:
        sql.append("seq > ?")
        args.append(rng.lo)
    if rng.died_hi is not None:
        sql += ["closed_at > ?", "closed_at <= ?"]
        args += [rng.died_lo, rng.died_hi]
    elif rng.died_lo > 0:
        sql.append("(closed_at IS NULL OR closed_at > ?)")
        args.append(rng.died_lo)
    sql.append(pred[0])
    return " AND ".join(sql), args + pred[1]


class Versions:
    """A set of versions, named and not read (SNP-14): the contents of a cut, or the union, the
    intersection, the difference or the symmetric difference of two sets (`|`, `&`, `-`, `^`).
    There is no complement, so a set lies inside the contents of the cuts it names. Combining
    reads nothing; `count` runs one statement and builds no row, and `columns` reads the rows as
    one buffer a column. The statement grows with `terms`, which an operator adds and never
    multiplies: each names its operands once."""

    __slots__ = ("_ev", "_e")

    def __init__(self, ev: Evaluation, e: _Expr) -> None:
        self._ev = ev
        self._e = e

    @property
    def terms(self) -> int:
        """How many times the set's statement names a cut: the size of its predicate on a
        chain, which bounds the statement's text and its parameters (two a cut a chain)."""
        return self._e.terms

    def _with(self, op: Literal["union", "inter", "diff", "xor"], other: Versions) -> Versions:
        if not isinstance(other, Versions):
            raise CutError(f"a set of versions combines with a set of versions, not with "
                           f"{_kind(other)}")
        if other._ev is not self._ev:
            raise CutError("two sets combine inside one evaluation, which reads one head")
        return Versions(self._ev, _Node(op, self._e, other._e))

    def __or__(self, other: Versions) -> Versions:
        """What either set holds: the union on contents (D22)."""
        return self._with("union", other)

    def __and__(self, other: Versions) -> Versions:
        """What both sets hold: the intersection on contents (D22)."""
        return self._with("inter", other)

    def __sub__(self, other: Versions) -> Versions:
        """What this set holds and `other` does not."""
        return self._with("diff", other)

    def __xor__(self, other: Versions) -> Versions:
        """What exactly one of the two sets holds: the rows of `Held.symm`, the union less the
        intersection (`Held.has_symm`), as a node of its own whose statement names each operand
        once. Written as `(a - b) | (b - a)` it would name both twice, and nested, double."""
        return self._with("xor", other)

    @property
    def cuts(self) -> tuple[Cut, ...]:
        """The cuts the set names, in the order it names them, each once."""
        return tuple(dict.fromkeys(_atoms(self._e)))

    def _parts(self) -> list[tuple[str, list[int]]]:
        return [w for k in self._ev.chains if (w := _where(self._e, k)) is not None]

    def tally(self) -> tuple[int, int]:
        """The versions in the set, and the holes it would hold: the `store` rows a purge emptied
        that its predicate takes (D33). One statement, which builds no row."""
        parts = self._parts()
        if not parts:
            return 0, 0
        sql = " UNION ALL ".join(
            "SELECT count(salt) AS n, count(*) - count(salt) AS h FROM landings "
            f"WHERE kind = 'store' AND {w}" for w, _ in parts)
        n, h = self._ev.one(f"SELECT coalesce(sum(n), 0), coalesce(sum(h), 0) FROM ({sql})",
                            [a for _, args in parts for a in args])
        return int(n), int(h)

    def count(self) -> int:
        """How many versions the set holds: a number, and no operand of a set operator."""
        return self.tally()[0]

    def holes(self) -> int:
        return self.tally()[1]

    def columns(self, *names: str, limit: int | None = None) -> Columns:
        """The set's rows as columns, `chain` and `seq` always among them, in position order
        chain by chain; the first `limit` rows when it is given."""
        parts = self._parts()
        return self._ev.columns([(f"{VERSION} AND {w}", args) for w, args in parts], names,
                                limit)

    def __repr__(self) -> str:
        return f"Versions({' '.join(str(c) for c in self.cuts) or 'bottom'})"


# --- the events between two cuts ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Events:
    """The events after one cut and up to another, chain by chain: the difference of two cuts on
    positions (SNP-11, `readBetween`). On a chain where the first cut is not under the second
    there are none, so the events between two cuts are those between their meet and the second.
    Every kind of row is an event: a landing, a tombstone, a `leave`, a hole."""

    ev: Evaluation
    since: Cut
    upto: Cut

    def after(self, cut: Cut) -> Events:
        """These events after `cut` as well: the read past the length of the first (§4.4)."""
        return Events(self.ev, self.since.join(cut), self.upto)

    def _parts(self) -> list[tuple[str, list[int]]]:
        out = []
        for k in self.ev.chains:
            lo, hi = self.since.at(k), self.upto.at(k)
            if lo < hi:
                out.append(("chain = ? AND seq > ? AND seq <= ?", [k, lo, hi]))
        return out

    def tally(self) -> tuple[int, int]:
        """How many events, and how many of them are holes: one statement."""
        parts = self._parts()
        if not parts:
            return 0, 0
        sql = " UNION ALL ".join(
            "SELECT count(*) AS n, count(*) - count(salt) AS h FROM landings "
            f"WHERE {w}" for w, _ in parts)
        n, h = self.ev.one(f"SELECT coalesce(sum(n), 0), coalesce(sum(h), 0) FROM ({sql})",
                           [a for _, args in parts for a in args])
        return int(n), int(h)

    def count(self) -> int:
        return self.tally()[0]

    def columns(self, *names: str, limit: int | None = None) -> Columns:
        return self.ev.columns(self._parts(), names, limit)


# --- columns --------------------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Text:
    """A column of text read as one buffer: the UTF-8 bytes of every value end to end, the offset
    of each, and which are null. A value is decoded when it is asked for."""

    data: bytes
    offsets: IntArray
    null: npt.NDArray[np.bool_]

    def __len__(self) -> int:
        return len(self.null)

    def __getitem__(self, i: int) -> str | None:
        if self.null[i]:
            return None
        return self.data[int(self.offsets[i]):int(self.offsets[i + 1])].decode("utf-8")

    def take(self, index: IntArray) -> Text:
        """The values at `index`, in its order, as a new buffer: no value is decoded."""
        lengths = np.diff(self.offsets)[index]
        offsets = np.zeros(len(index) + 1, dtype=np.int64)
        np.cumsum(lengths, out=offsets[1:])
        starts = self.offsets[:-1][index]
        gather = np.repeat(starts - offsets[:-1], lengths) + np.arange(offsets[-1])
        data = np.frombuffer(self.data, dtype=np.uint8)[gather].tobytes()
        return Text(data, offsets, self.null[index])


type Column = IntArray | npt.NDArray[np.void] | Text


@dataclass(frozen=True, slots=True)
class Columns:
    """Rows read as columns: one buffer a column, aligned, in position order chain by chain, with
    fewer than one Python object a row. An integer that is null reads -1, a path's key that is
    null 32 zero bytes, and text keeps a null mask (`Text`)."""

    values: Mapping[str, Column]

    def __len__(self) -> int:
        return len(self.values["seq"])

    def __getitem__(self, name: str) -> Column:
        return self.values[name]

    def ints(self, name: str) -> IntArray:
        col = self.values[name]
        if name not in INTEGER or isinstance(col, Text):
            raise KeyError(f"{name} is not an integer column")
        return col.astype(np.int64, copy=False)

    def keys(self) -> npt.NDArray[np.void]:
        """Each row's chain and its path's key as one 40-byte value: what pairs a row gone with
        a row come (D32)."""
        chain = self.ints("chain").astype(">i8").view(np.uint8).reshape(-1, 8)
        key = self.values["path_key"]
        if isinstance(key, Text):
            raise KeyError("path_key is not a key column")
        raw = key.view(np.uint8).reshape(-1, 32)
        return np.ascontiguousarray(np.hstack([chain, raw])).view("V40").ravel()

    def take(self, index: IntArray) -> Columns:
        """The rows at `index`, in its order."""
        out: dict[str, Column] = {}
        for name, col in self.values.items():
            out[name] = col.take(index) if isinstance(col, Text) else col[index]
        return Columns(out)

    def row(self, i: int) -> dict[str, object]:
        """One row as plain values, for a listing: an integer that reads -1 is null."""
        out: dict[str, object] = {}
        for name, col in self.values.items():
            if isinstance(col, Text):
                out[name] = col[i]
            elif name in INTEGER:
                v = int(col[i])
                out[name] = None if v < 0 else v
            else:
                out[name] = bytes(col[i].tobytes()).hex()
        return out


def _ints(text: str | None) -> IntArray:
    if not text:
        return np.zeros(0, dtype=np.int64)
    return np.fromstring(text, dtype=np.int64, sep=",").astype(np.int64, copy=False)


def _read_columns(row: Sequence[object], names: Sequence[str]) -> Columns:
    """The aggregates of one statement decoded into columns, in the order `_aggregates` wrote
    them."""
    values: dict[str, Column] = {}
    it = iter(row)
    for name in names:
        if name in INTEGER:
            values[name] = _ints(_text(next(it)))
        elif name in KEY:
            raw = bytes.fromhex(_text(next(it)) or "")
            values[name] = np.frombuffer(raw, dtype="V32")
        else:
            data = (_text(next(it)) or "").encode("utf-8")
            lengths = _ints(_text(next(it)))
            offsets = np.zeros(len(lengths) + 1, dtype=np.int64)
            np.cumsum(np.maximum(lengths, 0), out=offsets[1:])
            values[name] = Text(data, offsets, lengths < 0)
    return Columns(values)


def _text(v: object) -> str | None:
    return None if v is None else str(v)


def _aggregates(names: Sequence[str]) -> str:
    out = []
    for c in names:
        if c in INTEGER:
            out.append(f"group_concat(coalesce({c}, -1))")
        elif c in KEY:
            out.append(f"group_concat(coalesce(hex({c}), '{_NO_KEY}'), '')")
        else:
            out += [f"group_concat(coalesce({c}, ''), '')",
                    f"group_concat(coalesce(length(CAST({c} AS BLOB)), -1))"]
    return ", ".join(out)


# --- the signed difference ------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Counts:
    """A signed difference counted: the paths removed, added and replaced, and the holes among the
    rows its two range reads take (D33)."""

    removed: int
    added: int
    replaced: int
    holes: int


@dataclass(frozen=True, slots=True)
class Sorted:
    """A signed difference read and sorted by path within a chain (D32): the rows of the paths
    removed, of those added, and the two rows of each path replaced, aligned."""

    removed: Columns
    added: Columns
    replaced: tuple[Columns, Columns]


@dataclass(frozen=True, slots=True)
class Delta:
    """The signed difference of two cuts on contents (SNP-13): the versions `a` holds and `b` does
    not (`gone`) and the converse (`come`), each a set and an operand again. Each side's
    statement walks what changed between the two cuts, chain by chain in its own direction."""

    a: Cut
    b: Cut
    gone: Versions
    come: Versions

    def sizes(self) -> tuple[int, int]:
        """How many versions are gone and how many came: one statement."""
        g, c = self.gone._parts(), self.come._parts()
        if not g and not c:
            return 0, 0
        sides = [f"SELECT {i} AS side FROM landings WHERE {VERSION} AND {w}"
                 for i, parts in ((0, g), (1, c)) for w, _ in parts]
        n_gone, n_come = self.gone._ev.one(
            "SELECT coalesce(sum(side = 0), 0), coalesce(sum(side = 1), 0) "
            f"FROM ({' UNION ALL '.join(sides)})",
            [a for parts in (g, c) for _, args in parts for a in args])
        return int(n_gone), int(n_come)

    def counts(self) -> Counts:
        """The paths removed, added and replaced, and the holes in the two ranges: one statement,
        which pairs the two sides by path within a chain and builds no row."""
        g, c = self.gone._parts(), self.come._parts()
        if not g and not c:
            return Counts(0, 0, 0, 0)

        def side(parts: list[tuple[str, list[int]]]) -> str:
            if not parts:
                return "SELECT NULL AS chain, NULL AS path_key, 0 AS v WHERE 0"
            return " UNION ALL ".join(
                "SELECT chain, path_key, salt IS NOT NULL AS v FROM landings "
                f"WHERE kind = 'store' AND {w}" for w, _ in parts)

        n_gone, n_come, paired, holes = self.gone._ev.one(
            f"WITH g AS MATERIALIZED ({side(g)}), c AS MATERIALIZED ({side(c)}) "
            "SELECT (SELECT count(*) FROM g WHERE v), (SELECT count(*) FROM c WHERE v), "
            "(SELECT count(*) FROM g JOIN c USING (chain, path_key) WHERE g.v AND c.v), "
            "(SELECT count(*) FROM g WHERE NOT v) + (SELECT count(*) FROM c WHERE NOT v)",
            [a for parts in (g, c) for _, args in parts for a in args])
        return Counts(int(n_gone) - int(paired), int(n_come) - int(paired), int(paired),
                      int(holes))

    def sorted(self, *names: str, limit: int | None = None) -> Sorted:
        """The two sides read, every row of each (what changed), and sorted by path within a
        chain: a path with a row on each side is replaced, one with a row gone only removed, one
        with a row come only added (`removedOf`, `addedOf`, `replacedOf`). Each class in position
        order, its first `limit` entries when `limit` is given."""
        want = (*dict.fromkeys((*names, "path_key")),)
        gone, come = self.gone.columns(*want), self.come.columns(*want)
        # each key is on a side once (a cut holds one row a path on a chain), so after one sort
        # of both sides' keys a key on both is two neighbours, the row gone first
        keys = np.concatenate([gone.keys(), come.keys()])
        order = np.argsort(keys, kind="stable").astype(np.int64)
        twin = np.flatnonzero(keys[order][1:] == keys[order][:-1])
        rg, rc = order[twin], order[twin + 1] - len(gone)
        paired = np.zeros(len(keys), dtype=np.bool_)
        paired[rg], paired[rc + len(gone)] = True, True
        removed = np.flatnonzero(~paired[:len(gone)])[:limit]
        added = np.flatnonzero(~paired[len(gone):])[:limit]
        by_position = np.argsort(rg, kind="stable")      # the pairs in the gone rows' order
        rg, rc = rg[by_position][:limit], rc[by_position][:limit]
        return Sorted(gone.take(removed), come.take(added), (gone.take(rg), come.take(rc)))

    def apply(self, s: Versions) -> Versions:
        """The difference applied to a set: the set less the versions gone, with those come.
        Applied to what `a` holds it gives what `b` holds (`Held.has_cut_eq_apply`)."""
        return (s - self.gone) | self.come

    def then(self, other: Delta) -> Delta:
        """This difference composed with one from the cut it ends at: the difference from `a` to
        `other.b` (`Held.has_come_trans`, `Held.has_gone_trans`), a row that came and went on
        the way on neither side. Refused unless `other` starts where this one ends, at a cut
        that lies between the two outer ones on every chain, in either direction: through a cut
        outside them the composition is not the difference (`Witness.delta_through_outside`)."""
        if not isinstance(other, Delta):
            raise CutError(f"a signed difference composes with a signed difference, not with "
                           f"{_kind(other)}")
        if other.a != self.b:
            raise CutError(f"two signed differences compose through the cut they share: one "
                           f"ends at {self.b.name()} and the other starts at {other.a.name()}")
        ev = self.gone._ev
        for k in ev.chains:
            a, b, c = self.a.at(k), self.b.at(k), other.b.at(k)
            if not (min(a, c) <= b <= max(a, c)):
                raise CutError(f"the shared cut is not between the outer two on land.{k}: "
                               f"{b} is not between {a} and {c}, and through a cut outside "
                               "them the composition is not the difference")
        return Delta(self.a, other.b, self.gone | (other.gone - self.come),
                     (self.come - other.gone) | other.come)


# --- a family's results ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Series[T]:
    """A value at each cut of a family, in the family's order: a series, and no operand of a set
    operator."""

    cuts: tuple[Cut, ...]
    values: tuple[T, ...]


@dataclass(frozen=True, slots=True)
class Table:
    """The sizes of the pairwise differences of a family: `sizes[i][j]` is how many versions cut
    `i` holds and cut `j` does not. `sizes[i][j] - sizes[j][i]` is the difference of the two
    counts (`Held.length_rows_delta`), and `sizes[i][k] <= sizes[i][j] + sizes[j][k]`, since a
    row gone from `i` to `k` is gone from `i` to `j` or from `j` to `k`
    (`Held.has_gone_triangle`, which states the rows; the sizes follow)."""

    cuts: tuple[Cut, ...]
    sizes: tuple[tuple[int, ...], ...]


@dataclass(frozen=True, slots=True)
class Counted:
    """The rows of a set, each with the number of a family's cuts that hold it (`countIn`)."""

    cuts: tuple[Cut, ...]
    rows: Columns
    counts: IntArray


@dataclass(frozen=True, slots=True)
class Read:
    """One cut's read, as an operator is handed it: the cut, the versions it holds and the events
    up to it. Nothing is read until one of the two is. SN-4 adds the graph at the cut here."""

    cut: Cut
    versions: Versions
    events: Events


# --- the evaluation -------------------------------------------------------------------------------

class Evaluation:
    """One evaluation of the algebra: the log's connection, the chains of the classes the asker
    reads (the classes' chains now, §6.3), and the head of each, read once when the evaluation
    starts. Every operation takes its cuts as optional: one left out is that head (D19, D27).
    Every cut given is taken on the evaluation's chains alone, and refused past the head."""

    def __init__(self, conn: sqlite3.Connection, classes: Iterable[str]) -> None:
        self._conn = conn
        wanted = sorted({str(c) for c in classes})
        rows = conn.execute(
            "SELECT chain, class, (SELECT max(seq) FROM landings l WHERE l.chain = c.chain) "
            f"FROM landing_chains c WHERE class IN ({', '.join('?' * len(wanted))}) "
            "ORDER BY chain", wanted).fetchall() if wanted else []
        self.classes: dict[int, str] = {int(k): str(cls) for k, cls, _ in rows}
        self.chains: tuple[int, ...] = tuple(self.classes)
        self.head = Cut.of({int(k): int(h or 0) for k, _, h in rows})
        self.bottom = BOTTOM
        # what `served` has learnt of each chain's horizon, so that it walks a chain once: the
        # horizon found, or the greatest position found to lie under it
        self._horizon: dict[int, int] = {}
        self._under: dict[int, int] = {}

    # reading -----------------------------------------------------------------------------------

    def one(self, sql: str, args: Sequence[object]) -> tuple[Any, ...]:
        """The one row a statement of aggregates returns."""
        return tuple(self._conn.execute(sql, list(args)).fetchone())

    def columns(self, parts: Sequence[tuple[str, list[int]]], names: Sequence[str],
                limit: int | None) -> Columns:
        """The rows the conditions take, one condition a chain, as columns in one statement."""
        bad = [n for n in names if n not in COLUMNS]
        if bad:
            raise CutError(f"no column {', '.join(bad)}; the columns are {', '.join(COLUMNS)}")
        want = tuple(dict.fromkeys(("chain", "seq", *names)))
        if not parts:
            return _read_columns([None] * sum(1 + (c in TEXT) for c in want), want)
        body = " UNION ALL ".join(f"SELECT {', '.join(want)} FROM landings WHERE {w}"
                                  for w, _ in parts)
        args: list[object] = [a for _, ps in parts for a in ps]
        if limit is not None:
            body = f"{body} ORDER BY chain, seq LIMIT ?"
            args.append(int(limit))
        cols = _read_columns(self.one(f"SELECT {_aggregates(want)} FROM ({body})", args), want)
        chain, seq = cols.ints("chain"), cols.ints("seq")
        if len(seq) > 1 and not bool(np.all((chain[1:] > chain[:-1]) | (
                (chain[1:] == chain[:-1]) & (seq[1:] > seq[:-1])))):
            cols = cols.take(np.lexsort((seq, chain)).astype(np.int64))
        return cols

    # cuts --------------------------------------------------------------------------------------

    def cut(self, c: Cut | None = None) -> Cut:
        """`c` on the evaluation's chains, or the head when it is `None`. Refused past the head:
        a cut inside the log is at or under it."""
        if c is None:
            return self.head
        if not isinstance(c, Cut):
            raise CutError(f"a cut is expected, and {_kind(c)} was given")
        c = c.restrict(self.chains)
        for k, p in c.positions:
            h = self.head.at(k)
            if p > h:
                raise CutError(f"land.{k}@{p} is past the chain's head, land.{k}@{h}")
        return c

    def named(self, name: str) -> Cut:
        """A cut by its name (§7.5): `head`, `bottom`, or its positions. A position past a chain's
        head is refused with the head, and a chain the evaluation does not read is refused in the
        words used for a chain that does not exist."""
        text = name.strip()
        if text == "head":
            return self.head
        if text == "bottom":
            return self.bottom
        c = Cut.parse(text)
        for k in c.chains:
            if k not in self.classes:
                read = " ".join(f"land.{j}" for j in self.chains) or "none"
                raise CutError(f"there is no chain land.{k}; the chains read here are {read}")
        return self.cut(c)

    def serves(self, chain: int, position: int) -> bool:
        """Whether a chain serves a position under its head: whether the position is at or
        after the chain's horizon. A chain's positions before its horizon are its genesis block,
        which is not history, and are not served (§8). At this stage a chain has one horizon
        row, at the end of its genesis block, and no index finds it, so the statement walks the
        rows from the position back to it, or to the chain's first row when the position lies
        under it. No row is walked twice in one evaluation: the horizon found answers every later
        position on its chain, a later position under one found to lie under the horizon needs no
        walk, and one above it walks only down to it."""
        if chain in self._horizon:
            return position >= self._horizon[chain]
        under = self._under.get(chain, 0)
        if position <= under:
            return False
        row = self._conn.execute(
            "SELECT horizon FROM landings WHERE chain = ? AND seq <= ? AND seq > ? "
            "AND kind = 'horizon' ORDER BY seq DESC LIMIT 1", [chain, position, under]).fetchone()
        if row is None or row[0] is None:
            self._under[chain] = position
            return False
        self._horizon[chain] = int(row[0])
        return position >= int(row[0])

    def served(self, c: Cut) -> tuple[Cut, list[tuple[int, int]]]:
        """The cut read for the cut asked (§7.1): each chain at the greatest position it serves at
        or under the one asked. A position under a chain's horizon is not served, and the chain is
        read at its empty prefix (`serves`); the head serves itself and needs no walk. No
        reference of §3.5 lowers a landing chain before SN-2, so nothing else is lowered. One
        pair of rows is not among those references: a change of class writes a `leave` in the
        old class's chain and then the `store` in the new class's chain, and a cut of two chains
        or more that is neither the head nor the bottom can hold one of the two rows without the
        other, and so the path in both classes or in neither (§3.5, §7.5). It is read as asked.
        Returns the cut read and the chains read below the position asked, with that position."""
        lowered: list[tuple[int, int]] = []
        out = c.as_dict()
        for k, p in c.positions:
            if p == self.head.at(k) or self.serves(k, p):
                continue
            lowered.append((k, p))
            out[k] = 0
        return Cut.of(out), lowered

    # the interface: apply, combine, map and fold --------------------------------------------------

    def read(self, c: Cut | None = None) -> Read:
        """One cut's read; the head's when `c` is `None`."""
        c = self.cut(c)
        return Read(c, Versions(self, _Held(c)), Events(self, BOTTOM, c))

    def apply[T](self, f: Callable[[Read], T], c: Cut | None = None) -> T:
        """A function of one cut's read (`view`)."""
        return f(self.read(c))

    def combine[T](self, f: Callable[[Read, Read], T], a: Cut | None = None,
                   b: Cut | None = None) -> T:
        """A function of two cuts' reads (`combine`)."""
        return f(self.read(a), self.read(b))

    def family(self, cuts: Sequence[Cut] | None = None) -> tuple[Cut, ...]:
        """A family's cuts on the evaluation's chains: the head alone when none is given."""
        return tuple(self.cut(c) for c in cuts) if cuts else (self.head,)

    def map[T](self, f: Callable[[Read], T], cuts: Sequence[Cut] | None = None) -> Series[T]:
        """A function at each cut of a family (`series`): a series."""
        fam = self.family(cuts)
        return Series(fam, tuple(f(self.read(c)) for c in fam))

    def fold[T](self, g: Callable[[T, Read], T], init: T,
                cuts: Sequence[Cut] | None = None) -> T:
        """An accumulation over the cuts of a family, each read in its turn (`foldOver`)."""
        acc = init
        for c in self.family(cuts):
            acc = g(acc, self.read(c))
        return acc

    # the named operations, each one of the four forms ---------------------------------------------

    def held(self, c: Cut | None = None) -> Versions:
        """The versions a cut holds (an apply): the contents of every class the evaluation reads
        at the cut, a set and an operand of every set operator."""
        return self.apply(lambda r: r.versions, c)

    def between(self, a: Cut | None = None, b: Cut | None = None) -> Events:
        """The events after `a` and up to `b` (a combine): the difference on positions."""
        return self.combine(lambda ra, rb: rb.events.after(ra.cut), a, b)

    def delta(self, a: Cut | None = None, b: Cut | None = None) -> Delta:
        """The signed difference from `a` to `b` (a combine): what `a` holds and `b` does not,
        and the converse."""
        return self.combine(lambda ra, rb: Delta(ra.cut, rb.cut, ra.versions - rb.versions,
                                                 rb.versions - ra.versions), a, b)

    def persisted(self, cuts: Sequence[Cut] | None = None) -> Versions:
        """What every cut of a family holds (a fold): what the family's meet and its join both
        hold, two positions a chain whatever the size of the family (`Held.has_all_eq_kept`)."""
        fam = self.family(cuts)
        lo, hi = self.fold(lambda acc, r: (acc[0].meet(r.cut), acc[1].join(r.cut)),
                           (fam[0], fam[0]), fam)
        return self.held(lo) & self.held(hi)

    def existed(self, cuts: Sequence[Cut] | None = None) -> Versions:
        """What some cut of a family holds (a fold): the union of their contents."""

        def step(acc: Versions | None, r: Read) -> Versions | None:
            return r.versions if acc is None else acc | r.versions

        out = self.fold(step, None, self.family(cuts))
        assert out is not None              # a family has one cut at least
        return out

    def count_series(self, cuts: Sequence[Cut] | None = None) -> Series[int]:
        """The count at each cut of a family (a fold): the first cut counted, and each next count
        from the last by the signed difference between the two, which walks what changed
        (`Held.length_rows_delta`)."""
        fam = self.family(cuts)
        type Walk = tuple[Read | None, tuple[int, ...]]

        def step(acc: Walk, r: Read) -> Walk:
            last, values = acc
            if last is None:
                return r, (r.versions.count(),)
            gone, come = Delta(last.cut, r.cut, last.versions - r.versions,
                               r.versions - last.versions).sizes()
            return r, (*values, values[-1] - gone + come)

        start: Walk = (None, ())
        return Series(fam, self.fold(step, start, fam)[1])

    def in_how_many(self, s: Versions, cuts: Sequence[Cut] | None = None,
                    names: Sequence[str] = (), limit: int | None = None) -> Counted:
        """The rows of `s`, each with the number of the family's cuts that hold it: a row is held
        at `c` exactly when `seq <= c < closed_at`, read off its interval (`countIn`). Only the
        first `limit` rows are read when it is given; how many rows every cut holds is a count,
        `s & self.persisted(cuts)`, and needs none of them."""
        fam = self.family(cuts)
        rows = s.columns(*dict.fromkeys((*names, "closed_at")), limit=limit)
        return Counted(fam, rows, self._held_by(rows, fam).sum(axis=1).astype(np.int64))

    def pairwise(self, cuts: Sequence[Cut] | None = None) -> Table:
        """The sizes of the pairwise differences of a family: one read of what some cut of it
        holds, each row counted into the table by the cuts its interval covers."""
        fam = self.family(cuts)
        held = self._held_by(self.existed(fam).columns("closed_at"), fam).astype(np.int64)
        sizes = held.T @ (1 - held)
        return Table(fam, tuple(tuple(int(x) for x in row) for row in sizes))

    def _held_by(self, rows: Columns, fam: Sequence[Cut]) -> npt.NDArray[np.bool_]:
        """For each row and each cut of the family, whether the cut holds the row: its position
        at or under the cut's on the row's chain, and its closing stamp, if any, above it."""
        chain, seq = rows.ints("chain"), rows.ints("seq")
        died = rows.ints("closed_at")
        died = np.where(died < 0, np.iinfo(np.int64).max, died)
        at = np.array([[c.at(k) for c in fam] for k in self.chains], dtype=np.int64).reshape(
            len(self.chains), len(fam))
        # every row is of a chain of the evaluation, and the chains are in order
        pos = at[np.searchsorted(np.array(self.chains, dtype=np.int64), chain)]
        held: npt.NDArray[np.bool_] = (seq[:, None] <= pos) & (pos < died[:, None])
        return held


def read_only(path: Path) -> sqlite3.Connection:
    """A connection that only reads a catalog's file, for an evaluation that writes nothing. It
    takes no lock a writer waits on, and a writer's transaction does not hold it up: it reads
    the log as the last commit left it. Opening the catalog itself (`VaultCatalog`) runs its
    migration, a write transaction at every open, and may write the log's genesis."""
    return sqlite3.connect(f"{Path(path).resolve().as_uri()}?mode=ro", uri=True)


def _kind(v: object) -> str:
    """What a value is, as a refusal names it."""
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
        case bool():
            return "a truth value"
        case int() | float():
            return "a number"
        case None:
            return "nothing"
    return type(v).__name__
