"""bp-058 Item 3 — the composite report assembler (§2.3 contract).

Pins the §2.3 contract: every required section is present (E4 A/B + SE-1 selection + SE-2 fibers +
SE-3 tier occupancy/stability + control outcomes + the V1–V5 evidence block incl. the certified cut
+ the blind-judgment record); the assembly is deterministic (same inputs + date + commit ⇒ identical
bytes); a None piece degrades to a preview stub + a coverage note (no silent cap); the registered-
names discipline holds (an unregistered displayed metric is RECORDED, not silently shown as a store
reading); and the assembler emits nothing to any store (it takes no store — structural).
"""

from __future__ import annotations

from core.temporal.spine import Certificate, CertifiedCut
from eval.harness.experiment import (
    BlindJudgment,
    ControlOutcome,
    DeterminismCheck,
    SelfmodPosture,
    assemble_composite,
    render_composite_json,
    render_composite_markdown,
    tier_occupancy,
    tier_stability,
)
from eval.harness.fibers import ClaimFiber, FibersEvidence, FibersResult
from eval.harness.gate import GateValidation, Tier, TieredClaim
from eval.harness.report import Report
from eval.harness.sweep import CurvePoint, SweepResult

_SECTION_KEYS = {"v_evidence", "se1_selection", "se2_fibers", "se3_tiers", "ab_report",
                 "blind_judgment"}


def _tc(cid: str, tier: Tier, pers: float = 0.5) -> TieredClaim:
    fiber = ClaimFiber(claim_id=cid, kind="community", pers=pers, sigma_min=0.55, sigma_max=0.75,
                       gap=False, n_cells=1, n_seeds_rule=1)
    return TieredClaim(fiber=fiber, tier=tier, within_tier_rank=0.0)


def _green_control() -> ControlOutcome:
    v = GateValidation(noise_settled_rate=0.0, planted_reached_settled=True,
                       tiered_precision=1.0, baseline_precision=0.667)
    return ControlOutcome(noise_settled_rate=0.0, planted_reached_settled=True,
                          tiered_precision=1.0, baseline_precision=0.667, validation=v,
                          grid=(0.55, 0.6, 0.65, 0.7, 0.75))


def _fibers(agg_name: str = "sigma_persistence.mean") -> FibersResult:
    ev = FibersEvidence(grid=(0.55, 0.6, 0.65, 0.7, 0.75), base_fingerprint="fp123",
                        lever_registry_hash="reg456")
    return FibersResult(
        corpus_ref="digest789", evidence=ev,
        fibers={"dream_v2": ()}, aggregates={"dream_v2": {agg_name: 0.42}},
        spec_hashes={"dream_v2": "spec_dv2"}, readings_written=5, notes=(),
    )


def _sweep() -> SweepResult:
    curve = (
        CurvePoint(value=0.6, mean=0.9, halfwidth=0.01, admissible=True, grid_index=1, n_seeds=5),
        CurvePoint(value=0.65, mean=0.9, halfwidth=0.01, admissible=True, grid_index=2, n_seeds=5),
    )
    return SweepResult(
        spec_name="dreamer-sigma-ab", lever="dream_rnd_sigma", grid=(0.6, 0.65), curve=curve,
        select_pipeline="dream_v2", current=0.65, selected=0.65, epsilon=0.02, direction="maximize",
        degenerate_argmax=False, guardrails_captured=True, proposal_emitted=True, proposal_id=7,
        evidence_keys=(), notes=("emitted PROPOSED proposal #7",),
    )


def _cut() -> CertifiedCut:
    return CertifiedCut(frontier=(("versions:docA", 3),),
                        certificates=frozenset({Certificate.COMMIT}), evidence=("commit:abc",))


