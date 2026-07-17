"""The σ-sweep experiment instrument (bp-058) — V3 control battery, SE-3 blind sample, §2.3 report.

Design: `docs/design-notes/sigma-sweep-experiment.md` (RATIFIED, FROZEN @ `d932670`). This module
is the one thin wiring item §3 licenses: it composes the BUILT instruments (bp-049 sweep, bp-050
fibers, bp-057 gate, bp-044 report) into the three deterministic, model-free surfaces run 1 needs.
It runs NO experiment (the run is owner-fired per V5 and non-negotiable 5) and changes NO analysis
rule (every rule is frozen in the note §2.2). Model-free by construction: arithmetic over local
stores + already-computed instrument verdicts; no model import, no LLM call, no clock read (the
caller stamps `date` / `commit_sha`). Writes ONLY into `data/reports/` (∉ MIRROR_READABLE, local,
no egress — the `report.py`/`fibers.py` precedent); it emits NO eval-store readings (§2.3: readings
land under registered names only — this surface reads registered ones and renders report values).

Three surfaces, exactly as §3 stages them:

  1. **V3 control battery (`run_control_battery`).** bp-057's noise + planted fixtures through the
     CURRENT pipeline; the three F9 ship criteria recomputed as one GREEN/RED verdict. Controls fail
     ⇒ the run is INVALID (note V3) — `scripts/experiment.py controls` exits non-zero.
  2. **SE-3 blind sample (`generate_blind_sample`).** A tiering → ≤24 claims stratified across
  tiers,
     presented UNLABELED in seeded-random order, with labels SEALED to a separate artifact opened
     only after the owner rates. Deterministic: a seeded PRNG over a sorted claim list.
  3. **§2.3 composite report (`assemble_composite`).** The E4 A/B report + curve/selection + fibers
     summary + tier occupancy/stability + control outcomes + the V1–V5 evidence block (incl. the
     certified cut) + the post-unblinding blind-judgment record — one content-addressed artifact.
"""

from __future__ import annotations

import json
import random
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.temporal.spine import CertifiedCut
    from eval.harness.fibers import FibersResult
    from eval.harness.gate import GateValidation, TieredClaim
    from eval.harness.report import Report
    from eval.harness.sweep import SweepResult

# The F9 fixture grid — bp-057's `_M` (grid points on [0.55, 0.75]: [0.55,0.60,0.65,0.70,0.75]).
CONTROL_RESOLUTION = 5


# ==================================================================================================
# Item 1 — the V3 control battery (instrument integrity before data)
# ==================================================================================================


@dataclass(frozen=True)
class ControlOutcome:
    """The V3 control-battery verdict — the three F9 ship criteria recomputed through the CURRENT
    pipeline over bp-057's fixtures (verbatim). `.green` iff all three reproduce; a RED battery ⇒
    the run is INVALID regardless of real-data output (note §2.1 V3): stop, finding, read nothing.

    - (i)   `noise_settled_rate` — fraction of pure-noise (star) claims tiered SETTLED; must be ≈ 0.
    - (ii)  `planted_reached_settled` — both isolated planted clusters reach SETTLED.
    - (iii) `tiered_precision` > `baseline_precision` — persistence-tiering strictly beats the best
      single-σ baseline on the planted-in-noise fixture.
    """

    noise_settled_rate: float
    planted_reached_settled: bool
    tiered_precision: float
    baseline_precision: float
    validation: GateValidation      # bp-057's record; .crit_* / .ship / .failing_clauses()
    grid: tuple[float, ...]

    @property
    def green(self) -> bool:
        """GREEN iff ALL THREE §2.5 ship criteria hold — the exact `GateValidation.ship`."""
        return self.validation.ship

    def failing_clauses(self) -> list[str]:
        """The §2.5 falsifier clauses that did NOT reproduce — empty iff `green`."""
        return self.validation.failing_clauses()


