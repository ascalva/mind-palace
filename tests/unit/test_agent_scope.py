"""The agent taxonomy's role constructors + conformance (bp-070 D2, dn-agent-taxonomy §2.1).

Each role is a *region* of the ratified `(Σ, E, T, A)` lattice; a constructor must land an agent
INSIDE its region and REFUSE an out-of-region request, and `assert_conforms` must reject a handle
that exceeds the declared scope. These tests are that guard — the D2 analog of the Views'
declared-vs-actual `SCOPE` check (`test_view_scopes.py`). Composition is the EXISTING `Scope.meet`
(no new lattice ops), so the delegation law is reused verbatim, not re-proved here.
"""

from __future__ import annotations

import pytest

from core.agent_scope import (
    ConformanceError,
    Handle,
    assert_conforms,
    dreamer_scope,
    external_executor,
    external_proposer,
    integrator_scope,
    internal_actor,
    query_scope,
    sensor_scope,
)
from core.scope import (
    PRIVATE_STRATA,
    Clock,
    Privilege,
    Stratum,
    StratumScope,
    Tier,
    WorldReach,
    zone_admissible,
)


# ── each constructor lands inside its §2.1 region ─────────────────────────────────────────────
def test_sensor_scope_is_own_stratum_no_edges():
    """Sensor: its OWN stratum (downset), NO edges, the sensor-dual write bit W_Σ=1, W_world=NONE,
    clocked on its stratum's event clock N_s."""
    s = sensor_scope(Stratum.DIALOGUE)
    assert s.sigma.strata == StratumScope.of(Stratum.DIALOGUE).strata      # downset (+ refinements)
    assert Stratum.DIALOGUE_TRANSCRIPT in s.sigma.strata
    assert s.edges.fibers == frozenset()                        # produces nodes, not edges
    assert s.authority.privilege is Privilege.READ
    assert s.authority.store_write == 1                                    # the sensor dual
    assert s.authority.world is WorldReach.NONE
    assert s.time.clock is Clock.N_S
    assert s.tier is Tier.STATIC_GUARD


def test_query_scope_is_read_only_store_write_zero():
    """Query agent: reads a grantable subset, writes NOTHING structural (W_Σ=0), no world reach."""
    s = query_scope([Stratum.DIALOGUE, Stratum.OBSERVED])
    assert s.sigma.strata == StratumScope.of(Stratum.DIALOGUE, Stratum.OBSERVED).strata
    assert s.authority.privilege is Privilege.READ
    assert s.authority.store_write == 0                                    # the defining bit
    assert s.authority.world is WorldReach.NONE
    assert "C" in s.edges.fibers                                # may READ every edge class


def test_integrator_scope_spans_two_base_strata_and_writes_c_or_f():
    """Integrator: ≥ 2 BASE strata, edge-store writes over fibers ⊆ {C, F}, W_Σ=1, W_world=NONE."""
    s = integrator_scope(
        [(Stratum.DIALOGUE_TRANSCRIPT, "L1-action-log"), (Stratum.OBSERVED, "commit-ledger")],
        ["C", "F"],
    )
    assert {Stratum.DIALOGUE_TRANSCRIPT, Stratum.OBSERVED} <= s.sigma.strata
    assert s.edges.fibers == frozenset({"C", "F"})
    assert s.authority.store_write == 1
    assert s.authority.world is WorldReach.NONE


def test_dreamer_scope_is_apex_all_fibers():
    """Dreamer: up to ⊤_Σ per grant, ALL edge fibers, interpreted-only projection-write (W_Σ=1)."""
    s = dreamer_scope([Stratum.DIALOGUE, Stratum.OBSERVED, Stratum.MIRROR])
    assert s.edges.fibers == frozenset({"F", "D", "C"})                    # all edge types
    assert s.authority.store_write == 1
    assert s.authority.world is WorldReach.NONE


# ── the falsifier: a constructor CANNOT express an out-of-region scope ─────────────────────────
def test_integrator_rejects_single_base_stratum():
    """An integrator is inherently multi-strata: naming layers of ONE base stratum (which would be a
    sensor's region) is refused — the 'a constructor expresses an out-of-region scope' falsifier."""
    with pytest.raises(ValueError):
        integrator_scope(
            # both refine the SAME base stratum (dialogue) — a sensor's region, not an integrator's
            [(Stratum.DIALOGUE_TRANSCRIPT, "L0"), (Stratum.DIALOGUE_ARTIFACT, "docs")],
            ["C"],
        )


