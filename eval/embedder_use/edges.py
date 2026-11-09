"""Experiment 6: semantic edges, a global threshold against thresholds the data sets, and two
corrections for hubness, scored by stage 1's bridge reading (docs/experiments/
embedder-use-2026-11-08.md).

Items are the corpus instance's, each the mean of its chunk vectors at unit length (stage 1's
reading). Each item's 50 nearest other items by exact cosine are found once, in blocks; every rule
is a function of those lists:

- G, stage 1's: an item's at most 10 nearest above the global 0.785;
- GQ: one threshold, the median over all items of the cosine to the 10th nearest;
- SQ: one threshold a source, the median over its items of the cosine to the 10th nearest;
- M: mutual nearest neighbours, an edge when each item is among the other's 10 nearest;
- C: CSLS (Conneau et al. 2018), `2 cos(x, y) - r(x) - r(y)` with `r` the mean cosine to the 10
  nearest, an item's at most 10 best among its 50 nearest with a positive score.

The reading is stage 1's bridges (`eval/corpus/bridges.py`): the explicit graph with each rule's
semantic edges, the community pairs across sources joined by more edges than the configuration
null gives them, against the bridges the method finds on null draws scored against the other
draws; overall and per source pair. Item-local relations (versions, a thread's replies) join no two
items and are left out, as stage 1's final run leaves them out; the reading is made with and
without the OpenAlex and arXiv twins, which are one paper in two sources.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

from eval.embedder_use.common import F32, I64

Log = Callable[[str], None]
K = 10
CANDIDATES = 50
SIGMA = 0.785


def knn(x: F32, have: npt.NDArray[np.bool_], k: int = CANDIDATES, block: int = 512
        ) -> tuple[I64, F32]:
    """Each item's `k` nearest other items with a vector (gids, cosines, best first); rows of
    items without a vector are -1 and -inf."""
    idx = np.flatnonzero(have)
    xs = x[idx]
    nn = np.full((len(x), k), -1, dtype=np.int64)
    ss = np.full((len(x), k), -np.inf, dtype=np.float32)
    for s in range(0, len(idx), block):
        sim = xs[s:s + block] @ xs.T
        rows = np.arange(len(sim))
        sim[rows, s + rows] = -np.inf                       # not its own neighbour
        part = np.argpartition(-sim, kth=k - 1, axis=1)[:, :k]
        vals = np.take_along_axis(sim, part, axis=1)
        order = np.argsort(-vals, axis=1, kind="stable")
        nn[idx[s:s + block]] = idx[np.take_along_axis(part, order, axis=1)]
        ss[idx[s:s + block]] = np.take_along_axis(vals, order, axis=1)
    return nn, ss


def _pairs(rows: I64, cols: I64) -> tuple[I64, I64]:
    a, b = np.minimum(rows, cols), np.maximum(rows, cols)
    ok = (a >= 0) & (a != b)
    a, b = a[ok], b[ok]
    n = int(max(b.max(), 0)) + 1 if len(b) else 1
    key = np.unique(a * n + b)
    return key // n, key % n


def rules(nn: I64, ss: F32, source: I64, have: npt.NDArray[np.bool_]) -> dict[str, Any]:
    """Every rule's undirected edges, `(i, j)` with `i < j`, and the thresholds it set."""
    who = np.flatnonzero(have)
    kth = ss[who, K - 1]
    out: dict[str, Any] = {"thresholds": {}}
    rows = np.repeat(np.arange(len(nn)), K).reshape(len(nn), K)
    top, top_s = nn[:, :K], ss[:, :K]

    def thresholded(sig: npt.NDArray[np.float32]) -> tuple[I64, I64]:
        keep = (top_s >= sig[:, None]) & (top >= 0)
        return _pairs(rows[keep], top[keep])

    out["G"] = thresholded(np.full(len(nn), SIGMA, dtype=np.float32))
    out["thresholds"]["G"] = SIGMA
    g = float(np.median(kth))
    out["GQ"] = thresholded(np.full(len(nn), g, dtype=np.float32))
    out["thresholds"]["GQ"] = g
    per = np.full(len(nn), np.inf, dtype=np.float32)
    sq: dict[str, float] = {}
    for s in np.unique(source[who]).tolist():
        mine = who[source[who] == s]
        t = float(np.median(ss[mine, K - 1]))
        per[mine] = t
        sq[str(s)] = t
    out["SQ"] = thresholded(per)
    out["thresholds"]["SQ"] = sq
    # mutual: j among i's 10 nearest and i among j's
    a, b = rows[top >= 0], top[top >= 0]
    fwd = set(zip(a.tolist(), b.tolist(), strict=True))
    mutual = [(i, j) for i, j in fwd if i < j and (j, i) in fwd]
    mi = np.asarray([p[0] for p in mutual], dtype=np.int64)
    mj = np.asarray([p[1] for p in mutual], dtype=np.int64)
    out["M"] = (mi, mj)
    # CSLS over the 50 candidates
    r = np.where(have, np.mean(np.where(np.isfinite(top_s), top_s, 0.0), axis=1), 0.0)
    valid = nn >= 0
    csls = np.where(valid, 2.0 * ss - r[:, None] - r[np.maximum(nn, 0)], -np.inf)
    order = np.argsort(-csls, axis=1, kind="stable")[:, :K]
    best = np.take_along_axis(csls, order, axis=1)
    pick = np.take_along_axis(nn, order, axis=1)
    keep = best > 0
    out["C"] = _pairs(rows[keep], pick[keep])
    return out


