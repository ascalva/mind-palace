"""H4–H7 through the panel: the structural interpreters emit grounded Claims (flag-gated).

Planted structures the lenses must find: a ring of pairwise-similar notes with no center (the
`hole` lens — a conceptual gap, never a contradiction), two dense concerns (the `theme` lens with
a model-selected count + posterior), and a cross-cluster link (the curvature `bridge` lens —
covered by test_dream_rnd's planted graph; here we assert the panel wiring end to end).
"""

from __future__ import annotations

import dataclasses
import math
from typing import Any

import numpy as np
import pytest

from config.loader import load_config
from core.dreaming.interpreters import BRIDGE, HOLE, THEME, run_panel
from core.mirror import MirrorView


def _on_config():
    cfg = load_config()
    return dataclasses.replace(cfg, dream_rnd=dataclasses.replace(cfg.dream_rnd, enabled=True))


def _row(digest: str, vec: list[float]) -> dict[str, Any]:
    return {"digest": digest, "title": digest, "provenance": "authored-solo", "vector": vec}


def _ring_view(n: int = 6) -> MirrorView:
    """n notes on a circle: adjacent pairs similar (cos 2π/n), no chords, no center — one
    clean conceptual hole in the flag complex."""
    rows = [
        _row(f"r{i}", [math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)])
        for i in range(n)
    ]
    return MirrorView(_rows=tuple(rows))


def _two_concerns_view(per: int = 5) -> MirrorView:
    """Two dense orthogonal concerns (plus tiny jitter so neither block is degenerate)."""
    rng = np.random.default_rng(0)
    rows = []
    for i in range(per):
        rows.append(_row(f"p{i}", list(np.array([1.0, 0.0, 0.0, 0.0]) + rng.normal(0, .02, 4))))
    for i in range(per):
        rows.append(_row(f"s{i}", list(np.array([0.0, 0.0, 1.0, 0.0]) + rng.normal(0, .02, 4))))
    return MirrorView(_rows=tuple(rows))


AUTHORED_RING = {f"r{i}" for i in range(6)}
AUTHORED_CONCERNS = {f"p{i}" for i in range(5)} | {f"s{i}" for i in range(5)}


def test_hole_lens_surfaces_the_planted_ring():
    claims = [c for c in run_panel(_ring_view(), config=_on_config()) if c.method == HOLE]
    assert claims, "the planted ring hole was not surfaced"
    top = claims[0]
    assert set(top.support) <= AUTHORED_RING            # grounded in authored notes only
    assert len(top.support) >= 4                        # the notes circling the hole
    assert "hole" in top.statement                      # surfaced as a GAP...
    assert "contradiction" not in top.statement         # ...never as a contradiction (§4.2)
    assert top.data["lifetime"] >= 0.15


def test_theme_lens_finds_two_concerns_with_posterior():
    claims = [c for c in run_panel(_two_concerns_view(), config=_on_config())
              if c.method == THEME]
    assert len(claims) == 2                              # one claim per (non-singleton) block
    supports = {frozenset(c.support) for c in claims}
    assert frozenset(f"p{i}" for i in range(5)) in supports
    assert frozenset(f"s{i}" for i in range(5)) in supports
    for c in claims:
        assert c.data["k_sbm"] == 2                      # model-selected, not fiat
        assert 0.0 < c.data["mean_posterior"] <= 1.0     # membership WITH confidence
        assert isinstance(c.data["counts_agree"], bool)  # the spectral cross-check is recorded


def test_ring_yields_no_bridge_false_positive_and_all_support_is_authored():
    """Wiring sanity across every lens: the panel runs the structural interpreters, every claim's
    support is authored (firewall), and the symmetric ring — where every edge is alike — does not
    rank any edge as a *negative-curvature* bridge (uniform curvature ⇒ min-edge fallback only)."""
    claims = run_panel(_ring_view(), config=_on_config())
    for c in claims:
        assert set(c.support) <= AUTHORED_RING
    bridges = [c for c in claims if c.method == BRIDGE]
    for b in bridges:
        assert b.data["curvature"] == pytest.approx(bridges[0].data["curvature"])  # all alike