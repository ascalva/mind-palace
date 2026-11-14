"""The algebra of cuts on the code (dn-temporal-snapshot §4.4, §10; stage SN-1b).

`core/stores/cuts.py` reads the landing log's rows as a cut's contents, through a predicate on a
row's position and its closing stamp. Each law is checked here against a plain fold of the log
kept in this file: on every chain, each path's last event at or under a position, kept when it is
a `store` that keeps its content. The catalogs are SN-1's random ones, a build before the log
followed by random catalog writes with retires, renames, relabels, re-keys, changes of class and
both purges among them, so the logs have holes, closed rows and classes of several chains. The
cuts are the heads taken after every write and frontiers drawn at random, ordered and not. The
properties, each with the law it transcribes (§12, SN-1b):

1. the lattice laws on positions, and the events between two cuts read from their meet and to
   their join (SNP-11);
2. the four interval statements against the fold at every position and at pairs of positions,
   contiguity, and one row a path in every cut's contents (SNP-12);
3. the signed difference against the fold's set difference in both orders and for cuts neither
   of which is under the other; applied; composed through a cut between, with the composition
   through a cut outside as the control; the count walked along a family; the three classes
   disjoint and covering; every path of a difference among the paths of the events between
   (SNP-13);
4. expressions of any depth read lazily against the same operations on the fold's sets, results
   of each operator given to others, no statement run by combining, the count without the rows,
   and the family operations (SNP-14);
5. every set, difference and count at cuts inside the log unchanged by further writes, up to the
   holes a later purge leaves (SNP-14, with SNP-1);
6. on a class with no closes the contents of the join are the union of the contents and those of
   the meet the intersection; after one edit they differ, as the control (SNP-15);
7. the sets and differences of one class read only that class's chains: unchanged by writes to
   another class and by the positions named on its chains (SNP-16);
8. after a purge no set and no difference holds a row of the purged digest and every other row
   is the row it was; a retire is a removal in every difference that spans it (SNP-17);
9. the default: an evaluation with no cut named reads one head in every part, names it, and
   gives the same result when asked again with the positions it named after further writes
   (D27, SNF-19).

The tool's property, the tenth, is `tests/unit/test_cut_tool.py`'s.
"""

from __future__ import annotations

import itertools
import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from core.kernel.provenance import Provenance
from core.stores.catalog import VaultCatalog
from core.stores.cuts import (
    BOTTOM,
    Cut,
    CutError,
    Delta,
    Evaluation,
    Text,
    Versions,
    join_all,
    meet_all,
)
from core.stores.landings import Landing
from tests.property.test_landing_log import CLASSES, apply, from_legacy, legacy, ops

ALL = [str(c) for c in CLASSES]

Row = tuple[int, int]                   # a version, named by its position: (chain, seq)
Rows = frozenset[Row]
SETTINGS = settings(max_examples=120, deadline=None,
                    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])


# --- the reference fold, in test code ------------------------------------------------------------

@dataclass
class Fold:
    """Each chain's rows, and what every position of it holds by a fold of the prefix: each
    path's last event at or under the position, kept when it is a `store` that keeps its
    content."""

    rows: dict[int, list[Landing]]
    alive: dict[int, list[frozenset[int]]]

    @classmethod
    def of(cls, cat: VaultCatalog) -> Fold:
        rows: dict[int, list[Landing]] = {}
        alive: dict[int, list[frozenset[int]]] = {}
        for ch in cat._log.all_chains():
            rows[ch] = cat.read_at(ch, cat.head(ch))
            last: dict[bytes, Landing] = {}
            at = [frozenset[int]()]
            for row in rows[ch]:
                if row.path_key is not None:
                    last[row.path_key] = row
                at.append(frozenset(r.seq for r in last.values()
                                    if r.kind == "store" and not r.hole))
            alive[ch] = at
        return cls(rows, alive)

    def held(self, cut: Cut, chains: tuple[int, ...]) -> Rows:
        return frozenset((ch, s) for ch in chains for s in self.alive[ch][cut.at(ch)])

    def row(self, r: Row) -> Landing:
        return self.rows[r[0]][r[1] - 1]

    def between(self, a: Cut, b: Cut, chains: tuple[int, ...]) -> list[Row]:
        return [(ch, r.seq) for ch in chains for r in self.rows[ch]
                if a.at(ch) < r.seq <= b.at(ch)]


def rows_of(s: Versions) -> Rows:
    cols = s.columns()
    return frozenset(zip(cols.ints("chain").tolist(), cols.ints("seq").tolist(), strict=True))


def keyed(fold: Fold, rows: Rows) -> dict[tuple[int, bytes], Row]:
    out: dict[tuple[int, bytes], Row] = {}
    for r in rows:
        key = fold.row(r).path_key
        assert key is not None
        assert (r[0], key) not in out, "a cut holds one row a path on a chain"
        out[(r[0], key)] = r
    return out


def build(before: list[tuple[Any, ...]], writes: list[tuple[Any, ...]]) -> tuple[
        VaultCatalog, list[Cut]]:
    """A random catalog's genesis and writes, with the head taken after each."""
    cat = from_legacy(before)
    taken = [Cut.of(heads(cat))]
    for op in writes:
        apply(cat, op)
        taken.append(Cut.of(heads(cat)))
    return cat, taken