def run_control_battery(*, resolution: int = CONTROL_RESOLUTION) -> ControlOutcome:
    """V3 as one invocation: drive bp-057's noise + planted-in-noise fixtures through the BUILT
    ShadowRunner/SweepEngine at the F9 grid, tier the resulting fibers at the FROZEN θ defaults, and
    recompute the three ship criteria — the exact computation `test_sigma_gate._compute_validation`
    holds, LIFTED here so the pre-flight is one call. Model-free, deterministic; re-drives the
    pipeline each call (a pipeline regression reddens it), and writes to no store.

    The fixtures live under `tests/quality/` and are imported LAZILY (so importing this module drags
    no test deps, and the eval-isolation posture sees no test coupling at import time). Reusing them
    verbatim is deliberate — the note §2.1 V3 names bp-057's fixtures as the battery; forking them
    into `eval/` would risk drift from the very suite the battery mirrors (plan §11).
    """
    from eval.harness.gate import GateValidation, Tier, assign_tiers
    from tests.quality.fixtures_sigma_gate import (
        NOISE_ROWS,
        PLANTED_IN_NOISE_ROWS,
        ledger_confidence,
        ledger_labels,
        phase7_fibers,
        single_sigma_precisions,
    )

    # (i) noise-only — the morphing star; every identity should be transient (RETAINED), no SETTLED.
    nf, nl, ngrid = phase7_fibers(NOISE_ROWS, resolution=resolution)
    nlabels = ledger_labels(nl)
    ntiered = assign_tiers(nf, m=len(ngrid), confidence=ledger_confidence(nl))
    noise_claims = [t for t in ntiered if nlabels.get(t.fiber.claim_id) == "noise"]
    noise_rate = (
        sum(1 for t in noise_claims if t.tier is Tier.SETTLED) / len(noise_claims)
        if noise_claims
        else 0.0
    )

    # (ii) + (iii) planted-in-noise — planted structure persists to SETTLED; tiering beats single-σ.
    pf, pl, pgrid = phase7_fibers(PLANTED_IN_NOISE_ROWS, resolution=resolution)
    plabels = ledger_labels(pl)
    ptiered = assign_tiers(pf, m=len(pgrid), confidence=ledger_confidence(pl))
    planted_settled = [
        t for t in ptiered if t.tier is Tier.SETTLED and plabels.get(t.fiber.claim_id) == "planted"
    ]
    planted_ok = len(planted_settled) >= 2

    surfaced_set = [t for t in ptiered if t.tier in (Tier.SETTLED, Tier.HUNCH)]  # RETAINED excluded
    tp = sum(1 for t in surfaced_set if plabels.get(t.fiber.claim_id) == "planted")
    fp = sum(1 for t in surfaced_set if plabels.get(t.fiber.claim_id) == "noise")
    tiered_precision = tp / (tp + fp) if (tp + fp) else 0.0
    baseline_precision = max(single_sigma_precisions(pl, plabels))

    validation = GateValidation(
        noise_settled_rate=noise_rate,
        planted_reached_settled=planted_ok,
        tiered_precision=tiered_precision,
        baseline_precision=baseline_precision,
    )
    return ControlOutcome(
        noise_settled_rate=noise_rate,
        planted_reached_settled=planted_ok,
        tiered_precision=tiered_precision,
        baseline_precision=baseline_precision,
        validation=validation,
        grid=tuple(float(v) for v in pgrid),
    )


def render_control_markdown(outcome: ControlOutcome) -> list[str]:
    """The control-battery section (report-layer values — NOT eval-store readings, §3 Q3). Prints
    the three criteria + the GREEN/RED verdict + any failing clause. Returned as lines so the
    composite report can embed it; deterministic, no clock."""
    v = outcome.validation
    lines = [
        "## V3 · control battery (F9 criteria through the current pipeline)",
        "",
        f"- verdict: **{'GREEN' if outcome.green else 'RED — run INVALID (§2.1 V3)'}**",
        f"- grid (m={len(outcome.grid)}): {[round(x, 4) for x in outcome.grid]}",
        f"- (i) noise SETTLED rate: {outcome.noise_settled_rate:.4f} "
        f"(≤ {v.noise_settled_max:.4f} ⇒ {'ok' if v.crit_noise_clean else 'FAIL'})",
        f"- (ii) planted reached SETTLED: {outcome.planted_reached_settled} "
        f"({'ok' if v.crit_planted_settles else 'FAIL'})",
        f"- (iii) tiered precision {outcome.tiered_precision:.4f} vs best single-σ "
        f"{outcome.baseline_precision:.4f} ({'ok' if v.crit_precision_gain else 'FAIL'})",
    ]
    for clause in outcome.failing_clauses():
        lines.append(f"- FAILING: {clause}")
    lines.append("")
    return lines


