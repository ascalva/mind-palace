"""The lexical index's statements and its kept statistics (core/stores/lexical.py).

The keyword statements start from the query terms' postings (or from the given paths' units),
read the unit count, the mean length and the document frequencies from per-class tables that
every write changing which units are current keeps in its own transaction, and compute the
arithmetic, the sum over the terms and the top k in one statement. Three laws, over generated
stores (several classes, three tokenizers, ties, empty and absent classes, paths given and not):

1. the ranking is the old statements' to the bit: the same units in the same order with the same
   scores, for `search` and `scores`, every shape a caller uses (the old statements are kept,
   verbatim from the store before the change, in `tests/fixtures/lexical_reference.py`);
2. after any sequence of landings, re-landings, batched landings (one transaction landing a path
   more than once), retires and re-derivations, the stored statistics equal a recount from the
   units;
3. a reader's statistics, and so its scores, are a function of its cleared classes' units alone:
   a store that also holds other classes' units, landed and retired around the cleared ones,
   answers the reader exactly as a store holding the cleared units alone.

A control shows the first law has teeth: SQLite's `sum()` compensates its rounding, so a sum
taken by it differs from the reference's left-to-right sum, which the statement writes out.
"""

from __future__ import annotations

import sqlite3
import tempfile
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from core.ingest.lexical import LEGACY, TOKENIZER, Tokenizer
from core.kernel.ingest.chunk import Chunk
from core.kernel.provenance import Provenance
from core.stores.lexical import LexicalStore
from tests.fixtures.lexical_reference import new_search, old_scores, old_search, recount

CLASSES = [Provenance.AUTHORED_SOLO, Provenance.OBSERVED, Provenance.CURATED,
           Provenance.AUTHORED_DIALOGUE]
TOKENIZERS = [TOKENIZER, LEGACY, Tokenizer("NFC", "lower", False)]
# a small vocabulary, so units share terms and scores tie; forms that tokenizers tell apart
WORDS = ["graph", "Graph", "spectral", "gap", "random", "walk", "the", "of", "café", "café",
         "Straße", "strasse", "ﬁnancial", "x²", "x2"]
PATHS = [f"p{i}" for i in range(6)]

text = st.lists(st.sampled_from(WORDS), min_size=0, max_size=7).map(" ".join)
chunks = st.lists(text, min_size=0, max_size=3)
land = st.tuples(st.just("land"), st.sampled_from(PATHS), st.sampled_from(["v0", "v1", "v2"]),
                 st.sampled_from(CLASSES), chunks)
# one transaction of several versions, a path and a digest drawn again and again among them, so a
# unit's currency can move more than once before the batch's statistics move (`land_many`)
item = st.tuples(st.sampled_from(PATHS[:3]), st.sampled_from(["v0", "v1"]),
                 st.sampled_from(CLASSES), chunks)
batch = st.tuples(st.just("batch"), st.lists(item, min_size=1, max_size=6))
retire = st.tuples(st.just("retire"), st.sampled_from(PATHS))
rederive = st.tuples(st.just("rederive"))
ops = st.lists(st.one_of(land, land, land, batch, retire, rederive), min_size=1, max_size=14)
query = st.lists(st.sampled_from([*WORDS, "absent", "nowhere"]), min_size=0, max_size=5).map(
    " ".join)
classes = st.one_of(st.none(), st.lists(st.sampled_from(CLASSES), max_size=3))
paths = st.one_of(st.none(), st.lists(st.sampled_from([*PATHS, "nope"]), max_size=4))
asks = st.lists(st.tuples(query, classes, paths, st.sampled_from([1, 2, 3, 10, 0, -1])),
                min_size=1, max_size=6)
SETTINGS = settings(deadline=None, max_examples=60,
                    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])


def _chunks(texts: Sequence[str]) -> list[Chunk]:
    return [Chunk(i, t) for i, t in enumerate(texts)]


def apply(store: LexicalStore, steps: Iterable[tuple[Any, ...]],
          active: dict[str, tuple[str, str, list[str]]],
          after: Any = None) -> None:
    """Run the operations; `active` follows what a catalog would hold (the re-derivation lands
    it again, as `derive.derive_lexical` lands every active item)."""
    for step in steps:
        if step[0] == "land":
            _, path, digest, klass, texts = step
            store.land(source_path=path, digest=digest, provenance=klass.value, title=path,
                       chunks=_chunks(texts))
            active[path] = (digest, klass.value, list(texts))
        elif step[0] == "batch":
            store.land_many([(p, d, k.value, p, _chunks(t)) for p, d, k, t in step[1]])
            for p, d, k, t in step[1]:          # the batch's last version of a path is current
                active[p] = (d, k.value, list(t))
        elif step[0] == "retire":
            store.retire(step[1])
            active.pop(step[1], None)
        else:
            store.reset()
            store.land_many([(p, d, c, p, _chunks(t)) for p, (d, c, t) in sorted(active.items())])
        if after is not None:
            after(store)


