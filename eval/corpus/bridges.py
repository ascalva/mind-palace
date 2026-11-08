"""Cross-source bridges against a degree-preserving null (dn-corpus-instance §6, CIF-2).

The graph is the corpus's at the item grain: every explicit relation within a source (hyperlinks,
citations, answers, post links; a version joins an item to itself), every explicit bridge between
sources (citations by DOI and arXiv id, links, Gutenberg templates, the OpenAlex and arXiv twins),
and the semantic edges, each item to its `k` nearest items above σ by the cosine of their mean
chunk vectors. Communities are the rises' partition (`eval/corpus/rises.py`): every community lies
inside one source.

Two readings, each against the same null, the configuration model: the graph's edges rewired by
matching their endpoints' stubs uniformly at random, which keeps every item's degree and nothing
else (`reps` draws; loops dropped, a repeated pair kept once):

- the **share** of edges whose ends lie in different sources, observed and in the null; for
  sources that are domains it is below the null's, which mixes them freely, and that is expected,
  not a falsifier;
- the **bridges**: pairs of communities of different sources joined by more edges than the null
  gives them (above its mean by `z` of its standard deviations, and at least `min_edges`), counted
  against the same count made on a null draw scored against the other draws (the false
  positives). CIF-2's first half is broken when the observed bridges are no more than the false
  positives' mean and two standard deviations: then no pair of communities across sources is
  joined more than chance joins it.

A sample of chunks (`chunk_sample` of them against every chunk) gives the chunk-grain rate of
pairs across sources above σ, by pair of sources.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np
import numpy.typing as npt

from eval.corpus.data import Corpus, Vectors
from eval.corpus.edges import Relation

IntArr = npt.NDArray[np.int64]


def knn(x: npt.NDArray[np.float32], have: npt.NDArray[np.bool_], *, k: int, sigma: float,
        block: int = 1024) -> tuple[IntArr, IntArr, npt.NDArray[np.float32]]:
    """Each item's `k` nearest items with cosine at least `sigma` (rows of unit vectors; items
    without a vector neither ask nor answer): (i, j, cosine) with i < j, each pair once."""
    idx = np.flatnonzero(have)
    xs = x[idx]
    rows: list[IntArr] = []
    cols: list[IntArr] = []
    sims: list[npt.NDArray[np.float32]] = []
    for s in range(0, len(idx), block):
        q = xs[s:s + block]
        sim = q @ xs.T
        for r in range(len(q)):
            sim[r, s + r] = -1.0                   # not its own neighbour
        top = np.argpartition(-sim, kth=min(k, sim.shape[1] - 1), axis=1)[:, :k]
        vals = np.take_along_axis(sim, top, axis=1)
        ok = vals >= sigma
        rr = np.repeat(np.arange(s, s + len(q)), k).reshape(len(q), k)[ok]
        rows.append(idx[rr])
        cols.append(idx[top[ok]])
        sims.append(vals[ok].astype(np.float32))
    i = np.concatenate(rows) if rows else np.zeros(0, np.int64)
    j = np.concatenate(cols) if cols else np.zeros(0, np.int64)
    v = np.concatenate(sims) if sims else np.zeros(0, np.float32)
    a, b = np.minimum(i, j), np.maximum(i, j)
    key, first = np.unique(a * (int(max(len(x), 1))) + b, return_index=True)
    del key
    return a[first], b[first], v[first]


def union(c: Corpus, rel: dict[str, Relation], semantic: tuple[IntArr, IntArr] | None
          ) -> tuple[IntArr, IntArr, npt.NDArray[np.bool_]]:
    """The undirected item graph: (u, v) with u < v, once each, and which edges are semantic."""
    us, vs, sem = [], [], []
    for name, r in rel.items():
        if name.endswith(".version") or r.m == 0:
            continue
        us.append(r.src)
        vs.append(r.dst)
        sem.append(np.zeros(r.m, dtype=bool))
    if semantic is not None and len(semantic[0]):
        us.append(semantic[0])
        vs.append(semantic[1])
        sem.append(np.ones(len(semantic[0]), dtype=bool))
    u = np.concatenate(us)
    v = np.concatenate(vs)
    s = np.concatenate(sem)
    keep = u != v
    u, v, s = u[keep], v[keep], s[keep]
    a, b = np.minimum(u, v), np.maximum(u, v)
    key, first = np.unique(a * c.n + b, return_index=True)
    del key
    return a[first], b[first], s[first]


def configuration(u: IntArr, v: IntArr, rng: np.random.Generator) -> tuple[IntArr, IntArr]:
    """One draw of the configuration model on the graph's degree sequence (stubs matched at
    random; loops dropped, repeated pairs kept once)."""
    stubs = np.concatenate([u, v])
    rng.shuffle(stubs)
    half = len(stubs) // 2
    a, b = stubs[:half], stubs[half:2 * half]
    keep = a != b
    a, b = np.minimum(a[keep], b[keep]), np.maximum(a[keep], b[keep])
    n = int(max(stubs.max(), 0)) + 1
    key = np.unique(a * n + b)
    return key // n, key % n


def _pair_counts(u: IntArr, v: IntArr, comm: IntArr, ncomm: int, src_of_comm: IntArr
                 ) -> dict[int, int]:
    """Edges between each pair of communities of different sources, keyed `ca * ncomm + cb`."""
    ca, cb = comm[u], comm[v]
    ok = (ca >= 0) & (cb >= 0)
    ca, cb = ca[ok], cb[ok]
    lo, hi = np.minimum(ca, cb), np.maximum(ca, cb)
    cross = src_of_comm[lo] != src_of_comm[hi]
    keys, counts = np.unique(lo[cross] * ncomm + hi[cross], return_counts=True)
    return dict(zip(keys.tolist(), counts.tolist(), strict=True))


def measure(c: Corpus, rel: dict[str, Relation], part: dict[int, str], *,
            semantic: tuple[IntArr, IntArr] | None = None, reps: int = 20, z: float = 3.0,
            min_edges: int = 3, seed: int = 0) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    u, v, sem = union(c, rel, semantic)
    src = np.asarray(c.source_of, dtype=np.int64)
    names = sorted(set(part.values()))
    cid = {x: i for i, x in enumerate(names)}
    comm = np.full(c.n, -1, dtype=np.int64)
    for g, x in part.items():
        comm[g] = cid[x]
    src_of_comm = np.asarray([c.sources.index(x.split(":", 1)[0]) for x in names],
                             dtype=np.int64)
    cross = src[u] != src[v]
    obs = _pair_counts(u, v, comm, len(names), src_of_comm)
    null_shares, draws = [], []
    for _ in range(reps):
        a, b = configuration(u, v, rng)
        null_shares.append(float(np.mean(src[a] != src[b])))
        draws.append(_pair_counts(a, b, comm, len(names), src_of_comm))
    keys = set(obs).union(*draws)
    mean = {k: float(np.mean([d.get(k, 0) for d in draws])) for k in keys}
    sd = {k: float(np.std([d.get(k, 0) for d in draws])) for k in keys}

    def bridges(counts: dict[int, int], ref: list[dict[int, int]]) -> list[int]:
        mu = {k: float(np.mean([d.get(k, 0) for d in ref])) for k in counts}
        sg = {k: float(np.std([d.get(k, 0) for d in ref])) for k in counts}
        return [k for k, e in counts.items()
                if e >= min_edges and e > mu[k] + z * max(sg[k], math.sqrt(max(mu[k], 1.0)))]
    observed = bridges(obs, draws)
    false_pos = [len(bridges(draws[i], draws[:i] + draws[i + 1:])) for i in range(min(reps, 10))]
    by_pair: dict[str, dict[str, float]] = defaultdict(lambda: {"edges": 0, "bridges": 0})
    for k in observed:
        ka, kb = divmod(k, len(names))
        sa, sb = sorted((c.sources[src_of_comm[ka]], c.sources[src_of_comm[kb]]))
        by_pair[f"{sa}-{sb}"]["bridges"] += 1
    for k, e in obs.items():
        ka, kb = divmod(k, len(names))
        sa, sb = sorted((c.sources[src_of_comm[ka]], c.sources[src_of_comm[kb]]))
        by_pair[f"{sa}-{sb}"]["edges"] += e
    top = sorted(observed, key=lambda k: -(obs[k] - mean.get(k, 0.0)))[:15]
    return {"items": c.n, "edges": int(len(u)), "semantic_edges": int(sem.sum()),
            "cross_edges": int(cross.sum()), "cross_share": float(cross.mean()),
            "cross_explicit": int((cross & ~sem).sum()), "cross_semantic": int((cross & sem).sum()),
            "null_cross_share": float(np.mean(null_shares)),
            "null_cross_share_sd": float(np.std(null_shares)),
            "communities": len(names), "reps": reps, "z": z, "min_edges": min_edges,
            "bridges": len(observed), "false_positive_bridges": false_pos,
            "false_positive_mean": float(np.mean(false_pos)) if false_pos else math.nan,
            "false_positive_bar": (float(np.mean(false_pos) + 2 * np.std(false_pos))
                                   if false_pos else 0.0),
            "cif2_bridges_broken": bool(len(observed) <= (np.mean(false_pos)
                                                          + 2 * np.std(false_pos)
                                                          if false_pos else 0.0)),
            "by_source_pair": dict(by_pair),
            "top": [{"a": names[divmod(k, len(names))[0]], "b": names[divmod(k, len(names))[1]],
                     "edges": obs[k], "null_mean": round(mean.get(k, 0.0), 2),
                     "null_sd": round(sd.get(k, 0.0), 2)} for k in top]}


def chunk_pairs(c: Corpus, vec: Vectors, *, sigma: float, sample: int = 20000,
                block: int = 512, seed: int = 0) -> dict[str, Any]:
    """Of `sample` random chunks, the pairs with every other chunk at cosine at least `sigma`,
    counted by the pair of sources of their items (a pair within one item left out)."""
    rng = np.random.default_rng(seed)
    n = vec.matrix.shape[0]
    pick = rng.choice(n, size=min(sample, n), replace=False)
    first_src = np.asarray([c.source_of[h[0]] if h else -1 for h in vec.holders])
    first_item = np.asarray([h[0] if h else -1 for h in vec.holders])
    k = len(c.sources)
    counts = np.zeros((k, k), dtype=np.int64)
    asked = np.zeros(k, dtype=np.int64)
    for s in range(0, len(pick), block):
        q = pick[s:s + block]
        sim = vec.matrix[q].astype(np.float32) @ vec.matrix.astype(np.float32).T \
            if n <= 200000 else _blocked(vec.matrix, q)
        for r, qi in enumerate(q):
            hits = np.flatnonzero(sim[r] >= sigma)
            hits = hits[first_item[hits] != first_item[qi]]
            a = first_src[qi]
            asked[a] += 1
            np.add.at(counts[a], first_src[hits], 1)
    out = {}
    for a in range(k):
        for b in range(k):
            if asked[a]:
                out[f"{c.sources[a]}->{c.sources[b]}"] = round(counts[a, b] / asked[a], 4)
    return {"sample": int(len(pick)), "sigma": sigma, "pairs_per_chunk": out,
            "asked": {c.sources[a]: int(asked[a]) for a in range(k)}}


def _blocked(m: npt.NDArray[np.float16], q: IntArr, step: int = 200000) -> npt.NDArray[np.float32]:
    qv = m[q].astype(np.float32)
    parts = [qv @ m[s:s + step].astype(np.float32).T for s in range(0, m.shape[0], step)]
    return np.concatenate(parts, axis=1)