# ==================================================================================================
# Item 2 — the blind-sample generator (SE-3; labels sealed)
# ==================================================================================================

# The three surfacing tiers, in the FIXED order the stratified sample walks (determinism).
_TIER_ORDER: tuple[str, ...] = ("settled", "hunch", "retained")


@dataclass(frozen=True)
class BlindItem:
    """One claim as PRESENTED to the owner for blind rating — carries NO tier, NO pers, NO label.
    `presentation_index` is the position in the seeded-random order; `claim_id` is the opaque
    content-address join key (tier-neutral) used at unblinding; `content` is the caller-supplied
    display text (a claim's `surface_text`)."""

    presentation_index: int
    claim_id: str
    content: str


@dataclass(frozen=True)
class BlindSample:
    """A blind judgment sample (SE-3): the UNLABELED presentation (seeded-random order) + the SEALED
    `claim_id → tier` labels (a DISTINCT artifact opened only after the owner records ratings) +
    coverage notes (stratification shortfalls; no silent cap, §2.8). Deterministic given `seed`."""

    presentation: tuple[BlindItem, ...]
    sealed_labels: dict[str, str]        # claim_id -> tier.value — SEALED (post-rating only)
    notes: tuple[str, ...]
    seed: int
    cap: int


def generate_blind_sample(
    tiered: Sequence[TieredClaim],
    content: Mapping[str, str],
    *,
    seed: int,
    cap: int = 24,
) -> BlindSample:
    """Sample ≤`cap` claims stratified evenly across the three tiers (⌊cap/3⌋ each, or all available
    with the shortfall RECORDED), present them UNLABELED in seeded-random order, and seal the
    `claim_id → tier` labels separately (SE-3). Deterministic: one `random.Random(seed)` consumed in
    a FIXED sequence — sample SETTLED, then HUNCH, then RETAINED (each over a claim-id-sorted
    stratum), then shuffle the presentation — so identical inputs (with the seed) ⇒ same bytes.

    `content` maps `claim_id → display text` (the caller assembles it from the ledger's
    `surface_text` — never from the tier). The generator adds NO tier/pers to the presentation;
    blinding is structural. A claim with no content is presented blank + a note (no fabrication)."""
    per_tier = max(1, cap // len(_TIER_ORDER))
    rng = random.Random(seed)
    notes: list[str] = []
    chosen: list[tuple[str, str]] = []   # (claim_id, tier.value) in canonical (tier, id) order
    by_tier: dict[str, list[str]] = {name: [] for name in _TIER_ORDER}
    for tc in tiered:
        by_tier.setdefault(tc.tier.value, []).append(tc.fiber.claim_id)

    for tier_name in _TIER_ORDER:
        members = sorted(by_tier.get(tier_name, []))
        take = min(per_tier, len(members))
        if take < per_tier:
            notes.append(
                f"stratum {tier_name}: {len(members)} available < target {per_tier} — sampled all "
                f"{take} (no silent cap, §2.8)."
            )
        sampled = rng.sample(members, take) if take else []
        for cid in sorted(sampled):
            chosen.append((cid, tier_name))

    order = list(range(len(chosen)))
    rng.shuffle(order)
    presentation = tuple(
        BlindItem(presentation_index=i, claim_id=chosen[j][0],
                  content=content.get(chosen[j][0], ""))
        for i, j in enumerate(order)
    )
    if any(content.get(cid, "") == "" for cid, _ in chosen):
        notes.append(
            "one or more sampled claims had no content string — presented blank (the caller should "
            "supply surface_text; no fabrication)."
        )
    return BlindSample(
        presentation=presentation,
        sealed_labels={cid: tier for cid, tier in chosen},
        notes=tuple(notes),
        seed=seed,
        cap=cap,
    )


def render_blind_presentation(sample: BlindSample, *, date: str, topic: str) -> str:
    """The UNLABELED presentation the owner rates — NO tier, NO pers, NO label anywhere. Each entry
    is `#index`, the content, and a rating slot (`real connection / plausible / noise`)."""
    lines = [
        f"# Blind judgment · {topic}",
        "",
        f"_date: {date}_ · _rate each item BEFORE unblinding; labels are sealed separately (SE-3)_",
        "",
        f"{len(sample.presentation)} item(s), in seeded-random order. For each, mark one: "
        "`real connection` / `plausible` / `noise`.",
        "",
    ]
    for item in sample.presentation:
        lines += [
            f"## #{item.presentation_index}",
            "",
            f"{item.content or '_(no content supplied)_'}",
            "",
            "- rating: `[ ] real connection   [ ] plausible   [ ] noise`",
            "",
        ]
    return "\n".join(lines)


def render_sealed_labels(sample: BlindSample) -> str:
    """The SEALED labels — `claim_id → tier`, the sample seed/cap, and the coverage notes. Opened
    ONLY after the owner records ratings (unblinding). Deterministic JSON (`sort_keys`)."""
    return json.dumps(
        {
            "seed": sample.seed,
            "cap": sample.cap,
            "presentation_order": [it.claim_id for it in sample.presentation],
            "labels": sample.sealed_labels,
            "notes": list(sample.notes),
        },
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    ) + "\n"


def write_blind_sample(sample: BlindSample, *, date: str, topic: str,
                       root: str | Path = "data/reports") -> Path:
    """Write the presentation + the SEALED labels to `<root>/<date>-<topic>/blind/` as two DISTINCT
    files (`presentation.md`, `labels.sealed.json`) and return the blind dir. The only FS write —
    into `data/reports/` (∉ MIRROR_READABLE, local, no egress)."""
    out_dir = Path(root) / f"{date}-{topic}" / "blind"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "presentation.md").write_text(
        render_blind_presentation(sample, date=date, topic=topic), encoding="utf-8"
    )
    (out_dir / "labels.sealed.json").write_text(render_sealed_labels(sample), encoding="utf-8")
    return out_dir


