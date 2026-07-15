"""The capability-scope algebra's laws (bp-039 Item 2, dn-capability-scope §2.1/§2.2).

The algebra earns its "safe composition" reading only if it is genuinely a lattice and the
delegation move is monotone. These tests are that proof: the lattice laws (idempotent /
commutative / associative / absorptive) on the four coordinates, `⊑` consistent with `meet`, the
PARTIAL T-meet (a cross-clock meet raises, never guesses), delegation-exceeding-parent
unrepresentable (`meet(parent, template) ⊑ parent` always — non-negotiable #6), the SLICE rule,
and the firewall-ideal admissibility. Scopes are enumerated (no randomness) over ONE materialized
clock so windows form a clean lattice; the cross-clock partiality is tested separately.
"""

from __future__ import annotations

import itertools

import pytest

from core.scope import (
    DENYLIST_IDEAL,
    Authority,
    Clock,
    EdgeScope,
    Ideal,
    NoCommonClockError,
    Privilege,
    Scope,
    SliceError,
    Stratum,
    StratumScope,
    Tier,
    TimeScope,
    Window,
    WorldReach,
    admissible,
    common_refinement,
    req_admissible,
)


# ── a small, enumerated population of scopes on ONE clock (COMMIT) ────────────────────────────
def _scope(sigma: StratumScope, edges: EdgeScope, window: Window, auth: Authority) -> Scope:
    return Scope(sigma, edges, TimeScope(Clock.COMMIT, window), auth, tier=Tier.STATIC_GUARD)


def _population() -> list[Scope]:
    """A handful of scopes all on Clock.COMMIT with int-bounded windows (so windows are a proper
    lattice under intersection/hull) — enough to exercise the laws on every pair and triple."""
    sigmas = [
        StratumScope.bottom(),
        StratumScope.of(Stratum.REFERENCE_REPO),
        StratumScope.of(Stratum.REFERENCE),          # pulls in reference_repo (downward closure)
        StratumScope.of(Stratum.OPS),
        StratumScope.top(),
    ]
    edges = [EdgeScope.bottom(), EdgeScope.of("F"), EdgeScope.of("F", "D")]
    windows = [Window.all(), Window.interval(0, 10), Window.interval(4, 8), Window.point(5)]
    auths = [
        Authority.read_only(),
        Authority(Privilege.READ, 1, WorldReach.NONE),
        Authority(Privilege.READ_PROPOSE, 1, WorldReach.SENSING),
    ]
    # A representative cross-section (not the full product — enough distinct points for the laws).
    pop = []
    for i, sigma in enumerate(sigmas):
        pop.append(_scope(sigma, edges[i % len(edges)], windows[i % len(windows)], auths[i % len(auths)]))
    for w in windows:
        pop.append(_scope(StratumScope.of(Stratum.REFERENCE_REPO), EdgeScope.of("F"), w, auths[0]))
    for a in auths:
        pop.append(_scope(StratumScope.of(Stratum.OPS), EdgeScope.bottom(), Window.all(), a))
    return pop


POP = _population()


# ── lattice laws (meet/join) ─────────────────────────────────────────────────────────────────
def test_meet_and_join_idempotent():
    for s in POP:
        assert s.meet(s) == s
        assert s.join(s) == s


def test_meet_and_join_commutative():
    for a, b in itertools.combinations(POP, 2):
        assert a.meet(b) == b.meet(a)
        assert a.join(b) == b.join(a)


def test_meet_and_join_associative():
    for a, b, c in itertools.combinations(POP, 3):
        assert a.meet(b).meet(c) == a.meet(b.meet(c))
        assert a.join(b).join(c) == a.join(b.join(c))


def test_absorption():
    """meet(a, join(a, b)) == a  and  join(a, meet(a, b)) == a — the lattice absorption laws."""
    for a, b in itertools.combinations(POP, 2):
        assert a.meet(a.join(b)) == a
        assert a.join(a.meet(b)) == a


def test_le_consistent_with_meet():
    """`a ⊑ b  ⟺  meet(a, b) == a` — the partial order IS the meet (tier is compare=False, so `==`
    is on the four lattice coordinates)."""
    for a, b in itertools.product(POP, repeat=2):
        assert (a <= b) == (a.meet(b) == a)


