"""The macro quantities per source against N (dn-corpus-instance §6, stage 1's first two rows),
by the scale study's method (`eval/scale/`, `docs/experiments/scale-study-2026-11-07.md`).

For one dated relation: cuts at the dates where the relation's graph first holds N nodes, N on a
geometric ladder; at each cut the largest component of the symmetrized graph, the smallest
eigenvalues of its normalized Laplacian (gamma, the first four eigengaps), the minimum degree
against ln N, the same on the largest component of its k-cores (k = 3, 6, 10), the Hodge split
of its directed flow (gradient, curl, harmonic), and bootstrap widths of each (node subsampling at
several fractions, so one cut gives widths at several scales, and edge resampling). The crossing
is the smallest scale from which a width stays at or below 10% at every larger scale measured.
The bounds that keep a run in hours (a bootstrap only up to `max_boot_n` nodes, the Hodge split on
a node subsample above `max_hodge_m` edges) are reported with the rows they bound.
"""

from __future__ import annotations

import math
import time
from typing import Any

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from eval.corpus.edges import Relation
from eval.scale.bootstrap import (
    GAP_INDICES,
    edge_resample,
    interval_width,
    node_subsample,
)
from eval.scale.graphs import Component, TemporalEdges, component_at, k_core, normalized_laplacian
from eval.scale.hodge import hodge_split
from eval.scale.spectrum import CutStats, smallest_eigenvalues
from eval.scale.study import crossing

# Above this mean degree, or this many nodes, the shift-invert LU fills in (a hyperlink graph's
# mean degree is near 120; a citation graph's 10-core at 30,000 nodes took minutes a solve), and
# plain Lanczos on 2I - L, whose largest eigenvalues are L's smallest, converged in seconds on
# both at the sizes measured, to the same eigenvalues (tests/unit/test_corpus_measures.py).
DENSE_DEGREE = 30.0
LARGE_N = 20000


def eigenvalues(comp: Component, k: int) -> np.ndarray:
    """The k smallest eigenvalues of the normalized Laplacian: the scale study's shift-invert
    solve on a small sparse graph, Lanczos on 2I - L on a dense or a large one (falling back to
    shift-invert if Lanczos does not converge)."""
    lap = normalized_laplacian(comp.adj)
    n = lap.shape[0]
    k = min(k, n)
    if n <= 500 or (float(comp.degrees().mean()) < DENSE_DEGREE and n <= LARGE_N):
        return smallest_eigenvalues(lap, k)
    flip = (2.0 * sp.identity(n, format="csr") - lap).tocsr()
    try:
        vals = spla.eigsh(flip, k=k, which="LA", tol=1e-9, maxiter=50 * n,
                          return_eigenvectors=False)
    except spla.ArpackNoConvergence:
        return smallest_eigenvalues(lap, k)
    return np.sort(2.0 - np.asarray(vals, dtype=np.float64))


def cut_stats(comp: Component, k: int = 20) -> CutStats:
    """`eval.scale.spectrum.cut_stats` with the solver chosen by density."""
    n = comp.n
    if n < 3:
        return CutStats(n, comp.m, 0.0, 0, 0.0, 0.0, np.zeros(0))
    deg = comp.degrees()
    logn = float(np.log(n))
    mean, mn = float(deg.mean()), int(deg.min())
    return CutStats(n, comp.m, mean, mn, mean / logn, mn / logn, eigenvalues(comp, k))


