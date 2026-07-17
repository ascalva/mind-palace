"""bp-058 Item 2 — the blind-sample generator (SE-3).

Pins the SE-3 blinding discipline: the sample is stratified evenly across tiers (8/8/8 at cap 24, or
all-available with the shortfall RECORDED — no silent cap); it is deterministic given the seed (same
inputs ⇒ identical selection AND order AND bytes); the presentation leaks NO tier/pers/label; and
the labels live in a DISTINCT sealed artifact carrying the `claim_id → tier` join, opened only at
unblinding.
"""

from __future__ import annotations

from eval.harness.experiment import (
    generate_blind_sample,
    render_blind_presentation,
    render_sealed_labels,
)
from eval.harness.fibers import ClaimFiber
from eval.harness.gate import Tier, TieredClaim


def _tc(cid: str, tier: Tier) -> TieredClaim:
    """A TieredClaim of a chosen tier — pers is irrelevant to the generator (it samples by tier)."""
    fiber = ClaimFiber(claim_id=cid, kind="community", pers=0.5, sigma_min=0.55, sigma_max=0.75,
                       gap=False, n_cells=1, n_seeds_rule=1)
    return TieredClaim(fiber=fiber, tier=tier, within_tier_rank=0.0)


def _balanced_pool(n_per_tier: int = 10) -> list[TieredClaim]:
    out: list[TieredClaim] = []
    for tier, prefix in ((Tier.SETTLED, "s"), (Tier.HUNCH, "h"), (Tier.RETAINED, "r")):
        out += [_tc(f"{prefix}{i:02d}", tier) for i in range(n_per_tier)]
    return out


def _content_for(pool: list[TieredClaim]) -> dict[str, str]:
    return {tc.fiber.claim_id: f"claim {tc.fiber.claim_id} connects X and Y" for tc in pool}


def test_stratified_8_8_8_at_cap_24() -> None:
    """A balanced pool (≥8 per tier) yields exactly 8 from each tier at cap 24 (≤24 total)."""
    pool = _balanced_pool(10)
    sample = generate_blind_sample(pool, _content_for(pool), seed=7, cap=24)
    assert len(sample.presentation) == 24
    tiers = list(sample.sealed_labels.values())
    assert tiers.count("settled") == 8
    assert tiers.count("hunch") == 8
    assert tiers.count("retained") == 8


def test_determinism_same_seed_identical_bytes() -> None:
    """Same (tiered, content, seed, cap) ⇒ identical selection, order, and rendered bytes (V4)."""
    pool = _balanced_pool(10)
    content = _content_for(pool)
    a = generate_blind_sample(pool, content, seed=42, cap=24)
    b = generate_blind_sample(pool, content, seed=42, cap=24)
    assert [it.claim_id for it in a.presentation] == [it.claim_id for it in b.presentation]
    assert a.sealed_labels == b.sealed_labels
    assert render_blind_presentation(a, date="2026-07-17", topic="t") == \
        render_blind_presentation(b, date="2026-07-17", topic="t")
    assert render_sealed_labels(a) == render_sealed_labels(b)


def test_shortfall_is_recorded_never_silently_capped() -> None:
    """A stratum below target samples all it has AND records a note (no silent cap, §2.8)."""
    pool = [_tc("s0", Tier.SETTLED), _tc("s1", Tier.SETTLED)]  # only 2 SETTLED, 0 HUNCH, 0 RETAINED
    pool += [_tc(f"h{i}", Tier.HUNCH) for i in range(10)]
    sample = generate_blind_sample(pool, _content_for(pool), seed=1, cap=24)
    tiers = list(sample.sealed_labels.values())
    assert tiers.count("settled") == 2          # all available, not 8
    assert tiers.count("retained") == 0
    joined = " ".join(sample.notes)
    assert "settled" in joined and "retained" in joined       # both shortfalls recorded


def test_presentation_leaks_no_tier_or_pers() -> None:
    """The blinding is structural: the presentation carries NO tier name, NO 'pers', NO label."""
    pool = _balanced_pool(10)
    sample = generate_blind_sample(pool, _content_for(pool), seed=3, cap=24)
    text = render_blind_presentation(sample, date="2026-07-17", topic="t").lower()
    for leak in ("settled", "hunch", "retained", "pers", "tier"):
        assert leak not in text, f"presentation leaks {leak!r}"
    # the sealed file, by contrast, carries the join.
    for tier in sample.sealed_labels.values():
        assert tier in ("settled", "hunch", "retained")


def test_sealed_labels_are_a_distinct_join_absent_from_presentation() -> None:
    """The sealed artifact holds `claim_id → tier`; the presentation holds no label at all."""
    pool = _balanced_pool(10)
    sample = generate_blind_sample(pool, _content_for(pool), seed=9, cap=24)
    presented_ids = {it.claim_id for it in sample.presentation}
    assert presented_ids == set(sample.sealed_labels)         # same claims, join recoverable
    sealed_json = render_sealed_labels(sample)
    assert "labels" in sealed_json and "presentation_order" in sealed_json


def test_cap_bounds_total_and_content_missing_is_noted() -> None:
    """`cap` bounds the total; a sampled claim with no content is presented blank + a note."""
    pool = _balanced_pool(10)
    content = _content_for(pool)
    content.pop(next(iter(content)))                          # drop one claim's content
    sample = generate_blind_sample(pool, content, seed=5, cap=6)   # 2 per tier
    assert len(sample.presentation) <= 6
    # the missing-content note fires iff that claim was sampled; assert the mechanism when present.
    if any(it.content == "" for it in sample.presentation):
        assert any("no content" in n for n in sample.notes)