# ==================================================================================================
# Item 3 — the composite report assembler (§2.3 contract)
# ==================================================================================================


@dataclass(frozen=True)
class DeterminismCheck:
    """V4 — the determinism spot-check: one duplicated (σ, seed) cell re-run must agree bit-wise."""

    cell: str                    # the (σ, seed) cell identifier re-run
    bitwise_identical: bool


@dataclass(frozen=True)
class SelfmodPosture:
    """V5 — the selfmod posture the run executed under. Propose-only (`enabled` true,
    `unattended_enabled` false) emits a `ProposedChange` for owner blessing; `enabled` false is a
    preview (SE-1's proposal step deferred). Auto-apply: never."""

    enabled: bool
    unattended_enabled: bool
    proposal_emitted: bool
    proposal_id: int | None


@dataclass(frozen=True)
class BlindJudgment:
    """SE-3 post-unblinding — the owner's ratings joined to the sealed tier labels. DESCRIPTIVE: the
    assembler renders the tier × rating cross-tab; it applies NONE of the SE-3 bars (those are read
    off in ANALYSIS per the frozen note §2.2). Single-subject calibration evidence, so labelled."""

    ratings: dict[str, str]      # claim_id -> "real connection" | "plausible" | "noise"
    labels: dict[str, str]       # claim_id -> tier.value  (from the sealed file, post-unblinding)


@dataclass(frozen=True)
class CompositeSection:
    """One section of the composite report — a stable machine `key`, a human `title`, the markdown
    `lines`, and the machine `data`. `render_markdown` and `render_json` both derive from this one
    model, so the two renderings cannot drift (the report.py anti-drift guarantee)."""

    key: str
    title: str
    lines: tuple[str, ...]
    data: dict[str, Any]


@dataclass(frozen=True)
class CompositeReport:
    """The one composite report per run (§2.3), content-addressable via its deterministic
    renderings. `coverage_notes` records everything the assembler could NOT render (a None piece,
    an unregistered metric, an absent cut) — no silent caps (§2.8)."""

    topic: str
    date: str
    commit_sha: str
    sections: tuple[CompositeSection, ...]
    coverage_notes: tuple[str, ...]


def tier_occupancy(tiered: Sequence[TieredClaim]) -> dict[str, int]:
    """Count claims per tier (`settled`/`hunch`/`retained`). The occupancy the SE-3 apophenia cap
    (≤20% SETTLED) is read against — computed here, judged in analysis."""
    counts = {name: 0 for name in _TIER_ORDER}
    for tc in tiered:
        counts[tc.tier.value] = counts.get(tc.tier.value, 0) + 1
    return counts


