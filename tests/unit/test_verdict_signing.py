"""Owner verdict signing — build plan Item 4a (design-notes/verdict-authority.md §3).

The two §2 defects of TOTP that an Ed25519 signature over the payload fixes are exactly the
assertions here: **asymmetric** (the verifier holds only the public key, so a compromised
acceptor cannot forge) and **payload-bound** (a signature for verdict A does not verify for
verdict B — not replayable across verdicts). Pure: no store, no model, no network.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from core.attestation import Ed25519Signer, generate_seed
from core.verdict import SignedVerdict, VerdictPayload, sign_verdict


def _owner() -> Ed25519Signer:
    return Ed25519Signer.from_seed(generate_seed(), "owner")


def _payload(*, seq: int = 1, subject: str = "insight-1",
             verdict: str = "promote") -> VerdictPayload:
    return VerdictPayload(subject_id=subject, verdict=verdict, seq=seq,
                          timestamp="2026-07-04T00:00:00")


def test_sign_then_verify_roundtrips():
    owner = _owner()
    signed = sign_verdict(_payload(), owner)
    assert signed.signer == "owner"
    assert signed.verify(owner.public_b64())


def test_wrong_owner_key_does_not_verify():
    signed = sign_verdict(_payload(), _owner())
    assert not signed.verify(_owner().public_b64())      # a different key cannot verify


@pytest.mark.parametrize("field,forged", [
    ("subject_id", "insight-9"),
    ("verdict", "reject"),
    ("seq", 999),
    ("timestamp", "2099-01-01T00:00:00"),
])
def test_tampering_any_signed_field_breaks_the_signature(field, forged):
    # Content-binding: the signature covers every field, so altering ANY one invalidates it —
    # a compromised store cannot flip a `promote` to a `reject` and keep the owner's signature.
    owner = _owner()
    p = _payload()
    signed = sign_verdict(p, owner)
    tampered = SignedVerdict(payload=replace(p, **{field: forged}),
                             signature=signed.signature, signer=signed.signer)
    assert not tampered.verify(owner.public_b64())


def test_signature_is_not_replayable_across_verdicts():
    # verdict-authority.md §2 defect 2, fixed: a signature entered for verdict A cannot be
    # stapled onto a different verdict B (different subject) at the same sequence number.
    owner = _owner()
    a = sign_verdict(_payload(seq=1, subject="A"), owner)
    replayed = SignedVerdict(payload=_payload(seq=1, subject="B"),
                             signature=a.signature, signer=a.signer)
    assert not replayed.verify(owner.public_b64())


def test_canonical_serialization_is_deterministic():
    # The same fields always sign to the same bytes (sort_keys) → stable, verifiable signatures.
    assert _payload().signing_payload() == _payload().signing_payload()


def test_negative_seq_is_refused_at_the_boundary():
    with pytest.raises(ValueError):
        VerdictPayload(subject_id="x", verdict="promote", seq=-1, timestamp="t")
