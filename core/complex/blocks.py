"""Degree-corrected stochastic block model — themes *with* a posterior (companion III §6.2; H7).

The spectral clusterer gives a point partition and makes *you* pick k. The SBM is generative: it
says how likely each note belongs to each theme (a **posterior**, not a guess) and how many themes
the data support (**model selection**). Degree correction (Karrer–Newman) keeps a prolific topic
from swallowing the graph.

Light implementation, per the BUILD §2.2 disposition ("custom, ~200 lines, VEM; keep it thin"):
a mean-field variational EM for the *Poisson* DC-SBM —

    E:  log q_i(r) ∝ log π_r + Σ_j A_ij Σ_s q_js log ω_rs − d_i Σ_s κ_s ω_rs
    M:  m_rs = qᵀA q,   κ_r = Σ_i q_ir d_i,   ω_rs = m_rs/(κ_r κ_s),   π_r = n_r/n

initialized from the deterministic diffusion embedding (fixed-seed k-means), run a fixed number of
rounds — fully deterministic. Model selection by an ICL/BIC-style penalized complete-data
likelihood (the Karrer–Newman objective minus a parameter-count penalty); the exact penalty is a
declared engineering choice validated on planted graphs (the block-recovery property test), not a
derived MDL bound — stated honestly.

The line held (§6.3): the posterior organizes the *graph* (membership), it never certifies a
*thought*. Deterministic; model-free; no network.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

from core.complex.spectral import diffusion_map

_EPS = 1e-12
_VEM_ROUNDS = 30                # fixed iteration budget — deterministic, cheap at corpus scale


@dataclass(frozen=True)
class SBMResult:
    """The fitted blocks: hard labels, the n×k membership posterior, the model-selected k, and
    the ICL score per candidate k (the model-selection trace, for the cross-check)."""

    labels: np.ndarray            # hard assignment = argmax posterior
    posterior: np.ndarray         # n×k, rows sum to 1 — membership WITH confidence
    k: int                        # model-selected block count
    icl_by_k: dict[int, float]


def _init_posterior(A: sp.csr_matrix, k: int) -> np.ndarray:
    """Deterministic soft init: fixed-seed k-means over the diffusion embedding, softened."""
    from scipy.cluster.vq import kmeans2
    n = A.shape[0]
    if k == 1:
        return np.ones((n, 1))
    emb = diffusion_map(A, n_components=min(k, max(1, n - 1)))
    if emb.shape[1] == 0:
        emb = np.zeros((n, 1))
    _c, labels = kmeans2(emb, k, seed=0, minit="++", missing="warn")
    q = np.full((n, k), 0.05 / max(k - 1, 1))
    q[np.arange(n), labels] = 0.95
    posterior: np.ndarray = q / q.sum(axis=1, keepdims=True)
    return posterior


def _vem(A: sp.csr_matrix, k: int) -> np.ndarray:
    """Mean-field VEM for the Poisson DC-SBM at fixed k. Returns the membership posterior q."""
    n = A.shape[0]
    d = np.asarray(A.sum(axis=1)).ravel()
    q = _init_posterior(A, k)
    for _ in range(_VEM_ROUNDS):
        # --- M: block masses under q ---
        m = q.T @ (A @ q)                        # k×k expected inter-block edge weight
        kappa = q.T @ d                          # expected block degree
        omega = m / np.maximum(np.outer(kappa, kappa), _EPS)
        log_omega = np.log(np.maximum(omega, _EPS))
        pi = np.maximum(q.sum(axis=0) / n, _EPS)
        # --- E: mean-field update ---
        logq = (A @ q) @ log_omega.T             # Σ_j A_ij Σ_s q_js log ω_rs   (n×k)
        logq -= np.outer(d, omega @ kappa)       # − d_i Σ_s κ_s ω_rs
        logq += np.log(pi)
        logq -= logq.max(axis=1, keepdims=True)  # stabilize
        q_new = np.exp(logq)
        q_new /= q_new.sum(axis=1, keepdims=True)
        if np.allclose(q_new, q, atol=1e-10):
            q = q_new
            break
        q = q_new
    return q


def _kn_objective(A: sp.csr_matrix, labels: np.ndarray, k: int) -> float:
    """The Karrer–Newman DC-SBM complete-data objective at a hard labeling:
    L = Σ_rs m_rs · log(m_rs / (κ_r κ_s)), with 0·log0 = 0."""
    onehot = np.zeros((A.shape[0], k))
    onehot[np.arange(A.shape[0]), labels] = 1.0
    m = onehot.T @ (A @ onehot)
    kappa = onehot.T @ np.asarray(A.sum(axis=1)).ravel()
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = m / np.maximum(np.outer(kappa, kappa), _EPS)
        terms = np.where(m > 0.0, m * np.log(np.maximum(ratio, _EPS)), 0.0)
    return float(terms.sum())


def sbm(A: sp.csr_matrix, *, k_max: int = 8) -> SBMResult:
    """Fit the DC-SBM for k = 1..k_max and select k by the penalized objective (ICL/BIC style):

        ICL(k) = L_KN(k) − ½·[k(k+1)/2]·ln W − ½·(k−1)·ln n,      W = total edge weight.

    Returns the winning k's posterior + hard labels. Deterministic end to end."""
    A = A.tocsr().astype(float)
    n = A.shape[0]
    if n == 0:
        return SBMResult(labels=np.zeros(0, dtype=np.int64), posterior=np.zeros((0, 1)),
                         k=1, icl_by_k={1: 0.0})
    W = max(float(A.sum()), _EPS)
    best: tuple[float, int, np.ndarray] | None = None
    icl_by_k: dict[int, float] = {}
    for k in range(1, max(1, min(k_max, n)) + 1):
        q = _vem(A, k)
        labels = q.argmax(axis=1)
        # renumber to the occupied blocks only (an empty block is not a theme)
        occupied = np.unique(labels)
        k_eff = len(occupied)
        remap = {int(old): i for i, old in enumerate(occupied)}
        labels = np.asarray([remap[int(x)] for x in labels], dtype=np.int64)
        icl = (_kn_objective(A, labels, k_eff)
               - 0.5 * (k_eff * (k_eff + 1) / 2) * np.log(W)
               - 0.5 * (k_eff - 1) * np.log(max(n, 2)))
        icl_by_k[k] = float(icl)
        if best is None or icl > best[0] + 1e-12:
            best = (float(icl), k_eff, q[:, occupied] / np.maximum(
                q[:, occupied].sum(axis=1, keepdims=True), _EPS))
    assert best is not None
    _score, k_star, posterior = best
    return SBMResult(labels=posterior.argmax(axis=1).astype(np.int64),
                     posterior=posterior, k=k_star, icl_by_k=icl_by_k)
