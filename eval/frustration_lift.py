"""The frustration lift, measured: how far one contradiction lifts the signed Laplacian's zero
mode on the live relation edges — the limits program's L4
(`docs/brainstorms/limits-of-the-algebra.md`).

    uv run python eval/frustration_lift.py

It writes nothing: it reads the relation edges and prints. Reports `λ_min(L̄)`, the weighted
frustration `F_w` (the least weight of edges whose sign flip restores balance, by brute force
over the switchings of each component), the bound `λ_min ≤ 4·F_w / n` that the Rayleigh quotient
of the balancing switching proves (FRU-2), and the same after every single flip: one
contradiction asserted, or withdrawn. The graph is a multigraph, edge by edge, as the store
holds it: a pair that both supports and contradicts is frustrated, as the core's balance test
says.
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


def nodes_of(edges: list[Edge]) -> list[str]:
    return sorted({e.u for e in edges} | {e.v for e in edges})


def signed_laplacian(edges: list[Edge], nodes: list[str]) -> np.ndarray:
    """`L̄ = ∑_e w_e (e_u − σ_e e_v)(e_u − σ_e e_v)ᵀ`, edge by edge: parallel edges add, so a
    pair that both supports and contradicts keeps both terms (summing the signed weights first
    would cancel them and hide the frustration, the review of 2026-11-05)."""
    idx = {d: i for i, d in enumerate(nodes)}
    lap = np.zeros((len(nodes), len(nodes)))
    for e in edges:
        i, j = idx[e.u], idx[e.v]
        lap[i, i] += e.w
        lap[j, j] += e.w
        lap[i, j] -= e.sign * e.w
        lap[j, i] -= e.sign * e.w
    return lap


def components(edges: list[Edge], nodes: list[str]) -> list[list[int]]:
    """The components of the multigraph: an edge joins its ends whatever its sign."""
    idx = {d: i for i, d in enumerate(nodes)}
    parent = list(range(len(nodes)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in edges:
        parent[find(idx[e.u])] = find(idx[e.v])
    groups: dict[int, list[int]] = {}
    for i in range(len(nodes)):
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values())


def lam_min(edges: list[Edge], nodes: list[str]) -> float:
    """The least eigenvalue of the signed Laplacian."""
    return float(np.linalg.eigvalsh(signed_laplacian(edges, nodes))[0])


def frustration(edges: list[Edge], nodes: list[str]) -> tuple[float, int] | None:
    """`(F_w, f)`: the least weight of edges whose sign disagrees with `s_u s_v` over the
    switchings `s ∈ {±1}^V`, edge by edge (a supporting and a contradicting edge on one pair
    cost the lighter of the two), and that switching's count, component by component. `None`
    when a component is too large to enumerate."""
    idx = {d: i for i, d in enumerate(nodes)}
    weight, count = 0.0, 0
    for comp in components(edges, nodes):
        if len(comp) > MAX_BRUTE:
            return None
        where = {v: k for k, v in enumerate(comp)}
        inside = [e for e in edges if idx[e.u] in where]
        best: tuple[float, int] | None = None
        for bits in itertools.product((1, -1), repeat=len(comp) - 1):
            s = (1, *bits)
            cost, flips = 0.0, 0
            for e in inside:
                if e.sign * s[where[idx[e.u]]] * s[where[idx[e.v]]] < 0:
                    cost += e.w
                    flips += 1
            if best is None or cost < best[0]:
                best = (cost, flips)
        if best is not None:
            weight += best[0]
            count += best[1]
    return weight, count


def flipped(edges: list[Edge], k: int) -> list[Edge]:
    """The edges with the `k`-th one's sign flipped: one contradiction asserted or withdrawn."""
    e = edges[k]
    return [*edges[:k], Edge(e.u, e.v, e.w, -e.sign, e.rel_type), *edges[k + 1:]]


def measure(edges: list[Edge]) -> list[str]:
    """The report, as lines: the live graph, then every single flip against the bound. A self
    loop is dropped and counted, as the core's balance test drops it (`_balanced`)."""
    loops = [e for e in edges if e.u == e.v]
    edges = [e for e in edges if e.u != e.v]
    nodes = nodes_of(edges)
    n = len(nodes)
    comps = components(edges, nodes)
    lines = [f"edges {len(edges)}, notes {n}, components {len(comps)} "
             f"(sizes {sorted((len(c) for c in comps), reverse=True)}), "
             f"w in [{min(e.w for e in edges):.4f}, {max(e.w for e in edges):.4f}]"
             + (f"; {len(loops)} self loops dropped" if loops else "")]
    fr = frustration(edges, nodes)
    if fr is None:
        lines.append(f"a component has more than {MAX_BRUTE} notes: frustration not enumerated")
        return lines
    weight, count = fr
    bound = 4 * weight / n
    lines.append(f"lambda_min(L_signed) = {lam_min(edges, nodes):.6f}; frustration {count} "
                 f"edges, F_w = {weight:.4f}; balanced: {count == 0}; bound 4*F_w/n = "
                 f"{bound:.6f}")
    lines.append("single flips: edge -> lambda_min, frustration f/F_w, bound 4*F_w/n, ratio")
    worst = 0.0
    for k, e in enumerate(edges):
        edges_k = flipped(edges, k)
        lam, fr_k = lam_min(edges_k, nodes), frustration(edges_k, nodes)
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