# ── delegation is monotone — non-negotiable #6 ───────────────────────────────────────────────
def test_delegation_never_exceeds_parent():
    """meet(parent, template) ⊑ parent AND ⊑ template, for EVERY pair — a minted child cannot hold
    more than its parent, however wide the template. This is #6 as a runtime law."""
    for parent, template in itertools.product(POP, repeat=2):
        minted = parent.meet(template)
        assert minted <= parent
        assert minted <= template


def test_a_wider_template_cannot_widen_the_child():
    """A template that is strictly wider than the parent still yields a child ⊑ parent — delegation
    cannot launder authority upward (the delegation-exceeding-parent-unrepresentable falsifier)."""
    parent = _scope(StratumScope.of(Stratum.REFERENCE_REPO), EdgeScope.of("F"),
                    Window.interval(4, 8), Authority.read_only())
    wider = _scope(StratumScope.top(), EdgeScope.of("F", "D"),
                   Window.all(), Authority(Privilege.READ_PROPOSE, 1, WorldReach.IRREVERSIBLE))
    assert not (wider <= parent)          # the template really is wider
    assert parent.meet(wider) <= parent   # yet the child never exceeds the parent
    assert parent.meet(wider) == parent   # in fact meet with a superset returns the parent


# ── the PARTIAL T-meet — a cross-clock meet raises, never guesses ─────────────────────────────
def test_cross_clock_meet_raises():
    a = TimeScope(Clock.COMMIT, Window.all())
    b = TimeScope(Clock.N_S, Window.all())
    with pytest.raises(NoCommonClockError):
        a.meet(b)


def test_cross_clock_scope_meet_raises():
    a = _scope(StratumScope.of(Stratum.OPS), EdgeScope.bottom(), Window.all(), Authority.read_only())
    b = Scope(StratumScope.of(Stratum.OPS), EdgeScope.bottom(),
              TimeScope(Clock.LAST_WRITE, Window.all()), Authority.read_only(), tier=Tier.STATIC_GUARD)
    with pytest.raises(NoCommonClockError):
        a.meet(b)


def test_same_clock_meet_intersects_windows():
    a = TimeScope(Clock.COMMIT, Window.interval(0, 10))
    b = TimeScope(Clock.COMMIT, Window.interval(4, 20))
    assert a.meet(b) == TimeScope(Clock.COMMIT, Window.interval(4, 10))


def test_common_refinement_poset():
    """Comparable clocks resolve to the finer; every other distinct pair resolves only through the
    parked N ⇒ None (the constructor-error trigger). commit ⪰ distinct_snapshot is the one
    materialized comparability in v1."""
    assert common_refinement(Clock.COMMIT, Clock.DISTINCT_SNAPSHOT) is Clock.COMMIT
    assert common_refinement(Clock.COMMIT, Clock.N_S) is None       # only common refinement is N (parked)
    assert common_refinement(Clock.COMMIT, Clock.WALL) is None
    assert common_refinement(Clock.N, Clock.COMMIT) is None         # N itself is parked
    assert common_refinement(Clock.COMMIT, Clock.COMMIT) is Clock.COMMIT


# ── the SLICE rule ───────────────────────────────────────────────────────────────────────────
def test_slice_rule_rejects_cutless_multistratum_point():
    """|Σ|>1 + point window on a non-cut clock + no explicit cut ⇒ SliceError (bare 'now' is
    well-typed only single-stratum)."""
    with pytest.raises(SliceError):
        Scope(StratumScope.of(Stratum.OPS, Stratum.REFERENCE), EdgeScope.bottom(),
              TimeScope(Clock.WALL, Window.point(1)), Authority.read_only(), tier=Tier.STATIC_GUARD)


def test_slice_rule_satisfied_by_commit_clock():
    """The commit SHA IS the consistent cut for repo-backed strata — a multi-stratum point window
    on COMMIT is well-typed."""
    s = Scope(StratumScope.of(Stratum.OPS, Stratum.REFERENCE), EdgeScope.bottom(),
              TimeScope(Clock.COMMIT, Window.point("deadbeef")), Authority.read_only(),
              tier=Tier.STATIC_GUARD)
    assert len(s.sigma.strata) > 1


def test_slice_rule_satisfied_by_explicit_cut():
    s = Scope(StratumScope.of(Stratum.OPS, Stratum.REFERENCE), EdgeScope.bottom(),
              TimeScope(Clock.WALL, Window.point(1)), Authority.read_only(),
              tier=Tier.STATIC_GUARD, cut=("vector", 3, 7))
    assert s.cut == ("vector", 3, 7)


