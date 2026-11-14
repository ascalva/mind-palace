"""The lexical representation (core/ingest/lexical.py) and its store (core/stores/lexical.py):
tokens and BM25 weights with no model, landing idempotent by reconciliation, currency moving with
the version, scores read over current units of the cleared classes (dn-two-phase-ingestion D1,
D2)."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from core.ingest.lexical import (
    LEGACY,
    TOKENIZER,
    LexicalIndex,
    Tokenizer,
    bm25,
    fuse,
    idf,
    rrf,
    term_counts,
    tf_weight,
    tokens,
)
from core.kernel.ingest.chunk import Chunk
from core.kernel.provenance import Provenance
from core.stores.lexical import LexicalStore

AUTHORED, OBSERVED = Provenance.AUTHORED_SOLO.value, Provenance.OBSERVED.value


def test_tokens_are_lower_cased_runs_of_letters_and_digits_in_any_script():
    assert tokens("Graph-theory's 4-colour THEOREM, 1976.") == [
        "graph", "theory", "s", "4", "colour", "theorem", "1976"]
    assert tokens("Café naïve_snake 東京") == ["café", "naïve", "snake", "東京"]
    assert term_counts("a b a") == {"a": 2, "b": 1}


def test_the_weights_are_robertson_and_zaragozas():
    assert idf(4, 2) == pytest.approx(math.log1p((4 - 2 + 0.5) / (2 + 0.5)))
    # a term at the mean length saturates toward k1 + 1 = 2.2 as its count grows
    assert tf_weight(1, 10, 10.0) == pytest.approx(2.2 / 2.2)
    assert tf_weight(100, 10, 10.0) == pytest.approx(100 * 2.2 / 101.2)
    # a longer unit is penalized, a shorter one favoured, by b
    assert tf_weight(1, 20, 10.0) < tf_weight(1, 10, 10.0) < tf_weight(1, 5, 10.0)


def test_the_in_memory_reference_ranks_by_shared_rare_terms():
    units = [term_counts(t) for t in ("spectral gap of a random graph", "random walks on graphs",
                                       "the gap between two numbers", "nothing relevant here")]
    scores = bm25("spectral gap", units)
    assert scores[0] > scores[2] > 0 and scores[1] == 0 and scores[3] == 0
    assert bm25("absent words", units) == [0.0] * 4
    assert bm25("spectral gap", []) == []


def _chunks(*texts: str) -> list[Chunk]:
    return [Chunk(i, t) for i, t in enumerate(texts)]


def test_the_store_scores_as_the_reference_does(tmp_path: Path):
    store = LexicalStore(tmp_path / "lex.sqlite")
    texts = {"a.md": "spectral gap of a random graph", "b.md": "random walks on graphs",
             "c.md": "the gap between two numbers", "d.md": "nothing relevant here"}
    for path, text in texts.items():
        store.land(source_path=path, digest=f"d-{path}", provenance=AUTHORED, title=path,
                   chunks=_chunks(text))
    reference = bm25("spectral gap", [term_counts(t) for t in texts.values()])
    scored = store.scores("spectral gap", classes=[Provenance.AUTHORED_SOLO])
    for (path, _), ref in zip(texts.items(), reference, strict=True):
        if ref > 0:
            assert scored[path] == pytest.approx(ref, rel=1e-9)
        else:
            assert path not in scored
    hits = store.search("spectral gap", k=2, classes=[Provenance.AUTHORED_SOLO])
    assert [h.source_path for h in hits] == ["a.md", "c.md"]
    assert store.search("absent words") == []
    # a path's score is the best of its units
    store.land(source_path="e.md", digest="d-e", provenance=AUTHORED, title="e",
               chunks=_chunks("random graph", "spectral gap spectral gap"))
    best = store.scores("spectral gap")["e.md"]
    assert best == pytest.approx(max(
        s for s in bm25("spectral gap", [term_counts(t) for t in
                                         [*texts.values(), "random graph",
                                          "spectral gap spectral gap"]])[4:]), rel=1e-9)


def test_landing_is_idempotent_and_currency_moves_with_the_version(tmp_path: Path):
    store = LexicalStore(tmp_path / "lex.sqlite")
    first = store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
                       chunks=_chunks("alpha beta", "gamma"))
    assert (first.units_written, first.made_current, first.superseded) == (2, True, 0)
    again = store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
                       chunks=_chunks("alpha beta", "gamma"))
    assert (again.units_written, again.made_current) == (0, False)      # nothing written twice
    assert store.holds_current("a.md", "v1") and store.units_of("a.md") == 2
    second = store.land(source_path="a.md", digest="v2", provenance=AUTHORED, title="A",
                        chunks=_chunks("alpha delta"))
    assert (second.units_written, second.made_current, second.superseded) == (1, True, 2)
    assert store.holds_current("a.md", "v2") and not store.holds_current("a.md", "v1")
    assert store.units_of("a.md", digest="v1", current=False) == 2   # history kept, not current
    assert "a.md" in store.scores("delta") and "a.md" not in store.scores("gamma")
    # a revert to the old bytes writes nothing and makes the old version current again
    back = store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
                      chunks=_chunks("alpha beta", "gamma"))
    assert (back.units_written, back.made_current, back.superseded) == (0, True, 1)
    assert store.retire("a.md") == 2 and store.units_of("a.md") == 0
    assert store.scores("gamma") == {} and store.count() == 0


def test_every_landed_version_is_recorded_with_its_units_even_with_none(tmp_path: Path):
    """The record that tells an item with no text (landed, complete) from one the index never
    saw (landed before the index was opened): the drain's pending set reads it."""
    store = LexicalStore(tmp_path / "lex.sqlite")
    out = store.land_many([("a.md", "v1", AUTHORED, "A", _chunks("alpha beta", "gamma")),
                           ("e.md", "ve", AUTHORED, "E", [])])
    assert [o.units_written for o in out] == [2, 0]
    assert store.landed_versions() == {("a.md", "v1"), ("e.md", "ve")}
    assert store.empty_versions() == {("e.md", "ve")}
    assert store.holds_current("a.md", "v1") and not store.holds_current("e.md", "ve")
    store.land(source_path="a.md", digest="v2", provenance=AUTHORED, title="A",
               chunks=_chunks("delta"))
    assert store.landed_versions() == {("a.md", "v1"), ("a.md", "v2"), ("e.md", "ve")}


