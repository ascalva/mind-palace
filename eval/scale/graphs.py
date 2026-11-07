"""Temporal edge lists, date cuts, the symmetrized largest component and its normalized Laplacian.

A temporal graph is three aligned arrays: `src`, `dst` (node labels, any integers) and `t` (the
time the edge appears, any float). An edge `src -> dst` is directed; the spectral measures use the
symmetrized graph, the flow measures use the direction.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components

IntArr = npt.NDArray[np.int64]
FloatArr = npt.NDArray[np.float64]


@dataclass(frozen=True)
class TemporalEdges:
    """Directed edges with timestamps, sorted by time."""

    src: IntArr
    dst: IntArr
    t: FloatArr

    def __post_init__(self) -> None:
        if not (len(self.src) == len(self.dst) == len(self.t)):
            raise ValueError("src, dst and t must have equal length")

    @staticmethod
    def build(src: npt.ArrayLike, dst: npt.ArrayLike, t: npt.ArrayLike) -> TemporalEdges:
        s = np.asarray(src, dtype=np.int64)
        d = np.asarray(dst, dtype=np.int64)
        tt = np.asarray(t, dtype=np.float64)
        order = np.argsort(tt, kind="stable")
        return TemporalEdges(s[order], d[order], tt[order])

    def upto(self, t_cut: float) -> TemporalEdges:
        """The edges with timestamp at most `t_cut` (a prefix, because the edges are sorted)."""
        k = int(np.searchsorted(self.t, t_cut, side="right"))
        return TemporalEdges(self.src[:k], self.dst[:k], self.t[:k])


def load_edge_csv(path: Path) -> TemporalEdges:
    """Read `src,dst,t` rows (header optional) into a TemporalEdges."""
    arr = np.loadtxt(path, delimiter=",", skiprows=_header_rows(path), ndmin=2)
    return TemporalEdges.build(arr[:, 0].astype(np.int64), arr[:, 1].astype(np.int64), arr[:, 2])


def _header_rows(path: Path) -> int:
    with path.open() as fh:
        first = fh.readline().split(",")[0].strip()
    try:
        float(first)
    except ValueError:
        return 1
    return 0


@dataclass(frozen=True)
class Component:
    """The largest component of a symmetrized graph, nodes relabelled 0..n-1.

    `adj` is the symmetric 0/1 adjacency (no loops); `directed` holds the net flow of each
    canonical edge `(i, j)` with `i < j`: +1 when `i` points to `j`, -1 when `j` points to `i`,
    0 for a mutual pair.
    """

    adj: sp.csr_matrix
    eu: IntArr
    ev: IntArr
    flow: FloatArr

    @property
    def n(self) -> int:
        return int(self.adj.shape[0])

    @property
    def m(self) -> int:
        return len(self.eu)

    def degrees(self) -> IntArr:
        return np.asarray(self.adj.sum(axis=1)).ravel().astype(np.int64)


def component_from_edges(src: IntArr, dst: IntArr) -> Component:
    """Symmetrize, drop loops and duplicates, keep the largest component."""
    keep = src != dst
    s, d = src[keep], dst[keep]
    if len(s) == 0:
        return Component(sp.csr_matrix((0, 0)), _empty(), _empty(), np.zeros(0))
    nodes, inv = np.unique(np.concatenate([s, d]), return_inverse=True)
    n = len(nodes)
    a, b = inv[: len(s)].astype(np.int64), inv[len(s):].astype(np.int64)
    lo, hi = np.minimum(a, b), np.maximum(a, b)
    sign = np.where(a < b, 1.0, -1.0)
    key = lo * n + hi
    uniq, first = np.unique(key, return_inverse=True)
    net = np.zeros(len(uniq))
    np.add.at(net, first, sign)
    u, v = uniq // n, uniq % n
    half = sp.coo_matrix((np.ones(len(u)), (u, v)), shape=(n, n))
    graph = sp.csr_matrix(half + half.T)
    k, labels = connected_components(graph, directed=False)
    if k > 1:
        big = int(np.argmax(np.bincount(labels)))
        mask = labels == big
        newid = -np.ones(n, dtype=np.int64)
        newid[mask] = np.arange(int(mask.sum()))
        em = mask[u] & mask[v]
        u, v, net = newid[u[em]], newid[v[em]], net[em]
        n = int(mask.sum())
    order = np.lexsort((v, u))
    u, v, net = u[order], v[order], net[order]
    top = sp.coo_matrix((np.ones(len(u)), (u, v)), shape=(n, n))
    adj = sp.csr_matrix(top + top.T)
    return Component(adj, u.astype(np.int64), v.astype(np.int64), net)


def _empty() -> IntArr:
    return np.zeros(0, dtype=np.int64)


def component_at(edges: TemporalEdges, t_cut: float) -> Component:
    """The largest component of the symmetrized graph of the edges up to `t_cut`."""
    e = edges.upto(t_cut)
    return component_from_edges(e.src, e.dst)


def normalized_laplacian(adj: sp.csr_matrix) -> sp.csr_matrix:
    """L = I - D^{-1/2} A D^{-1/2} for a graph without isolated nodes."""
    deg = np.asarray(adj.sum(axis=1)).ravel()
    inv = 1.0 / np.sqrt(deg)
    scaled = sp.diags(inv) @ adj @ sp.diags(inv)
    return (sp.identity(adj.shape[0], format="csr") - scaled).tocsr()


def subcomponent(comp: Component, sel: npt.NDArray[Any]) -> Component:
    """The largest component of the graph on the edges `sel` (a mask or an index array)."""
    u, v, f = comp.eu[sel], comp.ev[sel], comp.flow[sel]
    # Re-orient by the flow sign so the directed meaning survives the rebuild: +1 means u -> v.
    src = np.where(f >= 0, u, v)
    dst = np.where(f >= 0, v, u)
    return component_from_edges(src, dst)


def k_core(comp: Component, k: int) -> Component:
    """The largest component of the k-core: peel nodes of degree below `k` until none remain."""
    cur = comp
    while cur.n > 0 and cur.degrees().min() < k:
        keep = cur.degrees() >= k
        nxt = subcomponent(cur, keep[cur.eu] & keep[cur.ev])
        if nxt.n == cur.n:
            break
        cur = nxt
    return cur
