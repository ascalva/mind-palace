"""Deterministic embedding clustering for the dreaming + curator agents (BUILD-SPEC §9).

No model, no scikit-learn — just NumPy cosine similarity and single-linkage connected
components over a similarity threshold. This is the §9 principle in miniature: the heavy,
*deterministic* work (grouping notes by theme) is done in cheap code so the scarce inference
slot is earned only for the synthesis step (the model reflects a cluster back as a theme).

Clustering is at the NOTE level: each note's chunk vectors are averaged into one centroid,
because chunk-level clustering over-fragments a single note across many themes. Given a
stable input order the output is fully reproducible — a dream run is deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class NoteVector:
    digest: str
    title: str
    vector: tuple[float, ...]      # the note centroid (mean of its chunk vectors)


@dataclass(frozen=True)
class Cluster:
    members: tuple[NoteVector, ...]

    @property
    def titles(self) -> tuple[str, ...]:
        return tuple(m.title for m in self.members)

    @property
    def digests(self) -> tuple[str, ...]:
        return tuple(m.digest for m in self.members)

    @property
    def size(self) -> int:
        return len(self.members)


def note_snippets(rows: list[dict[str, Any]], *, limit: int = 600) -> dict[str, str]:
    """Per-note grounding text: that note's chunk texts concatenated in row order and
    truncated to `limit` chars. Keeps a synthesis/contradiction context lean (§13) while
    still grounded in the owner's actual words."""
    out: dict[str, str] = {}
    for r in rows:
        d = r["digest"]
        if len(out.get(d, "")) < limit:
            out[d] = (out.get(d, "") + " " + r.get("text", "")).strip()
    return {d: t[:limit] for d, t in out.items()}


def note_centroids(rows: list[dict[str, Any]]) -> list[NoteVector]:
    """Aggregate chunk rows (one per vector) to one centroid per note (keyed by digest).
    Insertion order follows first appearance, so the result is deterministic."""
    vecs: dict[str, list[list[float]]] = {}
    titles: dict[str, str] = {}
    for r in rows:
        d = r["digest"]
        vecs.setdefault(d, []).append(list(r["vector"]))
        titles.setdefault(d, r.get("title", ""))
    out: list[NoteVector] = []
    for d, vlist in vecs.items():
        centroid = np.mean(np.asarray(vlist, dtype=np.float64), axis=0)
        out.append(NoteVector(digest=d, title=titles[d], vector=tuple(centroid.tolist())))
    return out


def _normalize(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms == 0] = 1.0          # leave zero vectors at the origin rather than divide by 0
    unit: np.ndarray = m / norms
    return unit


def similarity_matrix(notes: list[NoteVector]) -> np.ndarray:
    """Pairwise cosine similarity over note centroids."""
    if not notes:
        return np.zeros((0, 0))
    m = _normalize(np.asarray([n.vector for n in notes], dtype=np.float64))
    sim: np.ndarray = m @ m.T
    return sim


def cluster_notes(notes: list[NoteVector], *, threshold: float,
                  min_size: int = 2) -> list[Cluster]:
    """Single-linkage connected components: notes whose cosine similarity >= `threshold`
    are joined into a theme. Returns clusters of at least `min_size` members, largest
    first (ties broken by the first member's title — deterministic ordering)."""
    n = len(notes)
    if n == 0:
        return []
    sim = similarity_matrix(notes)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)   # attach to the lower index for stable roots

    for i in range(n):
        for j in range(i + 1, n):
            if sim[i, j] >= threshold:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    clusters = [
        Cluster(members=tuple(notes[i] for i in idxs))
        for idxs in groups.values()
        if len(idxs) >= min_size
    ]
    clusters.sort(key=lambda c: (-c.size, c.members[0].title))
    return clusters


def near_duplicate_pairs(notes: list[NoteVector], *,
                         threshold: float) -> list[tuple[NoteVector, NoteVector, float]]:
    """Distinct note pairs whose centroids are near-identical (cosine >= `threshold`).
    These are near-duplicate CANDIDATES the curator flags — never auto-merged, because
    authored notes are immutable ground truth (§8). Sorted most-similar first."""
    n = len(notes)
    if n < 2:
        return []
    sim = similarity_matrix(notes)
    pairs = [
        (notes[i], notes[j], float(sim[i, j]))
        for i in range(n) for j in range(i + 1, n)
        if sim[i, j] >= threshold
    ]
    pairs.sort(key=lambda p: (-p[2], p[0].title, p[1].title))
    return pairs
