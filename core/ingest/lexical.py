"""A lexical index of landed chunks: tokens to BM25 weights, no model (dn-corpus-instance, the
structural phase of stage 1).

The units are the chunks the landing derived (the same chunker, `derive_chunks`, over the same
raw bytes), so a lexical ranking and a vector ranking rank the same things. A unit's text is
lower-cased and cut into tokens (runs of letters and digits); the index holds, for each unit and
term, the BM25 weight

    w(t, d) = idf(t) * tf(t, d) * (k1 + 1) / (tf(t, d) + k1 * (1 - b + b * |d| / avgdl)),
    idf(t) = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5)),

with k1 = 1.2 and b = 0.75 (Robertson and Zaragoza's defaults), as one sparse matrix, units by
terms; a query's score for a unit is the sum of the weights of the query's distinct terms. It is
a derived index, rebuilt from the raw store whenever it is lost, as the vectors are.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt
import scipy.sparse as sp

TOKEN = re.compile(r"[0-9a-z]+")
K1, B = 1.2, 0.75


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


@dataclass
class LexicalIndex:
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
        idf = np.log1p((n - df + 0.5) / (df + 0.5)).astype(np.float32)
        norm = k1 * (1.0 - b + b * dl[r] / max(avgdl, 1e-9))
        w = idf[c] * tf * (k1 + 1.0) / (tf + norm)
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


def rrf(rankings: list[npt.NDArray[np.int64]], k: int = 10, c: float = 60.0
        ) -> npt.NDArray[np.int64]:
    """Reciprocal rank fusion of rankings of one set of units (Cormack, Clarke and Buettcher
    2009): a unit's score is the sum over rankings of 1 / (c + its rank); the top k, best first,
    ties by unit."""
    score: dict[int, float] = {}
    for ranking in rankings:
        for rank, u in enumerate(ranking.tolist()):
            score[u] = score.get(u, 0.0) + 1.0 / (c + rank + 1)
    top = sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
    return np.asarray([u for u, _ in top], dtype=np.int64)


def _idf_check(n: int, df: int) -> float:
    """The idf of a term in `df` of `n` units (the formula above, for tests)."""
    return math.log1p((n - df + 0.5) / (df + 0.5))