def test_integrator_rejects_write_fiber_outside_c_f():
    """D (supersession) is the D-machinery's, never an integrator's — a D write grant is refused."""
    with pytest.raises(ValueError):
        integrator_scope(
            [(Stratum.DIALOGUE_TRANSCRIPT, "L1"), (Stratum.OBSERVED, "commit")],
            ["C", "D"],
        )


# ── delegation is monotone — the EXISTING Scope.meet, reused (never widens the parent) ─────────
def test_delegation_meet_never_widens_the_parent():
    """meet(parent, template) ⊑ parent AND ⊑ template for role templates — the ratified delegation
    law reused verbatim (no new lattice op). A wide template cannot launder authority up to a narrow
    parent."""
    narrow = query_scope([Stratum.DIALOGUE])                              # ledger clock (N)
    wide = query_scope([Stratum.DIALOGUE, Stratum.OBSERVED, Stratum.OPS])
    minted = narrow.meet(wide)
    assert minted <= narrow and minted <= wide
    assert minted == narrow                                    # meet with a superset = parent

    # same law over the integrator region (COMMIT clock)
    p = integrator_scope(
        [(Stratum.DIALOGUE_TRANSCRIPT, "L1"), (Stratum.OBSERVED, "commit")], ["C"]
    )
    t = integrator_scope(
        [(Stratum.DIALOGUE_TRANSCRIPT, "L1"), (Stratum.OBSERVED, "commit"),
         (Stratum.REFERENCE_REPO, "docs")],
        ["C", "F"],
    )
    assert p.meet(t) <= p and p.meet(t) <= t


# ── conformance: an agent's actual handles ⊑ its declared scope ────────────────────────────────
def test_assert_conforms_accepts_a_matching_inventory():
    """A sensor over dialogue holding a handle on its refinement `dialogue_transcript` (inside the
    downset) that projection-writes (its W_Σ=1) conforms — no raise."""
    declared = sensor_scope(Stratum.DIALOGUE)
    handles = (
        Handle(name="rawstore", stratum=Stratum.DIALOGUE_TRANSCRIPT, writes_stratum=True),
        Handle(name="chatlog", stratum=Stratum.DIALOGUE_TRANSCRIPT, writes_stratum=True),
    )
    assert_conforms(declared, handles)          # does not raise


def test_assert_conforms_rejects_a_handle_outside_the_declared_sigma():
    """The smuggled-extra-handle falsifier: a sensor over dialogue holding a handle on `observed`
    (outside its declared Σ) is caught."""
    declared = sensor_scope(Stratum.DIALOGUE)
    handles = (Handle(name="smuggled", stratum=Stratum.OBSERVED),)
    with pytest.raises(ConformanceError):
        assert_conforms(declared, handles)


def test_assert_conforms_rejects_projection_write_beyond_authority():
    """A query agent (W_Σ=0) may not hold a projection-writing handle — conformance catches it."""
    declared = query_scope([Stratum.DIALOGUE])
    handles = (Handle(name="writer", stratum=Stratum.DIALOGUE, writes_stratum=True),)
    with pytest.raises(ConformanceError):
        assert_conforms(declared, handles)


def test_assert_conforms_rejects_edge_write_outside_declared_e():
    """A sensor writes no edges (E=⊥); a handle claiming to write fiber C exceeds the declared E."""
    declared = sensor_scope(Stratum.DIALOGUE)
    handles = (Handle(name="edge-writer", stratum=Stratum.DIALOGUE, writes_fiber="C"),)
    with pytest.raises(ConformanceError):
        assert_conforms(declared, handles)


