"""Deterministic embedding clustering (BUILD-SPEC §9) — NumPy only, no model.

Proves: chunk rows collapse to note centroids; cosine single-linkage groups related notes
and separates unrelated ones; near-duplicate pairs surface; output is reproducible.
"""

from core.dreaming.cluster import (
    cluster_notes,
    near_duplicate_pairs,
    note_centroids,
    note_snippets,
)


def _row(digest, vec, title, text="x"):
    return {"digest": digest, "title": title, "text": text, "vector": vec}


def test_centroids_average_chunk_vectors_per_note():
    rows = [
        _row("d1", [1.0, 0.0], "a"),
        _row("d1", [0.0, 1.0], "a"),    # same note, second chunk
        _row("d2", [1.0, 1.0], "b"),
    ]
    notes = note_centroids(rows)
    by_title = {n.title: n.vector for n in notes}
    assert by_title["a"] == (0.5, 0.5)     # mean of the two chunk vectors
    assert by_title["b"] == (1.0, 1.0)
    assert len(notes) == 2                 # one NoteVector per digest


def test_cluster_groups_similar_and_separates_dissimilar():
    notes = note_centroids([
        _row("d1", [1.0, 0.0, 0.0], "sleep-1"),
        _row("d2", [0.98, 0.02, 0.0], "sleep-2"),   # close to sleep-1
        _row("d3", [0.0, 0.0, 1.0], "cooking"),     # orthogonal -> its own (dropped: <min_size)
    ])
    clusters = cluster_notes(notes, threshold=0.9, min_size=2)
    assert len(clusters) == 1
    assert set(clusters[0].titles) == {"sleep-1", "sleep-2"}


def test_high_threshold_splits_everything():
    notes = note_centroids([
        _row("d1", [1.0, 0.0, 0.0], "a"),
        _row("d2", [0.8, 0.6, 0.0], "b"),
    ])
    assert cluster_notes(notes, threshold=0.999, min_size=2) == []   # nothing meets it


def test_clustering_is_deterministic():
    notes = note_centroids([
        _row("d1", [1.0, 0.0], "a"), _row("d2", [0.99, 0.01], "b"),
        _row("d3", [0.0, 1.0], "c"), _row("d4", [0.01, 0.99], "d"),
    ])
    a = [c.titles for c in cluster_notes(notes, threshold=0.9, min_size=2)]
    b = [c.titles for c in cluster_notes(notes, threshold=0.9, min_size=2)]
    assert a == b


def test_near_duplicate_pairs_surface_only_above_threshold():
    notes = note_centroids([
        _row("d1", [1.0, 0.0], "orig"),
        _row("d2", [0.999, 0.001], "dup"),   # near-identical
        _row("d3", [0.0, 1.0], "other"),
    ])
    pairs = near_duplicate_pairs(notes, threshold=0.98)
    assert len(pairs) == 1
    a, b, sim = pairs[0]
    assert {a.title, b.title} == {"orig", "dup"} and sim >= 0.98


def test_note_snippets_concatenate_and_truncate():
    rows = [_row("d1", [1.0], "a", text="hello"), _row("d1", [1.0], "a", text="world")]
    snips = note_snippets(rows, limit=8)
    assert snips["d1"] == "hello wo"     # joined then truncated to the limit


def test_empty_inputs_are_safe():
    assert note_centroids([]) == []
    assert cluster_notes([], threshold=0.5) == []
    assert near_duplicate_pairs([], threshold=0.5) == []
