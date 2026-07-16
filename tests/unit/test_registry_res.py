"""FB-2 registry rows: `sigma_persistence.*` (Res(sigma)) + `structural_axes.*` (Inv) — bp-054.

Resolves finding-0086 (structural_axes.* written un-registered). Two falsifiers guarded: (1) a NAME
MISMATCH between what the registry declares and what FB-1 / shadow actually WRITE — foreclosed by
importing FB-1's own name constants (`eval.harness.fibers`) and by deriving shadow's axis names from
the snapshot's own `structural_axes()` keys (the one source of truth for both), so the test cannot
drift from the writers; (2) any new row marked guardrail-eligible (Res metrics are descriptive, RT-c
parked; the structural axes FEED drift's A2, they are not themselves a guardrail).
"""

from __future__ import annotations

import pytest

from core.complex.temporal import StructuralSnapshot
from eval.harness import registry
from eval.harness.fibers import (
    METRIC_FRAC_GE_STRONG,
    METRIC_MAX,
    METRIC_MEAN,
    METRIC_N_CLAIMS,
    METRIC_P50,
)

# The five aggregate names, taken from FB-1's own constants (imported, not restrung). registry.py
# registers the identical literals; a drift on either side fails `registry.get` below.
_SIGMA_METRICS = [METRIC_MEAN, METRIC_P50, METRIC_MAX, METRIC_FRAC_GE_STRONG, METRIC_N_CLAIMS]


def _written_structural_axis_names() -> list[str]:
    """The `structural_axes.<axis>` names shadow.py actually writes: it emits
    `f"structural_axes.{axis}"` for each axis in the snapshot's `structural_axes()` dict
    (`core/dreaming/shadow.py:232-243` → `SnapshotStore.latest_structural` →
    `StructuralSnapshot.structural_axes`). Derived from that source of truth so the assertion cannot
    silently diverge from what is written."""
    snap = StructuralSnapshot(taken_at="t", n_nodes=1, n_components=1, fiedler=0.0,
                              frustration=0.0, mean_forman=0.0, frac_neg_curv=0.0, n_blocks_sbm=1,
                              min_conductance=1.0)
    return [f"structural_axes.{axis}" for axis in snap.structural_axes()]


# ── the five σ-fibers Res(π) rows resolve, tagged Res(sigma), non-guardrail ───────────────────
def test_sigma_persistence_family_resolves_as_res_sigma():
    for name in _SIGMA_METRICS:
        spec = registry.get(name)          # fail-closed get; KeyError if unregistered
        assert spec.name == name
        assert spec.type_tag == "Res(sigma)"
        assert spec.guardrail_eligible is False
        assert spec.assertion_shape == "regression"
        assert spec.source_instrument == "row15-sigma-fibers"


def test_sigma_names_match_fb1_constants_exactly():
    """Name agreement with FB-1's writes: the registered names ARE fibers' own constants — a drift
    in either side breaks resolution here (the finding-0086 failure class, foreclosed at CI)."""
    assert _SIGMA_METRICS == ["sigma_persistence.mean", "sigma_persistence.p50",
                              "sigma_persistence.max", "sigma_persistence.frac_ge_strong",
                              "sigma_persistence.n_claims"]
    assert all(registry.is_registered(n) for n in _SIGMA_METRICS)


# ── the structural_axes rows resolve, tagged Inv, non-guardrail (finding-0086) ────────────────
def test_structural_axes_family_resolves_as_inv():
    names = _written_structural_axis_names()
    assert names == ["structural_axes.frustration", "structural_axes.min_conductance"]
    for name in names:
        spec = registry.get(name)
        assert spec.type_tag == "Inv"
        assert spec.guardrail_eligible is False
        assert spec.assertion_shape == "regression"
        assert spec.source_instrument == "row6-structural-axes"


# ── duplicate registration refused (single namespace, §2.5) ───────────────────────────────────
def test_duplicate_registration_refused():
    """Re-registering an already-registered name is a namespace collision — refused (register raises
    BEFORE mutating, so this does not pollute the global REGISTRY for other tests)."""
    existing = registry.get(METRIC_MEAN)
    with pytest.raises(ValueError):
        registry.register(existing)


# ── no new row is guardrail-eligible (Res metrics are descriptive; RT-c parked) ───────────────
def test_no_new_row_is_guardrail_eligible():
    for name in _SIGMA_METRICS + _written_structural_axis_names():
        assert registry.get(name).guardrail_eligible is False
