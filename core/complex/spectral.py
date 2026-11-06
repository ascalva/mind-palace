"""Spectral & diffusion clustering (companion III §2.2) — the principled clusterer.

The bottom eigenvectors of the symmetric-normalized Laplacian are the graph Fourier basis; the
Fiedler value λ₂ is algebraic connectivity; spectral/diffusion clustering partitions by those
bottom modes. This **replaces the cosine single-linkage floor** and dissolves the chaining that
forced σ = 0.50 in F9: single-linkage merges any two notes joined by a weak bridge, whereas the
normalized cut respects global density, so a dense theme is recovered whole and a weak inter-theme
bridge is cut.

Deterministic: partial eigensolves use a fixed ARPACK start vector; k-means uses a fixed seed. No
model, no network. Clustering is done **per connected component** (distinct components are never
merged) with the eigengap heuristic choosing k within each; components smaller than `min_size` and
isolated notes are dropped, matching the single-linkage clusterer's contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import scipy.sparse as sp
from scipy.cluster.vq import kmeans2
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import eigsh

from core.complex.build import cosine_adjacency
from core.kernel.complex.laplacian import laplacian_sym

if TYPE_CHECKING:  # annotation-only; runtime import is lazy (package-init cycle, see build.py)
    from core.dreaming.cluster import Cluster, NoteVector

# Determinism + scale knobs (companion III §2.3 contracts). A fixed ARPACK start vector and a fixed
# k-means seed make every eigensolve/assignment reproducible run-to-run.
_KMEANS_SEED = 0
_EIGS_PROBE = 12               # how many bottom eigenvalues to inspect for the eigengap
_DENSE_MAX = 4                 # below this component size, use dense eigh (eigsh needs k < n-1)


def _bottom_eigen(L: sp.csr_matrix, k: int) -> tuple[np.ndarray, np.ndarray]:
    """The k smallest (algebraic) eigenpairs of a symmetric PSD Laplacian, ascending.

    Uses `scipy.sparse.linalg.eigsh` with a FIXED start vector (deterministic ARPACK); falls back
    to dense `eigh` for the tiny components where ARPACK's k < n−1 requirement can't be met.
    The start is a normalized ramp, not the uniform vector — on a regular component the uniform
    vector is exactly L_sym's kernel eigenvector, and Lanczos breaks down (zero residual) when
    started on an exact eigenvector. Any ARPACK failure falls back to dense, which is exact."""
    n = L.shape[0]
    k = max(1, min(k, n))
    if n <= _DENSE_MAX or k >= n - 1:
        vals, vecs = np.linalg.eigh(L.toarray())
        return vals[:k], vecs[:, :k]
    v0 = np.arange(1, n + 1, dtype=float)           # fixed, never an exact eigenvector in practice
    v0 /= np.linalg.norm(v0)
    try:
        vals, vecs = eigsh(L.astype(float), k=k, which="SA", v0=v0)
    except Exception:                               # ARPACK breakdown/stall — dense is exact
        vals, vecs = np.linalg.eigh(L.toarray())
        vals, vecs = vals[:k], vecs[:, :k]
    order = np.argsort(vals)
    return vals[order], vecs[:, order]


def _positive_support(A: sp.csr_matrix) -> sp.csr_matrix:
    """A copy of `A` keeping only the positive weights. scipy's `connected_components` reads an
    explicitly stored 0.0 as an edge, so a cut edge that decayed to a stored zero would hide the
    disconnection; the degrees `laplacian_sym` sees already ignore it."""
    P = sp.csr_matrix(A, copy=True)
    P.data = np.where(P.data > 0.0, P.data, 0.0)
    P.eliminate_zeros()
    return P


def _disconnected_mode(A: sp.csr_matrix, comp: np.ndarray) -> np.ndarray:
    """A unit vector orthogonal to the trivial mode that separates the first component from the
    rest. It lies in the kernel of L_sym with the isolated vertices' rows zeroed (the kernel is
    spanned by sqrt(d) on each component, taking d = 1 on an isolated vertex); LAP-4's identity
    row for an isolated vertex is what `fiedler` steps around, not a kernel direction."""
    deg = np.asarray(A.sum(axis=1)).ravel()
    root = np.sqrt(np.where(deg > 0.0, deg, 1.0))
    trivial = root / np.linalg.norm(root)
    first = np.where(comp == 0, root, 0.0)
    first /= np.linalg.norm(first)
    mode = first - float(first @ trivial) * trivial
    out: np.ndarray = mode / np.linalg.norm(mode)
    return out


def fiedler(A: sp.csr_matrix) -> tuple[float, np.ndarray]:
    """(λ₂, Fiedler vector): for a connected graph, the second eigenpair of L_sym, the algebraic
    connectivity and the smallest nontrivial mode. For a disconnected graph, 0.0 and a vector that
    separates a component from the rest; it is not L_sym's second eigenpair when a vertex is
    isolated, since that row's identity puts 1 in the spectrum (see below).
    λ₂ ≈ 0 signals a weak cut (a near-disconnection); its eigenvector bisects the graph (§2.2).

    A disconnected graph has λ₂ = 0 exactly. `laplacian_sym` gives an isolated vertex an identity
    row (LAP-4), which puts 1 (not 0) in the spectrum, so the eigensolve alone would read a graph
    cut off by one vertex as well connected. The components are counted first and a disconnected
    graph returns 0.0 with a vector that separates the first component from the rest.
    Components are counted on the positive-weight support, so a stored zero weight is no edge."""
    n = A.shape[0]
    if n < 2:
        return 0.0, np.zeros(n)
    support = _positive_support(A)
    n_comp, comp = connected_components(support, directed=False)
    if n_comp > 1:
        return 0.0, _disconnected_mode(support, comp)
    vals, vecs = _bottom_eigen(laplacian_sym(A), k=min(_EIGS_PROBE, n))
    return float(vals[1]), vecs[:, 1]


def diffusion_map(A: sp.csr_matrix, *, n_components: int = 8, t: float = 1.0) -> np.ndarray:
    """Diffusion-map coordinates: the nontrivial bottom eigenvectors of L_sym scaled by the heat
    weight e^{-tμ} (companion III §2.2). Row i is note i's position in diffusion space; Euclidean
    distance there is the diffusion distance at scale t. Deterministic."""
    n = A.shape[0]
    if n == 0:
        return np.zeros((0, 0))
    r = min(n_components, max(1, n - 1))
    vals, vecs = _bottom_eigen(laplacian_sym(A), k=r + 1)
    # drop the trivial μ₀ mode; scale the rest by the diffusion weight
    nontrivial_vals = vals[1:r + 1]
    nontrivial_vecs = vecs[:, 1:r + 1]
    weights = np.exp(-t * nontrivial_vals)
    return nontrivial_vecs * weights


def estimate_k(vals: np.ndarray, *, k_max: int) -> int:
    """Eigengap heuristic: k = the index of the largest gap among the smallest eigenvalues,
    bounded to [1, k_max]. A clean k-community graph has k small eigenvalues then a jump."""
    m = min(len(vals), k_max + 1)
    if m <= 1:
        return 1
    gaps = np.diff(vals[:m])
    return int(np.argmax(gaps) + 1)


def _spectral_labels_component(A: sp.csr_matrix, *, k_max: int) -> np.ndarray:
    """NJW spectral clustering on one connected component: pick k by eigengap, embed in the bottom
    k eigenvectors of L_sym, row-normalize, and k-means. Returns a label per node (0..k−1)."""
    n = A.shape[0]
    if n <= 2:
        return np.zeros(n, dtype=np.int64)
    probe = min(_EIGS_PROBE, n)
    vals, vecs = _bottom_eigen(laplacian_sym(A), k=probe)
    k = estimate_k(vals, k_max=min(k_max, n - 1))
    if k <= 1:
        return np.zeros(n, dtype=np.int64)
    embedding = vecs[:, :k]
    rownorm = np.linalg.norm(embedding, axis=1, keepdims=True)
    rownorm[rownorm == 0.0] = 1.0
    unit = embedding / rownorm
    _centroids, labels = kmeans2(unit, k, seed=_KMEANS_SEED, minit="++", missing="warn")
    out: np.ndarray = labels.astype(np.int64)
    return out


def spectral_labels(A: sp.csr_matrix, *, k_max: int = 8) -> np.ndarray:
    """A cluster label per node over the whole graph: connected components are clustered
    independently (never merged) and their labels offset into a single global labeling."""
    n = A.shape[0]
    if n == 0:
        return np.zeros(0, dtype=np.int64)
    n_comp, comp = connected_components(A, directed=False)
    labels = np.full(n, -1, dtype=np.int64)
    nxt = 0
    for c in range(n_comp):
        members = np.where(comp == c)[0]
        sub = A[members][:, members]
        sub_labels = _spectral_labels_component(sub, k_max=k_max)
        for lab in np.unique(sub_labels):
            labels[members[sub_labels == lab]] = nxt
            nxt += 1
    return labels


def louvain_labels(A: sp.csr_matrix, *, resolution: float = 1.0) -> np.ndarray:
    """Modularity (Louvain) community labels via scikit-network — a *second*, independent method
    to cross-check the spectral partition (companion III §2.3: three methods cross-checked;
    disagreement = a fragile theme). Deterministic (fixed `random_state`). Not on the live path —
    a diagnostic the strong-Dreamer pass can compare against `spectral_labels`."""
    n = A.shape[0]
    if n < 2:
        return np.zeros(n, dtype=np.int64)
    from core.typedshims.sknetwork import louvain_labels as _louvain_labels

    return _louvain_labels(A, resolution=resolution, random_state=0)


def diffusion_cluster_notes(notes: list[NoteVector], *, threshold: float = 0.62,
                            min_size: int = 2, k_max: int = 8,
                            sim_floor: float | None = None) -> list[Cluster]:
    """Diffusion/spectral clustering over note centroids — a drop-in for `cluster.cluster_notes`
    (same signature + return type) that the Dreamer/adapter can select behind the seam.

    The graph is the weighted cosine backbone with a light denoising `sim_floor` (default a third
    of `threshold`, capped at 0.15) — deliberately *below* the single-linkage cut, because spectral
    structure, not a hard threshold, separates the themes. Returns `Cluster`s of ≥ `min_size`,
    largest first (ties by first member's title), fully deterministic."""
    from core.dreaming.cluster import Cluster  # lazy: package-init cycle (see build.py)

    n = len(notes)
    if n == 0:
        return []
    floor = sim_floor if sim_floor is not None else min(0.15, threshold / 3.0)
    A = cosine_adjacency(np.asarray([nv.vector for nv in notes], dtype=np.float64),
                         sim_floor=floor)
    labels = spectral_labels(A, k_max=k_max)
    groups: dict[int, list[int]] = {}
    for i, lab in enumerate(labels):
        if lab >= 0:
            groups.setdefault(int(lab), []).append(i)
    clusters = [
        Cluster(members=tuple(notes[i] for i in idxs))
        for idxs in groups.values()
        if len(idxs) >= min_size
    ]
    clusters.sort(key=lambda c: (-c.size, c.members[0].title))
    return clusters
