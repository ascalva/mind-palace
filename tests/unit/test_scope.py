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

import dataclasses
import itertools

import pytest

from core.scope import (
    DENYLIST_IDEAL,
    PRIVATE_STRATA,
    Authority,
    Clock,
    ClockMismatchError,
    EdgeScope,
    Ideal,
    Inv,
    NoCommonClockError,
    Privilege,
    Rate,
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
    rate_under,
    req_admissible,
    zone_admissible,
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
        pop.append(_scope(sigma, edges[i % len(edges)],
                          windows[i % len(windows)], auths[i % len(auths)]))
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
    a = _scope(StratumScope.of(Stratum.OPS), EdgeScope.bottom(), Window.all(),
               Authority.read_only())
    b = Scope(StratumScope.of(Stratum.OPS), EdgeScope.bottom(),
              TimeScope(Clock.LAST_WRITE, Window.all()), Authority.read_only(),
              tier=Tier.STATIC_GUARD)
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
    assert common_refinement(Clock.COMMIT, Clock.N_S) is None   # only N (parked)
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
    strong = _scope(StratumScope.of(Stratum.OPS), EdgeScope.bottom(),
                    Window.all(), Authority.read_only())
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


# ── Item 4 — Inv vs Rate(κ) result typing + Rule CLOCK ────────────────────────────────────────
def test_rule_clock_accepts_matching_clock():
    s = _scope(StratumScope.of(Stratum.REFERENCE_REPO), EdgeScope.of("F"), Window.all(),
               Authority.read_only())   # clocked on COMMIT
    r = rate_under(3.5, scope=s, clock=Clock.COMMIT)
    assert isinstance(r, Rate)
    assert r.clock is Clock.COMMIT and r.value == 3.5


def test_rule_clock_rejects_mismatched_clock():
    """`q : s → Rate(κ')` under a scope clocked on κ≠κ' is rejected — a rate off an unacknowledged
    clock is unrepresentable (the A7 guard, one type earlier)."""
    s = _scope(StratumScope.of(Stratum.REFERENCE_REPO), EdgeScope.of("F"), Window.all(),
               Authority.read_only())   # clocked on COMMIT
    with pytest.raises(ClockMismatchError):
        rate_under(3.5, scope=s, clock=Clock.WALL)


def test_rate_carries_its_clock_never_a_bare_number():
    """A Rate is structurally unconstructable without a clock — `clock` is a required field."""
    field_names = {f.name for f in dataclasses.fields(Rate)}
    assert "clock" in field_names
    with pytest.raises(TypeError):
        Rate(value=1.0)          # type: ignore[call-arg]  # missing the required clock — the point


def test_coherence_report_audits_as_inv():
    """The one BUILT temporal instrument is Inv, not Rate: `CoherenceReport` holds a count
    (`coherence_norm`) + two anchors (`commit_from`/`commit_to`) + booleans/counts, and NO ratio
    field — it never divides (dn-capability-scope §2.3 / bp-039 §3 Q5). Asserted STRUCTURALLY so it
    stays true as the report evolves."""
    from core.temporal_view import CoherenceReport

    fields = {f.name: f.type for f in dataclasses.fields(CoherenceReport)}
    # the two anchors + the count are present
    assert {"commit_from", "commit_to", "coherence_norm"} <= set(fields)
    # NO field is a float / ratio / rate — the Inv guarantee (no clock index divides in)
    for name, ftype in fields.items():
        assert "float" not in str(ftype), f"CoherenceReport.{name} looks rate-like ({ftype})"
        assert "rate" not in name.lower() and "ratio" not in name.lower()
    # and the marker type wraps a value cleanly
    assert Inv(value=7).value == 7


# ── D1 (dn-agent-taxonomy §2.3/§2.5) — DIALOGUE stratum + fiber C, additive lattice extensions ──
# These EXTEND the suite: every test above passes verbatim; the extension adds no new machinery,
# only new elements to the existing enum/literal, so the lattice laws must still hold over them.
def test_dialogue_downward_closure():
    """A `dialogue` grant includes both refinement predicates (the downset)."""
    d = StratumScope.of(Stratum.DIALOGUE).strata
    assert Stratum.DIALOGUE_TRANSCRIPT in d
    assert Stratum.DIALOGUE_ARTIFACT in d
    # a leaf refinement alone is already downward-closed (no parent pulled in)
    assert (StratumScope.of(Stratum.DIALOGUE_TRANSCRIPT).strata
            == frozenset({Stratum.DIALOGUE_TRANSCRIPT}))


def test_top_sigma_includes_dialogue_and_still_excludes_foundation():
    """⊤_Σ grows by the DIALOGUE base stratum (+ its two refinements) and STILL excludes 𝔇 — the
    extension widens the grantable top by exactly one base stratum, the denylist untouched."""
    top = StratumScope.top().strata
    assert {Stratum.DIALOGUE, Stratum.DIALOGUE_TRANSCRIPT, Stratum.DIALOGUE_ARTIFACT} <= top
    assert Stratum.FOUNDATION not in top


def test_fiber_c_joins_the_edge_top():
    """C (causal-witnessed) joins F and D in the edge-fiber top (dn-agent-taxonomy §2.5). C is a
    fresh independent axis: it meets F/D to ⊥ and joins to the union — orthogonal, not a refine."""
    assert EdgeScope.top().fibers == frozenset({"F", "D", "C"})
    assert EdgeScope.of("C") <= EdgeScope.top()
    assert EdgeScope.of("C").meet(EdgeScope.of("F")) == EdgeScope.bottom()
    assert EdgeScope.of("C").join(EdgeScope.of("F")) == EdgeScope.of("C", "F")


def test_lattice_laws_hold_over_dialogue_and_c():
    """The lattice laws (idempotent / commutative / associative / absorption, `⊑ ⟺ meet`,
    delegation monotonicity) hold over a population carrying the NEW DIALOGUE strata and the C fiber
    — proof the extension is a genuine lattice extension, not merely new enum members."""
    def s(sigma: StratumScope, edges: EdgeScope) -> Scope:
        return _scope(sigma, edges, Window.all(), Authority.read_only())

    ext = [
        s(StratumScope.of(Stratum.DIALOGUE), EdgeScope.of("C")),
        s(StratumScope.of(Stratum.DIALOGUE_TRANSCRIPT), EdgeScope.of("F", "C")),
        s(StratumScope.of(Stratum.DIALOGUE, Stratum.OPS), EdgeScope.of("F", "D", "C")),
        s(StratumScope.top(), EdgeScope.top()),
        s(StratumScope.of(Stratum.REFERENCE), EdgeScope.of("D", "C")),
    ]
    for a in ext:
        assert a.meet(a) == a and a.join(a) == a
    for a, b in itertools.combinations(ext, 2):
        assert a.meet(b) == b.meet(a) and a.join(b) == b.join(a)
        assert a.meet(a.join(b)) == a and a.join(a.meet(b)) == a
        assert (a <= b) == (a.meet(b) == a)
        assert a.meet(b) <= a and a.meet(b) <= b        # delegation monotonicity over C/dialogue
    for a, b, c in itertools.combinations(ext, 3):
        assert a.meet(b).meet(c) == a.meet(b.meet(c))
        assert a.join(b).join(c) == a.join(b.join(c))


# ── H-0 (dn-synchronic-diachronic-dreamer §2.6-1) — the HYPOTHETICAL overlay stratum ─────────────
# ADDITIVE only: every test above passes verbatim (top() is byte-identical — HYPOTHETICAL is NOT in
# ⊤_Σ). The overlay is grantable ONLY by a scope that names it; a composed read {durable, HYP} is
# multi-stratum by construction, so SLICE fires; a grant omitting it cannot admit a staged read.
def test_default_grants_exclude_hypothetical():
    """"Default grants exclude it" is STRUCTURAL: even ⊤_Σ (the fullest ordinary grant) omits
    HYPOTHETICAL — unlike DIALOGUE (a base stratum IN top), the overlay must be named explicitly."""
    assert Stratum.HYPOTHETICAL not in StratumScope.top().strata
    assert Stratum.HYPOTHETICAL not in StratumScope.of(Stratum.MIRROR, Stratum.REFERENCE).strata
    # 𝔇-subtraction unaffected — top() still excludes FOUNDATION and still includes DIALOGUE.
    assert Stratum.FOUNDATION not in StratumScope.top().strata
    assert Stratum.DIALOGUE in StratumScope.top().strata


def test_hypothetical_is_grantable_only_when_named():
    """A scope CAN name HYPOTHETICAL (it is admissible — NOT the denylist), and naming it is the
    only way it appears; it pulls in no refinement (an overlay, not a refined base)."""
    named = StratumScope.of(Stratum.HYPOTHETICAL)
    assert named.strata == frozenset({Stratum.HYPOTHETICAL})       # no downward closure to pull
    hyp_scope = _scope(named, EdgeScope.bottom(), Window.all(), Authority.read_only())
    assert admissible(hyp_scope, [DENYLIST_IDEAL])                 # grantable when named (≠ 𝔇)


def test_hypothetical_composed_read_demands_slice():
    """The composed counterfactual read {durable, HYPOTHETICAL} is multi-stratum, so a point window
    on a non-cut clock with no explicit cut raises SliceError — a counterfactual read is well-typed
    only as 'the graph at cut c ∪ the subspace at generation g' (§2.6-1)."""
    with pytest.raises(SliceError):
        Scope(StratumScope.of(Stratum.MIRROR_AUTHORED, Stratum.HYPOTHETICAL), EdgeScope.bottom(),
              TimeScope(Clock.WALL, Window.point("g5")), Authority.read_only(),
              tier=Tier.STATIC_GUARD)
    # a COMMIT clock (the cut IS the commit SHA) OR an explicit cut satisfies SLICE
    ok_commit = Scope(StratumScope.of(Stratum.MIRROR_AUTHORED, Stratum.HYPOTHETICAL),
                      EdgeScope.bottom(), TimeScope(Clock.COMMIT, Window.point("deadbeef")),
                      Authority.read_only(), tier=Tier.STATIC_GUARD)
    assert Stratum.HYPOTHETICAL in ok_commit.sigma.strata
    ok_cut = Scope(StratumScope.of(Stratum.MIRROR_AUTHORED, Stratum.HYPOTHETICAL),
                   EdgeScope.bottom(), TimeScope(Clock.WALL, Window.point("t")),
                   Authority.read_only(), tier=Tier.STATIC_GUARD, cut=("cut-sha", "gen-3"))
    assert ok_cut.cut == ("cut-sha", "gen-3")


def test_req_admissible_fails_a_composed_read_whose_grant_omits_hypothetical():
    """A read naming HYPOTHETICAL is admissible ONLY under a grant that also names it — the
    Σ-visibility capability test. A grant over the durable side alone (however wide) refuses it."""
    required = _scope(StratumScope.of(Stratum.MIRROR_AUTHORED, Stratum.HYPOTHETICAL),
                      EdgeScope.bottom(), Window.all(), Authority.read_only())
    grant_without = _scope(StratumScope.top(), EdgeScope.top(), Window.all(),
                           Authority(Privilege.READ_PROPOSE, 1, WorldReach.SENSING))
    assert not req_admissible(required, grant_without)            # ⊤_Σ omits HYPOTHETICAL ⇒ refused
    grant_with = _scope(StratumScope.of(Stratum.MIRROR_AUTHORED, Stratum.HYPOTHETICAL),
                        EdgeScope.top(), Window.all(),
                        Authority(Privilege.READ_PROPOSE, 1, WorldReach.SENSING))
    assert req_admissible(required, grant_with)                   # naming it admits the read


def test_lattice_laws_hold_over_hypothetical():
    """The lattice laws hold over a population carrying HYPOTHETICAL beside durable strata — proof
    the overlay is a genuine additive lattice extension, not merely a new enum member. 𝔇-subtraction
    is unaffected (top() untouched)."""
    def s(sigma: StratumScope) -> Scope:
        return _scope(sigma, EdgeScope.of("F"), Window.all(), Authority.read_only())

    ext = [
        s(StratumScope.of(Stratum.HYPOTHETICAL)),
        s(StratumScope.of(Stratum.HYPOTHETICAL, Stratum.MIRROR_AUTHORED)),
        s(StratumScope.of(Stratum.HYPOTHETICAL, Stratum.OPS)),
        s(StratumScope.top()),
        s(StratumScope.of(Stratum.MIRROR_AUTHORED)),
    ]
    for a in ext:
        assert a.meet(a) == a and a.join(a) == a
    for a, b in itertools.combinations(ext, 2):
        assert a.meet(b) == b.meet(a) and a.join(b) == b.join(a)
        assert a.meet(a.join(b)) == a and a.join(a.meet(b)) == a
        assert (a <= b) == (a.meet(b) == a)
        assert a.meet(b) <= a and a.meet(b) <= b            # delegation monotonicity, overlay too
    for a, b, c in itertools.combinations(ext, 3):
        assert a.meet(b).meet(c) == a.meet(b.meet(c))
        assert a.join(b).join(c) == a.join(b.join(c))
    # the overlay never launders into ⊤_Σ: meeting top() with a HYPOTHETICAL-naming scope keeps it
    # out of top's strata (top has no HYPOTHETICAL to contribute)
    assert Stratum.HYPOTHETICAL not in ext[3].sigma.meet(ext[0].sigma).strata


# ── G-D (dn-agentic-loop §2.3; bp-086 / AL-1) — the zone-boundary law Σ(private) ⊥ W_world ────────
# The cross-coordinate law `s.Σ ⊓ PRIVATE_STRATA ≠ ⊥ ⇒ s.A.W_world = NONE`, made a ratchet. F-AL3
# demands the ADVERSARIAL case: a CONSTRUCTABLE deployed grant with non-⊥ private Σ AND W_world>NONE
# must be REFUSED — if it cannot be structurally refused, the §2.3 derivation is decorative. It can.
def test_private_strata_is_every_grantable_stratum_except_world():
    """PRIVATE_STRATA = ⊤_Σ ∖ {world}: the corpus/vault side. It carries the refinements (so a scope
    naming only `mirror_authored` counts private) and excludes `world`, FOUNDATION (𝔇, ungrantable),
    and the HYPOTHETICAL overlay (not a base stratum)."""
    assert PRIVATE_STRATA == StratumScope.top().strata - {Stratum.WORLD}
    assert Stratum.WORLD not in PRIVATE_STRATA
    assert Stratum.FOUNDATION not in PRIVATE_STRATA
    assert Stratum.HYPOTHETICAL not in PRIVATE_STRATA
    # private base strata + refinements ARE in (the widest-exclusion default: ops/reference
    # kept IN pending the owner's proposed→ready call, plan §3 Q3)
    for s in (Stratum.MIRROR, Stratum.MIRROR_AUTHORED, Stratum.CURATED, Stratum.OBSERVED,
              Stratum.OPS, Stratum.REFERENCE, Stratum.REFERENCE_REPO, Stratum.INTERPRETED,
              Stratum.DIALOGUE, Stratum.DIALOGUE_TRANSCRIPT, Stratum.DIALOGUE_ARTIFACT):
        assert s in PRIVATE_STRATA


def test_zone_law_REFUSES_a_constructable_private_read_with_world_reach():
    """F-AL3, the crux. A hand-built, WELL-TYPED deployed grant with non-⊥ private Σ (the fullest
    private read) AND W_world = SENSING (>NONE) is CONSTRUCTABLE — and `zone_admissible` REFUSES it.
    A single private refinement + world reach is refused too. This is the structural refusal
    §2.3 requires; without it the zone derivation would be decorative."""
    # the broad adversary: ⊤_Σ (all private strata) + a nonzero world reach, on a cut clock (Window
    # ALL, so SLICE does not fire) — a genuine, constructable scope, not a malformed one.
    adversary = Scope(StratumScope.top(), EdgeScope.top(),
                      TimeScope(Clock.COMMIT, Window.all()),
                      Authority(Privilege.READ_PROPOSE, 1, WorldReach.SENSING),
                      tier=Tier.STATIC_GUARD)
    assert adversary.sigma.strata & PRIVATE_STRATA        # antecedent TRUE — it reads private
    assert adversary.authority.world > WorldReach.NONE    # consequent's negation — it reaches world
    assert not zone_admissible(adversary)                 # ⇒ REFUSED (the law bites)

    # the same refusal at the finest granularity: one private refinement + any nonzero reach
    for reach in (WorldReach.SENSING, WorldReach.REVERSIBLE, WorldReach.IRREVERSIBLE):
        narrow_leak = _scope(StratumScope.of(Stratum.MIRROR_AUTHORED), EdgeScope.bottom(),
                             Window.all(), Authority(Privilege.READ, 0, reach))
        assert not zone_admissible(narrow_leak)


def test_zone_law_admits_private_read_with_no_world_reach():
    """The compliant internal-actor corner: broad private Σ but W_world = NONE ⇒ admissible (the
    consequent holds)."""
    compliant = Scope(StratumScope.top(), EdgeScope.top(),
                      TimeScope(Clock.COMMIT, Window.all()),
                      Authority(Privilege.READ_PROPOSE, 1, WorldReach.NONE),
                      tier=Tier.STATIC_GUARD)
    assert compliant.sigma.strata & PRIVATE_STRATA        # reads private
    assert zone_admissible(compliant)                     # but no world reach ⇒ admissible


def test_zone_law_admits_bottom_sigma_at_any_reach():
    """The external-executor corner: Σ = ⊥ reads nothing private, so the antecedent is FALSE and the
    scope is admissible at EVERY world reach — this is how EA-x holds world reach lawfully (bright
    line 2)."""
    for reach in (WorldReach.NONE, WorldReach.SENSING, WorldReach.REVERSIBLE,
                  WorldReach.IRREVERSIBLE):
        eax = Scope(StratumScope.bottom(), EdgeScope.bottom(),
                    TimeScope(Clock.NOW, Window.all()),
                    Authority(Privilege.READ, 0, reach), tier=Tier.STATIC_GUARD)
        assert not (eax.sigma.strata & PRIVATE_STRATA)    # antecedent FALSE
        assert zone_admissible(eax)


def test_zone_law_admits_world_only_sigma_at_any_reach():
    """A scope naming ONLY `world` (the public coordinate) reads nothing private ⇒ admissible at any
    reach. `world ∉ PRIVATE_STRATA` is the hinge."""
    for reach in (WorldReach.NONE, WorldReach.SENSING, WorldReach.IRREVERSIBLE):
        world_only = _scope(StratumScope.of(Stratum.WORLD), EdgeScope.bottom(),
                            Window.all(), Authority(Privilege.READ, 0, reach))
        assert world_only.sigma.strata == frozenset({Stratum.WORLD})
        assert zone_admissible(world_only)
