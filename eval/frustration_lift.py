"""The frustration lift, measured: how far one contradiction lifts the signed Laplacian's zero
mode on the live relation edges — the limits program's L4
(`docs/brainstorms/limits-of-the-algebra.md`).

    uv run python eval/frustration_lift.py

Read-only. Reports `λ_min(L̄)`, the weighted frustration `F_w` (the least weight of edges whose
sign flip restores balance, by brute force over the switchings of each component), the bound
`λ_min ≤ 4·F_w / n` that the Rayleigh quotient of the balancing switching proves, and the same
after every single flip — one contradiction asserted, or withdrawn.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np

MAX_BRUTE = 20   # switchings are enumerated per component; past this many notes, say so instead


@dataclass(frozen=True)
class Edge:
    u: str
    v: str
    w: float
    sign: int
    rel_type: str


def adjacency(edges: list[Edge]) -> tuple[np.ndarray, list[str]]:
    nodes = sorted({e.u for e in edges} | {e.v for e in edges})
    idx = {d: i for i, d in enumerate(nodes)}
    adj = np.zeros((len(nodes), len(nodes)))
    for e in edges:
        adj[idx[e.u], idx[e.v]] += e.sign * e.w
        adj[idx[e.v], idx[e.u]] += e.sign * e.w
    return adj, nodes


def components(adj: np.ndarray) -> list[list[int]]:
    n = adj.shape[0]
    seen: set[int] = set()
    out: list[list[int]] = []
    for start in range(n):
        if start in seen:
            continue
        stack, comp = [start], []
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            comp.append(x)
            stack.extend(j for j in range(n) if adj[x, j] != 0 and j not in seen)
        out.append(sorted(comp))
    return out


def lam_min(adj: np.ndarray) -> float:
    """The least eigenvalue of the signed Laplacian `L̄ = D − A`, `D` from `|A|`."""
    lap = np.diag(np.abs(adj).sum(axis=1)) - adj
    return float(np.linalg.eigvalsh(lap)[0])


def frustration(adj: np.ndarray) -> tuple[float, int] | None:
    """`(F_w, f)`: the least weight of edges whose sign disagrees with `s_i s_j` over the
    switchings `s ∈ {±1}^V`, and that switching's count — component by component. `None` when a
    component is too large to enumerate."""
    weight, count = 0.0, 0
    for comp in components(adj):
        if len(comp) > MAX_BRUTE:
            return None
        best: tuple[float, int] | None = None
        for bits in itertools.product((1, -1), repeat=len(comp) - 1):
            s = (1, *bits)
            cost, flips = 0.0, 0
            for a in range(len(comp)):
                for b in range(a + 1, len(comp)):
                    w = float(adj[comp[a], comp[b]])
                    if w != 0 and (w > 0) != (s[a] * s[b] > 0):
                        cost += abs(w)
                        flips += 1
            if best is None or cost < best[0]:
                best = (cost, flips)
        if best is not None:
            weight += best[0]
            count += best[1]
    return weight, count


def flipped(adj: np.ndarray, i: int, j: int) -> np.ndarray:
    out = adj.copy()
    out[i, j], out[j, i] = -out[i, j], -out[j, i]
    return out


def measure(edges: list[Edge]) -> list[str]:
    """The report, as lines: the live graph, then every single flip against the bound."""
    adj, nodes = adjacency(edges)
    n = len(nodes)
    idx = {d: i for i, d in enumerate(nodes)}
    comps = components(adj)
    lines = [f"edges {len(edges)}, notes {n}, components {len(comps)} "
             f"(sizes {sorted((len(c) for c in comps), reverse=True)}), "
             f"w in [{min(e.w for e in edges):.4f}, {max(e.w for e in edges):.4f}]"]
    fr = frustration(adj)
    if fr is None:
        lines.append(f"a component has more than {MAX_BRUTE} notes: frustration not enumerated")
        return lines
    weight, count = fr
    bound = 4 * weight / n
    lines.append(f"lambda_min(L_signed) = {lam_min(adj):.6f}; frustration {count} edges, "
                 f"F_w = {weight:.4f}; balanced: {count == 0}; bound 4*F_w/n = {bound:.6f}")
    lines.append("single flips: edge -> lambda_min, frustration f/F_w, bound 4*F_w/n, ratio")
    worst = 0.0
    for k, e in enumerate(edges):
        adj_k = flipped(adj, idx[e.u], idx[e.v])
        lam, fr_k = lam_min(adj_k), frustration(adj_k)
        if fr_k is None:
            continue
        w_k, f_k = fr_k
        b_k = 4 * w_k / n
        ratio = lam / b_k if b_k > 0 else 0.0
        worst = max(worst, ratio)
        flag = "VIOLATES" if lam > b_k + 1e-9 else "ok"
        lines.append(f"  {k:2d} {e.rel_type:12s} {e.sign:+d} w {e.w:.3f}: lambda_min {lam:.6f}  "
                     f"{f_k}/{w_k:.3f}  bound {b_k:.6f}  ratio {ratio:.3f} {flag}")
    lines.append(f"largest lambda_min/bound over single flips: {worst:.4f}")
    return lines


def main() -> int:
    from core.sealing import seal

    seal()
    from core.stores.edges import open_edge_store

    edges = [Edge(e.u, e.v, float(e.w), int(e.sign), e.rel_type) for e in open_edge_store().all()]
    if not edges:
        print("no relation edges")
        return 1
    for line in measure(edges):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
