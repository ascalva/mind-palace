"""The scale study driver: grow a temporal graph by cuts and measure at each cut.

    uv run python -m eval.scale.study EDGES.csv OUT_DIR --first 7305 --last 20000 --step 365.25

writes `cuts.csv` (size, degrees, spectrum, relaxation time, required window), `boot.csv` (bootstrap
interval widths per scheme and fraction) and `hodge.csv` (flow energies with bootstrap widths).
"""

from __future__ import annotations

import argparse
import csv
import math
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from eval.scale.bootstrap import (
    GAP_INDICES,
    BootRow,
    bootstrap_cut,
    edge_resample,
    interval_width,
    node_subsample,
)
from eval.scale.graphs import Component, TemporalEdges, component_at, load_edge_csv
from eval.scale.hodge import hodge_split
from eval.scale.spectrum import cut_stats

FRACTIONS = (0.25, 0.4, 0.55, 0.7, 0.85)


def required_window(gamma: float, precision: float = 0.1, rel_std: float = 1.0) -> float:
    """Steps of the walk needed to average an observable to relative precision `precision`.

    For a reversible chain with spectral gap `gamma`, the variance of the time average over T
    steps is at most 2 Var_pi(g) / (gamma T) (the standard asymptotic-variance bound). With
    relative standard deviation `rel_std` = sd / mean under the stationary law, a relative
    standard error `precision` needs T >= 2 rel_std^2 / (gamma precision^2).
    """
    return 2.0 * rel_std**2 / (gamma * precision**2)


def crossing(rows: Sequence[tuple[float, float]], threshold: float = 0.10) -> float:
    """Smallest scale from which the width stays at or below `threshold` at every larger scale.

    `rows` are (scale, width) pairs; NaN widths are ignored. Returns NaN if never.
    """
    pts = sorted((s, w) for s, w in rows if not math.isnan(w))
    best = float("nan")
    for s, w in reversed(pts):
        if w <= threshold:
            best = s
        else:
            break
    return best


def hodge_boot(
    comp: Component, scheme: str, fraction: float, reps: int, rng: np.random.Generator
) -> tuple[float, float, float, float]:
    """(width of gradient, curl, harmonic energy fractions, mean n) over replicates."""
    g: list[float] = []
    c: list[float] = []
    h: list[float] = []
    ns: list[int] = []
    for _ in range(reps):
        rep = node_subsample(comp, fraction, rng) if scheme == "node" else edge_resample(comp, rng)
        if rep.n < 6 or rep.m == 0:
            continue
        s = hodge_split(rep)
        g.append(s.gradient)
        c.append(s.curl)
        h.append(s.harmonic)
        ns.append(rep.n)
    if not g:
        nan = float("nan")
        return nan, nan, nan, nan
    return (
        interval_width(np.array(g))[0],
        interval_width(np.array(c))[0],
        interval_width(np.array(h))[0],
        float(np.mean(ns)),
    )


def run(
    edges: TemporalEdges,
    cuts: Sequence[float],
    out: Path,
    reps: int,
    hodge_reps: int,
    seed: int,
    fractions: Sequence[float] = FRACTIONS,
    max_boot_n: int = 10**9,
) -> None:
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    with (
        (out / "cuts.csv").open("w", newline="") as fc,
        (out / "boot.csv").open("w", newline="") as fb,
        (out / "hodge.csv").open("w", newline="") as fh,
    ):
        wc, wb, wh = csv.writer(fc), csv.writer(fb), csv.writer(fh)
        wc.writerow(
            ["cut", "n", "m", "mean_deg", "min_deg", "deg_over_logn", "mindeg_over_logn",
             "gamma", "relax_steps", "window_10pct"]
            + [f"lam{i}" for i in range(1, 21)]
            + [f"gap{i}" for i in GAP_INDICES]
        )
        wb.writerow(
            ["cut", "scheme", "fraction", "reps", "n_mean", "deg_over_logn", "min_deg_mean",
             "width_gamma", "median_gamma"] + [f"width_gap{i}" for i in GAP_INDICES]
        )
        wh.writerow(
            ["cut", "scheme", "fraction", "n", "triangles", "grad", "curl", "harm",
             "n_mean_boot", "w_grad", "w_curl", "w_harm"]
        )
        for cut in cuts:
            comp = component_at(edges, cut)
            if comp.n < 6:
                continue
            st = cut_stats(comp, k=20)
            eig = list(st.eigenvalues) + [float("nan")] * (20 - len(st.eigenvalues))
            wc.writerow(
                [cut, st.n, st.m, st.mean_degree, st.min_degree, st.degree_over_logn,
                 st.mindeg_over_logn, st.gamma, 1.0 / st.gamma, required_window(st.gamma)]
                + eig + [st.gap(i) for i in GAP_INDICES]
            )
            fc.flush()
            if comp.n <= max_boot_n:
                plan: list[tuple[str, float]] = [("node", f) for f in fractions] + [("edge", 1.0)]
                for scheme, frac in plan:
                    row: BootRow = bootstrap_cut(comp, scheme, frac, reps, rng)
                    wb.writerow([cut, scheme, frac, row.reps, row.n_mean, row.degree_over_logn,
                                 row.min_degree_mean, row.width_gamma, row.median_gamma,
                                 *row.width_gaps])
                fb.flush()
            hs = hodge_split(comp)
            wh.writerow([cut, "full", 1.0, comp.n, hs.triangles, hs.gradient, hs.curl,
                         hs.harmonic, comp.n, "", "", ""])
            if comp.n <= max_boot_n:
                for scheme, frac in (("node", 0.7), ("edge", 1.0)):
                    wg, wcu, wha, nm = hodge_boot(comp, scheme, frac, hodge_reps, rng)
                    wh.writerow([cut, scheme, frac, comp.n, hs.triangles, hs.gradient, hs.curl,
                                 hs.harmonic, nm, wg, wcu, wha])
            fh.flush()
            print(f"cut {cut:.0f} n={st.n} gamma={st.gamma:.4g}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("edges", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--first", type=float, required=True, help="first cut time")
    ap.add_argument("--last", type=float, required=True)
    ap.add_argument("--step", type=float, required=True)
    ap.add_argument("--extra", type=float, nargs="*", default=[], help="further cut times")
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--hodge-reps", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-boot-n", type=int, default=10**9)
    a = ap.parse_args()
    edges = load_edge_csv(a.edges.expanduser())
    cuts = sorted({*np.arange(a.first, a.last + 1e-9, a.step).tolist(), *a.extra})
    run(edges, cuts, a.out.expanduser(), a.reps, a.hodge_reps, a.seed, max_boot_n=a.max_boot_n)


if __name__ == "__main__":
    main()
