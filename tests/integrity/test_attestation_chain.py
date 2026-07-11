"""Attestation-as-oracle (holistic-testing.md §1e) — part of the non-skippable integrity gate.

Asserts properties of the attestation CHAIN produced by a real dreaming pass, not of the dream
TEXT: every derived dream carries a complete chain down to authored content, and no dreamer
attestation ever references an OBSERVED input — the firewall holds at the attestation level,
even when an observed note sits right next to the authored cluster in vector space.

This is the runtime half of the firewall proof: the static half (MirrorView, import-lint) proves
the dreamer *cannot* read observed; this proves a real run *did not*.
"""

from __future__ import annotations

from core.attestation import AttestationStore
from core.curator import Curator
from core.dreaming import Dreamer
from core.stores.derived import DREAM, FINDING, DerivedStore
from tests.fixtures.attestation import TEST_FINGERPRINT, attestor_with_store
from tests.fixtures.stores import raw_store


class _FakeVectorStore:
    """Exposes only the provenance-filtered scan the dreamer's MirrorView projects over."""

    def __init__(self, rows):
        self._rows = rows

    def all_rows(self, *, provenances=None):
        if provenances is None:
            return list(self._rows)
        allowed = {str(p) for p in provenances}
        return [r for r in self._rows if r["provenance"] in allowed]


def _corpus(tmp_path):
    """Two near-identical AUTHORED notes (which cluster) + one OBSERVED note sitting right next
    to them in vector space (which the firewall must still exclude). Digests are real raw-store
    addresses, so chain leaves resolve to authored content actually present in raw."""
    raw = raw_store(tmp_path)
    d1, _ = raw.add_text("racing thoughts keep me awake at night")
    d2, _ = raw.add_text("slow breathing settles me before bed")
    dobs, _ = raw.add_text("third-party sleep-tracker nightly summary")
    rows = [
        {"digest": d1, "title": "sleep-1", "text": "racing thoughts",
         "provenance": "authored-solo", "vector": [1.0, 0.0, 0.0]},
        {"digest": d2, "title": "sleep-2", "text": "slow breathing",
         "provenance": "authored-solo", "vector": [0.97, 0.03, 0.0]},
        {"digest": dobs, "title": "tracker", "text": "observed exhaust",
         "provenance": "observed", "vector": [0.96, 0.04, 0.0]},   # close, but OBSERVED
    ]
    return raw, _FakeVectorStore(rows), (d1, d2), dobs


def _run_dream(tmp_path):
    raw, store, authored, dobs = _corpus(tmp_path)
    att_store, attestor = attestor_with_store(tmp_path)
    # Ingest attestations first — the authored leaves the dream chain bottoms out in.
    for d in authored:
        attestor.emit(agent_role="vault_watcher", action="ingest_note",
                      input_hashes=[d], output_hashes=[d])
    dreamer = Dreamer(
        store=store,
        synthesize=lambda messages: "A theme of [[sleep-1]] and [[sleep-2]] — rest recurs.",
        derived=DerivedStore(tmp_path / "derived.sqlite"),
        threshold=0.6, min_cluster_size=2, attestor=attestor,
    )
    themes = dreamer.dream()
    return raw, att_store, dreamer, themes, authored, dobs


def test_dream_records_carry_a_complete_chain_to_authored_leaves(tmp_path):
    raw, att_store, dreamer, themes, authored, _ = _run_dream(tmp_path)
    assert themes                                          # the cluster formed
    records = dreamer.derived.all(kind=DREAM)
    assert records
    for rec in records:
        assert rec.attestation_id is not None             # record links to its attestation
        chain = att_store.chain_for(rec.attestation_id)
        assert chain.is_complete()                        # no broken links
        assert chain.roles() == {"dreamer", "vault_watcher"}   # links down to ingest
        assert chain.constitution_fingerprints() == {TEST_FINGERPRINT}
        assert chain.leaf_input_hashes() == set(authored)  # bottoms out in exactly those notes
        for h in chain.leaf_input_hashes():
            assert raw.exists(h)                           # authored content present in raw


def test_dreamer_attestation_never_references_observed(tmp_path):
    _, att_store, _, _, authored, dobs = _run_dream(tmp_path)
    dreamer_atts = att_store.by_role("dreamer")
    assert dreamer_atts
    for att in dreamer_atts:
        assert dobs not in att.input_hashes               # observed never entered a dream
        assert set(att.input_hashes) <= set(authored)     # only authored leaves


def _run_curate(tmp_path):
    raw, store, authored, dobs = _corpus(tmp_path)
    att_store, attestor = attestor_with_store(tmp_path)
    # Ingest attestations first — the authored leaves the curator's findings bottom out in.
    for d in authored:
        attestor.emit(agent_role="vault_watcher", action="ingest_note",
                      input_hashes=[d], output_hashes=[d])
    curator = Curator(
        store=store,
        derived=DerivedStore(tmp_path / "derived.sqlite"),
        raw=raw,                       # both authored digests exist in raw -> no prune noise
        near_dup_threshold=0.99,
        attestor=attestor,
    )
    report = curator.curate()
    return raw, att_store, curator, report, authored, dobs


def test_curator_finding_carries_a_complete_chain_to_authored_leaves(tmp_path):
    raw, att_store, curator, report, authored, _ = _run_curate(tmp_path)
    assert report.findings                                 # the near-dup pair fired
    records = curator.derived.all(kind=FINDING)
    assert records
    for rec in records:
        assert rec.attestation_id is not None             # record links to its attestation
        chain = att_store.chain_for(rec.attestation_id)
        assert chain.is_complete()                        # no broken links
        assert chain.roles() == {"curator", "vault_watcher"}   # links down to ingest
        assert chain.constitution_fingerprints() == {TEST_FINGERPRINT}
        assert chain.leaf_input_hashes() == set(authored)  # bottoms out in exactly those notes
        for h in chain.leaf_input_hashes():
            assert raw.exists(h)                           # authored content present in raw


def test_curator_attestation_never_references_observed(tmp_path):
    _, att_store, _, _, authored, dobs = _run_curate(tmp_path)
    curator_atts = att_store.by_role("curator")
    assert curator_atts
    for att in curator_atts:
        assert dobs not in att.input_hashes                # observed never entered a finding
        assert set(att.input_hashes) <= set(authored)      # only authored leaves


def test_attestation_store_is_append_only_by_construction():
    # The runtime audit trail cannot be rewritten: no mutation API exists to call.
    assert not hasattr(AttestationStore, "delete")
    assert not hasattr(AttestationStore, "update")