# ── 1. the ranking is the old statements', to the bit ─────────────────────────────────────────

@SETTINGS
@given(tok=st.sampled_from(TOKENIZERS), steps=ops, asked=asks)
def test_the_statements_rank_as_the_old_ones_to_the_bit(tok: Tokenizer, steps: list[Any],
                                                         asked: list[Any]) -> None:
    with tempfile.TemporaryDirectory() as d:
        store = LexicalStore(Path(d) / "lex.sqlite", tokenizer=tok)
        apply(store, steps, {})
        for q, cls, ps, k in asked:
            assert new_search(store, q, k=k, classes=cls, paths=ps) == \
                old_search(store, q, k=k, classes=cls, paths=ps)
            assert store.scores(q, classes=cls, paths=ps) == old_scores(store, q, classes=cls,
                                                                        paths=ps)
        store.close()


@SETTINGS
@given(tok=st.sampled_from(TOKENIZERS), steps=ops, asked=asks)
def test_a_query_past_the_written_sums_length_ranks_as_the_old_ones_too(
        tok: Tokenizer, steps: list[Any], asked: list[Any]) -> None:
    """A query of more terms than one written-out sum takes (`_SUM_TERMS`, here lowered to one so
    generated queries reach it) has its weights summed outside the statement, in the same order:
    the same law."""
    import core.stores.lexical as module

    limit = module._SUM_TERMS
    module._SUM_TERMS = 1
    try:
        with tempfile.TemporaryDirectory() as d:
            store = LexicalStore(Path(d) / "lex.sqlite", tokenizer=tok)
            apply(store, steps, {})
            for q, cls, ps, k in asked:
                assert new_search(store, q, k=k, classes=cls, paths=ps) == \
                    old_search(store, q, k=k, classes=cls, paths=ps)
                assert store.scores(q, classes=cls, paths=ps) == \
                    old_scores(store, q, classes=cls, paths=ps)
            store.close()
    finally:
        module._SUM_TERMS = limit


def test_a_query_of_more_terms_than_sqlite_parses_in_one_sum(tmp_path: Path) -> None:
    store = LexicalStore(tmp_path / "lex.sqlite")
    words = [f"w{i}" for i in range(1200)]
    store.land(source_path="a", digest="v", provenance=Provenance.OBSERVED.value, title="a",
               chunks=_chunks([" ".join(words[:700]), " ".join(words[500:])]))
    store.land(source_path="b", digest="v", provenance=Provenance.CURATED.value, title="b",
               chunks=_chunks([" ".join(words[::3])]))
    for n in (499, 500, 501, 1200):
        q = " ".join(words[:n])
        for cls in (None, [Provenance.OBSERVED]):
            assert new_search(store, q, k=3, classes=cls) == old_search(store, q, k=3,
                                                                       classes=cls)
            assert store.scores(q, classes=cls, paths=["a", "b"]) == \
                old_scores(store, q, classes=cls, paths=["a", "b"])


def test_ties_are_broken_by_unit_id_and_scores_are_equal_bit_for_bit(tmp_path: Path) -> None:
    store = LexicalStore(tmp_path / "lex.sqlite")
    for i in range(12):                    # identical units: every score ties
        store.land(source_path=f"t{i:02d}", digest="v", provenance=Provenance.OBSERVED.value,
                   title="t", chunks=_chunks(["spectral gap of a random graph"]))
    store.land(source_path="u", digest="v", provenance=Provenance.CURATED.value, title="u",
               chunks=_chunks(["spectral spectral gap", "graph"]))
    for q in ("spectral gap", "random graph gap", "graph"):
        for cls in (None, [Provenance.OBSERVED], [Provenance.CURATED, Provenance.OBSERVED]):
            got, want = new_search(store, q, k=5, classes=cls), old_search(store, q, k=5,
                                                                         classes=cls)
            assert got == want
            assert [s.hex() for *_, s in got] == [s.hex() for *_, s in want]
    assert [h.source_path for h in store.search("graph", k=3,
                                                classes=[Provenance.OBSERVED])] == \
        ["t00", "t01", "t02"]


def test_sqlites_own_sum_is_not_the_reference_sum_the_control() -> None:
    """Why the statement writes the sum out: `sum()` compensates its rounding (Kahan, Babuska and
    Neumaier), so over the same values in the same order it can give another double than the
    reference loop's left-to-right sum, which the written-out sum reproduces."""
    values = [1.0, 2.0 ** -53, 2.0 ** -53]
    reference = 0.0
    for v in values:
        reference += v
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE r (i INTEGER PRIMARY KEY, c REAL)")
    conn.executemany("INSERT INTO r VALUES (?, ?)", list(enumerate(values)))
    (compensated,) = conn.execute("SELECT sum(c) FROM (SELECT c FROM r ORDER BY i)").fetchone()
    (written,) = conn.execute(
        "SELECT " + " + ".join(f"COALESCE(max(c) FILTER (WHERE i = {i}), 0.0)"
                               for i in range(len(values))) + " FROM r").fetchone()
    assert compensated != reference and written == reference