def heads(cat: VaultCatalog) -> dict[int, int]:
    return {ch: cat.head(ch) for ch in cat._log.all_chains()}


def frontier(data: st.DataObject, head: Cut, chains: tuple[int, ...]) -> Cut:
    """A frontier inside the log drawn at random, one position a chain."""
    return Cut.of({ch: data.draw(st.integers(0, head.at(ch))) for ch in chains})


def cuts_of(data: st.DataObject, taken: list[Cut], ev: Evaluation, n: int) -> list[Cut]:
    """`n` cuts: heads taken after writes and frontiers drawn at random, in a random mix."""
    out = []
    for _ in range(n):
        if data.draw(st.booleans()):
            out.append(ev.cut(data.draw(st.sampled_from(taken))))
        else:
            out.append(frontier(data, ev.head, ev.chains))
    return out


@contextmanager
def statements(cat: VaultCatalog) -> Iterator[list[str]]:
    """The statements the catalog's connection runs inside the block."""
    seen: list[str] = []
    cat._conn.set_trace_callback(seen.append)
    try:
        yield seen
    finally:
        cat._conn.set_trace_callback(None)


# --- 1. the lattice of cuts (SNP-11) --------------------------------------------------------------

positions = st.dictionaries(st.integers(1, 4), st.integers(0, 12), max_size=4)


@given(positions, positions, positions)
def test_cuts_are_a_lattice_on_positions(x: dict[int, int], y: dict[int, int],
                                         z: dict[int, int]) -> None:
    """A cut is a value: equal positions are one cut and one key, and a chain left out stands
    at 0. The join and the meet are the pointwise maximum and minimum, and they satisfy the laws
    of a distributive lattice as equalities of values, with the empty cut at the bottom; the
    order is the pointwise one, and a cut prints as positions it parses back from."""
    a, b, c = Cut.of(x), Cut.of(y), Cut.of(z)
    assert Cut.of({**x, 9: 0}) == a and hash(Cut.of({**x, 9: 0})) == hash(a)
    for k in range(1, 6):
        assert a.join(b).at(k) == max(a.at(k), b.at(k))
        assert a.meet(b).at(k) == min(a.at(k), b.at(k))
    assert a.join(b) == b.join(a) and a.meet(b) == b.meet(a)
    assert a.join(b.join(c)) == a.join(b).join(c) and a.meet(b.meet(c)) == a.meet(b).meet(c)
    assert a.join(a.meet(b)) == a == a.meet(a.join(b))
    assert a.join(a) == a == a.meet(a)
    assert a.meet(b.join(c)) == a.meet(b).join(a.meet(c))
    assert a.join(b.meet(c)) == a.join(b).meet(a.join(c))
    assert BOTTOM <= a and BOTTOM.join(a) == a and BOTTOM.meet(a) == BOTTOM
    assert (a <= b) == all(a.at(k) <= b.at(k) for k in range(1, 6)) == (a.join(b) == b) \
        == (a.meet(b) == a)
    assert a.meet(b) <= a <= a.join(b)
    order = a.order(b)
    assert order == {(True, True): "equal", (True, False): "before", (False, True): "after",
                     (False, False): "unordered"}[(a <= b, b <= a)]
    assert Cut.parse(a.name(range(1, 6))) == a
    assert join_all([a, b, c]) == a.join(b).join(c) and meet_all([a, b, c]) == a.meet(b).meet(c)


@SETTINGS
@given(legacy, ops, st.data())
def test_the_join_and_meet_are_cuts_and_the_events_between_read_from_either(
        before: list[tuple[Any, ...]], writes: list[tuple[Any, ...]],
        data: st.DataObject) -> None:
    """On a random log the join and the meet of two cuts inside it are inside it; the events
    between two cuts are the fold's rows in the range, chain by chain, the same read from their
    meet and to their join; the events between the meet and the join are those between the two
    in either order (SNP-11)."""
    cat, taken = build(before, writes)
    ev = cat.cuts(ALL)
    fold = Fold.of(cat)
    for _ in range(6):
        a, b = cuts_of(data, taken, ev, 2)
        assert ev.cut(a.join(b)) <= ev.head and ev.cut(a.meet(b)) <= ev.head
        cols = ev.between(a, b).columns("kind")
        got = list(zip(cols.ints("chain").tolist(), cols.ints("seq").tolist(), strict=True))
        assert got == fold.between(a, b, ev.chains)
        assert ev.between(a, b).count() == len(got)
        assert rows_between(ev, a.meet(b), b) == rows_between(ev, a, b) == \
            rows_between(ev, a, a.join(b))
        assert rows_between(ev, a.meet(b), a.join(b)) == \
            rows_between(ev, a, b) | rows_between(ev, b, a)
        kinds = cols["kind"]
        assert isinstance(kinds, Text)
        assert [kinds[i] for i in range(len(kinds))] == \
            [fold.row(r).kind for r in got]
    cat.close()


