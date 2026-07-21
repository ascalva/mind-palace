"""The stratum member-set pin (bp-081 Item 7; dn-synchronic-diachronic-dreamer §2.6-1).

`tests/unit/test_scope.py` proves the lattice LAWS hold over the extended member set; this file is
the narrower guard the plan carries beside it: it PINS the exact `Stratum` membership and the three
structural facts that make HYPOTHETICAL the counterfactual OVERLAY the note designs —

  1. it is a member of R (grantable vocabulary), so a scope can name it;
  2. it is NOT in ⊤_Σ (unlike every ordinary base stratum) — "default grants exclude it" is
     structural, so the fullest ordinary grant cannot see staged rows; and
  3. it is NOT the denylist (unlike FOUNDATION) — a scope that NAMES it is admissible.

The pin fails loudly if a later edit weakens the member set or lets the overlay drift into ⊤_Σ (a
laundering path) or into 𝔇 (making a legitimate counterfactual grant unbuildable).
"""

from __future__ import annotations

from core.scope import (
    DENYLIST_IDEAL,
    PRIVATE_STRATA,
    Authority,
    Clock,
    EdgeScope,
    Scope,
    Stratum,
    StratumScope,
    Tier,
    TimeScope,
    Window,
    admissible,
)

# The exact member set of R after H-0. Enumerated so any addition/removal/rename is a deliberate,
# reviewed act (the DIALOGUE precedent pinned the same way). HYPOTHETICAL joins as one overlay
# element; FOUNDATION remains the denylist; nothing else changed.
_EXPECTED_MEMBERS = {
    "mirror", "mirror_authored",
    "curated", "observed", "ops",
    "reference", "reference_repo",
    "interpreted", "world",
    "dialogue", "dialogue_transcript", "dialogue_artifact",
    "exhaust",
    "hypothetical",
    "foundation",
}


def test_stratum_member_set_is_pinned():
    """The full `Stratum` enum, pinned by value — H-0 added `hypothetical`; AL-3 (dn-agentic-loop
    §2.4b EX-1) adds exactly `exhaust`, nothing else."""
    assert {s.value for s in Stratum} == _EXPECTED_MEMBERS
    assert Stratum.HYPOTHETICAL.value == "hypothetical"
    assert Stratum.EXHAUST.value == "exhaust"


def test_hypothetical_is_an_overlay_not_a_refinement():
    """An overlay pulls in no parent/child under downward closure — `of(HYPOTHETICAL)` is exactly
    the singleton, and no other stratum's downset contains it (it refines nothing, nothing refines
    it)."""
    assert StratumScope.of(Stratum.HYPOTHETICAL).strata == frozenset({Stratum.HYPOTHETICAL})
    for base in Stratum:
        if base is Stratum.HYPOTHETICAL:
            continue
        assert Stratum.HYPOTHETICAL not in StratumScope.of(base).strata


def test_hypothetical_absent_from_top_but_present_when_named():
    """The load-bearing asymmetry: ⊤_Σ omits HYPOTHETICAL (no ordinary grant sees staged rows), yet
    an explicit `of(HYPOTHETICAL, …)` names it. This makes the Σ-visibility test structural."""
    assert Stratum.HYPOTHETICAL not in StratumScope.top().strata
    assert Stratum.HYPOTHETICAL in StratumScope.of(Stratum.HYPOTHETICAL, Stratum.MIRROR).strata


def test_hypothetical_is_not_the_denylist():
    """FOUNDATION is ungrantable (𝔇); HYPOTHETICAL is grantable when named — the two exclusions from
    ⊤_Σ are for OPPOSITE reasons, and only FOUNDATION fails `admissible`."""
    naming_hyp = Scope(StratumScope.of(Stratum.HYPOTHETICAL), EdgeScope.bottom(),
                       TimeScope(Clock.COMMIT, Window.all()), Authority.read_only(),
                       tier=Tier.STATIC_GUARD)
    naming_foundation = Scope(StratumScope(frozenset({Stratum.FOUNDATION})), EdgeScope.bottom(),
                              TimeScope(Clock.COMMIT, Window.all()), Authority.read_only(),
                              tier=Tier.CONVENTION)
    assert admissible(naming_hyp, [DENYLIST_IDEAL])           # named overlay is admissible
    assert not admissible(naming_foundation, [DENYLIST_IDEAL])  # 𝔇 never is


# The exact PRIVATE_STRATA membership pin (bp-086 Item 12; dn-agentic-loop §2.3 G-D). The zone law
# reads off this declared set — any drift in its membership is a deliberate, reviewed act, exactly
# like the `_EXPECTED_MEMBERS` pin above. The widest-exclusion default keeps every stratum but
# `world` (plan §3 Q3: ops/reference IN, owner's call at proposed→ready).
# `exhaust` is excluded too: it is a default-EXCLUDED refinement (AL-3), so `_downward_close` never
# auto-adds it to `⊤_Σ` — PRIVATE_STRATA (derived from ⊤_Σ ∖ {world}) is therefore byte-identical to
# before `exhaust` existed (the additive property, mirroring `hypothetical`).
_EXPECTED_PRIVATE = _EXPECTED_MEMBERS - {"world", "foundation", "hypothetical", "exhaust"}


def test_private_strata_membership_is_pinned():
    """PRIVATE_STRATA = every grantable stratum (⊤_Σ, refinements included) EXCEPT `world`; excludes
    `foundation` (𝔇), the `hypothetical` overlay (not a base stratum), and `exhaust` (a default-
    excluded refinement, never in ⊤_Σ — AL-3 keeps PRIVATE_STRATA byte-identical)."""
    assert {s.value for s in PRIVATE_STRATA} == _EXPECTED_PRIVATE
    assert Stratum.WORLD not in PRIVATE_STRATA
    assert Stratum.FOUNDATION not in PRIVATE_STRATA
    assert Stratum.HYPOTHETICAL not in PRIVATE_STRATA
    assert Stratum.EXHAUST not in PRIVATE_STRATA