# ── 2. the stored statistics are a recount of the units ───────────────────────────────────────

@SETTINGS
@given(tok=st.sampled_from(TOKENIZERS), steps=ops)
def test_the_statistics_equal_a_recount_after_any_sequence(tok: Tokenizer,
                                                           steps: list[Any]) -> None:
    with tempfile.TemporaryDirectory() as d:
        store = LexicalStore(Path(d) / "lex.sqlite", tokenizer=tok)
        apply(store, steps, {}, after=recount)
        store.close()
        again = LexicalStore(Path(d) / "lex.sqlite", tokenizer=tok)   # reopened: kept, not redone
        recount(again)
        again.close()


def test_a_relanding_with_other_chunks_moves_the_statistics_before_its_postings_go(
        tmp_path: Path) -> None:
    """A version landed again with other chunks deletes its units and their postings; units that
    were current leave the statistics while their postings still exist."""
    store = LexicalStore(tmp_path / "lex.sqlite")
    store.land(source_path="a", digest="v", provenance=Provenance.OBSERVED.value, title="a",
               chunks=_chunks(["alpha beta", "gamma"]))
    recount(store)
    store.land(source_path="a", digest="v", provenance=Provenance.OBSERVED.value, title="a",
               chunks=_chunks(["delta"]))
    classes, terms = recount(store)
    assert terms == {("delta", Provenance.OBSERVED.value, 1)}
    # within one batch: made current, then rewritten, then superseded, then made current again
    store.land_many([("b", "v", Provenance.CURATED.value, "b", _chunks(["x y"])),
                     ("b", "v", Provenance.CURATED.value, "b", _chunks(["x", "z"])),
                     ("b", "w", Provenance.CURATED.value, "b", _chunks(["y"])),
                     ("b", "v", Provenance.CURATED.value, "b", _chunks(["x", "z"]))])
    recount(store)
    assert store.statistics(classes=[Provenance.CURATED], terms=["x", "y", "z"]).df == \
        {"x": 1, "z": 1}


# ── 3. a reader's statistics are its cleared classes' own ─────────────────────────────────────

@SETTINGS
@given(tok=st.sampled_from(TOKENIZERS), steps=ops,
       cleared=st.lists(st.sampled_from(CLASSES), min_size=1, max_size=2, unique=True),
       asked=st.lists(query, min_size=1, max_size=4))
def test_a_readers_statistics_ignore_the_classes_it_is_not_cleared_for(
        tok: Tokenizer, steps: list[Any], cleared: list[Provenance], asked: list[str]) -> None:
    """Store `a` takes every operation; store `b` only those on the cleared classes' items (and
    the re-derivations). After every step a reader cleared for those classes sees the same
    statistics in both, and so the same scores and the same ranking."""
    def mine(step: tuple[Any, ...]) -> tuple[Any, ...] | None:
        """The step as store `b` takes it: the cleared classes' items alone, or nothing."""
        if step[0] == "land":
            return step if step[3] in cleared else None
        if step[0] == "batch":
            items = [i for i in step[1] if i[2] in cleared]
            return ("batch", items) if items else None
        if step[0] == "retire" and first.get(step[1]) not in cleared:
            return None
        return step
    # a path keeps its class, as the catalog keeps an item's label (ING-17)
    first: dict[str, Provenance] = {}
    fixed = []
    for step in steps:
        if step[0] == "land":
            klass = first.setdefault(step[1], step[3])
            step = (*step[:3], klass, step[4])
        elif step[0] == "batch":
            step = ("batch", [(p, d, first.setdefault(p, k), t) for p, d, k, t in step[1]])
        fixed.append(step)
    vocabulary = sorted({t for w in WORDS for t in tok(w)})
    with tempfile.TemporaryDirectory() as d:
        a = LexicalStore(Path(d) / "a.sqlite", tokenizer=tok)
        b = LexicalStore(Path(d) / "b.sqlite", tokenizer=tok)
        active_a: dict[str, tuple[str, str, list[str]]] = {}
        active_b: dict[str, tuple[str, str, list[str]]] = {}
        for step in fixed:
            apply(a, [step], active_a)
            theirs = mine(step)
            if theirs is not None:
                apply(b, [theirs], active_b)
            assert a.statistics(classes=cleared, terms=vocabulary) == \
                b.statistics(classes=cleared, terms=vocabulary)
        for q in asked:
            assert a.scores(q, classes=cleared) == b.scores(q, classes=cleared)
            assert new_search(a, q, k=10, classes=cleared) == \
                new_search(b, q, k=10, classes=cleared)
        a.close()
        b.close()