def rows_between(ev: Evaluation, a: Cut, b: Cut) -> Rows:
    cols = ev.between(a, b).columns()
    return frozenset(zip(cols.ints("chain").tolist(), cols.ints("seq").tolist(), strict=True))


# --- 2. a version lives on an interval (SNP-12) ---------------------------------------------------

@settings(SETTINGS, max_examples=60)
@given(legacy, ops, st.data())
def test_a_version_lives_on_an_interval_and_the_four_reads_are_its_statements(
        before: list[tuple[Any, ...]], writes: list[tuple[Any, ...]],
        data: st.DataObject) -> None:
    """At every position of every chain the contents are the fold's, one row a path, and the
    positions a row is held at are one run: contiguity. At every pair of positions `a <= b`, what
    `b` holds and `a` does not, what `a` holds and `b` does not, and what both hold are the
    fold's set operations. What every position of a family holds is what its least and its
    greatest hold, and what some position holds lies among the rows stored by the greatest and
    not closed by the least (SNP-12)."""
    cat, _ = build(before, writes)
    fold = Fold.of(cat)
    for ch in cat._log.all_chains():
        ev = Evaluation(cat._conn, [cls for cls in ALL if ch in cat.chains(cls)])
        one = (ch,)
        head = ev.head.at(ch)
        at = [Cut.of({ch: c}) for c in range(head + 1)]
        got = [rows_of(ev.held(c)) for c in at]
        for c, rows in zip(at, got, strict=True):
            assert rows == fold.held(c, one)
            keyed(fold, rows)
        for r in frozenset().union(*got):
            held_at = [c for c in range(head + 1) if r in got[c]]
            assert held_at == list(range(held_at[0], held_at[-1] + 1))
        for a, b in itertools.combinations_with_replacement(range(head + 1), 2):
            fa, fb = got[a], got[b]
            assert rows_of(ev.held(at[b]) - ev.held(at[a])) == fb - fa
            assert rows_of(ev.held(at[a]) - ev.held(at[b])) == fa - fb
            assert rows_of(ev.held(at[a]) & ev.held(at[b])) == fa & fb
        for _ in range(4):
            family = [at[p] for p in data.draw(
                st.lists(st.integers(0, head), min_size=1, max_size=5))]
            held = [fold.held(c, one) for c in family]
            assert rows_of(ev.persisted(family)) == frozenset.intersection(*held)
            some = frozenset.union(*held)
            assert rows_of(ev.existed(family)) == some
            lo, hi = min(c.at(ch) for c in family), max(c.at(ch) for c in family)
            assert all(fold.row(r).seq <= hi and (fold.row(r).closed_at or hi + 1) > lo
                       for r in some)
    cat.close()


# --- 3. the signed difference (SNP-13) ------------------------------------------------------------

@SETTINGS
@given(legacy, ops, st.data())
def test_the_signed_difference_is_the_folds_and_composes_through_a_cut_between(
        before: list[tuple[Any, ...]], writes: list[tuple[Any, ...]],
        data: st.DataObject) -> None:
    """For cuts in either order and cuts neither of which is under the other, the two sides of
    the signed difference are the fold's set differences, and the counts sort them by path within
    a chain into removed, added and replaced, disjoint and covering, one row a path a side;
    applied to what the first cut holds it gives what the second holds; through a cut between the
    two on every chain it composes, and through one outside the composition is refused; every
    path of the difference is a path the events between the meet and the join name; and the
    count at each cut of a family, walked by the differences, is the count read (SNP-13)."""
    cat, taken = build(before, writes)
    ev = cat.cuts(ALL)
    fold = Fold.of(cat)
    for _ in range(6):
        a, b = cuts_of(data, taken, ev, 2)
        fa, fb = fold.held(a, ev.chains), fold.held(b, ev.chains)
        d = ev.delta(a, b)
        assert (rows_of(d.gone), rows_of(d.come)) == (fa - fb, fb - fa)
        back = ev.delta(b, a)
        assert (rows_of(back.gone), rows_of(back.come)) == (fb - fa, fa - fb)
        gone, come = keyed(fold, fa - fb), keyed(fold, fb - fa)
        counts = d.counts()
        assert counts.replaced == len(gone.keys() & come.keys())
        assert counts.removed == len(gone.keys() - come.keys())
        assert counts.added == len(come.keys() - gone.keys())
        assert counts.removed + counts.replaced == len(fa - fb) == d.sizes()[0]
        assert counts.added + counts.replaced == len(fb - fa) == d.sizes()[1]
        s = d.sorted("source_path")
        removed = set(zip(s.removed.ints("chain").tolist(), s.removed.ints("seq").tolist(),
                          strict=True))
        added = set(zip(s.added.ints("chain").tolist(), s.added.ints("seq").tolist(),
                        strict=True))
        old, new = s.replaced
        pairs = list(zip(zip(old.ints("chain").tolist(), old.ints("seq").tolist(), strict=True),
                         zip(new.ints("chain").tolist(), new.ints("seq").tolist(), strict=True),
                         strict=True))
        assert removed == {r for k, r in gone.items() if k not in come}
        assert added == {r for k, r in come.items() if k not in gone}
        assert sorted(pairs) == sorted((gone[k], come[k]) for k in gone.keys() & come.keys())
        assert removed.isdisjoint(p for p, _ in pairs) and added.isdisjoint(q for _, q in pairs)
        assert rows_of(d.apply(ev.held(a))) == fb
        named = {(r[0], fold.row(r).path_key)
                 for r in fold.between(a.meet(b), a.join(b), ev.chains)}
        assert gone.keys() | come.keys() <= named
        # composition through a cut between, chain by chain in either direction
        m = Cut.of({k: data.draw(st.integers(min(a.at(k), b.at(k)), max(a.at(k), b.at(k))))
                    for k in ev.chains})
        both = ev.delta(a, m).then(ev.delta(m, b))
        assert (both.a, both.b) == (a, b)
        assert (rows_of(both.gone), rows_of(both.come)) == (fa - fb, fb - fa)
        outside = [k for k in ev.chains
                   if not min(a.at(k), b.at(k)) <= taken[0].at(k) <= max(a.at(k), b.at(k))]
        if outside:
            with pytest.raises(CutError, match="not between"):
                ev.delta(a, ev.cut(taken[0])).then(ev.delta(ev.cut(taken[0]), b))
        elsewhere = next((x for x in (a, m, BOTTOM, ev.head) if x != b), None)
        if elsewhere is not None:
            with pytest.raises(CutError, match="compose through the cut they share"):
                d.then(ev.delta(elsewhere, b))
    family = cuts_of(data, taken, ev, 5)
    walked = ev.count_series(family)
    assert walked.cuts == tuple(family)
    assert list(walked.values) == [len(fold.held(c, ev.chains)) for c in family]
    cat.close()


