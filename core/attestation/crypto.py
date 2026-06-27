"""Ed25519 signing primitives for attestations (attestation-layer.md §4).

Thin wrappers over `cryptography`'s Ed25519. Keys are handled as base64 of the 32-byte raw seed
(private) / 32-byte raw point (public) — compact, copy-pasteable into Keychain, no PEM ceremony.
Signatures are base64 of the 64-byte raw signature.

`cryptography` is a crypto library, not a networking one — the import-lint network allowlist does
not flag it, so it is permitted in the sealed core (it opens no socket).
"""

from __future__ import annotations

import base64
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)


def generate_seed() -> str:
    """A fresh base64 Ed25519 private seed (32 bytes)."""
    return seed_b64(Ed25519PrivateKey.generate())


def seed_b64(priv: Ed25519PrivateKey) -> str:
    raw = priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    return base64.b64encode(raw).decode()


def public_b64(priv: Ed25519PrivateKey) -> str:
    raw = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return base64.b64encode(raw).decode()


def private_from_seed(seed: str) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(base64.b64decode(seed))


def public_from_b64(pub: str) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(base64.b64decode(pub))


def sign(priv: Ed25519PrivateKey, payload: bytes) -> str:
    return base64.b64encode(priv.sign(payload)).decode()


def verify(pub: Ed25519PublicKey, payload: bytes, signature_b64: str) -> bool:
    """True iff `signature_b64` is a valid Ed25519 signature of `payload` under `pub`. Any
    failure mode — bad signature, malformed base64, wrong length — returns False, never raises."""
    try:
        pub.verify(base64.b64decode(signature_b64), payload)
        return True
    except (InvalidSignature, ValueError):
        return False


@dataclass(frozen=True)
class Ed25519Signer:
    """A private key + a signer name ("supervisor" | "owner"). The key never leaves this object:
    callers hand it a payload and get a base64 signature back. (Code attests; the model — and any
    agent — only ever sees the signature, never the key. attestation-layer.md §4.)"""

    _private: Ed25519PrivateKey
    name: str

    @classmethod
    def from_seed(cls, seed: str, name: str) -> Ed25519Signer:
        return cls(private_from_seed(seed), name)

    def sign(self, payload: bytes) -> str:
        return sign(self._private, payload)

    def public_b64(self) -> str:
        return public_b64(self._private)
