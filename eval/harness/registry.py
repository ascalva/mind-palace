"""The metric registry — the single metric namespace (dn-evaluation-harness §2.5, bp-042).

Sweeps, batteries, and reports may reference ONLY a metric registered here — there are no ad-hoc
metrics. A registered metric declares (§2.5): its `name`; its `type_tag` (`Inv` / `Rate(κ)` — a Rate
carries its clock, Rule CLOCK §2.3); its `source_instrument` (a catalog row, §2.3); its
`comparability` rule (which corpus_refs / anchors it may be compared across — type-directed); its
`assertion_shape` (`regression` first; `absolute` only once a distribution stabilizes, §2.5); and
whether it is `guardrail_eligible` (§2.5's always-on guardrail set draws from these).

`eval/metrics.py` is **absorbed** here (§2.2): its three pure functions (`recall_at_k`,
`set_overlap`, `mean_cosine_distance`) keep their signatures and become the registered
*golden-recall* family — the module stays importable, this registry owns it. The registry holds no
model; it is metadata over the built instruments, not a computation path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AssertionShape = Literal["regression", "absolute"]


@dataclass(frozen=True)
class MetricSpec:
    name: str
    type_tag: str                       # "Inv" | "Rate(<clock>)"
    source_instrument: str              # a catalog row id (§2.3)
    comparability: str                  # which corpus_refs / anchors it may be compared across
    assertion_shape: AssertionShape     # regression-first (§2.5)
    guardrail_eligible: bool


REGISTRY: dict[str, MetricSpec] = {}


def register(spec: MetricSpec) -> None:
    """Register a metric. A duplicate name is a namespace collision and is refused (single
    namespace, §2.5) — the registry is the one source of truth for what a metric *is*."""
    if spec.name in REGISTRY:
        raise ValueError(f"metric {spec.name!r} already registered (single namespace, §2.5)")
    REGISTRY[spec.name] = spec


def get(name: str) -> MetricSpec:
    """Resolve a metric spec. Fail-closed: an unregistered name raises (no ad-hoc metrics)."""
    try:
        return REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"metric {name!r} is not registered — sweeps/reports may reference only registered "
            f"metrics (§2.5). Register it in eval/harness/registry.py first."
        ) from None


def is_registered(name: str) -> bool:
    return name in REGISTRY


# --- The BUILT metric families, registered at import (§3 E1 / §6). -----------------------------
# comparability is type-directed (§2.3): Inv readings may compare across distinct-snapshot anchors;
# a Rate never dedups and compares only within its own clock.
_BUILT: tuple[MetricSpec, ...] = (
    # row 1 — golden-set recall (eval/golden.py + the absorbed eval/metrics.py). The recall metric
    # is the frozen guardrail; overlap/mean-distance are diagnostics, not guardrails.
    MetricSpec("golden_recall", "Inv", "row1-golden-recall",
               "the frozen golden fixture only (baseline.json expectations)", "regression", True),
    MetricSpec("golden_overlap", "Inv", "row1-golden-recall",
               "the frozen golden fixture only", "regression", False),
    MetricSpec("golden_mean_distance", "Inv", "row1-golden-recall",
               "the frozen golden fixture only", "regression", False),
    # row 2 — the A1 drift gauge D(t) vs frozen B (eval/drift.py). A guardrail (advisory until Θ is
    # owner-blessed from calibrated curves — the harness reports, never trips, until then).
    MetricSpec("drift_D", "Inv", "row2-drift-gauge",
               "against the frozen anchor B (never against the eval store's own history)",
               "regression", True),
    # row 5 — the F9 quality battery (tests/quality THRESH). f9_composite is the headline family;
    # its members are the three THRESH-pinned components. Combined as no-regression-on-all +
    # improvement-on-headline (§2.6), never as scalar weights.
    MetricSpec("f9_composite", "Inv", "row5-f9-suite",
               "same fixture / same pipeline; k-seed intervals at owner scale",
               "regression", False),
    MetricSpec("f9_signal_recall", "Inv", "row5-f9-suite",
               "same fixture / same pipeline", "regression", False),
    MetricSpec("f9_noise_max_conf", "Inv", "row5-f9-suite",
               "same fixture / same pipeline", "regression", False),
    MetricSpec("f9_noise_max_mean", "Inv", "row5-f9-suite",
               "same fixture / same pipeline", "regression", False),
    # row 4 — telemetry vitals + context_usage (core/stores/telemetry.py). A wall-clock cost is a
    # Rate(wall) (carries its clock); context_usage is an Inv count.
    MetricSpec("telemetry_wall", "Rate(wall)", "row4-telemetry",
               "within the wall clock only (a Rate never dedups — a plateau is data)", "regression",
               False),
    MetricSpec("context_usage", "Inv", "row4-telemetry",
               "per agent/job window", "regression", False),
)

for _spec in _BUILT:
    register(_spec)
