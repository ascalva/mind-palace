"""Dialogue operations — build plan Item 2b + Item 9 (dialogue-ingest-and-recursion.md §3–§4;
supersession-lifecycle.md §4.2, §5).

A correction ACTS on claims (a supersede RELATION + a DERIVED conclusion), never entering as a peer
authored node (the §2 failure). The conclusion is INTERPRETED so γ^d bounds it, and grounds on the
warrant's K₀ anchors, NEVER on the claim it discredits (Item 9) — so `g` does not collapse when C is
superseded and a revision thread does not tower. The operations live in a store distinct from the
version + balance-edge stores (§4A C3). Deterministic; no model.
"""

from __future__ import annotations

from core.kernel.recursion import claim_confidence, decay_bound
from core.kernel.recursion_ops import (
    DIALOGUE_CONCLUSION,
    AttachDefeater,
    RecordWarrant,
    Supersede,
    no_op_analyzer,
)
from core.kernel.selfcheck import grounding_score
from core.stores.claim_ops import ClaimOpStore, apply_operations, stale_closure
from core.stores.derived import DerivedStore


def _stores(tmp_path):
    return ClaimOpStore(tmp_path / "claim_ops.sqlite"), DerivedStore(tmp_path / "derived.sqlite")


def test_supersede_acts_on_the_claim_not_a_peer_node(tmp_path):
    ops_store, derived = _stores(tmp_path)
    report = apply_operations(
        [Supersede(claim="noteC", conclusion="reconciled view", warrant="objection X answered")],
        ops_store=ops_store, derived=derived,
    )
    # C is superseded in the ACTIVE projection, recorded as a RELATION (not a peer node) ...
    assert ops_store.superseded() == {"noteC"}
    assert report.superseded == ("noteC",) and len(report.conclusions) == 1
    # ... and the conclusion C′ is a DERIVED interpreted claim, NOT an authored peer.
    art = derived.all(kind=DIALOGUE_CONCLUSION)[0]
    assert art.provenance.value == "interpreted"
    assert report.conclusions[0] == art.id
    assert derived.depth(art.id) >= 1                  # ≥1 step from authored ground → γ^d < 1


def test_conclusion_confidence_is_gamma_damped(tmp_path):
    # γ^d (I10): a dialogue conclusion can never reach an authored claim's confidence of 1.0.
    ops_store, derived = _stores(tmp_path)
    apply_operations([Supersede("noteC", "C prime", "because")],
                     ops_store=ops_store, derived=derived)
    art = derived.all(kind=DIALOGUE_CONCLUSION)[0]
    d = derived.depth(art.id)
    assert decay_bound(d) < 1.0 and claim_confidence(d) < 1.0


def test_defeater_and_warrant_are_recorded_without_superseding(tmp_path):
    ops_store, derived = _stores(tmp_path)
    apply_operations([AttachDefeater("noteC", "counterexample Y")],
                     ops_store=ops_store, derived=derived)
    apply_operations([RecordWarrant("the compromise", links=("noteC", "noteC2"))],
                     ops_store=ops_store, derived=derived)
    assert ops_store.defeaters("noteC") == ["counterexample Y"]
    assert ops_store.count() == 3                       # 1 defeater + 2 warrant links
    assert ops_store.superseded() == set()             # neither op supersedes anything
    assert derived.count() == 0                         # only Supersede mints a conclusion


def test_ops_live_in_a_store_distinct_from_version_and_edge_stores(tmp_path):
    # §4A C3: claim-supersede lives in its own store — never the version store, never the edge
    # store where a `sign` would corrupt the signed graph.
    from core.stores.edges import EdgeStore
    from core.stores.versions import VersionStore

    ops_store, derived = _stores(tmp_path)
    apply_operations([Supersede("noteC", "C prime", "because")],
                     ops_store=ops_store, derived=derived)
    assert ops_store.count() == 1
    assert VersionStore(tmp_path / "versions.sqlite").count() == 0     # untouched
    assert EdgeStore(tmp_path / "edges.sqlite").count() == 0     # no sign in the balance graph


def test_reapplying_the_same_operation_is_idempotent(tmp_path):
    ops_store, derived = _stores(tmp_path)
    op = [Supersede("noteC", "C prime", "because")]
    apply_operations(op, ops_store=ops_store, derived=derived)
    apply_operations(op, ops_store=ops_store, derived=derived)
    assert ops_store.count() == 1 and derived.count(kind=DIALOGUE_CONCLUSION) == 1


def test_default_analyzer_emits_no_operations(tmp_path):
    # PD4 floor: with no model analyzer wired, a dialogue emits NO ops → document-only ingest.
    ops_store, derived = _stores(tmp_path)
    ops = no_op_analyzer("some dialogue text where I changed my mind about X")
    apply_operations(ops, ops_store=ops_store, derived=derived)
    assert ops == [] and ops_store.count() == 0 and derived.count() == 0


# --- Item 9: revision grounds on the warrant's anchors, never on [C] (§4.2) ---

