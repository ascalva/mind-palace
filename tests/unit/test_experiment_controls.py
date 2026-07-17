"""bp-058 Item 1 — the V3 control battery.

The battery LIFTS `test_sigma_gate._compute_validation` into the harness as one importable call.
These tests pin that the lift is faithful — the three F9 criteria reproduce through the CURRENT
pipeline (noise SETTLED ≈ 0; both planted clusters reach SETTLED; tiered precision strictly beats
the best single-σ baseline) so the battery is GREEN — and that a failing battery makes
`scripts/experiment.py controls` exit non-zero (V3: controls fail ⇒ the run is INVALID). The Item-1
falsifier is a battery that reports GREEN while any bp-057 criterion is RED; the equality check
below forecloses it.
"""

from __future__ import annotations

from eval.harness.experiment import ControlOutcome, run_control_battery
from eval.harness.gate import GateValidation


def test_control_battery_is_green_on_the_current_pipeline() -> None:
    """All three §2.5 ship criteria reproduce ⇒ GREEN. This is instrument integrity: the pipeline
    that will measure run 1 passes its own controls first (§2.1 V3)."""
    outcome = run_control_battery()
    assert outcome.green
    # (i) noise ≈ 0 at SETTLED
    assert outcome.noise_settled_rate <= outcome.validation.noise_settled_max
    # (ii) both isolated planted clusters reach SETTLED
    assert outcome.planted_reached_settled
    # (iii) persistence-tiering strictly beats the best single-σ baseline
    assert outcome.tiered_precision > outcome.baseline_precision
    assert not outcome.failing_clauses()


def test_battery_matches_the_bp057_known_good_values() -> None:
    """The lift is faithful to `test_sigma_gate`'s recorded outcome on the same fixtures: noise
    SETTLED is exactly 0.0 (every star identity transient → RETAINED), tiered precision is 1.0
    (only the persistent planted structure surfaces), and the best single-σ baseline carries the
    transient FP (< 1.0). Divergence here is the battery lying — the Item-1 falsifier."""
    outcome = run_control_battery()
    assert outcome.noise_settled_rate == 0.0
    assert outcome.tiered_precision == 1.0
    assert outcome.baseline_precision < 1.0


def test_battery_recomputes_and_is_deterministic() -> None:
    """Model-free + deterministic: two calls agree on every criterion (re-driving the pipeline, not
    reading a cached constant)."""
    a = run_control_battery()
    b = run_control_battery()
    assert (a.noise_settled_rate, a.planted_reached_settled, a.tiered_precision,
            a.baseline_precision, a.grid) == (
        b.noise_settled_rate, b.planted_reached_settled, b.tiered_precision,
        b.baseline_precision, b.grid)


def test_red_battery_reports_not_green_and_names_the_failing_clause() -> None:
    """A synthetically-failed validation ⇒ `.green` False and a non-empty failing-clause list — the
    signal `scripts/experiment.py controls` turns into a non-zero exit (V3: run INVALID)."""
    red = GateValidation(noise_settled_rate=0.9, planted_reached_settled=False,
                         tiered_precision=0.4, baseline_precision=0.6)
    outcome = ControlOutcome(
        noise_settled_rate=0.9, planted_reached_settled=False, tiered_precision=0.4,
        baseline_precision=0.6, validation=red, grid=(0.55, 0.6, 0.65, 0.7, 0.75),
    )
    assert not outcome.green
    assert len(outcome.failing_clauses()) == 3
