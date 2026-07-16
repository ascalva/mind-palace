"""Rule SCALE — `Res(π)` carriage + comparability (bp-054 Item 1, dn-resolution-result-typing §2.2).

The additive THIRD result grade beside Inv/Rate: a value carrying its RESOLUTION RULER π. These
tests are the two halves of Rule SCALE's carriage law: (i) a π-less `Res` is unconstructable —
structural, mirroring `Rate`'s required `clock`; and the comparability law — two `Res` compare iff
their π are IDENTICAL, cross-π refused (RT-a, transport parked). The *additive guarantee* itself (no
behavior change to Inv/Rate/meet/join) is proved by `tests/unit/test_scope.py` passing UNCHANGED.
"""

from __future__ import annotations

import dataclasses

import pytest

from core.scope import Res, ResParam, res_comparable, res_under


def _pi(name: str = "sigma", lo: float = 0.55, hi: float = 0.75, grid: str = "Γ_21") -> ResParam:
    return ResParam(name=name, lo=lo, hi=hi, grid=grid)


# ── carriage: π is required, structural (Rule SCALE (i)) ──────────────────────────────────────
def test_res_carries_pi_never_a_bare_value():
    """A `Res` is structurally unconstructable without its resolution descriptor — `param` is a
    required field (mirrors `Rate.clock`; the §2.2(i) carriage law). The π-less construction is a
    TypeError, exactly as a clockless `Rate` is."""
    field_names = {f.name for f in dataclasses.fields(Res)}
    assert "param" in field_names
    with pytest.raises(TypeError):
        Res(value=0.9)          # type: ignore[call-arg]  # missing the required param — the point


def test_res_and_resparam_are_frozen():
    """Frozen ⇒ hashable + value-equal: a `Res`'s π is an immutable part of its identity (so two
    reads at the same π hash and compare equal). A non-frozen dataclass would be unhashable."""
    r1 = res_under(0.9, param=_pi())
    r2 = res_under(0.9, param=_pi())
    assert r1 == r2
    assert hash(r1) == hash(r2)


# ── res_under round-trips ─────────────────────────────────────────────────────────────────────
def test_res_under_round_trips():
    pi = _pi()
    r = res_under(0.83, param=pi)
    assert isinstance(r, Res)
    assert r.value == 0.83
    assert r.param is pi
    assert r.param == ResParam("sigma", 0.55, 0.75, "Γ_21")


# ── comparability: π-identical only (Rule SCALE) ──────────────────────────────────────────────
def test_res_comparable_true_iff_pi_identical():
    """Same π, different measured value ⇒ still comparable (comparability is over the RULER, not the
    reading — the whole point is to compare readings taken on the same ruler)."""
    a = res_under(0.9, param=_pi())
    b = res_under(0.4, param=_pi())
    assert res_comparable(a, b)


def test_res_comparable_false_across_distinct_range():
    """A change of declared range U is a different ruler — refused (a strength measured on
    [0.55,0.75] is not the same claim as one on [0.50,0.80], §2.3-3)."""
    a = res_under(0.9, param=_pi(lo=0.55, hi=0.75))
    b = res_under(0.9, param=_pi(lo=0.50, hi=0.80))
    assert not res_comparable(a, b)


def test_res_comparable_false_across_distinct_grid():
    a = res_under(0.9, param=_pi(grid="Γ_21"))
    b = res_under(0.9, param=_pi(grid="exact-partition"))
    assert not res_comparable(a, b)


def test_res_comparable_false_across_distinct_name():
    """Different parameter entirely (σ vs grain) — never comparable (the π_grain family is parked,
    §2.5; even were it live, cross-parameter transport is refused)."""
    a = res_under(0.9, param=_pi(name="sigma"))
    b = res_under(0.9, param=_pi(name="grain"))
    assert not res_comparable(a, b)
