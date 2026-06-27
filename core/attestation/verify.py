"""Attestation signature verification + the gate-action owner-key policy (attestation-layer.md §3).

`make_verifier(public_keys)` returns a `verify(att) -> bool` suitable for
`AttestationChain.verify_signatures(...)`. An attestation verifies iff:
  - it carries a non-empty signature and a known signer,
  - the signature is valid over `att.signing_payload()` under that signer's public key (so the id
    can stay stable while the signature is checked independently — §2), and
  - **gate-decision attestations are signed by the OWNER key** (§3): a `gate_approve`/`gate_reject`
    record signed by anything other than `"owner"` is rejected, making gate decisions
    non-repudiable. (Gate-attestation *emission* lands with the Phase-10 gate loop; this is the
    verification half, enforced now.)
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from core.attestation.crypto import public_from_b64
from core.attestation.crypto import verify as _verify
from core.attestation.record import Attestation

# Actions whose attestation MUST be owner-signed (the highest-stakes records, §3).
GATE_ACTIONS = frozenset({"gate_approve", "gate_reject"})


def make_verifier(
    public_keys: dict[str, Ed25519PublicKey],
    *,
    require_owner_for: frozenset[str] = GATE_ACTIONS,
) -> Callable[[Attestation], bool]:
    """Return verify(att) -> bool over the given {signer_name: public_key} map."""

    def verify(att: Attestation) -> bool:
        if not att.signature or not att.signer:
            return False                                  # unsigned: not verifiable
        if att.action in require_owner_for and att.signer != "owner":
            return False                                  # gate decisions must be owner-signed
        pub = public_keys.get(att.signer)
        if pub is None:
            return False                                  # unknown signer
        return _verify(pub, att.signing_payload(), att.signature)

    return verify


def load_public_keys(
    supervisor_pub: Path | None, owner_pub: Path | None
) -> dict[str, Ed25519PublicKey]:
    """Load the committed public keys (non-secret) into a {signer: key} map. A missing file is
    simply absent from the map (verification of that signer then fails closed)."""
    keys: dict[str, Ed25519PublicKey] = {}
    for name, path in (("supervisor", supervisor_pub), ("owner", owner_pub)):
        if path is not None and Path(path).exists():
            keys[name] = public_from_b64(Path(path).read_text().strip())
    return keys


def build_verifier(config: object | None = None) -> Callable[[Attestation], bool]:
    """Wire a verifier from the configured public-key paths (`[attestation]`)."""
    from config.loader import get_config

    cfg = config or get_config()
    acfg = cfg.attestation
    return make_verifier(load_public_keys(acfg.supervisor_pub, acfg.owner_pub))
