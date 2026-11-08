"""The utility field, simulated on synthetic graphs: no store is read.

    uv run python -m eval.utility_field OUT_DIR

The model is `formal/Palace/Utility/Defs.lean` (dn-utility-field): a field over the sites of a
graph that each tick decays toward a baseline `b` by the rate `lam` and receives this tick's use,
clamped to `[-c, c]`; the structural weights are nudged by `1 + eta (u - b)`, whose margin is
`theta = eta c / lam`. The functions at the top transcribe the model and are the ledger's anchors
for UTL-1 to UTL-6 (`docs/LAWS.md`, XV); the simulation below drives them under a query load on a
two-community graph and writes four tables and a summary: the trajectory of the field (arcs
forming on a hot path and fading when the load moves, the stationary distribution's distance from
the structural one, the spectral drift against its bound), the localization control
(reinforcement with an exponent, without decay: the walk's empirical measure concentrates once the
exponent crosses one), the two-site mean field's shares, and the closed loop's convergence. Every
random draw is seeded.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt

FloatArr = npt.NDArray[np.float64]
IntArr = npt.NDArray[np.int64]

# ---------------------------------------------------------------------------------------------
# The model, transcribed (the anchors of docs/LAWS.md XV)
# ---------------------------------------------------------------------------------------------


def sat(c: float, x: FloatArr) -> FloatArr:
    """The saturated increment: `x` clamped to `[-c, c]` (`Palace.Utility.sat`)."""
    return np.clip(x, -c, c)


def step(b: float, lam: float, c: float, u: FloatArr, use: FloatArr) -> FloatArr:
    """One tick: decay toward the baseline by `lam`, then the saturated increment
    (`Palace.Utility.step`)."""
    return b + (1.0 - lam) * (u - b) + sat(c, use)


def evolve(b: float, lam: float, c: float, u0: FloatArr, log: Sequence[FloatArr]) -> FloatArr:
    """The field after a log of uses: the fold of `step` (`Palace.Utility.evolve`)."""
    u = u0
    for use in log:
        u = step(b, lam, c, u, use)
    return u


def idle(b: float, lam: float, c: float, u: FloatArr, n: int) -> FloatArr:
    """`n` ticks with no use (`Palace.Utility.idle`)."""
    zero = np.zeros_like(u)
    return evolve(b, lam, c, u, [zero] * n)


def steady(b: float, lam: float, c: float, r: float, u: FloatArr, n: int) -> FloatArr:
    """`n` ticks of the constant use `r` (`Palace.Utility.steady`)."""
    use = np.full_like(u, r)
    return evolve(b, lam, c, u, [use] * n)


def ceiling(b: float, lam: float, c: float) -> float:
    """The box's ceiling `b + c/lam` (`Palace.Utility.ceiling`)."""
    return b + c / lam


def floor(b: float, lam: float, c: float) -> float:
    """The box's floor `b - c/lam` (`Palace.Utility.floor`)."""
    return b - c / lam


def in_box(b: float, lam: float, c: float, u: FloatArr, tol: float = 1e-9) -> bool:
    """Every site within the box, to `tol` (`Palace.Utility.InBox`)."""
    return bool(np.all(u >= floor(b, lam, c) - tol) and np.all(u <= ceiling(b, lam, c) + tol))


def is_arc(b: float, a: float, u: FloatArr) -> npt.NDArray[np.bool_]:
    """The sites whose field stands at least `a` above the baseline (`Palace.Utility.IsArc`)."""
    return np.asarray(u >= b + a)


def decay_window(lam: float, c: float, eps: float) -> int:
    """The ticks after which an idle site is within `eps` of the baseline, `log(c/(lam eps))/lam`
    rounded up (UTL-2, `Palace.Utility.idle_window`)."""
    return max(0, math.ceil(math.log(c / (lam * eps)) / lam))


def margin(eta: float, lam: float, c: float) -> float:
    """The margin `theta = eta c / lam` (`Palace.Utility.margin`)."""
    return eta * (c / lam)


def nudge(eta: float, b: float, adj: FloatArr, u: FloatArr) -> FloatArr:
    """The effective weights `A (1 + eta (u - b))` (`Palace.Utility.nudge`)."""
    return adj * (1.0 + eta * (u - b))


def stationary(adj: FloatArr) -> FloatArr:
    """The random walk's stationary distribution, degree over volume (`Palace.Utility.statDist`)."""
    deg = adj.sum(axis=1)
    return np.asarray(deg / deg.sum(), dtype=np.float64)


