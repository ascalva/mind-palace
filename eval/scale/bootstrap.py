"""Resampling a component: node subsampling and edge resampling, with interval widths.

The relative width of the 95% interval of a statistic is (q97.5 - q2.5) / |median| over the
replicates. The statistics are the spectral gap and the eigengaps lambda_{k+1} - lambda_k.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from eval.scale.graphs import Component, FloatArr, component_from_edges
from eval.scale.spectrum import cut_stats

GAP_INDICES = (1, 2, 3, 4)


def node_subsample(comp: Component, fraction: float, rng: np.random.Generator) -> Component:
    """The largest component of the subgraph induced by a uniform node sample."""
    n = comp.n
    take = max(3, int(round(fraction * n)))
    keep = np.zeros(n, dtype=bool)
    keep[rng.choice(n, size=min(take, n), replace=False)] = True
    em = keep[comp.eu] & keep[comp.ev]
    return _from_canonical(comp, em)


def edge_resample(comp: Component, rng: np.random.Generator) -> Component:
    """The largest component of m edges drawn with replacement from the m edges."""
    idx = rng.integers(0, comp.m, size=comp.m)
    return _from_canonical(comp, idx)


def _from_canonical(comp: Component, sel: npt.NDArray[Any]) -> Component:
    u, v, f = comp.eu[sel], comp.ev[sel], comp.flow[sel]
    # Re-orient by the flow sign so the directed meaning survives the rebuild: +1 means u -> v.
    src = np.where(f >= 0, u, v)
    dst = np.where(f >= 0, v, u)
    out = component_from_edges(src, dst)
    if out.n == 0:
        return out
    return out


def interval_width(values: FloatArr) -> tuple[float, float]:
    """(relative width of the 95% interval, median) of a sample, ignoring NaN."""
    x = values[~np.isnan(values)]
    if len(x) < 2:
        return float("nan"), float("nan")
    lo, med, hi = np.percentile(x, [2.5, 50.0, 97.5])
    return (float((hi - lo) / abs(med)) if med != 0 else float("nan")), float(med)


@dataclass(frozen=True)
class BootRow:
    """One (scheme, fraction) bootstrap at one cut."""

    scheme: str
    fraction: float
    reps: int
    n_mean: float
    degree_over_logn: float
    min_degree_mean: float
    width_gamma: float
    median_gamma: float
    width_gaps: tuple[float, ...]


def bootstrap_cut(
    comp: Component,
    scheme: str,
    fraction: float,
    reps: int,
    rng: np.random.Generator,
    k: int = 8,
) -> BootRow:
    """Resample `reps` times and summarize the spread of gamma and of the first eigengaps."""
    gam: list[float] = []
    gaps: list[list[float]] = [[] for _ in GAP_INDICES]
    ns: list[int] = []
    dl: list[float] = []
    md: list[int] = []
    for _ in range(reps):
        rep = node_subsample(comp, fraction, rng) if scheme == "node" else edge_resample(comp, rng)
        if rep.n < 6:
            continue
        st = cut_stats(rep, k=max(k, max(GAP_INDICES) + 1))
        ns.append(st.n)
        dl.append(st.degree_over_logn)
        md.append(st.min_degree)
        gam.append(st.gamma)
        for slot, g in enumerate(GAP_INDICES):
            gaps[slot].append(st.gap(g))
    if not gam:
        nan = float("nan")
        blank = tuple(nan for _ in GAP_INDICES)
        return BootRow(scheme, fraction, 0, nan, nan, nan, nan, nan, blank)
    w, med = interval_width(np.array(gam))
    return BootRow(
        scheme,
        fraction,
        len(gam),
        float(np.mean(ns)),
        float(np.mean(dl)),
        float(np.mean(md)),
        w,
        med,
        tuple(interval_width(np.array(g))[0] for g in gaps),
    )
