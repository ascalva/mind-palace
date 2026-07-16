"""The lever registry — the ENTIRE self-modifiable surface (BUILD-SPEC §14; Invariant 5).

This is the trust boundary the owner drew for Phase 10: self-modification may tune **knobs**
(numeric alignment/quality parameters) and nothing else. Infrastructure and code are an
extremely privileged resource the loop cannot write to.

That restriction is **structural, not a policy check**. A `ProposedChange` references a `Lever`
by name and carries a numeric `target`. There is no field on it — anywhere — that can hold a
file path, a diff, a command, or a Terraform plan. So "edit this file" / "run this" is not a
proposal the loop can *express*, the same way the airlock's `ResearchCriteria` has no field that
can carry note content (core/research/criteria.py). A future code/infra lever would be a
deliberate, separately-gated extension with its own apply path and human-only ceiling — adding it
here would be a visible, reviewable diff against this registry, never a guess.

Each lever names a single scalar config key (`section.key`) and its HARD bounds. The bounds are
the ones already written into config/defaults.toml's `[dreaming]` comments — promoted here from
prose to enforced code. A target outside `[lo, hi]` is rejected (fail-closed); the loop cannot
push a knob past the envelope the owner declared safe even with approval.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LeverKind(StrEnum):
    FLOAT = "float"
    INT = "int"


@dataclass(frozen=True)
class Lever:
    """One tunable knob: a single scalar config key with hard, owner-declared bounds.

    `name` is the stable identifier a proposal references. `section`/`key` locate the value in
    the TOML config (and in the machine-owned overlay the loop writes). `lo`/`hi` are INCLUSIVE
    bounds — the whole admissible range for this knob, never to be exceeded by any approved change.
    """

    name: str
    section: str
    key: str
    kind: LeverKind
    lo: float
    hi: float
    description: str = ""

    def coerce(self, value: float) -> float | int:
        """Snap a value to the lever's type (int levers carry whole numbers)."""
        return int(round(value)) if self.kind is LeverKind.INT else float(value)

    def in_bounds(self, value: float) -> bool:
        return self.lo <= value <= self.hi

    def validate(self, value: float) -> float | int:
        """Coerce + bounds-check. Raises (fail-closed) on out-of-bounds — the caller never
        silently clamps, because a proposal that wanted an out-of-range value is a proposal we
        refuse, not one we quietly rewrite."""
        coerced = self.coerce(value)
        if not self.in_bounds(coerced):
            raise ValueError(
                f"lever {self.name!r}: {coerced} outside hard bounds [{self.lo}, {self.hi}]"
            )
        return coerced


# --- The registry: the complete writable surface --------------------------------------------
#
# ONLY config knobs. Seeded with the `[dreaming]` tunables whose bounds defaults.toml already
# documents (gap G7). These are alignment/quality knobs — how the system clusters and reflects
# the owner's notes back — exactly the "system weights" the owner wants the loop to be able to
# nudge. Nothing here touches code, infrastructure, secrets, models, or the sandbox.

_LEVERS: tuple[Lever, ...] = (
    Lever(
        name="dream_similarity_threshold",
        section="dreaming",
        key="similarity_threshold",
        kind=LeverKind.FLOAT,
        lo=0.55,
        hi=0.75,
        description="σ: cosine at which two notes join a theme cluster (defaults.toml bound).",
    ),
    Lever(
        name="dream_near_dup_threshold",
        section="dreaming",
        key="near_dup_threshold",
        kind=LeverKind.FLOAT,
        lo=0.90,
        hi=0.99,
        description="cosine at which two authored notes are flagged a merge candidate (≥0.90).",
    ),
    Lever(
        name="dream_min_cluster_size",
        section="dreaming",
        key="min_cluster_size",
        kind=LeverKind.INT,
        lo=2,
        hi=6,
        description="minimum notes for a theme to count as a cluster.",
    ),
    Lever(
        name="dream_max_clusters",
        section="dreaming",
        key="max_clusters",
        kind=LeverKind.INT,
        lo=4,
        hi=16,
        description="cap on syntheses per dream run (the inference slot is scarce, §5).",
    ),
    Lever(
        name="dream_rnd_sigma",
        section="dream_rnd",
        key="sigma",
        kind=LeverKind.FLOAT,
        lo=0.55,
        hi=0.75,
        description="σ (dream_v2 lane): cosine edge threshold for the SHADOW mirror graph "
        "(core/dreaming/shadow.py reads dream_rnd.sigma; distinct from "
        "dream_similarity_threshold, which drives the live Phase-7 path).",
    ),
)

LEVERS: dict[str, Lever] = {lever.name: lever for lever in _LEVERS}


def get_lever(name: str) -> Lever:
    """Look up a registered lever. Raises (fail-closed) if `name` is not in the registry — a
    proposal can only ever target a knob that exists here."""
    try:
        return LEVERS[name]
    except KeyError:
        raise KeyError(f"unknown lever {name!r}; registered: {sorted(LEVERS)}") from None


@dataclass(frozen=True)
class ProposedChange:
    """A proposed knob change — the ONLY shape a self-modification can take.

    It is a (lever-name, target-number) pair and nothing more. Deliberately there is no `path`,
    `diff`, `command`, `code`, or `script` field: the loop physically cannot propose a code or
    infrastructure change because the value object has nowhere to put one. This is the structural
    expression of the owner's Phase-10 ceiling (see module docstring)."""

    lever: str
    target: float
    rationale: str = ""

    def resolve(self) -> tuple[Lever, float | int]:
        """Resolve to (lever, validated-target). Raises on unknown lever or out-of-bounds
        target — both fail-closed, so an invalid proposal never reaches the ledger as PROPOSED."""
        lever = get_lever(self.lever)
        return lever, lever.validate(self.target)