def tier_stability(
    a: Sequence[TieredClaim], b: Sequence[TieredClaim]
) -> tuple[float, int, int]:
    """SE-3 tier stability = the fraction of claims whose `Tier` is IDENTICAL across two tierings
    (§3 Q6). Computed over the `claim_id` INTERSECTION; returns `(fraction, n_agree, n_shared)`. An
    empty intersection yields `(1.0, 0, 0)` — vacuously stable, and the count makes that legible.
    The SE-3 ≥80% bar is applied in analysis (frozen §2.2), never here."""
    a_tier = {tc.fiber.claim_id: tc.tier.value for tc in a}
    b_tier = {tc.fiber.claim_id: tc.tier.value for tc in b}
    shared = sorted(set(a_tier) & set(b_tier))
    if not shared:
        return 1.0, 0, 0
    agree = sum(1 for cid in shared if a_tier[cid] == b_tier[cid])
    return agree / len(shared), agree, len(shared)


def _evidence_section(
    *, commit_sha: str, fibers_result: FibersResult | None, control: ControlOutcome | None,
    cut: CertifiedCut | None, determinism: DeterminismCheck | None,
    selfmod_posture: SelfmodPosture | None, notes: list[str],
) -> CompositeSection:
    """The V1–V5 evidence block (§2.3). V1 sources from `fibers_result.evidence` (config
    fingerprint, lever-registry hash, grid) + `commit_sha` + `corpus_ref`; V2 records the cut or a
    preview note; V3/V4/V5 record the control verdict, determinism check, and selfmod posture."""
    lines: list[str] = ["## V1–V5 · run-validity evidence", ""]
    data: dict[str, Any] = {}

    # V1 — environment pinning.
    if fibers_result is not None:
        ev = fibers_result.evidence
        v1 = {
            "config_fingerprint": ev.base_fingerprint,
            "lever_registry_hash": ev.lever_registry_hash,
            "corpus_ref": fibers_result.corpus_ref,
            "commit_sha": commit_sha,
            "grid": [round(float(x), 6) for x in ev.grid],
            "fibers_spec_hash": dict(sorted(fibers_result.spec_hashes.items())),
        }
    else:
        v1 = {"commit_sha": commit_sha}
        notes.append("V1: no fibers result — config fingerprint / registry hash / corpus_ref / "
                     "grid unrecorded (preview).")
    data["V1"] = v1
    lines += [f"- **V1** config_fingerprint: `{v1.get('config_fingerprint', '(preview)')}`",
              f"  · lever_registry_hash: `{v1.get('lever_registry_hash', '(preview)')}`",
              f"  · corpus_ref: `{v1.get('corpus_ref', '(preview)')}` · commit: `{commit_sha}`",
              f"  · grid: {v1.get('grid', '(preview)')}"]

    # V2 — certified cut.
    if cut is not None:
        v2: dict[str, Any] = {
            "frontier": [list(pair) for pair in cut.frontier],
            "certificates": sorted(c.value if hasattr(c, "value") else str(c)
                                   for c in cut.certificates),
            "evidence": list(cut.evidence),
        }
        lines.append(f"- **V2** certified cut: {len(cut.frontier)} frontier chain(s), "
                     f"certificates {v2['certificates']}")
    else:
        v2 = {"preview": True}
        notes.append("V2: no certified cut supplied — preview (the owner-fired run supplies the "
                     "real cut; no fabrication).")
        lines.append("- **V2** certified cut: _preview — no cut supplied_")
    data["V2"] = v2

    # V3 — control battery.
    if control is not None:
        data["V3"] = {
            "green": control.green,
            "noise_settled_rate": control.noise_settled_rate,
            "planted_reached_settled": control.planted_reached_settled,
            "tiered_precision": control.tiered_precision,
            "baseline_precision": control.baseline_precision,
        }
        lines.append(f"- **V3** controls: **{'GREEN' if control.green else 'RED — run INVALID'}** "
                     f"(noise {control.noise_settled_rate:.4f}, planted "
                     f"{control.planted_reached_settled}, tiered {control.tiered_precision:.4f} vs "
                     f"{control.baseline_precision:.4f})")
    else:
        data["V3"] = {"preview": True}
        notes.append("V3: no control outcome supplied — preview.")
        lines.append("- **V3** controls: _preview — not run_")

    # V4 — determinism.
    if determinism is not None:
        data["V4"] = {"cell": determinism.cell, "bitwise_identical": determinism.bitwise_identical}
        lines.append(f"- **V4** determinism: cell `{determinism.cell}` bit-wise identical: "
                     f"{determinism.bitwise_identical}")
    else:
        data["V4"] = {"preview": True}
        notes.append("V4: no determinism spot-check supplied — preview.")
        lines.append("- **V4** determinism: _preview — no spot-check_")

    # V5 — selfmod posture.
    if selfmod_posture is not None:
        sp = selfmod_posture
        data["V5"] = {"enabled": sp.enabled, "unattended_enabled": sp.unattended_enabled,
                      "proposal_emitted": sp.proposal_emitted, "proposal_id": sp.proposal_id}
        lines.append(f"- **V5** selfmod: enabled={sp.enabled} unattended={sp.unattended_enabled} "
                     f"proposal_emitted={sp.proposal_emitted} proposal_id={sp.proposal_id}")
    else:
        data["V5"] = {"preview": True}
        notes.append("V5: no selfmod posture supplied — preview.")
        lines.append("- **V5** selfmod: _preview — posture unrecorded_")

    lines.append("")
    return CompositeSection(key="v_evidence", title="V1–V5 evidence", lines=tuple(lines), data=data)


