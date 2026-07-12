"""Lane A L-b — the THREAD lens (core/dreaming/interpreters.py:thread_interpreter; bp-022 Item 5).

Proves: on a synthetic MirrorView whose notes form an empty cycle (β₁ = 1), the lens emits
exactly one THREAD claim, support == the carrying-cycle witness digests, persistence recorded in
`data`. On a filled/acyclic corpus (β₁ = 0), ZERO claims even when a below-scale hole exists — the
honest-seam order (β₁ = 0 short-circuits BEFORE any hole pairing) pinned by design note
`dn-edge-dynamics` §2.3 / plan §6(b). Determinism: two runs, identical claims. The L-b falsifier
(design note §3.1, verbatim): a THREAD claim on a β₁ = 0 complex (a fabricated thread), or a claim
whose support includes a note not on its carrying cycle.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Any

import numpy as np

from config.loader import load_config
from core.complex.hodge import harmonic_basis
from core.dreaming.graph import MirrorGraph
from core.dreaming.interpreters import (
    THREAD,
    build_structural_context,
    collect_claims,
    thread_interpreter,
)
from core.mirror import MirrorView


def _on_config(sigma: float = 0.3):
    cfg = load_config()
    return dataclasses.replace(
        cfg, dream_rnd=dataclasses.replace(cfg.dream_rnd, enabled=True, sigma=sigma)
    )


def _row(digest: str, vec: list[float]) -> dict[str, Any]:
    return {"digest": digest, "title": digest, "provenance": "authored-solo", "vector": vec}


def _ring_view(n: int = 6) -> MirrorView:
    """n notes on a circle: adjacent pairs similar, no chords — one clean β₁ = 1 harmonic class
    at sigma=0.3 (verified independently against `harmonic_basis`: exactly the 6 perimeter edges,
    no chords, matching `long_lived_holes`'s single reported hole at the same scale)."""
    rows = [
        _row(f"r{i}", [math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)])
        for i in range(n)
    ]
    return MirrorView(_rows=tuple(rows))


def _dense_clique_view(n: int = 5) -> MirrorView:
    """n near-identical notes: a single filled clique in the flag complex — β₁ = 0, no harmonic
    classes at all (every cycle is filled by a triangle)."""
    rng = np.random.default_rng(0)
    rows = [_row(f"d{i}", list(np.array([1.0, 0.0, 0.0, 0.0]) + rng.normal(0, 0.01, 4)))
            for i in range(n)]
    return MirrorView(_rows=tuple(rows))


AUTHORED_RING = {f"r{i}" for i in range(6)}


def _claims_for(view: MirrorView, cfg):
    ctx = build_structural_context(view, cfg.dream_rnd)
    return thread_interpreter(ctx, cfg.dream_rnd)


def test_thread_lens_emits_one_claim_on_the_planted_empty_cycle():
    cfg = _on_config(sigma=0.3)
    claims = _claims_for(_ring_view(), cfg)
    assert len(claims) == 1, "the planted beta1=1 ring must yield exactly one THREAD claim"
    claim = claims[0]
    assert claim.method == THREAD
    assert set(claim.support) == AUTHORED_RING          # support == the carrying-cycle witness
    assert claim.support == tuple(sorted(claim.support, key=lambda d: int(d[1:])))  # ordered
    assert "persistence" in claim.data
    assert claim.data["persistence"] == 1.0             # the ring hole's own lifetime
    assert "flow" in claim.data
    assert claim.data["witness"] == list(claim.support)


def test_thread_lens_yields_zero_claims_on_beta1_zero_even_with_holes_below_scale():
    """The honest-seam order (design note §2.3, plan §6(b) step order): beta1 == 0 short-circuits
    BEFORE any hole pairing is attempted, so a hole reported by the persistence filtration at a
    finer scale can never be misread as a thread once the harmonic classes are exhausted."""
    cfg = _on_config(sigma=0.3)
    view = _dense_clique_view()
    ctx = build_structural_context(view, cfg.dream_rnd)
    beta1 = harmonic_basis(ctx.complex.A).shape[1]
    assert beta1 == 0, "fixture must be a genuine beta1=0 complex for this falsifier to bind"
    claims = thread_interpreter(ctx, cfg.dream_rnd)
    assert claims == []                                  # ZERO claims, never fabricated


def test_thread_lens_support_is_always_a_subset_of_the_witness():
    """L-b falsifier, second clause: a claim whose support includes a note not on its carrying
    cycle. Support is built directly from `hole.vertices` by construction, so this is exact."""
    cfg = _on_config(sigma=0.3)
    claims = _claims_for(_ring_view(), cfg)
    for c in claims:
        assert set(c.support) <= AUTHORED_RING
        assert set(c.support) == set(c.data["witness"])


def test_thread_lens_deterministic_across_runs():
    cfg = _on_config(sigma=0.3)
    view = _ring_view()
    ctx1 = build_structural_context(view, cfg.dream_rnd)
    ctx2 = build_structural_context(view, cfg.dream_rnd)
    claims1 = thread_interpreter(ctx1, cfg.dream_rnd)
    claims2 = thread_interpreter(ctx2, cfg.dream_rnd)
    assert claims1 == claims2


def test_thread_lens_never_uses_the_word_contradiction():
    """Routing class pinned (plan §6(b) / design note §2.3): gap-family, never contradiction."""
    cfg = _on_config(sigma=0.3)
    claims = _claims_for(_ring_view(), cfg)
    assert claims, "the ring must yield at least one claim for this assertion to be meaningful"
    for c in claims:
        assert "contradiction" not in c.statement


def test_panel_integration_returns_thread_claims_alongside_existing_lenses():
    """Panel wiring end to end: `collect_claims` returns THREAD claims alongside the existing
    structural lenses; registration alone wires the dream path (plan Q1 — no dreamer.py edit)."""
    cfg = _on_config(sigma=0.3)
    view = _ring_view()
    ctx = build_structural_context(view, cfg.dream_rnd)
    graph = MirrorGraph.build(view, sigma=cfg.dream_rnd.sigma)
    claims = collect_claims(graph, ctx, cfg.dream_rnd)
    methods = {c.method for c in claims}
    assert THREAD in methods
    thread_claims = [c for c in claims if c.method == THREAD]
    assert len(thread_claims) == 1
    for c in claims:
        assert set(c.support) <= AUTHORED_RING          # firewall: every claim authored-only

    # Determinism at the panel level too.
    ctx2 = build_structural_context(view, cfg.dream_rnd)
    graph2 = MirrorGraph.build(view, sigma=cfg.dream_rnd.sigma)
    claims2 = collect_claims(graph2, ctx2, cfg.dream_rnd)
    assert claims == claims2
