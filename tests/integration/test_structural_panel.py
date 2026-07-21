"""H4–H7 + Lane A L-b through the panel: the structural interpreters emit grounded Claims
(flag-gated).

Planted structures the lenses must find: a ring of pairwise-similar notes with no center (the
`hole` lens — a conceptual gap, never a contradiction; and, at a sigma that keeps the ring's own
edges intact, the `thread` lens — the harmonic H1 flow orbiting that same gap, design note
`dn-edge-dynamics` §2.3 / bp-022), two dense concerns (the `theme` lens with a model-selected
count + posterior), and a cross-cluster link (the curvature `bridge` lens — covered by
test_dream_rnd's planted graph; here we assert the panel wiring end to end).
"""

from __future__ import annotations

import dataclasses
import math
from typing import Any

import numpy as np
import pytest

from config.loader import load_config
from core.dreaming.interpreters import (
    BRIDGE,
    CENSUS_LOOP,
    HOLE,
    THEME,
    THREAD,
    run_panel,
)
from core.graph.census import Arc, CensusReading, census
from core.mirror import MirrorView
from core.temporal.spine import Certificate, CertifiedCut


def _on_config():
    cfg = load_config()
    return dataclasses.replace(cfg, dream_rnd=dataclasses.replace(cfg.dream_rnd, enabled=True))


def _on_config_sigma(sigma: float):
    """A THREAD-lens variant: the harmonic lens needs the ring's OWN edges present in the
    sigma-skeleton (unlike `hole`, which reads the unthresholded distance matrix directly), so
    a THREAD-firing test needs sigma low enough to keep the ring intact."""
    cfg = load_config()
    return dataclasses.replace(
        cfg, dream_rnd=dataclasses.replace(cfg.dream_rnd, enabled=True, sigma=sigma)
    )


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


# --- Lane A L-b: the THREAD lens through the panel (bp-022 Item 5) ------------------------------

def test_thread_lens_fires_alongside_existing_lenses_when_ring_edges_are_intact():
    """`collect_claims` returns THREAD claims alongside the existing lenses (plan §7 acceptance):
    at a sigma that keeps the ring's own edges in the flag complex (beta1=1), the panel run
    includes exactly one THREAD claim, every claim's support stays authored-only, and the OTHER
    lenses' presence/behavior is unaffected by THREAD's registration."""
    cfg = _on_config_sigma(0.3)
    claims = run_panel(_ring_view(), config=cfg)
    methods = {c.method for c in claims}
    assert THREAD in methods
    thread_claims = [c for c in claims if c.method == THREAD]
    assert len(thread_claims) == 1
    assert set(thread_claims[0].support) <= AUTHORED_RING
    assert HOLE in methods                              # the sibling lens still fires too
    for c in claims:
        assert set(c.support) <= AUTHORED_RING          # firewall holds across every lens


def test_thread_lens_absent_at_default_sigma_where_ring_has_no_edges():
    """At the DEFAULT sigma (0.62), the ring's cosine similarities fall below the floor and the
    sigma-skeleton has zero edges — beta1 = 0, so THREAD must be silent even though `hole` still
    fires (hole reads the unthresholded distance matrix, not the sigma-skeleton). This is the
    honest seam at the panel level, and confirms every EXISTING panel test (which runs at default
    sigma) is unaffected by THREAD's registration."""
    claims = run_panel(_ring_view(), config=_on_config())
    assert not [c for c in claims if c.method == THREAD]
    assert [c for c in claims if c.method == HOLE]      # the sibling lens is unaffected


def test_panel_determinism_with_thread_registered():
    """Determinism: two runs, identical claims — across the WHOLE panel, now that THREAD is
    registered alongside the pre-existing lenses."""
    cfg = _on_config_sigma(0.3)
    view = _ring_view()
    claims1 = run_panel(view, config=cfg)
    claims2 = run_panel(view, config=cfg)
    assert claims1 == claims2


# --- bp-080 Item 5: the arrow-aware census lens joins the panel equal-citizen -------------------

def _census_cut() -> CertifiedCut:
    return CertifiedCut(
        frontier=(("versions:r0", 1),),
        certificates=frozenset({Certificate.COMMIT}),
        evidence=("cafe",),
    )


def _ring_census() -> CensusReading:
    """A census reading whose loop members ARE authored ring notes (r0/r1/r2), so census claims
    ground exactly like the structural lenses — the §2.9 equal-citizen demonstration."""
    arcs = [Arc("r0", "r1", "e1"), Arc("r1", "r2", "e2"), Arc("r2", "r0", "e3")]
    return census(arcs, {}, _census_cut())


def test_census_lens_joins_the_panel_equal_citizen_behind_the_flag():
    """With a census reading supplied, the panel returns the arrow-aware census claims ALONGSIDE
    the structural lenses — same flag, one call. Every census member is an authored ring note, so
    the firewall (support ⊆ authored) holds across the extended kind set."""
    claims = run_panel(_ring_view(), config=_on_config(), census=_ring_census())
    census_claims = [c for c in claims if c.method == CENSUS_LOOP]
    assert len(census_claims) == 1
    assert set(census_claims[0].support) <= AUTHORED_RING       # firewall holds for census too
    assert "closed influence loop" in census_claims[0].statement
    assert HOLE in {c.method for c in claims}                   # the existing lenses still fire


def test_panel_unchanged_when_no_census_supplied():
    """The retrofit is inert by default: absent a census reading the panel is byte-for-byte what
    it was before the census lens registered (no census method appears)."""
    claims = run_panel(_ring_view(), config=_on_config())
    assert not [c for c in claims if c.method == CENSUS_LOOP]


def test_census_lens_determinism_on_the_panel():
    view, cens = _ring_view(), _ring_census()
    a = run_panel(view, config=_on_config(), census=cens)
    b = run_panel(view, config=_on_config(), census=cens)
    assert a == b