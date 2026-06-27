"""Ed25519 attestation crypto (attestation-layer.md §4): sign/verify, key round-trips, tamper."""

from __future__ import annotations

from core.attestation import Attestation, Ed25519Signer, generate_seed
from core.attestation.crypto import (
    private_from_seed,
    public_b64,
    public_from_b64,
    sign,
    verify,
)


def _payload() -> bytes:
    return Attestation.create(
        timestamp="2026-06-27T00:00:00", agent_role="dreamer", action="dream_pass",
        constitution_fingerprint="F", input_hashes=["a"], output_hashes=["o"],
    ).signing_payload()


def test_sign_then_verify_roundtrips():
    priv = private_from_seed(generate_seed())
    payload = b"hello attestation"
    assert verify(priv.public_key(), payload, sign(priv, payload))


def test_wrong_key_does_not_verify():
    p1, p2 = private_from_seed(generate_seed()), private_from_seed(generate_seed())
    assert not verify(p2.public_key(), b"x", sign(p1, b"x"))


def test_tampered_payload_does_not_verify():
    priv = private_from_seed(generate_seed())
    sig = sign(priv, b"original")
    assert not verify(priv.public_key(), b"tampered", sig)


def test_malformed_signature_returns_false_not_raise():
    priv = private_from_seed(generate_seed())
    assert verify(priv.public_key(), b"x", "not-base64!!") is False
    assert verify(priv.public_key(), b"x", "") is False


def test_public_key_base64_roundtrip():
    priv = private_from_seed(generate_seed())
    pub = public_from_b64(public_b64(priv))
    assert verify(pub, b"y", sign(priv, b"y"))


def test_seed_is_deterministic_key_material():
    seed = generate_seed()
    # The same seed reconstructs the same key (so a placed Keychain seed always signs the same).
    assert public_b64(private_from_seed(seed)) == public_b64(private_from_seed(seed))


def test_signer_signs_over_the_signing_payload():
    signer = Ed25519Signer.from_seed(generate_seed(), "supervisor")
    payload = _payload()
    assert signer.name == "supervisor"
    assert verify(public_from_b64(signer.public_b64()), payload, signer.sign(payload))