def total_variation(p: FloatArr, q: FloatArr) -> float:
    """`½ Σ |p - q|` (`Palace.Utility.tv`)."""
    return float(0.5 * np.abs(p - q).sum())


def laplacian(adj: FloatArr) -> FloatArr:
    """`L = D - A`."""
    return np.diag(adj.sum(axis=1)) - adj


def spectral_gap(adj: FloatArr) -> float:
    """The least nonzero eigenvalue of `L` (the second smallest, on a connected support)."""
    vals = np.linalg.eigvalsh(laplacian(adj))
    return float(np.sort(vals)[1])


def closed_loop(
    b: float, lam: float, c: float, feedback: Callable[[FloatArr], FloatArr], u: FloatArr
) -> FloatArr:
    """One tick of the closed loop: this tick's use is a function of the field
    (`Palace.Utility.loop`)."""
    return step(b, lam, c, u, feedback(u))


def sup_dist(u: FloatArr, v: FloatArr) -> float:
    """The sup metric on fields."""
    return float(np.max(np.abs(u - v))) if u.size else 0.0


def polya_step(alpha: float, x: float, y: float) -> tuple[float, float]:
    """The two-site mean field of a reinforcement with exponent `alpha`
    (`Palace.Utility.polyaStep`)."""
    s = x**alpha + y**alpha
    return x + x**alpha / s, y + y**alpha / s


# ---------------------------------------------------------------------------------------------
# The synthetic graph and the query load
# ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Graph:
    """A weighted undirected graph: the structural backbone of the simulation."""

    adj: FloatArr
    edges: list[tuple[int, int]]

    @property
    def n(self) -> int:
        return int(self.adj.shape[0])


def two_communities(
    rng: np.random.Generator, size: int = 12, p_in: float = 0.5, bridges: int = 2
) -> Graph:
    """Two dense communities of `size` nodes each, joined by `bridges` edges, weights in
    `[0.5, 1]`; connected by construction (a spanning path inside each community)."""
    n = 2 * size
    adj = np.zeros((n, n))

    def connect(i: int, j: int) -> None:
        w = float(rng.uniform(0.5, 1.0))
        adj[i, j] = adj[j, i] = w

    for base in (0, size):
        for i in range(base, base + size - 1):
            connect(i, i + 1)
        for i in range(base, base + size):
            for j in range(i + 2, base + size):
                if rng.uniform() < p_in:
                    connect(i, j)
    left = rng.choice(size, size=bridges, replace=False)
    right = rng.choice(size, size=bridges, replace=False)
    for i, j in zip(left.tolist(), right.tolist(), strict=True):
        connect(int(i), size + int(j))
    edges = [(i, j) for i in range(n) for j in range(i + 1, n) if adj[i, j] > 0]
    return Graph(adj, edges)


def shortest_path(adj: FloatArr, source: int, target: int) -> list[int]:
    """Dijkstra on the lengths `1/w`: the path a retrieval follows, its edges the sites a use
    credits."""
    n = adj.shape[0]
    dist = np.full(n, np.inf)
    prev = np.full(n, -1)
    dist[source] = 0.0
    done = np.zeros(n, dtype=bool)
    for _ in range(n):
        cand = np.where(done, np.inf, dist)
        i = int(np.argmin(cand))
        if not np.isfinite(cand[i]):
            break
        done[i] = True
        if i == target:
            break
        for j in np.flatnonzero(adj[i] > 0):
            alt = dist[i] + 1.0 / adj[i, j]
            if alt < dist[j]:
                dist[j] = alt
                prev[j] = i
    path = [target]
    while path[-1] != source:
        if prev[path[-1]] < 0:
            return []
        path.append(int(prev[path[-1]]))
    return path[::-1]


def diffusion_scores(adj: FloatArr, anchor: int, z: float = 0.5) -> FloatArr:
    """The killed walk's fundamental matrix column at the anchor, `((1 - z P)^{-1})[anchor]`,
    normalized by its diagonal: the nearness `diffuse` ranks by (RSP-1), here on the nudged
    weights."""
    deg = adj.sum(axis=1)
    p = adj / deg[:, None]
    z_mat = np.linalg.inv(np.eye(adj.shape[0]) - z * p)
    scores = z_mat[anchor] / np.diag(z_mat)
    scores[anchor] = -np.inf
    return np.asarray(scores, dtype=np.float64)


