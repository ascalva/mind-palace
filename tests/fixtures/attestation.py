"""Attestation test helpers — append-only store, fixed-fingerprint attestor, and the dev keys.

A fixed fingerprint makes chain assertions independent of the live Constitution text, so a test
can assert `chain.constitution_fingerprints() == {TEST_FINGERPRINT}` without coupling to the
real CONSTITUTION.md. The signing helpers use the committed DEV keys in ``tests/keys/`` (NOT
production secrets — see tests/keys/README.md).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from core.attestation import (
    AttestationStore,
    Ed25519Signer,
    StoreAttestor,
    make_verifier,
)
from core.attestation.crypto import Ed25519PublicKey, private_from_seed, public_b64

TEST_FINGERPRINT = "F-test-constitution"
_KEYS_DIR = Path(__file__).resolve().parent.parent / "keys"


def _seed(role: str) -> str:
    return (_KEYS_DIR / f"{role}.seed").read_text().strip()


def dev_signer(role: str = "supervisor") -> Ed25519Signer:
    """An Ed25519 signer backed by the committed dev seed for ``role``."""
    return Ed25519Signer.from_seed(_seed(role), role)


def dev_public_keys() -> dict[str, Ed25519PublicKey]:
    """The {signer: public_key} map matching the dev signers — for `make_verifier`."""
    from core.attestation.crypto import public_from_b64

    return {
        role: public_from_b64(public_b64(private_from_seed(_seed(role))))
        for role in ("supervisor", "owner")
    }


def dev_verifier(**kwargs):
    """A verifier over the dev public keys (enforces the gate-action owner-key policy)."""
    return make_verifier(dev_public_keys(), **kwargs)


def attestor_with_store(
    tmp_path: Path, *, fingerprint: str = TEST_FINGERPRINT, signer: Ed25519Signer | None = None,
    clock: Callable[[], str] | None = None,
) -> tuple[AttestationStore, StoreAttestor]:
    """Return (store, attestor) sharing one append-only store under ``tmp_path``. Pass a
    ``signer`` (e.g. ``dev_signer()``) to exercise the signed path. Pass a ``clock`` to FREEZE the
    timestamp — needed when comparing ids across two attestors, since the id is over
    ``signing_payload()`` (which includes the timestamp) and `_utcnow` can straddle a 1-second
    boundary between two emits."""
    store = AttestationStore(tmp_path / "attestations.sqlite")
    extra = {} if clock is None else {"clock": clock}
    return store, StoreAttestor(store, fingerprint=lambda: fingerprint, signer=signer, **extra)
