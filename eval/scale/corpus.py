"""A synthetic graph with the size and shape of a small personal corpus.

Nothing here reads data: the graph is drawn at random with the stated node and edge counts and a
single generation (every edge joins a node to one earlier node, no node has a chain of ancestors
longer than one step).
"""

from __future__ import annotations

import numpy as np

from eval.scale.graphs import TemporalEdges


def one_generation_graph(n_nodes: int = 38, n_edges: int = 20, seed: int = 0) -> TemporalEdges:
    """`n_edges` edges from a 'child' half of the nodes to distinct 'parent' nodes.

    Nodes 0..p-1 are parents, p..n-1 are children, so no node is both: one generation. Each
    child holds at most one edge, so edges are distinct children, parents drawn uniformly.
    """
    rng = np.random.default_rng(seed)
    parents = n_nodes - n_edges if n_nodes - n_edges >= 1 else 1
    children = rng.choice(np.arange(parents, n_nodes), size=n_edges, replace=False)
    targets = rng.integers(0, parents, size=n_edges)
    return TemporalEdges.build(children, targets, np.arange(n_edges, dtype=np.float64))


def contrast(n_seeds: int = 200, reps: int = 100) -> list[dict[str, float]]:
    """Measure `n_seeds` synthetic corpora on the study's quantities.

    Per seed: the component count, the size of the largest component, its degrees, gamma and the
    edge-resample interval width of gamma. Graphs whose largest component has fewer than 6 nodes
    report NaN for the bootstrap (the resampled graph is too small to carry a spectrum).
    """
    from eval.scale.bootstrap import bootstrap_cut
    from eval.scale.graphs import component_at
    from eval.scale.spectrum import cut_stats

    rng = np.random.default_rng(12345)
    rows: list[dict[str, float]] = []
    for seed in range(n_seeds):
        edges = one_generation_graph(seed=seed)
        comp = component_at(edges, 1e9)
        ncomp = _components(edges)
        st = cut_stats(comp)
        width = float("nan")
        if comp.n >= 6:
            width = bootstrap_cut(comp, "edge", 1.0, reps, rng, k=5).width_gamma
        rows.append(
            {
                "seed": float(seed),
                "components_with_edges": float(ncomp),
                "lcc_n": float(comp.n),
                "lcc_m": float(comp.m),
                "mean_degree": st.mean_degree,
                "min_degree": float(st.min_degree),
                "deg_over_logn": st.degree_over_logn,
                "gamma": st.gamma,
                "width_gamma_edge": width,
            }
        )
    return rows


def reference_graphs(n_nodes: int = 38, seed: int = 0) -> dict[str, TemporalEdges]:
    """Two connected 38-node graphs for scale: a random recursive tree and a degree 2 ln N graph."""
    rng = np.random.default_rng(seed)
    child = np.arange(1, n_nodes)
    parent = np.array([rng.integers(0, c) for c in child])
    tree = TemporalEdges.build(child, parent, child.astype(np.float64))
    # a random recursive tree plus extra random edges until the mean degree is 2 ln N
    target = int(round(n_nodes * np.log(n_nodes)))
    src = [int(x) for x in child]
    dst = [int(x) for x in parent]
    seen = {(int(a), int(b)) for a, b in zip(src, dst, strict=True)}
    while len(src) < target:
        a, b = (int(x) for x in rng.integers(0, n_nodes, size=2))
        if a != b and (a, b) not in seen and (b, a) not in seen:
            seen.add((a, b))
            src.append(a)
            dst.append(b)
    dense = TemporalEdges.build(src, dst, np.arange(len(src), dtype=np.float64))
    return {"recursive_tree": tree, "degree_2logn": dense}


def reference_rows(reps: int = 200) -> list[dict[str, float]]:
    """The study's quantities on the reference graphs, with edge-resample widths of gamma."""
    from eval.scale.bootstrap import bootstrap_cut
    from eval.scale.graphs import component_at
    from eval.scale.spectrum import cut_stats

    rng = np.random.default_rng(7)
    rows: list[dict[str, float]] = []
    for name, edges in reference_graphs().items():
        comp = component_at(edges, 1e9)
        st = cut_stats(comp)
        row = bootstrap_cut(comp, "edge", 1.0, reps, rng, k=5)
        rows.append({"graph": float(len(rows)), "n": float(comp.n), "m": float(comp.m),
                     "mean_degree": st.mean_degree, "min_degree": float(st.min_degree),
                     "deg_over_logn": st.degree_over_logn, "gamma": st.gamma,
                     "width_gamma_edge": row.width_gamma, "n_mean_boot": row.n_mean})
        print(name, rows[-1], file=__import__("sys").stderr)
    return rows


def _components(edges: TemporalEdges) -> int:
    import scipy.sparse as sp
    from scipy.sparse.csgraph import connected_components

    nodes, inv = np.unique(np.concatenate([edges.src, edges.dst]), return_inverse=True)
    k = len(edges.src)
    g = sp.coo_matrix((np.ones(k), (inv[:k], inv[k:])), shape=(len(nodes), len(nodes)))
    return int(connected_components(g, directed=False)[0])


def main() -> None:
    import csv
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--references":
        reference_rows()
        return
    rows = contrast()
    w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)


if __name__ == "__main__":
    main()