def bootstrap_cut(comp: Component, scheme: str, fraction: float, reps: int,
                  rng: np.random.Generator, core: int = 1) -> dict[str, Any]:
    """The scale study's bootstrap (`eval.scale.bootstrap.bootstrap_cut`) on this module's
    solver: `reps` replicates, each reduced to its k-core when `core` is above 1."""
    gam: list[float] = []
    gaps: list[list[float]] = [[] for _ in GAP_INDICES]
    ns: list[int] = []
    for _ in range(reps):
        rep = node_subsample(comp, fraction, rng) if scheme == "node" else edge_resample(comp, rng)
        if core > 1:
            rep = k_core(rep, core)
        if rep.n < 6:
            continue
        st = cut_stats(rep, k=max(GAP_INDICES) + 4)
        ns.append(st.n)
        gam.append(st.gamma)
        for slot, g in enumerate(GAP_INDICES):
            gaps[slot].append(st.gap(g))
    if not gam:
        return {"scheme": scheme, "fraction": fraction, "reps": 0, "n_mean": math.nan,
                "width_gamma": math.nan, "median_gamma": math.nan,
                **{f"width_gap{g}": math.nan for g in GAP_INDICES}}
    w, med = interval_width(np.array(gam))
    return {"scheme": scheme, "fraction": fraction, "reps": len(gam),
            "n_mean": float(np.mean(ns)), "width_gamma": w, "median_gamma": med,
            **{f"width_gap{g}": interval_width(np.array(x))[0]
               for g, x in zip(GAP_INDICES, gaps, strict=True)}}

LADDER = (300, 1000, 3000, 10000, 30000, 100000)
CORES = (3, 6, 10)
FRACTIONS = (0.25, 0.5, 0.85)


def cut_times(rel: Relation, targets: tuple[int, ...] = LADDER) -> list[tuple[int, float]]:
    """(target N, the first day the relation's edges reach N distinct nodes), for each target
    the relation reaches, and its last day (the whole relation) as the final cut."""
    order = np.argsort(rel.t, kind="stable")
    seen: set[int] = set()
    out: list[tuple[int, float]] = []
    want = list(targets)
    for i in order.tolist():
        seen.add(int(rel.src[i]))
        seen.add(int(rel.dst[i]))
        while want and len(seen) >= want[0]:
            out.append((want.pop(0), float(rel.t[i])))
    out.append((len(seen), float(rel.t[order[-1]]) if len(order) else 0.0))
    return out


def _stats_row(comp: Component, k: int) -> dict[str, Any]:
    st = cut_stats(comp, k=k)
    return {"n": st.n, "m": st.m, "mean_deg": round(st.mean_degree, 3),
            "min_deg": st.min_degree, "deg_over_logn": round(st.degree_over_logn, 3),
            "mindeg_over_logn": round(st.mindeg_over_logn, 3), "gamma": st.gamma,
            **{f"gap{g}": st.gap(g) for g in GAP_INDICES}}


def _boot(comp: Component, reps: int, rng: np.random.Generator, core: int) -> list[dict[str, Any]]:
    return [bootstrap_cut(comp, scheme, frac, reps, rng, core=core)
            for scheme, frac in [("node", f) for f in FRACTIONS] + [("edge", 1.0)]]


def _hodge(comp: Component, max_m: int, rng: np.random.Generator, reps: int) -> dict[str, Any]:
    """The Hodge split of the component's flow, on a node subsample of it when it has more than
    `max_m` edges, with the widths of the three fractions over node subsamples at 0.7."""
    base = comp
    note = ""
    if comp.m > max_m:
        frac = max(0.05, math.sqrt(max_m / comp.m))
        base = node_subsample(comp, frac, rng)
        note = f"on a node subsample at {frac:.2f} ({base.n} nodes, {base.m} edges)"
    hs = hodge_split(base)
    g, c, h = [], [], []
    for _ in range(reps):
        rep = node_subsample(base, 0.7, rng)
        if rep.n < 6 or rep.m == 0:
            continue
        s = hodge_split(rep)
        g.append(s.gradient)
        c.append(s.curl)
        h.append(s.harmonic)
    return {"n": base.n, "m": base.m, "triangles": hs.triangles, "grad": hs.gradient,
            "curl": hs.curl, "harm": hs.harmonic, "note": note,
            "w_grad": interval_width(np.array(g))[0] if g else math.nan,
            "w_curl": interval_width(np.array(c))[0] if c else math.nan,
            "w_harm": interval_width(np.array(h))[0] if h else math.nan}