def test_supersede_grounds_on_warrant_anchors_not_the_claim(tmp_path):
    # The correction to committed Item 2b: C′.derived_from is the warrant's K₀ anchors, NEVER [C].
    ops_store, derived = _stores(tmp_path)
    apply_operations(
        [Supersede(claim="noteC", conclusion="C prime",
                   warrant="authA,authB answered it", anchors=("authA", "authB"))],
        ops_store=ops_store, derived=derived,
    )
    art = derived.all(kind=DIALOGUE_CONCLUSION)[0]
    assert set(art.derived_from) == {"authA", "authB"}     # grounds on the warrant's anchors ...
    assert "noteC" not in art.derived_from                 # ... never the claim it discredits


def test_a_thread_of_warrant_anchored_revisions_does_not_tower(tmp_path):
    # The §4.4 falsifier: strictly-improving revisions each cite K₀ anchors → g stays high (1.0) and
    # depth stays flat (1) along the thread — NO tower. The pre-fix predecessor-grounding towers.
    ops_store, derived = _stores(tmp_path)
    authored = {"authA", "authB"}

    r1 = apply_operations([Supersede("noteC", "rev1", "w1", anchors=("authA", "authB"))],
                          ops_store=ops_store, derived=derived).conclusions[0]
    r2 = apply_operations([Supersede(r1, "rev2", "w2", anchors=("authA",))],
                          ops_store=ops_store, derived=derived).conclusions[0]

    # flat depth + flat grounding ratio along the thread — the healthy signature
    assert derived.depth(r1) == 1 and derived.depth(r2) == 1
    assert grounding_score(derived.tails_of(r1), authored) == 1.0
    assert grounding_score(derived.tails_of(r2), authored) == 1.0

    # negative control: had rev2 grounded on its predecessor (a DERIVED node), it would tower —
    # depth rises (γ^d collapses) and flat grounding ratio falls to 0 (predecessor isn't authored)
    towered = derived.add(kind="control", summary="rev2-bad", subjects=("x",), derived_from=[r1]).id
    assert derived.depth(towered) == 2
    assert grounding_score(derived.tails_of(towered), authored) == 0.0


def test_default_anchors_for_a_derived_revision_inherit_leaves_never_the_claim(tmp_path):
    # No explicit anchors, DERIVED C: inherit its surviving authored leaves — never the claim itself
    # (a derived C decays / can be superseded without a verdict, so routing g through it is unsafe).
    ops_store, derived = _stores(tmp_path)
    seed = derived.add(kind=DIALOGUE_CONCLUSION, summary="seed", subjects=("s",),
                       derived_from=["authA"])
    r = apply_operations([Supersede(seed.id, "rev of seed", "w")],
                         ops_store=ops_store, derived=derived).conclusions[0]
    assert set(derived.tails_of(r)) == {"authA"}           # inherited the surviving authored leaf
    assert seed.id not in derived.tails_of(r)              # ... never the discredited derived claim
    assert derived.depth(r) == 1                           # authored leaf → depth 1, no tower


def test_authored_revision_grounds_on_bedrock_not_weightless(tmp_path):
    # Part 1 correction: superseding an AUTHORED (K₀) note with no anchors must NOT be weightless.
    # Authored content is bedrock (does not decay — I2 is derived-only), so C′ grounds on [C] → g=1;
    # the [C] prohibition applies only to a DERIVED C. Guards against a silent "blessed content
    # vanishes" bug (empty derived_from ⇒ g=0 ⇒ c=0 ⇒ not retrievable, with no verdict).
    ops_store, derived = _stores(tmp_path)
    r = apply_operations([Supersede("authZ", "a rephrase of authZ", "clarified wording")],
                         ops_store=ops_store, derived=derived).conclusions[0]
    assert set(derived.tails_of(r)) == {"authZ"}           # grounds on the authored bedrock, not ∅
    g = grounding_score(derived.tails_of(r), authored={"authZ"})
    assert g == 1.0 and decay_bound(derived.depth(r), grounding=g) > 0.0   # NOT weightless


def test_derived_cannot_outrank_authored_under_corrected_grounding(tmp_path):
    # The γ^{d≥1} guarantee survives correction: C′ grounds on authored anchors, so depth ≥ 1 and
    # decay_bound < 1 — it can never reach an authored claim's confidence of 1.0 (I1/I10).
    ops_store, derived = _stores(tmp_path)
    r = apply_operations([Supersede("noteC", "C prime", "w", anchors=("authA", "authB"))],
                         ops_store=ops_store, derived=derived).conclusions[0]
    assert derived.depth(r) >= 1 and decay_bound(derived.depth(r)) < 1.0


def test_stale_closure_flags_grounding_descendants_not_the_revision_chain(tmp_path):
    # Stale(C) = C's grounding-descendant closure (§5) — flagged for re-examination, not resolved.
    ops_store, derived = _stores(tmp_path)
    C = "authC"
    d = derived.add(kind=DIALOGUE_CONCLUSION, summary="D", subjects=("d",), derived_from=[C])
    e = derived.add(kind=DIALOGUE_CONCLUSION, summary="E", subjects=("e",), derived_from=[d.id])
    assert stale_closure(derived, C) == {d.id, e.id}       # D grounds on C; E grounds on D

    # a well-formed revision grounds on warrant anchors (not on C), so it does NOT extend Stale(C) —
    # the §5 "interaction with §4.2": correction stops revision chains self-generating stale sets
    rep = apply_operations([Supersede(C, "revC", "w", anchors=("authA",))],
                           ops_store=ops_store, derived=derived)
    assert set(rep.stale) == {d.id, e.id}
    assert rep.conclusions[0] not in rep.stale
