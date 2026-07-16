"""The pure terminal sparkline (dn-evaluation-harness §2.7, bp-044 Item 8).

A curve in the report is a row of Unicode block bars — one glyph per value, height ∝ the value's
position in the series' own [min, max] band. The renderer is **pure and model-free**: a function of
its input sequence only, no I/O, no clock, no external dependency (the report's determinism
falsifier reaches down to here — the same input must always yield the same string).

Degenerate series render, never raise (§2.7 "no silent caps" starts with not crashing on the empty
frontier): an empty series is the empty string; a single value or a constant series is a flat row at
the lowest bar (there is no band to place it in — a flat row reads honestly as "no variation").
"""

from __future__ import annotations

from collections.abc import Sequence

# Eight Unicode block levels, low → high. Index into this by each value's normalized band position.
_BARS = "▁▂▃▄▅▆▇█"


def sparkline(values: Sequence[float]) -> str:
    """Render `values` as a deterministic row of Unicode block bars (one glyph per value).

    * empty  → `""`;
    * single value / constant series (zero band) → a flat row of the lowest bar;
    * otherwise each value maps to a bar by its position in the series' own [min, max] band.

    Pure: same input → same output (asserted in the tests). No I/O, no model, no clock.
    """
    vals = [float(v) for v in values]
    if not vals:
        return ""
    lo = min(vals)
    hi = max(vals)
    band = hi - lo
    if band == 0.0:
        # No band to place values in — a flat row reads honestly as "no variation".
        return _BARS[0] * len(vals)
    top = len(_BARS) - 1
    out: list[str] = []
    for v in vals:
        idx = int((v - lo) / band * top + 0.5)  # round-to-nearest; monotone in v (determinism)
        idx = max(0, min(top, idx))
        out.append(_BARS[idx])
    return "".join(out)
