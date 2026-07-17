"""bp-057 — the strength→surfacing gate (SETTLED/HUNCH/RETAINED), F9-validated.

Item 1 (unit): tier assignment at the θ edges; within-tier order follows confidence c(κ) ALONE
(the one-scalar prohibition — a high-pers low-confidence claim never outranks within-tier); RETAINED
never surfaces; the module mutates nothing and imports no store writer (I1); no pers×confidence
fusion (source-level, AST-checked). The recursive-strata §9 never-list is re-asserted: the gate
changes no weight/confidence/promotion — confidence passes through VERBATIM.

Item 2 (F9 validation): the §2.5 protocol run end-to-end over the F1-variant fixtures — the three
ship criteria COMPUTED, landed as keyed `sigma_gate.validation.*` readings, and the ship/park
decision enforced. `surfaced` raises `GateNotValidated` unless the decision ships — never a silent
ship.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import eval.harness.gate as gate_mod
from eval.harness.fibers import ClaimFiber
from eval.harness.gate import (
    GATE_THRESH,
    GateNotValidated,
    GateValidation,
    Tier,
    TieredClaim,
    assign_tiers,
    hunch_section,
    surfaced,
    thresholds,
)
from eval.harness.store import EvalKey, EvalResultsStore, Reading
from tests.quality.fixtures_sigma_gate import (
    NOISE_ROWS,
    PLANTED_IN_NOISE_ROWS,
    PLANTED_ROWS,
    ledger_confidence,
    ledger_labels,
    phase7_fibers,
    single_sigma_precisions,
)

# =============================================================================
# helpers
# =============================================================================


def _fiber(cid: str, pers: float, *, n_cells: int = 1) -> ClaimFiber:
    """A hand-built fiber with a chosen `pers` — the only field the tier depends on."""
    return ClaimFiber(
        claim_id=cid, kind="community", pers=pers, sigma_min=0.55, sigma_max=0.75,
        gap=False, n_cells=n_cells, n_seeds_rule=1,
    )


def _tier_of(tiered: list[TieredClaim], cid: str) -> Tier:
    return next(t.tier for t in tiered if t.fiber.claim_id == cid)


# =============================================================================
# Item 1 — tier assignment
# =============================================================================


def test_gate_thresh_is_the_pinned_dict() -> None:
    """§6 pin, verbatim — exactly the two keys, at the ratified provisional defaults."""
    assert GATE_THRESH == {"theta_weak_cells": 2.0, "theta_strong": 0.5}


def test_thresholds_are_two_over_m_and_half() -> None:
    theta_weak, theta_strong = thresholds(10)
    assert theta_weak == pytest.approx(0.2)      # 2/10
    assert theta_strong == pytest.approx(0.5)


def test_tiers_partition_at_theta_edges() -> None:
    """The §2.5 rule: `pers ≥ θ_strong → SETTLED`; `θ_weak ≤ pers < θ_strong → HUNCH`; else RETAIN.
    m=10 ⇒ θ_weak=0.2, θ_strong=0.5. Boundaries are inclusive at the lower edge of each tier."""
    fibers = [
        _fiber("settled_edge", 0.5),      # == θ_strong → SETTLED
        _fiber("settled_high", 1.0),
        _fiber("hunch_high", 0.49),       # just below θ_strong → HUNCH
        _fiber("hunch_edge", 0.2),        # == θ_weak → HUNCH
        _fiber("retained_edge", 0.19),    # just below θ_weak → RETAINED
        _fiber("retained_low", 0.1),
    ]
    tiered = assign_tiers(fibers, m=10, confidence={})
    assert _tier_of(tiered, "settled_edge") is Tier.SETTLED
    assert _tier_of(tiered, "settled_high") is Tier.SETTLED
    assert _tier_of(tiered, "hunch_high") is Tier.HUNCH
    assert _tier_of(tiered, "hunch_edge") is Tier.HUNCH
    assert _tier_of(tiered, "retained_edge") is Tier.RETAINED
    assert _tier_of(tiered, "retained_low") is Tier.RETAINED


def test_theta_weak_scales_with_grid_m() -> None:
    """θ_weak = 2/m — a claim on exactly 2 of m cells sits at the HUNCH floor; 1 cell is RETAINED.
    (Kills single-cell flickers, §2.5.)"""
    # m=5: pers=2/5=0.4 == θ_weak → HUNCH; pers=1/5=0.2 < 0.4 → RETAINED.
    tiered = assign_tiers([_fiber("two", 0.4), _fiber("one", 0.2)], m=5, confidence={})
    assert _tier_of(tiered, "two") is Tier.HUNCH
    assert _tier_of(tiered, "one") is Tier.RETAINED


def test_coarse_grid_that_collapses_tiers_is_refused() -> None:
    """Boundary condition `0 < θ_weak < θ_strong ≤ 1` (§2.5) enforced fail-closed: m=4 ⇒ θ_weak =
    2/4 = 0.5 = θ_strong ⇒ the tiers cannot separate ⇒ refuse rather than silently degenerate."""
    with pytest.raises(ValueError, match="θ_weak"):
        assign_tiers([_fiber("x", 0.6)], m=4, confidence={})


# =============================================================================
# Item 1 — the one-scalar prohibition + within-tier ordering
# =============================================================================


def test_within_tier_order_follows_confidence_alone() -> None:
    """The one-scalar prohibition (adjudicator.py:20-21): within a tier, ordering is c(κ) ALONE.
    A HIGH-pers LOW-confidence claim must NOT outrank a LOW-pers HIGH-confidence claim WITHIN the
    same tier. Both below are SETTLED (pers ≥ 0.5), so pers must not break their tie."""
    high_pers_low_conf = _fiber("A_highpers_lowconf", 0.95)
    low_pers_high_conf = _fiber("B_lowpers_highconf", 0.55)
    confidence = {"A_highpers_lowconf": 0.10, "B_lowpers_highconf": 0.90}
    tiered = assign_tiers([high_pers_low_conf, low_pers_high_conf], m=10, confidence=confidence)
    settled = [t for t in tiered if t.tier is Tier.SETTLED]
    assert [t.fiber.claim_id for t in settled] == ["B_lowpers_highconf", "A_highpers_lowconf"], (
        "within SETTLED the higher-confidence claim ranks first even though the other has higher "
        "pers — pers must not leak into the within-tier order"
    )


def test_confidence_passes_through_verbatim() -> None:
    """recursive-strata §9 never-list — "no Dreamer-confidence-based weighting of derived content,
    ever". `within_tier_rank` is the supplied c(κ) UNCHANGED — never scaled by pers or anything
    else. The gate manufactures no confidence and mutates none."""
    confidence = {"p": 0.42, "q": 0.99}
    tiered = assign_tiers([_fiber("p", 0.8), _fiber("q", 0.3)], m=10, confidence=confidence)
    ranks = {t.fiber.claim_id: t.within_tier_rank for t in tiered}
    assert ranks["p"] == 0.42 and ranks["q"] == 0.99   # verbatim, not pers-weighted


def test_missing_confidence_defaults_to_zero_not_pers() -> None:
    """An unmapped claim ranks at 0.0 — an ordering default, NEVER `pers` substituted in."""
    tiered = assign_tiers([_fiber("unmapped", 0.9)], m=10, confidence={})
    assert tiered[0].within_tier_rank == 0.0


# =============================================================================
# Item 1 — RETAINED never surfaces; hunch section capped + labelled
# =============================================================================


def test_retained_never_appears_in_surfaced_output() -> None:
    """§2.5: RETAINED is ledger-only. It appears in NEITHER `surfaced` NOR `hunch_section`."""
    fibers = [_fiber("settled", 0.9), _fiber("hunch", 0.3), _fiber("retained", 0.1)]
    tiered = assign_tiers(fibers, m=10, confidence={})
    ok = GateValidation(noise_settled_rate=0.0, planted_reached_settled=True,
                        tiered_precision=1.0, baseline_precision=0.5)
    out_ids = {t.fiber.claim_id for t in surfaced(tiered, cap=10, validation=ok)}
    assert "retained" not in out_ids
    assert "settled" in out_ids and "hunch" in out_ids
    assert "retained" not in {t.fiber.claim_id for t in hunch_section(tiered, cap=10)}


def test_hunch_section_is_capped_and_labelled() -> None:
    """The HUNCH section is capped and every member carries `tier == HUNCH` (that IS the label),
    strongest c(κ) first."""
    fibers = [_fiber(f"h{i}", 0.3) for i in range(5)]
    confidence = {f"h{i}": i / 10 for i in range(5)}   # h4 strongest
    tiered = assign_tiers(fibers, m=10, confidence=confidence)
    section = hunch_section(tiered, cap=2)
    assert len(section) == 2
    assert all(t.tier is Tier.HUNCH for t in section)
    assert [t.fiber.claim_id for t in section] == ["h4", "h3"]


# =============================================================================
# Item 1 — I1: the module mutates nothing / imports no store writer (source-level)
# =============================================================================

_GATE_SRC = Path(gate_mod.__file__).read_text(encoding="utf-8")
_GATE_AST = ast.parse(_GATE_SRC)


def _runtime_imports(tree: ast.Module) -> set[str]:
    """Every module imported at RUNTIME (excluding an `if TYPE_CHECKING:` block)."""
    type_checking_nodes: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            is_tc = (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
                isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
            )
            if is_tc:
                for child in ast.walk(node):
                    type_checking_nodes.add(id(child))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if id(node) in type_checking_nodes:
            continue
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
    return mods


def test_gate_runtime_imports_are_stdlib_only() -> None:
    """I1 made structural: gate.py's RUNTIME namespace holds NO store writer — imports are stdlib
    only (`ClaimFiber` is TYPE_CHECKING-only). If a store/ledger/lever import ever appears at
    runtime, the gate could mutate — this fails loudly."""
    allowed = {"__future__", "collections.abc", "dataclasses", "enum", "typing"}
    runtime = _runtime_imports(_GATE_AST)
    assert runtime <= allowed, f"gate.py has non-stdlib runtime imports: {runtime - allowed}"


def test_gate_calls_no_store_mutator() -> None:
    """No call to any store/ledger/registry mutator anywhere in gate.py (AST — robust to prose in
    docstrings). The gate writes nothing: no ledger, no eval store, no DreamLogEntry, no lever."""
    forbidden = {"put", "add_claim", "start_run", "register", "write", "commit", "execute",
                 "delete", "update", "insert"}
    called: set[str] = set()
    for node in ast.walk(_GATE_AST):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute):
                called.add(fn.attr)
            elif isinstance(fn, ast.Name):
                called.add(fn.id)
    assert not (called & forbidden), f"gate.py calls a mutator: {called & forbidden}"


def test_no_pers_confidence_fusion_anywhere() -> None:
    """The one-scalar prohibition at the source level: NO multiplication in gate.py has `pers` on
    either operand (so pers can never be fused into a confidence/rank). AST — ignores docstrings."""
    offending: list[str] = []
    for node in ast.walk(_GATE_AST):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            left, right = ast.unparse(node.left), ast.unparse(node.right)
            if "pers" in left or "pers" in right:
                offending.append(f"{left} * {right}")
    assert not offending, f"pers appears in a multiplication (scalar fusion): {offending}"


def test_gate_exposes_no_promotion_or_weight_api() -> None:
    """recursive-strata §4 I1 / §9: the gate never promotes and never weights. No public symbol
    hints at a verdict/promotion/weight setter — the gate only tiers and surfaces."""
    forbidden_names = {"promote", "verdict", "set_weight", "weight", "reweight", "ratify"}
    public = {n for n in dir(gate_mod) if not n.startswith("_")}
    leaked = public & forbidden_names
    assert not leaked, f"gate exposes a promotion/weight symbol: {leaked}"


# =============================================================================
# Item 2 — the F9 validation protocol + the ship/park decision
# =============================================================================

_M = 5   # grid points on [0.55, 0.75]: [0.55, 0.60, 0.65, 0.70, 0.75]


def test_planted_clusters_reach_settled() -> None:
    """Criterion (ii): planted structure reaches SETTLED. Two isolated cos≈0.99 clusters each
    persist on the whole grid (pers = 1.0 ≥ θ_strong)."""
    fibers, ledger, grid = phase7_fibers(PLANTED_ROWS, resolution=_M)
    labels = ledger_labels(ledger)
    tiered = assign_tiers(fibers, m=len(grid), confidence=ledger_confidence(ledger))
    planted_settled = [t for t in tiered
                       if t.tier is Tier.SETTLED and labels.get(t.fiber.claim_id) == "planted"]
    assert len(planted_settled) == 2, "both isolated planted clusters must reach SETTLED"
    assert all(t.fiber.pers >= GATE_THRESH["theta_strong"] for t in planted_settled)


def test_noise_settled_rate_is_near_zero() -> None:
    """Criterion (i): the apophenia guard extended along σ. The morphing-star noise produces only
    transient (pers = 1/m) identities ⇒ NONE reach SETTLED ⇒ rate ≈ 0 — strictly below the
    single-σ noise-surfacing rate (the §2.5 falsifier: noise must NOT reach SETTLED at ≥ the
    single-σ baseline rate)."""
    fibers, ledger, grid = phase7_fibers(NOISE_ROWS, resolution=_M)
    labels = ledger_labels(ledger)
    tiered = assign_tiers(fibers, m=len(grid), confidence=ledger_confidence(ledger))
    noise = [t for t in tiered if labels.get(t.fiber.claim_id) == "noise"]
    assert noise, "the noise fixture must actually produce (transient) noise claims"
    settled_noise = [t for t in noise if t.tier is Tier.SETTLED]
    rate = len(settled_noise) / len(noise)
    assert rate <= gate_mod.NOISE_SETTLED_MAX
    # every noise identity is transient → RETAINED (pers < θ_weak); none even reaches HUNCH.
    assert all(t.tier is Tier.RETAINED for t in noise)
    # the single-σ baseline DOES surface noise at every cell → the gate strictly reduces it.
    assert min(single_sigma_precisions(ledger, labels)) < 1.0


def test_tiering_strictly_improves_precision_over_best_single_sigma() -> None:
    """Criterion (iii): persistence-tiering strictly improves surfaced precision over the BEST
    single-σ baseline (max over σ — the strongest, most-conservative reading). On planted-in-noise
    every single σ carries the transient noise FP (precision 2/3 even at the strictest cell), while
    tiering surfaces only the persistent planted structure (precision 1.0)."""
    fibers, ledger, grid = phase7_fibers(PLANTED_IN_NOISE_ROWS, resolution=_M)
    labels = ledger_labels(ledger)
    tiered = assign_tiers(fibers, m=len(grid), confidence=ledger_confidence(ledger))
    surfaced_set = [t for t in tiered if t.tier in (Tier.SETTLED, Tier.HUNCH)]  # RETAINED excluded
    tp = sum(1 for t in surfaced_set if labels.get(t.fiber.claim_id) == "planted")
    fp = sum(1 for t in surfaced_set if labels.get(t.fiber.claim_id) == "noise")
    tiered_precision = tp / (tp + fp) if (tp + fp) else 0.0
    baseline_precision = max(single_sigma_precisions(ledger, labels))
    assert tiered_precision > baseline_precision, (
        f"tiering must strictly beat the best single σ (tiered={tiered_precision:.3f} vs "
        f"baseline={baseline_precision:.3f})"
    )


def _compute_validation() -> tuple[GateValidation, dict[str, float]]:
    """Run the full §2.5 F9 protocol over the fixtures and COMPUTE the three criteria."""
    # (i) noise-only
    nf, nl_ledger, ngrid = phase7_fibers(NOISE_ROWS, resolution=_M)
    nlabels = ledger_labels(nl_ledger)
    ntiered = assign_tiers(nf, m=len(ngrid), confidence=ledger_confidence(nl_ledger))
    noise_claims = [t for t in ntiered if nlabels.get(t.fiber.claim_id) == "noise"]
    noise_settled = [t for t in noise_claims if t.tier is Tier.SETTLED]
    noise_rate = len(noise_settled) / len(noise_claims) if noise_claims else 0.0

    # (ii) + (iii) planted-in-noise
    pf, pl_ledger, pgrid = phase7_fibers(PLANTED_IN_NOISE_ROWS, resolution=_M)
    plabels = ledger_labels(pl_ledger)
    ptiered = assign_tiers(pf, m=len(pgrid), confidence=ledger_confidence(pl_ledger))
    planted_settled = [t for t in ptiered
                       if t.tier is Tier.SETTLED and plabels.get(t.fiber.claim_id) == "planted"]
    planted_ok = len(planted_settled) >= 2

    surfaced_set = [t for t in ptiered if t.tier in (Tier.SETTLED, Tier.HUNCH)]
    tp = sum(1 for t in surfaced_set if plabels.get(t.fiber.claim_id) == "planted")
    fp = sum(1 for t in surfaced_set if plabels.get(t.fiber.claim_id) == "noise")
    tiered_precision = tp / (tp + fp) if (tp + fp) else 0.0
    baseline_precision = max(single_sigma_precisions(pl_ledger, plabels))

    validation = GateValidation(
        noise_settled_rate=noise_rate,
        planted_reached_settled=planted_ok,
        tiered_precision=tiered_precision,
        baseline_precision=baseline_precision,
    )
    readings = {
        "sigma_gate.validation.noise_settled_rate": validation.noise_settled_rate,
        "sigma_gate.validation.planted_reached_settled": float(validation.planted_reached_settled),
        "sigma_gate.validation.tiered_precision": validation.tiered_precision,
        "sigma_gate.validation.baseline_precision": validation.baseline_precision,
        "sigma_gate.validation.ship": float(validation.ship),
    }
    return validation, readings


def test_f9_ship_decision_lands_as_readings_and_is_enforced() -> None:
    """The §2.5 ship/park decision — COMPUTED, landed as keyed `sigma_gate.validation.*` readings
    (Item 2 acceptance), and ENFORCED. The `surfaced` API is gated on the decision: it raises
    `GateNotValidated` unless all three criteria hold — never a silent ship. RETAINED never
    surfaces.

    This fixture is designed to give the gate a FAIR, honest test (genuine planted structure vs a
    genuine morphing-noise process). The recorded decision is what governs; the journal carries the
    three values verbatim."""
    validation, readings = _compute_validation()

    # the readings LAND (in-memory eval store — the module writes nothing itself, I1).
    store = EvalResultsStore(":memory:")
    key = EvalKey(spec_hash="sigma_gate/v1", corpus_ref="f9-fixtures",
                  config_fingerprint="f9", seed=0)
    for name, value in readings.items():
        store.put(Reading(key=key, metric_name=name, value=float(value),
                          type_tag="Val(sigma_gate)"))
    assert len(store.query()) == len(readings)

    # the three criteria — the recorded ship/park verdict.
    if validation.ship:
        # SHIP: the gate's quality tests join the suite green; surfacing is live.
        fibers, ledger, grid = phase7_fibers(PLANTED_IN_NOISE_ROWS, resolution=_M)
        labels = ledger_labels(ledger)
        tiered = assign_tiers(fibers, m=len(grid), confidence=ledger_confidence(ledger))
        out = surfaced(tiered, cap=5, validation=validation)
        assert out, "a shipped gate surfaces the persistent planted structure"
        assert all(labels.get(t.fiber.claim_id) == "planted" for t in out), (
            "only planted (persistent) structure is surfaced — the transient noise is filtered"
        )
        assert all(t.tier is not Tier.RETAINED for t in out)
    else:
        # PARK: the surfaced API stays closed — never a silent ship (the sanctioned outcome).
        dummy = assign_tiers([_fiber("x", 0.9)], m=10, confidence={})
        with pytest.raises(GateNotValidated):
            surfaced(dummy, cap=5, validation=validation)


def test_surfaced_refuses_when_not_validated() -> None:
    """Never a silent ship: a NON-shipping validation closes the surfaced API regardless of the
    tiering."""
    parked = GateValidation(noise_settled_rate=0.9, planted_reached_settled=False,
                           tiered_precision=0.4, baseline_precision=0.6)
    assert not parked.ship
    assert len(parked.failing_clauses()) == 3
    tiered = assign_tiers([_fiber("s", 0.9)], m=10, confidence={})
    with pytest.raises(GateNotValidated, match="not passed F9 validation"):
        surfaced(tiered, cap=5, validation=parked)
