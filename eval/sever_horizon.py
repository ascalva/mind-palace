"""The sever horizon, measured: `w·R_eff(a, b)` for every edge of the live similarity backbone —
the limits program's L1 (`docs/brainstorms/limits-of-the-algebra.md`).

    uv run python eval/sever_horizon.py

Read-only. SEV-3 says the product never exceeds one, SEV-4 and SEV-5 that it equals one exactly
at a bridge — where `assume sever` of the edge is singular. The report checks both on the live
backbone and says how close each edge sits to the horizon: the sever risk of every hypothesis.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

TOL = 1e-9


@dataclass(frozen=True)
class EdgeReport:
    i: int
    j: int
    w: float
    w_reff: float
    bridge: bool


def reachable_without(adj: np.ndarray, i: int, j: int) -> bool:
    """Whether `i` still reaches `j` once the edge `i ~ j` is removed — the cut reading."""
    seen, stack = {i}, [i]
    while stack:
        x = stack.pop()
        for y in np.flatnonzero(adj[x] > 0).tolist():
            if {x, y} == {i, j} or y in seen:
                continue
            seen.add(y)
            stack.append(y)
    return j in seen


def horizon(adj: np.ndarray) -> list[EdgeReport]:
    """Every edge's `w·R_eff`, through the pseudo-inverse of the Laplacian, and whether it is a
    bridge."""
    lap = np.diag(adj.sum(axis=1)) - adj
    pinv = np.linalg.pinv(lap)
    out: list[EdgeReport] = []
    for i, j in zip(*np.triu_indices_from(adj, k=1), strict=True):
        w = float(adj[i, j])
        if w <= 0:
            continue
        reff = float(pinv[i, i] + pinv[j, j] - 2 * pinv[i, j])
        a, b = int(i), int(j)
        out.append(EdgeReport(a, b, w, w * reff, not reachable_without(adj, a, b)))
    return out


def measure(adj: np.ndarray, titles: list[str]) -> list[str]:
    """The report, as lines: the backbone, the bound, the bridges, and the edges nearest the
    horizon."""
    edges = horizon(adj)
    n = adj.shape[0]
    lines = [f"notes {n}, edges {len(edges)}, "
             f"w in [{min((e.w for e in edges), default=0):.3f}, "
             f"{max((e.w for e in edges), default=0):.3f}]"]
    if not edges:
        return lines + ["no edges: nothing to sever"]
    over = [e for e in edges if e.w_reff > 1 + TOL]
    bridges = [e for e in edges if e.bridge]
    at_horizon = [e for e in edges if abs(e.w_reff - 1) <= 1e-6]
    lines.append(f"bound w*R_eff <= 1: {'holds' if not over else 'VIOLATED'} "
                 f"(max {max(e.w_reff for e in edges):.6f}, {len(over)} over)")
    same = {(e.i, e.j) for e in bridges} == {(e.i, e.j) for e in at_horizon}
    lines.append(f"bridges {len(bridges)}, edges at the horizon {len(at_horizon)}: "
                 f"{'agree' if same else 'DISAGREE'}")
    lines.append("edges nearest the horizon (w*R_eff, w, the two notes):")
    for e in sorted(edges, key=lambda e: -e.w_reff)[:8]:
        lines.append(f"  {e.w_reff:.4f}  w {e.w:.3f}  {titles[e.i][:30]} ~ {titles[e.j][:30]}"
                     f"{'  [bridge]' if e.bridge else ''}")
    lines.append(f"median w*R_eff {float(np.median([e.w_reff for e in edges])):.4f}; "
                 f"edges above 0.9: {sum(e.w_reff > 0.9 for e in edges)}")
    return lines


def main() -> int:
    from core.sealing import seal

    seal()
    from core.query import QueryEngine

    notes, _, weights = QueryEngine().note_graph()
    if not notes:
        print("no authored notes")
        return 1
    for line in measure(np.asarray(weights, dtype=np.float64),
                        [str(n.get("title") or n["source_path"]) for n in notes]):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
