"""The metric registry — the single namespace, fail-closed, with the built families registered
(dn-evaluation-harness §2.5, bp-042). Also proves the `eval/metrics.py` absorption is additive
(signatures unchanged, module still importable)."""

from __future__ import annotations

import pytest

from eval.harness import registry
from eval.harness.registry import MetricSpec, get, is_registered, register


def test_four_built_families_resolve_with_correct_declarations() -> None:
    """Each built family resolves with the right type_tag, source instrument (catalog row), and
    guardrail eligibility (§6). golden / drift / f9 are Inv; telemetry wall is a Rate(wall)."""
    golden = get("golden_recall")
    assert golden.type_tag == "Inv"
    assert golden.source_instrument == "row1-golden-recall"
    assert golden.guardrail_eligible is True

    drift = get("drift_D")
    assert drift.type_tag == "Inv"
    assert drift.source_instrument == "row2-drift-gauge"
    assert drift.guardrail_eligible is True

    f9 = get("f9_composite")
    assert f9.type_tag == "Inv"
    assert f9.source_instrument == "row5-f9-suite"

    wall = get("telemetry_wall")
    assert wall.type_tag == "Rate(wall)"          # a Rate carries its clock (Rule CLOCK, §2.3)
    assert wall.source_instrument == "row4-telemetry"


def test_only_recall_and_drift_are_guardrail_eligible() -> None:
    """The always-on guardrail set (§2.5) draws from guardrail-eligible metrics: golden recall +
    drift D. Diagnostics (overlap, f9 components, telemetry) are NOT guardrails."""
    eligible = {name for name, spec in registry.REGISTRY.items() if spec.guardrail_eligible}
    assert eligible == {"golden_recall", "drift_D"}


def test_get_is_fail_closed_on_unregistered_name() -> None:
    """No ad-hoc metrics: an unregistered name raises rather than silently resolving."""
    assert not is_registered("made_up_metric")
    with pytest.raises(KeyError):
        get("made_up_metric")


def test_register_rejects_duplicate_name() -> None:
    """The single namespace refuses a collision."""
    with pytest.raises(ValueError):
        register(MetricSpec("golden_recall", "Inv", "row1-golden-recall", "x", "regression", True))


def test_regression_is_the_default_assertion_shape() -> None:
    """Regression-first at current scale (§2.5): no built metric ships an absolute threshold yet."""
    assert all(spec.assertion_shape == "regression" for spec in registry.REGISTRY.values())


def test_metrics_absorption_is_additive() -> None:
    """The absorption re-registers, it does not rewrite: metrics.py's three functions keep their
    signatures and stay importable (the bit-identical-import falsifier)."""
    from eval.metrics import mean_cosine_distance, recall_at_k, set_overlap

    assert recall_at_k({"a"}, ["a", "b"], 2) == 1.0
    assert set_overlap({"a"}, ["a"], 1) == 1.0
    assert mean_cosine_distance([0.2, 0.4]) == pytest.approx(0.3)
    # the golden-recall family the functions are registered under exists in the namespace
    assert is_registered("golden_recall")