def _selection_section(sweep_result: SweepResult | None, notes: list[str]) -> CompositeSection:
    """SE-1 — the curve + selection (+ proposal id if emitted). Reads the optimizer's verdict; never
    re-derives it (the analysis rule is frozen, §2.2)."""
    lines: list[str] = ["## SE-1 · curve + selection", ""]
    if sweep_result is None:
        notes.append("SE-1: no sweep result — selection section omitted (preview).")
        return CompositeSection(key="se1_selection", title="SE-1 selection",
                                lines=("## SE-1 · curve + selection", "", "_preview — no run_", ""),
                                data={"preview": True})
    r = sweep_result
    lines += [
        f"- lever `{r.lever}` · select_pipeline `{r.select_pipeline}` · direction {r.direction}",
        f"- current={r.current} · ε={r.epsilon:.4f} · **selected={r.selected}**"
        f"{'  (degenerate argmax)' if r.degenerate_argmax else ''}",
        f"- proposal: {'#' + str(r.proposal_id) if r.proposal_emitted else 'none emitted'}",
        "",
        "| σ | ȳ | ±half | admissible |", "|---|---|---|---|",
    ]
    for p in r.curve:
        lines.append(f"| {p.value} | {p.mean:.4f} | {p.halfwidth:.4f} | "
                     f"{'yes' if p.admissible else 'NO'} |")
    lines += ["", *[f"- {n}" for n in r.notes], ""]
    data = {
        "lever": r.lever, "select_pipeline": r.select_pipeline, "direction": r.direction,
        "current": r.current, "epsilon": r.epsilon, "selected": r.selected,
        "degenerate_argmax": r.degenerate_argmax, "proposal_emitted": r.proposal_emitted,
        "proposal_id": r.proposal_id,
        "curve": [{"value": p.value, "mean": p.mean, "halfwidth": p.halfwidth,
                   "admissible": p.admissible, "grid_index": p.grid_index} for p in r.curve],
        "notes": list(r.notes),
    }
    return CompositeSection(key="se1_selection", title="SE-1 selection", lines=tuple(lines),
                            data=data)