def test_a_composition_through_a_cut_outside_the_two_is_not_the_difference() -> None:
    """The control of the composition (`Witness.delta_through_outside`): a path landed after `a`
    and `c` and edited after that, so a cut `b` past both lies outside them. The formula of the
    composition through `b` is not the difference from `a` to `c`, and `then` refuses it."""
    cat = VaultCatalog(Path(":memory:"))
    cat.record("p.md", "d1", "P")
    ev0 = cat.cuts(ALL)
    a = ev0.head
    cat.record("q.md", "d2", "Q")
    c = cat.cuts(ALL).head
    cat.record("p.md", "d3", "P")
    ev = cat.cuts(ALL)
    b = ev.head
    ab, bc = ev.delta(a, b), ev.delta(b, c)
    formula = (ab.come - bc.gone) | bc.come
    assert rows_of(formula) != rows_of(ev.delta(a, c).come)
    with pytest.raises(CutError, match="not between"):
        ab.then(bc)
    cat.close()


# --- 4. closure (SNP-14) --------------------------------------------------------------------------

Expr = tuple[Any, ...]
leaf = st.integers(0, 3).map(lambda i: ("held", i))
expressions: st.SearchStrategy[Expr] = st.recursive(
    leaf, lambda sub: st.tuples(st.sampled_from(["|", "&", "-", "^"]), sub, sub), max_leaves=8)


def lazily(ev: Evaluation, e: Expr, cuts: list[Cut]) -> Versions:
    if e[0] == "held":
        return ev.held(cuts[e[1]])
    p, q = lazily(ev, e[1], cuts), lazily(ev, e[2], cuts)
    return {"|": p | q, "&": p & q, "-": p - q, "^": p ^ q}[e[0]]


def folded(fold: Fold, chains: tuple[int, ...], e: Expr, cuts: list[Cut]) -> Rows:
    if e[0] == "held":
        return fold.held(cuts[e[1]], chains)
    p, q = folded(fold, chains, e[1], cuts), folded(fold, chains, e[2], cuts)
    return {"|": p | q, "&": p & q, "-": p - q, "^": p ^ q}[e[0]]


@SETTINGS
@given(legacy, ops, st.lists(expressions, min_size=1, max_size=4), st.data())
def test_a_set_of_any_depth_is_read_lazily_as_the_folds_set(
        before: list[tuple[Any, ...]], writes: list[tuple[Any, ...]], es: list[Expr],
        data: st.DataObject) -> None:
    """Random expressions of any depth over the contents of four cuts are composed with no
    statement run, and each is read by one statement as the same operations on the fold's sets;
    its count is the size of that set, by one statement that returns two numbers. The results of
    the other operators are operands too: the sides of a signed difference, what persisted and
    what existed, and a difference applied, each combined with a set. In how many of a family's
    cuts a row is held, and the sizes of the pairwise differences, are the fold's (SNP-14)."""
    cat, taken = build(before, writes)
    ev = cat.cuts(ALL)
    fold = Fold.of(cat)
    cuts = cuts_of(data, taken, ev, 4)
    for e in es:
        with statements(cat) as seen:
            s = lazily(ev, e, cuts)
        assert seen == []                               # combining reads nothing
        want = folded(fold, ev.chains, e, cuts)
        with statements(cat) as seen:
            n = s.count()
        assert n == len(want) and len(seen) <= 1
        assert all(re.match(r"SELECT coalesce\(sum\(n\), 0\), coalesce\(sum\(h\), 0\) FROM", q)
                   for q in seen)
        with statements(cat) as seen:
            got = rows_of(s)
        assert got == want and len(seen) <= 1
        assert set(s.cuts) <= set(cuts)
    a, b = cuts[0], cuts[1]
    fa, fb = fold.held(a, ev.chains), fold.held(b, ev.chains)
    d = ev.delta(a, b)
    other = lazily(ev, es[0], cuts)
    want_other = folded(fold, ev.chains, es[0], cuts)
    assert rows_of(d.gone | other) == (fa - fb) | want_other
    assert rows_of(d.come & other) == (fb - fa) & want_other
    assert rows_of(d.apply(other)) == (want_other - (fa - fb)) | (fb - fa)
    held = [fold.held(c, ev.chains) for c in cuts]
    assert rows_of(ev.persisted(cuts) ^ other) == frozenset.intersection(*held) ^ want_other
    assert rows_of(ev.existed(cuts) - other) == frozenset.union(*held) - want_other
    counted = ev.in_how_many(other, cuts, names=("digest",))
    pairs = zip(counted.rows.ints("chain").tolist(), counted.rows.ints("seq").tolist(),
                strict=True)
    assert [int(x) for x in counted.counts] == [sum(r in h for h in held) for r in pairs]
    table = ev.pairwise(cuts)
    assert table.sizes == tuple(tuple(len(hi - hj) for hj in held) for hi in held)
    cat.close()