def skew(x: npt.NDArray[np.float64]) -> float:
    m, sd = float(x.mean()), float(x.std())
    return float(((x - m) ** 3).mean() / sd ** 3) if sd > 0 else 0.0


def bridge_reading(c: Any, rel: dict[str, Any], part: dict[int, str],
                   semantic: tuple[I64, I64] | None, *, reps: int = 20, z: float = 3.0,
                   min_edges: int = 3, seed: int = 0) -> dict[str, Any]:
    """Stage 1's bridges against the configuration null, with each source pair's own false
    positives (`eval/corpus/bridges.py::measure`, as its final run reads it)."""
    from eval.corpus.bridges import _pair_counts, configuration, union

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
    obs = _pair_counts(u, v, comm, len(names), src_of_comm)
    draws = []
    for _ in range(reps):
        a, b = configuration(u, v, rng)
        draws.append(_pair_counts(a, b, comm, len(names), src_of_comm))

    def bridges(counts: dict[int, int], ref: list[dict[int, int]]) -> list[int]:
        mu = {k: float(np.mean([d.get(k, 0) for d in ref])) for k in counts}
        sg = {k: float(np.std([d.get(k, 0) for d in ref])) for k in counts}
        return [k for k, e in counts.items()
                if e >= min_edges and e > mu[k] + z * max(sg[k], math.sqrt(max(mu[k], 1.0)))]

    def pair_of(k: int) -> str:
        ka, kb = divmod(k, len(names))
        sa, sb = sorted((c.sources[src_of_comm[ka]], c.sources[src_of_comm[kb]]))
        return f"{sa}-{sb}"

    observed = bridges(obs, draws)
    fp_lists = [bridges(draws[i], draws[:i] + draws[i + 1:]) for i in range(min(reps, 10))]
    fp = [len(x) for x in fp_lists]
    by_pair: dict[str, dict[str, float]] = defaultdict(
        lambda: {"edges": 0, "bridges": 0, "fp_mean": 0.0, "fp_bar": 0.0})
    for k in observed:
        by_pair[pair_of(k)]["bridges"] += 1
    for k, e in obs.items():
        by_pair[pair_of(k)]["edges"] += e
    fp_pair: dict[str, list[int]] = defaultdict(lambda: [0] * len(fp_lists))
    for i, ks in enumerate(fp_lists):
        for k in ks:
            fp_pair[pair_of(k)][i] += 1
    for name, counts in fp_pair.items():
        by_pair[name]["fp_mean"] = float(np.mean(counts))
        by_pair[name]["fp_bar"] = float(np.mean(counts) + 2 * np.std(counts))
    bar = float(np.mean(fp) + 2 * np.std(fp)) if fp else 0.0
    cross = src[u] != src[v]
    return {"edges": int(len(u)), "semantic_edges": int(sem.sum()),
            "cross_semantic": int((cross & sem).sum()), "bridges": len(observed),
            "fp_mean": float(np.mean(fp)) if fp else 0.0, "fp_bar": bar,
            "excess_ratio": len(observed) / bar if bar > 0 else math.inf,
            "pairs_above_own_bar": sum(1 for p in by_pair.values()
                                       if p["bridges"] > p["fp_bar"]),
            "pairs_with_edges": sum(1 for p in by_pair.values() if p["edges"] > 0),
            "by_pair": dict(by_pair)}


