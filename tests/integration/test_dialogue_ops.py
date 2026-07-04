"""Dialogue operations — build plan Item 2b (dialogue-ingest-and-recursion.md §3–§4).

A correction ACTS on claims (a supersede RELATION + a DERIVED conclusion), never entering as a peer
authored node (the §2 failure). The conclusion is INTERPRETED so γ^d bounds it; the operations live
in a store distinct from the version + balance-edge stores (§4A C3). Deterministic; no model.
"""

from __future__ import annotations

from core.recursion import claim_confidence, decay_bound
from core.recursion_ops import (
    DIALOGUE_CONCLUSION,
    AttachDefeater,
    ClaimOpStore,
    RecordWarrant,
    Supersede,
    apply_operations,
    no_op_analyzer,
)
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