def test_land_many_commits_every_version_or_none(tmp_path: Path):
    store = LexicalStore(tmp_path / "lex.sqlite")
    store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
               chunks=_chunks("alpha"))
    broken: Any = [object()]                       # not a chunk: the landing raises midway
    with pytest.raises(AttributeError):
        store.land_many([("b.md", "v1", AUTHORED, "B", _chunks("beta")),
                         ("c.md", "v1", AUTHORED, "C", broken)])
    assert store.landed_versions() == {("a.md", "v1")}
    assert store.units_of("b.md", current=False) == 0 and store.scores("beta") == {}
    assert store.holds_current("a.md", "v1")                  # what was there is untouched


def test_scores_read_only_the_cleared_classes(tmp_path: Path):
    store = LexicalStore(tmp_path / "lex.sqlite")
    store.land(source_path="n.md", digest="dn", provenance=AUTHORED, title="n",
               chunks=_chunks("sleep debt and recovery"))
    store.land(source_path="dialogue/t/1", digest="dt", provenance=OBSERVED, title="t",
               chunks=_chunks("sleep debt, the model said"))
    assert set(store.scores("sleep debt")) == {"n.md", "dialogue/t/1"}
    assert set(store.scores("sleep debt", classes=[Provenance.AUTHORED_SOLO])) == {"n.md"}
    assert store.scores("sleep debt", classes=[]) == {}
    assert set(store.scores("sleep debt", paths=["dialogue/t/1"])) == {"dialogue/t/1"}
    # the document frequencies are the cleared classes' own: with one class cleared, "sleep" is
    # in one unit of one, and its weight is the single-unit idf
    one = store.scores("sleep", classes=[Provenance.AUTHORED_SOLO])["n.md"]
    assert one == pytest.approx(idf(1, 1) * tf_weight(1, 4, 4.0))


def test_reciprocal_rank_fusion_favours_agreement():
    fused = fuse([["a", "b", "c"], ["c", "a", "d"]], k=4)
    assert fused[:2] == ["a", "c"] and set(fused) == {"a", "b", "c", "d"}
    assert fuse([[], []], k=3) == []


# ── the in-memory index of a fixed set of units (the corpus battery's) ──────────────────────────

def test_the_in_memory_index_holds_the_reference_weights():
    texts = ["spectral gap of a random graph", "random walks on graphs",
             "the gap between two numbers", "nothing relevant here"]
    index = LexicalIndex.build(texts)
    assert index.units == 4
    n, df = 4, 2                                         # "gap" is in two of four units
    dl, avgdl = 6, (6 + 4 + 5 + 3) / 4
    w = idf(n, df) * tf_weight(1, dl, avgdl)
    assert index.weights[0, index.vocab["gap"]] == pytest.approx(w, rel=1e-6)
    assert index.scores("spectral gap").tolist() == pytest.approx(
        bm25("spectral gap", [term_counts(x) for x in texts]), rel=1e-5)
    top = index.search("spectral gap", k=2)
    assert top.tolist()[0] == 0 and set(top.tolist()) == {0, 2}
    assert index.search("absent words").tolist() == []
    assert index.search("random", among=np.asarray([1, 2, 3], dtype=np.int64)).tolist() == [1]


