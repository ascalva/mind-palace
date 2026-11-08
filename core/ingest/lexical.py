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
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from collections.abc import Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt
import scipy.sparse as sp

# A token is a maximal run of letters or digits, in any script, lower-cased; underscores split.
TOKEN = re.compile(r"[^\W_]+")
K1: float = 1.2
B: float = 0.75
RRF_C: float = 60.0


def tokens(text: str) -> list[str]:
    """The tokens of a text, in order."""
    return TOKEN.findall(text.lower())


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
    """The BM25 weights of a fixed set of units, in memory: one sparse matrix, units by terms."""

    vocab: dict[str, int]
    weights: sp.csc_matrix          # units x terms, BM25 weights (float32)

    @property
    def units(self) -> int:
        return int(self.weights.shape[0])

    @staticmethod
    def build(texts: Iterable[str], *, k1: float = K1, b: float = B,
              batch: int = 100000) -> LexicalIndex:
        """The index of `texts`, one unit each, in order."""
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
            toks = tokens(text)
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
        return LexicalIndex(vocab, m)

    def scores(self, query: str) -> npt.NDArray[np.float32]:
        """Every unit's score for a query (zeros where no term matches)."""
        ids = sorted({self.vocab[t] for t in tokens(query) if t in self.vocab})
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
        """Write the index under `d`; returns its bytes."""
        d.mkdir(parents=True, exist_ok=True)
        sp.save_npz(d / "weights.npz", self.weights, compressed=False)
        (d / "vocab.json").write_text(json.dumps(self.vocab))
        return sum(f.stat().st_size for f in d.iterdir() if f.is_file())

    @staticmethod
    def load(d: Path) -> LexicalIndex:
        m = sp.csc_matrix(sp.load_npz(d / "weights.npz"))
        return LexicalIndex(json.loads((d / "vocab.json").read_text()), m)


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
