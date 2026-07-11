"""Attestation signatures verify; tampering breaks them; gate decisions are owner-signed.

Part of the non-skippable integrity gate — this is the tamper-evidence of the runtime proof
layer. A signed attestation is only as trustworthy as the guarantee that any change to its
content invalidates the signature, and that the highest-stakes records (gate decisions) carry
the OWNER's signature, not the supervisor's (attestation-layer.md §3–4).
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from core.attestation import Attestation, make_verifier
from tests.fixtures.attestation import (
    attestor_with_store,
    dev_public_keys,
    dev_signer,
    dev_verifier,
)


def _signed(role: str = "supervisor", *, action: str = "dream_pass") -> Attestation:
    att = Attestation.create(
        timestamp="2026-06-27T00:00:00", agent_role="dreamer", action=action,
        constitution_fingerprint="F", input_hashes=["a"], output_hashes=["o"],
    )
    signer = dev_signer(role)
    return replace(att, signature=signer.sign(att.signing_payload()), signer=role)


def test_emitted_signatures_verify(tmp_path):
    store, attestor = attestor_with_store(tmp_path, signer=dev_signer("supervisor"))
    a = attestor.emit(agent_role="dreamer", action="dream_pass",
                      input_hashes=["d1"], output_hashes=["x"])
    verify = dev_verifier()
    assert a.signer == "supervisor" and a.signature
    assert verify(a)
    assert verify(store.get(a.id))                  # survives the store round-trip


def test_signing_does_not_change_the_content_address(tmp_path):
    # The id is over signing_payload(), which excludes signature/signer — so the SAME action
    # has the same id whether signed or not (the signature is verified independently, §2). Freeze
    # the clock so both attestors stamp the SAME timestamp: otherwise the two emits could straddle a
    # 1-second boundary and differ on the timestamp — an id change unrelated to signing (a flake).
    def clock() -> str:
        return "2026-06-27T00:00:00"

    _, signed = attestor_with_store(tmp_path / "s", signer=dev_signer("supervisor"), clock=clock)
    _, unsigned = attestor_with_store(tmp_path / "u", clock=clock)

    def _emit(attestor):
        return attestor.emit(agent_role="dreamer", action="dream_pass",
                             input_hashes=["d1"], output_hashes=["x"])

    a = _emit(signed)
    b = _emit(unsigned)
    assert a.id == b.id and a.signature and not b.signature


def test_tampering_a_field_breaks_the_signature():
    verify = dev_verifier()
    a = _signed()
    assert verify(a)
    assert not verify(replace(a, input_hashes=("evil",)))   # changed a signed field
    assert not verify(replace(a, constitution_fingerprint="G"))


def test_tampering_the_signature_breaks_verification():
    verify = dev_verifier()
    a = _signed()
    assert not verify(replace(a, signature="AAAA"))
    assert not verify(replace(a, signer=""))                # dropping the signer is unverifiable


def test_unknown_signer_does_not_verify():
    # A verifier that only holds the owner key cannot verify a supervisor-signed record.
    only_owner = make_verifier({"owner": dev_public_keys()["owner"]})
    assert not only_owner(_signed(role="supervisor"))


def test_chain_verify_signatures(tmp_path):
    store, attestor = attestor_with_store(tmp_path, signer=dev_signer("supervisor"))
    ingest = attestor.emit(agent_role="vault_watcher", action="ingest_note",
                           input_hashes=["d1"], output_hashes=["d1"])
    dream = attestor.emit(agent_role="dreamer", action="dream_pass",
                          input_hashes=["d1"], output_hashes=["x"])
    chain = store.chain_for(dream.id)
    verify = dev_verifier()
    assert chain.is_complete()
    assert chain.verify_signatures(verify)

    def one_link_tampered(att):
        return False if att.id == ingest.id else verify(att)

    assert not chain.verify_signatures(one_link_tampered)   # one bad link fails the whole chain


def test_gate_decisions_must_be_owner_signed():
    verify = dev_verifier()
    # A gate approval signed by the SUPERVISOR is rejected; the OWNER signature is required.
    assert not verify(_signed(role="supervisor", action="gate_approve"))
    assert verify(_signed(role="owner", action="gate_approve"))
    assert not verify(_signed(role="supervisor", action="gate_reject"))
    assert verify(_signed(role="owner", action="gate_reject"))


def test_committed_pubkeys_match_dev_seeds():
    # ops/attestation/*.pub (the verify-script default anchors) match tests/keys/*.seed, so a
    # dev-signed attestation verifies against the committed public keys out of the box.
    repo = Path(__file__).resolve().parents[2]
    for role in ("supervisor", "owner"):
        committed = (repo / "ops" / "attestation" / f"{role}.pub").read_text().strip()
        assert committed == dev_signer(role).public_b64()