def test_the_in_memory_index_survives_a_round_trip(tmp_path: Path):
    index = LexicalIndex.build(["alpha beta", "beta gamma", "gamma delta"])
    assert index.save(tmp_path / "lex") > 0
    back = LexicalIndex.load(tmp_path / "lex")
    assert back.vocab == index.vocab
    assert np.allclose(back.scores("beta gamma"), index.scores("beta gamma"))


def test_rrf_is_fuse_over_unit_numbers_with_ties_by_unit():
    a = np.asarray([1, 2, 3], dtype=np.int64)
    b = np.asarray([3, 1, 4], dtype=np.int64)
    fused = rrf([a, b], k=4).tolist()
    assert fused[:2] == [1, 3]                            # both rank them high
    assert set(fused) == {1, 2, 3, 4}
    assert fused[:2] == fuse([a.tolist(), b.tolist()], k=2)
    assert rrf([np.asarray([7], np.int64), np.asarray([5], np.int64)], k=2).tolist() == [5, 7]


# ── the tokenizer and its identity ──────────────────────────────────────────────────────────────

SAMPLES = ["Graph-theory's 4-colour THEOREM, 1976.", "naïve café Ǆemal", "Straße STRASSE",
           "ﬁnancial ﬂow", "µg μg H₂O x²", "ＡＢＣ１２３", "हिन्दी भाषा", "שָׁלוֹם", "مَرْحَبًا",
           "한국어 텍스트", "snake_case and kebab-case", "İstanbul", "é ́lead"]


def test_the_legacy_tokenizer_is_the_old_runs_of_the_lower_cased_text():
    import re

    old = re.compile(r"[^\W_]+")
    for text in SAMPLES:
        assert LEGACY(text) == old.findall(text.lower())


def test_tokens_is_the_current_tokenizer():
    for text in SAMPLES:
        assert tokens(text) == TOKENIZER(text)


def test_canonically_equivalent_texts_give_one_set_of_terms():
    """One text in two normal forms is one text to a reader: a normalizing tokenizer gives it one
    set of terms, where the legacy tokenizer splits the decomposed form at its marks."""
    import unicodedata

    for tk in (Tokenizer(), Tokenizer("NFC", "lower", False), Tokenizer("NFKC", "lower", True)):
        for text in SAMPLES:
            forms = {tuple(tk(unicodedata.normalize(f, text))) for f in ("NFC", "NFD")}
            assert len(forms) == 1, (tk.identity, text)
    nfd = unicodedata.normalize("NFD", "naïve café")
    assert LEGACY(nfd) == ["nai", "ve", "cafe"] and LEGACY("naïve café") == ["naïve", "café"]
    assert Tokenizer()(nfd) == ["naïve", "café"]


def test_nfkc_folds_compatibility_forms_and_casefold_folds_more_than_lower():
    tk = Tokenizer()
    assert tk("ﬁnancial ﬂow") == ["financial", "flow"]
    assert tk("ＡＢＣ１２３") == ["abc123"]
    assert tk("H₂O x²") == ["h2o", "x2"]
    assert tk("µg") == tk("μg")                       # the micro sign is the Greek letter
    assert tk("Straße") == tk("STRASSE") == ["strasse"]
    assert Tokenizer("NFKC", "lower", True)("Straße") == ["straße"]


def test_combining_marks_continue_a_token():
    """A word whose letters carry marks that compose into no precomposed character (Devanagari's
    vowel signs, Hebrew's points, Arabic's vowels) is one token, not its consonants."""
    tk = Tokenizer()
    assert tk("हिन्दी भाषा") == ["हिन्दी", "भाषा"]
    assert len(tk("שָׁלוֹם")) == 1 and len(tk("مَرْحَبًا")) == 1
    assert LEGACY("हिन्दी भाषा") == ["ह", "न", "द", "भ", "ष"]
    assert tk("snake_case") == ["snake", "case"]       # underscores still split
    assert tk("́lead") == ["lead"]                # a token starts with a letter or digit