def _fibers_section(fibers_result: FibersResult | None, notes: list[str]) -> CompositeSection:
    """SE-2 — the fibers summary. Registered-names discipline: each aggregate metric name displayed
    is checked with `registry.is_registered`; an unregistered one is RECORDED (the report.py
    precedent), never silently shown as a store reading."""
    from eval.harness import registry

    lines: list[str] = ["## SE-2 · σ-fibers summary", ""]
    if fibers_result is None or not fibers_result.aggregates:
        notes.append("SE-2: no fibers aggregates — summary omitted (preview / no claims).")
        return CompositeSection(key="se2_fibers", title="SE-2 fibers",
                                lines=("## SE-2 · σ-fibers summary", "",
                                       "_preview — no fibers_", ""),
                                data={"preview": True})
    data: dict[str, Any] = {"pipelines": {}}
    for pipeline in sorted(fibers_result.aggregates):
        agg = fibers_result.aggregates[pipeline]
        for name in agg:
            if not registry.is_registered(name):
                notes.append(f"SE-2: metric {name!r} is UNREGISTERED — displayed as-written, not "
                             "a store reading (report.py precedent; §2.3 registered-names rule).")
        data["pipelines"][pipeline] = dict(agg)
        summary = ", ".join(f"{n.split('.')[-1]}={v:.4f}" for n, v in sorted(agg.items()))
        lines.append(f"- **{pipeline}**: {summary}")
    lines.append("")
    return CompositeSection(key="se2_fibers", title="SE-2 fibers", lines=tuple(lines), data=data)


def _tiers_section(
    tiered: Sequence[TieredClaim], tiered_alt: Sequence[TieredClaim] | None, notes: list[str]
) -> CompositeSection:
    """SE-3 — tier occupancy + stability. Occupancy from `tiered`; stability from the pair
    `(tiered, tiered_alt)` when the alternate tiering is supplied, else recorded as uncomputed."""
    occ = tier_occupancy(tiered)
    total = sum(occ.values())
    occ_str = ", ".join(f"{k}={v}" for k, v in occ.items())
    lines: list[str] = ["## SE-3 · tier occupancy + stability", "",
                        f"- occupancy (n={total}): {occ_str}"]
    settled_frac = (occ.get("settled", 0) / total) if total else 0.0
    lines.append(f"- SETTLED fraction: {settled_frac:.4f}")
    data: dict[str, Any] = {"occupancy": occ, "n": total, "settled_fraction": settled_frac}
    if tiered_alt is not None:
        frac, agree, n_inter = tier_stability(tiered, tiered_alt)
        lines.append(f"- stability: {frac:.4f} ({agree}/{n_inter} claims tier-stable)")
        data["stability"] = {"fraction": frac, "agree": agree, "n_intersection": n_inter}
    else:
        notes.append("SE-3: no alternate tiering supplied — tier stability not computed (single "
                     "tiering).")
        data["stability"] = None
    lines.append("")
    return CompositeSection(key="se3_tiers", title="SE-3 tiers", lines=tuple(lines), data=data)


def _ab_section(ab_report: Report | None, notes: list[str]) -> CompositeSection:
    """The E4 A/B report (§2.3) — embedded as its own rendered model so the composite carries the
    per-pipeline splits + curves + cost appendix with every figure's key intact."""
    from eval.harness.report import render_markdown as report_md

    if ab_report is None:
        notes.append("E4 A/B: no report supplied — omitted (preview).")
        return CompositeSection(key="ab_report", title="E4 A/B",
                                lines=("## E4 · A/B report", "", "_preview — no report_", ""),
                                data={"preview": True})
    body = report_md(ab_report).splitlines()
    lines = ["## E4 · A/B report", "", *body, ""]
    return CompositeSection(key="ab_report", title="E4 A/B", lines=tuple(lines),
                            data={"report": asdict(ab_report)})


def _blind_section(blind: BlindJudgment | None, notes: list[str]) -> CompositeSection:
    """SE-3 blind judgment — post-unblinding, the tier × rating cross-tab. DESCRIPTIVE only (the
    bars
    are read in analysis, §2.2). Absent ⇒ 'pending' (rate before unblinding)."""
    if blind is None:
        return CompositeSection(
            key="blind_judgment", title="blind judgment",
            lines=("## SE-3 · blind judgment", "",
                   "_pending — rate before unblinding; sealed labels not yet joined_", ""),
            data={"pending": True})
    # tier × rating cross-tab over the claim-id intersection of ratings + labels.
    ratings = ("real connection", "plausible", "noise")
    crosstab: dict[str, dict[str, int]] = {t: {r: 0 for r in ratings} for t in _TIER_ORDER}
    unjoined = 0
    for cid, rating in sorted(blind.ratings.items()):
        tier = blind.labels.get(cid)
        if tier is None or tier not in crosstab or rating not in ratings:
            unjoined += 1
            continue
        crosstab[tier][rating] += 1
    if unjoined:
        notes.append(f"SE-3 blind: {unjoined} rating(s) had no sealed label or an unknown rating — "
                     "excluded from the cross-tab (no fabrication).")
    lines = ["## SE-3 · blind judgment (post-unblinding)", "",
             "_single-subject calibration evidence — not inferential statistics (§2.2)_", "",
             "| tier | real connection | plausible | noise |", "|---|---|---|---|"]
    for t in _TIER_ORDER:
        row = crosstab[t]
        lines.append(f"| {t} | {row['real connection']} | {row['plausible']} | {row['noise']} |")
    lines.append("")
    return CompositeSection(key="blind_judgment", title="blind judgment", lines=tuple(lines),
                            data={"crosstab": crosstab, "unjoined": unjoined})


