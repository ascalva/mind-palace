"""Blast-radius drift — effector reach as a drift Axis against a frozen anchor (Track G, item G7).

These pin the metric shape §4 calls for: reach summarizes how far the hands proposed to reach (mean
reversibility band); it is one-sided (reaching LESS than the anchor is not drift) and monotone
(reaching further deteriorates more); rising reach past the blessed tolerance trips the band; the
axis IS an `eval.drift.Axis` (composes with family 4); and the whole thing reads the effect ledger
and reports — detection only, never feeding the self-mod gate.
"""

from __future__ import annotations

from eval.drift import Axis
from eval.effector_drift import (
    EffectorAnchor,
    effector_reach_axis,
    measure_effector_drift,
    reach_from_ledger,
    reach_of,
)
from ops.effect_ledger import EffectLedger
from ops.effects import ReversibilityClass

S, R, IRR = (
    ReversibilityClass.SENSING,
    ReversibilityClass.REVERSIBLE,
    ReversibilityClass.IRREVERSIBLE,
)


def test_empty_history_sits_at_the_origin():
    rep = measure_effector_drift([])
    assert rep.reach.n == 0 and rep.reach.mean_reach == 0.0
    assert rep.deterioration == 0.0 and rep.within_tolerance      # no proposals is not drift


def test_reach_summary_shape():
    reach = reach_of([S, S, R, IRR])
    assert reach.mean_reach == (0 + 0 + 1 + 2) / 4                # 0.75
    assert reach.irreversible_fraction == 0.25
    assert reach.max_class == 2 and reach.n == 4


def test_reach_is_one_sided_and_monotone():
    anchor = EffectorAnchor(baseline_reach=0.5, reach_tol=0.5)
    # Reaching LESS than the anchor is not drift (one-sided): all-sensing mean 0 < 0.5 ⇒ 0.
    low = measure_effector_drift([S, S, S], anchor)
    assert low.deterioration == 0.0 and low.within_tolerance
    # Reaching further deteriorates more (monotone in reach).
    mid = measure_effector_drift([S, R, R], anchor)               # mean ≈ 0.67 > 0.5
    high = measure_effector_drift([R, IRR, IRR], anchor)         # mean ≈ 1.67
    assert mid.deterioration > 0.0
    assert high.deterioration > mid.deterioration


def test_rising_reach_trips_the_blessed_band():
    anchor = EffectorAnchor(baseline_reach=0.0, reach_tol=0.5)
    calm = measure_effector_drift([S, S, S, R], anchor)           # mean 0.25 ≤ 0.5 ⇒ within
    assert calm.within_tolerance
    surge = measure_effector_drift([IRR, IRR, R], anchor)        # mean ≈ 1.67 ⇒ ≫ 1 tol-unit
    assert not surge.within_tolerance


def test_the_axis_is_a_drift_axis_and_the_math_matches():
    # "Composes with the drift metric" is literal: it returns the SAME Axis type, with the same
    # one-sided, tolerance-normalized deterioration — so the A2 report can append it.
    anchor = EffectorAnchor(baseline_reach=0.5, reach_tol=0.5)
    axis = effector_reach_axis(reach_of([R, IRR]), anchor)        # mean 1.5
    assert isinstance(axis, Axis) and axis.name == "effector_reach"
    assert axis.higher_is_better is False
    assert axis.deterioration() == (1.5 - 0.5) / 0.5             # 2.0 tolerance-units


def test_reach_read_from_the_effect_ledger(tmp_path):
    lg = EffectLedger(tmp_path / "effects.sqlite")
    lg.propose("sense_fetch", S)
    lg.propose("draft_reply", R)
    lg.propose("send_email", IRR)
    rep = reach_from_ledger(lg)                       # reads .all(); anchor from baseline
    assert rep.reach.n == 3 and rep.reach.max_class == 2
    assert rep.reach.mean_reach == (0 + 1 + 2) / 3
    lg.close()