def test_single_stratum_point_needs_no_cut():
    """The five built Views are single-stratum, so the SLICE rule never fires for them."""
    s = _scope(StratumScope.of(Stratum.REFERENCE_REPO), EdgeScope.of("F"),
               Window.point("abc"), Authority.read_only())
    assert len(s.sigma.strata) == 1


# ── firewalls as order-ideals ────────────────────────────────────────────────────────────────
def test_denylist_ideal_excludes_foundation():
    grantable = _scope(StratumScope.top(), EdgeScope.top(), Window.all(),
                       Authority(Privilege.READ_PROPOSE, 1, WorldReach.SENSING))
    assert admissible(grantable, [DENYLIST_IDEAL])           # ⊤_Σ never names FOUNDATION
    naming_foundation = Scope(StratumScope(frozenset({Stratum.FOUNDATION})), EdgeScope.bottom(),
                              TimeScope(Clock.COMMIT, Window.all()), Authority.read_only(),
                              tier=Tier.CONVENTION)
    assert not admissible(naming_foundation, [DENYLIST_IDEAL])


def test_top_sigma_excludes_the_denylist():
    """⊤_Σ = R ∖ 𝔇 — even the fullest grant structurally excludes FOUNDATION."""
    assert Stratum.FOUNDATION not in StratumScope.top().strata


def test_mirror_payload_style_ideal():
    """The mechanism is general: an ideal over any stratum works the same way as the denylist."""
    curated_firewall = Ideal(name="no-curated", strata=frozenset({Stratum.CURATED}))
    reads_curated = _scope(StratumScope.of(Stratum.CURATED), EdgeScope.bottom(),
                           Window.all(), Authority.read_only())
    assert not admissible(reads_curated, [curated_firewall])


# ── Σ downward closure, E, A component behavior ───────────────────────────────────────────────
def test_stratum_downward_closure():
    """A grant over `reference` includes its `reference_repo` refinement (the downset)."""
    assert Stratum.REFERENCE_REPO in StratumScope.of(Stratum.REFERENCE).strata
    assert Stratum.MIRROR_AUTHORED in StratumScope.of(Stratum.MIRROR).strata
    # a leaf refinement alone is already downward-closed
    assert StratumScope.of(Stratum.REFERENCE_REPO).strata == frozenset({Stratum.REFERENCE_REPO})


def test_authority_meet_is_min_per_chain():
    a = Authority(Privilege.READ_PROPOSE, 1, WorldReach.REVERSIBLE)
    b = Authority(Privilege.READ, 1, WorldReach.SENSING)
    assert a.meet(b) == Authority(Privilege.READ, 1, WorldReach.SENSING)
    assert a.join(b) == Authority(Privilege.READ_PROPOSE, 1, WorldReach.REVERSIBLE)


def test_world_reach_has_the_none_floor():
    """WorldReach carries the NONE floor below SENSING that ReversibilityClass lacks (§2.1 / §4)."""
    assert WorldReach.NONE < WorldReach.SENSING < WorldReach.REVERSIBLE < WorldReach.IRREVERSIBLE
    assert Authority.read_only().world is WorldReach.NONE


def test_store_write_must_be_bit():
    with pytest.raises(ValueError):
        Authority(Privilege.READ, 2, WorldReach.NONE)


# ── tier is a min-composed annotation, NOT a lattice element ──────────────────────────────────
def test_tier_min_composed_and_excluded_from_equality():
    strong = _scope(StratumScope.of(Stratum.OPS), EdgeScope.bottom(), Window.all(), Authority.read_only())
    weak = Scope(StratumScope.of(Stratum.OPS), EdgeScope.bottom(),
                 TimeScope(Clock.COMMIT, Window.all()), Authority.read_only(), tier=Tier.CONVENTION)
    # same four lattice coordinates, different tier ⇒ EQUAL (tier is compare=False)
    assert strong == weak
    # composition takes the MIN tier along the chain
    assert strong.meet(weak).tier is Tier.CONVENTION
    assert strong.join(weak).tier is Tier.CONVENTION


# ── req() admissibility (the query-language check the Views' SCOPE constants feed) ────────────
def test_req_admissible_is_le():
    granted = _scope(StratumScope.top(), EdgeScope.top(), Window.all(),
                     Authority(Privilege.READ_PROPOSE, 1, WorldReach.SENSING))
    required = _scope(StratumScope.of(Stratum.REFERENCE_REPO), EdgeScope.of("F"),
                      Window.all(), Authority.read_only())
    assert req_admissible(required, granted)
    assert not req_admissible(granted, required)