def assemble_composite(
    *,
    topic: str,
    date: str,
    commit_sha: str,
    sweep_result: SweepResult | None,
    fibers_result: FibersResult | None,
    tiered: Sequence[TieredClaim],
    control: ControlOutcome | None,
    cut: CertifiedCut | None,
    determinism: DeterminismCheck | None,
    selfmod_posture: SelfmodPosture | None,
    ab_report: Report | None = None,
    tiered_alt: Sequence[TieredClaim] | None = None,
    blind_record: BlindJudgment | None = None,
) -> CompositeReport:
    """Assemble the ONE composite report per run (§2.3) — deterministic, model-free, READ-ONLY over
    every store (it takes already-computed verdicts + a pre-built E4 `Report`; it queries nothing
    and
    emits NO eval-store readings). Every §2.3 section is present; a None piece degrades to a preview
    stub + a coverage note (no silent cap, §2.8). `date`/`commit_sha` are passed in (no clock read —
    determinism). The sections are assembled in a FIXED order so `render_json` is byte-stable."""
    notes: list[str] = []
    sections = (
        _evidence_section(commit_sha=commit_sha, fibers_result=fibers_result, control=control,
                          cut=cut, determinism=determinism, selfmod_posture=selfmod_posture,
                          notes=notes),
        _selection_section(sweep_result, notes),
        _fibers_section(fibers_result, notes),
        _tiers_section(tiered, tiered_alt, notes),
        _ab_section(ab_report, notes),
        _blind_section(blind_record, notes),
    )
    return CompositeReport(topic=topic, date=date, commit_sha=commit_sha, sections=sections,
                           coverage_notes=tuple(notes))


def render_composite_markdown(report: CompositeReport) -> str:
    """The composite, human-rendered — the SAME model `render_composite_json` serializes, so they
    cannot drift. Every section prints; coverage notes last."""
    lines: list[str] = [f"# σ-sweep experiment · {report.topic}", "",
                        f"_date: {report.date}_ · _commit: {report.commit_sha}_",
                        "_pre-registration: dn-sigma-sweep-experiment @ d932670 (FROZEN)_", ""]
    for section in report.sections:
        lines += [*section.lines]
    lines += ["## Coverage notes", ""]
    lines += [f"- {n}" for n in report.coverage_notes] or ["- none — full coverage."]
    lines.append("")
    return "\n".join(lines)


def render_composite_json(report: CompositeReport) -> str:
    """The composite, machine-rendered — deterministic (`sort_keys`)."""
    return json.dumps(
        {
            "topic": report.topic,
            "date": report.date,
            "commit_sha": report.commit_sha,
            "sections": [{"key": s.key, "title": s.title, "data": s.data} for s in report.sections],
            "coverage_notes": list(report.coverage_notes),
        },
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    ) + "\n"


def write_composite(report: CompositeReport, *, root: str | Path = "data/reports") -> Path:
    """Write `composite.md` + `composite.json` into `<root>/<date>-<topic>/` and return that dir.
    The
    only FS write — into `data/reports/` (∉ MIRROR_READABLE, local, no egress), never a store."""
    out_dir = Path(root) / f"{report.date}-{report.topic}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "composite.md").write_text(render_composite_markdown(report), encoding="utf-8")
    (out_dir / "composite.json").write_text(render_composite_json(report), encoding="utf-8")
    return out_dir
