# ── Family 1 boundary (labelings & information-flow) · the inbound verdict channel ──
# OBJECT:    the signed verdict payload — owner judgment made attributable + content-bound
#            (design-notes/verdict-authority.md §3; the sacred boundary, inbound: verdict).
# INVARIANT: the signature covers the canonical bytes of (subject, verdict, seq, timestamp),
#            so it is NOT replayable onto a different verdict; the acceptor holds only the
#            public key and CANNOT forge (asymmetric — the capability-dissolution test passing).
# ENFORCED:  structural — verification is public-key-only; monotonic-seq ENFORCEMENT is the
#            store's job (core/stores/verdicts.py, build plan Item 4b), not this pure layer's.
"""Canonical serialization + signing for owner verdicts (design-notes/verdict-authority.md §3).

A verdict authorizes a promotion / supersession of an interpretation. Authentication is an
**Ed25519 signature over the canonical serialization of the verdict** — asymmetric, so the
acceptor holds only the public key and cannot forge (verdict-authority.md §3: the
capability-dissolution test passing, and the two TOTP defects of §2 fixed — payload-binding
and non-repudiation). This module is the PURE core: the payload, its canonical bytes, signing,
and verification. No store, no apply — those are separate (the append-only signed store is
`core/stores/verdicts.py`; verify+apply is a component distinct from the Ambassador, which is
read+propose only).

Reuses the attestation Ed25519 primitives **verbatim** (`core/attestation/crypto.py`) — the same
primitive family the prompt-integrity audit names as the Threat B defense set, since verdict
forgery *is* a Threat B event (tampering with a governing signal). It deliberately does NOT reuse
the attestation *record*: `record.py::_canonical` has no field for a verdict category, a subject
id, or a monotonic sequence number, so a verdict needs its own canonical serialization (build
plan risk R6). Zone A, no network (imports only hashlib/json/dataclasses + the crypto wrappers).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from core.attestation.crypto import Ed25519Signer, public_from_b64, verify


def _canonical(subject_id: str, verdict: str, seq: int, timestamp: str) -> bytes:
    """The deterministic bytes the signature is computed over. `sort_keys` + fixed separators
    make the encoding reproducible across processes/versions (the `record.py::_canonical`
    discipline), so the same verdict always signs and verifies to the same bytes."""
    obj = {"seq": seq, "subject_id": subject_id, "timestamp": timestamp, "verdict": verdict}
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class VerdictPayload:
    """One owner verdict — the minimum §3 commitment: which insight/cluster the verdict applies
    to, which category, a MONOTONIC sequence number, and a timestamp.

    Signing THIS binds the authorization to THIS verdict: a compromised transport cannot take a
    signature produced for verdict A and staple it to verdict B (verdict-authority.md §2, defect
    2 — "authenticates a message, not a moment"). The `verdict` category is intentionally a free
    string here, not an enum: the taxonomy is owner-ratified elsewhere (build plan R3), and this
    pure layer must sign whatever the ratified set turns out to be without a code change."""

    subject_id: str     # the insight / cluster identifier the verdict applies to
    verdict: str        # the verdict category (owner-ratified taxonomy; not fixed here — R3)
    seq: int            # monotonic sequence number (a gap is censorship, detectable by an auditor)
    timestamp: str      # ISO-8601

    def __post_init__(self) -> None:
        # Fail closed at the boundary on a malformed sequence number (house style: reject at the
        # edge, cf. EdgeStore rejecting w < 0). Monotonicity ACROSS verdicts is the store's job.
        if self.seq < 0:
            raise ValueError(f"verdict seq must be >= 0 (monotonic sequence), got {self.seq}")

    def signing_payload(self) -> bytes:
        """The exact bytes the owner signature covers."""
        return _canonical(self.subject_id, self.verdict, self.seq, self.timestamp)

    def to_dict(self) -> dict[str, Any]:
        return {"subject_id": self.subject_id, "verdict": self.verdict,
                "seq": self.seq, "timestamp": self.timestamp}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> VerdictPayload:
        return cls(subject_id=d["subject_id"], verdict=d["verdict"],
                   seq=int(d["seq"]), timestamp=d["timestamp"])


@dataclass(frozen=True)
class SignedVerdict:
    """A verdict payload plus its owner Ed25519 signature — the transport artifact.

    `verify` needs only the owner PUBLIC key, so the acceptor (a compromised Ambassador, a
    tampered store) can check authenticity but never forge one (verdict-authority.md §3–§4:
    the Ambassador degrades to transport). The append-only store (build plan Item 4b) adds
    monotonic-seq enforcement + persistence on top of this."""

    payload: VerdictPayload
    signature: str       # base64 Ed25519 over payload.signing_payload()
    signer: str          # the signer name — "owner"

    def verify(self, public_b64: str) -> bool:
        """True iff `signature` is a valid signature of THIS payload under the given owner public
        key. Any failure mode (bad signature, wrong key, tampered field, malformed base64) returns
        False, never raises (delegates to `crypto.verify`)."""
        return verify(public_from_b64(public_b64), self.payload.signing_payload(), self.signature)

    def to_dict(self) -> dict[str, Any]:
        """The transport form — what the Ambassador (or any carrier) moves inbound. The signature
        travels WITH the payload, so the receiver re-verifies against the owner public key."""
        return {"payload": self.payload.to_dict(), "signature": self.signature,
                "signer": self.signer}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SignedVerdict:
        return cls(payload=VerdictPayload.from_dict(d["payload"]),
                   signature=d["signature"], signer=d["signer"])


def sign_verdict(payload: VerdictPayload, signer: Ed25519Signer) -> SignedVerdict:
    """Sign a verdict with the owner's key. The signer holds the private key inside the
    `Ed25519Signer`; this module — and any agent that later handles the result — only ever sees
    the signature, never the key (model advises, code signs; attestation-layer.md §4)."""
    return SignedVerdict(
        payload=payload,
        signature=signer.sign(payload.signing_payload()),
        signer=signer.name,
    )