def test_a_count_builds_no_row_and_the_rows_are_one_buffer_a_column() -> None:
    """A count runs one statement and builds no row; the rows come back as columns, each one
    buffer: an integer column an array of int64, the key an array of 32-byte values, text one
    run of bytes with its offsets. So reading the rows makes fewer than one Python object a
    row, whatever their number; a value of text is decoded only when it is asked for."""
    cat = VaultCatalog(Path(":memory:"))
    with cat.deferred():
        for i in range(500):
            cat.record(f"notes/n{i:03}.md", f"d{i}", f"title {i} é", version=i + 1)
    ev = cat.cuts(ALL)
    with statements(cat) as seen:
        assert ev.held().count() == 500
    assert len(seen) == 1 and "count(salt)" in seen[0]
    with statements(cat) as seen:
        cols = ev.held().columns("path_key", "source_path", "title", "version", "closed_at")
    assert len(seen) == 1 and len(cols) == 500
    for name in ("chain", "seq", "version", "closed_at"):
        col = cols[name]
        assert isinstance(col, np.ndarray) and col.dtype == np.int64
    key = cols["path_key"]
    assert isinstance(key, np.ndarray) and key.dtype == np.dtype("V32")
    for name in ("source_path", "title"):
        text = cols[name]
        assert isinstance(text, Text) and isinstance(text.data, bytes)
        assert text.offsets.dtype == np.int64 and len(text.offsets) == 501
    assert cols.row(7) == {"chain": 1, "seq": 10, "path_key": cols.row(7)["path_key"],
                           "source_path": "notes/n007.md", "title": "title 7 é", "version": 8,
                           "closed_at": None}
    assert len(str(cols.row(7)["path_key"])) == 64
    assert cols.ints("seq").tolist() == sorted(cols.ints("seq").tolist())
    with pytest.raises(CutError, match="no column"):
        ev.held().columns("salt")
    cat.close()


def test_each_side_of_a_difference_walks_what_changed() -> None:
    """The rows come between two cuts are read on the primary key from the first cut's position,
    and the rows gone on `landings_closed` between the two positions: neither walks the prefix,
    so a difference costs what changed and not what is held (§4.4). What a cut holds walks its
    prefix."""
    cat = VaultCatalog(Path(":memory:"))
    with cat.deferred():
        for i in range(2000):
            cat.record(f"notes/n{i:04}.md", f"d{i}", "t")
    ev0 = cat.cuts(ALL)
    a = ev0.head
    with cat.deferred():
        for i in range(0, 2000, 100):
            cat.record(f"notes/n{i:04}.md", f"e{i}", "t")
    ev = cat.cuts(ALL)
    d = ev.delta(a)

    def plan(q: str) -> str:
        return " ".join(str(tuple(r)[-1]) for r in cat._conn.execute("EXPLAIN QUERY PLAN " + q))

    with statements(cat) as seen:
        d.come.count()
        d.gone.count()
        ev.held().count()
    come, gone, held = (plan(q) for q in seen)
    assert "PRIMARY KEY (chain=? AND seq>? AND seq<?)" in come, come
    assert "landings_closed (chain=? AND closed_at>? AND closed_at<?)" in gone, gone
    assert "PRIMARY KEY (chain=? AND seq<?)" in held, held
    assert d.counts().replaced == 20
    cat.close()


# --- 5. append invariance of every result (SNP-14 with SNP-1) -------------------------------------

