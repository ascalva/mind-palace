# ── Family 4 boundary (metric geometry) · symbols in docs/NOTATION.md ──
# OBJECT:    the blast-radius reach gauge — the effector analogue of the alignment drift metric:
#            how far the hands are REACHING (mean reversibility band) vs a frozen anchor
#            (hands-and-the-effector-layer.md §4: "misbehavior at the actuator becomes a number").
# INVARIANT: reach is one-sided (reaching LESS than the anchor is not drift); a rising reach past
#            the blessed tolerance trips; the anchor + tolerance are frozen fixed points.
# ENFORCED:  reuses eval.drift.Axis (same one-sided, tolerance-normalized deterioration math);
#            DETECTION ONLY — it reads the effect ledger and reports, altering nothing, and is
#            deliberately separate from the gate's D(t) (effector reach ≠ golden-set capability).
"""Blast-radius drift — watching how far the hands reach against a frozen anchor (Track G, item G7).

§4 makes the point precisely: the reversibility classes are a **metric** (a distance from the
reversible origin), so an effector that begins proposing higher-blast-radius effects than its
history warrants is a *measurable trajectory* — appendable as a drift `Axis`, exactly like a Dreamer
bubble whose conductance is falling. This module is that gauge.

It reuses `eval.drift.Axis` — the same flat, additive record with one-sided, tolerance-normalized
deterioration — so "composes with the drift metric (family 4)" is literal, not analogy: the blast-
radius axis IS a drift axis, and the A2 alignment report can append it beside the structural axes.
But it is **detection only** and kept OUT of the self-mod gate's `D(t)`: the gate weighs
golden-set *capability* drift; effector reach is a different concern (a different μ), and folding it
into the gate's D would conflate "the hands reached further" with "retrieval regressed". So this
gauge reports on its own, for the alignment report and the owner — it never gates self-mod.

The reach scalar. `β` itself is 0 / 1 / ∞ (irreversible has no finite undo), which cannot be
averaged; but the class INDEX (0 sensing, 1 reversible, 2 irreversible) is β's monotone
finite proxy (§4: "β is monotone in the class"). So reach = **mean class index** over a window of
proposals — a bounded [0, 2] "mean blast-radius band" — with the irreversible fraction and the max
class reported alongside for the trajectory. Rising reach is the bad direction.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from eval.drift import Axis
from eval.golden import BASELINE_PATH
from ops.effects import ReversibilityClass


@dataclass(frozen=True)
class EffectorReach:
    """μ for the hands: how far they reached over a window of proposals. `mean_reach` is the mean
    reversibility-class index ([0, 2]); `irreversible_fraction` and `max_class` give the trajectory
    shape. `n` is the window size (0 ⇒ no proposals ⇒ reach at the origin)."""

    mean_reach: float
    irreversible_fraction: float
    max_class: int
    n: int


@dataclass(frozen=True)
class EffectorAnchor:
    """The frozen fixed points for effector reach — owner-blessed, outside the lever set (§4/§15):
    the baseline reach the owner expects and one tolerance-unit of rising reach. Defaults sit at the
    reversible-adjacent origin (a system that mostly senses); the owner blesses a higher anchor only
    deliberately."""

    baseline_reach: float = 0.0        # B — the blessed mean-reach anchor
    reach_tol: float = 0.50            # one tolerance-unit of rising mean blast-radius band


def reach_of(classes: Iterable[ReversibilityClass]) -> EffectorReach:
    """Summarize the reach of a window of proposed effects (their reversibility classes). Empty ⇒
    reach at the origin (mean 0, nothing irreversible) — no proposals is not drift."""
    idx = [int(c) for c in classes]
    if not idx:
        return EffectorReach(mean_reach=0.0, irreversible_fraction=0.0, max_class=0, n=0)
    irr = sum(1 for i in idx if i == int(ReversibilityClass.IRREVERSIBLE))
    return EffectorReach(
        mean_reach=sum(idx) / len(idx),
        irreversible_fraction=irr / len(idx),
        max_class=max(idx),
        n=len(idx),
    )


def effector_reach_axis(reach: EffectorReach, anchor: EffectorAnchor) -> Axis:
    """The blast-radius reach as a drift `Axis` (family 4): value = mean reach, against the blessed
    baseline, normalized by the blessed tolerance. `higher_is_better=False` — reaching further than
    the anchor is the bad direction; reaching less contributes 0 (one-sided)."""
    return Axis(
        name="effector_reach",
        value=reach.mean_reach,
        baseline=anchor.baseline_reach,
        tolerance=anchor.reach_tol,
        higher_is_better=False,
    )


@dataclass(frozen=True)
class EffectorDriftReport:
    """The gauge reading: the reach profile, axis deterioration (tol-units), and whether it
    is within the blessed band. Detection only — consumed by the alignment report and the owner."""

    reach: EffectorReach
    deterioration: float          # the Axis one-sided, tolerance-normalized deterioration
    within_tolerance: bool        # deterioration ≤ 1 tolerance-unit
    anchor: EffectorAnchor


def measure_effector_drift(
    classes: Iterable[ReversibilityClass], anchor: EffectorAnchor | None = None
) -> EffectorDriftReport:
    """Measure blast-radius drift over proposed-effect classes against the frozen anchor.
    `within_tolerance` is deterioration ≤ 1, mirroring the gate's D ≤ Θ shape at a single axis
    — but this never feeds the gate."""
    anchor = anchor or EffectorAnchor()
    reach = reach_of(classes)
    det = effector_reach_axis(reach, anchor).deterioration()
    return EffectorDriftReport(reach=reach, deterioration=det, within_tolerance=det <= 1.0,
                               anchor=anchor)


def reach_from_ledger(ledger: object) -> EffectorDriftReport:
    """Convenience: measure reach over every proposal recorded in an `EffectLedger` (each row is a
    proposed effect). Windowing (recent-only) is the caller's; this reads the whole history.
    Duck-typed on `.all()` so this module imports no ledger."""
    records = ledger.all()  # type: ignore[attr-defined]
    return measure_effector_drift([r.reversibility for r in records], load_effector_anchor())


def load_effector_anchor(path: Path = BASELINE_PATH) -> EffectorAnchor:
    """Read the blessed `effectors` section of baseline.json (owner-only, frozen). Defaults apply if
    absent, so the gauge degrades gracefully on an un-extended baseline (origin anchor, 0.5 tol)."""
    import json

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    e = data.get("effectors", {})
    return EffectorAnchor(
        baseline_reach=float(e.get("baseline_reach", 0.0)),
        reach_tol=float(e.get("reach_tol", 0.50)),
    )
