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
