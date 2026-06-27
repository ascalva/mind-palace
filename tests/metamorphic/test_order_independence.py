"""Metamorphic: clustering is invariant to input order (holistic-testing.md §1b).

Feed the same note vectors in two different orders -> the same cluster structure. The
deterministic NumPy clustering must not depend on the order rows arrive in.
"""

from __future__ import annotations

from fixtures.corpus import vector_rows

from core.dreaming.cluster import cluster_notes, note_centroids

# two tight pairs + one outlier (which is dropped: it can't meet min_size on its own)
_SPECS = [
    ("d1", "sleep-a", [1.0, 0.0, 0.0]),
    ("d2", "sleep-b", [0.99, 0.01, 0.0]),
    ("d3", "food-a", [0.0, 1.0, 0.0]),
    ("d4", "food-b", [0.01, 0.99, 0.0]),
    ("d5", "lonely", [0.0, 0.0, 1.0]),
]


def _structure(rows):
    clusters = cluster_notes(note_centroids(rows), threshold=0.9, min_size=2)
    return sorted(tuple(sorted(c.titles)) for c in clusters)


def test_cluster_structure_is_order_independent():
    forward = _structure(vector_rows(_SPECS))
    backward = _structure(vector_rows(list(reversed(_SPECS))))
    assert forward == backward
    assert forward == [("food-a", "food-b"), ("sleep-a", "sleep-b")]
