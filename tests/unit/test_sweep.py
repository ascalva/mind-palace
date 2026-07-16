"""The sweep engine's pure surfaces (bp-049): spec parsing (Item 13) + the §8 selection instrument
(Item 14) over SYNTHETIC curves — no runner, no store.

The selection falsifiers (plan §8, the acceptance killers):
  * a flat-topped curve selects the PLATEAU CENTER, not the first max (the anti-peak-chasing rule);
  * two equal plateaus tie-break toward the value nearest `current`;
  * an inadmissible cell holding the objective max is EXCLUDED (guardrails lexicographically prior);
  * an all-inadmissible curve emits NO selection (None) — the engine then refuses a proposal;
  * a selected value is always a grid point in `[lo, hi]`.
"""

from __future__ import annotations

import pytest

from eval.harness.sweep import (
    CurvePoint,
    SweepSpecError,
    parse_spec_text,
    select,
)


def _pts(values_means_adm: list[tuple[float, float, bool]]) -> list[CurvePoint]:
    """Build an ascending-grid curve: (value, mean, admissible) triples become CurvePoints whose
    grid_index is their position (so grid adjacency == list adjacency here)."""
    return [
        CurvePoint(value=v, mean=m, halfwidth=0.0, admissible=a, grid_index=i, n_seeds=1)
        for i, (v, m, a) in enumerate(values_means_adm)
    ]


# --------------------------------------------------------------------------------------------------
# §8 selection instrument
# --------------------------------------------------------------------------------------------------


def test_flat_top_selects_plateau_center_not_first_max() -> None:
    """THE CARDINAL FALSIFIER: a knife-edge singleton max (1.0) coexists with a strictly WIDER
    near-optimal plateau (0.99 × 3). `select` must return the plateau CENTER, never the singleton —
    peak-chasing over stability is exactly the §2.6/§8 failure."""
    # grid indices:      0     1(max)  2     3     4     5     6
    curve = _pts([(0.0, 0.50, True), (0.1, 1.00, True), (0.2, 0.60, True),
                  (0.3, 0.99, True), (0.4, 0.99, True), (0.5, 0.99, True), (0.6, 0.55, True)])
    got = select(curve, current=0.0, epsilon=0.02, direction="maximize", grid_size=7)
    assert got == 0.4, "the 3-wide 0.99 plateau's center (index 4) wins, not the 1.0 singleton"
    # sanity: the singleton max would have been 0.1 — prove we did NOT pick it.
    assert got != 0.1


def test_two_equal_plateaus_tiebreak_toward_current() -> None:
    """Two equal-length near-optimal plateaus → pick the one whose center is nearest `current`."""
    # two 3-wide plateaus at 0.99, centers at value 0.2 (idx2) and 0.6 (idx6); a dip between.
    curve = _pts([(0.0, 0.5, True),
                  (0.1, 0.99, True), (0.2, 0.99, True), (0.3, 0.99, True),  # plateau A center=0.2
                  (0.4, 0.5, True),
                  (0.5, 0.99, True), (0.6, 0.99, True), (0.7, 0.99, True)])  # plateau B center=0.6
    assert select(curve, current=0.0, epsilon=0.01, direction="maximize", grid_size=8) == 0.2
    assert select(curve, current=1.0, epsilon=0.01, direction="maximize", grid_size=8) == 0.6


def test_inadmissible_max_is_excluded() -> None:
    """A guardrail-failed cell holding the objective max is dropped BEFORE the argmax (guardrails
    lexicographically prior); the winner comes from the admissible plateau."""
    curve = _pts([(0.0, 0.5, True),
                  (0.1, 1.00, False),  # the objective MAX, but INADMISSIBLE — must be excluded
                  (0.2, 0.90, True), (0.3, 0.90, True), (0.4, 0.90, True)])  # admissible plateau
    got = select(curve, current=0.0, epsilon=0.02, direction="maximize", grid_size=5)
    assert got == 0.3, "the admissible 0.90 plateau center wins; the inadmissible 1.0 is excluded"


def test_all_inadmissible_returns_none() -> None:
    curve = _pts([(0.0, 0.9, False), (0.1, 1.0, False), (0.2, 0.8, False)])
    assert select(curve, current=0.1, epsilon=0.05, direction="maximize", grid_size=3) is None


def test_selected_value_is_a_grid_point_in_bounds() -> None:
    """Whatever wins is one of the input grid values (so ProposedChange.resolve won't raise)."""
    curve = _pts([(0.55, 0.7, True), (0.60, 0.9, True), (0.65, 0.9, True),
                  (0.70, 0.9, True), (0.75, 0.6, True)])
    got = select(curve, current=0.55, epsilon=0.02, direction="maximize", grid_size=5)
    assert got in {0.55, 0.60, 0.65, 0.70, 0.75}
    assert 0.55 <= float(got) <= 0.75  # type: ignore[arg-type]


