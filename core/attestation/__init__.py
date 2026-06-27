"""Attestation layer — the runtime proof layer (design-notes/attestation-layer.md).

Complements the STATIC proof layer (import-lint / FSM checks / typed firewalls, which prove what
the code *cannot* do) with a RUNTIME record of what each agent *actually did*: signed (Step 3+),
content-addressed, chained back to authored content. Step 2 is records-only — unsigned.
"""

from core.attestation.attestor import Attestor, StoreAttestor, build_attestor
from core.attestation.record import Attestation
from core.attestation.store import (
    AttestationChain,
    AttestationStore,
    open_attestation_store,
)

__all__ = [
    "Attestation",
    "AttestationChain",
    "AttestationStore",
    "Attestor",
    "StoreAttestor",
    "build_attestor",
    "open_attestation_store",
]
