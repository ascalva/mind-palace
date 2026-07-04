"""The inbound verdict channel — the owner's authorization to promote/supersede an
interpretation (design-notes/verdict-authority.md; the sacred boundary, inbound: verdict).

This package holds the PURE signing core (`payload.py`): the canonical serialization, signing,
and verification of an owner verdict. The append-only signed verdict STORE and the verify+apply
component are separate, later items (build plan Items 4b) so that "sign" (pure, here) stays
decoupled from "store" and "apply" (stateful). Zone A, no network.
"""

from core.verdict.payload import SignedVerdict, VerdictPayload, sign_verdict

__all__ = ["SignedVerdict", "VerdictPayload", "sign_verdict"]