@dataclass(frozen=True)
class Load:
    """A query load: anchors drawn by a rank-frequency law over a set of hot anchors, each
    anchor with a planted answer, the node whose retrieval counts as realized value."""

    anchors: IntArr
    weights: FloatArr
    answer: dict[int, int]

    def draw(self, rng: np.random.Generator) -> int:
        return int(rng.choice(self.anchors, p=self.weights))


def hop_distances(adj: FloatArr, source: int) -> IntArr:
    """Hop distances from `source` on the support (breadth first)."""
    n = adj.shape[0]
    dist = np.full(n, -1, dtype=np.int64)
    dist[source] = 0
    frontier = [source]
    while frontier:
        nxt: list[int] = []
        for i in frontier:
            for j in np.flatnonzero(adj[i] > 0):
                if dist[j] < 0:
                    dist[j] = dist[i] + 1
                    nxt.append(int(j))
        frontier = nxt
    return dist


def plant_answers(graph: Graph, anchors: Sequence[int], position: int = 1) -> list[int]:
    """For each anchor, the planted answer: the neighbour the structural walk ranks at `position`
    among the anchor's neighbours (`0` the first result), so that it is not the first result and
    the field has room to lift it within its tier."""
    answers: list[int] = []
    for a in anchors:
        scores = diffusion_scores(graph.adj, a)
        neighbours = np.flatnonzero(graph.adj[a] > 0)
        ordered = neighbours[np.argsort(-scores[neighbours])]
        answers.append(int(ordered[min(position, len(ordered) - 1)]))
    return answers


def zipf_load(anchors: Sequence[int], answers: Sequence[int], s: float = 1.0) -> Load:
    """Anchors with rank-frequency weights `1/r^s` (Zipf), the first the hottest."""
    ranks = np.arange(1, len(anchors) + 1, dtype=np.float64)
    w = ranks ** (-s)
    return Load(
        np.asarray(anchors, dtype=np.int64),
        np.asarray(w / w.sum(), dtype=np.float64),
        dict(zip(anchors, answers, strict=True)),
    )


# ---------------------------------------------------------------------------------------------
# The simulation
# ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Params:
    """The field's declared parameters."""

    b: float = 1.0
    lam: float = 0.05
    c: float = 0.02
    eta: float = 5.0 / 6.0
    arc_height: float = 0.3
    value_credit: float = 1.0
    popularity_credit: float = 0.1
    queries_per_tick: int = 10
    follow: float = 0.5

    @property
    def theta(self) -> float:
        return margin(self.eta, self.lam, self.c)


@dataclass
class TickRow:
    """One row of the trajectory table."""

    tick: int
    phase: int
    arcs: int
    hot_edge_field: float
    cold_edge_field: float
    tv: float
    tv_bound: float
    max_eig_drift: float
    eig_bound: float
    gap: float
    gap_bound: float
    hit_rate: float
    probe_rank: float
    probe_hit: float
    in_box: bool


def hot_path_edges(graph: Graph, load: Load) -> list[tuple[int, int]]:
    """The edges of the structural shortest path from the hottest anchor to its answer."""
    a = int(load.anchors[0])
    path = shortest_path(graph.adj, a, load.answer[a])
    return [(min(i, j), max(i, j)) for i, j in zip(path, path[1:], strict=False)]


