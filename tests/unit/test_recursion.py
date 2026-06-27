"""Recursion-decay bound c ≤ γ^d·g (Invariant 10). Deterministic checks; the monotonicity
property over arbitrary depths/γ is in test_properties.py."""

import pytest

from core.recursion import DEFAULT_GAMMA, decay_bound


def test_authored_leaf_is_undiscounted():
    assert decay_bound(0, grounding=1.0) == 1.0          # depth 0: c ≤ g


def test_depth_strictly_discounts():
    assert decay_bound(1) == DEFAULT_GAMMA               # γ^1
    assert decay_bound(2) == DEFAULT_GAMMA ** 2
    assert decay_bound(3) == pytest.approx(0.125)        # depth-3 is clearly subordinate (G7)


def test_grounding_scales_the_ceiling():
    assert decay_bound(2, grounding=0.4) == pytest.approx((DEFAULT_GAMMA ** 2) * 0.4)


def test_gamma_must_contract():
    with pytest.raises(ValueError):
        decay_bound(1, gamma=1.0)                         # γ=1 would not decay
    with pytest.raises(ValueError):
        decay_bound(1, gamma=0.0)