# ── the three ACTOR profiles (dn-agentic-loop §2.3; bp-086 / AL-1) ────────────────────────────
# IA / EA-p / EA-x land in their §2.3 regions AND are zone-admissible BY CONSTRUCTION — IA/EA-p via
# W_world=NONE, EA-x via Σ=⊥. The falsifier here is Item 13's: a constructor that produced a scope
# `zone_admissible` REJECTS. It cannot — proven below.
def test_internal_actor_broad_private_no_world_reach():
    """IA: Σ = ⊤_Σ by default (broad private read), E = ⊤, cut-clock T, A = (READ_PROPOSE, 1, NONE).
    Zone-admissible (reads private, but W_world=NONE)."""
    s = internal_actor()
    assert s.sigma.strata == StratumScope.top().strata            # broad by grant (defaults to top)
    assert s.sigma.strata & PRIVATE_STRATA                        # it DOES read private strata
    assert s.edges.fibers == frozenset({"F", "D", "C"})          # reasons over all edge classes
    assert s.authority.privilege is Privilege.READ_PROPOSE
    assert s.authority.store_write == 1                           # interpreted-tier write
    assert s.authority.world is WorldReach.NONE                   # zero world reach
    assert s.time.clock is Clock.COMMIT                           # a CUT clock (SLICE-safe)
    assert s.tier is Tier.STATIC_GUARD
    assert zone_admissible(s)                                     # admissible BY CONSTRUCTION


def test_internal_actor_respects_the_grant_and_hypothetical_flag():
    """IA never widens past the grant: a narrower `strata` yields that downset; `hypothetical=True`
    names the overlay (still zone-admissible — W_world=NONE)."""
    narrow = internal_actor([Stratum.OPS])
    assert narrow.sigma.strata == StratumScope.of(Stratum.OPS).strata
    assert zone_admissible(narrow)
    staged = internal_actor([Stratum.MIRROR], hypothetical=True)
    assert Stratum.HYPOTHETICAL in staged.sigma.strata           # overlay named explicitly
    assert Stratum.MIRROR_AUTHORED in staged.sigma.strata        # downward closure preserved
    assert zone_admissible(staged)


def test_external_proposer_is_propose_only_mirror_authored():
    """EA-p: Σ = mirror_authored, A = (READ_PROPOSE, W_Σ=0, NONE) — propose-only, writes nothing
    structural, no world reach. Zone-admissible (reads private, W_world=NONE)."""
    s = external_proposer()
    assert s.sigma.strata == StratumScope.of(Stratum.MIRROR_AUTHORED).strata
    assert Stratum.MIRROR_AUTHORED in PRIVATE_STRATA             # it reads a private stratum
    assert s.authority.privilege is Privilege.READ_PROPOSE       # proposes
    assert s.authority.store_write == 0                          # writes NOTHING structural
    assert s.authority.world is WorldReach.NONE                  # no world reach
    assert zone_admissible(s)


def test_external_executor_bottom_sigma_holds_world_reach():
    """EA-x: Σ = ⊥ (never reads the vault — bright line 2), A = (READ, 0, W_world=reach). It HOLDS
    world reach, yet is zone-admissible via Σ=⊥ (antecedent false), NOT via W_world."""
    s = external_executor()
    assert s.sigma.strata == frozenset()                         # ⊥ — reads no corpus stratum
    assert not (s.sigma.strata & PRIVATE_STRATA)                 # reads nothing private
    assert s.edges.fibers == frozenset()
    assert s.authority.privilege is Privilege.READ
    assert s.authority.store_write == 0
    assert s.authority.world is WorldReach.SENSING               # default nonzero world reach
    assert s.authority.world > WorldReach.NONE                   # it genuinely reaches the world
    assert zone_admissible(s)                                    # admissible BY Σ=⊥, not by reach
    # even at the maximal reach it stays admissible — the whole point of the vault-blind executor
    assert zone_admissible(external_executor(WorldReach.IRREVERSIBLE))


def test_all_three_profiles_are_zone_admissible_by_construction():
    """The Item 13 falsifier: NO profile constructor expresses a scope the zone law rejects. IA/EA-p
    via W_world=NONE; EA-x via Σ=⊥."""
    for s in (internal_actor(), internal_actor([Stratum.MIRROR], hypothetical=True),
              external_proposer(), external_proposer([Stratum.MIRROR_AUTHORED]),
              external_executor(), external_executor(WorldReach.IRREVERSIBLE)):
        assert zone_admissible(s)


def test_internal_actor_delegation_never_widens_parent():
    """Composition stays the ratified `Scope.meet`: meet(parent, IA-template) ⊑ parent — a broad IA
    template cannot launder authority up to a narrow parent (both on the IA cut-clock, COMMIT)."""
    parent = internal_actor([Stratum.OPS])                       # a narrow IA parent (COMMIT clock)
    minted = parent.meet(internal_actor())                       # meet with the broad IA template
    assert minted <= parent
    assert minted == parent                                      # meet with a superset = the parent
