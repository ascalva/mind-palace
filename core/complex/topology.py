"""Flag complex + persistent H₁ — conceptual holes (companion III §4; H5).

Persistence runs over the **flag (clique) complex** K_σ of the similarity graph: sweep the
cosine-distance threshold (Vietoris–Rips filtration — Rips *is* the flag complex of the distance
graph), track when cycles are born and die. A long-lived H₁ feature is a **conceptual hole**:
notes pairwise related in a ring with no center tying them together — "you orbit this without
stating it". The bottleneck stability theorem makes the diagram a *stable* diagnostic (it moves no
more than the input perturbation).

**What H₁ is NOT (the §4.2 correction, load-bearing):** a 1-cycle is a topological hole — NEVER a
logical contradiction (that is a signed/semantic property, routed through `balance.py`) and NEVER
circular reasoning (structurally impossible on the acyclic derives-DAG). Route dissonance through
balance/frustration; route gaps through here. Holes are a *utility-axis* prompt (what to look at),
not a belief claim.

`ripser` (the BUILD §2.2-adopted C++ backend) is imported lazily inside the compute call — it drags
in plotting libs we never use at module import. Deterministic; no model; no network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Hole:
    """One long-lived H₁ feature: a conceptual hole in the flag complex.

    `vertices` is a deterministic *witness* on the cycle (the representative cocycle's endpoints,
    completed into a cycle through the birth-scale graph) — the notes that circle the hole. A
    witness, not the unique minimal cycle (which is not well-defined in general)."""

    birth: float          # cosine-distance scale at which the cycle closes
    death: float          # scale at which it fills in (∞ ⇒ never, within the filtration)
    vertices: tuple[int, ...]

    @property
    def lifetime(self) -> float:
        return self.death - self.birth


def cosine_distance_matrix(vectors: np.ndarray) -> np.ndarray:
    """1 − cosine similarity, symmetric, zero diagonal — the Rips filtration input. Zero vectors
    sit at distance 1 from everything (orthogonal), matching the backbone's convention."""
    n = vectors.shape[0]
    if n == 0:
        return np.zeros((0, 0))
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    unit = vectors / norms
    sim = np.clip(unit @ unit.T, -1.0, 1.0)
    D = 1.0 - sim
    np.fill_diagonal(D, 0.0)
    out: np.ndarray = np.maximum(D, D.T)      # exact symmetry
    return out


def persistence(D: np.ndarray, *, maxdim: int = 1) -> dict[str, Any]:
    """Vietoris–Rips persistence over a distance matrix via ripser (lazy import). Returns the raw
    ripser output (`dgms`, `cocycles`, …) — exact and deterministic for a fixed input."""
    # warrant: ripser ships no py.typed; the single lazy TDA entry point (T3)
    from ripser import ripser as _ripser  # type: ignore[import-untyped]
    result: dict[str, Any] = _ripser(D, maxdim=maxdim, distance_matrix=True, do_cocycles=True)
    return result


def _cycle_witness(D: np.ndarray, cocycle: np.ndarray, birth: float) -> tuple[int, ...]:
    """Complete a representative cocycle edge into an actual cycle at the birth scale: BFS the
    shortest path between the edge's endpoints through the graph {d ≤ birth} *excluding* the edge
    itself. Deterministic (neighbours visited in index order); falls back to the cocycle's own
    vertex set if no completing path exists (a witness is still honest evidence)."""
    verts = {int(v) for row in cocycle for v in row[:2]}
    if len(cocycle) == 0:
        return tuple(sorted(verts))
    i, j = int(cocycle[0][0]), int(cocycle[0][1])
    n = D.shape[0]
    eps = 1e-9
    # BFS i -> j over edges d <= birth, skipping the direct (i, j) edge.
    prev: dict[int, int] = {i: i}
    queue = [i]
    while queue:
        u = queue.pop(0)
        if u == j:
            break
        for v in range(n):
            if v == u or v in prev:
                continue
            if u == i and v == j:
                continue                        # the closing edge itself
            if D[u, v] <= birth + eps:
                prev[v] = u
                queue.append(v)
    if j in prev:
        path = [j]
        while path[-1] != i:
            path.append(prev[path[-1]])
        verts.update(path)
    return tuple(sorted(verts))


def long_lived_holes(D: np.ndarray, *, min_persistence: float) -> list[Hole]:
    """The H₁ features with lifetime ≥ `min_persistence`, each with a cycle witness — the
    conceptual holes worth surfacing. Sorted longest-lived first (ties by birth), deterministic."""
    if D.shape[0] < 4:                          # a 1-cycle needs at least 4 vertices un-filled
        return []
    out = persistence(D, maxdim=1)
    dgm = out["dgms"][1]
    cocycles = out["cocycles"][1]
    holes: list[Hole] = []
    for feature_idx in range(len(dgm)):
        birth, death = float(dgm[feature_idx][0]), float(dgm[feature_idx][1])
        if not np.isfinite(death):
            death = float(np.max(D))            # persists to the end of the filtration
        if death - birth < min_persistence:
            continue
        witness = _cycle_witness(D, np.asarray(cocycles[feature_idx]), birth)
        holes.append(Hole(birth=birth, death=death, vertices=witness))
    holes.sort(key=lambda h: (-h.lifetime, h.birth, h.vertices))
    return holes