def test_the_mark_class_holds_every_combining_mark():
    import re
    import unicodedata

    from core.ingest.lexical import _MARK_PLANES, _marks_class

    marks = [cp for cp in range(0x110000) if unicodedata.category(chr(cp))[0] == "M"]
    assert all(any(lo <= cp < hi for lo, hi in _MARK_PLANES) for cp in marks)
    cls = re.compile(f"[{_marks_class()}]")
    assert all(cls.fullmatch(chr(cp)) for cp in marks)
    assert not any(cls.fullmatch(ch) for ch in "aZ09_ \n-é")


def test_the_fast_token_pattern_matches_the_plain_one():
    """The token pattern with marks is written for speed; it matches what the plain statement of
    the rule matches, a letter or digit then letters, digits and marks."""
    import random
    import re

    from core.ingest.lexical import _marks_class, _pattern

    plain = re.compile(rf"[^\W_](?:[^\W_]|[{_marks_class()}])*")
    fast = _pattern(True)
    rng = random.Random(0)
    alphabet = "ab_ \u0301\u0302é1-\u093f\u0915\U0001d165\U0001e000\U000e0100x\u200d."
    for _ in range(20000):
        s = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 14)))
        assert fast.findall(s) == plain.findall(s), s


def test_a_tokenizer_identity_names_every_parameter_and_round_trips():
    import unicodedata

    from core.ingest.lexical import TokenizerMismatch

    tk = Tokenizer()
    assert tk.identity == f"runs/NFKC/casefold/marks/unicode-{unicodedata.unidata_version}"
    assert LEGACY.identity.startswith("runs/raw/lower/nomarks/")
    for t in (tk, LEGACY, Tokenizer("NFC", "casefold", False)):
        assert Tokenizer.from_identity(t.identity) == t
    other_unicode = tk.identity.rsplit("/", 1)[0] + "/unicode-1.0.0"
    for bad in (other_unicode, "runs/NFD/lower/marks/x", "nonsense"):
        with pytest.raises(TokenizerMismatch):
            Tokenizer.from_identity(bad)
    with pytest.raises(ValueError):
        Tokenizer(fold="upper")  # type: ignore[arg-type]


def test_the_in_memory_index_tokenizes_queries_as_it_tokenized_its_units(tmp_path: Path):
    import json

    texts = ["Straße und Weg", "strasse", "ﬁnancial report"]
    nfkc = LexicalIndex.build(texts, tokenizer=Tokenizer())
    legacy = LexicalIndex.build(texts, tokenizer=LEGACY)
    assert set(nfkc.search("STRASSE").tolist()) == {0, 1}
    assert set(legacy.search("STRASSE").tolist()) == {1}
    assert nfkc.search("financial").tolist() == [2] and legacy.search("financial").tolist() == []
    nfkc.save(tmp_path / "n")
    back = LexicalIndex.load(tmp_path / "n")
    assert back.tokenizer == Tokenizer() and set(back.search("strasse").tolist()) == {0, 1}
    legacy.save(tmp_path / "l")
    (tmp_path / "l" / "tokenizer.json").unlink()      # an index saved before the record
    assert LexicalIndex.load(tmp_path / "l").tokenizer == LEGACY
    assert json.loads((tmp_path / "n" / "tokenizer.json").read_text())["identity"] == \
        Tokenizer().identity


# ── the store records its tokenizer and refuses another ─────────────────────────────────────────

def test_the_store_records_its_tokenizer_and_refuses_another(tmp_path: Path):
    from core.ingest.lexical import TokenizerMismatch

    path = tmp_path / "lex.sqlite"
    old = LexicalStore(path, tokenizer=LEGACY)
    assert old.recorded_tokenizer() is None and not old.stale      # nothing recorded yet
    old.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
             chunks=_chunks("Straße und Weg"))
    assert old.recorded_tokenizer() == LEGACY.identity
    old.close()
    new = LexicalStore(path, tokenizer=Tokenizer())
    assert new.stale
    with pytest.raises(TokenizerMismatch):
        new.scores("strasse")
    with pytest.raises(TokenizerMismatch):
        new.land(source_path="b.md", digest="v1", provenance=AUTHORED, title="B",
                 chunks=_chunks("strasse"))
    assert new.units_of("b.md", current=False) == 0                  # nothing landed
    assert new.holds_current("a.md", "v1")         # currency does not depend on the terms
    new.reset()
    assert new.recorded_tokenizer() is None and new.count() == 0 and not new.landed_versions()
    new.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
             chunks=_chunks("Straße und Weg"))
    assert new.recorded_tokenizer() == Tokenizer().identity and "a.md" in new.scores("STRASSE")