def curves(rel: Relation, *, reps: int = 8, max_boot_n: int = 40000, max_hodge_m: int = 60000,
           max_core_boot_n: int = 100000, hodge_reps: int = 4, seed: int = 0,
           ladder: tuple[int, ...] = LADDER,
           cores: tuple[int, ...] = CORES, log: Any = print) -> dict[str, Any]:
    """Every cut of one relation: the full component, its k-cores, the Hodge split, bootstraps."""
    rng = np.random.default_rng(seed)
    out: dict[str, Any] = {"relation": rel.name, "source": rel.source, "edges": rel.m,
                           "cuts": [], "bounds": {"reps": reps, "max_boot_n": max_boot_n,
                                                  "max_core_boot_n": max_core_boot_n,
                                                  "max_hodge_m": max_hodge_m,
                                                  "fractions": list(FRACTIONS)}}
    if rel.m == 0:
        return out
    te = TemporalEdges.build(rel.src, rel.dst, rel.t)
    for target, t in cut_times(rel, ladder):
        t0 = time.time()
        comp = component_at(te, t)
        row: dict[str, Any] = {"target": target, "day": t}
        if comp.n < 6:
            row["component"] = {"n": comp.n, "m": comp.m}
            out["cuts"].append(row)
            continue
        k = 20 if comp.n <= 60000 else 8
        row["component"] = _stats_row(comp, k)
        row["boot"] = _boot(comp, reps, rng, 1) if comp.n <= max_boot_n else []
        row["cores"] = []
        for kc in cores:
            core = k_core(comp, kc)
            if core.n < 12:
                row["cores"].append({"k": kc, "n": core.n})
                continue
            crow = {"k": kc, **_stats_row(core, 8)}
            crow["boot"] = _boot(core, reps, rng, kc) if core.n <= max_core_boot_n else []
            row["cores"].append(crow)
        row["hodge"] = _hodge(comp, max_hodge_m, rng, hodge_reps)
        row["seconds"] = round(time.time() - t0, 1)
        out["cuts"].append(row)
        log(f"{rel.source}.{rel.name} N={comp.n} gamma={row['component']['gamma']:.4g} "
            f"({row['seconds']} s)")
    out["crossings"] = crossings(out)
    return out


def crossings(curve: dict[str, Any]) -> dict[str, Any]:
    """N* for gamma and each eigengap, on the full component and on each core, and for the
    three Hodge fractions: the scale from which the width stays at or below 10%."""
    out: dict[str, Any] = {}

    def pts(rows: list[dict[str, Any]], key: str) -> list[tuple[float, float]]:
        return [(float(r["n_mean"]), float(r[key])) for r in rows
                if r.get("n_mean") is not None and not math.isnan(float(r["n_mean"]))
                and r.get(key) is not None]
    full = [b for c in curve["cuts"] for b in c.get("boot", [])]
    for key in ["width_gamma"] + [f"width_gap{g}" for g in GAP_INDICES]:
        out[f"full.{key}"] = crossing(pts(full, key))
    for kc in CORES:
        rows = [b for c in curve["cuts"] for cr in c.get("cores", []) if cr.get("k") == kc
                for b in cr.get("boot", [])]
        for key in ["width_gamma"] + [f"width_gap{g}" for g in GAP_INDICES]:
            out[f"core{kc}.{key}"] = crossing(pts(rows, key))
    hodge = [c["hodge"] for c in curve["cuts"] if "hodge" in c]
    for key in ("w_grad", "w_curl", "w_harm"):
        out[f"hodge.{key}"] = crossing([(float(h["n"]), float(h[key])) for h in hodge
                                        if not math.isnan(float(h[key]))])
    return out


def degenerate(rel: Relation) -> dict[str, Any]:
    """What a relation that forms no large component is: its components' sizes."""
    if rel.m == 0:
        return {"edges": 0}
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    nodes, inv = np.unique(np.concatenate([rel.src, rel.dst]), return_inverse=True)
    n = len(nodes)
    a = coo_matrix((np.ones(rel.m), (inv[:rel.m], inv[rel.m:])), shape=(n, n))
    k, labels = connected_components(a, directed=False)
    sizes = np.bincount(labels)
    return {"edges": rel.m, "nodes": n, "components": int(k),
            "largest": int(sizes.max()), "median": float(np.median(sizes))}