@SETTINGS
@given(legacy, ops, ops, st.data())
def test_every_result_at_cuts_inside_the_log_is_unchanged_by_later_writes(
        before: list[tuple[Any, ...]], first: list[tuple[Any, ...]],
        later: list[tuple[Any, ...]], data: st.DataObject) -> None:
    """Sets, signed differences and counts taken at cuts inside the log read the same after any
    further writes, up to the holes a later purge leaves: a row emptied since is gone from them,
    and nothing else changes. So does the same lazy value made before the writes (SNP-14, SNP-1)."""
    cat, taken = build(before, first)
    ev = cat.cuts(ALL)
    a, b = cuts_of(data, taken, ev, 2)
    sets = {"a": ev.held(a), "b": ev.held(b), "union": ev.held(a) | ev.held(b),
            "gone": ev.delta(a, b).gone, "come": ev.delta(a, b).come,
            "persisted": ev.persisted([a, b])}
    then = {name: rows_of(s) for name, s in sets.items()}
    rows_then = {r: cat.read_at(r[0], r[1])[-1] for rs in then.values() for r in rs}
    for op in later:
        apply(cat, op)
    holes = {r for r in rows_then if cat.read_at(r[0], r[1])[-1].hole}
    again = cat.cuts(ALL)
    a2, b2 = again.cut(a), again.cut(b)
    now = {"a": again.held(a2), "b": again.held(b2), "union": again.held(a2) | again.held(b2),
           "gone": again.delta(a2, b2).gone, "come": again.delta(a2, b2).come,
           "persisted": again.persisted([a2, b2])}
    for name, s in now.items():
        assert rows_of(s) == then[name] - holes == rows_of(sets[name])
        assert s.count() == len(then[name] - holes)
    for r in set(rows_then) - holes:
        row = cat.read_at(r[0], r[1])[-1]
        assert (row.seq, row.digest, row.source_path, row.doc_id) == \
            (rows_then[r].seq, rows_then[r].digest, rows_then[r].source_path,
             rows_then[r].doc_id)
    cat.close()


# --- 6. contents against positions (SNP-15) -------------------------------------------------------

@SETTINGS
@given(st.lists(st.tuples(st.integers(0, 40), st.sampled_from(CLASSES)), min_size=1,
                max_size=30, unique_by=lambda w: w[0]), st.data())
def test_on_a_class_with_no_closes_the_join_holds_the_union(
        landings: list[tuple[int, Provenance]], data: st.DataObject) -> None:
    """In classes each of whose paths lands once and is never written again, no row is ever
    closed, and the contents of the join of two cuts are the union of their contents and those
    of the meet their intersection, for every pair of cuts taken; on any log, what either holds
    is what their join holds with the rows closed between their meet and their join (SNP-15)."""
    cat = VaultCatalog(Path(":memory:"))
    taken = [Cut()]
    for i, cls in landings:
        cat.record(f"once/{i}.md", f"d{i}", "t", provenance=cls)
        taken.append(Cut.of(heads(cat)))
    ev = cat.cuts(ALL)
    assert tuple(cat._conn.execute(
        "SELECT count(*) FROM landings WHERE closed_at IS NOT NULL").fetchone()) == (0,)
    pairs = list(itertools.combinations(taken, 2))
    for a, b in data.draw(st.lists(st.sampled_from(pairs), max_size=12)) if pairs else []:
        x, y = ev.cut(a), ev.cut(b)
        assert rows_of(ev.held(x.join(y))) == rows_of(ev.held(x) | ev.held(y))
        assert rows_of(ev.held(x.meet(y))) == rows_of(ev.held(x) & ev.held(y))
    cat.close()


@SETTINGS
@given(legacy, ops, st.data())
def test_the_union_is_the_join_with_the_rows_closed_between(
        before: list[tuple[Any, ...]], writes: list[tuple[Any, ...]],
        data: st.DataObject) -> None:
    """On any log, what either of two cuts holds is what their join holds with the rows gone
    between their meet and their join, and what both hold is what the meet and the join both
    hold (`Held.has_union_cut`, `Held.has_inter_cut`)."""
    cat, taken = build(before, writes)
    ev = cat.cuts(ALL)
    for _ in range(6):
        a, b = cuts_of(data, taken, ev, 2)
        lo, hi = a.meet(b), a.join(b)
        assert rows_of(ev.held(a) | ev.held(b)) == rows_of(ev.held(hi) | ev.delta(lo, hi).gone)
        assert rows_of(ev.held(a) & ev.held(b)) == rows_of(ev.held(lo) & ev.held(hi))
    cat.close()


def test_after_one_edit_the_union_holds_both_versions_and_the_join_one() -> None:
    """The control (`Witness.union_ne_join`): a note edited between two cuts. The union on
    contents holds both its versions, the contents of the join, a cut, the later one alone."""
    cat = VaultCatalog(Path(":memory:"))
    cat.record("note.md", "first", "N")
    a = cat.cuts(ALL).head
    cat.record("note.md", "second", "N")
    ev = cat.cuts(ALL)
    b = ev.head
    union = (ev.held(a) | ev.held(b)).columns("digest")
    join = ev.held(a.join(b)).columns("digest")
    assert [union.row(i)["digest"] for i in range(len(union))] == ["first", "second"]
    assert [join.row(i)["digest"] for i in range(len(join))] == ["second"]
    assert a.join(b) == b and (ev.held(a) | ev.held(b)).count() == 2
    cat.close()


# --- 7. the grant (SNP-16) ------------------------------------------------------------------------