def test_a_store_from_before_the_record_holds_legacy_units(tmp_path: Path):
    store = LexicalStore(tmp_path / "lex.sqlite", tokenizer=LEGACY)
    store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
               chunks=_chunks("alpha"))
    store._conn.execute("DELETE FROM meta")         # as a store written before the record
    assert store.recorded_tokenizer() == LEGACY.identity and not store.stale
    assert LexicalStore(tmp_path / "lex.sqlite", tokenizer=Tokenizer()).stale
    empty = LexicalStore(tmp_path / "empty.sqlite", tokenizer=Tokenizer())
    assert empty.recorded_tokenizer() is None and not empty.stale


# ── the kept statistics: the migration, the guards, a transaction that dies ────────────────────

def _old_store(path: Path, tokenizer: Tokenizer, *, record: bool = True) -> None:
    """A store written by the code before the statistics existed (its schema and its landing,
    `tests/fixtures/lexical_reference.py`), with a retire as that code retired a path."""
    import sqlite3

    from tests.fixtures.lexical_reference import OLD_DDL, old_land

    conn = sqlite3.connect(str(path), isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")           # as the old store opened its file
    conn.executescript(OLD_DDL)
    for p, d, cls, texts in (("a.md", "v1", AUTHORED, ["spectral gap of a graph", "random"]),
                             ("b.md", "v1", OBSERVED, ["random walks on graphs"]),
                             ("a.md", "v2", AUTHORED, ["spectral gap"]),
                             ("c.md", "v1", OBSERVED, ["the gap between two numbers"]),
                             ("d.md", "v1", AUTHORED, ["nothing relevant"])):
        old_land(conn, tokenizer, p, d, cls, p, _chunks(*texts))
    conn.execute("UPDATE units SET current = 0 WHERE source_path = 'd.md' AND current = 1")
    if not record:
        conn.execute("DELETE FROM meta")
    conn.close()


def test_a_store_from_before_the_statistics_counts_them_on_its_first_open(tmp_path: Path):
    from tests.fixtures.lexical_reference import new_search, old_search, recount

    path = tmp_path / "lex.sqlite"
    _old_store(path, TOKENIZER)
    store = LexicalStore(path)
    classes, terms = recount(store)
    assert classes == {(AUTHORED, 1, 2), (OBSERVED, 2, 9)}
    assert ("gap", OBSERVED, 1) in terms and ("gap", AUTHORED, 1) in terms
    for q in ("spectral gap", "random graphs", "the gap", "absent"):
        for cls in (None, [Provenance.OBSERVED], [Provenance.AUTHORED_SOLO]):
            assert new_search(store, q, k=10, classes=cls) == old_search(store, q, k=10,
                                                                         classes=cls)
    store.close()
    again = LexicalStore(path)                        # counted once: a second open counts nothing
    assert again.statistics().units == 3 and again.statistics(terms=["gap"]).df == {"gap": 2}


def test_a_stale_store_is_counted_by_its_reset_not_by_its_open(tmp_path: Path):
    import sqlite3

    path = tmp_path / "lex.sqlite"
    _old_store(path, LEGACY, record=False)            # LEGACY's units, from before the record
    store = LexicalStore(path)                        # the current tokenizer: stale
    assert store.stale and not store._counted()
    assert store._conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'class_stats'"
                               ).fetchone() is None   # its open wrote nothing
    raw = sqlite3.connect(str(path), isolation_level=None)
    raw.execute("UPDATE units SET current = 1 WHERE source_path = 'd.md'")   # nothing guards it
    raw.close()
    store.reset()
    store.land(source_path="a.md", digest="v3", provenance=AUTHORED, title="A",
               chunks=_chunks("Straße und Weg"))
    from tests.fixtures.lexical_reference import recount

    assert recount(store)[0] == {(AUTHORED, 1, 3)}
    assert "a.md" in store.scores("strasse")


def test_the_units_refuse_a_write_that_does_not_keep_the_statistics(tmp_path: Path):
    """A process of the code before the statistics (or any writer but this class) would change
    which units are current without moving the statistics; the units refuse it, whole."""
    import sqlite3

    from tests.fixtures.lexical_reference import old_land, recount

    path = tmp_path / "lex.sqlite"
    store = LexicalStore(path)
    store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
               chunks=_chunks("alpha beta", "gamma"))
    kept = recount(store)
    raw = sqlite3.connect(str(path), isolation_level=None)
    for sql in ("UPDATE units SET current = 0 WHERE source_path = 'a.md'",
                "DELETE FROM units WHERE source_path = 'a.md'",
                "INSERT INTO units (source_path, digest, chunk_index, provenance, title, length, "
                "current, landed_at) VALUES ('b.md', 'v', 0, 'observed', 'B', 1, 1, 'now')"):
        with pytest.raises(sqlite3.IntegrityError, match="keeps statistics"):
            raw.execute(sql)
    with pytest.raises(sqlite3.IntegrityError):
        old_land(raw, store.tokenizer, "b.md", "v1", OBSERVED, "B", _chunks("beta"))
    raw.close()
    assert recount(store) == kept and store.units_of("b.md", current=False) == 0
    assert store.retire("a.md") == 2 and recount(store) == (set(), set())


