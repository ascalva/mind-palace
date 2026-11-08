"""Shared rises (dn-corpus-instance §2.2, §6): how much the communities of one source rise
together, against how much communities of different sources do, and the effective number of
independent signals that leaves (CI-2).

A community's signal is its weekly activity: new items and new edges (its items' relations, on
the day each appears) per week, over a common window. Each series is detrended (the first
difference of its log), so a shared long-run growth of every source is not read as a shared rise.
The correlation of two communities is the largest absolute Pearson correlation of their detrended
series at a lag from 0 to 8 weeks (either direction). `rho_w` is its mean over pairs of
communities of one source, `rho_b` over pairs of communities of different sources, with a 95%
bootstrap band from resampling communities; and by CI-2, with D sources of m communities each,

    N_eff = D m / (1 + (m - 1) rho_w + m (D - 1) rho_b),     N_eff -> D / (rho_w + (D - 1) rho_b).

The partition (CI-b): OpenAlex's primary topic, arXiv's primary category, a Stack Exchange
question's first tag (an answer joins its question's), Gutenberg's Library of Congress subclass,
a Hacker News thread's link host, and for Wikipedia, which has none, Louvain communities of its
hyperlink graph. A community enters
with at least `min_items` items; each source contributes at most `per_source` of its largest.
CIF-2's second half is broken when `rho_b` lies inside the bootstrap band of `rho_w`. The null
is the same statistic with every series shifted circularly by its own random offset (each series
and its autocorrelation kept, their alignment removed): the level the largest lagged correlation
reaches by chance.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np
import numpy.typing as npt

from eval.corpus.data import Corpus, day
from eval.corpus.edges import Relation

WEEK = 7


def louvain(n: int, rel: Relation, nodes: list[int], seed: int = 0) -> dict[int, int]:
    """Louvain communities of a relation over `nodes` (gids), by scikit-network."""
    import scipy.sparse as sp

    from core.typedshims.sknetwork import louvain_labels

    index = {g: i for i, g in enumerate(nodes)}
    pairs = [(index[a], index[b]) for a, b in zip(rel.src.tolist(), rel.dst.tolist(), strict=True)
             if a in index and b in index]
    if not pairs:
        return {}
    r, c = np.asarray(pairs).T
    adj = sp.csr_matrix((np.ones(len(r)), (r, c)), shape=(len(nodes), len(nodes)))
    adj = ((adj + adj.T) > 0).astype(np.float64)
    labels = louvain_labels(adj.tocsr(), random_state=seed)
    return {nodes[i]: int(lab) for i, lab in enumerate(labels)}


def partition(c: Corpus, rel: dict[str, Relation]) -> dict[int, str]:
    """Each item's community, `<source>:<label>`."""
    out: dict[int, str] = {}
    questions: dict[str, str] = {}
    for g, k in enumerate(c.source_of):
        s, m = c.sources[k], c.meta[g]
        if s == "openalex":
            out[g] = f"openalex:{m.get('topic') or '?'}"
        elif s == "arxiv":
            cats = m.get("categories") or ["?"]
            out[g] = f"arxiv:{cats[0]}"
        elif s == "gutenberg":
            locc = str(m.get("locc") or "?").split(";")[0].strip()
            out[g] = f"gutenberg:{locc[:2]}"
        elif s == "hackernews":
            out[g] = f"hackernews:{m.get('host') or 'text'}"
        elif s == "stackexchange" and m.get("kind") == "question":
            tags = m.get("tags") or ["?"]
            label = f"stackexchange:{m.get('site')}:{tags[0]}"
            out[g] = label
            questions[str(m["id"])] = label
    for g, k in enumerate(c.source_of):
        if c.sources[k] == "stackexchange" and c.meta[g].get("kind") == "answer":
            out[g] = questions.get(str(c.meta[g].get("parent") or ""), "stackexchange:?")
    wiki = [g for g, k in enumerate(c.source_of) if c.sources[k] == "wikipedia"]
    labels = louvain(c.n, rel["wikipedia.hyperlink"], wiki) if "wikipedia.hyperlink" in rel else {}
    for g in wiki:
        out[g] = f"wikipedia:{labels.get(g, -1)}"
    return out


