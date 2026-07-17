"""FB-3 — the strength→surfacing gate (SETTLED / HUNCH / RETAINED), F9-validated.

Design: `docs/design-notes/sigma-fibers-and-multiscale-dreaming.md` §2.5 (RATIFIED; the rule, the
boundary conditions, the validation protocol, and the gate's three-clause falsifier are held here
VERBATIM, never re-derived). This module tiers bp-050's per-claim σ-fibers (`ClaimFiber`) for
SURFACING and nothing else.

**I1 is absolute — this module MUTATES NOTHING.** It filters the surfacing of PROPOSED-tier
candidates only: never an edge weight, never a confidence, never a promotion/verdict. No ledger
write, no eval-store write, no DreamLogEntry change, no lever registration — pure arithmetic over
report-layer fibers (`recursive-strata.md` §4 I1, §9: "no Dreamer-confidence-based weighting of
derived content, ever"). To make that structural rather than conventional, the module imports NO
store writer at all — `ClaimFiber` is imported under `TYPE_CHECKING` (annotations are strings), so
the runtime namespace is stdlib-only.

**The one-scalar prohibition (adjudicator.py:20-21), held verbatim.** `pers(χ)` is the SETTLED/HUNCH
strength axis; confidence c(κ) is the WITHIN-tier ordering axis. They are NEVER multiplied. Tier is
by `pers` alone (two thresholds partition [0,1]); rank within a tier is c(κ) alone. The ordering is
lexicographic two-axis `(tier, −c(κ), claim_id)` — no code path fuses pers into confidence, so a
high-`pers` low-confidence claim never outranks a low-`pers` high-confidence one WITHIN a tier.

**θ is tuning, not code (THRESH lifecycle).** `GATE_THRESH` provides the §2.5 provisional defaults
(`θ_weak = theta_weak_cells/m = 2/m`, `θ_strong = 0.5`); promotion to registered `ops/levers.py`
knobs is a separate future owner-visible act (parked, plan §11), never done here.

**Never a silent ship.** The surfaced API (`surfaced`) refuses with `GateNotValidated` unless a
`GateValidation` certifies all three §2.5 ship criteria hold on this corpus scale. A failing
validation parks the gate (the API stays closed) — the sanctioned conditional-plan outcome, not an
error. The validation READINGS (`sigma_gate.validation.*`) are written by the validation protocol
(the quality test), never by this module.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Annotation-only import (PEP 563 strings under `from __future__ import annotations`), so the
    # runtime module holds NO reference to fibers.py's store-coupled namespace. `ClaimFiber` is
    # bp-050's report artifact — used VERBATIM as the gate's input type (§6).
    from eval.harness.fibers import ClaimFiber


class Tier(Enum):
    """The three surfacing tiers (§2.5). SETTLED surfaces as a strong association; HUNCH surfaces
    only in a capped, labelled hunch section; RETAINED is ledger-only and NEVER surfaced."""

    SETTLED = "settled"
    HUNCH = "hunch"
    RETAINED = "retained"


# Descending surfacing strength — SETTLED first, RETAINED last. A discrete rank DERIVED from the
# pers-thresholding (never combined with confidence — the one-scalar prohibition).
_TIER_ORDER: dict[Tier, int] = {Tier.SETTLED: 0, Tier.HUNCH: 1, Tier.RETAINED: 2}


# The §2.5 provisional θ defaults, recorded for calibration — tuning, not code (THRESH lifecycle,
# `tests/quality/test_dreamer_quality.py:456`). `θ_weak = theta_weak_cells / m` (at least two grid
# cells — kills single-cell flickers); `θ_strong = 0.5` (holds on half the declared σ-range).
GATE_THRESH: dict[str, float] = {
    "theta_weak_cells": 2.0,   # θ_weak = theta_weak_cells / m
    "theta_strong": 0.5,       # θ_strong (fraction of the declared σ-range)
}

# "noise SETTLED-tier rate ≈ 0" tolerance for criterion (i) — tuning, kept OUT of GATE_THRESH so
# the pinned θ dict stays exactly the two §6 keys. A few percent counts as "≈ 0".
NOISE_SETTLED_MAX: float = 0.05


class GateNotValidated(RuntimeError):
    """The surfaced API refuses until the F9 validation (§2.5) certifies the gate on this corpus
    scale. Raised — never a silent ship — when the three ship criteria have not ALL held."""


@dataclass(frozen=True)
class TieredClaim:
    """One tiered surfacing candidate. `within_tier_rank` is the adjudicator confidence c(κ) and is
    the ONLY within-tier ordering key — it is NEVER combined with `fiber.pers` (§2.5 no scalar
    fusion)."""

    fiber: ClaimFiber            # bp-050's type, verbatim
    tier: Tier
    within_tier_rank: float      # = adjudicator confidence c(κ); NEVER combined with pers


def thresholds(m: int, thresh: Mapping[str, float] = GATE_THRESH) -> tuple[float, float]:
    """`(θ_weak, θ_strong)` for a grid of `m` cells. `θ_weak = theta_weak_cells / m` (§2.5);
    `θ_strong` is a bare fraction. Enforces the note's boundary condition `0 < θ_weak < θ_strong
    ≤ 1` fail-closed — a grid so coarse that `θ_weak` collapses onto `θ_strong` is refused rather
    than silently degenerating the tiers."""
    if m <= 0:
        raise ValueError(f"assign_tiers: grid size m must be >= 1 (got {m})")
    theta_strong = float(thresh["theta_strong"])
    theta_weak = float(thresh["theta_weak_cells"]) / m
    if not (0.0 < theta_weak < theta_strong <= 1.0):
        raise ValueError(
            "gate thresholds violate 0 < θ_weak < θ_strong ≤ 1 "
            f"(θ_weak={theta_weak:.4f} from {thresh['theta_weak_cells']}/{m}, "
            f"θ_strong={theta_strong:.4f}); the grid is too coarse to separate the tiers (§2.5)."
        )
    return theta_weak, theta_strong


def tier_for(pers: float, *, theta_weak: float, theta_strong: float) -> Tier:
    """The §2.5 partition — by `pers` ALONE. `pers ≥ θ_strong → SETTLED`; `θ_weak ≤ pers < θ_strong
    → HUNCH`; `pers < θ_weak → RETAINED`. No confidence enters here (one-scalar prohibition)."""
    if pers >= theta_strong:
        return Tier.SETTLED
    if pers >= theta_weak:
        return Tier.HUNCH
    return Tier.RETAINED


def assign_tiers(
    fibers: Sequence[ClaimFiber], *, m: int, confidence: Mapping[str, float]
) -> list[TieredClaim]:
    """Tier every fiber and rank it (§2.5). **Tier is a function of `fiber.pers` ONLY**; the
    within-tier rank is `confidence[claim_id]` (c(κ)) ONLY — the two axes are never fused. Result
    is sorted lexicographically `(tier, −rank, claim_id)`: SETTLED before HUNCH before RETAINED,
    then strongest belief first, then id-stable. A high-`pers` low-confidence claim therefore
    never outranks a low-`pers` high-confidence claim WITHIN the same tier.

    `confidence` is supplied by the caller (the adjudicator's c(κ), or 0.0 for the un-adjudicated
    phase7 lens). A claim absent from the map ranks at 0.0 — an ordering default, never a tier
    input."""
    theta_weak, theta_strong = thresholds(m)
    tiered = [
        TieredClaim(
            fiber=f,
            tier=tier_for(f.pers, theta_weak=theta_weak, theta_strong=theta_strong),
            within_tier_rank=float(confidence.get(f.claim_id, 0.0)),
        )
        for f in fibers
    ]
    # Two-axis lexicographic sort. `_TIER_ORDER[t.tier]` is derived from pers-thresholding; the
    # second key is confidence alone — the keys are ADJACENT, never multiplied (§2.5).
    tiered.sort(key=lambda t: (_TIER_ORDER[t.tier], -t.within_tier_rank, t.fiber.claim_id))
    return tiered


def hunch_section(claims: Sequence[TieredClaim], *, cap: int) -> list[TieredClaim]:
    """The capped, labelled HUNCH section (§2.5). Returns at most `cap` HUNCH-tier claims, strongest
    c(κ) first (id-stable). Every returned claim carries `tier == Tier.HUNCH` — that IS the label.
    SETTLED and RETAINED are excluded; RETAINED can never leak into a surfaced section."""
    if cap < 0:
        raise ValueError(f"hunch_section: cap must be >= 0 (got {cap})")
    hunches = [c for c in claims if c.tier is Tier.HUNCH]
    hunches.sort(key=lambda t: (-t.within_tier_rank, t.fiber.claim_id))
    return hunches[:cap]


@dataclass(frozen=True)
class GateValidation:
    """The §2.5 F9 ship/park verdict over one fixture battery — a PURE record. The three ship
    criteria and the decision; the eval-store `sigma_gate.validation.*` readings are written by the
    validation protocol (the quality test), NEVER here (I1: this module mutates nothing).

    - (i)   `noise_settled_rate`  — fraction of pure-noise claims tiered SETTLED; must be ≈ 0.
    - (ii)  `planted_reached_settled` — every planted signal reached SETTLED.
    - (iii) `tiered_precision` > `baseline_precision` — tiering strictly improves surfaced precision
            over the best single-σ baseline on the same fixtures.
    """

    noise_settled_rate: float
    planted_reached_settled: bool
    tiered_precision: float
    baseline_precision: float
    noise_settled_max: float = NOISE_SETTLED_MAX

    @property
    def crit_noise_clean(self) -> bool:
        """(i) The apophenia guard extended along σ: noise ≈ 0 at SETTLED."""
        return self.noise_settled_rate <= self.noise_settled_max

    @property
    def crit_planted_settles(self) -> bool:
        """(ii) Planted structure reaches SETTLED."""
        return self.planted_reached_settled

    @property
    def crit_precision_gain(self) -> bool:
        """(iii) Persistence-tiering STRICTLY improves surfaced precision over the best single σ."""
        return self.tiered_precision > self.baseline_precision

    @property
    def ship(self) -> bool:
        """The gate ships iff ALL THREE criteria hold (§2.5). Otherwise: park-and-record."""
        return self.crit_noise_clean and self.crit_planted_settles and self.crit_precision_gain

    def failing_clauses(self) -> list[str]:
        """The §2.5 falsifier clauses that did NOT hold — empty iff `ship`. Used to record which
        clause parks the gate and which re-entry it triggers."""
        out: list[str] = []
        if not self.crit_noise_clean:
            out.append(
                f"(i) noise SETTLED-tier rate {self.noise_settled_rate:.4f} exceeds ≈0 tol "
                f"{self.noise_settled_max:.4f} — the gate does not filter apophenia; corpus-growth "
                "re-entry"
            )
        if not self.crit_planted_settles:
            out.append(
                "(ii) planted claims did not reach SETTLED — over-filtering; first suspect §2.3's "
                "identity caveat (claim-identity flicker across σ) → SF-a v2-matching re-entry"
            )
        if not self.crit_precision_gain:
            out.append(
                f"(iii) tiered precision {self.tiered_precision:.4f} does not strictly exceed the "
                f"best single-σ baseline {self.baseline_precision:.4f} — no signal at this scale; "
                "corpus-growth re-entry"
            )
        return out


def surfaced(
    claims: Sequence[TieredClaim], *, cap: int, validation: GateValidation
) -> list[TieredClaim]:
    """The surfaced output — SETTLED (strongest c(κ) first) then the capped, labelled HUNCH section.
    **RETAINED never appears** (ledger-only, §2.5). Refuses with `GateNotValidated` unless
    `validation.ship` — never a silent ship (Item 2). This is the ONLY gated entry point; the
    tiering itself (`assign_tiers`) is always available (it mutates + surfaces nothing)."""
    if not validation.ship:
        raise GateNotValidated(
            "the σ-gate has not passed F9 validation on this corpus scale — surfacing is refused "
            f"(§2.5 park-and-record). Failing clause(s): {'; '.join(validation.failing_clauses())}"
        )
    settled = sorted(
        (c for c in claims if c.tier is Tier.SETTLED),
        key=lambda t: (-t.within_tier_rank, t.fiber.claim_id),
    )
    return [*settled, *hunch_section(claims, cap=cap)]