def test_a_transaction_that_dies_between_the_units_and_the_statistics_leaves_neither(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The statistics move once a transaction, after every unit row of it is written (a retire's
    after its currency moved): an exception there leaves neither the rows nor the statistics."""
    from tests.fixtures.lexical_reference import recount

    store = LexicalStore(tmp_path / "lex.sqlite")
    store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
               chunks=_chunks("alpha beta"))
    kept = recount(store)
    keep, seen = LexicalStore._keep, []

    def dying(self: LexicalStore, changes: dict[int, int]) -> None:
        if not changes:                   # a version's own call, before its rows: nothing moves
            keep(self, changes)
            return
        seen.append(self._conn.execute(
            "SELECT (SELECT count(*) FROM units WHERE source_path = 'b.md'), "
            "(SELECT count(*) FROM units WHERE source_path = 'a.md' AND current = 1)").fetchone())
        raise RuntimeError("died after the unit rows, before the statistics")
    monkeypatch.setattr(LexicalStore, "_keep", dying)
    with pytest.raises(RuntimeError):
        store.land_many([("b.md", "v1", OBSERVED, "B", _chunks("beta gamma")),
                         ("a.md", "v2", AUTHORED, "A", _chunks("delta"))])
    with pytest.raises(RuntimeError):
        store.retire("a.md")
    monkeypatch.undo()
    # the batch died with b.md's unit written and a.md's new version current; the retire with
    # a.md's units no longer current
    assert seen == [(1, 1), (0, 0)]
    assert recount(store) == kept
    assert store.units_of("b.md", current=False) == 0 and store.holds_current("a.md", "v1")
    assert store.landed_versions() == {("a.md", "v1")}


def test_a_write_killed_before_its_commit_leaves_neither(tmp_path: Path):
    """The process dies (no exception, no rollback) at the statistics, after the unit rows: a
    landing with its units written and made current, a retire with its currency moved. The
    uncommitted transaction is gone when the store is opened again."""
    import subprocess
    import sys

    from tests.fixtures.lexical_reference import recount

    path = tmp_path / "lex.sqlite"
    store = LexicalStore(path)
    store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
               chunks=_chunks("alpha beta"))
    kept = recount(store)
    store.close()
    script = (
        "import os, sys\n"
        "from pathlib import Path\n"
        "from core.kernel.ingest.chunk import Chunk\n"
        "from core.stores.lexical import LexicalStore\n"
        "keep = LexicalStore._keep\n"
        "def dying(self, changes):\n"
        "    if not changes:\n"
        "        return keep(self, changes)\n"
        "    row = self._conn.execute(\"SELECT (SELECT count(*) FROM units WHERE current = 1 \"\n"
        "                             \"AND source_path = 'b.md'), (SELECT count(*) FROM units \"\n"
        "                             \"WHERE current = 1 AND source_path = 'a.md')\").fetchone()\n"
        "    print(*row, flush=True)\n"
        "    os._exit(9)\n"
        "LexicalStore._keep = dying\n"
        "s = LexicalStore(Path(sys.argv[1]))\n"
        "if sys.argv[2] == 'land':\n"
        "    s.land_many([('b.md', 'v1', 'observed', 'B', [Chunk(0, 'beta gamma')])])\n"
        "else:\n"
        "    s.retire('a.md')\n")
    for write, inside in (("land", "1 1"), ("retire", "0 0")):
        done = subprocess.run([sys.executable, "-c", script, str(path), write],
                              capture_output=True, text=True)
        assert done.returncode == 9, done.stderr
        assert done.stdout.split() == inside.split()        # it died with its rows written
        again = LexicalStore(path)
        assert recount(again) == kept and again.units_of("b.md", current=False) == 0
        assert again.holds_current("a.md", "v1")
        again.close()


def test_a_write_whose_writer_key_fails_leaves_no_transaction_open(tmp_path: Path):
    """The writer's key is the transaction's first write: when it fails (here a trigger refuses
    it, as a full disk would), the transaction is rolled back, the write lock is free for other
    connections, and the store's next write begins its own."""
    import sqlite3

    from tests.fixtures.lexical_reference import recount

    path = tmp_path / "lex.sqlite"
    store = LexicalStore(path)
    store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
               chunks=_chunks("alpha beta"))
    kept = recount(store)
    raw = sqlite3.connect(str(path), isolation_level=None)
    raw.execute("CREATE TRIGGER refuse_writer BEFORE INSERT ON meta WHEN NEW.key = 'writer' "
                "BEGIN SELECT RAISE(ABORT, 'no room for the key'); END")
    for write in (lambda: store.retire("a.md"), store.reset,
                  lambda: store.land(source_path="b.md", digest="v1", provenance=OBSERVED,
                                     title="B", chunks=_chunks("beta"))):
        with pytest.raises(sqlite3.IntegrityError, match="no room"):
            write()
        assert not store._conn.in_transaction
        raw.execute("BEGIN IMMEDIATE")                       # the lock is free
        raw.execute("ROLLBACK")
    raw.execute("DROP TRIGGER refuse_writer")
    raw.close()
    assert recount(store) == kept
    store.land(source_path="b.md", digest="v1", provenance=OBSERVED, title="B",
               chunks=_chunks("beta"))
    assert store.holds_current("b.md", "v1") and recount(store)[0] == {(AUTHORED, 1, 2),
                                                                        (OBSERVED, 1, 1)}