def series(c: Corpus, rel: dict[str, Relation], part: dict[int, str], start: str, end: str
           ) -> tuple[list[str], npt.NDArray[np.float64]]:
    """Weekly new items plus new edges, per community, from `start` to `end`."""
    d0, d1 = day(start), day(end)
    weeks = (d1 - d0) // WEEK + 1
    comms = sorted(set(part.values()))
    idx = {x: i for i, x in enumerate(comms)}
    m = np.zeros((len(comms), weeks))
    for g, dd in enumerate(c.dates):
        if d0 <= dd <= d1 and g in part:
            m[idx[part[g]], (dd - d0) // WEEK] += 1
    for name, r in rel.items():
        if name.endswith(".version"):
            continue                       # a version's nodes are not items
        for a, t in zip(r.src.tolist(), r.t.tolist(), strict=True):
            if d0 <= t <= d1 and a in part:
                m[idx[part[a]], (t - d0) // WEEK] += 1
    return comms, m


def detrend(m: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return np.diff(np.log1p(m), axis=1)


def lagged_corr(x: npt.NDArray[np.float64], max_lag: int = 8) -> npt.NDArray[np.float64]:
    """For rows of `x`, the largest absolute Pearson correlation of each pair over lags 0 to
    `max_lag` either way (the pair's own row and column symmetric, the diagonal NaN)."""
    n, t = x.shape
    best = np.zeros((n, n))
    for lag in range(0, max_lag + 1):
        a = x[:, lag:]
        b = x[:, :t - lag] if lag else x
        az = (a - a.mean(axis=1, keepdims=True))
        bz = (b - b.mean(axis=1, keepdims=True))
        an = np.linalg.norm(az, axis=1)
        bn = np.linalg.norm(bz, axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            r = (az @ bz.T) / np.outer(an, bn)
        r = np.nan_to_num(r)
        best = np.maximum(best, np.abs(r))
        best = np.maximum(best, np.abs(r.T))
    np.fill_diagonal(best, np.nan)
    return best


def rho(r: npt.NDArray[np.float64], src: npt.NDArray[np.int64]) -> tuple[float, float]:
    """The mean correlation within sources and across them."""
    same = src[:, None] == src[None, :]
    off = ~np.eye(len(src), dtype=bool)
    w = r[same & off]
    b = r[~same]
    return (float(np.nanmean(w)) if w.size else math.nan,
            float(np.nanmean(b)) if b.size else math.nan)


def n_eff(rho_w: float, rho_b: float, d: int, m: float) -> tuple[float, float]:
    """CI-2's effective count at m communities a source, and its limit as m grows."""
    finite = d * m / (1 + (m - 1) * rho_w + m * (d - 1) * rho_b)
    limit = d / (rho_w + (d - 1) * rho_b) if rho_w + (d - 1) * rho_b > 0 else math.inf
    return finite, limit


def measure(c: Corpus, rel: dict[str, Relation], *, start: str = "2012-01-01",
            end: str = "2024-12-31", min_items: int = 150, per_source: int = 20,
            max_lag: int = 8, boot: int = 400, seed: int = 0) -> dict[str, Any]:
    part = partition(c, rel)
    comms, m = series(c, rel, part, start, end)
    size: defaultdict[str, int] = defaultdict(int)
    for g in part:
        size[part[g]] += 1
    keep: list[int] = []
    for s in c.sources:
        mine = sorted((i for i, x in enumerate(comms) if x.startswith(f"{s}:")
                       and size[x] >= min_items and m[i].sum() > 0),
                      key=lambda i: -size[comms[i]])[:per_source]
        keep.extend(mine)
    names = [comms[i] for i in keep]
    src = np.asarray([c.sources.index(x.split(":", 1)[0]) for x in names], dtype=np.int64)
    x = detrend(m[keep])
    r = lagged_corr(x, max_lag)
    r0 = lagged_corr(x, 0)
    rho_w, rho_b = rho(r, src)
    rho_w0, rho_b0 = rho(r0, src)
    rng = np.random.default_rng(seed)
    bw, bb = [], []
    for _ in range(boot):
        pick = np.concatenate([rng.choice(np.flatnonzero(src == k), size=int((src == k).sum()))
                               for k in np.unique(src)])
        rr = r[np.ix_(pick, pick)].copy()
        same_item = pick[:, None] == pick[None, :]
        rr[same_item] = np.nan                 # a community drawn twice is not its own pair
        w, b = rho(rr, src[pick])
        bw.append(w)
        bb.append(b)
    # the null: each community's detrended series shifted circularly by its own random offset,
    # which keeps every series and its autocorrelation and removes any alignment between them
    nw, nb = [], []
    for _ in range(max(20, boot // 20)):
        shifted = np.stack([np.roll(row, int(rng.integers(0, x.shape[1]))) for row in x])
        rn = lagged_corr(shifted, max_lag)
        w, b = rho(rn, src)
        nw.append(w)
        nb.append(b)
    d = len(np.unique(src))
    mean_m = len(keep) / max(1, d)
    finite, limit = n_eff(rho_w, rho_b, d, mean_m)
    band_w = [float(np.nanpercentile(bw, 2.5)), float(np.nanpercentile(bw, 97.5))]
    band_b = [float(np.nanpercentile(bb, 2.5)), float(np.nanpercentile(bb, 97.5))]
    by_source: dict[str, dict[str, float]] = {}
    for k in np.unique(src):
        sel = src == k
        sub = r[np.ix_(sel, sel)]
        by_source[c.sources[int(k)]] = {"communities": int(sel.sum()),
                                        "rho_w": float(np.nanmean(sub)) if sel.sum() > 1
                                        else math.nan}
    return {"window": [start, end], "weeks": int(m.shape[1]), "max_lag": max_lag,
            "communities": len(keep), "sources": d, "min_items": min_items,
            "per_source_cap": per_source, "rho_w": rho_w, "rho_b": rho_b,
            "rho_w_band": band_w, "rho_b_band": band_b,
            "rho_w_lag0": rho_w0, "rho_b_lag0": rho_b0,
            "rho_null_w": float(np.nanmean(nw)), "rho_null_b": float(np.nanmean(nb)),
            "rho_null_band": [float(np.nanpercentile(nw + nb, 2.5)),
                              float(np.nanpercentile(nw + nb, 97.5))],
            "n_eff": finite, "n_eff_limit": limit, "m_per_source": mean_m,
            "by_source": by_source,
            "cif2_rises_broken": bool(band_w[0] <= rho_b <= band_w[1]),
            "names": names}
