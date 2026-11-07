"""Hodge split of an edge flow into gradient, curl and harmonic energy.

On the clique complex of the symmetrized graph (nodes, edges, triangles), a flow `f` on edges
splits orthogonally as `f = grad s + curl^T w + h`. The gradient part is the least-squares
projection onto the image of the node-to-edge difference operator, the curl part the projection
onto the image of the transpose of the edge-to-triangle curl, and `h` the harmonic remainder.
Energies are squared norms as fractions of ||f||^2.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from eval.scale.graphs import Component, IntArr

LSMR_TOL = 1e-8


@dataclass(frozen=True)
class HodgeSplit:
    gradient: float
    curl: float
    harmonic: float
    triangles: int


def triangles(comp: Component) -> tuple[IntArr, IntArr, IntArr]:
    """All triangles (i < j < k) as three index arrays."""
    n = comp.n
    up = sp.csr_matrix((np.ones(comp.m), (comp.eu, comp.ev)), shape=(n, n))
    cnt = (up @ up).multiply(up).tocoo()  # edge (i, k) -> number of j with i<j<k
    lower = up.T.tocsr()
    ti: list[IntArr] = []
    tj: list[IntArr] = []
    tk: list[IntArr] = []
    for i, k in zip(cnt.row.tolist(), cnt.col.tolist(), strict=True):
        js = np.intersect1d(
            up.indices[up.indptr[i]: up.indptr[i + 1]],
            lower.indices[lower.indptr[k]: lower.indptr[k + 1]],
            assume_unique=True,
        )
        if len(js):
            ti.append(np.full(len(js), i, dtype=np.int64))
            tj.append(js.astype(np.int64))
            tk.append(np.full(len(js), k, dtype=np.int64))
    if not ti:
        z = np.zeros(0, dtype=np.int64)
        return z, z, z
    return np.concatenate(ti), np.concatenate(tj), np.concatenate(tk)


def hodge_split(comp: Component) -> HodgeSplit:
    """Gradient, curl and harmonic energy fractions of the component's citation flow."""
    f = comp.flow
    total = float(f @ f)
    if comp.m == 0 or total == 0.0:
        return HodgeSplit(float("nan"), float("nan"), float("nan"), 0)
    m, n = comp.m, comp.n
    rows = np.concatenate([np.arange(m), np.arange(m)])
    cols = np.concatenate([comp.eu, comp.ev])
    vals = np.concatenate([-np.ones(m), np.ones(m)])
    grad_op = sp.csr_matrix((vals, (rows, cols)), shape=(m, n))  # (grad s)_e = s_v - s_u
    s = spla.lsmr(grad_op, f, atol=LSMR_TOL, btol=LSMR_TOL)[0]
    g = grad_op @ s
    ti, tj, tk = triangles(comp)
    curl_energy = 0.0
    if len(ti):
        key = comp.eu * n + comp.ev  # sorted: edges are lexsorted by (u, v)
        e_ij = np.searchsorted(key, ti * n + tj)
        e_jk = np.searchsorted(key, tj * n + tk)
        e_ik = np.searchsorted(key, ti * n + tk)
        t_count = len(ti)
        r = np.repeat(np.arange(t_count), 3)
        c = np.stack([e_ij, e_jk, e_ik], axis=1).ravel()
        v = np.tile(np.array([1.0, 1.0, -1.0]), t_count)
        curl_op = sp.csr_matrix((v, (r, c)), shape=(t_count, m))  # (curl f)_ijk
        w = spla.lsmr(curl_op.T.tocsr(), f, atol=LSMR_TOL, btol=LSMR_TOL)[0]
        cf = curl_op.T @ w
        curl_energy = float(cf @ cf)
    ge = float(g @ g)
    harm = max(0.0, 1.0 - (ge + curl_energy) / total)
    return HodgeSplit(ge / total, curl_energy / total, harm, len(ti))