def test_minimize_direction_selects_low_plateau() -> None:
    """drift_D minimizes: M is the smallest mean; the near-optimal plateau is the LOW one."""
    curve = _pts([(0.0, 0.9, True),
                  (0.1, 0.10, True), (0.2, 0.10, True), (0.3, 0.10, True),  # low plateau (idx1-3)
                  (0.4, 0.90, True),  # a high dip separates the plateau from the singleton
                  (0.5, 0.05, True)])  # a singleton even-lower knife-edge (idx5), non-adjacent
    got = select(curve, current=0.0, epsilon=0.06, direction="minimize", grid_size=6)
    assert got == 0.2, "the wide low plateau center wins over the 0.05 singleton (anti-peak-chase)"


def test_three_point_grid_degenerates_to_argmax() -> None:
    """A ≤3-point grid has no meaningful adjacency (§8): selection is the argmax, tie-break near."""
    curve = _pts([(0.55, 0.7, True), (0.65, 0.9, True), (0.75, 0.8, True)])
    assert select(curve, current=0.55, epsilon=0.0, direction="maximize", grid_size=3) == 0.65


def test_adjacency_is_grid_adjacency_a_removed_cell_breaks_a_plateau() -> None:
    """Two near-optimal points separated by a NON-near-optimal grid cell are NOT one plateau — the
    longer contiguous run wins."""
    # idx 1 and idx 3 are near-optimal but idx 2 dips below ε → they are two singleton runs; the
    # contiguous run at idx 5,6 (len 2) is longest.
    curve = _pts([(0.0, 0.5, True),
                  (0.1, 1.0, True), (0.2, 0.5, True), (0.3, 1.0, True),
                  (0.4, 0.5, True),
                  (0.5, 0.99, True), (0.6, 0.99, True)])
    got = select(curve, current=0.6, epsilon=0.02, direction="maximize", grid_size=7)
    assert got == 0.6, "the contiguous 2-wide run beats the two isolated singleton maxima"


# --------------------------------------------------------------------------------------------------
# Item 13 — spec parsing (fail-closed)
# --------------------------------------------------------------------------------------------------


_FULL_SPEC = """
[sweep.demo]
levers = { dream_rnd_sigma = "full" }
resolution = 5
pipelines = ["phase7", "dream_v2"]
corpus = "mirror-snapshot"
seeds = 3
metrics = ["golden_recall", "drift_D"]
objective = "golden_recall"
guardrails = []
mode = "propose"
"""


def test_parse_full_spec_and_grid() -> None:
    spec = parse_spec_text(_FULL_SPEC)
    assert spec.name == "demo"
    assert spec.lever.name == "dream_rnd_sigma"
    assert spec.objective == "golden_recall"
    assert spec.direction == "maximize"
    assert spec.select_pipeline == "dream_v2"  # defaults to the last pipeline (finding-0089)
    grid = spec.grid()
    assert grid[0] == spec.lever.lo and grid[-1] == spec.lever.hi
    assert len(grid) == 5
    assert all(spec.lever.lo <= g <= spec.lever.hi for g in grid)


def test_mode_auto_raises_e3b() -> None:
    bad = _FULL_SPEC.replace('mode = "propose"', 'mode = "auto"')
    with pytest.raises(SweepSpecError, match="E3b"):
        parse_spec_text(bad)


def test_unregistered_objective_fails_closed() -> None:
    bad = _FULL_SPEC.replace('objective = "golden_recall"', 'objective = "not_a_metric"')
    with pytest.raises(SweepSpecError, match="not a registered metric"):
        parse_spec_text(bad)


def test_unknown_lever_fails_closed() -> None:
    bad = _FULL_SPEC.replace("dream_rnd_sigma", "nonexistent_lever")
    with pytest.raises(KeyError):
        parse_spec_text(bad)


def test_explicit_out_of_bounds_grid_point_raises_before_any_run() -> None:
    """An explicit grid list with a value outside the lever's hard bounds raises at grid()-build
    time — BEFORE any cell is driven (the §7 falsifier: a point outside [lo, hi] never reaches a
    run)."""
    bad = _FULL_SPEC.replace('{ dream_rnd_sigma = "full" }',
                             "{ dream_rnd_sigma = [0.55, 0.60, 0.99] }")  # 0.99 > hi (0.75)
    spec = parse_spec_text(bad)
    with pytest.raises(ValueError, match="outside hard bounds"):
        spec.grid()


def test_explicit_in_bounds_list_grid() -> None:
    ok = _FULL_SPEC.replace('{ dream_rnd_sigma = "full" }',
                            "{ dream_rnd_sigma = [0.55, 0.65, 0.75] }")
    spec = parse_spec_text(ok)
    assert spec.grid() == [0.55, 0.65, 0.75]


def test_select_pipeline_must_be_listed() -> None:
    bad = _FULL_SPEC.replace('mode = "propose"', 'select_pipeline = "ghost"\nmode = "propose"')
    with pytest.raises(SweepSpecError, match="select_pipeline"):
        parse_spec_text(bad)
