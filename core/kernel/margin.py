"""VEC-1: the margin certificate of a ranked read over float16 vectors (docs/LAWS.md, XIII).

The store holds each vector the embedder returns as float16 (dn-vector-membership-store A4), and
LanceDB scores a query against that column by rounding the query to float16 as well, through
float32, then computing `1 − cos` in float32 (measured with lancedb 0.33.0). So a ranked read is
ranked by scores that are not the exact cosines between the query and the float32 vectors. The
law (`formal/Palace/Cosine.lean::top_unchanged`) bounds how far each score can be from its exact
cosine, by `β = betaStore + betaQuery + γ`:

* `store_bound` (`betaStore`): float16 storage moves the cosine between any query and a vector of
  norm at least `ν` by at most `2η / (2 − η)`, `η = 2⁻¹¹ √(1 + d · 2⁻²⁸ / ν²)`; `4.884e-4` at
  `d = 768`. This is a hypothesis about the corpus: the embedder's vectors are unit length, and
  the store takes `ν = 1/2`.
* `query_bound` (`betaQuery`): scoring with the query's float16 rounding moves a cosine by at most
  `2 ‖q' − q‖ / (‖q‖ + ‖q'‖)`, computed here from the query itself.
* `kernel_bound` (`γ`): the float32 arithmetic of LanceDB's distance kernel is not modelled. Its
  error is a stated hypothesis, `2 (d + 4) 2⁻²⁴`, the classical bound for a dot product and two
  norms of `d` terms summed in any order, a square root and a division; measured, the kernel was
  within `5.6e-8` of the exact cosine of its float16 inputs.

When the gap between the `(k+1)`-th and the `k`-th distance exceeds `2β`, the top `k` the store
returns is the top `k` of the exact cosines: float16 storage cannot have changed it. The gap is
taken over distinct stored vectors, since two rows of one atom share its vector and its score.
"""

from __future__ import annotations

import math
from collections.abc import Hashable, Sequence
from dataclasses import dataclass

import numpy as np

U16: float = 2.0 ** -11      # binary16's unit roundoff
TAU16: float = 2.0 ** -14    # binary16's least normal magnitude
U32: float = 2.0 ** -24      # binary32's unit roundoff
NORM_FLOOR: float = 0.5      # ν: every stored vector is the float16 of a float32 vector of norm ≥ ν
# The bound itself is evaluated in float64, a few ulps from its exact value; this covers that
# evaluation many times over and stays far below anything a margin could resolve.
_EVAL_SLACK: float = 1.0 + 2.0 ** -20


def store_bound(dim: int, nu: float = NORM_FLOOR) -> float:
    """`betaStore d ν`: how far float16 storage can move a cosine (VEC-1)."""
    eta = U16 * math.sqrt(1.0 + dim * TAU16 ** 2 / nu ** 2)
    return 2.0 * eta / (2.0 - eta)


def kernel_bound(dim: int) -> float:
    """`γ`, the stated bound on the float32 distance kernel's own error (VEC-1's hypothesis)."""
    return 2.0 * (dim + 4) * U32


def query_bound(query: Sequence[float]) -> float:
    """`betaQuery q q'` for `q'` the query as LanceDB scores it: rounded to float32, then to
    float16 (VEC-1)."""
    q = np.asarray(query, dtype=np.float64)
    q16 = q.astype(np.float32).astype(np.float16).astype(np.float64)
    den = float(np.linalg.norm(q) + np.linalg.norm(q16))
    return 2.0 * float(np.linalg.norm(q16 - q)) / den if den > 0.0 else 0.0


def bound(query: Sequence[float]) -> float:
    """The margin a ranked read needs: `2 (betaStore + betaQuery + γ)` (VEC-1)."""
    d = len(query)
    return 2.0 * (store_bound(d) + query_bound(query) + kernel_bound(d)) * _EVAL_SLACK


@dataclass(frozen=True)
class Margin:
    """VEC-1's certificate for one ranked read of `k`: the gap between the best distance outside
    the top `k` and the worst inside it, over distinct stored vectors (`math.inf` when nothing
    lies outside), against the bound `2β`."""

    k: int
    gap: float
    bound: float

    @property
    def certified(self) -> bool:
        """Float16 storage cannot have changed which vectors make the top `k`."""
        return self.gap > self.bound


def certify(distances: Sequence[float], keys: Sequence[Hashable], k: int,
            query: Sequence[float]) -> Margin:
    """The certificate of the top `k` of a ranking. `distances` are the cosine distances the
    store computed, ascending, and `keys` name the stored vector each candidate is (two rows of
    one atom share a key). The candidates must hold every vector the read could rank above the
    best one outside its top `k`: a source asked for its `k + 1` best vectors holds them."""
    if k <= 0 or len(distances) <= k:
        return Margin(k=k, gap=math.inf, bound=bound(query))
    inside = set(keys[:k])
    worst = float(distances[k - 1])
    nxt = next((float(d) for d, key in zip(distances[k:], keys[k:], strict=True)
                if key not in inside), math.inf)
    return Margin(k=k, gap=nxt - worst, bound=bound(query))
