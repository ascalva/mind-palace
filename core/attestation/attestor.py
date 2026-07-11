"""The Attestor seam — agents emit attestations through this, not by touching store or crypto.

Keeping emission behind a small interface means the agents (dreamer, curator, vault watcher)
never learn about signing keys or the store schema: they describe what they did (role, action,
input/output hashes) and the attestor stamps the Constitution fingerprint + timestamp, links the
chain, (later) signs, and appends. Step 3 adds the signing step INSIDE `emit` — the agents do
not change. (Model advises; code attests — the agent never holds the key.)
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Protocol

from config.loader import Config
from core.attestation.crypto import Ed25519Signer
from core.attestation.record import Attestation
from core.attestation.store import AttestationStore
from core.constitution import constitution_fingerprint


class AttestationKeyMissing(RuntimeError):
    """Signing was enabled (`[attestation] enabled = true`) but no signing key is placed.

    Fail-closed: rather than silently emit UNSIGNED attestations when the owner asked for signed
    ones, construction stops. Place the key (Keychain/Vault) before enabling — see the runbook."""


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
        vault_token_accessor: str = "",
    ) -> Attestation: ...


@dataclass
class StoreAttestor:
    """Builds, links, signs, and appends an attestation per agent action."""

    store: AttestationStore
    fingerprint: Callable[[], str] = constitution_fingerprint
    clock: Callable[[], str] = _utcnow
    # When present, each emitted attestation is signed over its signing_payload() and tagged with
    # the signer's name. None = records-only (Step 2 behavior; unsigned but still chained).
    signer: Ed25519Signer | None = None

    def emit(self, *, agent_role: str, action: str,
             input_hashes: Iterable[str] = (), output_hashes: Iterable[str] = (),
             derived_from_ids: Iterable[str] | None = None,
             vault_token_accessor: str = "") -> Attestation:
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
            # The Vault token's non-secret accessor (Step-5 join) — the audit handle for the
            # authorization this action ran under. NEVER the token itself (MintedToken docstring).
            # It is part of signing_payload(), so the authorization claim is signed/tamper-evident.
            # Default "" leaves every current emitter (Dreamer/Curator/VaultSync) unchanged: live
            # token threading is Phase 5 (agent factory + dispatcher), as in Step 4.
            vault_token_accessor=vault_token_accessor,
        )
        if self.signer is not None:
            # The signature covers signing_payload(), which EXCLUDES signature/signer — so signing
            # does not change the content-addressed id. Verification recomputes the same payload.
            att = replace(att, signature=self.signer.sign(att.signing_payload()),
                          signer=self.signer.name)
        self.store.append(att)
        return att


def build_attestor(config: Config | None = None) -> StoreAttestor:
    """Wire a StoreAttestor against the configured append-only attestation store.

    Signing is owner-gated: only when `[attestation] enabled = true` is a supervisor signer
    attached, and only if the private seed is actually placed (else fail-closed, never silently
    unsigned). Default (`enabled = false`) is records-only — the Step-2 behavior."""
    from config.loader import get_config, get_secret
    from core.attestation.store import open_attestation_store

    cfg = config or get_config()
    store = open_attestation_store(cfg)
    acfg = getattr(cfg, "attestation", None)
    if acfg is None or not acfg.enabled:
        return StoreAttestor(store)
    seed = get_secret(acfg.signing_key_secret)
    if not seed:
        raise AttestationKeyMissing(
            f"[attestation] enabled = true but no signing key at "
            f"get_secret({acfg.signing_key_secret!r}); place it (Keychain/Vault) before enabling"
        )
    return StoreAttestor(store, signer=Ed25519Signer.from_seed(seed, "supervisor"))