def simulate(
    graph: Graph,
    loads: Sequence[Load],
    ticks_per_phase: int,
    params: Params,
    rng: np.random.Generator,
) -> tuple[list[TickRow], dict[tuple[int, int], FloatArr]]:
    """Drive the field under the loads, one phase per load, and record the trajectory.

    Each tick: `queries_per_tick` anchors are drawn from the phase's load; each query ranks the
    other nodes by the diffusion score on the nudged weights (the field's nudge of the ranking).
    When the planted answer is the first result, the query resolved with value and the path from
    the anchor to it receives the value credit; otherwise the path to the first result receives
    the popularity credit, a use that produced nothing, and with probability `follow` the answer
    is reached anyway (a citation followed, a question resolved) and its path receives the value
    credit. The field is updated once per tick with the summed credits. Every tick also probes
    the first load: the mean rank of its answers under the current ranking and how often each is
    first, which shows the field learning, forgetting and relearning as the load moves.
    """
    n = graph.n
    u = np.full((n, n), params.b)
    base_stat = stationary(graph.adj)
    base_eigs = np.sort(np.linalg.eigvalsh(laplacian(graph.adj)))
    base_gap = spectral_gap(graph.adj)
    dmax = float(graph.adj.sum(axis=1).max())
    theta = params.theta
    hot = hot_path_edges(graph, loads[0])
    cold = [e for e in graph.edges if e not in hot]
    traces: dict[tuple[int, int], list[float]] = {e: [] for e in hot[:1]}
    rows: list[TickRow] = []
    tick = 0
    for phase, load in enumerate(loads):
        for _ in range(ticks_per_phase):
            eff = nudge(params.eta, params.b, graph.adj, u)
            use = np.zeros((n, n))
            hits = 0
            for _ in range(params.queries_per_tick):
                a = load.draw(rng)
                answer = load.answer[a]
                order = np.argsort(-diffusion_scores(eff, a))
                hit = int(order[0]) == answer
                hits += int(hit)
                credits = (
                    [(answer, params.value_credit)]
                    if hit
                    else [(int(order[0]), params.popularity_credit)]
                )
                if not hit and rng.uniform() < params.follow:
                    credits.append((answer, params.value_credit))
                for target, credit in credits:
                    path = shortest_path(eff, a, target)
                    for i, j in zip(path, path[1:], strict=False):
                        use[i, j] += credit * params.c
                        use[j, i] += credit * params.c
            u = step(params.b, params.lam, params.c, u, use)
            eff = nudge(params.eta, params.b, graph.adj, u)
            stat = stationary(eff)
            eigs = np.sort(np.linalg.eigvalsh(laplacian(eff)))
            arcs = int(sum(1 for i, j in graph.edges if u[i, j] >= params.b + params.arc_height))
            for e in traces:
                traces[e].append(float(u[e]))
            probe_ranks = []
            probe_hits = 0
            for a in loads[0].anchors.tolist():
                order = np.argsort(-diffusion_scores(eff, int(a)))
                rank = int(np.flatnonzero(order == loads[0].answer[int(a)])[0]) + 1
                probe_ranks.append(rank)
                probe_hits += int(rank == 1)
            rows.append(
                TickRow(
                    tick=tick,
                    phase=phase,
                    arcs=arcs,
                    hot_edge_field=float(np.mean([u[e] for e in hot])),
                    cold_edge_field=float(np.mean([u[e] for e in cold])),
                    tv=total_variation(stat, base_stat),
                    tv_bound=theta / (1.0 - theta),
                    max_eig_drift=float(np.max(np.abs(eigs - base_eigs))),
                    eig_bound=2.0 * theta * dmax,
                    gap=spectral_gap(eff),
                    gap_bound=(1.0 - theta) * base_gap,
                    hit_rate=hits / params.queries_per_tick,
                    probe_rank=float(np.mean(probe_ranks)),
                    probe_hit=probe_hits / len(probe_ranks),
                    in_box=in_box(params.b, params.lam, params.c, u),
                )
            )
            tick += 1
    return rows, {e: np.asarray(v) for e, v in traces.items()}


# ---------------------------------------------------------------------------------------------
# The controls
# ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class LocalizationRow:
    """One row of the localization table; `alpha` is `None` for the bounded field, which has no
    exponent."""

    scheme: str
    alpha: float | None
    steps: int
    tv: float
    top_edge_share: float
    nodes_visited: int


def reinforced_walk(
    graph: Graph, alpha: float, steps: int, rng: np.random.Generator, start: int = 0
) -> LocalizationRow:
    """The control: an edge-reinforced walk without decay, each edge's weight its structural
    weight plus its traversal count to the power `alpha`; the empirical measure of the nodes
    against the structural stationary distribution, and the share of steps on the most used edge.
    Linear reinforcement (`alpha = 1`) is a mixture of reversible chains; superlinear
    reinforcement localizes; sublinear stays close to the structural walk."""
    adj = graph.adj.copy()
    counts = np.zeros_like(adj)
    visits = np.zeros(graph.n)
    pos = start
    for _ in range(steps):
        w = adj[pos] + np.where(adj[pos] > 0, counts[pos] ** alpha, 0.0)
        nxt = int(rng.choice(graph.n, p=w / w.sum()))
        counts[pos, nxt] += 1
        counts[nxt, pos] += 1
        visits[nxt] += 1
        pos = nxt
    emp = visits / visits.sum()
    top = float(counts.max() / steps)
    return LocalizationRow(
        "reinforced",
        alpha,
        steps,
        total_variation(emp, stationary(graph.adj)),
        top,
        int(np.count_nonzero(visits)),
    )


