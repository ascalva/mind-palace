"""Hypothesis strategies for small weighted graphs, shared by the law falsifiers of the Laplacian
and Hodge families (`tests/property/test_laplacian_laws.py`, `tests/property/test_hodge_laws.py`).
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from hypothesis import strategies as st


@st.composite
def graphs(draw: st.DrawFn, *, signed: bool = False, max_n: int = 9) -> sp.csr_matrix:
    """A symmetric, zero-diagonal adjacency on 1 to `max_n` vertices, each pair an edge or not,
    weights in [0.01, 1]; of either sign when `signed`."""
    n = draw(st.integers(min_value=1, max_value=max_n))
    a = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            if draw(st.booleans()):
                w = draw(st.floats(min_value=0.01, max_value=1.0))
                a[i, j] = a[j, i] = -w if signed and draw(st.booleans()) else w
    return sp.csr_matrix(a)