@SETTINGS
@given(legacy, ops, st.lists(st.tuples(st.integers(0, 5), st.sampled_from(["x", "y"])),
                             min_size=1, max_size=12), st.data())
def test_one_class_reads_only_its_chains(
        before: list[tuple[Any, ...]], writes: list[tuple[Any, ...]],
        others: list[tuple[int, str]], data: st.DataObject) -> None:
    """The sets and signed differences of one class read only its chains: every statement names
    those chains and no other; the results are the same after writes to another class and
    whatever positions a cut names on another class's chains; and a cut given with such
    positions reads none of them (SNP-16)."""
    cat, taken = build(before, writes)
    classes = [cls for cls in ALL if cat.chains(cls)]
    if not classes:
        return
    mine = data.draw(st.sampled_from(classes))
    elsewhere = next(c for c in ALL if c != mine)
    ev = cat.cuts([mine])
    assert set(ev.chains) == set(cat.chains(mine))
    a, b = cuts_of(data, taken, ev, 2)
    with statements(cat) as seen:
        before_rows = (rows_of(ev.held(a)), rows_of(ev.delta(a, b).gone),
                       rows_of(ev.delta(a, b).come), ev.delta(a, b).counts())
    named = {int(x) for q in seen for x in re.findall(r"chain = (\d+)", q)}
    assert named <= set(ev.chains)
    for i, tag in others:                       # writes to another class only
        cat.record(f"elsewhere/{i}.md", f"other-{tag}", "t", provenance=Provenance(elsewhere))
    again = cat.cuts([mine])
    assert again.chains == ev.chains
    noise = {k: 10_000 + k for k in cat._log.all_chains() if k not in ev.chains}
    a2, b2 = Cut.of({**a.as_dict(), **noise}), Cut.of({**b.as_dict(), **noise})
    assert again.cut(a2) == a and again.cut(b2) == b
    after = (rows_of(again.held(a2)), rows_of(again.delta(a2, b2).gone),
             rows_of(again.delta(a2, b2).come), again.delta(a2, b2).counts())
    assert after == before_rows
    cat.close()


# --- 8. erasure and retire (SNP-17) ---------------------------------------------------------------

@SETTINGS
@given(legacy, ops, st.data())
def test_a_purge_takes_its_rows_out_of_every_set_and_a_retire_is_a_removal(
        before: list[tuple[Any, ...]], writes: list[tuple[Any, ...]],
        data: st.DataObject) -> None:
    """After a purge of a digest no path holds, no set and no difference at any cut holds a row
    that carried it, every other row of every set is the row it was, and every count falls by
    the rows purged. A retire is a removal in every difference from a cut that holds the retired
    version to a cut at the retire or after it while the path stays retired, and every cut
    between the version's landing and the retire holds it (SNP-17)."""
    cat, taken = build(before, writes)
    ev = cat.cuts(ALL)
    fold = Fold.of(cat)
    cuts = [ev.cut(c) for c in taken]
    digests = sorted({str(fold.row(r).digest) for c in cuts for r in fold.held(c, ev.chains)})
    if digests:
        digest = data.draw(st.sampled_from(digests))
        if cat.active_refs(digest) == 0:
            sets = {c: rows_of(ev.held(c)) for c in cuts}
            holes = {c: ev.held(c).holes() for c in cuts}
            purged = {r for rs in sets.values() for r in rs if fold.row(r).digest == digest}
            pairs = list(zip(cuts, cuts[1:], strict=False))
            deltas = {p: (rows_of(ev.delta(*p).gone), rows_of(ev.delta(*p).come)) for p in pairs}
            cat.remove_digest(digest)
            after = cat.cuts(ALL)
            for c, rows in sets.items():
                assert rows_of(after.held(c)) == rows - purged
                assert after.held(c).count() == len(rows - purged)
                assert after.held(c).holes() == holes[c] + len(rows & purged)
            for pair, (g, c2) in deltas.items():
                d = after.delta(*pair)
                assert (rows_of(d.gone), rows_of(d.come)) == (g - purged, c2 - purged)
            for r in {r for rs in sets.values() for r in rs} - purged:
                assert cat.read_at(r[0], r[1])[-1] == fold.row(r)   # the row it was
            ev, fold = after, Fold.of(cat)
    for ch, chain_rows in fold.rows.items():
        if ch not in ev.chains:
            continue
        for retire in (r for r in chain_rows if r.kind == "retire"):
            version = next((r for r in reversed(chain_rows[:retire.seq - 1])
                            if r.path_key == retire.path_key), None)
            if version is None or version.kind != "store" or version.hole:
                continue
            for at in range(version.seq, retire.seq):
                assert (ch, version.seq) in rows_of(ev.held(Cut.of({ch: at})))
            end = retire.closed_at or ev.head.at(ch) + 1
            for at in {version.seq, retire.seq - 1}:
                for q in {retire.seq, end - 1}:
                    s = ev.delta(Cut.of({ch: at}), Cut.of({ch: q})).sorted()
                    removed = set(zip(s.removed.ints("chain").tolist(),
                                      s.removed.ints("seq").tolist(), strict=True))
                    assert (ch, version.seq) in removed
    cat.close()


