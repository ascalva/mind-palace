"""The Attestor seam — agents emit attestations through this, not by touching store or crypto.

Keeping emission behind a small interface means the agents (dreamer, curator, vault watcher)
never learn about signing keys or the store schema: they describe what they did (role, action,
input/output hashes) and the attestor stamps the Constitution fingerprint + timestamp, links the
chain, (later) signs, and appends. Step 3 adds the signing step INSIDE `emit` — the agents do
not change. (Model advises; code attests — the agent never holds the key.)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from core.attestation.record import Attestation
from core.attestation.store import AttestationStore
from core.constitution import constitution_fingerprint


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


class Attestor(Protocol):
    def emit(
        self,
        *,
        agent_role: str,
        action: str,
        input_hashes: tuple[str, ...] | list[str] = (),
        output_hashes: tuple[str, ...] | list[str] = (),
        derived_from_ids: list[str] | None = None,
    ) -> Attestation: ...


@dataclass
class StoreAttestor:
    """Builds, links, (Step-3) signs, and appends an attestation per agent action."""

    store: AttestationStore
    fingerprint: Callable[[], str] = constitution_fingerprint
    clock: Callable[[], str] = _utcnow

    def emit(self, *, agent_role, action, input_hashes=(), output_hashes=(),
             derived_from_ids=None) -> Attestation:
        ih = tuple(input_hashes)
        if derived_from_ids is None:
            # Auto-link the chain: any prior attestation that PRODUCED one of my inputs is a
            # parent. This is the mechanized form of "derived_from references the attestations
            # whose outputs are in my inputs" (attestation-layer.md §2) — so an ingest
            # attestation that output digest D becomes the parent of the dream that consumed D.
            derived_from_ids = sorted(self.store.producers_of(set(ih)))
        att = Attestation.create(
            timestamp=self.clock(),
            agent_role=agent_role,
            action=action,
            constitution_fingerprint=self.fingerprint(),
            input_hashes=ih,
            output_hashes=tuple(output_hashes),
            derived_from_ids=tuple(derived_from_ids),
        )
        # Step 3 inserts the signing step HERE (sign att.signing_payload(); set signature/signer)
        # before append — the agents stay untouched.
        self.store.append(att)
        return att


def build_attestor(config: object | None = None) -> StoreAttestor:
    """Wire a StoreAttestor against the configured append-only attestation store."""
    from core.attestation.store import open_attestation_store

    return StoreAttestor(open_attestation_store(config))