def test_a_store_opened_while_another_holds_its_lock_opens_at_once_and_counts_its_queries(
        tmp_path: Path):
    """The migration does not wait for the write lock: a store from before the statistics,
    opened while another connection holds the lock (another process counting it, or writing),
    opens at once and scores with statistics counted from the units, the same integers the
    tables will hold, so the same scores; the first query after the lock is free counts them."""
    import sqlite3
    import time

    from tests.fixtures.lexical_reference import new_search, old_scores, old_search, recount

    path = tmp_path / "lex.sqlite"
    _old_store(path, TOKENIZER)
    raw = sqlite3.connect(str(path), isolation_level=None)
    raw.execute("BEGIN IMMEDIATE")                          # another connection's write lock
    t0 = time.perf_counter()
    store = LexicalStore(path)
    assert time.perf_counter() - t0 < 5 and not store._counted()
    asked = [(q, cls) for q in ("spectral gap", "random graphs", "the gap", "absent")
             for cls in (None, [Provenance.OBSERVED], [Provenance.AUTHORED_SOLO])]
    for q, cls in asked:
        assert new_search(store, q, k=10, classes=cls) == old_search(store, q, k=10, classes=cls)
        assert store.scores(q, classes=cls) == old_scores(store, q, classes=cls)
    counted = store.statistics(classes=[Provenance.OBSERVED], terms=["gap", "random"])
    assert not store._counted()
    raw.execute("ROLLBACK")
    raw.close()
    assert new_search(store, "the gap", k=3) == old_search(store, "the gap", k=3)
    assert store._counted()                                 # that query counted them
    assert store.statistics(classes=[Provenance.OBSERVED], terms=["gap", "random"]) == counted
    recount(store)


