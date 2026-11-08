"""The lexical representation of landed text: tokens and BM25 weights, with no model
(dn-two-phase-ingestion D1, D2).

A tokenizer alone gives an item a representation a query can be ranked against: the tokens of its
chunks, each weighted by how rare it is across the units an index holds. This module is the
arithmetic, pure over its arguments, so the store that keeps the postings
(`core/stores/lexical.py`) and a test call one function: the tokens of a text, the term counts of
a unit, the inverse document frequency of a term among `n` units, and the BM25 weight of a term
in a unit of length `dl` against the mean length `avgdl`,

    w(t, d) = idf(t) · tf · (k1 + 1) / (tf + k1 · (1 − b + b · dl / avgdl)),
    idf(t)  = ln(1 + (n − df(t) + 0.5) / (df(t) + 0.5)),

with `k1 = 1.2` and `b = 0.75` (Robertson and Zaragoza 2009). A query's score for a unit is the
sum over the query's distinct terms. The representation is a function of the bytes alone, so it
is derived, rebuilt from the raw store as the vectors are, and it is complete the moment the item
lands: the structural phase of a two-phase landing answers a lexical `near` before any vector
exists (ING-19, ING-21). `fuse` combines a lexical and a semantic ranking by reciprocal rank
(Cormack, Clarke and Buettcher 2009), the "both" arm of the attribution battery.

`LexicalIndex` is the same weights held in memory as one sparse matrix, units by terms, for a
measurement over a whole corpus at once (the corpus instance's battery, `eval/corpus/`), where a
query scores millions of units and the store's SQL would be read term by term; `rrf` is `fuse`
over arrays of unit numbers, ties broken by unit. Both tokenize with `tokens`, so the store, the
matrix and a test agree on what a term is.

A term is a `Tokenizer`'s output, and a tokenizer has an identity: the Unicode normal form it
puts text in, its case fold, whether combining marks continue a token, and the version of the
Unicode database its character classes come from. One text in two normal forms (a precomposed
"é" and an "e" followed by a combining acute) is one text to a reader, and must give one set of
terms; without normalization the second form even splits the word at its mark. Units tokenized
under one identity cannot be scored against a query tokenized under another, so every store of
units records the identity it was built with and refuses another (`core/stores/lexical.py`), as
the plane records its embedder. `LEGACY` is the tokenizer every index was built with before the
identity was recorded; `TOKENIZER` is the current one. Only terms are normalized: content
hashes, the raw store and the chunks stay on the bytes as they came.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from collections.abc import Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Literal

import numpy as np
import numpy.typing as npt
import scipy.sparse as sp

K1: float = 1.2
B: float = 0.75
RRF_C: float = 60.0

Form = Literal["NFC", "NFKC"]
Fold = Literal["lower", "casefold"]
FORMS: tuple[Form | None, ...] = (None, "NFC", "NFKC")
FOLDS: tuple[Fold, ...] = ("lower", "casefold")
# The planes that hold every combining mark of the Unicode database (the BMP, the SMP and plane
# 14's variation selectors); a test checks the claim against a scan of every code point.
_MARK_PLANES = ((0, 0x30000), (0xE0000, 0xE1000))


class TokenizerMismatch(RuntimeError):
    """Units tokenized under one identity met a tokenizer of another. A query's terms and the
    units' terms would disagree on what a word is, which no score can detect, so the store
    refuses until its units are re-derived."""


@cache
def _mark_ranges(lo: int, hi: int) -> str:
    """The combining marks (general category M) in `[lo, hi)`, as regular-expression ranges."""
    ranges: list[list[int]] = []
    for cp in range(lo, hi):
        if unicodedata.category(chr(cp))[0] == "M":
            if ranges and ranges[-1][1] == cp - 1:
                ranges[-1][1] = cp
            else:
                ranges.append([cp, cp])
    return "".join(re.escape(chr(a)) if a == b else f"{re.escape(chr(a))}-{re.escape(chr(b))}"
                   for a, b in ranges)


def _marks_class() -> str:
    """Every combining mark, as the ranges of one class."""
    return "".join(_mark_ranges(lo, hi) for lo, hi in _MARK_PLANES)


@cache
def _pattern(marks: bool) -> re.Pattern[str]:
    """A token: a letter or digit, then letters and digits (and combining marks when `marks`);
    underscores and everything else split. With marks the pattern is a run of letters and digits
    followed by any number of (marks, then letters and digits), which matches what the plain rule
    matches; the marks are two classes, the BMP's and the rest behind a guard, because the regular
    expression engine reads a class that holds characters beyond the BMP range by range and a BMP
    class by table (measured: 1.4 times the unmarked pattern's time, against 3.3 for one class)."""
    if not marks:
        return re.compile(r"[^\W_]+")
    bmp = _mark_ranges(0, 0x10000)
    astral = "".join(_mark_ranges(max(lo, 0x10000), hi) for lo, hi in _MARK_PLANES
                     if hi > 0x10000)
    mark = rf"(?:[{bmp}]|(?=[\U00010000-\U0010FFFF])[{astral}])"
    return re.compile(rf"[^\W_]+(?:{mark}+[^\W_]*)*")


@dataclass(frozen=True)
class Tokenizer:
    """How text becomes terms: put in the normal form `form` (None: as it came), fold case, then
    take maximal runs of letters and digits, with combining marks inside a run when `marks`. Text
    is normalized again after the fold, which can leave it unnormalized, so the terms of a text
    and of any canonically equivalent text are the same (and of any compatibility-equivalent text
    under NFKC)."""

    form: Form | None = "NFKC"
    fold: Fold = "casefold"
    marks: bool = True

    def __post_init__(self) -> None:
        if self.form not in FORMS or self.fold not in FOLDS:
            raise ValueError(f"no tokenizer with form {self.form!r} and fold {self.fold!r}")

    @property
    def identity(self) -> str:
        """What a store records: every parameter the terms depend on, the Unicode database's
        version among them (its character classes and case folds change between versions)."""
        return (f"runs/{self.form or 'raw'}/{self.fold}/{'marks' if self.marks else 'nomarks'}"
                f"/unicode-{unicodedata.unidata_version}")

    @staticmethod
    def from_identity(identity: str) -> Tokenizer:
        """The tokenizer an identity names, if this process can reproduce it; a different Unicode
        database cannot, and is refused."""
        try:
            kind, form, fold, marks, version = identity.split("/")
        except ValueError:
            raise TokenizerMismatch(f"no tokenizer has the identity {identity!r}") from None
        if kind != "runs" or marks not in ("marks", "nomarks") \
                or version != f"unicode-{unicodedata.unidata_version}":
            raise TokenizerMismatch(f"this process cannot reproduce the tokenizer {identity!r} "
                                    f"(Unicode {unicodedata.unidata_version})")
        forms = {f or "raw": f for f in FORMS}
        if form not in forms or fold not in FOLDS:
            raise TokenizerMismatch(f"no tokenizer has the identity {identity!r}")
        return Tokenizer(forms[form], "casefold" if fold == "casefold" else "lower",
                         marks == "marks")

    def __call__(self, text: str) -> list[str]:
        if self.form is not None:
            text = unicodedata.normalize(self.form, text)
        text = text.casefold() if self.fold == "casefold" else text.lower()
        if self.form is not None:
            text = unicodedata.normalize(self.form, text)
        return _pattern(self.marks).findall(text)


# Every index built before tokenizers had an identity: maximal runs of letters and digits of the
# lower-cased text, no normalization, marks splitting.
LEGACY = Tokenizer(form=None, fold="lower", marks=False)
# The current tokenizer: NFKC, case folded, marks inside a token. The most normalizing of the arms
# docs/experiments/embedder-use-2026-11-08.md measured, chosen by its pre-declared rule (no loss
# against LEGACY on any primary set; the retrieval figures are equal to four places).
TOKENIZER = Tokenizer(form="NFKC", fold="casefold", marks=True)


def tokens(text: str) -> list[str]:
    """The tokens of a text, in order, by the current tokenizer."""
    return TOKENIZER(text)


def term_counts(text: str) -> Counter[str]:
    """Each distinct term of a text with its count: one unit's postings."""
    return Counter(tokens(text))


def idf(n: int, df: int) -> float:
    """The inverse document frequency of a term in `df` of `n` units."""
    return math.log1p((n - df + 0.5) / (df + 0.5))


def tf_weight(tf: int, dl: int, avgdl: float, *, k1: float = K1, b: float = B) -> float:
    """The saturated, length-normalized term frequency of BM25."""
    norm = k1 * (1.0 - b + b * dl / avgdl) if avgdl > 0 else k1
    return tf * (k1 + 1.0) / (tf + norm)


def bm25(query: str, units: Sequence[Mapping[str, int]], *, k1: float = K1,
         b: float = B) -> list[float]:
    """Every unit's score for a query, over units given as term counts: the reference the
    store's SQL-backed scoring is tested against. A unit that shares no term scores 0."""
    terms = sorted(set(tokens(query)))
    n = len(units)
    if n == 0 or not terms:
        return [0.0] * n
    lengths = [sum(u.values()) for u in units]
    avgdl = sum(lengths) / n
    out = [0.0] * n
    for t in terms:
        df = sum(1 for u in units if t in u)
        if df == 0:
            continue
        w = idf(n, df)
        for i, u in enumerate(units):
            tf = u.get(t, 0)
            if tf:
                out[i] += w * tf_weight(tf, lengths[i], avgdl, k1=k1, b=b)
    return out


def fuse[K: Hashable](rankings: Sequence[Sequence[K]], *, k: int, c: float = RRF_C) -> list[K]:
    """Reciprocal rank fusion of rankings of one set of items: an item's score is the sum over
    the rankings of `1 / (c + rank)`, ranks from 1; the top `k`, best first, ties by first
    appearance."""
    score: dict[K, float] = {}
    first: dict[K, int] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            score[item] = score.get(item, 0.0) + 1.0 / (c + rank)
            first.setdefault(item, len(first))
    return sorted(score, key=lambda item: (-score[item], first[item]))[:k]


@dataclass
class LexicalIndex:
    """The BM25 weights of a fixed set of units, in memory: one sparse matrix, units by terms, and
    the tokenizer that made its terms, which tokenizes its queries too."""

    vocab: dict[str, int]
    weights: sp.csc_matrix          # units x terms, BM25 weights (float32)
    tokenizer: Tokenizer = LEGACY   # an index made before identities were recorded is LEGACY's

    @property
    def units(self) -> int:
        return int(self.weights.shape[0])

    @staticmethod
    def build(texts: Iterable[str], *, k1: float = K1, b: float = B, batch: int = 100000,
              tokenizer: Tokenizer | None = None) -> LexicalIndex:
        """The index of `texts`, one unit each, in order, by `tokenizer` (the current one when
        None)."""
        tokenize = tokenizer if tokenizer is not None else TOKENIZER
        vocab: dict[str, int] = {}
        rows: list[npt.NDArray[np.int32]] = []
        cols: list[npt.NDArray[np.int32]] = []
        tfs: list[npt.NDArray[np.float32]] = []
        lengths: list[int] = []
        r_buf: list[int] = []
        c_buf: list[int] = []
        t_buf: list[int] = []
        unit = 0
        for text in texts:
            toks = tokenize(text)
            lengths.append(len(toks))
            if toks:
                ids = np.fromiter((vocab.setdefault(t, len(vocab)) for t in toks),
                                  dtype=np.int64, count=len(toks))
                u, cnt = np.unique(ids, return_counts=True)
                r_buf.extend([unit] * len(u))
                c_buf.extend(u.tolist())
                t_buf.extend(cnt.tolist())
            unit += 1
            if len(r_buf) >= batch * 50:
                rows.append(np.asarray(r_buf, np.int32))
                cols.append(np.asarray(c_buf, np.int32))
                tfs.append(np.asarray(t_buf, np.float32))
                r_buf, c_buf, t_buf = [], [], []
        rows.append(np.asarray(r_buf, np.int32))
        cols.append(np.asarray(c_buf, np.int32))
        tfs.append(np.asarray(t_buf, np.float32))
        r = np.concatenate(rows)
        c = np.concatenate(cols)
        tf = np.concatenate(tfs)
        n = unit
        dl = np.asarray(lengths, dtype=np.float32)
        avgdl = float(dl.mean()) if n else 1.0
        df = np.bincount(c, minlength=len(vocab)).astype(np.float64)
        idfs = np.log1p((n - df + 0.5) / (df + 0.5)).astype(np.float32)     # `idf`, every term
        norm = k1 * (1.0 - b + b * dl[r] / max(avgdl, 1e-9))
        w = idfs[c] * tf * (k1 + 1.0) / (tf + norm)
        m = sp.csc_matrix((w.astype(np.float32), (r, c)), shape=(n, len(vocab)))
        return LexicalIndex(vocab, m, tokenize)

    def scores(self, query: str) -> npt.NDArray[np.float32]:
        """Every unit's score for a query (zeros where no term matches)."""
        ids = sorted({self.vocab[t] for t in self.tokenizer(query) if t in self.vocab})
        if not ids:
            return np.zeros(self.units, dtype=np.float32)
        return np.asarray(self.weights[:, ids].sum(axis=1), dtype=np.float32).ravel()

    def search(self, query: str, k: int = 10,
               among: npt.NDArray[np.int64] | None = None) -> npt.NDArray[np.int64]:
        """The top-k units for a query, best first, among the given units if any; a unit that
        matches no term is never returned."""
        s = self.scores(query)
        idx = np.arange(self.units) if among is None else among
        sub = s[idx]
        hit = sub > 0
        idx, sub = idx[hit], sub[hit]
        if len(idx) == 0:
            return np.zeros(0, dtype=np.int64)
        kk = min(k, len(idx))
        part = np.argpartition(-sub, kth=kk - 1)[:kk]
        return idx[part[np.argsort(-sub[part])]]

    def save(self, d: Path) -> int:
        """Write the index under `d`, its tokenizer's identity beside its terms; returns its
        bytes."""
        d.mkdir(parents=True, exist_ok=True)
        sp.save_npz(d / "weights.npz", self.weights, compressed=False)
        (d / "vocab.json").write_text(json.dumps(self.vocab))
        (d / "tokenizer.json").write_text(json.dumps({"identity": self.tokenizer.identity}))
        return sum(f.stat().st_size for f in d.iterdir() if f.is_file())

    @staticmethod
    def load(d: Path) -> LexicalIndex:
        """The index saved under `d`, with the tokenizer it was built by (LEGACY's when it
        records none); `TokenizerMismatch` when this process cannot reproduce that tokenizer."""
        m = sp.csc_matrix(sp.load_npz(d / "weights.npz"))
        f = d / "tokenizer.json"
        tokenizer = (Tokenizer.from_identity(str(json.loads(f.read_text())["identity"]))
                     if f.is_file() else LEGACY)
        return LexicalIndex(json.loads((d / "vocab.json").read_text()), m, tokenizer)


def rrf(rankings: list[npt.NDArray[np.int64]], k: int = 10, c: float = RRF_C
        ) -> npt.NDArray[np.int64]:
    """Reciprocal rank fusion of rankings of one set of units, as `fuse`, over arrays of unit
    numbers: the top k, best first, ties by unit."""
    score: dict[int, float] = {}
    for ranking in rankings:
        for rank, u in enumerate(ranking.tolist(), start=1):
            score[u] = score.get(u, 0.0) + 1.0 / (c + rank)
    top = sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
    return np.asarray([u for u, _ in top], dtype=np.int64)