def _full_kwargs() -> dict[str, object]:
    tiered = [_tc("s0", Tier.SETTLED), _tc("h0", Tier.HUNCH), _tc("r0", Tier.RETAINED)]
    tiered_alt = [_tc("s0", Tier.SETTLED), _tc("h0", Tier.RETAINED), _tc("r0", Tier.RETAINED)]
    return dict(
        topic="sigma-run1", date="2026-07-17", commit_sha="deadbeef",
        sweep_result=_sweep(), fibers_result=_fibers(), tiered=tiered,
        control=_green_control(), cut=_cut(),
        determinism=DeterminismCheck(cell="(0.65,seed0)", bitwise_identical=True),
        selfmod_posture=SelfmodPosture(enabled=True, unattended_enabled=False,
                                       proposal_emitted=True, proposal_id=7),
        ab_report=Report(topic="ab", date="2026-07-17", figures=(), coverage_notes=()),
        tiered_alt=tiered_alt,
        blind_record=BlindJudgment(ratings={"s0": "real connection", "h0": "plausible"},
                                   labels={"s0": "settled", "h0": "hunch"}),
    )


def test_every_section_2_3_is_present() -> None:
    report = assemble_composite(**_full_kwargs())  # type: ignore[arg-type]
    assert {s.key for s in report.sections} == _SECTION_KEYS
    # V1–V5 all recorded in the evidence block.
    ev = next(s for s in report.sections if s.key == "v_evidence")
    assert set(ev.data) == {"V1", "V2", "V3", "V4", "V5"}
    assert ev.data["V1"]["config_fingerprint"] == "fp123"
    assert ev.data["V2"]["certificates"] == ["commit"]
    assert ev.data["V3"]["green"] is True
    assert ev.data["V4"]["bitwise_identical"] is True
    assert ev.data["V5"]["proposal_id"] == 7


def test_render_is_deterministic() -> None:
    a = assemble_composite(**_full_kwargs())  # type: ignore[arg-type]
    b = assemble_composite(**_full_kwargs())  # type: ignore[arg-type]
    assert render_composite_json(a) == render_composite_json(b)
    assert render_composite_markdown(a) == render_composite_markdown(b)


def test_preview_degrades_gracefully_with_coverage_notes() -> None:
    """All-None pieces ⇒ every section still present as a preview stub, each in coverage notes."""
    report = assemble_composite(
        topic="preview", date="2026-07-17", commit_sha="abc",
        sweep_result=None, fibers_result=None, tiered=[], control=None, cut=None,
        determinism=None, selfmod_posture=None,
    )
    assert {s.key for s in report.sections} == _SECTION_KEYS
    joined = " ".join(report.coverage_notes).lower()
    for token in ("v1", "v2", "v3", "v4", "v5", "se-1", "se-2"):
        assert token in joined
    # the certified-cut preview is explicit, never fabricated.
    ev = next(s for s in report.sections if s.key == "v_evidence")
    assert ev.data["V2"] == {"preview": True}


def test_unregistered_metric_is_recorded_not_silently_shown() -> None:
    """§2.3 registered-names discipline: a displayed aggregate under an UNREGISTERED name lands a
    coverage note (the report.py precedent); a registered name is clean."""
    kwargs = _full_kwargs()
    kwargs["fibers_result"] = _fibers(agg_name="bogus.unregistered_metric")
    report = assemble_composite(**kwargs)  # type: ignore[arg-type]
    assert any("unregistered" in n.lower() for n in report.coverage_notes)

    kwargs["fibers_result"] = _fibers(agg_name="sigma_persistence.mean")   # registered
    clean = assemble_composite(**kwargs)  # type: ignore[arg-type]
    assert not any("unregistered" in n.lower() for n in clean.coverage_notes)


def test_tier_occupancy_and_stability() -> None:
    tiered = [_tc("s0", Tier.SETTLED), _tc("s1", Tier.SETTLED), _tc("h0", Tier.HUNCH)]
    assert tier_occupancy(tiered) == {"settled": 2, "hunch": 1, "retained": 0}
    alt = [_tc("s0", Tier.SETTLED), _tc("s1", Tier.HUNCH), _tc("h0", Tier.HUNCH)]  # s1 moved
    frac, agree, n = tier_stability(tiered, alt)
    assert (agree, n) == (2, 3) and frac == 2 / 3


def test_blind_crosstab_is_descriptive_join() -> None:
    report = assemble_composite(**_full_kwargs())  # type: ignore[arg-type]
    blind = next(s for s in report.sections if s.key == "blind_judgment")
    ct = blind.data["crosstab"]
    assert ct["settled"]["real connection"] == 1
    assert ct["hunch"]["plausible"] == 1
