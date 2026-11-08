"""The utility field's laws on the simulator's transcription of the model (docs/LAWS.md XV,
`eval/utility_field.py`): each law's falsifier on float64, with a control beside it where the
Lean family has one. No store is read; every draw is seeded."""

from __future__ import annotations

import math

import numpy as np
import pytest

from eval.utility_field import (
    Params,
    bounded_walk,
    ceiling,
    closed_loop,
    decay_window,
    evolve,
    floor,
    idle,
    in_box,
    is_arc,
    laplacian,
    loop_convergence,
    margin,
    nudge,
    polya_step,
    reinforced_walk,
    stationary,
    steady,
    step,
    sup_dist,
    total_variation,
    two_communities,
)

B, LAM, C, ETA = 1.0, 0.1, 0.05, 0.5


def _rng(seed: int = 7) -> np.random.Generator:
    return np.random.default_rng(seed)


def _boxed(rng: np.random.Generator, shape: tuple[int, ...], scale: float = 1.0) -> np.ndarray:
    """A field in the box (or `scale` times as far from the baseline, for the controls)."""
    half = C / LAM
    return B + scale * rng.uniform(-half, half, size=shape)


def _symmetric_boxed(rng: np.random.Generator, n: int, scale: float = 1.0) -> np.ndarray:
    u = _boxed(rng, (n, n), scale)
    return (u + u.T) / 2


# UTL-1 -----------------------------------------------------------------------------------------


def test_the_box_is_invariant_under_any_use() -> None:
    rng = _rng()
    for _ in range(200):
        u = _boxed(rng, (16,))
        use = rng.normal(scale=10.0, size=16)
        assert in_box(B, LAM, C, step(B, LAM, C, u, use))
    log = [rng.normal(scale=10.0, size=16) for _ in range(300)]
    assert in_box(B, LAM, C, evolve(B, LAM, C, np.full(16, B), log))
    assert floor(B, LAM, C) > 0  # c < b * lam


def test_control_without_decay_the_field_leaves_the_box() -> None:
    rng = _rng()
    u = np.full(16, B)
    for _ in range(300):
        u = u + np.abs(rng.normal(scale=0.1, size=16))
    assert not in_box(B, LAM, C, u)


# UTL-2 -----------------------------------------------------------------------------------------


def test_an_idle_site_returns_within_epsilon_on_the_declared_window() -> None:
    rng = _rng()
    eps = 1e-3
    n = decay_window(LAM, C, eps)
    for _ in range(50):
        u = _boxed(rng, (16,))
        assert np.all(np.abs(idle(B, LAM, C, u, n) - B) <= eps)
    # the closed form, exactly up to rounding
    u = _boxed(rng, (16,))
    for k in range(6):
        np.testing.assert_allclose(idle(B, LAM, C, u, k), B + (1 - LAM) ** k * (u - B), rtol=1e-12)


def test_arcs_form_at_a_heat_spot_and_fade_when_it_cools() -> None:
    a = 0.3
    u = np.full(4, B)
    n_form = math.ceil(math.log(1 - a * LAM / C) / math.log(1 - LAM))
    hot = steady(B, LAM, C, C, u, n_form)
    assert is_arc(B, a, hot).all()
    assert not is_arc(B, a, steady(B, LAM, C, C, u, 1)).any()
    n_fade = math.ceil(math.log(a * LAM / C) / math.log(1 - LAM)) + 1
    assert not is_arc(B, a, idle(B, LAM, C, hot, n_fade)).any()
    assert is_arc(B, a, idle(B, LAM, C, hot, 0)).all()


def test_control_a_residual_use_holds_the_field_off_the_baseline() -> None:
    u = np.full(4, ceiling(B, LAM, C))
    n = decay_window(LAM, C, 1e-3)
    held = steady(B, LAM, C, C / 2, u, n)
    assert np.all(np.abs(held - B) > 1e-3)


# UTL-3 -----------------------------------------------------------------------------------------


def test_the_stationary_distribution_stays_within_the_margin_bound() -> None:
    rng = _rng()
    theta = margin(ETA, LAM, C)
    assert 0 < theta < 1
    for _ in range(50):
        g = two_communities(rng, size=6, p_in=0.4, bridges=1)
        u = _symmetric_boxed(rng, g.n)
        eff = nudge(ETA, B, g.adj, u)
        assert np.array_equal(eff > 0, g.adj > 0)  # the support is kept
        tv = total_variation(stationary(eff), stationary(g.adj))
        assert tv <= theta / (1 - theta) + 1e-12
        ratio = stationary(eff) / stationary(g.adj)
        assert np.all(ratio <= (1 + theta) / (1 - theta) + 1e-12)
        assert np.all(ratio >= (1 - theta) / (1 + theta) - 1e-12)


def test_control_a_field_outside_the_box_breaks_the_bound() -> None:
    rng = _rng(3)
    theta = margin(ETA, LAM, C)
    broke = False
    for _ in range(200):
        g = two_communities(rng, size=6, p_in=0.4, bridges=1)
        u = _symmetric_boxed(rng, g.n, scale=8.0)
        eff = nudge(ETA, B, g.adj, u)
        if np.any(eff < 0):
            broke = True
            break
        if total_variation(stationary(eff), stationary(g.adj)) > theta / (1 - theta):
            broke = True
            break
    assert broke


# UTL-4 -----------------------------------------------------------------------------------------


