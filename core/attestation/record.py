"""The attestation record — a content-addressed (eventually signed) claim about one action.

A Vault token already attests "role X was authorized for resource Y at time T"; this record is
the analogue for the ACTION itself: "agent X performed action A on inputs I (by hash),
producing outputs O (by hash), under Constitution F, derived from the prior attestations whose
outputs it consumed." Chaining records by `derived_from_ids` gives every derived artifact a
verifiable lineage back to authored content (design-notes/attestation-layer.md §0–2).

Step 2 builds the RECORDS only — `signature`/`signer` stay empty. The id and (later) the
signature are both computed over `signing_payload()`, so the id is stable and the signature is
verifiable independently of the id (attestation-layer.md §2, §8: "start without signatures").
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


def _canonical(
    timestamp: str,
    agent_role: str,
    action: str,
    constitution_fingerprint: str,
    input_hashes: tuple[str, ...],
    output_hashes: tuple[str, ...],
    derived_from_ids: tuple[str, ...],
    vault_token_accessor: str,
) -> bytes:
    """The deterministic bytes the id AND the signature are computed over.

    Hash tuples are sorted so the identity is order-insensitive in inputs/outputs/parents;
    `sort_keys` + fixed separators make the encoding reproducible across processes/versions.
    """
    obj = {
        "action": action,
        "agent_role": agent_role,
        "constitution_fingerprint": constitution_fingerprint,
        "derived_from_ids": sorted(derived_from_ids),
        "input_hashes": sorted(input_hashes),
        "output_hashes": sorted(output_hashes),
        "timestamp": timestamp,
        "vault_token_accessor": vault_token_accessor,
    }
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class Attestation:
    id: str                          # content-address: SHA-256(signing_payload())
    timestamp: str                   # ISO-8601 (UTC, naive)
    agent_role: str                  # "dreamer" | "curator" | "vault_watcher" | ...
    action: str                      # "dream_pass" | "curate_finding" | "ingest_note" | ...
    constitution_fingerprint: str    # the fixed-point identity in force at the time (§15)
    input_hashes: tuple[str, ...]    # SHA-256 of each input (authored note digests, ...)
    output_hashes: tuple[str, ...]   # SHA-256/id of each output written to a store
    derived_from_ids: tuple[str, ...]  # ids of prior attestations whose outputs are our inputs
    vault_token_accessor: str = ""   # Vault's non-sensitive token id; populated at Step 5
    signature: str = ""              # Ed25519 over signing_payload(), base64; empty until Step 3
    signer: str = ""                 # "supervisor" | "owner" | "" (unsigned)

    def signing_payload(self) -> bytes:
        """The exact bytes the id is SHA-256'd from and the signature (Step 3) signs."""
        return _canonical(
            self.timestamp, self.agent_role, self.action, self.constitution_fingerprint,
            self.input_hashes, self.output_hashes, self.derived_from_ids,
            self.vault_token_accessor,
        )

    @classmethod
    def create(
        cls,
        *,
        timestamp: str,
        agent_role: str,
        action: str,
        constitution_fingerprint: str,
        input_hashes: tuple[str, ...] | list[str] = (),
        output_hashes: tuple[str, ...] | list[str] = (),
        derived_from_ids: tuple[str, ...] | list[str] = (),
        vault_token_accessor: str = "",
        signature: str = "",
        signer: str = "",
    ) -> Attestation:
        """Build an attestation with its content-addressed id computed (never set by hand)."""
        ih = tuple(sorted(input_hashes))
        oh = tuple(sorted(output_hashes))
        df = tuple(sorted(derived_from_ids))
        payload = _canonical(timestamp, agent_role, action, constitution_fingerprint,
                             ih, oh, df, vault_token_accessor)
        return cls(
            id=hashlib.sha256(payload).hexdigest(),
            timestamp=timestamp, agent_role=agent_role, action=action,
            constitution_fingerprint=constitution_fingerprint,
            input_hashes=ih, output_hashes=oh, derived_from_ids=df,
            vault_token_accessor=vault_token_accessor, signature=signature, signer=signer,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "timestamp": self.timestamp, "agent_role": self.agent_role,
            "action": self.action, "constitution_fingerprint": self.constitution_fingerprint,
            "input_hashes": list(self.input_hashes), "output_hashes": list(self.output_hashes),
            "derived_from_ids": list(self.derived_from_ids),
            "vault_token_accessor": self.vault_token_accessor,
            "signature": self.signature, "signer": self.signer,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Attestation:
        return cls(
            id=d["id"], timestamp=d["timestamp"], agent_role=d["agent_role"],
            action=d["action"], constitution_fingerprint=d["constitution_fingerprint"],
            input_hashes=tuple(d["input_hashes"]), output_hashes=tuple(d["output_hashes"]),
            derived_from_ids=tuple(d["derived_from_ids"]),
            vault_token_accessor=d.get("vault_token_accessor", ""),
            signature=d.get("signature", ""), signer=d.get("signer", ""),
        )