def bounded_walk(
    graph: Graph, params: Params, steps: int, rng: np.random.Generator, start: int = 0
) -> LocalizationRow:
    """The design under the same load: a walk on the nudged weights whose traversals feed the
    field through `step`, decayed and capped, so the field stays in its box and the walk's
    stationary law within `theta/(1 - theta)` of the structural one at every time."""
    u = np.full_like(graph.adj, params.b)
    visits = np.zeros(graph.n)
    counts = np.zeros_like(graph.adj)
    pos = start
    for _ in range(steps):
        eff = nudge(params.eta, params.b, graph.adj, u)
        w = eff[pos]
        nxt = int(rng.choice(graph.n, p=w / w.sum()))
        use = np.zeros_like(graph.adj)
        use[pos, nxt] = use[nxt, pos] = params.c
        u = step(params.b, params.lam, params.c, u, use)
        counts[pos, nxt] += 1
        counts[nxt, pos] += 1
        visits[nxt] += 1
        pos = nxt
    emp = visits / visits.sum()
    return LocalizationRow(
        "bounded",
        None,
        steps,
        total_variation(emp, stationary(graph.adj)),
        float(counts.max() / steps),
        int(np.count_nonzero(visits)),
    )


def polya_shares(alpha: float, steps: int, x0: float = 1.2, y0: float = 1.0) -> FloatArr:
    """The leader's share `x/(x + y)` along the two-site mean field with exponent `alpha`."""
    x, y = x0, y0
    out = np.empty(steps)
    for k in range(steps):
        x, y = polya_step(alpha, x, y)
        out[k] = x / (x + y)
    return out


@dataclass(frozen=True)
class LoopRow:
    """One row of the closed-loop convergence table."""

    gain_over_rate: float
    rate_bound: float
    measured_rate: float
    fixed_points: int


def loop_convergence(params: Params, gain: float, sites: int, rng: np.random.Generator) -> LoopRow:
    """Iterate the loop `use = gain (u - b)` from two random fields in the box and measure the
    contraction of their sup distance per tick against `1 - lam + gain` (UTL-6); count the
    distinct fixed points found among the baseline, the ceiling and the floor."""
    b, lam, c = params.b, params.lam, params.c

    def feedback(u: FloatArr) -> FloatArr:
        return gain * (u - b)

    u = rng.uniform(floor(b, lam, c), ceiling(b, lam, c), size=sites)
    v = rng.uniform(floor(b, lam, c), ceiling(b, lam, c), size=sites)
    d0 = sup_dist(u, v)
    for _ in range(50):
        u = closed_loop(b, lam, c, feedback, u)
        v = closed_loop(b, lam, c, feedback, v)
    d1 = sup_dist(u, v)
    measured = (d1 / d0) ** (1.0 / 50) if d0 > 0 and d1 > 0 else 0.0
    fixed = 0
    for cand in (b, ceiling(b, lam, c), floor(b, lam, c)):
        w = np.full(sites, cand)
        if sup_dist(closed_loop(b, lam, c, feedback, w), w) < 1e-12:
            fixed += 1
    return LoopRow(gain / lam, 1.0 - lam + gain, measured, fixed)


# ---------------------------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------------------------


