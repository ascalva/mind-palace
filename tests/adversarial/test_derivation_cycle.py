"""Adversarial: a derivation cycle is refused at insert, through the store's own interface.

holistic-testing.md §1c (test_derivation_cycle_rejected). Structural guard I10: an edge that
would close a loop raises rather than corrupting the derivation DAG. Attempted via the public
`add()` path — no code patching — so this is a genuine red-team attempt, not a white-box poke.
"""

from __future__ import annotations

import pytest
from fixtures.stores import derived_store

from core.stores.derived import DREAM, DerivationCycleError, _artifact_id


def test_multi_hop_cycle_is_refused(tmp_path):
    s = derived_store(tmp_path)
    a = s.add(kind=DREAM, summary="A", subjects=["a"], derived_from=["dig-a"])
    b = s.add(kind=DREAM, summary="B", subjects=["b"], derived_from=[a.id])
    c = s.add(kind=DREAM, summary="C", subjects=["c"], derived_from=[b.id])
    # Re-adding A (content-addressed -> same id) with C as a parent closes A -> B -> C -> A.
    with pytest.raises(DerivationCycleError):
        s.add(kind=DREAM, summary="A", subjects=["a"], derived_from=[c.id])


def test_self_reference_is_refused(tmp_path):
    s = derived_store(tmp_path)
    self_id = _artifact_id(DREAM, None, ("a",))  # precompute the content-derived id
    with pytest.raises(DerivationCycleError):
        s.add(kind=DREAM, summary="loop", subjects=["a"], derived_from=[self_id])
