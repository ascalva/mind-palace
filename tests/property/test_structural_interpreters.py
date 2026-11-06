"""Property tests for the structural instruments (H4–H7; BUILD §6.1).

  * Curvature sign     — a planted bridge edge is negative Forman; a triangle-dense edge positive.
  * Persistence stability — the H₁ diagram moves no more than the input perturbation
    (bottleneck stability, checked feature-wise on a planted hole).
  * Alignment monotonicity — adding an authored support edge never lowers the grounding cut.
  * SBM recovery       — planted block structure is recovered (count + co-membership).
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from hypothesis import given, settings
from hypothesis import strategies as st

from core.complex.blocks import sbm
from core.complex.cut import grounding_cut
from core.complex.topology import long_lived_holes
from core.kernel.complex.curvature import forman
from core.kernel.complex.support import grounding_with_support
from core.kernel.selfcheck import grounding_score

# --- H4: curvature sign on planted structure -------------------------------------

@settings(deadline=None, max_examples=25)
@given(m=st.integers(min_value=3, max_value=8), seed=st.integers(min_value=0, max_value=2**16))
def test_planted_bridge_is_negative_and_clique_edges_positive(m, seed):
    """Two m-cliques joined by one bridge edge: the bridge must be the unique minimum-curvature
    edge and strictly negative for every m >= 3 (CRV-2: 4 - 2m <= -2); intra-clique edges
    are triangle-rich and strictly greater."""
    n = 2 * m
    A = np.zeros((n, n))
    for base in (0, m):
        for i in range(base, base + m):
            for j in range(i + 1, base + m):
                A[i, j] = A[j, i] = 1.0
    A[m - 1, m] = A[m, m - 1] = 1.0                      # the bridge
    del seed                                             # topology is m-determined; seed unused
    curv = forman(sp.csr_matrix(A))
    bridge = curv[(m - 1, m)]
    intra = [v for (i, j), v in curv.items() if (i, j) != (m - 1, m)]
    assert bridge == 4 - 2 * m                           # closed form: no triangles through it
    assert all(bridge < v for v in intra)                # strictly the least-curved edge
    assert bridge < 0                                    # CRV-2: negative from m = 3 (4 - 2m = -2)
    assert bridge <= -2                                  # and by at least 2 at every m in range


# --- H5: persistence stability ----------------------------------------------------

def _ring_distances(n: int, jitter: np.ndarray | None = None) -> np.ndarray:
    """A planted n-ring (adjacent notes close, everything else far) — one clean H₁ hole."""
    D = np.full((n, n), 0.9)
    np.fill_diagonal(D, 0.0)
    for i in range(n):
        j = (i + 1) % n
        D[i, j] = D[j, i] = 0.3
    if jitter is not None:
        D = D + jitter
        D = np.maximum((D + D.T) / 2.0, 0.0)
        np.fill_diagonal(D, 0.0)
    return D


@settings(deadline=None, max_examples=25)
@given(n=st.integers(min_value=4, max_value=9), seed=st.integers(min_value=0, max_value=2**16),
       eps=st.floats(min_value=0.0, max_value=0.05))
def test_persistence_is_stable_under_perturbation(n, seed, eps):
    """Bottleneck stability: perturbing every distance by <= eps moves the planted hole's
    birth/death by <= eps (checked feature-wise — the diagram cannot jump)."""
    base = _ring_distances(n)
    holes = long_lived_holes(base, min_persistence=0.2)
    assert len(holes) == 1                               # exactly the planted ring hole
    rng = np.random.default_rng(seed)
    jitter = rng.uniform(-eps, eps, size=base.shape)
    perturbed_holes = long_lived_holes(_ring_distances(n, jitter), min_persistence=0.2)
    assert len(perturbed_holes) == 1                     # a stable feature does not vanish
    h0, h1 = holes[0], perturbed_holes[0]
    tol = eps + 1e-9
    assert abs(h0.birth - h1.birth) <= tol
    assert abs(h0.death - h1.death) <= tol


# --- H6: alignment monotonicity ----------------------------------------------------

@settings(deadline=None, max_examples=40)
@given(n_refs=st.integers(min_value=0, max_value=6), extra=st.integers(min_value=1, max_value=4))
def test_adding_authored_support_never_lowers_the_grounding_cut(n_refs, extra):
    authored = {f"a{i}" for i in range(12)}
    before_refs = tuple(f"a{i}" for i in range(n_refs))
    after_refs = tuple(f"a{i}" for i in range(n_refs + extra))
    before = grounding_cut({"art": before_refs}, "art", authored)
    after = grounding_cut({"art": after_refs}, "art", authored)
    assert after >= before                               # metamorphic: support only adds capacity
    assert before == float(n_refs)                       # unit-capacity refs: cut = ref count


def test_grounding_cut_finds_the_chain_bottleneck():
    """Multi-hop grounding is limited by its narrowest layer: an artifact resting on one
    intermediate parent has cut 1 no matter how well the PARENT is grounded."""
    authored = {"a1", "a2", "a3"}
    chain = {"art": ("mid",), "mid": ("a1", "a2", "a3")}
    assert grounding_cut(chain, "art", authored) == 1.0
    assert grounding_cut(chain, "mid", authored) == 3.0


# --- H7: SBM block recovery ----------------------------------------------------------

def _planted_blocks(k_true: int, n_per: int, p_in: float, p_out: float,
                    seed: int) -> tuple[sp.csr_matrix, np.ndarray]:
    rng = np.random.default_rng(seed)
    n = n_per * k_true
    A = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            p = p_in if i // n_per == j // n_per else p_out
            if rng.random() < p:
                A[i, j] = A[j, i] = 1.0
    return sp.csr_matrix(A), np.repeat(np.arange(k_true), n_per)


def _co_membership_agreement(a: np.ndarray, b: np.ndarray) -> float:
    """Label-permutation-invariant agreement: do pairs land together/apart the same way?"""
    return float(((a[:, None] == a[None, :]) == (b[:, None] == b[None, :])).mean())


def test_sbm_recovers_planted_blocks():
    for k_true, n_per, seed in [(2, 12, 3), (3, 10, 7), (4, 8, 11)]:
        A, true = _planted_blocks(k_true, n_per, p_in=0.85, p_out=0.03, seed=seed)
        res = sbm(A, k_max=8)
        assert res.k == k_true, f"k*={res.k} != planted {k_true} (seed {seed})"
        assert _co_membership_agreement(true, res.labels) >= 0.95
        assert np.allclose(res.posterior.sum(axis=1), 1.0)   # rows are distributions
        # deterministic end to end
        res2 = sbm(A, k_max=8)
        assert res2.k == res.k and np.array_equal(res2.labels, res.labels)


def test_sbm_on_a_blockless_graph_selects_one_block():
    """No planted structure (uniform density) ⇒ model selection must NOT invent themes."""
    A, _ = _planted_blocks(1, 20, p_in=0.5, p_out=0.5, seed=5)
    assert sbm(A, k_max=8).k == 1


# --- H8: multi-path grounding reduces exactly to the flat score on flat evidence ------

@settings(deadline=None, max_examples=60)
@given(evidence=st.lists(
    st.sampled_from(["a0", "a1", "a2", "a3", "ghost1", "ghost2", "ghost3"]),
    min_size=0, max_size=8))
def test_grounding_with_support_flat_equality(evidence):
    """The behavior-preservation guarantee: with no interpreted refs in play (today's only live
    case), the noisy-OR-generalized g equals `grounding_score` exactly — the confidence law and
    every existing adjudication are untouched by the H8 seam."""
    authored = {"a0", "a1", "a2", "a3"}
    assert grounding_with_support(evidence, {}, authored) == grounding_score(evidence, authored)