def test_the_field_is_a_fold_over_the_log_and_switches_off_at_baseline() -> None:
    rng = _rng()
    l1 = [rng.normal(size=8) for _ in range(5)]
    l2 = [rng.normal(size=8) for _ in range(7)]
    u0 = _boxed(rng, (8,))
    np.testing.assert_allclose(
        evolve(B, LAM, C, u0, l1 + l2), evolve(B, LAM, C, evolve(B, LAM, C, u0, l1), l2)
    )
    g = two_communities(rng, size=5)
    np.testing.assert_array_equal(nudge(ETA, B, g.adj, np.full_like(g.adj, B)), g.adj)


# UTL-5 -----------------------------------------------------------------------------------------


def test_the_laplacian_eigenvalues_move_within_the_bound() -> None:
    rng = _rng()
    theta = margin(ETA, LAM, C)
    for _ in range(30):
        g = two_communities(rng, size=6, p_in=0.4, bridges=1)
        u = _symmetric_boxed(rng, g.n)
        base = np.sort(np.linalg.eigvalsh(laplacian(g.adj)))
        moved = np.sort(np.linalg.eigvalsh(laplacian(nudge(ETA, B, g.adj, u))))
        dmax = g.adj.sum(axis=1).max()
        assert np.max(np.abs(moved - base)) <= 2 * theta * dmax + 1e-9
        nonzero = base > 1e-9
        assert np.all(moved[nonzero] >= (1 - theta) * base[nonzero] - 1e-9)
        assert np.all(moved[nonzero] <= (1 + theta) * base[nonzero] + 1e-9)
        x = rng.normal(size=g.n)
        form = x @ laplacian(g.adj) @ x
        drift = x @ (laplacian(nudge(ETA, B, g.adj, u)) - laplacian(g.adj)) @ x
        assert abs(drift) <= theta * form + 1e-9


def test_order_is_kept_beyond_the_margin() -> None:
    rng = _rng()
    theta = margin(ETA, LAM, C)
    g = two_communities(rng, size=6)
    # every pair of edges whose structural weights are farther apart than the ratio
    # (1 + theta)/(1 - theta) = 5/3; the weights lie in [0.5, 1], so some are
    beyond = [
        (e, f) for e in g.edges for f in g.edges if (1 + theta) * g.adj[f] < (1 - theta) * g.adj[e]
    ]
    assert beyond
    for _ in range(100):
        u = _symmetric_boxed(rng, g.n)
        eff = nudge(ETA, B, g.adj, u)
        for e, f in beyond:
            assert eff[f] < eff[e]


def test_control_outside_the_box_the_eigenvalues_move_past_the_bound() -> None:
    rng = _rng(5)
    theta = margin(ETA, LAM, C)
    g = two_communities(rng, size=6, p_in=0.4, bridges=1)
    base = np.sort(np.linalg.eigvalsh(laplacian(g.adj)))
    broke = False
    for _ in range(200):
        u = _symmetric_boxed(rng, g.n, scale=4.0)
        moved = np.sort(np.linalg.eigvalsh(laplacian(nudge(ETA, B, g.adj, u))))
        nonzero = base > 1e-9
        if np.any(moved[nonzero] < (1 - theta) * base[nonzero] - 1e-9):
            broke = True
            break
    assert broke


# UTL-6 -----------------------------------------------------------------------------------------


def test_the_closed_loop_contracts_below_the_rate() -> None:
    rng = _rng()
    gain = 0.5 * LAM

    def feedback(u: np.ndarray) -> np.ndarray:
        return gain * (u - B)

    for _ in range(50):
        u, v = _boxed(rng, (8,)), _boxed(rng, (8,))
        d = sup_dist(closed_loop(B, LAM, C, feedback, u), closed_loop(B, LAM, C, feedback, v))
        assert d <= (1 - LAM + gain) * sup_dist(u, v) + 1e-12
    row = loop_convergence(Params(b=B, lam=LAM, c=C), gain, 8, rng)
    assert row.measured_rate <= row.rate_bound + 1e-9
    assert row.fixed_points == 1


def test_control_at_the_rate_the_ceiling_is_a_second_fixed_point() -> None:
    rng = _rng()
    row = loop_convergence(Params(b=B, lam=LAM, c=C), 1.5 * LAM, 8, rng)
    assert row.fixed_points >= 2
    top = np.full(8, ceiling(B, LAM, C))
    assert sup_dist(closed_loop(B, LAM, C, lambda u: 1.5 * LAM * (u - B), top), top) < 1e-12


# The exponent and the greedy limit --------------------------------------------------------------


def test_the_exponent_decides_the_two_site_regime() -> None:
    x, y = 1.5, 1.0
    x2, y2 = polya_step(2.0, x, y)
    x1, y1 = polya_step(1.0, x, y)
    x0, y0 = polya_step(0.0, x, y)
    assert x2 / y2 > x / y
    assert x1 / y1 == pytest.approx(x / y)
    assert x0 / y0 < x / y


def test_strong_reinforcement_localizes_and_the_bounded_field_does_not() -> None:
    rng = _rng(11)
    g = two_communities(rng, size=6, p_in=0.5, bridges=1)
    strong = reinforced_walk(g, 2.0, 3000, rng)
    bounded = bounded_walk(g, Params(b=B, lam=LAM, c=C, eta=ETA), 3000, rng)
    theta = margin(ETA, LAM, C)
    assert strong.top_edge_share > 0.9  # one edge carries almost every step
    assert bounded.top_edge_share < 0.2
    assert bounded.nodes_visited == g.n
    # the bounded walk's stationary law is within the bound at every time; its empirical measure
    # over 3000 steps is well inside the control's concentration
    assert bounded.tv < strong.tv
    assert theta / (1 - theta) < 0.5