def run(out_dir: Path, seed: int = 20261108) -> dict[str, object]:
    """Run every measurement and write the tables; return the summary."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    params = Params()
    graph = two_communities(rng)
    size = graph.n // 2
    # Phase 1: a hot spot of four anchors in the first community; phase 2 the load moves to three
    # anchors of the second community; phase 3 it comes back.
    anchors_a = [3, 1, 7, 10]
    anchors_b = [size + 2, size + 6, size + 9]
    load_a = zipf_load(anchors_a, plant_answers(graph, anchors_a))
    load_b = zipf_load(anchors_b, plant_answers(graph, anchors_b))
    rows, traces = simulate(graph, [load_a, load_b, load_a], 120, params, rng)
    with (out_dir / "trajectory.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([f for f in TickRow.__dataclass_fields__])
        for r in rows:
            w.writerow([getattr(r, f) for f in TickRow.__dataclass_fields__])

    loc_rows = [reinforced_walk(graph, a, 20_000, rng) for a in (0.5, 1.0, 2.0)]
    loc_rows.append(bounded_walk(graph, params, 20_000, rng))
    with (out_dir / "localization.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([f for f in LocalizationRow.__dataclass_fields__])
        for lr in loc_rows:
            w.writerow([getattr(lr, f) for f in LocalizationRow.__dataclass_fields__])

    shares = {a: polya_shares(a, 2000) for a in (0.5, 1.0, 2.0)}
    with (out_dir / "polya.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["step", "share_alpha_0.5", "share_alpha_1", "share_alpha_2"])
        for k in (0, 9, 99, 499, 999, 1999):
            w.writerow([k + 1, shares[0.5][k], shares[1.0][k], shares[2.0][k]])

    loop_rows = [loop_convergence(params, g * params.lam, 16, rng) for g in (0.25, 0.5, 0.9, 1.5)]
    with (out_dir / "loop.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([f for f in LoopRow.__dataclass_fields__])
        for pr in loop_rows:
            w.writerow([getattr(pr, f) for f in LoopRow.__dataclass_fields__])

    hot_trace = next(iter(traces.values()))
    phase_len = 120
    peak = float(hot_trace[:phase_len].max())
    window = decay_window(params.lam, params.c, 0.01)
    # the hot edge's field after `window` ticks of the second phase (index 120 is its first tick)
    after = float(hot_trace[phase_len - 1 + min(window, phase_len)])
    weights = graph.adj[graph.adj > 0]
    arcs_by_phase = [int(max(r.arcs for r in rows if r.phase == p)) for p in range(3)]
    first_arc = next((r.tick for r in rows if r.arcs > 0), None)
    arcs_gone = next((r.tick for r in rows if r.phase == 1 and r.arcs == 0), None)
    summary: dict[str, object] = {
        "seed": seed,
        "graph": {
            "nodes": graph.n,
            "edges": len(graph.edges),
            "max_degree": float(graph.adj.sum(axis=1).max()),
            "weight_ratio_max": float(weights.max() / weights.min()),
        },
        "params": {
            "b": params.b,
            "lam": params.lam,
            "c": params.c,
            "eta": params.eta,
            "theta": params.theta,
            "ceiling": ceiling(params.b, params.lam, params.c),
            "floor": floor(params.b, params.lam, params.c),
            "arc_height": params.arc_height,
        },
        "box_held_every_tick": all(r.in_box for r in rows),
        "arcs": {
            "hot_path": [list(e) for e in hot_path_edges(graph, load_a)],
            "max_by_phase": arcs_by_phase,
            "first_arc_tick": first_arc,
            "gone_tick_in_phase_2": arcs_gone,
            "hot_edge_peak": peak,
            "decay_window_ticks_eps_0.01": window,
            "hot_edge_after_window": after,
        },
        "tv": {"max": max(r.tv for r in rows), "bound": rows[0].tv_bound},
        "spectrum": {
            "max_eig_drift": max(r.max_eig_drift for r in rows),
            "bound": rows[0].eig_bound,
            "min_gap": min(r.gap for r in rows),
            "gap_bound": rows[0].gap_bound,
            "base_gap": spectral_gap(graph.adj),
        },
        "learning": {
            "hit_rate_phase_1_first_10": float(np.mean([r.hit_rate for r in rows[:10]])),
            "hit_rate_phase_1_last_20": float(np.mean([r.hit_rate for r in rows[100:120]])),
            "probe_rank_tick_0": rows[0].probe_rank,
            "probe_rank_phase_1_last_20": float(np.mean([r.probe_rank for r in rows[100:120]])),
            "probe_rank_phase_2_last_20": float(np.mean([r.probe_rank for r in rows[220:240]])),
            "probe_rank_phase_3_last_20": float(np.mean([r.probe_rank for r in rows[340:360]])),
            "probe_hit_phase_1_last_20": float(np.mean([r.probe_hit for r in rows[100:120]])),
            "probe_hit_phase_2_last_20": float(np.mean([r.probe_hit for r in rows[220:240]])),
            "probe_hit_phase_3_last_20": float(np.mean([r.probe_hit for r in rows[340:360]])),
        },
        "localization": [r.__dict__ for r in loc_rows],
        "polya_share_after_2000": {str(a): float(shares[a][-1]) for a in shares},
        "loop": [r.__dict__ for r in loop_rows],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--seed", type=int, default=20261108)
    args = parser.parse_args(argv)
    summary = run(args.out_dir, args.seed)
    print(json.dumps(summary, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
