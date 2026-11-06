"""The landing order of the ingress (dn-ingress D1, D5; ING-7 in `formal/Palace/Ingress.lean`).

A run lands in stages, and the stage order is what makes an interrupted run safe: every prefix is
a consistent state, every stage is idempotent, and the **idempotence key** (the catalog's digest
for the path, which the UNCHANGED check reads) is the last write. A crash before the key leaves a
run the next run repeats in full, so the next run lands exactly what the interrupted one would
have; a crash after the key changes nothing, since the key is the last write. The two lanes that
wrote the key first (`sync_path`, `capture_turn`) and the one that had no key (`ingest_curated`)
were the audit's defects 1 and 2 (dn-ingress §9).

Two helpers make the stages before the key idempotent at the ledger grain: a version is appended
only when the digest is not already the chain's head (`appendIfNew` in the model; a revert to an
older version's bytes still appends, since the head differs), and an attestation is emitted once
per (action, digest), so a re-run after a crash between the attestation and the key does not
attest twice. A rename is the one event the digest cannot show: the same bytes under a new path
are a version event by the identity design (bp-031), and `sync_path` tells it from a re-run by
the catalog, where the old path still binds the identity until the pass tombstones it. The
attestation check scans the store; an index by output hash is the efficiency item if it ever
shows in a profile.
"""

from __future__ import annotations

from typing import Any

from core.attestation import Attestation, Attestor
from core.stores.versions import Version, VersionStore


def record_version_if_new(versions: VersionStore, doc_id: str, digest: str) -> Version | None:
    """Append the next version unless `digest` is already the chain's head: the model's
    `appendIfNew`. A re-run after a crash appends nothing; a revert still appends."""
    current = versions.current(doc_id)
    if current is not None and current.digest == digest:
        return None
    return versions.record(doc_id, digest)


def attested_by(attestor: Attestor | None, action: str, digest: str) -> list[str]:
    """The ids of the attestations of `action` that name `digest` among their outputs, through
    the store's producer lookup (`producers_of`, a pass over the ledger)."""
    store: Any = getattr(attestor, "store", None)
    if store is None or not digest:
        return []
    out = []
    for att_id in sorted(store.producers_of({digest})):
        att = store.get(att_id)
        if att is not None and att.action == action:
            out.append(att_id)
    return out


def already_attested(attestor: Attestor | None, action: str, digest: str) -> bool:
    """Whether an attestation of `action` already names `digest` among its outputs."""
    return bool(attested_by(attestor, action, digest))


def attest_once(attestor: Attestor | None, *, agent_role: str, action: str, digest: str,
                event: bool = False) -> Attestation | None:
    """Emit the landing's attestation (input and output the content digest: the chain's leaf)
    unless one already names it, so a re-run after a crash attests nothing twice. `event` is a
    landing that is an event of its own though its bytes were attested before, a revert that
    appended a version: it is attested again. `None` when there is no attestor or nothing to add."""
    if attestor is None or (not event and already_attested(attestor, action, digest)):
        return None
    return attestor.emit(agent_role=agent_role, action=action,
                         input_hashes=[digest], output_hashes=[digest])
