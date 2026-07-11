"""Owner CLI logic: declare an authored-historical supersession between two vault notes.

The phone capture shortcut emits a NEW timestamp-named file per note, so a phone-side
"edit" is a new document, not an in-place amendment — the version machinery never fires.
The correct semantics for that flow is the owner-declared K₀↔K₀ cross-document
supersession (the-edge-model.md §4a; the founding edge's mechanism): the new note goes
active, the original stays intact in raw + history, and the edge records the owner's
ruling. This module resolves the two notes and mints the declaration; it is an
OWNER-OPERATED entry point (`mind-palace supersede`) — the store's boundary check refuses
any machine caller regardless (`MachineAuthorityRefused`).

In-place edits (Mac / Files app) still take the version-amendment path automatically;
this CLI is only for the new-file flow. Retrieval demotion of the superseded note is the
active-projection consumer (Item 8 territory) — until it lands, both notes surface in
retrieval and the edge is durable provenance awaiting its consumer.
"""

from __future__ import annotations

from core.stores.authored_supersession import (
    AuthoredSupersessionStore,
    owner_declaration,
)
from core.stores.catalog import VaultCatalog


class AmbiguousRef(ValueError):
    """A ref that matches zero or several active documents — refuse, never guess."""


def resolve(catalog: VaultCatalog, ref: str) -> tuple[str, str]:
    """(source_path, digest) for a unique active doc matched by full path or suffix."""
    matches = sorted(p for p in catalog.active_paths() if p == ref or p.endswith(ref))
    if len(matches) != 1:
        raise AmbiguousRef(f"{ref!r} matches {len(matches)} active document(s): "
                           f"{matches[:5] if matches else 'none'}")
    entry = catalog.get(matches[0])
    assert entry is not None
    return entry.source_path, entry.digest


def declare(catalog: VaultCatalog, store: AuthoredSupersessionStore,
            old_ref: str, new_ref: str, note: str = "") -> tuple[str, str]:
    """Resolve both notes and record `new supersedes old`. Returns the digest pair."""
    old_path, old_digest = resolve(catalog, old_ref)
    new_path, new_digest = resolve(catalog, new_ref)
    if old_digest == new_digest:
        raise AmbiguousRef(f"{old_ref!r} and {new_ref!r} resolve to the same content "
                           f"({old_digest[:12]}) — nothing to supersede")
    store.record(old_digest, new_digest, declaration=owner_declaration(),
                 note=note or f"owner-declared: {new_path} supersedes {old_path}")
    print(f"declared: {old_path}\n  ({old_digest[:12]}… → historical)\n"
          f"       ⤷ {new_path}\n  ({new_digest[:12]}… → active)")
    return old_digest, new_digest
