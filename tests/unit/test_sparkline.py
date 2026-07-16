"""The sparkline's contract (bp-044 Item 8): deterministic, degenerate-safe, pure.

Falsifier (plan §7 Item 8): the same input yields different output across calls (non-determinism),
or a degenerate series (empty / single / constant) raises instead of rendering.
"""

from __future__ import annotations

from eval.harness.sparkline import _BARS, sparkline


def test_monotone_rising_series_is_nondecreasing_and_right_length() -> None:
    out = sparkline([0, 1, 2, 3, 4, 5, 6, 7, 8])
    assert len(out) == 9
    # every glyph is a known bar, and the row never steps DOWN (input is monotone rising)
    idxs = [_BARS.index(ch) for ch in out]
    assert all(a <= b for a, b in zip(idxs, idxs[1:], strict=False))
    assert idxs[0] == 0 and idxs[-1] == len(_BARS) - 1   # spans the full band


def test_empty_series_is_empty_string() -> None:
    assert sparkline([]) == ""


def test_single_value_is_a_single_flat_bar() -> None:
    out = sparkline([42.0])
    assert out == _BARS[0]
    assert len(out) == 1


def test_constant_series_is_a_flat_row() -> None:
    out = sparkline([3.3, 3.3, 3.3, 3.3])
    assert out == _BARS[0] * 4
    assert len(set(out)) == 1               # genuinely flat — no phantom variation


def test_deterministic_same_input_same_output() -> None:
    vals = [0.1, 5.0, 2.2, 9.9, 3.3, 3.3, 7.0]
    first = sparkline(vals)
    assert first == sparkline(list(vals))   # a second call over an equal sequence is byte-identical
    assert all(ch in _BARS for ch in first)


def test_negative_values_render_without_error() -> None:
    out = sparkline([-5.0, 0.0, 5.0])
    assert len(out) == 3
    assert _BARS.index(out[0]) < _BARS.index(out[-1])