def title_atoms(instance: Path, c: Any, m: npt.NDArray[np.float16], ids: list[str], log: Log,
                *, per_source: int = 1000, seed: int = 0) -> dict[str, Any]:
    """The chunk-grain neighbours at the global 0.785 of title-only atoms (a chunk that is its
    item's title alone, which the chunker emits when the first paragraph does not fit beside the
    title) against the other atoms of the same items, for a sample of each source's items."""
    import random

    from core.kernel.ingest.pipeline import derive_chunks
    from core.stores.plane import atom_id
    from eval.embedder_use.common import raw_bytes, read_catalog

    row = {a: i for i, a in enumerate(ids)}
    catalog = read_catalog(instance)
    rng = random.Random(seed)
    out: dict[str, Any] = {}
    for s in c.sources:
        paths = [p for p in c.paths if p.split("/")[1] == s and p in catalog]
        kinds: dict[str, list[int]] = {"title": [], "body": []}
        for p in rng.sample(paths, min(per_source, len(paths))):
            title, digest = catalog[p]
            for ch in derive_chunks(raw_bytes(instance, digest)):
                r = row.get(atom_id(ch.text))
                if r is not None:
                    kinds["title" if ch.text.strip() == title.strip() else "body"].append(r)
        out[s] = {}
        for kind, rows in kinds.items():
            if not rows:
                out[s][kind] = {"atoms": 0}
                continue
            pick = np.asarray(rows[:2000], dtype=np.int64)
            q = m[pick].astype(np.float32)
            q /= np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-12)
            above = np.zeros(len(pick), dtype=np.int64)
            for r0 in range(0, m.shape[0], 200000):
                block = m[r0:r0 + 200000].astype(np.float32)
                block /= np.maximum(np.linalg.norm(block, axis=1, keepdims=True), 1e-12)
                above += np.sum(q @ block.T >= SIGMA, axis=1)
            above -= 1                                            # itself
            out[s][kind] = {"atoms": int(len(rows)), "sampled": int(len(pick)),
                            "neighbours_above_sigma_mean": float(above.mean()),
                            "neighbours_above_sigma_median": float(np.median(above))}
        log(f"  title-only atoms, {s}: {out[s]}")
    return out


def run_edges(instance: Path, log: Log, *, reps: int = 20) -> dict[str, Any]:
    from eval.corpus.data import SOURCES, Vectors, load
    from eval.corpus.edges import build, twins
    from eval.corpus.rises import partition
    from eval.embedder_use.corpus import load_vectors

    c = load(instance / "sources", SOURCES)
    rel_all = build(c)
    tw = twins(rel_all)
    # item-local relations join nodes inside one item, numbered on their own: never items
    rel = {k: r for k, r in rel_all.items()
           if not (k.endswith(".version") or k == "hackernews.reply")}
    no_twins = {k: r for k, r in rel.items() if k != "bridge.openalex-arxiv"}
    part = partition(c, rel_all)
    t0 = time.monotonic()
    ids: list[str] = []
    m, holders = load_vectors(instance, c.gid, ids)
    titled = title_atoms(instance, c, m, ids, log)
    item_atoms: dict[int, list[int]] = {}
    for row, gs in enumerate(holders):
        for g in gs:
            item_atoms.setdefault(g, []).append(row)
    x, have = Vectors([], m, holders, item_atoms).item_means(c.n)
    del m
    log(f"items with vectors: {int(have.sum())} ({time.monotonic() - t0:.0f} s)")
    t0 = time.monotonic()
    nn, ss = knn(x, have)
    log(f"50 nearest of every item in {time.monotonic() - t0:.0f} s")
    source = np.asarray(c.source_of, dtype=np.int64)
    rs = rules(nn, ss, source, have)
    indeg = np.bincount(nn[:, :K][nn[:, :K] >= 0], minlength=c.n)[have].astype(np.float64)
    out: dict[str, Any] = {
        "items": c.n, "items_with_vectors": int(have.sum()), "reps": reps,
        "thresholds": {"G": rs["thresholds"]["G"], "GQ": rs["thresholds"]["GQ"],
                       "SQ": {c.sources[int(s)]: t for s, t in rs["thresholds"]["SQ"].items()}},
        "hubness_10nn": {"skew_in_degree": skew(indeg), "max_in_degree": int(indeg.max()),
                         "share_never_a_neighbour": float(np.mean(indeg == 0))},
        "explicit_without_twins": bridge_reading(c, no_twins, part, None, reps=reps),
        "title_only_atoms": titled, "rules": {}}
    for name in ("G", "GQ", "SQ", "M", "C"):
        i, j = rs[name]
        twin = np.asarray([tw.get(int(p)) == int(q) or tw.get(int(q)) == int(p)
                           for p, q in zip(i.tolist(), j.tolist(), strict=True)], dtype=bool)
        deg = np.bincount(np.concatenate([i, j]), minlength=c.n).astype(np.float64)
        per_source = {s: float(deg[(source == k) & have].mean())
                      for k, s in enumerate(c.sources)}
        vals = [v for v in per_source.values() if v > 0]
        t0 = time.monotonic()
        out["rules"][name] = {
            "semantic_edges": int(len(i)), "twin_pairs": int(twin.sum()),
            "mean_degree_by_source": per_source,
            "degree_ratio_max_min": (max(vals) / min(vals)) if vals else None,
            "sources_without_edges": [s for s, v in per_source.items() if v == 0],
            "skew_degree": skew(deg[have]),
            "without_twins": bridge_reading(c, no_twins, part, (i[~twin], j[~twin]), reps=reps),
            "with_twins": bridge_reading(c, rel, part, (i, j), reps=reps)}
        r = out["rules"][name]["without_twins"]
        log(f"  {name}: {len(i)} edges, bridges {r['bridges']} against {r['fp_bar']:.1f} "
            f"(ratio {r['excess_ratio']:.2f}), pairs above their bar {r['pairs_above_own_bar']}"
            f" ({time.monotonic() - t0:.0f} s)")
    return out