@pytest.mark.parametrize("fault", ["read-only", "full"])
def test_a_store_that_cannot_take_the_count_opens_and_answers_from_its_units(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str):
    """The count is a write the open and the queries make, and it never fails them. When it
    fails for a reason other than another connection's lock (a file this process cannot write;
    a full file, which SQLite refuses as a full disk refuses it), it is rolled back, the store
    stays as it was and scores as the old statements do, its statistics counted from the units,
    and it does not try the count again until it is opened again; a write fails, as any write
    to such a file does. Its next open counts them."""
    import os
    import sqlite3
    import stat

    from tests.fixtures.lexical_reference import new_search, old_scores, old_search, recount

    path = tmp_path / "lex.sqlite"
    _old_store(path, TOKENIZER)
    connect = sqlite3.connect

    def full(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        conn = connect(*args, **kwargs)
        (pages,) = conn.execute("PRAGMA page_count").fetchone()
        conn.execute(f"PRAGMA max_page_count = {pages}")         # not one page more
        return conn

    if fault == "full":
        monkeypatch.setattr(sqlite3, "connect", full)
    else:
        os.chmod(path, stat.S_IRUSR)
    try:
        store = LexicalStore(path)
        assert not store._counted() and not store._conn.in_transaction
        ran: list[str] = []
        store._conn.set_trace_callback(ran.append)
        for q in ("spectral gap", "random graphs", "the gap", "absent"):
            for cls in (None, [Provenance.OBSERVED], [Provenance.AUTHORED_SOLO]):
                assert new_search(store, q, k=10, classes=cls) == old_search(store, q, k=10,
                                                                             classes=cls)
                assert store.scores(q, classes=cls) == old_scores(store, q, classes=cls)
        assert not any("BEGIN" in s for s in ran) and not store._counted()   # not tried again
        store._conn.set_trace_callback(None)
        with pytest.raises(sqlite3.OperationalError, match="readonly|full"):
            store.land(source_path="e.md", digest="v1", provenance=OBSERVED, title="E",
                       chunks=_chunks(" ".join(f"w{i}" for i in range(2000))))
        assert not store._conn.in_transaction
        store.close()
    finally:
        for name in ("", "-wal", "-shm"):   # SQLite made the companions read-only, as the file
            if Path(f"{path}{name}").exists():
                os.chmod(f"{path}{name}", stat.S_IRUSR | stat.S_IWUSR)
    monkeypatch.undo()
    again = LexicalStore(path)
    assert again._counted()
    recount(again)


# docs/runbook.md, "Reverting the kept lexical statistics": the step, and the check that the
# triggers stay dropped (it finds none)
_REVERT_STEP = ("DROP TRIGGER IF EXISTS units_kept_insert; "
                "DROP TRIGGER IF EXISTS units_kept_update; "
                "DROP TRIGGER IF EXISTS units_kept_delete; "
                "DELETE FROM meta WHERE key = 'statistics';")
_REVERT_CHECK = "SELECT name FROM sqlite_master WHERE type = 'trigger' AND name GLOB 'units_kept_*'"


def test_the_runbooks_revert_step_lets_the_old_code_write_and_the_change_count_again(
        tmp_path: Path):
    """docs/runbook.md, reverting the kept statistics: once the triggers and the record are
    dropped the code before the change writes the units again, and the change, if it lands
    again, counts the statistics anew from them instead of trusting tables nobody kept."""
    import sqlite3

    from tests.fixtures.lexical_reference import old_land, recount

    path = tmp_path / "lex.sqlite"
    store = LexicalStore(path)
    store.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
               chunks=_chunks("alpha beta", "gamma"))
    store.close()
    raw = sqlite3.connect(str(path), isolation_level=None)
    with pytest.raises(sqlite3.IntegrityError):
        old_land(raw, TOKENIZER, "b.md", "v1", OBSERVED, "B", _chunks("beta"))
    raw.executescript(_REVERT_STEP)
    assert raw.execute(_REVERT_CHECK).fetchall() == []
    old_land(raw, TOKENIZER, "b.md", "v1", OBSERVED, "B", _chunks("beta"))
    old_land(raw, TOKENIZER, "a.md", "v2", AUTHORED, "A", _chunks("delta"))
    raw.close()
    again = LexicalStore(path)                                # the change, landed again
    assert again._counted()
    assert recount(again)[0] == {(AUTHORED, 1, 1), (OBSERVED, 1, 1)}


def test_a_process_of_the_change_left_running_undoes_the_revert_step(tmp_path: Path):
    """docs/runbook.md, reverting the kept statistics: a store of the change still open when the
    step runs counts the statistics again at its next query, from the units as they are then,
    and installs the triggers with them, after which the code before the change cannot write the
    units. So the step waits until no process of the change is left, and its check finds the
    triggers back when one was."""
    import sqlite3

    from tests.fixtures.lexical_reference import old_land, recount

    path = tmp_path / "lex.sqlite"
    live = LexicalStore(path)                         # a process of the change, still running
    live.land(source_path="a.md", digest="v1", provenance=AUTHORED, title="A",
              chunks=_chunks("alpha beta", "gamma"))
    raw = sqlite3.connect(str(path), isolation_level=None)
    raw.executescript(_REVERT_STEP)
    old_land(raw, TOKENIZER, "b.md", "v1", OBSERVED, "B", _chunks("beta"))   # the reverted code
    assert raw.execute(_REVERT_CHECK).fetchall() == [] and not live._counted()
    assert [h.source_path for h in live.search("alpha", k=3)] == ["a.md"]    # its next query
    assert len(raw.execute(_REVERT_CHECK).fetchall()) == 3 and live._counted()
    assert recount(live)[0] == {(AUTHORED, 2, 3), (OBSERVED, 1, 1)}         # b.md counted too
    with pytest.raises(sqlite3.IntegrityError, match="keeps statistics"):
        old_land(raw, TOKENIZER, "c.md", "v1", OBSERVED, "C", _chunks("gamma"))
    raw.close()
