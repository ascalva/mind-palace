"""Attestation layer — the runtime proof layer (design-notes/attestation-layer.md).

Complements the STATIC proof layer (import-lint / FSM checks / typed firewalls, which prove what
the code *cannot* do) with a RUNTIME record of what each agent *actually did*: signed (Step 3+),
content-addressed, chained back to authored content. Step 2 is records-only — unsigned.
"""

from core.attestation.attestor import (
    AttestationKeyMissing,
    Attestor,
    StoreAttestor,
    build_attestor,
)
from core.attestation.crypto import Ed25519Signer, generate_seed
from core.attestation.record import Attestation
from core.attestation.store import (
    AttestationChain,
    AttestationStore,
    open_attestation_store,
)
from core.attestation.verify import (
    GATE_ACTIONS,
    build_verifier,
    load_public_keys,
    make_verifier,
)

__all__ = [
    "GATE_ACTIONS",
    "Attestation",
    "AttestationChain",
    "AttestationKeyMissing",
    "AttestationStore",
    "Attestor",
    "Ed25519Signer",
    "StoreAttestor",
    "build_attestor",
    "build_verifier",
    "generate_seed",
    "load_public_keys",
    "make_verifier",
    "open_attestation_store",
]