# --- 9. the default (D27) -------------------------------------------------------------------------

@SETTINGS
@given(legacy, ops, ops)
def test_an_evaluation_reads_one_head_in_every_part_and_names_it(
        before: list[tuple[Any, ...]], first: list[tuple[Any, ...]],
        later: list[tuple[Any, ...]]) -> None:
    """Every operation of one evaluation that names no cut reads the head the evaluation read when
    it started, even with writes between its parts, and its result names that head; asked again
    in a new evaluation with the positions named, after further writes, it is the same up to the
    holes a later purge leaves (D27, SNF-19)."""
    cat, _ = build(before, first)
    ev = cat.cuts(ALL)
    head = ev.head
    held = ev.held()
    apply_first = rows_of(held)
    for op in later[: len(later) // 2]:
        apply(cat, op)
    since = ev.delta(BOTTOM)
    assert held.cuts == (head,) and (since.a, since.b) == (BOTTOM, head)
    assert ev.between().upto == head and ev.persisted().cuts == (head,)
    assert ev.count_series().cuts == (head,)
    for op in later[len(later) // 2:]:
        apply(cat, op)
    again = cat.cuts(ALL)
    holes = {r for r in apply_first if cat.read_at(r[0], r[1])[-1].hole}
    assert rows_of(again.held(again.cut(head))) == apply_first - holes == rows_of(held)
    assert rows_of(since.come) == apply_first - holes
    assert again.head >= head
    cat.close()


def test_a_cut_past_the_head_or_of_an_unread_chain_is_refused() -> None:
    """A cut is taken inside the log: a position past a chain's head is refused, and the refusal
    names the head. A name of a chain the evaluation does not read is refused in the words used
    for a chain that does not exist; a cut given with positions on such a chain reads none of
    them. A malformed name is refused and says how a cut is named."""
    cat = VaultCatalog(Path(":memory:"))
    cat.record("a.md", "d1", "A")
    cat.record("c.md", "d2", "C", provenance=Provenance.CURATED)
    ev = cat.cuts(["authored-solo"])
    (solo,) = ev.chains
    (cur,) = cat.chains(Provenance.CURATED)
    head = ev.head.at(solo)
    with pytest.raises(CutError, match=rf"land.{solo}@{head + 1} is past the chain's head, "
                                       rf"land.{solo}@{head}"):
        ev.held(Cut.of({solo: head + 1}))
    with pytest.raises(CutError, match=rf"there is no chain land.{cur}; the chains read here "
                                       rf"are land.{solo}"):
        ev.named(f"land.{cur}@1")
    with pytest.raises(CutError, match="there is no chain land.99"):
        ev.named("land.99@1")
    assert ev.cut(Cut.of({solo: head, cur: 3})) == Cut.of({solo: head})
    for bad in ("land.1", "land.x@2", "1@2", "land.1@2 land.1@3", ""):
        with pytest.raises(CutError):
            ev.named(bad)
    assert ev.named("head") == ev.head and ev.named("bottom") == BOTTOM
    with pytest.raises(CutError, match="a cut is expected"):
        ev.held(ev.held())          # type: ignore[arg-type]
    with pytest.raises(CutError, match="combines with a set of versions, not with a cut"):
        ev.held() | ev.head         # type: ignore[operator]
    cat.close()


def test_a_position_under_a_chains_horizon_is_read_at_its_empty_prefix() -> None:
    """A chain's positions before its horizon are its genesis block, which is not history (§8):
    a cut asked there is read at the chain's empty prefix, and the chain is named as read below
    the position asked. The horizon and every position after it are served, and the head with
    no walk."""
    db_rows: list[tuple[str, str, str, Provenance, bool, str | None]] = [
        ("v/a.md", "da", "A", Provenance.AUTHORED_SOLO, True, None),
        ("v/b.md", "db", "B", Provenance.AUTHORED_SOLO, True, None)]
    cat = from_legacy(db_rows)
    (solo,) = cat.chains(Provenance.AUTHORED_SOLO)
    horizon = cat.head(solo)                        # genesis, two stores, the horizon
    cat.record("v/c.md", "dc", "C")
    ev = cat.cuts(ALL)
    for p in range(1, horizon):
        read, lowered = ev.served(Cut.of({solo: p}))
        assert read == BOTTOM and lowered == [(solo, p)]
    for p in range(horizon, ev.head.at(solo) + 1):
        assert ev.served(Cut.of({solo: p})) == (Cut.of({solo: p}), [])
    assert ev.served(BOTTOM) == (BOTTOM, [])
    assert ev.held(Cut.of({solo: horizon})).count() == 2
    cat.close()


def test_a_delta_from_another_evaluation_or_of_another_kind_is_refused() -> None:
    cat = VaultCatalog(Path(":memory:"))
    cat.record("a.md", "d1", "A")
    one, two = cat.cuts(ALL), cat.cuts(ALL)
    with pytest.raises(CutError, match="inside one evaluation"):
        one.held() | two.held()
    d: Delta = one.delta(BOTTOM)
    with pytest.raises(CutError, match="composes with a signed difference, not with a set"):
        d.then(one.held())          # type: ignore[arg-type]
    cat.close()
